"""Tests of Zone X programme 1 (IK-05 RMT factor count, IK-04 null-world moments).

No network, no market data: every fixture is synthetic.  Covered
  (a) Marchenko-Pastur edge against the formula and against a noise spectrum;
  (b) factor count on panels with k = 0 / 1 / 3 factors (residual and raw, Pearson and Spearman);
  (c) kurtosis / skewness estimators on known distributions (normal, exponential, Student t);
  (d) autocorrelation, effective cluster number, cross-sectional dispersion, terciles, missing-day share;
  (e) zone guard: a day after 2024-06-30 or a start before 2021-01-01 raises, before the client is touched;
  (f) loader against a stand-in for the Harvest client (same call sequence as the repository's extract scripts);
  (g) output schema: no mean / sign / series fields; location- and sign-invariance of the outputs;
  (h) determinism (two runs byte-identical), command line, source hygiene.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import warnings
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from scipy import stats

from bybit_edge.research.zone_x import common
from bybit_edge.research.zone_x import ik04_moments as ik04
from bybit_edge.research.zone_x import ik05_rmt as ik05
from bybit_edge.research.zone_x import run_zone_x_1 as run

START = date(2021, 1, 1)
ZONE_DIR = Path(common.__file__).resolve().parent


# ----------------------------------------------------------------------------
# synthetic fixtures
# ----------------------------------------------------------------------------

def make_panel(returns: np.ndarray, *, start: date = START, missing: np.ndarray | None = None,
               turnover: np.ndarray | None = None, symbols: list[str] | None = None) -> common.Panel:
    """Panel (through ``build_panel``) whose log returns are ``returns`` (T x S); day 0 carries the first close.

    ``missing`` (bool, (T + 1) x S) removes candle rows; default turnover grows with the symbol index."""
    t, s = returns.shape
    n = t + 1
    close = np.exp(np.log(100.0) + np.vstack([np.zeros((1, s)), np.cumsum(returns, axis=0)]))
    days = common.day_number(start) + np.arange(n)
    names = np.asarray(symbols or [f"S{i:03d}USDT" for i in range(s)])
    turn = turnover if turnover is not None else np.tile(1.0e6 * (1.0 + np.arange(s)), (n, 1))
    present = np.ones((n, s), dtype=bool) if missing is None else ~missing
    di, si = np.nonzero(present)
    end = date.fromordinal(start.toordinal() + n - 1)
    return common.build_panel(names[si], days[di], close[di, si], turn[di, si], start, end)


def factor_returns(k: int, *, seed: int = 7, n_days: int = 900, n_sym: int = 60, load: float = 0.6) -> np.ndarray:
    """Market + k block factors + noise.  A block factor loads with alternating signs on 20 symbols, so the
    equal-weighted market factor does not absorb it (it would, if all loadings had one sign)."""
    rng = np.random.default_rng(seed)
    sigma = 0.03
    f0 = 0.02 * rng.standard_normal(n_days)
    beta = 1.0 + 0.3 * rng.standard_normal(n_sym)
    r = f0[:, None] * beta[None, :] + sigma * rng.standard_normal((n_days, n_sym))
    sign = np.where(np.arange(20) % 2 == 0, 1.0, -1.0)
    for j in range(k):
        r[:, 20 * j: 20 * (j + 1)] += load * sigma * np.outer(rng.standard_normal(n_days), sign)
    return r


def walk(node: Any, path: str = ""):
    """Yield (path, key-or-None, value) for every dict key and list element of a JSON object."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for v in node:
            yield path, None, v
            yield from walk(v, path)


@pytest.fixture(scope="module")
def factor3_output() -> dict[str, Any]:
    return run.build_output(make_panel(factor_returns(3)), {"n_load_warnings": 0, "load_warnings": []})


# ----------------------------------------------------------------------------
# (a) Marchenko-Pastur edge
# ----------------------------------------------------------------------------

@pytest.mark.parametrize("k, t, expected", [(100, 400, 2.25), (1, 1, 4.0), (200, 1277, 1.95), (300, 1277, 2.20),
                                            (500, 1277, 2.64)])
def test_mp_edge_matches_formula(k, t, expected):
    assert ik05.mp_edge(k, t) == pytest.approx((1.0 + np.sqrt(k / t)) ** 2, rel=1e-15)
    assert ik05.mp_edge(k, t) == pytest.approx(expected, abs=0.006)     # values quoted in the IK-05 card


@pytest.mark.parametrize("k, t", [(0, 10), (10, 0), (-1, 5)])
def test_mp_edge_rejects_bad_input(k, t):
    with pytest.raises(ValueError):
        ik05.mp_edge(k, t)


def test_mp_edge_bounds_noise_spectrum():
    rng = np.random.default_rng(5)
    k, t = 100, 800
    eig = ik05.correlation_eigenvalues(rng.standard_normal((t, k)))
    assert eig.sum() == pytest.approx(k, rel=1e-10)                     # trace of a correlation matrix
    assert np.all(np.diff(eig) <= 1e-12)                                # descending
    edge = ik05.mp_edge(k, t)
    assert abs(eig[0] - edge) < 0.12
    assert abs(eig[-1] - (1.0 - np.sqrt(k / t)) ** 2) < 0.12


def test_spearman_is_rank_invariant_and_pearson_is_not():
    rng = np.random.default_rng(2)
    x = rng.standard_normal((300, 20))
    x[:, :10] += rng.standard_normal((300, 1))
    a = ik05.correlation_eigenvalues(x, rank=True)
    b = ik05.correlation_eigenvalues(np.exp(2.0 * x), rank=True)        # monotone transform
    assert np.allclose(a, b, atol=1e-10)
    assert not np.allclose(ik05.correlation_eigenvalues(x), ik05.correlation_eigenvalues(np.exp(2.0 * x)), atol=1e-3)


def test_correlation_eigenvalues_rejects_missing_and_constant():
    with pytest.raises(ValueError):
        ik05.correlation_eigenvalues(np.array([[1.0, np.nan], [2.0, 3.0], [3.0, 1.0]]))
    with pytest.raises(ValueError):
        ik05.correlation_eigenvalues(np.array([[1.0, 5.0], [2.0, 5.0], [3.0, 5.0]]))


# ----------------------------------------------------------------------------
# (b) factor count
# ----------------------------------------------------------------------------

@pytest.mark.parametrize("k", [0, 1, 3])
def test_factor_count_recovered_on_residuals(k):
    """k block factors on top of the market and noise: the residual spectrum has exactly k eigenvalues above the MP
    edge.  With k = 0 the largest NOISE eigenvalue fluctuates around the edge (Tracy-Widom scale, about 0.05 at
    K = 60): it may sit just above the formula edge, so up to one such eigenvalue is accepted -- but never one of
    factor size."""
    out = run.build_output(make_panel(factor_returns(k)))
    full = out["ik05"]["full"]
    assert full["status"] == "ok" and full["k_symbols"] == 60 and full["t_days"] == 900
    edge = full["mp_edge"]
    assert edge == pytest.approx((1.0 + np.sqrt(60 / 900)) ** 2, rel=1e-9)
    for kind in ("pearson", "spearman"):
        res = full[kind]["residual"]
        top = res["top_eigenvalues"]
        if k == 0:
            assert res["n_above_edge"] <= 1 and top[0] < 1.25 * edge, (kind, top[:3])
            assert res["explained_share_above_edge"] < 0.05
        else:
            assert res["n_above_edge"] == k, (kind, top[:5])
            assert top[k - 1] > 3.0 * edge and top[k] < 1.25 * edge
            assert 0.0 < res["explained_share_above_edge"] < 1.0


@pytest.mark.parametrize("load, n_needed", [(1.0, 2), (0.4, 0)])
def test_lambda_needed_separates_strong_from_weak_factors(load, n_needed):
    """Two block factors: both are above the MP edge, but only strong ones reach the eigenvalue 6.25 that a
    2.5-fold IC dispersion would need (eigenvalue about 1 + 19 * load^2 / (1 + load^2))."""
    res = run.build_output(make_panel(factor_returns(2, load=load)))["ik05"]["full"]["pearson"]["residual"]
    assert res["n_above_edge"] == 2 and res["n_ge_lambda_needed"] == n_needed


def test_raw_returns_carry_the_market_eigenvalue_that_residuals_lose():
    out = run.build_output(make_panel(factor_returns(1)))["ik05"]["full"]["pearson"]
    assert out["raw"]["n_above_edge"] == out["residual"]["n_above_edge"] + 1
    assert out["raw"]["top_eigenvalues"][0] > 2.0 * out["residual"]["top_eigenvalues"][0]
    assert len(out["raw"]["top_eigenvalues"]) == 20 and len(out["residual"]["top_eigenvalues"]) == 20


def test_spectrum_summary_counts_and_shares():
    eig = np.array([9.0, 6.25, 6.2499, 2.0, 1.0, 0.0])
    s = ik05.spectrum_summary(eig, 1.5)
    assert s["n_above_edge"] == 4 and s["n_ge_lambda_needed"] == 2            # 6.25 itself counts, 6.2499 does not
    assert s["explained_share_above_edge"] == pytest.approx((9.0 + 6.25 + 6.2499 + 2.0) / 6.0, rel=1e-12)
    assert s["top_eigenvalues"] == list(eig)
    assert len(ik05.spectrum_summary(np.arange(50.0)[::-1], 10.0)["top_eigenvalues"]) == 20
    assert ik05.LAMBDA_NEEDED == 6.25 == 1.0 + (2.5 ** 2 - 1.0)


def test_balanced_subpanel_rule():
    rng = np.random.default_rng(1)
    r = rng.standard_normal((100, 5))
    r[10:13, 3] = np.nan            # 97 % coverage: kept, but its gap days leave the complete-case rows
    r[:50, 4] = np.nan              # 50 % coverage: dropped
    eligible = np.ones(100, dtype=bool)
    eligible[0] = False             # a day without market factor does not count at all
    rows, cols, n_cov = ik05.balanced_subpanel(r, eligible, 0.9)
    assert list(cols) == [0, 1, 2, 3] and n_cov == 4
    assert len(rows) == 99 - 3 and not set(rows) & {0, 10, 11, 12}
    rows2, cols2, _ = ik05.balanced_subpanel(r, eligible, 0.4)
    assert list(cols2) == [0, 1, 2, 3, 4]
    assert list(rows2) == list(range(50, 100))        # only days 50..99 have all five symbols
    assert ik05.balanced_subpanel(r, np.zeros(100, dtype=bool), 0.9)[0].size == 0


def test_subwindows_are_reanalysed_and_clipped():
    full_days = 1277                                   # 2021-01-01 .. 2024-06-30 has 1277 calendar days
    rng = np.random.default_rng(9)
    ret = 0.03 * rng.standard_normal((full_days - 1, 30))
    out = run.build_output(make_panel(ret))
    assert out["window"]["start"] == "2021-01-01" and out["window"]["end"] == "2024-06-30"
    assert out["window"]["n_calendar_days"] == 1277 and out["window"]["n_return_days"] == 1276
    subs = out["ik05"]["sub_windows"]
    assert set(subs) == {"sub1", "sub2", "sub3"}
    assert subs["sub1"]["start"] == "2021-01-02" and subs["sub1"]["end"] == "2022-02-28"
    assert subs["sub2"]["start"] == "2022-03-01" and subs["sub2"]["end"] == "2023-04-30"
    assert subs["sub3"]["start"] == "2023-05-01" and subs["sub3"]["end"] == "2024-06-30"
    for name, t_expect in (("sub1", 423), ("sub2", 426), ("sub3", 427)):
        assert subs[name]["status"] == "ok" and subs[name]["k_symbols"] == 30 and subs[name]["t_days"] == t_expect
        assert subs[name]["mp_edge"] == pytest.approx((1.0 + np.sqrt(30 / t_expect)) ** 2, rel=1e-9)


def test_window_without_days_is_skipped_not_invented():
    out = run.build_output(make_panel(0.03 * np.random.default_rng(4).standard_normal((300, 20))))
    subs = out["ik05"]["sub_windows"]
    assert subs["sub1"]["status"] == "ok"
    assert subs["sub2"]["status"] == "skipped" and subs["sub3"]["status"] == "skipped"
    assert "pearson" not in subs["sub3"]


# ----------------------------------------------------------------------------
# (c) moment estimators
# ----------------------------------------------------------------------------

def test_moments_match_scipy_with_gaps():
    rng = np.random.default_rng(3)
    x = rng.standard_normal((400, 6)) ** 3
    x[::7, 2] = np.nan
    n, skew, kurt = ik04.column_moments(x)
    for j in range(6):
        col = x[np.isfinite(x[:, j]), j]
        assert n[j] == col.size
        assert skew[j] == pytest.approx(stats.skew(col, bias=True), rel=1e-10)
        assert kurt[j] == pytest.approx(stats.kurtosis(col, fisher=True, bias=True), rel=1e-10)


def test_moments_nan_for_short_or_constant_columns():
    x = np.column_stack([np.arange(10.0), np.ones(100)[:10]])
    n, skew, kurt = ik04.column_moments(x, min_obs=5)
    assert np.isfinite(skew[0]) and np.isnan(skew[1]) and np.isnan(kurt[1])
    _, s2, k2 = ik04.column_moments(x, min_obs=11)
    assert np.isnan(s2).all() and np.isnan(k2).all()


def _grid(ppf, n: int) -> np.ndarray:
    """Deterministic equal-probability sample: ppf at (i + 0.5) / n."""
    return ppf((np.arange(n) + 0.5) / n)[:, None]


def test_moments_on_normal_and_exponential_grids():
    _, sk, ku = ik04.column_moments(_grid(stats.norm.ppf, 400_000))
    assert abs(sk[0]) < 1e-9 and abs(ku[0]) < 0.01
    _, sk, ku = ik04.column_moments(_grid(lambda p: -np.log1p(-p), 1_000_000))       # exponential: skew 2, excess 6
    assert sk[0] == pytest.approx(2.0, abs=0.01) and ku[0] == pytest.approx(6.0, abs=0.05)


@pytest.mark.parametrize("nu, tol", [(30, 0.01), (10, 0.05)])
def test_excess_kurtosis_on_student_t_grid_with_finite_eighth_moment(nu, tol):
    ku = ik04.column_moments(_grid(lambda p: stats.t.ppf(p, nu), 2_000_000))[2][0]
    assert ku == pytest.approx(6.0 / (nu - 4.0), abs=tol)


def test_excess_kurtosis_on_student_t5_is_about_six():
    """Excess kurtosis 6 is the value of t(5), 6 / (nu - 4).  The grid truncates the tails, hence a slight
    underestimate; the random sample has a huge estimator variance (the eighth moment does not exist)."""
    ku_grid = ik04.column_moments(_grid(lambda p: stats.t.ppf(p, 5), 4_000_000))[2][0]
    assert 5.0 < ku_grid < 6.5
    x = np.random.default_rng(11).standard_t(5, size=(1_000_000, 1))
    assert 3.5 < ik04.column_moments(x)[2][0] < 12.0


def test_excess_kurtosis_of_t4_is_not_six_but_unbounded():
    """t(4) has an infinite fourth moment: the estimate grows with the sample size instead of settling near 6."""
    small = ik04.column_moments(_grid(lambda p: stats.t.ppf(p, 4), 100_000))[2][0]
    large = ik04.column_moments(_grid(lambda p: stats.t.ppf(p, 4), 4_000_000))[2][0]
    assert small > 8.0 and large > small + 2.0


def test_quantile_block_and_terciles():
    qb = ik04.quantile_block(np.array([1.0, 2.0, 3.0, 4.0, 5.0, np.nan]))
    assert qb["n"] == 5 and qb["q50"] == 3.0 and qb["q10"] == pytest.approx(1.4) and qb["q90"] == pytest.approx(4.6)
    assert ik04.quantile_block(np.array([np.nan]))["q50"] is None
    med = np.array([5.0, 1.0, 9.0, 3.0, 7.0, 2.0, 8.0, 4.0, 6.0])
    cls = ik04.turnover_terciles(med, [f"S{i}USDT" for i in range(9)])
    assert sorted(set(cls)) == [0, 1, 2] and [int((cls == g).sum()) for g in range(3)] == [3, 3, 3]
    assert set(np.flatnonzero(cls == 0)) == {1, 5, 3} and set(np.flatnonzero(cls == 2)) == {2, 6, 4}
    tie = ik04.turnover_terciles(np.ones(6), list("fedcba"))                 # ties broken by the symbol name
    assert list(tie) == [2, 2, 1, 1, 0, 0]
    nan_first = ik04.turnover_terciles(np.array([np.nan, 5.0, 6.0]), ["A", "B", "C"])
    assert nan_first[0] == 0


# ----------------------------------------------------------------------------
# (d) autocorrelation, n_eff, dispersion, missing days
# ----------------------------------------------------------------------------

def test_autocorrelation_ar1_and_reference():
    from scipy.signal import lfilter
    phi, n = 0.6, 40_000
    x = lfilter([1.0], [1.0, -phi], np.random.default_rng(8).standard_normal(n))
    rho = ik04.autocorrelation(x, 5)
    assert np.allclose(rho, phi ** np.arange(1, 6), atol=0.02)
    d = x - x.mean()
    acov = np.fft.irfft(np.abs(np.fft.rfft(d, 2 * n)) ** 2)[: 6]                  # textbook estimator via FFT
    assert np.allclose(rho, acov[1:] / acov[0], atol=1e-12)


def test_autocorrelation_drops_pairs_with_gaps():
    x = np.tile([1.0, -1.0], 50)                     # lag-1 autocorrelation close to -1
    full = ik04.autocorrelation(x, 1)[0]
    assert full == pytest.approx(-99.0 / 100.0)
    y = x.copy()
    y[50] = np.nan
    gap = ik04.autocorrelation(y, 1)[0]
    assert gap == pytest.approx(-97.0 / 99.0, abs=1e-9)          # two pairs lost; denominator over 99 observed
    assert np.isnan(ik04.autocorrelation(np.array([1.0, 2.0]), 5)).all()
    assert np.isnan(ik04.autocorrelation(np.ones(50), 3)).all()


def test_effective_clusters_formula_and_floor():
    c_hat, n_eff = ik04.effective_clusters([0.2] * 5)
    assert c_hat == pytest.approx(3.0) and n_eff == pytest.approx(365.0 / 3.0)
    c_neg, n_neg = ik04.effective_clusters([-0.1] * 5)
    assert c_neg == pytest.approx(0.0) and n_neg == 365.0              # c = max(1, c_hat): never above n
    assert ik04.effective_clusters([0.1, np.nan, 0.1, 0.1, 0.1]) == (None, None)
    assert ik04.effective_clusters([0.1] * 3) == (None, None)          # fewer lags than asked
    assert ik04.effective_clusters([0.5] * 10, 100, max_lag=10)[1] == pytest.approx(100.0 / 11.0)


def test_volatility_clustering_lowers_n_eff():
    rng = np.random.default_rng(21)
    n_days, n_sym = 900, 40
    h = np.zeros(n_days)
    for t in range(1, n_days):
        h[t] = 0.97 * h[t - 1] + 0.2 * rng.standard_normal()
    f0 = 0.02 * np.exp(h) * rng.standard_normal(n_days)
    clustered = f0[:, None] + 0.01 * rng.standard_normal((n_days, n_sym))
    iid = 0.02 * rng.standard_normal((n_days, 1)) + 0.01 * rng.standard_normal((n_days, n_sym))
    a = run.build_output(make_panel(clustered))["ik04"]["abs_r_market"]
    b = run.build_output(make_panel(iid))["ik04"]["abs_r_market"]
    assert a["acf"]["1"] > 0.15 and abs(b["acf"]["1"]) < 0.1
    assert a["n_eff_365"] < 0.7 * 365.0 and b["n_eff_365"] > 0.8 * 365.0
    assert a["n_eff_by_max_lag"]["40"] <= a["n_eff_by_max_lag"]["5"]
    assert a["c_overlap"] == 1.0


def test_cross_section_sd_matches_numpy():
    rng = np.random.default_rng(6)
    r = rng.standard_normal((50, 12))
    r[rng.random(r.shape) < 0.3] = np.nan
    r[7, :] = np.nan
    r[8, 2:] = np.nan                                       # only two symbols: below the minimum
    got = common.cross_section_sd(r, 5)
    for t in range(50):
        col = r[t][np.isfinite(r[t])]
        if col.size >= 5:
            assert got[t] == pytest.approx(np.std(col, ddof=1), rel=1e-12)
        else:
            assert np.isnan(got[t])


def test_xs_dispersion_block_on_known_scaling():
    rng = np.random.default_rng(13)
    z = rng.standard_normal(30)
    scale = np.where(np.arange(600) % 2 == 0, 1.0, 2.0)
    out = run.build_output(make_panel(0.01 * scale[:, None] * z[None, :]))["ik04"]["xs_dispersion"]
    sd_z = np.std(z, ddof=1) * 0.01
    assert out["n_days"] == 600
    assert out["quantiles"]["q10"] == pytest.approx(sd_z, rel=1e-9)
    assert out["quantiles"]["q90"] == pytest.approx(2 * sd_z, rel=1e-9)
    assert out["level_over_days"] == pytest.approx(1.5 * sd_z, rel=1e-9)
    assert out["acf"]["1"] < -0.99 and out["acf"]["2"] > 0.99          # the alternating scale


def test_missing_day_share_counts_gaps_between_first_and_last_day_only():
    close = np.full((10, 3), np.nan)
    close[:, 0] = 1.0                                       # complete
    close[2:9, 1] = 1.0
    close[[4, 5], 1] = np.nan                               # 2 gaps inside a 7-day span
    close[5:, 2] = 1.0                                      # listed late: no gap
    share = ik04.missing_day_share(close)
    assert share[0] == 0.0 and share[1] == pytest.approx(2.0 / 7.0) and share[2] == 0.0
    assert np.isnan(ik04.missing_day_share(np.full((4, 1), np.nan))[0])


def test_gaps_are_never_bridged_in_returns():
    ret = 0.01 * np.random.default_rng(0).standard_normal((20, 3))
    missing = np.zeros((21, 3), dtype=bool)
    missing[8, 1] = True                                   # close of day 8 of symbol 1 is missing
    r = common.daily_log_returns(make_panel(ret, missing=missing))
    assert np.isnan(r[7, 1]) and np.isnan(r[8, 1])           # return INTO day 8 and OUT of day 8 are both gone
    assert np.isfinite(r[:, 0]).all() and np.isfinite(np.delete(r[:, 1], [7, 8])).all()
    assert np.isfinite(r[[6, 9], 1]).all()


def test_market_model_properties():
    rng = np.random.default_rng(12)
    f = rng.standard_normal(200)
    b = 1.0 + 0.4 * rng.random(15)
    pure = common.market_model(f[:, None] * b[None, :])
    assert np.abs(pure.resid).max() < 1e-12                  # a pure one-factor panel has no residual
    r = f[:, None] * b[None, :] + 0.5 * rng.standard_normal((200, 15))
    mm = common.market_model(r)
    assert np.allclose(mm.rm, r.mean(axis=1))
    cov = ((mm.resid - mm.resid.mean(axis=0)) * (mm.rm - mm.rm.mean())[:, None]).mean(axis=0)
    assert np.abs(cov).max() < 1e-12                         # residuals are orthogonal to the market factor
    few = common.market_model(r[:, :6], min_cross_section=10)
    assert np.isnan(few.rm).all() and np.isnan(few.resid).all()


# ----------------------------------------------------------------------------
# (e) zone guard
# ----------------------------------------------------------------------------

def test_check_window_accepts_zone_x_and_rejects_the_rest():
    assert common.check_window("2021-01-01", "2024-06-30") == (date(2021, 1, 1), date(2024, 6, 30))
    assert common.check_window(date(2022, 5, 1), date(2022, 5, 1))[0] == date(2022, 5, 1)
    for start, end in [("2020-12-31", "2022-01-01"), ("2021-01-01", "2024-07-01"), ("2024-07-01", "2024-07-02"),
                       ("2022-01-02", "2022-01-01"), ("not-a-date", "2022-01-01")]:
        with pytest.raises(common.ZoneGuardError):
            common.check_window(start, end)


def test_build_panel_raises_on_a_day_after_the_zone_end():
    ret = 0.01 * np.random.default_rng(1).standard_normal((20, 12))
    p = make_panel(ret)                                      # fine
    assert p.close.shape == (21, 12)
    n = 21
    day_after = common.day_number(date(2024, 7, 1))
    sym = np.array(["AAAUSDT"] * n + ["AAAUSDT"])
    days = np.concatenate([common.day_number(START) + np.arange(n), [day_after]])
    px = np.ones(n + 1)
    with pytest.raises(common.ZoneGuardError, match="after 2024-06-30"):
        common.build_panel(sym, days, px, px, START, date(2024, 6, 30))
    # also when the dropped symbol is not a USDT perpetual: the guard looks at every row
    sym2 = np.array(["AAAUSDT"] * n + ["BTC-26DEC25"])
    with pytest.raises(common.ZoneGuardError):
        common.build_panel(sym2, days, px, px, START, date(2024, 6, 30))


def test_build_panel_raises_on_a_day_before_the_zone_start():
    before = common.day_number(date(2020, 12, 31))
    with pytest.raises(common.ZoneGuardError, match="before 2021-01-01"):
        common.build_panel(["AAAUSDT", "AAAUSDT"], [before, before + 2], [1.0, 1.0], [1.0, 1.0], START,
                           date(2021, 1, 10))
    with pytest.raises(common.ZoneGuardError):
        common.build_panel(["AAAUSDT"], [common.day_number(START)], [1.0], [1.0], "2020-12-31", "2021-01-10")
    with pytest.raises(common.ZoneGuardError):
        common.build_panel(["AAAUSDT"], [common.day_number(START)], [1.0], [1.0], START, "2024-07-01")


def test_build_panel_rejects_candles_outside_the_requested_window():
    with pytest.raises(common.PanelError):
        common.build_panel(["AAAUSDT", "AAAUSDT"], [common.day_number(START), common.day_number(date(2021, 3, 1))],
                           [1.0, 1.0], [1.0, 1.0], START, date(2021, 2, 1))


# ----------------------------------------------------------------------------
# (f) loader against a stand-in for the Harvest client
# ----------------------------------------------------------------------------

class FakeClient:
    """Same surface as the Harvest client module: configure / load / extract (JSON payload with named fields)."""

    def __init__(self, rows: list[dict[str, Any]], warn: str | None = None):
        self.rows = rows
        self.warn = warn
        self.calls: list[tuple] = []

    def configure(self, **kwargs):
        self.calls.append(("configure", kwargs))

    def load(self, stream, symbols, start, end, *, exchange=None, columns=None, **kwargs):
        import polars as pl
        self.calls.append(("load", stream, list(symbols), start, end, exchange, tuple(columns or ())))
        if self.warn:
            warnings.warn(self.warn, stacklevel=2)
        payload = [json.dumps({"symbol": r.get("psym", r["symbol"]), "category": "linear", "interval": "D",
                               "startTime": str(r["start_ms"]), "openPrice": "1", "highPrice": "1", "lowPrice": "1",
                               "closePrice": r["close"], "volume": "1", "turnover": r["turnover"]}) for r in self.rows]
        return pl.DataFrame({"symbol": [r["symbol"] for r in self.rows], "payload_json": payload})

    def extract(self, df, fields):
        import polars as pl
        return df.with_columns(pl.col("payload_json").str.json_path_match(p).alias(n) for n, p in fields.items())


def _rows(n_days=5, symbols=("AAAUSDT", "BBBUSDT"), first=START):
    out = []
    for s in symbols:
        for i in range(n_days):
            ms = (common.day_number(first) + i) * common.DAY_MS
            out.append({"symbol": s, "start_ms": ms, "close": f"{10.0 + i}", "turnover": "5000.5"})
    return out


def test_loader_end_to_end_with_stand_in_client():
    rows = _rows() + [{"symbol": "BTC-26DEC25", "start_ms": common.day_number(START) * common.DAY_MS,
                       "close": "5", "turnover": "1"},
                      {"symbol": "ETHPERP", "start_ms": common.day_number(START) * common.DAY_MS,
                       "close": "5", "turnover": "1"},
                      {"symbol": "CCCUSDT", "start_ms": common.day_number(START) * common.DAY_MS,
                       "close": "0", "turnover": "bad"}]
    rows.append(dict(rows[0]))                               # an identical duplicate
    client = FakeClient(rows, warn="harvest_data: 1 (symbol, day) without data")
    panel, info = common.load_daily_panel("2021-01-01", "2021-01-05", client=client, cache_dir="/some/cache")
    assert client.calls[0] == ("configure", {"cache_dir": "/some/cache"})
    assert client.calls[1] == ("load", "rest.kline1d", ["ALL"], "2021-01-01", "2021-01-05", "bybit",
                               ("symbol", "payload_json"))
    assert panel.symbols == ("AAAUSDT", "BBBUSDT", "CCCUSDT")
    assert panel.close.shape == (5, 3) and panel.days[0] == common.day_number(START)
    assert panel.close[2, 0] == 12.0 and panel.turnover[2, 0] == 5000.5
    assert np.isnan(panel.close[0, 2]) and np.isnan(panel.turnover[0, 2])        # invalid close / turnover -> missing
    assert panel.stats["n_rows_non_usdt"] == 2 and panel.stats["n_rows_identical_duplicates"] == 1
    assert panel.stats["n_invalid_close"] == 1 and panel.stats["n_invalid_turnover"] == 1
    assert info["n_load_warnings"] == 1 and info["load_warnings"][0].startswith("harvest_data: 1")


def test_loader_guard_runs_before_the_client_is_touched(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the client must not be imported or called for a window outside Zone X")
    monkeypatch.setattr(common, "import_harvest_client", boom)
    client = FakeClient(_rows())
    client.load = boom
    client.configure = boom
    for start, end in [("2021-01-01", "2024-07-01"), ("2020-12-31", "2021-01-05"), ("2021-01-01", "2025-01-01")]:
        with pytest.raises(common.ZoneGuardError):
            common.load_daily_panel(start, end)
        with pytest.raises(common.ZoneGuardError):
            common.load_daily_panel(start, end, client=client)


def test_loader_refuses_a_cache_below_the_archive_tree():
    client = FakeClient(_rows())
    with pytest.raises(common.ZoneXError, match="data/harvest"):
        common.load_daily_panel("2021-01-01", "2021-01-05", client=client, cache_dir="/x/data/harvest/cache")
    assert client.calls == []


def test_loader_raises_when_the_client_delivers_a_day_after_the_zone():
    rows = _rows() + [{"symbol": "AAAUSDT", "start_ms": common.day_number(date(2024, 7, 1)) * common.DAY_MS,
                       "close": "1", "turnover": "1"}]
    with pytest.raises(common.ZoneGuardError):
        common.load_daily_panel("2021-01-01", "2024-06-30", client=FakeClient(rows))


def test_loader_rejects_malformed_payloads():
    bad_symbol = _rows()
    bad_symbol[0]["psym"] = "OTHERUSDT"
    with pytest.raises(common.PanelError, match="payload symbol"):
        common.load_daily_panel("2021-01-01", "2021-01-05", client=FakeClient(bad_symbol))
    conflict = _rows() + [dict(_rows()[0], close="99")]
    with pytest.raises(common.PanelError, match="DIFFERENT"):
        common.load_daily_panel("2021-01-01", "2021-01-05", client=FakeClient(conflict))
    off_boundary = _rows()
    off_boundary[0]["start_ms"] += 1000
    with pytest.raises(common.PanelError, match="day boundary"):
        common.load_daily_panel("2021-01-01", "2021-01-05", client=FakeClient(off_boundary))
    with pytest.raises(common.PanelError, match="no rows"):
        common.load_daily_panel("2021-01-01", "2021-01-05", client=FakeClient([]))


def test_missing_client_gives_a_clear_error(monkeypatch):
    monkeypatch.delitem(sys.modules, "harvest_data", raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if "harvest" not in p.lower()])
    monkeypatch.delenv("HARVEST_CLIENT_DIR", raising=False)
    try:
        import harvest_data  # noqa: F401
    except ImportError:
        with pytest.raises(common.HarvestClientError, match="HARVEST_CLIENT_DIR"):
            common.import_harvest_client()
    else:                                                    # a client is installed on this machine: nothing to test
        pytest.skip("harvest_data is importable here")


# ----------------------------------------------------------------------------
# (g) output schema, forbidden outputs, invariances
# ----------------------------------------------------------------------------

def test_output_has_the_required_fields(factor3_output):
    out = factor3_output
    assert out["zone"] == "X" and out["program"] == "zone_x_1"
    assert out["window"]["start"] == "2021-01-01" and out["window"]["n_calendar_days"] == 901
    assert out["inputs"]["stream"] == "rest.kline1d" and out["inputs"]["n_symbols_analysed"] == 60
    assert out["inputs"]["n_symbols_excluded_min_days"] == 0 and out["inputs"]["n_symbols_loaded"] == 60
    rep = out["report"]
    assert rep["zone"] == "X" and rep["c_overlap"] == 1.0 and rep["selection_k"] == 1
    assert rep["n_eff"] == out["ik04"]["abs_r_market"]["n_eff_365"]
    assert rep["estimate"] is None and rep["upper_limit95"] is None
    for name in ("common", "ik05_rmt", "ik04_moments", "run_zone_x_1"):
        assert out["code_sha256"][name] == hashlib.sha256((ZONE_DIR / f"{name}.py").read_bytes()).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", out["code_sha256"]["combined"])


def test_output_schema_has_no_mean_sign_or_series_fields(factor3_output):
    forbidden = ("mean", "avg", "average", "sign", "positive", "negative", "drift", "cumul", "series", "beta",
                 "alpha", "intercept", "pnl", "per_symbol", "by_symbol", "per_day", "by_day")
    common.validate_output(factor3_output)
    for _, key, _ in walk(factor3_output):
        if key is not None:
            assert key in common.ALLOWED_KEYS
            assert not any(tok in key.lower() for tok in forbidden), key
    for key in common.ALLOWED_KEYS:
        assert not any(tok in key.lower() for tok in forbidden), key
    for path, key, val in walk(factor3_output):
        if isinstance(val, list):
            assert len(val) <= 20 and all(not isinstance(v, (list, dict)) for v in val), (path, key)
    leaves = [v for _, _, v in walk(factor3_output) if isinstance(v, (int, float)) and not isinstance(v, bool)]
    assert len(leaves) < 1500
    assert not re.search(r"\d{4}-\d{2}-\d{2}", " ".join(k for _, k, _ in walk(factor3_output) if k))    # no date keys
    assert not any(re.fullmatch(r"[A-Z0-9]+USDT", k or "") for _, k, _ in walk(factor3_output))        # no symbol keys


@pytest.mark.parametrize("bad", [
    {"mean_return": 0.1},
    {"ik04": {"r_mean": 0.1}},
    {"ik04": {"BTCUSDT": {"q50": 1.0}}},
    {"ik04": {"2021-01-02": 1.0}},
    {"ik05": {"top_eigenvalues": list(range(21))}},
    {"ik05": {"top_eigenvalues": [[1.0, 2.0]]}},
    {"ik05": {"top_eigenvalues": [{"q50": 1.0}]}},
    {"ik05": {"mp_edge": float("nan")}},
    {"ik05": {"mp_edge": float("inf")}},
    {"ik05": {"method": "x" * 301}},
    {"ik05": {"mp_edge": (1, 2)}},
    {"report": {"sign": 1}},
    {"ik04": {"moments": {"r_daily": {"all": {"skewness": {"q50": {"q50": {"q50": {"q50": {"q50": {"q50": 1.0}}}}}}}}}}},
])
def test_validate_output_rejects_forbidden_shapes(bad):
    with pytest.raises(common.OutputSchemaError):
        common.validate_output(bad)


def test_validate_output_accepts_the_largest_legitimate_shapes_and_bounds_the_leaf_count(monkeypatch):
    with pytest.raises(common.OutputSchemaError):
        common.validate_output([1, 2])
    common.validate_output({"ik05": {"full": {"pearson": {"residual": {"top_eigenvalues": [1.0] * 20}}}}})
    assert common.MAX_LIST_LEN == 20
    monkeypatch.setattr(common, "MAX_LEAVES", 5)
    with pytest.raises(common.OutputSchemaError, match="too many values"):
        common.validate_output({"ik05": {"full": {"top_eigenvalues": [1.0] * 6}}})


def test_allowed_keys_are_checked_at_import_time():
    assert common.ALLOWED_KEYS and not any(t in k for k in common.ALLOWED_KEYS for t in common.FORBIDDEN_KEY_TOKENS)


def test_no_class_count_with_dispersion_nesting(factor3_output):
    """DEC-103 N1 (2c): no dict may carry a count together with an SD-like value (nested class dispersions)."""
    counts = {"n", "count", "N", "n_days", "n_obs"}
    sdk = {"sd", "std", "sigma", "sd_cluster", "sd_bp", "sd_ddof1"}
    def check(node):
        if isinstance(node, dict):
            assert not (counts & set(node) and sdk & set(node)), node.keys()
            for v in node.values():
                check(v)
    check(factor3_output)


def test_channel_scan_of_the_programme_finds_nothing(tmp_path, factor3_output):
    import bybit_edge.research as research
    roots = [Path(__file__).resolve().parents[2], Path(list(research.__path__)[-1]).resolve().parents[2]]
    found = [r / "scinance3-impl" / "tools" / "channel_scan.py" for r in roots
             if (r / "scinance3-impl" / "tools" / "channel_scan.py").exists()]
    if not found:
        pytest.skip("channel_scan.py is not part of this tree")
    scan = found[0]
    f = tmp_path / "out.json"
    f.write_text(common.dumps_canonical(factor3_output), encoding="ascii")
    res = subprocess.run([sys.executable, "-I", str(scan), str(f)], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0 and "nesting groups flagged: 0" in res.stdout


def _compare_blocks(a: dict[str, Any], b: dict[str, Any], keys: list[str], rel: float = 1e-8):
    for key in keys:
        x, y = a, b
        for part in key.split("/"):
            x, y = x[part], y[part]
        assert x == pytest.approx(y, rel=rel, abs=1e-10), key


def _moment_paths() -> list[str]:
    paths = []
    for mat in ("r_daily", "e_market_resid"):
        for cls in ("all", "t1_low", "t2_mid", "t3_high"):
            for stat in ("excess_kurtosis", "skewness"):
                paths += [f"ik04/moments/{mat}/{cls}/{stat}/{q}" for q in ("q10", "q25", "q50", "q75", "q90")]
    return paths


def _spectrum_paths() -> list[str]:
    paths = []
    for kind in ("pearson", "spearman"):
        for base in ("residual", "raw"):
            paths += [f"ik05/full/{kind}/{base}/top_eigenvalues", f"ik05/full/{kind}/{base}/n_above_edge",
                      f"ik05/full/{kind}/{base}/explained_share_above_edge"]
    return paths


def _get(out, path):
    node = out
    for part in path.split("/"):
        node = node[part]
    return node


def test_outputs_do_not_depend_on_the_location_of_returns():
    """Adding a constant drift per symbol (a different mean of every return series) leaves every moment of shape and
    every eigenvalue unchanged: the output carries no information about the mean of a return."""
    base = factor_returns(1, n_days=500, n_sym=40)
    drift = np.random.default_rng(99).uniform(-0.004, 0.004, size=40)
    a = run.build_output(make_panel(base))
    b = run.build_output(make_panel(base + drift[None, :]))
    for p in _moment_paths() + _spectrum_paths():
        va, vb = _get(a, p), _get(b, p)
        if isinstance(va, list):
            assert np.allclose(va, vb, rtol=1e-7, atol=1e-9), p
        else:
            assert va == pytest.approx(vb, rel=1e-7, abs=1e-9), p
    a_abs = a["ik04"]["abs_r_market"]["acf"]["1"]                      # |r_M| does depend on the mean (not compared)
    assert np.isfinite(a_abs)


def test_dispersion_does_not_depend_on_a_common_drift():
    base = factor_returns(1, n_days=400, n_sym=30)
    a = run.build_output(make_panel(base))["ik04"]["xs_dispersion"]
    b = run.build_output(make_panel(base + 0.01))["ik04"]["xs_dispersion"]       # +1 % every day, every symbol
    for q in ("q10", "q50", "q90"):
        assert a["quantiles"][q] == pytest.approx(b["quantiles"][q], rel=1e-7)
    assert a["level_over_days"] == pytest.approx(b["level_over_days"], rel=1e-7)


def test_outputs_do_not_depend_on_the_sign_of_returns():
    """Negating every return (price inversion) leaves eigenvalues, kurtosis, dispersion and the autocorrelations of
    absolute values unchanged; only the skewness quantiles flip (the specification asks for skewness)."""
    base = factor_returns(1, n_days=500, n_sym=40) ** 3 * 20.0                   # skewed, heavy tailed
    a = run.build_output(make_panel(base))
    b = run.build_output(make_panel(-base))
    for p in _spectrum_paths() + [p for p in _moment_paths() if "excess_kurtosis" in p]:
        va, vb = _get(a, p), _get(b, p)
        assert np.allclose(va, vb, rtol=1e-6, atol=1e-9), p
    for p in ("ik04/xs_dispersion/quantiles/q50", "ik04/xs_dispersion/acf/1", "ik04/abs_r_market/acf/1",
              "ik04/abs_r_market/n_eff_365", "ik04/abs_r_symbol_acf/1/q50", "ik04/missing_days/share/q50"):
        assert _get(a, p) == pytest.approx(_get(b, p), rel=1e-6, abs=1e-9), p
    assert _get(a, "ik04/moments/r_daily/all/skewness/q50") == pytest.approx(
        -_get(b, "ik04/moments/r_daily/all/skewness/q50"), rel=1e-6)


# ----------------------------------------------------------------------------
# (h) exclusions, determinism, command line, hygiene
# ----------------------------------------------------------------------------

def test_symbols_with_few_days_are_excluded_and_counted():
    ret = 0.02 * np.random.default_rng(17).standard_normal((400, 25))
    missing = np.zeros((401, 25), dtype=bool)
    missing[:300, 24] = True                                  # symbol 24 lives 101 days only
    out = run.build_output(make_panel(ret, missing=missing), min_days=250)
    assert out["inputs"]["n_symbols_loaded"] == 25 and out["inputs"]["n_symbols_excluded_min_days"] == 1
    assert out["inputs"]["n_symbols_analysed"] == 24 and out["ik05"]["full"]["k_symbols"] == 24
    assert out["ik04"]["moments"]["r_daily"]["all"]["n_symbols"] == 24
    assert out["params"]["min_days"] == 250
    out2 = run.build_output(make_panel(ret, missing=missing), min_days=100)
    assert out2["inputs"]["n_symbols_excluded_min_days"] == 0 and out2["inputs"]["n_symbols_analysed"] == 25
    assert out2["ik04"]["missing_days"]["n_symbols_with_gaps"] == 0


def test_too_few_symbols_is_a_loud_failure():
    ret = 0.02 * np.random.default_rng(3).standard_normal((300, 6))
    with pytest.raises(common.PanelError, match="symbol"):
        run.build_output(make_panel(ret))


def test_tercile_classes_partition_the_symbols(factor3_output):
    m = factor3_output["ik04"]["moments"]["r_daily"]
    assert [m[c]["n_symbols"] for c in ("t1_low", "t2_mid", "t3_high")] == [20, 20, 20] and m["all"]["n_symbols"] == 60
    assert factor3_output["ik04"]["n_symbols_without_turnover"] == 0


def test_two_runs_are_byte_identical():
    ret = factor_returns(3, n_days=600, n_sym=60, seed=5)
    a = common.dumps_canonical(run.build_output(make_panel(ret)))
    b = common.dumps_canonical(run.build_output(make_panel(ret)))
    assert a == b and hashlib.sha256(a.encode()).hexdigest() == hashlib.sha256(b.encode()).hexdigest()
    assert a.isascii() and json.loads(a)["zone"] == "X"


def _loader_for(panel: common.Panel, calls: list):
    def loader(start, end, *, client_dir=None, cache_dir=None):
        calls.append((start, end, client_dir, cache_dir))
        return panel, {"n_load_warnings": 0, "load_warnings": []}
    return loader


def test_cli_writes_a_valid_output_twice_identically(tmp_path):
    panel = make_panel(factor_returns(1, n_days=500, n_sym=40))
    calls: list = []
    outs = []
    for i in range(2):
        out = tmp_path / f"run{i}.json"
        argv = ["--out", str(out), "--min-days", "250", "--client-dir", "/some/dir", "--cache-dir", "/some/cache"]
        rc = run.main(argv, panel_loader=_loader_for(panel, calls))
        assert rc == 0
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]
    assert calls[0] == ("2021-01-01", "2024-06-30", "/some/dir", "/some/cache")
    data = json.loads(outs[0])
    common.validate_output(data)
    assert data["zone"] == "X" and data["params"]["min_days"] == 250


def test_cli_refuses_windows_outside_zone_x_before_loading(tmp_path):
    panel = make_panel(factor_returns(0, n_days=300, n_sym=20))
    for args in (["--end", "2024-07-01"], ["--start", "2020-12-31"], ["--start", "2024-07-01", "--end", "2024-07-31"],
                 ["--start", "2022-01-02", "--end", "2022-01-01"]):
        calls: list = []
        out = tmp_path / "never.json"
        rc = run.main(["--out", str(out), *args], panel_loader=_loader_for(panel, calls))
        assert rc == 2 and not calls and not out.exists(), args


def test_cli_refuses_unsafe_outputs(tmp_path):
    panel = make_panel(factor_returns(0, n_days=300, n_sym=20))
    calls: list = []
    bad = [tmp_path / "data" / "harvest" / "x.json", tmp_path / "weekly_ic_series.csv",
           tmp_path / "foo_L_window_sealed.json", tmp_path / "ic_series_w2_UNION_REAL.csv"]
    for path in bad:
        assert run.main(["--out", str(path)], panel_loader=_loader_for(panel, calls)) == 1
        assert not path.exists()
    exists = tmp_path / "exists.json"
    exists.write_text("{}")
    assert run.main(["--out", str(exists)], panel_loader=_loader_for(panel, calls)) == 1
    assert exists.read_text() == "{}" and not calls                          # never overwritten, loader never called


def test_cli_reports_loader_failures_with_a_nonzero_exit(tmp_path):
    def failing(start, end, *, client_dir=None, cache_dir=None):
        raise common.HarvestClientError("no client")
    assert run.main(["--out", str(tmp_path / "o.json")], panel_loader=failing) == 1
    assert not (tmp_path / "o.json").exists()


def test_sources_are_ascii_and_free_of_hosts_credentials_and_model_names():
    bad_fragments = ["://", "amazonaws", "secret_key", "access_key", "HARVEST_S3", "api_key", "password",
                     "cla" + "ude", "fab" + "le", "op" + "us", "son" + "net", "hai" + "ku", "g" + "pt",
                     "anthr" + "opic"]
    for path in sorted(ZONE_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert text.isascii(), path.name
        low = text.lower()
        for frag in bad_fragments:
            assert frag.lower() not in low, (path.name, frag)
    assert "data/harvest" not in "".join(p.read_text() for p in ZONE_DIR.glob("ik0*.py"))


def test_modules_use_no_random_numbers():
    src = "".join(p.read_text() for p in ZONE_DIR.glob("*.py"))
    for needle in ("default_rng", "np.random", "import random", "RandomState", "permutation(", "shuffle("):
        assert needle not in src, needle                                          # the measurements are deterministic
