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
"""
from __future__ import annotations
