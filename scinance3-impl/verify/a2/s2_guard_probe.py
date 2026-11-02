"""Review A2 Teil C, Pruefpunkt 1: provoke the guard of the derivation with a COPY of its code.
No return is loaded here: only calendar dates (RV-2) and synthetic numbers.  The real contrast is never formed.
Also: synthetic demonstration of the variance-decomposition channel (SD of a union + class SDs -> |contrast|)
on the real calendar structure with SYNTHETIC returns.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rv_common as rv  # noqa: E402

SRC = Path("/home/user/scinance_work/a2_teilC")
PROBE = rv.WORK / "probe_copy"
PROBE.mkdir(parents=True, exist_ok=True)
res = {}
for f in ("c_common.py", "test_c_guards.py"):
    shutil.copyfile(SRC / f, PROBE / f)
    assert rv.sha(SRC / f) == rv.sha(PROBE / f)
    res[f"copy_sha256_{f}"] = rv.sha(PROBE / f)
off = json.load(open("/home/user/scinance/scinance3-impl/state/herleitung_a2/a2_teilC.json"))["skripte_sha256"]
res["copy_equals_official_script_hash"] = all(off[f] == res[f"copy_sha256_{f}"] for f in ("c_common.py", "test_c_guards.py"))
# 1) the derivation's own tests on the copy
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_c_guards.py"],
                   cwd=PROBE, capture_output=True, text=True)
res["pytest_copy_tail"] = r.stdout.strip().splitlines()[-1].split(" in ")[0]
sys.path.insert(0, str(PROBE))
import c_common as cc  # noqa: E402  (the COPY, sha256-identical)

flags, _ = rv.load_calendar()
probes = {}
for wn, (lo, hi) in {"VP": (rv.D_LO, rv.D_HI), "W2": (rv.W2_LO, rv.W2_HI)}.items():
    S = rv.sets_of(lo, hi, flags)
    U = sorted(S["E"] + S["P2ss"])
    pn = cc.PermNull(U, np.array([d.weekday() == 4 for d in U]))
    real = np.array([d.weekday() == 4 for d in pn.days], dtype=np.uint8)
    out = {}
    # (a) real row, x = None: guard must fire before x is touched
    try:
        pn.centred_replicates(None, real[None, :]); out["a_real_row_x_none"] = "NICHT verweigert"
    except cc.RealLabelError:
        out["a_real_row_x_none"] = "RealLabelError"
    except Exception as e:  # noqa: BLE001
        out["a_real_row_x_none"] = f"anderer Fehler {type(e).__name__} (Waechter zu spaet)"
    syn = np.random.default_rng(11).normal(0, 40, pn.n)            # SYNTHETIC returns
    # (b) real row hidden among 1,000 permuted rows
    L = pn.draw_labels(1000, seed=99)
    L[500] = real
    try:
        pn.centred_replicates(syn, L); out["b_real_row_hidden"] = "NICHT verweigert"
    except cc.RealLabelError:
        out["b_real_row_hidden"] = "RealLabelError"
    # (c) real row in other dtypes (bool, int64, float64)
    for dt in (bool, np.int64, np.float64):
        try:
            pn.centred_replicates(syn, real.astype(dt)[None, :]); out[f"c_real_row_{np.dtype(dt).name}"] = "NICHT verweigert"
        except cc.RealLabelError:
            out[f"c_real_row_{np.dtype(dt).name}"] = "RealLabelError"
        except Exception as e:  # noqa: BLE001
            out[f"c_real_row_{np.dtype(dt).name}"] = f"{type(e).__name__}"
    # (d) near-real row: real except ONE permutable week moved to another day (synthetic x)
    near = real.copy()
    w = pn.perm_weeks[0]
    ids = pn.idx_of_week[w]
    near[ids] = 0
    near[[i for i in ids if not real[i]][0]] = 1
    try:
        pn.centred_replicates(syn, near[None, :]); out["d_near_real_row_one_week_moved"] = "akzeptiert (Waechter nur exakte Gleichheit)"
    except cc.RealLabelError:
        out["d_near_real_row_one_week_moved"] = "RealLabelError"
    # (e) W2: share of real Fridays fixed in every replicate
    out["fixed_event_weeks"] = len(pn.fixed_event_weeks)
    probes[wn] = out
res["probes"] = probes
# (f) key guard against the variance-decomposition channel
try:
    cc.guard_keys({"sd_of_null_shift_iid": 1.0, "sd_class_window": {"E": 1.0, "P2ss": 1.0}})
    res["f_guard_keys_union_sd_channel"] = "akzeptiert (Schluessel-Waechter erkennt den Kanal nicht)"
except ValueError:
    res["f_guard_keys_union_sd_channel"] = "verweigert"


# (g) SYNTHETIC demonstration of the channel on the real calendar structure (no real return involved)
def g12(v, d=12):
    return float(f"{v:.{d}g}")


def shift_factor(nl: rv.Null) -> float:
    f = sum((1.0 / nl.W - (len(ids) - 1) / nl.NP) ** 2 / len(ids) for ids in nl.perm)
    f += len(nl.fix_ev) * (1.0 / nl.W) ** 2 + sum(len(i) for i in nl.fix_pl) * (1.0 / nl.NP) ** 2
    return math.sqrt(f)


demo = {}
for wn, (lo, hi) in {"V1": (rv.date(2021, 6, 1), rv.date(2022, 5, 31)), "VP": (rv.D_LO, rv.D_HI)}.items():
    S = rv.sets_of(lo, hi, flags)
    nl = rv.Null(S["E"], S["P2ss"])
    isfri = np.array([d.weekday() == 4 for d in nl.U])
    rng = np.random.default_rng(2026)
    rows = {}
    for planted in (-12.0, -3.0, 5.0):
        x = rng.standard_t(5, nl.U.__len__()) * 30.0 + planted * isfri          # SYNTHETIC
        true_abs = abs(x[isfri].mean() - x[~isfri].mean())                       # synthetic contrast only
        sU, sE, sP = (float(np.std(v, ddof=1)) for v in (x, x[isfri], x[~isfri]))
        fac = shift_factor(nl)
        for digits in (12, 4, 3):
            shift_stored = g12(sU * fac, digits)                                 # what the JSON stores
            sE_s, sP_s = g12(sE, digits), g12(sP, digits)
            sU_rec = shift_stored / fac                                         # factor is pure calendar
            n, W, NP = len(nl.U), nl.W, nl.NP
            d2 = n / (W * NP) * ((n - 1) * sU_rec ** 2 - (W - 1) * sE_s ** 2 - (NP - 1) * sP_s ** 2)
            rec = math.sqrt(max(d2, 0.0))
            rows[f"planted_{planted:+.0f}_digits_{digits}"] = {"abs_err_bp": abs(rec - true_abs)}
    demo[wn] = {"calendar_shift_factor": shift_factor(nl), "recovery": rows}
res["g_synthetic_channel_demo"] = demo
h = rv.dump(res, rv.WORK / "s2_probe.json")
print("s2_probe.json sha256", h)
