# Review-Auftrag (adversarisch, Gate-Auditor): Registrierung H-32 - Vorlauf v6, Registrierungsdatei, Registry-Eintrag

Du bist der Gate-Auditor (Veto-Recht, Richtung Strenge) im Forschungsprogramm Scinance 3.0. Der Orchestrator registriert
nur, wenn dein Urteil kein offenes VETO traegt. Repo `/home/user/scinance`, `PYTHONPATH=/home/user/scinance/src`. Eigene
Skripte NUR unter `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h32_reg_review/`.
Volltext `/home/user/scinance/scinance3-impl/state/herleitung_h32/REVIEW_REGISTRIERUNG_H32.md`. Kurzfassung <= 10 Zeilen.
Nichts committen. Keine Zugangsdaten/Hostnamen/Modellnamen. Deutsch (ASCII-safe), Code Englisch.

## Harte Regeln
- KEINE Datenrechnung mit Outcome: das Pilot-Fenster und W1/W2 bleiben zu (kein realer IC, kein Pilot-Lauf, kein
  `--pilot`/`--run`/`--positive-control`). Erlaubt: das v6-Artefakt lesen und Kernzahlen daraus mit `power_p1` und
  eigenen Formeln nachrechnen; Fixture-Laeufe der CLI; Tests. NIE `*_L_window_sealed.json`, `weekly_ic_series.csv`,
  `ic_series_*_UNION_REAL.csv` oeffnen; nichts unter `data/harvest`; Blind-Siegel DEC-96 E3 (nichts ab 2026-07-01).
- Massstab (in dieser Reihenfolge): `scinance3-impl/CLAUDE.md`; `state/decisions.md` DEC-94, DEC-96, DEC-99 (+N1),
  DEC-100 (+N1); `state/herleitung_h32/ERSTFASSUNG_H32_entwurf.md` (Abschnitte 0, 1, 2, 4, 5, 9, 10, 11) und
  `REVIEW_H32.md` (Auflagen); `state/BEFUND_DATENSTROEME_2026-10-21.md`; `src/bybit_edge/research/h32_fm8/` (constants,
  vorlauf, handover, gate, fweek, calibration, nullsim, pnull, delisted_tree, checks, schema) und `scripts/h32_fm8.py`.

## Gegenstand
1. Vorlauf v6: `state/runs/h32_20261021_v6/` (h32_prelaunch.json, .md, p-Replikate-Datei, Log `scratchpad/h32_v6.log`).
2. Registrierungs-Vorlage und finale Datei: `state/registered/h32_v1.yaml` (Entwurf; sha256 erst nach deinem Urteil).
3. Registry-Eintrag (Entwurf) in `state/hypothesis_registry.md` bzw. `state/herleitung_h32/REGISTRIERUNG_H32_entwurf.md`
   und der DEC-Entwurf (DEC-101) in `state/decisions.md` bzw. als Entwurfsdatei.

## Pruefpunkte (Befund je Punkt: BESTAETIGT / ABWEICHUNG / VETO, mit Beleg und Richtung)
1. **Panel und Fingerprints:** v6 auf dem Union-Panel mit Delisted-Baum v2 (Register-sha a28c7eb7..., Baum-sha
   250a923b..., union_range e503bedb...) und hartem Schnitt 2026-06-28 (Log: "82 days removed", max. Tag im Artefakt)?
   Stimmen die Fingerprints im Artefakt, in der YAML und im Registry-Eintrag ueberein? Ist die Abweichung "W1-
   Determinismus-Kontrolle entfaellt (DEC-100 N1)" ehrlich etikettiert und ist der Ersatz (Zweitlauf oder T2) ausreichend?
2. **Fenster und Zaehlungen:** P 2022-04-18..2024-06-17 (w_pilot: 114 in der Erstfassung, v6 meldet 115 Wochen - welche
   Zahl ist richtig, und steht sie konsistent in YAML/constants/Registry?), W1 52, W2 50; K_t je Fenster (v6: P 127/213/353,
   W1 360/440/536) gegen die Erstfassung-Vorabwerte; Outcome-Woche von P ragt nicht in W1.
3. **Eingefrorene Groessen nachrechnen** (aus dem v6-JSON, je Fenster und Variante): se_mean, e_se_rule, sd_week,
   null_mean (extremeres aus driftfrei/Drift, in Richtung), q95, ceiling_k4 (vorzeichenbereinigt), floor_fm8, v_fm8, m_P;
   Plausibilitaet gegen v5e (Erstfassung 1.6 Vorabwerte; Panel ist jetzt vollstaendig, Richtung der Aenderung?);
   Schwellen T_W,v = 1,6449 x e_se_rule + max(0, null_mean) und Decke/Schwelle-Verhaeltnis (Vor-Verdikt-Kill?).
4. **Power-Zeile und Uebergaberegel U** mit `power_p1`: MDE80*_v = max_W(1,6449 x SE_T,W + 0,8416 x SD_T,W) aus den
   v6-Konstanten (vor Pilot: SE_T = e_se_rule, SD_T = se_mean), m* = max(0, m_P, m_W1, m_W2), Uebergabeschwelle auf x_P;
   Endpower-Tabelle F-WEEK m = 1..4 und 11; OC der Uebergaberegel (P(Uebergabe | IC = 0) <= 0,3 %?). Ist Regel U in
   `handover.py` bitgleich mit Erstfassung 1.8 (T4-Test)? Lesart A (Punkt) vs. B etikettiert?
5. **p-Konvention (DEC-99 N1):** p aus Null-Replikaten (R = 10.000, Zelle mit groesserem Null-Mittel, Max-p ueber W1/W2),
   Replikate-sha in der YAML; Block-Permutation nur report-only; BH Nenner 4; F-WEEK m nach DEC-99 (7) + Doppelausweis 11.
6. **Siegel und Sperren:** Panel-Schnitt-Waechter, Pilot-Schnitt 2024-06-30, Genau-ein-Pilot-Sperre (`pilot_result_sha256`
   null in der YAML, `--pilot-rerun-dec`), Startsperre (`--registered-sha256`), Stress-Listen-Datumsfilter, keine
   Siegelmuster geoeffnet (constants.SEALED_PATTERNS), `not_computed` (roher IC, Lag-Profil, Beta-Kalibrierungs-IC).
7. **Ergebnisblindheit (C.17):** Was hat der Orchestrator heute gesehen? (Zaehlungen je Tag, Symbol-Listen, Tagesschluss-
   Gleichheit als Zaehlung, v6-Nuisance ohne Mittel.) Ist das in der Liste; ist nichts davon ergebnisnah?
8. **Registry-Eintrag / YAML gegen Erstfassung 10/11:** Pflichtfelder vollstaendig; Abweichungen (Erstfassung 9) plus die
   neuen (DEC-100: Delisting-Datum = letzter Handelstag statt Announcement, vollstaendiges Panel, W1 nicht v5e-identisch,
   Fingerprints neu) als Erratum/Etikett; Etikett "zugelassen nur durch DEC-99"; Positivkontroll-Regel (Erstfassung 4)
   unveraendert; `rules.bounce_spread` aus dem Spread-Zensus; EV-2..EV-8 als Entscheidungen des Orchestrators dokumentiert.
9. **Tests:** `tests/unit/test_h32*.py` gruen auf dem aktuellen Commit? code_sha256 im Artefakt = HEAD?

## Ausgabe
`REVIEW_REGISTRIERUNG_H32.md`: Urteil (ZUSTIMMUNG / ZUSTIMMUNG MIT AUFLAGEN / VETO), Befunde B-1.. mit Schwere, Tabelle
Nachrechnung (v6-Wert, dein Wert, Abweichung), Auflagen VOR der Registrierung, was NICHT folgt. Kurzfassung <= 10 Zeilen.
