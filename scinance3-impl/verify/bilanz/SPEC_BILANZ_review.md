# Review-Auftrag P-2 (adversarisch): Programm-Bilanz / Power-Zensus 2026-10-18

Du bist der zweite, adversarische Gutachter im Forschungsprogramm Scinance 3.0. Gegenstand:
`/home/user/scinance/scinance3-impl/state/PROGRAMM_BILANZ_2026-10-18.md`, `.../state/programm_bilanz.json`, Skripte
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/bilanz/`. Auftrag der Herleitung:
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/SPEC_BILANZ_power_zensus.md`
(seine harten Regeln gelten fuer dich genauso: keine Outcome-Rechnung, nur Nuisance aus den Akten, Siegeldateien und
WP-10(A)/(A2)-IV-RV-Dateien nie oeffnen, Blind-Siegel DEC-96 E3, nichts committen/pushen, keine Zugangsdaten/Hostnamen/
Modellnamen). Eigene Skripte nur unter `.../scratchpad/bilanz_review/`. Massstab: `scinance3-impl/CLAUDE.md`, PRD,
DEC-51/52/58/59/61/67/73/92-97, `power_p1.py`, 2.0-Registry H-26 (`scinance2-impl/state/hypothesis_registry.md`).

## Pruefpunkte (Fehler in BEIDE Richtungen; eine Bilanz, die zu pessimistisch ist, waere genauso falsch)
1. **Arithmetik:** Dauer je Fenster und Volldatum fuer H-27 (672 Tage, 2030-04-04), A3 mom1 stress (119 Wochen,
   2031-05-11; measured 57 Wochen), A1 (theta 1: 85 Wochen; 0,77: 2032-04), A4 (2029-06-29), DEC-52-Mehrbedarf
   (+9,5 %), A3-Praxis-Faktor 1,79, Ein-Fenster-Vergleich (+7,7 %) - mit eigenem Code und `power_p1`. Welche
   Nuisance ging je Zeile ein (bindend stress/measured, c-Regel)? Stimmen Startdaten und Kalenderrechnung?
2. **Hebel-Rechnungen:** mehr Symbole (-14 %, Faktorvarianz 86 %), zweite Boerse ~0, fm8 als Primaerstatistik
   (-81 %; Prior UNBELEGT - ist die Zahl ueberhaupt belastbar oder nur Illustration?), HF-RV (-34 %, SD 15,1
   UNBELEGT), BTC+ETH (-4..-9 %), nicht ueberlappende Monatsziele (+8 % - plausibel? Ueberlappung erhoeht
   die Autokorrelation, aber die Monatsvariante hat 12x weniger Punkte; rechne nach), A1-Hedge (-7 %).
3. **Fehlende Hebel:** Gibt es einen Weg zu Power 0,80, den die Bilanz uebersieht und der KEINE Regel-Lockerung und
   KEINE Outcome-Kenntnis braucht? (z. B. laengere Vorperiode fuer die Nuisance, andere Cluster-Einheit, Ereignisse mit
   vielen Einheiten, Kombination von Boersen fuer die VRP, Varianz-Swap-Replikation statt IV-RV, ...). Benenne auch
   Wege, die nur scheinbar helfen (Datenschnueffeln).
4. **Teil B Datenbedarf:** vollstaendig, richtig priorisiert, als Data-Harvest-Auftrag umsetzbar (Strom, Symbole,
   Aufloesung, Zeitraum, Zweck, Volumen)? Fehlt etwas (z. B. Binance-DVOL-Aequivalent, Options-Quotes, Delisting-
   Register)? Ist "irreversibel" richtig gesetzt (was heute nicht aufgezeichnet wird, ist fuer blinde Fenster
   verloren)?
5. **Teil C Optionen:** neutral, vollstaendig, jede mit Richtung, Kosten, Falsch-Positiv-Rate wo relevant? Ist die
   Aussage "blinde Fenster sind ein Einmal-Gut" richtig und ihre Folge fuer H-26 (2.0, gegen done_days registriert,
   W2 wuerde ab 2026-07-01 im Blindbereich liegen) korrekt dargestellt? Welche Reihenfolge-Optionen gibt es fuer
   H-26 vs. H-27-Nachfolger, und was ist die reversibelste?
6. **Ehrlichkeit:** Werden Konsequenzen weggelassen, die dem Programm unangenehm sind (z. B. dass 3.0 bei
   Recording-first bis 2030 keine Alpha-Aussage liefert)? Werden UNBELEGT-Punkte als solche gefuehrt?

## Ergebnis
`scinance3-impl/state/REVIEW_PROGRAMM_BILANZ_2026-10-18.md`: Urteil ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO,
nummerierte Befunde mit Schweregrad und Beleg (Datei, Zeile, nachgerechnete Zahl), eine Empfehlung an den
Orchestrator, wie die Entscheidungsvorlage an den Nutzer gehen soll. Kurzfassung hoechstens 10 Zeilen. Deutsch, ASCII-safe.
