"""Review A1 -- independent loader. Reads the union panel READ-ONLY via the repo loader, truncates
daily rows after 2026-06-28 (last W2 formation week 2026-06-22), and builds OWN weekly arrays:
key = sum over days with funding of (funding_sum - 0.0003) [I = 0.01 %/8h scaled per payment
=> 0.03 %/day for every interval class], raw weekly F sum, 1h-day counts. No outcome is computed here."""
import sys, pickle, time
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, "/home/user/scinance/src")
import numpy as np
from bybit_edge.research.wp7_universe import panel_load

SP = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad")
PB, DB = SP / "panel/panel_1d", SP / "panel/panel_1d_delisted"
OUT = SP / "a1_review/cache/rv_data.pkl"
LAST = "2026-06-28"

t0 = time.time()
syms = panel_load.load_panel_symbols(PB / "panel_manifest.sqlite")
P = panel_load.load_panel_union(PB, PB / "panel_manifest.sqlite", DB, DB / "panel_manifest.sqlite",
                                year_start=2021, year_end=2026, as_of=date(2026, 9, 28),
                                delisting_dates_path=DB / "delisting_dates.json", symbols=syms, allow_partial=True)
keep = [i for i, d in enumerate(P["dates"]) if d <= LAST]
for k in ("close", "turnover", "funding_n", "funding_sum"):
    P[k] = P[k][keep, :]
P["dates"] = [P["dates"][i] for i in keep]
P["day_index"] = [P["day_index"][i] for i in keep]
W = panel_load.weekly_returns_and_mask_union(P, P["last_alive_day"])
weeks = W["weeks"]; wpos = {w: i for i, w in enumerate(weeks)}
fn, fs = P["funding_n"], P["funding_sum"]
ok = np.isfinite(fn) & (fn > 0) & np.isfinite(fs)
nW, nS = len(weeks), fn.shape[1]
key = np.zeros((nW, nS)); fsum = np.zeros((nW, nS)); nday = np.zeros((nW, nS), int); h1 = np.zeros((nW, nS), int)
fsum_nan = np.full((nW, nS), np.nan)   # WP-7 style weekly nansum is zero-filled; keep a NaN-aware version too
for i, ds in enumerate(P["dates"]):
    dd = date.fromisoformat(ds); wk = (dd - timedelta(days=dd.weekday())).isoformat()
    wi = wpos.get(wk)
    if wi is None:
        continue
    key[wi] += np.where(ok[i], fs[i] - 0.0003, 0.0)
    fsum[wi] += np.where(ok[i], fs[i], 0.0)
    nday[wi] += ok[i]
    h1[wi] += ok[i] & (np.round(np.nan_to_num(fn[i])) == 24)
fsum_nan = np.where(nday > 0, fsum, np.nan)
d = {"weeks": weeks, "symbols": P["symbols"], "alive": W["alive"], "returns": W["returns"],
     "returns_valid": W["returns_valid"], "key": key, "fsum": fsum, "fsum_nan": fsum_nan, "nday": nday, "h1": h1,
     "last_alive_day": P["last_alive_day"], "dates": P["dates"], "funding_sum_daily": fs, "funding_n_daily": fn}
pickle.dump(d, open(OUT, "wb"), protocol=pickle.HIGHEST_PROTOCOL)
print("loaded", round(time.time() - t0, 1), "s; days", len(P["dates"]), P["dates"][0], P["dates"][-1], "weeks", nW,
      weeks[0], weeks[-1], "symbols", nS)
