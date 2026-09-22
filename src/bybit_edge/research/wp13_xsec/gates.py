"""WP-13 run mode -- pure gate arithmetic (PRD 5.3 Gate-Text (1)-(7),
DEC-75 Entscheidung 1 (1)-(7)).

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
  (2) Selection ceiling (factor-preserving null, mean-of-max, real K
      series) is a PRE-VERDICT KILL, not a PASS component: ``ceiling >=
      IC_min_capped`` on EITHER window -> GL-012, verdict forced DROP
      with that label, checked BEFORE the PASS logic (DEC-75, verbatim:
      "Kill: Decke >= IC_min -> GL-012 vor dem Verdikt").
  (3) Beta-control (market-residualised outcome) is an ADDITIONAL PASS
      component (DEC-75 Entscheidung 1 (3)): same sign, ``|residualized_
      mean_ic| >= IC_min_capped``, both windows.
  (4) H-30-specific (vol-weighted outcome) is computed upstream in
      ``run.py`` -- the SAME (1)/(3) machinery applies to its own
      variant's ``mean_ic``/``residualized_mean_ic`` here, nothing
      H-30-specific belongs in this module.
  (5) PRD Kills (3)/(4) (survivorship / bounce) are WITHDRAWN as gate
      conditions (DEC-75 Entscheidung 1 (5), verbatim: "PRD-Kills (3) und
      (4) zurueck") -- ``bounce_label``/``survivorship_label`` are
      REPORT-ONLY string labels attached to the verdict, never boolean
      gate inputs. H-29 specifically: if the bounce-fixture's ``|IC_
      bounce| >= |IC_real|``, the label ``"artefakt_bounce"`` is attached
      (PRD 5.3, still verbatim for the LABEL, just not for the KILL).
  (6) Gate (2) persistence-null and Gate (3) BH-FDR are REPORT-ONLY
      (DEC-75 Entscheidung 1 (6), verbatim: "Gate (2) Persistenz-Null und
      Gate (3) BH ... sind report-only (protokolliert: nie bindend)") --
      their comparison booleans are attached as labels, never gate
      inputs.
  (f) A3-R liquidity-decile sensitivity: ``IC_ohne_D1 > -0.5*IC_min`` is
      a LABEL rule (PRD 5.3 Gate-Text (4): "faellt er dort weg, ist der
      Befund eine Illiquiditaets-Artefakt-Messung ... Verdikt steht,
      Lesart eingeschraenkt") -- verdict UNCHANGED, reading restricted.
"""
from __future__ import annotations

import math
from typing import Any

__all__ = ["Z_PER_WINDOW", "evaluate"]

Z_PER_WINDOW = 2.4865


def _window_pass(w: dict[str, Any], direction: str, ic_min_capped: float) -> dict[str, Any]:
    mean_ic = w["mean_ic"]
    se = w["se"]
    ci_bound = w["ci_bound_toward_sign"]
    resid_ic = w.get("residualized_mean_ic")

    sign_ok = (mean_ic > 0) if direction == "positive" else (mean_ic < 0)
    magnitude_ok = abs(mean_ic) >= Z_PER_WINDOW * se if se and not math.isnan(se) else False
    ci_ok = (ci_bound > 0) if direction == "positive" else (ci_bound < 0)
    ic_min_ok = abs(mean_ic) >= ic_min_capped

    resid_sign_ok = (resid_ic is not None) and ((resid_ic > 0) if direction == "positive" else (resid_ic < 0))
    resid_magnitude_ok = (resid_ic is not None) and (abs(resid_ic) >= ic_min_capped)

    window_pass = sign_ok and magnitude_ok and ci_ok and ic_min_ok and resid_sign_ok and resid_magnitude_ok
    return {
        "sign_ok": sign_ok, "magnitude_ok": magnitude_ok, "ci_ok": ci_ok, "ic_min_ok": ic_min_ok,
        "beta_control_sign_ok": resid_sign_ok, "beta_control_magnitude_ok": resid_magnitude_ok,
        "window_pass": window_pass,
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """PRD 5.3 / DEC-75 Entscheidung 1 (1)-(7) gate arithmetic on ONE
    hypothesis's already-computed numbers.

    Expected ``payload`` shape::

        {
          "hypothesis": "H-28", "variant": "mom1", "direction": "positive",
          "windows": {
            "W1": {"mean_ic": float, "se": float, "ci_bound_toward_sign": float,
                    "ic_min_capped": float, "residualized_mean_ic": float,
                    "selection_ceiling_mean_of_max": float,
                    "block_permutation_p": float},
            "W2": {...},
          },
          "persistence_null_pass": bool | None,     # report-only, Gate (2)
          "bh_fdr_pass": bool | None,                # report-only, Gate (3)
          "liquidity_ic_without_d1": float | None,   # A3-R only
          "bounce_ic": float | None,                 # A3-R/H-29 only
        }

    Returns ``{"verdict": "PASS"|"DROP", "hypothesis", "variant", "labels":
    [...], "gl012_kill": bool, "per_window": {...}}``. Deterministic and
    side-effect-free: calling this twice on the SAME payload gives the
    IDENTICAL dict (T4)."""
    direction = payload["direction"]
    windows = payload["windows"]
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

    if gl012_kill:
        verdict = "DROP"
        labels.append("GL-012 vor dem Verdikt (DEC-75 Entscheidung 1 (2))")
    elif all_windows_pass:
        verdict = "PASS"
    else:
        verdict = "DROP"
        labels.append("C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3) nicht")

    # report-only components (DEC-75 Entscheidung 1 (6)) -- attached as labels, NEVER gate inputs
    if payload.get("persistence_null_pass") is False:
        labels.append("Persistenz-Null (Gate 2) nicht bestanden -- report-only, nicht bindend")
    if payload.get("bh_fdr_pass") is False:
        labels.append("BH-FDR (Gate 3) nicht bestanden -- report-only, nicht bindend")

    # A3-R liquidity-decile sensitivity label (PRD 5.3 Gate-Text (4)) -- reading, not verdict
    liq = payload.get("liquidity_ic_without_d1")
    ic_min_w1 = windows.get("W1", {}).get("ic_min_capped")
    if liq is not None and ic_min_w1 is not None and not math.isnan(liq):
        if liq <= -0.5 * ic_min_w1:
            labels.append(f"Illiquiditaets-Artefakt (H-16-Muster): IC_ohne_D1={liq:.5f} <= "
                           f"-0.5*IC_min={-0.5 * ic_min_w1:.5f} -- Verdikt steht, Lesart eingeschraenkt")

    # H-29 bounce-fixture label (DEC-75 Entscheidung 1 (5), verdict WITHDRAWN as a kill, label only)
    bounce_ic = payload.get("bounce_ic")
    real_ic_w1 = windows.get("W1", {}).get("mean_ic")
    if bounce_ic is not None and real_ic_w1 is not None:
        if abs(bounce_ic) >= abs(real_ic_w1):
            labels.append(f"Artefakt-Etikett (H-29 Bounce): |IC_bounce|={abs(bounce_ic):.5f} >= "
                           f"|IC_real|={abs(real_ic_w1):.5f} -- KEIN PASS-Kill (DEC-75 (5)), nur Etikett")

    return {
        "verdict": verdict, "hypothesis": payload.get("hypothesis"), "variant": payload.get("variant"),
        "direction": direction, "labels": labels, "gl012_kill": gl012_kill,
        "per_window": per_window, "c10_hard": True,
    }
