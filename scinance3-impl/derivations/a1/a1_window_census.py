"""A1 Stufe 1 -- FORMATION-SIDE census on W1/W2 (task rule 1: allowed after 2024-07-01).

Computes per judged formation week t of each window ONLY quantities that use data of week t or
earlier (key distribution, D1 degeneration, D1-minus-universe key spread in the formation week,
interval classes, K, PIT betas / idiosyncratic variances from TRAILING returns) plus the market
factor SDs of the window (allowed: "Faktor-SDs des Marktes") and the per-symbol time-series lag-1
autocorrelation of the key (Stufe 1 (b), the WP-7 estimator applied to the DEC-67 key: no sort,
no portfolio). No holding-week return, no holding-week funding of any sorted set is computed.
"""
from __future__ import annotations

import json
import pickle
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")

import numpy as np  # noqa: E402

import a1_common as C  # noqa: E402
import a1_model as M  # noqa: E402

K_MIN = 117  # PRD 5.1 Kill (3) / DEC-73 K_min


def q(x, ps=(0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return None
    return {f"q{int(p * 100):03d}": float(np.quantile(x, p)) for p in ps} | {"mean": float(x.mean()), "n": int(x.size)}


def ts_lag1_autocorr(key: np.ndarray, member: np.ndarray, min_weeks: int = 12) -> dict:
    """Per-symbol lag-1 autocorrelation of the key over consecutive weeks where the symbol is a
    member (WP-7 estimator: plain Pearson of (x_t, x_{t+1}) pairs), median over symbols with
    >= min_weeks member weeks. Also the pooled within-symbol estimate (pairs demeaned per symbol)."""
    n_w, n_s = key.shape
    vals, pooled_a, pooled_b = [], [], []
    for j in range(n_s):
        m = member[:, j]
        if m.sum() < min_weeks:
            continue
        pair = m[:-1] & m[1:]
        if pair.sum() < min_weeks - 1:
            continue
        a, b = key[:-1, j][pair], key[1:, j][pair]
        if a.std() == 0 or b.std() == 0:
            continue
        vals.append(float(np.corrcoef(a, b)[0, 1]))
        mu = key[m, j].mean()
        pooled_a.append(a - mu)
        pooled_b.append(b - mu)
    pa, pb = np.concatenate(pooled_a), np.concatenate(pooled_b)
    pooled = float(np.sum(pa * pb) / np.sqrt(np.sum(pa * pa) * np.sum(pb * pb)))
    return {"median_symbol_lag1": float(np.median(vals)), "q25": float(np.quantile(vals, 0.25)),
            "q75": float(np.quantile(vals, 0.75)), "n_symbols": len(vals), "pooled_within_lag1": pooled}


def buehlmann_straub(key: np.ndarray, member: np.ndarray, min_weeks: int = 12) -> dict:
    """One-way random-effects decomposition of the weekly key over member weeks of the window:
    s2 = pooled within-symbol variance (per week), a = between-symbol variance of the true means
    (method of moments, Buehlmann-Straub with weights = number of weeks), k = s2/a in WEEKS.
    PRD 11.4 / DEC-58 E1 (e): Kill-4 parameter 0.30 <=> z = w/(w+k) >= 0.30 <=> k <= 2.333 w;
    for the one-week key (w = 1) the criterion is k <= 2.333, z1 = 1/(1+k)."""
    xs, ws = [], []
    for j in range(key.shape[1]):
        m = member[:, j]
        if m.sum() < min_weeks:
            continue
        xs.append(key[m, j])
        ws.append(int(m.sum()))
    w = np.array(ws, dtype=float)
    means = np.array([x.mean() for x in xs])
    s2 = float(sum(((x - x.mean()) ** 2).sum() for x in xs) / (w.sum() - len(xs)))
    wt = w.sum()
    xbar = float((w * means).sum() / wt)
    c = wt - (w * w).sum() / wt
    a = float(((w * (means - xbar) ** 2).sum() - (len(xs) - 1) * s2) / c)
    k = s2 / a if a > 0 else float("inf")
    return {"s2_within_per_week": s2, "a_between": a, "k_weeks": k, "z_one_week": 1.0 / (1.0 + k),
            "criterion_k_le_2_333": bool(k <= 2.333), "n_symbols": len(xs), "mean_weeks": float(w.mean())}


def main() -> None:
    d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
    weeks, sym = d["weeks"], d["symbols"]
    key = d["key"]
    fac = M.market_factors(d)
    special = {"USDCUSDT", "ETHBTCUSDT"}          # I = 0 per V-1 (DEC-82, help-centre rule)
    special_idx = np.array([s.split("#")[0] in special for s in sym])
    out = {"fingerprint": d["fingerprint"], "panel_meta": d["panel_meta"], "windows": {},
           "label": "formationsseitig (Regel 1 erlaubt); keine Folgewochen-Groesse einer Sortierung"}
    member_by_window = {}
    for wn, (a, b) in C.WINDOWS.items():
        ts = C.judged_formation_weeks(weeks, a, b)
        rows = []
        member = np.zeros_like(d["alive"])
        cls_d1 = {}
        cls_u = {}
        any1h_d1 = any1h_u = n_d1_tot = n_u_tot = 0
        special_d1 = zero_all_d1 = 0
        partial_d1 = 0
        for t in ts:
            m = C.universe_mask(d, t)
            member[t] = m
            u = np.flatnonzero(m)
            k_t = key[t, u]
            d1 = C.d1_members(key[t], m)
            neg = float(np.mean(k_t < -C.KEY_TOL))
            pos = float(np.mean(k_t > C.KEY_TOL))
            lump = float(np.mean(np.abs(k_t) <= C.KEY_TOL))
            spread = float(np.mean(key[t, u]) - np.mean(key[t, d1]))
            # interval classes (modal day class of the formation week)
            c_d1 = M.interval_class_of_week(d, t, d1)
            c_u = M.interval_class_of_week(d, t, u)
            for c in c_d1:
                cls_d1[c] = cls_d1.get(c, 0) + 1
            for c in c_u:
                cls_u[c] = cls_u.get(c, 0) + 1
            any1h_d1 += int((d["cls_days"]["1h"][t, d1] > 0).sum())
            any1h_u += int((d["cls_days"]["1h"][t, u] > 0).sum())
            n_d1_tot += d1.size
            n_u_tot += u.size
            special_d1 += int(special_idx[d1].sum())
            nd = d["n_days_with_funding"][t, d1]
            zero_all_d1 += int(((d["zero_days_w"][t, d1] == nd) & (nd > 0)).sum())
            partial_d1 += int((nd < 7).sum())
            rows.append({"week": weeks[t], "K": int(u.size), "K_with_funding": int((d["n_days_with_funding"][t, u] > 0).sum()),
                         "n_d1": int(d1.size), "neg_share": neg, "pos_share": pos, "lump_share": lump,
                         "d1_degenerate": neg < C.DEGENERACY_SHARE,
                         "key_mean_u_bp": M.fmt_bp(np.mean(key[t, u])), "key_mean_d1_bp": M.fmt_bp(np.mean(key[t, d1])),
                         "key_max_d1_bp": M.fmt_bp(np.max(key[t, d1])), "spread_bp": M.fmt_bp(spread)})
        member_by_window[wn] = (ts, member)
        mid = rows[(len(rows) - 1) // 2]
        negs = np.array([r["neg_share"] for r in rows])
        Ks = np.array([r["K"] for r in rows])
        spreads = np.array([r["spread_bp"] for r in rows])
        # (a) symbols with funding history over both windows -> computed after the loop (needs both)
        # (b) key autocorrelation (time series per symbol; WP-7 estimator) + Buehlmann-Straub
        ac = ts_lag1_autocorr(key[min(ts):max(ts) + 1], member[min(ts):max(ts) + 1])
        bs = buehlmann_straub(key[min(ts):max(ts) + 1], member[min(ts):max(ts) + 1])
        # raw weekly funding SUM (WP-7's original estimator object) for comparison
        ac_raw = ts_lag1_autocorr(d["f_sum_w"][min(ts):max(ts) + 1], member[min(ts):max(ts) + 1])
        # market factor SDs over the window's weeks (formation weeks t and their holding weeks t+1
        # inside the truncated grid): SD only.
        hold = [t + 1 for t in ts if t + 1 < len(weeks)]
        f_sd = {k: float(np.nanstd(v[hold], ddof=1)) for k, v in fac.items()}
        # PIT betas (trailing 26 w) and predicted price-leg variance per formation week
        pv = {}
        for fname in ("ew", "btc"):
            var_f = f_sd[fname] ** 2
            per = []
            for t in ts:
                m = C.universe_mask(d, t)
                d1 = C.d1_members(key[t], m)
                beta, idio = M.trailing_beta_idio(d, fac[fname], t)
                per.append(M.predicted_ls_price_variance(beta, idio, d1, m, var_f))
            pv[fname] = {
                "var_f_window": var_f,
                "delta_mean": float(np.mean([p["delta"] for p in per])),
                "delta_rms": float(np.sqrt(np.mean([p["delta"] ** 2 for p in per]))),
                "beta_d1_mean": float(np.mean([p["beta_d1"] for p in per])),
                "beta_u_mean": float(np.mean([p["beta_u"] for p in per])),
                "factor_var_mean": float(np.mean([p["factor_var"] for p in per])),
                "idio_var_mean": float(np.mean([p["idio_var"] for p in per])),
                "pred_var_mean": float(np.mean([p["pred_var"] for p in per])),
                "pred_sd_bp": float(np.sqrt(np.mean([p["pred_var"] for p in per])) * 1e4),
                "factor_share_of_pred_var": float(np.mean([p["factor_var"] for p in per]) / np.mean([p["pred_var"] for p in per])),
                "n_d1_mean": float(np.mean([p["n_d1"] for p in per])),
                "mean_idio_sd_d1": float(np.mean([p["mean_idio_sd_d1"] for p in per])),
                "mean_idio_sd_u": float(np.mean([p["mean_idio_sd_u"] for p in per])),
                "beta_coverage_d1_min": float(np.min([p["beta_coverage_d1"] for p in per])),
                "beta_coverage_u_min": float(np.min([p["beta_coverage_u"] for p in per])),
            }
        out["windows"][wn] = {
            "start": a, "end": b, "n_formation_weeks": len(ts), "first_formation_week": weeks[ts[0]],
            "last_formation_week": weeks[ts[-1]],
            "K": {"min": int(Ks.min()), "median": float(np.median(Ks)), "max": int(Ks.max()),
                  "kill3_K_min_lt_117": bool(Ks.min() < K_MIN)},
            "degeneration": {"chronological_median_week": mid["week"], "median_week_neg_share": mid["neg_share"],
                             "median_week_d1_degenerate": mid["d1_degenerate"],
                             "median_over_weeks_neg_share": float(np.median(negs)), "min_neg_share": float(negs.min()),
                             "n_weeks_d1_degenerate": int(sum(r["d1_degenerate"] for r in rows)),
                             "lump_share_median": float(np.median([r["lump_share"] for r in rows])),
                             "pos_share_median": float(np.median([r["pos_share"] for r in rows]))},
            "spread_bp_per_week": q(spreads),
            "key_mean_d1_bp": q([r["key_mean_d1_bp"] for r in rows]),
            "key_mean_u_bp": q([r["key_mean_u_bp"] for r in rows]),
            "key_max_d1_bp": q([r["key_max_d1_bp"] for r in rows]),
            "key_autocorr": {"key_F_minus_I": ac, "raw_weekly_funding_sum": ac_raw},
            "buehlmann_straub": bs,
            "interval_class_d1": {c: v / n_d1_tot for c, v in sorted(cls_d1.items())},
            "interval_class_u": {c: v / n_u_tot for c, v in sorted(cls_u.items())},
            "share_any_1h_day": {"d1": any1h_d1 / n_d1_tot, "u": any1h_u / n_u_tot},
            "d1_symbol_weeks": n_d1_tot, "d1_special_I0_pairs_symbol_weeks": special_d1,
            "d1_all_funding_days_exactly_zero_symbol_weeks": zero_all_d1,
            "d1_partial_funding_week_symbol_weeks": partial_d1,
            "market_factor_sd_weekly": f_sd,
            "pit_beta_model": pv,
            "weekly_rows": rows,
        }
    # (a) symbols with funding history over both windows
    ts1, mem1 = member_by_window["W1"]
    ts2, mem2 = member_by_window["W2"]
    f_any_w1 = (d["n_days_with_funding"][ts1] > 0).any(axis=0)
    f_any_w2 = (d["n_days_with_funding"][ts2] > 0).any(axis=0)
    in_all = mem1[ts1].all(axis=0) & mem2[ts2].all(axis=0)
    f_all = (d["n_days_with_funding"][ts1] == 7).all(axis=0) & (d["n_days_with_funding"][ts2] == 7).all(axis=0)
    out["symbols_both_windows"] = {
        "funding_any_day_in_W1_and_W2": int((f_any_w1 & f_any_w2).sum()),
        "member_of_universe_every_formation_week_W1_and_W2": int(in_all.sum()),
        "funding_all_7_days_every_formation_week_W1_and_W2": int(f_all.sum()),
        "kill3_threshold": K_MIN,
    }
    path = C.WORK / f"window_census{C.SUFFIX}.json"
    path.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    for wn, w in out["windows"].items():
        print(wn, {k: w[k] for k in ("n_formation_weeks", "K", "degeneration", "spread_bp_per_week", "key_autocorr", "buehlmann_straub", "interval_class_d1", "interval_class_u", "share_any_1h_day", "d1_symbol_weeks", "d1_special_I0_pairs_symbol_weeks", "d1_all_funding_days_exactly_zero_symbol_weeks", "d1_partial_funding_week_symbol_weeks", "market_factor_sd_weekly")})
        for fname, p in w["pit_beta_model"].items():
            print("  ", fname, p)
    print(out["symbols_both_windows"])


if __name__ == "__main__":
    main()
