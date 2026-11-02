"""SESOI (smallest effect size of interest) from the cost model, two frames, as a CURVE (DEC-104 E3 (a)).

Frames
------
* ``single_position`` (class E/P): the expected edge of a sign-following position is ``IC * 0.798 * sigma`` (Gauss
  consistent, Pearson IC).  Break-even IC: ``IC_min = c * w / (0.798 * sigma)`` with ``c`` the cost per sign change in bp,
  ``w = arccos(phi) / pi`` the sign-change rate of an AR(1) signal with persistence ``phi`` and ``sigma`` the SD of the
  return per decision period.  Reference (sigma 262 bp, Taker 11 bp): 0.0263 / 0.0175 / 0.0108 at phi 0 / 0.5 / 0.8.
* ``decile`` (class W, long/short top-minus-bottom decile): gross spread ``3.51 * IC * sigma_xs`` (3.51 = 2 E[z | top
  decile]); both legs pay ``c`` per unit turnover: ``IC_min = 2 c U / (3.51 sigma_xs)``.  Reference (sigma_xs 370 bp,
  Taker 11 bp, full turnover U = 1, i.e. phi = -1): 0.0169; with the persistence turnover ``U = arccos(phi) / pi`` the
  same formula gives 0.0085 / 0.0056 / 0.0035 at phi 0 / 0.5 / 0.8.
* ``direct``: premium statistics (A1, A2, VRP) carry the SESOI directly in units of the statistic.

Horizon: with a daily sigma the period sigma scales with ``sqrt(horizon_days)`` (random-walk scaling, label).
The rank option converts the Pearson break-even to a Spearman IC: ``rank = 6/pi * asin(pearson / 2)``.
Cost basis default is Taker (VIP0) with the label "fork towards testability against Maker" (DEC-104 E3 (a)).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .schema import FeasibilityInputError, SesoiCfg

__all__ = ["EDGE_FACTOR", "DECILE_FACTOR", "sign_change_rate", "ic_min_single_position", "ic_min_decile",
           "pearson_from_rank", "rank_from_pearson", "sesoi_curve", "resolve_sesoi", "SesoiResult", "COST_LABEL"]

EDGE_FACTOR = 0.798          # E[r sign(s)] = IC * 0.798 * sigma (K-1; sqrt(2/pi) = 0.7979)
DECILE_FACTOR = 3.51         # 2 * E[z | top decile] (L-18)
COST_LABEL = {"taker": "Taker (VIP0) - default; fork towards testability against Maker (DEC-104 E3 (a))",
              "maker": "Maker", "total": "total cost (Maker + Taker wall)"}


def sign_change_rate(phi: float) -> float:
    """Sign-change rate per period of an AR(1) signal with persistence ``phi`` in [-1, 1] (arccos(phi) / pi)."""
    if not -1.0 <= phi <= 1.0:
        raise FeasibilityInputError(f"persistence phi must be in [-1, 1], got {phi}")
    return math.acos(phi) / math.pi


def pearson_from_rank(ic_rank: float) -> float:
    return 2.0 * math.sin(math.pi * ic_rank / 6.0)


def rank_from_pearson(ic_pearson: float) -> float:
    if abs(ic_pearson) > 2.0:
        raise FeasibilityInputError("Pearson IC out of range")
    return 6.0 / math.pi * math.asin(ic_pearson / 2.0)


def _positive(x: float, name: str) -> float:
    if not (isinstance(x, (int, float)) and math.isfinite(x) and x > 0.0):
        raise FeasibilityInputError(f"{name} must be a positive number, got {x!r}")
    return float(x)


def ic_min_single_position(cost_bp: float, sigma_bp: float, phi: float | None = None, turnover: float | None = None,
                           rank: bool = False) -> float:
    """Break-even IC of the single-position frame (edge 0.798 sigma IC)."""
    c, s = _positive(cost_bp, "cost_bp"), _positive(sigma_bp, "sigma_bp")
    w = _turnover(phi, turnover)
    ic = c * w / (EDGE_FACTOR * s)
    return rank_from_pearson(ic) if rank else ic


def ic_min_decile(cost_bp: float, sigma_xs_bp: float, phi: float | None = None, turnover: float | None = None,
                  rank: bool = False) -> float:
    """Break-even IC of the decile long/short frame: ``2 c U / (3.51 sigma_xs)``."""
    c, s = _positive(cost_bp, "cost_bp"), _positive(sigma_xs_bp, "sigma_xs_bp")
    u = _turnover(phi, turnover)
    ic = 2.0 * c * u / (DECILE_FACTOR * s)
    return rank_from_pearson(ic) if rank else ic


def _turnover(phi: float | None, turnover: float | None) -> float:
    if turnover is not None:
        return _positive(turnover, "turnover")
    if phi is None:
        raise FeasibilityInputError("give phi or turnover")
    return sign_change_rate(phi)


@dataclass(frozen=True)
class SesoiResult:
    value: float
    unit: str
    label: str
    mode: str
    cost_side: str
    curve: list[dict]

    def as_dict(self) -> dict:
        by_key = {}
        for r in self.curve:
            key = f"{r['frame']}_{r['cost_side']}_h{r['horizon_days']:g}_phi{int(round(r['phi'] * 100))}"
            by_key[key.replace(".", "p")] = r["ic_min"]
        return {"value": self.value, "unit": self.unit, "label": self.label, "mode": self.mode,
                "cost_side": self.cost_side, "curve": self.curve, "curve_by_key": by_key}


def sesoi_curve(frame: str, costs_bp: dict[str, float], sigma_bp: float | None, sigma_daily_bp: float | None,
                phis: tuple[float, ...], horizons_days: tuple[float, ...] = (), default_horizon: float = 1.0,
                rank: bool = False) -> list[dict]:
    """Rows ``{frame, cost_side, cost_bp, horizon_days, phi, turnover, sigma_bp, ic_min}`` over cost side x horizon x phi."""
    if frame not in ("decile", "single_position"):
        raise FeasibilityInputError(f"unknown frame {frame!r}")
    fn = ic_min_decile if frame == "decile" else ic_min_single_position
    horizons = horizons_days or (default_horizon,)
    rows = []
    for side in ("maker", "taker", "total"):
        if side not in costs_bp:
            continue
        for h in horizons:
            if sigma_daily_bp is not None:
                sig = sigma_daily_bp * math.sqrt(h)
            elif sigma_bp is not None:
                sig = sigma_bp
            else:
                raise FeasibilityInputError("sesoi curve needs sigma_bp or sigma_daily_bp")
            for phi in phis:
                rows.append({"frame": frame, "cost_side": side, "cost_bp": costs_bp[side], "horizon_days": h, "phi": phi,
                             "turnover": sign_change_rate(phi), "sigma_bp": sig,
                             "ic_min": fn(costs_bp[side], sig, phi=phi, rank=rank)})
    return rows


def resolve_sesoi(cfg: SesoiCfg) -> SesoiResult:
    """SESOI value in units of the statistic, plus the curve over horizon and persistence when the frame is given."""
    costs = {k: v.value for k, v in cfg.cost_bp.items()}
    sigma = cfg.sigma_bp.value if cfg.sigma_bp is not None else None
    sigma_d = cfg.sigma_daily_bp.value if cfg.sigma_daily_bp is not None else None
    label = f"{cfg.label} | cost basis: {COST_LABEL[cfg.cost_side]}"
    curve: list[dict] = []
    frames: dict[str, tuple[float | None, float | None]] = {}
    if cfg.mode in ("decile", "single_position"):
        frames[cfg.mode] = (sigma, sigma_d)
    for fr, sv in cfg.curve_sigma_bp.items():
        frames.setdefault(fr, (sv.value, None))
    for fr, (sg, sgd) in frames.items():
        if not costs:
            raise FeasibilityInputError("sesoi curve needs cost_bp")
        curve += sesoi_curve(fr, costs, sg, sgd, cfg.curve_phis, cfg.curve_horizons_days, cfg.horizon_days, cfg.rank_ic)
    if cfg.mode == "direct":
        value = cfg.value.value
    else:
        sig = sigma_d * math.sqrt(cfg.horizon_days) if sigma_d is not None else sigma
        fn = ic_min_decile if cfg.mode == "decile" else ic_min_single_position
        value = fn(costs[cfg.cost_side], sig, phi=cfg.phi, turnover=cfg.turnover, rank=cfg.rank_ic)
    if not value > 0.0:
        raise FeasibilityInputError("SESOI must be > 0")
    return SesoiResult(float(value), cfg.unit, label, cfg.mode, cfg.cost_side, curve)
