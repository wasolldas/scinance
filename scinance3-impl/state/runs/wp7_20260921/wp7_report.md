# WP-7 -- Universums-Zensus: Befund

## B2
Klasse W testbar. A3-Registrierung erlaubt; welches Fenster-Regime gilt, entscheidet die gerechnete Per-Fenster-Power nach der in 5.3 vorab fixierten Zuordnungsregel.

SD_null-Schranke = IC_prior * sqrt(W) / z (DEC-51/52):

- SD_null je Fenster: 0.04112 (Schranke 0.08700, aus IC_prior=0.03 * sqrt(W=52) / z=2.4865)
- SD_null gepoolt: 0.04398 (Schranke 0.09657, aus IC_prior=0.03 * sqrt(W=104) / z=3.168)
- K verfuegbar: 252

## B3
Kein Survivorship-freies Universum aus Bybit-Bordmitteln. Konsequenz vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture eine Verzerrung kleiner als die halbe registrierte Schwelle zeigt; sonst nicht registrierbar. Externes Delisting-Register (Announcement-Scraping) ist keine Welle-1-Aufgabe.

Survivorship-freies Universum aus oeffentlichen Daten (WP-12b, DEC-70): n_delisted_symbols=268, n_with_history=261, Verzerrung IC_union - IC_survivors = 0.0033 [-0.0076; 0.0132] (n_weeks=271, seed=53, n_boot=1000)
Die registrierte Schwelle (PRD 4.1 B3: 'kleiner als die halbe registrierte Schwelle') ist noch NICHT gesetzt -- A3 ist nicht registriert (DEC-67 Entscheidung 1: der A3-Lauf ist bis zum Survivorship-Fixture gesperrt). Diese Messung berichtet ausschliesslich die gemessene Verzerrung (IC_with - IC_without) und ihr Cluster-Bootstrap-CI -- KEIN PASS/FAIL, KEIN VERDIKT.

## B4 (nicht ausgeloest)
kein Befund -- sigma_xs erreicht sigma_xs_min.

## B5
Ergebnis wird als DEC registriert, bevor ein Kandidat davon profitiert (Review R1-R4 3.6). Bis dahin RAISED tradability3.perp (Par. 6). Klarstellung (Review PRD3 W-8): 15 bps ist die Gesamtwand (11 bp Gebuehr + ~4 bp Slippage), nicht eine 'Majors-Slippage-Konstante'; eine Spread-Messung korrigiert die Konstante um hoechstens ~27% und kann sie nie unter 11 bps Taker druecken (Review R1-R4 1-R3-K-35, woertlich). Ein Schwellenwert fuer 'Alt-Spread zu breit' wird deshalb nicht gesetzt - der v1-Faktor 3x war unhergeleitet und ist gestrichen.

- Dezil 1: n=88 PERP_SPREAD_BP median=1.6178
- Dezil 2: n=89 PERP_SPREAD_BP median=5.322
- Dezil 3: n=88 PERP_SPREAD_BP median=7.3855
- Dezil 4: n=89 PERP_SPREAD_BP median=9.2773
- Dezil 5: n=89 PERP_SPREAD_BP median=9.8678
- Dezil 6: n=88 PERP_SPREAD_BP median=10.1424
- Dezil 7: n=89 PERP_SPREAD_BP median=13.3879
- Dezil 8: n=88 PERP_SPREAD_BP median=14.9539
- Dezil 9: n=89 PERP_SPREAD_BP median=19.5312
- Dezil 10: n=89 PERP_SPREAD_BP median=36.21

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)
- Wert: nan (n_symbols_balanced=0)

## rho(BTC,ETH), 30-Minuten-Renditen
- Pearson: 0.8149 [0.7996, 0.8296] (seed=53)
- Spearman: 0.7972 [0.7886, 0.8064]
- n_aligned_buckets: 32591

## Hinweis: NICHT urteilstragend
nicht urteilstragend (--allow-partial) -- PARTIAL/FAILED-Partitionen unter --allow-partial akzeptiert; dieser Report ersetzt keinen vollstaendigen Lauf.

## K je Kalenderwoche
- min=5 median=252.0000 max=719 (n_weeks=299)
- erste/letzte Woche mit Mitgliedern: 2021-02-22 .. 2026-09-14

Sensitivitaet MIN_WEEKS_HISTORY (4/12 Wochen, nur berichtet, kein Urteil):
- min_weeks_4: min=5 median=259.0000 max=806
- min_weeks_12: min=5 median=241.0000 max=652

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) -- volle Historie
- Wert: n/a (n_symbols_balanced=0)

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) (STRESS_ABS-Wochen)
- Wert: n/a (n_symbols_balanced=0, n_stress_wochen=18)

## DEC-59: Totzonen-/Bindungs-Zensus (deskriptiv, kein Urteil)
- Anteil Symbol-Tage exakt bei I: 0.5039 (329147/653261)
- Intervallklassen (funding_n-abgeleitet):
  - 120min: 6723
  - 240min: 196427
  - 480min: 431173
  - 60min: 16532
  - funding_n=1 (unklassifiziert): 101
  - funding_n=10 (unklassifiziert): 45
  - funding_n=11 (unklassifiziert): 16
  - funding_n=13 (unklassifiziert): 12
  - funding_n=14 (unklassifiziert): 16
  - funding_n=15 (unklassifiziert): 41
  - funding_n=16 (unklassifiziert): 6
  - funding_n=17 (unklassifiziert): 33
  - funding_n=18 (unklassifiziert): 52
  - funding_n=19 (unklassifiziert): 20
  - funding_n=2 (unklassifiziert): 1001
  - funding_n=20 (unklassifiziert): 27
  - funding_n=21 (unklassifiziert): 31
  - funding_n=22 (unklassifiziert): 11
  - funding_n=23 (unklassifiziert): 8
  - funding_n=4 (unklassifiziert): 631
  - funding_n=5 (unklassifiziert): 225
  - funding_n=7 (unklassifiziert): 33
  - funding_n=8 (unklassifiziert): 57
  - funding_n=9 (unklassifiziert): 40
- je Dezil (Wochen-SUMME-Sortierschluessel, DEC-59):
  - Dezil 1: Totzonen-Anteil=0.4733 (n_symbol_wochen=9318)
  - Dezil 2: Totzonen-Anteil=0.7867 (n_symbol_wochen=9471)
  - Dezil 3: Totzonen-Anteil=0.8432 (n_symbol_wochen=9429)
  - Dezil 4: Totzonen-Anteil=0.7178 (n_symbol_wochen=9473)
  - Dezil 5: Totzonen-Anteil=0.5733 (n_symbol_wochen=9482)
  - Dezil 6: Totzonen-Anteil=0.4527 (n_symbol_wochen=9408)
  - Dezil 7: Totzonen-Anteil=0.3768 (n_symbol_wochen=9432)
  - Dezil 8: Totzonen-Anteil=0.3238 (n_symbol_wochen=9470)
  - Dezil 9: Totzonen-Anteil=0.2904 (n_symbol_wochen=9430)
  - Dezil 10: Totzonen-Anteil=0.1964 (n_symbol_wochen=9587)

## Funding-Autokorrelation (Wochen-SUMME, Median ueber Symbole, deskriptiv)
- lag1: 0.4334
- lag2: 0.2628
- lag3: 0.1874
- lag4: 0.1605
(n_symbols_used=1080 von 1138)

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil) -- urteilstragende Fenster (DEC-67 Korrektur)
- letzte 52 Wochen (2025-09-22..2026-09-14): Wert=182.2800 (n_symbols_balanced=423, n_wochen_im_fenster=52)
- letzte 104 Wochen (2024-09-23..2026-09-14): Wert=97.1095 (n_symbols_balanced=260, n_wochen_im_fenster=104)
- STRESS_ABS (auf letzte 104 Wochen begrenzt): Wert=2.1550 (n_symbols_balanced=308, n_stress_wochen=3)

## A1-Schluessel Permutations-Null (deskriptiv, KEIN echter IC, Feasibility-Zeile)
Deskriptiv, kein Verdikt -- die reale IC des A1-Schluessels wird hier NICHT berechnet oder berichtet (DEC-67 E6, gesperrt bis A1-Registrierung).
- SD_null je Fenster (W=52): 0.04112 (Schranke 0.08700, W_eff-adjustiert=0.06422)
- SD_null gepoolt (W=104): 0.04398 (Schranke 0.09657, W_eff-adjustiert=0.06868)
- W_eff-Faktor: 0.41 (DEC-67 E4)
- feasible je Fenster=True, feasible gepoolt=True

## Dezil-Degeneration des A1-Schluessels (DEC-67 E3, deskriptiv, kein Urteil)
- letzte 52 Wochen (2025-09-22..2026-09-14), Median-Woche 2026-03-16: Klumpen=0.1360 neg=0.7413 pos=0.1227 D1-degeneriert=False D10-degeneriert=False (n_wochen_degeneriert D1=0/D10=14 von 52)
- vorherige 52 Wochen (2024-09-23..2025-09-15), Median-Woche 2025-03-17: Klumpen=0.1572 neg=0.8260 pos=0.0168 D1-degeneriert=False D10-degeneriert=True (n_wochen_degeneriert D1=4/D10=27 von 52)

## Intervallklassen-Wechsel je Symbol (deskriptiv, kein Urteil)
- Verteilung Wechsel je Symbol (n=1138): {'0': 754, '1': 199, '2-5': 170, '>5': 15}
- Symbol-Tage je Klasse:
  - 120min: 6723
  - 240min: 196427
  - 480min: 431173
  - 60min: 16532

## WP-12b/DEC-70: Survivorship-freies Universum (--include-delisted)
- n_delisted_symbols_register=268, n_with_history=261, n_no_history_only=7
- delisting_dates.json sha256=852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
- Union-Range-Fingerprint sha256=a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a (n_partitions=6507)

## DEC-58(g): Delisting-Hazard "Beifahrer" je Listing-Jahrgang (deskriptiv, kein Modell)
| Jahrgang | gelistet | delistet |
|---|---|---|
| 2020 | 5 | 0 |
| 2021 | 91 | 18 |
| 2022 | 86 | 30 |
| 2023 | 113 | 55 |
| 2024 | 228 | 105 |
| 2025 | 255 | 51 |
| 2026 | 358 | 9 |

## PERP_SPREAD_BP -- Quelle
- REST-Fallback (bybit_rest.fetch_tickers, ein Call; Inhaltsprobe fehlgeschlagen)

## Kostenkonstante (B4)
- Taker-Round-Trip-Wand (PRD B.1: 11 bp): 11.00 bp (Quelle: bybit_edge.config.FEE_TAKER (0.055%/Bein) * 2)

## DEC-53-Artefakte
- weekly_ic_series_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\weekly_ic_series.csv (sha256=b8b38cf7723e6eb344ff9f886cec50344b816586fcdbe0161481f0da57d53f51)
- null_ic_per_window: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\null_ic_per_window_w52.json (sha256=3f8fe7e7a89a3221734fc9001ac76856a1193d16a93dec4f9e09ef106deede62)
- null_ic_pooled: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\null_ic_pooled_w104.json (sha256=9266c1219ea3a33bc5716e033e87bab856b8fae9f111abfe31bf83049484ae08)
- weekly_sigma_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\weekly_sigma_xs_sigma_ls.csv (sha256=280e8503e1efe40b98fd66856734581061db6f80fc0da00b3c8ea32da0ca2407)
- deadzone_by_decile_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\deadzone_by_decile.csv (sha256=9fd89840d951ad7c15570e317488e6a35976ec1a62654aa6a19330a6eef7a945)
- spread_census_json: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\spread_census.json (sha256=fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083)
- a1_key_null_per_window: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\null_ic_funding_excess_key_per_window_w52.json (sha256=3f8fe7e7a89a3221734fc9001ac76856a1193d16a93dec4f9e09ef106deede62)
- a1_key_null_pooled: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\null_ic_funding_excess_key_pooled_w104.json (sha256=9266c1219ea3a33bc5716e033e87bab856b8fae9f111abfe31bf83049484ae08)
- decile_degeneration_weekly_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\decile_degeneration_weekly.csv (sha256=7c6119afe3bbaa862acd5f65bfcb3e53ffb8244e7056aba7f5a56df3a0fac9e5)
- pair_corr_btc_eth: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\pair_corr_BTCUSDT_ETHUSDT.json (sha256=ea38b041c5181a1dee8c3684992b94c5ae768b8aafde3db5d5af6a62d6f1402a)
- survivorship_bias_union: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260921\survivorship_bias_UNION_REAL.json (sha256=4fb81859040d9cb1c581aa8e23ac9ca942ef5d77bf2c4c8f4aa79e607d00c90d)

## Range-Fingerprint (panel_1d)
- sha256=a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a (n_partitions=6507, Jahre=[2021, 2026])

