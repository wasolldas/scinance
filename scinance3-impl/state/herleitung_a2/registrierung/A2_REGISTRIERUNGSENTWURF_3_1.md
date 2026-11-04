# A2-Registrierungsentwurf unter Verfassung 3.1 (H-34, EXP-CLOCK) - Herleitung je Pflichtzeile - 2026-11-04

> **Rolle:** Herleitung. **ENTWURF, nichts registriert, kein Verdikt.** Registriert nur der Orchestrator nach dem
> adversarischen Review (VR-h03, VR-f06). Nichts im Repository geaendert, nichts committet; keine Marktdaten, keine
> Siegeldatei, kein Harvest-Client, kein Netz; kein Mittel und kein Vorzeichen eines r_pre-Kontrasts (VR-g06).
> **Auftrag:** `BRIEF_a2_registrierung_3_1.md` (Zu leisten 1..5). **Dateien dieses Verzeichnisses:**
> `a2_registration_3_1.yaml` (Linter: 0 FEHLER, 2 HINWEIS, rc 0; Aufruf und Ergebnis in `calc/a2_reg_calc.out` (7)),
> `calc/a2_reg_calc.py` (sha256 295775466fe286bdd6cbd61ad84597763f79cf79d2f5616ef36bc0f7f2ce8391; Seed 20261104,
> 300.000 Pfade, `python3 -I`, numpy/scipy; Laufzeit 63 s), `calc/a2_reg_calc.json`, `calc/a2_reg_calc.out`.
> **Quellen (nur die im Brief genannten Abschnitte):** PRD v3 0.1, 2 (VR-b/c/d/e/f), 3, 4.2; DEC-103 (+N1), DEC-104
> (E2..E8, N1, N2, N4), DEC-105, DEC-107 (1), (2) BE-04, N1 (1)-(3); NULL_SIMULATION_A2.md (nur Streuungen);
> feasibility/A2.yaml und Rechner F3 (ausgefuehrt); HERLEITUNG_STABILITAETSTEST.md 1, 2, 4, 6.1, 7 und
> stab_results.json; TEMPLATE_3_1.yaml, Linter registry31; FENSTERREGISTER 6, 9, 10; KONTO_ZONE_X; Registry-Kopf;
> GL-036; DATENANNAHMEN 1, 5, 12 (und 10 fuer den Futures-Kalender); KONTO_INVENTAR nur die A2-Zeilen (O-051..O-054);
> `state/runs/stress_abs.json` nur Datumsliste.
> **Marken:** [R] Rechnung des Rechners, [U] Urteil, [V] Vermutung/Modellannahme, [sek] Sekundaerbeleg, UNBELEGT.
> Dezimalkomma im Text, Dezimalpunkt in YAML/JSON.

## Kurzfassung (<= 12 Zeilen)

1. Linter registry31: **0 FEHLER, 2 HINWEIS** (P2''-Tage in Zone K = 0; G-C8 = 0 Tage), rc 0.
2. Regel: gepoolt 0,0025 (OBF, 4 K-Blicke 2027-04-01..2028-01-01, C_B 2,886) + Stabilitaetstest an jedem Stopp
   (terminal) + Konjunktion P2''/P3fix/P3all + skalierte Null + Gate (4); Zone V ein Blick = erster K-Blick (Lesart B).
3. MDE80 feste Regel (c), SE 7,58, Gate 0,9025: 24 Monate (V allein) **23,08** bp > 22 -> kein V-Blick allein; 30 Monate
   (K1) **20,64** bp, mit Datenaufschlag x1,03 **20,95** bp [R, reproduziert DEC-107 N1 (1)].
4. Gesamtregel exakt (MC, mit Konjunktion und OBF-Grenze je Blick): MDE80 des Plans **19,50 bp** (<= 22, testbar);
   je Blick kumuliert 24,56 / 22,60 / 20,96 / 19,50 bp; P(PASS | 22 bp) 0,71 / 0,78 / 0,82 / 0,84 [R].
5. Entscheidung fruehestens 2027-04-01 (moeglich); Power 0,80 an der SESOI erst am Blick 3 (2027-10-01) [R].
6. OC: P(PASS | 0) 0,00033 (Konjunktion drueckt unter 0,0025), P(PASS | SESOI) 0,842, P(PASS | 16,5 bp) 0,669;
   **Schutzzeile P(PASS bei Effekt nur im aelteren Teil, 1 MDE) 0,283** (ohne Stabilitaetstest 0,405; nur W1 0,026).
7. Strenge-Quotient **1,2548** (< 1,3; keine Vorlage nach E8 (b)); Zerlegung: P3fix x1,122, P3all x1,001, Null x1,000,
   Gate x1,118; Stress-Sensitivitaet 21,46 bp (x1,10; gegen Grundfassung 1,38).
8. Stress-Zeile (SE 8,52): Plan 21,46 bp, P(PASS | 22) 0,81, feste Regel 30 Monate 23,20 bp; E7 (c)-Vorbehalt greift
   nur bei fester Planungs-SE in der Schwelle (alpha_eff 0,0063) - t-artige Schwelle aus der Konfirmations-SE: 0,0025.
9. Jahresbuch 2027: vorher 0, mit A2 0,0025 (MC-Anteil 2027 0,00023); K 1, kumuliert 1; STRESS_ABS-Tage 3 (W1 2, W2 1).
10. **Reachability-Befund:** P2'' nach DEC-103 E3 erreicht in Zone K **0 Tage** (taegliche Futures-Deliveries seit
    2026-04-04); Entwurf setzt fuer K P2' (alle Mo-Do, Gabelung F-4, Richtung Testbarkeit) - Entscheid O/N noetig.
11. Vorfenster-SE 2023-07..2024-06 nachzuliefern (Konto); Hinweis [R]: T2-Zeile V3 ergibt ~5,5 bp statt 7,58
    (feste Regel 30 Monate dann ~15 bp) - Planungsgroesse, aendert alpha nicht.
12. Offen fuer Review/Orchestrator: Vorfenster-SE, Negativ-Panel-Probe (Gate-(4)-Faktor UNBELEGT), PK-Fixture,
    Placebo in K, OBF-Grenze fuer Nebenbedingungen, MDE80-Lesart (Plan 19,50 gegen Orchestrator 20,95).

## 1. Rahmen und Lesarten (vor jeder Zahl fixiert) [U]

- **Geltung:** Registrierung fuer Kohorte 1 (2027-01-01) vor dem Stichtag; steht unter 3.1 (BE-06). Variante (c)
  (DEC-107 (1)); Nuisance BE-04; Zonen Lesart B (VR-d17): Zone V (W1/W2) ein Blick zusammen mit den reinen K-Quartalen
  (F1 ab 2026-10-01, FENSTERREGISTER 6); die K-Luecke 2026-07..09 ist nicht urteilstragend (DEC-104 N1 (2)).
- **Blickplan:** Daten je Blick = V 24 Monate + K 6 / 9 / 12 / 15 Monate = 30 / 33 / 36 / 39 Monate an den Blicken
  2027-04-01, 07-01, 10-01, 2028-01-01 (Brief; stab_results s4b "V24+K_30_33_36_39"). Die Zone-V-Oeffnung ist der
  erste K-Blick: ein V-Blick allein (24 Monate) haette MDE80 23,08 bp > SESOI und wuerde einen Blick ohne Power
  verbrauchen (Gabelung G-07).
- **Konjunktion:** vier PASS-Bedingungen je Blick (P2''-z, P3fix-z, P3all-z mit derselben OBF-Grenze; Null-Bedingung
  als Boden tau95 x SE), Stabilitaetstest nur auf dem P2''-Kontrast (HERLEITUNG_STABILITAETSTEST 6.1), terminal.
  Scheitert eine Nebenbedingung bei erreichter P2''-Grenze, laeuft die Konfirmation zum naechsten Blick weiter;
  alpha bleibt durch die P2''-Grenze begrenzt (PASS ist Teilmenge von "P2'' kreuzt irgendwann") [R: alpha-Kontrolle
  Primaerstatistik allein 0,00246 gegen stab_results 0,00249].
- **Gate (4):** Negativ-Panel XRP/BNB(/SOL) beta-residualisiert, als Faktor 0,9025 (0,95 je Symbol, UNBELEGT bis zur
  Probe; Daten seit 2026-11-04 bei Data-Harvest, DATENANNAHMEN Zeile 1 Nachtrag 2026-11-04).
- **Modell des Rechners [V]:** Gauss-Kontrastmodell der Akte (NULL_SIMULATION T3; feasibility31
  `conjunction.shared_term_spec`): Kontrast_j = Ebar - Pbar_j mit gemeinsamem Ereignis-Term (Var c_E s_E^2 / N_E,
  c_E 1,1491, s_E 43,83), Placebo-Terme unkorreliert, effektive Tagesvarianz je Placebo aus den veroeffentlichten
  Fenster-SEs (sigma_j^2 = (SE_j^2 - Var(Ebar)) x N_j; W1 und W2 stimmen auf < 1 % ueberein: P2'' 2.375, P3fix 5.056,
  P3all 151 [R]); 13 Quartalsbloecke (W1 4, W2 4, K 5) mit Kalenderzaehlungen (W2-Q4: P2'' 0, 12 feste Freitage,
  F-1); Null-Bedingung skaliert mit kappa = 1 - feste Freitage / N_E und Zentrumsrauschen 2,97 x 52/N_E; Brownsche
  Information nach Ereigniszahl; Welch-Grenze als z-Grenze (bei >= 40 Clustern alpha_stab 0,0498..0,0506 nach Welch,
  HERLEITUNG 5). Grenzen: Normalitaet, Cov(P_i, P_j) = 0, kein Regimebruch in K, Gate (4) unabhaengig.

## 2. Herleitung je Pflichtzeile (PZ-01..PZ-30 und Kopffelder)

**Kopf (id, klasse, hypothese, ertragsquelle, metric, richtung).** id H-34 = naechste freie Nummer (GL-036). Klasse E,
kapitalfrei (C.2). Hypothese: ein Satz mit Richtung negativ (DEC-103 E2: Fall vor dem Verfall, Richtung [sek], bindend
erst mit dieser Registrierung; BE-08 offen -> DEC-58 E4: Richtung aus V-5c primaer, Groesse Etikett). Metric und
Statistik nach VR-e10; Placebosatz VR-e11; Gate-Text PRD 5.2 (1)-(6) mit den Ersetzungen VR-e09..VR-e15 (PRD v3 4.2).

**PZ-13 `zone`, PZ-30 `vorwissens_klasse`, PZ-14 `cohort`.** F1-Eintraege X (2021-03-24..2024-06-30, nur Nuisance),
V (2024-07-01..2026-06-30, `ausnahme: a2_r_pre`, VR-d16) und K (rein ab 2026-10-01, FENSTERREGISTER 6). Kohorte
2027-01-01 (VR-d13). Vorwissens-Klasse nach FENSTERREGISTER 2/6: F1 nur prospektiv, A2-Ausnahme; die 1-min-Kerzen
(F6-Strom) tragen die F1-Aggregatstatistik; Kalender F4 nur SK0. Linter R06/R08/R09 OK.

**PZ-25 `lesestatus`.** Gelesen: NULL_SIMULATION (nur Streuung), a2_vorarbeit.json (Teil B, B-2-Kanal offengelegt,
O-053), stab_results.json, feasibility/A2.yaml, stress_abs.json (Datumsliste); a2_teilC.json Fassung 2 (Arbeits-
verzeichnis, nur Streuung) als gelesen; nie berechnet: jede r_pre-Cluster-Serie auf W1/W2 (DEC-103 N1 (7)) und in K.

**PZ-29 `c17_refs`.** A2-Zeilen des Konto-Inventars: O-051 (Ereigniszensus, Instrumentzahlen bis 2026-06-30 gesehen),
O-052 (Kontraktzahlen, Futures-Kalender, Funding-Termine W1/W2), O-053 (sigma30-Nuisance, B-2-Kanal), O-054
(Null-Simulation, Funding-Termine); O-009 (WP-10(A2)-Spearman-Matrix mit IV-RV bis 2026-07-31, F1-Marktebene) und
O-902 (Kontaminations-Register: Presse-Schlagzeile zu einem Deribit-Verfall 2026 mit Preisniveau) als Vorbelastung.
Kein r_pre-Mittel je gebildet (Inventar Abschnitt 3 "A2 EXP-CLOCK: 0").

**`windows`.** W1, W2 (Zone V, urteilstragend, VR-d01), K1 2026-10-01..2027-12-31 (Zone K, urteilstragend; Ende =
letzter Blick 2028-01-01 minus einen Tag). Kein Pilotfenster (Pilot-Route nur Vorlage, VR-g06).

**PZ-15/PZ-16 `decision_rule`.** alpha_test 0,0025, z_krit 2,8070, Variante c, screen null; Stabilitaetstest nach
DEC-107 (1) (a)-(e) mit Text aus HERLEITUNG 7.1: D = Mittel juengster Teil (letzte 12 Monate vor dem Blick, Lesart B
inkl. V-Ende) minus aelterer Teil, Welch-t einseitig 0,05, an jedem Wirksamkeits-Stopp, terminal; entfaellt bei <= 12
Monaten (tritt nie ein: erster Blick 30 Monate). Kostenquote: q 0,95 registriert (konservativ); exakt je Blickplan
0,9639 (s4b each_term; R_max 1,084 N_fix); Sensitivitaet k 0,7..1,5 -> q 0,943..0,966 (HERLEITUNG 2.3). mde_faktor
4,3062 = z_krit + Phi^-1(0,80 / (0,95 x 0,9025)) [R] (ohne Gate 3,8102; mit q_plan 4,2099); nie Schwelle.

**PZ-17 `looks`.** zone_v anzahl 1 (= erster K-Blick); zone_k 4 Blicke, O'Brien-Fleming, C_B 2,886 (s4b, exakt),
Informationsanteile nach Ereigniszahl 130/143/156/170 [R, Kalender], z-Grenzen 3,300 / 3,147 / 3,013 / 2,886,
`screen_an_jedem_stopp: true` (unter (c): Stabilitaetstest an jedem Stopp, DEC-107 (1) (c)), Futility Z < 0 an den
Blicken 1-3 (VR-d12; unter H0 stoppt sie 58 % der Pfade [R]), Grenzen t-artig (df = Cluster - 1; am Blick 1 df 129,
t_0,0025 2,856 gegen 2,807 [R]). Erster Blick mit 130 Clustern >= 26 (OC (e)).

**PZ-18 `sesoi_curve`, PZ-02 `economic_minimum`.** SESOI 22 bp = 2 x 11 bp Taker-Wand je Bein (KRITIK_PRD K-10 Zeile
A2; DEC-104 E7 (d)); Maker 2 x 5,4 = 10,8 bp als Gabelungsetikett (VR-c01). Einzelpositionsrahmen (Klasse E,
VR-c04). Kurve: Ereignis-Horizont (ein Tag, einmaliger Umschlag), daher konstant in Horizont und Persistenz (drei
Punkte 22,0 bp; phi 0 Default mit Etikett). Kein registriertes Kostenmodell tradability3 (WD-08, Modul nicht im
Repo): `kostenmodell_constants_hash` = sha256 der Quelle KRITIK_PRD.md (8c198d01...), `constants_hash`
"n/a - kapitalfrei ohne Kostenmodell" (R23 OK). economic_minimum 22 bp, Etikett ueber_wand, nie Gate (C.2, BE-03).

**PZ-19 `prior_label`.** Literatur UNBELEGT (V-5b: Richtung [sek] Weiss et al. 2026, Ni/Pearson/Poteshman 2005; keine
Basispunkt-Zahl, DEC-103); Sensitivitaetsspanne 5..25 bp, nominal 16,5 bp (T6-Referenzzeile [sek]) in beide
Richtungen (VR-c07); kein Zone-X-Prior (Mittel in der Vorperiode verboten, VR-g06); Fallzahl nur gegen SESOI (VR-f09).

**`threshold`, `structural_null` (VR-e12, VR-e06).** Schwelle max(oberes 95-%-Quantil der skalierten Null;
t_krit x SE_Konfirmation) je Bedingung und Blick, OBF-alpha je Blick; SE aus den Konfirmationsdaten (DEC-107 N1 (2)),
damit alpha unter jeder Nuisance 0,0025 (E7 (c) gegenstandslos). Null: J-(i) Label-Permutation je ISO-Woche,
>= 1.000 Replikate, Seed 103 + Fensterindex, Labelmatrix nur intern (A-8); skaliert k = max(1, SE_Lauf / Null-SD);
feste Freitage F-1 (W2 kappa 0,815); P3-Identitaet N3-1; Grenze Wochentagseffekt offengelegt.

**`nuisance` (BE-04, VR-b10, VR-e03).** Bindend das juengste Vorfenster 2023-07-01..2024-06-30 (12 Monate vor W1),
groessere SE aus Vorfenster und Null-Simulation dieses Fensters; **nachzuliefern durch den Orchestrator als
Konto-Eintrag** (DEC-107 N1 (2)); Platzhalter 7,58 (Null-Simulation W2 zentral), Sensitivitaet 7,34 (W1) / 8,52
(Stress V1). Stress-Zeile: siehe Abschnitt 3. Hinweis [R, reine Arithmetik aus T2]: die veroeffentlichte Zeile
V3 (2023-06..2024-05) hat P2''-SE 5,31 (eigene N 53/209), mit W2-Zaehlungen 52/159 5,51 bp, Null-SD 4,51; mit 5,51
laege die feste Regel bei 30 Monaten bei 15,0 bp. Das ist nur ein Hinweis auf die Groessenordnung des bindenden
Vorfensters; die Lesart (eigene N des Vorfensters oder Konfirmations-N; Vorfenster 2023-07..2024-06 gegen V3) legt
der Orchestrator im Konto-Eintrag fest. Planungs-SE aendert alpha nicht, nur MDE/OC/PK-Injektion.

**PZ-01 `power`, PZ-03 `cluster_unit`, PZ-23 `n_eff`, PZ-24 `c_overlap`.** SE-Regel VR-b09 (Bootstrap, c >= 1,
Blocklaenge aus der ACF; je Teil getrennt im Stabilitaetstest). sd_teststatistik 7,58 (SE_12 P2'' W2 zentral). MDE80
registriert **19,50 bp** = Effekt mit P(PASS bis Blick 4) = 0,80 inklusive Gate (4) ueber die gesamte Regel
(VR-b14 "gemeinsame Entscheidungsregel", VR-b08 mit der SE des Tests) [R, MC]; <= SESOI 22 -> testbar. Cluster =
Ereignis (Kalendertag, VR-b03); n_eff 130 Ereignis-Cluster am ersten Blick (104 in V + 26 in K; N_E/c_MoDo = 98,7;
170 am Endblick), Placebo-Tage 471 (P2''/P2') am Blick 1; c_overlap 1,3177 (c_bind Mo-Do, groesster der Klassen;
Freitag 1,1491).

**PZ-04/PZ-20 `selection`.** K = 1 (eine registrierte Variante: P2''-Kontrast auf x; Placebosatz ist Konjunktion,
keine Varianten; Gabelungen ohne Datenblick zaehlen nicht, N1 (9)); kumuliert F-EXPCLOCK 1 (Inventar: 0 vorher).
z_max(1) = 0, die Power-Zeile rechnet mit max(z_krit, 0) = 2,8070 (VR-b04); Decke am Null-Fixture (T1) zu messen.

**PZ-26 `design_menu` (VR-e01).** Optionen D1..D5 (Placebo P2'' ueberall / P2'' in W1,W2 und P2' in K / K allein
/ ein Endblick / V allein); mechanische Regel: Placebo je Fenster P2'' nur bei N_P2'' >= 0,5 x N_MoDo (Kalender SK0;
W1 208/208, W2 159/207, K 0/261), sonst P2'; Plan = kleinste Plan-MDE80 <= SESOI, bei Gleichstand frueherer Blick.
Gewaehlt D2. Begruendung der Kalenderzahlen: DATENANNAHMEN 10 / O-052 (taegliche Futures-Deliveries seit 2026-04-04);
NULL_SIMULATION 5.3 (alle Mo-Do 2026-04-06..06-25 Futures-Tage). Ausnahme (i) der VR-e01 (A2-Schwelle) ist durch die
t-artige Schwelle aus der Konfirmations-SE und die bindende Vorfenster-Lesart (oben) etikettiert.

**PZ-27 `reachability` (VR-f07).** Ereignis-Freitage 170 (52 + 52 + 66 [R, Kalender: K-Quartale 13/13/13/13/14]);
P2'' W1+W2 367; **P2'' in K 0** (HINWEIS des Linters, beabsichtigt - Grund fuer D2); P2' in K 261; P3fix 807, P3all
846; Cluster am Blick 1 130; STRESS_ABS-Tage 3 (W1: 2024-08-05 Mo, 2025-02-03 Mo; W2: 2025-10-10 Fr; K bis heute 0;
2026-08-19 liegt in der nicht urteilstragenden Luecke); Ereignis-Freitag mit Stress 1; G-C8 0 Tage (HINWEIS).

**PZ-21 `oc_line` (VR-f04; DEC-107 (1) (e)).** Simulation der gesamten Regel (300.000 Pfade, Seed 20261104) [R]:
P(PASS | 0) 0,00033 (Regel ohne Gate 0,00037; Primaerstatistik allein 0,00246 - die Konjunktion mit OBF-Grenzen je
Nebenbedingung drueckt alpha weit unter 0,0025); P(PASS | SESOI 22) 0,842; P(PASS | 16,5) 0,669 (Spanne: 5 bp 0,017,
25 bp 0,855); **Schutzzeile P(PASS | Effekt 1 MDE nur im aelteren Teil = Zone V, 0 in K) 0,283** (kumuliert je Blick
0,227 / 0,255 / 0,270 / 0,283; "veraltet", d. h. PASS an den Blicken 3-4 mit effektfreiem juengstem Fenster, 0,028;
Stabilitaets-FAIL 0,242); ohne Stabilitaetstest 0,405; 2 MDE nur in V 0,319; Effekt nur in W1 0,026. Vergleich:
ein Blick, Primaerstatistik, r 1/2: 0,0729 (s0); Plan s4b each_term ohne Konjunktion/Gate 0,299. Der hohe Wert ist
der bekannte Preis von (c) bei langem aelterem Teil (DEC-107 (1) (f): bis 0,55) - keine Abweichung, aber Pflicht-
ausweis. Die Zahl geht in die Vorlage, falls der Orchestrator sie fuer A2 als unzureichend ansieht (Gabelung G-09).

**PZ-22 `strictness_ratio` (VR-f05, OC (g)).** Grundfassung = P2''-Kontrast allein, zentrale Nuisance 7,58,
dieselbe Regel (c) mit Blickplan, ohne Null-Bedingung, ohne Gate: 15,54 bp [R]. Kette: + P3fix exakt 17,43 (x1,1216);
+ P3all 17,44 (x1,0006); + skalierte Null (kappa, Zentrum) 17,44 (x1,0000; unter OBF-Grenzen 2,89..3,30 bindet der
Null-Boden 1,655 x SE nicht); + Gate (4) 19,50 (x1,1181). **Quotient 1,2548 < 1,3**: keine Nutzer-Vorlage nach E8 (b)
[R]. Stress (Sensitivitaet, nicht im Quotienten): 21,46 bp, gegen Grundfassung 1,381 - eine bindende Stress-Zeile
haette die Vorlage ausgeloest (wie DEC-104 N4 (5): 1,44). Doppelausweis Blick 1 (feste Regel, 30 Monate, OBF-Grenze
3,300, q 0,95, Gate): Produkt 25,10 bp gegen exakt gemeinsam 24,56 bp (DEC-105 (7)).

**PZ-28 `annual_book` (VR-d14).** 2027: vorher 0 (keine registrierte Hypothese mit Blick in 2027: H-27..H-33 GL-012
oder geschlossen, FENSTERREGISTER 8); mit A2: Summe alpha 0,0025 (konservativ; MC-Anteil der Blicke 1-3 in 2027
0,00023, Blick 4 am 2028-01-01 0,00010); < 0,10. Die Positivkontrolle ist synthetisch und zaehlt nicht.

**PZ-02 `decision_relevance`.** PASS = Mess-PASS (Praemien-Existenz des Verfallstag-Kontrasts); naechster Schritt
nur Pflicht-Bestaetigung auf neuen Daten (VR-b15) und getrennt registriertes Tradability-Gate (Quote-Schatten,
kapitalfrei, VR-g08); DROP/FAIL schliesst A2 auf BTC/ETH fuer Kontraste >= Ausschlussgrenze; GL-012 (Futility) ohne
Verdikt mit Schaetzer/CI/Ausschlussgrenze (VR-f01).

**PZ-09 `capital_tax_venue`.** kapitalfrei; m UNGEMESSEN mit Sensitivitaetsetikett; Steuer "UNBELEGT - PRD 8.2";
Venue-Ereignisse: Deribit-Kalender (taeglich Optionen seit 2020-03-25, taeglich Futures seit 2026-04-04), Ausreisser
2020-08-27 / 2024-08-19 (VR-e09), CME-Fenster [sek] (VR-e14); Zahler nach 2024: Kontraktzahlen Freitag ~13x Mo-Do
(O-052), OI-Proportionalitaet UNBELEGT.

**PZ-10 `stress_episode` (VR-g13).** STRESS_ABS (Liquiditaets-/Fill-Frage des TWAP-Fensters), Datei-sha256
b8008257... (Fixture-Feld b75fb7a0...), Rolle Abdeckungsnachweis, 3 Tage in den Urteilsfenstern [R, nur Datumsliste];
Erreichbarkeit: eine Stress-Zelle mit 1 Ereignis-Freitag ist keine Schaetzgrundlage - Stress wirkt nur als
Nuisance-Sensitivitaet (BE-04), nie als Filter.

**PZ-07 `irreversibility_probe`.** Nachladbar: `rest.kline1m` BTCUSDT/ETHUSDT im Archiv, Negativ-Panel XRP/BNB/SOL
seit 2026-11-04 (DATENANNAHMEN 1, 5, Nachtraege 2026-11-04); Kalender `rest.settlements` / `deliveryPrices`;
Alternative Minutenbars aus `bybit/publicTrade` (Zeile 5); kein Dauerstrom noetig.

**PZ-08 `positive_control` (VR-f12; DEC-103 N1 (8e)).** Vorgeschaltet, allein, Produktionskonfiguration mit der
registrierten YAML; Welt = J-(i)-Null mit Kalenderstruktur der Konfirmationsfenster und Vorperioden-Streuung;
Injektion 19,50 bp (MDE80 des Plans) in registrierter Richtung an allen Ereignis-Tagen; Kriterium vorab: PASS-Quote
ueber 200 Seeds >= 0,80 - 2,3263 x sqrt(0,8 x 0,2 / 200) = **0,7342** [R] und SD der Kontrollwelt <= 1,10 x 7,58 bp
(VR-b10) und Gate (4) in der Kette; NICHT BESTANDEN -> kein Lauf, Ursachenanalyse, neue DEC. Fixture-Bau nach der
Registrierung (P-0); die Welt braucht die Negativ-Panel-Daten (XRP/BNB/SOL) fuer Gate (4).

**PZ-05 `fixtures`.** Positiv (Injektion), Null (J-(i) und Random Walk mit realem Kalender), adversarial Klasse E
(PZ-05: auf vergangenen Renditen selektierte Ereignisse auf einem Random Walk; zusaetzlich reiner Wochentagseffekt
in allen Symbolen -> Gate (4) FAIL).

**PZ-12 `test_pflichten`, PZ-11 `artifacts`/`report_line`, `fdr`, PZ-06 `constants_hash`, `code_sha256`,
`data_fingerprints`.** T0-T7 als verbindliche Test-IDs in `tests/unit/test_a2_expclock.py` (Bau nach der
Registrierung, P-0; fehlt etwas: KEIN VERDIKT). Artefakte: Cluster-Serie je Ereignis-Tag mit sha256, Bootstrap-Seed
20261104 + Generator-Fingerprint, J-(i)-Replikate; Berichtszeile DEC-105 (neun Felder); FDR: Familie F-EXPCLOCK
(K 1), p des gepoolten P2''-Tests am Stopp-Blick, Kohorte BY q 0,10 (VR-d13). code_sha256: Rechner dieses Entwurfs,
stab_sim.py, feasibility31/rules.py (Pfad des Rechners = vorgesehener Ablageort `state/herleitung_a2/registrierung/`).
Fingerprints: Akten-Hashes, Repo-Commit a874fa75, Panel-Fingerprint vor dem Lauf.

## 3. Feasibility-Satz (VR-e08, DEC-107 N1 (1)) [R]

| Groesse | zentral 7,58 | W1 7,34 | Stress 8,52 |
|---|---|---|---|
| feste Regel (c) + Gate, 24 Monate (V allein) | **23,08** | 22,35 | 25,94 |
| feste Regel, 27 Monate | 21,76 | 21,07 | 24,46 |
| feste Regel, 30 Monate (K1 2027-04-01) | **20,64** (x sqrt(1,03) = **20,95**) | 19,99 | 23,20 |
| feste Regel, 33 / 36 / 39 Monate | 19,68 / 18,85 / 18,11 | 19,06 / 18,25 / 17,53 | 22,12 / 21,18 / 20,35 |
| 22 bp erreicht ab (feste Regel) | 26,4 Monate | 24,8 | 33,4 (Blick 2027-10-01) |
| Gesamtplan exakt: MDE80 (P(PASS bis Blick 4) 0,80) | **19,50** | - | 21,46 |
| Gesamtplan: MDE80 kumuliert je Blick 1..4 | 24,56 / 22,60 / 20,96 / 19,50 | - | - |
| P(PASS bei 22 bp) kumuliert je Blick | 0,713 / 0,784 / 0,822 / 0,842 | - | 0,599 / 0,703 / 0,770 / 0,812 |

- Die Zeile "feste Regel" reproduziert DEC-107 N1 (1) exakt (23,08 / 21,76 / 20,64 / 26,42 Monate / 20,95) [R].
- **Entscheidung fruehestens 2027-04-01** (erster Blick, 130 Cluster). Mit OBF-Grenze 3,300 am Blick 1 und der
  Konjunktion liegt die Power an der SESOI am Blick 1 bei 0,71; die gemeinsame Power 0,80 (VR-b14) wird am Blick 3
  (2027-10-01) erreicht; die registrierte MDE80 ist die des Plans (19,50 bp <= 22). V allein (23,08 bp) ist nicht
  testbar -> kein V-Blick vor 2027-04-01.
- **Stress-Sensitivitaet:** Plan 21,46 bp (<= 22, P(PASS | 22) 0,81), feste Regel 30 Monate 23,20 bp, 22 bp erst
  2027-10-01. E7 (c)-Vorbehalt: nur bei fester Planungs-SE in der Schwelle (z_eff 2,497, alpha_eff 0,0063); mit der
  t-artigen Schwelle aus der Konfirmations-SE bleibt alpha 0,0025 (DEC-107 N1 (2); WD-03 geschlossen).
- **Lesart-Abweichung (fuer den Review):** der Orchestrator fuehrt 20,95 bp (feste Regel bei 30 Monaten, Primaer-
  statistik, Datenfaktor 1,03); die exakte Plan-Rechnung ergibt am Blick 1 24,56 bp (OBF-Grenze 3,30 statt 2,81,
  Konjunktion x1,12) und ueber den Plan 19,50 bp. Beide sind <= 22 nur in der Plan-Lesart; die YAML registriert
  19,50 mit Fundstelle.

## 4. Gabelungsregister (jede Festlegung mit Alternative und Richtung) [U]

| Nr | Festlegung (Entwurf) | Alternative | Richtung der Alternative | Wirkung [R] |
|---|---|---|---|---|
| G-01 | Variante (c), q 0,95 registriert | q_plan 0,9639 (s4b) | Testbarkeit (MDE-Faktor 4,210 statt 4,306) | ca. -2 % MDE |
| G-02 | Placebo in Zone K = P2' (alle Mo-Do), in W1/W2 P2'' (F-4 nur fuer K, mechanische Regel) | (a) P2'' woertlich: 0 Tage in K, K-Freitage alle fest, kappa faellt, Kontrast in K undefiniert; (b) P2' auch in W2 (F-4 voll, SE 7,34 statt 7,58) | (a) Strenge bis Unbrauchbarkeit; (b) Testbarkeit, Inhomogenitaet W1/W2 vermieden | (b): -3 % SE in W2 |
| G-03 | Nebenbedingungen P3fix/P3all mit derselben OBF-Grenze je Blick | fest 2,8070 je Blick | Testbarkeit (alpha unveraendert, da P2''-Grenze traegt) | P3fix-Faktor < 1,12 |
| G-04 | Nebenbedingung scheitert bei erreichter P2''-Grenze -> weiter zum naechsten Blick | terminaler FAIL | Strenge | P(PASS) sinkt, veraltete PASS sinken |
| G-05 | Gate (4) als Faktor 0,9025 (UNBELEGT) | Power aus Negativ-Panel-Daten | offen; bei Power 0,99 je Symbol MDE -6 % | x1,118 heute |
| G-06 | Nuisance zentral 7,58 als Planungs-Platzhalter | bindendes Vorfenster (Konto); V3-Hinweis ~5,5 | Testbarkeit bei ruhigem Vorfenster; alpha neutral | feste Regel T30 15,0 bp bei 5,51 |
| G-07 | Zone-V-Blick = erster K-Blick | eigener V-Blick 2027-01-01 (24 Monate) | Zeit; nicht testbar (23,08 > 22), verbraucht Blick | - |
| G-08 | Blickplan 4 Quartale | ein Endblick 2028-01-01 (q 0,95, feste Regel 39 Monate 18,11 bp) | Testbarkeit (MDE), keine fruehe Entscheidung | -7 % MDE, +9 Monate |
| G-09 | Schutzzeile 0,283 hingenommen (Preis von (c)) | Screen 0,05 (a; Boden 24,30, nie testbar) oder alpha_stab 0,10 (q 0,90) | Strenge (REZENZ) | alpha_stab 0,10: Daten x1,22 (HERLEITUNG 2.2) |
| G-10 | Stress nur Sensitivitaet (BE-04) | Stress bindend | Strenge | 21,46 statt 19,50 bp; Quotient 1,38 -> Vorlage |
| G-11 | SESOI Taker 22 bp | Maker 10,8 bp | Strenge (nie testbar: Plan 19,50 > 10,8) | - |
| G-12 | F-1 (12 feste Freitage W2) | F-3 (aus E entfernen) / F-4 | Strenge in SE / Testbarkeit | NULL_SIM T6a |
| G-13 | t-artige Schwelle aus Konfirmations-SE | feste Planungs-SE in der Schwelle | Lockerung des effektiven alpha (0,0063 unter Stress) - abgelehnt | - |
| G-14 | Futility Z < 0 an Blicken 1-3 | ohne Futility | Testbarkeit (keine Wirkung an der MDE), Zeit unter H0 | E[N bei H0] 0,65 |
| G-15 | Konjunktion exakt gemeinsam (VR-e04) | Produkt der Einzel-Powers | Strenge (Doppelausweis 25,10 gegen 24,56 am Blick 1) | +2 % |

## 5. Was nicht folgt

- Kein Verdikt ueber einen Markteffekt, keine Registrierung (nur der Orchestrator), kein Code-Bau (P-0), keine
  Aenderung an DEC-103/104/107, kein Mittel und kein Vorzeichen eines Kontrasts (Vorperiode, W1/W2, K).
- Alle Zahlen sind Fehlerraten und Aufloesungsgrenzen unter dem Modell aus Abschnitt 1 (Normalitaet, unkorrelierte
  Placebo-Terme, Brownsche Information, Welch als z, Gate (4) unabhaengig); keine Effektgroessen, keine Zusagen.
- Die Planungs-SE 7,58 ist ein Platzhalter; die registrierte MDE80 (19,50 bp), OC-Zeile und PK-Injektion sind mit
  dem bindenden Vorfenster neu zu rechnen (Rechner: `INPUTS["se12_central_W2"]` und `se_W1/se_W2` ersetzen, Seed
  unveraendert); alpha und Schwelle haengen nicht daran.
- Der Gate-(4)-Faktor 0,9025 ist eine Annahme bis zur Negativ-Panel-Probe; alle Zeilen "mit Gate" sind vorlaeufig.
- Der Stabilitaetstest schuetzt bei diesem Plan schwach gegen einen Effekt, der nur in Zone V lag (0,283); das ist
  die beschlossene Eigenschaft von (c), nicht heilbar ohne Lockerung der Testbarkeit (G-09).

## 6. Offene Punkte

**Fuer den Review (adversarisch, symmetrisches Mandat VR-f06):**
1. Pflichtfrage: ist der Test gegen SESOI/Prior nach allen Auflagen noch sensitiv? [R]: P(PASS | 22 bp) 0,842 ueber
   den Plan, 0,713 am ersten Blick; bei 16,5 bp 0,669. Bitte die MDE80-Lesart (Plan 19,50 gegen feste Regel 20,95)
   und die OBF-Grenze je Nebenbedingung (G-03) pruefen.
2. Modell des Rechners (Abschnitt 1): Placebo-Varianzen aus den Fenster-SEs, Null-Bedingung mit kappa/Zentrum,
   Welch als z, Information nach Ereigniszahl; Gegenrechnung mit eigenem Code und anderem Seed erbeten.
3. Schutzzeile 0,283: Lesart "Effekt nur in Zone V" als "aelterer Teil" (am Blick 1 ist der aeltere Teil 18 Monate,
   V-Ende liegt im juengsten Teil); alternative Definitionen (nur W1: 0,026) bitte bewerten.
4. Placebo in K (G-02): Austauschbarkeit Freitag gegen Mo-Do mit taeglichen Futures-Deliveries (Groessen-Kontrast
   bleibt: Freitag Wochen-/Monats-/Quartalsoptionen plus Futures gegen Tagesoptionen plus Tagesfutures) - ist die
   DEC-103-E1-Klassenregel damit noch erfuellt oder braucht es eine DEC?
5. Hygiene: Kanal-Test (R-C12a) auf den Rechner-Ausgaben (nur Streuungen und Zaehlungen; keine Klassen-SD einer
   Vereinigung ausgegeben); Hostnamen/Modellnamen: Linter R26 OK.

**Fuer den Orchestrator:**
1. **Vorfenster-SE** 2023-07-01..2024-06-30 als Konto-Eintrag (VR-b10 (i), Streuung/c/Null-Simulation, kein Mittel);
   Lesart der N (eigene oder Konfirmations-N) fixieren; dann Rechner neu laufen lassen, YAML-Zahlen nachfuehren.
2. **Negativ-Panel-Probe** XRP/BNB/SOL (Prueffeld-Probe vor Nutzung, DATENANNAHMEN 1 Nachtrag): beta der Vorperiode
   vorab fixieren, Gate-(4)-Power messen oder Faktor 0,9025 als Etikett bestaetigen; Entscheidung ob SOL dazu gehoert
   (DEC-103 E5 nennt XRP/BNB, Anfrage nennt drei Symbole).
3. **Positivkontroll-Fixture:** Bau nach der Registrierung (P-0) mit der registrierten YAML, Injektion 19,50 bp
   (bzw. neu gerechnet), Kriterium 0,7342 bei 200 Seeds, SD-Grenze 1,10 x Planungs-SE, Gate (4) in der Kette.
4. Entscheid zu G-02 (Placebo in K: P2' - Richtung Testbarkeit, Nachtrag zu DEC-103 E3 noetig; Lockerung -> N?),
   G-03, G-04, G-09; Strenge-Quotient 1,2548 < 1,3: keine Vorlage, aber Ausweis in der Registrierung.
5. Ablageort des Rechners im Repo (`state/herleitung_a2/registrierung/`), Hash-Pins der YAML bei der Registrierung,
   Jahresbuch-Eintrag 2027 (0,0025), FENSTERREGISTER-Nachtrag (V-Oeffnung am 2027-04-01 fuer A2 r_pre).
