# WP-13a -- Vorlauf-Befund (DEC-74 Entscheidung 3)

DEC-74 Entscheidung 3 -- keine reale Signal-Outcome-Verknuepfung berechnet (Siegel-Test).

**KEIN VERDIKT -- keine reale Charakteristik-gegen-reale-Folgewochenrendite-IC wurde in diesem Lauf berechnet.**

## Fenster W1 (2024-07-01..2025-06-30, 53 Wochen, 2024-07-01..2025-06-30)
- Delisting-Symbol-Wochen: 80
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.15890185988733707 (< 0,60 = True, n=53 Wochen)
- E_t[1/sqrt(K_t-1)] = 0.04849 (K min/median/max siehe Artefakt)
  - mom1: IC_min = 0.01838 (c_rho=1.1099)
  - mom2: IC_min = 0.01614 (c_rho=0.9744)
  - mom4: IC_min = 0.01588 (c_rho=0.9589)
  - rev_gap: IC_min = 0.01585 (c_rho=0.9572)
  - vol_rv: IC_min = 0.01550 (c_rho=0.9358)
  - vol_max: IC_min = 0.01555 (c_rho=0.9389)
  - vol_beta: IC_min = 0.01511 (c_rho=0.9120)
- Selektions-Decke K=7 analytisch = 0.00653, gemessen = 0.00909 (n_replicates=300)
- STRESS_REL: 22
- STRESS_ABS: 2

## Fenster W2 (2025-07-01..2026-06-30, 52 Wochen, 2025-07-07..2026-06-29)
- Delisting-Symbol-Wochen: 140
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.14161985512108177 (< 0,60 = True, n=52 Wochen)
- E_t[1/sqrt(K_t-1)] = 0.04190 (K min/median/max siehe Artefakt)
  - mom1: IC_min = 0.01634 (c_rho=1.1308)
  - mom2: IC_min = 0.01438 (c_rho=0.9953)
  - mom4: IC_min = 0.01419 (c_rho=0.9822)
  - rev_gap: IC_min = 0.01409 (c_rho=0.9755)
  - vol_rv: IC_min = 0.01343 (c_rho=0.9299)
  - vol_max: IC_min = 0.01337 (c_rho=0.9254)
  - vol_beta: IC_min = 0.01218 (c_rho=0.8433)
- Selektions-Decke K=7 analytisch = 0.00570, gemessen = 0.00809 (n_replicates=300)
- STRESS_REL: 8
- STRESS_ABS: 1

## Fenster L (2021-03-01..2024-06-30, 174 Wochen, 2021-03-01..2024-06-24)
- Delisting-Symbol-Wochen: 17
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.1146177764214012 (< 0,60 = True, n=156 Wochen)
- H-30 Kante = 91.42 bp/Woche, Drag_rest = 8.51 bp/Woche, Drag_rest/Kante = 0.093 (feasibel <= 0,5: True)
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