"""Fassung 2 (A-1, A-5): same-day correlations between placebo cluster series (inputs of the conjunction
covariance, R-15) and the week-level correlation of the paired difference series Friday vs Mo-Do (DiD
covariance term, used only if negative).  Correlations only (R-11/R-12 guards); returns <= 2024-05-31."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402
import a2v_sigma30 as s30  # noqa: E402  (own loader incl. R-13 assert, own slot grid R-3)


def main() -> dict:
    kl = s30.load()
    days_s = kl["BTC"]["days"]
    days = [date.fromisoformat(x) for x in days_s]
    fine = np.array([c.day_class(d) for d in days])
    masks = {k: np.isin(fine, v) for k, v in c.CLASS_SETS.items()}
    sr = {s: s30.slot_returns(kl[s]["closes"], kl[s]["opens"], kl[s]["complete"]) for s in ("BTC", "ETH")}
    pre = 0.5 * (sr["BTC"]["pre"] + sr["ETH"]["pre"])
    fix = 0.5 * (sr["BTC"]["fix1530"] + sr["ETH"]["fix1530"])
    keep = [j for j in range(48) if j not in s30.EXCL_P3ALL]
    p3 = {}
    for s in ("BTC", "ETH"):
        prof = sr[s]["_profile"][:, keep]
        v = prof.sum(axis=1) / len(keep)          # same per-day statistic as a2v_sigma30 (internal)
        v[np.isnan(prof).any(axis=1)] = np.nan
        p3[s] = v
    p3c = 0.5 * (p3["BTC"] + p3["ETH"])

    def corr(a, b, cl):
        m = masks[cl] & np.isfinite(a) & np.isfinite(b)
        return {"n": int(m.sum()), "pearson": float(np.corrcoef(a[m], b[m])[0, 1])}

    out: dict = {"label": c.LABEL, "quelle": "S:a2v_corr2.py (R-15, A-5)",
                 "same_day_corr_cluster": {
                     "pre_vs_fix1530": {cl: corr(pre, fix, cl) for cl in ("MODO", "FRI_W", "FRI", "NONFRI", "ALL")},
                     "pre_vs_p3all44": {cl: corr(pre, p3c, cl) for cl in ("MODO", "FRI_W", "FRI", "NONFRI", "ALL")},
                     "fix1530_vs_p3all44": {cl: corr(fix, p3c, cl) for cl in ("ALL", "FRI", "MODO")},
                 }}
    # DiD: week-level correlation of the paired difference series (Friday vs Mo-Do of the same ISO week)
    dser = pre - fix
    fr, mo = {}, {}
    for i, d in enumerate(days):
        if not np.isfinite(dser[i]):
            continue
        wk = d.isocalendar()[:2]
        if fine[i] in c.CLASS_SETS["FRI"]:
            fr.setdefault(wk, []).append(dser[i])
        elif fine[i] == "MODO":
            mo.setdefault(wk, []).append(dser[i])
    keys = sorted(set(fr) & set(mo))
    a = np.array([np.sum(fr[k]) / len(fr[k]) for k in keys])     # internal aggregation only
    b = np.array([np.sum(mo[k]) / len(mo[k]) for k in keys])
    out["did_week_corr_fri_vs_modo_paired_series"] = {"n_weeks": len(keys), "pearson": float(np.corrcoef(a, b)[0, 1])}
    c.check_out(out)
    return out


if __name__ == "__main__":
    print("sha256", c.dump(main(), c.WORK / "a2v_corr2.json"))
