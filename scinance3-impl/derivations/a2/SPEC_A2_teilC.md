# Auftrag: A2-Vorarbeit Teil C - Null-Simulation (DEC-103 E4), bindende SE, Funding-Intervall W2, Pilot-Uebergaberegel als Vorlage

Rolle: Herleitung (Gate-Design/Rauschboden) fuer den Orchestrator von Scinance 3.0. Du schreibst Volltexte in Dateien;
an den Orchestrator geht am Ende eine Kurzfassung (<= 10 Zeilen). **Nichts registrieren, nichts committen, kein Verdikt.**

## Lies zuerst (in dieser Reihenfolge, vollstaendig)
1. `/home/user/scinance/scinance3-impl/state/decisions.md`: Abschnitt `### DEC-103` (A2-Design, bindend fuer diesen
   Auftrag), DEC-98 Nachtrag 5 und 7, DEC-99 (Pilot-Schaetzfenster), DEC-94 (P-1), DEC-101 Entscheidung 7 (Regel U-4).
2. `/home/user/scinance/scinance3-impl/state/herleitung_a2/`: ENTSCHEIDUNGSVORLAGEN.md, PLACEBO_DESIGN_A2.md,
   NUISANCE_SIGMA30.md (Fassung 2), REVIEW_A2_VORARBEIT.md, NACHRECHNUNG_ORCHESTRATOR.md, a2_vorarbeit.json (Kuerzel).
3. `/home/user/scinance/scinance3-impl/PRD_SCINANCE3.md` Abschnitt 5.2 (A2) und `scinance3-impl/CLAUDE.md`.
4. `/home/user/scinance/src/bybit_edge/research/power_p1.py` (benutzen, nicht nachbauen) und, als Muster fuer eine
   Uebergaberegel mit Pilot, `/home/user/scinance/src/bybit_edge/research/h32_fm8/handover.py`.

## Daten (bereitgestellt vom Orchestrator; NICHTS anderes laden, keinen Harvest-Client benutzen, keine Siegeldateien)
Verzeichnis `/home/user/scinance_work/hf_data/raw/` (Hashes in `EXTRACT_LOG.json`):
- `bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet`: symbol, start_ms (UTC, Kerzenbeginn), open, high,
  low, close, volume, turnover. **Nur diese Renditen; jeder Tag liegt vor 2024-06-01** (Assert im Code vor jedem Preis).
- `deribit_settlements_CALENDAR_fields4_2017-05-25_2026-06-30.parquet`: ccy, type, instrument_name, timestamp, position
  (keine Preisfelder). Klassen (Freitag Woche/Monat/Quartal, Mo-Do, Wochenende, Futures-Tage) nach DEC-98 N5 (3) und
  DEC-103 E1/E3 aus Instrumentnamen und Datum.
- `bybit_funding_timestamps_BTCUSDT_ETHUSDT_2025-07-01_2026-06-28.parquet`: symbol, fts (Funding-Zeitstempel, ms).
  Keine Funding-Rate enthalten; nur Zaehlung der Zeitpunkte je Tag.

## Regeln (bindend, Waechter im Code)
- **Kein Mittel, kein Median, kein Vorzeichen irgendeiner Verfallstag-Rendite** (r_pre, r_post, Differenz Ereignis
  minus Placebo, Permutations-Teststatistik auf den REALEN Labels) wird berechnet, gespeichert, geloggt oder gedruckt.
  Die Null-Simulation darf nur die Verteilung unter permutierten Labels ausgeben (SD, Quantile, Anzahl Replikate); der
  beobachtete Kontrast mit den echten Labels wird **nie gebildet** (Code-Waechter: die Funktion, die den Kontrast
  bildet, akzeptiert nur Label-Vektoren, deren Hash nicht dem realen Label-Vektor entspricht; Test dafuer).
- Renditen nur 2021-03-24..2024-05-31; Kalender nur <= 2026-06-30; keine Preisfelder der Settlements; Wochenende in
  keiner Menge; Ausreisser-Tage 2020-08-27, 2024-08-19 ausgeschlossen (DEC-103 E1).
- `print` nur sha256/Zaehlungen; Skripte unter `/home/user/scinance_work/a2_teilC/` (nicht im Repo); deterministisch
  (fester Seed, zwei Laeufe bitgleich, sha256 ausweisen); Python 3, numpy/polars/pyarrow, `-I` nicht noetig.
- Ausgabe: `/home/user/scinance/scinance3-impl/state/herleitung_a2/NULL_SIMULATION_A2.md`,
  `.../PILOT_ROUTE_A2.md`, `.../a2_teilC.json`. ASCII-only, Deutsch, Kuerzel `[aj-C:<pfad>]` auf das JSON. Keine
  Modellnamen in den Dateien.

## Aufgaben
C-1 **Null-Simulation nach DEC-103 E4 (J-(i)) auf der Vorperiode.** Fuer jedes 12-Monats-Fenster der Vorperiode
  (2021-06..2022-05, 2022-06..2023-05, 2023-06..2024-05; dazu gepoolt 2021-03-24..2024-05-31) und fuer das Design
  DEC-103 (Ereignis = Freitage, P2'' = Mo-Do ohne Futures-Tage (in der Vorperiode: alle Mo-Do), P3fix = [15:30, 16:00)
  ohne Monatsend-Freitage, P3all = uebrige Halbstunden-Slots): Label-Permutation Freitag <-> Mo-Do innerhalb derselben
  ISO-Woche (je Woche genau ein Tag erhaelt das Freitags-Label; Anzahl erhalten), >= 2.000 Replikate, Seed fest.
  Ausgeben: SD der Null-Verteilung des Kontrasts x = (r_BTC + r_ETH)/2 (bp), oberes 95-%-Quantil, 99-%-Quantil,
  Exzess-Kurtosis, je Fenster und gepoolt; Vergleich mit der analytischen SE der Vorperiode (Teil B: Klassen-SD,
  c_bind; D_i 7,34 bp je 12 Monate). **Bindende SE nach DEC-94 (5) = max(Vorperiode, Null-Simulation)**; MDE80 Einzel
  und Produkt gegen den Satz neu mit der bindenden SE (power_p1). Dasselbe fuer P3fix/P3all als Kontrastbedingungen
  (Permutation der Tageszeit-Labels innerhalb des Tages ist eine andere Null - benenne, welche Null fuer die
  P3-Bedingungen gilt, mit Richtung, nicht bauen, wenn unklar; Default-Vorschlag begruenden).
  Schwelle nach PRD 5.2 / DEC-103 E4: max(95-%-Quantil der Null; z_krit x SE) - je Fenster ausweisen, welcher Term bindet.
C-2 **Funding-Intervall W2.** Aus den Funding-Zeitstempeln je Tag die Anzahl und die Uhrzeiten (UTC) je Symbol zaehlen;
  Tage mit anderem als 8h-Takt (00/08/16) in W2 (2025-07-01..2026-06-28) je Monat; Folge fuer P2'' (gleicher
  Funding-Termin um 08:00 in Ereignis und Placebo) ausweisen: Anteil der Mo-Do-Tage und Freitage mit Funding um 08:00;
  Vorlage, ob Tage ohne 08:00-Funding aus beiden Mengen auszuschliessen sind (Richtung).
C-3 **Pilot-Uebergaberegel (Vorlage, DEC-103 Abschnitt "Pilot-Schaetzfenster-Route").** Analog DEC-99 (3) und U-4:
  Pilot = Vorperiode 2021-03-24..2024-05-31 (167 Freitage, Mo-Do 666), Pilot-Statistik = derselbe Kontrast; Uebergabe
  nach W1/W2 nur, wenn x_P (Pilot-Kontrast, negatives Vorzeichen registriert) <= -(m*_null + max_W MDE80_W) mit der
  bindenden SE der Testfenster (12 Monate) - formuliere die Regel mechanisch (Formel, alle Groessen vorab fixiert,
  k_pred-Analogon: Verhaeltnis realer Pilot-SD zur Null-SD wie U-4), Power der Pilotstufe gegen das Prior-Gitter
  (5/8/12/16,5/25 bp, Kontrast-Skala und Ereignis-Skala mit 0,842), Fehlerraten (Pilot alpha, Zwei-Stufen-Gesamtrate),
  was GL-012 (Pilot) ausloest, K-Zaehlung (eine Variante), Positivkontrolle in Produktionskonfiguration (Injektion eines
  negativen Kontrasts von -MDE80 an den Ereignis-Tagen der Nullwelt; Kriterium wie DEC-101 N-1/N-2). **Keine Pilot-Zahl
  rechnen** (kein Mittel!). Richtung: Lockerung (ersetzt die PRD-5.2-Vorbedingung) - als Etikett ausformulieren.
C-4 **Entscheidungsvorlagen** in PILOT_ROUTE_A2.md: Default bei Stille (Vorbereitung ja, Registrierung nach Nutzer-OK),
  Alternativen, was fuer eine Registrierung noch fehlt (Negativ-Panel-Daten, Code T0-T7, PK), Gabelungen mit Richtung.

## Form
Kopf jeder MD-Datei: Etikett (kein Mittel/Vorzeichen; Renditen nur Vorperiode; Kalender <= 2026-06-30; nichts
registriert), Quellen, Kuerzel. Tabellen mit Zahlen je Fenster. Abschnitt "Was NICHT folgt". Abschnitt "Reproduktion"
(Skripte, Seeds, sha256). Kurzfassung an den Orchestrator: bindende SE je Fenster, Null-SD gegen analytische SE,
95-%-Quantil, MDE80 Einzel/Produkt neu, Funding-Befund W2 (Anteil 8h-Tage), Pilot-Regel in einer Formel, Pilot-Power bei
16,5 bp, sha256 der JSON, Waechter bestanden.
