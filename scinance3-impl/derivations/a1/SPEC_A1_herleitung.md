# Herleitungs-Auftrag A1 (H-31): Feasibility zuerst, dann Testdesign - Funding-Long-Bein gegen Universums-Hedge

Du bist der Herleitungs-Agent (Gate-Design, Power, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert, nicht du. Repo `/home/user/scinance`, Paket `bybit_edge` unter `src/`. Python immer mit
`PYTHONPATH=/home/user/scinance/src python ...`. Eigene Skripte nur im Ordner
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung/` (anlegen).
Volltexte in Dateien unter `scinance3-impl/state/herleitung_a1/` (anlegen); an den Orchestrator nur eine Kurzfassung
(hoechstens 10 Zeilen).

## Pflichtlektuere (zuerst)
- `scinance3-impl/CLAUDE.md` (Verfassung), `scinance3-impl/UEBERGABE_2026-10-12.md`.
- `scinance3-impl/PRD_SCINANCE3.md` Abschnitt 5.1 (A1), Abschnitt 3.3 (zwoelf Pflichtzeilen), 4.4 (V-1..V-3).
- `scinance3-impl/state/decisions.md`: DEC-51, -52, -53, -58 (E2/E3), -59, -67, -70, -73, -82, -84, -91, -92 (Lehre).
- `scinance3-impl/state/gate_log.md` GL-032 und `scinance3-impl/state/REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md`
  (warum A3 an der Power gescheitert ist: Power mit Boden-SE statt mit der SE des registrierten Tests).
- Vorbild fuer Aufbau und Tiefe: `scinance3-impl/state/herleitung_h28_h30_v3/` und
  `scinance3-impl/state/registered/h28_h30_v3.yaml`.
- Code: `src/bybit_edge/research/wp7_universe/panel_load.py` (`funding_i_per_payment`, `funding_excess_daily`,
  `funding_excess_weekly`, `weekly_returns_and_mask_union`, `returns_valid`), `.../wp7_universe/stats.py`,
  `src/bybit_edge/research/wp13_xsec/` (Nullen, Positivkontrolle, Gate-Logik - wiederverwendbar?).

## Harte Regeln
1. **Ergebnisblindheit:** Keine A1-Outcome-Groesse auf Daten ab 2024-07-01 berechnen, ansehen oder speichern. Outcome
   ist alles, was fuer das A1-Portfolio (oder irgendeine Funding-Sortierung) Daten aus der Woche NACH der Formation
   benutzt: Preisbein, Funding-Bein, Gesamtrendite, Korrelation Schluessel->Folgewoche. Erlaubt ab 2024-07-01 sind nur
   formationsseitige Groessen (Schluessel-Verteilung, Dezil-Spread des Schluessels in der Formationswoche, Klumpen-/
   Degenerations-Anteile, Universumsgroesse, Intervallklassen, PIT-Betas aus Vergangenheitsrenditen, Faktor-SDs des
   Marktes) - also das, was ein Zensus misst. Outcome-seitige STREUUNGS-Groessen (Nuisance: SD, Autokorrelation) nur auf
   2021-03-01..2024-06-30 und nur ueber Code, der den Mittelwert weder ausgibt noch speichert; das ist als Etikett zu
   fuehren. Die Wochen nach 2026-06-30 bleiben ganz unbenutzt.
2. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder `ic_series_*_UNION_REAL.csv` heissen.
   Nie unter `data/harvest` schreiben. Kein Live-Order-Code. Nichts committen, nichts pushen. Keine Zugangsdaten, keine
   Hostnamen in Dateien. Keine Modellnamen in Repo-Dateien.
3. Jede Zahl mit Herleitung oder Quelle; Sekundaerbelege `[sek]`; Fehlendes heisst UNBELEGT und blockiert.
4. Panel (Union, inkl. Delistete; beide mit `funding_n`/`funding_sum` je Tag):
   `--panel-base /tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/panel/panel_1d`
   `--delisted-base /tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/panel/panel_1d_delisted`
   Nur lesen, Pfade als Argumente uebergeben, Skripte nie aus diesem Ordner starten.
5. Rechnungen > 2 h: mit `nohup setsid` starten und abwarten; sonst normal.

## Stufe 1 - Feasibility (C.12) VOR jedem Design; Datei `FEASIBILITY.md` + `feasibility.json`
Konstruktion fest (DEC-70): Long D1 (staerkste Unterschreitung von I nach Schluessel = Wochen-SUMME (F - I) mit I je
Zahlung skaliert nach Intervallklasse, DEC-67 E2/DEC-84) gegen den gleichgewichteten PIT-Universums-Hedge, Wochen-
Halteperiode, Union-Panel. Fenster W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30.
Je Fenster formationsseitig (erlaubt):
- (a) Zahl der Symbole mit Funding-Historie ueber beide Fenster (Kill PRD 5.1 (3): < 117), K je Woche.
- (b) Schluessel-Autokorrelation lag 1 (Kill (4): < 0,30; WP-7 hatte 0,42 - auf den Fenstern bestaetigen).
- (c) D1-Degeneration je Woche (DEC-67 E3 / DEC-70: streng negativer Anteil >= 10 % in der Median-Woche).
- (d) Schluessel-Spread in der Formationswoche: Mittel(Schluessel D1) - Mittel(Schluessel Universum), je Woche,
  Median/Quantile, in bp/Woche.
- (e) Intervallklassen-Anteile in D1 (1h/2h/4h/8h) je Fenster; W1/W2-Inhomogenitaet schriftlich (DEC-58 E3).
Auf 2021-03..2024-06 (Nuisance, Etikett nach Regel 1): SD und Autokorrelation der Wochen-Gesamtrendite von
D1-minus-Universum, Zerlegung der SD in Preis- und Funding-Bein, Beta-Fehlanpassung D1 vs Universum (PIT-Beta) und ihr
Beitrag zur SD (faktorbedingte Streuung - die A3-Lehre), sowie die Persistenz des Funding-Beins (Formations-Spread ->
Folgewochen-Funding-Spread als Verhaeltnis; nur das Verhaeltnis, kein Rendite-Mittel ausgeben).
Dann der A-priori-Effekt: `prem_prior` = erwarteter Funding-Vorteil der Haltewoche (Formations-Spread je Fenster mal
Persistenz) mal Anteil theta, der NICHT durch das Preisbein kompensiert wird. theta braucht eine Quelle; ohne Quelle
rechne theta in {0,25; 0,5; 1,0} (1,0 = gar keine Kompensation, Obergrenze) und kennzeichne. Power und Zuordnungsregel
PRD 5.1 mit der SE des REGISTRIERTEN Tests (Mittelwert-Test mit Block-Bootstrap bzw. Residual-Alpha-Test gegen die
A3-Faktoren; SE inklusive faktorbedingter Streuung und Autokorrelation, W_eff), je Fenster W = 52:
`P_fenster`, Zuordnung C.10 / DEC-52, und GL-012-Pruefung `3,1680 * SE_gepoolt-Aequivalent > prem_prior`.
**Ist A1 selbst bei theta = 1,0 in der GL-012-Pruefung nicht testbar, hoere hier auf:** Befund und Begruendung in
`FEASIBILITY.md`, Kurzfassung an den Orchestrator. Kein Design.

## Stufe 2 - nur wenn Stufe 1 testbar ist: Testdesign; Dateien `ENTSCHEIDUNGSVORLAGEN.md`, `ERSTFASSUNG_H31_entwurf.md`
- Registriertes Design: Statistik (Gesamtrendite D1 - Universum; urteilstragend das Residual-Alpha gegen Momentum und
  Reversal, PRD 5.1 (d)), SE-Regel, Fenster-Regime nach der Zuordnungsregel (C.10 hart oder DEC-52 - falls DEC-52, was
  gebaut werden muss), Selektions-K (PRD: K = 3 Lookbacks 3/5/7 Tage - begruende K; weniger Varianten = weniger
  Deflation), BH-Familie, Selektions-Decke am Null-Fixture, Schwelle als Herleitungs-Referenz (DEC-58b).
- Null mit exakter Kompensation (8h- und 1h-Symbole nebeneinander), Peso-Fixture (Merton-Spruenge), Positiv-Fixture
  (50 % unkompensiert) als DEC-39-Trio; Positivkontrolle in Produktionskonfiguration auf der echten Fensterform
  (Wochen, Alive-Masken, synthetische Renditen) mit vorab fixierter Bestehensregel - sie muss die Power-Annahme
  pruefen (A3-Lehre).
- Funding-Buchhaltung: Intervall-Normierung, Umschalt-Tage, I = 0 fuer Sonderpaare, 1h-Ausschluss als look-ahead-freie
  Symbol-Wochen-Regel plus Pflicht-Sensitivitaet (DEC-58 E3), Delisting-Behandlung (letzter Schlusskurs, keine
  Imputation), Survivorship-Etikett.
- Kill-Regeln (Degeneration D1, kein Residuum), Etiketten (PRD 5.1), DEC-53-Artefakte, Testpflichten T0-T7.
- Zwoelf Pflichtzeilen (PRD 3.3) vollstaendig, jede mit Quelle.
- Liste der Bauarbeiten (was im Code fehlt) als eigener Abschnitt.

## Rueckmeldung
Hoechstens 10 Zeilen: Feasibility-Befund mit den entscheidenden Zahlen (K, Autokorrelation, Degeneration, Spread,
SE, Power je theta, Zuordnung), ob Stufe 2 gemacht wurde, Liste der erzeugten Dateien, offene UNBELEGT-Punkte.
