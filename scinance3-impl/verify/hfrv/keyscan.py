"""Scan JSON outputs for keys that could hold a premium/DVOL mean or sign (no values printed)."""
import json
import re
import sys
from collections import Counter

PAT = re.compile(r"(mean|avg|average|mittel|sign|vorzeichen|level|niveau|median|sum|bias|drift|pos|neg|frac|share|hit)", re.I)


def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else str(k)
            out.append(p)
            walk(v, p, out)
    elif isinstance(o, list):
        for i, v in enumerate(o[:3]):
            walk(v, f"{path}[]", out)


for f in sys.argv[1:]:
    d = json.load(open(f))
    paths = []
    walk(d, "", paths)
    leaf = Counter(re.sub(r"\[\]", "", p).split(".")[-1] for p in paths)
    print("==", f, "n_paths", len(paths), "distinct_keys", len(leaf))
    sus = sorted({k for k in leaf if PAT.search(k)})
    print("suspicious keys:", sus)
