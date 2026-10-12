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
- Selektions-Decke K=7 analytisch ohne Faktor 1/sqrt(2) (DEC-87 (C)) = 0.00934 (v5d-Zeile mit Faktor, historisch = 0.00661), gemessen (reines Rauschen) = 0.00919 (n_replicates=300)
- Faktorerhaltende Null v3 (DEC-76), n_reps=1000: sigma_e gesamt=0.17186, sigma_e idiosynkratisch (verwendet)=0.12064
- v3-TS-Decke (driftfree, TS-residualisiert, rho_f 0,2) -- HISTORISCH, NICHT BINDEND (DEC-87 (A)) = 0.04963 (driftfree roh, report-only = 0.01773; drifting roh, report-only = 0.01877; drifting residualisiert, report-only = 0.04721)

| Variante | E_t[1/sqrt(K-1)] | c_rho_corrected | IC_min_capped | Decke driftfree roh (Fenster, report-only) | Decke driftfree res (TS v3, historisch, nicht bindend) | Quantil drifting res (TS v3, historisch, nicht bindend) | Mittel drifting roh (Beta-Prognostizierbarkeit, report-only) |
|---|---|---|---|---|---|---|---|
| mom1 | 0.04858 | 1.1739 | 0.01966 | 0.01773 | 0.04963 | 0.05074 | 0.01019 |
| mom2 | 0.04858 | 1.0469 | 0.01754 | 0.01773 | 0.04963 | 0.06551 | 0.00892 |
| mom4 | 0.04858 | 1.0325 | 0.01729 | 0.01773 | 0.04963 | 0.08115 | 0.00670 |
| rev_gap | 0.04858 | 1.0309 | 0.01727 | 0.01773 | 0.04963 | -0.02059 | 0.00253 |
| vol_rv | 0.04858 | 1.0110 | 0.01694 | 0.01773 | 0.04963 | -0.04279 | 0.00108 |
| vol_max | 0.04858 | 1.0139 | 0.01698 | 0.01773 | 0.04963 | -0.04279 | 0.00108 |
| vol_beta | 0.04858 | 0.9891 | 0.01675 | 0.01773 | 0.04963 | -0.14894 | 0.00353 |

- Survivorship-Fixture: mom1 Diff=-0.00389 (-0.198 IC_min-Einheiten), rev_gap Diff=-0.00327 (-0.189 IC_min-Einheiten), n_deleted=19/419 (kein Verdikt)

- **DEC-77 Kalibrierung** (26-Wochen-PIT-Beta, 'vorherige Wochen'): rho_f_gemessen=0.0462, sigma_f=0.06685 (n=53 Wochen); Faktoranteil (Median Querschnitts-R^2)=0.0321 (n=53 Wochen); Beta-Dispersion (PIT-Pool, ueberwiegend Schaetzrauschen -- DEC-78 Befund): SD=0.6045, Quantile[0.05/0.25/0.5/0.75/0.95]=[0.691/1.276/1.582/1.947/2.560] (n_gepoolt=18348)
  - Analytische Approximation (Plausibilitaetszeile, DEC-77 item 4) -- KEIN Verdikt. (2/pi)*arcsin(rho_f_measured) * factor_share_median = 0.00095
  - DEC-78 Entscheidung 1: wahre Beta-Dispersion aus dem gemessenen Faktoranteil (ersetzt den PIT-Beta-Pool, ueberwiegend Schaetzrauschen -- DEC-78 Befund). sqrt(share/(1-share)) * sigma_e_used/sigma_f = 0.32870

| Kalibrierung | rho_f | beta_sd (analyt. Erstschaetzung) | beta_sd (kalibriert) | Ziel-Faktoranteil | erreichter Faktoranteil (Suche) | wahrer Faktoranteil (Suche) | Iterationen | konvergiert | Gegenprobe simuliert | Gegenprobe rel. Abw. | Gegenprobe se_diff | Gegenprobe z | Marktspalte SD-Band | rho-Band | Gegenprobe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| measured | 0.04624 | 0.32870 | 0.57367 | 0.03211 | 0.03196 | 0.08116 | 10 | ja | 0.03282 | 0.02200 | 0.00113 | 0.62644 | [0.05417, 0.07971] (Ziel 0.06685: ok) | [-0.23983, 0.27498] (Ziel 0.04624: ok) | OK |
| stress | 0.09248 | 0.47276 | 0.77067 | 0.06422 | 0.06373 | 0.12819 | 8 | ja | 0.06426 | 0.00068 | 0.00210 | 0.02088 | [0.05414, 0.07980] (Ziel 0.06685: ok) | [-0.20356, 0.32353] (Ziel 0.09248: ok) | OK |
| zero | 0.00000 | 0.32870 | 0.57687 | 0.03211 | 0.03205 | 0.08178 | 7 | ja | 0.03325 | 0.03541 | 0.00110 | 1.02928 | [0.05428, 0.07985] (Ziel 0.06685: ok) | [-0.28396, 0.23476] (Ziel 0.00000: ok) | OK |

- Beta-Kontroll-Kriterium: |Null-Mittel| <= 0.00168 UND Decke <= 0.01378 (measured UND stress)

| Methode | measured Null-Mittel | measured Decke | stress Null-Mittel | stress Decke | PASS |
|---|---|---|---|---|---|
| none | 0.00326 | 0.01770 | 0.01071 | 0.02777 | FAIL |
| fm_neutral_8w | 0.00071 | 0.00750 | 0.00123 | 0.00810 | PASS |
| fm_neutral_13w | 0.00049 | 0.00764 | 0.00069 | 0.00776 | PASS |
| fm_neutral_26w | 0.00099 | 0.00959 | 0.00104 | 0.00943 | PASS |
| double_sort_13w | 0.00055 | 0.00888 | 0.00119 | 0.00967 | PASS |
| double_sort_26w | 0.00111 | 0.01077 | 0.00169 | 0.01139 | FAIL |

- Gewinner-Methode, hoehere Replikatzahl (n_reps=1000): measured Decke=0.00757, stress Decke=0.00834 (Details: Abschnitte Gewinner-Bestaetigung / bindende Decke / Drift-Quantile)
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
- Selektions-Decke K=7 analytisch ohne Faktor 1/sqrt(2) (DEC-87 (C)) = 0.00814 (v5d-Zeile mit Faktor, historisch = 0.00576), gemessen (reines Rauschen) = 0.00778 (n_replicates=300)
- Faktorerhaltende Null v3 (DEC-76), n_reps=1000: sigma_e gesamt=0.13311, sigma_e idiosynkratisch (verwendet)=0.10729
- v3-TS-Decke (driftfree, TS-residualisiert, rho_f 0,2) -- HISTORISCH, NICHT BINDEND (DEC-87 (A)) = 0.04993 (driftfree roh, report-only = 0.01557; drifting roh, report-only = 0.01680; drifting residualisiert, report-only = 0.04697)

| Variante | E_t[1/sqrt(K-1)] | c_rho_corrected | IC_min_capped | Decke driftfree roh (Fenster, report-only) | Decke driftfree res (TS v3, historisch, nicht bindend) | Quantil drifting res (TS v3, historisch, nicht bindend) | Mittel drifting roh (Beta-Prognostizierbarkeit, report-only) |
|---|---|---|---|---|---|---|---|
| mom1 | 0.04192 | 1.1948 | 0.01744 | 0.01557 | 0.04993 | 0.05179 | 0.00911 |
| mom2 | 0.04192 | 1.0677 | 0.01558 | 0.01557 | 0.04993 | 0.06646 | 0.00767 |
| mom4 | 0.04192 | 1.0555 | 0.01541 | 0.01557 | 0.04993 | 0.07823 | 0.00587 |
| rev_gap | 0.04192 | 1.0492 | 0.01531 | 0.01557 | 0.04993 | -0.02152 | 0.00190 |
| vol_rv | 0.04192 | 1.0070 | 0.01470 | 0.01557 | 0.04993 | -0.03918 | 0.00096 |
| vol_max | 0.04192 | 1.0028 | 0.01464 | 0.01557 | 0.04993 | -0.03918 | 0.00096 |
| vol_beta | 0.04192 | 0.9276 | 0.01460 | 0.01557 | 0.04993 | -0.16218 | 0.00470 |

- Survivorship-Fixture: mom1 Diff=-0.00763 (-0.438 IC_min-Einheiten), rev_gap Diff=-0.00887 (-0.579 IC_min-Einheiten), n_deleted=46/589 (kein Verdikt)

- **DEC-77 Kalibrierung** (26-Wochen-PIT-Beta, 'vorherige Wochen'): rho_f_gemessen=0.0416, sigma_f=0.05514 (n=52 Wochen); Faktoranteil (Median Querschnitts-R^2)=0.0139 (n=52 Wochen); Beta-Dispersion (PIT-Pool, ueberwiegend Schaetzrauschen -- DEC-78 Befund): SD=0.7825, Quantile[0.05/0.25/0.5/0.75/0.95]=[0.325/1.027/1.421/1.889/2.841] (n_gepoolt=25277)
  - Analytische Approximation (Plausibilitaetszeile, DEC-77 item 4) -- KEIN Verdikt. (2/pi)*arcsin(rho_f_measured) * factor_share_median = 0.00037
  - DEC-78 Entscheidung 1: wahre Beta-Dispersion aus dem gemessenen Faktoranteil (ersetzt den PIT-Beta-Pool, ueberwiegend Schaetzrauschen -- DEC-78 Befund). sqrt(share/(1-share)) * sigma_e_used/sigma_f = 0.23089

| Kalibrierung | rho_f | beta_sd (analyt. Erstschaetzung) | beta_sd (kalibriert) | Ziel-Faktoranteil | erreichter Faktoranteil (Suche) | wahrer Faktoranteil (Suche) | Iterationen | konvergiert | Gegenprobe simuliert | Gegenprobe rel. Abw. | Gegenprobe se_diff | Gegenprobe z | Marktspalte SD-Band | rho-Band | Gegenprobe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| measured | 0.04158 | 0.23089 | 0.44648 | 0.01389 | 0.01375 | 0.04735 | 9 | ja | 0.01476 | 0.06325 | 0.00046 | 1.90481 | [0.04514, 0.06542] (Ziel 0.05514: ok) | [-0.23837, 0.26422] (Ziel 0.04158: ok) | OK |
| stress | 0.08317 | 0.32886 | 0.58333 | 0.02777 | 0.02795 | 0.07449 | 9 | ja | 0.02899 | 0.04388 | 0.00098 | 1.24421 | [0.04538, 0.06585] (Ziel 0.05514: ok) | [-0.19670, 0.31072] (Ziel 0.08317: ok) | OK |
| zero | 0.00000 | 0.23089 | 0.44648 | 0.01389 | 0.01379 | 0.04726 | 9 | ja | 0.01477 | 0.06402 | 0.00047 | 1.89807 | [0.04514, 0.06538] (Ziel 0.05514: ok) | [-0.27506, 0.23211] (Ziel 0.00000: ok) | OK |

- Beta-Kontroll-Kriterium: |Null-Mittel| <= 0.00147 UND Decke <= 0.01167 (measured UND stress)

| Methode | measured Null-Mittel | measured Decke | stress Null-Mittel | stress Decke | PASS |
|---|---|---|---|---|---|
| none | 0.00172 | 0.01154 | 0.00582 | 0.01740 | FAIL |
| fm_neutral_8w | 0.00045 | 0.00615 | 0.00056 | 0.00669 | PASS |
| fm_neutral_13w | 0.00054 | 0.00659 | 0.00038 | 0.00670 | PASS |
| fm_neutral_26w | 0.00043 | 0.00756 | 0.00037 | 0.00749 | PASS |
| double_sort_13w | 0.00047 | 0.00775 | 0.00072 | 0.00821 | PASS |
| double_sort_26w | 0.00050 | 0.00900 | 0.00098 | 0.00929 | PASS |

- Gewinner-Methode, hoehere Replikatzahl (n_reps=1000): measured Decke=0.00637, stress Decke=0.00685 (Details: Abschnitte Gewinner-Bestaetigung / bindende Decke / Drift-Quantile)
- STRESS_REL: 8
- STRESS_ABS: 1

## Fenster L (2021-03-01..2024-06-30, 174 Wochen, 2021-03-01..2024-06-24)
- Delisting-Symbol-Wochen: 17
- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = 0.1146177764214012 (< 0,60 = True, n=156 Wochen)
- H-30 (v2, Wocheneinheiten, DEC-87 (G)) Kante = 91.42 bp/Woche, Spread(D10-D1)/Kante = 2.764, SE(sigma_w^2/2)/Kante = 0.175 (feasibel <= 0,5 beide: False)
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

## Gewinner-Bestaetigung (DEC-87 V1, DEC-77-Regel unveraendert)
- Gewinner bestaetigt: fm_neutral_8w besteht die unveraenderte DEC-77-Regel mit 1000 Replikaten in W1 und W2 (je Fenster eigene Kalibrierung)
- Reihenfolge nach der Auswahlregel: ['fm_neutral_8w', 'fm_neutral_13w', 'double_sort_13w', 'fm_neutral_26w']; Replikate je Zelle: 1000; je Fenster die EIGENE Kalibrierung (measured/stress).

| Fenster | Methode | n_reps | measured Null-Mittel | Grenze | measured Decke | Grenze | stress Null-Mittel | stress Decke | Regel | Ergebnis |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 | fm_neutral_8w | 1000 | 0.00072 | 0.00168 | 0.00757 | 0.01378 | 0.00165 | 0.00834 | PASS | bestaetigt |
| W2 | fm_neutral_8w | 1000 | 0.00022 | 0.00147 | 0.00637 | 0.01167 | 0.00084 | 0.00685 | PASS | bestaetigt |

## Bindende GL-012-Decke (DEC-87 (A)) und Drift-Quantile (DEC-87 (E))
- Bindende Decke je Fenster = Mittel des Maximums ueber K=7 der bestaetigten Methode unter der STRESS-Kalibrierung des Fensters, driftfrei, Seed 53 (`ceiling_method_stress`). Die Zeile 'Decke driftfree res' der TS-Residualisierung (v3, rho_f 0,2) ist **historisch, nicht bindend**.

- W1: Methode fm_neutral_8w, stress (rho_f=0.09248, beta_sd=0.77067), n_reps=1000, Seed 53: **Decke (bindend) = 0.00834** (drifting, report-only = 0.00851)

| Variante (W1) | Quantil driftfrei | Quantil drifting (0,002/Woche) | bindend (extremeres) |
|---|---|---|---|
| mom1 | 0.02244 | 0.02219 | 0.02244 |
| mom2 | 0.02756 | 0.02780 | 0.02780 |
| mom4 | 0.03243 | 0.03331 | 0.03331 |
| rev_gap | -0.01666 | -0.01659 | -0.01666 |
| vol_rv | -0.01843 | -0.01748 | -0.01843 |
| vol_max | -0.01843 | -0.01748 | -0.01843 |
| vol_beta | -0.00557 | -0.00559 | -0.00559 |

- W2: Methode fm_neutral_8w, stress (rho_f=0.08317, beta_sd=0.58333), n_reps=1000, Seed 53: **Decke (bindend) = 0.00685** (drifting, report-only = 0.00696)

| Variante (W2) | Quantil driftfrei | Quantil drifting (0,002/Woche) | bindend (extremeres) |
|---|---|---|---|
| mom1 | 0.01700 | 0.01691 | 0.01700 |
| mom2 | 0.02029 | 0.02043 | 0.02043 |
| mom4 | 0.02490 | 0.02506 | 0.02506 |
| rev_gap | -0.01546 | -0.01514 | -0.01546 |
| vol_rv | -0.01639 | -0.01609 | -0.01639 |
| vol_max | -0.01639 | -0.01609 | -0.01639 |
| vol_beta | -0.00483 | -0.00486 | -0.00486 |

## H-30-Feasibility in Wocheneinheiten (DEC-87 (G))
- sigma_w = sqrt(n_t) * vol_rv, Drag = +sigma_w^2/2 auf dem Log-Outcome; Kante = 91.42 bp/Woche; Spread(D10-D1)/Kante = 2.764; SE(sigma_w^2/2)/Kante = 0.175 (n_Tage Median 7.0); feasibel (beide <= 0,5): False. **GL-012 fuer H-30 vor dem Lauf (DEC-74 (h), DEC-87 (G)); K bleibt 7.**

## Gate-(5)-Erreichbarkeit (DEC-87 V5; Median Spearman(Rang, Turnover-Rang) < 0,60)
| Fenster | vol_rv | vol_max | vol_beta |
|---|---|---|---|
| W1 | 0.159 (erreichbar) | 0.150 (erreichbar) | 0.154 (erreichbar) |
| W2 | 0.142 (erreichbar) | 0.104 (erreichbar) | 0.050 (erreichbar) |
| L | 0.115 (erreichbar) | 0.113 (erreichbar) | 0.068 (erreichbar) |

## Daten-Fingerprints (DEC-87 V9)
- union_range_fingerprint: a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a
- delisting_dates_sha256: 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
- union_range_detail: {'year_range': [2021, 2026], 'n_partitions': 6507, 'survivors_fingerprint': 'abccdbd3e0a809ac5723ac7a5d6055e55b864c72f5c2980c11dc920aedecfabc', 'delisted_fingerprint': '08be8556de8ed13227f80ff3b79f760b3c6b65ac428a38d41bf66c5746660dcd', 'n_symbols': 1138, 'as_of': '2026-09-28'}

## DEC-77 Beta-Kontroll-Empfehlung
- Empfehlung: fm_neutral_8w (kleinste residualisierte SD ueber Fenster gemittelt, Tie -> kuerzeres Beta-Fenster). (Fenster 8, zulaessige Methoden: double_sort_13w, fm_neutral_13w, fm_neutral_26w, fm_neutral_8w)

## Abweichungen (registriert/etikettiert, DEC-87 (B)/(C))
- PRD 5.3 verlangt einen EIN-TAGES-Gap zwischen Formation und Halteperiode; WP-13 laeuft auf dem woechentlichen panel_1d/panel_1d_delisted-Panel, der kleinste Gap auf dem Wochenraster ist EINE WOCHE (siehe characteristics.py Modul-Docstring). DEC-87 (B): registrierte, etikettierte Abweichung von PRD 5.3 (Lag-2-Reversal; PRD-Ein-Tages-Design nicht getestet); der Bounce wird mindestens so streng eliminiert wie bei einem Tag Gap.
- HALF_SQRT2_FACTOR=1/sqrt(2) ist PRD 5.3's eigener woertlicher Faktor (sigma_SR eines gepoolten Zwei-Jahres-Schaetzers). DEC-87 (C): fuer die Je-Fenster-Decke VERWORFEN; die analytische Report-Zeile ist z_max * SE_W (ceiling_ic_without_factor), die v5d-Zeile mit Faktor bleibt historisch. Keine bindende Zahl haengt daran (bindend ist die Methoden-Decke unter stress, DEC-87 (A)).
- Die Zeile 'factor_preserving_null.driftfree.selection_ceiling_mean_of_max_residualized' (TS-8w-Residualisierung, rho_f 0,2) ist historisch, NICHT bindend (DEC-87 (A)): andere Statistik als die registrierte Methode, durch DEC-77/78 widerlegte Null.

Das W1/W2-Fenster-Detail (Wochenlisten, K-Serien, Persistenz-Null-Replikate) steht in den DEC-53-Artefakten; das L-Fenster liegt in einer separaten, versiegelten Datei (DEC-74 (k)).