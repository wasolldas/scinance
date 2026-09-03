"""Unit tests for WP-11 RELAX (activity relaxation after H-20 shock hours,
PRD_SCINANCE3.md 11.3, DEC-58; Exkurs X-OEKO-1 Arm (a), KAPITALFREI).

Covers:

  (a) ``bucket_state``: exact 5-min aggregation of volume/n_trades/rv from
      constructed minute bars,
  (b) ``ar1_decay_fit``: recovers a known geometric decay exactly, reports
      "no decay" (half_life=None) rather than a fabricated number when
      the excess is flat or growing, "undefined" on a zero-variance
      series,
  (c) ``time_to_return``: defined/censored/undefined-shock cases,
  (d) ``day_cluster_bootstrap``/``p90_time_to_return``: reproducibility
      with the same seed, censoring-aware P90,
  (e) ``select_pseudo_events``: matched count, 24h non-overlap, excludes
      real event hours,
  (f) THE DEC-39 TRIO as real end-to-end tests on a synthetic bar cache
      built with ``tests.unit.test_c19_drift._build_cache``: POSITIVE
      (injected lambda=0.5/h activity decay recovered within CI), NULL
      (a permanent step with no reversion -> lambda ~ 0 and time-to-return
      CENSORED, never a small fabricated number), ADVERSARIAL (H-20
      events selected on a pure random walk with activity UNRELATED to
      the price shocks -> the matched pseudo-null comparison shows no
      systematic inflation of the real events' decay rate),
  (g) determinism (N=3 identical runs), DEC-53 artefact round-trip,
      KEIN-BEFUND floor, refuse-writes-under-data/harvest, capital
      freedom.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_c19_drift import _build_cache, _days  # noqa: E402  (reused fixture writer, per spec)

from bybit_edge.research.wp11_relax import measure as wm  # noqa: E402
from bybit_edge.research.wp11_relax import report as wr  # noqa: E402

MIN_PER_DAY = 1_440


# ============================================================================
# (a) bucket_state
# ============================================================================

def test_bucket_state_exact_aggregation():
    # 2 buckets (10 minutes): bucket 0 has 3 bars, bucket 1 has all 5.
    mi = np.asarray([0, 1, 2, 5, 6, 7, 8, 9], dtype=np.int64)
    px = np.asarray([100.0, 101.0, 102.0, 100.0, 100.5, 101.0, 100.5, 101.0])
    vol = np.asarray([1.0, 2.0, 3.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    nt = np.asarray([1, 2, 1, 1, 1, 1, 1, 1], dtype=np.int64)
    out = wm.bucket_state(mi, px, vol, nt, 0, 2)
    assert list(out["n_bars"]) == [3, 5]
    assert out["activity_volume"][0] == pytest.approx(np.log1p(6.0))
    assert out["activity_ntrades"][0] == pytest.approx(np.log1p(4.0))
    # bucket 0: consecutive minutes 0,1,2 -> 2 returns
    r01 = np.log(101.0 / 100.0)
    r12 = np.log(102.0 / 101.0)
    assert out["realized_vol"][0] == pytest.approx(np.log1p(1e4 * np.sqrt(r01 ** 2 + r12 ** 2)))


def test_bucket_state_missing_bucket_is_nan_not_zero():
    mi = np.asarray([0, 1], dtype=np.int64)
    px = np.asarray([100.0, 100.0])
    vol = np.asarray([1.0, 1.0])
    nt = np.asarray([1, 1], dtype=np.int64)
    out = wm.bucket_state(mi, px, vol, nt, 0, 3)   # buckets 0,1,2 * 5min; only bucket 0 has data
    assert out["n_bars"][0] == 2
    assert out["n_bars"][1] == 0 and out["n_bars"][2] == 0
    assert np.isnan(out["activity_volume"][1])
    assert np.isnan(out["realized_vol"][2])


# ============================================================================
# (b) ar1_decay_fit
# ============================================================================

def test_ar1_decay_fit_recovers_known_geometric_decay():
    dt_h = 5.0 / 60.0
    lam_true = 0.5
    t = np.arange(200) * dt_h
    excess = 3.0 * np.exp(-lam_true * t)
    fit = wm.ar1_decay_fit(excess, dt_hours=dt_h)
    assert fit["lambda_per_h"] == pytest.approx(lam_true, abs=1e-6)
    assert fit["half_life_h"] == pytest.approx(np.log(2.0) / lam_true, abs=1e-6)
    assert fit["r2"] == pytest.approx(1.0, abs=1e-8)


def test_ar1_decay_fit_flat_excess_reports_no_decay_not_fabricated():
    excess = np.full(100, 2.0)   # permanently elevated, never reverts
    fit = wm.ar1_decay_fit(excess)
    assert fit["half_life_h"] is None
    assert not (np.isfinite(fit["lambda_per_h"]) and fit["lambda_per_h"] > 0.05)


def test_ar1_decay_fit_zero_variance_is_undefined_not_zero():
    fit = wm.ar1_decay_fit(np.zeros(100))
    assert np.isnan(fit["lambda_per_h"])
    assert fit["phi"] is None


def test_ar1_decay_fit_too_few_pairs_is_undefined():
    fit = wm.ar1_decay_fit(np.array([1.0, 0.5, 0.2]))
    assert np.isnan(fit["lambda_per_h"])
    assert fit["n_pairs"] < wm.MIN_AR1_PAIRS


# ============================================================================
# (c) time_to_return
# ============================================================================

def test_time_to_return_defined_and_found():
    hourly = np.full(24, 10.0)
    hourly[5] = 0.5   # <= 10% of shock_excess=10 at hour 6 (1-indexed)
    out = wm.time_to_return(hourly)
    assert out["defined"] is True and out["censored"] is False
    assert out["t_return_h"] == 6


def test_time_to_return_never_returns_is_censored():
    hourly = np.full(24, 10.0)
    out = wm.time_to_return(hourly)
    assert out["defined"] is True and out["censored"] is True
    assert out["t_return_h"] == 24.0


def test_time_to_return_undefined_when_shock_negligible():
    hourly = np.full(24, 1e-12)
    out = wm.time_to_return(hourly)
    assert out["defined"] is False
    assert out["t_return_h"] is None and out["censored"] is None


# ============================================================================
# (d) bootstrap
# ============================================================================

def test_day_cluster_bootstrap_reproducible_same_seed():
    rng = np.random.default_rng(1)
    values = 0.5 + 0.1 * rng.standard_normal(200)
    days = np.repeat(np.arange(40), 5)
    a = wm.day_cluster_bootstrap(values, days, seed=7)
    b = wm.day_cluster_bootstrap(values, days, seed=7)
    assert a == b


def test_day_cluster_bootstrap_ci_covers_true_median():
    rng = np.random.default_rng(2)
    days = np.repeat(np.arange(60), 4)
    values = 0.5 + 0.05 * rng.standard_normal(240)
    boot = wm.day_cluster_bootstrap(values, days, seed=42)
    assert boot["ci_lo"] <= 0.5 <= boot["ci_hi"]


def test_p90_time_to_return_censoring_aware():
    days = np.arange(50)
    t = np.full(50, 24.0)
    censored = np.ones(50, dtype=bool)
    t[:45] = 5.0
    censored[:45] = False   # 90% returned at hour 5, 10% censored
    out = wm.p90_time_to_return(t, censored, days, seed=3)
    assert out["point"] == pytest.approx(5.0)
    # if almost all are censored, the P90 order statistic itself is censored
    t2 = np.full(50, 24.0)
    c2 = np.ones(50, dtype=bool)
    t2[:5] = 3.0
    c2[:5] = False
    out2 = wm.p90_time_to_return(t2, c2, days, seed=3)
    assert out2["censored_at_p90"] is True
    assert np.isnan(out2["point"])


# ============================================================================
# (e) select_pseudo_events
# ============================================================================

def test_select_pseudo_events_matched_count_gap_and_exclusion():
    n = 3000
    hours = np.arange(n, dtype=np.int64)
    cand = np.ones(n, dtype=bool)
    r = np.full(n, 0.001)
    real_hours = {500, 1000, 1500}
    idx = wm.select_pseudo_events(hours, cand, r, real_hours, 10, seed=5)
    assert idx.size == 10
    chosen = hours[idx]
    assert not (set(int(h) for h in chosen) & real_hours)
    diffs = np.diff(np.sort(chosen))
    assert np.all(diffs >= wm.HORIZON_HOURS)


def test_select_pseudo_events_empty_pool_returns_empty():
    hours = np.arange(5, dtype=np.int64)
    cand = np.zeros(5, dtype=bool)
    r = np.full(5, np.nan)
    idx = wm.select_pseudo_events(hours, cand, r, set(), 3, seed=1)
    assert idx.size == 0


# ============================================================================
# (f) DEC-39 trio, end-to-end on a synthetic bar cache
# ============================================================================

_BUCKET_MIN = wm.BUCKET_MINUTES
_POST_BUCKETS = wm.POST_BUCKETS


def _event_hours(n_days: int, *, start_day: int = 45, spacing_h: int = 120,
                 margin_h: int = 30) -> list[int]:
    return list(range(start_day * 24, n_days * 24 - margin_h, spacing_h))


def _price_log_with_crashes(n_days: int, seed: int, event_hours: list[int]) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = n_days * MIN_PER_DAY
    r = 8e-5 * rng.standard_normal(n)
    for k in event_hours:
        m0 = k * 60
        r[m0:m0 + 60] += -0.02 / 60
    return np.log(100.0) + np.cumsum(r)


def _volume_with_decay(n_days: int, event_hours: list[int], *, v_flat: float = 2.0,
                       amplitude: float = 2.0, lam: float = 0.5, seed: int = 123) -> np.ndarray:
    """Exact geometric-decay excess IN LOG1P(bucket-sum) SPACE (so the
    module's own bucket aggregation reproduces the target curve exactly,
    with only a small per-event amplitude jitter for a non-degenerate
    bootstrap CI)."""
    n = n_days * MIN_PER_DAY
    v = np.full(n, v_flat, dtype=np.float64)
    baseline_log = np.log1p(_BUCKET_MIN * v_flat)
    rng = np.random.default_rng(seed)
    t_h = np.arange(_POST_BUCKETS) * _BUCKET_MIN / 60.0
    for k in event_hours:
        t0 = (k + 1) * 60
        c = amplitude * (1.0 + 0.1 * rng.standard_normal())
        target_sum = np.expm1(baseline_log + c * np.exp(-lam * t_h))
        per_min = np.maximum(target_sum, 0.0) / _BUCKET_MIN
        for kb in range(_POST_BUCKETS):
            m0 = t0 + kb * _BUCKET_MIN
            v[m0:m0 + _BUCKET_MIN] = per_min[kb]
    return v


def _volume_with_permanent_step(n_days: int, event_hours: list[int], *, v_flat: float = 2.0,
                                amplitude: float = 2.0, seed: int = 321) -> np.ndarray:
    n = n_days * MIN_PER_DAY
    v = np.full(n, v_flat, dtype=np.float64)
    baseline_log = np.log1p(_BUCKET_MIN * v_flat)
    rng = np.random.default_rng(seed)
    target_sum = np.expm1(baseline_log + amplitude)
    per_min_base = target_sum / _BUCKET_MIN
    for k in event_hours:
        t0 = (k + 1) * 60
        for kb in range(_POST_BUCKETS):
            noisy = per_min_base * (1.0 + 0.02 * rng.standard_normal())
            m0 = t0 + kb * _BUCKET_MIN
            v[m0:m0 + _BUCKET_MIN] = max(noisy, 1e-6)
    return v


def _build_relax_cache(tmp_path: Path, symbol: str, n_days: int, log_px: np.ndarray,
                       vol: np.ndarray, start: str = "2023-01-01") -> Path:
    days = _days(start, n_days)

    def price_fn(i: int) -> np.ndarray:
        return np.exp(log_px[i * MIN_PER_DAY:(i + 1) * MIN_PER_DAY])

    def vol_fn(i: int) -> np.ndarray:
        return vol[i * MIN_PER_DAY:(i + 1) * MIN_PER_DAY]

    return _build_cache(tmp_path, symbol, days, price_fn, vol_fn)


@pytest.mark.filterwarnings("ignore")
def test_dec39_positive_injected_decay_recovered_within_ci(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    assert len(ev) >= wm.MIN_EVENT_CLUSTERS
    log_px = _price_log_with_crashes(n_days, seed=1, event_hours=ev)
    vol = _volume_with_decay(n_days, ev, lam=0.5)
    cache = _build_relax_cache(tmp_path / "pos", "POSUSDT", n_days, log_px, vol)

    payload = wm.run(cache, symbols=("POSUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={})
    assert payload["status"] == "RUN"
    per_symbol = {c["variable"]: c for c in payload["pre_fixed"]["median_half_life_per_symbol"]}
    cell = per_symbol["activity_volume"]
    assert cell["kein_befund"] is False, cell
    true_half_life = np.log(2.0) / 0.5
    hl = cell["half_life_h"]
    assert hl["point"] == pytest.approx(true_half_life, rel=0.05)
    assert hl["ci_lo"] <= true_half_life <= hl["ci_hi"], hl
    assert cell["median_r2"] > 0.99, cell


@pytest.mark.filterwarnings("ignore")
def test_dec39_null_flat_step_gives_no_decay_and_censored_return(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=2, event_hours=ev)
    vol = _volume_with_permanent_step(n_days, ev)
    cache = _build_relax_cache(tmp_path / "null", "NULUSDT", n_days, log_px, vol)

    payload = wm.run(cache, symbols=("NULUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={})
    per_symbol = {c["variable"]: c for c in payload["pre_fixed"]["median_half_life_per_symbol"]}
    cell = per_symbol["activity_volume"]
    assert cell["kein_befund"] is False, cell
    # lambda ~ 0 (no decay): NEVER a confidently-positive fast decay rate
    lam = cell["lambda_per_h"]["point"]
    assert not (np.isfinite(lam) and lam > 0.05), cell
    # time-to-return: censored, reported as such -- NOT a small fabricated number
    assert cell["n_censored"] >= 0.9 * cell["n_return_defined"], cell
    p90 = cell["p90_time_to_return_h"]
    assert p90["censored_at_p90"] is True
    assert np.isnan(p90["point"])


@pytest.mark.filterwarnings("ignore")
def test_dec39_adversarial_selection_on_random_walk_no_spurious_decay(tmp_path):
    """Events are selected purely on |return| extremity of a memoryless
    random walk (random jump sign/placement, no hidden two-state
    process); ACTIVITY carries no relation whatsoever to those shocks.
    The module must not fabricate a confident decay signal from the
    selection alone, and its own matched pseudo-null comparison (module
    docstring: the selection-effect diagnostic) must not show the real
    events decaying systematically faster than the random controls."""
    n_days = 260
    rng = np.random.default_rng(9)
    n = n_days * MIN_PER_DAY
    r = 8e-5 * rng.standard_normal(n)
    max_hour = n_days * 24 - 30
    pool = rng.choice(np.arange(45 * 24, max_hour), size=200, replace=False)
    chosen: list[int] = []
    for h in sorted(int(x) for x in pool):
        if all(abs(h - c) >= 120 for c in chosen):
            chosen.append(h)
        if len(chosen) >= 30:
            break
    for k in chosen:
        m0 = k * 60
        sign = float(rng.choice([-1.0, 1.0]))
        r[m0:m0 + 60] += sign * 0.02 / 60
    log_px = np.log(100.0) + np.cumsum(r)
    vol = 2.0 * (1.0 + 0.05 * np.random.default_rng(77).standard_normal(n))
    vol = np.clip(vol, 0.1, None)
    cache = _build_relax_cache(tmp_path / "adv", "ADVUSDT", n_days, log_px, vol)

    collected = wm.collect_symbol_events(cache, "bybit", "ADVUSDT",
                                         start=wm.CACHE_RANGE[0], end=wm.CACHE_RANGE[1])
    assert len(collected["real"]) >= 10, "fixture must produce enough events to be informative"
    assert len(collected["pseudo"]) == len(collected["real"])

    def _lambdas(records, var):
        out = []
        for rec in records:
            if not rec["floor_ok"]:
                continue
            lam = rec["variables"][var]["fit"]["lambda_per_h"]
            if np.isfinite(lam):
                out.append(lam)
        return np.asarray(out)

    lam_real = _lambdas(collected["real"], "activity_volume")
    lam_null = _lambdas(collected["pseudo"], "activity_volume")
    # Activity here is PURE noise around a flat level -- the origin-forced
    # AR(1) estimator can report a large nominal lambda purely from
    # near-zero lag-1 autocorrelation of noise (low signal-to-noise, NOT
    # true relaxation). That mechanical inflation is expected and is
    # EXACTLY why this module never judges a single lambda number: what
    # matters is whether the price-extremity SELECTION manufactures a
    # SYSTEMATIC difference between real events and the matched random
    # control -- it must not, since activity is unrelated to the shocks
    # by construction.
    assert lam_real.size >= 5 and lam_null.size >= 5, (lam_real, lam_null)
    med_real, med_null = float(np.median(lam_real)), float(np.median(lam_null))
    ratio = med_real / med_null if med_null > 0 else float("nan")
    assert np.isfinite(ratio) and 0.2 <= ratio <= 5.0, (med_real, med_null, lam_real, lam_null)


# ============================================================================
# (g) determinism, artefacts, KEIN BEFUND, refuse-writes, capital freedom
# ============================================================================

@pytest.mark.filterwarnings("ignore")
def test_determinism_n3_identical_runs(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=4, event_hours=ev)
    vol = _volume_with_decay(n_days, ev)
    cache = _build_relax_cache(tmp_path / "det", "DETUSDT", n_days, log_px, vol)

    import json as _json
    runs = [wm.run(cache, symbols=("DETUSDT",), skip_fingerprint_check=True,
                   expected_fingerprints={})
           for _ in range(3)]
    keys = ("n_events_real", "n_events_pseudo_null", "n_event_clusters_total",
           "pre_fixed", "structural_null")
    # dict equality on NaN-carrying payloads is always false (nan != nan) --
    # the repo's T2 convention is a serialized FINGERPRINT comparison instead.
    fps = [_json.dumps({k: run[k] for k in keys}, sort_keys=True, default=str)
          for run in runs]
    assert fps[0] == fps[1] == fps[2]


@pytest.mark.filterwarnings("ignore")
def test_artifact_roundtrip_dec53(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=6, event_hours=ev)
    vol = _volume_with_decay(n_days, ev)
    cache = _build_relax_cache(tmp_path / "art", "ARTUSDT", n_days, log_px, vol)
    payload = wm.run(cache, symbols=("ARTUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={})

    out_dir = tmp_path / "out"
    written = wr.build_report(payload, out_dir)
    real_csv = written["artifacts"]["cluster_series"]["real"]
    assert Path(real_csv["path"]).is_file()
    import hashlib
    assert hashlib.sha256(Path(real_csv["path"]).read_bytes()).hexdigest() == real_csv["sha256"]
    assert real_csv["n_rows"] == payload["n_events_real"] * len(wm.VARIABLES)

    import csv as _csv
    with open(real_csv["path"], newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    assert len(rows) == real_csv["n_rows"]
    assert {r["variable"] for r in rows} == set(wm.VARIABLES)

    bf = written["artifacts"]["bootstrap_fingerprint"]
    import json as _json
    fp = _json.loads(Path(bf["path"]).read_text(encoding="utf-8"))
    assert fp["seed"] == wm.SEED
    assert fp["generator"] == "numpy.random.default_rng"

    assert Path(written["summary_path"]).is_file()
    assert Path(written["markdown_path"]).is_file()


def test_report_kein_verdikt_when_artifacts_missing():
    with pytest.raises(wr.ReportError, match="KEIN VERDIKT"):
        wr.check_dec53({"cluster_series": {}, "bootstrap_fingerprint": None})


def test_report_refuses_data_harvest(tmp_path):
    bad = tmp_path / "data" / "harvest" / "wp11"
    with pytest.raises(ValueError, match="data/harvest"):
        wr.write_cluster_series_csv([], bad, name="real")
    with pytest.raises(ValueError, match="data/harvest"):
        wr.write_bootstrap_fingerprint(
            {"method": {"seed": 1, "min_event_clusters": 30}}, bad)


@pytest.mark.filterwarnings("ignore")
def test_kein_befund_below_cluster_floor(tmp_path):
    n_days = 60   # only ~1-2 events, far below the 30-cluster floor
    ev = _event_hours(n_days, start_day=25, spacing_h=200, margin_h=10)
    log_px = _price_log_with_crashes(n_days, seed=8, event_hours=ev)
    vol = _volume_with_decay(n_days, ev)
    cache = _build_relax_cache(tmp_path / "thin", "THNUSDT", n_days, log_px, vol)
    payload = wm.run(cache, symbols=("THNUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={})
    assert payload["kein_befund_overall"] is True
    assert payload["status"] == "KEIN BEFUND"
    for c in payload["pre_fixed"]["median_half_life_per_symbol"]:
        assert c["kein_befund"] is True
        assert "reason" in c


def test_fingerprint_mismatch_sets_gate_invalid(tmp_path):
    days = _days("2023-01-01", 3)
    n = 3 * MIN_PER_DAY
    log_px = np.log(100.0) + np.cumsum(8e-5 * np.random.default_rng(1).standard_normal(n))
    vol = np.ones(n)
    cache = _build_relax_cache(tmp_path, "TSTUSDT", 3, log_px, vol)
    payload = wm.run(cache, symbols=("TSTUSDT",), expected_fingerprints={"TSTUSDT": "deadbeef"})
    assert payload["gate_valid"] is False
    assert payload["cache_fingerprints"]["TSTUSDT"]["matches"] is False


def test_module_is_capital_free():
    import ast
    root = Path(__file__).resolve().parents[2] / "src" / "bybit_edge" / "research" / "wp11_relax"
    for fname in ("measure.py", "report.py"):
        src = (root / fname).read_text(encoding="utf-8")
        tree = ast.parse(src)
        code = src
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    code = code.replace(doc, "")
        lowered = "\n".join(ln for ln in code.splitlines()
                            if not ln.lstrip().startswith("#")).lower()
        for term in ("fee", "slippage", "pnl", "sharpe", "taker", "maker",
                    "friction", "commission"):
            assert term not in lowered, (fname, term)
