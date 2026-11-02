# Herleitungs-Auftrag A2-Vorarbeit: Placebo-Design bei taeglichen Verfaellen und sigma30-Nuisance der Vorperiode (optionsneutral, kein Verdikt)

Du bist der Herleitungs-Agent (Gate-Design, Nuisance, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert, nicht du. Repo `/home/user/scinance`, `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte NUR unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a2_vorarbeit/` (anlegen); Volltexte
unter `scinance3-impl/state/herleitung_a2/` (anlegen). Kurzfassung hoechstens 12 Zeilen. Nichts committen, nichts pushen.
Keine Zugangsdaten/Hostnamen/Modellnamen. Doku Deutsch (ASCII-safe), Code Englisch.

## Ausgangslage (bindend, lesen)
1. `scinance3-impl/CLAUDE.md`; `scinance3-impl/PRD_SCINANCE3.md` Abschnitt **5.2 A2 - EXP-CLOCK** (Hypothese, r_pre =
   log-Rendite [07:30, 08:00) UTC, Placebos P1/P2/P3, Cluster = Verfallsereignis ueber BTC+ETH, Varianten (a) woechentlich /
   (b) monatlich, Vol-Kette 36 bp BTC, rho 0,8 Arbeitswert, V-5-Vorfragen); `state/PROGRAMM_BILANZ_2026-10-18.md` 2.4
   (Formel SE(Delta), N je Fenster, Siegel-Hinweis W2-Ende 2026-06-30); `state/decisions.md` DEC-94 (P-1), DEC-96 E3,
   DEC-98 (+N4, **N5** = A2-Ereigniszensus: jeder Kalendertag seit 2020-03-25 Verfallstag, Zeitlage 08:00:00 UTC,
   Ereigniszahlen), DEC-67 E4 (rho 0,815 Praemie), DEC-58 E4; `state/herleitung_hfrv/A2_EREIGNISZENSUS.md` + `a2_census.json`
   (Kalender, Klassen, Placebo-Kalender); `state/RECHERCHE_BELEGE_2026-10-18.md` Frage 3 (V-5a/b/c) und
   `state/BELEGE_AUS_PDF_2026-10-20.md` Abschnitt 6 (Deribit-Settlement: TWAP 07:30-08:00 UTC, 4-s-Takt) und 8.3/8.4.
2. Vorbild fuer Nuisance-Disziplin: `state/herleitung_hfrv/NUISANCE_HFRV.md` (Waechter "kein Mittel", Etiketten) und
   `scratchpad/h27_herleitung/h27_common.py` (`no_mean`, `truncate_prices`).
3. `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/Zuordnungszahl; `variance_factor`,
   `stationary_bootstrap_se`, `assign_regime`, `assign_regime_a3_practice`, `mde80`).

## Daten (lokal, bereits extrahiert; NICHT den Harvest-Client benutzen, nichts nachladen, nichts listen)
`D = /tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/`
- `D/bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet`, `D/bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet`:
  1-min-Kerzen (symbol, start_ms UTC-ms Kerzenbeginn, open, high, low, close, volume, turnover, ...), 1.440 je UTC-Tag.
  **Vor jeder Rechnung per assert: kein Tag nach 2024-05-31.**
- `D/deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet`: NUR Kalender (column_symbol BTC/ETH, instrument_name,
  type delivery|settlement, timestamp_ms) - keine Preise.
- Rohpartitionen des Stroms `deribit/rest.settlements` liegen im Cache
  `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hcache/raw/deribit/rest.settlements/`
  (Layout `symbol=<BTC|ETH>/date=<YYYY-MM-DD>/<hash>.parquet`, Kestrel-Spalten, `payload_json` mit `type`, `instrument_name`,
  `timestamp`, `position`, `index_price`, `mark_price`, `profit_loss`). Du darfst daraus **ausschliesslich** `type`,
  `instrument_name`, `timestamp` und `position` (= gelieferte Kontrakte/Open Interest am Verfall, KEIN Preis) lesen, nur fuer
  Tage **<= 2026-06-30**, und die Preisfelder nie in den Speicher nehmen (Spalten-/Feldfilter beim Parsen; Waechter im
  Skript, der bei Zugriff auf `index_price`/`mark_price`/`profit_loss` raised). Zweck: Ereignisgroesse (OI je Verfallstag
  und Klasse) fuer das Design - nur Zaehlungen/Summen von Kontrakten.
- `D/deribit_rest_deliveryPrices_DATES_2016-03-18_2026-10-20.parquet`: nur Daten.

## Harte Regeln
1. **Kein Mittel von r_pre, r_post oder irgendeiner Verfallstag-Rendite** (das ist der Effekt der Hypothese) - weder je
   Klasse noch gepoolt noch als Differenz Ereignis minus Placebo; kein Vorzeichen. Erlaubt: Streuung (SD), Quantile des
   Betrags nur als Streuungsmass, Autokorrelation, Korrelation BTC/ETH, Varianzfaktor c, Kurtosis, Placebo-SE als
   Streuungsgroesse. Waechter `no_mean` auf JEDES Ausgabe-Dict; Etikett in jeder Datei. Pruefe deine Ausgaben vor dem
   Schreiben auf verbotene Schluessel (mean/avg/sign/effect/delta/r_pre_mean ...).
2. **Nur Vorperiode <= 2024-05-31** fuer jede Renditegroesse (BTC/ETH-Vol-Statistik: DEC-96 E3 und die H-27-Grenze).
   Kalender- und OI-Groessen bis 2026-06-30.
3. NIE Siegeldateien oeffnen (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`,
   WP-10(A2)-/WP-10(A)-IV-RV-Dateien, `state/runs/wp10a2_*`); nichts unter `data/harvest`; kein Harvest-Client.
4. Jede Zahl mit Quelle (`[S:skript.py]`, `[aj:]`, `[nj:]`); UNBELEGT markieren; Ermessen mit Richtung (Testbarkeit/
   Strenge, DEC-93 H-1). Nichts registrieren, kein Verdikt. Deterministisch (Seeds fest).

## Teil A - Placebo-Design neu (weil seit 2020-03-25 jeder Kalendertag Verfallstag ist, DEC-98 N5)
A-1 **Problem praezise:** P1 (Nicht-Verfalls-Freitage) ist leer; P2 (Nicht-Freitags-08:00-Slots) enthaelt jetzt taegliche
    Optionsverfaelle (BTC ab 2020-02-04, ETH ab 2020-02-18) UND die Bybit-Funding-Abrechnung 08:00 UTC; P3 (uebrige Stunden)
    bleibt. Lege dar, was jedes Placebo nach heutigem Kalender misst und welche Kontamination (Funding, taeglicher
    Verfall, Wochenend-Liquiditaet, US-Makro-Termine 12:30/13:30 UTC nur als Hinweis) jeweils bleibt.
A-2 **Ereignisgroesse statt Ereignisexistenz:** Aus `position` je Delivery (Optionen) die Summe gelieferter Kontrakte je
    Verfallstag und Klasse (taeglich / woechentlich Freitag / monatlich / quartalsweise), je Waehrung, 2020-03-25..2026-06-30
    (nur Zaehlungen/Summen; Verteilung je Klasse, Quantile; Verhaeltnis Freitag zu Mo-Do; Verhaeltnis Monat zu Woche).
    Daraus: Kandidaten-Designs mit vorab fixierbarer Ereignismenge und Placebo, z. B. (i) Ereignis = Freitagsverfaelle
    (woechentlich+monatlich+quartal), Placebo P2' = Mo-Do-Slots 07:30-08:00 (taeglicher Verfall klein + Funding) - dann ist
    die Differenz ein **Groessen**-Effekt und das Placebo konservativ (Richtung ausweisen); (ii) Ereignis = Monats-/
    Quartalsverfaelle, Placebo = Wochenverfaelle (P1 lebt wieder als "kleiner Freitag"); (iii) OI-sortiert: oberes
    Quantil der Verfallstage nach gelieferten Kontrakten gegen unteres Quantil (PIT-fixierbar? OI am Vortag 08:00 ist
    bekannt - ja, aber aus `tickers` erst ab 2026-06-16; aus `settlements.position` nur ex post -> fuer die Registrierung
    nur Kalender-Klassen zulaessig, OI-Sortierung als Bericht). Fuer jedes Design: N je Fenster (W = 12 Monate ab einem
    Fensterbeginn, der VOR dem Blind-Siegel liegt? - NEIN: die A2-Fenster liegen nach dem PRD im Blindbereich; zaehle N
    je Kalenderjahr 2021..2025 und fuer ein hypothetisches Fenster 2024-07..2025-06 und 2025-07..2026-06 NUR als
    Ereigniszahl, ohne Renditen), Cluster-Definition (BTC+ETH ein Cluster), Placebo-N, welche Kontamination bleibt,
    Richtung. Empfehlung eines Designs mit Begruendung (Gabelungsmuster).
A-3 **V-5c-Datenteil:** Zeitlage des TWAP-Fensters [07:30, 08:00) gegen die Delivery-Zeitstempel (DEC-98 N5: 08:00:00 +0,04 s)
    bestaetigen; r_pre-Definition auf 1-min-Kerzen praezise (Kerzen 07:30..07:59 Close-to-Close? open 07:30 bis close 07:59?
    - beide nennen, eine empfehlen; Konvention mit dem Settlement-TWAP begruenden).

## Teil B - sigma30-Nuisance der Vorperiode (2021-03-24..2024-05-31; nur Streuung)
B-1 Je Symbol (BTC, ETH) und je Slot-Klasse: 30-min-Log-Rendite r_pre nach A-3 an (a) Freitagen (woechentlich+monatlich+
    quartal, getrennt ausweisen), (b) Mo-Do (nur taeglicher Verfall), (c) Samstag/Sonntag, (d) P3-Slots: dieselbe Uhrzeit
    +/- k Stunden und ein fester Vergleichsslot (z. B. [15:30, 16:00) UTC, vor dem 16:00-Funding) an allen Tagen, (e)
    r_post [08:00, 09:00) nur als Streuung. Je Klasse: n, SD (ddof 1), MAD/1,4826, Kurtosis, Quantile des Betrags,
    Jahres-Aufschluesselung 2021/2022/2023/2024 (Vol-Regime), SD-Verhaeltnisse Freitag/Mo-Do/Wochenende/P3 mit
    Bootstrap-Band (2.000 Replikate, Seed 27). KEIN Mittel.
B-2 rho(BTC, ETH) der 30-min-Renditen je Klasse (Pearson und Spearman) - PRD-Arbeitswert 0,8, DEC-67 0,815 (Praemie).
B-3 Autokorrelation von r_pre ueber aufeinanderfolgende Ereignisse (Lags 1..10) je Klasse; Varianzfaktor c nach P-3-Logik
    (Bartlett/Batch-Means/stationaerer Bootstrap) fuer eine Ereignis-Mittel-Statistik; erwartet ~1 (Ereignisse eine Woche
    auseinander) - messen.
B-4 **Placebo-SE und SE(Delta) je Design aus A-2 mit gemessenen Groessen:** Formel `[pb:A2]` der Bilanz 2.4
    (`SE(Delta) = sqrt(sigma30^2 (1+rho)/(2N) + SE_placebo^2)` - pruefe die Formel: gepoolt BTC+ETH als ein Cluster;
    leite sie her oder korrigiere sie), mit N je Fenster (12 Monate) je Design; MDE80 nach DEC-94 (3) mit `power_p1`
    (z_krit 1,6449, A3-Praxis 2,4865 als Doppelausweis); Vergleich mit der PRD-Vol-Kette (36 bp BTC) und der Bilanz-
    Tabelle (4,76 / 1,93 / 5,13 bp woechentlich; 9,90 / 5,40 / 11,28 bp monatlich). Prior nur aus der Akte: Monatsverfaelle
    16,5 bp [sek, Ni/Pearson/Poteshman 2005, Aktien]; Wochenverfaelle UNBELEGT (V-5b) -> Prior-Gitter 5 / 8 / 12 / 16,5 /
    25 bp mit Fenster-Power, Regime (`power_p1.assign_regime`), Jahre bis C10. **Keine Zuordnung als Verdikt**, nur die
    Zahlen und was sie fuer die Feasibility bedeuten (GL-012-Kandidat ja/nein je Design, mit Richtung).
B-5 Etiketten: V-5b UNBELEGT bleibt; Vorperiode ist ein anderes Vol-Regime; Bybit-Funding-Kontamination um 08:00; Datenlage.

## Dateien
`scinance3-impl/state/herleitung_a2/PLACEBO_DESIGN_A2.md` (Teil A), `NUISANCE_SIGMA30.md` (Teil B), `a2_vorarbeit.json`
(alle Zahlen, deterministisch, `no_mean`-geprueft, mit Herkunft je Zahl), `ENTSCHEIDUNGSVORLAGEN.md` (Design-Empfehlung,
Gabelungen mit Richtung, was fuer eine A2-Feasibility noch fehlt: V-5b, Fensterlage/Blind-Siegel, Reihenfolge-Frage), und
eine Kurzfassung <= 12 Zeilen: sigma30 je Klasse (BTC/ETH/gepoolt), rho, c, SE(Delta)/MDE80 je Design, N je Fenster,
empfohlenes Design, UNBELEGT-Punkte, Dateipfade. KEIN Mittel, kein Vorzeichen.
