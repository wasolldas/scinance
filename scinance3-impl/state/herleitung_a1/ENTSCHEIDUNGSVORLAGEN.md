# Entscheidungsvorlagen A1 (H-31) - Funding-Long-Bein D1 gegen Universums-Hedge

> **ORCHESTRATOR-VERMERK 2026-10-13 (DEC-93, GL-033):** Ersetzt durch die Feststellung des Reviews (`REVIEW_A1.md`):
> A1 ist unter den geltenden Beschluessen (DEC-67 E4, fuer A1 bestaetigt in DEC-70 E1: W_eff = 0,41 W) vor der
> Registrierung GL-012 (176,5 > 147,6 bp schon bei theta = 1) und zusaetzlich theta-UNBELEGT. Die Aussage "Stopp-Regel
> greift nicht" unten ist damit hinfaellig; Stufe 2 ist Akte ohne Rechtswirkung. Kein Verdikt ueber den Funding-Carry.

> ENTWURF der Herleitung, 2026-10-13. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren darf
> nur der Orchestrator. Keine A1-Outcome-Groesse ab 2024-07-01, keine Siegeldatei geoeffnet.
> Zahlen und Kuerzel wie in `FEASIBILITY.md` (`[fj]`, `[fj:A]`, `[fj:B]`, `[S:...]`, `[abg.]`).
>
> **Bedingtheit.** Stufe 2 existiert, weil die Stopp-Regel des Auftrags in Konfiguration A mit gemessener SE nicht
> greift (FEASIBILITY 8). Die Vorlagen EV-1 bis EV-6 entscheiden, ob A1 ueberhaupt registrierbar ist; die strenge
> Lesart von EV-1 oder EV-2 macht A1 bei jedem theta <= 1 zum GL-012-Fall, EV-3 in der A3-Lesart (ohne DEC-52-Zweig)
> ebenso, EV-4 (b) unterhalb theta 0,969, EV-5 (b) ganz; EV-6 blockiert ohne Quelle.
> EV-7 bis EV-13 betreffen das Design und werden nur gebraucht, wenn EV-1 bis EV-6 A1 offen lassen.
>
> **Reihenfolge-Empfehlung:** EV-2, EV-4 und die Luecken-Regel aus EV-3 betreffen Programm-Regeln und muessen nach
> dem Sequenz-Zwang (DEC-52) programmweit und VOR einer A1-Registrierung beschlossen werden, nie kandidatenspezifisch.

---

## Teil 1 - Feasibility-entscheidende Vorlagen

### EV-1. 1h-Symbol-Wochen: primaer eingeschlossen (Konfiguration A) oder ausgeschlossen (B)?

**Frage.** Laeuft das registrierte Design auf allen Intervallklassen (Schluessel intervall-normiert) oder schliesst es
Symbol-Wochen mit 1h-Funding look-ahead-frei aus?

**Fundstellen.**
- PRD 5.1 (b): "Der Zins-Term fuer 1h-Symbole ist UNBELEGT - V-1; **solange er offen ist**, laeuft A1 nur auf der
  homogenen 8h-Klasse".
- DEC-58 E3: "Ausschluss der 1h-Klasse nur als look-ahead-freie Symbol-Wochen-Regel; ... Pflicht-Sensitivitaet mit
  intervall-normiert eingeschlossenen 1h-Symbolen (Bericht, kein zweites Gate); schriftliche Feststellung der
  W1/W2-Inhomogenitaet".
- DEC-59: "Der A1-'1h-Ausschluss' ist gegenstandslos; funding_n-Normierung ist Kern des Sortierschluessels" (damals
  1 Symbol mit 60 min).
- DEC-84: I skaliert exakt mit dem Intervall (1h-Totzone bei 0,00125 %, 29,9 % der Tage); "Die tagesweise Normierung
  `funding_i_per_payment` ist die richtige Konstruktion"; W2 ueberwiegend im Auto-Switch-Regime.
- Auftrag Stufe 1: "Konstruktion fest (DEC-70) ... I je Zahlung skaliert nach Intervallklasse" (ohne Ausschluss);
  Auftrag Stufe 2: "1h-Ausschluss als look-ahead-freie Symbol-Wochen-Regel plus Pflicht-Sensitivitaet (DEC-58 E3)".

**Befund** [fj:A], [fj:B]: In W2 sind 20,5 % der D1-Symbol-Wochen modal 1h (W1 1,8 %); ohne sie faellt der W2-Spread von
339,6 auf 197,6 bp/Woche. Persistenz innerhalb der Formationswoche: 1h-Mitglieder 0,493, uebrige 0,650 (W2).
Konfiguration B ist bei jedem theta <= 1 GL-012 (theta_min 1,161 bei c = 1; 1,041 bei c = MBB).

**Optionen.**
- (A) Primaer alle Klassen (intervall-normiert), Pflicht-Sensitivitaet = Konfiguration B (Bericht, kein Gate).
- (B) Primaer Konfiguration B (Ausschlussregel: Formationswoche mit mindestens einem Tag `funding_n = 24`),
  Pflicht-Sensitivitaet = A (Bericht). Folge: GL-012 vor dem Design.

**Herleitung.** Der Ausschluss in PRD 5.1 (b) war an das offene I_1h gebunden; DEC-84 hat I_1h empirisch belegt. DEC-58
E3 regelt die FORM eines Ausschlusses ("nur als ... Symbol-Wochen-Regel") und verlangt die Sensitivitaet MIT 1h; es
fuehrt keinen neuen Ausschlussgrund ein. Die Konstruktion des Auftrags (Stufe 1) und DEC-84 wurden vor jeder
A1-Feasibility-Zahl festgelegt und schliessen 1h ein. Gegenargument (Gewicht hoch): Der Auto-Switch macht die
1h-Klasse zu einem Zustand, der durch Floor-Treffer ausgeloest wird; W2 wird von kurzen Episoden (Median 8 Tage, DEC-84)
gepraegt; der woertliche Satzbau von DEC-58 E3 (Ausschluss primaer, Einschluss als Sensitivitaet) und der
Stufe-2-Auftrag sprechen fuer (B).

**Empfehlung.** (A), weil sie die vor den Zahlen fixierte Konstruktion ist (ein Wechsel nach (B) jetzt waere eine
Aenderung NACH Kenntnis der formationsseitigen Feasibility, in der strengen Richtung) und weil der dokumentierte
Ausschlussgrund entfallen ist. Die Rollenumkehr gegenueber dem Satzbau von DEC-58 E3 braucht eine eigene DEC mit
Offenlegung: "Konfiguration nach formationsseitiger Feasibility bestaetigt, nicht gewechselt; B waere GL-012".
Entscheidet der Orchestrator (B), endet A1 hier als GL-012 vor dem Design (kein Verdikt).

### EV-2. Autokorrelations-Korrektur der SE: gemessen oder DEC-67 E4 (W_eff = 0,41 W)?

**Fundstellen.** DEC-67 E4 ("DEC-51-Power fuer Funding-basierte Hypothesen rechnet mit W_eff = 0,41 W", hergeleitet als
AR(1)-Naeherung (1-0,42)/(1+0,42) aus der Autokorrelation des Funding-Wochen-Schluessels, WELLE1_BEFUND_TEIL4);
`stats.sd_null_w_eff_adjusted` ("reported ALONGSIDE ... never replacing it"); DEC-92 Lehre ("Power-/MDE-Zeilen ... mit
genau der SE-Regel des registrierten Tests"); PRD 5.1 Power-Zeile ("korrigiert um die Autokorrelation ueber den
stationaeren Bootstrap").

**Befund** [fj:A nuisance.bases.K_ge_117]: Gesamtrendite rho_1 = -0,250, c (trunk. 4) 0,598, Bartlett 0,717, MBB 0,756;
Funding-Bein allein c 2,0..3,2 (passt zu DEC-67), traegt aber 4 % der Varianz. Unter DEC-67 E4: GL-012 bei theta = 1
(176,5 > 147,6 bp).

**Optionen.** (a) c = max(1, gemessen) = 1 (keine Gutschrift fuer negative Autokorrelation); (b) c = gemessenes MBB-
Verhaeltnis 0,756; (c) DEC-67 E4 woertlich (c = 2,439).

**Empfehlung.** (a). DEC-67 E4 setzte eine Ersatzgroesse (Persistenz des Schluessels) fuer die damals unbekannte
Persistenz der getesteten Statistik; diese ist jetzt gemessen und widerlegt den Ersatz (Abstand ~4,8 SE [abg.:
(2,44-0,60)/0,38, SE(c) ~ 2*sqrt(4)*0,094]). Eine neue DEC begrenzt DEC-67 E4 auf Statistiken, deren Autokorrelation
die des Schluessels ist (IC des Schluessels, Funding-Bein allein), und legt fuer A1 die SE-Regel aus EV-10 fest.
(b) wird nicht empfohlen: rho_1 = -0,25 ist nur ~2,7 SE von 0 entfernt; eine Gutschrift waere nicht robust.

### EV-3. DEC-51 (2) je Fenster neben der PRD-5.1-Zuordnungsregel; die Luecke 0,60 <= P < 0,80

**Fundstellen.** DEC-51 (2) (Power-Ziel 0,80; "liegt die A-priori-Erwartung darunter, ist die Registrierung ein
GL-012-Fall ... oder braucht ein anderes Design"); PRD 5.1 Zuordnungsregel (P >= 0,60 -> C.10 hart, < 0,60 -> DEC-52,
GL-012 nur ueber `3,168*SE_gepoolt > prem`); DEC-52 (i) (nur bei P < 0,60 anwendbar); DEC-87 (F) und GL-032 (A3: MDE80 >
Prior in einem Fenster -> GL-012).

**Befund** [fj:A power.grid]: Bei theta = 1 ist P_W1 = 0,619, P_W2 = 0,990 -> C.10 hart; gemeinsame Power 0,612;
MDE80_W1 = 128,6 bp > prem_W1 = 100,7 bp. W1 erreicht Power 0,80 erst bei theta = 1,277 (> 1, also nie). Fuer
0,766 <= theta < 0,975 ergibt die PRD-Regel DEC-52 (P_W1 < 0,60), fuer theta >= 0,975 C.10 mit P_W1 0,60..0,62.

**Die Luecke.** Eine Regel "MDE80 > Prior -> GL-012" (DEC-87 (F)) zusammen mit DEC-52 (i) ist inkoharent: Ein Fenster mit
P = 0,59 bekommt den DEC-52-Zweig, eines mit P = 0,62 waere GL-012 - ein groesserer Prior wuerde A1 toeten.

**Optionen.** (a) PRD 5.1 woertlich: GL-012 nur ueber die gepoolte Pruefung (die genau DEC-51 (2) fuer den gepoolten
Test bei alpha 0,01 ist: 3,1680 = 2,3263 + 0,8416); C.10-Fenster mit 0,60 <= P < 0,80 bleiben C.10 mit Etikett
"W1 unterpowert". (b) Programmweite DEC: 0,60 <= P < 0,80 -> DEC-52-Zweig (Aenderung von DEC-52 (i), nie
kandidatenspezifisch, Retro-Check). (c) DEC-87-(F)-Analogie: MDE80 > Prior in einem Fenster -> GL-012.

**Empfehlung.** (a) fuer A1 (vorab fixierte, kandidatenspezifische Regel des PRD), mit Pflicht-Etikett und der
Entscheidungsrelevanz-Einschraenkung aus EV-6; die Luecke wird programmweit per DEC geklaert (Option (b) oder (c)),
bevor A1 registriert wird. Unter (c) mit gebautem und genutztem DEC-52-Zweig ist A1 GL-012 nur fuer theta >= 0,975
(inkoharent: der groessere Prior toetet); unter (c) wie in A3 ohne DEC-52-Zweig bei jedem theta <= 1.

### EV-4. Schwelle: kritischer Wert (1,6449 * SE) oder detektierbarer Effekt (2,4865 * SE)?

**Fundstellen.** DEC-51 (1) (Mess-Gates "alpha = 0,05 einseitig"); PRD 3.5 ("vor DEC-52 lag die gemeinsame Rate bei
0,05^2 = 0,25 %" - also alpha 0,05 je Fenster); PRD 5.1 `P_fenster = Phi(prem/(sigma/sqrt(52)) - 1,6449)` und
GL-012 ueber `3,1680 = 2,3263 + 0,8416` (= MDE80 des gepoolten Tests bei alpha 0,01); dagegen PRD 5.1 Schwelle
`mean_min = max(obere CI-Grenze des Nulleffekts; z * sigma_LS/sqrt(W))` "mit dem z des registrierten Fenster-Regimes"
(z = 2,4865 bzw. 3,1680 - das sind MDE-Faktoren, keine kritischen Werte); A3-Praxis `IC_min = 2,4865 * ...` mit
Groesse 0,0064 je Fenster (DEC-74 (d)); Gate-Audit A3 1.3 (Power eines solchen Gates `Phi(Prior/SE - 2,4865)`).

**Befund.** PRD 5.1 ist in sich widerspruechlich. Ist die Schwelle 2,4865 * SE, dann ist die Power des Gates
`Phi(prem/SE - 2,4865)` und nicht `P_fenster`; bei theta = 1: W1 0,295, W2 0,929, gemeinsam 0,274; gepoolt mit
Schwelle 3,168 * SE 0,834; MDE80 172,1 / 163,6 bp [fj:A power.grid."c1_binding|theta=1.0"]. Genau dieser Fehlertyp
(Power-Formel passt nicht zur registrierten Pruefung) war die Ursache von DEC-91.

**Optionen.**
- (a) Schwelle = kritischer Wert zu alpha nach DEC-51/52: C.10 je Fenster `alpha_hat >= 1,6449 * SE_W` UND
  MBB-Untergrenze (95 %, einseitig) > 0; DEC-52 gepoolt `>= 2,3263 * SE_gepoolt`, Screens je Fenster `> 0` und
  `>= 0,5 * 2,3263 * SE_gepoolt`. Dann sind `P_fenster` und die GL-012-Pruefung des PRD genau die Power bzw. die
  MDE80-Bedingung dieses Tests (in sich konsistent). Die PRD-Zeile "z des Regimes" wird als Verwechslung von
  kritischem Wert und MDE festgestellt (Etikett, DEC). Werte bei theta = 1: C.10 gemeinsam 0,612; DEC-52 (falls
  zugeordnet) ~0,84 (gepoolt 0,965, Screens 0,874 / 0,999).
- (b) Schwelle = 2,4865 * SE bzw. 3,168 * SE_gepoolt (PRD-Schwellentext, A3-Praxis, effektives alpha 0,0064 je
  Fenster). Dann MUSS die Zuordnung mit der Gate-Power gerechnet werden: bei theta = 1 W1 0,295 < 0,60 -> DEC-52;
  gepoolte Power 0,834, mit Screens ~0,77; Power 0,80 des gepoolten Gates erst ab theta = 0,969 [abg.: 4,01 * 35,67 /
  147,6]; die PRD-GL-012-Pruefung ist dann nur noch die 50-%-Power-Grenze.

**Empfehlung.** (a): sie folgt der bindenden Power-Konvention DEC-51 (1) und der PRD-eigenen Power- und
GL-012-Formel; (b) setzt stillschweigend ein strengeres alpha als registriert. Weil (a) gegenueber dem Wortlaut der
Schwellenzeile eine niedrigere Zahl ergibt, braucht sie eine programmweite DEC vor der Registrierung (sonst
kandidatenspezifisch). Entscheidet der Orchestrator (b), ist A1 bei jedem theta < 0,969 unter DEC-51 (2) unterpowert
und praktisch nicht registrierbar.

### EV-5. Kill (4): WP-7-Schaetzer oder Buehlmann-Straub-Ersatz?

**Fundstellen.** PRD 5.1 Kill (4) (Autokorrelation des Sortierschluessels ueber eine Woche < 0,30, gemessen wie WP-7;
Design-Parameter, Konsequenz vorab fixiert); PRD 11.4 / DEC-58 E1 (e) ("der Kill-4-Parameter 0,30 wird durch
`k <= 2,333*w` (Buehlmann-Straub) ersetzt"); S5 X-AKT-4 (Aequivalenz nur unter (i) konstantem wahrem Mittel und (ii)
unkorrelierten Messfehlern); REVIEW_S1_S5 X-AKT-4 (Schaetzer vorher festlegen).

**Befund** [fj kill4_ci_formationsseitig], [fj:A]: WP-7-Schaetzer W1 0,403, W2 0,303 (90-%-KI 0,281..0,329; min 8
Wochen 0,2997). Buehlmann-Straub: k = 8,98 / 11,70 Wochen > 2,333 -> verletzt; Nuisance-Basis k = 24,3 (z = 0,040),
dort aber gemessene Persistenz 0,445..0,590 - Bedingung (i) messbar verletzt, z unterschaetzt die Persistenz um Faktor
> 10.

**Optionen.** (a) WP-7-Schaetzer (registrierter Messweg, min 12 Wochen) - nicht ausgeloest, W2 an der Grenze. (b)
Buehlmann-Straub woertlich - ausgeloest, Registrierung unterbleibt. (c) Buehlmann-Straub mit geprueften
Gueltigkeitsbedingungen - nicht anwendbar, weil (i) verletzt.

**Empfehlung.** (a) mit Etikett "W2 auf der Kill-(4)-Grenze (0,303; KI reicht unter 0,30)" und (c) als dokumentierte
Begruendung, warum der Ersatz hier nicht greift. Eine DEC haelt fest, dass die Aequivalenz aus PRD 11.4 nur bei
erfuellten Bedingungen (i)/(ii) gilt. Unter (b) endet A1 vor dem Design.

### EV-6. Prior theta - Quelle oder Blockade

**Befund.** theta ist UNBELEGT (FEASIBILITY 5). Notwendig (Konfiguration A, c = 1): theta >= 0,766 (GL-012-frei);
theta >= 0,975 fuer P_W1 >= 0,60; Power 0,80 in W1 unerreichbar. Bei theta = 0,5 ist A1 GL-012 (73,8 < 113,0 bp).

**Folgen.** (1) Ohne Quelle fuer theta >= 0,77 ist die Power-Zeile nicht belegbar (Regel 3: UNBELEGT blockiert) - keine
Registrierung. (2) Registriert man dennoch gegen die Obergrenze theta = 1, ist ein DROP uninformativ fuer jedes
realistische theta < ~0,9 (C.13); die DROP-Zeile "Klasse P auf Perp-Funding erschoepft" waere dann falsch und muesste
auf "theta nahe 1 ausgeschlossen" eingeschraenkt werden. (3) theta ist aus den Daten nur ueber das Rendite-Mittel
bestimmbar - auf der Nuisance-Periode verboten (Regel 1), auf W1/W2 das Outcome selbst.

**Empfehlung.** Keine Registrierung ohne belegte Untergrenze theta >= 0,77 [sek oder primaer]. Eine Literaturrecherche
(Querschnitts-Funding-Carry auf Perps, Anteil nicht kompensierter Funding-Differenz) ist der naechste Schritt; ein
Fundstueck traegt nur, wenn es den Querschnitt (nicht die Zeitreihen-Basis) und eine Wochenhaltedauer betrifft.

---

## Teil 2 - Design-Vorlagen (nur bei offener Feasibility)

### EV-7. Selektions-K: 1 (Wochen-SUMME) oder 3 (Lookbacks 3/5/7 Tage, PRD 5.1)?

**Fundstellen.** PRD 5.1 Selektions-K = 3 (Lookback 3/5/7 Tage), analytische Decke 0,60 (SR-Einheiten, T = 2 a);
DEC-67 E2 (Schluessel = Wochen-SUMME (F - I), "vorab, vor jeder Null-Messung des Schluessels"); DEC-70 (Schluessel
bleibt); DEC-58 E2 (eigene Hypothese mit eigenem K fuer jede neue Variante).

**Herleitung.** DEC-67 E2 hat den Schluessel nach PRD v2 festgelegt; 3- und 5-Tages-Varianten waeren neue Schluessel,
fuer die weder Degeneration noch Autokorrelation noch Spread gemessen sind. K = 3 verbraucht Deflation (BH ueber 3,
Decke ~0,85 * SE in Mittelwert-Einheiten [abg.: (1-g)*Phi^-1(2/3) + g*Phi^-1(1-1/(3e)) = 0,4228*0,4307 +
0,5772*1,1614 = 0,852, unabhaengige Varianten; korrelierte Lookbacks liegen darunter]) ohne Power zu gewinnen.

**Empfehlung.** K = 1 (Wochen-SUMME, ISO-Woche = 7-Tage-Lookback). Familie F-CARRY1 mit einem Mitglied (BH trivial),
Ueber-Familie F-PREM abhaengigkeitsrobust (BY). Die Decke wird trotzdem am Null-Fixture gemessen (T1) und berichtet.
Abweichung von PRD 5.1 (K = 3) als Etikett.

### EV-8. Faktorset des Residual-Alpha (PRD 5.1 (d), Gate (3))

**Befund** [fj:A nuisance.bases.K_ge_117.a3_factor_regression]: R^2 der Gesamtrendite auf (mom1, rev_gap) 0,063, auf
(mom1, mom2, mom4, rev_gap) 0,066, mit Markt 0,068; die Momentum-1-Woche-Ladung ist positiv (0,13..0,15).

**Empfehlung.** Faktoren MKT_EW (Beta-Fehlanpassung, A3-Lehre: delta W1 -0,13), MOM1 und REV_GAP (die zwei in DEC-88
gerechneten A3-Varianten), je als Dezil-L/S-Haltewochenrendite im selben U_t; 3 Regressoren, SE-Aufschlag
sqrt(W/(W-4)). Etikett C.17: "Der A1-Lauf legt MOM1/REV_GAP-Faktorrenditen auf W1/W2 offen; jede kuenftige A3-Fassung
auf diesen Fenstern fuehrt sie als gesehen."

### EV-9. Fenster-Regime und Bau des DEC-52-Zweigs

Die Zuordnung erfolgt mechanisch bei der Registrierung mit dem belegten theta (EV-6) und der Power des Gates nach
EV-4. Mit EV-4 (a): theta in [0,766; 0,975) -> DEC-52, theta >= 0,975 -> C.10 hart (W1 0,60..0,62, EV-3); mit EV-4 (b)
fuer jedes zulaessige theta DEC-52. Der DEC-52-Zweig muss deshalb in jedem Fall gebaut sein. Zu bauen und zu
entscheiden:
1. (ii) Screen je Fenster: Residual-Alpha > 0 UND >= 0,5 * registrierte Schwelle. **Magnituden-Band [0,5x; 2,0x]**
   (PRD 3.5): Bedeutung der Obergrenze 2,0x ist im PRD nicht erklaert - Optionen: (a) Bericht/Etikett "W1/W2-Divergenz"
   bei Ueberschreitung, (b) KEIN PASS bei Ueberschreitung. Empfehlung: (a) mit Begruendung, dass ein Gate, das zu
   grosse Effekte toetet, eine Mess-Gate-Regel mit Richtungsfehler waere (vgl. Tail-Ratio, PRD 3.6) - braucht eine
   programmweite DEC, weil es DEC-52 auslegt.
2. (iii) "fenster-geclusterter stationaerer Bootstrap": mit zwei Fenstern nicht als Cluster-Resampling ausfuehrbar.
   Empfehlung: stratifiziert - stationaerer Bootstrap (mittlere Blocklaenge 4, wie A3 `rules.block_len`) getrennt je
   Fenster, gepoolter Schaetzer = Mittel der Fensterschaetzer, 1.000 Replikate, Seed 53; Fenster nie gemischt.
3. (iv) gepooltes alpha 0,01; Schwelle nach EV-4 (Empfehlung (a): 2,3263 * SE_gepoolt).
4. DEC-53: gepoolte Replikate bzw. Seed + Generator-Fingerprint; T4 auf konserviertem Payload beider Regime.

### EV-10. SE-Regel des registrierten Tests

**Empfehlung.** `SE_W = max(SD(x_W)/sqrt(W_j), SE_MBB(x_W))` mit MBB Block 4, 1.000 Replikate, Seed 53 (keine Gutschrift
fuer negative Autokorrelation, Gegenstueck zu A3 `max(Boden, SD(IC_t))`); Residual-Alpha:
`SE_alpha = max(OLS-SE mit W_j-4 Freiheitsgraden, SE_MBB(alpha))`, MBB ueber Wochenzeilen (x, Faktoren) mit
Neuschaetzung je Replikat. Die Power-Zeile rechnet mit genau dieser Regel und der bindenden SD-Projektion
(FEASIBILITY 4).

### EV-11. Funding-Buchhaltung (Details)

1. **Intervall-Normierung:** `I_Zahlung = 0,01 % * 3/funding_n` ergibt fuer jeden vollstaendigen Tag 0,03 %/Tag in jeder
   Klasse (FEASIBILITY 1.2). Umschalt-Tage (funding_n nicht in {3,6,12,24}): 0,37 % (W1) / 0,83 % (W2) der D1-Funding-
   Tage; Fehler je Umschalttag hoechstens 0,875 bp (8h -> 1h um 16:00: 3*0,01 % + 7*0,00125 % = 0,03875 % statt
   0,03 %) [abg.; S:a1_bookkeeping.py]. Empfehlung: belassen, Etikett.
2. **Teiltage** (Listung/Delisting/Luecke, weniger Zahlungen als die Klasse vorsieht): I wird ueberschaetzt (1 Zahlung
   einer 8h-Klasse traegt 0,03 % statt 0,01 %). In W1/W2 haben D1-Wochen keine Teiltage (0 / 0); Listungstage liegen
   durch die 8-Wochen-PIT-Regel ausserhalb. Empfehlung: laut zaehlen und berichten (loud count), kein Fix.
3. **I = 0 fuer Sonderpaare:** USDCUSDT, ETHBTCUSDT (DEC-82, Hilfe-Center [Snippet], empirisch: 790/1.462 bzw. 519/752
   Tage exakt 0). Dazu TradFi-Perps (AMZN, AAPL, XAU, SPY, ...) mit ueberwiegend exakt-0-Funding - Status UNBELEGT.
   Empfehlung: explizite I=0-Liste fuer die zwei belegten Paare (Schluessel = Summe F) und eine look-ahead-freie Regel
   "Symbol-Woche aus U_t, wenn in den 8 Wochen bis t >= 50 % der Funding-Tage exakt 0 sind" (TradFi-Schliessung),
   Sensitivitaet ohne Regel. Materialitaet: D1-Symbol-Wochen der Paare 16 / 9 von 2.196 / 2.875.
4. **1h:** nach EV-1; die Ausschlussregel (Formationswoche mit einem `funding_n = 24`-Tag) ist look-ahead-frei.
5. **Haltewochen-Funding:** Summe der Tages-`funding_sum` der ISO-Woche t+1 (Abrechnungen Mo 00:00 .. So, Position ab
   Wochenschluss t gehalten; Konvention: die Mo-00:00-Abrechnung gehoert zur Haltewoche). Etikett.
6. **Delisting:** letzter gehandelter Kurs (DEC-72-Union-Konvention, keine Imputation); ein in der Haltewoche
   delistetes Mitglied traegt seine reale Rendite bis zum letzten Kurs und sein Funding bis dahin. Formation nur aus
   Symbolen, die am Schluss der Woche t handelbar sind.
7. **Survivorship-Etikett:** Union-Panel mit 261 delisteten Symbolen; 7 delistete ohne oeffentliche Kline-Historie
   fehlen (DEC-72).

### EV-12. Positivkontrolle in Produktionskonfiguration - vorab fixierte Bestehensregel (A3-Lehre)

**Konstruktion.** Echte W1/W2-Wochenraster, echte PIT-Alive-Masken, echte Formationsschluessel und D1/U_t
(formationsseitig, erlaubt); synthetische Haltewochen-Renditen je Symbol aus einer kalibrierten Welt:
`R = beta_{i,t} * f + u_{D1} + e_i` mit PIT-Betas des Fensters, Faktor-SD des Fensters, gemeinsamem D1-Schock (kalibriert
auf kappa = 1,877) und Residualvarianzen der Mitglieder; synthetisches Haltewochen-Funding
`F_sum = 0,21 % + phi * (key_i - mean_U key) + Rauschen` (SD und Autokorrelation des Funding-Beins aus der Nuisance);
Kompensation `E[Preisbein] = -(1 - theta_pc) * E[Funding-Vorteil]`. Volle Gate-Kette (SE-Regel EV-10, Regime, Residual-
Alpha mit synthetischen Faktoren, Kills), R = 500 Replikate je theta_pc, Seeds 53..552.

**Bestehensregel (vorab, alle vier noetig):**
1. Kalibrierung: SD der synthetischen A1-Serie je Fenster innerhalb +-10 % der bindenden SD (373 / 354 bp); liegt sie
   ueber +10 %, ist die Power-Zeile zu optimistisch -> NICHT BESTANDEN.
2. theta_pc = 0 (exakte Kompensation): PASS-Rate <= nominales gemeinsames alpha + 3 MC-SE.
3. theta_pc = registriertes theta: PASS-Rate >= registrierte Power - 3 MC-SE (MC-SE = sqrt(P(1-P)/500)).
4. Je Fenster: Rate der Fensterbedingung innerhalb +-3 MC-SE der Fenster-Power der Power-Zeile.
Andere Seeds ergeben nie BESTANDEN. NICHT BESTANDEN -> kein Lauf, Ursachenanalyse, neue DEC.

### EV-13. Peso-Fixture - Operationalisierung fuer A1

PRD-Parameter (Rate 1/3 Jahre, Sprung -35 % auf das D1-Bein, Nullpraemie): die Sprung-Kompensation ergibt einen
Carry von 0,35/(3*52) = 22,4 bp/Woche [abg.]. Bei SE 49..52 bp je Fenster ist dieser Carry im sprungfreien Fall
(Wahrscheinlichkeit e^(-2/3) = 0,51 ueber zwei Jahre [abg.]) nicht signifikant; das Gate faellt durch, weil der Peso-
Carry unter der MDE liegt, nicht wegen einer Peso-Abwehr. **Ehrlichkeitszeile:** Ein Mittelwert-Test kann ein
Peso-Risiko in der Groessenordnung des Funding-Vorteils (100..200 bp/Woche) nicht erkennen; die Abwehr ist das
Pflicht-Etikett "Praemien-EXISTENZ ... PARK" und der STRESS_REL-Abdeckungsnachweis (W1 13, W2 6 Episoden; STRESS_ABS
2 / 1 inklusive 2025-10-10), kein Gate (DEC-56). Bestehensregel T1: PASS-Rate ueber 1.000 Realisierungen <= nominales
alpha + 3 MC-SE, und im sprungfreien Teil <= 0,05.
