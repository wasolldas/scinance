"""Pure gate arithmetic of the H-32 test (ERSTFASSUNG 2, DEC-94 (1)): ``evaluate(payload) -> verdict``.

**Pure by construction** (T4): one already-computed ``payload`` of numbers in, one verdict out, no I/O, no randomness, no
access to the panel; the same payload gives the identical dict.  All statistics are in the registered direction
``y = s * IC``.

Provisional PASS iff in W1 AND W2 (C.10 hard, no DEC-52 branch -- rule U only admits C10):

  (1a) ``y_W > 0`` (NaN fails);
  (1b) ``y_W >= z_krit * SE_W`` (SE_W by rule P-1 (4); NaN or 0 fails);
  (1c) ``y_W >= q95_eff,W,v`` (DEC-101 E2: the frozen 95 % quantile of the null window mean, scaled to the real weekly SD:
       ``q95_eff = max(0, m) + k (q95 - m)``, ``k = max(1, SD(IC_t,W) / sd_week_W,v)``, ``m`` the frozen null mean of the
       binding cell; a window payload without a ``null_scaling`` block uses the frozen ``q95`` as before, ``k = 1``);

and, only for ``rev_gap``, (4b) no bounce kill: ``|IC_bounce,W| >= |statistic_W|`` in any window -> NO PASS ("Artefakt
Bounce").  Before the verdict: the pre-verdict kill ``ceiling_k4_W >= T_W,frozen`` in any window -> DROP, label GL-012
(``T_W,frozen = z_krit * e_se_rule + max(0, null_mean)``; one ceiling, four thresholds -- the smallest binds first).

F-WEEK (BY) is applied afterwards on the p values (``fweek.py``); a PASS is labelled "vorlaeufig bis F-WEEK geschlossen".
"""
from __future__ import annotations

import math
from typing import Any

from . import estimators as est

__all__ = ["evaluate", "window_conditions", "effective_q95"]


def _finite(x: Any) -> bool:
    return x is not None and isinstance(x, (int, float)) and math.isfinite(float(x))


def effective_q95(w: dict[str, Any]) -> dict[str, Any]:
    """DEC-101 E2: the null quantile that condition (1c) of ONE window payload uses, derived from the payload alone.  With a
    ``null_scaling`` block ``{"sd_real", "sd_week", "m", "q95_frozen"}``: ``k = max(1, sd_real / sd_week)`` and
    ``q95_eff = max(0, m) + k (q95_frozen - m)`` (pure arithmetic, T4); without it the frozen ``w["q95"]`` with ``k = 1``."""
    ns = w.get("null_scaling")
    if isinstance(ns, dict):
        k = est.scale_factor(ns.get("sd_real"), ns.get("sd_week"))
        return {"k": k, "q95_effective": est.q95_effective(ns.get("m"), k, ns.get("q95_frozen")), "scaled": True}
    q = w.get("q95")
    return {"k": 1.0, "q95_effective": float(q) if _finite(q) else float("nan"), "scaled": False}


def window_conditions(w: dict[str, Any], z_krit: float) -> dict[str, Any]:
    """Conditions (1a)-(1c) of ONE window payload ``{"y", "se_w", "q95"}`` (DEC-101 E2: or with a ``null_scaling`` block) and
    the threshold ``T_W = max(z SE_W, q95_eff)``."""
    y, se = w.get("y"), w.get("se_w")
    eff = effective_q95(w)
    q95 = eff["q95_effective"]
    a = bool(_finite(y) and float(y) > 0.0)
    b = bool(_finite(y) and _finite(se) and float(se) > 0.0 and float(y) >= z_krit * float(se))
    c = bool(_finite(y) and _finite(q95) and float(y) >= float(q95))
    thr_terms = [z_krit * float(se)] if (_finite(se) and float(se) > 0.0) else []
    if _finite(q95):
        thr_terms.append(float(q95))
    thr = max(thr_terms) if len(thr_terms) == 2 else float("nan")
    return {"a_sign": a, "b_magnitude": b, "c_null_quantile": c, "window_pass": bool(a and b and c), "threshold_t": thr,
            "k": eff["k"], "q95_effective": eff["q95_effective"]}


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """H-32 gate on ONE entry's payload::

        {"entry": "H-32_mom1", "variant": "mom1", "direction": "positive", "z_krit": 1.6449,
         "windows": {"W1": {"y", "mean_ic", "se_w", "q95", "ceiling_k4", "threshold_frozen", "bounce_ic"|None}, "W2": {...}}}

    ``bounce_ic`` is only supplied for ``rev_gap``.  Deterministic and side-effect-free."""
    z = float(payload["z_krit"])
    windows = payload["windows"]
    labels: list[str] = []
    kill_windows: list[str] = []
    for wn, w in windows.items():
        ceil, thr = w.get("ceiling_k4"), w.get("threshold_frozen")
        if _finite(ceil) and _finite(thr) and float(ceil) >= float(thr):
            kill_windows.append(wn)
            labels.append(f"GL-012 Decke >= Schwelle in {wn} (ceiling_k4={float(ceil):.5f}, T_frozen={float(thr):.5f})")
    per_window: dict[str, Any] = {}
    all_pass = True
    for wn, w in windows.items():
        cond = window_conditions(w, z)
        per_window[wn] = cond
        all_pass = all_pass and cond["window_pass"]
        for key, name in (("a_sign", "(1a) y > 0"), ("b_magnitude", "(1b) y >= z_krit * SE_W"), ("c_null_quantile", "(1c) y >= q95_eff")):
            if not cond[key]:
                labels.append(f"{name} verfehlt in {wn} (y={w.get('y')!r}, SE_W={w.get('se_w')!r}, q95={w.get('q95')!r}, "
                              f"q95_eff={cond['q95_effective']!r}, k={cond['k']!r})")
    bounce_windows: list[str] = []
    for wn, w in windows.items():
        b, real = w.get("bounce_ic"), w.get("mean_ic")
        if _finite(b) and _finite(real) and abs(float(b)) >= abs(float(real)):
            bounce_windows.append(wn)
            labels.append(f"Artefakt Bounce in {wn}: |IC_bounce|={abs(float(b)):.5f} >= |Statistik|={abs(float(real)):.5f} -- KEIN PASS")
    bounce_kill = bool(bounce_windows)
    if kill_windows:
        verdict = "DROP"
        labels.append("GL-012 vor dem Verdikt (Selektionsdecke ueber der eingefrorenen Schwelle)")
    elif all_pass and not bounce_kill:
        verdict = "PASS"
        labels.append("vorlaeufig bis F-WEEK geschlossen (DEC-99 (7))")
    else:
        verdict = "DROP"
        if not all_pass:
            labels.append("C.10 hart: mindestens ein Fenster erfuellt (1a)-(1c) nicht")
    return {"verdict": verdict, "entry": payload.get("entry"), "variant": payload.get("variant"),
            "direction": payload.get("direction"), "labels": labels, "gl012_kill": bool(kill_windows),
            "kill_windows": kill_windows, "bounce_kill": bounce_kill, "bounce_windows": bounce_windows,
            "per_window": per_window, "c10_hard": True}
