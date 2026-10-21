# H-32 Vorlauf v6 (outcome-frei)

- result_sha256: `2ae9bad63a69580d551183764579318f7e5f82f1bc050a30c9bd470c09dd6fa0`
- Stichtag (Panel-Schnitt): 2026-06-28, letzte Woche 2026-06-22, 287 Wochen, 956 Symbole
- Replikate 1000, Bootstrap 1000, Seed 53
- Daten-Fingerprints: `{'union_range_fingerprint': 'e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589', 'delisting_dates_sha256': 'c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3', 'delisting_register_sha256': 'a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22', 'delisted_tree_sha256': '250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401', 'union_range_detail': {'year_range': [2021, 2026], 'n_partitions': 5940, 'n_symbols': 1182, 'as_of': '2026-09-28'}}`

## Fenster

| Fenster | Wochen | w_judged | K min/Median/max | floor_fm8 | v_fm8 | K-Reihe sha256 |
|---|---|---|---|---|---|---|
| P | 2022-04-18..2024-06-24 | 114 | 127/213/353 | 0.068771 | 0.004804 | `b2584131bbe2...` |
| W1 | 2024-07-01..2025-06-30 | 52 | 360/440/536 | 0.047441 | 0.002258 | `8b7eb6ff2f3d...` |
| W2 | 2025-07-07..2026-06-22 | 50 | 537/590/603 | 0.041552 | 0.001727 | `4ea9739edcad...` |

## Kalibrierung je Fenster (nur Streuung / Autokorrelation / Faktoranteil)

| Fenster | Kalibrierung | rho_f | beta_sd | Ziel-Faktoranteil | Gegenprobe |
|---|---|---|---|---|---|
| P | stress | 0.235207 | 0.527683 | 0.035204 | z 1.369 ok True |
| W1 | measured | 0.046241 | 0.536575 | 0.026613 | z 1.150 ok True |
| W1 | stress | 0.092481 | 0.712858 | 0.053227 | z 0.901 ok True |
| W1 | zero | 0.000000 | 0.539572 | 0.026613 | z 1.512 ok True |
| W2 | measured | 0.070203 | 0.441533 | 0.013306 | z 1.268 ok True |
| W2 | stress | 0.140405 | 0.570480 | 0.026613 | z 1.118 ok True |
| W2 | zero | 0.000000 | 0.441533 | 0.013306 | z 0.865 ok True |

## Pilot-Null m_P (stress, Richtung, extremeres aus driftfrei / Drift)

| Variante | m_P |
|---|---|
| mom1 | 0.002176 |
| mom2 | 0.003274 |
| mom4 | 0.004296 |
| rev_gap | -0.002540 |

## Eingefrorene Konstanten W1

| Variante | se_mean | e_se_rule | sd_week | null_mean | q95 | q95 driftfrei | q95 Drift |
|---|---|---|---|---|---|---|---|
| mom1 | 0.006982 | 0.007250 | 0.050019 | 0.001101 | 0.012655 | 0.012263 | 0.012655 |
| mom2 | 0.007723 | 0.007968 | 0.055793 | 0.001344 | 0.014786 | 0.014786 | 0.014605 |
| mom4 | 0.009397 | 0.009313 | 0.065547 | 0.001835 | 0.017766 | 0.017751 | 0.017766 |
| rev_gap | 0.007098 | 0.007235 | 0.049802 | -0.000800 | 0.010149 | 0.010132 | 0.010149 |

- ceiling_k4 W1 (vorzeichenbereinigt, stress, driftfrei): 0.007602
- bounce_sigma_true W1: 0.172364; Survivorship (Schwellen-Einheiten): mom1 -0.696, rev_gap -0.507
- stress_rel: 22 Tage im Fenster (Datumsfilter <= 2026-06-28)
- stress_abs: 2 Tage im Fenster (Datumsfilter <= 2026-06-28)

## Eingefrorene Konstanten W2

| Variante | se_mean | e_se_rule | sd_week | null_mean | q95 | q95 driftfrei | q95 Drift |
|---|---|---|---|---|---|---|---|
| mom1 | 0.006389 | 0.006406 | 0.043140 | 0.001238 | 0.011792 | 0.011264 | 0.011792 |
| mom2 | 0.007357 | 0.006902 | 0.047323 | 0.001626 | 0.014182 | 0.013926 | 0.014182 |
| mom4 | 0.008621 | 0.007900 | 0.054706 | 0.002172 | 0.017004 | 0.017004 | 0.016875 |
| rev_gap | 0.006444 | 0.006374 | 0.043002 | -0.001107 | 0.008571 | 0.008571 | 0.008412 |

- ceiling_k4 W2 (vorzeichenbereinigt, stress, driftfrei): 0.006975
- bounce_sigma_true W2: 0.132020; Survivorship (Schwellen-Einheiten): mom1 -0.823, rev_gap -0.518
- stress_rel: 8 Tage im Fenster (Datumsfilter <= 2026-06-28)
- stress_abs: 1 Tage im Fenster (Datumsfilter <= 2026-06-28)

## Replikate fuer p (DEC-99, faktorerhaltende Null)

- Datei `h32_prelaunch_p_replicates.json` sha256 `f10250dda8e842c7e748e758cad97926361edc30011c43b18c84a70e02847a62`; R = 10000 (Konstanten aus den ersten 1000), Seed 53
- p = (1 + #{Replikat-Fenstermittel >= beobachtetes Fenstermittel in Richtung}) / (1 + R); je Fenster und Variante die Zelle mit dem groesseren Null-Mittel; Max-p ueber W1 / W2. Blockpermutation und Normalnaeherung sind report-only.

| Fenster | Variante | Zelle | Null-Mittel der Replikate |
|---|---|---|---|
| W1 | mom1 | drifting | 0.001101 |
| W1 | mom2 | drifting | 0.001344 |
| W1 | mom4 | drifting | 0.001835 |
| W1 | rev_gap | driftfree | -0.000800 |
| W2 | mom1 | drifting | 0.001238 |
| W2 | mom2 | drifting | 0.001626 |
| W2 | mom4 | drifting | 0.002172 |
| W2 | rev_gap | driftfree | -0.001107 |

## W1-Determinismus-Kontrolle gegen v5e

nicht angefordert (--v5e-reference)

KEIN VERDIKT -- der Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung.
