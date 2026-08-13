"""Unit tests for the H-11c gate (AnEn vs. dispersion-matched HAR, KAPITALFREI).

H-11c is the registered follow-up obligation from GL-022. Its whole point is
that the H-11 gate could not separate INFORMATION from DISTRIBUTIONAL
GEOMETRY: scoring a Dirac baseline against a 20-member ensemble hands an
information-free forecaster a CRPSS of ~0.21-0.29, four to five times the
registered 0.05 threshold. These tests pin exactly that:

  (a) the dressed baseline's forecast path is BIT-IDENTICAL to the registered
      HAR path — dressing must add spread, never move the point forecast,
  (b) the dressing offsets are a mean-centred deterministic quantile sample
      (no RNG, exactly reproducible) built ONLY from in-fit residuals,
  (c) THE DECISIVE TEST: on the same structureless AR(1) fixture that
      test_c11_anen.py uses to characterise the artifact, the OLD rule shows
      a large positive CRPSS while the NEW rule collapses it towards zero —
      i.e. the H-11c gate has the discriminating power the H-11 gate lacked,
  (d) on a fixture with genuine exploitable structure, the new gate still
      fires (it is not simply "always zero"),
  (e) the chi^2 helper matches published chi^2 tail probabilities,
  (f) capital_free=true and no cost-model identifiers in the new modules,
  (g) the continuity precondition (DEC-32): a MATERIALITY bound derived from
      the gate arithmetic — pinned >=100x below the threshold so it can never
      move a decision — plus the panel fingerprint that makes a moving
      harvest snapshot visible instead of silent.
"""
from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from bybit_edge.research.c11_anen.analog import analog_forecast
from bybit_edge.research.c11_anen.baseline import har_fit, har_forecast_series
from bybit_edge.research.c11_anen.dressed import (
    block_bootstrap_p_two_sided,
    chi2_uniform_pvalue,
    dressing_offsets,
    har_forecast_series_dressed,
)
from bybit_edge.research.c11_anen.features import compute_feature_matrix, compute_target
from bybit_edge.research.c11_anen.stats import crps_ensemble, crps_point, crpss

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REPO_ROOT / "src" / "bybit_edge" / "research" / "c11_anen"

K = 20


def _iso_dates(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def _ar1_null(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Structureless AR(1) log-RV with PURE NOISE funding.

    Identical construction to
    ``test_c11_anen.py::test_ensemble_crps_vs_point_crps_asymmetry_is_documented_not_a_bug``
    so both tests characterise the SAME null fixture from opposite sides.
    """
    rng = np.random.default_rng(seed)
    log_rv = np.empty(n)
    log_rv[0] = np.log(0.02)
    mu, phi = np.log(0.02), 0.85
    for t in range(1, n):
        log_rv[t] = mu + phi * (log_rv[t - 1] - mu) + 0.25 * rng.standard_normal()
    return np.exp(log_rv), 1e-4 * rng.standard_normal(n)


def _regime_series(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Funding square wave LEADS the vol regime by 3 days (AnEn-favourable)."""
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    funding = np.where((idx // 30) % 2 == 0, 1e-4, -1e-4)
    lead = np.roll(funding, 3)
    lead[:3] = funding[0]
    regime_rv = np.where(lead > 0, 0.05, 0.012)
    return regime_rv * np.exp(0.10 * rng.standard_normal(n)), funding


def _score_cell(rv, funding, weights, *, start=260, k=K):
    """Both rules on one fixture: (CRPSS_old_dirac, CRPSS_new_dressed)."""
    n = rv.size
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", n)
    fidx = np.arange(start, n - 4, dtype=np.int64)

    members_list, days = [], []
    for t in fidx:
        t = int(t)
        if not np.isfinite(targets[t]):
            continue
        members, _sel = analog_forecast(feats, targets, t, weights, k=k)
        if members.size:
            members_list.append(members)
            days.append(t)
    days = np.asarray(days, dtype=np.int64)
    har, _n, dressed = har_forecast_series_dressed(
        feats[:, 0], feats[:, 1], log_rv22, targets, dates, days, k=k)
    paired = np.isfinite(har)
    obs = targets[days][paired]
    members_mat = np.vstack(members_list)[paired]

    c_anen = crps_ensemble(members_mat, obs)
    c_point = crps_point(har[paired], obs)
    c_dressed = crps_ensemble(dressed[paired], obs)
    return crpss(c_anen, c_point), crpss(c_anen, c_dressed)


# ----------------------------------------------------------------------------
# (a) the dressed path must not move the HAR point forecast
# ----------------------------------------------------------------------------

def test_dressed_forecast_path_is_bit_identical_to_registered_har():
    rv, funding = _ar1_null(500, seed=3)
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", rv.size)
    fidx = np.arange(200, rv.size - 4, dtype=np.int64)

    ref, ref_refits = har_forecast_series(
        feats[:, 0], feats[:, 1], log_rv22, targets, dates, fidx)
    got, got_refits, members = har_forecast_series_dressed(
        feats[:, 0], feats[:, 1], log_rv22, targets, dates, fidx, k=K)

    assert got_refits == ref_refits
    finite = np.isfinite(ref)
    assert np.array_equal(np.isfinite(got), finite)
    assert np.array_equal(got[finite], ref[finite]), (
        "dressing must leave the HAR point forecast byte-for-byte unchanged")
    # the ensemble MEAN equals the point forecast exactly (mean-centred offsets)
    assert np.allclose(members[finite].mean(axis=1), ref[finite], atol=1e-12)
    assert members.shape == (fidx.size, K)


def test_dressed_members_are_the_point_forecast_plus_frozen_offsets():
    rv, funding = _ar1_null(400, seed=11)
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", rv.size)
    fidx = np.arange(200, rv.size - 4, dtype=np.int64)
    fc, _n, members = har_forecast_series_dressed(
        feats[:, 0], feats[:, 1], log_rv22, targets, dates, fidx, k=K)
    ok = np.isfinite(fc)
    offsets = members[ok] - fc[ok][:, None]
    # offsets are frozen per monthly refit -> only a handful of distinct rows
    distinct = np.unique(np.round(offsets, 12), axis=0)
    assert 1 <= distinct.shape[0] <= 12, (
        f"offsets must be frozen with beta between monthly refits, got "
        f"{distinct.shape[0]} distinct offset vectors")
    assert np.all(np.diff(offsets, axis=1) >= -1e-12), "offsets must be sorted"


# ----------------------------------------------------------------------------
# (b) dressing offsets: deterministic, centred, from in-fit residuals only
# ----------------------------------------------------------------------------

def test_dressing_offsets_are_centred_deterministic_quantiles():
    rng = np.random.default_rng(5)
    r = rng.standard_normal(500)
    a = dressing_offsets(r, K)
    b = dressing_offsets(r, K)
    assert np.array_equal(a, b), "no RNG: the offsets must be exactly reproducible"
    assert a.shape == (K,)
    assert abs(float(a.mean())) < 1e-12, "offsets must be mean-centred"
    pos = (np.arange(1, K + 1) - 0.5) / K
    assert np.allclose(a, np.quantile(r, pos) - np.mean(np.quantile(r, pos)))
    # a wider residual sample must produce a wider cloud
    assert float(np.std(dressing_offsets(3.0 * r, K))) > 2.5 * float(np.std(a))


def test_dressing_uses_only_in_fit_residuals_no_lookahead():
    """The dressing of the FIRST forecast day must be computable from the fit
    window alone — recomputing it by hand from data <= t-embargo reproduces it.
    """
    rv, funding = _ar1_null(400, seed=7)
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", rv.size)
    t0 = 200
    fidx = np.arange(t0, t0 + 5, dtype=np.int64)
    fc, _n, members = har_forecast_series_dressed(
        feats[:, 0], feats[:, 1], log_rv22, targets, dates, fidx, k=K)

    x_all = np.column_stack([feats[:, 0], feats[:, 1], log_rv22])
    ok = np.all(np.isfinite(x_all), axis=1) & np.isfinite(targets)
    mask = ok.copy()
    mask[t0 - 30 + 1:] = False          # strictly <= t0 - embargo
    beta = har_fit(x_all[mask], targets[mask])
    design = np.column_stack([np.ones(int(mask.sum())), x_all[mask]])
    expected = dressing_offsets(targets[mask] - design @ beta, K)
    assert np.allclose(members[0] - fc[0], expected, atol=1e-12)


# ----------------------------------------------------------------------------
# (c) THE DECISIVE TEST — GL-022's finding, pinned
# ----------------------------------------------------------------------------

def test_null_fixture_old_rule_inflates_new_rule_does_not():
    """GL-022 label E1/E2, as a regression test.

    On a structureless AR(1) fixture with pure-noise funding there is nothing
    to forecast beyond persistence. The OLD (registered H-11) rule still
    awards a large positive CRPSS because it scores a Dirac against an
    ensemble. The NEW (H-11c) rule, which gives the identical HAR point
    forecast a zero-information cloud of the same shape, must collapse that
    advantage towards zero — well under the 0.05 gate threshold.
    """
    rv, funding = _ar1_null(560, seed=19)
    old, new = _score_cell(rv, funding, np.ones(5))
    assert old > 0.15, (
        f"fixture must reproduce the documented Dirac-vs-ensemble inflation "
        f"(CRPSS_old={old:.4f}); if this drops, the fixture stopped "
        f"characterising GL-022")
    assert new < 0.05, (
        f"the dispersion-matched gate must NOT fire on a structureless "
        f"fixture (CRPSS_dressed={new:.4f} >= 0.05 threshold)")
    assert new < old - 0.10, (
        f"removing the Dirac term must remove most of the apparent skill "
        f"(old={old:.4f}, new={new:.4f})")


def test_dressing_alone_beats_the_point_rule_by_the_structural_amount():
    """A zero-information dressing of a point forecast must ITSELF score a
    large positive CRPSS under the old rule — the quantitative core of GL-022
    label E1 (expected ~0.21-0.29 depending on the error tails).
    """
    rng = np.random.default_rng(23)
    n = 4000
    err = rng.standard_normal(n)               # HAR errors, unit scale
    obs = np.zeros(n)
    point = err                                # forecast - obs = err
    members = point[:, None] + dressing_offsets(rng.standard_normal(5000), K)[None, :]
    skill = crpss(crps_ensemble(members, obs), crps_point(point, obs))
    assert 0.18 < skill < 0.32, (
        f"structural null effect of dressing out of the documented band "
        f"(CRPSS={skill:.4f}); GL-022 quantifies 0.2123 (Laplace) .. 0.2929 "
        f"(Gauss, k->inf)")


# ----------------------------------------------------------------------------
# (d) the new gate is not simply always zero
# ----------------------------------------------------------------------------

def test_new_rule_still_detects_genuine_structure():
    rv, funding = _regime_series(560, seed=18)
    weights = np.array([0.5, 0.5, 0.5, 2.0, 2.0])
    old, new = _score_cell(rv, funding, weights)
    assert new >= 0.05, (
        f"a genuinely exploitable regime lead must still clear the H-11c "
        f"threshold (CRPSS_dressed={new:.4f}, old rule {old:.4f})")


def test_two_sided_bootstrap_is_symmetric_and_bounded():
    rng = np.random.default_rng(31)
    noise = rng.standard_normal(200)
    p_noise = block_bootstrap_p_two_sided(noise, block_len=5, n_bootstrap=400)
    p_shift = block_bootstrap_p_two_sided(noise + 3.0, block_len=5, n_bootstrap=400)
    assert p_noise > 0.10, f"zero-mean noise must not be significant (p={p_noise:.3f})"
    assert p_shift <= 1.0 / 401.0 * 2, f"a 3-sigma shift must be significant (p={p_shift:.4f})"
    assert block_bootstrap_p_two_sided(-(noise + 3.0), block_len=5,
                                       n_bootstrap=400) == p_shift


# ----------------------------------------------------------------------------
# (e) chi^2 helper
# ----------------------------------------------------------------------------

def test_chi2_uniform_pvalue_matches_published_values():
    # published chi^2 tail probabilities (df=20): P(X>31.410)=0.05,
    # P(X>28.412)=0.10, P(X>37.566)=0.01
    for x, ref in ((31.4104, 0.05), (28.4120, 0.10), (37.5662, 0.01)):
        got = chi2_uniform_pvalue(np.zeros(21))[0]  # smoke: uniform -> chi2 0
        assert got == 0.0 or np.isnan(got)
        from bybit_edge.research.c11_anen.dressed import _chi2_sf
        assert abs(_chi2_sf(x, 20) - ref) < 5e-4, f"chi2_sf({x}, 20)"
    # the GL-022 BTC-W2 histogram must reproduce the adjudicated chi2/p
    hist = np.array([2, 4, 9, 5, 3, 10, 7, 2, 4, 3, 7, 10, 4, 6, 6, 5, 3, 1, 0, 1, 4])
    chi2, p = chi2_uniform_pvalue(hist)
    assert abs(chi2 - 35.6875) < 1e-3, chi2
    assert abs(p - 0.0167) < 5e-4, p


# ----------------------------------------------------------------------------
# (f) capital freedom
# ----------------------------------------------------------------------------

def test_new_modules_are_capital_free():
    forbidden = ("bps", "fee", "slippage", "pnl", "commission", "taker", "maker",
                 "spread_cost", "friction")
    for name in ("dressed.py", "driver_c.py"):
        src = (MODULE_DIR / name).read_text(encoding="utf-8")
        ast.parse(src)  # must stay syntactically valid
        code = "\n".join(
            line for line in src.splitlines()
            if not line.lstrip().startswith("#"))
        # strip docstrings before scanning for cost identifiers
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    code = code.replace(doc, "")
        lowered = code.lower()
        for term in forbidden:
            assert term not in lowered, f"{name} must stay capital-free ({term})"


# ----------------------------------------------------------------------------
# (g) continuity precondition: materiality bound, not bit-identity (DEC-32)
# ----------------------------------------------------------------------------

def test_materiality_bound_is_derived_from_the_gate_not_from_an_observation():
    """The bound must be small enough that it cannot move a gate decision.

    A relative perturbation eps on the CRPS sums moves CRPSS = 1 - A/D by at
    most ~2*eps. The registered threshold is 0.05, so the induced error must
    stay orders of magnitude below it. Pinned here so nobody can quietly widen
    the bound into a range where it WOULD matter.
    """
    from bybit_edge.research.c11_anen.driver_c import MATERIALITY_RTOL
    from bybit_edge.research.c11_anen.stats import CRPSS_MIN

    induced_crpss_error = 2.0 * MATERIALITY_RTOL
    assert induced_crpss_error <= CRPSS_MIN / 100.0, (
        f"the continuity bound must stay >=100x below the gate threshold "
        f"(induced {induced_crpss_error:.1e} vs threshold {CRPSS_MIN})")


def test_continuity_check_needs_both_quantities_inside_the_bound():
    from bybit_edge.research.c11_anen.driver_c import (
        GL022_CRPSS_POINT_RULE,
        GL022_SUM_CRPS_ANEN,
        MATERIALITY_RTOL,
        _repro_check,
    )
    key = ("BTCUSDT", "W1")
    s, sk = GL022_SUM_CRPS_ANEN[key], GL022_CRPSS_POINT_RULE[key]

    assert _repro_check(*key, s, sk)["matches"] is True
    # the 2026-08-12 ETH-W1 deviation (8.3e-9 on the CRPSS) must now pass —
    # it is four orders of magnitude below the bound
    assert _repro_check(*key, s * (1 + 3.8e-9), sk * (1 + 8.3e-9))["matches"] is True
    # a deviation ABOVE the bound must still fail, in either quantity alone
    assert _repro_check(*key, s * (1 + 10 * MATERIALITY_RTOL), sk)["matches"] is False
    assert _repro_check(*key, s, sk * (1 + 10 * MATERIALITY_RTOL))["matches"] is False
    # the raw deviations stay visible regardless of pass/fail
    r = _repro_check(*key, s * (1 + 3.8e-9), sk * (1 + 8.3e-9))
    assert abs(r["rel_diff"] - 3.8e-9) < 1e-12
    assert abs(r["rel_diff_crpss_point_rule"] - 8.3e-9) < 1e-12


def test_panel_fingerprint_detects_a_single_changed_day():
    from bybit_edge.research.c11_anen.driver_c import _panel_fingerprint

    rv = np.linspace(0.01, 0.05, 50)
    fd = np.zeros(50)
    dates = _iso_dates("2025-01-01", 50)
    base = _panel_fingerprint(rv, fd, dates)
    assert base == _panel_fingerprint(rv.copy(), fd.copy(), list(dates))
    moved = rv.copy()
    moved[17] *= 1 + 1e-15          # one day, last-bit change
    assert _panel_fingerprint(moved, fd, dates)["sha256_rv_daily"] != base["sha256_rv_daily"]
