# H-09 · Risk-Limit-Tier-Bunching Mess-Gate (F-BUNCH, KAPITALFREI)

- **Hypothese:** H-09 — `scinance2-impl/state/hypothesis_registry.md` (+ DEC-19)
- **Erzeugt:** 2026-07-26T08:52:45+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade (W1 2026-03-27..2026-05-15 + W2 2026-05-16..2026-07-04, DuckDB-side order aggregation, uncapped)` (Symbole: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT)
- **Fenster (vorregistriert):** W1@2026-03-27..2026-05-15, W2@2026-05-16..2026-07-04
- **Beobachtungseinheit:** Taker-Order-Aggregat (konsekutive publicTrade-Records gleichen symbol/side/ts_exchange_ms gemerged), Notional in USDT
- **Methodik:** Band [0.4, 1.3]·K_s, 90 Bins a 0.01·K_s · Polynom Grad 7 (Ausschluss [0.9, 1.1]·K_s) · B- [0.95, 1.0]·K_s, B+ [1.0, 1.05]·K_s · Placebos [0.5, 0.75]·K_s (NICHT in FDR-Familie) · Residuen-Bootstrap (Chetty et al. 2011), Null b-=0 (500 Reps, Seed 42)
- **FDR-Familie:** F-BUNCH · BH-FDR alpha 0.1 · p_crit 0.0000 · FDR-signifikant: 0
- **K_s je Symbol (USDT):** BTCUSDT=2,000,000, ETHUSDT=1,500,000, SOLUSDT=1,000,000, BNBUSDT=500,000, XRPUSDT=500,000
- **PLATZHALTER-WARNUNG:** K_s-Werte fuer ETH/SOL/BNB/XRP sind PLATZHALTER — vor echtem Lauf gegen die aktuelle Bybit-Risk-Limit-Tabelle verifizieren (inkl. Konstanz ueber W1+W2), DEC-09-Muster, datierter append-only Operationalisierungs-Nachtrag erforderlich. Nur BTCUSDT=2.000.000 USDT ist registry-beziffert.
- **KAPITALFREI:** ja — reiner Struktur-/Verhaltensfakt (Notional-Zaehlungen, dimensionslose Excess-Mass-Ratios). Tradability waere NEUE H-09b, NICHT impliziert.
- **gate_valid_assumptions:** ja — WEITER nur gueltig bei n_bootstrap >= 500 UND Polynom-Grad 7 UND N-Floor >= 2000 UND Counterfactual-Floor >= 50 UND Panel = registrierte 5 Symbole UND Fenster = registrierte W1/W2 UND K_s = registrierte Werte UND F-BUNCH-Familiengroesse = 10 (keine Sentinel-Zellen) UND kein Fenster truncated (keine Band-/Bin-/Placebo-Anpassung, Registry H-09). Abweichung -> gate_valid_assumptions=false, eine WEITER-Indikation waere ungueltig.

> Gate-Urteil faellt der gate-auditor gegen H-09. WEITER verlangt fuer >= 1 Symbol in BEIDEN Fenstern (gueltige Zelle): Bootstrap-p <= 0,05 nach BH-FDR alpha=0,10 ueber F-BUNCH UND b- >= 1,0 UND b- - b+ >= 0,5 UND b- > max(b_P1, b_P2). N-Floor: >= 2.000 Order-Beobachtungen im Schaetzband UND Counterfactual-Erwartung in B- >= 50, sonst Zelle ungueltig; alle 5 Zellen eines Fensters ungueltig -> DROP wegen Power. Hartes Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP (Rundzahl-Praeferenz).

**Mind. ein Symbol besteht BEIDE Fenster:** nein · **WEITER-Indikation (nur bei gueltigen Annahmen):** nein · **Alle Zellen ungueltig je Fenster:** [False, False]

## Rollup je Symbol

| Symbol | K_s (USDT) | Platzhalter | Fenster gueltig | Fenster bestanden | beide Fenster |
|---|---:|:---:|---:|---:|:---:|
| BTCUSDT | 2,000,000 | nein | 2/2 | 0 | nein |
| ETHUSDT | 1,500,000 | ja | 1/2 | 0 | nein |
| SOLUSDT | 1,000,000 | ja | 2/2 | 0 | nein |
| BNBUSDT | 500,000 | ja | 0/2 | 0 | nein |
| XRPUSDT | 500,000 | ja | 2/2 | 0 | nein |

## Zellen (Symbol x Fenster, Order-Level)

| Symbol | Fenster | N Band | b- | b+ | b- − b+ | b_P1 | b_P2 | boot p | FDR-sig | b->=1,0 | Asym>=0,5 | Placebo-Dominanz | Zelle gueltig | bestanden |
|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BTCUSDT | W1@2026-03-27..2026-05-15 | 26466 | 1.054 | 0.702 | 0.352 | 6.065 | 14.098 | 0.3573 | nein | ja | nein | nein | ja | nein |
| BTCUSDT | W2@2026-05-16..2026-07-04 | 25574 | 10.198 | 5.763 | 4.436 | 13.280 | 0.287 | 0.1776 | nein | ja | ja | nein | ja | nein |
| ETHUSDT | W1@2026-03-27..2026-05-15 | 18210 | 0.000 | 0.000 | 0.000 | 0.334 | -0.007 | 0.9042 | nein | nein | nein | nein | nein | nein |
| ETHUSDT | W2@2026-05-16..2026-07-04 | 13723 | -1.405 | -1.212 | -0.193 | -0.255 | 0.989 | 0.7265 | nein | nein | nein | nein | ja | nein |
| SOLUSDT | W1@2026-03-27..2026-05-15 | 8404 | 3.329 | 6.910 | -3.581 | -1.748 | -3.106 | 0.0559 | nein | ja | nein | ja | ja | nein |
| SOLUSDT | W2@2026-05-16..2026-07-04 | 7221 | -2.257 | 1.134 | -3.390 | 3.200 | -2.400 | 0.9980 | nein | nein | nein | nein | ja | nein |
| BNBUSDT | W1@2026-03-27..2026-05-15 | 303 | 0.000 | 0.000 | 0.000 | 1.001 | -3.910 | 0.6627 | nein | nein | nein | nein | nein | nein |
| BNBUSDT | W2@2026-05-16..2026-07-04 | 535 | 0.000 | 0.000 | 0.000 | -0.994 | -3.336 | 0.7804 | nein | nein | nein | ja | nein | nein |
| XRPUSDT | W1@2026-03-27..2026-05-15 | 4306 | -3.492 | -3.116 | -0.376 | -2.588 | -1.525 | 0.9980 | nein | nein | nein | nein | ja | nein |
| XRPUSDT | W2@2026-05-16..2026-07-04 | 3275 | 1.765 | 0.076 | 1.689 | -0.396 | -0.556 | 0.3253 | nein | ja | ja | ja | ja | nein |

*Erzeugt von `scripts/c09_bunch.py` (Welle-4, read-only Harvester-Backfill, DEC-19). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-09.*
