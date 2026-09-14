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

- Dezil 1: n=87 PERP_SPREAD_BP median=1.5834
- Dezil 2: n=87 PERP_SPREAD_BP median=4.2221
- Dezil 3: n=88 PERP_SPREAD_BP median=6.2707
- Dezil 4: n=87 PERP_SPREAD_BP median=8.707
- Dezil 5: n=88 PERP_SPREAD_BP median=8.1521
- Dezil 6: n=87 PERP_SPREAD_BP median=11.5781
- Dezil 7: n=87 PERP_SPREAD_BP median=10.4207
- Dezil 8: n=88 PERP_SPREAD_BP median=13.2524
- Dezil 9: n=87 PERP_SPREAD_BP median=13.018
- Dezil 10: n=88 PERP_SPREAD_BP median=30.6245

## N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)
- Wert: nan (n_symbols_balanced=0)

## rho(BTC,ETH), 30-Minuten-Renditen
- Pearson: 0.8148 [0.7996, 0.8282] (seed=53)
- Spearman: 0.7971 [0.7882, 0.8056]
- n_aligned_buckets: 32927

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
- Anteil Symbol-Tage exakt bei I: 0.4667 (236541/506863)
- Intervallklassen (funding_n-abgeleitet):
  - 240min: 163679
  - 480min: 320377
  - 60min: 14620
  - funding_n=1 (unklassifiziert): 70
  - funding_n=10 (unklassifiziert): 39
  - funding_n=11 (unklassifiziert): 13
  - funding_n=12 (unklassifiziert): 6129
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
  - Dezil 1: Totzonen-Anteil=0.4845 (n_symbol_wochen=7210)
  - Dezil 2: Totzonen-Anteil=0.7852 (n_symbol_wochen=7352)
  - Dezil 3: Totzonen-Anteil=0.8057 (n_symbol_wochen=7317)
  - Dezil 4: Totzonen-Anteil=0.6535 (n_symbol_wochen=7358)
  - Dezil 5: Totzonen-Anteil=0.5017 (n_symbol_wochen=7376)
  - Dezil 6: Totzonen-Anteil=0.3974 (n_symbol_wochen=7294)
  - Dezil 7: Totzonen-Anteil=0.3325 (n_symbol_wochen=7321)
  - Dezil 8: Totzonen-Anteil=0.2826 (n_symbol_wochen=7354)
  - Dezil 9: Totzonen-Anteil=0.2535 (n_symbol_wochen=7315)
  - Dezil 10: Totzonen-Anteil=0.1705 (n_symbol_wochen=7477)

## Funding-Autokorrelation (Wochen-SUMME, Median ueber Symbole, deskriptiv)
- lag1: 0.4209
- lag2: 0.2445
- lag3: 0.1751
- lag4: 0.1517
(n_symbols_used=820 von 878)

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
- weekly_ic_series_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\weekly_ic_series.csv (sha256=780f3b7f5863c7b7b1b2503895653622db596799fa3618a3c17971a1205cdcfb)
- null_ic_per_window: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\null_ic_per_window_w52.json (sha256=d2baf523bfaa04b106a0eeeba2e99138b46fd206f83aeb1c454e0d2ddaf5b637)
- null_ic_pooled: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\null_ic_pooled_w104.json (sha256=7b1b701e593b734517a55df51240f44f3f1ce28ab9dabd124004993d27b781d6)
- weekly_sigma_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\weekly_sigma_xs_sigma_ls.csv (sha256=5766624541e5eda42801f8f6cec7bbc01ee8e670d7fa578b05ad35a19fbc300f)
- deadzone_by_decile_csv: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\deadzone_by_decile.csv (sha256=7b8c4041d0a6877168dc4cc6025ea4e2a244fa4ae3b1d87356b286a82f272e48)
- spread_census_json: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\spread_census.json (sha256=30a4b82bbc83fbd99f8613583a5d6add8ea4615844a09b65df7b065421b21a47)
- pair_corr_btc_eth: E:\Claude\Projects\scinance\scinance3-impl\state\wp7_20260914\pair_corr_BTCUSDT_ETHUSDT.json (sha256=dc9f2c05b62a54e9aedb861a2dd9f157328012b46706790c9292ce891efdd734)

## Range-Fingerprint (panel_1d)
- sha256=6d4c325275f80f7dd4ac4ad9611500a24e22f7a56f0f5f59c32b1f7f50cc25fc (n_partitions=5268, Jahre=[2021, 2026])

