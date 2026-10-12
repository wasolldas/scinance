"""WP-13 run mode -- pure gate arithmetic (PRD 5.3 Gate-Text (1)-(7),
DEC-75 Entscheidung 1 (1)-(7), DEC-87 (I) and Gate (5)).

**Pure by construction.** :func:`evaluate` takes ONE already-computed
``payload`` dict (numbers only -- means, SEs, CI bounds, p-values,
thresholds) and returns a verdict. No I/O, no randomness, no access to
``characteristics``/``ic``/``nulls`` -- every number in ``payload`` was
computed elsewhere (``run.py``) and handed in already-conserved. This is
what the task brief's T4 ("gate arithmetic in a pure function
``gates.evaluate(payload) -> verdict dict`` with a T4 test on a conserved
payload") asks for: the SAME payload, re-evaluated twice, must give the
IDENTICAL verdict (trivially true for a pure function, but the T4 test
exists to catch a future regression that sneaks in hidden state).

**Gate components, DEC-75 Entscheidung 1, verbatim mapping.**
  (1) SE = ``max(floor, SD(IC_t)) / sqrt(W_judged)``; PASS requires
      ``|mean_ic| >= 2.4865 * SE`` AND the sign-facing one-sided CI bound
      (level ``1 - 0.0064``, moving-block bootstrap) beyond 0, AND
      ``|mean_ic| >= IC_min_capped`` -- **in BOTH windows** (C.10 hard,
      the registered per-hypothesis fixed rule, DEC-52's controlled
      single-window exception is NOT wired here because A3 was found to
      run under C.10 hard, PRD 5.3/DEC-73).
  (2) Selection ceiling is a PRE-VERDICT KILL, not a PASS component:
      ``ceiling >= IC_min_capped`` on EITHER window -> GL-012, verdict forced
      DROP with that label, checked BEFORE the PASS logic (DEC-75, verbatim:
      "Kill: Decke >= IC_min -> GL-012 vor dem Verdikt"). **DEC-87 (A):** the
      ceiling is the registered method's mean-of-max under the window's STRESS
      calibration (``windows.<W>.ceiling_method_stress``), not the v3 TS-
      residualisation line (historical, not binding).
  (3) Beta-control (market-residualised outcome) is an ADDITIONAL PASS
      component (DEC-75 Entscheidung 1 (3)): same sign, ``|residualized_
      mean_ic| >= IC_min_capped``, both windows. **DEC-76 Entscheidung 1
      (b), additive:** the residualised mean IC must ALSO lie beyond the
      null's own residualised-mean-IC one-sided 99.36% quantile in the
      registered direction. **DEC-87 (E):** that quantile is the more extreme
      of the driftfree and the drifting (0.002/week) stress-null quantile --
      the payload carries it as ``res_quantile_binding`` (a payload that only
      has the older ``res_quantile_drifting`` key is judged against that value,
      backward compatible). A payload window WITHOUT any quantile trivially
      satisfies this component; present quantile but no residualised IC fails
      closed.
  (4) H-30-specific (vol-weighted outcome) is computed upstream in ``run.py``
      -- the SAME (1)/(3) machinery applies to its own variant's numbers.
  (4') **DEC-87 (I), PRD-Kills (3)/(4) back in force (DEC-75 (5): "PRD-Kills (3)
      und (4) zurueck" means REINSTATED, "Etikett Artefakt, KEIN PASS").**
      *Bounce, per window:* ``|IC_bounce,W| >= |IC_W|`` in ANY window -> the
      verdict is NOT PASS (DROP) with the label ``Artefakt Bounce``. *Liquidity
      sensitivity, label only:* ``IC_ohne_D1,W`` not beyond half of that
      window's ``IC_min`` (``> -0.5*IC_min`` for a negative registration, ``<
      +0.5*IC_min`` for a positive one) in AT LEAST ONE window -> label
      ``Illiquiditaets-Artefakt`` (the pre-DEC-87 code labelled the opposite
      case and looked at W1 only), verdict unchanged. *Survivorship* stays a
      label (DEC-76: the union panel makes "not reconstructible" false).
  (5) **Gate (5), H-30 only:** the window payload carries
      ``gate5_median_spearman`` (median over weeks of Spearman(rank of the
      characteristic, rank of the trailing 8-week median turnover),
      ``characteristics.characteristic_turnover_spearman``); it must be
      ``< GATE5_SPEARMAN_MAX`` (0.60) in each judged window or the window --
      and so the variant -- fails. Absent/``None`` = not applicable (non-H-30);
      NaN fails closed.
  (6) Gate (2) persistence-null and Gate (3) BH-FDR are REPORT-ONLY
      (DEC-75 Entscheidung 1 (6)): their comparison booleans are attached as
      labels, never gate inputs.

``bounce_ic`` and ``liquidity_ic_without_d1`` in the payload are either a
float (the same number for every window, the pre-DEC-87 shape) or a dict
``{"W1": float, "W2": float}`` (what ``run.run_full`` supplies).
"""
from __future__ import annotations

import math
from typing import Any

__all__ = ["Z_PER_WINDOW", "GATE5_SPEARMAN_MAX", "evaluate"]

Z_PER_WINDOW = 2.4865

#: DEC-74 (g) / PRD 5.3 Gate (5): mirrors ``characteristics.GATE5_SPEARMAN_MAX``
#: (gates.py stays import-free so it is purely arithmetic).
GATE5_SPEARMAN_MAX = 0.60


def _window_pass(w: dict[str, Any], direction: str, ic_min_capped: float) -> dict[str, Any]:
    mean_ic = w["mean_ic"]
    se = w["se"]
    ci_bound = w["ci_bound_toward_sign"]
    resid_ic = w.get("residualized_mean_ic")
    # DEC-87 (E): the binding quantile (more extreme of driftfree/drifting); the pre-DEC-87
    # single `res_quantile_drifting` key is the fallback (backward compatible).
    resid_quantile = w.get("res_quantile_binding", w.get("res_quantile_drifting"))
    gate5_value = w.get("gate5_median_spearman")

    sign_ok = (mean_ic > 0) if direction == "positive" else (mean_ic < 0)
    magnitude_ok = abs(mean_ic) >= Z_PER_WINDOW * se if se and not math.isnan(se) else False
    ci_ok = (ci_bound > 0) if direction == "positive" else (ci_bound < 0)
    ic_min_ok = abs(mean_ic) >= ic_min_capped

    resid_sign_ok = (resid_ic is not None) and ((resid_ic > 0) if direction == "positive" else (resid_ic < 0))
    resid_magnitude_ok = (resid_ic is not None) and (abs(resid_ic) >= ic_min_capped)

    # DEC-76 Entscheidung 1 (b): additive -- absent quantile (older/unit-test payload)
    # trivially satisfies this component; present but no residualized IC to compare fails
    # closed (never silently PASS on missing data).
    if resid_quantile is None:
        resid_beyond_null_ok = True
    elif resid_ic is None:
        resid_beyond_null_ok = False
    else:
        resid_beyond_null_ok = (resid_ic > resid_quantile) if direction == "positive" else (resid_ic < resid_quantile)

    # Gate (5): None = not applicable; NaN fails closed.
    if gate5_value is None:
        gate5_ok = True
    else:
        gate5_ok = (not math.isnan(gate5_value)) and gate5_value < GATE5_SPEARMAN_MAX

    window_pass = (sign_ok and magnitude_ok and ci_ok and ic_min_ok
                   and resid_sign_ok and resid_magnitude_ok and resid_beyond_null_ok and gate5_ok)
    return {
        "sign_ok": sign_ok, "magnitude_ok": magnitude_ok, "ci_ok": ci_ok, "ic_min_ok": ic_min_ok,
        "beta_control_sign_ok": resid_sign_ok, "beta_control_magnitude_ok": resid_magnitude_ok,
        "beta_control_beyond_drifting_null_ok": resid_beyond_null_ok,
        "gate5_ok": gate5_ok,
        "window_pass": window_pass,
    }


def _by_window(value: Any, window_names: list[str]) -> dict[str, float | None]:
    """A payload scalar is the SAME number for every window (pre-DEC-87 shape);
    a dict is per window; ``None`` means "not supplied"."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {wn: value.get(wn) for wn in window_names}
    return {wn: value for wn in window_names}


def _finite(x: Any) -> bool:
    return x is not None and math.isfinite(float(x))


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """PRD 5.3 / DEC-75 Entscheidung 1 (1)-(7) + DEC-87 gate arithmetic on ONE
    hypothesis-variant's already-computed numbers.

    Expected ``payload`` shape::

        {
          "hypothesis": "H-28", "variant": "mom1", "direction": "positive",
          "windows": {
            "W1": {"mean_ic": float, "se": float, "ci_bound_toward_sign": float,
                    "ic_min_capped": float, "residualized_mean_ic": float,
                    "res_quantile_binding": float | None,   # DEC-87 (E), optional/additive
                    "res_quantile_drifting": float | None,  # DEC-76 (b) fallback
                    "gate5_median_spearman": float | None,  # DEC-87 Gate (5), H-30 only
                    "selection_ceiling_mean_of_max": float,
                    "block_permutation_p": float},
            "W2": {...},
          },
          "persistence_null_pass": bool | None,     # report-only, Gate (2)
          "bh_fdr_pass": bool | None,                # report-only, Gate (3)
          "liquidity_ic_without_d1": float | {W: float} | None,   # H-29 label
          "bounce_ic": float | {W: float} | None,                 # H-29 KEIN PASS
        }

    Returns ``{"verdict": "PASS"|"DROP", "hypothesis", "variant", "labels":
    [...], "gl012_kill": bool, "bounce_kill": bool, "liquidity_label": bool,
    "per_window": {...}}``. Deterministic and side-effect-free: calling this
    twice on the SAME payload gives the IDENTICAL dict (T4)."""
    direction = payload["direction"]
    windows = payload["windows"]
    window_names = list(windows)
    labels: list[str] = []

    gl012_kill = False
    for wname, w in windows.items():
        ceiling = w.get("selection_ceiling_mean_of_max")
        ic_min = w["ic_min_capped"]
        if ceiling is not None and not math.isnan(ceiling) and ceiling >= ic_min:
            gl012_kill = True
            labels.append(f"GL-012 Decke >= IC_min in {wname} (Decke={ceiling:.5f}, IC_min={ic_min:.5f})")

    per_window: dict[str, Any] = {}
    all_windows_pass = True
    for wname, w in windows.items():
        res = _window_pass(w, direction, w["ic_min_capped"])
        per_window[wname] = res
        all_windows_pass = all_windows_pass and res["window_pass"]
        if not res["gate5_ok"]:
            labels.append(f"Gate (5) verfehlt in {wname}: Median Spearman(Rang, Turnover-Rang)="
                          f"{w.get('gate5_median_spearman')!r} nicht < {GATE5_SPEARMAN_MAX:.2f} (DEC-74 (g))")

    # DEC-87 (I): bounce per window -- |IC_bounce,W| >= |IC_W| in ANY window -> not PASS.
    bounce_by_w = _by_window(payload.get("bounce_ic"), window_names)
    bounce_windows: list[str] = []
    for wname in window_names:
        b, real = bounce_by_w.get(wname), windows[wname].get("mean_ic")
        if _finite(b) and _finite(real) and abs(b) >= abs(real):
            bounce_windows.append(wname)
            labels.append(f"Artefakt Bounce in {wname}: |IC_bounce|={abs(b):.5f} >= |IC|={abs(real):.5f} -- "
                          "KEIN PASS (DEC-75 (5), DEC-87 (I))")
    bounce_kill = bool(bounce_windows)

    if gl012_kill:
        verdict = "DROP"
        labels.append("GL-012 vor dem Verdikt (DEC-75 Entscheidung 1 (2))")
    elif all_windows_pass and not bounce_kill:
        verdict = "PASS"
    else:
        verdict = "DROP"
        if not all_windows_pass:
            labels.append("C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht")

    # report-only components (DEC-75 Entscheidung 1 (6)) -- attached as labels, NEVER gate inputs
    if payload.get("persistence_null_pass") is False:
        labels.append("Persistenz-Null (Gate 2) nicht bestanden -- report-only, nicht bindend")
    if payload.get("bh_fdr_pass") is False:
        labels.append("BH-FDR (Gate 3) nicht bestanden -- report-only, nicht bindend")

    # A3-R liquidity-decile sensitivity (PRD 5.3 Gate-Text (4)): the finding must SURVIVE the exclusion
    # of the lowest-turnover decile; if it does not (in at least one window) the reading is restricted.
    liq_by_w = _by_window(payload.get("liquidity_ic_without_d1"), window_names)
    liq_windows: list[str] = []
    for wname in window_names:
        liq = liq_by_w.get(wname)
        if not _finite(liq):
            continue
        half = 0.5 * windows[wname]["ic_min_capped"]
        gone = (liq > -half) if direction == "negative" else (liq < half)
        if gone:
            liq_windows.append(wname)
            bound = f"-0.5*IC_min={-half:.5f}" if direction == "negative" else f"+0.5*IC_min={half:.5f}"
            labels.append(f"Illiquiditaets-Artefakt (H-16-Muster) in {wname}: IC_ohne_D1={liq:.5f} nicht jenseits "
                          f"{bound} -- Verdikt steht, Lesart eingeschraenkt")
    liquidity_label = bool(liq_windows)

    return {
        "verdict": verdict, "hypothesis": payload.get("hypothesis"), "variant": payload.get("variant"),
        "direction": direction, "labels": labels, "gl012_kill": gl012_kill,
        "bounce_kill": bounce_kill, "bounce_windows": bounce_windows,
        "liquidity_label": liquidity_label, "liquidity_windows": liq_windows,
        "per_window": per_window, "c10_hard": True,
    }
