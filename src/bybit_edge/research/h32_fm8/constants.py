"""H-32 constants with their sources (T5 pins: the registered YAML must repeat exactly these numbers).

Modules read them as attributes (``constants.N_PERM``) at call time, so a unit test can shrink the replicate counts of a
fixture run with ``monkeypatch.setattr`` while the pin checks keep comparing the YAML with the SAME (patched) value.
"""
from __future__ import annotations

from statistics import NormalDist

from .. import power_p1

#: ERSTFASSUNG 1.1: family F-H32, K = 4 variants, fixed order; direction registered per variant.
VARIANTS: tuple[str, ...] = ("mom1", "mom2", "mom4", "rev_gap")
DIRECTION: dict[str, str] = {"mom1": "positive", "mom2": "positive", "mom4": "positive", "rev_gap": "negative"}
SIGN: dict[str, int] = {"positive": 1, "negative": -1}
ENTRY: dict[str, str] = {v: f"H-32_{v}" for v in VARIANTS}
HYPOTHESIS = "H-32"
K_FAMILY = 4

MARKET_SYMBOL = "BTCUSDT"
#: ERSTFASSUNG 1.4: the registered beta control (DEC-86) and the delisting convention (DEC-74 (i)).
PRIMARY_STATISTIC = "fm_neutral_8w"
BETA_WINDOW_WEEKS = 8
CONVENTION = "close_at_last"
#: ERSTFASSUNG 1.6: eight beta lead weeks in front of every simulated window.
LEAD_WEEKS = 8

#: DEC-51 (1) / DEC-94 (1): alpha per window, one-sided; the critical value is a NUMBER in the YAML.
ALPHA = 0.05
Z_KRIT = power_p1.z_krit(ALPHA)               # 1.6448536...
Z_KRIT_YAML_DIGITS = 7
Z_POWER = power_p1.Z_POWER                    # Phi^-1(0.80) = 0.8416
MDE_FAKTOR = 2.4865                           # power line only, never a threshold (DEC-94 (1))
#: ERSTFASSUNG 1.7: 80 % band of the pilot point, normal, two-sided: Phi^-1(0.90).
BAND_Z = NormalDist().inv_cdf(0.90)           # 1.2816
BAND_LEVEL = 0.80
#: ERSTFASSUNG 1.8: minimum pilot t.
T_MIN = 2.0

SEED = 53
#: P-1 (4): stationary bootstrap, mean block 4 weeks, at least 1.000 replicates (DEC-53: seed registered).
MEAN_BLOCK = 4
N_BOOT_MIN = 1000
#: ERSTFASSUNG 1.6: factor-null replicates (v6 and the null re-check of the run), driftfree and drift 0.002.
N_REPS_MIN = 1000
#: ERSTFASSUNG 1.6: 95 % level of the window-mean quantile (P-1 (1): level 1 - alpha, not 0.9936).
NULL_LEVEL = 1.0 - ALPHA
#: ERSTFASSUNG 1.10 / DEC-74 (e): block-permutation p of the fm8 window mean.
N_PERM = 10_000
PERM_BLOCK = 4
#: run-time re-check of the frozen null constants (DEC-76 Task A item 3): +-10 %, absolute 1e-4 where the frozen value is ~0.
NULL_REL_TOL = 0.10
NULL_ABS_TOL = 1e-4

#: DEC-99 (3)/(8) + ERSTFASSUNG 1.2/1.3: the panel is cut before any calculation.
CUT_TEST = "2026-06-28"
CUT_PILOT = "2024-06-30"
#: ERSTFASSUNG 1.3: window calendar (week-start strings are compared with these bounds).
WINDOWS: dict[str, tuple[str, str]] = {
    "P": ("2022-04-18", CUT_PILOT),
    "W1": ("2024-07-01", "2025-06-30"),
    "W2": ("2025-07-01", CUT_TEST),
}
W_JUDGED: dict[str, int] = {"P": 114, "W1": 52, "W2": 50}
W_PILOT = 114
PILOT_FIRST_FORMATION = "2022-04-18"
PILOT_LAST_FORMATION = "2024-06-17"
PILOT_OUTCOME_FIRST = "2022-04-25"
PILOT_OUTCOME_LAST = "2024-06-24"
#: PRD 5.3 Kill (2) (ERSTFASSUNG 6): minimal K_t per window.
K_MIN: dict[str, int] = {"P": 117, "W1": 134, "W2": 134}
#: first / last outcome week of the judged windows (week starts), ERSTFASSUNG 1.3.
TEST_OUTCOME_FIRST = {"W1": "2024-07-08", "W2": "2025-07-14"}
TEST_OUTCOME_LAST = {"W1": "2025-06-30", "W2": "2026-06-22"}

#: DEC-74 (e) / ERSTFASSUNG 1.10: BH inside F-H32 (report-only, denominator 4), F-WEEK = BY alpha 0.10 (binding).
BH_ALPHA = 0.10
BH_DENOMINATOR = 4
BY_ALPHA = 0.10
#: DEC-99 (7): old count (m including the p = 1 entries of the third version), report-only double statement.
FWEEK_DOUBLE_M = 11

#: ERSTFASSUNG 4 (positive control, fixed in advance).
PC_SEEDS_SIGMA_G = tuple(range(2000, 2050))
PC_SEEDS_INJECT = tuple(range(1000, 1050))
PC_SEEDS_JUDGE = tuple(range(53, 253))
PC_WORLD_SD_TOL = 0.05
PC_INJECT_TOL = 0.05
PC_SD_RATIO_MAX = 1.10
PC_PASS_SHARE_MIN = 0.734
PC_NEG_PASS_MAX = 0.086
PC_INJECT_JUDGE_TOL = 0.10
PC_N_SECTORS = 8
#: PRD/DEC-89 sector shock relative to sigma_e (report-only world).
PC_PRD_SECTOR_REL = 0.375

# ----------------------------------------------------------------------------
# DEC-101 Teil 2 (Nachpruefung N-1, N-2): positive control in production configuration, injection target F
# ----------------------------------------------------------------------------

#: DEC-101 Teil 2 (N-1): the gate chain of the control uses the scaled null exactly as the test run does (DEC-101 E2); the YAML
#: block ``positive_control.null_scaling`` repeats exactly these texts.
PC_NULL_SCALING_RULE = ("wie Testlauf (DEC-101 E2); k je Seed aus der Wochen-SD der synthetischen Serie gegen sd_week")
PC_NULL_SCALING_REF = "DEC-101 Teil 2 (N-1)"
#: DEC-101 Teil 2 (N-2): the injection target F of the control (replaces only the target of ERSTFASSUNG 4; criteria (a)-(d), seeds and
#: world stay).  ``m_df`` = frozen null mean of the DRIFTFREE cell (the control world has drift 0), ``m`` = frozen ``null_mean`` (binding
#: cell), ``q95_eff(k_pred) = max(0, m) + k_pred (q95 - m)``; the injection aims at the REALISED fm8 effect of the binding window
#: (argmax over W of the target).
PC_INJECT_TARGET = ("realisierter fm8-Effekt im bindenden Fenster (argmax_W): Ziel_W = max(z_krit * SE_T,W + z_80 * SD_T,W - min(0, m_df,W), "
                    "q95_eff,W(k_pred,W) - m_df,W + z_80 * SD_T,W); m_df,W = eingefrorenes Null-Mittel der driftfreien Zelle (stress), "
                    "q95_eff,W(k_pred,W) = max(0, m_W) + k_pred,W * (q95_W,v - m_W), m_W = eingefrorenes null_mean (bindende Zelle), "
                    "k_pred,W = max(1, sqrt(v_fm8_W + F2_real) / sd_week_W,v), SE_T,W / SD_T,W wie Regel U")
PC_INJECT_LABEL = ("Injektionsziel F: Korrektur nach DEC-94 (3) (Review B-4/A-4, Nachpruefung N-2), vor jeder Pilot-Zahl")
PC_INJECT_REF = "DEC-101 Teil 2 (N-2)"

#: schema markers
#: DEC-101 Teil 2 (N-3, Review Nachpruefung N-3): rule U-4.  U-3 (Review A-4) made condition (ii) cover BOTH gate conditions --
#: (1b) with the null-mean credit and (1c); U-4 puts the scaled null of the test run (DEC-101 E2) into the (1c) term:
#: ``max(0, m_W) + k_pred,W (q95_W,v - m_W) + z_80 SD_T,W`` with ``k_pred,W`` from the pilot's F2_real.  The threshold on the pilot
#: point can only rise (direction: strictness, fixed before any pilot number); at ``k_pred = 1`` and ``m >= 0`` no number changes.
HANDOVER_VERSION = "U-4"
HANDOVER_COND_II = ("x_P >= max(m* + max_W(z_krit * SE_T,W + z_80 * SD_T,W), "
                    "max_W(max(0, m_W) + k_pred,W * (q95_W,v - m_W) + z_80 * SD_T,W))")
#: DEC-101 Teil 2 (N-3): ``k_pred`` is the prediction of the test run's scale factor from the pilot's F2_real -- the same quantity the
#: positive control calibrates its world SD on (N-2).  Before the pilot (power line of the Vorlauf) ``k_pred = 1``.
HANDOVER_K_PRED = "k_pred,W = max(1, sqrt(v_fm8_W + F2_real) / sd_week_W,v); before the pilot (power line of the Vorlauf) k_pred = 1"
HANDOVER_C_V = "c_v = max(MDE80*_U + m*, max_W(max(0, m_W) + k_pred,W * (q95_W,v - m_W) + z_80 * SD_T,W)) (U-4)"
PILOT_SCHEMA = "H-32 pilot result (DEC-99)"
RUN_SCHEMA = "H-32 test run (DEC-99, DEC-94)"
PC_SCHEMA = "H-32 positive control (PRD 3.3.8, DEC-94 (5))"
PRELAUNCH_SCHEMA = "H-32 Vorlauf v6 (outcome-free)"

PILOT_GL012 = "GL-012 (Pilot)"
PILOT_HANDED = "UEBERGEBEN"
#: DEC-101 Teil 2 (N-4): the attempt marker written BEFORE the panel is loaded (``<prefix>_attempt.json`` in the pinned pilot directory;
#: it matches ``PILOT_FILE_GLOB`` and carries the ``registered_sha256``, so the exactly-one-pilot lock sees an aborted attempt).
PILOT_ATTEMPT_SUFFIX = "_attempt"
PILOT_ATTEMPT_SCHEMA = "H-32 pilot attempt marker (DEC-101 Teil 2, N-4)"
PILOT_ATTEMPT_REF = "DEC-101 Teil 2 (N-4)"

#: DEC-99 amendment (p convention, binding): p_W,v is the exceedance share of the replicate window means of the v6
#: factor-preserving null (stress; the cell with the larger null mean of driftfree / drift).  The block permutation of the
#: real outcome rows and the normal approximation are report-only (DEC-76/77: market persistence contaminates permutations).
P_SOURCE = "factor_preserving_null_replicates"
P_STATISTIC = "null_replicate_exceedance_fm8_window_mean"
P_REPORT_ONLY = ("block_permutation_fm8_window_mean", "normal_approximation")
P_REPLICATES_SCHEMA = "H-32 null replicate window means for p (DEC-99, factor-preserving null)"
P_REPLICATES_FILE = "h32_prelaunch_p_replicates.json"
#: DEC-101 Teil 2 (N-5): the registered ``fdr.p_formula`` names the scaling of the replicates (DEC-101 E2, block ``null_scaling``).
P_FORMULA = ("p = (1 + #{scaled null replicate window means d' >= observed window mean y, registered direction}) / (1 + R), "
             "d' = max(0, m) + k * (d - m), k = max(1, SD(IC_t,W) / sd_week_W,v), m = frozen null_mean of the binding cell "
             "(DEC-101 E2, block null_scaling)")

#: the sealed file name patterns of the programme: no code path here opens a path matching one of them.
SEALED_PATTERNS: tuple[str, ...] = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")

# ----------------------------------------------------------------------------
# DEC-101 (H-32 registration, part 1): universe, scaled null, technical exactly-one-pilot lock, pins, q95 rule, PP3
# ----------------------------------------------------------------------------

#: DEC-101 E1 (V-1 (a)): the H-32 universe is the set of linear USDT perpetuals (symbol ends on ``USDT``, no ``-``).
UNIVERSE_RULE = "linear_usdt_perpetual"
UNIVERSE_CLASSES: tuple[str, ...] = ("usdc_perp", "dated_future", "other")
UNIVERSE_LABEL = ("Bereinigung (Strenge), beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl (DEC-101 E1)")
#: suffix of the earlier episode column of a relisted symbol in the union panel (``panel_load``): the episode belongs to the
#: same contract, the universe rule looks at the name in front of it.
EPISODE_SUFFIX = "#delisted"

#: DEC-101 E2 (A-1): scaled null in the test run; the YAML block ``null_scaling`` repeats exactly this rule text.
NULL_SCALING_RULE = ("k = max(1, SD(IC_t,W)/sd_week_W,v); q95_eff = max(0,m) + k*(q95 - m); "
                     "p from max(0,m) + k*(d - m)")
NULL_SCALING_DIRECTION = "strictness"
NULL_SCALING_REF = "DEC-101 E2"

#: DEC-101 E3 (A-2): the pilot writes below this repository-relative root; the YAML pins the exact directory.
RUNS_REL = "scinance3-impl/state/runs"
PILOT_OUT_DIR = "scinance3-impl/state/runs/h32_pilot_v1"
PILOT_FILE_GLOB = "h32_pilot*.json"

#: DEC-101 E5 (A-4): the frozen q95 is max(q95 of the constants replicates, empirical 95 % quantile of all p replicates of the
#: binding cell); numpy default (linear) interpolation.
Q95_QUANTILE_METHOD = "numpy.quantile(finite replicates, 0.95), linear interpolation (numpy default)"
#: DEC-101 E5: the numbers of tested entries m for which the power line states the end power after F-WEEK.
POWER_M_GRID: tuple[int, ...] = (1, 2, 3, 4, 11)

#: DEC-101 E6 (A-5): the PP3 dry run (no IC), its result file and schema marker.
PP3_SCHEMA = "H-32 PP3 dry run (DEC-101 E6)"
PP3_FILE = "h32_pp3_dry_run.json"
W1_CONTROL_NOTE = ("W1-Determinismus-Kontrolle gegen v5e: entfaellt (DEC-100 N1); Ersatz: Fixture-T2, Zweitlauf bitgleich, "
                   "PP3-Trockenprobe")

# ----------------------------------------------------------------------------
# DEC-101 Teil 2 (Nachpruefung N-5): documentation fields of the registration
# ----------------------------------------------------------------------------

#: The template names the code commit of the Vorlauf (v6b: 6e4b447) and the registration commit SEPARATELY (the changes since the
#: Vorlauf touch no frozen constant); the registration commit is set by the orchestrator.
CODE_COMMIT_PRELAUNCH_UNSET = "<nicht angegeben: --code-commit-prelaunch>"
CODE_COMMIT_REGISTRATION_PLACEHOLDER = "<wird vom Orchestrator gesetzt>"
CODE_COMMIT_NOTE = ("code_commit_prelaunch = Code-Stand, mit dem der Vorlauf gerechnet wurde (nur damit bitgleich reproduzierbar); "
                    "code_commit_registration = Code-Stand der Registrierung; die seitherigen Aenderungen beruehren keine eingefrorene "
                    "Konstante (nur Regeltexte, Gate-Kette der Positivkontrolle, Injektionsziel, Uebergaberegel, Pilot-Sperre)")

