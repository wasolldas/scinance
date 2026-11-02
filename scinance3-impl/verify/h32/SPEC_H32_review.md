# Review-Auftrag H-32 (adversarisch): Zweistufen-Design Pilot/Test fuer den beta-neutralen Querschnitts-IC

Du bist der zweite, adversarische Gutachter im Forschungsprogramm Scinance 3.0. Gegenstand: alles unter
`/home/user/scinance/scinance3-impl/state/herleitung_h32/` (ENTSCHEIDUNGSVORLAGEN.md, ERSTFASSUNG_H32_entwurf.md,
power_h32.json) und die Skripte unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/
h32_herleitung/`. Auftrag der Herleitung: `.../scratchpad/SPEC_H32_herleitung.md` (seine harten Regeln gelten fuer dich:
KEINE Datenrechnung, weder Pilot-Fenster noch W1/W2 oeffnen, Siegeldateien nie oeffnen, nur Nuisance aus
`state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json`, Blind-Siegel ab 2026-07-01, nichts committen/pushen, keine
Zugangsdaten/Hostnamen/Modellnamen). Eigene Skripte nur unter `.../scratchpad/h32_review/`. Massstab: CLAUDE.md, PRD 3.3/5.3,
DEC-51/52/53/58 E2/85/87/89/91-98 (inkl. Nachtraege), GL-032..034, `power_p1.py`, Drittfassung H-28..H-30 (Registry, YAML).

## Pruefpunkte (Fehler in BEIDE Richtungen)
1. **Power-Zahlen nachrechnen** (eigener Code + power_p1): MDE80 je Variante/Fenster mit Varianzfaktor c und
   mechanischem Null-Mittel - woher stammt c (die Herleitung sagt, die v5e-Null rechne nur 45 Wochen und das c_hat
   der Bilanz sei ein Artefakt - pruefen!), woher das Null-Mittel; Pilot-SE 0,0071 (K 120..339) und Fensterwahl
   2022-04-18..2024-06-17 (W_P 114; warum nicht frueher/spaeter; Outcome-Woche darf nicht in W1 ragen).
2. **Uebergaberegel U:** ist sie vorab eindeutig, monoton, und laesst sie keine Wahl nach dem Sehen? Operations-
   charakteristik (Uebergabe-Wahrscheinlichkeit als Funktion des wahren IC) nachrechnen, inkl. "bei IC 0 hoechstens
   0,3 %" und "im Literaturband 0,4..14 %". Lesart A (Pilot-Punkt) vs. B (untere 80-%-Grenze): Richtung und
   Fehlerfolgen; ist der Pilot-Punkt als Prior fuer die Zuordnung ein Optimismus-Bias (Winner's curse ueber 4
   Varianten)? Wenn ja, welche Korrektur ist vorab fixierbar?
3. **K = 4, BH, Ueber-Familie F-WEEK, Selektionsdecke** (Hinweis der Herleitung: mean_of_max nicht vorzeichen-
   bereinigt) - korrekt und konsistent mit DEC-51 (4)/DEC-94 (7)?
4. **Neue Befunde pruefen:** (a) W2-Endwoche verletzt das Blind-Siegel -> W2 bis 2026-06-28 (w 50)? (b) Sektorwelt der
   Positivkontrolle erhoeht die fm8-SD um 17,6 % und reisst die 10-%-Regel DEC-94 (5) - ist die Positivkontroll-Welt
   oder die Regel falsch, und welche vorab fixierbare Bestehensregel ist richtig? (c) nominale Injektion wirkt nur zu
   75 % - Folge fuer die Positivkontrolle? (d) c_hat-Artefakt der Bilanz - Folge fuer DEC-98/Bilanz-Zahlen?
5. **Ergebnisblindheit:** W1/W2 fuer fm8 wirklich blind (Akte pruefen: v5e, Drittfassung, Positivkontrolle, WP-7-Rohserie
   versiegelt, Survivorship-Differenz +0,0033 gesehen)? C.17-Liste vollstaendig? Ist das Pilot-Fenster selbst noch
   blind (A1-/H-27-Nuisance-Rechnungen auf 2022-04..2024-05 haben Streuungen gesehen - reicht das?)?
6. **DEC-99-Wortlaut und Gabelungen:** ist der vorgeschlagene Regeltext programmweit, prospektiv, ehrlich etikettiert
   (Richtung Testbarkeit, nach GL-032..034), ohne Fehlerraten-/Power-Aenderung? Zaehlung der Gabelungen (4/9/2)
   nachvollziehbar? Gibt es eine versteckte Gabelung Richtung Testbarkeit (z. B. Fensterende, K, Universum U0)?
7. **Zwoelf Pflichtzeilen, Gate-Text, DEC-39-Trio, Bauliste:** vollstaendig, registrierbar, Aufwand plausibel?

## Ergebnis
`scinance3-impl/state/herleitung_h32/REVIEW_H32.md`: Urteil ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO, nummerierte
Befunde mit Schweregrad und Beleg (Datei, Zeile, nachgerechnete Zahl), Empfehlung an den Orchestrator (welche EV-Lesart,
welcher DEC-99-Text, was vor der Registrierung zu aendern ist). Kurzfassung hoechstens 10 Zeilen. Deutsch, ASCII-safe.
