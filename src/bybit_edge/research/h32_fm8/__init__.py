"""H-32 (A3-fm8) -- two-stage driver for the beta-neutral cross-sectional IC (DEC-99, DEC-94, DEC-96 E3).

Class W, capital-free.  One family F-H32 with K = 4 variants (mom1, mom2, mom4 positive, rev_gap negative); the
primary statistic is the mean weekly Spearman rank IC of the characteristic against the ``fm_neutral_8w``-neutralised
next-week outcome (``ic.apply_beta_control("fm_neutral_8w", ...)`` + ``ic.weekly_ic_series(..., "close_at_last")``,
i.e. the IC_res of the third version H-28..H-30), in the registered direction.

**Additive.**  This package and ``scripts/h32_fm8.py`` are new; ``wp13_xsec`` and ``wp7_universe`` (code hash of the A3
registration) are only imported, never changed; ``power_p1`` is only imported.

DEC-101 (H-32 registration, part 1) adds, additively: the universe filter ``universe.py`` (linear USDT perpetuals, in ALL
modes, before the cut), the scaled null of the test run (``estimators.scale_factor`` / ``q95_effective`` / ``scaled_replicates``,
used by ``testrun.py`` and ``gate.py``), the technical exactly-one-pilot lock and the runner / delisted-tree / universe pins
(``checks.py``, ``schema.py``), the q95 rule and the report-only ``power_line`` (``estimators.frozen_q95``,
``estimators.end_power_replicates``, ``powerline.py``), and the PP3 dry run ``pp3.py`` (no IC).

Modes (``scripts/h32_fm8.py``), every one of them gated before any data is read:

  * ``--prelaunch`` (``vorlauf.py``, ``nullsim.py``) -- Vorlauf v6, outcome-free: hard panel cut (``panel_cut.py``)
    BEFORE any calculation, windows P/W1/W2, factor-preserving null with 8 beta lead weeks, K = 4, calibration per
    window, frozen constants per window and variant (``sd_week``, ``se_mean``, ``e_se_rule``, ``null_mean``, ``q95``,
    ``ceiling_k4``, ``floor_fm8``, ``v_fm8``, K series) and ``m_P`` of the pilot period; ``--emit-template`` writes the
    skeleton of ``state/registered/h32_v1.yaml``.
  * ``--pilot`` (``pilot.py``) -- stage P: start lock, exactly-one-pilot lock, panel cut <= 2024-06-30, per variant mean
    fm8-IC, SE by rule P-1 (4), hand-over rule U (``handover.py``), selection-adjusted ``mu_sel`` as a mandatory double
    statement, DEC-53 artifacts, ``h32_pilot.json`` + sha256.
  * ``--pp3-dry-run`` (``pp3.py``) -- DEC-101 E6: start lock, runner pins, fingerprints, universe, K_fm8 series and window pins of P
    (cut 2024-06-30) and W1 / W2 (cut 2026-06-28) against the registration; no IC is computed.
  * ``--positive-control`` (``positive_control.py``) -- PRD 3.3.8 control, alone and before the test, synthetic returns
    on the real week shape, injection calibrated on the REALISED effect.
  * ``--run`` (``testrun.py``, ``gate.py``, ``pnull.py``, ``permutation.py``, ``fweek.py``) -- stage T on the handed-over
    variants only: pilot lock, replicate lock, panel cut <= 2026-06-28, pure gate function (T4), the binding p from the
    pinned v6 replicates of the factor-preserving null (DEC-99 p convention; max-p over W1/W2; the block permutation and the
    normal approximation are report-only), BH (denominator 4) and F-WEEK (BY, DEC-99 (7)) with the double statement m = 11.

DEC-100: ``delisted_tree.py`` / ``scripts/h32_build_delisted_tree.py`` build the ``panel_1d_delisted`` tree from the
Data-Harvest delisting register and backfill partitions; the modes quote and check ``delisting_register_sha256``.

Every number the run checks against the registered YAML is frozen (T5 pin, ``constants.py``).  Nothing here opens the
sealed files of the programme and nothing computes a raw IC, a lag profile or a beta-calibration IC.
"""
from __future__ import annotations
