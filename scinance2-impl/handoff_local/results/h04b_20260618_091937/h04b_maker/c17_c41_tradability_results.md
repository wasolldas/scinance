# C-17/C-41 Lead-Lag-TRADABILITY-Gate (H-04b · Friction-Wand + Latenz-Haircut, capital_free=FALSE)

- **Hypothese:** H-04b — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-18T09:22:21+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::trades` (Paar `BTCUSDT`/`ETHUSDT`)
- **Fenster:** 2 · **Bootstrap-N:** 200 · **Seed:** 42 · **BH-FDR alpha:** 0.1 (Familie `F-LEADLAG-TRADE`)
- **Grid:** 1000 ms · **Lags (Survivor 1-3 s):** [1, 2, 3] · **horizon = lag (DEC-13 default)**
- **Friction-Wand:** 11 bps · **Slippage:** 4 bps · **Gesamt-Wand:** 6 bps · **Latenz:** 300 ms · **Maker-Sekundaer:** ja
- **Latenz-Haircut angewandt:** ja — Einfang-Fenster `[t+latenz, t+lag+horizon] (ETH capture, causal, no lookahead)`
- **capital_free:** nein — Tradability-Gate (Edge-bps/Friction/Latenz). Bleibt historischer Backtest mit Kostenmodell, KEIN Live-Order-Code, KEIN Geldeinsatz (CLAUDE.md §4).
- **gate_valid_assumptions:** nein (registriert: Wand 11 bps / Latenz 300 ms). WEITER nur gueltig bei latency >= 300 ms UND friction >= 11 bps UND Latenz-Haircut angewandt UND Taker (nicht Maker). Abweichung -> gate_valid_assumptions=false, ein WEITER waere ungueltig (Anti-Gaming, Registry H-04b Z.132; eine andere Annahme ist eine NEUE Hypothese H-04c).

> Maker-Sekundaerfall ist adverse-selection-anfaellig (Fill bevorzugt wenn man falsch liegt); NIE Primaer-Pass. Ein Maker-WEITER bei Taker-DROP ist 'adverse-selection-vorbehaltlich, nicht handelbar bestaetigt' (registry H-04b Z.127).

> Der Report liefert jedes Gate-Kriterium einzeln je Fenster/Lag. Das GATE-URTEIL (WEITER/DROP/PARK) faellt der gate-auditor gegen H-04b — hartes Ein-Fenster-PARK-Kriterium (PRD §8.5), KEIN GRAUBEREICH. Der PRD-§4-A-priori erwartet PARK (abgegraste HFT-Anomalie).

**Alle Fenster mit Netto-Edge-Survivor (FDR-global):** nein · **WEITER-Indikation (nur bei gueltigen Annahmen):** nein
**Pass je Fenster:** [False, False]
**BH-FDR p_crit (global):** 0.0000

## Fenster 0 — 9984 Round-Trips gesamt
- Zeitspanne: 1780611314526 .. 1780615189170 ms
- Beste Variante: `NET_BTCUSDT->ETHUSDT_lag3_h3` (Netto -5.95 bps, bootstrap p 1.0000)
- Fenster hat Netto-Edge-Survivor (per-Fenster-FDR): nein

| Variante | Lag (ms) | Horizon (ms) | Trips | Brutto-Einfang (bps) | Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | FDR-sig (global) | bestanden |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `NET_BTCUSDT->ETHUSDT_lag1_h1` | 1000 | 1000 | 2910 | -0.10 | -0.05 | 6.0 | -6.10 | 1.0000 | 1.0000 | nein | nein |
| `NET_BTCUSDT->ETHUSDT_lag2_h2` | 2000 | 2000 | 3433 | 0.02 | 0.06 | 6.0 | -5.98 | 1.0000 | 0.3433 | nein | nein |
| `NET_BTCUSDT->ETHUSDT_lag3_h3` | 3000 | 3000 | 3641 | 0.05 | 0.08 | 6.0 | -5.95 | 1.0000 | 0.1940 | nein | nein |

- BH-FDR p_crit (Fenster): 0.0000 · FDR-signifikante Varianten (Fenster): 0

## Fenster 1 — 9619 Round-Trips gesamt
- Zeitspanne: 1780615190990 .. 1780619066816 ms
- Beste Variante: `NET_BTCUSDT->ETHUSDT_lag3_h3` (Netto -5.83 bps, bootstrap p 1.0000)
- Fenster hat Netto-Edge-Survivor (per-Fenster-FDR): nein

| Variante | Lag (ms) | Horizon (ms) | Trips | Brutto-Einfang (bps) | Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | FDR-sig (global) | bestanden |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `NET_BTCUSDT->ETHUSDT_lag1_h1` | 1000 | 1000 | 2770 | 0.01 | 0.06 | 6.0 | -5.99 | 1.0000 | 0.4328 | nein | nein |
| `NET_BTCUSDT->ETHUSDT_lag2_h2` | 2000 | 2000 | 3322 | 0.09 | 0.12 | 6.0 | -5.91 | 1.0000 | 0.0100 | nein | nein |
| `NET_BTCUSDT->ETHUSDT_lag3_h3` | 3000 | 3000 | 3527 | 0.17 | 0.19 | 6.0 | -5.83 | 1.0000 | 0.0050 | nein | nein |

- BH-FDR p_crit (Fenster): 0.0000 · FDR-signifikante Varianten (Fenster): 0

---
*Erzeugt von `scripts/c17_c41_tradability.py` (Welle-2-Folge-WP, read-only Driver, H-04b/DEC-13). capital_free=false (Tradability), KEIN Live-Order-Code. Endgueltiges Gate-Urteil: gate-auditor gegen H-04b.*
