# C-01 OFI-Fade-TRADABILITY-Gate (H-05c · Friction-Wand + Latenz-Haircut, capital_free=FALSE)

- **Hypothese:** H-05c — `scinance2-impl/state/hypothesis_registry.md` (+ DEC-16)
- **Erzeugt:** 2026-07-01T15:36:11+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade/SOLUSDT (windows 2026-04-15 + 2026-05-15)` (Symbol SOLUSDT)
- **Fenster:** 2 · **delta (GL-010-Survivor):** [1, 5] s · **horizon = delta** (DEC-16) · **Grid:** 1000 ms
- **Friction-Wand:** 11.0 bps · **Slippage:** 4.0 bps · **Gesamt-Wand:** 6.0 bps · **Latenz:** 300.0 ms · **Maker-Sekundaer:** ja
- **Latenz-Haircut angewandt:** ja — Einfang-Fenster `[t+latenz, t+delta] (SOL capture, causal, no lookahead)`
- **FDR-Familie:** F-OFI-INV-TRADE · **BH-FDR alpha:** 0.1 · **p_crit:** 0.0000
- **capital_free:** nein — Tradability-Gate. Bleibt historischer Backtest mit Kostenmodell, KEIN Live-Order-Code, KEIN Geldeinsatz (CLAUDE.md §4). Kapital-Status PARK.
- **gate_valid_assumptions:** nein — WEITER nur gueltig bei latency>=300ms UND friction>=11bps UND Latenz-Haircut angewandt UND Taker UND Pass-Zelle in {SOL-d1s,SOL-d5s}. Abweichung -> gate_valid_assumptions=false (Anti-Gaming, registry H-05c/DEC-16; andere Annahme = NEUE H-05d).

> Das GATE-URTEIL (WEITER/DROP/PARK) faellt der gate-auditor gegen H-05c — hartes Ein-Fenster-PARK-Kriterium (PRD §8.5), KEIN GRAUBEREICH. Der A-priori erwartet PARK (schwaches Mess-Signal aus GL-010 vs. 15-bps-Wand).

**Tradable-konsistent (Netto>0 + p<=0.05 + FDR-sig in >=2 Fenstern):** nein · **WEITER-Indikation (nur bei gueltigen Annahmen):** nein

## Tradability-Konsistenz je delta

| delta (s) | Fenster gemessen | Fenster bestanden | bestandene Fenster | tradable-konsistent (>=2) |
|---:|---:|---:|---|---|
| 1 | 2 | 0 | [] | nein |
| 5 | 2 | 0 | [] | nein |

## Detail je Fenster / delta

| Fenster | delta (s) | Trips | Brutto-Einfang (bps) | Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | FDR-sig | bestanden |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 1 | 29813 | +0.048 | +0.076 | 6.0 | -5.952 | 1.0000 | 0.0050 | nein | nein |
| 0 | 5 | 29809 | +0.099 | +0.127 | 6.0 | -5.901 | 1.0000 | 0.0050 | nein | nein |
| 1 | 1 | 25523 | +0.031 | +0.057 | 6.0 | -5.969 | 1.0000 | 0.0050 | nein | nein |
| 1 | 5 | 25519 | +0.062 | +0.088 | 6.0 | -5.938 | 1.0000 | 0.0050 | nein | nein |

*Erzeugt von `c01_ofi_tradability/driver.py` (H-05c/DEC-16, read-only Harvester-Backfill). capital_free=false (Tradability), KEIN Live-Order-Code. Endgueltiges Gate-Urteil: gate-auditor gegen H-05c.*