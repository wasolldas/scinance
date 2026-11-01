# REVIEW_PRD_ANALYSE - Adversarischer Review der vier Analysen der PRD-Gesamtanalyse (Stand 2026-11-01)

> Rolle: Reviewer (Gate-Auditor, Richtung Strenge). Gegenstand: `state/prd_analyse_2026-11-01/` KRITIK_PRD.md, EDGE_INVENTUR.md,
> KONZEPT_UND_FORSCHUNGSFELDER.md, ARCHITEKTUR_AUTOMATION.md; Hilfslisten FAKTENBLATT_STATUS.md und LISTE_DEC_GL.md
> nur als Index benutzt (nicht vollstaendig geprueft). Geprueft gegen die Primaerquellen der Leseliste (PRD, Verfassung,
> Kompendium, decisions, gate_log, Bilanz, A2-Akte, BELEGE_AUS_PDF, KONTAMINATION.md, Dateninventar 2026-11-01,
> DATA_INVENTORY_2026-08-10), nicht gegen die Analysen untereinander.
> Nur gelesen; nichts im Repo geaendert oder committet; kein Harvest-Client, kein Netz, keine Siegeldatei geoeffnet
> (unter `state/runs/` nur Dateinamen gelistet), keine Outcome-Statistik. Eigene Nachrechnung ausschliesslich mit
> Formeln und synthetischer Simulation: `state/prd_analyse_2026-11-01/scripts/review_calc.py` (`python3 -I`, Seeds fest; Gitterintegration
> fuer die gruppensequentiellen Zahlen).
> Kennzeichen: [F] Fakt mit Fundstelle, [R] eigene Rechnung, [U] Urteil des Reviewers, [V] Vermutung.
> Richtung: Strenge / Testbarkeit / neutral. Zustaendigkeit: N = Programmfrage des Nutzers (PRD Par. 8), O = Orchestrator.

---

## 0. Urteil je Analyse

| Analyse | Urteil | Kern |
|---|---|---|
| KRITIK_PRD | **ZUSTIMMUNG MIT AUFLAGEN; VETO gegen Uebernahme von drei Punkten** | K-1, K-2, K-3, K-4, K-6 (PPV), K-9 rechnerisch bestaetigt (Abschnitt 2). VETO gegen (a) K-5 (1) "Null-Bedingung streichen, Rechenartefakt, neutral, O" (B-1), (b) die Aussage "A2 heute registrierbar gegen Taker-SESOI" in K-10 / K-6 / Abschnitt 8 (B-2), (c) die H-27-Rueckwirkung "L ~22 Monate, Urteil ~2030" mit dem ueberholten Prior 9,47 VP (B-3). |
| EDGE_INVENTUR | **ZUSTIMMUNG MIT AUFLAGEN** | Faktentreu in allen 14 Stichproben bis auf D.17 (B-9). Rechnungen R-1 bestaetigt; Lesart "100 % Pilot-Betrag" und "unplausibel hoch" zu relativieren (B-15); H-21-Aussage in der Kurzfassung ohne Vorbehalt (B-16). Kein Veto. |
| KONZEPT_UND_FORSCHUNGSFELDER | **ZUSTIMMUNG MIT AUFLAGEN; VETO gegen Uebernahme von vier Punkten** | Diagnose T-1, T-2, T-11, T-13, T-14 tragfaehig. VETO gegen (a) F1 "loest IC 0,006-0,013 auf ... unter heutigen Regeln registrierbar" (B-4), (b) Power-Zahlen der BTC/ETH-Tagesfelder (T-8/T-9, F2a, F3, F4, F6) ohne Siegel- und Vorwissens-Etikett (B-5), (c) die Begruendung "W1/W2 faktisch nicht mehr blind" in T-12 (4) und die DEC-95-Lesart in T-5 (B-6), (d) das Etikett "neutral in alpha" fuer den Ersatz von C.10 durch ein Budget-Regime (B-7). |
| ARCHITEKTUR_AUTOMATION | **ZUSTIMMUNG MIT AUFLAGEN** | Faktentreu (61 Scratch-Verweise, 656.775 Byte, 221.371 Byte, OBF-Zahlen nachgerechnet). Auflagen: VRP-Beispiel mit ueberholtem Prior (B-3), Kohorten-Datenfaktor 1,54 nicht vergleichbar mit Serialisierung (B-8), Reproduktion nur ohne Neulauf siegeldateierzeugenden Codes (B-20). Kein Veto. |

**Stichproben Faktentreue (Punkt 1 des Auftrags).**

| Analyse | geprueft | abweichend | Abweichungen (Befund) |
|---|---:|---:|---|
| KRITIK | 17 | 4 | Prior 9,47 statt 7,14 (B-3); A2-Kette ohne skalierte Null (B-1); "2.0 starb an der Friktionswand" ist kein PRD-Zitat (B-13); Tardis-Monate inkl. Siegelmonate (B-9) |
| EDGE | 14 | 1 | D.17 "beruht auf 2 Tagen" (B-9) |
| KONZEPT | 14 | 6 | DEC-95 E2 (B-6); DEC-103 N1 (2) (B-6); "14 Monate 3.0" (PROGRAMMENTWURF Stand 2026-09-02, also 2 Monate); "sechs Gate-Eintraege (GL-032..036 plus H-32-Pilot)" (GL-035 IST der Pilot: fuenf); Bianchi als [sek] statt [PDF]/[abg.] (B-4); IC_min-Zuordnung phi 0,5 (B-18) |
| ARCHITEKTUR | 12 | 1 | VRP 2 x 672 Tage / voll 2030-04-04 mit ueberholtem Prior (B-3) |

Geprueft und ohne Befund u. a.: PRD 9.2 K-0.1 (6,6 h / 53 min / 2,7 Tage), R4 1.2.d (arcsin-Formel, 0,031 / 0,062),
PRD 3.6 Lo-Beispiel, PRD 3.5 und K-0.6, PRD 4.1 (0,344886), PRD 7.1/7.2 (41 min, "nicht nachholbar", OI "kritischste"),
PRD 5.5 (~38 Tage), DEC-94 (1)-(9), DEC-97 A-2 (c 28,2 / Konsens 18,6 / 14 % / Power 0,73), DEC-98 E1 (b)-(d), N2, N4 (f), N5,
DEC-99 (1)-(9), DEC-103 E1-E8 und N1 (2), (3), (6), (8), (9), REVIEW_A2_TEILC B-4, GL-035-Tabelle, DEC-84 (46,7 %, 412/409),
NUISANCE_SIGMA30 (43,8 bp; 0,82 [0,69; 0,98]), KONTAMINATION.md K-1..K-12, Inventar (allLiquidation 125/139,
tardis 91/2.741, kline1d 2.130/2.130), BELEGE_AUS_PDF 3.2/4 (Bianchi), Kompendium D.1-D.17 und E.1.

---

## 1. Befunde

### B-1 KRITIK K-5 (a)/(1): Die "doppelt gezaehlte Null-Bedingung" ist keine reine Rechnung, sondern eine dokumentierte, teils echte Strenge-Lesart; die Kette 27,2 -> 32,1 ist falsch zugeordnet
- **Stelle.** KRITIK K-5 Tabelle und Einzeldefekt (a); Vorschlag (1) "aus dem Produkt streichen (Rechenkorrektur, neutral, O)";
  Kurzfassung Punkt 4.
- **Befund [F].** REVIEW_A2_TEILC B-4 hat genau diesen Punkt am 2026-10-31 gefunden und als **Lesart** (Default Strenge,
  Gabelung G-C5/P-G3) ausgewiesen; DEC-103 N1 (8a) hat ihn nach Kenntnis von B-4 bewusst festgelegt ("Null-Bedingung als
  eigener Faktor im Produkt (Zuordnung), exakte P2''-Bedingung als Bericht"). Die beiden Bedingungen sind im
  Zuordnungsmodell **nicht identisch**: Modell-Korrelation 0,91 (W1) / 0,82 (W2), weil in W2 12 von 52 Wochen nicht
  permutierbar sind (kappa 0,815, DEC-103 N1 (5)); B-4: "In W2 ist der Beitrag ueberwiegend echt (Null-Bedingung allein
  19,1 > z 18,8)". Die Akte fuehrt die korrekte gemeinsame Rechnung bereits: MDE80 mit exakter P2''-Bedingung
  **22,93 / 23,77** gegen Produkt 23,43 / 24,36 (W1/W2). Der Artefakt-Anteil ist also 0,5..0,6 bp, nicht die 1,3 bp
  (23,1 -> 24,4) der KRITIK-Tabelle.
- **Zweiter Fehler [F/R].** Die KRITIK-Tabelle springt von 27,2 ("Stress bindend") auf 32,1 und schreibt die 4,9 bp allein
  dem Gate-(4)-Faktor zu. Laut DEC-103 N1 (9) ist die Zusammensetzung in W2: Stress +2,8, **skalierte Null +2,1**
  (k_pred,W 1,215), Gate (4) +2,8 -> 24,4 + 2,8 + 2,1 + 2,8 = 32,1 [R]. KONZEPT T-13 gibt die Kette richtig wieder.
- **Rechnung [R].** Zwei Bedingungen mit je Power 0,90: Produkt 0,810; exakt bei Korrelation 0,82 / 0,91 / 1,0:
  0,858 / 0,870 / 0,900. "Quadriert" ist nur der Grenzfall Korrelation 1.
- **Folge [U].** Die Diagnose "Produktregel bei korrelierten Ereignissen ist zu streng" stimmt; die Groesse ist klein und
  bereits beziffert. "Streichen" waere falsch (es verwirft den echten W2-Anteil). Die Aenderung ist keine Rechenkorrektur,
  sondern eine Gabelung **Richtung Testbarkeit** gegen eine vor der ersten A2-Zahl mit Prior, aber nach Kenntnis der
  Pilot-Power-Tabelle getroffene Strenge-Festlegung.
- **Auflage.** (i) KRITIK-Tabelle korrigieren (skalierte Null als eigene Zeile; 24,4 -> 27,2 -> 29,3 -> 32,1).
  (ii) Vorschlag (1) umformulieren: "exakte P2''-Bedingung (Akte: 22,93 / 23,77) statt Null-Faktor als
  Zuordnungsgrundlage; Richtung Testbarkeit, alpha unveraendert; O mit Etikett 'nach Kenntnis REVIEW_A2_TEILC B-4'".
  (iii) K-5 (2) (exakte gemeinsame Power statt Produkt) aendert DEC-94 (6) und bleibt N.

### B-2 KRITIK K-10 / K-6 / Abschnitt 8: "A2 heute registrierbar gegen Taker-SESOI 22 bp" gilt fuer kein festgelegtes A2-Design
- **Stelle.** K-10 Tabelle (A2 "gegen die Taker-SESOI registrierbar, ohne V-5b"), Rueckwirkung "DEC-103: A2 auf W1/W2
  registrierbar ohne Pilotroute", K-6 ("A2 ... waere testbar"), Abschnitt 8 Zeile DEC-103, Kurzfassung Punkt 8.
- **Befund [F/R].** Unter dem geltenden Placebosatz (DEC-103 E3: drei Placebos, Konjunktion) liegt die MDE80 in W2 bei
  exakt gemeinsam 22,3 (zentral, Bericht), Produkt 24,4, stress 27,2 bp (DEC-103 N1 (6)) - **alle > 22**. Unter 22 kommt
  nur (a) der Einzel-Placebo P2'' (18,8; verwirft P3fix/P3all, widerspricht DEC-103 E3) oder (b) ein gepoolter Test
  (16,7 bp bei alpha 0,01 / 19,2 bp bei 0,0025 [R]; aendert die Fehlerrate bzw. C.10 -> N). Mit der Maker-SESOI
  (2 x 5,4 = 10,8 bp, ebenfalls in K-10 genannt) ist A2 in **keiner** Lesart registrierbar [R].
- **Etikett fehlt [U].** Die Wahl "Taker statt Maker" als SESOI-Basis ist bei A2 genau die Gabelung, die zwischen
  "registrierbar" und "nicht registrierbar" entscheidet - Richtung Testbarkeit, nicht ausgewiesen. Zudem stammt die
  SESOI aus der Wand, deren Unsicherheit K-1 selbst mit Faktor ~2,5 (Modell) x ~4 (Kosten) im Horizont beziffert; das PRD
  hat die Feasibility 2026-09 gerade wegen des Kostenbasis-Widerspruchs (Faktor 23 zwischen vier Lesarten, PRD 4.1, 9.3
  B-7) von der Wand entkoppelt - K-10 nennt diesen Grund nicht.
- **Innerer Widerspruch [F].** K-6 und Abschnitt 8 erklaeren "A3-Roh-IC unter measured (MDE 0,024) testbar" gegen den
  PRD-Prior 0,03, den K-10 (4) selbst als unbelegt einstuft (DEC-98 N2: "fuer ein breites Perp-Universum nicht gestuetzt").
- **Folge.** Die Kernidee SESOI statt Literatur-Prior (K-10) bleibt diskutierbar (N); die Folgerung "A2 heute
  registrierbar" darf nicht in die Synthese.
- **Auflage.** A2-Zeile: "registrierbar nur bei N-Entscheid fuer (a) gepoolten Test oder (b) Einzel-Placebo, und nur mit
  Taker-SESOI (Gabelung Richtung Testbarkeit)"; A3-Zeile: "gegen welchen Wert?" offen lassen.

### B-3 KRITIK K-7 / K-2-Rueckwirkung / Abschnitt 8 und ARCHITEKTUR 3.5: VRP-Zeitlinie mit ueberholtem Prior
- **Befund [F].** 9,47 VP war der H-27-Prior in DEC-97; DEC-98 Nachtrag 2 stellt fest: "Der zentrale H-27-Wert 9,47 VP
  ist nicht gestuetzt", Referenz pi-2 **7,14 VP**, Band 3,2..10,5. KRITIK ("H-27 waere mit L ~22 Monaten ... registrierbar
  gewesen (Urteil ~2030)") und ARCHITEKTUR 3.5 ("2 x 672 Tage ab 2026-07-01, voll 2030-04-04") rechnen mit 9,47.
- **Rechnung [R].** SE(12 Monate) = 18,6 x sqrt(28,2/365) = 5,17 VP; Prior 7,14: SR_eff 1,381 -> 1.183 Tage je Fenster
  (voll ~2033-01, wie EDGE E-22 und DEC-98 N5); 10,48: 549 Tage; 3,16: 6.040 Tage. K-2s Kernaussage (Klasse P braucht
  SR_eff >= 2,486 / 1,758 / 1,436 bei 1 / 2 / 3 Jahren je Fenster) ist davon unberuehrt und bestaetigt.
- **Auflage.** Beide Analysen auf 7,14 VP (Band) umstellen; "Urteil ~2030" -> "2029-07 (oberer Rand) .. 2033-01 (Referenz)".

### B-4 KONZEPT T-9 / F1 / Kurzfassung 5 und 9: Tages-Querschnitts-Reversal ueberzeichnet; Prior beschreibt nicht die registrierte Statistik
- **Stelle.** 0. Punkt 4, Felder-Tabelle F1, "F1 und F5 ... unter heutigen Regeln registrierbar", Kurzfassung 5 und 9.
- **(a) Fenster [F/R].** "N 2.130" ist das ganze Panel 2021-01..2026-10. Davon ist der Pilotabschnitt 2022-04-18..
  2024-06-24 fuer jede korrelierte Statistik verbraucht (DEC-99 (5): "gleiche Charakteristik-Familie, andere ...
  Formationslaenge"; Tages-Reversal ist Vergangenheitsrendite mit kuerzerer Formation), die Tage ab 2026-07-01 sind fuer
  Klasse W gesperrt (DEC-98 E1 (b)). Urteilstragend bleiben unter geltenden Regeln W1/W2 (je 365 Tage, C.10). Mit der
  KONZEPT-Annahme (SD = 2,5 x 1/sqrt(K-1)): MDE80 je Fenster **0,0133 / 0,0146 / 0,0188** (K 600 / 500 / 300) gegen
  KONZEPT 0,006-0,013 - Faktor 1,7..2,4 in der IC, 3..6 in den Daten [R]. (0,013 der KONZEPT-Spanne entspricht K 300 bei
  N 730.)
- **(b) Prior [F].** Bianchi/Babiak/Dickerson steht in BELEGE_AUS_PDF als **[PDF], zulaessig**; die IC-Werte 0,090 (EW) /
  0,023 (VW) sind dort **[abg.] nach Weg A** (Mittel unter Normalitaet), und BELEGE 4 laesst ausdruecklich offen, ob Weg A
  oder Weg B (Untergrenze) massgeblich ist. KONZEPT etikettiert [sek] und "belegt". Wichtiger: Bianchi misst ein
  1-Tages-Reversal **ohne Luecke**, ohne Beta-Neutralisierung, auf Spot-Top-100 2017-2022 (aggregiert ueber > 80 Boersen);
  F1 schreibt ein **Gap-Design** vor (wegen Bid-Ask-Bounce). Der Prior beschreibt damit nicht die zu registrierende
  Statistik - exakt die H-33-Lehre (GL-036: Literaturkonstruktion != registrierte Statistik).
- **(c) Streuungsbasis [F].** Der Faktor 2,3..2,6 aus GL-035 bezieht sich auf die **faktorerhaltende Null** (v6b), nicht
  auf 1/sqrt(K-1); im Pilot liegt SD_P 0,116..0,134 bei Median-K ~206 etwa 1,8x ueber 1/sqrt(K-1). Als markierte
  Vermutung vertretbar, Bezug falsch angegeben. (d) Bei 1-3-Tages-Horizont mit taeglichem Schritt ueberlappen die
  Outcomes -> c > 1, nicht beruecksichtigt.
- **Folge [U].** F1 bleibt das interessanteste neue Feld (VW-Weg-A 0,023 liegt ueber der W1/W2-MDE 0,013..0,019), ist
  aber **nicht** "unter heutigen Regeln registrierbar": fuer die Gap-Statistik fehlt ein belegter Prior (Arbeitsregel 4),
  W2 ist fuer Reversal vorbelastet (GL-036 (4)), der Pilot ist als gesehen zu fuehren (C.17).
- **Auflage.** F1-Zeile auf W1/W2 umrechnen; Prior als "Bianchi Weg A, ohne Gap, ohne Beta-Kontrolle - fuer Gap-Design
  UNBELEGT"; c fuer Ueberlappung; C.17-Etikett. Gleiches Muster fuer F5 (Ereignis-CAR braucht BTC-Beta, ab 2026-07 gesperrt).

### B-5 KONZEPT T-8 / T-9 / F2(a) / F3 / F4 / F6 / T-2 Anhang 8: Power auf BTC/ETH-Tagen ohne Siegel- und Vorwissens-Etikett
- **Befund [F].** Die Zahlen "2.000-2.400 BTC/ETH-Tage -> IC 0,051-0,056 aufloesbar" und die vorgeschlagene OOS-Disziplin
  ("Exploration 2020-2023, Validierung 2024-2025, Konfirmation rollierend ab 2026") (i) schliessen die Tage ab 2026-07-01
  ein, auf denen DEC-96 E3 jede Rendite-/Vol-Streuungsstatistik von BTC/ETH sperrt und deren Verwendung an der offenen
  Reihenfolge-Frage (DEC-98 E4 (b)) haengt; (ii) behandeln historische BTC/ETH-Fenster als blind, obwohl die Akte
  agentenbekannte Aggregatgroessen nur prospektiv konfirmiert (DEC-96 E1, Praezedenz H-27; ARCHITEKTUR R-1 schlaegt das
  als Regel vor). T-2 Anhang 8 (Ausschlussgrenze auf 2.400 BTC-Tagen) schliesst ebenfalls Siegeltage ein.
- **Rechnung [R].** Prospektiv sind es ~365 Tage je Jahr: MDE80 0,130 je Einjahresfenster (C.10 je Haelfte bei zwei Jahren
  0,130), Ausschlussgrenze 0,086. Die 0,051 gelten nur fuer eine Explorationsmessung.
- **Folge [U].** Kein offener Siegelbruch (KONZEPT 6 schliesst ihn aus), aber die Felder-Tabelle setzt still Siegel- und
  Vorwissens-Daten in die Power - eine nicht etikettierte Lockerung. Konflikt mit ARCHITEKTUR R-1 (Abschnitt 3).
- **Auflage.** Je Feld zwei Power-Spalten: "Exploration (nur Vorperiode, S1/S2 im Konto)" und "Konfirmation unter
  geltenden Regeln (W1/W2 bzw. prospektiv nach Reihenfolge-Entscheid)"; Siegel-Etikett DEC-96 E3 / DEC-98 E1 (b).

### B-6 KONZEPT T-5 und T-12 (4): falsche Belege fuer "Siegel schuetzt nur Vorwissen" und "W1/W2 faktisch nicht mehr blind"
- **Befund [F].** T-5: "die realisierte Vol der Fenster ist ohnehin schon in der Akte (DEC-95 E2) - das Siegel schuetzt
  heute vor allem gegen Vorwissen der Agenten, nicht gegen Daten". DEC-95 E2 betrifft die BTC-RV von **W1/W2**
  (0,067 / 0,055 je Woche), nicht die Tage ab 2026-07-01, die das Siegel schuetzt und die in der Akte nicht ausgewertet
  sind. T-12 (4): "W1/W2 fuer Klasse W ... (Lockerung, ehrlich: sie sind faktisch nicht mehr blind, DEC-103 N1 (2))".
  DEC-103 N1 (2) betrifft r_pre der **A2-Vorperiode 2021-03..2024-05**; fuer W1/W2 sagen GL-035 und GL-036 das Gegenteil
  ("W1/W2 bleiben fuer fm8 blind", "ungeoeffnet"; vorbelastet ist nur rev1 in W2, GL-036 (4)).
- **Folge [U].** Der Vorschlag, W1/W2 zur Explorationszone zu erklaeren, ist zwar als Lockerung (N) etikettiert, wird
  aber mit einer falschen Tatsachenbehauptung begruendet; er gaebe die einzigen historischen Blindfenster der Klasse W
  auf. Das ist der schwerste Faktenfehler mit Blindheitsfolge in den vier Analysen.
- **Auflage.** Begruendungen streichen; Vorschlag nur als reine Lockerung mit Preis ("einzige blinde Klasse-W-Fenster")
  vorlegen.

### B-7 KONZEPT T-12: "neutral in alpha" und "ein Drittel bei gleicher Fehlerrate" sind so nicht belegt
- **Befund [F/R].** Die Rechenbeispiele (c 1,73, +3,4 %, E[Info bei H1] 0,79) gelten fuer alpha **0,05 einseitig**; C.10 hat
  gemeinsam 0,0025. Das Regime verteilt ein Jahresbudget (z. B. alpha_Jahr 0,05) auf Registrierungen - das alpha je Test
  ist nicht festgelegt und kann bei wenigen Registrierungen bis Faktor 20 ueber 0,0025 liegen. Die Zeile "Interimsblicke
  ... ersetzt C.10/DEC-52 durch EIN Regime | Lockerung in der Zeit, neutral in alpha" ist damit unbelegt; zusaetzlich
  entfaellt die Zwei-Fenster-Regime-Robustheit (C.10-Zweck, PRD 3.5 (a)) - eine weitere Lockerung.
- **Rechnung [R, Gitterintegration].** Bei gleichem alpha 0,0025 und Power 0,80 (OBF, 4 Blicke): Maximum 1,007,
  E[N bei H1] 0,871 der Festgroesse = 1,875 N_0,05-Einheiten; C.10 mit gemeinsamer Power 0,80 braucht 2,712, C.10 in der
  heutigen Praxis (gemeinsam 0,64) 2,000. Ersparnis also -31 % gegen C.10-0,80 (die Aussage "ein Drittel" haelt nur so),
  -6 % (bei hoeherer Power) gegen die heutige Praxis; unter H0 ohne Futility keine Ersparnis (E[N bei H0] 1,007).
- **Auflage.** alpha je Test explizit = 0,0025 setzen oder die Lockerung mit Faktor etikettieren; Vergleichsbasis nennen.

### B-8 ARCHITEKTUR 3.4/3.5: Kohorten-Datenfaktor 1,54 vergleicht Ungleiches
- **Befund [F/R].** 1,27 / 1,54 / 1,80 / 1,96 (m 2/4/8/12) sind als Bonferroni-Rechnung richtig [R]. Verglichen wird aber
  "geteilte Scheibe + Bonferroni je Fenster" mit "Serialisierung ohne Korrektur". Die Akte korrigiert Mehrfachtests
  ohnehin ueber F-WEEK (BY, DEC-99 (7)) - unabhaengig davon, ob Hypothesen dieselben oder getrennte Fenster nutzen. Der
  echte Mehrpreis des Teilens ist die Abhaengigkeit der Statistiken (von BY abgedeckt), nicht 1,54. Zudem senkt Bonferroni
  je Fenster die Fehlerrate je Test unter 0,25 % - im Widerspruch zum Satz "Fehlerrate je Test unveraendert".
- **Folge [U].** Richtung konservativ; die Schlussfolgerung (Teilen schlaegt Serialisieren) wird staerker, nicht schwaecher.
- **Auflage.** 1,54 als Obergrenze unter einer nicht geltenden Zusatzregel kennzeichnen.

### B-9 EDGE E-25 / 0 (5 ii) / S-3 und KRITIK K-13: D.17 beruht nicht auf "2 Tagen"; Tardis-Monate im Siegel
- **Befund [F].** DATA_INVENTORY_2026-08-10 Z. 70: "`tardis/options_chain` 2 Tage ueber 3 Monate - **bestaetigt
  1-Tag-pro-Monat-Sampling** -> Options-Chain-Kandidaten (CHAIN-GRAPH, SET-SHAPE) endgueltig nicht registrierbar".
  D.17 stuetzt sich auf die **Dichte**, und die bestaetigt das Inventar 2026-11-01 (91 / 2.741 Tage = 1 je Monat). Neu ist
  nur die **Tiefe** (ab 2019-04). D.17 bleibt fuer dichte Ketten-Kandidaten gueltig; monatliche Skew-/Term-/VRP-Designs
  sind neue Hypothesen, keine D.17-Revision (KONZEPT F8 liest das richtig).
- **Siegel [F].** KRITIK K-13 "[V] ... fuer ~91 Monate rekonstruierbar" schliesst die Stichtage 2026-07-01, 08-01, 09-01,
  10-01 ein; eine VRP- oder IV-Statistik dort verletzt DEC-96 E3. EDGE E-25 beschraenkt korrekt auf Tage vor 2026-07-01.
- **Auflage.** EDGE: "D.17 revidieren" -> "D.17 unberuehrt; neue monatliche Designs nach C.8-Inhaltsprobe". KRITIK K-13:
  "nur Stichtage <= 2026-06-01".

### B-10 KRITIK K-1: bestaetigt, mit zwei Praezisierungen und einem neuen PRD-Rechenfehler
- **Bestaetigt [R].** Unter bivariater Normalitaet gilt E[r sign(s)] = rho x 0,798 x sigma; Monte Carlo (4 Mio., rho 0,05):
  0,03972 gegen Theorie 0,03989 und PRD-Formel 0,02541. Verhaeltnis pi/2 = 1,571 (bei IC 0,05: 1,5702), Horizont x2,467.
  Alle Tabellenwerte K-1 reproduziert (6,65 h / 2,72 h; 2,73 / 1,108 Tage; 0,267 Tage; 0,0312 / 0,0199).
- **Praezisierung 1 [R].** "Exakt" gilt fuer Pearson-rho. Ist IC (wie im Programm) ein Rang-IC (Spearman), ist der
  Gauss-konsistente Pearson-Wert 2 sin(pi IC / 6) und der Faktor gegen die PRD-Formel pi^2/6 = 1,645 (Horizont x2,71).
  Bei IC 0,05: 4,7 % Unterschied. (BELEGE_AUS_PDF 4 fuehrt den Faktor 0,955 ebenfalls nur als Vermerk.)
- **Praezisierung 2 [U].** Der tiefere Fehler ist kategorial: ein Querschnitts-IC wird im Einzelpositionsrahmen als
  Zeitreihenkorrelation eines Assets gelesen. K-1 benennt "zwei unvereinbare Modelle" - richtig, aber die pi/2-Korrektur
  heilt diesen Punkt nicht.
- **Neu [R].** PRD 9.2 K-0.1 / R4 K-0.1 nennen bei Wochen-IC 0,05 "~7 h (Maker)"; mit der PRD-eigenen Formel sind es
  **8,7 h** (4 / 6,657 bp, quadriert); Gauss-konsistent 3,5 h. "Abstand halbiert" (0,03 gegen 0,062 -> 0,040) ist ein
  Drittel (0,032 -> 0,010).
- **Etikett.** (a) neutral, O - richtig. (b) Stundenhorizonte zu oeffnen ist N und muss D.4, D.12, D.14 als Nicht-
  Wiederholungs-Nachweis (C.1) adressieren - fehlt.

### B-11 KRITIK K-2 und K-3: Mathematik bestaetigt, "vorhersagbar am PRD-Tag" und "4 Wochen vermeidbar" sind Rueckschau
- **K-2 [R].** Lo mit q = 365: 1,554 Jahre (Kurzform 1,546); 1,80 nur mit q = 12 - PRD 3.6 widerspricht sich selbst
  ("Fehler klein", dann 16 %). t des Praemienmittels = SR_p x sqrt(n): identische Nachweisdauer, bestaetigt. A1 SR_eff
  1,947. **Ueberdehnung [U]:** "GL-033/034 waren am 2026-09-02 mit einer Zahl je Kandidat vorhersagbar" - bekannt war nur
  die Schwelle 2,49; SD 18,6 VP, c 28,2 und 372,9 bp wurden erst in DEC-93/97 gemessen. "~4 Wochen vermeidbar" ist [V].
- **K-3 [R].** Identitaet eigenstaendig simuliert: SD von Spearman(permutierte Charakteristik, Rendite) bei K 200 ohne /
  mit starkem Faktor 0,0722 / 0,0718 gegen 1/sqrt(K-1) = 0,0709 - unabhaengig von der Korrelationsstruktur. N = 5:
  0,098 x 2,4865/2 = 0,122 bestaetigt. **Einordnung [F]:** DEC-74 hat die Identitaet selbst festgehalten; fehlerhaft
  waren PRD 4.1 ("enthaelt die effektive Breite exakt") und DEC-67 B2. "DEC-73..92 vermeidbar" setzt voraus, dass die
  Teststatistik-SD unter Faktorstruktur am 2026-09-14 bekannt war - sie wurde erst mit DEC-75..91 gemessen. [V].
- **Auflage.** Rueckschau-Saetze als [V] kennzeichnen; die prospektiven Vorschlaege (Klassen-Feasibility, Null-Fixture
  mit Faktorstruktur) uebernehmen.

### B-12 KRITIK K-6 / K-7: Kernaussage "Power-/Prior-/L-Wahlen beruehren alpha nicht" richtig je Test, mit drei ungenannten Ausnahmen
- **Bestaetigt [F/R].** DEC-94 (1)(4): Schwelle mit Lauf-SE; vor dem Outcome und nur aus Nuisance gewaehlte Designs aendern
  das alpha des Tests nicht. PPV-Tabelle K-6 identisch nachgerechnet; gepoolte Power 0,761, +36 % / +8 % / +26 % (je
  andere Basis, alle richtig); DEC-52-H0-Rate 0,99 % / 0,85 % (Screens nach DEC-94 (6)); K-0.6 0,163 / Faktor 5,2.
- **Ausnahmen [F/U].** (i) **A2:** DEC-103 E4 bindet die Schwellen-SE an "die groessere aus Vorperiode und
  Null-Simulation"; Nuisance-Wahlen (Stress bindend, N1 (8c)) verschieben dort das **effektive** alpha (nach unten).
  K-12 (c) ("bindende Nuisance aus dem juengsten Vorfenster, neutral") ist fuer A2 eine Lockerung des effektiven alpha
  Richtung Nominalwert - Etikett "neutral" falsch. (ii) Historische Fenster + Vorwissen der Agenten (DEC-96 E1): K-7
  nennt das als C.17-Ausnahme - richtig, aber fuer A1 (Formation in W1/W2 gesehen) greift sie. (iii) Programmebene: mehr
  testbare Designs -> mehr Tests je Jahr -> mehr erwartete Falsch-Entdeckungen trotz FDR je Familie; und die PPV haengt an
  der Power (K-6 selbst).
- **Auflage.** K-7 als "alpha je Test neutral; A2-Schwelle, Vorwissen und Programmebene ausgenommen" fassen; K-5 (4)
  (UNBELEGT symmetrisch) aendert Arbeitsregel 4 der Verfassung -> **N**, nicht O.

### B-13 KRITIK K-11: Fakten richtig, Zitat und Schluss ueberzogen
- **Befund [F].** "2.0 starb an der Friktionswand" steht nicht im PRD; PRD Par. 1 sagt, die Sekunden-/Minuten-Horizonte
  seien arithmetisch vorgezeichnet tot (1-s-Orakel 0,71 bp) - das gilt unabhaengig davon, woran H-03 (Surrogate-p ~1,0,
  D.4), H-09 (Rauschmuster, D.8) und H-24 (Vorzeichen, D.14) tatsaechlich scheiterten.
- **Auflage.** "Pivot-Diagnose falsch" -> "Pivot-Begruendung unvollstaendig: der dominante 2.0-Fehlermodus 'kein Signal'
  wird durch den Horizontwechsel nicht adressiert" [U].

### B-14 KONZEPT T-9: Kostendeckung falsch zugeordnet (zu pessimistisch)
- **Befund [R].** Vorzeichenwechsel eines AR(1)-Signals je Tag arccos(phi)/pi: 0,500 / 0,333 / 0,205 (phi 0 / 0,5 / 0,8).
  Taker-IC_min = 11 x Wechselrate / (0,798 x 262): **0,0263 / 0,0175 / 0,0108**. KONZEPT: "bei persistenten Signalen
  (phi 0,5) Taker 0,026" - 0,026 gilt fuer phi 0; "voller Tagesumschlag 0,053" entspricht phi = -1 (taeglicher
  Vorzeichenwechsel), keine realistische Obergrenze.
- **Folge [U].** Fuer phi >= 0 liegt die Taker-Grenze bei 0,011..0,026, also unter der (nur explorativ) aufloesbaren 0,05;
  der Satz "aufloesbar ~ Wand" ist im Kostenteil zu pessimistisch, im Aufloesungsteil (B-5) zu optimistisch.
- **Auflage.** Tabelle mit phi-Spalten statt "Umschlag 1,0/0,5/0,33" (O, Erratum).

### B-15 EDGE R-1 / E-15: Arithmetik bestaetigt; "voller Pilot-Betrag" ist keine programmkonforme Obergrenze, "unplausibel hoch" ueberzogen
- **Bestaetigt [R].** Informationsrate |x|/SD x sqrt(52) = 2,246 / 2,772 / 2,399; Wochen je Fenster 63,7 / 41,8 / 55,9;
  Power je 52 Wochen 0,726 / 0,870 / 0,775; 75 %: 113,3 / 74,4 / 99,3; 50 %: 254,9 / 167,4 / 223,4; Literatur 0,014: 481
  Wochen. Daten ab 2026-10-05: 2028-05-11 / 2029-03-14 (EDGE mit Wochenrundung 2028-05-14 / 2029-03-18) - ok.
- **Befund [F/U].** (a) DEC-99 (3) verlangt fuer Pilot-Priors den **selektionsbereinigten** Schaetzer (bedingt
  median-unverzerrt); die 42 Wochen nutzen die Variante mit maximalem |t| (mom2 aus K = 4, zudem gegen die registrierte
  Richtung) - Winner's Curse. Die 75-%-Zeile (74..113 Wochen, voll ~2029-08..2031-02) ist die ehrlichere Leitzahl.
  (b) "Unplausibel hoch": Literatur-Informationsraten [R aus BELEGE]: Ficura Large/Liquid 1-Woche 0,99, LTW Terzil 1,66,
  Ficura Small/Illiquid 3,09, Bianchi taeglich VW 1,17 / EW 7,1. 2,3..2,8 ist **hoch fuer liquide Universen**, nicht
  unplausibel an sich; als [U/V] markiert - Formulierung abschwaechen.
- **Auflage.** Kurzfassung Punkt 5: Leitzahl 75 % neben 100 % nennen; "selektionsbereinigt nach DEC-99 (3) zu rechnen".

### B-16 EDGE E-29 / Kurzfassung 9 und KRITIK K-13: H-21 "nie entsperrbar" gut gestuetzt, aber nur mit Vorbehalt formulierbar
- **Befund [F].** Das Inventar zeigt dasselbe 14-Tage-Muster (125 / 139) fuer `bybit/allLiquidation` BTC/ETH,
  `deribit/markprice.options` und `deribit/orderbook` (BNB/SOL/XRP 117 / 131) - systemische Ausfalltage des Live-Sammlers,
  passend zur Luecken-Karte DEC-98 N4 (f) (06-26, 07-06..07-16, 08-01, 08-14; davon 13 in H-21-W1). Die Registrierung
  verlangt lueckenlose done_days in **festen** Fenstern (KOMP E.1). Nicht-Nachladbarkeit von allLiquidation ist [V].
- **Folge.** Richtige Form: "in der registrierten Form nicht entsperrbar [V bis Lueckenliste]". EDGE-Kurzfassung 9
  laesst beide Vorbehalte fallen; KONZEPT T-7 und F9 fuehren H-21 noch als "gesperrt bis 2026-12-27" (veraltet).
- **Auflage.** Pruefung ist reine Vollstaendigkeit (S0, Katalog/Lueckenliste) und im Siegel erlaubt (DEC-96 E3) -> O kann
  vor der Synthese mit einer Katalogabfrage entscheiden.

### B-17 KONZEPT F8 / F9: Siegelabhaengigkeit nicht offengelegt
- **Befund [F].** F9: allLiquidation beginnt 2026-06-16; ~124 von ~139 Tagen liegen im Siegelbereich. Zaehlungen und
  Groessenverteilungen von BTC/ETH-Liquidationen sind ein starker Vol-Stellvertreter; DEC-97 A-3 hat schon
  Katalog-Bytesummen als "schwache Aktivitaets-Stellvertreter, kuenftig vermeiden" eingestuft. F9 beruehrt zudem die
  registrierten H-21-Fenster. F8: "Freitage mit GEX bis 2027-06: 52" sind A2-Statistiken (r_pre BTC/ETH) im Siegel und
  haengen an A2-Option P-3 / Reihenfolge-Frage.
- **Auflage.** F8 und F9: "vor Reihenfolge-Entscheid nur S0 (Zeilen, Luecken, Zeitstempel)"; Power erst danach.

### B-18 KONZEPT T-3: Kompendium D.16 nur als Gegenargument, Zustaendigkeit falsch
- **Befund [F].** Das gemeinsame Mehrsymbol-Modell (SV, Spruenge, Beta-Dispersion, Funding-Mechanik, Delisting-Hazard,
  Tageszeitprofil) ist schwere Modell-Infrastruktur vor validiertem Signal - D.16 ("die teuerste Form, nichts zu
  lernen"). KONZEPT nennt D.16 im Gegenargument und fuehrt T-3 trotzdem als "Orchestrator, keine Nutzerentscheidung".
- **Auflage.** T-3 auf die OC-Simulation der Gate-Kette (T-16) mit minimalen, je Familie validierten Nullwelten
  beschraenken (O); ein umfassendes generatives Modell braucht eine ausdrueckliche D.16-Abgrenzung (N).

### B-19 KONZEPT, kleinere Faktenfehler
- "In 14 Monaten 3.0 (seit PROGRAMMENTWURF)": PROGRAMMENTWURF_3.0.md "Stand 2026-09-02" -> zwei Monate.
- "sechs Gate-Eintraege (GL-032..036 plus H-32-Pilot)": GL-035 ist der H-32-Pilot -> fuenf.
- GSD-Zahlen (c 1,734, +3,4 %, 0,793, 0,717) sind richtig [R], aber anders definiert als in den anderen Analysen
  (E[Info] bei Festdesign-Drift ohne Inflation, Power dort 0,788; Futility ohne Nachinflation) - siehe Widerspruch W-1.

### B-20 ARCHITEKTUR F3/F4 und Siegeldateien
- **Befund [F].** F4 (H-32-Pilot bitgleich) ist unbedenklich: die Pilot-Artefakte (`h32_pilot_*_P_ic_weekly.csv`) stehen
  nicht auf der Siegelliste (nur Dateinamen gelistet). F3 "reproduziert die Zuordnungen von GL-032 ..." ist zulaessig,
  solange aus veroeffentlichten Akte-Zahlen; ein Neulauf des wp13a-Vorlaufcodes wuerde `*_L_window_sealed.json`-Inhalte
  erzeugen.
- **Auflage.** Fertig-Kriterium F3: "ohne Neulauf von Code, der Siegeldateien schreibt".

### B-21 Alle: Veroeffentlichung
- **Befund [F].** Die Analysen liegen bereits als ungetrackte Kopie unter `scinance3-impl/state/prd_analyse_2026-11-01/`
  (nur Pfade geaendert). Scan: kein Hostname, keine Zugangsdaten, keine Modellnamen (ausser dem Dateinamen `CLAUDE.md`),
  ASCII. Keine der Analysen fuehrt neue Nuisance-Zahlen ein; ein B-2-Kanal ist nicht erkennbar [U]. EDGE verweist noch auf
  "Rechenskript nur im Scratchpad, `edge_calc/calc.py`", die Kopie liegt unter `scripts/edge_calc.py`.
- **Auflage.** Vor dem Commit: Struktur-Scan nach DEC-103 N1 (2c) ueber die neuen Dateien; Verweis in EDGE nachziehen.

---

## 2. Nachrechnungstabelle (eigener Code, `state/prd_analyse_2026-11-01/scripts/review_calc.py`)

| # | Groesse | Analyse | Wert dort | eigene Rechnung | Urteil |
|---|---|---|---|---|---|
| 1 | Kante Gauss / PRD-Formel, IC 0,05 | KRITIK K-1 | 1,570 | 1,5702; MC 0,03972 / 0,02541 | bestaetigt |
| 2 | dto. fuer Rang-IC | - | - | pi^2/6 = 1,645, Horizont x2,71 | Praezisierung |
| 3 | Mindesthorizont p 0,55 Taker PRD / Gauss | KRITIK | 6,6 h / 2,7 h | 6,65 / 2,72 h | ok |
| 4 | dto. Wochen-IC 0,05 Taker | KRITIK | 2,73 / 1,11 Tage | 2,73 / 1,108 | ok |
| 5 | PRD "7 h Maker" bei IC 0,05 | PRD 9.2 | 7 h | 8,67 h (PRD-Formel) | neuer PRD-Fehler |
| 6 | Break-even Wochen-IC PRD / Gauss | KRITIK | 0,031 / 0,020 | 0,0312 / 0,0199 | ok |
| 7 | Lo SR 2 q 365 / q 12 | KRITIK K-2 | 1,554 / 1,80 | 1,554 / 1,803 | ok |
| 8 | SR_eff noetig bei 1 / 2 / 3 Jahren | KRITIK K-2 | 2,49 / 1,76 / 1,44 | 2,486 / 1,758 / 1,436 | ok |
| 9 | H-27 SR_eff, Tage je Fenster | KRITIK, ARCH | 1,83; 672 | 9,47: 1,832 / 673; **7,14: 1,381 / 1.183** | Prior ueberholt |
| 10 | A1 SR_eff theta 1 | KRITIK | 1,95 | 1,947 | ok |
| 11 | Permutationsboden unter Faktorstruktur | KRITIK K-3 | Identitaet | 0,0722 / 0,0718 vs 0,0709 (K 200) | bestaetigt |
| 12 | gepoolt 0,0025 Power bei C.10-MDE | KRITIK K-4 | 0,76 | 0,761 | ok |
| 13 | C.10 gemeinsam 0,80 / gepoolt vs C.10 / C.10 vs gepoolt | KRITIK, EDGE, KONZEPT | +36 % / +8 % / +26 % | 1,356 / 1,077 / 1,259 | alle ok (verschiedene Basis) |
| 14 | DEC-52-H0-Rate z 2,3263 ohne / mit Screens | KRITIK K-4 | 1,00 % / 0,86 % | 0,99 % / 0,85 % | ok |
| 15 | K-0.6 | KRITIK | 0,163; x5,2 | 0,1626; x5,2 | ok |
| 16 | Produkt vs exakt (Illustration) 22 / 20 bp | KRITIK K-5 (b) | 0,76/0,83; 0,64/0,76 | 0,757/0,833; 0,637/0,755 | ok |
| 17 | je Bedingung bei m 3 / 5 | KRITIK | 0,928 x1,25/1,56; 0,956 x1,35/1,82 | identisch | ok |
| 18 | Null-Faktor, zwei Bedingungen je 0,90 | KRITIK K-5 (a) | "0,9 -> 0,81" | exakt 0,858 / 0,870 / 0,900 bei Korr. 0,82 / 0,91 / 1 | nur Grenzfall |
| 19 | A2-Kette W2 bis 32,1 | KRITIK / KONZEPT | Gate (4) +4,9 / +2,8, skal. Null +2,1 | 27,2 + 2,1 + 2,8 = 32,1 | KRITIK falsch, KONZEPT richtig |
| 20 | Datenfaktoren gegen 18,8 | KRITIK | 1,10/1,51/1,68/2,09/2,92 | 1,098/1,510/1,684/2,093/2,915 | ok |
| 21 | PPV C.10 / gepoolt 0,01 / ein Fenster | KRITIK K-6 | 0,93..0,98 / 0,81..0,95 / 0,46..0,80 | identisch | ok |
| 22 | A2 P2'' gepoolt alpha 0,01 / 0,0025 | KRITIK | 16,7 (0,79) / 19,3 | 16,70 (0,788) / 19,24 | ok, nur Einzel-Placebo |
| 23 | A3 Roh-IC gepoolt 0,01 measured / stress | KRITIK | 0,024 / 0,034 | 0,0239 / 0,0338 | ok, Prior 0,03 unbelegt |
| 24 | Pilot-Uebergabe A2 bei 16,5 / 25 bp; Pilot-alpha | KRITIK K-9 | 7e-5 / 0,042; 2,4e-15 | 7,1e-5 / 0,0417; 2,44e-15 | ok |
| 25 | OBF K 4, alpha 0,05: c; Maximum | KONZEPT / ARCH / KRITIK | 1,733; 1,034 / 1,030 / 1,04 | c 1,734; R 1,035 | ok |
| 26 | E[N bei H1]/N_fix | KONZEPT / ARCH / KRITIK | 0,79 / 0,81 / 0,82 | 0,793 (Fest-Drift, ohne R, Power 0,788) / **0,814** (Power 0,80, mit R) | alle ok, Definition verschieden |
| 27 | OBF K 4, alpha 0,0025 | KRITIK | x1,02 / 0,88 | R 1,007 / E[N bei H1] 0,871 | ok (MC-Rauschen) |
| 28 | Futility Z<0 an Blicken 1-3 | KRITIK | Max x1,20 (0,05) / x1,04 (0,0025); E[N bei H0] 0,57..0,65 | 1,198 / 1,033; 0,646 / 0,565 | ok |
| 29 | Futility ab halber Information | KONZEPT | E[Info bei H0] 0,717 | 0,718 ohne, 0,755 mit Nachinflation | ok, Definition |
| 30 | OBF K 2 / 8, alpha 0,05 (Max; E[N bei H1]) | ARCH | 1,008; 0,870 / 1,050; 0,782 | 1,015; 0,876 / 1,050; 0,782 | ok |
| 31 | Bonferroni-Datenfaktor m 2/4/8/12 | ARCH | 1,27/1,54/1,80/1,96 | 1,270/1,537/1,804/1,959 | Rechnung ok, Vergleich nicht (B-8) |
| 32 | GSD-Ersparnis "ein Drittel bei gleicher Fehlerrate" | KONZEPT T-12 | ~1/3 | -31 % vs C.10 gemeinsam 0,80; -6 % vs C.10 Praxis | nur gegen C.10-0,80 |
| 33 | Tages-TS MDE80 N 2.400 / prospektiv 365 | KONZEPT T-9 | 0,051 / - | 0,0508 / 0,130 | Kontext fehlt (B-5) |
| 34 | Taker-IC_min phi 0 / 0,5 / 0,8 | KONZEPT T-9 | 0,026 bei phi 0,5 | 0,0263 / 0,0175 / 0,0108 | falsch zugeordnet |
| 35 | F1 MDE80 | KONZEPT | 0,006-0,013 | alle 2.130 d 0,0055..0,0110; **W1/W2 je Fenster 0,0133..0,0188** | ueberzeichnet |
| 36 | Bianchi Weg A EW / VW | KONZEPT | 0,09 / 0,023 | 0,0904 / 0,0231 (VW t ~2,6) | Zahl ok, ohne Gap |
| 37 | Ausschlussgrenze IC 0, N 2.400 | KONZEPT T-2 | 0,034 / 7,0 bp | 0,0336 / 7,0 bp | Zahl ok, Fenster im Siegel |
| 38 | R-1 Wochen je Fenster / Power je 52 W | EDGE | 63,7/41,8/55,9; 0,73/0,87/0,78 | identisch | ok |
| 39 | R-1 Informationsrate | EDGE | 2,25/2,77/2,40 | identisch; Literatur 0,99..3,09 (liquid 0,99..1,66) | "unplausibel" ueberzogen |
| 40 | R-1 voll ab 2026-10-05 | EDGE | 2028-05-14 / 2029-03-18 | 2028-05-11 / 2029-03-14 (ohne Wochenrundung) | ok |
| 41 | zweiseitig: MDE / Daten | KRITIK K-10 | x1,13 / x1,27 | 1,1267 / 1,2695 | ok |
| 42 | A1 Jahre je Fenster bei SESOI 36 bp | KRITIK K-10 | 12,8 | 12,76 | ok |
| 43 | A2 gegen SESOI 22 / 10,8 bp | KRITIK K-10 | registrierbar | nur Einzel 18,8 < 22; exakt 22,3, Produkt 24,4, stress 27,2 > 22; Maker in keiner Lesart | ueberzeichnet (B-2) |
| 44 | A2 Jahre je Fenster bei 16,5 bp (stress) | EDGE E-28 | 2,5..2,7 | 2,50 / 2,72 | ok |
| 45 | R-6 Cluster fuer 500/300/200 bp | EDGE | 24/67/150 | 24,0/66,6/150 | ok |
| 46 | 7-Tage-VRP-Hebel SD-Grenze | EDGE E-22 | ~37 VP | 37,3 | ok |
| 47 | F6 FOMC / F8 Freitage 52/104/10 | KONZEPT | 26,6; 15,1/10,7/34 | 26,56; 15,10/10,68/34,4 | ok |

---

## 3. Widerspruchsliste zwischen den Analysen

| # | Gegenstand | Positionen | Richtig nach Nachrechnung / Akte |
|---|---|---|---|
| W-1 | E[N bei H1] bei OBF, 4 Blicke | KONZEPT 0,79; ARCH 0,81; KRITIK 0,82 (alpha 0,05) bzw. 0,88 (0,0025) | Alle drei numerisch richtig, verschiedene Definitionen. Einheitlich verwenden: Power 0,80 mit Maximumsinflation: **0,814 (alpha 0,05), 0,871 (alpha 0,0025)**; Maximum 1,035 / 1,007. Fuer das Programm (gemeinsam 0,0025) gilt 0,87, nicht 0,79. |
| W-2 | Fenster-Regime | KONZEPT: C.10 durch EIN sequentielles Regime mit Jahresbudget ersetzen; ARCH: C.10 behalten, GSD je Fenster (alpha 0,05 je Fenster, gemeinsam 0,25 %); KRITIK: gepoolt alpha 0,0025..0,01 plus REZENZ-Screen | Drei unvereinbare Alternativen fuer dieselbe Nutzerfrage. Nur ARCH haelt die Fehlerrate je Test nachweislich konstant; KONZEPT ist ohne festes alpha je Test eine Lockerung (B-7); KRITIK-Variante 0,01 ist Lockerung x4. Synthese: als Optionen mit alpha je Test und Regime-Robustheit vorlegen. |
| W-3 | BTC/ETH-Aggregatstatistiken historisch | KONZEPT T-9: Validierung 2024-2025, Konfirmation ab 2026; ARCH R-1: nur prospektiv | ARCH entspricht der Praezedenz DEC-96 E1; KONZEPT nicht etikettiert (B-5). |
| W-4 | VRP-Zeitlinie | KRITIK ~2030 (L ~22 Monate); ARCH voll 2030-04-04; EDGE 2029-07..2033-01; KONZEPT "eher 2033" | EDGE/KONZEPT richtig (DEC-98 N2: 7,14 VP). |
| W-5 | A2-Testbarkeit | KRITIK "heute registrierbar gegen 22 bp"; EDGE "nur bei Effekt >= ~25-30 bp"; ARCH "V/C-MDE 23..32 bp bleibt" | EDGE/ARCH richtig unter geltendem Design (B-2). |
| W-6 | A2-Kette 27,2 -> 32,1 | KRITIK: Gate (4); KONZEPT: skalierte Null +2,1, Gate (4) +2,8 | KONZEPT (DEC-103 N1 (9)). |
| W-7 | H-21 | EDGE/KRITIK: nicht entsperrbar [V]; KONZEPT T-7/F9: gesperrt bis 2026-12-27 | EDGE/KRITIK, mit Vorbehalt (B-16). |
| W-8 | Tardis / D.17 | EDGE: D.17 beruht auf 2 Tagen, revidieren; KONZEPT F8: 1 Tag/Monat, fuer Fluss unbrauchbar; KRITIK: monatliche PnL [V] | KONZEPT (DATA_INVENTORY 2026-08-10 Z. 70; B-9). |
| W-9 | Reversal-Prior | KONZEPT F1: Ein-Tages-Reversal belegt (Bianchi), registrierbar; EDGE: fuer liquide Universen kein Reversal-Prior (GL-036), Betrag des Piloten verboten | Fuer Gap-Design gilt EDGE: kein belegter Prior (B-4). Fuer ein Tagesdesign ohne Gap waere Bianchi-VW eine Prior-Kandidatin - Bounce-Risiko dann Pflicht-Kontrolle. |
| W-10 | Mehrkosten zweier Fenster | KRITIK +36 % bzw. +8 %; EDGE/KONZEPT +26 % | Alle richtig, verschiedene Basen (Zeile 13). Synthese: eine Basis waehlen (empfohlen: +26 % = C.10 gemeinsam 0,80 gegen ein Fenster alpha 0,0025, DEC-98 E1 (c)). |
| W-11 | Prior-Ersatz | KRITIK: SESOI aus der Wand; KONZEPT: Ausschlussgrenzen + Prior-Verteilung; ARCH: X-Pilot/Screen als Standardquelle; EDGE: Literaturpflicht bleibt, Pilot-Betrag nur per N | Kein Rechenwiderspruch, aber vier Alternativen fuer eine Programmfrage; SESOI ist nicht etikettierungsfrei (B-2). |
| W-12 | Kosten des Teilens von Blindfenstern | ARCH: Datenfaktor 1,54 (m 4); KONZEPT: BY ueber alle Blicke; EDGE/KRITIK: gemeinsame Vorregistrierung ohne Preisangabe | Unter geltender F-WEEK-Korrektur ist der Mehrpreis des Teilens die Abhaengigkeit, nicht Bonferroni (B-8). |

---

## 4. Luecken (fehlen allen vier Analysen; muss die Synthese ergaenzen)

1. **Bedarfsbilanz der knappen Blinddaten.** Alle Vorschlaege konkurrieren um dieselben zwei Ressourcen: W1/W2
   (F1, A2, H-33-artige Reversals, A3-fm8) und die Siegelperiode ab 2026-07-01 (R-1, VRP, A1, A2-Option P-3, F8, F9,
   H-21). Keine Analyse stellt den Gesamtbedarf gegen den Bestand; ohne diese Tabelle ist die Reihenfolge-Frage
   (DEC-98 E4 (b)) nicht entscheidbar. [U]
2. **Gesamt-OC des Lockerungspakets.** KRITIK verlangt eine Operationscharakteristik fuer die gestapelte Strenge (K-5),
   keine Analyse rechnet sie fuer das gestapelte Lockerungspaket (gepooltes alpha 0,01, SESOI, X-Screens, Kohorten,
   Budget-GSD, Zone E): erwartete Falsch-PASS je Jahr und PPV bei realistischen Basisraten. Pflichtzeile der Synthese.
3. **Schwere Raender und kleine Clusterzahlen.** Alle MDE-, Power- und GSD-Zahlen sind Normalnaeherungen mit bekannter
   Varianz. Akte: Exzess-Kurtosis 5..10 fuer r_pre (NUISANCE_SIGMA30), Merkposten 2,6 (DEC-98 N5, B-9); stationaerer
   Bootstrap bei 40-52 Clustern ist eher antikonservativ; Zwischenblicke mit geschaetzter Varianz brauchen t-artige
   Grenzen. Effekt: wahre Power niedriger, wahres alpha eher hoeher. Ebenso Rang-IC vs Pearson (~5 %, BELEGE 4).
4. **Ausfalltage der Live-Stroeme.** Das 14-Tage-Muster trifft alle Live-Stroeme (Optionen, Orderbuecher,
   allLiquidation). Prospektive Designs, die auf Live-Stroemen beruhen (A4 `rest.tickers15m`, F8 GEX aus
   `deribit/tickers`, Optionsticker), verlieren effektives N und koennen "lueckenlos"-Bedingungen verfehlen; keine
   Analyse budgetiert das. (Rueckfuellbare REST-Stroeme sind lueckenlos.)
5. **Perp-spezifische Renditebestandteile.** Funding-Zahlungen als Teil der L/S-Rendite (A3/F1/R-1 "brutto" ohne
   Funding), Short-Restriktionen/Caps, Rendite am Delisting-Tag (IPCW) im Tagespanel, Ueberlappung bei
   Mehrtageshorizonten (c > 1).
6. **Vorwissen der Agenten als Regel statt Einzelfall.** Nur ARCH (R-1) macht daraus eine Familienregel; KONZEPT und
   KRITIK (K-7 nennt es nur als C.17-Ausnahme) nicht. Die Synthese braucht eine einheitliche Vorwissens-Klasse je
   Datenfamilie (BTC/ETH-Aggregate: nur prospektiv).
7. **Veroeffentlichungs-Scan.** Die Analysen werden ins oeffentliche Repo kopiert; Struktur-Scan nach DEC-103 N1 (2c)
   und Pruefung auf Hostnamen/Modellnamen als Pflicht vor dem Commit (hier ohne Befund, B-21).

---

## 5. Was NICHT folgt

- Kein Verdikt ueber irgendeinen Markteffekt; keine Analyse und dieser Review haben eine Outcome-Statistik gerechnet.
- Die Bestaetigung von K-1..K-4 aendert kein GL: GL-032..GL-036 bleiben Feststellungen "nicht testbar".
- Die Korrektur zu K-5 (B-1) heisst nicht, dass die A2-Zuordnung richtig streng ist; sie heisst nur, dass der
  Artefakt-Anteil 0,5..0,6 bp betraegt und der Rest Festlegung (Stress, skalierte Null, Gate (4)) bzw. Nutzerfrage ist.
- B-4 entwertet F1 nicht; F1 bleibt der interessanteste neue Kandidat, braucht aber einen Prior fuer das Gap-Design und
  rechnet auf W1/W2.
- Kein Vorschlag dieses Reviews oeffnet ein Siegel, verkuerzt eine Blindheit oder lockert eine Regel; die Auflagen sind
  Etiketten, Zahlenkorrekturen und Zustaendigkeiten.
- Die H-21-Feststellung (B-16) ist erst nach der Lueckenliste (S0) eine Tatsache.
- Die Hilfslisten FAKTENBLATT_STATUS und LISTE_DEC_GL wurden nicht vollstaendig geprueft; massgeblich bleiben die
  Primaerquellen.

---

## Kurzfassung an den Orchestrator (<= 12 Zeilen)

1. Urteil: KRITIK und KONZEPT mit Auflagen und Teil-Veto, EDGE und ARCHITEKTUR mit Auflagen ohne Veto.
2. Bestaetigt mit eigenem Code: K-1 (pi/2; bei Rang-IC pi^2/6 = 1,645; PRD "7 h Maker" ist 8,7 h), K-2 (SR_eff >= 2,49), K-3 (Identitaet, MC), K-4, K-6-PPV, K-9.
3. VETO K-5 (1): Null-Faktor ist dokumentierte Lesart (REVIEW_A2_TEILC B-4, DEC-103 N1 (8a)), Korrelation 0,82/0,91, Artefakt nur 0,5-0,6 bp (exakt 22,93/23,77 in der Akte); Kette 27,2->32,1 enthaelt skalierte Null +2,1. Nicht "streichen", sondern exakte P2''-Bedingung, Etikett Testbarkeit.
4. VETO "A2 heute registrierbar gegen 22 bp": exakt 22,3, Produkt 24,4, stress 27,2 > 22; nur Einzel-Placebo oder gepoolter Test (beides N); Taker- statt Maker-SESOI ist unetikettierte Testbarkeits-Gabelung.
5. VRP-Prior 9,47 ist seit DEC-98 N2 ueberholt (7,14): 1.183 statt 672 Tage je Fenster, ~2033 statt ~2030 (KRITIK, ARCH falsch; EDGE richtig).
6. VETO F1: 0,006-0,013 nutzt Pilot- und Siegeltage; auf W1/W2 MDE80 0,013-0,019; Bianchi-Prior (Weg A, ohne Gap) passt nicht zum Gap-Design -> nicht "registrierbar heute".
7. VETO KONZEPT-Tagesfelder BTC/ETH: Power mit Siegeltagen und agentenbekannten Fenstern ohne Etikett; prospektiv MDE 0,13 je Jahr. Konflikt mit ARCH R-1.
8. VETO T-12 (4)/T-5-Begruendungen: DEC-103 N1 (2) betrifft die A2-Vorperiode, DEC-95 E2 W1/W2 - W1/W2 sind fuer Klasse W blind; "neutral in alpha" ohne alpha je Test unbelegt (gleiches alpha 0,0025: E[N bei H1] 0,871; -31 % nur gegen C.10-0,80).
9. GSD-Zahlen 0,79/0,81/0,82 alle richtig, Definitionen verschieden; einheitlich 0,814 (0,05) bzw. 0,871 (0,0025); Kohortenfaktor 1,54 vergleicht Bonferroni mit Serialisierung ohne F-WEEK.
10. EDGE: D.17 beruht auf 1-Tag-pro-Monat-Sampling, nicht auf 2 Tagen; R-1 Leitzahl 75 % (74-113 Wochen) statt 100 % (DEC-99 (3) selektionsbereinigt); H-21 nur "in registrierter Form" und [V] bis S0-Lueckenliste.
11. Siegel: keine Analyse schlaegt Oeffnen von Siegeldateien vor; ungekennzeichnet sind KONZEPT F8/F9, T-2 (2.400 Tage) und KRITIK-Tardis (4 Siegelmonate). D.16 bei KONZEPT T-3 nur als Gegenargument (gehoert zu N).
12. Synthese ergaenzen: Bedarfsbilanz der Blinddaten, Gesamt-OC des Lockerungspakets, schwere Raender/kleine Clusterzahlen, Ausfalltage der Live-Stroeme, Funding in L/S-Renditen.
