# WP-7 -- Universums-Zensus: Befund

## B2
Klasse W testbar. A3-Registrierung erlaubt; welches Fenster-Regime gilt, entscheidet die gerechnete Per-Fenster-Power nach der in 5.3 vorab fixierten Zuordnungsregel.

SD_null-Schranke = IC_prior * sqrt(W) / z (DEC-51/52):

- SD_null je Fenster: 0.04349 (Schranke 0.08700, aus IC_prior=0.03 * sqrt(W=52) / z=2.4865)
- SD_null gepoolt: 0.04950 (Schranke 0.09657, aus IC_prior=0.03 * sqrt(W=104) / z=3.168)
- K verfuegbar: 171

## B3
Kein Survivorship-freies Universum aus Bybit-Bordmitteln. Konsequenz vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture eine Verzerrung kleiner als die halbe registrierte Schwelle zeigt; sonst nicht registrierbar. Externes Delisting-Register (Announcement-Scraping) ist keine Welle-1-Aufgabe.

## B4 (nicht ausgeloest)
kein Befund -- sigma_xs erreicht sigma_xs_min.

## B5
Ergebnis wird als DEC registriert, bevor ein Kandidat davon profitiert (Review R1-R4 3.6). Bis dahin RAISED tradability3.perp (Par. 6). Klarstellung (Review PRD3 W-8): 15 bps ist die Gesamtwand (11 bp Gebuehr + ~4 bp Slippage), nicht eine 'Majors-Slippage-Konstante'; eine Spread-Messung korrigiert die Konstante um hoechstens ~27% und kann sie nie unter 11 bps Taker druecken (Review R1-R4 1-R3-K-35, woertlich). Ein Schwellenwert fuer 'Alt-Spread zu breit' wird deshalb nicht gesetzt - der v1-Faktor 3x war unhergeleitet und ist gestrichen.

- Dezil 1: n=87 PERP_SPREAD_BP median=1.87
- Dezil 2: n=88 PERP_SPREAD_BP median=4.5594
- Dezil 3: n=88 PERP_SPREAD_BP median=7.908
- Dezil 4: n=87 PERP_SPREAD_BP median=10.2908
- Dezil 5: n=88 PERP_SPREAD_BP median=10.5121
- Dezil 6: n=88 PERP_SPREAD_BP median=11.159
- Dezil 7: n=87 PERP_SPREAD_BP median=12.6783
- Dezil 8: n=88 PERP_SPREAD_BP median=15.3638
- Dezil 9: n=88 PERP_SPREAD_BP median=16.5027
- Dezil 10: n=88 PERP_SPREAD_BP median=29.782

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)
- Wert: nan (n_symbols_balanced=0)

## rho(BTC,ETH), 30-Minuten-Renditen
- Pearson: 0.8148 [0.8008, 0.8290] (seed=53)
- Spearman: 0.7970 [0.7882, 0.8055]
- n_aligned_buckets: 32831

## Hinweis: NICHT urteilstragend
nicht urteilstragend (--allow-partial) -- PARTIAL/FAILED-Partitionen unter --allow-partial akzeptiert; dieser Report ersetzt keinen vollstaendigen Lauf.

## K je Kalenderwoche
- min=5 median=171.0000 max=719 (n_weeks=299)
- erste/letzte Woche mit Mitgliedern: 2021-02-22 .. 2026-09-14

Sensitivitaet MIN_WEEKS_HISTORY (4/12 Wochen, nur berichtet, kein Urteil):
- min_weeks_4: min=5 median=175.0000 max=806
- min_weeks_12: min=5 median=168.0000 max=652

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) -- volle Historie
- Wert: n/a (n_symbols_balanced=0)

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) (STRESS_ABS-Wochen)
- Wert: n/a (n_symbols_balanced=0, n_stress_wochen=18)

## DEC-59: Totzonen-/Bindungs-Zensus (deskriptiv, kein Urteil)
- Anteil Symbol-Tage exakt bei I: 0.4727 (239586/506863)
- Intervallklassen (funding_n-abgeleitet):
  - 120min: 6129
  - 240min: 163679
  - 480min: 320377
  - 60min: 14620
  - funding_n=1 (unklassifiziert): 70
  - funding_n=10 (unklassifiziert): 39
  - funding_n=11 (unklassifiziert): 13
  - funding_n=13 (unklassifiziert): 12
  - funding_n=14 (unklassifiziert): 14
  - funding_n=15 (unklassifiziert): 38
  - funding_n=16 (unklassifiziert): 5
  - funding_n=17 (unklassifiziert): 29
  - funding_n=18 (unklassifiziert): 46
  - funding_n=19 (unklassifiziert): 17
  - funding_n=2 (unklassifiziert): 837
  - funding_n=20 (unklassifiziert): 27
  - funding_n=21 (unklassifiziert): 26
  - funding_n=22 (unklassifiziert): 10
  - funding_n=23 (unklassifiziert): 7
  - funding_n=4 (unklassifiziert): 579
  - funding_n=5 (unklassifiziert): 167
  - funding_n=7 (unklassifiziert): 30
  - funding_n=8 (unklassifiziert): 56
  - funding_n=9 (unklassifiziert): 36
- je Dezil (Wochen-SUMME-Sortierschluessel, DEC-59):
  - Dezil 1: Totzonen-Anteil=0.5004 (n_symbol_wochen=7210)
  - Dezil 2: Totzonen-Anteil=0.7970 (n_symbol_wochen=7352)
  - Dezil 3: Totzonen-Anteil=0.8126 (n_symbol_wochen=7317)
  - Dezil 4: Totzonen-Anteil=0.6606 (n_symbol_wochen=7358)
  - Dezil 5: Totzonen-Anteil=0.5052 (n_symbol_wochen=7376)
  - Dezil 6: Totzonen-Anteil=0.3995 (n_symbol_wochen=7294)
  - Dezil 7: Totzonen-Anteil=0.3347 (n_symbol_wochen=7321)
  - Dezil 8: Totzonen-Anteil=0.2855 (n_symbol_wochen=7354)
  - Dezil 9: Totzonen-Anteil=0.2575 (n_symbol_wochen=7315)
  - Dezil 10: Totzonen-Anteil=0.1742 (n_symbol_wochen=7477)

## Funding-Autokorrelation (Wochen-SUMME, Median ueber Symbole, deskriptiv)
- lag1: 0.4209
- lag2: 0.2445
- lag3: 0.1751
- lag4: 0.1517
(n_symbols_used=820 von 878)

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) -- urteilstragende Fenster (DEC-67 Korrektur)
- letzte 52 Wochen (2025-09-22..2026-09-14): Wert=178.7811 (n_symbols_balanced=423, n_wochen_im_fenster=52)
- letzte 104 Wochen (2024-09-23..2026-09-14): Wert=101.2302 (n_symbols_balanced=260, n_wochen_im_fenster=104)
- STRESS_ABS (auf letzte 104 Wochen begrenzt): Wert=2.4364 (n_symbols_balanced=305, n_stress_wochen=3)

## A1-Schluessel Permutations-Null (deskriptiv, KEIN echter IC, Feasibility-Zeile)
Deskriptiv, kein Verdikt -- die reale IC des A1-Schluessels wird hier NICHT berechnet oder berichtet (DEC-67 E6, gesperrt bis A1-Registrierung).
- SD_null je Fenster (W=52): 0.04349 (Schranke 0.08700, W_eff-adjustiert=0.06792)
- SD_null gepoolt (W=104): 0.04950 (Schranke 0.09657, W_eff-adjustiert=0.07731)
- W_eff-Faktor: 0.41 (DEC-67 E4)
- feasible je Fenster=True, feasible gepoolt=True

## Dezil-Degeneration des A1-Schluessels (DEC-67 E3, deskriptiv, kein Urteil)
- letzte 52 Wochen (2025-09-22..2026-09-14), Median-Woche 2026-03-16: Klumpen=0.1245 neg=0.7621 pos=0.1134 D1-degeneriert=False D10-degeneriert=False (n_wochen_degeneriert D1=0/D10=21 von 52)
- vorherige 52 Wochen (2024-09-23..2025-09-15), Median-Woche 2025-03-17: Klumpen=0.1223 neg=0.8716 pos=0.0061 D1-degeneriert=False D10-degeneriert=True (n_wochen_degeneriert D1=4/D10=36 von 52)

## Intervallklassen-Wechsel je Symbol (deskriptiv, kein Urteil)
- Verteilung Wechsel je Symbol (n=878): {'0': 580, '1': 140, '2-5': 143, '>5': 15}
- Symbol-Tage je Klasse:
  - 120min: 6129
  - 240min: 163679
  - 480min: 320377
  - 60min: 14620

## DEC-58(g): Delisting-Hazard "Beifahrer" je Listing-Jahrgang (deskriptiv, kein Modell)
| Jahrgang | gelistet | delistet |
|---|---|---|
| 2020 | 5 | 0 |
| 2021 | 73 | 0 |
| 2022 | 56 | 0 |
| 2023 | 58 | 0 |
| 2024 | 123 | 0 |
| 2025 | 204 | 0 |
| 2026 | 357 | 8 |

## PERP_SPREAD_BP -- Quelle
- REST-Fallback (bybit_rest.fetch_tickers, ein Call; Inhaltsprobe fehlgeschlagen)

## Kostenkonstante (B4)
- Taker-Round-Trip-Wand (PRD B.1: 11 bp): 11.00 bp (Quelle: bybit_edge.config.FEE_TAKER (0.055%/Bein) * 2)

## DEC-53-Artefakte
- weekly_ic_series_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\weekly_ic_series.csv (sha256=780f3b7f5863c7b7b1b2503895653622db596799fa3618a3c17971a1205cdcfb)
- null_ic_per_window: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\null_ic_per_window_w52.json (sha256=d2baf523bfaa04b106a0eeeba2e99138b46fd206f83aeb1c454e0d2ddaf5b637)
- null_ic_pooled: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\null_ic_pooled_w104.json (sha256=7b1b701e593b734517a55df51240f44f3f1ce28ab9dabd124004993d27b781d6)
- weekly_sigma_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\weekly_sigma_xs_sigma_ls.csv (sha256=5766624541e5eda42801f8f6cec7bbc01ee8e670d7fa578b05ad35a19fbc300f)
- deadzone_by_decile_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\deadzone_by_decile.csv (sha256=158ef851747bfe1a5d3d0c498cdce225aea01ede78d975a26421b282846ad703)
- spread_census_json: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\spread_census.json (sha256=2fbb6e14b9c9e831eaf3d85ccc337c25739be2d3203913409d31d4e47e4ae3c3)
- a1_key_null_per_window: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\null_ic_funding_excess_key_per_window_w52.json (sha256=d2baf523bfaa04b106a0eeeba2e99138b46fd206f83aeb1c454e0d2ddaf5b637)
- a1_key_null_pooled: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\null_ic_funding_excess_key_pooled_w104.json (sha256=7b1b701e593b734517a55df51240f44f3f1ce28ab9dabd124004993d27b781d6)
- decile_degeneration_weekly_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\decile_degeneration_weekly.csv (sha256=558a8e453868f35265c1c796ef11f53e72773d627d2a5f19fb25e7ee3c592312)
- pair_corr_btc_eth: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260916\pair_corr_BTCUSDT_ETHUSDT.json (sha256=3c50cbf0ce4d37c7f16afa94a1b59397048c981de347a0790156fd462d561d0d)

## Range-Fingerprint (panel_1d)
- sha256=6d4c325275f80f7dd4ac4ad9611500a24e22f7a56f0f5f59c32b1f7f50cc25fc (n_partitions=5268, Jahre=[2021, 2026])

