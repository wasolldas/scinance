"""WP-13 -- Kohorte F-XSEC1 (H-28 Momentum, H-29 Reversal-Gap, H-30 Vol-
Anomalie), Klasse W, PRD 5.3, DEC-73/DEC-74.

**DEC-74 Entscheidung 3 -- Vorlauf WP-13a (this package's current scope).**
Only pipeline FUNCTIONS (characteristics, IC, permutation/persistence
nulls) plus ``scripts/wp13_xsec.py --prelaunch`` exist so far. The
prelaunch mode delivers exactly DEC-74 Entscheidung 2 points (a), (b)/(c),
(g), (h), the delisting-week symbol-week count of point (i), STRESS_REL
coverage, and the DEC-74 (j) fixtures -- and **never computes a real
characteristic-vs-real-next-week-return IC** (the "Siegel-Test", DEC-74
Entscheidung 3, verbatim: "keine reale Signal-Outcome-Verknuepfung"). The
run mode (the actual H-28/H-29/H-30 measurement against the registered
Zweitfassung) is future work, built only after that registration exists.

Modules:
  - ``characteristics.py`` -- pure, no I/O: the 7 F-XSEC1 variants (mom1/2/4,
    rev_gap, vol_rv, vol_max, vol_beta) plus the liquidity-turnover helpers
    Gate (5)/(f) need. Weekly arrays only (``wp7_universe`` convention:
    ``[n_weeks, n_symbols]``, ascending weeks, fixed symbol column order).
  - ``ic.py`` -- pure: the ONE Spearman-IC entry point every caller in this
    package uses (``weekly_ic_series``), both delisting conventions
    ("drop" / "close_at_last", PRD 4.1 DoD (4)), cross-sectional outcome
    demeaning (DEC-39 adversarial default), and the H-30 vol-weighted-
    outcome/drag helper. **THE SEAL** (task brief, verbatim): this function
    takes explicit ``(characteristic, returns, alive)`` arrays and is
    monkeypatch-observable -- ``--prelaunch`` never calls it with the real
    union panel's returns matrix as ``returns``.
  - ``nulls.py`` -- the analytic permutation floor (``E_t[1/sqrt(K_t-1)]``,
    tie-corrected) and the DEC-74 (b)/(c) persistence null (per-symbol
    AR(1), 1000 simulations, full per-variant pipeline, one-sided 95%
    quantile + lag1..4 autocorrelation -> ``c_rho``), plus the (a)/(d)
    threshold arithmetic.
  - ``prelaunch.py`` -- assembles the DEC-74 (a)-(k) prelaunch report +
    DEC-53 artifacts for W1/W2/L; reuses ``wp7_universe.panel_load``'s
    union loader, never reimplements it.
"""
from __future__ import annotations
