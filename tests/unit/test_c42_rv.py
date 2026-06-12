"""WP-4-VERIFY: T0 tests for the C-42 vol-regression repro pipeline (H-02).

Covers, in forensics style (No-Lookahead first):

1. Hard no-lookahead: future perturbation never changes feature row i;
   the target IS forward-looking (changes under future perturbation);
   the last HORIZON_BARS target rows are NaN.
2. Target maths: log(realised_vol_60m) against an exact hand calculation.
3. Purged-WF splitter discipline: disjoint OOS windows, chronological order,
   gap >= purge + embargo (timestamp assertions), >= 2 OOS windows enforced,
   deterministic.
4. Feature completeness: exactly 36 numeric features, no all-NaN column on the
   fixture, ASSUMED/DOCUMENTED provenance tagging present and consistent.
5. HAR baseline sanity on the GARCH fixture (regression vs builder smoke
   0.26-0.33 per fold).
6. QLIKE correctness (hand calculation) + asymmetry (under-forecast costlier).
7. Benjamini-Hochberg FDR on a constructed 36-p-value family (hand-derived
   rejection set, includes the step-up rescue case).
8. Model adapters: har + histgbm fit/predict; lightgbm import guard raises a
   clean ImportError with the `.[vol]` hint.
9. CLI end-to-end: `--quick --model har` on the fixture writes JSON+MD with the
   H-02 reference and per-fold criteria, exit 0; defective CSV -> exit 1
   without a traceback.

All seeds fixed; heavy fixture loads are session-scoped.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bybit_edge.research.c42_rv import (
    FEATURE_PROVENANCE,
    HARRVBaseline,
    HORIZON_BARS,
    HistGBMVolModel,
    benjamini_hochberg,
    build_features,
    build_model,
    build_target,
    feature_names,
    purged_walk_forward,
    qlike,
    run_pipeline,
)
from bybit_edge.research.c42_rv.splits import (
    DEFAULT_EMBARGO_BARS,
    PURGE_HORIZON_BARS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CSV = REPO_ROOT / "tests" / "fixtures" / "c42" / "btc_garch_30d.csv"
CLI_SCRIPT = REPO_ROOT / "scripts" / "c42_repro.py"

KLINE_COLUMNS = ["ts", "open", "high", "low", "close", "volume", "turnover"]
SEED = 42
BAR_MS = 60_000  # 1-minute bars


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def garch_klines() -> pd.DataFrame:
    """Full 30d GARCH(1,1) fixture (43200 1-min bars), loaded once."""
    df = pd.read_csv(FIXTURE_CSV)
    return df[KLINE_COLUMNS].sort_values("ts").reset_index(drop=True)


@pytest.fixture(scope="session")
def garch_slice(garch_klines: pd.DataFrame) -> pd.DataFrame:
    """Small slice (1500 bars) for the perturbation tests — fast rebuilds."""
    return garch_klines.iloc[:1500].reset_index(drop=True)


@pytest.fixture(scope="session")
def base_features(garch_slice: pd.DataFrame):
    """Unperturbed features on the slice (reference for no-lookahead checks)."""
    feats, specs = build_features(garch_slice)
    return feats, specs


def _perturb_future(klines: pd.DataFrame, from_pos: int) -> pd.DataFrame:
    """Return a copy whose rows >= from_pos are aggressively distorted.

    Prices are scaled and shifted, volume/turnover multiplied — any leak of
    rows >= from_pos into earlier features/targets must show up.
    """
    out = klines.copy()
    price_cols = ["open", "high", "low", "close"]
    out.loc[from_pos:, price_cols] = out.loc[from_pos:, price_cols] * 1.5 + 123.0
    out.loc[from_pos:, ["volume", "turnover"]] *= 3.0
    return out


def _plain_close_frame(close: np.ndarray) -> pd.DataFrame:
    """Minimal frame accepted by build_target (only `close` is required)."""
    ts = np.arange(len(close), dtype=np.int64) * BAR_MS + 1_735_689_600_000
    return pd.DataFrame({"close": close}, index=pd.Index(ts, name="ts"))


# --------------------------------------------------------------------------- #
# 1) No-Lookahead (hard)                                                      #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("i", [400, 800, 1200])
def test_feature_row_invariant_under_future_perturbation(
    garch_slice: pd.DataFrame, base_features, i: int
) -> None:
    """Feature[i] must be a function of bars [..., i] only: distorting every
    bar from i+1 onward may not change row i in ANY of the 36 columns."""
    feats_base, specs = base_features
    names = feature_names(specs)

    perturbed = _perturb_future(garch_slice, from_pos=i + 1)
    feats_pert, _ = build_features(perturbed)

    row_base = feats_base[names].iloc[i]
    row_pert = feats_pert[names].iloc[i]
    pd.testing.assert_series_equal(
        row_base, row_pert, check_exact=True,
        obj=f"feature row {i} changed under future-only perturbation",
    )
    # The whole causal past must be invariant too, not just row i.
    pd.testing.assert_frame_equal(
        feats_base[names].iloc[: i + 1],
        feats_pert[names].iloc[: i + 1],
        check_exact=True,
    )


@pytest.mark.parametrize("i", [100, 500])
def test_target_row_changes_under_future_perturbation(i: int) -> None:
    """Target[i] covers forward returns r_{i+1}..r_{i+60}: perturbing a close
    INSIDE that window must change target[i] (forward-looking confirmed)."""
    rng = np.random.default_rng(SEED)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 1e-3, size=i + 200)))
    frame = _plain_close_frame(close)
    target_base = build_target(frame)

    perturbed = close.copy()
    perturbed[i + 30] *= 1.10  # inside the forward window i+1..i+60
    target_pert = build_target(_plain_close_frame(perturbed))

    assert not np.isclose(target_base.iloc[i], target_pert.iloc[i]), (
        "target[i] ignored a perturbation inside its forward 60m window — "
        "the target is not forward-looking"
    )
    # ...and a perturbation strictly AFTER the window must NOT change target[i].
    perturbed2 = close.copy()
    perturbed2[i + HORIZON_BARS + 1:] *= 1.10
    target_pert2 = build_target(_plain_close_frame(perturbed2))
    assert target_base.iloc[i] == target_pert2.iloc[i], (
        "target[i] leaked information from beyond bar i+60"
    )


def test_target_last_horizon_rows_nan() -> None:
    """The final HORIZON_BARS rows have an incomplete forward window -> NaN."""
    rng = np.random.default_rng(SEED)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 1e-3, size=400)))
    target = build_target(_plain_close_frame(close))

    assert target.iloc[-HORIZON_BARS:].isna().all(), (
        f"last {HORIZON_BARS} target rows must be NaN (incomplete forward window)"
    )
    assert not np.isnan(target.iloc[-HORIZON_BARS - 1]), (
        "row -(HORIZON_BARS+1) has a complete forward window and must be finite"
    )


# --------------------------------------------------------------------------- #
# 2) Target maths                                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("i", [0, 37, 110])
def test_target_matches_hand_calculation(i: int) -> None:
    """log(realised_vol_60m)[i] == log(sqrt(sum_{k=1..60} ln(c_{i+k}/c_{i+k-1})^2))."""
    rng = np.random.default_rng(7)
    close = 50.0 * np.exp(np.cumsum(rng.normal(0.0, 2e-3, size=240)))
    target = build_target(_plain_close_frame(close))

    fwd_sq = [
        np.log(close[i + k] / close[i + k - 1]) ** 2
        for k in range(1, HORIZON_BARS + 1)
    ]
    expected = np.log(np.sqrt(np.sum(fwd_sq)))
    assert target.iloc[i] == pytest.approx(expected, rel=1e-12, abs=1e-15)


# --------------------------------------------------------------------------- #
# 3) Splitter discipline                                                      #
# --------------------------------------------------------------------------- #

def test_splitter_disjoint_chronological_purged_with_timestamps() -> None:
    """OOS windows disjoint + chronological; train/test gap >= purge+embargo,
    asserted on real timestamps (1 bar = 60000 ms)."""
    n_rows = 10_000
    embargo = DEFAULT_EMBARGO_BARS
    t0 = 1_735_689_600_000
    ts = t0 + np.arange(n_rows, dtype=np.int64) * BAR_MS

    folds = purged_walk_forward(n_rows, n_folds=3, embargo_bars=embargo)
    assert len(folds) == 3

    min_gap_ms = (PURGE_HORIZON_BARS + embargo) * BAR_MS
    prev_test_end_ts = -np.inf
    for f in folds:
        # chronological: train strictly before test
        assert f.train_idx.max() < f.test_idx.min()
        # contiguous positional blocks
        assert np.array_equal(
            f.test_idx, np.arange(f.test_span[0], f.test_span[1] + 1)
        )
        # timestamp gap: last train ts to first test ts must exceed purge+embargo
        gap_ms = ts[f.test_idx.min()] - ts[f.train_idx.max()]
        assert gap_ms > min_gap_ms, (
            f"fold {f.fold_id}: train->test timestamp gap {gap_ms} ms "
            f"<= required purge+embargo {min_gap_ms} ms"
        )
        # builder-verified positional gap: 60 purge + 1440 embargo -> 1501 bars
        assert f.test_idx.min() - f.train_idx.max() == PURGE_HORIZON_BARS + embargo + 1
        # OOS windows disjoint + strictly increasing in time
        assert ts[f.test_idx.min()] > prev_test_end_ts
        prev_test_end_ts = ts[f.test_idx.max()]
        # no train row's forward label window may reach into the test block:
        # last train bar + HORIZON_BARS must end before the first test bar.
        assert f.train_idx.max() + HORIZON_BARS < f.test_idx.min()


def test_splitter_enforces_two_oos_windows() -> None:
    """H-02 requires >= 2 disjoint OOS windows — n_folds=1 must raise."""
    with pytest.raises(ValueError, match=">= 2"):
        purged_walk_forward(10_000, n_folds=1)


def test_splitter_rejects_too_short_data() -> None:
    """Too few rows for folds + purge + embargo -> clean ValueError, no folds."""
    with pytest.raises(ValueError, match="too few rows"):
        purged_walk_forward(2_000, n_folds=2, embargo_bars=DEFAULT_EMBARGO_BARS)


def test_splitter_deterministic() -> None:
    """Identical inputs -> identical folds (no hidden RNG / discretion)."""
    a = purged_walk_forward(9_000, n_folds=3, embargo_bars=720)
    b = purged_walk_forward(9_000, n_folds=3, embargo_bars=720)
    assert len(a) == len(b)
    for fa, fb in zip(a, b):
        assert fa.fold_id == fb.fold_id
        assert fa.train_span == fb.train_span
        assert fa.test_span == fb.test_span
        assert np.array_equal(fa.train_idx, fb.train_idx)
        assert np.array_equal(fa.test_idx, fb.test_idx)


# --------------------------------------------------------------------------- #
# 4) Feature completeness + provenance tagging                                #
# --------------------------------------------------------------------------- #

def test_feature_completeness_and_provenance(base_features) -> None:
    """Exactly 36 numeric features on the fixture, none all-NaN, every feature
    carries a checkable DOCUMENTED/ASSUMED provenance tag."""
    feats, specs = base_features
    names = feature_names(specs)

    assert len(specs) == 36
    assert len(names) == len(set(names)) == 36
    # 36 feature columns + the `close` passthrough (NOT a model feature)
    assert set(feats.columns) == set(names) | {"close"}

    for name in names:
        col = feats[name]
        assert pd.api.types.is_numeric_dtype(col), f"{name} is not numeric"
        assert not col.isna().all(), f"{name} is all-NaN on the fixture"

    # provenance tagging: attribute present and consistent with the summary
    assert all(s.provenance in ("DOCUMENTED", "ASSUMED") for s in specs)
    counts = {
        "DOCUMENTED": sum(s.provenance == "DOCUMENTED" for s in specs),
        "ASSUMED": sum(s.provenance == "ASSUMED" for s in specs),
    }
    assert counts == FEATURE_PROVENANCE == {"DOCUMENTED": 1, "ASSUMED": 35}
    # the one documented feature is atr_60 (research_notes #1)
    documented = [s.name for s in specs if s.provenance == "DOCUMENTED"]
    assert documented == ["atr_60"]
    # ASSUMED tagging is also documented in the module docstring
    from bybit_edge.research.c42_rv import features as features_mod
    assert "ASSUMED" in (features_mod.__doc__ or "")


def test_features_require_sorted_input(garch_slice: pd.DataFrame) -> None:
    """Unsorted ts (causal-order violation) must raise, not silently compute."""
    shuffled = garch_slice.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted"):
        build_features(shuffled)


# --------------------------------------------------------------------------- #
# 5) HAR baseline sanity on the GARCH fixture                                 #
# --------------------------------------------------------------------------- #

def test_har_baseline_r2_on_garch_fixture(garch_klines: pd.DataFrame) -> None:
    """GARCH data has genuine vol clustering: HAR must achieve OOS-R^2 > 0.1
    in EVERY fold (builder smoke reference: 0.26-0.33); an R^2 near 1 would
    itself indicate leakage, so we also cap it."""
    result = run_pipeline(
        garch_klines, symbol="BTCUSDT", model_name="har", n_folds=2, seed=SEED
    )
    assert result["n_folds"] == 2
    assert len(result["folds"]) == 2
    for fr in result["folds"]:
        assert fr["model_r2"] > 0.1, (
            f"fold {fr['fold_id']}: HAR OOS-R^2 {fr['model_r2']:.4f} <= 0.1 "
            "on GARCH fixture — vol-clustering signal lost (regression vs "
            "builder smoke 0.26-0.33)"
        )
        assert fr["model_r2"] < 0.7, (
            f"fold {fr['fold_id']}: HAR OOS-R^2 {fr['model_r2']:.4f} suspiciously "
            "high on noisy GARCH data — possible lookahead leak"
        )
        # comparison HAR (rv_60/120/240 regressors) must also see the signal
        assert fr["har_r2"] > 0.1
    assert result["precheck_verdict"] == "BASELINE-ONLY"


# --------------------------------------------------------------------------- #
# 6) QLIKE                                                                    #
# --------------------------------------------------------------------------- #

def test_qlike_hand_calculation() -> None:
    """QLIKE = mean(ratio - log(ratio) - 1) on the VARIANCE scale, computed by
    hand on constructed (forecast, actual) pairs."""
    # pair 1: perfect forecast -> contribution 0
    # pair 2: true vol 0.02 vs predicted 0.01 -> variance ratio 4
    y_true_log = np.log(np.array([0.01, 0.02]))
    y_pred_log = np.log(np.array([0.01, 0.01]))
    expected = (0.0 + (4.0 - np.log(4.0) - 1.0)) / 2.0
    assert qlike(y_true_log, y_pred_log) == pytest.approx(expected, rel=1e-12)

    # perfect forecast over a whole vector -> exactly 0
    y = np.log(np.array([0.005, 0.01, 0.03]))
    assert qlike(y, y) == pytest.approx(0.0, abs=1e-12)

    # single pair, ratio 1/4 (over-forecast): 0.25 - log(0.25) - 1
    y_true_log2 = np.log(np.array([0.01]))
    y_pred_log2 = np.log(np.array([0.02]))
    expected2 = 0.25 - np.log(0.25) - 1.0
    assert qlike(y_true_log2, y_pred_log2) == pytest.approx(expected2, rel=1e-12)


@pytest.mark.parametrize("delta", [0.1, 0.5, 1.0])
def test_qlike_penalises_underestimation_more(delta: float) -> None:
    """Property: QLIKE is asymmetric — under-forecasting vol by `delta` in log
    space costs MORE than over-forecasting by the same amount."""
    y_true = np.log(np.full(16, 0.02))
    under = qlike(y_true, y_true - delta)  # predicted vol too LOW
    over = qlike(y_true, y_true + delta)   # predicted vol too HIGH
    assert under > over, (
        f"QLIKE must punish underestimation harder (delta={delta}): "
        f"under={under:.6f} <= over={over:.6f}"
    )
    assert under > 0.0 and over > 0.0


# --------------------------------------------------------------------------- #
# 7) Benjamini-Hochberg FDR                                                   #
# --------------------------------------------------------------------------- #

def test_benjamini_hochberg_known_rejection_set() -> None:
    """36-p family with a hand-derived BH(alpha=0.10) rejection set, including
    the step-up rescue: p_(10)=0.029 fails its own threshold (10/36*0.1=0.02778)
    but is rejected because p_(11)=0.0305 <= 11/36*0.1=0.030556."""
    p_values: dict[str, float] = {}
    for k in range(9):  # ranks 1..9: clearly significant
        p_values[f"sig_{k}"] = 0.001
    p_values["rescued"] = 0.029   # rank 10: above own threshold, rescued
    p_values["anchor"] = 0.0305   # rank 11: passes 0.030556 -> k_max = 11
    for k in range(25):           # ranks 12..36: clearly insignificant
        p_values[f"null_{k}"] = 0.5 + k * 0.01

    res = benjamini_hochberg(p_values, alpha=0.10)
    assert res.n_features == 36
    assert res.alpha == 0.10
    assert res.threshold_p == pytest.approx(0.0305)
    assert res.n_significant == 11
    expected = {f"sig_{k}" for k in range(9)} | {"rescued", "anchor"}
    assert set(res.significant_features) == expected
    assert all(not res.rejected[f"null_{k}"] for k in range(25))


def test_benjamini_hochberg_no_rejections() -> None:
    """All p large -> empty rejection set, threshold 0."""
    p_values = {f"f{k}": 0.4 + 0.01 * k for k in range(36)}
    res = benjamini_hochberg(p_values, alpha=0.10)
    assert res.n_significant == 0
    assert res.significant_features == []
    assert res.threshold_p == 0.0


# --------------------------------------------------------------------------- #
# 8) Model adapters                                                           #
# --------------------------------------------------------------------------- #

def _mini_xy(n: int = 300, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    X = np.abs(rng.normal(0.01, 0.003, size=(n, k))) + 1e-4  # positive, vol-like
    y = np.log(X[:, 0] + 0.5 * X[:, 1] + 1e-6) + rng.normal(0, 0.05, size=n)
    return X, y


def test_har_adapter_fit_predict() -> None:
    X, y = _mini_xy()
    model = HARRVBaseline()
    assert model.name == "har"
    with pytest.raises(RuntimeError, match="before fit"):
        model.predict(X)
    pred = model.fit(X, y).predict(X)
    assert pred.shape == (X.shape[0],)
    assert np.isfinite(pred).all(), "HAR produced NaN/inf predictions"
    assert model.feature_importance() is None


def test_histgbm_adapter_fit_predict() -> None:
    pytest.importorskip("sklearn", reason="histgbm needs scikit-learn ([vol] extra)")
    X, y = _mini_xy()
    model = HistGBMVolModel(seed=SEED, max_iter=20)  # small for T0 runtime
    assert model.name == "histgbm"
    pred = model.fit(X, y).predict(X)
    assert pred.shape == (X.shape[0],)
    assert np.isfinite(pred).all(), "HistGBM produced NaN/inf predictions"
    # HistGBM has no native gain importance; pipeline uses permutation importance
    assert model.feature_importance() is None


def test_lightgbm_import_guard_mentions_vol_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing lightgbm must raise a clean, actionable ImportError pointing at
    `pip install -e .[vol]` — never a bare ModuleNotFoundError at fit time.
    Forced via sys.modules so the test holds even if lightgbm IS installed."""
    monkeypatch.setitem(sys.modules, "lightgbm", None)  # forces ImportError
    with pytest.raises(ImportError) as excinfo:
        build_model("lightgbm", seed=SEED)
    msg = str(excinfo.value)
    assert ".[vol]" in msg, f"ImportError lacks the [vol] install hint: {msg}"
    assert "lightgbm" in msg.lower()


def test_build_model_unknown_name_raises() -> None:
    with pytest.raises(ValueError, match="unknown model"):
        build_model("xgboost")


# --------------------------------------------------------------------------- #
# 9) CLI end-to-end                                                           #
# --------------------------------------------------------------------------- #

def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )


def test_cli_quick_har_end_to_end(tmp_path: Path) -> None:
    """`--quick --model har` on the fixture: exit 0, JSON+MD written, JSON
    carries the H-02 reference and the per-fold criteria individually."""
    proc = _run_cli(
        [
            "--csv-path", str(FIXTURE_CSV),
            "--model", "har",
            "--quick",
            "--seed", str(SEED),
            "--out", str(tmp_path),
        ]
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"

    json_path = tmp_path / "c42_results.json"
    md_path = tmp_path / "c42_report.md"
    assert json_path.is_file(), "c42_results.json not written"
    assert md_path.is_file(), "c42_report.md not written"

    result = json.loads(json_path.read_text(encoding="utf-8"))
    # H-02 reference
    assert result["hypothesis"] == "H-02"
    assert "hypothesis_registry" in result
    assert result["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert result["gate_oos_r2_min"] == 0.15
    # quick mode -> 2 disjoint OOS folds, per-fold criteria reported INDIVIDUALLY
    assert result["n_folds"] == 2
    assert len(result["folds"]) == 2
    for fr in result["folds"]:
        for key in (
            "fold_id", "n_train", "n_test",
            "model_r2", "model_qlike", "har_r2", "har_qlike",
            "qlike_beats_har", "r2_passes",
        ):
            assert key in fr, f"per-fold criterion '{key}' missing in JSON"
        assert isinstance(fr["qlike_beats_har"], bool)
        assert isinstance(fr["r2_passes"], bool)
    # seed + provenance recorded for reproducibility
    assert result["seed"] == SEED
    assert result["feature_provenance"] == {"DOCUMENTED": 1, "ASSUMED": 35}
    assert len(result["features"]) == 36

    md = md_path.read_text(encoding="utf-8")
    assert "H-02" in md
    assert "QLIKE" in md
    # one metrics row per fold in the report table
    assert md.count("| 0 |") >= 1 and md.count("| 1 |") >= 1

    # summary line on stdout names hypothesis + verdict
    assert "H-02" in proc.stdout
    assert "C42-REPRO" in proc.stdout


def test_cli_defective_csv_exits_1_without_traceback(tmp_path: Path) -> None:
    """A CSV missing mandatory columns -> exit code 1, clean German error
    message on stderr, NO Python traceback."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("ts,close\n1,2\n", encoding="utf-8")
    proc = _run_cli(
        ["--csv-path", str(bad_csv), "--model", "har", "--out", str(tmp_path)]
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert "DATENDEFEKT" in proc.stderr
    assert not (tmp_path / "c42_results.json").exists()


def test_cli_missing_input_exits_1(tmp_path: Path) -> None:
    """Neither --csv-path nor --db-path -> exit 1 (clean), not a crash."""
    proc = _run_cli(["--model", "har", "--out", str(tmp_path)])
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr


# --------------------------------------------------------------------------- #
# 10) DuckDB lock robustness: open timeout + --db-copy                        #
#     (T2 defect 2026-06-12: 900 s hang at "opening duckdb read-only" while   #
#     the 1.0 collector held the RW lock)                                     #
# --------------------------------------------------------------------------- #

def test_open_db_with_timeout_hung_opener_raises_clierror() -> None:
    """A blocking DuckDB open must become a CLIError with the --db-copy hint
    after the hard timeout — never an unbounded hang."""
    import threading
    import time as _time

    import scripts.c42_repro as c42_cli

    started = threading.Event()

    def hung_opener():
        started.set()
        _time.sleep(30)  # daemon thread; abandoned after the timeout

    with pytest.raises(c42_cli.CLIError, match="--db-copy"):
        c42_cli._open_db_with_timeout(hung_opener, timeout_s=0.2)
    assert started.wait(1.0)


def test_open_db_with_timeout_maps_lock_error_to_clierror() -> None:
    """A DuckDB lock error surfaces as CLIError carrying the --db-copy hint."""
    import scripts.c42_repro as c42_cli

    def lock_opener():
        raise RuntimeError(
            'IO Error: Could not set lock on file "bybit_edge.duckdb": '
            "Conflicting lock is held"
        )

    with pytest.raises(c42_cli.CLIError, match="--db-copy"):
        c42_cli._open_db_with_timeout(lock_opener, timeout_s=5.0)


def test_open_db_with_timeout_passes_through_unrelated_errors() -> None:
    """Non-lock errors keep their type (no blanket CLIError masking)."""
    import scripts.c42_repro as c42_cli

    def boom():
        raise ValueError("unrelated failure")

    with pytest.raises(ValueError, match="unrelated failure"):
        c42_cli._open_db_with_timeout(boom, timeout_s=5.0)


def test_db_copy_reads_temp_copy_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, garch_klines: pd.DataFrame
) -> None:
    """--db-copy: loads klines from a temp copy of the .duckdb file and deletes
    the copy afterwards; the original stays untouched."""
    import tempfile

    import duckdb

    import scripts.c42_repro as c42_cli

    db_path = tmp_path / "bybit_edge.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(
        "CREATE TABLE kline_1min (ts BIGINT NOT NULL, symbol VARCHAR NOT NULL, "
        "open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, "
        "volume DOUBLE, turnover DOUBLE)"
    )
    df = garch_klines.head(2000)
    conn.execute(
        "INSERT INTO kline_1min "
        "SELECT ts, 'BTCUSDT', open, high, low, close, volume, turnover FROM df"
    )
    conn.close()
    original_bytes = db_path.read_bytes()

    made_dirs: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def tracking_mkdtemp(*args, **kwargs):
        d = real_mkdtemp(*args, **kwargs)
        made_dirs.append(d)
        return d

    monkeypatch.setattr(tempfile, "mkdtemp", tracking_mkdtemp)

    klines = c42_cli._load_from_db(db_path, "BTCUSDT", max_bars=500, db_copy=True)

    assert len(klines) == 500
    assert list(klines.columns) == KLINE_COLUMNS
    assert made_dirs, "no temp copy directory was created"
    assert not Path(made_dirs[0]).exists(), "temp copy not cleaned up"
    assert db_path.read_bytes() == original_bytes  # original untouched
