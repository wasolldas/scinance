# Review-Auftrag H-27 (adversarisch): Befund "GL-012 vor der Registrierung" fuer W3/W4

Du bist der zweite, adversarische Gutachter im Forschungsprogramm Scinance 3.0. Gegenstand: alles unter
`/home/user/scinance/scinance3-impl/state/herleitung_h27/` und die Skripte unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h27_herleitung/`; Auftrag der
Herleitung: `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/SPEC_H27_herleitung.md`
(inkl. Abschnitt FORTSETZUNG). Massstab: `scinance3-impl/CLAUDE.md`, DEC-51/52/94/95/96 (mit Nachtraegen), GL-032/033,
`src/bybit_edge/research/power_p1.py`. Eigene Skripte nur unter `.../scratchpad/h27_review/`.

## Harte Regeln (wie die Herleitung)
Keine RV von BTC/ETH ab 2024-06-01, keine DVOL-Niveau-/Streuungsstatistik ab 2024-07-01 (Blind-Siegel DEC-96 E3 ab
2026-07-01 zusaetzlich), WP-10(A2)-IV-RV-Dateien und Siegeldateien nie oeffnen, kein Praemienmittel ausgeben oder
speichern, Harvest-Bucket nie listen (nur `hd.catalog()`/`hd.load()`/`hd.gaps()`), nichts committen/pushen, keine
Zugangsdaten/Hostnamen/Modellnamen in Dateien. Harvest-Client: `.../scratchpad/harvest_client/` (`DATA_ACCESS.md`).

## Pruefpunkte - Fehler in BEIDE Richtungen suchen
1. Nuisance unabhaengig nachrechnen (eigener Code): SD der taeglichen Praemie S1 (BTC), Varianzfaktor c (Batch-Means vs.
   Bartlett vs. Theorie fuer ueberlappende 30-Tage-Ziele ~h), Jensen-Verzerrung. Ist c = 28,2 richtig oder zu
   konservativ/zu optimistisch? Wird c an der TESTSTATISTIK gemessen (DEC-94 (4))?
2. Prior 9,47 Vol-Punkte aus BVRP 0,14 (Varianzeinheit) - Umrechnung nachpruefen; Band 7,0..13,7 plausibel?
3. Power/Zuordnung mit `power_p1` nachrechnen (L = 6/9/12, C10/DEC52/GL012, Doppelausweis A3-Praxis).
4. Gibt es eine im Rahmen von DEC-96 zulaessige, VORAB begruendbare Designwahl, die die Testbarkeit materiell aendert
   (z. B. nicht ueberlappende Monatsstatistik, anderer RV-Schaetzer, BTC+ETH-Aggregation)? Bewerte sie, aber beachte:
   eine Wahl NACH Kenntnis dieser Feasibility zugunsten der Testbarkeit ist ein Torpfosten (A1-Lehre, DEC-93 H-1).
5. Ergebnisblindheit: wurde irgendwo gegen die Regeln verstossen (Code lesen)? Offenlegungen in `KONTAMINATION.md`
   vollstaendig?
6. Ist die Schlussfolgerung "GL-012 vor der Registrierung, kein Urteil ueber die VRP" korrekt formuliert?

## Ergebnis
`scinance3-impl/state/herleitung_h27/REVIEW_H27.md`: Urteil ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO, nummerierte
Befunde mit Schweregrad und Beleg, nachgerechnete Zahlen. An den Orchestrator hoechstens 10 Zeilen. Deutsch, ASCII-safe.
