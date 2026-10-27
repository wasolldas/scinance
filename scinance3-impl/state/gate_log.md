# Gate-Log Scinance 3.0 (append-only)

> Fortsetzung von `scinance2-impl/state/gate_log.md` (GL-001..GL-031).
> Neue Eintraege ab GL-032. Kein Lauf ohne registrierten Eintrag, kein
> Urteil ausser gegen das registrierte Gate.

_(noch keine Eintraege)_

## GL-032 - 2026-10-12 - H-28/H-29/H-30 Drittfassung (F-XSEC1, A3, YAML bd948f34...c299) - GL-012 vor dem Lauf, kein Lauf
- Anlass: Positivkontrolle NICHT BESTANDEN (rc 3, `state/runs/wp13_positivkontrolle_20261012`, result_sha256 b3daeea8...041d):
  mom1 PASS 1/3 Seeds, rev_gap 3/3, Negativkontrolle 0/3. Gate-Kette ohne Defekt (Injektion pos-neg +0,051..0,056).
- Ursache (outcome-frei, v5e): DEC-88 rechnete die Roh-IC-Bedingungen mit Boden-SE IC_min/2,4865; registriert ist
  SE = max(Boden, SD(IC_t))/sqrt(W) (DEC-75 (1)). SD(IC_t) der Roh-Null (methods.none factor_sd) W1 0,090/0,130,
  W2 0,061/0,082 (measured/stress) gegen Boden 0,049/0,042.
- Korrigiert, Prior 0,03, W1 measured/stress: mom1 P 0,47/0,21 (MDE80 0,042/0,060), rev_gap 0,48/0,21 (0,041/0,059);
  W2 0,85/0,55 (0,028/0,038). IC_min-Bedingung ebenso betroffen (W1 mom1 0,79/0,71). Bindend stress; gleiches Ergebnis.
- Zuordnung DEC-87 (F)/DEC-51 (2), mechanisch: MDE80 > 0,03 in W1 -> GL-012 fuer mom1 und rev_gap; mom2, mom4 (verschaerft),
  H-30 (Feasibility 2,764; vol_beta strukturell) unveraendert. Alle 7 Varianten GL-012 vor dem Lauf.
- DEC-52 anwendbar, nach DEC-87 (F) nicht genutzt; keine Viertfassung (gepoolt unter stress MDE80 0,034 > 0,03).
- Feststellung: Drittfassung F-XSEC1 im registrierten Design (Roh-IC je Fenster, C.10 hart, W1/W2, Union-Panel) bei
  IC_prior 0,03 nicht testbar. KEIN Verdikt ueber Momentum, Reversal, Vol-Anomalie; DROP-Relevanzzeile greift nicht.
- K = 7 bleibt (p = 1, BH/F-WEEK). YAML bitgleich, --run entfaellt; kein PC-Neulauf, keine Teilkohorte, kein Prior-Wechsel.
  L-Siegel und alle Siegeldateien bleiben geschlossen. Anderes Design nur als neue Hypothese mit eigenem K (DEC-58 E2).
- Akte: DEC-91, DEC-92; Audit `state/REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md`; Gate-Auditor: BESTAETIGT.

## GL-033 - 2026-10-13 - A1 (H-31, Funding-Long-Bein D1 gegen Universums-Hedge, DEC-70) - GL-012 vor der Registrierung, nicht registriert
- Anlass: Feasibility vor dem Design (C.12), `state/herleitung_a1/` (FEASIBILITY sha `b4680f7c...ca72d9e`), ergebnisblind
  (keine A1-Outcome-Groesse ab 2024-07-01). Formationsseitig W1/W2: K 343..511 / 512..600 (Kill (3) nein), Schluessel-
  Autokorrelation 0,403 / 0,303 (Kill (4) formal nein, W2 an der Grenze), D1 nicht degeneriert (0,52 / 0,71), Spread
  175,8 / 339,6 bp/Woche. Nuisance 2022-04..2024-06 (nur Streuung): SD 354 bp, rho_1 -0,25, phi 0,573.
- Prior: prem = Spread x phi x theta; theta (nicht kompensierter Anteil) UNBELEGT. Bei theta = 1: prem W1/W2 100,7 / 194,5,
  gepoolt 147,6 bp.
- Zuordnung nach geltender Regel (DEC-67 E4, fuer A1 bestaetigt DEC-70 E1: W_eff = 0,41 W): 3,168 x SE_gepoolt = 176,5 bp
  > 147,6 bp -> GL-012 schon bei theta = 1 (theta_min 1,196). Guenstigste Lesart (c = max(1, gemessen)) braucht theta
  >= 0,766, ohne Quelle -> blockiert; W1 Power 0,80 bei keinem theta <= 1.
- Review `state/herleitung_a1/REVIEW_A1.md`: VETO gegen "knapp testbar", Zahlen bestaetigt; Orchestrator-Nachrechnung mit
  eigenem Code bestaetigt (Spread 174,0 / 336,3; SD 354,4; phi 0,568). Keine A1-spezifische Regelaenderung (DEC-93 E3).
- Feststellung: A1 in der Konstruktion DEC-70 unter den geltenden Beschluessen nicht testbar; nicht registriert. KEIN
  Verdikt ueber den Funding-Carry; DROP-Relevanzzeile greift nicht. Stufe 2 Akte ohne Rechtswirkung. Siegel unberuehrt.
- Akte: DEC-93; Reviewer: VETO (gegen Testbarkeit) angenommen.

## GL-034 - 2026-10-17 - H-27 (VRP auf DVOL-Backfill, blinde Fenster ab 2026-07-01, EV-0c/DEC-96) - GL-012 vor der Registrierung, nicht registriert
- Anlass: Feasibility vor dem Design (C.12), `state/herleitung_h27/` (Kontamination, Datenprobe, Feasibility), ergebnisblind
  (keine RV ab 2024-06-01, keine DVOL-Niveaus ab 2024-07-01, Blind-Siegel ab 2026-07-01). W1/W2 nicht blind (DEC-96).
- Daten: DVOL BTC/ETH 2021-03-24..2026-10-16 lueckenlos (Katalog 2026-10-17); Panel-close = letzter Trade vor 00:00 UTC.
- Nuisance 2021-03-24..2024-05-31 (nur Streuung): SD S1 18,60 VP, c 28,2 (Regel P-3, Batch-Means), Jensen ~2,1 VP.
  Prior 9,47 VP aus BVRP 0,14 [sek] (Band 7,0..13,7).
- Zuordnung DEC-94/DEC-96 E2: L 6/9/12 -> GL012/GL012/GL012 (P-1 und A3-Praxis); L 12: Fenster-Power 0,575,
  DEC-52-Gate 0,359, MDE80 12,85 VP; C10 braeuchte >= 672 Tage je Fenster.
- Review `REVIEW_H27.md`: ZUSTIMMUNG MIT AUFLAGEN (umgesetzt, DEC-97); Orchestrator-Gegenprobe bestaetigt.
- Feststellung: H-27 nicht registriert. KEIN Verdikt ueber die Volatilitaets-Risikopraemie; DROP-Relevanzzeile greift
  nicht; H-26 (2.0) unberuehrt. Testbarkeit nur ueber nicht beschlossene Lesarten (Prior-Rand, c ohne Batch-Means,
  Hochfrequenz-RV), jede nur unter DEC-94. Siegel unberuehrt; Blind-Siegel DEC-96 E3 bleibt.
- Akte: DEC-95, DEC-96 (Nachtraege 1-3), DEC-97; Reviewer: ZUSTIMMUNG MIT AUFLAGEN.

- **Vermerk 2026-10-21 (Erratum-Etikett, DEC-101 Teil 1; keine Neubewertung):** Die Nuisance-Rechnungen hinter GL-032 (Positivkontrolle A3 v5e), GL-033 (A1) und GL-034 (H-27, Panel-Schluesse) nutzten den Ueberlebenden-Baum einschliesslich 68 USDC-Perpetuals (Zwillinge der USDT-Perps) und datierter Futures (Gate-Review Registrierung H-32, B-1). Die Feststellungen bleiben bestehen; das Universum der kuenftigen H-32-Rechnungen ist auf lineare USDT-Perps eingeschraenkt.

### GL-035 · H-32 (A3-fm8, Zweistufen-Design): GL-012 (Pilot) fuer alle vier Varianten - keine Uebergabe, kein Test, W1/W2 bleiben blind (2026-10-21, DEC-101 Teil 3)
- **Lauf:** `scripts/h32_fm8.py --pilot` genau einmal (DEC-99 (3), DEC-101 E10), registrierte Datei `state/registered/h32_v1.yaml` sha256 0fadda78..., Versuchsmarker 2026-10-21T20:33:05Z, Panel-Schnitt 2024-06-30, Universum lineare USDT-Perps (1.182 -> 1.066), Fenster P 2022-04-18..2024-06-24, w_pilot 114, K 126/206/339; Artefakte `state/runs/h32_pilot_v1/` (result_sha256 8b63a56eb0a68afb0748f84806b9f491f75f09ac8d980063cdfb8c4893e69627, h32_pilot.json sha256 be20a826...). Orchestrator-Nachrechnung aus den Wochenreihen: x_P, SD_P, SE_P bitgleich (W = 114 je Variante).
- **Ergebnis (Regel U-4, mechanisch):**

| Variante | x_P (in Richtung) | SD_P | SE_P | t_P | 80-%-Band | F2_real | k_pred W1/W2 | Schwelle auf x_P (U-4) | (i)/(ii)/(iii) | Status |
|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| mom1 | -0,03847 | 0,12351 | 0,01157 | -3,33 | [-0,0533, -0,0236] | 0,01033 | 2,20 / 2,49 | 0,04229 | nein/nein/nein | GL-012 (Pilot) |
| mom2 | -0,05003 | 0,13015 | 0,01219 | -4,10 | [-0,0657, -0,0344] | 0,01202 | 2,11 / 2,45 | 0,04583 | nein/nein/nein | GL-012 (Pilot) |
| mom4 | -0,04463 | 0,13415 | 0,01256 | -3,55 | [-0,0607, -0,0285] | 0,01307 | 1,88 / 2,23 | 0,05005 | nein/nein/nein | GL-012 (Pilot) |
| rev_gap | +0,01667 | 0,11611 | 0,01088 | +1,53 | [+0,0027, +0,0306] | 0,00856 | 2,05 / 2,30 | 0,03629 | ja/nein/nein | GL-012 (Pilot) |

- **Feststellung:** keine Variante erfuellt die registrierte Uebergaberegel; H-32 endet als GL-012 (Pilot) mit gemessenem Grund. Es gibt keinen Testlauf, keine Positivkontrolle und kein Verdikt; W1 und W2 bleiben fuer A3-fm8 blind (keine reale IC je berechnet). p = 1 je Eintrag im BH-Nenner 4; H-32 zaehlt nicht in m von F-WEEK (DEC-99 (7)). Der Pilotabschnitt 2022-04-18..2024-06-24 ist fuer jede mit dem fm8-IC korrelierte Statistik verbraucht (DEC-99 (5)).
- **Gesehen (C.17, nur Pilotfenster):** x_P, SD_P, Bootstrap-SE, F2_real, c_real (1,000), Liquiditaets-Etiketten je Variante (report-only, im Artefakt). Nichts aus W1/W2.
- **Nebenbefund (nuisance, pilotbezogen):** Die reale Wochen-SD der fm8-IC-Serie im Pilot (0,116..0,134) liegt um das ~2,3..2,6-fache ueber der Wochen-SD der faktorerhaltenden Null (v6b sd_week W1/W2 0,044..0,066; P-Null aehnlich) - F2_real 0,0086..0,0131 gegen v_fm8_P 0,0049. Die skalierte Null (DEC-101 E2, k = 2..2,5) haette im Test entsprechend hoehere Quantile gesetzt. Fuer kuenftige Querschnitts-Designs ist die Querschnitts-Abhaengigkeit jenseits des Ein-Faktor-Modells die bindende Streuungsquelle (Etikett, keine Regelaenderung).
- **Was nicht folgt:** kein Verdikt ueber Momentum oder Reversal; die negativen Pilot-ICs der mom-Varianten sind Screening-Werte aus einem anderen Marktregime (2022-2024), nicht urteilstragend, und begruenden keine umgedrehte Hypothese auf W1/W2 ohne eigene DEC (Richtung nach Kenntnis des Pilots = Testbarkeit; der Pilot ist verbraucht, ein neuer Prior muesste aus der Literatur kommen).

### GL-036 · H-33 (beta-neutrales Kurzfrist-Reversal 1/2/4 Wochen, W1/W2): GL-012 VOR der Registrierung - Literatur-Prior UNBELEGT, kein Lauf, W1/W2 bleiben fuer fm8-Reversal ungeoeffnet (2026-10-27, DEC-102 Nachtrag 2, Nutzerentscheid Option 1 = Default)
- **Grundlage:** `state/herleitung_h33/` (ENTSCHEIDUNGSVORLAGEN, ERSTFASSUNG_H33_entwurf, power_h33.json sha256 026494b6..., nuisance_neg.json sha256 05e6f2a0..., REVIEW_H33 = ZUSTIMMUNG MIT AUFLAGEN zur Herleitung, bedingtes Vorab-VETO gegen eine C10-Registrierung auf W1/W2; 300 Groessen bitgleich nachgerechnet), DEC-102 (+N1), Vorlage `state/VORLAGE_NUTZER_H33_PRIOR_2026-10-26.md`. Keine Outcome-Rechnung; W1/W2 nicht geoeffnet; kein Code gebaut; kein Vorlauf v7.
- **Feststellung (gemessen/hergeleitet):** (1) Prior UNBELEGT: Literaturband auf fm8-Skala klein/illiquide +0,039..0,048, breit/gleichgewichtet ~0..+0,014, gross/liquide -0,015..-0,026 (Momentum); das Bybit-USDT-Perp-Universum ist keiner Gruppe belegbar zuzuordnen (kein USD-Umsatz/keine Marktkapitalisierung in der Akte), das Zaehl-Indiz zeigt auf breit..gross/liquide. (2) Mindest-Prior fuer C10 (Lesart S, Pilot-Streuung als Nuisance, DEC-102 N1 (3)): rev1 0,0395, rev2 0,0418, rev4 0,0431 - oberhalb jeder belegten Literaturzahl fuer ein Universum mit Groessen-/Umsatzfilter; unter der Referenz-Lesart R3 (und R4) sind alle drei Eintraege GL-012 (gemeinsame Power am oberen R3-Wert 0,0144: rev1 0,06 unter S). (3) Die einzige C10-Lesart (R1, Pilot-Niveau) ist als Literatur-Prior nicht zulaessig (DEC-102 E3). (4) C.17: W2 ist fuer rev1 nicht voll ergebnisblind (Persistenz-Null der Drittfassung, richtungsgleich, ~0,5 x S-MDE80).
- **Status:** H-33_rev1, H-33_rev2, H-33_rev4 = **GL-012 vor der Registrierung** (kein K verbraucht, kein Eintrag in F-WEEK, kein Verdikt). Der Nutzer hat am 2026-10-27 den Default gewaehlt (Option 1 der Vorlage); die Optionen Lockerung (L), blindes Fenster (B) und PDF-Nachlieferung (P) sind nicht gewaehlt (P bleibt moeglich, aendert diesen Vermerk nicht ohne neue Herleitung).
- **Was folgt / nicht folgt:** W1/W2 bleiben fuer fm8-Reversal und fm8-Momentum unberuehrt (DEC-101 E12, GL-035) und stehen spaeteren Hypothesen anderer Statistik oder mit belegtem Prior offen; die Herleitungsakte bleibt als Vorarbeit (Nuisance in negativer Richtung, Power-Gitter) gueltig fuer einen etwaigen spaeteren Kandidaten mit belegtem Prior. Kein Verdikt ueber Reversal oder Momentum. Naechste freie Hypothesennummer: H-34.

