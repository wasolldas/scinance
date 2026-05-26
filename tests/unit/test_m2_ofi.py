"""
Tests fuer M2 -- Order Flow Imbalance (Cont-Kukanov-Stoikov).

Testet:
- e_n Berechnung fuer verschiedene Bid/Ask-Szenarien
- Rolling-Window-Verhalten
- Signal-Erzeugung bei starkem Kauf-/Verkaufsdruck
- Quantil-Tracker und Mindest-History
- Erster Update ohne Crash
- Reset-Verhalten
"""

from __future__ import annotations

import pytest

from bybit_edge.layers.l1_ingestion.m2_ofi import M2OFI, _MIN_QUANTILE_SAMPLES


class TestEnCalculation:
    """Tests fuer die e_n Berechnung nach Cont-Kukanov-Stoikov."""

    def test_e_n_bid_increase(self) -> None:
        """Bid-Preis steigt -> positive e_n Contribution von der Bid-Seite."""
        mod = M2OFI()
        # Initialer Tick
        mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        # Bid steigt: 100 -> 102
        result = mod.update((102.0, 10.0), (101.0, 5.0), ts=1.1)
        # bid_price(102) >= prev_bid_price(100) -> +bid_size(10)
        # bid_price(102) > prev_bid_price(100), not <= -> kein -prev_bid_size
        # ask_price(101) <= prev_ask_price(101) -> -ask_size(5)
        # ask_price(101) >= prev_ask_price(101) -> +prev_ask_size(5)
        # e_n = 10 - 5 + 5 = 10
        assert result["e_n"] == 10.0

    def test_e_n_bid_decrease(self) -> None:
        """Bid-Preis faellt -> negative e_n Contribution von der Bid-Seite."""
        mod = M2OFI()
        mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        # Bid faellt: 100 -> 98
        result = mod.update((98.0, 3.0), (101.0, 5.0), ts=1.1)
        # bid_price(98) < prev_bid_price(100), not >= -> kein +bid_size
        # bid_price(98) <= prev_bid_price(100) -> -prev_bid_size(5)
        # ask_price(101) <= prev_ask_price(101) -> -ask_size(5)
        # ask_price(101) >= prev_ask_price(101) -> +prev_ask_size(5)
        # e_n = 0 - 5 - 5 + 5 = -5
        assert result["e_n"] == -5.0

    def test_e_n_no_change(self) -> None:
        """Gleiche Preise -> bid_price==prev_bid_price triggert beide Indikatoren."""
        mod = M2OFI()
        mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        # Gleiche Preise, gleiche Sizes
        result = mod.update((100.0, 5.0), (101.0, 5.0), ts=1.1)
        # bid_price(100) >= prev_bid_price(100) -> +bid_size(5)
        # bid_price(100) <= prev_bid_price(100) -> -prev_bid_size(5)
        # ask_price(101) <= prev_ask_price(101) -> -ask_size(5)
        # ask_price(101) >= prev_ask_price(101) -> +prev_ask_size(5)
        # e_n = 5 - 5 - 5 + 5 = 0
        assert result["e_n"] == 0.0

    def test_e_n_ask_decrease(self) -> None:
        """Ask-Preis faellt -> negativer Ask-Beitrag (Verkaufsdruck)."""
        mod = M2OFI()
        mod.update((100.0, 5.0), (105.0, 5.0), ts=1.0)
        # Ask faellt: 105 -> 103, grosse Size
        result = mod.update((100.0, 5.0), (103.0, 20.0), ts=1.1)
        # bid: 100 >= 100 -> +5, 100 <= 100 -> -5 => 0
        # ask: 103 <= 105 -> -20, 103 < 105 not >= -> kein +prev_ask
        # e_n = 0 - 20 = -20
        assert result["e_n"] == -20.0

    def test_e_n_ask_increase(self) -> None:
        """Ask-Preis steigt -> positiver Ask-Beitrag."""
        mod = M2OFI()
        mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        # Ask steigt: 101 -> 103
        result = mod.update((100.0, 5.0), (103.0, 3.0), ts=1.1)
        # bid: 100 >= 100 -> +5, 100 <= 100 -> -5 => 0
        # ask: 103 > 101 not <= -> kein -ask_size
        # ask: 103 >= 101 -> +prev_ask_size(5)
        # e_n = 0 + 5 = 5
        assert result["e_n"] == 5.0


class TestOFIRollingWindow:
    """Tests fuer das Rolling-Window-Verhalten."""

    def test_ofi_rolling_window(self) -> None:
        """Events ausserhalb des OFI_WINDOW_SECONDS werden entfernt."""
        mod = M2OFI()
        # Initialer Tick bei t=0
        mod.update((100.0, 10.0), (101.0, 10.0), ts=0.0)

        # Tick bei t=1 erzeugt e_n
        r1 = mod.update((102.0, 10.0), (103.0, 10.0), ts=1.0)
        e1 = r1["e_n"]

        # Tick bei t=7 (> 5s Window) -> erstes Event sollte rausfallen
        r2 = mod.update((104.0, 10.0), (105.0, 10.0), ts=7.0)
        # OFI sollte nur das Event bei t=7 enthalten (t=1 ist > 5s alt)
        assert r2["ofi"] == r2["e_n"]


class TestSignalGeneration:
    """Tests fuer die Signal-Erzeugung."""

    def test_signal_strong_buy_pressure(self) -> None:
        """OFI > Q90 -> signal=1 (starker Kaufdruck)."""
        mod = M2OFI()
        # Baue History mit kleinen positiven/negativen Schwankungen auf
        base_ts = 0.0
        mod.update((100.0, 1.0), (101.0, 1.0), ts=base_ts)
        for i in range(1, _MIN_QUANTILE_SAMPLES + 50):
            # Abwechselnd kleiner Bid-Anstieg und -Abfall fuer OFI-Varianz
            if i % 2 == 0:
                mod.update((100.5, 2.0), (101.5, 2.0), ts=base_ts + i * 0.1)
            else:
                mod.update((99.5, 2.0), (100.5, 2.0), ts=base_ts + i * 0.1)

        # Jetzt starker Kaufdruck: Bid steigt massiv, alle Events im 5s-Window
        spike_ts = base_ts + (_MIN_QUANTILE_SAMPLES + 50) * 0.1
        result = mod.update((200.0, 1000.0), (201.0, 1.0), ts=spike_ts)
        assert result["signal"] == 1

    def test_signal_strong_sell_pressure(self) -> None:
        """OFI < -Q90 -> signal=-1 (starker Verkaufsdruck)."""
        mod = M2OFI()
        base_ts = 0.0
        mod.update((100.0, 1.0), (101.0, 1.0), ts=base_ts)

        # History mit kleinen Schwankungen aufbauen
        for i in range(1, _MIN_QUANTILE_SAMPLES + 50):
            if i % 2 == 0:
                mod.update((100.5, 2.0), (101.5, 2.0), ts=base_ts + i * 0.1)
            else:
                mod.update((99.5, 2.0), (100.5, 2.0), ts=base_ts + i * 0.1)

        # Starker Verkaufsdruck: Bid faellt, Ask faellt mit grosser Size
        spike_ts = base_ts + (_MIN_QUANTILE_SAMPLES + 50) * 0.1
        result = mod.update((50.0, 1.0), (51.0, 1000.0), ts=spike_ts)
        assert result["signal"] == -1

    def test_signal_neutral(self) -> None:
        """OFI innerhalb Q90 -> signal=0."""
        mod = M2OFI()
        mod.update((100.0, 1.0), (101.0, 1.0), ts=0.0)

        # Neutrale Updates
        for i in range(1, _MIN_QUANTILE_SAMPLES + 50):
            mod.update((100.0, 1.0), (101.0, 1.0), ts=0.0 + i * 0.01)

        # Noch ein neutraler Tick
        result = mod.update((100.0, 1.0), (101.0, 1.0), ts=100.0)
        assert result["signal"] == 0

    def test_quantile_needs_history(self) -> None:
        """< _MIN_QUANTILE_SAMPLES Events -> signal=0 immer."""
        mod = M2OFI()
        mod.update((100.0, 1.0), (101.0, 1.0), ts=0.0)

        # Weniger als _MIN_QUANTILE_SAMPLES Updates
        for i in range(1, _MIN_QUANTILE_SAMPLES - 5):
            result = mod.update((200.0, 1000.0), (201.0, 1.0), ts=float(i))
            assert result["signal"] == 0


class TestEdgeCases:
    """Tests fuer Randfaelle."""

    def test_first_update_no_crash(self) -> None:
        """Erster Update mit Nullen als prev soll nicht crashen."""
        mod = M2OFI()
        result = mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        assert result["signal"] == 0
        assert result["e_n"] == 0.0
        assert result["method_id"] == "M2"

    def test_reset_clears_state(self) -> None:
        """Reset setzt alle internen Zustaende zurueck."""
        mod = M2OFI()
        mod.update((100.0, 5.0), (101.0, 5.0), ts=1.0)
        mod.update((102.0, 10.0), (103.0, 10.0), ts=1.1)

        mod.reset()

        assert len(mod._events) == 0
        assert len(mod._ofi_history) == 0
        assert mod._prev_bb == (0.0, 0.0)
        assert mod._prev_ba == (0.0, 0.0)
        assert mod._q90 == 0.0
        assert not mod._initialized

    def test_compute_delegates_to_update(self) -> None:
        """compute() ist ein Wrapper um update()."""
        mod = M2OFI()
        result = mod.compute(best_bid=(100.0, 5.0), best_ask=(101.0, 5.0), ts=1.0)
        assert result["method_id"] == "M2"
        assert "ofi" in result
        assert "signal" in result

    def test_validate(self) -> None:
        """validate() gibt True bei korrekter Konfiguration."""
        mod = M2OFI()
        assert mod.validate() is True

    def test_ofi_q90_updates_with_history(self) -> None:
        """Q90 wird nach genuegend Samples berechnet und ist > 0 bei Varianz."""
        mod = M2OFI()
        base_ts = 0.0
        mod.update((100.0, 5.0), (101.0, 5.0), ts=base_ts)

        # Abwechselnd starke positive/negative e_n erzeugen, eng getaktet
        # damit die rolling sums variieren und abs(ofi) > 0 Werte entstehen
        for i in range(1, _MIN_QUANTILE_SAMPLES + 10):
            if i % 2 == 0:
                mod.update((110.0, 10.0), (111.0, 1.0), ts=base_ts + i * 0.05)
            else:
                mod.update((90.0, 1.0), (91.0, 10.0), ts=base_ts + i * 0.05)

        result = mod.update((100.0, 5.0), (101.0, 5.0), ts=base_ts + (_MIN_QUANTILE_SAMPLES + 11) * 0.05)
        assert result["ofi_q90"] > 0
