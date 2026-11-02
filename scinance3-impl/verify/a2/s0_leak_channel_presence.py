"""Review A2 Teil C - Pruefpunkt 1: presence and stored precision of the fields that would form an
algebraic location channel (SD of the union U = E u P2'' via the shift SD, plus class SDs).
This script NEVER combines the real values: it only reports key presence and the number of significant
digits of the stored JSON literals (text level).  No mean, no contrast.
"""
import re, sys, hashlib
P = "/home/user/scinance/scinance3-impl/state/herleitung_a2/a2_teilC.json"
txt = open(P, encoding="ascii").read()
print("sha256", hashlib.sha256(txt.encode()).hexdigest())
# text-level scan: find literal of a key inside a given window block, count significant digits only
def sig_digits(lit: str) -> int:
    m = lit.lstrip("-").split("e")[0].replace(".", "").lstrip("0")
    return len(m)
blocks = ["V1_2021-06..2022-05", "V2_2022-06..2023-05", "V3_2023-06..2024-05", "VP_2021-03-24..2024-05-31"]
for b in blocks:
    i = txt.index('"%s": {' % b, txt.index('"pre_windows"'))
    seg = txt[i:i + 20000]
    out = {}
    m = re.search(r'"sd_of_null_shift_iid": (-?[0-9.e+-]+)', seg)
    out["sd_of_null_shift_iid"] = sig_digits(m.group(1)) if m else None
    j = seg.index('"sd_class_window"')
    sub = seg[j:j + 400]
    for k in ("E", "P2ss"):
        mm = re.search(r'"%s": (-?[0-9.e+-]+)' % k, sub)
        out["sd_class_window/" + k] = sig_digits(mm.group(1)) if mm else None
    print(b, "significant digits stored:", out)
