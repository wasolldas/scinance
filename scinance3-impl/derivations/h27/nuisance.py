"""H-27 nuisance (FEASIBILITY.md section 3, P-1..P-3; DEC-96 E2): dispersion and persistence of the
daily premium IV - RV_fwd30 on the pre-period 2021-03-24..2024-05-31 -- NEVER its mean.

Outputs per symbol (BTC, ETH) and leg (mean of both), units S1 (vol points), S2 (variance x 100),
S3 (log ratio): n, SD, ACF, variance factor c (Bartlett / batch means / stationary bootstrap,
binding rule P-3), monthly non-overlapping variant, cross-window correlation of adjacent window
means, BTC/ETH correlation; plus the RV level sigma_n (allowed: RV only, pre-period) used by P-7.
The output passes the ``no_mean`` guard; LABEL is attached.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/scinance/src")
from h27_common import LABEL, no_mean  # noqa: E402
from h27_series import premium_frame  # noqa: E402
from bybit_edge.research import power_p1  # noqa: E402

LAGS = [1, 5, 10, 20, 29, 30, 31, 45, 60, 90, 120, 150, 180]
BANDS = [30, 60, 90, 120, 180]
WINDOW_DAYS = [181, 184, 274, 275, 365, 366]
SEED = 27


def acf(x: np.ndarray, k: int) -> float:
    d = x - x.mean()
    return float(d[k:] @ d[:-k] / (d @ d))


def autocov(x: np.ndarray, kmax: int) -> np.ndarray:
    d = x - x.mean()
    n = d.size
    return np.array([float(d[k:] @ d[:n - k]) / n for k in range(kmax + 1)])


def batch_means_c(x: np.ndarray, L: int) -> float:
    m = x.size // L
    bm = x[: m * L].reshape(m, L).mean(axis=1)
    return float(L * np.var(bm, ddof=1) / np.var(x, ddof=1))


def contiguous(x: np.ndarray) -> np.ndarray:
    """Longest run without NaN (the estimators need a gap-free series)."""
    ok = np.isfinite(x)
    best, cur, start, bstart = 0, 0, 0, 0
    for i, v in enumerate(ok):
        if v:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bstart = cur, start
        else:
            cur = 0
    return x[bstart:bstart + best]


def adjacent_window_corr(x: np.ndarray, n: int, kmax: int = 180) -> float:
    """Corr(mean of block A, mean of adjacent block B), blocks of n days, autocovariances up to
    kmax (beyond set to 0)."""
    g = autocov(x, min(kmax, 2 * n - 1))
    cov = sum(min(k, 2 * n - k) * g[k] for k in range(1, g.size)) / n ** 2
    var = (n * g[0] + 2 * sum((n - k) * g[k] for k in range(1, min(n, g.size)))) / n ** 2
    return float(cov / var)


def monthly(x_full: np.ndarray) -> dict:
    """Non-overlapping 30-day sampling, all 30 phases; SD and ACF 1..3 averaged over phases."""
    sds, a1, a2, a3, ns = [], [], [], [], []
    for ph in range(30):
        s = x_full[ph::30]
        s = s[np.isfinite(s)]
        if s.size < 10:
            continue
        ns.append(s.size)
        sds.append(float(np.std(s, ddof=1)))
        a1.append(acf(s, 1)); a2.append(acf(s, 2)); a3.append(acf(s, 3))
    rho1 = float(np.mean(a1))
    sd_m = float(np.mean(sds))
    bart3 = 1 + 2 * sum((1 - k / 4) * r for k, r in zip((1, 2, 3), (np.mean(a1), np.mean(a2), np.mean(a3))))
    ar1 = (1 + rho1) / (1 - rho1)
    return {"n_per_phase": [min(ns), max(ns)], "sd_m": sd_m, "acf1": rho1,
            "acf2": float(np.mean(a2)), "acf3": float(np.mean(a3)),
            "c_bartlett3": float(bart3), "c_ar1": float(ar1),
            "c_bind_m": float(max(1.0, bart3, ar1))}


def describe(x_full: np.ndarray) -> dict:
    x = contiguous(x_full)
    n = x.size
    out: dict = {"n_finite": int(np.isfinite(x_full).sum()), "n_missing": int((~np.isfinite(x_full)).sum()),
                 "n_contiguous_used": int(n), "sd": float(np.std(x, ddof=1))}
    out["excess_kurtosis"] = float(((x - x.mean()) ** 4).mean() / np.var(x) ** 2 - 3.0)
    out["acf"] = {str(k): acf(x, k) for k in LAGS}
    below = [k for k in range(1, 361) if acf(x, k) < 0.10]
    out["first_lag_acf_below_0_10"] = below[0] if below else None
    out["c_bartlett"] = {str(b): power_p1.variance_factor(x, b).c_hat for b in BANDS}
    out["c_batch_means"] = {str(L): batch_means_c(x, L) for L in BANDS}
    sb = {}
    var = float(np.var(x, ddof=1))
    for mb in (30, 60, 90):
        se = power_p1.stationary_bootstrap_se(x, float(mb), 2000, seed=SEED)
        sb[str(mb)] = n * se * se / var
    out["c_stationary_bootstrap"] = sb
    cand = [out["c_bartlett"][str(b)] for b in (60, 90, 120)] + \
           [out["c_batch_means"][str(L)] for L in (60, 90, 120)]
    extended = out["acf"]["120"] > 0.10
    if extended:
        cand += [out["c_bartlett"]["180"], out["c_batch_means"]["180"]]
    out["c_rule"] = "max(1, Bartlett 60/90/120, BM 60/90/120)" + (" + 180 (ACF(120) > 0.10)" if extended else "")
    out["c_bind"] = float(max(1.0, *cand))
    out["adjacent_window_corr"] = {str(n_w): adjacent_window_corr(x, n_w) for n_w in WINDOW_DAYS}
    out["monthly"] = monthly(x_full)
    return out


def main() -> None:
    frames = {s: premium_frame(s) for s in ("BTC", "ETH")}
    res: dict = {"label": LABEL, "period_iv_days": "2021-03-24..2024-05-01",
                 "price_days": "<= 2024-05-31", "seed_bootstrap": SEED}
    for s, f in frames.items():
        rv = f["rv"][np.isfinite(f["rv"])]
        res[f"rv_level_{s}"] = {"sigma_n_rms": float(np.sqrt(np.mean(rv * rv))),
                                "n": int(rv.size)}
        res[s] = {u: describe(f[u]) for u in ("S1", "S2", "S3")}
    leg = {u: 0.5 * (frames["BTC"][u] + frames["ETH"][u]) for u in ("S1", "S2", "S3")}
    res["LEG_MEAN"] = {u: describe(leg[u]) for u in ("S1", "S2", "S3")}
    corr = {}
    for u in ("S1", "S2", "S3"):
        a, b = frames["BTC"][u], frames["ETH"][u]
        ok = np.isfinite(a) & np.isfinite(b)
        corr[u] = float(np.corrcoef(a[ok], b[ok])[0, 1])
    res["corr_btc_eth"] = corr
    no_mean(res)
    (HERE / "nuisance.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
