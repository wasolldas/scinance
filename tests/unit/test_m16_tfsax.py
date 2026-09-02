"""
Tests fuer M16 -- TFSAX + Smith-Waterman Alignment.

Testet:
- PAA reduziert Laenge
- SAX-Alphabet-Range (Symbole aus 'abcde')
- SAX konstante Serie (selbes Symbol)
- Smith-Waterman identische Sequenzen (max Score)
- Smith-Waterman kein Match (Score ~ 0)
- Normalize-Score im Bereich [0, 1]
- Compute Top-Matches
- Reset
"""

from __future__ import annotations

import pytest
import numpy as np

from bybit_edge._legacy_v1.layers.l4_pattern.m16_tfsax_sw import M16TFSAXSW


class TestM16TFSAXSW:
    """Tests fuer das TFSAX + Smith-Waterman Pattern-Matching-Modul."""

    def test_paa_reduces_length(self) -> None:
        """PAA reduziert die Laenge der Serie auf n_segments."""
        mod = M16TFSAXSW()
        series = np.random.randn(100)
        paa = mod._paa(series, n_segments=10)
        assert len(paa) == 10

        # PAA mit mehr Segmenten als Daten -> gleiche Laenge
        paa_long = mod._paa(series, n_segments=200)
        assert len(paa_long) == len(series)

    def test_sax_alphabet_range(self) -> None:
        """SAX-Symbole stammen aus dem Alphabet 'abcde' (alphabet_size=5)."""
        mod = M16TFSAXSW(alphabet_size=5)
        series = np.random.randn(50)
        paa = mod._paa(series, n_segments=20)
        sax_str = mod._sax(paa, alphabet_size=5)
        assert len(sax_str) == 20
        for ch in sax_str:
            assert ch in "abcde"

    def test_sax_constant_series(self) -> None:
        """Konstante Serie -> alle gleichen Symbole (mittleres Symbol)."""
        mod = M16TFSAXSW(alphabet_size=5)
        series = np.ones(50)
        paa = mod._paa(series, n_segments=10)
        sax_str = mod._sax(paa, alphabet_size=5)
        # Alle Symbole sollten gleich sein (mittleres Symbol 'c')
        assert len(set(sax_str)) == 1
        assert sax_str[0] == "c"

    def test_smith_waterman_identical(self) -> None:
        """Identische Sequenzen -> maximaler Score."""
        mod = M16TFSAXSW()
        seq = "abcde"
        score, a1, a2 = mod._smith_waterman(seq, seq, match=2, mismatch=-1, gap=-1)
        # Identisch -> Score = len * match = 5 * 2 = 10
        assert score == 10.0
        assert a1 == seq
        assert a2 == seq

    def test_smith_waterman_no_match(self) -> None:
        """Komplett verschiedene Sequenzen -> Score nahe 0."""
        mod = M16TFSAXSW()
        # Verwende Sequenzen ohne gemeinsame Zeichen
        score, a1, a2 = mod._smith_waterman("aaaa", "bbbb", match=2, mismatch=-1, gap=-1)
        # Keine Matches -> Score sollte 0 sein
        assert score == 0.0

    def test_normalize_score_range(self) -> None:
        """Normalisierter Score liegt immer in [0, 1]."""
        mod = M16TFSAXSW()
        # Perfekter Match
        assert mod._normalize_score(10.0, 5, 5, match=2) == 1.0
        # Null-Score
        assert mod._normalize_score(0.0, 5, 5, match=2) == 0.0
        # Teilmatch
        normalized = mod._normalize_score(4.0, 5, 5, match=2)
        assert 0.0 <= normalized <= 1.0
        # Edge case: Laenge 0
        assert mod._normalize_score(5.0, 0, 5, match=2) == 0.0

    def test_compute_top_matches(self) -> None:
        """Compute findet Top-Matches und berechnet Forward-Return-Statistiken."""
        mod = M16TFSAXSW(
            alphabet_size=5,
            n_segments=20,
            top_k=3,
            match_threshold=0.1,
        )
        np.random.seed(42)

        query = np.sin(np.linspace(0, 2 * np.pi, 100))
        library = [
            {"series": np.sin(np.linspace(0, 2 * np.pi, 100)), "forward_return": 0.02},
            {"series": np.cos(np.linspace(0, 2 * np.pi, 100)), "forward_return": -0.01},
            {"series": np.random.randn(100), "forward_return": 0.005},
            {"series": np.sin(np.linspace(0, 2 * np.pi, 100)) * 1.1, "forward_return": 0.03},
        ]

        result = mod.compute(query_series=query, library=library, ts=1.0)
        assert len(result["top_matches"]) <= 3
        assert "mean_forward_return" in result
        assert "match_score" in result
        assert result["method_id"] == "M16"
        assert result["signal"] in (-1, 0, 1)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_reset(self) -> None:
        """Reset re-initialisiert die Breakpoints."""
        mod = M16TFSAXSW(alphabet_size=5)
        old_bp = list(mod._breakpoints)
        mod.reset()
        assert mod._breakpoints == old_bp  # Breakpoints bleiben gleich (stateless)
