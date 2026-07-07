"""Risk-limit tier-1->2 kink constants + band/bin configuration for H-09 (F-BUNCH).

This is the ``costs.py``-Analogon of the c17_c41_tradability package for the
KAPITALFREIE H-09 bunching mess-gate (registry "### H-09 · Risk-Limit-Tier-
Bunching", DEC-19). Every number here is BINDING per the registered
methodology; the CLI MAY override band-neutral run parameters (bootstrap reps,
seed) for tests, but a WEITER reading is ONLY gate-valid at the registered
point — see :func:`gate_assumptions_valid`.

Registered geometry (registry H-09, verbatim):

* Estimation band ``[0.40*K_s, 1.30*K_s)``, bin width ``0.01*K_s`` -> 90 bins.
* Counterfactual: polynomial degree 7, fitted EXCLUDING ``[0.90*K_s, 1.10*K_s)``.
* Bunching window ``B- = [0.95*K_s, 1.00*K_s)``,
  control window ``B+ = (1.00*K_s, 1.05*K_s]``.
* Excess-mass ratio ``b_hat`` via residual bootstrap (Chetty et al. 2011),
  500 reps; null: smooth polynomial density, ``b- = 0``.
* Placebo kinks ``P1 = 0.50*K_s``, ``P2 = 0.75*K_s`` (NOT in the FDR family).
* N-floor: cell valid only with >= 2,000 order observations in the estimation
  band AND counterfactual expectation in B- >= 50.
* Gate thresholds: bootstrap-p <= 0.05 after BH-FDR alpha=0.10 over F-BUNCH,
  ``b_hat- >= 1.0``, ``b_hat- - b_hat+ >= 0.5``,
  ``b_hat- > max(b_hat_P1, b_hat_P2)``.

KAPITALFREI: pure structural/behavioural measurement. No cost model, no
tradability column of any kind.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# K_s per symbol: Bybit USDT-Perp risk-limit tier-1 -> tier-2 notional kink.
#
# PLATZHALTER — vor echtem Lauf gegen aktuelle Bybit-Risk-Limit-Tabelle
# verifizieren, DEC-09-Muster, append-only Nachtrag erforderlich.
#
# Only BTCUSDT (K = 2,000,000 USDT, MMR 0.50% -> 0.56%) is quoted in the
# registry entry itself; the remaining four are conservative, plausible
# placeholders in the historically typical Bybit tier-1 range. The registered
# operationalisation addendum (dated, append-only, DEC-09 pattern) MUST fix
# the real values — including the check that K_s was CONSTANT over both
# windows W1/W2 — BEFORE the real run. Running with unverified placeholders
# would invalidate the affected cells (registry H-09 Selbstkill note).
# ---------------------------------------------------------------------------
RISK_LIMIT_TIER1_KINK_USDT: dict[str, float] = {
    "BTCUSDT": 2_000_000.0,  # registry example (MMR 0.50% -> 0.56%)
    "ETHUSDT": 1_500_000.0,  # PLATZHALTER (typical range 1.5M-2M USDT)
    "SOLUSDT": 1_000_000.0,  # PLATZHALTER
    "BNBUSDT": 500_000.0,    # PLATZHALTER
    "XRPUSDT": 500_000.0,    # PLATZHALTER
}

#: Symbols whose kink value is a PLACEHOLDER (not registry-quoted).
KINK_PLACEHOLDER_SYMBOLS: tuple[str, ...] = ("ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

KINK_PLACEHOLDER_NOTE = (
    "K_s-Werte fuer ETH/SOL/BNB/XRP sind PLATZHALTER — vor echtem Lauf gegen "
    "die aktuelle Bybit-Risk-Limit-Tabelle verifizieren (inkl. Konstanz ueber "
    "W1+W2), DEC-09-Muster, datierter append-only Operationalisierungs-"
    "Nachtrag erforderlich. Nur BTCUSDT=2.000.000 USDT ist registry-beziffert."
)

# --- Band / bin geometry (relative to K_s) ---------------------------------
BAND_LO_REL: float = 0.40   # estimation band lower bound (inclusive)
BAND_HI_REL: float = 1.30   # estimation band upper bound (exclusive)
BIN_WIDTH_REL: float = 0.01
N_BINS: int = 90            # (1.30 - 0.40) / 0.01

# --- Counterfactual ---------------------------------------------------------
POLY_DEGREE: int = 7
EXCLUDE_LO_REL: float = 0.90  # excluded from the polynomial fit (inclusive)
EXCLUDE_HI_REL: float = 1.10  # (exclusive)

# --- Bunching / control windows --------------------------------------------
BUNCH_LO_REL: float = 0.95   # B- = [0.95, 1.00) * K_s
BUNCH_HI_REL: float = 1.00
CTRL_LO_REL: float = 1.00    # B+ = (1.00, 1.05] * K_s
CTRL_HI_REL: float = 1.05

# --- Placebos (NOT part of the FDR family) ----------------------------------
PLACEBO_FRACTIONS: tuple[float, ...] = (0.50, 0.75)

# --- Bootstrap / significance ------------------------------------------------
N_BOOTSTRAP: int = 500       # registered residual-bootstrap reps
BOOT_P_MAX: float = 0.05     # per-cell significance threshold (after BH-FDR)
FDR_ALPHA: float = 0.10      # BH-FDR over F-BUNCH (10 cells, order-level)

# --- Gate thresholds ----------------------------------------------------------
B_MINUS_FLOOR: float = 1.0       # b_hat- >= 1.0
ASYMMETRY_FLOOR: float = 0.5     # b_hat- - b_hat+ >= 0.5

# --- N-floor (gate component) -------------------------------------------------
N_FLOOR_ORDERS: int = 2_000      # order observations in the estimation band
CF_EXPECTATION_FLOOR: float = 50.0  # counterfactual expectation in B-


def gate_assumptions_valid(
    *,
    n_bootstrap: int,
    poly_degree: int,
    n_floor_orders: int,
    cf_expectation_floor: float,
) -> bool:
    """Anti-gaming check (registry H-09: no band/bin/placebo/floor adaptation).

    A WEITER reading is ONLY gate-valid when the run used the registered
    methodology point:

    * ``n_bootstrap >= 500`` (registered residual-bootstrap reps not reduced),
    * ``poly_degree == 7`` (counterfactual degree not changed),
    * ``n_floor_orders >= 2000`` (order N-floor not lowered),
    * ``cf_expectation_floor >= 50`` (counterfactual B- floor not lowered).

    Band/bin/window/placebo geometry is NOT parameterised at run level (fixed
    module constants), so it cannot be gamed via the CLI. When this returns
    False the driver MUST set ``gate_valid_assumptions: false`` in the payload
    and any ``weiter_indication`` is void (a deviating setup would be a NEW
    hypothesis, not a goalpost shift on H-09).
    """
    return (
        (n_bootstrap >= N_BOOTSTRAP)
        and (poly_degree == POLY_DEGREE)
        and (n_floor_orders >= N_FLOOR_ORDERS)
        and (cf_expectation_floor >= CF_EXPECTATION_FLOOR)
    )
