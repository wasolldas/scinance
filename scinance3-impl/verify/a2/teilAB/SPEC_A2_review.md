# Review-Auftrag (adversarisch, kurz): A2-Vorarbeit - Placebo-Design und sigma30-Nuisance

Du bist der adversarische Reviewer (Gate-Auditor-Rolle, Richtung Strenge) im Forschungsprogramm Scinance 3.0.
Repo `/home/user/scinance`, `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte NUR unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a2_review/`. Volltext
`/home/user/scinance/scinance3-impl/state/herleitung_a2/REVIEW_A2_VORARBEIT.md`. Kurzfassung <= 10 Zeilen. Nichts committen.
Keine Zugangsdaten/Hostnamen/Modellnamen. Deutsch (ASCII-safe), Code Englisch.

## Gegenstand
`scinance3-impl/state/herleitung_a2/` (PLACEBO_DESIGN_A2.md, NUISANCE_SIGMA30.md, a2_vorarbeit.json, ENTSCHEIDUNGSVORLAGEN.md),
Skripte unter `.../scratchpad/a2_vorarbeit/`. Auftrag: `.../scratchpad/SPEC_A2_vorarbeit.md` (seine harten Regeln gelten
fuer dich: kein Mittel/Vorzeichen einer Verfallstag-Rendite, Renditen nur <= 2024-05-31, aus den Settlement-Rohpartitionen
nur type/instrument_name/timestamp/position, Kalender/OI nur <= 2026-06-30, keine Siegeldateien, kein Harvest-Client).
Massstab: PRD_SCINANCE3.md 5.2, PROGRAMM_BILANZ 2.4, DEC-94, DEC-96 E3, DEC-98 N5, DEC-67 E4, `power_p1.py`.

## Pruefpunkte (BESTAETIGT / ABWEICHUNG / VETO je Punkt, mit Beleg und Richtung)
1. **Siegel-Treue (zuerst, hart):** Wurde ein Mittel, Vorzeichen, Median oder eine Differenz von r_pre/r_post je Klasse
   berechnet, gespeichert oder geloggt (JSON, MD, Skripte, Zwischen-Dateien, Logs)? Tage nach 2024-05-31 in Rendite-
   Groessen? Preisfelder der Settlements im Speicher? Waechter wirksam? Scanne die Skripte auf `.mean(`, `np.mean`,
   `median` auf r-Serien und auf Preis-Schluessel.
2. **r_pre-Konvention und Zeitlage:** Definition auf 1-min-Kerzen gegen den Deribit-TWAP [07:30, 08:00); Delivery-Zeitstempel;
   Kerzenzuordnung (UTC-Grenzen) nachgeprueft.
3. **Ereignisgroesse/OI:** Summen von `position` je Klasse und Tag korrekt (Optionen vs. Futures getrennt; Klassenregeln nach
   DEC-98 N5); Verhaeltnisse Freitag/Mo-Do, Monat/Woche; Datumsgrenze 2026-06-30.
4. **Placebo-Design:** Ist die Analyse der Kontaminationen (taeglicher Verfall, Funding 08:00, Wochenende) richtig und die
   Richtung je Design ausgewiesen? Ist die Empfehlung vorab fixierbar (PIT), ohne Wahl nach Sehen? Fehlt ein naheliegender
   Placebo (z. B. 07:30-08:00 an Tagen ohne jeden Verfall vor 2020-02, als historische Baseline)?
5. **sigma30/rho/c nachrechnen** (eigenes Skript auf den Extrakten, nur Streuung): SD je Klasse BTC/ETH, Verhaeltnisse,
   rho, Autokorrelation, c; Abweichungen > 1 % benennen; Bootstrap-Band plausibel.
6. **SE(Delta)/MDE80/Power:** Formel `[pb:A2]` hergeleitet oder korrigiert; N je Fenster richtig gezaehlt (Kalender
   DEC-98 N5); `power_p1` benutzt; Prior-Gitter konsistent; Vergleich mit PRD-Vol-Kette und Bilanz-Tabelle; keine
   verdeckte Zuordnung/Verdikt.
7. **Vollstaendigkeit/Belege:** jede Zahl mit Quelle; UNBELEGT (V-5b, Fensterlage, Reihenfolge) benannt; Gabelungen
   mit Richtung; deterministisch.

## Ausgabe
`REVIEW_A2_VORARBEIT.md`: Urteil (ZUSTIMMUNG / MIT AUFLAGEN / VETO), Befunde B-1.. mit Schwere, Nachrechnungstabelle,
Auflagen vor einem DEC-Nachtrag, was NICHT folgt. Kurzfassung <= 10 Zeilen, kein Mittel, kein Vorzeichen.
