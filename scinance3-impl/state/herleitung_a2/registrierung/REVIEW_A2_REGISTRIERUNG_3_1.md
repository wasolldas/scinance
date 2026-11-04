# Review des A2-Registrierungsentwurfs unter Verfassung 3.1 (H-34, EXP-CLOCK) - adversarisch, symmetrisches Mandat (VR-f06) - 2026-11-04

> **Rolle:** Review (unabhaengig von der Herleitung). **Gegenstand:** `A2_REGISTRIERUNGSENTWURF_3_1.md`,
> `a2_registration_3_1.yaml` (sha256 211d05d0...), `calc/a2_reg_calc.py` (sha256 29577546...), `.out`, `.json`,
> `lint_a2_registration_3_1.out`; Auftrag `BRIEF_a2_registrierung_3_1.md`. **Mandat:** Fehler in beide Richtungen
> (zu lax UND zu streng); Pflichtfrage VR-f06. **Eigene Gegenrechnung:** `calc/review_a2_calc.py` (eigene
> Implementierung des Blockmodells, Seed 7, 400.000 Pfade, exakte OBF-Integration; sha256 9f85e0105a612a686a44c75ebf6af552110f8d7efc115c43f51ba208d21b68b0; Laufzeit 147 s; Ausgabe `calc/review_a2_calc.out`,
> `.json`). Nichts im Repository geaendert, nichts committet, keine Marktdaten, keine Siegeldatei, kein Netz;
> `stress_abs.json` nur Datumsliste. Kein Mittel, kein Vorzeichen eines r_pre-Kontrasts (VR-g06); keine
> Vereinigungs-Streuung gebildet (DEC-103 N1 (2c)). Rollen statt Modellnamen, keine Hostnamen, ASCII.
> **Gelesene Quellen (nur die im Auftrag genannten Stellen):** PRD v3 0.1, VR-b01..b17, VR-c01..c08, VR-d01..d20,
> VR-e01..e15, VR-f01..f12, Abschnitt 3 (PZ-01..PZ-30, YAML 3.3), 4.2; DEC-103 (+N1), DEC-104 E0..E10, N1, N2, N4,
> DEC-107 (1), (2) BE-03/04/06/12, (6), N1 (1)-(3); NULL_SIMULATION_A2.md 5, 5.3, 7 (nur Streuungen, Zaehlungen);
> HERLEITUNG_STABILITAETSTEST.md 1, 2, 4, 6.1, 7; feasibility/A2.yaml und Rechner F3 (ausgefuehrt); Linter
> registry31 (lint.py, schema.py), TEMPLATE_3_1.yaml; FENSTERREGISTER 6, 9, 10; KONTO_INVENTAR (A2-Zeilen O-051..O-054,
> O-009, O-902; F1-Zone-V-Zeilen O-013, O-116/117, O-122..O-125 nur Kopf); DATENANNAHMEN Zeile 10; Registry-Kopf (H-34);
> `stress_abs.json` (Datumsliste, Feld `sha256`, Datei-Hash); `stress_rel.json` (nur Hash-Konvention).
> **Marken:** [R] eigene Rechnung, [U] Urteil, [V] Vermutung, [sek] Sekundaerbeleg. Dezimalkomma im Text.

## Kurzfassung (<= 12 Zeilen)

1. **Ergebnis: 1 VETO (aufloesbar), 6 Auflagen, 9 Hinweise. Zweitfassung noetig** (VETO und Auflagen B-2..B-7 betreffen
   den normativen Text und eine offene Designentscheidung; die Rechenkerne halten).
2. Alle Kernzahlen mit eigenem Code und anderem Seed reproduziert: alpha_eff 0,00030 (Entwurf 0,00033; Binomialrauschen),
   P(PASS | 22 bp) 0,842, MDE80 Plan 19,49 bp, je Blick 24,56 / 22,57 / 20,96 / 19,49, Schutzzeile 0,281 (0,283),
   Strenge-Quotient 1,254 (1,2548), Stress 21,49 bp / 0,811, feste Regel 23,08 / 20,64 / 20,95, OBF alpha exakt 0,00249 [R].
3. **Pflichtfrage (VR-f06): ja, der Test ist gegen die SESOI sensitiv** - P(PASS | 22) 0,84 ueber den Plan (Stress 0,81),
   Power 0,80 an der SESOI aber erst am Blick 3 (2027-10-01); am Blick 1 0,71 (MDE80 dort 24,6 bp > 22). Gegen den
   Prior-Nominalwert 16,5 bp (UNBELEGT) nur 0,67. **Nicht mehr sensitiv**, wenn der K-Placebo P2' >= 25 % des Effekts
   traegt (0,78) - das ist der Preis der unentschiedenen Gabelung G-02 (B-1).
4. **B-1 VETO (aufloesbar):** Placebo in Zone K. DEC-103 E3 (P2'') erreicht in K 0 Tage; der Entwurf setzt P2' (alle
   Mo-Do). Das ist eine Aenderung des per Nutzerentscheid fixierten Placebosatzes ("jede Aenderung ist eine neue Gabelung
   mit Etikett", E3), an der die Testbarkeit haengt (ohne K: V allein 23,08 bp > 22 -> GL-012). Der YAML-Text ist dazu in
   sich widerspruechlich (Hypothese/Metrik "P2 (Mo-Do)", Design-Menue "P2'' auf V, P2strich in K", Null "P2-Partner").
   Erforderlich: DEC-Nachtrag (Entscheider N), Etikett, Placebo je Fenster im Hypothesensatz, Sensitivitaetszeile
   "Verduennung f" in der OC. Welche Gabelung Lockerung ist: (b) P2' auch in W2Q4 = Lockerung (SE 7,58 -> 7,34, F-1
   aufgehoben); die Entwurfswahl ist auf V neutral, in K neu (Estimand-Wechsel UNBELEGT); (a) woertlich = unbrauchbar.
5. **B-2 Auflage:** Hypothesensatz "um mindestens die SESOI 22 bp kleiner" und on_pass "Kontrast <= -22 bp" widersprechen
   der Entscheidungsregel (Test gegen 0) und BE-03/C.2 (keine Kostenzahl in PASS). Woertlich gelesen MDE ~41 bp (zu streng).
6. **B-3 Auflage:** juengster Teil "12 Monate bzw. vier Quartale" ist an den Blicken 1-2 zweideutig (Luecke 2026-07..09:
   3 gegen 4 Datenquartale); Schutzzeile 0,249 gegen 0,281 [R]. Quartale je Blick explizit registrieren (Torpfosten).
7. **B-4 Auflage:** Schutzzeile 0,283 ist "Effekt in Zone V (24 Monate), 0 in K", nicht "nur im aelteren Teil am Blick"
   (dann 0,068 [R]); beide Lesarten ausweisen; 0,253 davon sind PASS an Blicken 1-2 mit teilweise effekttragendem J.
8. **B-5 Auflage:** C.17-Verweise unvollstaendig (F1-Zone-V-Oeffnungen O-122..O-125, O-116/O-117, O-013 fehlen oder sind
   begruendet auszuschliessen). **B-6 Auflage:** Registrierung erst mit Konto-Eintrag der Vorfenster-SE (PZ-01 ist mit
   Platzhalter 7,58 nicht vollstaendig); bei SE ~5,5 skaliert die Plan-MDE auf ~14 bp. **B-7 Auflage:** t-artige
   Grenzen (registriert) gegen z-Grenzen (gerechnet): MDE +1,0 % (19,69), alpha 0,00024 - OC/PK-Injektion nachfuehren.
9. Hinweise (nicht blockierend): alpha_eff 0,0003 ist der beschlossene Preis der Konjunktion (DEC-103 E3/E4, VR-e04), nicht
   versteckt (Kette x1,12 ausgewiesen); Strenge-Quotient liegt je nach Grundfassungs-Lesart bei 1,25..1,30 (feste
   Ein-Blick-Grundfassung 1,304 -> Vorlage-Linie); n_eff 130 ist Rohzahl (effektiv 113); z_max-Etikett; Hash-Konvention
   STRESS_ABS (Datei-Hash wie H-32-Praezedenz) in Ordnung; Hygiene (R-C12a, R26) ohne Befund.

## 1. Pflichtfrage VR-f06: Sensitivitaet gegen SESOI und Prior nach allen Auflagen [R]

| Szenario (zentrale Nuisance 7,58, Gate 0,9025, Plan 30/33/36/39 Monate) | P(PASS) | je Blick kumuliert |
|---|---|---|
| Effekt 22 bp (SESOI), homogen V+K, Entwurfsregel | **0,842** | 0,713 / 0,785 / 0,822 / 0,842 |
| dto. mit t-artigen Grenzen (df N_E - 1, registrierter Wortlaut) | 0,840 | - |
| dto. Stress-Nuisance 8,52 | 0,811 | 0,599 / 0,704 / 0,770 / 0,811 |
| dto. Nebenbedingungen fest 2,8070 (G-03 Alternative) | 0,847 | - |
| Prior-Nominal 16,5 bp [sek, UNBELEGT] / 5 bp / 25 bp | 0,669 / 0,016 / 0,856 | - |
| 22 bp in V, K-Kontrast um f verduennt (P2' traegt f des Effekts): f 0,25 / 0,50 / 0,75 | 0,776 / 0,665 / 0,517 | Stab-FAIL 0,09 / 0,16 / 0,24 |
| MDE80 des Plans (P(PASS bis Blick 4) = 0,80): 19,49 bp; je Blick 24,56 / 22,57 / 20,96 / 19,49 bp | - | - |

[U] Antwort: **sensitiv** im Sinne von VR-b14 (gemeinsame Regel, Power 0,80 an der SESOI ueber den Plan). Einschraenkungen:
(i) am ersten Blick 2027-04-01 ist die Power an der SESOI 0,71 - "Entscheidung fruehestens 2027-04-01" ist eine
Moeglichkeit, keine 0,80-Zusage; 0,80 wird am Blick 3 (2027-10-01) erreicht; (ii) gegen den unbelegten Prior-Nominalwert
16,5 bp 0,67 (die Spanne 5..25 bp ist korrekt in beide Richtungen ausgewiesen, VR-c07); (iii) die Sensitivitaet haengt an der
Annahme, dass der K-Placebo P2' effektfrei ist - UNBELEGT (B-1); bei f >= 0,25 faellt die Power unter 0,80 und der
Stabilitaetstest erzeugt strukturelle FAILs (0,09..0,24) ohne realen "Abfall".

## 2. Befunde

Schwere: VETO (blockiert die Registrierung bis zur Aufloesung) / Auflage (vor der Registrierung zu erfuellen) / Hinweis.
Richtung: "zu lax" (Fehlerseite/Lockerung ohne Beschluss) / "zu streng" (Power/Testbarkeit ohne Beschluss) / neutral.

### B-1 - VETO (aufloesbar) - Placebo in Zone K: unentschiedene Aenderung des registrierten Placebosatzes, an der die Testbarkeit haengt; YAML in sich widerspruechlich - Richtung: beide

**Beleg.** DEC-103 E3 (Nutzerentscheid): P2'' = Mo-Do-Slots ohne Tage mit Futures-Delivery; "Die Groesse des
Placebosatzes ist hiermit fixiert; jede Aenderung ist eine neue Gabelung mit Etikett." DEC-103 N1 (5): F-4 ("P2' alle
Mo-Do") nur Bericht, "kehrt DEC-103 E3/K-1 um"; Festlegung F-1. DATENANNAHMEN Zeile 10 / O-052: taegliche
Futures-Deliveries seit 2026-04-04. Linter R30 HINWEIS: "P2-Tage nach DEC-103 E3 woertlich in Zone K: 0". VR-f07:
ein Design-Parameter, der 0 Beobachtungen erreicht, ist eine gescheiterte Erreichbarkeitspruefung. DEC-107 (6) P-12:
Lockerungen nur N, ab naechster Kohorte; Verschaerfungen O mit Quotient; Klarstellungen neutral.

**Rechnung [R].** (i) Kalender: P2'' in K = 0 (alle 261 Mo-Do sind Futures-Tage); unter E3 woertlich bleiben alle 66
K-Freitage unter J-(i) fest (kappa am Endblick 0,541), K liefert keinen Placebo-Kontrast, der Stabilitaetstest
(juengster Teil = K) ist nicht definierbar. (ii) Ohne K: V allein 24 Monate, feste Regel (c) + Gate 23,08 bp > 22 ->
GL-012 "strukturell nicht testbar" (DEC-107 N1 (1) Zeile 24 Monate). Die Registrierung steht und faellt also mit G-02.
(iii) Estimand: in W1 ist der Kontrast "Freitag (Wochen-/Monats-/Quartalsoptionen + Futures) gegen Mo-Do (nur
Tagesoptionen)"; in K "Freitag (dto.) gegen Mo-Do (Tagesoptionen + Tagesfutures)". Der Zahler-Mechanismus der
Hypothese ("in den Liefer-TWAP hinein handeln") gilt fuer Futures-Lieferungen ebenso; traegt der K-Placebo einen Anteil f
des Effekts, sinkt P(PASS | 22) auf 0,776 (f 0,25) / 0,665 (0,50) / 0,517 (0,75), und der Stabilitaetstest verwirft in
0,09 / 0,16 / 0,24 der Pfade ohne realen Abfall (Tabelle Abschnitt 1). f ist UNBELEGT (Tagesfutures-OI gegen
Wochen-/Monatsoptions-OI: O-052 nennt Kontraktzahlen Freitag ~13x Mo-Do fuer Optionen, nichts fuer Tagesfutures).
(iv) Die Alternative (b) P2' auch in W2Q4 (F-4 voll) senkt die W2-SE von 7,58 auf 7,34 und hebt kappa auf 1 (T6a):
das ist die Lockerung, die DEC-103 N1 (5) mit F-1 ausdruecklich nicht gewaehlt hat.

**Widerspruch im YAML.** `hypothese`: "Placebo-Tagen P2 (Mo-Do, [07:30, 08:00))" ohne Futures-Qualifikator (= P2'
ueberall); `metric`: "Placebo P2"; `design_menu.auswahlregel`: P2 (ohne Futures-Delivery) auf W1/W2, P2strich in K;
`structural_null`: "feste Freitage in Wochen ohne P2-Partner bleiben Ereignis" - in K waere das unter E3 jede Woche;
`reachability`: P2'' W1+W2 367 und P2strich K 261 getrennt. Der normative Satz (Hypothese) und die Auswahlregel
beschreiben zwei verschiedene Placebomengen auf W2Q4 und K.

**Welche Gabelung ist Lockerung, welche neutral [U].** (a) P2'' woertlich: keine Lockerung, aber unbrauchbar (K ohne
Kontrast; Gesamtplan nicht testbar). (b) P2' in W2Q4 und K: **Lockerung** (SE -3 % in W2, F-1 aufgehoben; Estimand in V
geaendert) -> N, ab naechster Kohorte. (c) Entwurf (P2'' auf V, P2' nur in K, mechanische Regel N_P2'' >= 0,5 N_MoDo):
auf V **neutral** (DEC-103 bleibt), in K eine **neue Festlegung** - in der SE Richtung Testbarkeit gegen (a), im Estimand
Richtung Strenge/unbekannt (Verduennung f); dazu eine Inhomogenitaet innerhalb der Stabilitaetsstatistik D (juengster
Teil mischt P2'' aus W2Q3 mit P2' aus K; B-3). Da (c) einen per Nutzerentscheid fixierten Placebosatz aendert und
Testbarkeit erst herstellt, ist Entscheider N (DEC-103-Nachtrag oder DEC-108), nicht O.

**Aufloesung.** (1) DEC-Nachtrag mit Wortlaut "P2 je Fenster: P2'' auf W1/W2 (E3), P2' in Zone K ab 2026-10-01
(taegliche Futures-Deliveries), Null J-(i) in K mit P2'-Partnern", Etikett "Aenderung des Placebosatzes in K; SE
Richtung Testbarkeit; Estimand-Anteil f UNBELEGT, Sensitivitaetsspanne f 0..0,5 in beide Richtungen (VR-c07)",
Entscheider N, Geltung Kohorte 1. (2) YAML: Hypothesensatz und `metric` nennen den Placebo je Fenster; `structural_null`
nennt P2' als Partner in K. (3) OC-Zeile um "P(PASS | 22, f 0,25 / 0,50)" ergaenzen; Positivkontrolle mit f 0 (Welt
ohne Mo-Do-Effekt) ist dann ausdruecklich die optimistische Welt. (4) Alternativ pruefbar (nur Vorschlag, nicht
Auflage): Stabilitaetstest auf dem P3fix-Kontrast (in allen Fenstern homogen definiert) als Nebenzeile berichten.

### B-2 - Auflage - Hypothesensatz und on_pass fuehren die SESOI als PASS-Bedingung - Richtung: zu streng (woertlich) / widerspruechlich

**Beleg.** YAML `hypothese`: "... um mindestens die SESOI 22 bp kleiner als an den Placebo-Tagen ..."; `decision_relevance.on_pass`:
"Kontrast <= -22 bp gegen alle Placebos". Dagegen `decision_rule`/`threshold`: Statistik in Richtung >= t_krit x SE
(Test gegen 0); DEC-107 (2) BE-03: SESOI ist Mess-Massstab, "eine Handelskostenzahl bleibt als PASS-, DROP- oder
Kill-Bedingung verboten"; C.2; PZ-02 "oekonomische Mindestmagnitude als Etikett, nie Gate". PRD 3.1: der Markdown-/
Hypothesentext ist der normative Text.

**Rechnung [R].** Woertlich (H0: Delta >= -22 bp) laege die MDE80 des Plans bei 22 + 19,5 = 41,5 bp (Verschiebung der
Null um die SESOI) - strukturell nicht testbar. So ist es nicht gemeint, aber so steht es. **Aufloesung:** H1 "Delta < 0 in
registrierter Richtung (negativ)"; SESOI nur in `sesoi_curve`/`economic_minimum` (Etikett ueber_wand) und in der
Power-Zeile; on_pass ohne die Zahl 22 als Bedingung ("PASS = Grenze erreicht und Stabilitaetstest nicht verworfen;
Schaetzer/CI werden gegen die SESOI-Kurve nur berichtet").

### B-3 - Auflage - Juengster Teil des Stabilitaetstests nicht torpfostenfrei definiert (12 Monate gegen vier Quartale; Luecke 2026-07..09) - Richtung: beide

**Beleg.** YAML `stability_test.statistik`: "letzte 12 Monate bzw. vier Quartale vor dem Blick, Lesart B einschliesslich
V-Ende". HERLEITUNG 1.1: "Zone K mit Quartalsblicken: die letzten vier Quartale; in Lesart B schliesst J das Ende von Zone V
ein, wenn K kuerzer als 12 Monate ist". DEC-107 (1)(a): "letzte 12 Monate bzw. vier Quartale". Fuer A2 sind das an den
Blicken 1-2 verschiedene Mengen, weil 2026-07..09 nicht urteilstragend ist: "12 Kalendermonate vor 2027-04-01" =
W2Q4 + KQ1 + KQ2 (39 Freitage, 3 Datenquartale, 15 Kalendermonate ohne Luecke nicht erreichbar); "vier Datenquartale" =
W2Q3 + W2Q4 + KQ1 + KQ2 (52 Freitage, 2026-01..2027-03). Der Rechner des Entwurfs nimmt vier Datenquartale.

**Rechnung [R].** Vier Datenquartale: alpha 0,00030, MDE80 19,49, P(PASS | 22) 0,842, Schutzzeile nur V 0,281. Zwoelf
Kalendermonate: alpha 0,00030, MDE80 19,46, P(PASS | 22) 0,843, Schutzzeile nur V **0,249**. Die Schutzwirkung haengt
also an der Lesart (0,25 gegen 0,28); beide Lesarten sind mit dem DEC-107-Wortlaut vereinbar -> Torpfosten-Risiko in
beide Richtungen (ein spaeterer Wechsel koennte einen FAIL in ein PASS oder umgekehrt drehen). **Aufloesung:** die
J-Quartale je Blick als Liste registrieren (Blick 1: W2Q3, W2Q4, KQ1, KQ2; Blick 2: W2Q4, KQ1, KQ2, KQ3; Blick 3:
KQ1..KQ4; Blick 4: KQ2..KQ5) und die Placebo-Inhomogenitaet von D an den Blicken 1-2 (P2'' in W2Q3/W2Q4-Freitage ohne
Quartalspartner, P2' in K) ausdruecklich benennen (B-1). Nebenbefund: "entfaellt bei <= 12 Monaten" tritt nie ein (30
Monate am Blick 1) - korrekt ausgewiesen.

### B-4 - Auflage - Schutzzeile: Szenario benennen; zwei Lesarten liegen um den Faktor 4 auseinander - Richtung: neutral (Selbstausweis)

**Beleg.** DEC-107 (1)(e): Pflicht-Schutzzeile "P(PASS bei Effekt nur im aelteren Teil, 1 MDE)". Entwurf: 0,283 fuer
"Effekt 1 MDE in Zone V (24 Monate), 0 in K"; Entwurf selbst (Abschnitt 6 Punkt 3) weist auf die Spannung hin.

**Rechnung [R].** Effekt nur in V (8 Quartale): 0,281, kumuliert 0,225 / 0,253 / 0,268 / 0,281; "veraltet" (PASS an
Blicken 3-4 mit effektfreiem J) 0,028; Stab-FAIL 0,242. Effekt nur im **aelteren Teil, wie er am Blick 1 definiert ist**
(W1 + W2Q1-Q2, 18 Monate): **0,068** (2 MDE: 0,010). Nur W1: 0,025. Ohne Stabilitaetstest, nur V: 0,403. Die 0,283 sind zu
0,253 PASS an den Blicken 1-2, an denen der juengste Teil zur Haelfte (W2Q3-Q4) noch Effekt traegt - das ist nach der
Logik von DEC-104 N4 (3)/(4.3) kein "veralteter" PASS, sondern ein PASS bei 24 von 30..33 Monaten Effekt. Die Zahl ist
als Worst-Case-Ausweis richtig und konservativ; als "Schutzzeile nach (1)(e)" ist sie nicht die Definition der DEC.
**Aufloesung:** `oc_line.p_pass_nur_aelter_1mde` mit Szenario-Etikett ("Effekt nur in Zone V") registrieren und die
Blick-1-Lesart (0,068) sowie "veraltet" (0,028) daneben ausweisen; keine Aenderung der Regel. [U] Der Entwurf ist hier eher
zu streng gegen sich selbst als zu lax; G-09 (Screen/alpha_stab 0,10) bleibt eine N-Frage, kein Review-Befund.

### B-5 - Auflage - C.17-Verweise (PZ-29) unvollstaendig - Richtung: neutral (Vollstaendigkeit)

**Beleg.** `c17_refs`: O-051, O-052, O-053, O-054, O-009, O-902. FENSTERREGISTER 6, Zeile F1: Zone V "verbraucht fuer
Vol/RV/VRP (O-116/O-117), fuer Stunden-/Tagesvorzeichen der 2.0-Statistiken (H-19/H-20/H-22/H-24) und fuer die
Funding-Lage (A1-Formation O-030); blind nur fuer A2 r_pre (Disziplin)". Inventar Abschnitt 2 (Zeile "V", F1): O-122..O-125
(S2: Mittel mit Vorzeichen je Fenster, u. a. O-125 Minuten-Fluss gegen Forward-Logmove bis Minute +30 auf W-R1/W-R2
2025-08..2026-07, BTC/ETH), O-013 (Mid-Bewegung nach Fill 2026-06-22..09-24), O-101..O-121 (2.0-Gate-Bits 2026-03-27..
06-28). PZ-29: "Zeilen des Konto-Inventars, Vorbelastungen, gesehene Groessen".

**Rechnung/Urteil [U].** Diese Oeffnungen betreffen BTC/ETH-Renditegroessen auf W1/W2, teils intraday mit 30-Minuten-
Horizont; sie beruehren nicht den Freitags-Slot [07:30, 08:00) als Statistik, sind aber Vorbelastungen der Datenfamilie F1 auf
Zone V im Sinne von VR-d16/VR-d18. Entweder in `c17_refs` aufnehmen (mit Vermerk "Vorbelastung F1/V, nicht der
A2-Slot") oder je Zeile begruendet ausschliessen; der Linter R19 prueft nur Existenz und Eindeutigkeit, nicht
Vollstaendigkeit. Dazu `etiketten`: "W1/W2 fuer A2 r_pre blind durch Disziplin" um die Liste der gesehenen F1-Groessen
ergaenzen (Kopf-Etikett wie DEC-104 N1 (5) fuer fm8).

### B-6 - Auflage - Bindende Nuisance ist ein Platzhalter; PZ-01/VR-b10 (i) nicht erfuellt - Richtung: unbekannt (vermutlich Testbarkeit)

**Beleg.** DEC-107 (2) BE-04: bindend das juengste Vorfenster 2023-07-01..2024-06-30 (VR-b10 (i) Vorperiode nur
Streuung, (ii) Null-Simulation; groessere SE). DEC-107 N1 (2): "nachzuliefern". Entwurf: 7,58 (Null-Simulation W2
zentral) als Platzhalter; Hinweis auf T2-Zeile V3 (2023-06..2024-05): SE 5,31 (eigene N) / 5,51 (W2-N), Null-SD 4,51.
PZ-01: Power "gerechnet mit genau der SE-Regel des Tests".

**Rechnung [R].** Skaliert mit 5,51/7,58 laege die Plan-MDE80 bei 14,2 bp, die feste Regel bei 30 Monaten bei 15,0 bp
(Entwurf identisch). alpha und Schwelle sind davon unabhaengig (t-artig aus der Konfirmations-SE, DEC-107 N1 (2)) - richtig.
Aber: PK-Injektion (19,50), PK-SD-Grenze (1,10 x 7,58), OC-Zeile, Schutzzeile, Strenge-Kette und mde_faktor-Lesart haengen
daran. **Aufloesung:** Konto-Eintrag der Vorfenster-SE (nur Streuung, c, Null-SD; Lesart der N fixieren) vor der
Registrierung; Rechner mit `se12_central_W2`/`se_W1`/`se_W2` nachfuehren; YAML-Zahlen ersetzen. Bis dahin ist die
Registrierung nicht vollstaendig (PRD 3.1: "ohne vollstaendige Pflichtzeilen kein gueltiger Eintrag"). Hygiene-Vermerk:
der V3-Hinweis nennt nur Streuungen; keine Vereinigungs-SD, kein Mittel - in Ordnung.

### B-7 - Auflage - Registriert sind t-artige Grenzen, gerechnet wurde mit z-Grenzen - Richtung: zu lax in der Planung (kleiner Betrag)

**Beleg.** YAML `looks.zone_k.grenzen: t_artig`, `threshold`: "t_krit(df = Ereignis-Cluster - 1, alpha des Blicks nach
OBF) x SE_Konfirmation"; VR-f08/DEC-104 N2 (7). Rechner des Entwurfs: z-Grenzen 3,300 / 3,147 / 3,013 / 2,886 (nur im
Text am Blick 1 t_0,0025 2,856 gegen 2,807 - das ist die Ein-Blick-Grenze, nicht die OBF-Grenze).

**Rechnung [R].** Gleiche alpha je Blick, df 129 / 142 / 155 / 169: t-Grenzen 3,378 / 3,208 / 3,062 / 2,926 (x1,024 ..
x1,014). Gesamtregel mit t-Grenzen: alpha_eff 0,00024, MDE80 Plan **19,69 bp** (+1,0 %), P(PASS | 22) 0,840. Klein, aber die
registrierte MDE80 und die PK-Injektion (Kriterium 0,7342 bei erwarteter Quote 0,80) sollen die registrierte Regel
treffen; mit 19,50 bp unter t-Grenzen ist die erwartete PK-Quote ~0,79. df_eff nach Kurtosis (VR-f08) ist nicht adressiert
(die J-(i)-Null ist normal, DEC-103 N1 (3); die Cluster-Serie selbst nicht geprueft) - als Etikett nennen.
**Aufloesung:** Rechner mit t-Grenzen laufen lassen (oder OC als "z-Naeherung, -1 %" etikettieren) und PK-Injektion an die
t-Regel binden. Nebenbefund [R]: OBF-C_B 2,886 stammt aus Monats-Anteilen (alpha exakt 0,002497); mit Ereignis-Anteilen
130/143/156/170 alpha exakt 0,002486 (C_B fuer 0,0025 waere 2,8845) - unter 0,0025, keine Auflage.

### B-8 - Hinweis - alpha_eff 0,00033: beschlossener Preis der Konjunktion, nicht versteckt; Zerlegung - Richtung: zu streng, aber so beschlossen

**Rechnung [R].** OBF-Plan allein 0,00244; + Stabilitaetstest + Futility 0,00240; + P3fix an der OBF-Grenze **0,00048**;
+ P3all 0,00033; + Null-Bedingung 0,00033 (bindet nie: tau95 1,655 << 2,886); x Gate 0,00030. Treiber ist die
Konjunktion dreier gleichrangiger z-Bedingungen (Korrelation ueber den Ereignis-Term ~0,77 der Varianz, Placebo-Terme
unabhaengig). **Beschlusslage:** DEC-103 E3 "Konjunktion gegen alle Placebos", E4 Schwelle je Bedingung max(q95;
z_krit x SE); VR-e04/DEC-104 E7 (a) aenderten nur Produkt -> exakte gemeinsame Power, nicht das alpha je Bedingung;
VR-b14 "alpha je Test fest 0,0025" ist das nominale alpha je Bedingung. Also beschlossen; der Entwurf weist den Preis in
PZ-22 (x1,12) und in der OC (p_pass_0 0,00033) aus - nicht versteckt. [U] Zwei Dinge sind trotzdem zu sagen: (i) das
Jahresbuch bucht 0,0025, realisiert 0,0003 - konservativ, in Ordnung; (ii) G-03 (Nebenbedingungen fest 2,8070 statt
OBF-Grenze je Blick) ergaebe alpha 0,00049, MDE80 18,99 (-2,6 %), P(PASS | 22) 0,847 - beides zulaessig, die Entwurfswahl ist
eine Verschaerfung mit Quotient-Ausweis (O, P-12 (b)). Nur zum Vergleich, nicht beschlossen: Nebenbedingungen bei
1,6449 ergaeben alpha 0,00185, MDE80 17,56.

### B-9 - Hinweis - MDE80-Lesart (Plan 19,50 gegen feste Regel 20,95) - Richtung: neutral; Zeitangabe praezisieren

[R] Die Plan-MDE80 19,50 bp (P(PASS bis Blick 4) = 0,80) ist die richtige Lesart von VR-b14 fuer eine gruppensequentielle
Regel; die 20,95 bp des Orchestrators (feste Regel 30 Monate x sqrt(1,03)) sind eine Ein-Blick-Naeherung; der Faktor 1,03
passt zu gleichverteilten Blicken (N4 (3)), nicht zum Plan each_term 30/33/36/39 (R_max 1,084 -> 21,50 bp). Beide werden
durch die Plan-Rechnung abgeloest. Zu praezisieren: "Entscheidung fruehestens 2027-04-01" meint Moeglichkeit (Power 0,71 an
der SESOI; MDE80 am Blick 1 24,6 bp > 22); Power 0,80 an der SESOI ab Blick 3 (2027-10-01). Doppelausweis Blick 1 Produkt
25,10 gegen exakt 24,56 reproduziert.

### B-10 - Hinweis - Strenge-Quotient 1,254 liegt knapp unter der Vorlage-Linie und haengt an der Grundfassungs-Lesart - Richtung: zu lax (Ausweis)

[R] Entwurfs-Grundfassung (P2'' allein, Regel (c) mit Plan, Stabilitaetstest, Futility, kein Gate): 15,54 -> Kette
17,44 (x1,122) -> 17,45 (x1,001) -> 17,45 (x1,000) -> 19,49 (x1,117); Quotient **1,254** (reproduziert). Alternativen:
Plan, Primaerstatistik ohne Stabilitaetstest/Futility 15,10 -> **1,291**; fester Ein-Blick-Test 39 Monate, Primaer allein,
alpha 0,0025, ohne Stabilitaetstest 14,94 -> **1,304**; mit q 0,95 15,61 -> 1,249; am Blick 1 gegen festen Test 30 Monate
17,13 -> 1,434. VR-f05 nennt die Grundfassung "Primaerstatistik allein, zentrale Nuisance, dieselbe Entscheidungsregel und
dasselbe alpha" als Vorschlag der OC (g) - der Entwurf folgt ihr korrekt (Stabilitaetstest ist Teil der Regel). [U] Die
Spanne 1,25..1,30 gehoert in die Zerlegung; groesster Einzelterm ist der UNBELEGTE Gate-Faktor (x1,117). Ob der
Orchestrator trotz < 1,3 vorlegt, ist seine Entscheidung (P-12 (d)); kein Review-Veto.

### B-11 - Hinweis - n_eff, c_overlap, z_max: Etiketten - Richtung: neutral

n_eff 130 ist die Rohzahl der Ereignis-Cluster am Blick 1; PZ-23 verlangt das effektive N mit gemessenem c: 130/1,1491 =
113 (Ereignis-Serie); die registrierten 98,7 (N_E/1,3177) benutzen den Mo-Do-Faktor der Placebo-Serie. c_overlap 1,3177 ist
der Placebo-Faktor; beide c je Klasse nennen. `selection.z_max 2.8070` ist max(z_krit, z_max(K=1) = 0), nicht die
Bailey/Lopez-de-Prado-Decke (0 fuer K = 1; Schema erzwingt > 0) - als solches etikettieren. K = 1 / kumuliert 1 stimmt mit
Inventar Abschnitt 3 ("A2 EXP-CLOCK: 0") ueberein.

### B-12 - Hinweis - STRESS_ABS, Jahresbuch, Erreichbarkeit - Richtung: neutral (bestaetigt)

[R] STRESS_ABS-Tage in den Urteilsfenstern 3 (W1: 2024-08-05, 2025-02-03; W2: 2025-10-10; K registriert 0; Luecke
2026-08-19; Vorfenster 2023-08-17) reproduziert; Ereignis-Freitag mit Stress 1 (2025-10-10) - Stress-Zelle nicht
schaetzbar, nur Sensitivitaet: richtig. Hash: `liste_ref` traegt den Datei-Hash b8008257... (Praezedenz H-32, Registry
Zeile 596 benutzt denselben Datei-Hash); das Feld `sha256` der Datei (b75fb7a0...) ist der DEC-56-Kanon-Hash
(ANTWORT_AN_DATA_HARVEST 2026-11-04 zitiert ihn); der Entwurf nennt beide in `data_fingerprints` - Wortlaut "Datei-sha256"
in `liste_ref` empfohlen. Jahresbuch 2027: 0 vorher (H-27..H-33 ohne Blick 2027), 0,0025 mit A2 (realisiert 0,0003) < 0,10.
Erreichbarkeit: 170 Ereignis-Freitage (52/52/66), P3fix 807, P3all 846, 130 Cluster am Blick 1 >= 26 reproduziert; W2Q4
Mo-Do ab 2026-04-06 48 Futures-Tage (P2'' 159) bestaetigt.

### B-13 - Hinweis - Vollstaendigkeit der 30 Pflichtzeilen, Lesestatus, Positivkontrolle - Richtung: neutral

Linter 0 FEHLER / 2 HINWEIS reproduziert (Aufruf wie im Entwurf). PZ-01..PZ-30 vorhanden; Lesestatus plausibel
(a2_teilC.json Fassung 2 ausserhalb des Repos mit Hash; "nie_berechnet" fuer beide Cluster-Serien). Positivkontrolle:
Kriterium 0,80 - 2,3263 x 0,0283 = 0,7342 reproduziert; P(NICHT BESTANDEN | wahre Quote 0,80) 0,010, bei 0,75 0,30 [R] -
das Kriterium ist trennscharf genug. Offen (B-6, B-7): Injektion und SD-Grenze haengen an Platzhalter-SE und z-Naeherung.
Fixtures (positiv/null/adversarial Klasse E) nach PZ-05 vollstaendig. `windows.K1 bis 2027-12-31` gegen das Rollieren
VR-d09 (2026Q4 wandert 2027-07-01 nach V): fuer eine registrierte Hypothese bleibt die Zuordnung eingefroren - ein Satz im
Zoneneintrag genuegt.

### B-14 - Hinweis - Hygiene (Pruefpunkt 5 des Entwurfs, Auftragspunkt 6) - ohne Befund

Keine Modellbezeichnung, kein Hostname, kein Nicht-ASCII-Zeichen in Entwurf, YAML, Rechner, Ausgaben [R, grep]. Kein
Mittel, kein Vorzeichen eines r_pre-Kontrasts; der Rechner liest nur veroeffentlichte SEs, Null-SDs, Zaehlungen und die
Datumsliste von `stress_abs.json`. Keine Vereinigungs-Streuung: die Placebo-Tagesvarianzen werden aus den
Fenster-SEs je Fenster abgeleitet und gemittelt (keine SD einer Vereinigung zweier Klassen derselben Werte; W1/W2
stimmen auf 0,4 % ueberein [R]). Der V3-Hinweis (SE 5,31 / Null-SD 4,51) ist Streuung. Linter R26/R27 OK.

### B-15 - Hinweis - Gabelungsregister (Abschnitt 4 des Entwurfs): Bewertung der Richtungen

| Nr | Bewertung [U] |
|---|---|
| G-01 q 0,95 statt q_plan 0,964 | konservativ, neutral; mde_faktor-Etikett korrekt ("nie Schwelle") |
| G-02 | **B-1**; (a) unbrauchbar, (b) Lockerung (N), Entwurf: neutral auf V, neu in K (N) |
| G-03 Nebenbedingungen an OBF-Grenze | Verschaerfung (O mit Quotient), alpha 0,00033 gegen 0,00049; MDE +2,6 % |
| G-04 Nebenbedingung scheitert -> weiter | alpha durch P2''-Grenze begrenzt (PASS Teilmenge von "P2'' kreuzt") [R bestaetigt]; neutral/O |
| G-05 Gate 0,9025 | UNBELEGT, groesster Kettenterm; Spanne nach VR-c07 in beide Richtungen (0,99^2 .. 0,90^2) ausweisen |
| G-06 Platzhalter-SE | **B-6** |
| G-07 V-Blick = erster K-Blick | folgerichtig (V allein 23,08 > 22); FENSTERREGISTER-Nachtrag noetig (O) |
| G-08 vier Quartalsblicke | Lockerung in der Zeit bei festem alpha (DEC-104 E4 (e)), beschlossen |
| G-09 Schutzzeile hingenommen | **B-4**; Regelaenderung waere N |
| G-10 Stress Sensitivitaet | BE-04 beschlossen; E7 (c)-Vorbehalt korrekt entkraeftet (t-artige Schwelle) |
| G-11 Taker-SESOI | beschlossen (E3 (a)), Etikett vorhanden |
| G-12 F-1 | DEC-103 N1 (5) Festlegung, bleibt |
| G-13 t-artige Schwelle | DEC-107 N1 (2); **B-7** (im Rechner nicht umgesetzt) |
| G-14 Futility | beschlossen (E4 (e)); unter H0 0,58 Stopps [R] |
| G-15 exakte Konjunktion | VR-e04 beschlossen; Doppelausweis vorhanden |

## 3. Antworten auf die fuenf Pruefpunkte des Entwurfs (Abschnitt 6) und die sechs Auftragspunkte

1. **Sensitivitaet / MDE80-Lesart / G-03:** Abschnitt 1; B-9; B-8. Plan-Lesart richtig; G-03 ist Verschaerfung mit kleinem Preis.
2. **Modell des Rechners:** mit eigener Implementierung (andere Blockstruktur-Kodierung, Seed 7, 400.000 Pfade) auf
   <= 0,3 bp bzw. <= 0,003 in allen Zeilen reproduziert; Placebo-Varianzen aus den Fenster-SEs konsistent (W1/W2 0,4 %);
   Welch als z unbedenklich (df > 100); OBF-Grenze exakt 0,00249; Grenzen: Normalitaet, unkorrelierte Placebo-Terme,
   Gate unabhaengig - wie im Entwurf benannt; dazu kommt die Annahme "K-Placebo effektfrei" (B-1).
3. **Schutzzeile:** B-3, B-4 (0,281 / 0,249 / 0,068 / 0,025 je nach Definition).
4. **Placebo in K:** B-1 - braucht eine DEC (N), keine Orchestrator-Klarstellung.
5. **Hygiene:** B-14 ohne Befund.
6. Auftragspunkte (1) alpha/Power/Quotient: B-8, B-9, B-10; (2) Schwelle t-artig/Null-Boden: B-7 (Rechner z), Null-Boden
   bindet nie, Null in K braucht P2'-Partner (B-1); (3) Stabilitaetszeile: B-3; (4) Zone K: B-1; (5) Vollstaendigkeit,
   Lesestatus, C.17, Jahresbuch, STRESS_ABS: B-5, B-12, B-13; (6) Hygiene: B-14.

## 4. Gegenrechnung (Entwurf gegen Review) [R]

| Groesse | Entwurf (Seed 20261104, 300k) | Review (Seed 7, 400k) |
|---|---|---|
| alpha_eff Regel ohne/mit Gate | 0,00037 / 0,00033 | 0,00033 / 0,00030 |
| alpha Primaer allein (Stab+Futility) / OBF allein | 0,00246 / 0,00251 | 0,00240 / 0,00244 (exakt 0,00249) |
| P(PASS | 22) gesamt; je Blick | 0,8421; 0,713/0,784/0,822/0,842 | 0,8421; 0,713/0,785/0,822/0,842 |
| MDE80 Plan; je Blick | 19,50; 24,56/22,60/20,96/19,50 | 19,49; 24,56/22,57/20,96/19,49 |
| P(PASS | 5 / 16,5 / 25) | 0,017 / 0,669 / 0,855 | 0,016 / 0,669 / 0,856 |
| Schutzzeile nur V 1 MDE; veraltet; ohne Stab | 0,283; 0,028; 0,405 | 0,281; 0,028; 0,403 |
| nur V 2 MDE; nur W1 1 MDE | 0,319; 0,026 | 0,318; 0,025 |
| Strenge-Kette | 15,54 / 17,43 / 17,44 / 17,44 / 19,50; 1,2548 | 15,54 / 17,44 / 17,45 / 17,45 / 19,49; 1,254 |
| Doppelausweis Blick 1 | 25,10 / 24,56 | 25,10 / 24,56 |
| Stress: MDE80, P(PASS | 22), alpha | 21,46; 0,812; 0,00048 | 21,49; 0,811; 0,00034 |
| feste Regel 7,58: T24/T30/T30x1,03; 22 bp ab | 23,08/20,64/20,95; 26,4 Mon. | identisch |
| STRESS_ABS in Urteilsfenstern; Kalender K | 3; 66/261/312/327 | 3; 66/261/312/327 |
| neu: t-Grenzen MDE80 / alpha | - | 19,69 / 0,00024 |
| neu: J = 12 Kalendermonate: Schutzzeile | - | 0,249 |
| neu: nur aelterer Teil am Blick 1 (1 / 2 MDE) | - | 0,068 / 0,010 |
| neu: Verduennung f 0,25 / 0,5: P(PASS | 22) | - | 0,776 / 0,665 |
| neu: G-03 fest 2,807: alpha / MDE80 | - | 0,00049 / 18,99 |

## 5. Was nicht folgt

Kein Verdikt ueber einen Markteffekt; keine Registrierung; keine Aenderung an DEC-103/104/107; keine Effektgroesse, kein
Vorzeichen; alle Zahlen sind Fehlerraten und Aufloesungsgrenzen unter dem Gauss-Blockmodell (Normalitaet, unkorrelierte
Placebo-Terme, Brownsche Information, Gate unabhaengig, K-Placebo effektfrei ausser in der f-Sonde). Der Review ersetzt
nicht den Konto-Eintrag der Vorfenster-SE und nicht die Negativ-Panel-Probe.

## 6. Auflagen fuer die Zweitfassung (kompakt)

1. B-1: DEC-Nachtrag (N) zum Placebo in K; Hypothese/Metrik/Null je Fenster konsistent; OC-Zeile f 0,25 / 0,50.
2. B-2: SESOI aus Hypothesensatz und on_pass entfernen; H1 "Delta < 0".
3. B-3: J-Quartale je Blick als Liste; Placebo-Inhomogenitaet von D benennen.
4. B-4: Schutzzeile mit Szenario-Etikett; Blick-1-Lesart 0,068 und "veraltet" 0,028 daneben.
5. B-5: c17_refs um F1-Zone-V-Oeffnungen ergaenzen oder begruendet ausschliessen.
6. B-6: Vorfenster-SE als Konto-Eintrag vor der Registrierung; alle SE-abhaengigen Zahlen nachfuehren.
7. B-7: Rechner mit t-Grenzen; PK-Injektion an die registrierte Regel binden; df_eff-Etikett.
Empfohlen (Hinweise): Spanne des Strenge-Quotienten 1,25..1,30 in die Zerlegung; n_eff/c je Klasse; z_max-Etikett;
"Entscheidung fruehestens" als Moeglichkeit mit Power 0,71 am Blick 1 formulieren; Gate-Faktor-Spanne nach VR-c07.
