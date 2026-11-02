"""Handover probability (Lesart A, analytic as derivation) for literature-band ICs mapped to the fm8 scale with the
synthetic attenuation share 0.75 (rv_inject)."""
import json
from statistics import NormalDist
N = NormalDist(); J = json.load(open("rv_nuis.json")); nu = J["nu"]
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    s = nu[v]["P"]["sep"]; mp = nu[v]["W1"]["m"]
    c = max(2.4865 * max(nu[v][W]["S1"] for W in ("W1", "W2")) + max(0, max(nu[v][W]["m"] for W in ("W1", "W2"))), 2 * s)
    row = {ic: (1 - N.cdf((c - mp - ic) / s), 1 - N.cdf((c - mp - 0.75 * ic) / s)) for ic in (0.004, 0.012, 0.033)}
    print(v, " ".join(f"IC {ic}: {a*100:.1f}% -> {b*100:.1f}%" for ic, (a, b) in row.items()))
