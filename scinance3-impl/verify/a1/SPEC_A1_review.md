# Review-Auftrag A1 (H-31): adversarische Pruefung der Herleitung

Du bist der zweite, adversarische Gutachter im Forschungsprogramm Scinance 3.0. Du suchst Fehler, die einen
falschen Befund erzeugen wuerden - in beide Richtungen (A1 faelschlich testbar ODER faelschlich nicht testbar).
Repo `/home/user/scinance`; Python mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte nur unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_review/`.

## Gegenstand
- Auftrag an die Herleitung: `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/SPEC_A1_herleitung.md`
  (seine harten Regeln gelten fuer dich genauso: Ergebnisblindheit ab 2024-07-01, versiegelte Dateien nie oeffnen,
  nichts committen/pushen, nie unter `data/harvest` schreiben, keine Zugangsdaten/Hostnamen, keine Modellnamen).
- Ergebnis: alles unter `scinance3-impl/state/herleitung_a1/` und die Skripte unter
  `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung/`.
- Massstab: `scinance3-impl/CLAUDE.md`, PRD 5.1/3.3, DEC-51/52/53/58/59/67/70/84/91/92, GL-032.

## Pruefpunkte (mindestens)
1. Ergebnisblindheit eingehalten? (Code lesen: wird irgendwo eine Folgewochen-Groesse ab 2024-07-01 berechnet?)
2. Funding-Buchhaltung: I je Intervallklasse, Umschalt-Tage, Sonderpaare, Wochen-SUMME, Vorzeichen Long/Short-Bein.
3. SE des registrierten Tests: enthaelt sie faktorbedingte Streuung (Beta-Fehlanpassung D1 vs. Universum,
   Momentum-Ladung) und Autokorrelation? Ist die Power mit genau dieser SE gerechnet (A3-Lehre DEC-91)?
4. A-priori-Effekt: Ist `prem_prior` sauber hergeleitet (Persistenz, theta mit Quelle oder als Gitter gekennzeichnet)?
   Wird das Funding-Bein als Effekt verkauft, obwohl die Null exakte Kompensation sagt?
5. Zuordnungsregel PRD 5.1 korrekt angewandt (P_fenster, C.10/DEC-52, GL-012-Pruefung)?
6. Rechne mindestens die drei entscheidenden Zahlen unabhaengig nach (eigener Code, gleiche Daten).
7. Falls Stufe 2: Positivkontrolle prueft die Power-Annahme in Produktionskonfiguration? DEC-39-Trio vollstaendig?
   Zwoelf Pflichtzeilen vollstaendig und belegt? Selektions-K begruendet?

## Ergebnis
Datei `scinance3-impl/state/herleitung_a1/REVIEW_A1.md`: Urteil ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO, Befunde
nummeriert mit Schweregrad, je Befund Beleg (Datei, Zeile, nachgerechnete Zahl). An den Orchestrator hoechstens
10 Zeilen.
