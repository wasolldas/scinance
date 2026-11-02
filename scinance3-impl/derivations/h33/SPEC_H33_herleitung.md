# Herleitungs-Auftrag H-33: beta-neutrales Kurzfrist-Reversal (1, 2, 4 Wochen) auf W1/W2 mit Literatur-Prior (DEC-102, Option (a))

Du bist der Herleitungs-Agent (Gate-Design, Power, Rauschboden) im Forschungsprogramm Scinance 3.0. Der Orchestrator
registriert, nicht du. Repo `/home/user/scinance`, Python mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte nur
unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h33_herleitung/` (anlegen),
Volltexte unter `scinance3-impl/state/herleitung_h33/` (anlegen). Kurzfassung an den Orchestrator hoechstens 12 Zeilen.
Nichts committen, nichts pushen. Keine Zugangsdaten/Hostnamen/Modellnamen. Doku Deutsch (ASCII-safe), Code Englisch.

## Ausgangslage (bindend, in dieser Reihenfolge lesen)
1. `scinance3-impl/CLAUDE.md`; `state/decisions.md`: **DEC-102** (Rahmen, Etikett, Prior-Regel, Ausschluss rev_gap,
   Ablauf - bindend), DEC-101 Teil 1-3 (Universum, skalierte Null, q95-Regel, U-4, Positivkontrolle in
   Produktionskonfiguration, Pilot-Ergebnis), DEC-99 (+N1), DEC-100 (+N1/N2), DEC-94 (P-1), DEC-96 E3 (Blind-Siegel),
   DEC-85/87/89, DEC-58 E2, DEC-51/52/53; `state/gate_log.md` GL-032..035.
2. `state/herleitung_h32/`: `REGISTRIERUNG_H32_entwurf.md` (Fassung 3 = registriertes Design H-32, Pflichtzeilen,
   EV-Entscheidungen, Abweichungen, C.17), `ERSTFASSUNG_H32_entwurf.md` (Abschnitte 1, 2, 4, 5, 6, 9, 10, 11 als Vorbild),
   `REVIEW_REGISTRIERUNG_H32.md` + `..._NACHPRUEFUNG.md` (gelernte Regeln: Universum, Null-Streuung, PK-Ziel, Pins),
   `state/registered/h32_v1.yaml` (Schema-Vorbild), `state/runs/h32_pilot_v1/h32_pilot.md` (GL-035; nur als Etikett -
   die Pilot-Zahlen sind NICHT der Prior).
3. Nuisance-Quelle: `state/runs/h32_20261021_v6b/h32_prelaunch.json` (+ `.md`, `h32_prelaunch_p_replicates.json` mit
   10.000 Replikaten je Fenster/Variante in der POSITIVEN Richtung, Zelle = groesseres Null-Mittel; K-Reihen) - NUR
   Nuisance (Streuung, Null-Mittel, Quantile), kein Outcome. Die Replikate darfst du lesen und fuer die negative
   Richtung umrechnen (q95_neg = -Quantil_5 der Replikatverteilung in Rohrichtung bzw. Zelle mit dem fuer die negative
   Richtung groesseren Null-Mittel - begruenden, welche Zelle in der negativen Richtung bindet: driftfrei oder Drift).
4. Literatur: `state/RECHERCHE_BELEGE_2026-10-18.md` Frage 1 (1.1-1.3), `state/BELEGE_AUS_PDF_2026-10-20.md`
   (Abschnitte 3.1 Ficura, 3.2 Bianchi, 4 IC-Naeherungen, 8 Folgen, 10 fehlende PDFs), DEC-98 N2; PDFs unter
   `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/pdfs_2026-10-20/` und
   Textextrakte unter `.../scratchpad/pdf_belege_txt/` (nur Stichproben vor 2024-07 verwenden; Quellen, die in W1/W2
   hineinreichen, nicht fuer den Prior).
5. Code: `src/bybit_edge/research/h32_fm8/` (constants: `DIRECTION`, `VARIANTS`, `ENTRY`, `HYPOTHESIS`; powerline.py,
   handover.py, estimators.py, testrun.py, positive_control.py, pilot.py, checks.py, schema.py, vorlauf.py, pnull.py),
   `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/Zuordnungszahl), `scripts/h32_fm8.py`.

## Harte Regeln
1. **Keine Datenrechnung mit Outcome.** W1/W2 werden nicht geoeffnet; kein realer IC, keine Rendite. Zahlen nur aus dem
   v6b-Artefakt (Nuisance) und der Literatur. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv`
   oder `ic_series_*_UNION_REAL.csv` heissen; nichts unter `data/harvest`; kein Harvest-Client; Blind-Siegel ab 2026-07-01.
2. **Prior nur aus der Literatur** (DEC-102 E3). Der Pilot (GL-035) ist verbraucht und darf die Groesse des Priors nicht
   bestimmen; die Richtungswahl ist nach Kenntnis des Pilots erfolgt und traegt das Etikett aus DEC-102 E2 - fuehre es
   in jeder Datei. Ist der Prior auf der fm8-Skala (Daempfung ~0,75) und fuer das Bybit-USDT-Perp-Universum nicht
   belastbar herleitbar, schreibe **UNBELEGT** und liefere stattdessen das Prior-Gitter (0,010 / 0,015 / 0,020 / 0,025 /
   0,033 / 0,048) mit Fenster-Power, Regime und Endpower je Variante - die Registrierung ist dann blockiert, der
   Orchestrator fragt den Nutzer. Keine Zahl ohne Quelle; Ermessen mit Richtung (Testbarkeit/Strenge, DEC-93 H-1).
3. Nichts registrieren, kein Verdikt.

## Design, das herzuleiten ist (Rahmen DEC-102 E1; Abweichungen nur mit Richtung und Grund)
- **Hypothese H-33, Familie F-H33, K = 3:** `H-33_rev1`, `H-33_rev2`, `H-33_rev4` = Charakteristiken mom1/mom2/mom4
  (Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4; `characteristics.momentum_characteristic`) mit **negativer**
  Richtung (Reversal); Primaerstatistik exakt die H-32-Statistik (`fm_neutral_8w`, close_at_last, min 10). Pruefe und
  begruende: K = 3 oder zusaetzliche Variante (z. B. 2-Wochen-Reversal mit 1-Wochen-Gap wie Dobrynskaya/Jegadeesh;
  Liquiditaets-Split "klein/illiquide" als eigenes Universum) - jede gerechnete Variante zaehlt in K und in der
  Selektionsdecke; Richtung ausweisen. `rev_gap` ist ausgeschlossen (DEC-102 E4).
- **Fenster:** W1 2024-07-01..2025-06-30 (52 geurteilte Wochen), W2 2025-07-01..2026-06-28 (50), Panel-Schnitt
  2026-06-28, Universum lineare USDT-Perps (DEC-101 E1), C10 hart (beide Fenster) oder DEC-52 nach
  `power_p1.assign_regime` mit dem Literatur-Prior; REZENZ (W2 muss bestehen). Kein Pilot.
- **Gate (wie H-32 Test, Erstfassung 2 + DEC-101):** (1b) y_W >= z_krit x SE_W (P-1 (4)), (1c) y_W >= q95_eff (skalierte
  Null, DEC-101 E2) - in der negativen Richtung: q95_neg aus den v6b-Replikaten, Null-Mittel in Richtung = -null_mean_raw
  (fuer mom: negativ, also keine Gutschrift; pruefe die bindende Zelle), p aus den transformierten Replikaten, Max-p
  W1/W2, BH Nenner K report-only, F-WEEK BY bindend mit m = getestete Eintraege (H-33: 3; Doppelausweis alte Zaehlung
  7 + 4 + 3 = 14), Selektionsdecke K=3 vorzeichenbereinigt (aus den Replikaten herleitbar), Bounce-/Liquiditaets-/
  Survivorship-Etiketten wie H-32 (Survivorship-Differenz der v6b-Akte ist fuer mom1 in POSITIVER Richtung -0,425 /
  -0,538 Schwellen-Einheiten - fuer die negative Richtung Vorzeichen umkehren und als Etikett fuehren; Richtung!).
- **Eingefrorene Groessen je Fenster/Variante (aus v6b, umgerechnet auf die negative Richtung):** se_mean, e_se_rule,
  sd_week (richtungsfrei), null_mean_neg = -null_mean_raw je Zelle (bindende Zelle = groesseres Null-Mittel in der
  NEGATIVEN Richtung, d. h. die Zelle mit dem KLEINEREN rohen Null-Mittel - driftfrei?), q95_neg = max(q95_1000_neg,
  q95_10000_neg) nach DEC-101 E5, ceiling_k3_neg, floor_fm8, v_fm8, K-Reihen-Hashes (unveraendert). Lege dar, ob diese
  Umrechnung aus dem v6b-Artefakt ohne neuen Vorlauf registrierbar ist (Replikate liegen als Fenstermittel in
  Rohrichtung vor: ja/nein je Groesse) oder ob ein Vorlauf v7 (Richtung negativ, 2 h) noetig ist - Empfehlung mit
  Richtung (Strenge: v7 zweimal bitgleich).
- **Power-Zeile (DEC-94 (3), P-1):** je Fenster MDE80 = max((1b)+Gutschrift(0), (1c) = q95_neg + z_80 x se_mean);
  Fenster-Power und gemeinsame Power am Literatur-Prior; Zuordnung `power_p1.assign_regime` (P-1) und
  `assign_regime_a3_practice` (Doppelausweis); Endpower nach F-WEEK (m = 3; Doppelausweis 14) mit
  `estimators.end_power_replicates` (Replikat-Quantile in negativer Richtung) - alles mit `power_p1`/`estimators`, keine
  eigene Normalnaeherung ausser als Bericht.
- **Prior (Kern der Herleitung):** Aus der Literatur fuer "Kurzfrist-Reversal im breiten/kleinen-illiquiden
  Krypto-Universum, Wochenhorizont" (Ficura Small or Illiquid t -7,31, Weg A* -0,064; Bianchi 1-Tag-Reversal; LTW FM
  > 1 Mio -0,011..-0,019; Dobrynskaya Umschlag nach ~1 Monat; Shen/Urquhart/Wang 2020 woechentliches Reversal, falls
  im Textextrakt) -> Band auf der fm8-Skala (x ~0,75) fuer das Bybit-USDT-Universum (514..603 Perps, davon ein grosser
  Teil klein/illiquide - Zuordnung begruenden, Universums-Zusammensetzung nur ueber Zaehlungen/Umsatzdezile aus dem
  WP-7-Spread-Zensus `state/runs/wp7_20260921/spread_census.json`, keine Renditen). Zwei Umrechnungswege (A*/B) mit
  Richtung; Empfehlung einer Referenz-Lesart; was UNBELEGT bleibt.
- **Positivkontrolle:** Erstfassung H-32 Abschnitt 4 mit DEC-101 Teil 2 E8 (skalierte Gate-Kette, Injektionsziel F) in
  negativer Richtung; ohne Pilot: F2_real und k_pred stammen nicht aus einem Pilot - Vorschlag, woher (Strenge: F2_real
  := F2_null, k_pred = 1, mit Etikett; oder Welt-SD = sd_week x k_pilotbefund? NEIN - der Pilot ist verbraucht;
  begruende, ob die GL-035-Nebenbefund-Zahl (reale Wochen-SD ~2,3..2,6 x Null-SD) als reine Streuungs-Nuisance fuer die
  PK-Welt verwendet werden darf (DEC-94 (5) (i): Streuung ist zulaessig) - beide Lesarten mit Richtung, eine empfehlen).
- **Nicht-Wiederholungs-Nachweis (C.1):** Abgrenzung zu H-29 (A3-R Gap-Reversal, GL-032 Positivkontrolle), H-32_rev_gap
  (GL-035) und H-32_mom* (Richtung umgekehrt, Fenster W1/W2 ungesehen): woertlich.
- **Ergebnisblindheit (C.17):** Liste alles, was fuer W1/W2 und fuer die Statistik je gesehen wurde (v6b-Nuisance,
  Pilot-Werte 2022-24, Survivorship-Differenzen, Spread-Zensus), und das Etikett aus DEC-102 E2.
- **Bauliste** fuer den Builder: Richtung je Hypothese konfigurierbar (YAML `hypotheses.*.direction`, Konstanten-Satz
  H-33 additiv neben H-32, `HYPOTHESIS`/`ENTRY`/`DIRECTION`/`VARIANTS` als Konfiguration), Modus ohne Pilot
  (`--run` mit `prior_source: literature`, Startsperre, Pins, Positivkontrolle davor), Vorlage aus v6b oder v7, Tests
  (T0-T7 analog), Determinismus.
- **Schema `state/registered/h33_v1.yaml`** (Entwurf, Abschnitt wie H-32 Erstfassung 11): hypotheses mit direction
  negative, kein pilot_window (oder `pilot: none` mit Grund DEC-99 (5)), `prior: {source: literature, value, band, scale:
  fm8, label}`, windows W1/W2 mit frozen (negativ), fdr, fweek_counting, universe, null_scaling, runner, seal,
  positive_control, data_fingerprints (v6b-Pins unveraendert), code commits.

## Dateien
`ENTSCHEIDUNGSVORLAGEN.md` (Prior-Lesarten mit Richtung, K, Umrechnung/v7, PK-Welt, offene Punkte), `ERSTFASSUNG_H33_entwurf.md`
(zwoelf Pflichtzeilen, Gate-Text woertlich, Positivkontroll-Regel, DEC-39-Trio, Kill-Bedingungen, Etiketten C.17,
Nicht-Wiederholung, Abweichungen, Registry-Block, YAML-Schema, Bauliste), `power_h33.json` (alle Zahlen, deterministisch,
`[fj:]`-Pfade), `nuisance_neg.json` (die auf die negative Richtung umgerechneten v6b-Groessen mit Herkunft je Zahl).

## Rueckmeldung
Hoechstens 12 Zeilen: Prior-Band und Referenz-Lesart (oder UNBELEGT), MDE80 je Variante/Fenster in negativer Richtung,
Regime am Prior, Endpower m = 3, K, v7 noetig ja/nein, PK-Welt-Vorschlag, offene Vorlagen, UNBELEGT-Punkte, Dateipfade.
