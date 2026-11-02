# Herleitungs-Auftrag H-27 (VRP auf DVOL-Backfill): Kontaminations-Inventur, Datenprobe, Feasibility - erst dann Design

Du bist der Herleitungs-Agent (Gate-Design, Power, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert, nicht du. Repo `/home/user/scinance`, Python mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte nur
unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h27_herleitung/` (anlegen),
Volltexte unter `scinance3-impl/state/herleitung_h27/` (anlegen). An den Orchestrator nur eine Kurzfassung
(hoechstens 10 Zeilen). Nichts committen, nichts pushen.

## Pflichtlektuere
- `scinance3-impl/CLAUDE.md` (Verfassung, inkl. DEC-94-Absatz), `scinance3-impl/UEBERGABE_2026-10-12.md` (Abschnitte 3-5).
- `scinance3-impl/state/decisions.md`: DEC-51, -52, -53, -55/56 (Stress), -58 E2, -61 (H-27 eroeffnet, Quellen nicht
  mischen), -62 E3 (BTC+ETH zaehlen als EIN Bein), -73 E3, -85 (BTC-Wochen-SD W1/W2), -91/-92/-93 (Lehren),
  **-94 (Programmregel P-1, bindend fuer H-27)**.
- `scinance3-impl/state/ANTWORT_DATA_HARVEST_DVOL_2026-10-13.md` (Datenquelle), `PRD_SCINANCE3.md` 3.3 (zwoelf
  Pflichtzeilen), 4.2 (WP-9), Klasse P, C.18 (REZENZ-Fenster W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30).
- 2.0-Akte nur lesen: `scinance2-impl/state/hypothesis_registry.md` H-26 (VRP, gesperrt) - H-27 ist eine NEUE
  Hypothese auf anderer Quelle, keine Entsperrung von H-26 (PRD 4.2). Kompendium `survey/ERKENNTNIS_KOMPENDIUM.md`
  E.2/E.7 (C-33), Abschnitt C (C.1-C.19).
- `scinance3-impl/research/R1_RISIKOPRAEMIEN.md` (VRP-Literatur [sek]).
- Code: `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/Zuordnungszahl, inkl. Doppelausweis
  `assign_regime_a3_practice`), `src/bybit_edge/research/wp9_dvol/` (Tagesaggregation, Konventionen).
- Data-Harvest-Client: `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/harvest_client/`
  (`DATA_ACCESS.md` lesen; `harvest_data.py` per `sys.path`; `hd.configure(cache_dir=...)` mit einem Cache-Ordner in
  deinem Skriptordner; Zugang nur ueber die Umgebungs-Secrets `HARVEST_S3_*`).

## Harte Regeln
1. **Ergebnisblindheit fuer H-27 (strenger als ueblich, wegen Vorwissen):** Vor der Registrierung KEINE realisierte
   Volatilitaet (vorwaerts oder nachlaufend, aus beliebigen Preisdaten) von BTC oder ETH auf Tagen ab 2024-06-01
   berechnen, und KEINE DVOL-Niveau-Statistik (Mittel, Median, Quantile, Plots) auf Tagen ab 2024-07-01. Grund: die
   realisierte BTC-Volatilitaet der Urteilsfenster steht bereits in der Akte (Wochen-SD 0,067 / 0,055, DEC-85; A1-
   Feasibility), damit verriete das DVOL-Niveau in W1/W2 das Ergebnis. Erlaubt ab 2024-07-01: Vollstaendigkeit
   (Zeilen je Tag, Luecken, Zeitstempel, Schema), Anschluss am 2025-07-31/08-01 als reine Gleichheits-/Stetigkeits-
   pruefung ohne Niveauausgabe. Nuisance-Groessen (Streuung, Autokorrelation, Jensen-Verzerrung) nur auf
   2021-03-24..2024-05-31, ueber Code, der den Mittelwert der Praemie weder ausgibt noch speichert (Etikett).
2. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder `ic_series_*_UNION_REAL.csv` heissen.
   Die WP-10(A2)-Dateien `state/runs/wp10a2_20260910/wp10a_ivrv_backfill_*_daily.csv` NICHT oeffnen (IV-RV-Niveaus).
   Nie unter `data/harvest` schreiben. Harvest-Bucket nie listen oder globben; nur `hd.catalog()`, `hd.load()`,
   `hd.gaps()`. Kleine Zeitraeume, `columns=` nutzen (Endpunkt ~2 MB/s, geteilt). Keine Zugangsdaten, keine
   Hostnamen, keine Modellnamen in Dateien. Kein Live-Order-Code.
3. Jede Zahl mit Herleitung oder Quelle; Sekundaerbelege `[sek]`; Fehlendes heisst UNBELEGT und blockiert.
4. Rechnungen > 2 h mit `nohup setsid` starten.

## Stufe 0 - Kontaminations-Inventur (zuerst, Datei `KONTAMINATION.md`)
Liste jede bereits in der Akte stehende Groesse, die das H-27-Ergebnis in W1/W2 teilweise verraet (mindestens:
BTC-Wochen-SD W1/W2 aus DEC-85 und v5e; BTC-/EW-Faktor-SD aus `herleitung_a1/FEASIBILITY.md`; WP-10(A2)-IV-RV-Serie
(existiert, Inhalt nicht ansehen); R1-Literaturzahl BVRP; was der Orchestrator nach eigener Aussage gesehen hat).
Bewerte: Welche Teststatistiken waeren dadurch nicht mehr blind (z. B. mittlere Praemie IV - RV_fwd30 in W1/W2), welche
bleiben blind (z. B. Konstrukte, die aus Fenster-RV und Fenster-IV-Mittel nicht ableitbar sind)? Folge fuer das
Design als Entscheidungsvorlage; das Etikett C.17 ("gesehen") ist Pflicht.

## Stufe 1 - Datenprobe (C.8) und Feasibility (C.12), Dateien `DATENPROBE.md`, `FEASIBILITY.md`, `feasibility.json`
- Katalog: Abdeckung `deribit/dvol` BTC/ETH ab 2021-03-24, `hd.gaps` benennen (nicht interpolieren). Tagesreihe aus
  den Stundenkerzen nach WP-9-Konvention (Tagesschluss = letzte Stundenkerze des UTC-Tages; begruenden, ob close oder
  open der Folgestunde). DEC-61: eine Quelle durchgehend - pruefen und dokumentieren, dass Backfill und Strom ab
  2025-08-01 dieselbe Quelle/Konvention sind.
- RV-Quelle festlegen und begruenden (gleiches Underlying wie DVOL so nah wie moeglich; verfuegbar ueber Harvest fuer
  2021..2026 bei vertretbarem Datenvolumen - pruefe den Katalog auf kompakte Preisquellen; Rueckfall: Tagesschluesse
  aus dem Union-Panel `.../scratchpad/panel/panel_1d` BTCUSDT/ETHUSDT). Annualisierung/Day-Count EINE gemeinsame
  Konstante (24/7).
- Nuisance auf 2021-03-24..2024-05-31 (Regel 1): SD und Autokorrelation der taeglichen Praemie IV - RV_fwd30
  (ueberlappende 30-Tage-Ziele!) und der nicht ueberlappenden Monatsvariante, Varianzfaktor c der TESTSTATISTIK nach
  DEC-94 (4) - Achtung: `power_p1.variance_factor` mit kurzer Bandbreite unterschaetzt starke Persistenz (Docstring);
  die Blocklaenge/Bandbreite muss zur gemessenen Autokorrelation passen und begruendet werden. Jensen-Verzerrung des
  RV-Schaetzers (Nullwelt-Simulation).
- Prior: aus der Literatur [sek] mit Quelle, Zeitraum vor 2024-07 (eine Quelle mit Stichprobe in W1/W2 waere
  Outcome-Information); ohne Quelle UNBELEGT -> blockiert.
- Power und Zuordnung ausschliesslich mit `power_p1.assign_regime` (SE inkl. c, BTC+ETH als EIN Bein nach DEC-62 E3 -
  begruende die Aggregation) plus Doppelausweis `assign_regime_a3_practice`. Ergebnis: C10 / DEC52 / GL012.
  **Ist das Ergebnis GL012 oder der Prior UNBELEGT oder macht Stufe 0 jede sinnvolle Statistik nicht-blind, hoere hier
  auf** (Befund in `FEASIBILITY.md`, Kurzfassung an den Orchestrator).

## Stufe 2 - nur wenn Stufe 1 offen bleibt: `ENTSCHEIDUNGSVORLAGEN.md`, `ERSTFASSUNG_H27_entwurf.md`
Registriertes Design (Statistik, SE-Regel nach DEC-94, Regime, K und Familie, Schwelle als kritischer Wert, Selektions-
decke), DEC-39-Trio (positiv, Null mit IV = wahre Forward-Vol inkl. Jensen, adversarial/Peso: Vol-Spruenge), Positiv-
kontrolle in Produktionskonfiguration mit vorab fixierter Bestehensregel (prueft die Power-Annahme, DEC-94 (5) 10-%-
Regel), Stress-Abdeckung (DEC-55/56), zwoelf Pflichtzeilen mit Quelle, Kapitalfreiheit/C-33-Abgrenzung, Bauliste.
Weise bei jeder Ermessensentscheidung aus, in welche Richtung (Testbarkeit oder Strenge) sie faellt (A1-Lehre:
Gabelungsmuster).

## Rueckmeldung
Hoechstens 10 Zeilen: Kontaminationsbefund, Datenprobe (Abdeckung, Luecken), RV-Quelle, Nuisance-SD und c, Prior mit
Quelle, Zuordnung (P-1 und A3-Praxis), ob Stufe 2 gemacht wurde, Dateiliste, UNBELEGT-Punkte.

## Datenstand beim Start (2026-10-13 12:55 UTC) - Reihenfolge
Der Katalog-Export vom 2026-10-12 10:50 UTC fuehrt `deribit/dvol` erst ab 2025-08-01; der Backfill 2021-03-24..2025-07-31
erscheint erst mit einem spaeteren Export. Der Katalog ist ~280 MB (Download einige Minuten) - nur einmal laden, dann
`hd.catalog()` im selben Prozess wiederverwenden; `refresh=True` nur fuer die Abdeckungspruefung.
Mach zuerst Stufe 0 und die datenunabhaengigen Teile von Stufe 1 (RV-Quelle anhand des Katalogs, Prior-Literatur,
Konventionen, Plan der Nuisance-Rechnung). Pruefe dann einmal mit `hd.catalog(refresh=True)`, ob `deribit/dvol` BTC und
ETH ab 2021-03-24 fuehrt. Wenn NEIN: hoere auf und melde "wartet auf Daten" mit dem bisherigen Stand (Dateien bleiben
liegen; der Orchestrator setzt dich fort). Wenn JA: weiter mit Datenprobe und Feasibility.

## FORTSETZUNG 2026-10-17 - Orchestrator-Beschluesse DEC-96 (bindend, gehen dem Text oben vor)
Lies in `scinance3-impl/state/decisions.md` DEC-96 mit Nachtrag 1 und 2 (und DEC-95). Kurzfassung:
- **EV-0c beschlossen:** H-27 wird NICHT auf W1/W2 registriert, sondern auf zwei gleich langen, prospektiven,
  blinden Fenstern W3/W4 ab 2026-07-01. Laenge L in Monaten aus {6, 9, 12}: das kleinste L, fuer das
  `power_p1.assign_regime` (P-1, Prior und Nuisance aus Stufe 1) C10 oder DEC52 ergibt; ist auch L = 12 GL012, ist
  H-27 GL-012 vor der Registrierung. Jedes Fenster braucht 30 Tage Vorwaerts-RV nach Fensterende. W1/W2 sind nur
  Aera-Profil (nach dem Urteil, Etikett "nicht blind") - jetzt NICHT rechnen.
- **Blind-Siegel (programmweit):** keine DVOL-Niveau-/Streuungs-/Verteilungsstatistik und keine RV bzw.
  Renditestreuung von BTC/ETH auf Tagen ab 2026-07-01. Weiterhin gilt Regel 1 oben (keine RV ab 2024-06-01, keine
  DVOL-Niveaus ab 2024-07-01). Erlaubt ab dort nur Vollstaendigkeit (Zeilen, Luecken, Zeitstempel, Schema).
- **Daten (Katalog 2026-10-17T10:39:26Z, vom Orchestrator geprueft):** `deribit/dvol` BTC/ETH 2021-03-24..2026-10-16,
  2.033 Tage, keine Luecken, alle DONE. `bybit/publicTrade` BTCUSDT/ETHUSDT ab 2026-07-01 lueckenlos. Gemischte
  Live/Archiv-Tage aendern den Tagesschluss (letzter Trade vor 00:00 UTC) nicht (DEC-96 Nachtrag 2).
- **RV-Quelle und Definition:** Nuisance-Periode und kuenftiger Lauf muessen DIESELBE RV-Definition haben. Panel-
  Tagesschluesse (Bybit, 00:00 UTC) gibt es fuer 2021..2026-09-14; fuer W3/W4 kommen die Tagesschluesse aus
  `bybit/publicTrade` (gleiche 00:00-UTC-Konvention) oder einem kuenftigen Panel-Strom. Pruefe und dokumentiere
  die Gleichheit der Konvention (Panel-close vs. letzter Trade vor 00:00 UTC) auf einem Ueberlappungszeitraum VOR
  2024-06-01 (sonst Blind-Siegel), z. B. einige Tage 2023 aus publicTrade - nur Gleichheit/Abweichung ausgeben.
- **Aufgabe jetzt:** Stufe 1 fertig rechnen fuer W3/W4: Datenprobe DVOL (Tagesschluss-Konvention, Anschluss 2025-07-31/
  08-01 als Gleichheitspruefung ohne Niveau), Nuisance auf 2021-03-24..2024-05-31 (SD, Autokorrelation, Varianzfaktor c
  der Teststatistik mit begruendeter Bandbreite, Jensen-Verzerrung in einer Nullwelt), Prior [sek] mit Quelle,
  Fensterlaenge L nach der Regel oben, Zuordnung `assign_regime` + Doppelausweis `assign_regime_a3_practice`.
  Dann Stufe 2 (Design, DEC-39-Trio, Positivkontroll-Plan, zwoelf Pflichtzeilen, Bauliste), nur wenn L existiert.
  `FEASIBILITY.md`/`feasibility.json` fortschreiben; die bisherige W1/W2-Feasibility-Planung als ueberholt kennzeichnen.
