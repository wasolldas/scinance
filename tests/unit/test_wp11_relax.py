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

v2 (Orchestrator Nacharbeit 2026-09-08 -- the per-event AR(1) estimator
above was found uninformative on the real 3.570-event run; kept as a
diagnostic, unchanged, per (a)-(g) above). Additionally covers:

  (h) superposed-epoch profile machinery in isolation on fast synthetic
      records (no bar cache): ``build_profile_matrix`` (floor_ok
      filtering), ``_cluster_bootstrap_profile_reps`` (reproducibility,
      degenerate single-cluster case), ``loglinear_decay_fit``
      (exponential AND power-law recover known parameters; insufficient
      points -> undefined, never fabricated), ``mean_profile_return_time``
      (found vs. censored), ``remaining_fraction_at`` (known fractions at
      1h/6h/24h), ``profile_replicate_recovery_p90`` (censoring-aware,
      including "the P90 order statistic itself is censored"),
      ``_filter_records``/``_annotate_records``/``strip_profile_arrays``,
      and ``profile_group_summary`` end-to-end on synthetic records
      (known decay recovered; KEIN BEFUND below the cluster floor),
  (i) the v2 DEC-39 trio as real end-to-end tests on a synthetic bar
      cache: POSITIVE (injected lambda=0.5/h excess with SUBSTANTIAL
      PER-EVENT NOISE -- the per-event AR(1) is not required to recover
      it, only the group PROFILE fit is), NULL (activity with no shock-
      conditioned change at all -> no fabricated half-life, the
      difference profile's own CI covers zero quickly), ADVERSARIAL
      (price-extremity selection on a near-random-walk with a REALISTIC,
      BOUNDED "selection bump" leaked into only the FIRST post-shock
      bucket of realized-vol -- the fit must not extend that bump into a
      multi-hour fabricated decay),
  (j) determinism and DEC-53 artefact round-trip (``wp11_profile_matrix.csv``)
      extended to the v2 profile outputs.
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
                     expected_fingerprints={}, profile_n_bootstrap=150)
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
                     expected_fingerprints={}, profile_n_bootstrap=150)
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
                   expected_fingerprints={}, profile_n_bootstrap=150)
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
                     expected_fingerprints={}, profile_n_bootstrap=150)

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
                     expected_fingerprints={}, profile_n_bootstrap=150)
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


# ============================================================================
# v2 -- (h) superposed-epoch profile machinery on FAST synthetic records
# (no bar cache -- exercises measure.py's v2 functions directly).
# ============================================================================

def _fake_event_record(event_hour: int, day: int, excess_by_var: dict[str, np.ndarray],
                       *, floor_ok: bool = True) -> dict:
    variables = {}
    for var in wm.VARIABLES:
        arr = excess_by_var.get(var, np.full(wm.POST_BUCKETS, np.nan))
        variables[var] = {
            "baseline": 0.0, "fit": wm.ar1_decay_fit(np.empty(0)),
            "return": {"defined": False, "shock_excess": float("nan"),
                      "t_return_h": None, "censored": None},
            "excess": arr,
        }
    return {"symbol": "TSTUSDT", "event_hour": event_hour, "event_day": day,
           "n_pre_present": 999, "n_post_present": 999, "floor_ok": floor_ok,
           "variables": variables}


def test_loglinear_decay_fit_exponential_recovers_known_params():
    t = np.arange(wm.POST_BUCKETS) * wm.BUCKET_MINUTES / 60.0
    a_true, lam_true = 3.0, 0.4
    y_point = a_true * np.exp(-lam_true * t)
    rng = np.random.default_rng(1)
    y_reps = y_point[None, :] * (1.0 + 0.02 * rng.standard_normal((80, t.size)))
    fit = wm.loglinear_decay_fit(t, y_point, y_reps, kind="exponential")
    assert fit["param"] == pytest.approx(lam_true, rel=0.02)
    assert fit["r2"] > 0.999
    lo, hi = fit["param_ci"]
    assert lo <= lam_true <= hi


def test_loglinear_decay_fit_power_law_recovers_known_exponent():
    t = np.arange(wm.POST_BUCKETS) * wm.BUCKET_MINUTES / 60.0
    a_true, p_true = 2.0, 0.8
    t0 = (wm.BUCKET_MINUTES / 60.0) / 2.0
    y_point = a_true * (t + t0) ** (-p_true)
    rng = np.random.default_rng(2)
    y_reps = y_point[None, :] * (1.0 + 0.02 * rng.standard_normal((80, t.size)))
    fit = wm.loglinear_decay_fit(t, y_point, y_reps, kind="power")
    assert fit["param"] == pytest.approx(p_true, rel=0.02)
    lo, hi = fit["param_ci"]
    assert lo <= p_true <= hi


def test_loglinear_decay_fit_insufficient_points_is_undefined_not_fabricated():
    t = np.arange(wm.POST_BUCKETS) * wm.BUCKET_MINUTES / 60.0
    y_point = np.full(t.size, -1.0)   # never clears eps -> no usable points
    y_reps = np.tile(y_point, (10, 1))
    fit = wm.loglinear_decay_fit(t, y_point, y_reps, kind="exponential")
    assert np.isnan(fit["param"])
    assert fit["n_points"] < 20


def test_mean_profile_return_time_found_and_censored():
    n = wm.POST_BUCKETS
    diff = np.full(n, 5.0)
    lo, hi = np.full(n, 4.0), np.full(n, 6.0)   # CI never covers 0
    out = wm.mean_profile_return_time(diff, lo, hi)
    assert out["censored"] is True

    h3 = 3 * wm.BUCKETS_PER_HOUR
    lo2 = lo.copy()
    lo2[h3:] = -1.0                              # from hour 4 on, CI covers 0
    out2 = wm.mean_profile_return_time(diff, lo2, hi)
    assert out2["censored"] is False
    assert out2["t_return_h"] == 4


def test_remaining_fraction_at_known_values():
    n = wm.POST_BUCKETS
    diff = np.zeros(n)
    diff[0] = 4.0
    diff[wm.BUCKETS_PER_HOUR - 1] = 2.0
    diff[6 * wm.BUCKETS_PER_HOUR - 1] = 1.0
    diff[n - 1] = 0.4
    reps = np.tile(diff, (20, 1))
    out = wm.remaining_fraction_at(diff, reps)
    assert out["h1"]["point"] == pytest.approx(0.5)
    assert out["h6"]["point"] == pytest.approx(0.25)
    assert out["h24"]["point"] == pytest.approx(0.1)
    assert out["h1"]["ci_lo"] == pytest.approx(0.5) and out["h1"]["ci_hi"] == pytest.approx(0.5)


def test_profile_replicate_recovery_p90_quick_return_with_some_censoring():
    n = wm.POST_BUCKETS
    reps = np.zeros((20, n))
    for i in range(20):
        reps[i, 0] = 10.0
        if i < 18:
            reps[i, wm.BUCKETS_PER_HOUR:] = 0.0   # returns within hour 1
        else:
            reps[i, :] = 10.0                     # never returns
    out = wm.profile_replicate_recovery_p90(reps)
    assert out["n_defined_reps"] == 20
    assert out["n_censored_reps"] == 2
    # hour 0 IS the shock-excess reference itself (100% by definition), so
    # the earliest a return can register is hour 2 (hourly-averaged buckets)
    assert out["point"] == pytest.approx(2.0)
    assert out["censored_at_p90"] is False


def test_profile_replicate_recovery_p90_censored_at_p90():
    n = wm.POST_BUCKETS
    reps = np.zeros((20, n))
    for i in range(20):
        reps[i, 0] = 10.0
        if i < 10:
            reps[i, wm.BUCKETS_PER_HOUR:] = 0.0
        else:
            reps[i, :] = 10.0
    out = wm.profile_replicate_recovery_p90(reps)
    assert out["censored_at_p90"] is True
    assert np.isnan(out["point"])


def test_build_profile_matrix_stacks_and_filters_floor_ok():
    a = _fake_event_record(0, 0, {"activity_volume": np.full(wm.POST_BUCKETS, 1.0)})
    b = _fake_event_record(24, 1, {"activity_volume": np.full(wm.POST_BUCKETS, 3.0)},
                           floor_ok=False)
    mat, days = wm.build_profile_matrix([a, b], "activity_volume")
    assert mat.shape == (1, wm.POST_BUCKETS)
    assert list(days) == [0]


def test_cluster_bootstrap_profile_reps_reproducible_and_degenerate_single_cluster():
    a = _fake_event_record(0, 5, {"activity_volume": np.full(wm.POST_BUCKETS, 2.0)})
    b = _fake_event_record(24, 5, {"activity_volume": np.full(wm.POST_BUCKETS, 4.0)})
    mat, days = wm.build_profile_matrix([a, b], "activity_volume")
    reps1 = wm._cluster_bootstrap_profile_reps(mat, days, n_bootstrap=50, seed=3)
    reps2 = wm._cluster_bootstrap_profile_reps(mat, days, n_bootstrap=50, seed=3)
    assert np.array_equal(reps1, reps2, equal_nan=True)
    # both events share ONE calendar day -> every bootstrap draw resamples
    # that SAME pair -> the mean is constant across all reps
    assert np.allclose(reps1, 3.0)


def test_filter_records_symbol_era_regime():
    a = {**_fake_event_record(0, 0, {}), "era": "OOS1", "stress_abs": True}
    b = {**_fake_event_record(24, 1, {}), "era": "OOS2", "stress_abs": False}
    assert wm._filter_records([a, b], era="OOS1") == [a]
    assert wm._filter_records([a, b], regime=True) == [a]
    assert wm._filter_records([a, b], symbol="TSTUSDT") == [a, b]


def test_annotate_records_adds_era_and_stress_abs():
    rec = _fake_event_record(24 * 400, 400, {})
    day_iso = wm._epoch_day_iso(400)
    out = wm._annotate_records([rec], stress_abs_days=frozenset({day_iso}), windows=wm.WINDOWS)
    assert out[0]["stress_abs"] is True
    assert out[0]["event_date"] == day_iso
    assert out[0]["era"] in {w[0] for w in wm.WINDOWS} | {"OTHER"}


def test_strip_profile_arrays_removes_nested_arrays_key_only():
    node = {"a": 1, "profile": {"_arrays": {"x": np.zeros(3)}, "kein_befund": False},
           "list": [{"_arrays": {"y": 1}, "b": 2}]}
    out = wm.strip_profile_arrays(node)
    assert "_arrays" not in out["profile"]
    assert out["profile"]["kein_befund"] is False
    assert "_arrays" not in out["list"][0] and out["list"][0]["b"] == 2


def test_profile_group_summary_recovers_known_decay_on_synthetic_records():
    n_events = 40
    lam_true = 0.6
    t = np.arange(wm.POST_BUCKETS) * wm.BUCKET_MINUTES / 60.0
    rng = np.random.default_rng(11)
    real_records = []
    for i in range(n_events):
        base = 3.0 * np.exp(-lam_true * t)
        noisy = base * (1.0 + 0.1 * rng.standard_normal(t.size))
        real_records.append(_fake_event_record(i * 100, i, {"activity_volume": noisy}))
    pseudo_records = []
    for i in range(n_events):
        noise = 0.05 * rng.standard_normal(t.size)
        pseudo_records.append(_fake_event_record(i * 100 + 50, i + 1000,
                                                  {"activity_volume": noise}))
    out = wm.profile_group_summary(real_records, pseudo_records, "activity_volume",
                                   min_clusters=30, seed=5, n_bootstrap=200)
    assert out["kein_befund"] is False
    exp = out["exponential_fit"]
    assert exp["lambda_per_h"] == pytest.approx(lam_true, rel=0.2)
    lo, hi = exp["lambda_ci90"]
    assert lo <= lam_true <= hi
    assert exp["half_life_h"] == pytest.approx(np.log(2.0) / lam_true, rel=0.2)
    assert "_arrays" in out


def test_profile_group_summary_kein_befund_below_cluster_floor():
    real_records = [_fake_event_record(0, 0, {"activity_volume": np.ones(wm.POST_BUCKETS)})]
    out = wm.profile_group_summary(real_records, [], "activity_volume", min_clusters=30, seed=1)
    assert out["kein_befund"] is True
    assert "reason" in out
    assert "_arrays" not in out


# ============================================================================
# v2 -- (i) the v2 DEC-39 trio, end-to-end on a synthetic bar cache
# ============================================================================

def _volume_with_decay_noisy(n_days: int, event_hours: list[int], *, v_flat: float = 2.0,
                             amplitude: float = 2.0, lam: float = 0.5,
                             noise_frac: float = 0.35, seed: int = 222) -> np.ndarray:
    """Same exact-construction exponential excess as ``_volume_with_decay``,
    but with SUBSTANTIAL per-bucket multiplicative noise -- realistic
    enough that the PER-EVENT AR(1) fit is expected to be noisy/off, while
    superposing ~40+ such noisy events should still recover the true
    lambda cleanly (v2's whole point)."""
    n = n_days * MIN_PER_DAY
    v = np.full(n, v_flat, dtype=np.float64)
    baseline_log = np.log1p(_BUCKET_MIN * v_flat)
    rng = np.random.default_rng(seed)
    t_h = np.arange(_POST_BUCKETS) * _BUCKET_MIN / 60.0
    target_sum = np.expm1(baseline_log + amplitude * np.exp(-lam * t_h))
    for k in event_hours:
        t0 = (k + 1) * 60
        noise = 1.0 + noise_frac * rng.standard_normal(_POST_BUCKETS)
        noisy_sum = np.maximum(target_sum * noise, 0.0)
        per_min = noisy_sum / _BUCKET_MIN
        for kb in range(_POST_BUCKETS):
            m0 = t0 + kb * _BUCKET_MIN
            v[m0:m0 + _BUCKET_MIN] = per_min[kb]
    return v


@pytest.mark.filterwarnings("ignore")
def test_v2_dec39_positive_profile_recovers_decay_despite_noisy_per_event_fits(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=21, event_hours=ev)
    vol = _volume_with_decay_noisy(n_days, ev, lam=0.5)
    cache = _build_relax_cache(tmp_path / "v2pos", "V2POSUSDT", n_days, log_px, vol)

    payload = wm.run(cache, symbols=("V2POSUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={}, profile_n_bootstrap=200)
    entry = {c["variable"]: c for c in
            payload["pre_fixed"]["median_half_life_per_symbol"]}["activity_volume"]
    assert entry["kein_befund"] is False
    assert entry["diagnostic_ar1_note"] == wm._AR1_DIAGNOSTIC_NOTE
    prof = entry["profile"]
    assert prof["kein_befund"] is False
    true_half_life = np.log(2.0) / 0.5
    exp = prof["exponential_fit"]
    assert exp["half_life_h"] == pytest.approx(true_half_life, rel=0.15)
    ci_lo, ci_hi = exp["half_life_ci90"]
    assert ci_lo <= true_half_life <= ci_hi, exp
    assert exp["r2"] > 0.9, exp


@pytest.mark.filterwarnings("ignore")
def test_v2_dec39_null_no_shock_conditioned_activity_no_fabricated_half_life(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=22, event_hours=ev)
    # activity carries NO shock-conditioned change whatsoever -- pure
    # stationary noise around the flat baseline, identical regardless of
    # whether an hour is an event hour or not.
    rng = np.random.default_rng(333)
    vol = np.clip(2.0 * (1.0 + 0.1 * rng.standard_normal(n_days * MIN_PER_DAY)), 0.1, None)
    cache = _build_relax_cache(tmp_path / "v2null", "V2NULUSDT", n_days, log_px, vol)

    payload = wm.run(cache, symbols=("V2NULUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={}, profile_n_bootstrap=200)
    entry = {c["variable"]: c for c in
            payload["pre_fixed"]["median_half_life_per_symbol"]}["activity_volume"]
    assert entry["kein_befund"] is False
    prof = entry["profile"]
    assert prof["kein_befund"] is False
    exp = prof["exponential_fit"]
    # no shock excess exists to decay -- NEVER a fabricated half-life
    assert exp["half_life_h"] is None, exp
    # the difference profile's own CI should cover zero essentially
    # immediately (there is no real elevation to return FROM)
    ret = prof["mean_profile_return_time_h"]
    assert ret["t_return_h"] <= 3, ret


@pytest.mark.filterwarnings("ignore")
def test_v2_dec39_adversarial_selection_bump_confined_to_first_bucket(tmp_path):
    """Price-extremity selection on a near-random-walk with a REALISTIC,
    BOUNDED artefact: a little extra return volatility leaks into ONLY
    the first 5-min bucket after each REAL shock hour (a plausible
    boundary/settling effect of the shock itself) -- pseudo (randomly
    placed, not preceded by any shock) events get NO such leak. The
    difference profile must show the bump confined to bucket 0 and the
    exponential/power-law fits must not extend it into a multi-hour
    fabricated decay."""
    n_days = 260
    rng = np.random.default_rng(44)
    n = n_days * MIN_PER_DAY
    r = 8e-5 * rng.standard_normal(n)
    max_hour = n_days * 24 - 30
    pool = rng.choice(np.arange(45 * 24, max_hour), size=160, replace=False)
    chosen: list[int] = []
    for h in sorted(int(x) for x in pool):
        if all(abs(h - c) >= 120 for c in chosen):
            chosen.append(h)
        if len(chosen) >= 32:
            break
    leak_minutes = 5
    for k in chosen:
        m0 = k * 60
        sign = float(rng.choice([-1.0, 1.0]))
        r[m0:m0 + 60] += sign * 0.02 / 60
        t0 = (k + 1) * 60   # end of the shock hour -- first post-shock bucket only
        r[t0:t0 + leak_minutes] += 6e-4 * rng.standard_normal(leak_minutes)
    log_px = np.log(100.0) + np.cumsum(r)
    vol = np.clip(2.0 * (1.0 + 0.05 * np.random.default_rng(55).standard_normal(n)), 0.1, None)
    cache = _build_relax_cache(tmp_path / "v2adv", "V2ADVUSDT", n_days, log_px, vol)

    payload = wm.run(cache, symbols=("V2ADVUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={}, profile_n_bootstrap=200)
    assert payload["n_event_clusters_total"] >= 20, "fixture must produce enough events"
    entry = {c["variable"]: c for c in
            payload["pre_fixed"]["median_half_life_per_symbol"]}["realized_vol"]
    if entry["kein_befund"]:
        pytest.skip("fewer than the 30-cluster floor on this seed -- not informative")
    prof = entry["profile"]
    assert prof["kein_befund"] is False
    diff = prof["_arrays"]["diff"]
    tail_scale = float(np.std(diff[50:]))
    assert abs(diff[0]) > 4.0 * max(tail_scale, 1e-9), (diff[0], tail_scale)
    # nothing beyond the first post-shock HOUR remotely approaches the bump
    assert np.mean(np.abs(diff[wm.BUCKETS_PER_HOUR:])) < 0.3 * abs(diff[0])
    # the fit must not fabricate a broad multi-hour decay from a one-bucket artefact
    exp = prof["exponential_fit"]
    assert exp["n_points"] <= 2 * wm.BUCKETS_PER_HOUR, exp
    if exp["half_life_h"] is not None:
        assert exp["half_life_h"] < 1.0, exp


# ============================================================================
# v2 -- (j) determinism / DEC-53 profile-matrix artefact
# ============================================================================

@pytest.mark.filterwarnings("ignore")
def test_v2_profile_determinism_n3_identical_runs(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=23, event_hours=ev)
    vol = _volume_with_decay(n_days, ev)
    cache = _build_relax_cache(tmp_path / "v2det", "V2DETUSDT", n_days, log_px, vol)

    import json as _json
    runs = [wm.run(cache, symbols=("V2DETUSDT",), skip_fingerprint_check=True,
                   expected_fingerprints={}, profile_n_bootstrap=100)
           for _ in range(3)]
    fps = [_json.dumps(wm.strip_profile_arrays(run["pre_fixed"]), sort_keys=True, default=str)
          for run in runs]
    assert fps[0] == fps[1] == fps[2]


@pytest.mark.filterwarnings("ignore")
def test_v2_profile_matrix_artifact_roundtrip(tmp_path):
    n_days = 260
    ev = _event_hours(n_days)
    log_px = _price_log_with_crashes(n_days, seed=24, event_hours=ev)
    vol = _volume_with_decay(n_days, ev)
    cache = _build_relax_cache(tmp_path / "v2art", "V2ARTUSDT", n_days, log_px, vol)
    payload = wm.run(cache, symbols=("V2ARTUSDT",), skip_fingerprint_check=True,
                     expected_fingerprints={}, profile_n_bootstrap=100)

    out_dir = tmp_path / "out"
    written = wr.build_report(payload, out_dir)
    pm = written["artifacts"]["profile_matrix"]
    assert Path(pm["path"]).is_file()
    import hashlib
    assert hashlib.sha256(Path(pm["path"]).read_bytes()).hexdigest() == pm["sha256"]
    assert pm["n_groups"] > 0
    assert pm["n_rows"] == pm["n_groups"] * wm.POST_BUCKETS

    import csv as _csv
    with open(pm["path"], newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    assert len(rows) == pm["n_rows"]
    groups = {r["group"] for r in rows}
    assert any("variable=activity_volume" in g for g in groups)
    # JSON summary must NOT carry the raw profile arrays (they live in the CSV)
    summary_text = Path(written["summary_path"]).read_text(encoding="utf-8")
    assert "_arrays" not in summary_text


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
