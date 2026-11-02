"""Synthetic check (NO real data): per-week SD of the fm_neutral_8w mom1 IC in the DEC-89 positive-control
world with and without the PRD sector blocks, and the empirical pass rate of the P-1 window condition at an
injected IC equal to the H-32 handover threshold. Uses the repo's own simulation/IC code on a synthetic,
all-alive panel shaped like W1 (K = 419, 52 judged weeks + 8 burn-in weeks for the 8-week beta).

Usage: PYTHONPATH=<repo>/src python3 sector_check.py <repo_root> <power_json> <out_json>
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import yaml

REPO, POWER_JSON, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(REPO, "src"))
from bybit_edge.research.wp13_xsec import characteristics, ic, positive_control as pc  # noqa: E402

reg = yaml.safe_load(open(os.path.join(REPO, "scinance3-impl/state/registered/h28_h30_v3.yaml")))
pw = json.load(open(POWER_JSON))
K, BURN, WJ = 419, 8, 52
N_WEEKS = BURN + WJ + 1
symbols = ["BTCUSDT"] + [f"SYN{i:04d}" for i in range(K - 1)]
alive = np.ones((N_WEEKS, K), dtype=bool)
valid = np.ones((N_WEEKS, K), dtype=bool)


def one_rep(world, seed, signal_ic):
    sim = pc.synthesize_window_returns(alive, valid, symbols, world, seed=seed, window_index=1, signal_ic=signal_ic)
    r, r_est = sim["returns"], sim["returns_est"]
    beta = characteristics.beta_characteristic(r_est, symbols, market_symbol="BTCUSDT", trail_win=8, min_weeks=8)
    char = characteristics.momentum_characteristic(r, trail_win=1)
    sl = slice(BURN, N_WEEKS)
    applied = ic.apply_beta_control("fm_neutral_8w", char[sl], r[sl], alive[sl], beta_pit=beta[sl],
                                    symbols=symbols, market_symbol="BTCUSDT")
    res = ic.weekly_ic_series(applied["characteristic"], applied["returns"], alive[sl], convention="close_at_last")
    x = np.array([w["ic"] for w in res["weekly"]], dtype=float)
    x = x[~np.isnan(x)]
    return x


def study(sector_rel, signal_ic, n_reps, seed0):
    world = pc.window_world(reg, "W1")
    world = dict(world)
    world["sigma_g"] = sector_rel * world["sigma_e"]
    world["sigma_tot"] = math.sqrt(world["sigma_e"] ** 2 + world["sigma_g"] ** 2 + (world["beta_sd"] * world["sigma_f"]) ** 2)
    pooled, means = [], []
    for k in range(n_reps):
        x = one_rep(world, seed0 + k, signal_ic)
        pooled.extend(x.tolist())
        means.append(float(x.mean()))
    pooled = np.array(pooled)
    means = np.array(means)
    return {"sector_rel": sector_rel, "signal_ic": signal_ic, "n_reps": n_reps,
            "sd_weekly_ic": float(pooled.std(ddof=1)), "mean_of_means": float(means.mean()),
            "sd_of_means": float(means.std(ddof=1)), "means": means}


out = {"setup": {"K": K, "judged_weeks": WJ, "burn_in_weeks": BURN, "world": "positive_control.window_world(h28_h30_v3.yaml, W1) stress",
                 "statistic": "fm_neutral_8w mom1 weekly Spearman IC, close_at_last"}}
sd_rows = []
for rel in (0.0, 0.1, 0.2, 0.375):
    s = study(rel, 0.0, 60, 1000)
    s.pop("means")
    sd_rows.append(s)
out["sd_by_sector_strength"] = sd_rows

# empirical power of the P-1 window condition at the injected handover threshold (no sectors = null world)
thr = pw["power_table"]["mom1"]["S1_draws_sd_bindend"]["thresholds"]["W1"]
T, se_s1, mde = thr["threshold_T"], thr["se"], thr["mde80"]
z = 1.6448536269514722
pos = study(0.0, mde, 300, 5000)
neg = study(0.0, 0.0, 300, 5000)
inj = pos["means"] - neg["means"]
out["power_check_null_world"] = {
    "injected_signal_ic": mde, "threshold_T_frozen_style": T, "se_power_line_S1": se_s1,
    "realized_injection_mean": float(inj.mean()),
    "pass_rate_T_frozen": float((pos["means"] >= T).mean()),
    "neg_pass_rate_T_frozen": float((neg["means"] >= T).mean()),
    "sd_of_means_pos": pos["sd_of_means"], "sd_of_means_neg": neg["sd_of_means"],
    "sd_weekly_pos": pos["sd_weekly_ic"], "mean_of_means_neg": neg["mean_of_means"], "mean_of_means_pos": pos["mean_of_means"],
    "expected_power_from_realized": None, "note": "SE-Regel hier vereinfacht: feste Schwelle T aus der Power-Zeile (S1); "
                                                  "der Lauf rechnet SE aus der realisierten Serie (max(Boden, SD, SE_stat)).",
}
with open(OUT, "w") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print(json.dumps(out, indent=1))
