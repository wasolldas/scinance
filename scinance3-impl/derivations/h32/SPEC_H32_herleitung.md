# Herleitungs-Auftrag H-32: Zweistufen-Design fuer den beta-neutralen Querschnitts-IC (Pilot auf der Vorperiode, Test auf W1/W2)

Du bist der Herleitungs-Agent (Gate-Design, Power, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert, nicht du. Repo `/home/user/scinance`, Python mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte nur
unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h32_herleitung/` (anlegen),
Volltexte unter `scinance3-impl/state/herleitung_h32/` (anlegen). Kurzfassung an den Orchestrator hoechstens 10 Zeilen.
Nichts committen, nichts pushen. Keine Zugangsdaten/Hostnamen/Modellnamen. Doku Deutsch (ASCII-safe), Code Englisch.

## Ausgangslage (bindend, lesen)
- `scinance3-impl/CLAUDE.md` (inkl. DEC-94-Absatz), `UEBERGABE_2026-10-12.md` (alle Nachtraege), `STAND_2026-10-18.md`.
- `state/decisions.md`: DEC-51/52/53/58 (E2!), -67, -72, -74..-78, -85..-98 (mit allen Nachtraegen; DEC-98 Nachtrag 2 =
  PDF-Belege); `state/gate_log.md` GL-032..034; `state/hypothesis_registry.md` (Drittfassung H-28..H-30, Vermerke H-31/H-27).
- Akten: `state/herleitung_h28_h30_v3/` (Design-Vorbild), `state/registered/h28_h30_v3.yaml` (Schema), `state/runs/
  wp13a_20261012_v5e/wp13a_prelaunch.json` (Nuisance: fm_neutral_8w factor_sd je Fenster/Kalibrierung/Variante,
  e_floor, w_judged, Kalibrierung, Drift-Quantile) - NICHT die Siegeldateien; `state/PROGRAMM_BILANZ_2026-10-18.md` +
  Review; `state/BELEGE_AUS_PDF_2026-10-20.md` (Prior-Band, Universums-Abhaengigkeit, Ficura-Warnung).
- Code: `src/bybit_edge/research/wp13_xsec/` (run.py, prelaunch.py, gates.py, ic.py, nulls.py, positive_control.py),
  `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/Zuordnungszahl), `scripts/wp13_xsec.py`.

## Harte Regeln
1. **Keine Datenrechnung in dieser Herleitung.** Weder das Pilot-Fenster noch W1/W2 werden geoeffnet; keine reale IC,
   kein Outcome. Alle Power-Zahlen nur aus den Nuisance-Werten der Akte (v5e-JSON) mit `power_p1`. Blind-Siegel
   DEC-96 E3 (ab 2026-07-01) gilt; W1/W2 sind fuer A3 blind (keine reale IC je berechnet - pruefe das an der Akte und
   fuehre die C.17-Liste der gesehenen Groessen: Beta-Kalibrierungs-IC, Lag-Profil, Survivorship-Differenz, Streuungen,
   Literatur-Band). NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder
   `ic_series_*_UNION_REAL.csv` heissen. Nie unter `data/harvest` schreiben.
2. Voraussetzung der Registrierung ist eine noch nicht beschlossene Programmregel **DEC-99** (REZENZ C.18 fuer 3.0 als
   notwendige Bedingung: das juengste Fenster muss bestehen; aeltere Daten duerfen vorab registriert als Pilot-
   Schaetzfenster oder als zweites Urteilsfenster dienen; Richtung Testbarkeit; Etikett "beschlossen nach GL-032..034";
   Fehlerraten und Power-Ziel unveraendert). Schlage den Wortlaut vor; entscheiden tut der Orchestrator nach
   Nutzer-Zustimmung.
3. Jede Ermessensentscheidung mit Richtung (Testbarkeit/Strenge) ausweisen (Gabelungsmuster, DEC-93 H-1). Jede Zahl
   mit Quelle; UNBELEGT blockiert.

## Design, das herzuleiten ist (Zweistufen-Design, alles VOR dem Oeffnen fixiert)
**Stufe P (Pilot-Schaetzfenster):** Formationswochen 2022-04-04..2024-06-24 (K_t >= 117; davor zu klein - belegen aus
WP-7/A1-Akte), Union-Panel, Statistik = beta-neutraler Wochen-Rang-IC (`fm_neutral_8w`, exakt wie in der Drittfassung
beschrieben) fuer die Varianten mom1, mom2, mom4, rev_gap (H-30-Varianten: begruende Ausschluss oder Aufnahme - H-30 war
strukturell GL-012). Ausgabe: Mittel-IC, SE nach P-1 (SD(IC_t)/sqrt(W) mit stationaerem Bootstrap), 80-%-Band, je Variante.
**Vorab fixierte Uebergaberegel P -> Test (eine Regel, nicht nach dem Sehen waehlbar):** Variante geht in den Test, wenn
(i) Vorzeichen in registrierter Richtung UND (ii) Pilot-Punkt >= MDE80 des schwaecheren Testfensters (aus Nuisance:
W1 stress fm8 SD 0,0511 -> MDE80 ~0,0176; rev_gap 0,0513; W2 0,0425/0,0433) UND (iii) t >= 2 im Pilot. Sonst ist die
Variante GL-012 mit GEMESSENEM Grund. Prior fuer die Zuordnung = Pilot-Punkt (alternativ: untere 80-%-Grenze - beide
Lesarten mit Richtung ausweisen, eine empfehlen). Das Pilot-Fenster ist danach verbraucht (nicht urteilstragend, Etikett).
**Stufe T (Test):** W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30, C.10 hart oder DEC-52 nach `power_p1.assign_regime`
mit dem Pilot-Prior; Schwelle = kritischer Wert (DEC-94); SE-Regel P-1 (4); Doppelausweis A3-Praxis; Selektions-K vorab
(K = Zahl der Pilot-Varianten, BH-Nenner fest, Varianten ohne Uebergabe mit p = 1); faktorerhaltende Null und Kalibrierung
je Fenster wie Drittfassung (DEC-85/87), eingefrorene Konstanten; Bounce-/Liquiditaets-/Survivorship-Etiketten; DEC-53-
Artefakte; Positivkontrolle in Produktionskonfiguration VOR dem Test mit vorab fixierter Bestehensregel, die die
Power-Annahme prueft (DEC-89/91-Lehre, DEC-94 (5) 10-%-Regel).
**Power vorab (aus Nuisance, ohne Pilot):** Tabelle Prior-Gitter 0,010/0,015/0,020/0,025/0,033 -> Fenster-Power W1/W2,
Regime, MDE80; Pilot-Praezision (SE ~0,0047 bei 117 Wochen, aus v5e-SD); Wahrscheinlichkeit, dass der Pilot eine
Variante uebergibt, als Funktion des wahren IC (Operationscharakteristik der Uebergaberegel) - rein analytisch.
**Universums-Frage (aus den PDF-Belegen):** Momentum-Vorzeichen haengt am Universum (breit ~0/negativ, Large-and-Liquid
positiv). Pruefe, ob eine vorab fixierte Universums-Variante (z. B. Umsatz-Dezile >= 3 oder Top-N nach Turnover,
PIT, look-ahead-frei) als eigene Variante mit eigenem K sinnvoll ist - Richtung ausweisen; keine Wahl nach dem Pilot.
**Was NICHT folgt:** kein Verdikt; keine Registrierung; der Pilot wird erst nach DEC-99 + Registrierung + Review gebaut.

## Dateien
`ENTSCHEIDUNGSVORLAGEN.md` (inkl. DEC-99-Wortlaut, Uebergaberegel-Lesarten, Universum, K, H-30), `ERSTFASSUNG_H32_entwurf.md`
(zwoelf Pflichtzeilen, Gate-Text woertlich, DEC-39-Trio, Positivkontroll-Regel, Etiketten C.17, Bauliste: Pilot-Modus im
Code, YAML-Schema-Felder `pilot_window`, `handover_rule`), `power_h32.json` (alle Zahlen, deterministisch).

## Rueckmeldung
Hoechstens 10 Zeilen: Power-Tabelle in Kurzform, Uebergaberegel, K, offene Vorlagen, Bauaufwand, UNBELEGT-Punkte.
