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

#: schema markers
HANDOVER_VERSION = "U-2"
PILOT_SCHEMA = "H-32 pilot result (DEC-99)"
RUN_SCHEMA = "H-32 test run (DEC-99, DEC-94)"
PC_SCHEMA = "H-32 positive control (PRD 3.3.8, DEC-94 (5))"
PRELAUNCH_SCHEMA = "H-32 Vorlauf v6 (outcome-free)"

PILOT_GL012 = "GL-012 (Pilot)"
PILOT_HANDED = "UEBERGEBEN"

#: the sealed file name patterns of the programme: no code path here opens a path matching one of them.
SEALED_PATTERNS: tuple[str, ...] = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")
