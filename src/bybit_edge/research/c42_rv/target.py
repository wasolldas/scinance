"""Forward-looking regression target: ``log(realised_vol_60m)`` (WP-4).

Reproduces the Kestrel volatility target (``research_notes.md`` §"Volatility
prediction"): the regression target is the *forward* realised volatility over
the next 60 minutes, expressed in logs.

No-overlap / no-leakage contract (H-02 No-Lookahead):

- Features at bar ``i`` use bars ``[..., i]`` (close of bar i).
- The target at bar ``i`` is the realised vol of the *forward* returns
  ``r_{i+1}, ..., r_{i+60}`` — i.e. bars ``i+1 .. i+60``. Feature[i] and
  target[i] therefore share NO bar; the first forward return r_{i+1} uses
  close_{i} and close_{i+1}, so it begins strictly after the feature horizon.
- The last 60 bars of any contiguous block have an incomplete forward window
  and are dropped (NaN target). ``splits.py`` additionally purges
  ``HORIZON_BARS`` rows around each fold boundary so a training row's forward
  target window can never bleed into an OOS fold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Forward horizon of the target, in 1-minute bars (60 minutes).
HORIZON_BARS = 60

#: Floor before taking the log, to keep log(0) finite on flat synthetic bars.
_VOL_FLOOR = 1e-12


def build_target(features_with_close: pd.DataFrame) -> pd.Series:
    """Compute ``log(realised_vol_60m)`` forward target indexed by feature ts.

    Parameters
    ----------
    features_with_close:
        Output of :func:`features.build_features` — must carry a ``close``
        column and be indexed ascending by ``ts``.

    Returns
    -------
    pd.Series:
        ``log(realised_vol_60m)`` aligned to the SAME index as the features.
        Row ``i`` holds the realised vol of forward returns over bars
        ``i+1 .. i+HORIZON_BARS``; the final ``HORIZON_BARS`` rows are NaN
        (incomplete forward window) and are dropped by the pipeline.
    """
    if "close" not in features_with_close.columns:
        raise ValueError("features frame must carry a 'close' passthrough column")
    close = features_with_close["close"].astype(float)

    # Forward 1-min log returns: fwd_r at index i == ln(close_{i+1}/close_i).
    fwd_r = np.log(close.shift(-1) / close)
    # Realised vol of bars i+1..i+H == rolling sum of fwd_r over a FORWARD
    # window. Implement via a reversed trailing sum so min_periods is honoured.
    sq = fwd_r.pow(2)
    # forward sum of squared returns over the next H bars, anchored at i:
    #   sum_{k=1..H} r_{i+k}^2  ==  reverse( trailing_sum( reverse(sq) ) ) shifted.
    rev = sq[::-1]
    fwd_sumsq = rev.rolling(window=HORIZON_BARS, min_periods=HORIZON_BARS).sum()[::-1]
    # fwd_sumsq at i currently covers bars i..i+H-1 of fwd_r, i.e. returns
    # r_{i+1}..r_{i+H}; that is exactly the forward 60-min window. Good.
    rv_fwd = np.sqrt(fwd_sumsq)
    target = np.log(rv_fwd.clip(lower=_VOL_FLOOR))
    target.name = "log_realised_vol_60m"
    return target
