# Auftrag (adversarischer Review): Pruefung der vier Analysen der PRD-Gesamtanalyse
Lies zuerst state/prd_analyse_2026-11-01/REGELN_UND_LESELISTE.md (Regeln gelten). Gegenstand: die vier Analysen unter
state/prd_analyse_2026-11-01/: KRITIK_PRD.md, EDGE_INVENTUR.md, KONZEPT_UND_FORSCHUNGSFELDER.md, ARCHITEKTUR_AUTOMATION.md
(dazu als Hilfslisten FAKTENBLATT_STATUS.md und LISTE_DEC_GL.md). Du bist der Gate-Auditor (Richtung Strenge) und
pruefst gegen die Primaerquellen der Leseliste (PRD, Kompendium, decisions, Bilanz, Dateninventar), nicht gegen die
Analysen untereinander.
Pruefpunkte je Analyse:
1. Faktentreue: jede Fundstelle stichprobenartig (mindestens 10 je Analyse) gegen die Quelle; Fehlzitate, Zahlendreher,
   erfundene Regeln oder Daten (z. B. behauptete Datenstroeme, die das Inventar nicht fuehrt).
2. Ueberdehnung: Behauptungen ohne Beleg, Vermutungen als Fakten, Power-Ueberschlaege mit falschen Eingaben
   (nachrechnen mit Python), Vorschlaege, die gegen Kompendium D verstossen, ohne das zu sagen.
3. Richtungs-Etiketten: ist bei jedem Vorschlag korrekt benannt, ob er Lockerung/Testbarkeit oder Strenge ist, und ob
   er Programmfrage (Nutzer) oder Orchestrator-Sache ist? Wo fehlt das Etikett?
4. Siegel/Blindheit: schlaegt eine Analyse etwas vor, das die Blindheit von W1/W2 oder der Blindperiode ab 2026-07-01
   verletzen wuerde, ohne das offenzulegen? Wird irgendwo nahegelegt, versiegelte Dateien zu oeffnen?
5. Widersprueche zwischen den vier Analysen (z. B. unterschiedliche Power-Zahlen fuer dasselbe Feld) - benennen,
   mit eigener Nachrechnung, welche richtig ist.
6. Luecken: Was fehlt allen vier (eine wichtige Fehlerquelle, ein Datenstrom, eine Regel), das der Orchestrator in der
   Synthese ergaenzen muss?
Ausgabe: state/prd_analyse_2026-11-01/REVIEW_PRD_ANALYSE.md mit: 0 Urteil je Analyse (ZUSTIMMUNG / MIT AUFLAGEN / VETO gegen
Uebernahme einzelner Punkte), 1 Befunde B-n (Analyse, Stelle, Befund, Beleg, Folge, Auflage), 2 Nachrechnungstabelle,
3 Widerspruchsliste, 4 Luecken, 5 Was NICHT folgt. Kurzfassung <= 12 Zeilen. Keine Modellnamen, kein Hostname, ASCII.
