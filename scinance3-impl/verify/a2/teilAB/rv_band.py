"""Band width of pooled SD ratios / class SD under calendar-month blocks vs ISO-week blocks (SD only)."""
import sys
import numpy as np
sys.path.insert(0, ".")
import rv_sigma as R
days, cl, comp = {}, {}, {}
for s in ("BTC", "ETH"):
    days[s], cl[s], _, comp[s], _ = R.load(s)
dl = days["BTC"]
fine = np.array([R.fine_class(d) for d in dl])
pre = {s: R.slot(cl[s], comp[s], 450, 480) for s in ("BTC", "ETH")}
mask = {k: np.isin(fine, list(v)) for k, v in R.SETS.items()}
for lab, key in (("ISO-week", lambda d: d.isocalendar()[0] * 100 + d.isocalendar()[1]), ("month", lambda d: d.year * 100 + d.month)):
    g = np.array([key(d) for d in dl]); _, idx = np.unique(g, return_inverse=True); W = idx.max() + 1
    cnt = np.random.default_rng(99).multinomial(W, np.full(W, 1 / W), size=2000).astype(float)
    def sdr(x, m):
        ok = m & np.isfinite(x); xv = np.where(ok, x, 0.0)
        agg = lambda v: np.bincount(idx, weights=v, minlength=W)
        n = cnt @ agg(ok.astype(float)); s1 = cnt @ agg(xv); s2 = cnt @ agg(xv * xv)
        return np.sqrt((s2 - s1 * s1 / n) / (n - 1))
    pool = lambda c: np.sqrt((sdr(pre["BTC"], mask[c]) ** 2 + sdr(pre["ETH"], mask[c]) ** 2) / 2)
    for a, b in (("FRI", "MODO"), ("FRI_MQ", "FRI_W"), ("WE", "MODO")):
        q = np.quantile(pool(a) / pool(b), [0.025, 0.975]); print(lab, f"{a}/{b}", np.round(q, 3))
    q = np.quantile(pool("FRI"), [0.025, 0.975]); print(lab, "pooled SD FRI band", np.round(q, 1))
