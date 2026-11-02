"""HF-RV power / window-length helpers (R-8).

``_crit_ok``, ``solve_n``, ``se_fn``, ``durations``, ``ceil_units`` and ``daily_full`` are copied
unchanged from the programme balance (``scratchpad/bilanz/bilanz_census.py``, DEC-98) so that the
day counts here are computed exactly like Bilanz table rows 272-274.  Every power / MDE / regime
number goes through ``bybit_edge.research.power_p1`` (DEC-94 (8)).
"""
from __future__ import annotations

import datetime as dt
import math
import sys

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

Z = pp.z_krit(pp.ALPHA_WINDOW)                 # 1.6449
ZMDE = pp.mde_factor(pp.ALPHA_WINDOW)          # 2.4865
ZMDE_A3 = pp.Z_PER_WINDOW_A3_PRACTICE + pp.Z_POWER   # 3.3281 (A3 practice MDE factor)
START_VRP = dt.date(2026, 7, 1)


# --- copied from bilanz_census.py (unchanged) -------------------------------------------------

def _crit_ok(name: str, priors, ses) -> bool:
    if name == "p1_c10":
        return pp.assign_regime(priors, ses)["regime"] == pp.REGIME_C10
    if name == "p1_admit":
        return pp.assign_regime(priors, ses)["regime"] != pp.REGIME_GL012
    if name == "p1_dec52_gate":
        return pp.dec52_gate_power(priors, ses)["power_product"] >= pp.POWER_TARGET - 1e-12
    if name == "a3_c10":
        return pp.assign_regime_a3_practice(priors, ses)["regime"] == pp.REGIME_C10
    if name == "a3_admit_dec52":
        return pp.assign_regime_a3_practice(priors, ses, allow_dec52=True)["regime"] != pp.REGIME_GL012
    if name == "a3_dec52_gate":
        return (pp.dec52_gate_power(priors, ses, pp.Z_POOLED_A3_PRACTICE)["power_product"]
                >= pp.POWER_TARGET - 1e-12)
    raise ValueError(name)


def solve_n(priors, se_fns, crit: str, lo: float = 1e-3, hi: float = 1e7) -> float | None:
    """Smallest continuous n with crit(priors, [f(n) for f in se_fns]) True (bisection, log)."""
    def ok(n: float) -> bool:
        return _crit_ok(crit, priors, [f(n) for f in se_fns])
    if not ok(hi):
        return None
    if ok(lo):
        return lo
    a, b = math.log(lo), math.log(hi)
    for _ in range(200):
        m = 0.5 * (a + b)
        if ok(math.exp(m)):
            b = m
        else:
            a = m
        if b - a < 1e-12:
            break
    return math.exp(b)


def se_fn(sd: float, c: float, null_at: tuple[float, float] | None = None):
    """SE(n) = max(SD * sqrt(c / n), SE_null(n)); SE_null scaled ~1/sqrt(n) from a reference."""
    def f(n: float) -> float:
        s = sd * math.sqrt(c / n)
        if null_at is not None:
            se0, n0 = null_at
            s = max(s, se0 * math.sqrt(n0 / n))
        return s
    return f


def durations(prior: float, sd: float, c: float, null_at=None) -> dict:
    """Equal-window durations under P-1 and the A3 practice (double statement DEC-94 (9))."""
    f = se_fn(sd, c, null_at)
    pr = [prior, prior]
    out = {
        "c10_p1": solve_n(pr, [f, f], "p1_c10"),
        "dec52_gate_p1": solve_n(pr, [f, f], "p1_dec52_gate"),
        "admit_p1": solve_n(pr, [f, f], "p1_admit"),
        "c10_a3": solve_n(pr, [f, f], "a3_c10"),
        "dec52_gate_a3_3168": solve_n(pr, [f, f], "a3_dec52_gate"),
        "admit_a3_with_dec52": solve_n(pr, [f, f], "a3_admit_dec52"),
        "closed_form_c10_p1": c * (ZMDE * sd / prior) ** 2,
        "closed_form_c10_a3": c * (ZMDE_A3 * sd / prior) ** 2,
    }
    n = out["c10_p1"]
    if n is not None:
        se = f(n)
        out["check_window_power_at_c10_p1"] = pp.window_power(prior, se, Z)
        out["check_mde80_at_c10_p1"] = pp.mde80(se, Z)
    return out


def ceil_units(x):
    return None if x is None else int(math.ceil(x - 1e-9))


def daily_full(start: dt.date, n_days, rv_tail: int = 30) -> str | None:
    if n_days is None:
        return None
    n = ceil_units(n_days)
    return (start + dt.timedelta(days=2 * n - 1 + rv_tail)).isoformat()

# --- end of copy -------------------------------------------------------------------------------


def window_rows(prior: float, sd: float, c: float, null_at, n_list=(335, 365)) -> dict:
    """SE, window power and regime (P-1 and A3 practice) for two equal windows of n IV days."""
    out = {}
    f = se_fn(sd, c, null_at)
    for n in n_list:
        se_n = sd * math.sqrt(c / n)
        se_null = None if null_at is None else null_at[0] * math.sqrt(null_at[1] / n)
        se = f(n)
        p1 = pp.assign_regime([prior, prior], [se, se])
        a3 = pp.assign_regime_a3_practice([prior, prior], [se, se])
        out[str(n)] = {"se_nuis": se_n, "se_null": se_null, "se": se,
                       "binding_source": "nuisance" if (se_null is None or se_n >= se_null) else "null_world_h27",
                       "window_power_p1": p1["window_power"][0], "mde80_p1": p1["mde80"][0],
                       "gate_power_product_p1": p1["gate_power_product"], "regime_p1": p1["regime"],
                       "window_power_a3": a3["window_power"][0], "regime_a3": a3["regime"],
                       "zugelassen_nur_durch_dec94": a3["zugelassen_nur_durch_dec94"]}
    return out


def duration_block(prior: float, sd: float, c: float, null_at) -> dict:
    dur = durations(prior, sd, c, null_at)
    return {"prior": prior, "sd": sd, "c": c, "se_null_ref": None if null_at is None else list(null_at),
            "days": dur,
            "full_c10_p1": daily_full(START_VRP, dur["c10_p1"]),
            "full_dec52_gate_p1": daily_full(START_VRP, dur["dec52_gate_p1"]),
            "full_c10_a3": daily_full(START_VRP, dur["c10_a3"]),
            "full_dec52_gate_a3_3168": daily_full(START_VRP, dur["dec52_gate_a3_3168"])}
