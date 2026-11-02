# Review-Auftrag (adversarisch): HF-RV-Nuisance (Option 3, DEC-98) und A2-Ereigniszensus

Du bist der adversarische Reviewer im Forschungsprogramm Scinance 3.0 (Gate-Auditor-Rolle: Veto-Recht, Richtung Strenge).
Repo `/home/user/scinance`, Python mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte NUR unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hfrv_review/` (anlegen). Volltext
`/home/user/scinance/scinance3-impl/state/herleitung_hfrv/REVIEW_HFRV.md`. Kurzfassung hoechstens 10 Zeilen. Nichts
committen. Keine Zugangsdaten, Hostnamen, Modellnamen. Deutsch (ASCII-safe), Code Englisch.

## Gegenstand
`scinance3-impl/state/herleitung_hfrv/`: `NUISANCE_HFRV.md`, `nuisance_hfrv.json`, `ENTSCHEIDUNGSVORLAGEN.md`,
`A2_EREIGNISZENSUS.md`, `a2_census.json`; Skripte des Herleitungsagenten unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hfrv_herleitung/`.
Auftrag, gegen den geprueft wird: `.../scratchpad/SPEC_HFRV_herleitung.md` (woertlich lesen). Massstaebe:
`scinance3-impl/CLAUDE.md`, `state/decisions.md` DEC-94 (P-1), DEC-96 (Blind-Siegel E3), DEC-97/GL-034, DEC-98 (Option 3,
Nachtrag 4), `state/herleitung_h27/FEASIBILITY.md` (P-1..P-7, Nuisance-Tabelle), `REVIEW_H27.md` (B-1, B-2),
`state/PROGRAMM_BILANZ_2026-10-18.md` (Zeilen 264-280, Abschnitt 2.4), `src/bybit_edge/research/power_p1.py`.

## Harte Regeln
- Dieselben Siegel wie der Herleitungsagent: kein Mittel der Praemie (keine Einheit), kein DVOL-Mittel, keine Preise/
  Renditen ab 2024-06-01, keine Siegeldateien (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`),
  keine WP-10-IV-RV-Dateien, kein Harvest-Client, nichts unter `data/harvest`. Daten nur aus
  `.../scratchpad/hf_data/raw/` (Extrakte) - pruefe zuerst per assert, dass du keinen Tag nach 2024-05-31 in den
  Kline-Extrakten anfasst.
- Nachrechnen ist Pflicht: mindestens SD je RV-Variante (BTC, S1), c nach Regel P-3 (Bartlett 60/90/120, Batch-Means
  60/90/120) und die Fensterlaengen-Zeile fuer pi-2 zentral mit `power_p1` - unabhaengig vom Code des Agenten (eigenes
  Skript). Abweichungen > 1 % benennen.

## Pruefpunkte (jeder mit Befund: BESTAETIGT / ABWEICHUNG / VETO und Richtung)
1. Siegel-Treue: Wurde ein Praemienmittel, Vorzeichen oder DVOL-Mittel ausgegeben/gespeichert (JSON, MD, Logs, Skripte)?
   `no_mean`-Waechter auf jedem Ausgabe-Dict? Tage ab 2024-06-01 beruehrt? IV-Tage <= 2024-05-01?
2. Definitionstreue: RV_fwd30 mit Konstante 365 und 30 Folgetagen, S1/S2/S3 wie H-27; IV-Konvention (23:00-Kerze);
   UTC-Tagesgrenzen der 1-min-Kerzen; Behandlung unvollstaendiger Tage (nie fuellen); Duplikate.
3. HF-RV-Schaetzer: sind 1/5/15/30-min, subsample-gemittelt und close-to-close korrekt gebaut? Reproduziert close-to-close
   aus dem letzten 1-min-close die H-27-Zahl 18,60 (Abweichung erklaert)? kappa-Mass wie Review B-1? Niveau-Verzerrung
   (rms RV HF gegen cc) benannt -> braucht ein eigenes J?
4. c-Regel P-3: korrekt angewandt (max(1, max{...}), 180-Regel bei ACF(120) > 0,10)? Stationaerer Bootstrap Seed 27?
   Konsens-c nur als Bericht?
5. Fensterlaenge/Power: `power_p1` benutzt? SE_W = SD*sqrt(c/335); bindende SE = max(SE_nuis, SE_null) mit SE_null aus
   H-27; Tage je Fenster fuer C10 nach P-1 und A3-Praxis; Kalenderdaten ab 2026-07-01 korrekt (zwei disjunkte Fenster,
   RV-Ziel +30 Tage)? Ist die Aussage "SD 15,1 bestaetigt/nicht bestaetigt" sauber (ohne Mittel) hergeleitet?
6. Gabelungen: ist die Wahl der RV-Variante als Ermessen mit Richtung ausgewiesen, VOR jeder Zahl begruendbar (Kriterien
   kappa/Mikrostruktur/Definitionsgleichheit), und wird klar, dass sie nur fuer eine NEUE Hypothese gilt (Etikett
   "beschlossen nach Kenntnis GL-034", kein Torpfosten fuer H-27)?
7. A2-Zensus: Instrument-Parsing (Future/Option/Perpetual), Verfallsklassifikation geprueft statt angenommen? Zeitlage
   relativ 08:00 UTC korrekt (Sekunden, Zeitzone)? Ereigniszahlen je Jahr/Menge nachvollziehbar? Keine Preise/Renditen?
   sigma30 nur als offene Vorlage?
8. Vollstaendigkeit/Belege: jede Zahl mit [S:]/[fj:]-Quelle; UNBELEGT markiert; ETH nur Bericht; deterministisch?

## Ausgabe
`REVIEW_HFRV.md`: Gesamturteil (ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO), Befunde B-1.. mit Schwere, Nachrechnung
(Tabelle Agent vs. Review), konkrete Auflagen (was der Orchestrator vor einem DEC-Nachtrag aendern muss), was NICHT folgt.
Kurzfassung <= 10 Zeilen: Urteil, Top-3-Befunde, Nachrechnungs-Abweichungen, Auflagen. KEIN Mittel, kein Vorzeichen.
