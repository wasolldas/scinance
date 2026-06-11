"""36-feature causal feature engineering for the C-42 vol-regression repro (WP-4).

Reproduces the Kestrel "36-feature 1m-snapshot" feature set that fed the one
positive OOS finding of the whole project: the LightGBM regression on
``log(realised_vol_60m)`` (Test R^2 = 0.249, ``research_notes.md`` §"Volatility
prediction"). The original code (`kestrel.features.bars`) is not in this repo,
so the notes are the only source of truth for the feature list.

Source coverage (see module-level ``FEATURE_PROVENANCE``):

- DOCUMENTED in research_notes.md:
    * ``atr_60``        — explicitly named, ranked #1 with 35.8 % gain.
    * trade-flow family — named generically ("trade-flow features", 38 % of
      total gain) but NOT individually enumerated. We materialise a standard
      microstructure trade-flow block and mark every member ASSUMED, because
      the notes give the *family* but not the *members*.
- ASSUMED (filled from standard realised-volatility literature, every one
  tagged with an ``ASSUMED:`` comment below and listed in ``FEATURE_PROVENANCE``):
    lagged realised vol over multiple horizons, bipower variation, jump
    component, return moments (skew/kurtosis), volume features, intraday
    seasonality. These are the canonical RV-forecasting inputs (HAR-RV,
    Barndorff-Nielsen/Shephard bipower, Andersen et al. realised moments).

Causality discipline (critical — H-02 No-Lookahead):

- Every feature at bar index ``i`` is a function of bars ``[..., i]`` ONLY,
  i.e. of information available at the CLOSE of bar ``i``. No future bar ever
  enters a feature. The feature *timestamp* is the close timestamp of bar ``i``
  (``ts`` column == kline close-minute epoch ms). The target
  (``target.py``) is forward-looking from ``i+1`` onward, so feature[i] and
  target[i] never share a bar — see ``target.py`` for the no-overlap proof.
- Rolling windows use ``min_periods = window`` so the first ``window-1`` rows
  are NaN rather than computed from a short (look-ahead-equivalent) window;
  those rows are dropped by the pipeline before fitting.

All computation is deterministic and pandas/numpy only (no model deps here).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

#: Bars per hour at 1-minute resolution — the "60m" horizon of the target.
BARS_PER_HOUR = 60

#: Annualisation is intentionally NOT applied: the target is log realised vol
#: over a fixed 60-minute forward window, so features live on the same
#: per-minute-return scale (research_notes uses raw realised vol, not annualised).

#: Multi-horizon lookback windows (in 1-min bars) for the lagged-RV block.
#: ASSUMED horizons — chosen to span the HAR-RV daily/weekly span at minute
#: granularity plus the target's own 60m scale.
RV_HORIZONS_MIN: tuple[int, ...] = (5, 15, 30, 60, 120, 240)


@dataclass(frozen=True)
class FeatureSpec:
    """One feature column: name, provenance, and a short description."""

    name: str
    provenance: Literal["DOCUMENTED", "ASSUMED"]
    description: str


def _log_returns(close: pd.Series) -> pd.Series:
    """1-minute log returns r_t = ln(close_t / close_{t-1}). Causal."""
    return np.log(close / close.shift(1))


def _realised_vol(returns: pd.Series, window: int) -> pd.Series:
    """Realised volatility = sqrt(sum of squared returns) over a trailing window.

    Trailing only (``shift`` not needed: ``rolling`` at index i uses i-window+1..i,
    all <= i). ``min_periods = window`` => no short-window leakage.
    """
    rv2 = returns.pow(2).rolling(window=window, min_periods=window).sum()
    return np.sqrt(rv2)


def _bipower_variation(returns: pd.Series, window: int) -> pd.Series:
    """Realised bipower variation (Barndorff-Nielsen & Shephard, 2004).

    BV_t = mu1^-2 * sum |r_{s-1}| |r_s|, a jump-robust integrated-variance
    estimator. ``mu1 = sqrt(2/pi)`` is E|N(0,1)|. Causal (products of past
    absolute returns only).
    """
    mu1 = np.sqrt(2.0 / np.pi)
    abs_r = returns.abs()
    prod = abs_r * abs_r.shift(1)
    bv2 = (mu1 ** -2) * prod.rolling(window=window, min_periods=window).sum()
    return np.sqrt(bv2.clip(lower=0.0))


def build_features(klines: pd.DataFrame) -> tuple[pd.DataFrame, list[FeatureSpec]]:
    """Build the 36-feature causal matrix from a 1-minute kline frame.

    Parameters
    ----------
    klines:
        DataFrame with columns ``ts`` (epoch ms, close-of-minute, ascending),
        ``open``, ``high``, ``low``, ``close``, ``volume``, ``turnover``. One
        symbol, contiguous-as-available 1-minute bars.

    Returns
    -------
    (features, specs):
        ``features`` is indexed by ``ts`` with exactly 36 feature columns plus
        the passthrough ``close`` (needed downstream by the target join; it is
        NOT one of the 36 model features). ``specs`` is the ordered provenance
        list (length 36).

    Raises
    ------
    ValueError:
        if required columns are missing or the frame is not sorted by ``ts``.
    """
    required = {"ts", "open", "high", "low", "close", "volume", "turnover"}
    missing = required - set(klines.columns)
    if missing:
        raise ValueError(f"klines missing columns: {sorted(missing)}")
    df = klines.copy()
    if not df["ts"].is_monotonic_increasing:
        raise ValueError("klines must be sorted ascending by ts (causal order)")
    df = df.set_index("ts")

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    open_ = df["open"].astype(float)
    volume = df["volume"].astype(float)
    turnover = df["turnover"].astype(float)

    r = _log_returns(close)
    feats: dict[str, pd.Series] = {}
    specs: list[FeatureSpec] = []

    def add(name: str, series: pd.Series, provenance: str, desc: str) -> None:
        feats[name] = series
        specs.append(FeatureSpec(name, provenance, desc))  # type: ignore[arg-type]

    # ------------------------------------------------------------------ #
    # 1) atr_60  — DOCUMENTED (research_notes: ranked #1, 35.8 % gain)    #
    # ------------------------------------------------------------------ #
    # Classic Wilder True Range, averaged over 60 bars. TR uses the prior
    # close (shift(1)) so it is strictly causal.
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    add(
        "atr_60",
        tr.rolling(window=BARS_PER_HOUR, min_periods=BARS_PER_HOUR).mean(),
        "DOCUMENTED",
        "Average True Range over 60 bars (research_notes #1, 35.8% gain).",
    )

    # ------------------------------------------------------------------ #
    # 2) Lagged realised-vol block, multiple horizons — ASSUMED          #
    #    (HAR-RV / realised-vol literature; notes name only the family    #
    #     implicitly via the vol target, not these members).             #
    # ------------------------------------------------------------------ #
    for w in RV_HORIZONS_MIN:
        # ASSUMED: trailing realised vol at horizon w (RV_{t-w+1..t}).
        add(
            f"rv_{w}m",
            _realised_vol(r, w),
            "ASSUMED",
            f"Trailing realised vol over {w} bars (HAR-RV style lagged RV).",
        )
    for w in RV_HORIZONS_MIN:
        # ASSUMED: log realised vol at horizon w — same scale as the target.
        add(
            f"log_rv_{w}m",
            np.log(_realised_vol(r, w).clip(lower=1e-12)),
            "ASSUMED",
            f"log of trailing realised vol over {w} bars.",
        )

    # ------------------------------------------------------------------ #
    # 3) Bipower variation & jump component — ASSUMED                    #
    #    (Barndorff-Nielsen/Shephard jump-robust IV + jump = RV - BV).   #
    # ------------------------------------------------------------------ #
    for w in (30, 60):
        bv = _bipower_variation(r, w)
        # ASSUMED: bipower variation (jump-robust vol estimate).
        add(
            f"bipower_{w}m",
            bv,
            "ASSUMED",
            f"Bipower variation over {w} bars (jump-robust IV estimator).",
        )
        rv = _realised_vol(r, w)
        # ASSUMED: jump component = max(RV^2 - BV^2, 0), the discontinuous part.
        add(
            f"jump_{w}m",
            (rv.pow(2) - bv.pow(2)).clip(lower=0.0),
            "ASSUMED",
            f"Jump component RV^2-BV^2 over {w} bars (truncated at 0).",
        )

    # ------------------------------------------------------------------ #
    # 4) Return moments — ASSUMED                                        #
    #    (Andersen et al. realised skewness/kurtosis; mean/abs return).  #
    # ------------------------------------------------------------------ #
    for w in (30, 60):
        # ASSUMED: realised skewness over w bars.
        add(
            f"ret_skew_{w}m",
            r.rolling(window=w, min_periods=w).skew(),
            "ASSUMED",
            f"Realised return skewness over {w} bars.",
        )
        # ASSUMED: realised (excess) kurtosis over w bars.
        add(
            f"ret_kurt_{w}m",
            r.rolling(window=w, min_periods=w).kurt(),
            "ASSUMED",
            f"Realised return kurtosis over {w} bars.",
        )
    # ASSUMED: mean log return over 60 bars (drift proxy).
    add(
        "ret_mean_60m",
        r.rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Mean log return over 60 bars (drift / trend proxy).",
    )
    # ASSUMED: mean absolute return over 60 bars (robust vol proxy).
    add(
        "abs_ret_mean_60m",
        r.abs().rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Mean absolute log return over 60 bars.",
    )
    # ASSUMED: most recent 1-min log return (last-bar shock).
    add("ret_1m", r, "ASSUMED", "Last 1-minute log return (current shock).")
    # ASSUMED: high-low (Parkinson) range of the current bar, log scale.
    add(
        "parkinson_range_1m",
        np.log(high.clip(lower=1e-12) / low.clip(lower=1e-12)).abs(),
        "ASSUMED",
        "Parkinson log high-low range of the current bar.",
    )

    # ------------------------------------------------------------------ #
    # 5) Trade-flow / microstructure family — research_notes names the   #
    #    FAMILY ("trade-flow features", 38% gain) but not its members,   #
    #    so every member below is ASSUMED.                               #
    # ------------------------------------------------------------------ #
    # ASSUMED: trailing volume mean over 60 bars (activity level).
    add(
        "volume_mean_60m",
        volume.rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Trade-flow family: mean volume over 60 bars.",
    )
    # ASSUMED: trailing volume std over 60 bars (activity dispersion).
    add(
        "volume_std_60m",
        volume.rolling(window=60, min_periods=60).std(),
        "ASSUMED",
        "Trade-flow family: volume std over 60 bars.",
    )
    # ASSUMED: current volume vs its 60-bar mean (volume surprise).
    add(
        "volume_ratio_60m",
        volume / volume.rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Trade-flow family: current volume / 60-bar mean volume.",
    )
    # ASSUMED: turnover mean over 60 bars (quote-volume activity).
    add(
        "turnover_mean_60m",
        turnover.rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Trade-flow family: mean turnover over 60 bars.",
    )
    # ASSUMED: average trade size proxy = turnover/volume (per-bar VWAP-ish).
    vwap_like = (turnover / volume.replace(0.0, np.nan))
    add(
        "avg_trade_price_60m",
        vwap_like.rolling(window=60, min_periods=60).mean(),
        "ASSUMED",
        "Trade-flow family: mean turnover/volume (VWAP-like) over 60 bars.",
    )
    # ASSUMED: signed-volume / order-flow imbalance proxy. publicTrade buy/sell
    # split is NOT in kline_1min, so we approximate trade sign by the bar's
    # close-vs-open direction (causal: uses only bar i's own OHLC).
    bar_sign = np.sign(close - open_)
    signed_vol = bar_sign * volume
    add(
        "ofi_proxy_60m",
        signed_vol.rolling(window=60, min_periods=60).sum()
        / volume.rolling(window=60, min_periods=60).sum(),
        "ASSUMED",
        "Trade-flow family: order-flow-imbalance proxy "
        "(sum signed volume / sum volume, sign from close-open).",
    )
    # ASSUMED: trade-direction persistence — mean bar sign over 30 bars.
    add(
        "bar_sign_mean_30m",
        bar_sign.rolling(window=30, min_periods=30).mean(),
        "ASSUMED",
        "Trade-flow family: mean bar direction over 30 bars.",
    )

    # ------------------------------------------------------------------ #
    # 6) Intraday seasonality — ASSUMED                                  #
    #    (intraday vol "U-shape"; encode minute-of-day cyclically).      #
    # ------------------------------------------------------------------ #
    minute_of_day = ((df.index // 60_000) % 1440).astype(float)
    # ASSUMED: cyclic sin/cos of minute-of-day (deterministic from ts, causal).
    add(
        "tod_sin",
        np.sin(2.0 * np.pi * minute_of_day / 1440.0),
        "ASSUMED",
        "Intraday seasonality: sin(minute-of-day).",
    )
    add(
        "tod_cos",
        np.cos(2.0 * np.pi * minute_of_day / 1440.0),
        "ASSUMED",
        "Intraday seasonality: cos(minute-of-day).",
    )

    # ------------------------------------------------------------------ #
    # 7) Vol-of-vol & RV ratios — ASSUMED                                #
    #    (HAR-RV cross-horizon ratios + short-term vol-of-vol).          #
    # ------------------------------------------------------------------ #
    rv60 = _realised_vol(r, 60)
    rv240 = _realised_vol(r, 240)
    # ASSUMED: ratio of 60m to 240m realised vol (term-structure slope).
    add(
        "rv_ratio_60_240",
        rv60 / rv240.replace(0.0, np.nan),
        "ASSUMED",
        "RV term-structure slope: rv_60m / rv_240m.",
    )
    # ASSUMED: vol-of-vol = std of 5m-RV over the last 60 bars.
    add(
        "vol_of_vol_60m",
        _realised_vol(r, 5).rolling(window=60, min_periods=60).std(),
        "ASSUMED",
        "Vol-of-vol: 60-bar std of trailing 5m realised vol.",
    )

    features = pd.DataFrame(feats, index=df.index)
    features["close"] = close  # passthrough for the target join (NOT a feature)

    n_feats = len(specs)
    if n_feats != 36:
        raise AssertionError(
            f"feature builder must yield exactly 36 features, got {n_feats}"
        )
    return features, specs


def feature_names(specs: list[FeatureSpec]) -> list[str]:
    """Ordered list of the 36 model-feature names (excludes ``close``)."""
    return [s.name for s in specs]


#: Static provenance summary, importable by the pipeline / report without
#: re-running the builder. (1 DOCUMENTED + 35 ASSUMED = 36.)
FEATURE_PROVENANCE: dict[str, int] = {"DOCUMENTED": 1, "ASSUMED": 35}
