# Herleitungs-Auftrag: HF-RV-Nuisance (Option 3, DEC-98) und A2-Ereigniszensus - NUR NUISANCE, KEIN MITTEL

Du bist der Herleitungs-Agent (Nuisance, Power, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert und entscheidet, nicht du. Repo `/home/user/scinance`, Python mit `PYTHONPATH=/home/user/scinance/src`.
Eigene Skripte NUR unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hfrv_herleitung/`
(anlegen). Volltexte unter `/home/user/scinance/scinance3-impl/state/herleitung_hfrv/` (anlegen). Kurzfassung an den
Orchestrator hoechstens 12 Zeilen. Nichts committen, nichts pushen. Keine Zugangsdaten, keine Hostnamen, keine
Modellnamen. Doku Deutsch (ASCII-safe: ae/oe/ue/ss), Code Englisch.

## Daten (lokal, bereits extrahiert; NICHT den Harvest-Client benutzen, nichts nachladen, nichts listen)
Verzeichnis `D = /tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/`.
Die Dateien entstehen gerade (Download laeuft). WARTE, bis in BEIDEN Logs
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hout/download_hf.log` und
`.../hout/download_deribit.log` eine Zeile mit `ALLDONE` steht (Bash: `until grep -q ALLDONE LOG; do sleep 30; done`,
Timeout grosszuegig, ggf. mehrfach). Lies vorher die Akten (unten). Enthaelt die ALLDONE-Zeile `failed_months` mit
Eintraegen, melde das und rechne nur mit vollstaendigen Dateien (Luecken benennen, nie fuellen).
- `D/bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet`, `D/bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet`:
  1-min-Kerzen Bybit linear, Spalten symbol, start_ms (UTC-ms, Kerzenbeginn), open, high, low, close, volume, turnover,
  column_symbol, category, interval. Erwartung 1.440 Zeilen je UTC-Tag; pruefe Duplikate/Luecken je Tag und benenne sie.
- `D/deribit_dvol_raw_2021-03-24_2024-05-31.parquet`: Rohzeilen (symbol BTC/ETH, ts_exchange_ms, payload_json) des
  Stroms `deribit/dvol` (Stundenkerzen des DVOL-Index). Extraktion wie in der H-27-Akte: IV(t) = close der 23:00-UTC-
  Stundenkerze (Wert um 24:00 UTC) - siehe `scratchpad/h27_herleitung/dvol_probe.py` und `h27_series.py`, dieselbe
  Konvention uebernehmen (Payload-Layout zuerst ansehen).
- `D/deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet`: NUR Kalender: column_symbol (BTC/ETH),
  instrument_name (z. B. `BTC-29MAR24`, `BTC-29MAR24-60000-C`, `ETH-PERPETUAL`), type (`delivery` | `settlement`),
  timestamp_ms. Preise wurden absichtlich entfernt.
- `D/deribit_rest_deliveryPrices_DATES_2016-03-18_2026-10-20.parquet`: NUR index_name (btc_usd/eth_usd) und date.
- Vorbild-Code und Waechter: `scratchpad/h27_herleitung/` (h27_common.py: `truncate_prices`, `assert_rv_day`,
  `assert_dvol_level_day`, `no_mean`, `LABEL`; h27_series.py; nuisance-Skripte; `power_h27.py`). Waechter und
  Statistik-Definitionen S1/S2/S3 EXAKT wiederverwenden (kopieren, nicht veraendern; bei Bedarf eigene Zusatzwaechter).
- Vergleichszahlen: `scinance3-impl/state/herleitung_h27/feasibility.json` (nuisance.BTC.S1: SD 18,60 VP, c 28,17,
  ACF-Profil; Nullwelt SE_null 4,17 bei n 365; Prior pi-2 9,47, Band 7,00..13,72, pi-1 10,48) und FEASIBILITY.md
  Abschnitte 2, 3, 5, P-1..P-7; REVIEW_H27.md B-1 (HF-RV: Rausch-SD ~10,9 VP, SD rauschfrei ~15,1 UNBELEGT, Konsens-c
  18,6); `state/PROGRAMM_BILANZ_2026-10-18.md` Zeilen 264-280 (Fensterlaengen-Tabelle, Spalten) und Abschnitt 2.4 (A2).

## Harte Regeln (Blind-Siegel und Waechter)
1. **Kein Mittel.** Der Mittelwert der Praemie P(t) = IV - RV (in keiner Einheit), das DVOL-Mittel und jede
   Vorzeichen-/Niveau-Aussage der Praemie werden weder ausgegeben noch gespeichert noch in die Kurzfassung
   geschrieben. `no_mean` auf JEDES Ausgabe-Dict; `LABEL` in jeder Datei. RV-Niveaus (rms RV) sind zulaessig.
2. **Keine Preise/Renditen ab 2024-06-01**: `truncate_prices`/`assert_rv_day` auf 2024-05-31; IV-Tage t in
   [2021-03-24, 2024-05-01] (t + 30 <= 2024-05-31). Pruefe am Anfang per assert, dass die Kline-Extrakte keinen Tag
   nach 2024-05-31 enthalten; kein DVOL-Niveau ab 2024-07-01 (Extrakt endet ohnehin 2024-05-31).
3. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder `ic_series_*_UNION_REAL.csv`
   heissen; keine WP-10(A2)-/WP-10(A)-IV-RV-Dateien; nichts unter `data/harvest`; keine `state/runs/*`-Siegel.
4. A2-Zensus: NUR Kalender und Zeitlage (Zeitstempel). Keine Renditen, keine Volatilitaet an Verfallstagen (sigma30
   ist NICHT Teil dieses Auftrags - als offene Vorlage nennen).
5. Jede Zahl mit Quelle (`[S:skript.py]`, `[fj:pfad.im.json]`); UNBELEGT markieren statt schaetzen. Ermessen mit
   Richtung (Testbarkeit/Strenge) ausweisen (Gabelungsmuster DEC-93 H-1). Alles deterministisch (Seeds fest).

## Teil A - HF-RV-Nuisance (Vorperiode)
A-1 **Serien.** Je Symbol (BTC bindend, ETH Bericht): Tages-Realized-Variance aus Intraday-Log-Renditen der UTC-Tage,
    Varianten (alle rechnen, Richtung ausweisen): (i) 1-min roh; (ii) 5-min (Kerzen 0,5,10,...); (iii) 5-min
    subsample-gemittelt (5 Phasen); (iv) 15-min; (v) 30-min; (vi) close-to-close aus dem letzten 1-min-close des
    Tages (Konsistenzkontrolle gegen die Panel-basierte H-27-Zahl SD 18,60 - Abweichung benennen).
    RV_fwd30^HF(t) = sqrt((365/30) * sum_{k=1..30} RV_day(t+k)) (Konstante 365 wie H-27; Tage t+k = UTC-Tage nach dem
    IV-Tag t). Praemie P(t) = IV(t) - RV_fwd30(t) in S1 (Vol-Punkte), S2 (Varianz x 100), S3 (ln IV - ln RV).
    Tage mit unvollstaendigen 1-min-Daten (< 1.440 Zeilen) oder fehlender IV: P(t) fehlend, zaehlen, nie fuellen;
    Regel vorab fixieren (z. B. Tag gilt als vollstaendig ab >= 1.380 Zeilen? - nein: nur 1.440 = vollstaendig,
    sonst fehlend; Abweichung mit Grund).
A-2 **Statistiken** (im Speicher, je Variante, Symbol, Einheit): n, SD (ddof 1), ACF Lags 1..180 (ausgeben 1, 10, 20, 30,
    60, 120, 180, erster Lag < 0,10), Kurtosis, Korrelation BTC/ETH der Praemie, kappa-Rauschmass wie REVIEW_H27 B-1
    (E[x^2]/E[x_s x_{s+L}], L 2..5, auf RV_day) je Variante; Verhaeltnis SD_HF / SD_cc; rms RV je Variante
    (Niveau-Verzerrung gegen close-to-close benennen, braucht ggf. eigenes J).
A-3 **Varianzfaktor c nach Regel P-3** (H-27 FEASIBILITY P-3, bindend: c = max(1, max{Bartlett 60/90/120, Batch-Means
    60/90/120}); 180-Regel bei ACF(120) > 0,10; stationaerer Bootstrap 30/60/90 mit `power_p1.stationary_bootstrap_se`,
    2.000 Replikate, Seed 27, Bericht; Monatsvariante c_m). Konsens-c (Review B-2/B-1) ebenfalls ausweisen.
A-4 **Fenster-SE und Fensterlaenge** mit `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/
    Zuordnungszahl): SE_W = SD * sqrt(c / n_W), n_W = 335 (bindend) und 365 (Bericht); bindende SE = max(SE_nuis,
    SE_null) mit SE_null aus der H-27-Akte (4,17 bei n 365, skaliert mit sqrt(365/n); Hinweis: die rauschfreie
    SE_null der HF-Welt waere kleiner - als UNBELEGT ausweisen, nicht neu kalibrieren). Tabelle wie Bilanz Zeilen
    272-274: fuer Prior pi-2 zentral 9,47 (Band 7,00 / 13,72; pi-1 10,48): Tage je Fenster fuer C10 nach P-1
    (z_krit, DEC-94) und nach A3-Praxis (2,4865), mit c nach Regel UND mit Konsens-c, je RV-Variante; daraus
    Kalenderdaten (zwei disjunkte Fenster ab 2026-07-01, RV-Ziel 30 Tage nach Fensterende) - wann waere ein VRP-
    Urteil mit HF-RV fruehestens moeglich. Vergleich mit der UNBELEGT-Annahme SD 15,1: bestaetigt / nicht bestaetigt.
A-5 **Bein-Aggregation** (Bericht): Tagesmittel BTC/ETH, Konjunktion; Rangkorrelation der P-Serien.
A-6 **Vorlage** `ENTSCHEIDUNGSVORLAGEN.md`: (a) Ist Option 3 tragfaehig (SD-Gewinn, c, Fensterlaenge)? (b) Welche
    RV-Variante vorab fixieren (eine Empfehlung mit Richtung; Kriterien: kappa, SD, Robustheit gegen Mikrostruktur,
    Definitionsgleichheit kuenftiger Fenster aus `bybit/rest.kline1m` laufend)? (c) Text-Entwurf fuer eine neue
    VRP-Hypothese (H-33-Kandidat, eigenes K, Etikett "beschlossen nach Kenntnis der H-27-Feasibility (GL-034)",
    Richtung Testbarkeit, blinde Fenster ab 2026-07-01, Laenge VORAB fixiert aus dieser Nuisance; Fenster-Ende fuer
    das Blind-Siegel, Vorlauf/Registrierung spaeter); (d) was NICHT folgt (kein Verdikt, keine Registrierung, kein
    Mittel gesehen); (e) offene UNBELEGT-Punkte (J der HF-Welt, SE_null HF, ETH-Prior, Konsens-c als P-3-Aenderung).
    Ausgaben: `NUISANCE_HFRV.md` (Tabellen, Quellen), `nuisance_hfrv.json` (alle Zahlen, deterministisch, no_mean-
    geprueft), `ENTSCHEIDUNGSVORLAGEN.md`.

## Teil B - A2-Ereigniszensus (nur Kalender/Zeitlage)
B-1 Aus dem Settlement-Kalender je Waehrung: `delivery`-Ereignisse nach Instrument-Typ (Future `CCY-DDMMMYY`,
    Option `CCY-DDMMMYY-STRIKE-C/P`, Perpetual), Verfallsdatum aus dem Namen; je Verfallsdatum: Zahl der gelieferten
    Instrumente; Klassifikation der Verfaelle (taeglich / woechentlich Freitag / monatlich letzter Freitag /
    quartalsweise) nach Deribit-Regeln (pruefen, nicht annehmen: Wochentag-Verteilung, Abstand aufeinanderfolgender
    Verfaelle). Seit wann gibt es woechentliche Options-/Futures-Verfaelle (V-5a), seit wann taegliche Verfaelle?
    Ereigniszahlen je Jahr und je Menge (woechentlich-ohne-monatlich, monatlich, quartalsweise) fuer 2020-03-25..
    2026-06-30 und fuer die Teilperioden (Vorperiode bis 2024-05-31; W-Fenster 2024-07..2026-06; blind ab 2026-07).
B-2 **Zeitlage:** Verteilung der delivery-/settlement-Zeitstempel innerhalb des UTC-Tages (Sekunden nach 08:00 UTC;
    Quantile, Ausreisser benennen), Stabilitaet ueber die Jahre; Datum des Zeitstempels gegen Verfallsdatum aus dem
    Namen (gleicher Tag?). Zeitlage der taeglichen `settlement`-Zeilen (Perpetual/Futures) ebenso.
B-3 **Placebo-Kalender:** Fuer V-5c/A2 die Menge der Nicht-Verfalls-Freitage und der uebrigen Wochentage je Periode
    (Zaehlung), plus `deliveryPrices`-Datumsreihe (seit wann taeglich/woechentlich; Luecken benennen; fruehe Jahre
    woechentlich).
B-4 Ausgaben: `A2_EREIGNISZENSUS.md`, `a2_census.json`. Keine Renditen, keine Volatilitaet, keine Preise (sind nicht
    in den Extrakten). Offene Vorlage: sigma30 (gepoolt BTC/ETH, Verfalls-Slot 07:30-08:00 UTC gegen Placebo-Slots,
    Vorperiode <= 2024-05-31, 1-min-Kerzen) als naechste Nuisance-Messung - nur benennen, NICHT rechnen.

## Rueckmeldung (<= 12 Zeilen)
SD je RV-Variante gegen 18,60; c (Regel/Konsens); Tage je Fenster fuer C10 (P-1 und A3-Praxis, pi-2 zentral), fruehestes
Urteilsdatum; empfohlene RV-Variante mit Richtung; A2: seit wann woechentlich, Ereignisse je Jahr, Zeitlage;
UNBELEGT-Punkte; Dateipfade. KEIN Mittel, kein Vorzeichen der Praemie.
