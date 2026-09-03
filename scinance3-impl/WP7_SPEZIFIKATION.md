# WP-7 - Universums-Zensus (Klasse-W-Feasibility): Spezifikation

> Orchestrator 2026-09-02. Massgeblicher Volltext: PRD 3.0 Abschnitt 4.1
> (Entwurf v2, wird als `scinance3-impl/PRD_SCINANCE3.md` committet). Diese
> Datei ist die Bauanleitung; bei Widerspruch gilt das PRD.

## 1. Was gemessen wird (kein Alpha-Gate, binaerer Befund)
Auf einem point-in-time-Universum aller Bybit-USDT-Perps (inkl. delisteter)
mit Tages-Klines:
- **K** je Kalenderwoche (Symbole mit >= 8 Wochen Bars UND noch handelnd;
  8 Wochen = Design-Parameter, Sensitivitaet 4/12 nur berichten),
- **SD_null(IC_t)**: je Woche 1.000 Permutationen eines Querschnittssignals
  ueber die Symbole von U_t, Spearman-IC gegen die Folgewochenrendite,
  SD der Nullverteilung, gemittelt ueber die Wochen je Fenster; Seed und
  die Wochen-Serie der Nullverteilung sind Pflicht-Artefakte (DEC-53),
- deskriptiv **N_eff** = (sum lambda)^2 / sum lambda^2 der Residual-
  Kovarianz nach Querschnitts-Demeaning (kein Urteil),
- **sigma_xs** (wochenweise Querschnitts-SD der Renditen, Median/Quartile),
- **sigma_LS** (Wochen-SD einer Dezil-Long/Short-Rendite auf einem
  ZUFAELLIGEN Sortierschluessel, Nuisance fuer A1),
- **rho(BTC,ETH)** auf 30-Minuten-Renditen aus dem WP-0-Bar-Cache,
- **PERP_SPREAD_BP je Symbol-Dezil** (Umsatzdezile) - ZUERST Inhaltsprobe
  auf `data/harvest/raw/bybit/tickers` (Felder bid1Price/ask1Price/
  openInterest/fundingRate vorhanden? loud), sonst ein REST-Tickers-Call,
- **funding_n** je Symbol-Tag (1h- vs 8h-Symbole) als Pflichtspalte.

Feasibility (rein statistisch, C.2): per Fenster W=52: 2,4865*SD_null/sqrt(52)
<= 0,03; gepoolt W=104: 3,1680*SD_null/sqrt(104) <= 0,03. Befunde B1..B5 und
Konsequenzen exakt wie PRD 4.1 (B1 Klasse W nicht testbar; B2 testbar; B3
Survivorship nicht herstellbar; B4 nur Etikett `unter_wand`; B5 Spread als DEC).

## 2. Daten (oeffentlich, keyfrei, Nutzer-Maschine)
- `GET /v5/market/instruments-info?category=linear` mit Cursor-Paginierung,
  ALLE status-Werte (Trading, Settling, Closed ...) [sek]; loud fail, wenn
  keine Nicht-Trading-Zeilen kommen (Befund B3).
- `GET /v5/market/kline?category=linear&symbol=..&interval=D&limit=1000`,
  rueckwaerts paginieren ueber `end`; Drossel 5 Req/s; Rohantworten
  SHA-256; NIE unter data/harvest schreiben. Ziel: `data/panel_1d/
  source=bybit/category=linear/symbol=<S>/year=<YYYY>/part.parquet`
  (Jahrespartitionen), `data/panel_1d/panel_manifest.sqlite` mit
  status in {DONE, PARTIAL, EMPTY, FAILED}, DONE nur bei n_rows ==
  erwartete Tage; `frozen/`-Semantik: abgeschlossene Jahre unveraenderlich,
  laufendes Jahr `open/` mit Laufzeit-Fingerprint.
- Fingerprints: je (symbol, year) SHA-256 ueber kanonische Wertbytes;
  Bereichs-Fingerprint ueber (Symbolmenge, Jahresbereich) im Report.
- Provenienz: `--reverify` zieht 1 % zufaellige eingefrorene Partitionen
  neu und vergleicht Fingerprints (Alarm bei Abweichung).

## 3. Deliverables
- `src/bybit_edge/research/wp7_universe/`: `bybit_rest.py` (instruments,
  klines, Paginierung, Drossel, Rohantwort-Hash; keine Netzannahmen im
  Test), `panel_store.py` (Jahrespartitionen, Manifest, Fingerprints,
  frozen/open), `pit_universe.py` (point-in-time-Universum, Delisting-
  Behandlung: Symbol bleibt bis zum letzten Bar, Schluss zum letzten Kurs),
  `null_ic.py` (Permutations-Rauschboden, Seeds, Artefakte), `stats.py`
  (N_eff Partizipationszahl, sigma_xs, sigma_LS, Feasibility-Rechnung mit
  DEC-51/52-z), `spread_probe.py` (Tickers-Inhaltsprobe + Dezil-Spread),
  `report.py` (Befund B1..B5 mit vorab fixierter Konsequenz, JSON+MD).
- `scripts/wp7_universe_census.py` mit `--probe-tickers`, `--fetch`,
  `--census`, `--reverify`.
- `scinance3-impl/handoff_local/run_wp7_universe.ps1` (PS 5.1, ASCII).
- Tests `tests/unit/test_wp7_universe.py`, DEC-39-Trio PFLICHT:
  POSITIV (injizierter IC 0,04 bei realer Korrelationsstruktur wird im CI
  wiedergefunden, SD_null erlaubt Detektion), NULL (unabhaengige Reihen mit
  lognormaler Vol-Heterogenitaet sigma_log 0,6: SD_null ~ 1/sqrt(K-1),
  N_eff ~ K - der Test, an dem der v1-Schaetzer scheiterte), ADVERSARIAL
  (Survivorship: 30 % der Symbole nach Drawdown-Trigger geloescht; der
  unkontrollierte Schaetzer zeigt Schein-Momentum, der kontrollierte nicht;
  sonst "methodisch invalide"). Dazu: Determinismus (2 Laeufe, identische
  Fingerprints und identische SD_null bei gleichem Seed), Manifest-Loud-
  Fail bei n_rows-Abweichung, Paginierung gegen Fixture-Antworten,
  DEC-53-Artefakte vorhanden.

## 4. Nicht-Ziele
Kein 1h-Panel, kein Alpha-Gate, keine Kandidaten-Registrierung, keine
Aenderung an bestehenden Stores.

## Nachtrag 2026-09-03 (DEC-58): drei Pflichtzeilen aus dem Wissenschafts-Exkurs
1. **Totzonen-/Bindungs-Zensus:** Anteil der Symbol-Intervalle mit Funding-Rate
   exakt = I (0,01 %/8h bzw. intervall-normiert) je Woche und Dezil; bei
   breiter Bindung ist die Dezil-Sortierung degeneriert (A1-Feasibility).
2. **Intervallklasse je Symbol-Woche** (aus `funding_n`) und Zaehlung der
   Wechsel je Tag/Dezil/Fenster; Materialitaetsgrenze vorab im Report.
3. **Delisting-Hazard/IPCW** (deskriptiv, wenn < 32 Delisting-Chargen):
   Zahl statt Haekchen fuer die Survivorship-Verzerrung.
