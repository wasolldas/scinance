"""WP-13 -- Kohorte F-XSEC1 (H-28 Momentum, H-29 Reversal-Gap, H-30 Vol-
Anomalie), Klasse W, PRD 5.3, DEC-73/DEC-74/DEC-75.

**DEC-74/DEC-75 -- two modes, one package.**
  - ``scripts/wp13_xsec.py --prelaunch``: DEC-74 Entscheidung 2 + DEC-75
    Entscheidung 2 (Vorlauf v2 -- W_judged, bias-corrected/capped c_rho,
    factor-preserving null, H-30 feasibility v2, survivorship-drawdown
    report line). **Never computes a real characteristic-vs-real-next-
    week-return IC** (the "Siegel-Test", DEC-74 Entscheidung 3, verbatim:
    "keine reale Signal-Outcome-Verknuepfung") -- see ``ic.py``'s "THE
    SEAL" docstring, enforced structurally and tested (``test_seal_*`` in
    ``tests/unit/test_wp13_xsec.py``).
  - ``scripts/wp13_xsec.py --run --registered <yaml> --registered-sha256
    <hex>``: DEC-75 Entscheidung 1 (the real H-28/H-29/H-30 measurement),
    gated by a START LOCK (``run.py``'s module docstring) that refuses to
    run unless the given sha256 matches the ``--registered`` YAML.

Modules:
  - ``characteristics.py`` -- pure, no I/O: the 7 F-XSEC1 variants (mom1/2/4,
    rev_gap, vol_rv, vol_max, vol_beta) plus the liquidity-turnover helpers
    Gate (5)/(f) need. Weekly arrays only (``wp7_universe`` convention:
    ``[n_weeks, n_symbols]``, ascending weeks, fixed symbol column order).
  - ``ic.py`` -- pure: the ONE Spearman-IC entry point every caller in this
    package uses (``weekly_ic_series``), both delisting conventions
    ("drop" / "close_at_last", PRD 4.1 DoD (4)), cross-sectional outcome
    demeaning (DEC-39 adversarial default), the H-30 vol-weighted-
    outcome/drag helper (v2, DEC-75 (4)) and the beta-control
    residualisation (``residualize_outcome``, DEC-75 (3)). **THE SEAL**
    (task brief, verbatim): this function takes explicit
    ``(characteristic, returns, alive)`` arrays and is monkeypatch-
    observable -- ``--prelaunch`` never calls it with the real union
    panel's returns matrix as ``returns``.
  - ``nulls.py`` -- the analytic permutation floor (``E_t[1/sqrt(K_t-1)]``,
    over the JUDGED weeks), the DEC-74 (b)/(c) persistence null
    (bias-corrected + capped ``c_rho``), the DEC-75 (2)/(3) factor-
    preserving null (simulated ``beta_i*f_t+e_it`` panel) and the
    run-mode block-permutation p-value, plus the (a)/(d)/(8) threshold
    arithmetic (``ic_threshold``, capped vs raw).
  - ``prelaunch.py`` -- assembles the DEC-74/DEC-75 prelaunch report +
    DEC-53 artifacts for W1/W2/L; reuses ``wp7_universe.panel_load``'s
    union loader, never reimplements it.
  - ``run.py`` -- the run-mode pipeline (SE, moving-block bootstrap CI,
    Max-p, liquidity-decile sensitivity, bounce fixture, lag profile, BH)
    and the top-level orchestrator ``run_full``; the CLI owns the START
    LOCK and all I/O.
  - ``gates.py`` -- pure gate arithmetic (``evaluate(payload) -> verdict``)
    on an already-computed payload, no I/O, no randomness.

**DEC-77 -- Vorlauf v4 (additive, all in ``nulls.py``/``ic.py``/
``prelaunch.py``/``run.py``).** The Vorlauf v3 finding (DEC-77 "Anlass"):
market persistence ALONE (``rho_f``, no drift needed) already produces a
mechanical cross-sectional momentum artifact the 8-week beta
residualisation does not remove. Vorlauf v4 (a) CALIBRATES the
factor-null's ``rho_f``/``sigma_f`` (single-series) and ``factor_share``/
beta-dispersion (returns-vs-beta, ``ic.py``'s "THE SEAL" allowed
category) from the real panel (``nulls.factor_calibration_report``), (b)
runs NINE beta-control METHODS (``ic.BETA_CONTROL_METHODS`` --
time-series/Fama-MacBeth residualisation and double-sort characteristic
neutralisation at 8/13/26 weeks, plus ``"none"``) x THREE rho_f/beta-draw
calibrations (``measured``/``stress``/``zero``, ``nulls.
beta_control_method_study``) x the 7 F-XSEC1 variants, and (c) applies
DEC-77's PRE-FIXED PASS/FAIL rule (``prelaunch.beta_control_pass_table``)
to recommend a method (``prelaunch.beta_control_recommendation``). Run
mode reads the REGISTERED ``beta_control: {method, beta_window_weeks}``
(``run.py``'s ``run_full``, C.14 loud fail if missing/empty/unknown) and
applies EXACTLY that method via ``ic.apply_beta_control`` -- the SAME
dispatcher the calibration study uses.
"""
from __future__ import annotations
