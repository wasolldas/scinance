# Review-Auftrag H-33 (adversarisch, Gate-Auditor-Rolle): Kurzfrist-Reversal mit Literatur-Prior auf W1/W2

Du bist der zweite, adversarische Gutachter im Forschungsprogramm Scinance 3.0 (Veto-Recht, Richtung Strenge).
Gegenstand: alles unter `/home/user/scinance/scinance3-impl/state/herleitung_h33/` (ENTSCHEIDUNGSVORLAGEN.md,
ERSTFASSUNG_H33_entwurf.md, power_h33.json, nuisance_neg.json) und die Skripte unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h33_herleitung/`. Auftrag der
Herleitung: `.../scratchpad/SPEC_H33_herleitung.md` (seine harten Regeln gelten fuer dich: KEINE Datenrechnung mit
Outcome, W1/W2 nie oeffnen, Siegeldateien nie oeffnen, kein Harvest-Client, Nuisance nur aus
`state/runs/h32_20261021_v6b/`, Blind-Siegel ab 2026-07-01, nichts committen, keine Zugangsdaten/Hostnamen/Modellnamen).
Eigene Skripte nur unter `.../scratchpad/h33_review/`. Massstab in dieser Reihenfolge: `scinance3-impl/CLAUDE.md`;
DEC-102 (Rahmen, bindend), DEC-101 Teil 1-3, DEC-99 (+N1), DEC-94, DEC-96, DEC-58 E2, DEC-51/52/53; GL-032..035;
`state/herleitung_h32/REGISTRIERUNG_H32_entwurf.md` (Fassung 3), die beiden Registrierungs-Reviews zu H-32 (gelernte
Regeln), `power_p1.py`, `h32_fm8/` (estimators, powerline, pnull, gate, positive_control).

## Pruefpunkte (Fehler in BEIDE Richtungen; Befund je Punkt BESTAETIGT / ABWEICHUNG / VETO mit Beleg und Richtung)
1. **Prior:** Ist der Literatur-Prior belastbar hergeleitet (Quellen mit Stichprobe vor 2024-07, Umrechnung auf fm8-Skala
   und Wochenhorizont, Universums-Zuordnung des Bybit-USDT-Perp-Universums nur ueber Zaehlungen), oder ist er UNBELEGT?
   Fliesst der Pilot (GL-035) irgendwo in die Groesse des Priors ein (verboten, DEC-102 E3)? Ist die Richtungswahl mit
   dem Pflicht-Etikett aus DEC-102 E2 gefuehrt? Nachrechnen der Umrechnungswege (A*/B) aus den Akten.
2. **Nuisance in negativer Richtung:** Sind null_mean_neg, bindende Zelle, q95_neg (= max aus 1.000er- und 10.000er-Quantil
   nach DEC-101 E5), ceiling_k3_neg, se_mean/e_se_rule/sd_week korrekt aus dem v6b-Artefakt und den Replikaten
   abgeleitet? Nachrechnen mit eigenem Skript (Replikate liegen in Rohrichtung vor). Ist die Empfehlung "aus v6b
   umrechnen vs. Vorlauf v7" sauber begruendet (Strenge: v7 zweimal bitgleich)?
3. **Power-Zeile und Zuordnung:** MDE80 je Fenster = max((1b) ohne Gutschrift, (1c) = q95_neg + z_80 se_mean); Fenster-
   und gemeinsame Power am Prior mit `power_p1`; Regime P-1 und A3-Praxis; Endpower nach F-WEEK m = 3 (Doppelausweis
   14) mit Replikat-Quantilen in negativer Richtung. Nachrechnen; Abweichungen > 1 % benennen.
4. **Design ohne Pilot:** Gate (1b)/(1c) mit skalierter Null, p-Konvention, F-WEEK-Zaehlung, Selektionsdecke K = 3,
   Kill-Bedingungen, Etiketten (Bounce, Liquiditaet, Survivorship in negativer Richtung!), REZENZ, Panel-Schnitt,
   Universum, Startsperre/Pins, Positivkontroll-Regel (Erstfassung H-32 Abschnitt 4 + DEC-101 Teil 2 E8) in negativer
   Richtung - woher stammen F2_real/k_pred ohne Pilot? Ist die vorgeschlagene PK-Welt-Lesart zulaessig (DEC-94 (5) (i):
   nur Streuung) und mit Richtung ausgewiesen?
5. **Nicht-Wiederholung (C.1) und Blindheit (C.17):** Abgrenzung zu H-29, H-32_rev_gap, H-32_mom* woertlich und
   stichhaltig? C.17-Liste vollstaendig (v6b-Nuisance, Pilotwerte 2022-24, Survivorship-Differenzen, Spread-Zensus)?
   Ist W1/W2 fuer diese Statistik wirklich ungesehen (Akte pruefen)?
6. **Gabelungen:** Vollstaendigkeit der Ermessensentscheidungen mit Richtung (K, Varianten, Prior-Lesart, v7, PK-Welt,
   Universum); versteckte Gabelungen Richtung Testbarkeit (z. B. Horizontwahl, Liquiditaets-Split nach Kenntnis der
   Literatur)? Zaehlt jede gerechnete Variante in K?
7. **Registrierbarkeit:** zwoelf Pflichtzeilen, Gate-Text, DEC-39-Trio, YAML-Schema, Bauliste vollstaendig; Aufwand
   plausibel; UNBELEGT-Punkte benannt.

## Ergebnis
`scinance3-impl/state/herleitung_h33/REVIEW_H33.md`: Urteil ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO, nummerierte
Befunde mit Schweregrad und Beleg (Datei, Zeile, nachgerechnete Zahl), Nachrechnungstabelle (Herleitung vs. Review),
Auflagen vor der Registrierung, Empfehlung an den Orchestrator (welche Prior-Lesart, v7 ja/nein, PK-Welt), was NICHT
folgt. Kurzfassung hoechstens 10 Zeilen. Deutsch, ASCII-safe.
