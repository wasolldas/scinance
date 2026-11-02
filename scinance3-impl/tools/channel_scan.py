"""Orchestrator channel scan for a nuisance JSON (structure only, never combines values).
Finds dispersion entries carrying a count n and an sd-like value, groups them by every 'one segment wildcarded' path,
and flags groups where one class count equals the sum of 2..3 other class counts (nesting -> variance decomposition
would reveal a mean difference). Also lists union/shift-like keys."""
import json, sys, re, itertools
path = sys.argv[1]; d = json.load(open(path))
entries = []
SDK = ("sd", "std", "sigma", "sd_cluster", "sd_bp", "sd_ddof1")
def walk(o, p=""):
    if isinstance(o, dict):
        ks = set(o.keys())
        n = next((o[k] for k in ("n", "count", "N", "n_days", "n_obs") if k in ks and isinstance(o[k], (int, float))), None)
        if n is not None and any(k in ks for k in SDK): entries.append((p, int(n)))
        for k, v in o.items(): walk(v, p + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, p + f"[{i}]")
walk(d)
def walk2(o, p=""):
    if isinstance(o, dict):
        cnt = [k for k, v in o.items() if isinstance(v, dict) and re.search(r"^(counts?|n_[a-z_]*|N)$", k)]
        sds = [k for k, v in o.items() if isinstance(v, dict) and re.search(r"^(sd|std|sigma)", k)]
        for ck in cnt:
            for sk in sds:
                common = set(o[ck].keys()) & set(o[sk].keys())
                for c in common:
                    if isinstance(o[ck][c], (int, float)): entries.append((p + "/" + sk + "/" + c, int(o[ck][c])))
        for k, v in o.items(): walk2(v, p + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk2(v, p + f"[{i}]")
walk2(d)
groups = {}
for p, n in entries:
    segs = p.split("/")
    for i in range(1, len(segs)):
        key = "/".join(segs[:i] + ["*"] + segs[i + 1:]); groups.setdefault(key, []).append((segs[i], n))
flags = set()
for key, lst in groups.items():
    if len(lst) < 3: continue
    for (c, n) in lst:
        others = [(c2, n2) for (c2, n2) in lst if c2 != c and n2 < n]
        for r in (2, 3):
            for combo in itertools.combinations(others, r):
                if sum(x[1] for x in combo) == n: flags.add((key, c, n, tuple(sorted(x[0] for x in combo))))
print("entries (n + sd):", len(entries), "| nesting groups flagged:", len(flags))
seen = set()
for f in sorted(flags):
    sig = (f[0].split("/")[-2] if "*" not in f[0].split("/")[-1] else f[0], f[1], f[3])
    if (f[1], f[3]) in seen: continue
    seen.add((f[1], f[3])); print("  parent", f[1], "=", " + ".join(f[3]), "| n", f[2], "| e.g.", f[0][:110])
    if len(seen) >= 12: break
print("union/shift-like keys with numeric value:")
def keys(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if re.search(r"union|shift|vereinig|_u$|^u_|sd_all|sd_total", k.lower()) and isinstance(v, (int, float)): print("  ", p + "/" + k)
            keys(v, p + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o): keys(v, p + f"[{i}]")
keys(d)
