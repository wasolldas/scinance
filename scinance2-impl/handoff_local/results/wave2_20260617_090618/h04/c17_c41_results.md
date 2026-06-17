# C-17/C-41 Lead-Lag-Mess-Gate (H-04 · Cross-Sectional, KAPITALFREI)

- **Hypothese:** H-04 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-17T09:07:27+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::trades` (Paar `BTCUSDT`/`ETHUSDT`)
- **Fenster:** 2 · **Surrogates:** 200 · **Seed:** 42 · **BH-FDR alpha:** 0.1
- **Grid:** 1000 ms · **Quantil-Bins:** 3 · **Lags (Bars):** [1, 2, 3, 5, 10] · **Achsen:** TE (C-17), WCOH (C-41)
- **KAPITALFREI:** ja — reines Mess-Gate fuer gerichteten Informationsfluss, KEINE bps/Edge/PnL/Friction-Metrik.

> Der Report liefert jedes Gate-Kriterium einzeln je Fenster. Das GATE-URTEIL (WEITER/DROP) faellt der gate-auditor gegen H-04 — hartes Ein-Fenster-Kriterium (PRD §8.5), Lead-Symbol-Stabilitaet ueber Fenster.

**Existenz in allen Fenstern + Lead-Stabilitaet:** ja
**Lead-Symbole je Fenster:** ['BTCUSDT', 'BTCUSDT'] (stabil: ja)

## Fenster 0 — 3874 gemeinsame Bars
- Zeitspanne: 1780611314526 .. 1780615189170 ms
- Beste Variante (F-LEADLAG): `WCOH_BTCUSDT/ETHUSDT`

| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |
|---|---|---:|---:|---|
| Surrogate p | Konditionale gerichtete Information signifikant > Surrogate-Null, p <= 0.05 (BH-FDR, F-LEADLAG) | 0.0050 | <= 0.05 | ja (FDR sig: ja) |
| Lead-Symbol | Lead-Symbol (Vorzeichen/Richtung) ueber Fenster konsistent | BTCUSDT (Achse TE, Lag 2000.0 ms) | konsistent | siehe oben |

- BH-FDR p_crit: 0.0697 · FDR-signifikante Varianten: 8

| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |
|---|---|---|---:|---:|---:|---|
| `TE_BTCUSDT->ETHUSDT_lag1` | TE | BTCUSDT->ETHUSDT | 1000.0 | 0.0054 | 0.0249 | ja |
| `TE_ETHUSDT->BTCUSDT_lag1` | TE | ETHUSDT->BTCUSDT | 1000.0 | 0.0040 | 0.0647 | ja |
| `TE_BTCUSDT->ETHUSDT_lag2` | TE | BTCUSDT->ETHUSDT | 2000.0 | 0.0074 | 0.0100 | ja |
| `TE_ETHUSDT->BTCUSDT_lag2` | TE | ETHUSDT->BTCUSDT | 2000.0 | 0.0046 | 0.0697 | ja |
| `TE_BTCUSDT->ETHUSDT_lag3` | TE | BTCUSDT->ETHUSDT | 3000.0 | 0.0059 | 0.0149 | ja |
| `TE_ETHUSDT->BTCUSDT_lag3` | TE | ETHUSDT->BTCUSDT | 3000.0 | 0.0046 | 0.0199 | ja |
| `TE_BTCUSDT->ETHUSDT_lag5` | TE | BTCUSDT->ETHUSDT | 5000.0 | 0.0048 | 0.0448 | ja |
| `TE_ETHUSDT->BTCUSDT_lag5` | TE | ETHUSDT->BTCUSDT | 5000.0 | 0.0029 | 0.2786 | nein |
| `TE_BTCUSDT->ETHUSDT_lag10` | TE | BTCUSDT->ETHUSDT | 10000.0 | 0.0037 | 0.1592 | nein |
| `TE_ETHUSDT->BTCUSDT_lag10` | TE | ETHUSDT->BTCUSDT | 10000.0 | 0.0022 | 0.5124 | nein |
| `WCOH_BTCUSDT/ETHUSDT` | WCOH | BTCUSDT->ETHUSDT | 1261.3 | 0.9028 | 0.0050 | ja |

## Fenster 1 — 3875 gemeinsame Bars
- Zeitspanne: 1780615190990 .. 1780619066816 ms
- Beste Variante (F-LEADLAG): `WCOH_BTCUSDT/ETHUSDT`

| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |
|---|---|---:|---:|---|
| Surrogate p | Konditionale gerichtete Information signifikant > Surrogate-Null, p <= 0.05 (BH-FDR, F-LEADLAG) | 0.0050 | <= 0.05 | ja (FDR sig: ja) |
| Lead-Symbol | Lead-Symbol (Vorzeichen/Richtung) ueber Fenster konsistent | BTCUSDT (Achse TE, Lag 1000.0 ms) | konsistent | siehe oben |

- BH-FDR p_crit: 0.0199 · FDR-signifikante Varianten: 4

| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |
|---|---|---|---:|---:|---:|---|
| `TE_BTCUSDT->ETHUSDT_lag1` | TE | BTCUSDT->ETHUSDT | 1000.0 | 0.0087 | 0.0050 | ja |
| `TE_ETHUSDT->BTCUSDT_lag1` | TE | ETHUSDT->BTCUSDT | 1000.0 | 0.0055 | 0.0050 | ja |
| `TE_BTCUSDT->ETHUSDT_lag2` | TE | BTCUSDT->ETHUSDT | 2000.0 | 0.0049 | 0.0199 | ja |
| `TE_ETHUSDT->BTCUSDT_lag2` | TE | ETHUSDT->BTCUSDT | 2000.0 | 0.0028 | 0.2139 | nein |
| `TE_BTCUSDT->ETHUSDT_lag3` | TE | BTCUSDT->ETHUSDT | 3000.0 | 0.0017 | 0.7214 | nein |
| `TE_ETHUSDT->BTCUSDT_lag3` | TE | ETHUSDT->BTCUSDT | 3000.0 | 0.0036 | 0.0746 | nein |
| `TE_BTCUSDT->ETHUSDT_lag5` | TE | BTCUSDT->ETHUSDT | 5000.0 | 0.0037 | 0.0796 | nein |
| `TE_ETHUSDT->BTCUSDT_lag5` | TE | ETHUSDT->BTCUSDT | 5000.0 | 0.0024 | 0.4677 | nein |
| `TE_BTCUSDT->ETHUSDT_lag10` | TE | BTCUSDT->ETHUSDT | 10000.0 | 0.0012 | 0.9104 | nein |
| `TE_ETHUSDT->BTCUSDT_lag10` | TE | ETHUSDT->BTCUSDT | 10000.0 | 0.0009 | 0.9701 | nein |
| `WCOH_BTCUSDT/ETHUSDT` | WCOH | BTCUSDT->ETHUSDT | 2232.6 | 0.9076 | 0.0050 | ja |

---
*Erzeugt von `scripts/c17_c41_lead_lag.py` (Welle-2-WP, read-only Driver, DEC-10). KAPITALFREI. Endgueltiges Gate-Urteil: gate-auditor gegen H-04.*
