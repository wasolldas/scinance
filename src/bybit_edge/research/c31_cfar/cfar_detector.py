"""CA-CFAR peak detector over the Spectral Correlation Density (WP-3).

Cell-Averaging Constant False Alarm Rate: for every cell under test (CUT) the
local noise floor is estimated from a ring of *training* cells, separated from
the CUT by *guard* cells (which would otherwise leak the peak's own energy into
the noise estimate). A cell is declared a detection when

    SCD(cut) > threshold_factor * noise_floor(cut)

The threshold factor is parametric and, under an exponential-noise assumption
for power-like cells, maps to a nominal per-cell false-alarm probability
``Pfa = (1 + T/N)^(-N)`` with ``N`` training cells — but the binding
false-positive control for H-03 is the *surrogate* test (``surrogate.py``), not
this analytic Pfa. CA-CFAR here is the candidate-peak generator; the surrogate
null decides significance.

Detection runs on the 2-D ``(alpha, f)`` SCD but excludes the ``alpha = 0`` row
(that is the ordinary PSD — cyclostationarity is the ``alpha != 0`` structure).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cyclic_spectrum import CyclicSpectrum


@dataclass(slots=True)
class CfarPeak:
    """A single CA-CFAR detection in the (alpha, f) plane."""

    alpha_hz: float
    freq_hz: float
    alpha_idx: int
    freq_idx: int
    scd: float          # SCD magnitude at the cell
    noise_floor: float  # CA-CFAR local noise estimate
    snr: float          # scd / noise_floor (the CFAR test statistic)
    p_local: float      # analytic per-cell Pfa at the detected SNR

    def as_dict(self) -> dict[str, float | int]:
        return {
            "alpha_hz": float(self.alpha_hz),
            "freq_hz": float(self.freq_hz),
            "alpha_idx": int(self.alpha_idx),
            "freq_idx": int(self.freq_idx),
            "scd": float(self.scd),
            "noise_floor": float(self.noise_floor),
            "snr": float(self.snr),
            "p_local": float(self.p_local),
        }


@dataclass(slots=True)
class CfarConfig:
    """Parametric CA-CFAR configuration (one F-CFAR family member)."""

    train_cells: int = 8        # training cells per side, along the alpha axis
    guard_cells: int = 2        # guard cells per side
    threshold_factor: float = 6.0   # T: multiplies the local noise floor
    min_alpha_hz: float = 0.0   # ignore detections below this cyclic frequency

    def nominal_pfa(self) -> float:
        """Analytic per-cell false-alarm probability (exponential noise)."""
        n = 2 * self.train_cells
        if n <= 0:
            return 1.0
        return float((1.0 + self.threshold_factor / n) ** (-n))


def _local_noise_floor(
    column: np.ndarray, idx: int, train: int, guard: int
) -> float:
    """Cell-averaging noise estimate for cell ``idx`` of a 1-D vector.

    Training cells are taken from both sides, skipping the guard band and the
    CUT. Edge cells fall back to whatever training cells are available.
    """
    n = column.size
    lo_train_start = max(0, idx - guard - train)
    lo_train_end = max(0, idx - guard)
    hi_train_start = min(n, idx + guard + 1)
    hi_train_end = min(n, idx + guard + 1 + train)
    cells = np.concatenate([
        column[lo_train_start:lo_train_end],
        column[hi_train_start:hi_train_end],
    ])
    if cells.size == 0:
        return float(np.mean(column)) if n else 0.0
    return float(np.mean(cells))


def detect_peaks(
    spectrum: CyclicSpectrum,
    config: CfarConfig | None = None,
) -> list[CfarPeak]:
    """Run CA-CFAR over the SCD and return detected peaks (alpha != 0 only).

    The averaging runs *along the cyclic-frequency (alpha) axis* for each fixed
    spectral frequency ``f``: at a fixed ``f`` a genuine cycle shows up as a
    localised bump across alpha against a flat alpha-noise floor, which is
    exactly the contrast CA-CFAR is built to find.
    """
    cfg = config or CfarConfig()
    scd = spectrum.scd
    n_alpha, n_freq = scd.shape
    peaks: list[CfarPeak] = []
    if n_alpha < 2:
        return peaks

    train, guard = cfg.train_cells, cfg.guard_cells
    for fj in range(n_freq):
        col = scd[:, fj]
        for ai in range(1, n_alpha):  # skip alpha = 0 (PSD row)
            alpha_hz = float(spectrum.alphas[ai])
            if alpha_hz < cfg.min_alpha_hz:
                continue
            cut = float(col[ai])
            floor = _local_noise_floor(col, ai, train, guard)
            if floor <= 0.0:
                continue
            snr = cut / floor
            if cut > cfg.threshold_factor * floor:
                # Local exponential-tail p-value at this SNR.
                p_local = float(np.exp(-snr)) if snr < 700 else 0.0
                peaks.append(
                    CfarPeak(
                        alpha_hz=alpha_hz,
                        freq_hz=float(spectrum.freqs[fj]),
                        alpha_idx=ai,
                        freq_idx=fj,
                        scd=cut,
                        noise_floor=floor,
                        snr=snr,
                        p_local=p_local,
                    )
                )
    # Strongest first — the driver/surrogate test pairs against the top peak.
    peaks.sort(key=lambda p: p.snr, reverse=True)
    return peaks


def top_snr(peaks: list[CfarPeak]) -> float:
    """Maximum CFAR SNR among ``peaks`` (0.0 if none) — the window statistic."""
    return max((p.snr for p in peaks), default=0.0)
