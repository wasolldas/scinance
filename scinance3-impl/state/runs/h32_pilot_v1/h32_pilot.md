# H-32 Pilot (Stufe P) -- Schaetzung, nicht urteilstragend

- Status: **GL-012 (Pilot)** (uebergeben: -)
- result_sha256: `8b63a56eb0a68afb0748f84806b9f491f75f09ac8d980063cdfb8c4893e69627`
- registrierte Datei sha256: `0fadda785f37a9ab24b31f650611a468f5c6bfef8be8fb65a7dc54261c1bbd60`
- Panel-Schnitt 2024-06-30 (letzte Woche 2024-06-24), Fenster 2022-04-18..2024-06-24, w_pilot 114, K {'min': 126, 'median': 206.0, 'max': 339}

## Je Variante

| Variante | x_P | SD_P | SE_P | t_P | 80-%-Band | F2_real | c_real | m* | MDE80* | (i) | (ii) | (iii) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mom1 | -0.03847 | 0.12351 | 0.01157 | -3.33 | [-0.05329, -0.02364] | 0.010331 | 1.000 | 0.00215 | 0.03890 | False | False | False | GL-012 (Pilot) |
| mom2 | -0.05003 | 0.13015 | 0.01219 | -4.10 | [-0.06565, -0.03440] | 0.012016 | 1.000 | 0.00286 | 0.04149 | False | False | False | GL-012 (Pilot) |
| mom4 | -0.04463 | 0.13415 | 0.01256 | -3.55 | [-0.06073, -0.02853] | 0.013072 | 1.000 | 0.00383 | 0.04303 | False | False | False | GL-012 (Pilot) |
| rev_gap | 0.01667 | 0.11611 | 0.01088 | 1.53 | [0.00273, 0.03061] | 0.008559 | 1.000 | 0.00000 | 0.03608 | True | False | False | GL-012 (Pilot) |

- Universum linear_usdt_perpetual (DEC-101 E1; Bereinigung (Strenge), beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl (DEC-101 E1)): 1182 -> 1066 Symbole, ausgeschlossen usdc_perp 68, dated_future 48, other 0; excluded_sha256 `50aaee3c1e63d560b69a7aa42748abdea0e0cf742f6ff3f618e6f00c54083098`

## Uebergaberegel U-4 (DEC-101 Teil 2 (N-3)): k_pred und (1c)-Term

x_P >= max(m* + max_W(z_krit * SE_T,W + z_80 * SD_T,W), max_W(max(0, m_W) + k_pred,W * (q95_W,v - m_W) + z_80 * SD_T,W))

| Variante | k_pred W1 / W2 | Schwelle U (m* + MDE80*_U) | Schwelle (1c) | bindend | Schwelle auf x_P |
|---|---|---|---|---|---|
| mom1 | 2.200 / 2.486 | 0.04105 | 0.04229 | 1c | 0.04229 |
| mom2 | 2.111 / 2.447 | 0.04435 | 0.04583 | 1c | 0.04583 |
| mom4 | 1.884 / 2.228 | 0.04686 | 0.05005 | 1c | 0.05005 |
| rev_gap | 2.053 / 2.299 | 0.03608 | 0.03629 | 1c | 0.03629 |

## Pflicht-Doppelausweis (DEC-99 (3)) und Zuordnung (nur uebergebene Varianten)

| Variante | Regime P-1 | Regime A3-Praxis | mu_sel | gemeinsame Power am Punkt | gemeinsame Power an mu_sel |
|---|---|---|---|---|---|
| (keine Variante uebergeben) | | | | | |

## Nicht uebergebene Varianten

- mom1: GL-012 (Pilot): verfehlte Bedingung(en) (i),(ii),(iii); x_P=-0.038467, SE_P=0.011568, t_P=-3.325, MDE80*=0.038897, m*=0.002152 (p = 1 im BH-Nenner 4; nicht in m von F-WEEK)
- mom2: GL-012 (Pilot): verfehlte Bedingung(en) (i),(ii),(iii); x_P=-0.050026, SE_P=0.012190, t_P=-4.104, MDE80*=0.041489, m*=0.002857 (p = 1 im BH-Nenner 4; nicht in m von F-WEEK)
- mom4: GL-012 (Pilot): verfehlte Bedingung(en) (i),(ii),(iii); x_P=-0.044628, SE_P=0.012564, t_P=-3.552, MDE80*=0.043034, m*=0.003829 (p = 1 im BH-Nenner 4; nicht in m von F-WEEK)
- rev_gap: GL-012 (Pilot): verfehlte Bedingung(en) (ii),(iii); x_P=0.016672, SE_P=0.010875, t_P=1.533, MDE80*=0.036082, m*=0.000000 (p = 1 im BH-Nenner 4; nicht in m von F-WEEK)

## Etiketten

- Pilot, nicht urteilstragend; Screening, nie Konfirmation (C.17/C.18)
- zugelassen nur durch DEC-99 (Pilot-Prior)
- fm8-Skala (Daempfung ~25 %): ein beta-unabhaengiges Signal erscheint zu ~75 %
- Pilot aus anderem Marktregime (2022-2024, Aera-Uebergang ~Mitte 2024)
- Pilotabschnitt nach der Uebergabe fuer jede korrelierte Statistik verbraucht (DEC-99 (5))

Die Uebergabe und `result_sha256` sind vom Orchestrator festzuhalten (DEC-/GL-Vermerk), bevor ein Testfenster gerechnet wird.
