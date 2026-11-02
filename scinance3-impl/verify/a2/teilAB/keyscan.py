"""Collect every key path of the reviewed JSON files and flag suspicious names (mean/median/sign/...)."""
import json, re, sys
from collections import Counter
BAD = re.compile(r"mean|avg|average|mittel|median|drift|bias|effect|effekt|delta|sign|vorzeichen|durchschn|center|centre|loc|mu\b|sum|total|rms|raw|level|price|close|open|skew", re.I)
def walk(d, path, keys):
    if isinstance(d, dict):
        for k, v in d.items():
            keys[re.sub(r"\d{4}-\d{2}-\d{2}", "<d>", str(k))] += 1
            walk(v, path + "/" + str(k), keys)
    elif isinstance(d, list):
        for v in d:
            walk(v, path, keys)
for f in sys.argv[1:]:
    keys = Counter()
    walk(json.load(open(f)), "", keys)
    print("==", f, "unique keys", len(keys))
    for k in sorted(keys):
        if BAD.search(k):
            print("  FLAG", k, keys[k])
