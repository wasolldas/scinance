# C-07 Permutation-Entropy-Mess-Gate (H-06, KAPITALFREI)

- **Hypothese:** H-06 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-17T09:11:54+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::kline_1min` (Symbole: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT)
- **Fenster:** 2 · **Surrogates:** 200 · **Seed:** 42 · **BH-FDR alpha:** 0.1
- **Bandt-Pompe Embedding (VORAB FIXIERT, DEC-12):** m = 4, tau = 1 · **Rolling-PE-Fenster:** 240 Bars · **MI-Bins:** 4
- **Vol-Cluster:** RV ueber 15-min-Forward-Fenster (Summe quadrierter 1-min-log-Returns) · **delta-Lags:** [1, 5, 15, 60] min · **Bar-Cap/Fenster:** 43200 (= 30 Tage, Stationaritaets-Cap)
- **G1:** top vol quartile of the surrogate-null distribution (pre-fixed)
- **KAPITALFREI:** ja — reiner Detektions-/Info-Mess-Test, KEINE bps/Edge/PnL/Sharpe/Friction-Metrik.

> Der Report liefert das ZWEISTUFIGE Gate je Fenster EINZELN: PRE-Gate rho (rho >= 0.30 Floor) und je delta das Haupt-Gate (surrogate_p, FDR-sig, AUC-Lift in G1, n_g1). KEIN Gesamturteil. Das GATE-URTEIL (WEITER/DROP) faellt der gate-auditor gegen H-06 (PRE-Gate rho < 0.30 in EINEM Fenster -> DROP; hartes Ein-Fenster-Kriterium PRD §8.5).

**PRE-Gate rho je Fenster:** [0.0044, -0.0059, 0.0111, 0.0025, -0.0001, -0.0004, -0.0002, 0.0145, -0.0006, 0.0081] · alle Fenster rho >= 0.30: nein · >=1 Fenster rho < 0.30: ja
**F-ENTROPY BH-FDR p_crit:** 0.0050 · **FDR-signifikante Varianten:** 2

## PRE-Gate (rho PE-Drop vs. 15-min-Vol-Cluster)

| Symbol | Fenster | n | rho | rho >= 0.30 |
|---|---:|---:|---:|:--:|
| BTCUSDT | 0 | 25744 | 0.0044 | nein |
| BTCUSDT | 1 | 25744 | -0.0059 | nein |
| ETHUSDT | 0 | 25744 | 0.0111 | nein |
| ETHUSDT | 1 | 25744 | 0.0025 | nein |
| SOLUSDT | 0 | 25744 | -0.0001 | nein |
| SOLUSDT | 1 | 25744 | -0.0004 | nein |
| BNBUSDT | 0 | 25744 | -0.0002 | nein |
| BNBUSDT | 1 | 25744 | 0.0145 | nein |
| XRPUSDT | 0 | 25744 | -0.0006 | nein |
| XRPUSDT | 1 | 25744 | 0.0081 | nein |

## Haupt-Gate (bedingte Information PE -> ret/vol_{t+delta})

| Symbol | Fenster | delta (min) | n | MI | Surr p | FDR sig | AUC-Lift | n_g1 | AUC-Lift >= 0.03 | Variante OK |
|---|---:|---:|---:|---:|---:|:--:|---:|---:|:--:|:--:|
| BTCUSDT | 0 | 1 | 25759 | 0.00051 | 0.7214 | nein | -0.0085 | 6457 | nein | nein |
| BTCUSDT | 0 | 5 | 25755 | 0.00364 | 0.1841 | nein | -0.0077 | 6421 | nein | nein |
| BTCUSDT | 0 | 15 | 25745 | 0.00469 | 0.2786 | nein | -0.0077 | 6429 | nein | nein |
| BTCUSDT | 0 | 60 | 25700 | 0.00617 | 0.3085 | nein | -0.0083 | 6438 | nein | nein |
| BTCUSDT | 1 | 1 | 25759 | 0.00047 | 0.6368 | nein | -0.0021 | 6440 | nein | nein |
| BTCUSDT | 1 | 5 | 25755 | 0.00301 | 0.2488 | nein | -0.0010 | 6427 | nein | nein |
| BTCUSDT | 1 | 15 | 25745 | 0.00674 | 0.1592 | nein | -0.0015 | 6431 | nein | nein |
| BTCUSDT | 1 | 60 | 25700 | 0.00531 | 0.5771 | nein | -0.0011 | 6426 | nein | nein |
| ETHUSDT | 0 | 1 | 25759 | 0.00103 | 0.4826 | nein | -0.0014 | 6432 | nein | nein |
| ETHUSDT | 0 | 5 | 25755 | 0.00311 | 0.5522 | nein | -0.0014 | 6442 | nein | nein |
| ETHUSDT | 0 | 15 | 25745 | 0.00396 | 0.5871 | nein | -0.0017 | 6427 | nein | nein |
| ETHUSDT | 0 | 60 | 25700 | 0.01091 | 0.2338 | nein | -0.0014 | 6470 | nein | nein |
| ETHUSDT | 1 | 1 | 25759 | 0.00045 | 0.6915 | nein | -0.0071 | 6433 | nein | nein |
| ETHUSDT | 1 | 5 | 25755 | 0.00149 | 0.6866 | nein | -0.0066 | 6423 | nein | nein |
| ETHUSDT | 1 | 15 | 25745 | 0.00352 | 0.4428 | nein | -0.0071 | 6431 | nein | nein |
| ETHUSDT | 1 | 60 | 25700 | 0.00585 | 0.4577 | nein | -0.0072 | 6414 | nein | nein |
| SOLUSDT | 0 | 1 | 25759 | 0.00031 | 0.7662 | nein | -0.0039 | 6443 | nein | nein |
| SOLUSDT | 0 | 5 | 25755 | 0.00108 | 0.7065 | nein | -0.0041 | 6445 | nein | nein |
| SOLUSDT | 0 | 15 | 25745 | 0.00260 | 0.6567 | nein | -0.0040 | 6433 | nein | nein |
| SOLUSDT | 0 | 60 | 25700 | 0.00730 | 0.2139 | nein | -0.0030 | 6462 | nein | nein |
| SOLUSDT | 1 | 1 | 25759 | 0.00070 | 0.2438 | nein | 0.0088 | 6433 | nein | nein |
| SOLUSDT | 1 | 5 | 25755 | 0.00238 | 0.2239 | nein | 0.0089 | 6439 | nein | nein |
| SOLUSDT | 1 | 15 | 25745 | 0.00335 | 0.3731 | nein | 0.0093 | 6468 | nein | nein |
| SOLUSDT | 1 | 60 | 25700 | 0.00708 | 0.1791 | nein | 0.0088 | 6445 | nein | nein |
| BNBUSDT | 0 | 1 | 25759 | 0.00064 | 0.4627 | nein | -0.0078 | 6436 | nein | nein |
| BNBUSDT | 0 | 5 | 25755 | 0.00231 | 0.3234 | nein | -0.0088 | 6426 | nein | nein |
| BNBUSDT | 0 | 15 | 25745 | 0.00495 | 0.1244 | nein | -0.0071 | 6448 | nein | nein |
| BNBUSDT | 0 | 60 | 25700 | 0.00472 | 0.5274 | nein | -0.0076 | 6433 | nein | nein |
| BNBUSDT | 1 | 1 | 25759 | 0.00089 | 0.3035 | nein | 0.0010 | 6406 | nein | nein |
| BNBUSDT | 1 | 5 | 25755 | 0.00279 | 0.1990 | nein | 0.0010 | 6426 | nein | nein |
| BNBUSDT | 1 | 15 | 25745 | 0.00601 | 0.1343 | nein | 0.0011 | 6410 | nein | nein |
| BNBUSDT | 1 | 60 | 25700 | 0.01232 | 0.0846 | nein | 0.0005 | 6439 | nein | nein |
| XRPUSDT | 0 | 1 | 25759 | 0.00095 | 0.3731 | nein | 0.0028 | 6453 | nein | nein |
| XRPUSDT | 0 | 5 | 25755 | 0.00374 | 0.2587 | nein | 0.0027 | 6423 | nein | nein |
| XRPUSDT | 0 | 15 | 25745 | 0.00553 | 0.2736 | nein | 0.0030 | 6455 | nein | nein |
| XRPUSDT | 0 | 60 | 25700 | 0.00926 | 0.1841 | nein | 0.0027 | 6466 | nein | nein |
| XRPUSDT | 1 | 1 | 25759 | 0.00223 | 0.0149 | nein | 0.0075 | 6420 | nein | nein |
| XRPUSDT | 1 | 5 | 25755 | 0.00735 | 0.0100 | nein | 0.0081 | 6404 | nein | nein |
| XRPUSDT | 1 | 15 | 25745 | 0.01379 | 0.0050 | ja | 0.0072 | 6440 | nein | nein |
| XRPUSDT | 1 | 60 | 25700 | 0.01949 | 0.0050 | ja | 0.0072 | 6451 | nein | nein |

---
**Gate-Schwellen (registriert, NICHT hier beurteilt):** PRE-Gate rho >= 0.3 in >= 2 disjunkten Fenstern (rho < 0.30 in EINEM Fenster -> DROP, kein Voll-Lauf). Haupt-Gate: Surrogate p <= 0.05 nach BH-FDR alpha 0.1 ueber F-ENTROPY in >= 2 Fenstern UND bedingter AUC-Lift >= +0.03 in G1-Fenstern. Hartes Ein-Fenster-DROP-Kriterium (PRD §8.5), kein GRAUBEREICH.

*Erzeugt von `scripts/c07_pe.py` (Welle-2-WP, read-only Driver, DEC-12, kline_1min — NICHT trades). Bandt-Pompe m=4/tau=1 VORAB FIXIERT (kein CLI-Flag). KAPITALFREI. Endgueltiges Gate-Urteil: gate-auditor gegen H-06.*
