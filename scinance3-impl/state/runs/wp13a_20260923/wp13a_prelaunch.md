# WP-13a -- Vorlauf-Befund (DEC-74 Entscheidung 3)

DEC-74 Entscheidung 3 -- keine reale Signal-Outcome-Verknuepfung berechnet (Siegel-Test).

**KEIN VERDIKT -- keine reale Charakteristik-gegen-reale-Folgewochenrendite-IC wurde in diesem Lauf berechnet.**

## Fenster W1 (2024-07-01..2025-06-30, 53 Wochen, 2024-07-01..2025-06-30)
- Delisting-Symbol-Wochen: 80
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.15890185988733707 (< 0,60 = True, n=53 Wochen)
- W_geurteilt = 52, E_t[1/sqrt(K_t-1)] = 0.04858 (K min/median/max siehe Artefakt)
  - mom1: IC_min_capped = 0.01966, IC_min_raw = 0.01966 (c_rho_raw=1.1098, c_rho_corrected=1.1739)
  - mom2: IC_min_capped = 0.01754, IC_min_raw = 0.01754 (c_rho_raw=0.9744, c_rho_corrected=1.0469)
  - mom4: IC_min_capped = 0.01729, IC_min_raw = 0.01729 (c_rho_raw=0.9589, c_rho_corrected=1.0325)
  - rev_gap: IC_min_capped = 0.01727, IC_min_raw = 0.01727 (c_rho_raw=0.9573, c_rho_corrected=1.0309)
  - vol_rv: IC_min_capped = 0.01694, IC_min_raw = 0.01694 (c_rho_raw=0.9358, c_rho_corrected=1.0110)
  - vol_max: IC_min_capped = 0.01698, IC_min_raw = 0.01698 (c_rho_raw=0.9389, c_rho_corrected=1.0139)
  - vol_beta: IC_min_capped = 0.01675, IC_min_raw = 0.01657 (c_rho_raw=0.9121, c_rho_corrected=0.9891)
- Selektions-Decke K=7 analytisch = 0.00661, gemessen (reine Rauschen) = 0.00919 (n_replicates=300)
- Faktorerhaltende Null v3 (DEC-76), n_reps=1000: sigma_e gesamt=0.06272, sigma_e idiosynkratisch (verwendet)=0.05695
- GL-012-bindende Decke (driftfree, residualisiert) = 0.05776 (driftfree roh, report-only = 0.04791; drifting roh, report-only = 0.05055; drifting residualisiert, report-only = 0.05767)

| Variante | E_t[1/sqrt(K-1)] | c_rho_corrected | IC_min_capped | Decke driftfree roh (Fenster, report-only) | Decke driftfree res (Fenster, bindend GL-012) | Quantil drifting res (bindend Beta-Kontrolle) | Mittel drifting roh (Beta-Prognostizierbarkeit, report-only) |
|---|---|---|---|---|---|---|---|
| mom1 | 0.04858 | 1.1739 | 0.01966 | 0.04791 | 0.05776 | 0.09152 | 0.03292 |
| mom2 | 0.04858 | 1.0469 | 0.01754 | 0.04791 | 0.05776 | 0.10334 | 0.02767 |
| mom4 | 0.04858 | 1.0325 | 0.01729 | 0.04791 | 0.05776 | 0.11262 | 0.02055 |
| rev_gap | 0.04858 | 1.0309 | 0.01727 | 0.04791 | 0.05776 | -0.02753 | 0.00744 |
| vol_rv | 0.04858 | 1.0110 | 0.01694 | 0.04791 | 0.05776 | -0.05837 | 0.00513 |
| vol_max | 0.04858 | 1.0139 | 0.01698 | 0.04791 | 0.05776 | -0.05837 | 0.00513 |
| vol_beta | 0.04858 | 0.9891 | 0.01675 | 0.04791 | 0.05776 | -0.11540 | 0.01014 |

- Survivorship-Fixture: mom1 Diff=-0.00389 (-0.198 IC_min-Einheiten), rev_gap Diff=-0.00327 (-0.189 IC_min-Einheiten), n_deleted=19/419 (kein Verdikt)
- STRESS_REL: 22
- STRESS_ABS: 2

## Fenster W2 (2025-07-01..2026-06-30, 52 Wochen, 2025-07-07..2026-06-29)
- Delisting-Symbol-Wochen: 140
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.14161985512108177 (< 0,60 = True, n=52 Wochen)
- W_geurteilt = 51, E_t[1/sqrt(K_t-1)] = 0.04192 (K min/median/max siehe Artefakt)
  - mom1: IC_min_capped = 0.01744, IC_min_raw = 0.01744 (c_rho_raw=1.1307, c_rho_corrected=1.1948)
  - mom2: IC_min_capped = 0.01558, IC_min_raw = 0.01558 (c_rho_raw=0.9953, c_rho_corrected=1.0677)
  - mom4: IC_min_capped = 0.01541, IC_min_raw = 0.01541 (c_rho_raw=0.9823, c_rho_corrected=1.0555)
  - rev_gap: IC_min_capped = 0.01531, IC_min_raw = 0.01531 (c_rho_raw=0.9756, c_rho_corrected=1.0492)
  - vol_rv: IC_min_capped = 0.01470, IC_min_raw = 0.01470 (c_rho_raw=0.9300, c_rho_corrected=1.0070)
  - vol_max: IC_min_capped = 0.01464, IC_min_raw = 0.01464 (c_rho_raw=0.9254, c_rho_corrected=1.0028)
  - vol_beta: IC_min_capped = 0.01460, IC_min_raw = 0.01354 (c_rho_raw=0.8434, c_rho_corrected=0.9276)
- Selektions-Decke K=7 analytisch = 0.00576, gemessen (reine Rauschen) = 0.00778 (n_replicates=300)
- Faktorerhaltende Null v3 (DEC-76), n_reps=1000: sigma_e gesamt=0.09393, sigma_e idiosynkratisch (verwendet)=0.07281
- GL-012-bindende Decke (driftfree, residualisiert) = 0.05535 (driftfree roh, report-only = 0.02661; drifting roh, report-only = 0.02896; drifting residualisiert, report-only = 0.05530)

| Variante | E_t[1/sqrt(K-1)] | c_rho_corrected | IC_min_capped | Decke driftfree roh (Fenster, report-only) | Decke driftfree res (Fenster, bindend GL-012) | Quantil drifting res (bindend Beta-Kontrolle) | Mittel drifting roh (Beta-Prognostizierbarkeit, report-only) |
|---|---|---|---|---|---|---|---|
| mom1 | 0.04192 | 1.1948 | 0.01744 | 0.02661 | 0.05535 | 0.08563 | 0.01733 |
| mom2 | 0.04192 | 1.0677 | 0.01558 | 0.02661 | 0.05535 | 0.09073 | 0.01449 |
| mom4 | 0.04192 | 1.0555 | 0.01541 | 0.02661 | 0.05535 | 0.09546 | 0.01114 |
| rev_gap | 0.04192 | 1.0492 | 0.01531 | 0.02661 | 0.05535 | -0.02658 | 0.00356 |
| vol_rv | 0.04192 | 1.0070 | 0.01470 | 0.02661 | 0.05535 | -0.04268 | 0.00268 |
| vol_max | 0.04192 | 1.0028 | 0.01464 | 0.02661 | 0.05535 | -0.04268 | 0.00268 |
| vol_beta | 0.04192 | 0.9276 | 0.01460 | 0.02661 | 0.05535 | -0.11057 | 0.00850 |

- Survivorship-Fixture: mom1 Diff=-0.00763 (-0.438 IC_min-Einheiten), rev_gap Diff=-0.00887 (-0.579 IC_min-Einheiten), n_deleted=46/589 (kein Verdikt)
- STRESS_REL: 8
- STRESS_ABS: 1

## Fenster L (2021-03-01..2024-06-30, 174 Wochen, 2021-03-01..2024-06-24)
- Delisting-Symbol-Wochen: 17
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.1146177764214012 (< 0,60 = True, n=156 Wochen)
- H-30 (v2) Kante = 91.42 bp/Woche, Spread(D10-D1)/Kante = 0.395, SE(sigma_w^2/2)/Kante = 0.025 (feasibel <= 0,5 beide: True)
- STRESS_REL: 23
- STRESS_ABS: 19

## NO_HISTORY-Symbole (7)
- BNXUSDT: delistet 2023-02-14 (Woche 2023-02-13)
- DATAUSDT: delistet 2025-05-26 (Woche 2025-05-26)
- KORUUSDT: delistet 2026-07-09 (Woche 2026-07-06)
- LITUSDT: delistet 2025-02-04 (Woche 2025-02-03)
- MONUSDT: delistet 2025-02-27 (Woche 2025-02-24)
- SPCXUSDT: delistet 2026-06-09 (Woche 2026-06-08)
- ZKUSDT: delistet 2024-06-03 (Woche 2024-06-03)

## Abweichungen (zur Bestaetigung durch den Orchestrator)
- PRD 5.3 verlangt einen EIN-TAGES-Gap zwischen Formation und Halteperiode; WP-13 laeuft ausschliesslich auf dem woechentlichen panel_1d/panel_1d_delisted-Panel, der kleinste darstellbare Gap ist daher EINE WOCHE (siehe characteristics.py Modul-Docstring). Abweichung, VOM ORCHESTRATOR VOR DER ZWEITFASSUNG ZU BESTAETIGEN.
- HALF_SQRT2_FACTOR=1/sqrt(2) ist PRD 5.3's eigener woertlicher Faktor; diese Implementierung interpretiert ihn als Kombination der ZWEI unabhaengigen Fenster W1/W2 (siehe prelaunch.py Modul-Docstring). Interpretation, VOM ORCHESTRATOR ZU BESTAETIGEN.

Das W1/W2-Fenster-Detail (Wochenlisten, K-Serien, Persistenz-Null-Replikate) steht in den DEC-53-Artefakten; das L-Fenster liegt in einer separaten, versiegelten Datei (DEC-74 (k)).