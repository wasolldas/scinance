# Review: Herleitung "Kapitalregel Klasse P ohne MinTRL" (DEC-107 (5), P-10, WD-12) - 2026-11-04

Rolle: Review (adversarisch, symmetrisches Mandat: zu lax UND zu streng). Gegenstand: `HERLEITUNG_KAPITALREGEL_P.md`,
`calc/kapital_sim.py`, `kapital_results.json`, `kapital_sim.out`; Auftrag `BRIEF_kapitalregel_klasse_p.md`.
Gelesen (nur lesend, nichts geaendert): DEC-107 (5), (6); PRD v3 VR-f13, VR-a02, VR-b09, VR-b15, VR-c01, VR-d11, VR-d12,
VR-f07, VR-g08, VR-g13, VR-g14, PZ-05, PZ-09, PZ-10, 5.2 P-10, WD-12, WD-13; PRD v2 L-12, 3.6, 8.1, 8.2; DEC-56, DEC-58 E1 (e),
DEC-67 E4, DEC-74 N (1), DEC-93, DEC-97, DEC-98 N2/N5, DEC-104 E3 (e)/E8; KRITIK_PRD K-12; Kompendium C.2/C.3 und
Verdikt-Kuerzel; gate_log GL-033/GL-034; `state/runs/stress_abs.json` (nur Datumsliste und Zaehlfelder der Fixture - keine
Siegeldatei). Keine Marktdaten.

Eigene Rechnung: `calc/review_sim.py` (Seed 7071, anderer Seed als die Herleitung; Laufzeit 139 s), Stdout `calc/review_sim.out`,
Ergebnisse `review_results.json` (Abschnitte R0..R9). Marken: [R] Rechnung, [U] Urteil, [V] Vermutung, [sek] Sekundaerbeleg.

---

## 0. Gesamturteil

**ZUSTIMMUNG MIT AUFLAGEN.** 0 VETO, 5 Auflagen (B-1, B-2, B-3, B-5, B-11), 8 Hinweise (B-4, B-6..B-10, B-12, B-13).

Was steht: Die Kernformel ist korrekt hergeleitet (Ruin-Kapital, Kelly-Bruchteil-Identitaet kappa = 2/ln(1/eps), geometrisches
Drawdown-Gesetz, MaxDD-Konstante 1,2533, E[mu_L | PASS, Null] = 0,297 SE), alle Zahlen der Beispiele A1 und H-27 sind mit
eigenem Code aus den offenen Akten-Zahlen reproduziert, und die alpha-Vererbung P(Kapital > 0 | Null) <= 0,0025 haelt in
jeder geprueften Variante (anderer Seed, Serienebene, OBF-Blicke, Kosten k > 0). C.2 ist gewahrt: die PASS-Bedingung
bleibt woertlich unveraendert, `L* > 0 => PASS`, nie umgekehrt.

Was nicht steht: (i) Die Herleitung rechnet mit genau einem Blick; Zone K ist gruppensequentiell (VR-d12, OBF, 4 Blicke).
Mit festem `z_ci = 2,8070` springt mu_L an einem fruehen Wirksamkeits-Stopp um 2,86 / 1,20 / 0,46 SE_k (Blick 1/2/3); die
Aussage "stetig an der PASS-Grenze, kein Klippeneffekt" gilt dort nicht, und der Gewinner-Fluch des fruehen Stopps
(E[mu_hat/mu] 1,66 an Blick 2) wandert ungebremst in L* [R, R3] - zu lax. (ii) Die Zeitboden-Aussage "fruehestens 2029"
beruht auf 3,65 STRESS_ABS-Tagen je Jahr (Konstruktion); die Fixture selbst zeigt seit 2023 nur 1,36 Tage je Jahr (5 Tage
in 3,67 Jahren, davon 2 benannte), W1/W2 1,5 je Jahr. Median des ersten positiven Kapitalwerts bei stress_n_min 10 damit
2033/2034, P(bis 2029) ~0 [R, R7] - die Regel ist bei dieser Rate de facto wieder PARK bis ~2033, also zu streng gegen
die Absicht von DEC-107 (5). (iii) Das Stress-Bein ist keine Peso-Protektion: mit 10 nicht-informativen Markt-Stress-Tagen
(keine Strategieverluste darin) empfiehlt die Regel in der Peso-Welt median 2,45x, ein -35-%-Sprung kostet 86 % des
Kapitals - identisch mit "ohne Stress-Bein" [R, R6]; PZ-05 ("Gate MUSS durchfallen") kann die Luecke nicht schliessen, weil
der gepoolte Test die Peso-Fixture bei n 52..260 Wochen mit 8..15 % passiert [R, R9]. Abhilfe in allen drei Faellen ist
eine Praezisierung, kein Umbau: blickabhaengiges z_ci (oder nur am Bestaetigungsblick rechnen), Szenario-Boden fuer s_up,
Nutzerfrage zu stress_n_min mit der Fixture-Rate.

---

## 1. Befunde

### B-1 (Auflage, Richtung zu lax) - Gruppensequentielle Blicke ignoriert: mu_L springt an fruehen Stopps, Gewinner-Fluch im Kapital

**Beleg.** Herleitung 1.2 (a): "Die alpha_test-Grenze ist stetig an der PASS-Grenze ... kein Klippeneffekt"; 1.4 (ii)
"stetig und monoton"; Kurzfassung 1: `mu_L = mu_hat - 2,8070 SE`. Simulation S1/S4 rechnen genau einen Blick. VR-d12:
Zone K "Blicke nach O'Brien-Fleming, bis zu 4 Blicke ... alpha gesamt 0,0025 je Test; Wirksamkeitsabbruch am Blick k";
DEC-107 (1)(c): Stabilitaetstest "an jedem Wirksamkeits-Stopp".

**Rechnung [R, R3].** OBF-Grenzen fuer 4 gleich grosse Blicke bei einseitig 0,0025 (MC-kalibriert, 4e6 Pfade):
z_1..z_4 = 5,665 / 4,006 / 3,271 / 2,833; P(PASS | Null) = 0,002500. Mit festem z_ci 2,8070 ist mu_L an der Grenze des
Blicks k gleich (z_k - 2,807) SE_k > 0: Sprung 2,858 / 1,199 / 0,464 / 0,026 SE_k. Unter der Null: E[mu_L | PASS] = 0,414
SE_final (fest) gegen 0,263 (blickabhaengiges z_k) und 0,297 (Ein-Blick-Referenz der Herleitung); min mu_L | PASS = 0,026
SE_final > 0 (nicht stetig). Null-PASS enden zu 1,4 % / 20,1 % / 78,5 % an Blick 2/3/4. Unter H1 an der MDE80 (3,8101
SE_final): E[mu_hat/mu | Stopp an Blick 2/3/4] = 1,66 / 1,19 / 0,92, und E[mu_L(fest)/mu] = 0,62 / 0,34 / 0,18 - der
fruehe Stopp empfiehlt das 3,4-fache des spaeten Stopps bei gleichem wahren mu. Die alpha-Vererbung bleibt gewahrt
(P(L* > 0 | Null) <= P(PASS | Null) = 0,0025), die Groesse nicht.

**Auflage.** (a) `ci_basis` lautet "untere Grenze zum Niveau der Grenze des Stopp-Blicks": `mu_L = mu_hat_k - z_k SE_k` mit
z_k aus dem registrierten Spending-Plan (YAML-Feld `z_krit` ist dann die Blickgrenze, nicht 2,8070); oder (b) L* wird
ausschliesslich am Bestaetigungsblick nach VR-b15 mit der gepoolten Statistik und deren Grenze gerechnet (siehe B-5).
(c) Die OC-Zeile `oc_kapital` wird ueber den registrierten Blickplan simuliert (nicht Ein-Blick-Formel), mit Ausweis von
E[L* | PASS, Null] und E[L*/L*_wahr | Stopp-Blick]. (d) Satz "stetig an der PASS-Grenze" auf "stetig je Blick" einschraenken.
Zusatz [U]: Die Gruppensequenz macht auch die Aussage 1.4 (iv) "Schaden eines falschen PASS beschraenkt, 0,297 SE" zu einer
Untergrenze (0,41 SE_final mit festem z).

### B-2 (Auflage, Richtung zu streng) - Zeitboden des Stress-Beins falsch beziffert; stress_n_min 10 ist bei der Fixture-Rate PARK bis ~2033; Episodenbegriff fuer STRESS_ABS offen

**Beleg.** Herleitung 3.6: "bei 99-Perzentil-Definition fallen im Erwartungswert ~3,65 Stress-Tage je Jahr [R, Konstruktion],
also >= 2,7 Jahre Zone K ... fruehestens 2029"; Kurzfassung 12 "fruehestens 2029"; 5 "Zeitboden ... >= 2,7 Jahre Zone K".
Fixture `state/runs/stress_abs.json` (nur Daten): 30 Tage, 19 Episoden (Feld `n_episodes`), 2020-05-10..2026-08-19; je Jahr
2020 1 / 2021 16 / 2022 8 / 2023 1 / 2024 1 / 2025 2 / 2026 1; W1 2 (2024-08-05, 2025-02-03), W2 1 (2025-10-10, benannt),
Zone K bisher 1 (2026-08-19, benannt). DEC-74 N (1) bestaetigt W1 2 / W2 1. DEC-56 (2): 99-Perzentil der GESAMTEN
WP-0-Historie - 24 der 30 Tage liegen in 2021/22; die 1-%-Rate ist ein Mittel ueber ein Regime, das seit 2023 nicht mehr
gilt.

**Rechnung [R, R7].** Poisson-Wartezeit auf die n_min-te Episode ab 2026-07-01 (Gamma(n_min, rate)):

| n_min | Rate/Jahr (Quelle) | Median | P(bis 2029) | P(bis 2031) | P(bis 2033) |
|---|---|---|---|---|---|
| 10 | 3,65 (Konstruktion, Herleitung) | 2,6 a -> 2029 | 0,43 | 0,96 | 1,00 |
| 10 | 3,02 (Fixture gesamt, Episoden) | 3,2 a -> 2030 | 0,23 | 0,87 | 0,99 |
| 10 | 1,36 (Fixture ab 2023, Tage) | 7,1 a -> 2034 | 0,00 | 0,09 | 0,39 |
| 10 | 1,50 (W1/W2, Tage) | 6,4 a -> 2033 | 0,01 | 0,15 | 0,51 |
| 5 | 1,36 | 3,4 a -> 2030 | 0,26 | 0,73 | 0,94 |
| 19 | 1,36 | 13,7 a -> 2040 | 0,00 | 0,00 | 0,00 |

Selbst "fruehestens" (q10) liegt bei der Fixture-Rate seit 2023 bei 4,6 Jahren (2031). Die Formulierung "fruehestens 2029"
gilt nur unter der Konstruktionsrate, die die eigene Fixture seit 2023 um Faktor 2,7 unterschreitet. Mit stress_n_min 10
ist das "bestmoegliche Ergebnis" der Klasse P materiell weiter PARK bis in die 2030er - L-12 ist formal, nicht materiell
geheilt; das widerspricht der Absicht von DEC-107 (5). Zugleich ist der Begriff "Episode" fuer STRESS_ABS nirgends
definiert (VR-g13 definiert Episoden nur fuer STRESS_REL: "hoechstens ein Nicht-Stress-Tag Luecke"); Tage gegen Episoden
aendern N um den Faktor 30/19 = 1,6 - ein Torpfosten, wenn erst nach dem Lauf festgelegt (WD-13).

**Auflage.** (a) Zeitboden mit der Fixture-Rate seit 2023 (1,36/a) UND der Konstruktionsrate ausweisen (Tabelle oben);
"fruehestens 2029" streichen bzw. als q10 unter 3,65/a etikettieren. (b) `stress_n_min` ist eine Nutzerfrage mit
Konsequenztabelle (n_min 5 / 10 / 19 gegen 1/(N+1) = 16,7 / 9,1 / 5 % und Median-Jahr 2030 / 2034 / 2040 bei 1,36/a) - nicht
"Vorschlag 10 [U]" mit falschem Zeitboden. (c) Episodendefinition fuer STRESS_ABS (Tag oder Episode mit Lueckenregel) vor
der Registrierung per DEC fixieren (WD-13, Entscheider O/N); bis dahin ist `n_stress` UNBELEGT. (d) Die Zaehlung muss
die benannten Tage (2025-10-10, 2026-08-19) ausweisen: 2 von 5 Tagen seit 2023 sind per DEC gesetzt, nicht gemessen.
Symmetrie-Vermerk [U]: Eine Alternative (STRESS_REL-Episoden als N, W1 22 / W2 8 Tage) scheidet aus, weil VR-g13 STRESS_REL
"nie Filter oder Gate" vorschreibt; die Abhilfe liegt in B-3 (Szenario-Boden), die n_min entlasten kann.

### B-3 (Auflage, Richtung zu lax) - Stress-Bein ist Stress-Abdeckung, keine Peso-Protektion; Szenario-Boden fehlt; PZ-05 kann die Luecke nicht schliessen

**Beleg.** Kurzfassung 8: "Stress-Bein (N_stress >= 10, s_up) ist die einzige Peso-Protektion des Kapitalschritts";
3.5 Simulation: Sprungtage = Stress-Tage, N_stress = Sprungzahl im Fenster; eigene Einschraenkung in 3.5 [U] ("reale
STRESS_ABS-Tage sind marktweit definiert und existieren auch in einem Fenster ohne Strategie-Verlust"); 1.2 (c) s_up =
"groesster beobachteter Episodenverlust". K-12 Vorschlag (a) woertlich: "Kapitalregel ohne MinTRL (z. B. Erwartungsverlust
mit Stress-Szenarien)". PZ-05: Peso-Fixture, "das Gate MUSS durchfallen".

**Rechnung [R, R6, R9].** Peso-Welt der Herleitung (Rate 1/156 je Woche, -35 %, Gesamtmittel 0, n 104), jetzt mit 10
Markt-Stress-Tagen im Fenster, auf die kein Strategiesprung faellt (s_up 1 / 2 / 4 sigma_kalm): P(L* > 0) 0,1395 in allen
drei Faellen, L* median 2,45x (q90 3,32x), L_str 20 / 10 / 5 (nie bindend; L_dd 3,32 bindet), Verlust beim Sprung 86 % des
Kapitals - exakt der Wert der Herleitung "ohne Stress-Bein" (S5: 2,462x). Mit registriertem Szenario-Boden s_scen 0,35
(PZ-05-Sprung): L_str <= 0,20/0,35 = 0,571x, Sprungverlust <= 20 % per Konstruktion. PZ-05 als Rettung: der gepoolte t-Test
passiert die Peso-Fixture mit P(PASS) 0,076 / 0,146 / 0,146 / 0,041 bei n 52 / 104 / 260 / 520 Wochen (P(kein Sprung)
0,72 / 0,51 / 0,19 / 0,035; P(PASS | kein Sprung) 0,11 / 0,29 / 0,78 / 0,99): "MUSS durchfallen" ist auf 2..5-Jahres-Fenstern
eine Forderung, die der Test nicht erfuellt; die Herleitung sagt das selbst (3.5) und delegiert trotzdem.

**Auflage.** (a) `s_up := max(s_obs, s_scen)` mit registriertem Szenario-Boden `s_scen` (Design-Parameter, N): Vorschlag
Default = Strategieverlust je Einheit Notional im PZ-05-Sprung (0,35 x Sprung-Beta der Strategie, Beta UNBELEGT -> 1) und
Pflicht-Sensitivitaet gegen die beiden benannten Tage (DEC-56). Damit L_str <= stress_loss_tol / s_scen auch bei
N_stress >= n_min. (b) Etikett des Beins im Text und YAML: "Stress-Abdeckung (Ueberschreitungszeile 1/(N+1)) plus
Szenario-Boden", nicht "Peso-Protektion". (c) Kurzfassung 8 entsprechend berichtigen; 3.5 um die Zeile "mit 10
nicht-informativen Stress-Tagen: L* 2,45x, Sprungverlust 86 %" ergaenzen. (d) PZ-05-Feststellung als eigenen Merkposten an
den Orchestrator: der gepoolte Test allein kann die Peso-Fixture nicht zuverlaessig verwerfen; welches Element des Pakets
(struktureller Nulleffekt, Sprung-Screen, Stabilitaetstest) PZ-05 leisten soll, ist offen und ist eine Mess-Gate-Frage,
keine Kapitalfrage.

### B-4 (Hinweis, Artefakt; durch B-3 (a) erledigt) - s_up <= 0 gibt L* = 0, s_up -> 0+ gibt unbegrenztes L_str

**Beleg/Rechnung [R, R8].** `capital_rule`: `elif n_stress >= stress_n_min and s_up > 0: L_str = tol/s_up; else: L_str = 0`.
N_stress 12, s_up = -0,5 (Strategie gewinnt in jeder Stress-Episode): L* = 0,000. s_up = 1e-6: L* = 0,952 (L_str 2e5,
nicht bindend). Eine Strategie, die in Stresstagen gewinnt, bekommt kein Kapital; eine, die 1 bp verliert, hat kein
Stress-Bein. Der Text (1.2 (c), YAML `s_up_regel`) definiert den Fall s_up <= 0 nicht. Der Szenario-Boden aus B-3 (a)
beseitigt beides.

### B-5 (Auflage, Torpfosten-Schutz) - Welche Statistik und welcher Zeitpunkt speisen L*? Nicht festgelegt

**Beleg.** 1.5: "Eingaben zum Zeitpunkt des PASS (mu_hat, SE aus dem Lauf)"; T5: "das Gate rechnet fruehestens am
naechsten K-Blick bzw. in der naechsten Kohorte nach dem PASS"; 4.: "(i) die registrierte Kapitalfunktion L* wird mit den
Lauf-Groessen berechnet und berichtet; (ii) das Tradability-Gate ... nach VR-b15 am naechsten Blick gerechnet". Offen: ob
am Bestaetigungsblick mu_hat/SE des PASS-Blicks, die der Bestaetigungsdaten allein oder die gepoolte Statistik eingehen;
ob L* nach weiteren Blicken neu gerechnet wird (nach oben?); ob ein Bestaetigungs-FAIL L* auf 0 setzt.

**Rechnung [R, R3].** Der Unterschied ist nicht kosmetisch: unter H1 an der MDE80 liegt E[mu_hat | Stopp Blick 2] beim
1,66-fachen des wahren mu, E[mu_hat | Blick 4] beim 0,92-fachen; wer zwischen "PASS-Blick" und "gepoolt mit Bestaetigung"
nach dem Lauf waehlen darf, waehlt das 1,8-fache.

**Auflage.** Registrieren: (a) L* wird genau einmal gerechnet, am Bestaetigungsblick (VR-b15), aus der gepoolten Statistik
ueber alle Konfirmations- UND Bestaetigungsdaten, mit der Grenze dieses Blicks (B-1 (b)); (b) spaetere Neuberechnungen nur
monoton nach unten (Ratsche) oder in einer neuen Registrierung; (c) Bestaetigungs-FAIL => L* = 0 (Tradability-PARK) ohne
Rueckwirkung auf den Mess-PASS (C.2 symmetrisch, wie in 2. formuliert); (d) `s_up`, `sigma`, `n_stress` werden am selben
Blick gelesen (Lesestatus im YAML, wie T3 vorsieht).

### B-6 (Hinweis) - Notional-Einheit nicht definiert (Faktor 2 bei Long-Short)

**Beleg.** Notation: "L Notional je Einheit Kapital"; A1 ist ein Dezil-Long-Short gegen Universums-Hedge (GL-033), `prem_t`
"je Einheit Notional". Ob Notional das Brutto (Long + Short) oder ein Bein ist, aendert Kapital_min = Notional/L* um den
Faktor 2; fuer H-27 ist "1 USD je VP Vega" [U] eine Einheit, die im YAML stehen muss. **Vorschlag:** Pflichtfeld
`notional_definition` (brutto / ein Bein / Vega) im `capital_rule`-Block; A1-Beispiel mit beiden Lesarten.

### B-7 (Hinweis, Nutzerfrage) - dd_tol ist ein Budget fuer den ERWARTETEN MaxDD, nicht fuer den realisierten

**Rechnung [R, R0, R5].** Driftlos: MaxDD/(sigma sqrt T) hat Median 1,11, q90 1,92, q95 2,20 gegen Mittel 1,2533;
P(MaxDD > E[MaxDD]) = 0,42. Bei L = L_dd (A1: 0,937x, dd_tol 0,30, 1 Jahr, 52 Schritte): driftlos E[MaxDD] 0,263 (diskreter
Schritt), q90 0,434, P(MaxDD > 0,30) = 0,32, P(> 0,45) = 0,086; am wahren mu = SESOI P(> 0,30) = 0,14; am Prior theta 1
0,003. Liest der Nutzer "dd_tol 0,30" als "30 % sollen nicht ueberschritten werden", ist das Bein um q90/Mittel = 1,53
zu lax; liest er es als Erwartungswert, ist es richtig. **Vorschlag:** `dd_basis: erwartungswert | q90` als Nutzerfrage mit
beiden L_dd-Werten (A1: 0,937x bzw. 0,61x). Die Begruendung "driftloser Boden = Null-Welt-Rechnung" (1.2 (d)) ist korrekt [R].

### B-8 (Hinweis, entlastend) - Schwere Raender aendern das Ruin-Bein kaum

**Rechnung [R, R4].** Additive Ruinwahrscheinlichkeit bei kappa 0,4343 (eps 0,01), gleiche mu, sigma: Gauss 0,0088,
t(4) 0,0097, t(3) 0,0115 (MC-SE 0,0005) gegen Theorie 0,0100; kappa 0,5: 0,0171 / 0,0178 / 0,0188 gegen 0,0183. Bei
endlicher Varianz bleibt die Gauss-Formel auf 15 % genau; die Tail-Frage gehoert ins Szenario-Bein (B-3), nicht in sigma.
Das stuetzt die Entscheidung der Herleitung, Sprungrisiko nicht zu "gaussifizieren" (1.2 (c)).

### B-9 (Hinweis) - Zahlenpruefung: alles reproduziert; drei kleine Unstimmigkeiten

**Rechnung [R, R0, R1, R2].** Reproduziert (eigener Code, Seed 7071): kappa(0,01) 0,4343; eps(1/4) 3,35e-4; geometrischer
Exponent 2/kappa - 1 (hergeleitet aus Drift L mu - L^2 sigma^2/2); E[MaxDD]-Konstante per Richardson-Extrapolation
(T 250/1000/4000: 1,179/1,211/1,239 -> 1,2553 gegen sqrt(pi/2) 1,2533, Magdon-Ismail Q_p(0) = sqrt(pi/8) [sek]);
E[mu_L | PASS, Null] 0,2973 SE; MDE-Faktor 3,8101; A1: sigma_ann 0,2556, Kelly 11,75x, SR 3,00, L_dd 0,937, L_str 1,411,
SE 34,8 bp, MDE80 132,4 bp, Kapital-MDE80 168,4 / 119,7 / 88,4 bp, P(L* > 0 | 0, k) 5,8e-5, Kapital-Power am Prior 0,624,
Strenge-Quotient 1,272, Datenfaktor 1,749; H-27: SE 5,17 VP, MDE80 19,7 VP, 91 / 146 Monate, u 141 VP/Vega, Faktor 1,603;
Null-Rate z-Ebene 0,002416 (MC-SE 3,5e-5), Serienebene n 104: z-Grenze 0,00307 (analytisch t_103 0,00299), t-Grenze
0,00257, voll 0,00247. Alle Akten-Zahlen stimmen mit DEC-93 (354,4; -0,28; 147,6; 0,766), DEC-104 E3 (e) (36 bp; ~1,5 VP),
GL-034/DEC-97 (18,6; 28,2; 5,17), DEC-98 N2 (7,14; 3,2..10,5), DEC-98 N5 (2) ("vor 2029"), DEC-74 N (1) ueberein; keine
Siegeldatei noetig. Unstimmigkeiten: (a) 3.1 "Kapital-Power an der SESOI 0,0025" - mit Kostenquote q 0,95 sind es 0,0024
(S0 rechnet ohne q, S2 mit); (b) H-27-Tabelle: Spalte "P(L* > 0)" ist P(u endlich) (Stress-Bein UNBELEGT -> P(L* > 0) = 0,
wie der Text sagt) - umbenennen; (c) A1 MDE80 132,4 bp (Faktor 3,8101) gegen DEC-104 E3 (e) "~129 bp" (anderer Faktor) -
Fussnote genuegt. Das S4-Ergebnis "z-Grenze 0,00299 > alpha" ist bestaetigt und eine Mess-Gate-Eigenschaft, die DEC-107
(1)(a) ("t-artig") bereits abdeckt.

### B-10 (Hinweis, C.2) - Wand gewahrt; Kosten-Zahl gehoert nicht in die Mess-YAML

**Beleg.** PASS-Bedingung unveraendert (4.); `L* > 0 => PASS` im Code (`np.where(passed, L, 0)`) und in der Formel
(1[PASS]); OC-Zeile des Mess-Gates von der Kapitalregel unabhaengig (S1/R1 identische PASS-Raten). Kein Pfad, auf dem
Kapital > 0 ohne Mess-PASS entsteht; ein Tradability-PARK kippt den PASS nicht. Aber: 6.2 legt `kosten_k: {quelle:
constants_hash, wert: <Zahl | RAISE>}` und `oc_kapital` in die Mess-Registrierung (PZ-31). VR-a02: "keine Handelskostenzahl
als PASS-Bedingung ... die Wand ist Etikett in der Entscheidungsrelevanz-Zeile". Eine Kostenzahl in der Mess-YAML ist
keine PASS-Bedingung, aber sie verwischt die Wand, die das Muster H-04/H-04b gerade durch getrennte Eintraege zieht.
**Vorschlag:** Mess-YAML traegt nur `capital_rule: {formel, ci_basis, notional_definition, tradability_gate_ref}`; k, eps,
dd_tol, dd_basis, stress_n_min, stress_loss_tol, s_scen, oc_kapital stehen im H-nnb-Eintrag. Zusatz [R, R1]: die
relevante Null fuer "Kapital > 0 zu Unrecht" ist mu <= k, nicht mu <= 0; P(L* > 0 | mu = k) = 0,00239 (analytisch
0,95 x 0,0025) - die Herleitung darf diese staerkere Aussage fuehren.

### B-11 (Auflage) - Nutzerfragen fehlen als Fragen

**Beleg.** 6.2 etikettiert eps, dd_tol, stress_n_min, stress_loss_tol als "Risikopraeferenz, N"; 6.3 (b) nennt sie
"Design-Parameter"; weder die Herleitung noch der DEC-Nachtrags-Wortlaut stellt eine Frage mit Default und Konsequenz.
DEC-107 (6)(d): Vorlage an den Nutzer bei jeder Lockerung und jedem Geldeinsatz.

**Auflage.** Vorlage-Tabelle (Frage, Default, Alternative, Konsequenz am A1-Beispiel):
(1) eps 0,01 (kappa 0,434) gegen 0,001 (0,290) / 0,05 (0,668): L_ruin skaliert mit 0,67 / 1,54 [R, S0];
(2) dd_tol 0,30 und dd_basis Erwartungswert gegen q90: L_dd 0,937x gegen 0,61x [R, R5]; T_dd 1 gegen 3 Jahre: 0,937 gegen 0,541x [R, S2];
(3) stress_n_min 5 / 10 / 19: Ueberschreitung 16,7 / 9,1 / 5 %, Median-Jahr bei Fixture-Rate 2030 / 2034 / 2040 [R, R7];
(4) stress_loss_tol 0,20 und s_scen (B-3): L_str <= 0,571x bei s_scen 0,35;
(5) Kapitalbasis C und Steuerregime (PRD 8.2) - ohne C ist L* dimensionslos (T4 korrekt), aber die Vorlage muss die Frage
    als offen fuehren, nicht nur als Zeile;
(6) notional_definition (B-6); (7) ci_basis Blickgrenze gegen 2,8070 (B-1); (8) Kostenbasis k Taker gegen Maker
    (VR-c01-Gabelung; Maker im Stress RAISE, VR-g14) - bei Maker-k sinkt die Kapital-MDE80, Etikett Pflicht.
Stress-Episodendefinition (B-2 (c)) ist O/DEC, keine Nutzerfrage.

### B-12 (Hinweis) - Etikett und Strenge-Quotient: korrekt, drei Ergaenzungen

**Beleg/Rechnung.** Lockerung gegenueber PRD 3.6 (2) / VR-f13 (2): ja; Verschaerfung (Gate, UNBELEGT = 0): ja;
Mess-Gate-Quotient 1,00 [R: alpha, SE, MDE80 unberuehrt]; Kapitalpfad 1 + k/MDE80 = 1,272 (A1, 104 Wochen), 2,0 an der
SESOI [R, R0]; Datenfaktor (mu/(mu - k))^2 = 1,749 (A1 Prior) / 1,603 (H-27) [R]. Entscheider N, Geltung ab K1, Rueckbau
`capital_rule: null` - vollstaendig. Ergaenzen: (a) auch VR-f13 Auflage (1) (PASS-Text "PARK, nicht WEITER") wird
geaendert - im Etikett nennen; (b) der "Strenge-Quotient Kapitalpfad" ist keine Groesse im Sinn von E8 (b) (MDE80 neu/alt
desselben Gates), sondern eine neue Kennzahl - als "Kapital-MDE80 / Mess-MDE80" etikettieren, damit die 1,3-Regel nicht
faelschlich auf das Mess-Gate bezogen wird; (c) der Zeitboden im Etikett muss die Fixture-Rate tragen (B-2): ">= 2,7 Jahre"
wird "Median 7,1 Jahre bei 1,36/a, 2,6 Jahre bei 3,65/a". Nichts im Etikett ist zu lax; zu streng ist nur der Zeitboden
(B-2), und der ist Parameterwahl, nicht Formel.

### B-13 (Hinweis, bestaetigend) - Unabhaengigkeit von Stabilitaetstest und gepooltem Test

Unter iid-Gauss-Null ist Cov(mean_J - mean_A, gepooltes Mittel) = (n_J sigma^2/n_J - n_A sigma^2/n_A)/n = 0, also
Unabhaengigkeit [R, Umformung]; der Produktansatz 0,95 x 0,0025 = 0,002375 der Herleitung ist exakt, nicht nur
Naeherung; MC bestaetigt 0,002406 (Herleitung) / 0,002416 (Review, R1). Auf der Serienebene mit Welch-df 0,00247 (R2).

---

## 2. Antworten auf die sieben Pruefpunkte des Auftrags

| Nr. | Frage | Antwort |
|---|---|---|
| 1 | Kernformel korrekt? | Ja [R, R0]: Ruin exp(-2 mu u/sigma^2), u(eps), L_ruin, Kelly-Identitaet, geometrisches Gesetz, MaxDD-Konstante, E[mu_L \| PASS]; A1/H-27-Arithmetik reproduziert. Kein Rechenfehler. Fehlende Faelle: Blickabhaengigkeit (B-1), s_up <= 0 (B-4). |
| 2 | alpha geerbt? Pfad ohne PASS? Torpfosten? | Geerbt: ja in allen Varianten (0,0024 / 0,00247 / OBF 0,0025; mit k praktisch 0) [R, R1-R3]. Kein Pfad ohne PASS. Torpfosten-Risiken: Statistik/Zeitpunkt von L* (B-5), Episodendefinition (B-2 (c)), s_up-Regel (B-3/B-4). Nach den Auflagen geschlossen. |
| 3 | C.2 verletzt? Gate getrennt? | Nein; PASS-Bedingung unveraendert, `L* > 0 => PASS`. Gate getrennt (T1..T6, Muster H-04b). Kosten-Zahl aus der Mess-YAML in den H-nnb-Eintrag verschieben (B-10). |
| 4 | A1/H-27 konsistent mit offenen Zahlen? | Ja, alle Eingaben belegt (B-9); keine Siegeldatei. Drei Beschriftungsfehler (B-9 a-c). |
| 5 | Peso-Analyse richtig? Stress-Bein reicht? | Simulation richtig, Lesart nicht: das Bein schuetzt nur, wenn Sprungtage = Stress-Tage mit Strategieverlust; sonst 2,45x und 86 % Verlust [R, R6]. Reicht nicht; Szenario-Boden noetig (B-3). PZ-05 ist keine Rettung [R, R9]. |
| 6 | Etikett korrekt/vollstaendig? Zu streng/zu lax? | Korrekt; Ergaenzungen B-12. Zu streng: stress_n_min 10 bei Fixture-Rate = PARK bis ~2033 (B-2). Zu lax: fester z_ci bei fruehem Stopp (B-1), kein Szenario-Boden (B-3), dd_tol als Erwartungswert, falls anders gemeint (B-7). |
| 7 | Nutzerfragen fehlen? | Ja: eps, dd_tol/dd_basis/T_dd, stress_n_min, stress_loss_tol/s_scen, Kapitalbasis, Notional, ci_basis, Kostenbasis - als Fragetabelle mit Konsequenzen (B-11). |

## 3. Was nach den Auflagen gilt

Die Regel ist mit den Auflagen B-1, B-2, B-3, B-5, B-11 **vorlagefaehig** (eine Fassung, kein Patt). Keine Auflage
aendert die Formelfamilie; alle sind Praezisierungen (Blickgrenze, Szenario-Boden, Lesezeitpunkt, Episodenbegriff,
Fragetabelle) oder Berichtigungen von Bezifferungen (Zeitboden). Der Review bestaetigt die Kernaussage der Herleitung:
P(Kapital > 0 | Null) <= alpha ist eine Eigenschaft der Konstruktion `1[PASS] x f(mu_L)` und bleibt unter jeder geprueften
Abweichung erhalten; was sich aendert, ist die Groesse eines zu Unrecht oder zu frueh empfohlenen Kapitals - und die ist
ohne B-1 und B-3 nach oben offen (3,4-fach am Blick 2; 86 % Sprungverlust).

**Was nicht folgt:** kein Verdikt, keine Registrierung, keine Zahl einer Hypothese, kein Kapital, kein Code im Repo; keine
Aenderung an GL-033/GL-034; die Feststellung zu PZ-05 (B-3 (d)) ist ein Merkposten fuer das Mess-Gate, nicht Teil dieser
Vorlage.
