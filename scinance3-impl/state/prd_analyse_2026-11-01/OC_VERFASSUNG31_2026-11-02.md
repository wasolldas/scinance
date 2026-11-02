# Gesamt-Operationscharakteristik des Pakets "Verfassung 3.1" (Stand 2026-11-02)

> **Rolle:** Herleitung mit eigenem Code (nur Formeln und Simulation). **Keine Marktdaten, keine Siegeldatei, kein
> Harvest-Client, keine Registrierung, kein Verdikt ueber Markteffekte.** Nichts im Repository geaendert.
> **Auftrag:** `oc/BRIEF_oc_verfassung31.md` (Review-Luecke 2; Synthese 9.2 Nr. 3). Paket wie am 2026-11-02 angenommen
> (`state/PRD_ANALYSE_2026-11-01.md` 9.1, P-1..P-7 mit Default-Vorschlaegen).
> **Code und Ergebnisse:** `oc/calc/oc_sim.py` (deterministisch, Seeds 31001..31010 je Abschnitt plus Zellindex,
> `python3 -I`, nur numpy/scipy), `oc/calc/oc_results.json`, `oc/calc/oc_sim.out`. Jede Zahl dieses Textes steht in
> einer der beiden Ausgabedateien (JSON-Pfad oder Ausgabezeile des Abschnitts). Monte Carlo: >= 200.000 Pfade je Zelle
> (Abschnitt b: 1.000.000; a: analytisch plus 1.000.000; g: 2.000.000 gemeinsame Ziehungen).
> Laufzeit: 761,9 s CPU fuer das Skript, 817,2 s einschliesslich der Reproduktions-Kindprozesse (Grenze 20 min).
> **Markierungen:** [R] Rechnung (Formel oder Simulation dieses Skripts), [U] Urteil, [V] Vermutung / Modellannahme
> ohne Messung. Dezimalkomma im Text, Dezimalpunkt in den Ausgabedateien.

## Konventionen und Annahmen (gelten fuer alle Abschnitte, wo nicht anders gesagt)

- **Informationsskala [R].** Ein Test sieht Z = theta x sqrt(I) + N(0,1). "N_fix" = Information des gepoolten
  einseitigen Tests bei alpha 0,0025 und Power 0,80 (Drift 3,6487); "N_0,05" = ein Fenster bei 0,05 / 0,80 (Drift
  2,4865); C.10 je 0,80 = 2,000 N_0,05, C.10 gemeinsam 0,80 = 2,7117 N_0,05, N_fix = 2,1533 N_0,05.
- **REZENZ-Screen [Annahme].** Das juengste 12-Monats-Fenster hat den Anteil r an den Konfirmationsdaten (r = 1/2, 1/3,
  1/4 = 24, 36, 48 Monate). Homogene Varianz: Korrelation gepoolte Statistik / Screen = sqrt(r). Alternative (Vol-Regime):
  Informationsanteil r_I != r (gerechnet, Abschnitt a).
- **MDE in (a)** = Effekt, bei dem P-2 (a) mit den gegebenen Daten Power 0,80 fuer die **gemeinsame** Regel hat.
- **GSD [Annahme].** OBF, 4 Blicke gleich verteilt in der Information, Grenze auf der B-Skala konstant (c 2,8320 aus
  exakter Gitterintegration, alpha 0,0025), Futility "Z < 0 an Blicken 1-3" nicht bindend kalibriert (wie Akte).
- **t(4) [Hinweis R].** t(4) hat **unendliche** Kurtosis; Exzess-Kurtosis 6 hat t(5). Gerechnet sind t(5), t(4), t(3)
  und zwei schiefe Varianten (Fernandez-Steel-t(4), Schiefe 2,4075 bzw. 1,2391), damit die Abweichung vom Auftrag
  nichts verdeckt.
- **A2 (g) [Annahme].** Nur Akten-Zahlen (`NULL_SIMULATION_A2.md` T2/T3/T4, DEC-103 N1 (6)/(8)/(9), REVIEW_A2_TEILC
  B-4). Gauss-Modell der drei Kontraste plus Null-Bedingung; Cov(P_i, P_j) = 0; Var(E) aus Klassen-SD und c_bind
  (disjunkte Klassen, keine Vereinigung, keine Lage); Korrelation Null-Bedingung / P2''-Bedingung unskaliert
  nullSD/SE (Modell des Reviews), skaliert sqrt(1 - SD_Zentrum^2/SE^2). Das Modell reproduziert alle 16 Akten-Zeilen
  bis auf die zweite Nachkommastelle (Abschnitt g); erst danach wird es fuer 3.1 extrapoliert.

## (0) Reproduktion der Vorarbeiten

Die drei Skripte laufen in `oc_sim.py` Abschnitt (0) unveraendert als Kindprozess (`python3 -I`, nur stdout, keine
Dateien); ihre volle Ausgabe steht in `oc_sim.out` und unter `reproduktion` im JSON (mit sha256).

| Skript | Ergebnis | Abweichung |
|---|---|---|
| `orch_review_check.py` | Ausgabe **identisch** mit der abgelegten `orch_review_check.out` [R] | keine |
| `review_calc.py` | alle Zahlen der Review-Nachrechnungstabelle reproduziert, u. a. OBF K 4, alpha 0,0025: c 2,832, Maximum 1,0074, E[N bei H1] 0,871, E[N bei H0] 1,007; mit Futility 1,0327 / 0,863 / 0,565; DEC-52-H0-Raten 0,00991 / 0,00847 (z 2,3263) und 0,00571 / 0,00500 (z 2,5287) [R] | keine (die Repo-Fassung hat keine .out; Vergleich gegen REVIEW_PRD_ANALYSE Abschnitt 2) |
| `gsd_fut.py` | alpha 0,0025: c 2,842, Maximum 1,016, E[N bei H1] 0,879; mit Futility 1,041 / 0,871 / E[N bei H0] 0,569 [R] | **ja, Monte-Carlo-Rauschen:** das Skript kalibriert c auf denselben 400.000 Pfaden, auf denen bei alpha 0,0025 nur wenige hundert bis tausend Ueberschreitungen liegen; c 2,842 liegt ueber dem exakten 2,8320, daher Maximum und E[N bei H1] zu hoch gegen das Gitter (1,0074 / 0,8712; Futility 1,0327 / 0,8627 / 0,5651). Mit c aus dem Gitter und 1.000.000 Pfaden: 1,0078 / 0,8717 bzw. 1,0334 / 0,8630 / 0,5653. Die Zahlen der Analyse (0,871 / 1,007) gelten; die Kritik-Zahlen "x1,02 / 0,88; x1,04" stammen aus diesem verrauschten Verfahren |

Eigene Gegenrechnung derselben Groessen in `oc_sim.py` [R]: DEC-52-H0-Rate exakt (Quadratur) 0,0099 / 0,00851 bei
z 2,3263 (Akte-MC 0,00991 / 0,00847, Differenz innerhalb des MC-Fehlers der Akte) und 0,00569 / 0,005 bei z 2,5287;
K-4-Faktoren 1,0766 / 1,3558 / 1,2593, gepoolte Power bei C.10-MDE 0,761 - identisch.

## (a) Entscheidungsregel P-2 (a) gegen C.10 und DEC-52

Regel P-2 (a): Z_pool > 2,8070 (einseitig 0,0025) **und** Z_rec > 1,6449 (juengstes 12-Monats-Fenster, einseitig 0,05),
Z_rec ist Teil von Z_pool (Korrelation sqrt(r)). Exakt per Quadratur, Monte-Carlo-Gegenprobe mit 1.000.000 Pfaden
je r stimmt auf 3 Stellen (`a.monte_carlo_1e6`).

| r (juengstes Fenster) | alpha_eff P-2 (a) | Daten fuer gemeinsame Power 0,80: gegen C.10 je 0,80 / C.10 gemeinsam 0,80 / gepoolt ohne Screen | MDE in SE_12-Einheiten |
|---|---|---|---|
| 1/2 (24 Monate) | 0,001933 | 1,2324 / 0,9089 / 1,1446 | 2,7603 |
| 1/3 (36 Monate) | 0,001424 | 1,5886 / 1,1717 / 1,4755 | 2,5588 |
| 1/4 (48 Monate) | 0,001144 | 2,0258 / 1,4941 / 1,8816 | 2,5025 |
| r -> 0 | -> 0 | - | **Boden 2,4865** |

SE_12 = Standardfehler eines 12-Monats-Fensters. Zum Vergleich C.10 je 0,80: 2,4865 SE_12 (gemeinsame Power 0,64),
C.10 gemeinsam 0,80: 2,8953 SE_12.

**Power bei 0 / 0,5 / 1 / 1,5 MDE (gleiche Daten) [R]:**

| r | P-2 (a) | gepoolt ohne Screen | C.10 (r 1/2) bzw. C.10-artig (aelterer und juengster Teil je 0,05) | DEC-52 (z 2,5287, Halbschwellen-Screens) |
|---|---|---|---|---|
| 1/2 | 0,0019 / 0,1622 / 0,8000 / 0,9930 | 0,0025 / 0,1962 / 0,8636 / 0,9988 | 0,0025 / 0,1565 / 0,7528 / 0,9875 | 0,0050 / 0,2578 / 0,8914 / 0,9985 |
| 1/3 | 0,0014 / 0,1794 / 0,8000 / 0,9858 | 0,0025 / 0,2773 / 0,9479 / 0,9999 | 0,0025 / 0,2021 / 0,7998 / 0,9858 | 0,0048 / 0,3372 / 0,9444 / 0,9990 |
| 1/4 | 0,0011 / 0,2073 / 0,8000 / 0,9825 | 0,0025 / 0,3803 / 0,9860 / 1,0000 | 0,0025 / 0,2426 / 0,8016 / 0,9825 | 0,0046 / 0,4244 / 0,9645 / 0,9991 |

Befunde:
1. **alpha_eff <= 0,0025: ja** [R]. Der Screen senkt alpha auf 0,001933 (r 1/2) bis 0,001144 (r 1/4); P-2 (a) ist auf
   der alpha-Seite strenger als C.10 (0,0025) und DEC-52 (0,005 in der DEC-94-Fassung; 0,008509 mit z 2,3263).
2. **Korrektur an der Analyse [R].** "+8 % Daten gegen C.10 je 0,80" (K-4, P-2 (a) in 9.1) gilt fuer den gepoolten Test
   **ohne** Screen (1,0766). Mit dem beschlossenen Screen und Power 0,80 auf der gemeinsamen Regel sind es Faktor
   1,2324 (+23,235 %, r 1/2), 1,5886 (+58,859 %, r 1/3), 2,0258 (+102,582 %, r 1/4); gegen den gepoolten Test ohne
   Screen +14,464 / +47,552 / +88,162 %. Gegen C.10 mit gemeinsamer Power 0,80 spart P-2 (a) bei r 1/2 (0,9089,
   -9,1083 %), kostet aber schon bei r 1/3 mehr (1,1717, +17,166 %).
3. **Struktureller Boden durch den Screen [R].** P(PASS) <= P(Z_rec > 1,6449). Power 0,80 der gemeinsamen Regel
   verlangt daher Effekt >= 2,4865 SE_12, gleich wie lang die Konfirmation ist. **P-2 (a) macht keinen Effekt
   testbar, den ein einzelnes 12-Monats-Fenster bei 0,05 nicht mit Power 0,80 sieht**; es hebt nur die
   Entscheidungs-Power von 0,64 auf 0,80. Bei 24 Monaten liegt die MDE von P-2 (a) beim 1,1101-fachen der
   C.10-je-0,80-MDE. Das Wurzelgesetz wirkt hier nicht auf die Gesamtdaten, sondern auf das feste juengste Fenster.
   Folgen fuer W und A2 in (g)/(h).
4. **Regime-Robustheit [R].** Effekt nur im aelteren Teil (juengster Teil 0), Effekt f x MDE: P-2 (a) bei r 1/2
   0,0154 / 0,0394 / 0,0492 / 0,05 (f 0,5 / 1 / 1,5 / 2), Grenzwert 0,05 = Niveau des Screens; C.10 gleich (0,0434 bei
   f 1, Grenzwert 0,05); gepoolt ohne Screen 0,1962 bei f 1 und gegen 1; DEC-52 0,1322 bei f 1, Grenzwert 0,1857
   (r 1/3: 0,2327; r 1/4: 0,2636). Die REZENZ-Logik von P-2 (a) ist so gut wie C.10; DEC-52 schuetzt schwach.
   Abklingen (juengster Teil halber Effekt, f 1): P-2 (a) 0,3333, C.10 0,3433, gepoolt 0,5480 (r 1/2).
5. **Korrelationsannahme [R].** Traegt das juengste Fenster weniger Information als sein Kalenderanteil (hoehere Vol),
   steigt der Datenbedarf steil: Informationsanteil 0,15 -> alpha 0,000792, Daten x3,0964 gegen gepoolt; 0,25 -> x1,8816;
   0,75 -> x1,0091 (`a.korrelationsannahme_infoanteil`).
6. **Alternativen zum 0,05-Screen (nur gerechnet, Entscheidung N) [R]:** Screen-Niveau alpha_s setzt Boden
   (z_s + 0,8416) SE_12 und Grenzwert falsch-PASS alpha_s: 0,10 -> Boden 2,1232, Daten x1,0576 gegen gepoolt (r 1/2);
   0,20 -> 1,6832, x1,0149; 0,50 (Vorzeichen) -> 0,8416, x1,0005. **P-6-Lesart** (REZENZ als pruefbare Hypothese:
   gepoolt 0,0025 plus registrierter Stabilitaetstest "juengster Teil faellt ab", einseitig 0,05): die beiden
   Statistiken sind unabhaengig, alpha 0,002375, Daten x1,0905 gegen gepoolt (x1,1741 gegen C.10 je 0,80) **fuer jedes
   r, ohne Boden** (MDE 2,6942 / 2,1998 / 1,9051 SE_12 bei r 1/2 / 1/3 / 1/4); Effekt nur im aelteren Teil: PASS
   0,0729 / 0,0128 (1 / 2 MDE, r 1/2), 0,2591 / 0,0489 (r 1/4) - schwaecher als der Screen genau an der MDE, staerker
   ab 2 MDE.

## (b) GSD O'Brien-Fleming, 4 Blicke, alpha 0,0025 einseitig, Power 0,80

| Variante | Maximum / N_fix | alpha_eff | E[N bei H1] | E[N bei H0] | Quelle |
|---|---|---|---|---|---|
| OBF ohne Futility | 1,0074 (MC 1,0078) | 0,00251 | 0,8712 (MC 0,8717) | 1,0073 | Gitter [R] |
| OBF, Futility Z < 0 an Blicken 1-3 | 1,0327 (MC 1,0334) | 0,00242 | 0,8627 | 0,5651 | Gitter [R] |
| zum Vergleich alpha 0,05 ohne / mit Futility | 1,0346 / 1,1979 | 0,05001 / 0,04457 | 0,8141 / 0,8303 | 1,0261 / 0,6463 | Gitter [R] |
| GSD + REZENZ-Screen an jedem Stopp, r 1/2 | 1,0695 | 0,00217 | 0,9125 | 1,0693 | MC 1e6 [R] |
| dto. mit Futility | 1,0957 | 0,00209 | 0,9054 | 0,5993 | MC [R] |
| GSD + Screen an jedem Stopp, r 1/3 / mit Futility | 1,1646 / 1,1898 | 0,00173 / 0,00166 | 0,9808 / 0,9751 | 1,1644 / 0,6509 | MC [R] |
| GSD + Screen an jedem Stopp, r 1/4 / mit Futility | 1,2378 / 1,2609 | 0,00144 / 0,00138 | 1,0375 / 1,0318 | 1,2377 / 0,6897 | MC [R] |
| GSD + Screen nur am letzten Blick, r 1/2 / 1/3 / 1/4 | 1,0678 / 1,1376 / 1,1751 | 0,00218 / 0,00181 / 0,00160 | 0,9106 / 0,9539 / 0,9764 | - | MC [R] |

- **Analyse-Zahlen bestaetigt [R]:** 0,871 / 1,007 (ohne Screen). In N_0,05-Einheiten E[N bei H1] 1,8759: gegen C.10
  gemeinsam 0,80 Faktor 0,6918 (-30,8221 %), gegen C.10 je 0,80 0,9379 (-6,2051 %) - wie Abschnitt 6 der Analyse.
- **Mit dem beschlossenen Screen [R]:** E[N bei H1] 1,9649 N_0,05 (r 1/2): gegen C.10 gemeinsam 0,80 Faktor 0,7246
  (-27,5411 %), gegen C.10 je 0,80 0,9824 (-1,7566 %, bei Power 0,80 statt 0,64); bei r 1/3 2,112 N_0,05, gegen C.10
  gemeinsam 0,80 -22,1159 %, gegen C.10 je 0,80 1,056 (+5,599 %). GSD+Screen braucht im Maximum weniger als der
  feste P-2-(a)-Test (1,0695 gegen 1,1446 bei r 1/2), weil ein frueher Stopp den Screen auf dem dann juengsten Fenster
  prueft.
- **REZENZ im sequentiellen Design [R/U].** Effekt nur bis zur Info-Zeit t0 = 0,5, Effekt = MDE: P(PASS) 0,1786 bei
  r 1/2 (Screen an jedem Stopp), davon **veraltet** (PASS an einem Blick, dessen juengstes Fenster ganz effektfrei ist)
  0,0181; der Rest sind PASS an Blicken, an denen der Effekt im juengsten Fenster noch lag - zum Zeitpunkt richtig.
  Veraltete PASS bleiben <= 0,05 bei Screen an jedem Stopp (r 1/4, t0 0,5: 0,0477), nicht bei Screen nur am letzten
  Blick (r 1/4, t0 0,5: 0,0997) und nicht ohne Screen (0,0586 bei r 1/2, t0 0,5; 0,0853 bei r 1/4, t0 0,75). [U]
  Empfehlung: Screen an **jedem** Wirksamkeits-Stopp (Lesart "letzte vier Quartale vor dem Blick").
- Futility senkt E[N bei H0] auf 0,5993..0,6897 (mit Screen) und hebt das Maximum um 0,0262 / 0,0253 / 0,0231
  (r 1/2 / 1/3 / 1/4).
- OBF-Grenzen (z je Blick, alpha 0,0025): 5,664 / 4,0051 / 3,2701 / 2,832; bei alpha 0,05: 3,468 / 2,4522 / 2,0023 /
  1,734 (`t.b_OBF_grenzen`, mit nominalem p je Blick). Mit geschaetzter Varianz gelten die t-Grenzen aus (e).

## (c) Selektion in Zone X (K Varianten, beste registriert)

Modell [Annahme]: X-Schaetzer x_i ~ N(theta_i, 1) (Einheit: SE der X-Messung), jede Variante mit Wahrscheinlichkeit pi
echt (theta = delta), sonst 0; registriert wird argmax x_i; Konfirmation mit P-2 (a), r 1/2, auf disjunkten Daten,
Information so geplant, dass die Power beim Planungseffekt 0,80 waere. 200.000 Pfade je Zelle (`c.zellen`).

**Selektionsbereinigter Schaetzer (bedingt median-unverzerrt) [R]:** mit x = Gewinner und M = Maximum der anderen
loest theta_hat

    [1 - Phi(x - theta_hat)] / [1 - Phi(M - theta_hat)] = 1/2

(Inversion der gestutzten Normalverteilung von x gegeben x > M; Andrews/Kitagawa/McCloskey, "Inference on Winners"
[Lit.]). Geprueft: P(theta_hat <= theta_sel) = 0,4977..0,5017 in allen 30 Zellen.

| K | pi | delta | Basisrate pi_K = P(gewaehlt echt) | E[x_sel] / E[theta_sel] | E[x_sel] gegeben echt (gegen delta) | Power echt, roh geplant / bereinigt geplant (nominal 0,80) | Info / Orakel (Median, roh / ber.) |
|---|---|---|---|---|---|---|---|
| 4 | 0,10 | 2 | 0,2906 | 1,4288 / 0,5812 | 2,3100 | 0,642 / 0,666 | 0,770 / 0,834 |
| 10 | 0,10 | 1 | 0,2902 | 1,7263 / 0,2902 | 2,0058 | 0,256 / 0,428 | 0,262 / 0,360 |
| 10 | 0,10 | 2 | 0,4981 | 2,1281 / 0,9963 | 2,6118 | 0,547 / 0,631 | 0,605 / 0,739 |
| 10 | 0,10 | 3 | 0,6093 | 2,6840 / 1,8279 | 3,3759 | 0,669 / 0,718 | 0,796 / 0,913 |
| 10 | 0,25 | 2 | 0,8251 | 2,6673 / 1,6502 | 2,8388 | 0,470 / 0,605 | 0,505 / 0,685 |
| 25 | 0,10 | 1 | 0,3832 | 2,1893 / 0,3832 | 2,3741 | 0,139 / 0,385 | 0,185 / 0,298 |
| 25 | 0,10 | 2 | 0,7128 | 2,7482 / 1,4256 | 2,9680 | 0,424 / 0,592 | 0,467 / 0,654 |
| 4 / 10 / 25 | 0 | - | 0 | 1,0292 / 1,5394 / 1,9660 (reines E[max]) / 0 | - | - | - |

(i) **Winner's Curse [R]:** der rohe Schaetzer des Gewinners liegt bei echten Varianten beim 1,0531- bis 2,7144-fachen
von delta (z. B. 2,6118 gegen 2 bei K 10, pi 0,10; 2,3741 gegen 1 bei K 25, pi 0,10); unbedingt mischt er Nullvarianten
ein (E[x_sel] 2,1281 gegen E[theta_sel] 0,9963). (ii) **Basisrate [R]:** pi_K steigt durch die Auswahl ueber pi
(pi 0,10 -> pi_K 0,2043..0,876 je K und delta); bei delta 1 bleibt sie maessig (0,2043 / 0,2902 / 0,3832 fuer
K 4 / 10 / 25). (iii) **Power-Ueberschaetzung [R]:** roh geplant erreicht die Konfirmation fuer echte Varianten im
Mittel 0,0868..0,7184 statt 0,80 (Anteil mit Power < 0,5: 0,2107..0,9993); bedingt median-unverzerrt geplant
0,3508..0,735 - besser, aber **nicht** 0,80, weil Median-Unverzerrtheit die Haelfte der Planungen unterdimensioniert und
die Power-Kurve dort steil faellt. Der bereinigte Schaetzer ist oft <= 0 (nicht registrierbar): Anteil registriert
0,4983..0,8567. (iv) **alpha bleibt [R]:** gewaehlte Nullvarianten bestehen die Konfirmation auf disjunkten Daten mit
0,0011..0,0022 (MC in Zellen mit >= 1.000 Null-Gewinnern; Soll alpha_eff 0,001933). Wuerden die X-Daten
wiederverwendet, waere alpha bei reiner Null 0,00996 / 0,02472 / 0,06066 (K 4 / 10 / 25, analytisch 1 - (1 - 0,0025)^K) und
bedingt auf einen Null-Gewinner neben echten Varianten 0,0099..0,7249.

## (d) Programmebene je Jahr (m Registrierungen, Kohorte)

Modell [Annahme]: m unabhaengige Registrierungen je Jahr, Basisrate pi_K, echte mit Power 0,80 an der MDE (feste
Szenarien) oder mit der realisierten Power aus (c) (roh geplant); Regel P-2 (a), r 1/2; 200.000 Kohorten je Zelle.

**BY q 0,10 ist bei festem alpha 0,0025 fuer m <= 12 nie bindend [R]:** die kleinste BY-Schwelle q/(m c_m) ist 0,012
(m 4), 0,0046 (m 8), 0,00269 (m 12) - alle ueber 0,0025; erst ab m 13 (0,00242) koennte BY greifen. In allen 30 Zellen
ist "BY plus festes alpha" identisch mit "festes alpha" (`identisch_BY_plus_fest_und_fest` = True).

| Szenario | m | pi_K | E[Falsch-PASS] | E[wahre PASS] | PPV | FDR | P(>= 1 Falsch-PASS) | nur BY q 0,10 statt festem alpha: E[Falsch-PASS] / FDR |
|---|---|---|---|---|---|---|---|---|
| fest | 4 | 0,05 | 0,0071 | 0,161 | 0,9581 | 0,0066 | 0,0070 | 0,0313 / 0,0274 |
| fest | 8 | 0,05 | 0,0147 | 0,318 | 0,9558 | 0,0128 | 0,0146 | 0,0330 / 0,0253 |
| fest | 8 | 0,10 | 0,0141 | 0,639 | 0,9784 | 0,0107 | 0,0141 | 0,0373 / 0,0239 |
| fest | 8 | 0,25 | 0,0114 | 1,596 | 0,9929 | 0,0059 | 0,0113 | 0,0437 / 0,0183 |
| fest | 12 | 0,05 | 0,0220 | 0,477 | 0,9558 | 0,0176 | 0,0218 | 0,0343 / 0,0235 |
| fest | 12 | 0,10 | 0,0205 | 0,961 | 0,9791 | 0,0133 | 0,0203 | 0,0401 / 0,0211 |
| aus (c): K 10, pi 0,10, delta 2 | 8 | 0,4981 | 0,0076 | 2,180 | 0,9965 | 0,0032 | 0,0076 | 0,0378 / 0,0120 |
| aus (c): K 10, pi 0,10, delta 1 | 8 | 0,2902 | 0,0111 | 0,597 | 0,9817 | 0,0085 | 0,0111 | 0,0325 / 0,0194 |
| aus (c): K 25, pi 0,10, delta 2 | 8 | 0,7128 | 0,0046 | 2,415 | 0,9981 | 0,0018 | 0,0046 | 0,0262 / 0,0073 |

Lesart [U]: Unter 3.1 kosten acht Registrierungen je Jahr 0,0114..0,0147 erwartete Falsch-PASS (feste Szenarien); der PPV liegt bei
Basisrate >= 0,05 ueber 0,95. Heute (C.10, faktisch m ~ 0) entstehen weder falsche noch wahre PASS; haette man m 8 unter
C.10 je 0,80, waeren es 0,018 Falsch-PASS je Jahr (pi_K 0,10) bei Power 0,64 statt 0,80. Ein Budget, das das feste alpha
ersetzt (nur BY), vervielfacht die Falsch-PASS (0,0373 gegen 0,0141 bei m 8, pi_K 0,10: Faktor 2,6403; Spanne
ueber alle Zellen 1,5575..8,7609) - der Satz der
Analyse "festes alpha je Test bleibt" ist die tragende Schranke, BY ist darunter Formsache. PPV analytisch (Basisrate
0,05 / 0,10 / 0,25): C.10 heute 0,9309 / 0,966 / 0,9884; P-2 (a) 0,9561 / 0,9787 / 0,9928 (`d.ppv_analytisch`).

## (e) Schwere Raender und kleine Clusterzahlen

Teststatistik: Mittel / SE mit (i) naiver SE und z-Grenze, (ii) naiver SE und t(n-1)-Grenze, (iii) SE nach DEC-94 (4)
= max(naiv, stationaerer Bootstrap mit mittlerer Blocklaenge 4, power_p1-Konvention) und z-Grenze. Die Bootstrap-SE
wird exakt als Grenzwert B -> unendlich gerechnet (Politis/Romano-Formel mit zirkulaerer Autokovarianz); Gegenprobe
gegen den power_p1-Algorithmus mit 100.000 Replikaten: 0,12726 gegen 0,12716 bzw. 0,12496 gegen 0,12488 [R].
200.000 Pfade je Zelle (`e.einzeltest`, `e.gsd_geschaetzte_varianz`).

**Wahres alpha bei nominal 0,0025 (einseitig, obere Flanke) [R]:**

| Verteilung | n 40: z naiv / t / SB-max | n 52 | n 104 | untere Flanke SB-max (n 40 / 52 / 104) |
|---|---|---|---|---|
| normal | 0,00391 / 0,00241 / 0,00338 | 0,00372 / 0,00260 / 0,00328 | 0,00301 / 0,00254 / 0,00266 | 0,00331 / 0,00293 / 0,00286 |
| t(5) | 0,00341 / 0,00214 / 0,00307 | 0,00311 / 0,00220 / 0,00277 | 0,00273 / 0,00228 / 0,00237 | 0,00308 / 0,00268 / 0,00236 |
| t(4) | 0,00351 / 0,00226 / 0,00314 | 0,00294 / 0,00200 / 0,00254 | 0,00252 / 0,00209 / 0,00214 | 0,00278 / 0,00247 / 0,00215 |
| t(3) | 0,00274 / 0,00168 / 0,00244 | 0,00257 / 0,00170 / 0,00225 | 0,00217 / 0,00175 / 0,00183 | 0,00251 / 0,00226 / 0,00220 |
| schief t(4), Schiefe 2,41 | 0,00075 / 0,00038 / 0,00065 | 0,00064 / 0,00038 / 0,00053 | 0,00078 / 0,00061 / 0,00064 | **0,01141 / 0,00945 / 0,00713** |
| schief t(4), Schiefe 1,24 | 0,00150 / 0,00090 / 0,00129 | 0,00151 / 0,00097 / 0,00128 | 0,00143 / 0,00112 / 0,00122 | **0,00599 / 0,00507 / 0,00405** |
| AR(1) phi 0,3, normal (c 1,857) | - | naiv 0,02282, SB-max 0,01402 | naiv 0,02106, SB-max 0,00978 | - |
| AR(1) phi 0,3, t(4) | - | naiv 0,02223, SB-max 0,01308 | naiv 0,02093, SB-max 0,0095 | - |

Bei nominal 0,05 liegen alle iid-Faelle bei 0,0472..0,0539 (z naiv normal n 40: 0,0539); schief 0,0287..0,0435 oben;
AR(1) mit SB-max 0,07838..0,09077.

Befunde:
1. **Symmetrische schwere Raender machen den studentisierten Test im fernen Rand konservativ, nicht liberal [R]**
   (t(3), n 104, SB-max 0,00183). Die Sorge der Analyse ("wahres alpha eher hoeher") stimmt fuer die
   **Normal-Grenze bei kleinem n** (normal n 40, z naiv 0,00391 = 1,564-fach nominal; SB-max 0,00338 = 1,354-fach) und
   vor allem fuer **Schiefe gegen die Testrichtung** (untere Flanke 0,01141 = 4,566-fach bei Schiefe 2,41 und n 40;
   0,00599 = 2,396-fach bei Schiefe 1,24) und **Autokorrelation** (AR(1) phi 0,3: naiv 9,128-fach, SB-max 0,01402 =
   5,61-fach bei n 52, 3,912-fach bei n 104; der Block-4-Bootstrap erfasst c 1,857 nur teilweise). [U] Groesstes
   praktisches Risiko: Abhaengigkeit, dann Schiefe; Kurtosis allein nicht.
2. **Power gegen die Normalnaeherung [R]** (Design-Power 0,80 bei alpha 0,0025): normal n 40 z naiv 0,7948, t-Grenze
   0,7454, SB-max 0,7734; n 104: 0,7987 / 0,7812 / 0,7769. Bei t(3) liegt die Power ueber 0,80 (0,8378 / 0,8066 /
   0,8258 bei n 40), weil die Stichproben-SD dort meist unter der Populations-SD liegt.
3. **Zwischenblicke mit geschaetzter Varianz (OBF c 2,8321, Blicke bei n/4..n) [R]:** z-Grenzen ergeben alpha 0,00444
   (normal n 40, 1,776-fach), 0,00394 (n 52, 1,576-fach), 0,00308 (n 104, 1,232-fach); mit SB-max 0,00412 / 0,00363 /
   0,00265. **t-artige Grenzen**
   (Grenze je Blick = t_{n_k - 1}-Quantil zu Phi(c / sqrt(t_k))) geben 0,00254 / 0,00251 / 0,00240 (naiv) bzw.
   0,00235 / 0,00225 / 0,00206 (SB-max). Preis: Power 0,7437 statt 0,7988 (n 40), 0,7573 statt 0,7979 (n 52),
   0,7792 statt 0,7984 (n 104). Die erste t-Grenze ist bei 10 / 13 / 26 Clustern 18,926 / 13,338 / 8,205 - ein erster
   Blick vor ~26 Clustern ist praktisch wertlos. [U] Empfehlung: t-artige Grenzen Pflicht; erster Blick nicht vor
   ~26 Clustern; Power-Zeile mit der t-Grenze rechnen; fuer Schiefe ein Pflicht-Bericht der Schiefe der Cluster-Serie
   aus der Vorperiode und bei |Schiefe| >= 1 gegen die Testrichtung ein Schiefe-korrigierter Test (z. B. Johnson-t
   oder Bootstrap-t) [V: nicht gerechnet].

## (f) Ueberlappung: 1-3-Tages-Horizont mit taeglichem Schritt

Varianzinflation c der Mittelwert-Statistik bei N 365 Tagen [R] (`f.analytisch`, `f.monte_carlo`):

| Horizont h | Zeitreihe, persistenter Praediktor (rho_k = (h-k)/h) | Querschnitts-IC, Formation ueber h Tage (rho_k = ((h-k)/h)^2) | Querschnitts-IC, iid-Praediktor | NW-Erwartung L = h-1 / L = 4 (TS; XS) |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 |
| 2 | 1,9973 | 1,4986 | 1 | 1,5 / 1,8; 1,25 / 1,4 |
| 3 | 2,9927 | 2,1075 | 1 | 2,1111 / 2,4667; 1,6667 / 1,8444 |

Die Ueberlappung wirkt im Querschnitt nur ueber die Persistenz des Praediktors [R]: Cov(IC_t, IC_{t+k}) =
rho_Praediktor(k) x (h-k)/h x Var(IC) bei faktorbereinigten Renditen [V: ohne Faktorterme]. MDE x sqrt(c), Fallzahl x c.
**F1 (Akte MDE80 je Fenster 0,0133 / 0,0146 / 0,0188 bei K 600 / 500 / 300) [R]:** h 2: 0,0163 (XS) bis 0,0188 (TS)
bei K 600; h 3: 0,0193 bis 0,023; K 300 h 3: 0,0273 / 0,0325.

**Wahres alpha bei nominal 0,0025 / 0,05 (MC 200.000) [R]:** TS h 3: naive SE 0,05337 / 0,1710; Newey-West L = h-1
0,01038 / 0,0849; L = 4 0,00675 / 0,0704; L = 2h 0,00588 / 0,0657; SB-max (Block 4) 0,00813 / 0,0757. XS h 3: naiv
0,02821; NW(h-1) 0,00737; NW(4) 0,00554; SB-max 0,00647. E[c_hat] liegt deutlich unter c (TS h 3: 2,0962 / 2,4331 /
2,5680 gegen 2,9927). Vielfache von 0,0025 bei TS h 3: naiv 21,35, NW(h-1) 4,152, NW(4) 2,702, NW(2h) 2,352,
SB-max 3,25; XS h 3: 11,282 / 2,948 / 2,216 / 2,038 / 2,588. [U] Kein Bartlett-/Bootstrap-Schaetzer mit kurzer
Bandbreite haelt alpha 0,0025; bindend sollte c_bind = max(c analytisch aus Horizont und Formationsueberlappung, c_hat) sein
(Hansen-Hodrick-artig, bekannte MA(h-1)-Struktur) oder nicht ueberlappende Stichproben.

## (g) Strenge-Quotient und A2 unter 3.1 (nur Akten-Zahlen)

**Definition (Vorschlag) [U]:** Strenge-Quotient SQ = MDE80(registrierte Entscheidungsregel mit allen Festlegungen) /
MDE80(Grundfassung), Grundfassung = Primaerstatistik allein, zentrale Nuisance, **dieselbe** Entscheidungsregel und
dasselbe alpha; Datenfaktor = SQ^2; ab SQ 1,3 Nutzer-Vorlage (9.2 Nr. 3, P-12).

**Modellpruefung gegen die Akte [R]** (MDE80 bp, W1 / W2, Akte in Klammern): Grundfassung 18,25 / 18,85 (18,25 / 18,8);
drei z Produkt 22,82 / 23,09 (22,8 / 23,1); Produkt mit Null-Faktor 23,44 / 24,39 (23,43 / 24,36); **exakte
P2''-Bedingung 22,95 / 23,79 (22,93 / 23,77)**; gemeinsam zentral 21,18 / 22,31 (21,2 / 22,3); stress unskaliert
Produkt 26,08 / 27,19 (26,1 / 27,2), bivariat 25,49 / 26,48 (25,5 / 26,5); stress skaliert Produkt 26,63 / 29,31
(26,6 / 29,3), bivariat 25,40 / 28,43 (25,4 / 28,5); stress skaliert x Gate (4) Produkt 28,98 / 32,16 (29,0 / 32,1),
gemeinsam 26,19 / 30,55 (26,2 / 30,6); zentral skaliert x Gate (4) Produkt 26,05 / 28,79 (26,0 / 28,8), gemeinsam
23,76 / 27,37 (23,7 / 27,4). Mit der Korrelation nullSD/SE auch im skalierten Fall laege die bivariate Zeile bei
25,84 / 28,57 - die Zentrum-Variante trifft die Akte besser und ist gesetzt.

**A2 W2, Kette je Fenster (alpha 0,05 je Bedingung; C.10-Welt) [R]:**

| Schritt | heute (Produkt, DEC-103 N1 (8a)) | P-7 minimal (exakte P2''-Bedingung, Rest Produkt) | P-7 voll (exakte gemeinsame Power) |
|---|---|---|---|
| Grundfassung P2'' zentral | 18,85 | 18,85 | 18,85 |
| Placebosatz (P3fix bindend 19,72) | 23,09 (Produkt drei z) | - | 21,34 (drei z gemeinsam) |
| + Null-Bedingung | 24,39 | 23,79 | 22,31 |
| + Stress bindend | 27,19 | 26,48 | 24,74 |
| + skalierte Null | 29,31 | 28,43 | 27,01 |
| + Gate-(4)-Faktor 0,9025 | **32,16** | **31,48** | **30,55** |
| Strenge-Quotient (Daten) | 1,707 (2,912) | 1,670 (2,790) | 1,621 (2,626) |

P-7 allein senkt die Zuordnungs-MDE um 0,6832 bp (minimal) bzw. 1,6182 bp (voll) [R]; die drei Festlegungen tragen
in der vollen Kette +2,4246 (Stress), +2,2708 (skalierte Null), +3,5374 bp (Gate (4)) und bleiben unter 3.1 stehen
(P-7-Default).

**A2 unter P-2 (a): gepoolt W1+W2, alpha 0,0025 je Bedingung, REZENZ-Screen P2'' in W2 bei 0,05 [R, Modell]:**
Q0 P2'' gepoolt ohne Screen 19,258 (analytisch 19,249; Akte 19,24) -> Q1 mit Screen 20,707 -> Q2 drei z gemeinsam
22,239 -> Q3 plus Null 22,433 -> Q4 Stress 24,875 -> Q5 skalierte Null 25,708 -> **Q6 Gate (4) 28,058 bp**.
Zuwachs je Schritt: Screen +1,4486, Placebos +1,5327, Null +0,1936, Stress +2,4418, skalierte Null +0,8334, Gate (4)
+2,3493 bp; die drei Festlegungen zusammen +5,6245 bp. **SQ = 1,355 gegen die Grundfassung mit Screen (Q1), Daten
x1,836; 1,457 gegen Q0 (x2,1226) - ueber der Schwelle 1,3.** Varianten: Gate (4)
bei alpha 0,0025 (Faktor (1 - 0,0025)^2) 25,8; Screen auf allen drei z-Bedingungen 28,779. Annahme tau_0,9975 = 2,825
(Tail-Faktor der Null wie bei 95 % [V]).

**Laenge der Konfirmation (Q6, Screen letzte 12 Monate) [R]:** 24 Monate 28,06; 30: 26,24; 36: 25,25; 48: 24,48;
60: 24,33; 120: 24,30. **Boden 24,304 bp = (1,6449 + Phi^-1(0,8/0,9025)) x 8,52** (SE_W2 stress): die Taker-SESOI
22 bp ist mit den Festlegungen unter P-2 (a) **auf keiner Datenlaenge** erreichbar. Grundfassung Q1: Boden 18,847 =
2,4865 x 7,58. Mit P-6-Stabilitaetstest statt Screen (Ziel 0,8/0,95) faellt der Boden weg: 28,98 (24) / 25,92 (30) /
23,66 (36) / 21,91 (42) / 20,49 (48) / 18,33 (60) / 12,96 (120) [R; Unabhaengigkeit des Stabilitaetstests von den
Placebo-Bedingungen V].

## (h) Gegenueberstellung heute / 3.1

| Regel | alpha je Test | Entscheidungs-Power | E[N bei H1] (N_0,05) | PPV bei pi 0,05 / 0,10 / 0,25 | erwartete Falsch-PASS je Jahr (m 8, pi 0,10) |
|---|---|---|---|---|---|
| heute C.10 je 0,80 | 0,0025 | 0,64 | 2,000 (fest) | 0,9309 / 0,966 / 0,9884 | 0,018 (hypothetisch); real m ~ 0: 0 |
| Referenz C.10 gemeinsam 0,80 | 0,0025 | 0,80 | 2,7117 | - | - |
| 3.1 fest, P-2 (a), r 1/2 | 0,001933 | 0,80 | 2,46471 (fest, kein frueher Stopp) | 0,9561 / 0,9787 / 0,9928 | 0,01391 |
| 3.1 fest, P-2 (a), r 1/3 | 0,001424 | 0,80 | 3,17718 (fest) | - | - |
| 3.1 GSD ohne Screen (Referenz der Analyse) | 0,00251 | 0,80 | 1,8759 (Max. 2,16923) | - | - |
| **3.1 GSD + Screen an jedem Stopp, r 1/2** | 0,00217 | 0,80 | 1,9649 (Max. 2,30285) | 0,9511 / 0,9762 / 0,9919 | 0,0156 |
| 3.1 GSD + Screen, r 1/3, mit Futility | 0,00166 | 0,80 | 2,09966 (Max. 2,56204; E[N bei H0] 0,65086 N_fix) | 0,962 / 0,9816 / 0,9938 | 0,01197 |

**Fruehester Konfirmationszeitpunkt** einer am naechsten Kohorten-Stichtag (Annahme: Quartalstakt, 2027-01-01)
registrierten Hypothese mit MDE am SESOI. Zwei Lesarten der Zonenregel [U, offen]: **B** - W1/W2 bleiben blinde
Klasse-W-Fenster und sind mit den K-Quartalen 2026-07..12 nutzbar (Daten ab 2024-07); **A** - nur Quartale, die bei
Registrierung in Zone K liegen (ab 2026-01).

| Beispiel | heute (C.10 je 0,80, Fensterlaenge <= 12 Monate nach DEC-96 E2) | 3.1 (P-2 (a), fest / GSD) | 3.1 mit P-6-Stabilitaetstest statt Screen |
|---|---|---|---|
| Klasse W, Wochen-IC, SD 0,09 je Woche (A3-roh W1 gemessen), SESOI 0,040 | 31,2992 Wochen je Fenster -> auf W1/W2 sofort nach Registrierung | 67,8428 Wochen (GSD max 72,556) -> **B: 2027-01** (Daten liegen vor); A: 2027-05 (GSD max 2027-06) | B: 2027-01; A: 2027-06 |
| Klasse W, SD 0,13 (stress), SESOI 0,040 | 65,3 Wochen je Fenster -> GL-012 (L > 12); hypothetisch prospektiv ab 2026-07: 2029-02 | **nie**: Screen-Boden 0,0448 > 0,040 | B: 2027-07; A: 2029-01 |
| Klasse W, SD 0,09, SESOI 0,020 (Taker-Break-even Gauss) | 125,1968 Wochen -> GL-012; hypothetisch 2031-05 | **nie** (Boden ueber SESOI) | B: 2030-03; A: 2031-09 |
| Klasse E, A2, SESOI 22 bp (Taker) | 25,65 Monate je Fenster -> GL-012; hypothetisch prospektiv 2030-11 | **nie**: Boden 24,30 bp | 41,64 Monate -> B: 2028-01 |
| Klasse E, A2, Effekt 25 bp | 19,86 Monate je Fenster -> GL-012; hypothetisch 2029-11 | 38,78 Monate -> B: 2027-10 (GSD max 45,97 -> 2028-05); A: 2029-04 | 32,25 Monate -> B: 2027-04 |

Quellen der Eingaben: SD je Woche A3-roh-IC 0,090 (gemessen W1) / 0,130 (stress W1) aus REVIEW-Nachrechnung E;
SESOI 0,040 = korrigiertes IC_min (Analyse 0.2 (a)), 0,020 = Taker-Break-even Gauss (review_calc A: 0,0199) [U: als
SESOI gesetzt]; A2-Kette aus (g), MDE ~ T^(-1/2) zwischen den Stuetzstellen des Laengen-Scans; GSD-Maximum fuer A2 mit
dem eindimensionalen Faktor aus (b) uebertragen [V]. Die Termine zaehlen nur Kalenderdaten (keine Bearbeitungszeit).
"Heute" setzt zusaetzlich einen belegten Literatur-Prior >= MDE voraus (Prior-Pflicht), 3.1 nur die SESOI (P-3).

## Was folgt / Was nicht folgt

**Was folgt [U, gestuetzt auf R]:**
1. **Fehlerseite:** Das Paket haelt alpha je Test unter 0,0025 (P-2 (a) 0,001144..0,001933; GSD+Screen
   0,00138..0,00217), Programmebene bei m 8 0,0114..0,0156 Falsch-PASS je Jahr (fest bzw. GSD+Screen), PPV >= 0,95 ab Basisrate 0,05. Die
   Synthese-Tabelle "Gesamt-OC" (Abschnitt 6) war auf der alpha-Seite eher pessimistisch.
2. **Power-/Testbarkeitsseite - Korrektur:** Der REZENZ-Screen bei 0,05 auf einem festen 12-Monats-Fenster setzt
   zusammen mit "Power 0,80 auf der gemeinsamen Regel" einen **Boden: MDE >= 2,4865 SE_12**. 3.1 macht damit keinen
   Effekt testbar, den heute ein einzelnes 12-Monats-Fenster nicht sieht; es kauft Entscheidungs-Power 0,80 statt 0,64
   fuer Datenfaktor 1,2324 (r 1/2) gegen C.10 je 0,80 - nicht 1,08 wie in der Analyse (ohne Screen gerechnet). Fuer
   Klasse W mit Stress-SD und fuer A2 an der Taker-SESOI heisst das "nie". Das ist kein Fehler der Rechnung, sondern
   der Preis der REZENZ-Kodierung; die Abwaegung (Regime-Schutz gegen erreichbare MDE) ist eine **Nutzerfrage**:
   (a) Screen-Niveau 0,10 / 0,20 (Boden 2,1232 / 1,6832 SE_12, Grenzwert falsch-PASS bei Regimewechsel 0,10 / 0,20);
   (b) P-6-Lesart Stabilitaetstest (kein Boden, Daten x1,0905 gegen gepoolt, Schutz waechst mit dem Effekt); (c)
   Screen-Fenster proportional zur Konfirmationslaenge. Jede Variante ist gegen den Wortlaut von P-2 (a) eine
   Lockerung in der REZENZ-Dimension.
3. **A2:** Unter 3.1 wie beschlossen (P-2 (a), P-7-Defaults) liegt die Zuordnungs-MDE bei 28,058 bp auf W1+W2,
   SQ 1,355 > 1,3 -> Pflicht-Vorlage nach 9.2 Nr. 3. P-7 allein bewegt 0,6832..1,6182 bp; Stress, skalierte Null und
   Gate (4) bewegen gepoolt zusammen 5,6245 bp.
4. **Selektion:** Wer die MDE aus dem rohen X-Schaetzer setzt, plant systematisch zu klein (realisierte Power
   0,0868..0,7184 statt 0,80); der bedingt median-unverzerrte Schaetzer (DEC-99 (3)) hilft (0,3508..0,735), reicht aber
   nicht. Vorschlag [U]: Planung an einer unteren Konfidenzgrenze des bereinigten Schaetzers oder an der SESOI, nie am
   rohen Gewinner; X-Daten nie in der Konfirmation wiederverwenden.
5. **Mehrfachtest:** BY q 0,10 je Kohorte ist bei festem alpha 0,0025 fuer m <= 12 redundant; das feste alpha ist die
   tragende Schranke. Faellt es (nur Budget), steigen die Falsch-PASS um Faktor 1,5575..8,7609 (m 8, pi_K 0,10:
   2,6403).
6. **Kleine Clusterzahlen, Abhaengigkeit, Ueberlappung:** t-artige Grenzen fuer jeden Blick mit geschaetzter Varianz;
   erster Blick nicht vor ~26 Clustern; bei Autokorrelation und ueberlappenden Horizonten c analytisch als Untergrenze
   (Block-4-Bootstrap und Newey-West mit L <= 4 liegen bei 0,0025 beim 1,626- bis 5,61-fachen des Nominalwerts:
   Ueberlappung h 2..3, AR(1) phi 0,3); Schiefe-Bericht.
7. **GSD:** Gegen C.10 gemeinsam 0,80 spart GSD+Screen im Erwartungswert 27,5411 % (r 1/2), gegen die heutige Praxis
   1,7566 % bei Power 0,80 statt 0,64; bei r 1/3 kostet es gegen die Praxis 5,599 % mehr. Der Screen gehoert an jeden
   Wirksamkeits-Stopp.

**Was nicht folgt:**
- Kein Verdikt ueber irgendeinen Markteffekt; keine Registrierung; kein Siegel geoeffnet; keine Marktdaten.
- Alle Zahlen sind Aufloesungsgrenzen und Fehlerraten unter Modellannahmen (Normalitaet der Teststatistik ausser in
  (e), homogene Varianz ausser in (a) Nr. 5, Gauss-Modell der A2-Bedingungen mit Cov(P_i,P_j) = 0), keine
  Effektgroessen. Die A2-Zahlen unter P-2 (a) sind Extrapolationen eines an der Akte kalibrierten Modells, keine
  Herleitung mit Daten.
- Der Boden-Befund sagt nicht, dass REZENZ falsch ist; er beziffert ihren Preis. Ob 0,05, eine Stabilitaetspruefung oder
  ein anderes Niveau gilt, entscheidet der Nutzer.
- Die Termine in (h) haengen an der offenen Lesart A/B der Zonenregel und an SESOI-Setzungen; sie sind keine Zusagen.
  Die Beispiel-SD fuer Klasse W ist A3-Nuisance, kein registriertes Design.
- Basisraten aus (c) setzen ein Prior-Modell (pi, delta) voraus, das niemand gemessen hat [V].
- Die Monte-Carlo-Zahlen haben Binomial-Zufallsfehler; Unterschiede in der vierten Nachkommastelle bei alpha-Zahlen
  um 0,0025 sind nicht belastbar.

## Kurzfassung (<= 12 Zeilen)

1. Reproduktion: orch_review_check bitgleich, review_calc reproduziert; gsd_fut nur MC-Rauschen (1,016 / 0,879 statt 1,0074 / 0,8712).
2. alpha haelt: P-2 (a) 0,001933 / 0,001424 / 0,001144 (r 1/2, 1/3, 1/4), GSD+Screen 0,00217; m 8, pi_K 0,10: 0,0141 Falsch-PASS/Jahr, PPV 0,9784.
3. BY q 0,10 ist neben festem alpha 0,0025 fuer m <= 12 nie bindend; ersetzt BY das feste alpha, steigen die Falsch-PASS x2,6403.
4. Korrektur: Datenfaktor P-2 (a) gegen C.10 je 0,80 ist 1,2324 / 1,5886 / 2,0258, nicht 1,08 (das war ohne Screen gerechnet).
5. Boden: der 0,05-Screen auf festen 12 Monaten erzwingt MDE >= 2,4865 SE_12 - 3.1 macht nichts testbar, was ein 12-Monats-Fenster nicht sieht.
6. Dafuer Regime-Schutz: P(PASS | Effekt nur aelter) <= 0,05; Alternative P-6-Stabilitaetstest ohne Boden, Daten x1,0905 (Nutzerfrage).
7. GSD: 0,871 / 1,007 bestaetigt; mit Screen (r 1/2) E[N|H1] 0,9125, Max 1,0695 N_fix; -27,5411 % gegen C.10 gemeinsam 0,80.
8. Selektion: roh geplante Konfirmations-Power 0,0868..0,7184 statt 0,80, median-unverzerrt 0,3508..0,735; alpha bleibt (disjunkt).
9. Raender: symmetrisch schwer = konservativ; liberal sind z-Grenzen bei n 40..52 (GSD 0,00444), Schiefe (0,01141), AR(1) 0,3 mit Bootstrap (0,01402).
10. A2: W2-Kette 32,16 -> P-7 31,48 / 30,55 bp; P-2 (a) gepoolt 28,058 bp, SQ 1,355 > 1,3; Boden 24,30 > SESOI 22 -> nie.
11. Klasse W (SESOI 0,040): SD 0,09 ab 2027-01 (Lesart B); SD 0,13 nie (Boden 0,0448), mit P-6 2027-07.
