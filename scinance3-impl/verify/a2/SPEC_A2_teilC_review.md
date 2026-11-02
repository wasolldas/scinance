# Auftrag: adversarischer Review der A2-Vorarbeit Teil C (Null-Simulation, bindende SE, Funding-Intervall W2, Pilot-Uebergaberegel)

Rolle: Gate-Auditor (Richtung Strenge) fuer den Orchestrator von Scinance 3.0. Unabhaengig von der Herleitung: deren
Skripte unter `/home/user/scinance_work/a2_teilC/` darfst du lesen, aber **nicht importieren oder kopieren**; jede
Nachrechnung mit eigenem Code unter `/home/user/scinance_work/a2_teilC_review/`. Nichts committen, kein Verdikt,
nichts registrieren. Volltext nach `/home/user/scinance/scinance3-impl/state/herleitung_a2/REVIEW_A2_TEILC.md`
(ASCII, Deutsch, keine Modellnamen); Kurzfassung (<= 10 Zeilen) an den Orchestrator.

## Gegenstand
`/home/user/scinance/scinance3-impl/state/herleitung_a2/`: NULL_SIMULATION_A2.md, PILOT_ROUTE_A2.md, a2_teilC.json
(sha256 pruefen und nennen). Auftrag der Herleitung: `/home/user/scinance_work/drafts/SPEC_A2_teilC.md`.
Massstab: DEC-103 (bindend), DEC-94 (3)(5)(6), DEC-99 (2)(3)(5)(6), DEC-101 Entscheidung 7 (U-4), PRD 5.2, DEC-98 N5/N7,
Fassung 2 der Teile A/B und REVIEW_A2_VORARBEIT.md (alle unter `state/`), `power_p1.py`.

## Daten (nur diese; kein Harvest-Client, keine Siegeldateien)
`/home/user/scinance_work/hf_data/raw/` (Hashes in `EXTRACT_LOG.json`): 1-min BTCUSDT/ETHUSDT 2021-03-24..2024-05-31,
Settlement-Kalender (4 Felder, <= 2026-06-30), Funding-Zeitstempel BTC/ETH W2.

## Regeln (bindend)
Kein Mittel, kein Median, kein Vorzeichen irgendeiner Verfallstag-Rendite und **nie der Kontrast mit den realen Labels**
- auch nicht zur Probe. Renditen nur Vorperiode; eigener Datums-Assert vor jedem Preis. Nur Streuung, Quantile der
permutierten Null, Zaehlungen.

## Pruefpunkte (jeder mit Status BESTAETIGT / ABWEICHUNG / UNBELEGT, Beleg, Richtung)
1. **Siegel-Treue zuerst:** Schluessel-/Pfad-Scan der JSON und Zwischen-Dateien, Skript-Lesung (jede Stelle, an der ein
   Mittel gebildet wird; wird es ausgegeben?), Waechter gegen den realen Label-Vektor wirklich wirksam (Test lesen, selbst
   provozieren mit einem Kopie-Skript, das NICHT den realen Kontrast berechnet, sondern nur prueft, ob der Waechter
   greift), Datumsgrenzen, keine Preisfelder der Settlements.
2. **Null-Definition** gegen DEC-103 E4: genau ein Freitags-Label je ISO-Woche, Mo-Do ohne Futures-Tage, Wochenende
   nirgends, Ausreisser-Tage raus, Anzahl erhalten; ist die Permutation unter der Null austauschbar (gleiche Tageszeit,
   gleicher Funding-Termin)? Welche Null gilt fuer P3fix/P3all und ist das begruendet und mit Richtung versehen?
3. **Nachrechnung:** Null-SD, 95-/99-%-Quantil je Fenster und gepoolt mit eigenem Code und anderem Seed (Toleranz
   Monte-Carlo-Rauschen, ausweisen); Vergleich mit der analytischen SE (7,34 bp D_i; Teil B); bindende SE = max; MDE80
   Einzel/Produkt mit power_p1; Funding-Zaehlung W2 (Tage mit 8h-Takt, Anteil Freitage/Mo-Do mit 08:00-Funding).
4. **Pilot-Uebergaberegel:** mechanisch und vorab fixierbar? Jede Groesse definiert, bevor der Pilot geoeffnet wird?
   Schwelle deckt die Gate-Bedingungen (Vorzeichen, Konjunktion gegen drei Placebos, Produkt-Zuordnung, skalierte Null
   analog U-4)? Fehlerraten der Zwei-Stufen-Regel korrekt (Pilot-Alpha, Gesamtrate)? Pilot-Power gegen das Prior-Gitter
   plausibel? Ist irgendwo eine Richtungswahl nach Kenntnis der Nuisance versteckt (Gabelungsmuster DEC-93 H-1)?
   Verbrauch nach DEC-99 (5) korrekt beschrieben? Positivkontroll-Design (Injektion, Kriterium) vollstaendig?
5. **Vollstaendigkeit/Belege:** UNBELEGTES benannt (V-5b, OI-Proportionalitaet, CME [sek], Negativ-Panel-Daten)?
   Richtung (Lockerung) als Etikett ausformuliert? Gabelungen mit Richtung? Rundung einheitlich? Determinismus
   (zwei Laeufe bitgleich, sha256)?

## Form
Abschnitte: 0 Urteil (ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO, mit Grund), 1 Pruefpunkte-Tabelle, 2 Befunde
(B-n mit Schwere, Befund, Richtung, Auflage), 3 Nachrechnungstabelle (eigene Zahlen gegen Herleitung), 4 Auflagen vor
einem DEC-Nachtrag, 5 Was NICHT folgt, 6 Reproduktion (Skripte, Seeds, sha256). Lies NACHRECHNUNG_ORCHESTRATOR.md nicht,
bevor du fertig bist (Unabhaengigkeit).
