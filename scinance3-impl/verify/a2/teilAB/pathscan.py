"""List generalized leaf paths of the sigma30 work JSON (structure only, no values printed)."""
import json, re, sys
from collections import Counter
CL = r"(FRI|FRI_W|FRI_M|FRI_Q|FRI_MQ|MODO|WE|NONFRI|ALL)"
def gen(p):
    p = re.sub(r"/(20\d\d)(?=/|$)", "/<y>", p)
    p = re.sub(r"/" + CL + r"(?=/|$)", "/<cl>", p)
    p = re.sub(r"/(BTC|ETH|CLUSTER|POOLED)(?=/|$)", "/<k>", p)
    p = re.sub(r"/shift[+-]\dh", "/<shift>", p)
    p = re.sub(r"/\d+(?=/|$)", "/<n>", p)
    return p
def walk(d, p, out):
    if isinstance(d, dict):
        for k, v in d.items():
            walk(v, p + "/" + str(k), out)
    elif isinstance(d, list):
        out[gen(p) + "[]"] += 1
    else:
        out[gen(p)] += 1
out = Counter()
walk(json.load(open(sys.argv[1])), "", out)
for k in sorted(out):
    print(out[k], k)
