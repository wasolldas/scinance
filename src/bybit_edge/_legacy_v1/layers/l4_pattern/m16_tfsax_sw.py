"""
M16 — TFSAX + Smith-Waterman Alignment [L4] [Moonshot]

Eigene Implementierung von SAX (Symbolic Aggregate approXimation) mit
Piecewise Aggregate Approximation (PAA) und Smith-Waterman Local Alignment.

Formeln (PRD):
    PAA:  C_bar_i = (w/n) * Sum c_j
    SAX:  symbol_i = bin(C_bar_i) mit gleichwahrscheinlichen Gauss-Bins
    SW:   H(i,j) = max{0, H(i-1,j-1)+s(a_i,b_j), H(i-1,j)-d, H(i,j-1)-d}

Kein tslearn/saxpy/Biopython — alles eigene Implementierung.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.stats import norm

from bybit_edge.config import (
    TFSAX_ALPHABET_SIZE,
    TFSAX_MATCH_SCORE_THRESHOLD,
    TFSAX_SEGMENT_LENGTH,
    TFSAX_TOP_K_MATCHES,
)
from bybit_edge._legacy_v1.layers.base import BaseModule


def _gauss_breakpoints(alphabet_size: int) -> list[float]:
    """Berechnet gleichwahrscheinliche Gauss-Breakpoints fuer SAX.

    Teilt die Standard-Normalverteilung in alphabet_size Bins mit gleicher
    Wahrscheinlichkeit und gibt die inneren Breakpoints zurueck.
    """
    return [float(norm.ppf(i / alphabet_size)) for i in range(1, alphabet_size)]


class M16TFSAXSW(BaseModule):
    """Time-Frequency SAX mit Smith-Waterman Pattern Matching.

    Konvertiert Zeitreihen in symbolische SAX-Repraesentationen und
    sucht via Smith-Waterman Local Alignment nach historischen Mustern
    mit aehnlicher Struktur.
    """

    def __init__(
        self,
        alphabet_size: int = TFSAX_ALPHABET_SIZE,
        n_segments: int = TFSAX_SEGMENT_LENGTH,
        top_k: int = TFSAX_TOP_K_MATCHES,
        match_threshold: float = TFSAX_MATCH_SCORE_THRESHOLD,
    ) -> None:
        self._alphabet_size: int = alphabet_size
        self._n_segments: int = n_segments
        self._top_k: int = top_k
        self._match_threshold: float = match_threshold
        self._breakpoints: list[float] = _gauss_breakpoints(alphabet_size)
        self._alphabet: str = "abcdefghijklmnopqrstuvwxyz"[:alphabet_size]

    # ------------------------------------------------------------------
    # PAA
    # ------------------------------------------------------------------

    def _paa(self, series: np.ndarray, n_segments: int) -> np.ndarray:
        """Piecewise Aggregate Approximation.

        Reduziert die Zeitreihe auf n_segments Segmente durch Mittelwertbildung.
        """
        n = len(series)
        if n_segments >= n:
            return series.copy().astype(float)

        paa_values = np.zeros(n_segments, dtype=float)
        for i in range(n_segments):
            start = int(round(i * n / n_segments))
            end = int(round((i + 1) * n / n_segments))
            end = max(end, start + 1)  # mindestens 1 Element
            paa_values[i] = np.mean(series[start:end])
        return paa_values

    # ------------------------------------------------------------------
    # SAX
    # ------------------------------------------------------------------

    def _sax(self, paa_values: np.ndarray, alphabet_size: int | None = None) -> str:
        """Symbolische Repraesentation via SAX.

        Z-Normalisierung der PAA-Werte und Zuordnung zu Symbolen
        anhand der Gauss-Breakpoints.
        """
        if alphabet_size is None:
            alphabet_size = self._alphabet_size

        # z-Normalisierung
        std = float(np.std(paa_values))
        if std < 1e-12:
            # Konstante Serie -> mittleres Symbol
            mid_idx = alphabet_size // 2
            return self._alphabet[mid_idx] * len(paa_values)

        z_vals = (paa_values - np.mean(paa_values)) / std

        breakpoints = _gauss_breakpoints(alphabet_size)
        symbols: list[str] = []
        for val in z_vals:
            assigned = False
            for k, bp in enumerate(breakpoints):
                if val < bp:
                    symbols.append(self._alphabet[k])
                    assigned = True
                    break
            if not assigned:
                symbols.append(self._alphabet[alphabet_size - 1])

        return "".join(symbols)

    # ------------------------------------------------------------------
    # Smith-Waterman
    # ------------------------------------------------------------------

    def _smith_waterman(
        self,
        seq1: str,
        seq2: str,
        match: int = 2,
        mismatch: int = -1,
        gap: int = -1,
    ) -> tuple[float, str, str]:
        """Vollstaendiger Smith-Waterman Local Alignment mit Traceback.

        Returns (score, aligned_seq1, aligned_seq2).
        """
        m = len(seq1)
        n = len(seq2)

        # Score-Matrix
        H = np.zeros((m + 1, n + 1), dtype=int)
        # Traceback: 0=stop, 1=diag, 2=up, 3=left
        traceback = np.zeros((m + 1, n + 1), dtype=int)

        max_score = 0
        max_pos = (0, 0)

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                s = match if seq1[i - 1] == seq2[j - 1] else mismatch
                diag = H[i - 1, j - 1] + s
                up = H[i - 1, j] + gap
                left = H[i, j - 1] + gap

                best = max(0, diag, up, left)
                H[i, j] = best

                if best == 0:
                    traceback[i, j] = 0
                elif best == diag:
                    traceback[i, j] = 1
                elif best == up:
                    traceback[i, j] = 2
                else:
                    traceback[i, j] = 3

                if best > max_score:
                    max_score = best
                    max_pos = (i, j)

        # Traceback
        aligned1: list[str] = []
        aligned2: list[str] = []
        i, j = max_pos

        while i > 0 and j > 0 and H[i, j] > 0:
            if traceback[i, j] == 1:  # diagonal
                aligned1.append(seq1[i - 1])
                aligned2.append(seq2[j - 1])
                i -= 1
                j -= 1
            elif traceback[i, j] == 2:  # up
                aligned1.append(seq1[i - 1])
                aligned2.append("-")
                i -= 1
            elif traceback[i, j] == 3:  # left
                aligned1.append("-")
                aligned2.append(seq2[j - 1])
                j -= 1
            else:
                break

        aligned1.reverse()
        aligned2.reverse()

        return float(max_score), "".join(aligned1), "".join(aligned2)

    # ------------------------------------------------------------------
    # Score-Normalisierung
    # ------------------------------------------------------------------

    def _normalize_score(
        self, score: float, len1: int, len2: int, match: int = 2
    ) -> float:
        """Normalisiert den SW-Score auf [0, 1].

        score / (min(len1, len2) * match)
        """
        max_possible = min(len1, len2) * match
        if max_possible <= 0:
            return 0.0
        return min(score / max_possible, 1.0)

    # ------------------------------------------------------------------
    # Hauptberechnung
    # ------------------------------------------------------------------

    def compute(  # type: ignore[override]
        self,
        query_series: np.ndarray | None = None,
        library: list[dict[str, Any]] | None = None,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Sucht historische Pattern-Matches via TFSAX + Smith-Waterman.

        Parameters
        ----------
        query_series : np.ndarray | None
            Aktuelle 24h-Returns als 1-D Array.
        library : list[dict] | None
            Historische Segmente: [{"series": np.ndarray, "forward_return": float}].
        ts : float | None
            Zeitstempel; falls None wird time.time() verwendet.

        Returns
        -------
        dict mit top_matches, mean_forward_return, match_score,
        signal, method_id, confidence, ts.
        """
        if ts is None:
            ts = time.time()
        if query_series is None:
            query_series = np.array([])
        if library is None:
            library = []

        # Leere Eingabe abfangen
        if len(query_series) == 0 or len(library) == 0:
            return {
                "top_matches": [],
                "mean_forward_return": 0.0,
                "match_score": 0.0,
                "signal": 0,
                "method_id": "M16",
                "confidence": 0.0,
                "ts": ts,
            }

        # PAA + SAX fuer Query
        n_seg = min(self._n_segments, len(query_series))
        query_paa = self._paa(query_series, n_seg)
        query_sax = self._sax(query_paa)

        # Score jedes Library-Elements
        scored: list[tuple[float, float, str, str, int]] = []
        for idx, entry in enumerate(library):
            lib_series = entry["series"]
            lib_seg = min(self._n_segments, len(lib_series))
            lib_paa = self._paa(lib_series, lib_seg)
            lib_sax = self._sax(lib_paa)

            sw_score, aligned1, aligned2 = self._smith_waterman(query_sax, lib_sax)
            norm_score = self._normalize_score(
                sw_score, len(query_sax), len(lib_sax)
            )
            scored.append((norm_score, entry["forward_return"], aligned1, aligned2, idx))

        # Sortiere nach Score absteigend
        scored.sort(key=lambda x: x[0], reverse=True)

        # Top-k
        top_k = scored[: self._top_k]

        top_matches: list[dict[str, Any]] = []
        for norm_score, fwd_ret, a1, a2, idx in top_k:
            top_matches.append({
                "index": idx,
                "score": norm_score,
                "forward_return": fwd_ret,
                "aligned_query": a1,
                "aligned_library": a2,
            })

        # Aggregierte Metriken
        if top_matches:
            match_score = top_matches[0]["score"]
            fwd_returns = [m["forward_return"] for m in top_matches]
            mean_fwd = float(np.mean(fwd_returns))
        else:
            match_score = 0.0
            mean_fwd = 0.0

        # Signal-Bestimmung
        signal: int = 0
        if match_score > self._match_threshold:
            if mean_fwd > 0:
                signal = 1
            elif mean_fwd < 0:
                signal = -1

        # Confidence: basiert auf Match-Score
        confidence = match_score

        return {
            "top_matches": top_matches,
            "mean_forward_return": mean_fwd,
            "match_score": match_score,
            "signal": signal,
            "method_id": "M16",
            "confidence": confidence,
            "ts": ts,
        }

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Prueft TFSAX-Parameter auf Plausibilitaet."""
        return (
            self._alphabet_size >= 2
            and self._n_segments >= 1
            and self._top_k >= 1
            and 0.0 < self._match_threshold <= 1.0
        )

    def reset(self) -> None:
        """Setzt internen State zurueck (stateless Modul — no-op bis auf Re-Init)."""
        self._breakpoints = _gauss_breakpoints(self._alphabet_size)
