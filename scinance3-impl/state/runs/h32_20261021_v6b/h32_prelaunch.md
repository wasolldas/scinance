# H-32 Vorlauf v6 (outcome-frei)

- result_sha256: `eee9ced98582913b891b2466990f467f8a58db58d8a880bab7d19ca0be965ab1`
- Stichtag (Panel-Schnitt): 2026-06-28, letzte Woche 2026-06-22, 287 Wochen, 882 Symbole
- Replikate 1000, Bootstrap 1000, Seed 53
- Daten-Fingerprints: `{'union_range_fingerprint': 'e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589', 'delisting_dates_sha256': 'c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3', 'delisting_register_sha256': 'a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22', 'delisted_tree_sha256': '250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401', 'union_range_detail': {'year_range': [2021, 2026], 'n_partitions': 5940, 'n_symbols': 1182, 'as_of': '2026-09-28'}}`
- Universum linear_usdt_perpetual (DEC-101 E1; Bereinigung (Strenge), beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl (DEC-101 E1)): 1182 -> 1066 Symbole; ausgeschlossen: usdc_perp 68, dated_future 48, other 0; excluded_sha256 `50aaee3c1e63d560b69a7aa42748abdea0e0cf742f6ff3f618e6f00c54083098`
- Runner (DEC-101 E4): as_of 2026-09-28, start_year 2021, end_year 2026, allow_partial True

## Fenster

| Fenster | Wochen | w_judged | K min/Median/max | floor_fm8 | v_fm8 | K-Reihe sha256 |
|---|---|---|---|---|---|---|
| P | 2022-04-18..2024-06-24 | 114 | 126/206/339 | 0.069642 | 0.004924 | `4a2f09376d8e...` |
| W1 | 2024-07-01..2025-06-30 | 52 | 343/416/500 | 0.048821 | 0.002391 | `f35fb20b6514...` |
| W2 | 2025-07-07..2026-06-22 | 50 | 501/526/545 | 0.043639 | 0.001905 | `6b69b6f7bbd0...` |

## Kalibrierung je Fenster (nur Streuung / Autokorrelation / Faktoranteil)

| Fenster | Kalibrierung | rho_f | beta_sd | Ziel-Faktoranteil | Gegenprobe |
|---|---|---|---|---|---|
| P | stress | 0.235207 | 0.527683 | 0.035905 | z 2.486 ok True |
| W1 | measured | 0.046241 | 0.539572 | 0.025837 | z 1.217 ok True |
| W1 | stress | 0.092481 | 0.716839 | 0.051675 | z 0.635 ok True |
| W1 | zero | 0.000000 | 0.539572 | 0.025837 | z 1.304 ok True |
| W2 | measured | 0.070203 | 0.439081 | 0.012387 | z 0.079 ok True |
| W2 | stress | 0.140405 | 0.570480 | 0.024774 | z 0.265 ok True |
| W2 | zero | 0.000000 | 0.439081 | 0.012387 | z 0.373 ok True |

## Pilot-Null m_P (stress, Richtung, extremeres aus driftfrei / Drift)

| Variante | m_P |
|---|---|
| mom1 | 0.002152 |
| mom2 | 0.002857 |
| mom4 | 0.003829 |
| rev_gap | -0.002079 |

## Eingefrorene Konstanten W1

| Variante | se_mean | e_se_rule | sd_week | null_mean | q95 (eingefroren = max) | q95_1000 | q95_10000 | q95 driftfrei | q95 Drift |
|---|---|---|---|---|---|---|---|---|---|
| mom1 | 0.007302 | 0.007441 | 0.051279 | 0.001290 | 0.013947 | 0.013947 | 0.013290 | 0.013770 | 0.013947 |
| mom2 | 0.008090 | 0.008123 | 0.056866 | 0.001679 | 0.015960 | 0.015960 | 0.015176 | 0.015960 | 0.015790 |
| mom4 | 0.009768 | 0.009370 | 0.065995 | 0.002066 | 0.019828 | 0.019828 | 0.018380 | 0.019086 | 0.019828 |
| rev_gap | 0.007429 | 0.007425 | 0.050975 | -0.001196 | 0.010533 | 0.010300 | 0.010533 | 0.010300 | 0.010230 |

- ceiling_k4 W1 (vorzeichenbereinigt, stress, driftfrei): 0.007820
- bounce_sigma_true W1: 0.173542; Survivorship (Schwellen-Einheiten): mom1 -0.425, rev_gap -0.448
- stress_rel: 22 Tage im Fenster (Datumsfilter <= 2026-06-28)
- stress_abs: 2 Tage im Fenster (Datumsfilter <= 2026-06-28)

## Eingefrorene Konstanten W2

| Variante | se_mean | e_se_rule | sd_week | null_mean | q95 (eingefroren = max) | q95_1000 | q95_10000 | q95 driftfrei | q95 Drift |
|---|---|---|---|---|---|---|---|---|---|
| mom1 | 0.006197 | 0.006630 | 0.044494 | 0.000936 | 0.011573 | 0.011426 | 0.011573 | 0.011426 | 0.011339 |
| mom2 | 0.007046 | 0.007084 | 0.048215 | 0.001502 | 0.013498 | 0.013422 | 0.013498 | 0.013277 | 0.013422 |
| mom4 | 0.008190 | 0.007981 | 0.054924 | 0.001953 | 0.016395 | 0.016353 | 0.016395 | 0.015650 | 0.016353 |
| rev_gap | 0.006486 | 0.006629 | 0.044489 | -0.001224 | 0.009239 | 0.008847 | 0.009239 | 0.008790 | 0.008847 |

- ceiling_k4 W2 (vorzeichenbereinigt, stress, driftfrei): 0.006714
- bounce_sigma_true W2: 0.134285; Survivorship (Schwellen-Einheiten): mom1 -0.538, rev_gap -0.522
- stress_rel: 8 Tage im Fenster (Datumsfilter <= 2026-06-28)
- stress_abs: 1 Tage im Fenster (Datumsfilter <= 2026-06-28)

## Replikate fuer p (DEC-99, faktorerhaltende Null)

- Datei `h32_prelaunch_p_replicates.json` sha256 `3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef`; R = 10000 (Konstanten aus den ersten 1000), Seed 53
- p = (1 + #{Replikat-Fenstermittel >= beobachtetes Fenstermittel in Richtung}) / (1 + R); je Fenster und Variante die Zelle mit dem groesseren Null-Mittel; Max-p ueber W1 / W2. Blockpermutation und Normalnaeherung sind report-only.

| Fenster | Variante | Zelle | Null-Mittel der Replikate |
|---|---|---|---|
| W1 | mom1 | drifting | 0.001290 |
| W1 | mom2 | drifting | 0.001679 |
| W1 | mom4 | drifting | 0.002066 |
| W1 | rev_gap | driftfree | -0.001196 |
| W2 | mom1 | drifting | 0.000936 |
| W2 | mom2 | drifting | 0.001502 |
| W2 | mom4 | drifting | 0.001953 |
| W2 | rev_gap | driftfree | -0.001224 |

## Power-Zeile (DEC-101 E5, report-only)

report-only (DEC-101 E5): MDE80 as the maximum over (1b) with credit and (1c); hand-over threshold on x_P = MDE80*_U + m*; proof line 'rule U covers (1c)'; end power after F-WEEK from the replicates of the binding cell (not the normal approximation) at pi = hand-over threshold

| Variante | MDE80 W1 (1b / 1c / W) | MDE80 W2 (1b / 1c / W) | MDE80* | m* | MDE80*_U | Uebergabeschwelle x_P | Marge Regel U gegen (1c) |
|---|---|---|---|---|---|---|---|
| mom1 | 0.019676 / 0.020093 / 0.020093 | 0.017057 / 0.016788 / 0.017057 | 0.020093 | 0.002152 | 0.018385 | 0.020538 | Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c = 0.000445 (>= 0: ja) |
| mom2 | 0.021848 / 0.022769 / 0.022769 | 0.019084 / 0.019428 / 0.019428 | 0.022769 | 0.002857 | 0.020169 | 0.023027 | Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c = 0.000258 (>= 0: ja) |
| mom4 | 0.025699 / 0.028049 / 0.028049 | 0.021974 / 0.023288 / 0.023288 | 0.028049 | 0.003829 | 0.023633 | 0.027462 | Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c = -0.000587 (>= 0: nein) |
| rev_gap | 0.018465 / 0.016785 / 0.018465 | 0.016363 / 0.014698 / 0.016363 | 0.018465 | 0.000000 | 0.018465 | 0.018465 | Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c = 0.001680 (>= 0: ja) |

Endpower nach F-WEEK am Punkt pi = Uebergabeschwelle (Replikat-Quantil der bindenden Zelle; in Klammern die Normalnaeherung, report-only):

| Variante | m = 1 | m = 2 | m = 3 | m = 4 | m = 11 |
|---|---|---|---|---|---|
| mom1 | 0.751 (0.765) | 0.689 (0.689) | 0.548 (0.569) | 0.444 (0.488) | 0.201 (0.256) |
| mom2 | 0.738 (0.771) | 0.661 (0.698) | 0.494 (0.584) | 0.382 (0.506) | 0.124 (0.279) |
| mom4 | 0.714 (0.791) | 0.648 (0.726) | 0.475 (0.621) | 0.349 (0.548) | 0.110 (0.325) |
| rev_gap | 0.703 (0.703) | 0.620 (0.620) | 0.497 (0.497) | 0.417 (0.417) | 0.205 (0.205) |

## W1-Determinismus-Kontrolle gegen v5e

W1-Determinismus-Kontrolle gegen v5e: entfaellt (DEC-100 N1); Ersatz: Fixture-T2, Zweitlauf bitgleich, PP3-Trockenprobe

KEIN VERDIKT -- der Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung.
