"""H-27 review, check point 4: how much of the premium variance is RV measurement noise?

Pre-period daily variance proxies only (prices <= 2024-05-31).  For proxy x_s of sigma_s^2
(cc = r^2, pk = Parkinson), the conditional 'kurtosis' kappa = E[x^2] / E[x_s x_{s+L}] (smooth-vol
approximation, L = 1..5; vol clustering inflates the denominator -> kappa understated at L = 1).
Noise SD of the 30-day vol estimate (delta method) ~ sqrt((kappa - 1) / (4 * 30)) * sigma_rms.
Compared with the premium SD (S1, cc) of the review nuisance (nuisance_review.json).
Nothing about the premium level is computed.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rv_common import daily_vars, guard_out  # noqa: E402


def main() -> None:
    nuis = json.loads((HERE / "nuisance_review.json").read_text())
    out = {}
    for sym in ("BTC", "ETH"):
        ds, dv = daily_vars(sym)
        sel = np.array([d >= "2021-03-25" for d in ds])
        rec = {}
        for est in ("cc", "pk", "gk"):
            x = dv[est][sel]
            if not np.all(np.isfinite(x)):
                raise RuntimeError("gap")
            kap = {}
            for L in (1, 2, 3, 5):
                kap[str(L)] = float(np.mean(x * x) / np.mean(x[L:] * x[:-L]))
            rec[est] = {"kappa_by_lag": kap}
        sig = nuis[f"{sym}/cc"]["rv_rms"]
        sd_p = nuis[f"{sym}/cc"]["S1"]["sd"]
        for est in ("cc", "pk", "gk"):
            k = np.mean([rec[est]["kappa_by_lag"][L] for L in ("2", "3", "5")])
            sd_noise = 100 * math.sqrt(max(k - 1, 0) / 120.0) * sig
            rec[est]["kappa_lag2_5"] = float(k)
            rec[est]["sd_noise_volpts_delta"] = sd_noise
            rec[est]["share_of_premium_var_S1cc"] = sd_noise ** 2 / sd_p ** 2
        rec["sd_premium_S1_cc"] = sd_p
        rec["sd_premium_S1_if_noise_free"] = math.sqrt(max(sd_p ** 2 - rec["cc"]["sd_noise_volpts_delta"] ** 2, 0))
        out[sym] = rec
        print(sym, json.dumps(rec, indent=1))
    guard_out(out)
    (HERE / "noise_share.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
