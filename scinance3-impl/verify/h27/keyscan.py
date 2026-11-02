"""Print unique key paths (no values) of JSON files; flag suspicious names."""
import json, re, sys
SUS = re.compile(r"mean|avg|median|quantile|p50|p10|p90|level|iv_|dvol|prem", re.I)
def walk(o, path, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, path + "/" + str(k), acc)
    elif isinstance(o, list):
        for v in o[:3]:
            walk(v, path + "[]", acc)
    else:
        acc.add(path)
for f in sys.argv[1:]:
    acc = set()
    walk(json.load(open(f)), "", acc)
    # collapse numeric-ish segments
    col = sorted({re.sub(r"/(\d+(\.\d+)?)(?=/|$)", "/#", p) for p in acc})
    sus = [p for p in col if SUS.search(p)]
    print(f"== {f}: {len(col)} paths, suspicious {len(sus)}")
    for p in sus:
        print("   ", p)
