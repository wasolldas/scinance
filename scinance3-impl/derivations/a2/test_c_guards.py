"""T0 tests of part C (synthetic returns only - the real contrast is never formed, R-C6).

Run: python3 -m pytest -q test_c_guards.py   (or python3 test_c_guards.py)
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402


def _window(lo="2021-03-24", hi="2021-06-30"):
    days = [d for d in cc.days_range(lo, hi) if d.weekday() <= 4]          # Mon-Fri (E u P2'' in the pre-period)
    ev = np.array([d.weekday() == 4 for d in days])
    return days, ev


def _real_labels(pn: cc.PermNull) -> np.ndarray:
    return np.array([d.weekday() == 4 for d in pn.days], dtype=np.uint8)


def test_real_label_row_is_refused_before_returns_are_touched():
    days, ev = _window()
    pn = cc.PermNull(days, ev)
    L = _real_labels(pn)[None, :]
    try:
        pn.centred_replicates(None, L)            # x=None: a guard that came AFTER touching x would raise TypeError
    except cc.RealLabelError:
        pass
    else:
        raise AssertionError("real label row accepted")


def test_real_row_hidden_among_permuted_rows_is_refused():
    days, ev = _window()
    pn = cc.PermNull(days, ev)
    L = pn.draw_labels(50, seed=1)
    L[17] = _real_labels(pn)
    try:
        pn.centred_replicates(np.random.default_rng(0).normal(size=pn.n), L)
    except cc.RealLabelError:
        pass
    else:
        raise AssertionError("real row among permuted rows accepted")


def test_permuted_rows_pass_and_count_is_preserved():
    days, ev = _window()
    pn = cc.PermNull(days, ev)
    L = pn.draw_labels(200, seed=2)
    assert np.all(L.sum(axis=1) == pn.W)
    v = pn.centred_replicates(np.random.default_rng(1).normal(size=pn.n), L)
    assert v.shape == (200,) and np.all(np.isfinite(v))


def test_malformed_rows_are_refused():
    days, ev = _window()
    pn = cc.PermNull(days, ev)
    L = pn.draw_labels(5, seed=3)
    bad = L.copy()
    w = pn.perm_weeks[0]
    bad[0, pn.idx_of_week[w]] = 1                    # two or more labels in one week
    for M in (bad, L[:, :-1], L * 2):
        try:
            pn.check_labels(M)
        except cc.RealLabelError:
            continue
        raise AssertionError("malformed label matrix accepted")


def test_event_set_must_be_the_fridays():
    days, ev = _window()
    ev2 = ev.copy()
    ev2[0] = not ev2[0]
    try:
        cc.PermNull(days, ev2)
    except ValueError:
        return
    raise AssertionError("non-Friday event set accepted")


def test_exact_sd_matches_monte_carlo_and_null_is_centred():
    days, ev = _window("2021-03-24", "2022-03-31")
    pn = cc.PermNull(days, ev)
    x = np.random.default_rng(5).standard_t(5, size=pn.n) * 40.0
    v = pn.centred_replicates(x, pn.draw_labels(40_000, seed=4))
    ex = pn.exact_cumulants(x)
    assert abs(v.std(ddof=1) / ex["sd"] - 1.0) < 0.02
    assert abs(v.mean()) < 4.0 * ex["sd"] / np.sqrt(v.size)      # centred by construction (synthetic data)


def test_label_invariance_of_the_null_distribution():
    """Swapping which day of a week is the 'Friday' value leaves the exact null unchanged (synthetic)."""
    days, ev = _window()
    pn = cc.PermNull(days, ev)
    x = np.random.default_rng(6).normal(size=pn.n)
    y = x.copy()
    for w in pn.perm_weeks:
        ids = pn.idx_of_week[w]
        y[ids] = np.random.default_rng(int(w)).permutation(x[ids])
    a, b = pn.exact_cumulants(x), pn.exact_cumulants(y)
    assert abs(a["sd"] - b["sd"]) < 1e-12 and abs(a["excess_kurtosis"] - b["excess_kurtosis"]) < 1e-9


def test_p3_identity_on_synthetic_data():
    """R-C6: T_P3(J) - E = N_P/(N_P+W) (T_P2(J) - E), replicate by replicate (raw contrasts on SYNTHETIC data)."""
    days, ev = _window()
    rng = np.random.default_rng(7)
    x = rng.normal(size=len(days)) * 40 + 3.0
    y3 = rng.normal(size=len(days)) * 55 - 2.0                    # a P3 placebo series, fixed set
    pn = cc.PermNull(days, ev)
    L = pn.draw_labels(300, seed=8).astype(float)
    t2 = (L @ x) / pn.W - ((1 - L) @ x) / pn.N_P
    t3 = (L @ x) / pn.W - y3.mean()
    real = _real_labels(pn).astype(float)
    # exact permutation expectations (synthetic data - allowed in a test)
    def e_perm(stat):
        acc = 0.0
        tot = 0
        # enumerate is too large; use the linearity: E[L_d] = 1/n_w in permutable weeks
        p = np.zeros(pn.n)
        for w in pn.perm_weeks:
            p[pn.idx_of_week[w]] = 1.0 / len(pn.idx_of_week[w])
        for w in pn.fixed_event_weeks:
            p[pn.idx_of_week[w]] = 1.0
        return stat(p)
    e2 = e_perm(lambda p: (p @ x) / pn.W - ((1 - p) @ x) / pn.N_P)
    e3 = e_perm(lambda p: (p @ x) / pn.W - y3.mean())
    f = pn.N_P / (pn.N_P + pn.W)
    assert np.allclose(t3 - e3, f * (t2 - e2), atol=1e-9)
    assert np.allclose(pn.centred_replicates(x, L.astype(np.uint8)), t2 - e2, atol=1e-9)
    del real


def test_key_guard():
    for bad in ("mean", "x_mean", "median", "q50", "sign", "vorzeichen", "null_centre", "delta", "observed"):
        try:
            cc.guard_keys({"a": {bad: 1.0}})
        except ValueError:
            continue
        raise AssertionError(f"key {bad} accepted")
    cc.guard_keys({"null_sd": 1.0, "d95_reg": 1.0, "se_bind": 1.0, "block": 1, "design": 2})


def test_kline_date_assert_refuses_days_after_2024_05_31():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "k.parquet"
        ms = int(datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        ms0 = int(datetime(2021, 3, 24, tzinfo=timezone.utc).timestamp() * 1000)
        pq.write_table(pa.table({"symbol": ["BTCUSDT", "ETHUSDT"], "start_ms": [ms0, ms],
                                 "close": [1.0, 1.0]}), p)
        try:
            cc.assert_kline_dates(p)
        except RuntimeError:
            return
        raise AssertionError("kline day after 2024-05-31 accepted")


def test_calendar_rules():
    assert cc.cal_class(date(2024, 5, 31)) == "FRI_M"
    assert cc.cal_class(date(2024, 6, 28)) == "FRI_Q"
    assert cc.cal_class(date(2024, 6, 21)) == "FRI_W"
    assert cc.cal_class(date(2024, 6, 20)) == "MODO"
    assert cc.cal_class(date(2024, 6, 22)) == "WE"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
    print(f"tests passed: {n}")


# ------------------------------------------------------------------------------------------------ Fassung 2 (A-1)
def _synthetic_kline(path: Path, seed: int = 2026) -> None:
    """Synthetic 1-min closes for BTCUSDT/ETHUSDT on the pre-period grid (random walk, t noise) - no real data."""
    days = cc.days_range(cc.FIRST_RETURN_DAY, cc.LAST_RETURN_DAY)
    n = len(days) * 1440
    rng = np.random.default_rng(seed)
    base = int(datetime(2021, 3, 24, tzinfo=timezone.utc).timestamp() * 1000)
    ms = base + 60000 * np.arange(n, dtype=np.int64)
    cols = {"symbol": [], "start_ms": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "turnover": []}
    tabs = []
    for s, p0 in (("BTCUSDT", 50000.0), ("ETHUSDT", 3000.0)):
        r = rng.standard_t(5, size=n) * 0.0007
        # a planted Friday-07:30 location so that a reconstructed |contrast| is non-trivial (synthetic only)
        c = p0 * np.exp(np.cumsum(r))
        tabs.append(pa.table({"symbol": [s] * n, "start_ms": ms, "open": c, "high": c, "low": c, "close": c,
                              "volume": np.ones(n), "turnover": np.ones(n)}))
    pq.write_table(pa.concat_tables(tabs), path)
    del cols


def test_channel_scan_on_synthetic_run_and_positive_control():
    """R-C12a / A-1: the pre-period output built on SYNTHETIC returns has no (n, sd) triple of the same series with
    n_k = n_i + n_j; adding the union SD (the Fassung-1 channel) is detected, and on synthetic data the variance
    decomposition indeed recovers |contrast| from such a triple."""
    import c1_nullsim as c1
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "kline.parquet"
        _synthetic_kline(p)
        old = cc.F_KLINE
        cc.F_KLINE = p
        try:
            out = c1.main(pre_only=True)
        finally:
            cc.F_KLINE = old
    rep = cc.scan_variance_channels(out)
    assert rep["violations"] == [], rep["violations"][:2]
    assert rep["class_entries"] >= 16
    assert all(c["series"] != ["r_pre"] for c in rep["count_coincidences_different_series"])
    # positive control: plant the Fassung-1 union field as a class entry and recover |Delta| on synthetic numbers
    rng = np.random.default_rng(3)
    xe, xp = rng.normal(1.5, 40, 52), rng.normal(0.0, 42, 209)
    u = np.concatenate([xe, xp])
    blk = {"E": {"series": "r_pre", "n": 52, "sd": float(np.std(xe, ddof=1))},
           "P2ss": {"series": "r_pre", "n": 209, "sd": float(np.std(xp, ddof=1))},
           "U": {"series": "r_pre", "n": 261, "sd": float(np.std(u, ddof=1))}}
    rep2 = cc.scan_variance_channels({"blk": blk})
    assert len(rep2["violations"]) == 1 and rep2["violations"][0]["parent"].endswith("U")
    ss = lambda e: (e["n"] - 1) * e["sd"] ** 2  # noqa: E731
    d2 = (ss(blk["U"]) - ss(blk["E"]) - ss(blk["P2ss"])) * 261 / (52 * 209)
    assert abs(np.sqrt(d2) - abs(xe.mean() - xp.mean())) < 1e-9       # the channel is real (synthetic check)
    try:
        cc.assert_no_variance_channel({"blk": blk})
    except ValueError:
        pass
    else:
        raise AssertionError("union SD not refused")


def test_scaled_null_power_reduces_to_tau_condition():
    """R-C13: with k = SE / SD_null the scaled null condition is Phi(kappa pi / SE - tau)."""
    import c1_nullsim as c1
    se, sdn, tau, kap = 7.34, 6.70, 1.6553, 0.999
    nul = {"sd": sdn, "d95": tau * sdn, "kappa": kap, "k": se / sdn}
    for pi in (10.0, 20.0, 30.0):
        a = c1.null_power(pi, nul, "scaled")
        b = c1._N.cdf(kap * pi / se - tau)
        assert abs(a - b) < 1e-12
