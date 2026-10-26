# Review H-33 (adversarisch, Gate-Auditor-Rolle): Herleitung "beta-neutrales Kurzfrist-Reversal 1/2/4 Wochen auf W1/W2 mit Literatur-Prior"

> **Kein Verdikt, keine Registrierung.** Review nach `SPEC_H33_review` vom 2026-10-26. Gegenstand: `ENTSCHEIDUNGSVORLAGEN.md`
> (EV), `ERSTFASSUNG_H33_entwurf.md` (EF), `power_h33.json` (sha256 `026494b6...5bc9`), `nuisance_neg.json` (sha256
> `05e6f2a0...0835`) in diesem Ordner und das Skript `scratchpad/h33_herleitung/h33_compute.py` (sha256 `ef0788a0...46b0`,
> stimmt mit dem JSON-Kopf ueberein; `run1/` und `run2/` bitgleich mit den Repo-Dateien).
> **Etikett (DEC-102 E2, Pflicht):** "beschlossen nach Kenntnis von GL-035 (Pilot-Vorzeichen der mom-Varianten); Richtung
> Testbarkeit; Richtungswahl nach Kenntnis korrelierter Daten eines anderen Fensters (2022-04..2024-06)" - nach Befund B-2
> unvollstaendig (Ergaenzung Auflage A-2).
> **Ergebnisblindheit des Reviews:** keine Datenrechnung mit Outcome, kein Panel, kein Harvest-Client, W1/W2 nicht geoeffnet,
> keine Siegeldatei geoeffnet, `h32_pilot.json` und die Pilot-Wochenreihen nicht geoeffnet. Gelesen: v6b-Artefakt
> (`h32_prelaunch.json`, `h32_prelaunch_p_replicates.json`; Nuisance), `h32_pilot.md` nur Spalten F2_real/c_real,
> Akten-Texte (decisions, gate_log, hypothesis_registry Z. 105-125, Drittfassung Z. 150-172, H-32-Herleitung und -Reviews,
> BELEGE_AUS_PDF, Ficura-/LTW-Textextrakte). **Offenlegung:** von `state/runs/wp7_20260921/survivorship_bias_UNION_REAL.json`
> wurden nur die Schluesselnamen gelesen (keine Werte), um festzustellen, ob die Datei IC-Niveaus traegt (Befund B-5).
> Eigenes Skript `scratchpad/h33_review/review_h33.py` (sha256 `723fa4a4...dee4`), zweimal gerechnet, Ausgabe
> `out1.json` = `out2.json` (sha256 `97f76824...6fbe`); alle Power-/MDE-/Zuordnungszahlen mit `power_p1` und
> `h32_fm8.estimators`, Endpower zusaetzlich in geschlossener Form gegengerechnet. Nichts committet.

---

## 1. Urteil: ZUSTIMMUNG MIT AUFLAGEN zur Herleitung - und VORAB-VETO (bedingt) gegen jede Registrierung von H-33 auf W1/W2 mit einem C10-Eintrag

- Die Herleitung ist rechnerisch fehlerfrei: 300 Vergleichsgroessen (MDE80 je Bedingung, k, SE_T/SD_T, Fenster-Power am
  Gitter, Regime P-1, A3-Praxis, Endpower m = 3/14) stimmen mit der Nachrechnung auf <= 1,6e-16 relativ ueberein; alle
  sechs negativen Null-Mittel, bindenden Zellen, q95_neg (1.000/10.000), dev95 und alle Selektionsdecken bitgleich.
- Die Kernaussagen sind richtig und in Richtung Strenge: Prior **UNBELEGT**, Referenz-Lesart R3 -> alle drei Eintraege
  GL-012 vor der Registrierung; Lesart S; v7 nur bei einem C10-Eintrag; Rezentrierung bei (1c); K = 3; nur C10.
- Die Literatur spricht fuer das Bybit-Perp-Universum noch deutlicher gegen einen positiven Prior als die Herleitung
  schreibt (B-1): R1 ("klein/illiquide") ist fuer dieses Universum nicht belegt und faellt mit dem verbrauchten Pilot
  zusammen.
- Der neue C.17-Befund der Herleitung (Persistenz-Null W1/W2 in H-33-Richtung) ist echt und wiegt fuer rev1 in W2 schwer
  (B-2). Er beruehrt auch die Entscheidungsgrundlage von DEC-102 (in der Vorlage DEC-101 Teil 3 nicht genannt).
- **Vorab-VETO (bedingt):** Sollte nach der Nutzerrueckfrage eine Prior-Lesart gewaehlt werden, unter der ein Eintrag C10
  wird (praktisch nur R1 bzw. ein Gitterwert >= MDE80\*), legt der Review VETO gegen die Registrierung auf W1/W2 ein:
  Richtungswahl nach dem Pilot, Prior-Groesse auf Pilot-Niveau und ein in W2 vorab gesehener, richtungsgleicher
  Eigen-Autokorrelationsanteil fuer rev1 waeren drei gestapelte Gabelungen in Richtung Testbarkeit; ein PASS waere nach C.17
  nicht konfirmatorisch. Aufhebbar nur durch ausdruecklichen Nutzerentscheid mit Etikett "Lockerung" (wie DEC-99) und der
  festgeschriebenen Feststellung "PASS auf W1/W2 nicht konfirmatorisch". Gegen die empfohlene Referenz-Lesart (alle GL-012)
  besteht kein VETO.

## 2. Kurzfassung (<= 10 Zeilen)

1. Nachrechnung bitgleich (300 Groessen, max. rel. Abweichung 1,6e-16): MDE80\* T 0,0184/0,0202/0,0236, S 0,0395/0,0418/0,0431.
2. Pilot fliesst nicht in die Prior-Groesse ein (F2_real nur in Lesart S); R1 liegt aber auf Pilot-Niveau und ist fuer
   Perps nicht belegt (Ficura Tab. 7 B: Reversal nur bei Wochenvolumen < 100 Tsd. USD; mit Groessenfilter Momentum).
3. Referenz R3 (robust auch unter R4) -> alle GL-012, kein v7, kein Bau; dokumentierter Default bei Stille fehlt (A-3).
4. Lesart S ist die mit DEC-94 (3)/(5) vereinbare (T wiederholt den DEC-91-Fehler, PK leer), braucht aber eine Auslegungs-DEC.
5. C.17: Persistenz-Null W2 mom1 roh ~ -0,046 (Akte); nach grober Kendall-Bereinigung bleibt bis ~0,02 (fm8, Reversal) -
   ~1 x T-MDE80, ~0,5 x S-MDE80 in W2; W1 ~ Kendall-Groesse. W2-rev1 nicht konfirmatorisch; DROP bliebe aussagekraeftig.
6. Rezentrierung (1c) ist Pflicht (DEC-94 (3) + DEC-101 E2, Praezedenz U-4 rev_gap), keine "Abweichung".
7. Bounce-Mehrseed: richtig, aber fuer Seed 53 entscheidungsneutral (|Bounce|/T <= 0,82 in allen 6 Paaren).
8. Neu: Knife-edge rev2 bei R1/S (W2-(1b)-Marge 3,6e-7, haengt an der 6. Stelle von F2_real); adversariales Fixture
   prueft nur Momentum-Artefakte (wirkungslos in Reversal-Richtung); C.17 ohne WP-7-Survivorship-JSON mit IC-Niveaus.
9. Vorab-VETO (bedingt) gegen C10-Registrierung auf W1/W2; sonst ZUSTIMMUNG MIT AUFLAGEN A-1..A-7.

## 3. Pruefpunkte

| # | Pruefpunkt | Befund | Richtung | Beleg |
|---|---|---|---|---|
| 1 | Prior | **BESTAETIGT** (UNBELEGT, Umrechnung A\*/B/FM bitgleich nachgerechnet, kein Pilot in der Groesse, Etikett in allen vier Dateien) mit **ABWEICHUNG** in der Begruendung: Zuordnungs-Indiz und Ficura Tab. 7 B sprechen gegen R1 und eher fuer R3..R4 (B-1); Weg-B-Richtung mit GL-035 begruendet statt mit BELEGE 4 (B-9) | Strenge | EV Z. 92-93, 123-138; B-1, B-9 |
| 2 | Nuisance negativ | **BESTAETIGT**: null_mean_neg, bindende Zelle driftfrei (6/6), q95_neg Drift 1.000/10.000 (10.000 bindet 6/6), dev95, se_mean/e_se_rule/sd_week (Maximum der Zellen, richtungsfrei), Decken roh/rezentriert bitgleich; v7-Begruendung sauber (driftfreie 10.000 in `vorlauf.py` Z. 158-170 gerechnet und verworfen). Kleine Ueberzeichnung "haengt nicht an der Zelle" (B-8) | - | Abschnitt 5 |
| 3 | Power-Zeile, Zuordnung, Endpower | **BESTAETIGT** (keine Abweichung > 1 %, max. 1,6e-16); (1c) ueber den effektiven Prior in `assign_regime` ist strenger als H-32-U-4 (dort nur (1b)) und mit DEC-94 (3) vereinbar | Strenge | Abschnitt 5 |
| 4 | Design ohne Pilot | **BESTAETIGT** fuer Gate, p, F-WEEK, K, Kills, Etiketten (Survivorship-Vorzeichen korrekt umgekehrt: +0,47..+0,70 T_neg, v6b +0,425/+0,538), REZENZ, Schnitt, Universum, Pins, PK-Ziel F (|m_df| korrekt addiert). **ABWEICHUNG**: adversariales Fixture prueft Momentum- statt Reversal-Artefakte (B-6); PK-Welt S nur per Auslegungs-DEC zulaessig (B-3); Speicher-Einheit der v7-p-Datei offen (B-10) | Strenge | EF Z. 188, 238; B-3, B-6 |
| 5 | C.1 / C.17 | C.1 **BESTAETIGT** (Wortlaut-Korrektur GL-032, B-9). C.17: Befund C-2 **BESTAETIGT und verschaerft** (B-2); Liste **unvollstaendig** (B-5). fm8-IC in W1/W2 ungesehen: BESTAETIGT (kein Testlauf-Verzeichnis, GL-035, DEC-101 E12) | Strenge | B-2, B-5 |
| 6 | Gabelungen | **ABWEICHUNG (gering)**: Bilanz EV 8 vollstaendig fuer die EV-Punkte; nicht gelistet: R3 vs. R4, Punktwahl im R3-Band (oberer Wert), SD-Wahl in Weg B, F2_real-Rundung (knife-edge B-4), m in F-WEEK = Zahl der C10-Eintraege. Keine davon entscheidungsrelevant unter R3; unter R1 alle in Richtung Testbarkeit | gemischt | B-4, B-7 |
| 7 | Registrierbarkeit | **BESTAETIGT** als Entwurf (zwoelf Zeilen, Gate-Text, Trio, YAML, Bauliste, UNBELEGT u1..u5); Default bei Stille fehlt (B-7); Aufwand nur bei C10 (v7 ~1..1,5 h x 2 + Bau) plausibel | - | EF Z. 88; B-7 |

## 4. Befunde

### B-1 (HOCH; Pruefpunkt 1) Die Literatur belegt fuer das Bybit-USDT-Perp-Universum eher keinen oder einen negativen Reversal-Prior; R1 ist nicht zuordenbar
- Ficura (S. 13, Tab. 7, Textextrakt p013): Das 1-Wochen-Reversal haengt am Wochenvolumen < 100 Tsd. USD (Panel B Sp. 1:
  -3,06 %, t -5,93); schon "M > 10 Mio, V < 1 Mio" zeigt **+0,54 %** (Momentum, t 0,80), "M > 10 Mio, V > 1 Mio" +1,44 %
  (t 2,08). Ficura S. 4 (p004 Z. 10-27): Reversal nur in Studien ohne Mindest-Marktkapitalisierung (Shen et al.), Momentum
  1-4 Wochen mit Groessenfilter (LTW 2022, Dobrynskaya 2023). Ein Universum aller Bybit-Perps (Listung setzt Derivate-Umsatz
  voraus; Spread-Zensus D10-Median 36 bp) liegt nach jeder dieser Abgrenzungen ausserhalb des Reversal-Treibers.
- Das Zaehl-Indiz der Herleitung (EV Z. 123-125; Ficura Tab. 1 nachgeprueft: > 10 Mio 1.083/684, > 50 Mio 601/315 Ende
  2021/2022) zeigt auf Tab. 7 A Sp. 2/3 = **R4** (Momentum). R3 ist damit die mildere der beiden belegnahen Lesarten; die
  Empfehlung "R3 (Strenge)" (EV Z. 135) ist im Ergebnis richtig, weil R3 und R4 beide GL-012 geben, die Richtungsangabe
  "Strenge" gilt aber nur gegenueber R1.
- R1 A\* (0,048/0,041/0,039) liegt auf dem Niveau der Pilotwerte (GL-035 x_P in Reversal-Richtung 0,038/0,050/0,045) und
  hat nach dem Vorstehenden keine Universums-Grundlage. Eine Wahl von R1 waere eine pilotgeleitete Prior-Wahl - DEC-102 E3
  waere umgangen. Die Herleitung nennt die Naehe (EV Z. 138-140), zieht aber nicht den Schluss "nicht zulaessig".
- Robustheit: R3 oberer Wert rev1 0,0144 < MDE80\* T 0,0184 (Fensterpower 0,617/0,714); unter S liegt die Schwelle beim
  2,7-fachen. Auch der ganze R3-FM-Bogen (0,0085..0,0144) und R4 sind GL-012.
- **Folge:** UNBELEGT bleibt formal richtig (u1..u5); inhaltlich zeigt die Literatur fuer dieses Universum auf ~0 oder
  Momentum. Die Nutzerrueckfrage muss das so sagen (A-3).

### B-2 (HOCH; Pruefpunkte 5, 6) C.17: Persistenz-Null W1/W2 - richtungsgleich, fuer rev1 in W2 schwer; DEC-102-Grundlage unvollstaendig
- Akte (registry Z. 121, Drittfassung Z. 156-168): AR(1) je Symbol auf den **Outcome-Wochenrenditen** von W1/W2; mom1-q95
  (positive Richtung) W1 -0,0064, **W2 -0,0362**; Null-Mittel mom1/2/4 -0,0036..-0,0469. Ueberschlag aus diesen Aktenzahlen
  (q95 - 1,645 x Boden-SE 0,00674/0,00587): mom1-Null-Mittel W1 ~ -0,017, **W2 ~ -0,046** (roh).
- Gewichtung: Der Kendall-Anteil der phi-Schaetzung (~ -1/T, T <= 51; bei kurzen Symbolhistorien groesser) erklaert W1
  praktisch ganz, in W2 bleibt nach grober Bereinigung ein Rest von **0 bis ~ -0,026 roh**, auf fm8-Skala (x 0,754) **bis
  ~0,02 in Reversal-Richtung**. Im realen IC wird der Kendall-Anteil durch die Querschnittsstreuung der Symbolmittel
  weitgehend ausgeglichen (Lo/MacKinlay-Zerlegung), die Grosse ist also kein fertiger Schaetzer - aber ein aus den
  W2-Outcomes gerechneter, richtungsgleicher Eigen-Autokorrelationsanteil der rev1-Statistik. Vergleich: T-MDE80 W2 rev1
  0,0161 (~1 x), S-MDE80 W2 0,0389 (~0,5 x). mom2/mom4: W2-q95 -0,0094/-0,0064 -> Null-Mittel ~ -0,019/-0,016, Kendall-gross
  (fuer mom2 ~ -1/(T sqrt 2)); leicht.
- **Schwere:** W2 ist das REZENZ-Fenster (muss bestehen). Fuer rev1 waere ein PASS auf W2 nach C.17 ("Konfirmation braucht
  ANDERE Fenster") nicht konfirmatorisch; ein DROP bliebe aussagekraeftig (der gesehene Hinweis zeigt Richtung PASS).
  W1/W2 sind fuer H-33 also nicht unbrauchbar, aber asymmetrisch: nur fuer Falsifikation, nicht fuer Bestaetigung von rev1.
  Unter T waere der Vorab-Hinweis von der Groesse der Schwelle - ein weiterer Grund gegen T (B-3).
- Die Vorlage DEC-101 Teil 3 (a), auf der der Nutzerentscheid DEC-102 beruht, nennt diesen Befund nicht; das DEC-102-E2-
  Etikett spricht nur von "einem anderen Fenster". Die Herleitung hat das gefunden (EV Z. 46, 58-65) - richtig und wichtig.
- Empfehlung: EV-0 Option (b) (strenge Lesart) als Review-Position; mindestens das Etikett (A-2) und die Nutzerkenntnis (A-3).

### B-3 (MITTEL; Pruefpunkte 4, 6) Lesart T/S: S ist die regelkonforme Lesart, braucht aber eine Auslegungs-DEC vor der Nutzerfrage
- Fuer S: DEC-94 (3) verlangt Power mit der SE-Regel des Gates und bei datenabhaengiger SE "die SD der getesteten
  Statistik, nie ein Rauschboden allein (DEC-92-Lehre)". Der Test rechnet SE_W = max(Boden, SD(IC_t)/sqrt(W), SE_stat) und
  k = SD(IC_t)/sd_week mit der **realen** SD. Traegt der GL-035-Nebenbefund (2,2..2,5 x Null-SD; k_pred W1/W2 rev1 2,20/2,49
  nachgerechnet) nach W1/W2, ist die reale Power bei T-Zuordnung die von S (rev1 bei 0,020: T 0,795 gemeinsam, real ~0,12).
  Das ist der DEC-91-Fehler (Zuordnung mit zu kleiner SE). Unter T waere die PK-Welt die Null-Welt (sigma_g = 0, EF Z. 207);
  die 10-%-Regel von DEC-94 (5) waere leer.
- Gegen S (Wortlaut): DEC-94 (5) (i) verlangt "kein Mittel ausgegeben"; das Pilotmittel ist ausgegeben; DEC-99 (6) hebt das
  nur fuer Registrierungen mit Pilotfenster auf; DEC-101 Teil 3 sagt "Keine Regelaenderung". Die Herleitung nennt das selbst
  (EV Z. 201-205).
- Urteil: S zulaessig als **Auslegung in Richtung Strenge** (nur Streuung, kein Mittel; jede Wirkung senkt Power und hebt die
  PK-Anforderung), festzulegen per DEC **vor** der Nutzerfrage, mit Etikett "Streuungs-Nuisance aus GL-035 (DEC-94 (5) (i)
  sinngemaess), kein Mittel; beschlossen nach Kenntnis von GL-035; Strenge". Dem Nutzer wird dann nur das S-Gitter als
  bindend vorgelegt (T nur Bericht), damit T/S keine Gabelung nach der Prior-Wahl wird.
- Nebenbedingung: F2_ref muss mit voller Stellenzahl aus `h32_pilot.json` (sha256-Pin) kommen, nicht aus der md-Tabelle
  (B-4).

### B-4 (MITTEL; Pruefpunkte 3, 6) Knife-edge: rev2 bei R1 unter S haengt an der 6. Stelle
- R1-A\*-Prior rev2 0,04148884; S-MDE80 W2 (1b) 0,04148848 (Marge **+3,6e-7**) mit F2_real 0,012016 (h32_pilot.md); mit der
  GL-035-Rundung 0,01202 wird die Marge **-5,6e-6**. Derzeit bindet (1c) (W1 0,04180, Marge -3,2e-4) - aber (1c) ist
  vorlaeufig (Form der Drift-Zelle). Ist die negative Flanke der driftfreien Zelle um mehr als ~1,5e-4 (W1) bzw. ~1,1e-4
  (W2) duenner (k 2,11/2,45; in der positiven Flanke unterscheiden sich die Zellen um bis zu 6e-4), entscheidet die
  (1b)-Marge von 3,6e-7.
- Die Aussage "unter S nur rev1 C10" (EV Z. 138) ist damit fuer rev2 nicht belastbar; das Regime haengt an Rundung
  (F2_real, fm8-Faktor 0,75423) und an v7. Unter R3 irrelevant.

### B-5 (MITTEL; Pruefpunkt 5) C.17-Liste unvollstaendig: WP-7-Artefakte mit IC-Niveaus
- `state/runs/wp7_20260921/survivorship_bias_UNION_REAL.json` (sha256 laut wp7_report.md Z. 163 `4fb81859...c90d`) traegt
  laut Schluesselnamen `rho_with`, `rho_without`, `bias_point`, `bootstrap.*` - also die **Niveaus** des rohen
  4-Wochen-Momentum-IC ueber 271 Wochen (ganze Historie inkl. W1/W2 und Wochen nach 2026-07-01), nicht nur die Differenz.
  `wp7_report.json` (`findings`) kann dieselben Werte tragen. Die H-32-Akte fuehrt die Datei als "nie geoeffnet"
  (H-32 EV Z. 19, Review H-32 Z. 14); die H-33-Liste (EV Z. 55, EF Z. 280) nennt sie nicht. Ob sie je jemand gelesen hat, ist
  nicht dokumentiert.
- Weitere fehlende, richtungstragende Kleinigkeit: gemessenes rho_f (Markt-Autokorrelation, v5d W1 0,046 / W2 0,042, DEC-86
  Nachtrag; v6b-Kalibrierung analog) - positiv, also gegen H-33; nur ausdruecklich zu nennen.
- Folge: in C.17 als "vorhanden, Niveaus des rohen mom4-IC inkl. W1/W2, nicht geoeffnet (Herleitung, Review: nur
  Schluesselnamen)" fuehren und die beiden Dateien in die Abweisungsliste des Codes aufnehmen (A-4).

### B-6 (MITTEL; Pruefpunkt 4) Adversariales Fixture ist in Reversal-Richtung wirkungslos
- Zeile 5 / T1 adversarial (EF Z. 188, 238): Beta-Proxy bei persistentem (rho 0,2), driftendem Markt. Drift beider Vorzeichen
  und positive Persistenz erzeugen mechanisches **Momentum** - in negativer Richtung kann dieses Fixture nie PASS geben; es
  prueft nichts.
- Fuer H-33 muss das Fixture **mechanisches Reversal** erzeugen: Beta-Proxy bei mean-revertierendem Markt (rho_f < 0, z. B.
  -0,2, Beta-Streuung 0,5..2,0) -> kein PASS in negativer Richtung unter fm8; dazu Bounce und Survivorship-drop (vorhanden)
  sowie ein Fixture mit Null-/Stale-Renditen illiquider Symbole (returns_valid). Richtung: Strenge.

### B-7 (NIEDRIG; Pruefpunkte 6, 7) Gabelungs-Bilanz und Default
- Nicht gelistete Gabelungen: R3 vs. R4 (R4 strenger, gleiches Ergebnis); oberer statt mittlerer R3-Wert (Testbarkeit,
  folgenlos); SD-Wahl in Weg B (Null-SD statt der aus der Quelle implizierten 0,24 je Woche, BELEGE 4 - Strenge); F2_real-
  Stellenzahl (B-4); "m = 3" in F-WEEK ist eine Obergrenze - m = Zahl der tatsaechlich getesteten (C10-)Eintraege der Welle
  (Strenge der Anzeige, kein Fehler). "MDE80 >= ~0,035" fuer das Teiluniversum (EV Z. 180) ist ein Ueberschlag ohne
  `power_p1` (nur Bericht, als solcher kennzeichnen).
- Default bei Stille fehlt: EF Z. 88 "Default bei Stille: keiner - UNBELEGT blockiert". Autonomie-Protokoll 3 verlangt einen
  dokumentierten Default. Vorschlag: "GL-012 vor der Registrierung fuer alle drei Eintraege (Prior UNBELEGT; Literatur fuer
  dieses Universum ~0/Momentum), kein Bau, kein v7, W1/W2 bleiben fuer fm8-Reversal ungeoeffnet".

### B-8 (NIEDRIG; Pruefpunkt 2) "Zuordnung haengt nicht an der Zelle" leicht ueberzeichnet
- Unter T liegt (1c) in W1 rev2 nur 1,4 % (abs. 1,9e-4) unter (1b); in der positiven Flanke ist die driftfreie Zelle dort
  um 2,7e-4 breiter als die Drift-Zelle (W1 mom4: 6,1e-4 duenner). Gilt das auch fuer die negative Flanke, bindet nach v7 in
  W1 rev2 (1c); Wirkung auf MDE80 <= ~0,5 %. Satz EV Z. 235-236 entsprechend abschwaechen.

### B-9 (NIEDRIG; Pruefpunkte 1, 5) Wortlaut
- Rezentrierung (1c) ist keine "Abweichung zur Strenge" (EV Z. 253, EF Abschnitt 9 Nr. 5), sondern Pflicht: DEC-94 (3)
  (Power mit der Entscheidungsregel des Gates) + DEC-101 E2 (q95_eff = max(0, m) + k (q95 - m)); Praezedenz `handover.term_1c`
  ("for m_W < 0 (rev_gap) it is q95 + |m| + z_80 SD_T"). Der Auftragswortlaut waere eine Lockerung (W1 rev1 0,0168 statt 0,0181).
- Weg B "Untergrenze" (EV Z. 93) mit BELEGE 4 begruenden (implizierte Quell-SD 0,24 je Woche gegen 0,051), nicht mit GL-035 -
  so bleibt die Prior-Herleitung frei von Pilot-Bezuegen.
- C.1 (EF Z. 290): "die Positivkontrolle bestand fuer rev_gap" -> "Positivkontrolle insgesamt NICHT BESTANDEN (rc 3); rev_gap
  3/3 Seeds" (GL-032).
- Bounce (EV Z. 259-264): die Zufallsrate 2..6,5 % gilt fuer einen beliebigen Seed; fuer den registrierten Seed 53 sind die
  Werte bekannt (|IC_bounce| / T_neg: W1 0,13/0,34/0,60, W2 0,38/0,64/0,82) - der Ein-Seed-Kill trifft keinen Wert, der (1b)
  besteht. Der Wechsel auf das 200-Seed-Mittel (|Mittel| <= 5,3e-4, analytisch ~1e-4) ist methodisch richtig (Schaetzung des
  mechanischen Erwartungswerts, seed-unabhaengig), aber **entscheidungsneutral**; Etikett "Richtung Testbarkeit" durch
  "neutral (Seed 53 bekannt)" ersetzen. Die PK nutzt im H-32-Code einen festen Bounce-Wert (Seed 53, `positive_control.py`
  Z. 427), keinen je Urteils-Seed - kein PK-Risiko.

### B-10 (NIEDRIG; Pruefpunkt 4, nur bei C10) Einheit der v7-p-Datei
- EF P4' verlangt "die ersten 1.000 reproduzieren das eingefrorene null_mean_neg", die YAML-Formel spricht von
  "d_neg = -raw replicate", die Bruecke vergleicht Roh-Hashes. Festlegen: v7 speichert die Replikate in registrierter
  Richtung (y = -IC, wie `pnull.build_payload` "unit: registered direction"), zusaetzlich `draws_sha256_raw` je Zelle fuer die
  Bruecke zu v6b.

## 5. Nachrechnungstabelle (Herleitung vs. Review; `[fj: power_h33.json#...]`, `nuisance_neg.json`, `h33_review/out1.json`)

| Groesse | Herleitung | Review | Abw. |
|---|---|---|---|
| null_mean_neg driftfrei / Drift W1 rev1, rev2, rev4 | -0,001221/-0,001290, -0,001583/-0,001679, -0,001934/-0,002066 | gleich | 0 |
| dto. W2 | -0,000847/-0,000936, -0,001379/-0,001502, -0,001784/-0,001953 | gleich | 0 |
| bindende Zelle negativ (6 Faelle) | driftfrei | driftfrei | 0 |
| q95_neg Drift 1.000 / 10.000 W1 rev1/rev2/rev4 | 0,009992/0,010696, 0,010274/0,011489, 0,012377/0,012766 | gleich (auch als -Q_0,05 der Rohreihe) | 0 |
| dto. W2 | 0,009019/0,009293, 0,009668/0,009825, 0,010826/0,010857 | gleich | 0 |
| dev95 Drift W1 / W2 rev1, rev2, rev4 | 0,011986/0,010229, 0,013168/0,011327, 0,014832/0,012811 | gleich | 0 |
| Decke K = 3 roh 1.000 / roh 10.000 / rezentriert 10.000 W1 | 0,001851 / 0,002264 / 0,003936 | gleich | 0 |
| dto. W2 | 0,001658 / 0,001678 / 0,003114 | gleich | 0 |
| Decke/T max (rezentriert) | 0,322 (W1 rev1) | gleich | 0 |
| MDE80 T W1 (1b/1c) rev1, rev2, rev4 | 0,018385/0,018132, 0,020169/0,019977, 0,023633/0,023053 | gleich | 0 |
| MDE80 T W2 (1b/1c) | 0,016121/0,015444, 0,017583/0,017257, 0,020020/0,019704 | gleich | 0 |
| MDE80 S W1 (1b/1c) | 0,038892/0,039529, 0,041388/0,041804, 0,042878/0,042460 | gleich | 0 |
| MDE80 S W2 (1b/1c) | 0,038897/0,038595, 0,041488/0,041761, 0,043033/0,043110 | gleich | 0 |
| k_pred S W1/W2 rev1, rev2, rev4 | 2,1996/2,4861, 2,1108/2,4471, 1,8842/2,2281 | gleich (GL-035: 2,20/2,49, 2,11/2,45, 1,88/2,23) | 0 |
| (1c) ohne Rezentrierung W1 rev1 (Bericht) | 0,016842 | gleich | 0 |
| Gitter T rev1 0,020: W1/W2/gem./Regime/A3/EP3/EP14 | 0,856/0,929/0,795/C10/GL012/0,610/0,249 | gleich (EP auch geschlossen: 0,610/0,249) | 0 |
| Gitter T rev2 0,020 | 0,794/0,882/0,700/DEC52 (0,811)/GL012/0,495/0,171 | gleich | 0 |
| Gitter T rev4 0,025 | 0,837/0,926/0,775/C10/GL012/0,599/0,263 | gleich | 0 |
| Gitter S rev1 0,048 | 0,917/0,923/0,846/C10/GL012/0,698/0,345 | gleich | 0 |
| Gitter S rev2 0,048 / rev4 0,048 | 0,888/0,888/0,788/C10 / 0,873/0,870/0,759/C10 | gleich | 0 |
| alle 36 Gitterzeilen x (W1, W2, Regime, A3, EP3, EP14), beide Lesarten | - | 300 Vergleiche, max. rel. 1,6e-16 | 0 |
| BY-Schwelle m = 3 / 14; z_max(3) | 0,018182 / 0,002197; 0,8528 | gleich | 0 |
| R1 A\* fm8 rev1/rev2/rev4 | 0,0484/0,0415/0,0390 | 0,04842/0,04149/0,03901 | 0 |
| R3 Ficura / LTW-FM fm8 rev1 | 0,0015..0,0022 / 0,0085..0,0144 | gleich | 0 |
| R4 A\* fm8 rev1/rev2/rev4 | -0,0248/-0,0262/-0,0153 | gleich | 0 |
| R1 Weg B fm8 rev1 W1/W2 | 0,0166/0,0144 | gleich | 0 |
| Review-Zusatz: R1 rev2 vs. S-MDE80 W2 (1b) | - | 0,04148884 vs. 0,04148848 (+3,6e-7; mit F2 0,01202: -5,6e-6) | B-4 |
| Review-Zusatz: Persistenz-Null mom1 roh (Aktenzahlen) | -0,0036..-0,047 | W1 ~ -0,017, W2 ~ -0,046 (Ueberschlag) | B-2 |

## 6. Auflagen (vor der Nutzerrueckfrage bzw. vor jeder Registrierung)

- **A-1 (vor der Rueckfrage, DEC des Orchestrators):** EV-2 (K = 3), EV-3 (**Lesart S** als Auslegung DEC-94 (3)/(5) in
  Richtung Strenge, Etikett B-3), EV-4 (v7 nur bei C10), EV-5 ((1c) rezentriert als Pflicht; Bounce-Mehrseed als neutral),
  EV-6 (nur C10) beschliessen, bevor der Nutzer eine Prior-Zahl sieht oder nennt.
- **A-2:** DEC-102-E2-Etikett per Nachtrag ergaenzen: "... und nach Kenntnis eines richtungsgleichen, modellbasierten
  Eigen-Autokorrelationsanteils derselben Fenster W1/W2 (Persistenz-Null v5d, mom1 W2 deutlich)". In allen H-33-Dateien fuehren.
- **A-3 (Inhalt der Nutzerrueckfrage nach DEC-102 E3):** (i) Prior UNBELEGT; Literatur zeigt fuer ein Perp-Universum mit
  Groessen-/Umsatzfilter ~0 oder Momentum (B-1); (ii) S-Gitter bindend, T nur Bericht; (iii) R1 liegt auf Pilot-Niveau und
  ist fuer Perps nicht belegt - Wahl = pilotgeleitet; (iv) EV-0/B-2 mit der Gewichtung dieses Reviews; (v) Vorab-VETO des
  Reviews fuer C10 auf W1/W2; (vi) dokumentierter **Default bei Stille: alle drei GL-012 vor der Registrierung, kein Bau,
  kein v7, W1/W2 bleiben fuer fm8-Reversal ungeoeffnet**; (vii) Alternative ist nur ein blindes Fenster ab 2026-07-01
  (Reihenfolge-Frage DEC-98 E4 (b)) - mit einem Literatur-Prior von <= 0,0144 waere H-33 aber auch dort auf absehbare Zeit
  GL-012 (unter S skaliert MDE80 ~ 1/sqrt(W); 0,0144 verlangt grob das 7-Fache der heutigen Fensterlaenge).
- **A-4 (C.17):** Liste um B-5 (WP-7-Survivorship-JSON / `wp7_report.json` mit IC-Niveaus; gemessenes rho_f) ergaenzen;
  beide Dateien in die Abweisungsliste aufnehmen; Wortlaut C.1 (GL-032) und Weg-B-Begruendung nach B-9 korrigieren.
- **A-5 (nur falls ein Eintrag C10 wird):** v7 wie EV-4 (beide Zellen, 10.000, beide Replikatsaetze gespeichert, Bruecke,
  zweimal bitgleich); F2_ref mit voller Stellenzahl aus `h32_pilot.json` (sha256 `be20a826...`) pinnen; Einheit der p-Datei
  nach B-10; Regime erst nach v7 feststellen (B-4: rev2 ist bei R1/S vorher unentscheidbar); F-WEEK m = Zahl der C10-Eintraege.
- **A-6 (nur bei C10):** adversariales Fixture nach B-6 (rho_f < 0, Stale-Renditen) in Zeile 5 und T1.
- **A-7:** Kennzeichnungen nach B-7/B-8/B-9 (Default, Ueberschlag "MDE80 >= ~0,035", "haengt nicht an der Zelle", Rezentrierung
  = Konformitaet, Bounce = neutral).

## 7. Empfehlung an den Orchestrator

| Frage | Empfehlung | Richtung | Grund |
|---|---|---|---|
| Prior-Lesart | **R3 (mit R4 als Robustheit)** -> alle drei GL-012 vor der Registrierung; R1 nicht als Literatur-Prior anbieten, nur als Gitterwert mit Etikett "pilotgeleitet" | Strenge | B-1 |
| v7 | **nein** (unter R3/R4 kein C10); ja nur nach A-5 | - | EV-4 bestaetigt |
| Nuisance / PK-Welt | **Lesart S** per DEC vor der Rueckfrage | Strenge | B-3 |
| EV-0 | **(b) strenge Lesart** als Programmposition; mindestens Etikett + Nutzerkenntnis | Strenge | B-2 |
| DEC-52-Zweig | nur C10 (EV-6) | Strenge | unter S ohnehin ohne Wirkung |
| Bounce | 200-Seed-Mittel, Etikett "neutral" | neutral | B-9 |
| Registrierung | keine; GL-Vermerk "GL-012 vor der Registrierung (Prior UNBELEGT)" nach der Rueckfrage oder dem Default | - | - |

Bei Widerspruch Orchestrator/Herleitung/Review: Der einzige inhaltliche Unterschied zur Herleitung ist die Schaerfe bei R1
(Herleitung: "nur mit Nutzerentscheid und Etikett"; Review: bedingtes VETO auf W1/W2) und EV-0 (Herleitung: (a) mit
Nutzerkenntnis; Review: (b)). Beides wird nur relevant, wenn der Nutzer gegen den Default eine C10-Lesart waehlt.

## 8. Was NICHT folgt

- Kein Verdikt ueber Kurzfrist-Reversal, Momentum oder die fm8-Statistik; keine Registrierung; GL-035, DEC-101, DEC-102
  unveraendert (A-2 ist ein Nachtrag-Vorschlag).
- Keine Aussage, dass W1/W2 Reversal enthalten: Die Persistenz-Null-Gewichtung in B-2 ist ein Ueberschlag aus Aktenzahlen
  (modellbasiert, roh, Kendall-verzerrt) und dient nur der C.17-Schwere.
- Die Nachrechnung bestaetigt die Arithmetik auf dem v6b-Artefakt, nicht die Realitaet der Null (GL-035-Nebenbefund).
- (1c)-Werte bleiben vorlaeufig (Form der Drift-Zelle) bis zu einem etwaigen v7.
- Das Review hat W1/W2, Siegeldateien, `h32_pilot.json`, die Pilot-Wochenreihen und die v5-Artefakte nicht geoeffnet; von
  `survivorship_bias_UNION_REAL.json` nur Schluesselnamen gelesen.

## 9. Reproduktion

`python3 -I scratchpad/h33_review/review_h33.py /home/user/scinance > out1.json` (zweimal, bitgleich; sha256 `97f76824...6fbe`).
Eingaben-sha256 im Kopf von `out1.json`: v6b `f872a3af...f98c`, Replikate `3c498e07...56ef`, power_h33 `026494b6...5bc9`,
nuisance_neg `05e6f2a0...0835`. Inhalt: Umrechnung negativ (unabhaengig, -Q_0,05 und Quantil von -d), Power-Zeilen T/S
(inkl. GL-035-Rundung), Gitter mit `power_p1.assign_regime`/`assign_regime_a3_practice`, Endpower mit
`estimators.end_power_replicates` und geschlossener Gegenrechnung, Decken, Literatur A\*/FM, Vergleich mit den JSON der
Herleitung, Persistenz-Null-Ueberschlag aus Aktenzahlen.
