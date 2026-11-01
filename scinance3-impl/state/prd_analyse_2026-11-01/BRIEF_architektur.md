# Auftrag (Herleitung): Architektur einer vollautomatischen Analyseinstitution aus der Sandbox
Lies zuerst state/prd_analyse_2026-11-01/REGELN_UND_LESELISTE.md (Regeln gelten), dann Leseliste 1-2, 4-7, 9-10 (CLAUDE.md,
UEBERGABE mit Arbeitsweise, decisions zu Prozessregeln, A2-/H-32-Akten als Beispiele fuer den heutigen Ablauf, DATA_ACCESS,
Code-Inventar, Dateninventar). Ausgabe: state/prd_analyse_2026-11-01/ARCHITEKTUR_AUTOMATION.md.

Ziel des Nutzers: eine vollautomatische Analyseinstitution, die aus der Sandbox per Schluessel auf Data-Harvest zugreift
und Hypothesen eigenstaendig entwickelt, prueft und dokumentiert, mit so wenig menschlichem Eingreifen wie moeglich.
1. Ist-Zustand: Was ist heute automatisiert (Client, Katalog, power_p1, h32-Pipeline mit Pins/Waechtern, Registry-
   Dokumente, Agentenrollen), was laeuft ueber den Orchestrator von Hand (Spezifikationen, Abnahmen, Nachrechnungen,
   DEC-Texte, Commits), was braucht den Nutzer (Programmfragen, Datenauftraege weiterleiten, Volltexte)? Zeitbedarf und
   Tokenkosten je Hypothese (schaetze aus den Akten: H-32, H-33, A2).
2. Soll-Architektur in Bausteinen: (a) Datenzugang und Cache (Siegel-Regeln als Code: Datumsgrenzen, Klassen, Waechter,
   Kanal-Scan gegen Varianzzerlegung), (b) Hypothesen-Generator (Quellen: Literatur-Suche in der Sandbox mit ihren
   Grenzen, systematische Zensus-Screens mit Mehrfachtest-Budget, Mechanismus-Checkliste Zahler/Horizont/Wand),
   (c) maschinenlesbare Vorregistrierung (YAML-Schema mit allen Pflichtzeilen, automatische Power-Vorpruefung, Fenster-
   Zuweisung aus einem Fensterregister), (d) Fensterregister/Lockbox (welche Daten fuer welche Statistikfamilie noch
   blind sind; rollierende Freigabe; Verbuchung von K und FDR ueber die ganze Institution), (e) Ausfuehrung (Scheduler/
   Trigger, Laufzeitgrenzen der Sandbox, Determinismus, Artefakte DEC-53), (f) Pruefschleifen (adversarischer Reviewer,
   Positivkontrolle, Orchestrator-Nachrechnung als Code statt Hand), (g) Dokumentation (append-only Ledger, Registry,
   Gate-Log, Nutzerbericht), (h) menschliche Eingriffspunkte (nur: Programmrichtung, Geld, Datenauftraege, Recht).
3. Fenster-Politik fuer die Institution: Vorschlag, wie Daten in Explorations-/Validierungs-/Konfirmationszonen
   aufgeteilt und rollierend freigegeben werden, mit Verbuchung aller Tests (auch der verworfenen), damit nicht jede
   Hypothese Jahre wartet; Vergleich zur heutigen Praxis (Einmal-Gut, REZENZ, Blind-Siegel) nach Strenge und Wartezeit.
4. Fehlerbilder und Schutz: Agenten-p-Hacking (Gabelungen nach Kenntnis), Siegel-Lecks (B-2-Typ), Drift der
   Spezifikationen, Kosten-Explosion, stille Defaults, Determinismusverlust, Scratch-Verlust (geschehen am 2026-10-31).
5. Fahrplan: was zuerst gebaut wird (Reihenfolge, Aufwand in Agenten-Stunden/Tokens grob), welche heutigen Regeln als
   Code formalisiert werden, welche Entscheidungen der Nutzer einmalig treffen muss, und was in den ersten 90 Tagen
   messbar sein sollte.
Form: Abschnitte 1-5, Tabellen fuer Bausteine und Fahrplan, "Was NICHT folgt". Kurzfassung <= 12 Zeilen.
