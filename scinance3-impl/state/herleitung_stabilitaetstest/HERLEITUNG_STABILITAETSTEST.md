# Herleitung des registrierten Stabilitaetstests (P-2 Variante (c), DEC-104 Nachtrag 2 (4)) - Stand 2026-11-02

> **Rolle:** Herleitung mit eigenem Code (Formeln und Simulation). **Keine Marktdaten, keine Siegeldatei, kein
> Harvest-Client, keine Registrierung, kein Verdikt.** Nichts im Repository geaendert, nichts committet.
> **Auftrag:** `stab/BRIEF_stabilitaetstest.md` (Nr. 1..8).
> **Code und Ergebnisse:** `stab/calc/stab_sim.py` (deterministisch, Seeds 31104..31107 sowie 31108 + T_max fuer die
> Monats-Blickplaene, `python3 -I`, nur numpy/scipy), `stab/calc/stab_results.json`, `stab/calc/stab_sim.out`.
> Jede Zahl dieses Textes steht in einer der beiden Ausgabedateien (Abschnitt (0)..(7) der Ausgabe). Monte Carlo:
> GSD 1.000.000 Pfade (gleichverteilte Blicke) bzw. 500.000 (Monats-Blickplaene); Raender 200.000 (AR(1) 100.000);
> A2 2.000.000 gemeinsame Ziehungen. Laufzeit 597,5 s CPU.
> **Quellen:** OC-Bericht `state/prd_analyse_2026-11-01/OC_VERFASSUNG31_2026-11-02.md` und `scripts/oc_sim.py`
> (A2-Konstanten und Kovarianzmodell woertlich uebernommen), `scripts/orch_oc_check.py`, `state/decisions.md`
> (DEC-51/52/94/99/104 mit N1-N3/105), `FENSTERREGISTER.md` Abschnitt 6, `PRD_SCINANCE3_v3_ENTWURF.md` 2b/3.2/3.3,
> `src/bybit_edge/research/feasibility31/rules.py` (R4/R5 gelesen, nicht geaendert).
> **Markierungen:** [R] Rechnung dieses Skripts, [U] Urteil, [V] Vermutung / Modellannahme ohne Messung.
> Dezimalkomma im Text, Dezimalpunkt in den Ausgabedateien.

## Ergebnis in fuenf Saetzen [U, gestuetzt auf R]

1. Die Statistik ist die Differenz D = Mittel(juengste 12 Monate) - Mittel(aeltere Konfirmationsdaten) mit getrennt
   geschaetzten SE (Welch), einseitig 0,05 gegen "Abfall"; bei gleicher Cluster-Varianz ist D exakt unabhaengig vom
   gepoolten Mittel, die OC-Zahlen fuer **einen** Blick (alpha 0,002375, Daten x1,0905 gegen gepoolt, x1,1741 gegen
   C.10 je 0,80, kein Boden) stimmen [R].
2. Der Preis "kein Boden" ist ein REZENZ-Schutz, der nur gegen **absolut** grosse Abfaelle wirkt (>= 2,4865 /
   sqrt(1-r) SE_12 mit 0,80): bei langen Konfirmationen besteht ein Effekt, der nur im aelteren Teil liegt, im
   schlechtesten Fall mit 0,0787 (r 1/2) bis 0,5501 (r 1/10) statt <= 0,05 (Screen) [R].
3. An gruppensequentiellen Blicken kostet der Test fast nichts und schuetzt wenig, weil die Erstkreuzung des
   O'Brien-Fleming-Pfades den juengsten Zuwachs nach oben selektiert; "nur am letzten Blick" (N2 (5)) ist praktisch
   leer (q 0,9934..1,0000) [R]. Empfohlen wird der Test an **jedem** Wirksamkeits-Stopp mit **terminaler**
   Verwerfung (FAIL), nicht mit Weiterlaufen [U].
4. Schwere Raender (Kurtosis 5..13) stoeren den Welch-Test nicht (alpha_stab 0,0491..0,0506); unterschaetzte
   Autokorrelation kostet Power (q bis 0,8863), nicht alpha der Gesamtregel [R].
5. A2: unter (c) 28,969 bp bei 24 Monaten (schlechter als (a) 28,053), 22 bp ab 41,62 Monaten -> **2028-04** (nicht
   2028-01: die OC zaehlte F1-Daten durchgehend ab 2024-07, Zone K fuer BTC/ETH beginnt aber 2026-10-01); Klasse W
   SD 0,13 / SESOI 0,040: 2027-07 statt "nie"; gegen die Dezil-SESOI 0,0085 auch unter (c) 31,3 bzw. 65,3 Jahre [R].

## 1. Definition

### 1.1 Statistik, Nullhypothese, Richtung [U, Formeln R]

- Konfirmationsdaten einer Registrierung am Blick b: die urteilstragende Cluster-Serie x_1..x_n (Cluster nach VR-b03),
  **in registrierter Richtung** (Vorzeichen so, dass der Effekt positiv ist; A2-Kontrast negativ -> mit -1 multipliziert).
- **Juengster Teil J:** alle Cluster der letzten 12 Monate vor dem Blick (Zone K mit Quartalsblicken: die letzten vier
  Quartale; in Lesart B schliesst J das Ende von Zone V ein, wenn K kuerzer als 12 Monate ist). **Aelterer Teil A:**
  alle uebrigen Konfirmationsdaten derselben Registrierung (Zone V und aeltere K-Quartale). Anteil r = n_J / n.
- **Statistik:** D = xbar_J - xbar_A, SE(D) = sqrt(SE_J^2 + SE_A^2), jede Teil-SE nach VR-b09 (max(naiv, Bootstrap),
  c >= 1, Blocklaenge aus gemessener Autokorrelation) und **getrennt je Teil** geschaetzt; Z_D = D / SE(D).
- **H0_stab:** mu_J >= mu_A ("der juengste Teil faellt nicht ab"). **Verwerfung** (Befund "Abfall"): Z_D < -t_krit,
  t_krit = Quantil 0,95 der t-Verteilung mit Welch-Satterthwaite-Freiheitsgraden (bei bekannter Varianz 1,6449);
  einseitig 0,05.
- Liegt der Effekt nur im aelteren Teil (mu_J = 0, mu_A = mu in SE_12), ist E[Z_D] = -mu sqrt(1-r) [R]; an der MDE der
  Variante (c) sind das -1,9051 (r 1/2), -1,7961 (1/3), -1,6499 (1/4), -1,4200 (1/6), -1,1431 (1/10) [R, (7)].
- **Entfaellt**, wenn die Konfirmationsdaten am Blick hoechstens 12 Monate umfassen (kein aelterer Teil; alle Daten sind
  juengste, die REZENZ-Frage stellt sich nicht) [U]. Hinweis an F3: `PooledStability` (R5) in `rules.py` rechnet die
  Kostenquote 0,95 auch fuer T <= 12 Monate; das ist dann konservativ, aber nicht die Regel [R, Codelesung].

### 1.2 Beziehung zur gepoolten Statistik [R]

Mit Cluster-Varianzen sigma_J^2, sigma_A^2 und dem registrierten gepoolten Mittel aller Cluster
m_p = r xbar_J + (1-r) xbar_A gilt

    Cov(m_p, D) = r Var(xbar_J) - (1-r) Var(xbar_A) = (sigma_J^2 - sigma_A^2) / n.

Bei gleicher Varianz ist die Kovarianz 0; da (m_p, D) gemeinsam normal sind, sind gepoolte Statistik und
Stabilitaetsstatistik **unabhaengig**, fuer jedes r. Daraus: alpha_eff = 0,0025 x 0,95 = 0,002375 und
q := P(Stabilitaet haelt | gepoolt besteht, homogener Effekt) = 0,95 exakt (Abschnitt (0)/(2)).

Ungleiche Varianzen (k = sigma_J / sigma_A, Informationsanteil r_I des juengsten Teils): Korrelation gepoolt / D

| r | k 0,5 (r_I) | k 0,7 | k 0,85 | k 1 | k 1,25 | k 1,5 | k 2 (r_I) |
|---|---|---|---|---|---|---|---|
| 1/2 | -0,6000 (0,8000) | -0,3423 | -0,1611 | 0 | +0,2195 | +0,3846 | +0,6000 (0,2000) |
| 1/4 | -0,5447 (0,5714) | -0,3009 | -0,1400 | 0 | +0,1913 | +0,3394 | +0,5447 (0,0769) |

Ein ruhigerer juengster Teil (k < 1) macht die Korrelation negativ (gepoolter Erfolg geht mit "Abfall" einher, q < 0,95),
ein unruhigerer positiv. **alpha_eff bleibt in jedem Fall <= 0,0025**, weil der Stabilitaetstest eine zusaetzliche
PASS-Bedingung ist (Spanne 0,000989 bei k 0,5 bis 0,002500 bei k 2, r 1/2) [R]. Ein invers-varianzgewichtetes
Poolen stellte exakte Unabhaengigkeit her, aenderte aber die registrierte Primaerstatistik (DEC-104 E2: gepoolter
Test ueber alle Konfirmationsdaten) - nicht vorgeschlagen [U]. Mit geschaetzter Varianz enthaelt die Gesamtvarianz
den Term n_J n_A / n (xbar_J - xbar_A)^2; die Abhaengigkeit ist klein (q 0,9488..0,9511 bei symmetrischen Raendern,
Abschnitt 5) [R].

### 1.3 Alternative: Nicht-Unterlegenheit mit f = 0,5 [R, U]

| Form | Bedingung | MDE (SE_12) r 1/2 / 1/4 / 1/10 | Boden | sup P(PASS / Effekt nur aelter) r 1/2 / 1/4 / 1/10 |
|---|---|---|---|---|
| (c) Differenz (vorgeschlagen) | Z_D >= -1,6449 | 2,6942 / 1,9051 / 1,2049 | keiner | 0,0787 / 0,2741 / 0,5501 |
| NI-Nachweis (Last beim Effekt) | (xbar_J - 0,5 m_p)/SE > 1,6449 | 3,9361 / 4,4826 / 4,7828 | **4,9729** = (z95 + z80)/(1 - f) | 0,0046 / 0,0066 / 0,0119 |
| NI-Marge (verwirft nur Abfall unter 0,5 x gepoolt) | (xbar_J - 0,5 m_p)/SE > -1,6449 | 2,5803 / 1,8279 / 1,1632 | keiner | 0,4597 / 0,6447 / 0,7883 |

- **NI-Nachweis:** schuetzt am besten, hat aber den **doppelten** Boden des 0,05-Screens (4,9729 gegen 2,4865 SE_12)
  und verschlechtert jede MDE gegen (a) - verwerfen [U].
- **NI-Marge:** fast kostenlos (q 0,9898..0,9999), aber praktisch ohne Schutz und mit gepoolter Statistik korreliert
  (0,1644..0,4472), also ohne feste Kostenquote - verwerfen [U].
- **Differenz (c):** einzige Form mit fester Kostenquote (q = 0,95 bei gleicher Varianz), Unabhaengigkeit und ohne
  Boden. Nachteil: ihr Schutz ist absolut, nicht relativ zur MDE (Abschnitt 3) [U].

## 2. Entscheidungsregel und Power-Planung

### 2.1 Regel (Vorschlag) [U]

PASS genau dann, wenn (i) der gepoolte einseitige Test ueber alle Konfirmationsdaten Z >= 2,8070 erreicht (t-artige
Grenze nach DEC-104 N2 (7)) **und** (ii) der Stabilitaetstest **nicht** verwirft. Power-Ziel 0,80 fuer die gemeinsame
Regel an der SESOI: gepoolte Power 0,80 / q.

### 2.2 Ein Blick (Zone V oder fester Endblick) [R]

| r | MDE (c) in SE_12 | q | Daten gegen gepoolt / C.10 je 0,80 / C.10 gemeinsam 0,80 | Power des Stabilitaetstests gegen Abfall auf 0 an der MDE |
|---|---|---|---|---|
| 1/2 | 2,6942 | 0,950000 | 1,0905 / 1,1741 / 0,8659 | 0,6027 |
| 1/3 | 2,1998 | 0,950000 | 1,0905 / 1,1741 / 0,8659 | 0,5601 |
| 1/4 | 1,9051 | 0,950000 | 1,0905 / 1,1741 / 0,8659 | 0,5020 |
| 1/6 | 1,5555 | 0,950000 | 1,0905 / 1,1741 / 0,8659 | 0,4110 |
| 1/10 | 1,2049 | 0,950000 | 1,0905 / 1,1741 / 0,8659 | 0,3079 |

- **OC-Zahlen reproduziert:** MDE = (2,8070 + 1,0031) sqrt(r) = 3,8102 sqrt(r) SE_12; 1,0905 / 1,1741 fuer jedes r;
  alpha 0,002375; PASS bei Effekt nur aelter 0,0729 / 0,0128 (1 / 2 MDE, r 1/2), 0,2591 / 0,0489 (r 1/4) [R, (0)].
  Monte-Carlo-Gegenprobe (ein Blick): Max/N_fix 1,0915, q 0,9495, alpha 0,00235 [R, (4)].
- **Korrektur am Wortlaut von N2 (4):** "Power 0,95" ist 1 - alpha_stab = P(Stabilitaet haelt | kein Abfall), keine
  Power. Die Power gegen einen vollen Abfall an der MDE liegt bei 0,6027..0,3079 und faellt mit der Konfirmationslaenge.
- **Niveau als Stellschraube:** alpha_stab 0,10 -> Daten x1,2185 gegen gepoolt (x1,3119 gegen C.10 je 0,80), PASS
  nur aelter 0,0496 / 0,0027 (r 1/2); 0,15 -> x1,4356; **0,20 -> unerreichbar** (1 - alpha_stab <= 0,80) [R].

### 2.3 Ungleiche Varianzen: q ist nicht pauschal 0,95 [R]

| r | k 0,5 | k 0,7 | k 0,85 | k 1 | k 1,25 | k 1,5 | k 2 |
|---|---|---|---|---|---|---|---|
| 1/2: q an der MDE / Datenfaktor gegen gepoolt (gleiches k) | 0,9413 / 1,1093 | 0,9430 / 1,1055 | 0,9460 / 1,0991 | 0,9500 / 1,0905 | 0,9579 / 1,0743 | 0,9658 / 1,0588 | 0,9789 / 1,0351 |
| 1/2: realisierte Power bei Planung mit q 0,95 | 0,7923 | 0,7939 | 0,7965 | 0,8000 | 0,8065 | 0,8126 | 0,8226 |
| 1/4: q / Faktor | 0,9415 / 1,1089 | 0,9436 / 1,1043 | 0,9464 / 1,0981 | 0,9500 / 1,0905 | 0,9567 / 1,0767 | 0,9635 / 1,0633 | 0,9752 / 1,0415 |

Bei k 0,7..1,5 liegt der Datenfaktor bei 1,0588..1,1055 und die realisierte Power bei Planung mit q 0,95 bei
0,7939..0,8126 [R]. [U] Planung mit q = 0,95 (ein Blick) ist zulaessig; k aus der Vorperiode ist als
Sensitivitaetszeile Pflicht; liegt k unter 0,7, wird mit dem exakten q geplant.

### 2.4 q als Funktion von r und Blickzahl (O'Brien-Fleming, alpha 0,0025, gleichverteilte Blicke) [R, (4)]

| Blicke K | r 1/2: last / each_cont / each_term | r 1/3 | r 1/4 |
|---|---|---|---|
| 1 | 0,9495 (MC; exakt 0,95) | 0,9495 | 0,9495 |
| 2 | 0,9834 / 0,9834 / 0,9834 | 0,9719 / 0,9708 / 0,9664 | 0,9679 / 0,9669 / 0,9623 |
| 3 | 0,9901 / 0,9863 / 0,9711 | 0,9986 / 0,9967 / 0,9807 | 0,9935 / 0,9916 / 0,9746 |
| 4 | 0,9934 / 0,9918 / 0,9766 | 0,9974 / 0,9959 / 0,9812 | 1,0000 / 0,9997 / 0,9897 |

q = P(PASS) / P(gepoolte Grenze irgendwann gekreuzt) am Design-Effekt. Bei mehreren Blicken ist q nicht 0,95, sondern
0,96..1,00; die Kostenquote ist daher je Blickplan aus der Tabelle zu nehmen (Abschnitt 4).

## 3. Schutzwirkung (ein Blick, exakt) [R, (3)]

P(PASS) bei Effekt nur im aelteren Teil (Vielfache der **eigenen** MDE der Regel), abklingend (juengster Teil halber
Effekt, 1 MDE), nur im juengsten Teil (1 MDE), und der schlechteste Fall ueber alle Effektgroessen:

| r | Regel | MDE (SE_12) | nur aelter 0,5 / 1 / 1,5 / 2 MDE | abklingend | nur juengst | sup nur aelter (bei SE_12) |
|---|---|---|---|---|---|---|
| 1/2 | Screen 0,05 (a) | 2,7603 | 0,0154 / 0,0394 / 0,0492 / 0,0500 | 0,3333 | 0,1957 | 0,0500 |
| 1/2 | Screen 0,20 (a') | 2,5992 | 0,0250 / 0,1009 / 0,1776 / 0,1986 | 0,4327 | 0,1662 | 0,2000 |
| 1/2 | **Stabilitaet (c)** | 2,6942 | 0,0241 / 0,0729 / 0,0586 / 0,0128 | 0,3931 | 0,1835 | **0,0787** (3,148) |
| 1/3 | Screen 0,05 / 0,20 / (c) | 2,5588 / 2,1992 / 2,1998 | (c): 0,0480 / 0,1736 / 0,1238 / 0,0254 | (c) 0,4971 | (c) 0,0621 | 0,0500 / 0,2000 / **0,1839** |
| 1/4 | Screen 0,05 | 2,5025 | 0,0272 / 0,0494 / 0,0500 / 0,0500 | 0,3436 | 0,0588 | 0,0500 |
| 1/4 | Screen 0,20 | 1,9953 | 0,0494 / 0,1677 / 0,1993 / 0,2000 | 0,4889 | 0,0350 | 0,2000 |
| 1/4 | **Stabilitaet (c)** | 1,9051 | 0,0667 / 0,2591 / 0,1892 / 0,0489 | 0,5564 | 0,0318 | **0,2741** (2,158) |
| 1/6 | (c) | 1,5555 | 0,0919 / 0,3791 / 0,3059 / 0,1160 | 0,6217 | 0,0149 | **0,4042** |
| 1/10 | (c) | 1,2049 | 0,1179 / 0,5074 / 0,4676 / 0,2607 | 0,6797 | 0,0076 | **0,5501** |

Mit der Effektskala der OC (Vielfache der MDE von (a)) ergeben sich fuer den Screen 0,05 die OC-Zahlen
0,0154 / 0,0394 / 0,0492 / 0,05 und abklingend 0,3333 (r 1/2) [R]. Bei gemeinsamer Effektskala MDE_c (r 1/2):
nur aelter 1 / 2 MDE_c: Screen 0,05 0,0385 / 0,0500, Screen 0,20 0,1078 / 0,1991, (c) 0,0729 / 0,0128.

Lesart [U, gestuetzt auf R]:
- Der Stabilitaetstest verwirft einen vollen Abfall mit 0,80 erst ab 2,4865 / sqrt(1-r) SE_12: 3,5164 SE_12
  (= 1,3052 MDE_c, r 1/2), 2,8711 (1,5071 MDE_c, r 1/4), 2,6210 (2,1753 MDE_c, r 1/10). Sein Schutz ist in
  **absoluten** Einheiten eines 12-Monats-Fensters fest, waehrend die MDE mit der Konfirmationslaenge schrumpft.
  Genau dort, wo der Screen einen Boden setzt (lange Konfirmation, kleiner Effekt), schuetzt (c) kaum: sup
  0,0787 (r 1/2), 0,1839 (1/3), 0,2741 (1/4), 0,4042 (1/6), 0,5501 (1/10).
- "Kein Boden" und "kein Schutz an der MDE bei langer Konfirmation" sind dieselbe Eigenschaft: was ein 12-Monats-
  Fenster nicht aufloesen kann, kann es weder bestaetigen (Screen) noch widerlegen (Stabilitaetstest).
- Ab 2 MDE schuetzt (c) bis r 1/6 besser als der Screen 0,20 (r 1/6: 0,1160 gegen 0,2000; bei r 1/10 nicht mehr: 0,2607)
  und bei r 1/2 auch besser als der Screen 0,05 (0,0128 gegen 0,0500).
- Effekt nur im juengsten Teil: (c) laesst ihn wie gepoolt durch (0,1835 bei r 1/2; der Screen 0,05 0,1957).

## 4. Gruppensequentielle Fuehrung [R, (4)/(4b)]

Modell: Brownsche Bewegung auf der Informationsskala, OBF-Grenze B >= C auf der B-Skala (C aus exakter
Gitterintegration: K 1 2,8070; 2 2,8080; 3 2,8200; 4 2,8320; Monatsplaene 2,8820 / 2,8860 / 2,8880), juengster
Teil = letzte 12 Monate vor dem Blick (Anteil r der Endinformation), an Blicken ohne aelteren Teil entfaellt der Test.
Varianten: **last** (nur am letzten Blick; Zwischenstopps nur gepoolt), **each_cont** (an jedem Wirksamkeits-Stopp;
verwirft er, wird nicht gestoppt, weiter zum naechsten Blick), **each_term** (an jedem Wirksamkeits-Stopp; verwirft
er, endet die Konfirmation mit FAIL). Design: maximale Information so, dass P(PASS) = 0,80.

### 4.1 Gleichverteilte Blicke, K 4 (Information in N_fix = Information des festen gepoolten Tests)

| Variante | r | Max / N_fix | alpha_eff (MC) | E[N bei H1] | E[N bei H0] | q | mit Futility Z < 0 (Blicke 1-3): Max / E[N H1] / E[N H0] |
|---|---|---|---|---|---|---|---|
| ohne Stabilitaetstest | - | 1,0079 | 0,00247 | 0,8716 | 1,0078 | 1 | (OC: 1,0327 / 0,8627 / 0,5651) |
| last | 1/2 / 1/3 / 1/4 | 1,0184 / 1,0120 / 1,0079 | 0,00242 / 0,00245 / 0,00247 | 0,8784 / 0,8742 / 0,8716 | 1,0183 / 1,0118 / 1,0078 | 0,9934 / 0,9974 / 1,0000 | - |
| each_cont | 1/2 / 1/3 / 1/4 | 1,0210 / 1,0144 / 1,0084 | 0,00240 / 0,00244 / 0,00246 | 0,8836 / 0,8794 / 0,8742 | 1,0209 / 1,0143 / 1,0083 | 0,9918 / 0,9959 / 0,9997 | 1,0468 / 0,8756 / 0,5724 (r 1/2) |
| **each_term** | 1/2 / 1/3 / 1/4 | 1,0470 / 1,0389 / 1,0245 | 0,00240 / 0,00243 / 0,00246 | 0,8970 / 0,8918 / 0,8824 | 1,0468 / 1,0388 / 1,0244 | 0,9766 / 0,9812 / 0,9897 | 1,0745 / 0,8904 / 0,5876 (r 1/2); 1,0664 / 0,8851 / 0,5832 (1/3); 1,0515 / 0,8751 / 0,5750 (1/4) |
| Screen 0,05 an jedem Stopp (a) | 1/2 | 1,0702 | 0,00211 | 0,9127 | 1,0701 | 0,9640 | (OC 1,0695 / 0,9125) |

In N_0,05-Einheiten: each_term E[N bei H1] 1,9315 / 1,9202 / 1,9000 (r 1/2 / 1/3 / 1/4), gegen C.10 gemeinsam 0,80
x0,7123 / x0,7081 / x0,7007, gegen C.10 je 0,80 x0,9657 / x0,9601 / x0,9500; gegen GSD ohne Stabilitaetstest E[N]
x1,0292 / x1,0232 / x1,0124, Maximum x1,0387 / x1,0307 / x1,0165 (Screen 0,05: x1,0472 / x1,0618) [R].
**Die "+9 % Daten" gelten nur fuer einen Blick**; mit vier gleichverteilten OBF-Blicken kostet (c) im Erwartungswert
x1,0124..1,0292 [R].

### 4.2 Warum der Test an Blicken wenig beisst [R, (7)]

Ein Pfad, der die konstante B-Grenze erstmals am Blick k kreuzt, hatte am Blick davor B < C und hat jetzt B >= C:
der juengste Zuwachs ist durch die Auswahl nach oben verzerrt. Faellt der vorige Blick genau auf den Beginn des
juengsten Teils (K 4, r 1/4, letzter Blick), folgt deterministisch z_D > -C sqrt(r/(1-r)) = -1,6351 > -1,6449: der
Test **kann** dort nicht verwerfen; daher q 1,0000 fuer "last" bei r 1/4. "Nur am letzten Blick" (N2 (5)) ist damit
fast leer und laesst alle Zwischenstopps ungeprueft [U].

### 4.3 Veraltete PASS (Effekt nur bis Info-Zeit t0; PASS an einem Blick, dessen juengstes Fenster effektfrei ist)

| K 4, gleichverteilt | ohne | last | each_cont | each_term | Screen jeder Stopp |
|---|---|---|---|---|---|
| r 1/2, t0 0,5, 1 MDE: P(PASS) / veraltet | 0,2062 / 0,0586 | 0,1901 / 0,0398 | 0,1856 / 0,0414 | 0,1909 / 0,0400 | 0,1792 / 0,0179 |
| r 1/2, t0 0,5, 2 MDE | 0,9286 / 0,0152 | 0,9215 / 0,0040 | 0,9188 / 0,0045 | 0,9272 / 0,0035 | - |
| r 1/3, t0 0,5, 2 MDE | 0,9286 / 0,0152 | 0,9276 / 0,0126 | 0,8958 / 0,0193 | 0,8930 / 0,0113 | - |
| r 1/4, t0 0,5, 1 MDE | 0,2062 / 0,1273 | 0,2062 / 0,1273 | 0,1990 / 0,1239 | 0,1972 / 0,1192 | (OC: 0,0477 veraltet) |
| r 1/4, t0 0,5, 2 MDE | 0,9286 / 0,0487 | 0,9286 / 0,0487 | 0,9027 / 0,0547 | 0,8930 / 0,0366 | - |

Monats-Blickplaene der Lesart B (Zone V 24 Monate + vier K-Quartalsblicke; Effekt nur in den 24 V-Monaten;
"veraltet" = PASS an Blicken ab Monat 36) [R, (4b)]:

| Plan (Monate) | Variante | Max / N_fix | E[N bei H1] | q | 1 MDE: P(PASS) / veraltet | 2 MDE: P(PASS) / veraltet |
|---|---|---|---|---|---|---|
| 27, 30, 33, 36 | ohne / each_cont / **each_term** / Screen | 1,0184 / 1,0260 / **1,0810** / 1,1266 | 0,8705 / 0,8797 / 0,9139 / 0,9592 | 1 / 0,9951 / 0,9643 / 0,9426 | 0,4256/0,0286; 0,3972/0,0271; 0,4066/0,0234; 0,3574/0,0078 | 0,9944/0,0007; 0,8193/0,0011; 0,7926/0,0002; 0,9590/0,0002 |
| 30, 33, 36, 39 | dto. | 1,0207 / 1,0277 / **1,0842** / 1,1520 | 0,8791 / 0,8877 / 0,9243 / 0,9904 | 1 / 0,9954 / 0,9639 / 0,9327 | 0,3448/0,0599; 0,3033/0,0642; 0,2987/0,0495; 0,2184/0,0236 | 0,9812/0,0054; 0,5486/0,0234; 0,4977/0,0014; 0,7139/0,0064 |
| 33, 36, 39, 42 | dto. | 1,0202 / 1,0271 / **1,0857** / 1,1762 | 0,8851 / 0,8937 / 0,9329 / 1,0208 | 1 / 0,9955 / 0,9626 / 0,9229 | 0,2794/0,0907; 0,2338/0,1043; 0,2136/0,0742; 0,1250/0,0427 | 0,9553/0,0231; 0,3292/0,1094; 0,2101/0,0055; 0,3135/0,0358 |

Befunde [R]: (i) **each_cont kann veraltete PASS erhoehen** (0,1094 gegen 0,0231 ohne Test, Plan 33..42, 2 MDE): ein
Abfall, der an einem frueheren Blick erkannt wird, verhindert dort den zeitgerechten Stopp und gibt dem veralteten
Effekt an spaeteren Blicken neue Chancen. each_term schliesst das aus (0,0055). (ii) Im Monats-Plan beisst der Test
mehr als bei gleichverteilten Blicken (q 0,9626..0,9643, Max 1,0810..1,0857 gegen 1,0184..1,0207 N_fix ohne Test), weil
schon der erste Blick einen aelteren Teil von 15..21 Monaten hat. (iii) Der Screen schuetzt an Blicken weiter am staerksten
(veraltet 0,0078..0,0427 bei 1 MDE), kostet aber Max 1,1266..1,1762 und behaelt den Boden. Die alpha-Werte der
Monatsplaene (MC, 500.000 Pfade: 0,00249..0,00261 fuer ohne/last/each) liegen im Binomialrauschen um 0,0025
(Grenze aus dem Gitter exakt).

Niveau an Blicken (each_term, K 4): alpha_stab 0,10: Max 1,1049 / E[N] 0,9336 / veraltet 0,0294 (r 1/2, t0 0,5,
1 MDE), r 1/4: 1,0621 / 0,9067 / 0,1069; alpha_stab 0,20: 1,2786 / 1,0361 / 0,0161 (r 1/2) und 1,2087 / 0,9962 /
0,0841 (r 1/4) [R, (4b)].

### 4.4 Empfehlung zur Fuehrung [U]

Stabilitaetstest an **jedem** Wirksamkeits-Stopp, an dem ein aelterer Teil existiert, mit **terminaler** Verwerfung
(each_term): verwirft er, endet die Konfirmation mit FAIL ("juengster Teil faellt ab", kein spaeterer Blick). Gruende:
(a) "nur am letzten Blick" ist fast leer (4.2) und laesst Zwischenstopps ungeprueft; (b) Weiterlaufen erzeugt neue
Chancen fuer veraltete PASS (4.3 (i)); (c) eine signifikante Verschlechterung ist ein Befund gegen die aktuelle
Gueltigkeit und soll nicht durch Abwarten ueberschrieben werden. Kosten: Max x1,0165..1,0387 (gleichverteilt) bzw.
1,0810..1,0857 N_fix (Monatsplaene); alpha bleibt <= 0,0025. **Offen zu sagen:** auch so schuetzt (c) an Blicken gegen
veraltete Effekte deutlich schwaecher als der Screen (r 1/4, t0 0,5: 0,1192 gegen OC 0,0477).

## 5. Nuisance und schwere Raender [R, (5)]

Zwei Teile mit n_J 40 / 52 Clustern und r 1/2 / 1/4 (n_A 40 / 52 / 120 / 156), 200.000 Pfade je Zelle; Verteilungen:
normal; t(7) (Kurtosis 5); t(4,857) (Kurtosis 10); t(5,2) (Exzess 5); t(4,6) (Exzess 10); Fernandez-Steel-t(7) mit
Schiefe +-1,0543. Gemeinsame Regel mit t-Grenzen: gepoolt t_{n-1}(0,9975), Stabilitaet Welch.

| Groesse (nominal) | symmetrisch, alle n und r | schief +1,05 (r 1/4) | schief -1,05 (r 1/4) | schief, r 1/2 |
|---|---|---|---|---|
| alpha_stab z-Grenze (0,05) | 0,0507..0,0527 | 0,0604 / 0,0618 | 0,0441 / 0,0441 | 0,0508..0,0522 |
| alpha_stab Welch-t (0,05) | **0,0491..0,0506** | 0,0586 / 0,0597 | 0,0416 / 0,0423 | 0,0491..0,0506 |
| q mit t-Grenzen (0,95) | 0,9488..0,9511 | 0,9401 / 0,9412 | 0,9578 / 0,9579 | 0,9493..0,9510 |
| Power gegen Abfall, Welch (0,80) | 0,7923..0,8014 | 0,7811 / 0,7853 | 0,8112 / 0,8113 | 0,7946..0,7984 |

- Kurtosis 5..13 aendert alpha_stab mit Welch-Grenze nicht messbar; die z-Grenze ist bei n_J 40 leicht liberal
  (bis 0,0527). Bei r 1/2 (gleiche n) ist D symmetrisch verteilt, Schiefe wirkt nicht; bei ungleichen n verschiebt sie
  alpha_stab um +-0,01 [R].
- Die gemeinsame Power mit t-Grenzen (0,7764..0,7917 symmetrisch; schief 0,7505..0,8145) und das gemeinsame alpha
  (z.B. normal n_J 52, r 1/2: 0,00289 mit z-, 0,00247 mit t-Grenzen; schief negativ bis 0,00525) werden vom
  **gepoolten** Test bestimmt (OC (e)), nicht vom Stabilitaetstest [R].
- **Autokorrelation** AR(1) phi 0,3 (n_J 52, 100.000 Pfade; c 1,8336): alpha_stab naiv 0,1155 / 0,1138, SB-max
  Block 4 0,0850 / 0,0798, SB-max mit Welch 0,0831 / 0,0778, analytisches c 0,0531 / 0,0515 (r 1/2 / 1/4). Analytisch
  q = Phi(1,6449 sqrt(c_benutzt/c_wahr)): 0,8863 (naiv bei c 1,857), 0,9156 (c 1,3). Eine unterschaetzte
  Abhaengigkeit **kostet Power** (q sinkt), erhoeht aber das alpha der Gesamtregel nicht (das bestimmt der gepoolte
  Test: naiv 0,02093, SB-max 0,00967, c analytisch 0,00338 bei r 1/2) [R].
- [U] Pflichten: Welch-t-Grenze (df aus den Clusterzahlen beider Teile); Teil-SE mit derselben Blocklaengen- bzw.
  c-Regel wie der gepoolte Test (c_bind aus der gemessenen Autokorrelation, N2 (7)); Schiefe-Bericht je Teil, wenn
  n_J != n_A.

## 6. Beispiele mit Akten-Zahlen [R, (6)]

### 6.1 A2 (SE P2'' 7,34 / 7,58 zentral, 8,25 / 8,52 stress; Gate-(4)-Faktor 0,9025; exakte Konjunktion)

Modell der OC (g) unveraendert (drei Kontraste plus Null-Bedingung, Stress bindend, skalierte Null, gepoolt alpha
0,0025 je Bedingung), erweitert um den juengsten Teil (12 Monate, Kovarianz W2) und den aelteren Teil (Kovarianz so,
dass die gepoolte Kovarianz der OC-Konvention entspricht; bei 24 Monaten exakt W1 / W2). Stabilitaetstest auf dem
P2''-Kontrast, SE(D) stress 11,860 bp bei 24 Monaten.

| T (Monate) | Q6 (a) Screen | Q6 (c) exakt | Q6 (c) unter Unabhaengigkeit, Ziel 0,8/0,95 (OC) | gepoolt ohne | q an der MDE | SQ (c) / SQ (a) |
|---|---|---|---|---|---|---|
| 24 | **28,053** | **28,969** | 28,985 | 27,176 | 0,9503 | 1,4429 / 1,3551 |
| 27 | 27,003 | 27,314 | 27,331 | 25,622 | 0,9504 | 1,4429 / 1,3388 |
| 30 | 26,235 | 25,913 | 25,926 | 24,310 | 0,9503 | 1,4427 / 1,3259 |
| 36 | 25,248 | 23,657 | 23,664 | 22,195 | 0,9502 | 1,4422 / 1,3077 |
| 42 | 24,733 | 21,901 | 21,910 | 20,549 | 0,9503 | 1,4420 / 1,2977 |
| 60 | 24,330 | 18,325 | 18,331 | 17,193 | 0,9502 | 1,4420 / 1,2898 |
| 120 | 24,305 | 12,959 | 12,962 | 12,158 | 0,9502 | 1,4416 / 1,2895 |

- Unabhaengigkeit traegt auch in der A2-Konjunktion (q 0,9501..0,9504; exakt 28,969 gegen OC-Naeherung 28,985 bp bei
  24 Monaten) [R].
- **Bei zwei Fenstern ist (c) fuer A2 teurer als (a)** (28,969 gegen 28,053 bp; gepoolt ohne 27,176) [R]. Deutung [V]:
  der Screen auf W2 ist mit der gepoolten P2''-Bedingung und den uebrigen Bedingungen der Konjunktion positiv
  korreliert und kostet dort wenig, der unabhaengige Stabilitaetstest kostet die volle Quote 0,95. Ab 30 Monaten ist
  (c) besser (25,913 gegen 26,235 bp) [R]. Boden unter (a): 24,304 bp.
- Strenge-Quotient unter (c) 1,4429 (Grundfassung (c) 20,077 bp bei 24 Monaten) - ueber 1,3, Nutzer-Vorlage nach E8 (b)
  unter beiden Varianten [R].
- Schutz bei 24 Monaten, gleiche Effektgroesse fuer beide Regeln (Vielfache der MDE (c)): nur W1-Effekt 1 / 2 MDE:
  (a) 0,0329 / 0,0453, (c) 0,0416 / 0,0005; bei 42 Monaten (a) 0,0411 / 0,0453, (c) 0,1556 / 0,0029 [R].

**Fruehester Konfirmationszeitpunkt (Lesart B, Registrierung 2027-01-01).** F1 (BTC/ETH): Zone V 2024-07..2026-06
(24 Monate), Luecke 2026-07..09 (geoeffnet, N1 (2)), reine K-Daten ab 2026-10-01; bei Registrierung liegen 27 Monate vor.

| SESOI | (a) Screen | (c) Stabilitaet | OC-Angabe (Daten durchgehend ab 2024-07) |
|---|---|---|---|
| 22 bp (Taker) | nie (Boden 24,304) | 41,62 Monate -> **2028-04** | (c) 2028-01 |
| 25 bp | 38,76 Monate -> **2028-01** | 32,23 Monate -> **2027-07** | (a) 2027-10, (c) 2027-04 |

**Korrektur [R]:** Die OC-Termine fuer A2 (h) zaehlen die Monate ab 2024-07 ohne die F1-Luecke; mit Zone K fuer BTC/ETH
ab 2026-10-01 (N1 (2), N2 (8)) liegen sie drei Monate spaeter. DEC-104 N2 (4)/(9) ("42 Monate: Lesart B 2028-01";
"2027-04 bei 25 bp") sind entsprechend zu lesen.

### 6.2 Klasse W (Wochen-IC; SE_12 = SD / sqrt(52); F2 durchgehend ab 2024-07, bei Registrierung 30 Monate)

| SD je Woche / SESOI | MDE80 bei 104 / 130 Wochen: (a) / (c) | (a): Boden; Termin | (c): T; Termin; GSD-Maximum (each_term) |
|---|---|---|---|
| 0,09 / 0,040 | 0,0345 / 0,0328; 0,0336 / 0,0301 | 0,0310; 15,66 Mon. -> 2027-01 | 16,96 Mon. -> 2027-01; 17,76 Mon. -> 2027-01 |
| 0,13 / 0,040 | 0,0498 / 0,0474; 0,0486 / 0,0434 | 0,0448; **nie** | 35,39 Mon. -> **2027-07**; 36,77 Mon. -> 2027-08 |
| 0,09 / 0,0085 (Dezil) | wie oben | 0,0310; nie | 375,6 Mon. (31,3 Jahre) -> 2055-11 |
| 0,13 / 0,0085 (Dezil) | wie oben | 0,0448; nie | 783,6 Mon. (65,3 Jahre) -> 2089-11 |

[V] Die Dezil-SESOI 0,0085 ist fuer Tagesumschlag hergeleitet (PRD_ANALYSE Nachtrag 3); die Paarung mit der
Wochen-IC-SD ist eine Modellannahme des Auftrags. Auch ohne Boden ist ein Effekt dieser Groesse mit Wochen-IC-SD
0,09..0,13 auf keiner realen Laenge testbar; (c) aendert daran nichts. [V] GSD-Maximum fuer Klasse W mit dem Faktor
aus 4.1 uebertragen (r ausserhalb 1/4..1/2 auf den Rand gesetzt).

## 7. Registrierungstext (Vorschlag)

### 7.1 Pflichtzeilen PZ-16 `screen` / `stability_test` (YAML-Template 3.1, `decision_rule`) [U]

```yaml
decision_rule:                                  # PZ-15/PZ-16; DEC-104 E2 in der Fassung von Nachtrag <n> (Variante c)
  variante: c                                   # P-2 (c); bis zum Nutzerentscheid gilt (a)
  alpha_test: 0.0025                            # fest je Test
  z_krit: 2.8070                                # gepoolt einseitig; t-artig bei geschaetzter SE (N2 (7))
  screen: null                                  # (a) entfaellt unter (c)
  stability_test:
    statistik: "D = Mittel(juengster Teil) - Mittel(aelterer Teil), in registrierter Richtung"
    juengster_teil: "letzte 12 Monate vor dem Blick (Zone K: letzte vier Quartale; Lesart B: inkl. V-Ende)"
    aelterer_teil: "alle uebrigen Konfirmationsdaten der Registrierung"
    se: "sqrt(SE_J^2 + SE_A^2); je Teil nach VR-b09 (max(naiv, Bootstrap), c_bind aus gemessener Autokorrelation)"
    h0: "mu_J >= mu_A (kein Abfall)"
    grenze: "Z_D < t_{df_WS}(0.05) -> verworfen (Welch-Satterthwaite)"
    alpha_stab: 0.05
    entfaellt_wenn: "Konfirmationsdaten am Blick <= 12 Monate"
    an_blicken: "jeder Wirksamkeits-Stopp mit aelterem Teil; verworfen -> FAIL (terminal)"
    kostenquote_q: <0.95 bei einem Blick | Wert aus stab_results.json s4_gsd / s4b_blickplaene je Blickplan>
    sensitivitaet_k: "SD-Verhaeltnis juengst/aelter aus der Vorperiode; bei k < 0.7 exaktes q"
    ref: "stab/calc/stab_sim.py (s2, s4, s4b)"
  power_target_gemeinsam: 0.80                  # gepoolte Power 0.80 / q
  mde_faktor: <z_krit + Phi^-1(0.80 / q)>       # 3.8102 bei q 0.95; nie Schwelle
oc_line:                                        # PZ-21, ergaenzt
  p_pass_nur_aelter_1mde: <exakt oder Simulation>   # Schutzzeile; Screen-Vergleich als Bericht
report_line_stabilitaet: [D, se_D, ci95_D, z_D, df_ws, verworfen]   # DEC-104 E6 Bericht
```

### 7.2 Wortlaut fuer einen DEC-104-Nachtrag (Entwurf; Entscheider N) [U]

> **DEC-104 Nachtrag <n> (Entwurf): Konfirmationsregel E2, Variante (c) - registrierter Stabilitaetstest statt
> REZENZ-Screen.** (1) PASS genau dann, wenn der gepoolte einseitige Test ueber alle Konfirmationsdaten die Grenze
> 2,8070 (t-artig) erreicht **und** der Stabilitaetstest nicht verwirft: D = Mittel des juengsten Teils (letzte
> 12 Monate bzw. vier Quartale vor dem Blick) minus Mittel des aelteren Teils (alle uebrigen Konfirmationsdaten) in
> registrierter Richtung, SE(D) aus getrennt geschaetzten Teil-SE nach VR-b09, Verwerfung bei D/SE(D) unter dem
> 0,05-Quantil der Welch-t-Verteilung. Bei hoechstens 12 Monaten Konfirmationsdaten entfaellt der Test.
> (2) Blicke: an jedem Wirksamkeits-Stopp mit aelterem Teil; Verwerfung beendet die Konfirmation mit FAIL.
> (3) Power-Planung: gemeinsame Power 0,80 an der SESOI, gepoolte Power 0,80/q mit q = 0,95 bei einem Blick und q aus
> der Herleitung je Blickplan; Sensitivitaetszeile fuer das SD-Verhaeltnis der Teile. (4) Bericht: D, SE(D), CI95 und
> die Schutzzeile P(PASS bei Effekt nur im aelteren Teil, 1 MDE) in der OC-Zeile (E8 (a)). (5) DEC-104 E6 Satz 1
> ("REZENZ als Screen") gilt unter (c) nicht; der Stabilitaetstest ist Gate und Bericht. (6) Was nicht folgt: kein
> Verdikt, keine Registrierung; alpha je Test unveraendert.
> **Etikett:** gegenueber (a) **Lockerung** (kein Boden; REZENZ-Schutz an der MDE schwaecher: P(PASS bei Effekt nur
> im aelteren Teil) im schlechtesten Fall 0,0787 (r 1/2) bis 0,5501 (r 1/10) statt <= 0,05; an Blicken veraltete
> PASS bis 0,1192 statt 0,0477 bei r 1/4); gegenueber "gepoolt ohne Screen" **Verschaerfung** (zusaetzlicher Test,
> Daten x1,0905 bei einem Blick, Max x1,0165..1,0387 an vier OBF-Blicken); **alpha je Test unveraendert** 0,0025
> (alpha_eff 0,002375 bei gleicher Varianz, <= 0,0025 immer); Richtung Testbarkeit; **Entscheider N**; prospektiv
> ab Kohorte 1. Zugleich zu berichtigen (Orchestrator, neutral): N2 (4) "Power 0,95" -> "Kostenquote q = 1 -
> alpha_stab"; N2 (5) "am letzten Blick" -> "an jedem Wirksamkeits-Stopp, terminal"; A2-Termine N2 (4)/(9) drei Monate
> spaeter (F1-Zone K ab 2026-10-01).

## 8. Was folgt / Was nicht folgt

**Was folgt [U, gestuetzt auf R]:**
1. Die Variante (c) ist sauber definierbar, haelt alpha <= 0,0025 unter jeder Varianzlage und hat keinen Boden; die
   OC-Kennzahlen fuer einen Blick (0,002375; x1,0905; x1,1741) sind bestaetigt.
2. Ihr REZENZ-Schutz ist absolut (2,4865 / sqrt(1-r) SE_12 mit 0,80), nicht relativ zur MDE. Fuer lange
   Konfirmationen und an gruppensequentiellen Blicken naehert sich (c) dem gepoolten Test ohne REZENZ. Die
   Nutzerentscheidung lautet damit nicht "Screen oder gleich guter Test ohne Boden", sondern "Boden (a) oder schwacher
   REZENZ-Schutz (c)" - mit (a') Screen 0,20 als Zwischenstufe (Boden 1,6832 SE_12, Schutz <= 0,20; OC (a) Nr. 6).
3. Fuer die Fuehrung an Blicken: jeder Stopp, terminal; Kostenquote je Blickplan aus der Tabelle (q 0,9626..0,9897
   fuer each_term bei K 4 und in den Monatsplaenen), nicht pauschal 0,95.
4. Korrekturen an der Akte: "Power 0,95" (N2 (4)); "+9 % Daten" nur fuer einen Blick; "am letzten Blick" (N2 (5)) ist
   fast wirkungslos; A2-Termine drei Monate spaeter (2028-04 bei 22 bp, 2027-07 bei 25 bp; unter (a) 2028-01 bei
   25 bp); A2 bei 24 Monaten unter (c) 28,969 bp und damit teurer als (a); F3-Hinweis zu R5 fuer T <= 12 Monate.

**Was nicht folgt:**
- Kein Verdikt ueber einen Markteffekt, keine Registrierung, keine Marktdaten, keine Siegeldatei, keine Aenderung im
  Repository.
- Alle Zahlen sind Fehlerraten und Aufloesungsgrenzen unter Modellannahmen (Normalitaet bzw. die simulierten
  Verteilungen, Brownsche Bewegung mit gleichmaessigem Informationszuwachs, A2-Gauss-Modell der OC mit
  Cov(P_i, P_j) = 0), keine Effektgroessen.
- Die Wahl zwischen (a), (a') und (c) ist eine Nutzerfrage; diese Herleitung liefert die Rechnung, nicht die Abwaegung
  zwischen Regime-Schutz und Testbarkeit.
- Monte-Carlo-alpha-Werte (MC 0,00235..0,00261) tragen Binomialrauschen; Unterschiede in der vierten Nachkommastelle
  sind nicht belastbar. Termine haengen an Lesart B, an der F1-Zonenregel und an SESOI-Setzungen; keine Zusagen.

## Kurzfassung (<= 12 Zeilen)

1. Statistik: D = Mittel(letzte 12 Monate) - Mittel(aeltere Konfirmationsdaten), Welch-SE, einseitig 0,05 gegen Abfall; entfaellt bei <= 12 Monaten.
2. Gleiche Varianz: D unabhaengig vom gepoolten Mittel; alpha 0,002375, q 0,95, Daten x1,0905 / x1,1741 (OC bestaetigt), kein Boden.
3. Ungleiche Varianz (k 0,5..2): alpha 0,000989..0,0025, q 0,9413..0,9789; Planung mit q 0,95 gibt Power 0,7939..0,8126 (k 0,7..1,5).
4. Schutz absolut: Abfall >= 2,4865/sqrt(1-r) SE_12 erkannt; P(PASS | Effekt nur aelter) max 0,0787 (r 1/2) .. 0,5501 (r 1/10) statt <= 0,05.
5. NI-Formen f 0,5: Nachweis hat Boden 4,9729 SE_12, Marge schuetzt nicht (sup bis 0,7883) - beide verworfen.
6. GSD: q 0,9623..1,0000; "nur letzter Blick" fast leer (q bis 1,0000, Schranke -1,6351); Empfehlung: jeder Stopp, terminal.
7. each_term K 4: Max x1,0165..1,0387, E[N] x1,0124..1,0292 gegen GSD ohne; Monatsplaene V+K Max 1,0810..1,0857 N_fix.
8. Veraltete PASS an Blicken: (c) 0,0400 / 0,1192 gegen Screen 0,0179 / 0,0477 (r 1/2 / 1/4); each_cont kann sie erhoehen.
9. Raender: Welch alpha_stab 0,0491..0,0506 (Kurtosis 5..13); AR(1) 0,3 naiv q 0,8863 - kostet Power, nicht alpha.
10. A2: (c) 28,969 bp bei 24 Mon. (> (a) 28,053); 22 bp -> 2028-04, 25 bp -> 2027-07 (OC 3 Monate zu frueh: F1-K ab 2026-10).
11. Klasse W SD 0,13 / 0,040: (c) 2027-07 statt nie; Dezil-SESOI 0,0085: (c) 31,3 / 65,3 Jahre.
12. Vorschlag YAML/DEC-Text in 7; Etikett: Lockerung gg. (a), Verschaerfung gg. gepoolt, alpha unveraendert, N.
