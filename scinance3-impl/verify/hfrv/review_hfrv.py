"""Independent re-computation of the HF-RV nuisance (Option 3, DEC-98) for the adversarial review.

Written from scratch (no import of the derivation agent's code).  Programme code used: only
``bybit_edge.research.power_p1`` (DEC-94 (8): every power / MDE / regime number goes through it).

Blindness (same seals as the derivation):
  * kline extracts: the timestamp range is asserted from the parquet row-group statistics BEFORE any
    price column is read, and again on the loaded column (no UTC day > 2024-05-31);
  * IV days t in [2021-03-24, 2024-05-01] only; DVOL values of later days are never parsed;
  * the premium P = IV - RV_fwd30 exists only in memory; outputs are SD, ACF, variance factors,
    ratios, correlations, RV levels (rms) and power rows -- never a mean, median or sign of P or of
    DVOL (guard ``guard`` on the whole output dict before writing).
Run: python3 -I review_hfrv.py   (writes review_hfrv.json next to this file)
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "hf_data" / "raw"
KL = {"BTC": RAW / "bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet",
      "ETH": RAW / "bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet"}
DV = RAW / "deribit_dvol_raw_2021-03-24_2024-05-31.parquet"
FJ = Path("/home/user/scinance/scinance3-impl/state/herleitung_h27/feasibility.json")
LAST_PRICE_DAY = date(2024, 5, 31)
IV_LO, IV_HI = date(2021, 3, 24), date(2024, 5, 1)
DAY_MS, MIN_MS = 86_400_000, 60_000
SEED = 27
VARS = ("v1_1min", "v2_5min", "v3_5min_sub", "v4_15min", "v5_30min", "v6_cc")

_BAD = re.compile(r"mean|avg|median|sign|vorzeichen|mittel", re.I)


def guard(o, path=""):
    """Refuse any key that could carry a mean / median / sign (of anything)."""
    if isinstance(o, dict):
        for k, v in o.items():
            if _BAD.search(str(k)):
                raise RuntimeError(f"review guard: key {path}/{k} refused")
            guard(v, f"{path}/{k}")
    elif isinstance(o, (list, tuple)):
        for v in o:
            guard(v, path)
    return o


# ---------------------------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------------------------

def assert_kline_range(path: Path) -> None:
    pf = pq.ParquetFile(path)
    i = pf.schema_arrow.names.index("start_ms")
    mx = max(pf.metadata.row_group(r).column(i).statistics.max for r in range(pf.metadata.num_row_groups))
    last = datetime.fromtimestamp(mx / 1000, tz=timezone.utc).date()
    assert last <= LAST_PRICE_DAY, f"{path.name}: day {last} > {LAST_PRICE_DAY} (metadata)"


def load_logclose(sym: str):
    """(days, logclose[n_days, 1440]) on full UTC days; asserts range before reading closes."""
    assert_kline_range(KL[sym])
    ms = pq.read_table(KL[sym], columns=["start_ms"]).column(0).to_numpy().astype(np.int64)
    assert datetime.fromtimestamp(ms.max() / 1000, tz=timezone.utc).date() <= LAST_PRICE_DAY
    assert np.all(ms % MIN_MS == 0), "start_ms off the full minute"
    t = pq.read_table(KL[sym], columns=["start_ms", "close", "symbol"])
    ms = t.column("start_ms").to_numpy().astype(np.int64)
    cl = t.column("close").to_numpy().astype(np.float64)
    syms = set(t.column("symbol").to_pylist())
    order = np.argsort(ms, kind="stable")
    ms, cl = ms[order], cl[order]
    dup = int(np.sum(np.diff(ms) == 0))
    d_abs = ms // DAY_MS
    d0, d1 = int(d_abs.min()), int(d_abs.max())
    nd = d1 - d0 + 1
    grid = np.full((nd, 1440), np.nan)
    grid[d_abs - d0, (ms % DAY_MS) // MIN_MS] = cl
    rows = np.isfinite(grid).sum(axis=1)
    days = [date(1970, 1, 1) + timedelta(days=d0 + i) for i in range(nd)]
    meta = {"symbols": sorted(syms), "rows": int(ms.size), "dup_start_ms": dup, "n_days": nd,
            "first_day": days[0].isoformat(), "last_day": days[-1].isoformat(),
            "days_not_1440": int(np.sum(rows != 1440)), "nonpositive_close": int(np.sum(cl <= 0))}
    assert days[-1] <= LAST_PRICE_DAY
    with np.errstate(divide="ignore", invalid="ignore"):
        lg = np.log(grid)
    lg[rows != 1440] = np.nan          # incomplete day -> whole day missing (never filled)
    return days, lg, meta


def one_min_returns(lg: np.ndarray) -> np.ndarray:
    """r[d, j] = log return over minute boundary j -> j+1 (j = 0..1439); j = 0 uses the 23:59 close
    of day d-1 as the 00:00 price.  Row 0 (no anchor) is NaN."""
    r = np.full(lg.shape, np.nan)
    r[:, 1:] = np.diff(lg, axis=1)
    r[1:, 0] = lg[1:, 0] - lg[:-1, 1439]
    r[0, :] = np.nan
    bad = ~np.all(np.isfinite(r), axis=1)
    r[bad] = np.nan
    return r


def block_rv(r: np.ndarray, step: int, phase: int) -> np.ndarray:
    """RV from block sums of 1-min returns; blocks [0, phase), [phase, phase+step), ..., [.., 1440)."""
    cs = np.concatenate([np.zeros((r.shape[0], 1)), np.cumsum(r, axis=1)], axis=1)  # cs[:, j] = sum_{i<j}
    b = sorted(set([0] + list(range(phase, 1440, step)) + [1440]))
    seg = np.diff(cs[:, b], axis=1)
    return np.sum(seg * seg, axis=1)


def rv_variants(r: np.ndarray) -> dict:
    out = {"v1_1min": np.sum(r * r, axis=1),
           "v2_5min": block_rv(r, 5, 0),
           "v3_5min_sub": np.mean([block_rv(r, 5, p) for p in range(5)], axis=0),
           "v4_15min": block_rv(r, 15, 0),
           "v5_30min": block_rv(r, 30, 0),
           "v6_cc": np.sum(r, axis=1) ** 2}
    return out


def rv30_series(rv_day: np.ndarray, days: list, t_days: list) -> np.ndarray:
    """sqrt(365/30 * sum_{k=1..30} RV(t+k)) via cumulative sums; NaN if a day is missing."""
    idx = {d: i for i, d in enumerate(days)}
    ok = np.isfinite(rv_day)
    cs = np.concatenate([[0.0], np.cumsum(np.where(ok, rv_day, 0.0))])
    cn = np.concatenate([[0], np.cumsum(ok)])
    out = np.full(len(t_days), np.nan)
    for j, t in enumerate(t_days):
        i = idx[t]
        lo, hi = i + 1, i + 31                     # days t+1 .. t+30
        assert days[hi - 1] <= LAST_PRICE_DAY
        if cn[hi] - cn[lo] == 30:
            out[j] = math.sqrt(365.0 / 30.0 * (cs[hi] - cs[lo]))
    return out


def load_iv() -> tuple[dict, dict]:
    t = pq.read_table(DV, columns=["symbol", "ts_exchange_ms", "payload_json"])
    iv = {"BTC": {}, "ETH": {}}
    n23 = {"BTC": 0, "ETH": 0}
    ts_mismatch = 0
    for s, ts, pj in zip(t.column("symbol").to_pylist(), t.column("ts_exchange_ms").to_pylist(),
                         t.column("payload_json").to_pylist()):
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        if dt.hour != 23 or dt.minute != 0:
            continue
        d = dt.date()
        if not (IV_LO <= d <= IV_HI):          # later DVOL values are never parsed
            continue
        o = json.loads(pj)
        if int(o["timestamp"]) != int(ts):
            ts_mismatch += 1
        if d in iv[s]:
            raise RuntimeError("duplicate 23h candle")
        iv[s][d] = float(o["close"]) / 100.0
        n23[s] += 1
    return iv, {"n_iv_days": n23, "ts_payload_mismatch_23h": ts_mismatch}


# ---------------------------------------------------------------------------------------------
# statistics (own implementations; power_p1 only where named)
# ---------------------------------------------------------------------------------------------

def acf_vec(x: np.ndarray, kmax: int) -> np.ndarray:
    d = x - x.mean()
    g0 = float(d @ d)
    return np.array([1.0] + [float(d[k:] @ d[:-k]) / g0 for k in range(1, kmax + 1)])


def bartlett(x: np.ndarray, B: int) -> float:
    rho = acf_vec(x, B)
    w = 1.0 - np.arange(1, B + 1) / (B + 1.0)
    return float(1.0 + 2.0 * np.sum(w * rho[1:]))


def batch_means(x: np.ndarray, L: int, align: str = "head") -> float:
    m = x.size // L
    seg = x[: m * L] if align == "head" else x[x.size - m * L:]
    bm = seg.reshape(m, L).mean(axis=1)
    return float(L * bm.var(ddof=1) / x.var(ddof=1))


def tapered_c(x: np.ndarray) -> float:
    rho = acf_vec(x, 90)
    k = np.arange(91)
    w = np.where(k <= 60, 1.0, 0.5 * (1.0 + np.cos(np.pi * (k - 60) / 30.0)))
    return float(1.0 + 2.0 * np.sum((rho * w)[1:]))


def stats_block(x: np.ndarray, boot: bool) -> dict:
    assert np.all(np.isfinite(x)), "gap in premium series"
    n = x.size
    rho = acf_vec(x, 180)
    bart = {B: bartlett(x, B) for B in (60, 90, 120, 180)}
    bart_pp = {B: pp.variance_factor(x, B).c_hat for B in (60, 90, 120)}
    bm = {L: batch_means(x, L) for L in (60, 90, 120, 180)}
    bm_tail = {L: batch_means(x, L, "tail") for L in (60, 90, 120)}
    cand = [bart[60], bart[90], bart[120], bm[60], bm[90], bm[120]]
    rule180 = bool(rho[120] > 0.10)
    if rule180:
        cand += [bart[180], bm[180]]
    out = {"n": n, "sd": float(x.std(ddof=1)),
           "acf": {str(k): float(rho[k]) for k in (1, 10, 20, 30, 60, 120, 180)},
           "first_lag_below_0_10": int(np.argmax(rho[1:] < 0.10) + 1),
           "c_bartlett": {str(k): v for k, v in bart.items()},
           "c_bartlett_power_p1": {str(k): v for k, v in bart_pp.items()},
           "c_bm_head": {str(k): v for k, v in bm.items()},
           "c_bm_tail_alignment": {str(k): v for k, v in bm_tail.items()},
           "rule180_triggered": rule180,
           "c_rule_P3": float(max(1.0, *cand)),
           "c_rule_P3_argmax": ["B60", "B90", "B120", "BM60", "BM90", "BM120", "B180", "BM180"][int(np.argmax(cand))],
           "c_rule_P3_with_tail_aligned_BM": float(max(1.0, bart[60], bart[90], bart[120], *bm_tail.values())),
           "c_consensus_tapered": tapered_c(x),
           "excess_kurtosis": float(np.mean((x - x.mean()) ** 4) / x.var() ** 2 - 3.0)}
    if boot:
        v = x.var(ddof=1)
        out["c_stat_bootstrap"] = {str(mb): float(n * pp.stationary_bootstrap_se(x, float(mb), 2000, seed=SEED) ** 2 / v)
                                   for mb in (30, 60, 90)}
    return out


def kappa(x: np.ndarray) -> float:
    vals = []
    for L in (2, 3, 5):
        vals.append(float(np.mean(x * x) / np.mean(x[L:] * x[:-L])))
    return float(np.mean(vals))


# ---------------------------------------------------------------------------------------------
# power (power_p1)
# ---------------------------------------------------------------------------------------------

SE0, N0 = None, 365


def se_of(n: float, sd: float, c: float, se_null365: float | None) -> float:
    s = sd * math.sqrt(c / n)
    if se_null365 is not None:
        s = max(s, se_null365 * math.sqrt(365.0 / n))
    return s


def smallest_n(pred, lo=1.0, hi=1e6) -> float | None:
    if not pred(hi):
        return None
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if pred(mid):
            hi = mid
        else:
            lo = mid
        if hi / lo - 1 < 1e-12:
            break
    return hi


def days_block(prior: float, sd: float, c: float, se_null365: float | None) -> dict:
    f = lambda n: se_of(n, sd, c, se_null365)  # noqa: E731
    c10 = smallest_n(lambda n: pp.assign_regime([prior, prior], [f(n), f(n)])["regime"] == pp.REGIME_C10)
    a3 = smallest_n(lambda n: pp.assign_regime_a3_practice([prior, prior], [f(n), f(n)])["regime"] == pp.REGIME_C10)
    g52 = smallest_n(lambda n: pp.dec52_gate_power([prior, prior], [f(n), f(n)])["power_product"] >= 0.8 - 1e-12)

    def full(n):
        if n is None:
            return None
        k = int(math.ceil(n - 1e-9))
        return (date(2026, 7, 1) + timedelta(days=2 * k - 1 + 30)).isoformat()
    return {"c10_p1": c10, "dec52_gate_p1": g52, "c10_a3": a3,
            "closed_c10_p1": c * (pp.mde_factor(0.05) * sd / prior) ** 2,
            "full_c10_p1": full(c10), "full_dec52_p1": full(g52), "full_c10_a3": full(a3)}


def window_row(prior: float, sd: float, c: float, se_null365: float, n: int) -> dict:
    se = se_of(n, sd, c, se_null365)
    r = pp.assign_regime([prior, prior], [se, se])
    a = pp.assign_regime_a3_practice([prior, prior], [se, se])
    return {"se": se, "se_nuis": sd * math.sqrt(c / n), "power_p1": r["window_power"][0],
            "regime_p1": r["regime"], "regime_a3": a["regime"], "power_a3": a["window_power"][0],
            "gate_product_p1": r["gate_power_product"], "only_dec94": a["zugelassen_nur_durch_dec94"]}


# ---------------------------------------------------------------------------------------------

def main() -> None:
    fj = json.loads(FJ.read_text())
    se_null365 = fj["nullwelt"]["BTC"]["windows"]["365"]["S1"]["se_null_at_ref"]
    priors = fj["power"]["configs"]["BTC/S1"]["priors"]
    sig_cc_h27 = fj["nuisance"]["rv_level_BTC"]["sigma_n_rms"]
    out: dict = {"label": "Review HF-RV: nur Streuung/ACF/c/Verhaeltnisse/RV-rms; kein Praemien- oder DVOL-Mittel, kein Vorzeichen",
                 "inputs": {"se_null365_BTC_S1": se_null365, "priors_BTC_S1": priors}}
    t_days = [IV_LO + timedelta(days=i) for i in range((IV_HI - IV_LO).days + 1)]
    iv, ivmeta = load_iv()
    out["iv_meta"] = ivmeta
    res: dict = {}
    prem_store: dict = {}
    for sym in ("BTC", "ETH"):
        days, lg, meta = load_logclose(sym)
        r = one_min_returns(lg)
        rvd = rv_variants(r)
        # per-phase 5-min RV (diagnostic of the grid phase)
        ph = {p: block_rv(r, 5, p) for p in range(5)}
        rv30 = {v: rv30_series(rvd[v], days, t_days) for v in VARS}
        ivs = np.array([iv[sym].get(t, np.nan) for t in t_days])
        assert np.all(np.isfinite(ivs)), "missing IV"
        rec: dict = {"meta": meta, "variants": {}}
        rms_cc = float(np.sqrt(np.mean(rv30["v6_cc"] ** 2)))
        rms_30 = float(np.sqrt(np.mean(rv30["v5_30min"] ** 2)))
        sel = np.array([d >= date(2021, 3, 25) for d in days])
        for v in VARS:
            x30 = rv30[v]
            assert np.all(np.isfinite(x30))
            P1 = 100.0 * (ivs - x30)
            P2 = 100.0 * (ivs ** 2 - x30 ** 2)
            P3 = np.log(ivs / x30)
            prem_store[(sym, v)] = P1
            rms = float(np.sqrt(np.mean(x30 ** 2)))
            vr = {"S1": stats_block(P1, boot=(sym == "BTC")),
                  "S2_sd": float(P2.std(ddof=1)), "S3_sd": float(P3.std(ddof=1)),
                  "S3_c_rule": stats_block(P3, boot=False)["c_rule_P3"],
                  "rms_rv30_pct": 100 * rms, "ratio_rms_cc": rms / rms_cc, "ratio_rms_30min": rms / rms_30,
                  "kappa_L235": kappa(rvd[v][sel])}
            vr["noise_sd_delta_volpts"] = 100 * math.sqrt(max(vr["kappa_L235"] - 1, 0) / 120) * rms
            if v != "v6_cc":
                D = 100.0 * (x30 - rv30["v6_cc"])
                vr["sd_D"] = float(D.std(ddof=1))
                vr["corr_D_P_v"] = float(np.corrcoef(D, P1)[0, 1])
                vr["corr_D_RV_v"] = float(np.corrcoef(D, x30)[0, 1])
            rec["variants"][v] = vr
        rec["phase_rms_rv30_ratio_to_cc"] = {str(p): float(np.sqrt(np.mean(rv30_series(ph[p], days, t_days) ** 2)) / rms_cc)
                                              for p in range(5)}
        # intraday return autocorrelation (diagnostic, returns only, <= 2024-05-31)
        rr = r[np.all(np.isfinite(r), axis=1)]
        rec["acf1_1min_returns"] = float(np.corrcoef(rr[:, 1:].ravel(), rr[:, :-1].ravel())[0, 1])
        r5 = np.add.reduceat(rr, np.arange(0, 1440, 5), axis=1)
        rec["acf1_5min_returns_phase0"] = float(np.corrcoef(r5[:, 1:].ravel(), r5[:, :-1].ravel())[0, 1])
        res[sym] = rec
    out["symbols"] = res
    # BTC/ETH correlation of S1 per variant
    out["corr_btc_eth_S1"] = {v: float(np.corrcoef(prem_store[("BTC", v)], prem_store[("ETH", v)])[0, 1]) for v in VARS}
    # power rows (BTC S1)
    pw: dict = {}
    for v in VARS:
        st = res["BTC"]["variants"][v]["S1"]
        sd = st["sd"]
        rows = {}
        for cname, c in (("c_rule", st["c_rule_P3"]), ("c_consensus", max(1.0, st["c_consensus_tapered"])),
                         ("c_review_18_6", 18.6)):
            rows[cname] = {"c": c,
                           "L12_n335": window_row(priors["pi2_central"], sd, c, se_null365, 335),
                           "L12_n365": window_row(priors["pi2_central"], sd, c, se_null365, 365),
                           "L12_n365_pi2_high": window_row(priors["pi2_high"], sd, c, se_null365, 365),
                           "days_pi2_central": days_block(priors["pi2_central"], sd, c, se_null365),
                           "days_pi2_7_14": days_block(7.14, sd, c, se_null365),
                           "days_pi2_3_16": days_block(3.16, sd, c, se_null365)}
        pw[v] = rows
    # Bilanz rows (assumption SD 15.1) and H-27 reference
    pw["bilanz_hf_15_1_c28_2"] = days_block(priors["pi2_central"], 15.1, 28.2, se_null365)
    pw["bilanz_hf_15_1_c18_6"] = days_block(priors["pi2_central"], 15.1, 18.6, se_null365)
    pw["h27_reference"] = days_block(priors["pi2_central"], fj["nuisance"]["BTC"]["S1"]["sd"],
                                     fj["nuisance"]["BTC"]["S1"]["c_bind"], se_null365)
    # prior readings at the HF level (report)
    lv = res["BTC"]["variants"]["v3_5min_sub"]["ratio_rms_cc"]
    pw["prior_readings_v3"] = {"pi2_at_hf_level": 100 * sig_cc_h27 * lv * (math.exp(0.1431) - 1),
                               "pi2_cc_literature_level_bias": 100 * sig_cc_h27 * (math.exp(0.1431) - lv)}
    out["power_BTC_S1"] = pw
    guard(out)
    (HERE / "review_hfrv.json").write_text(json.dumps(out, indent=1, default=str))
    print("WROTE review_hfrv.json")


if __name__ == "__main__":
    main()
