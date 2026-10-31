# A2-Vorarbeit Teil C (2): Pilot-Schaetzfenster-Route - Uebergaberegel U-A2 (Vorlage), Positivkontrolle, Gate (4), Entscheidungsvorlagen

> **Fassung 2 (2026-10-31) nach REVIEW_A2_TEILC.md: VETO-Aufloesung A-1, Auflagen A-2..A-9 eingearbeitet.** Zahlen der
> Fassung 1 unveraendert (als "Fassung 1" ausgewiesen); neu sind die Zeilen nach den Festlegungen des Orchestrators.
> Aenderungen am Ende.
> ENTWURF der Herleitung, Stand 2026-10-31. **Vorlage, nicht beschlossen, nichts registriert, kein Verdikt; keine
> Pilot-Zahl gerechnet** (kein Mittel, kein Vorzeichen eines Kontrasts auf irgendeinem Fenster). Registrierung und
> Pilotlauf nur nach Zustimmung des Nutzers (DEC-103).
> **Etikett:** wie `NULL_SIMULATION_A2.md` (`label` in `a2_teilC.json`): Renditen nur 2021-03-24..2024-05-31, Kalender
> nur <= 2026-06-30, Funding-Zeitstempel ohne Rate; nur Streuung, Schwellen, Powers, Fehlerraten, Zaehlungen; keine
> Vereinigungs-SD (R-C12a).
> **Festlegung des Orchestrators (2026-10-31, nach Kenntnis der Nuisance einschliesslich der Pilot-Power-Tabelle,
> Richtung Strenge):** (a) Null-Bedingung als eigener Faktor, exakte bivariate P2''-Bedingung Bericht; (b) Test skaliert
> seine Null wie DEC-101 E2, die Pilot-Schwelle behaelt k_pred (U-4 woertlich); (c) Stress-Kalibrierung (V1) bindet,
> zentral Bericht; (d) **Regel R0 (U-A2) als registrierte Regel**, R1/R2 nur Bericht, R3/R5 strengere Alternativen;
> (e) PK-Kriterium (b) = erwartete PASS-Quote am Ziel - 2,3263 x Binomial-SE, Gate (4) in der PK-Kette; (f) Gate (4)
> mechanisch, Faktor 0,95 je Symbol (vorlaeufig, UNBELEGT bis Negativ-Panel-Daten). Alternativen als Bericht.
> **Quellen:** DEC-103 "Pilot-Schaetzfenster-Route", DEC-99 (2a)/(3)/(5)/(6)/(7), DEC-101 E2/E7/E8, DEC-94 (3)-(6), PRD
> 5.2 und 3.3.8, `REVIEW_A2_TEILC.md` (B-3..B-7, A-2..A-9), `h32_fm8/handover.py` (Muster, nicht benutzt),
> `power_p1.py` (benutzt), `NULL_SIMULATION_A2.md` (Konstanten). **Kuerzel:** `[aj-C:<pfad>]` = `a2_teilC.json`.

## 0. Kurzfassung

- **Zuerst (Review A-9, woertlich):** "Beim einzigen belegten Prior (16,5 bp) uebergibt die Route mit ~2,7 % (Kontrast)
  bzw. ~0,5 % (Ereignis-Skala); mit ~97 % ist die Vorperiode danach verbraucht und A2 endet in GL-012 (Pilot). Ein
  16,5-bp-Effekt ist auf 12-Monats-Fenstern unter C10 in keiner DEC-konformen Lesart testbar (MDE80prod >= 22,8 bp)."
  **Mit den Festlegungen (a)-(f) sinkt die Uebergabe-Wahrscheinlichkeit bei 16,5 bp auf 0,0001 (Kontrast) / < 0,0001
  (Ereignis-Skala); A2 ist dann auf jedem Gitterpunkt bis 25 bp GL012.**
- **Zuerst (Review B-2 / A-2):** "`a2_vorarbeit.json` (Commit 363f3d9) speichert implizit (Varianzzerlegung ALL/FRI/NONFRI,
  NONFRI/MODO/WE, FRI/FRI_W/FRI_MQ) die Betraege von Lage-Differenzen auf r_pre der Vorperiode; |x_P| ist daraus auf zwei
  Kandidaten bestimmbar; niemand hat die Kombination gebildet." Die Blindheit der Vorperiode haengt damit nur an
  Disziplin. Dazu aus Teil C (G-C9): die gepoolte P3fix-Klasse ist die Vereinigung der Teil-B-Klassen fix1530 MODO und
  FRI_W (Wochentags-Lage des 15:30-Slots, nicht die Pilotstatistik).
- **Regel R0 (U-A2) in einer Formel** (registrierte Richtung negativ, Pilot = 2021-03-24..2024-05-31):

      Uebergabe  <=>  max_j x_P,j < 0   und   x_P <= -( m*_null + max_W MDE80prod_W(k_pred,W) )   und   -x_P / SE_P >= 2,0

  mit x_P = Pilot-Kontrast Freitag gegen P2'' (dieselbe Statistik wie im Test), j ueber {P2'', P3fix, P3all},
  MDE80prod_W = Ereignis-Prior, bei dem das Produkt der Einzel-Powers aller Gate-Bedingungen im Testfenster W (stress,
  bindend) einschliesslich der skalierten Null-Bedingung und des Gate-(4)-Faktors 0,80 erreicht, k_pred,W = max(1,
  SE_T,W / SD_null,W) (U-4 woertlich), m*_null = max(0, Null-Zentrum des Pilots in registrierter Richtung).
- **Schwelle vor dem Pilot: c_A2 = 32,1 bp** (stress, bindend W2; W1 29,0); vorlaeufig wegen Gate (4) - ohne den
  Gate-(4)-Faktor 29,3; zentral (Bericht) 28,8; Fassung 1 24,4. t am Schwellenwert 7,85 (SE_P 4,10).
- **Positivkontrolle:** Ziel 32,1 bp im bindenden Fenster W2 (stress); erwartete PASS-Quote 0,825 (gemeinsame Power x
  Gate (4)); **Kriterium (b) = 0,763** (= 0,825 - 2,3263 x 0,0268).
- **Gate (4):** mechanische Form in Abschnitt 6a; Faktor 0,9025 im Produkt (vorlaeufig).
- **Richtung: Lockerung** (Etikett Abschnitt 7).

## 1. Ausgangslage

DEC-103: V-5b bleibt UNBELEGT; ohne weiteren Schritt ist A2 GL-012 vor der Registrierung. DEC-99 (2a) erlaubt aeltere
Daten als vorab registriertes **Pilot-Schaetzfenster** (nie urteilstragend; genau ein Pilotlauf; Uebergaberegel und
Prior-Lesart vor dem Oeffnen registriert; Panel-Schnitt mit Waechter; Ergebnis mit sha256 festgehalten, bevor ein
Testfenster gerechnet wird; Pflicht-Doppelausweis des selektionsbereinigten Schaetzers). Muster: H-32 (U-4, GL-035).
**Pilot fuer A2:** Vorperiode 2021-03-24..2024-05-31 (endet vor W1); E 167 Freitage, P2'' = alle 666 Mo-Do, P3fix 794,
P3all 832 Tage; jede Pilotwoche permutierbar (kappa 0,9996); Funding-Termin 08:00 an allen Pilot-Tagen belegt (C-2).
Pilot-Statistik = derselbe Kontrast (DEC-103 E2) und dieselben drei Bedingungen. Nuisance der Pilotstufe (nur Streuung):
SE_P P2'' 4,10, P3fix 4,43, P3all 3,66 bp; Null-SD des Pilots 3,74 bp [aj-C:teil_C3.se_pilot_nuisance].

## 2. Regel R0 (U-A2), mechanisch, alle Groessen vorab fixiert

**Vorab fixiert (aus Teil C, in der Registrierung als Konstanten):** je Testfenster W und Bedingung j die bindenden SE
der Stress-Kalibrierung (SE_bind,j,W: P2'' 8,25 / 8,52, P3fix 8,66 / 8,67, P3all 7,39 / 7,39), Null-SD_W (7,53 / 7,01),
d95_W = tau95 x Null-SD_W (tau95 = 1,6553), kappa_W (0,999 / 0,815), der Gate-(4)-Faktor (vorlaeufig 0,9025, bis
Negativ-Panel-Daten), z_krit 1,6449, z_80 0,8416, Ziel 0,80, t_min 2,0, Produkt-Regel, Prior-Lesart A, SE-Regel des Tests
(DEC-94 (4): je Mittel-Term max(SD/sqrt(N), stationaerer Bootstrap Blocklaenge 4, >= 1.000 Replikate, Seed registriert),
Kovarianz nur wenn erhoehend), die J-(i)-Null mit Waechter, die Null-Skalierung des Tests (Festlegung (b)) und die Seeds.

**Im einen Pilotlauf berechnet (mechanisch, danach mit sha256 festgehalten):** x_P,j und SE_P,j (SE-Regel des Tests);
das J-(i)-Zentrum m_P des Pilots (registrierte Richtung); SE^Pilot_j,W = SE-Regel des Pilots mit jedem Mittel-Term um
sqrt(N_Pilot / N_W) auf die Mengen von W skaliert.

**Regel:**

    SE_T,j,W = SD_T,j,W = max( SE_bind,j,W , SE^Pilot_j,W )                                        (U-4, erste Zeile)
    k_pred,W = max( 1, SE_T,P2'',W / SD_null,W )                     (U-4 woertlich; vor dem Pilot 1,096 / 1,215)
    P_W(pi)  = Phi(pi/SE_T,P2'',W - z_krit) x Phi((kappa_W pi - k_pred,W d95_W) / (k_pred,W SD_null,W))
               x Phi(pi/SE_T,P3fix,W - z_krit) x Phi(pi/SE_T,P3all,W - z_krit) x G4                (Produkt, DEC-103 E3)
    MDE80prod_W(k_pred,W) = min{ pi : P_W(pi) >= 0,80 }                                     (Bisektion, power_p1)
    m*_null  = max(0, m_P)                                                                        (keine Gutschrift)
    c_A2     = m*_null + max_W MDE80prod_W(k_pred,W)
    UEBERGABE  <=>  (i) x_P,P2'' < 0, x_P,P3fix < 0, x_P,P3all < 0
                    (ii) -x_P,P2'' >= c_A2
                    (iii) t_P = -x_P,P2'' / SE_P,P2'' >= 2,0
    sonst GL-012 (Pilot); nicht endliche Eingabe -> keine Uebergabe (fail closed).

**Gegen Fassung 1 geaendert:** k_pred ist jetzt fensterweise SE_T,W / SD_null,W (U-4: vorhergesagte reale SE des
Testfensters gegen dessen eingefrorene Null-SD) statt des Pilot-Quotienten SE_P / SD_null,P (1,095); das ist die mit der
skalierten Test-Null (Festlegung (b)) konsistente Lesart - in W2 ist k 1,215, weil SE_T die Streuung des festen Zentrums
enthaelt. Monotonie: k_pred, SE^Pilot, m* und der Gate-(4)-Faktor koennen c_A2 nur erhoehen.
**Prior-Lesart A:** pi = -x_P,P2'' fuer alle drei Bedingungen (unabgeschwaecht; Strenge gegen die OI-Lesart).
**Was die Schwelle deckt:** am Pilotpunkt pi = c_A2 hat jedes Testfenster eine Produkt-Power >= 0,80 ueber (a) die
z-Bedingungen der drei Placebos (Konjunktion), (b) die skalierte Null-Bedingung von P2'' (U-4-Term (1c); in W2 mit
kappa 0,815), (c) Gate (4) (vorlaeufig, Faktor), (d) die Produkt-Zuordnung C10 in beiden Fenstern (DEC-52-Zweig
ausgeschlossen, P-G4).
**Pflicht-Doppelausweis (DEC-99 (3)), nur bei Uebergabe:** mu_sel = Loesung von P_mu(X >= x | X >= c_A2) = 0,5 und die
Produkt-Power am Punkt mu_sel (Bericht).
**Regel-Familie (Review B-3, Festlegung (d)):** R0 = obige Regel (registriert); R1 = P2''-Bedingung exakt bivariat
(Bericht); R2 = ohne Null-Faktor (Bericht); R3 = Stress-Linie - durch Festlegung (c) in R0 aufgegangen; R5 = untere
80-%-Schranke x_P - 0,8416 SE_P >= c_A2 (strengere Alternative, selektionsrobust); R4 (nur t >= 2) verletzt DEC-94 (6),
unzulaessig.

**Zahlen vor dem Pilot** [aj-C:teil_C3.thresholds]:

### T10 Pilot-Schwelle c_A2 (Kontrast-Skala, bp): Regel R0 und Varianten

| Linie | Variante | MDE80prod W1 | MDE80prod W2 | c_A2 (max_W) | bindendes Fenster |
|---|---|---|---|---|---|
| stress | R0_bindend_vorlaeufig_gate4 | 29,0 | 32,1 | 32,1 | W2 |
| stress | R0_k_pred_x1.1 | 29,9 | 34,1 | 34,1 | W2 |
| stress | R0_ohne_gate4_bis_negativpanel | 26,6 | 29,3 | 29,3 | W2 |
| stress | R0_pilot_se_plus_10pct | 31,9 | 35,4 | 35,4 | W2 |
| stress | R1_bivariat_P2ss_exakt_bericht | 27,9 | 31,5 | 31,5 | W2 |
| stress | R2_ohne_null_faktor_bericht | 27,8 | 28,2 | 28,2 | W2 |
| stress | a3_praxis_gate4 | 35,0 | 36,5 | 36,5 | W2 |
| stress | fassung1_unskaliert_ohne_gate4 | 26,1 | 27,2 | 27,2 | W2 |
| stress | lesart_OI_0842: Ereignis-Skala W1 / W2; Schwelle auf x_P = 0,842 x max | 32,5 | 37,2 | 31,3 (auf x_P) | - |
| stress | k_pred,W vor dem Pilot (SE_T,W / Null-SD_W) | 1,096 | 1,215 | - | - |
| zentral | R0_bindend_vorlaeufig_gate4 | 26,0 | 28,8 | 28,8 | W2 |
| zentral | R0_k_pred_x1.1 | 26,8 | 30,5 | 30,5 | W2 |
| zentral | R0_ohne_gate4_bis_negativpanel | 23,9 | 26,2 | 26,2 | W2 |
| zentral | R0_pilot_se_plus_10pct | 28,7 | 31,6 | 31,6 | W2 |
| zentral | R1_bivariat_P2ss_exakt_bericht | 25,1 | 28,2 | 28,2 | W2 |
| zentral | R2_ohne_null_faktor_bericht | 25,1 | 25,4 | 25,4 | W2 |
| zentral | a3_praxis_gate4 | 31,5 | 32,8 | 32,8 | W2 |
| zentral | fassung1_unskaliert_ohne_gate4 | 23,4 | 24,4 | 24,4 | W2 |
| zentral | lesart_OI_0842: Ereignis-Skala W1 / W2; Schwelle auf x_P = 0,842 x max | 29,0 | 33,1 | 27,9 (auf x_P) | - |
| zentral | k_pred,W vor dem Pilot (SE_T,W / Null-SD_W) | 1,095 | 1,214 | - | - |

Lesart: Die bindende Schwelle 32,1 bp setzt sich gegen Fassung 1 (24,4) aus Stress (+2,8), Skalierung (+2,1) und
Gate (4) (+2,8) zusammen (W2). R5 laege bei 35,6 bp. Je 10 % mehr Pilot-SE kosten 3,2 bp, je 10 % mehr k_pred 2,0 bp.
Unter der OI-Lesart (P3 mit pi / 0,842) laege die Schwelle auf x_P bei 31,3 bp (Testbarkeit, nicht empfohlen).

## 3. Power der Pilotstufe gegen das Prior-Gitter

Modell: y_P,P2'' ~ N(mu_c, SE_P^2) mit SE_P = 4,10 bp; Uebergabe = (ii) und (iii) und die Vorzeichen der beiden
P3-Pilotkontraste (SE 4,43 / 3,66) als Produkt (Untergrenze). Kontrast-Skala: mu_c = Prior; Ereignis-Skala: mu_c =
0,842 x Prior (OI-Proportionalitaet, UNBELEGT), P3 voller Prior. Zwei-Stufen-Power = Pilot-Power x Produkt-Power des
Tests in W1 x W2 (getrennte Daten) [aj-C:teil_C3.pilot_power_grid]. Beide Linien (stress bindend, zentral Bericht), dazu
R5 und Fassung 1.

### T11 Power der Pilotstufe (Uebergabe-Wahrscheinlichkeit) und Zwei-Stufen-Power gegen das Prior-Gitter

| Prior (bp) | Kontrast: R0 stress (bindend) | R0 zentral | R5 stress | Fassung 1 | Zwei-Stufen R0 stress / zentral | Ereignis 0,842: R0 stress | R0 zentral | R5 stress | Fassung 1 | Zwei-Stufen R0 stress / zentral |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,0 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 / 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 / 0,0000 |
| 8,0 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 / 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 / 0,0000 |
| 12,0 | 0,0000 | 0,0000 | 0,0000 | 0,0012 | 0,0000 / 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0002 | 0,0000 / 0,0000 |
| 16,5 | 0,0001 | 0,0014 | 0,0000 | 0,0271 | 0,0000 / 0,0001 | 0,0000 | 0,0001 | 0,0000 | 0,0052 | 0,0000 / 0,0000 |
| 25,0 | 0,0406 | 0,1786 | 0,0049 | 0,5593 | 0,0141 / 0,0918 | 0,0034 | 0,0296 | 0,0002 | 0,2071 | 0,0007 / 0,0102 |

**Lesart:** Die Pilotstufe ist ein reines Power-Tor (Review B-3: korrekte Folge von DEC-99 (6) + DEC-94 (6), kein
Fehler). Mit den Festlegungen uebergibt sie erst ab ~32 bp Pilot-Kontrast (t ~ 7,8); bei 25 bp in 4,1 % (Kontrast) bzw.
0,3 % (Ereignis-Skala) der Faelle, bei 16,5 bp praktisch nie. Ein echter Effekt unter ~30 bp endet mit hoher
Wahrscheinlichkeit in GL-012 (Pilot) bei verbrauchter Vorperiode.

## 4. Fehlerraten

| Groesse | Wert | Herleitung |
|---|---|---|
| Pilot-alpha P(Uebergabe \| mu = 0) | <= 2,2e-15 (R0 stress); 1,1e-12 (zentral); 1,3e-9 (Fassung 1) | 1 - Phi(c_A2 / SE_P), ohne Ausloeschung (erfc); die Vorzeichen-Bedingungen senken weiter |
| Test-alpha je Fenster und Bedingung | 0,05 einseitig (DEC-51 (1), P-1) | unveraendert (DEC-99 (6)); die skalierte Null und Gate (4) senken die Fehlrate weiter |
| Test C10 gemeinsam | <= 0,0025 | 0,05^2 |
| Zwei-Stufen-Fehlrate | <= 5,4e-18 (R0 stress) | Pilot-alpha x 0,0025, getrennte Daten |
| FDR | F-EXPCLOCK = 1 Test; nicht uebergeben: p = 1, nicht in m (DEC-99 (7)) | K = 1 |

Der Preis der Route ist nicht die Fehlrate, sondern der Verbrauch der Vorperiode bei sehr kleiner Uebergabe-Power und die
Lockerung der Vorbedingung (Abschnitt 7).

## 5. Was GL-012 (Pilot) ausloest, Verbrauch, K-Zaehlung

- **GL-012 (Pilot)** bei Verfehlen von (i), (ii) oder (iii) oder nicht endlicher Eingabe: p = 1, nicht in m, keine
  Positivkontrolle, kein Test, W1/W2 bleiben fuer A2 ungeoeffnet; GL-Eintrag mit Grund und sha256 des Pilot-Ergebnisses.
  Ein zweiter Pilotlauf nur bei nachgewiesenem Code-/Datenfehler per DEC (Versuchsmarker wie DEC-101 E9a).
- **Vor der Uebergabe ausserdem:** liegen die Negativ-Panel-Daten vor, wird der Gate-(4)-Faktor durch die gemessene
  Power ersetzt (Formel unveraendert; nur Erhoehung zulaessig, Strenge) - sonst bleibt 0,9025 (vorlaeufig) und die
  Registrierung wartet auf die Daten (Abschnitt 8).
- **Nach Uebergabe:** Positivkontrolle allein und zuerst (Abschnitt 6); NICHT BESTANDEN -> kein Test, neue DEC.
- **Verbrauch (DEC-99 (5)):** nach dem Pilot ist 2021-03-24..2024-05-31 fuer jede mit A2 korrelierte Statistik nicht mehr
  blind; ein weiterer Pilot zaehlt alle frueheren Pilot-Varianten in K.
- **K-Zaehlung:** eine Variante (D_i, {P2'', P3fix, P3all}, r_pre, x = (r_BTC + r_ETH)/2, J-(i), Lesart A, R0); K = 1,
  F-EXPCLOCK = 1 Test; jede weitere Pilot-Variante zaehlt in K.

## 6. Positivkontrolle in Produktionskonfiguration (Design, nicht gebaut)

- **Zeitpunkt:** nach Uebergabe, allein, vor dem Test; Registrierung und Pilot-Ergebnis per sha256 gesperrt.
- **Nullwelt:** reale Kalenderform von W1 und W2 (E, P2'' mit den 12 festen Wochen in W2, P3fix, P3all,
  Monatsend-Freitage, Futures-Tage) mit **nur synthetischen Renditen** (keine W1/W2-Rendite wird gelesen): je Tag BTC/ETH
  fuer [07:30, 08:00), [15:30, 16:00) und das P3all-Aggregat, Student-t (Freiheitsgrade aus der Vorperioden-Kurtosis),
  BTC/ETH-Korrelation je Klasse (Teil B), Klassen-SDs der bindenden Power-Zeile (stress), skaliert, sodass die SD jedes
  Kontrasts die SE_T,j,W trifft (+-5 %); **dazu ein synthetisches Negativ-Panel** (XRP/BNB-Reihen mit Beta zu BTC und
  Restrauschen, ohne Injektion), das durch dieselbe Gate-(4)-Kette laeuft.
- **Gate-Kette = Test (N-1):** derselbe Code: Mengen, SE-Regel, J-(i)-Null mit Waechter und Skalierung (Festlegung (b)),
  drei z-Bedingungen, Null-Bedingung, **Gate (4)**, C10 in beiden Fenstern.
- **Injektion:** -F auf jede Ereignis-Rendite [07:30, 08:00) (BTC und ETH), nicht an Placebo-Tagen/-Slots und nicht im
  Negativ-Panel; **F = MDE80prod (R0) im bindenden Fenster: 32,1 bp (W2, stress)**; Seeds wie H-32 (Welt 2000..2049,
  Injektion 1000..1049, Urteil 53..252). In W2 verschiebt die Injektion auch das J-(i)-Zentrum (12 feste Freitage).
- **Kriterien (Festlegung (e), analog DEC-101 N-1/N-2/E8):** (a) SD der Kontrollwelt <= 1,10 x SD der Power-Zeile je
  Fenster und Bedingung; **(b) PASS-Quote (alle Bedingungen einschliesslich Gate (4)) im bindenden Fenster >= 0,763** =
  erwartete Quote am Ziel 0,825 (gemeinsame Power 0,914 x Gate (4) 0,9025, Modell) - 2,3263 x Binomial-SE 0,0268 bei 200
  Seeds (zum Vergleich: ohne Gate (4) waere die Erwartung 0,914 und das Kriterium ~0,87; W1 stress 0,847 -> 0,788);
  (c) falsche PASS-Quote der Negativkontrolle (F = 0) <= 0,086 je Fenster; (d) realisierter Injektionseffekt innerhalb
  +-10 % des Ziels. NICHT BESTANDEN -> kein Test, neue DEC. Das Kriterium wird nach den Negativ-Panel-Daten mit dem
  gemessenen Gate-(4)-Faktor neu fixiert (vor dem Pilot).

## 6a. Gate (4) (Negativ-Panel), mechanische Form (Vorlage, Festlegung (f))

Je Negativ-Symbol s in {XRPUSDT, BNBUSDT}: Residual-Rendite r_res,s = r_pre,s - beta_s x r_pre,BTC (r_pre wie A2 auf den
1-min-Kerzen von s; beta_s = OLS-Steigung der 30-min-Slot-Renditen von s auf BTC ueber alle Tage der Vorperiode
2021-03-24..2024-05-31, vorab fixiert, nur Streuungs-/Kovarianzgroesse); dieselben Mengen (E, P2'') und Slots wie A2,
Cluster = Tag; Kontrast Delta_s = Mittel r_res,s(E) - Mittel r_res,s(P2''), SE-Regel und J-(i)-Null (skaliert) wie A2.
**Bedingung "kein vergleichbares Delta":** -Delta_s (registrierte Richtung) liegt **nicht** ueber max(q95 der eigenen
J-(i)-Null; z_krit x SE_s) - fuer beide Symbole; sonst ist Gate (4) verfehlt (Wochentags-/Uhrzeit-Artefakt, PRD
Kill-Bedingung (5)). **Power-Faktor:** unter einem echten BTC/ETH-Effekt und vollstaendiger Residualisierung ist Delta_s
null, die Bedingung haelt mit 0,95 je Symbol, 0,9025 fuer beide (Unabhaengigkeit angenommen) - **UNBELEGT bis zu den
Daten** (Rest-Spillover und Korrelation der Panel-Symbole koennen ihn senken). Folge: MDE80prod und c_A2 steigen um
+2,4 / +2,8 bp (W1 / W2, stress; T10 "ohne gate4" gegen R0). Gabelung P-G8: Gate (4) auch auf der Pilotstufe pruefen
(Strenge) - nicht im Default.

## 7. Etikett "Lockerung" (ausformuliert)

"**Zuerst:** Beim einzigen belegten Prior (16,5 bp) uebergibt die Route mit ~2,7 % (Kontrast) bzw. ~0,5 %
(Ereignis-Skala) (Fassung 1; mit den Festlegungen des Orchestrators 0,01 % bzw. < 0,01 %); mit ~97 % (bzw. praktisch
sicher) ist die Vorperiode danach verbraucht und A2 endet in GL-012 (Pilot). Ein 16,5-bp-Effekt ist auf
12-Monats-Fenstern unter C10 in keiner DEC-konformen Lesart testbar (MDE80prod >= 22,8 bp; mit den Festlegungen 29,0 /
32,1 bp). **`a2_vorarbeit.json` (Commit 363f3d9) speichert implizit** (Varianzzerlegung ALL/FRI/NONFRI, NONFRI/MODO/WE,
FRI/FRI_W/FRI_MQ) die Betraege von Lage-Differenzen auf r_pre der Vorperiode; |x_P| ist daraus auf zwei Kandidaten
bestimmbar; niemand hat die Kombination gebildet - die Ergebnisblindheit der Vorperiode haengt nur an Disziplin (dazu
G-C9: P3fix-Vereinigung gegen Teil B, 15:30-Slot).
**Lockerung (Richtung Testbarkeit)** der PRD-5.2-Vorbedingung 'V-5 belegt eine Effektgroesse fuer die gewaehlte
Ereignismenge': fuer A2 (D_i, DEC-103) wird der fehlende Literaturbeleg (V-5b UNBELEGT) durch eine eigene, vorab
registrierte Messung auf dem Pilot-Schaetzfenster 2021-03-24..2024-05-31 ersetzt (DEC-99 (2a)); der Pilot ist nicht
urteilstragend ('Pilot, nicht urteilstragend; Screening, nie Konfirmation', C.17/C.18). Beschlossen nach Kenntnis der
A2-Nuisance (Teil A/B/C: Streuung, Null-SD, Rauschboden, Pilot-Power-Tabelle) und ohne Kenntnis eines A2-Mittels. Preis:
(1) die Vorperiode ist danach fuer A2 und jede korrelierte Statistik verbraucht (DEC-99 (5)); (2) die
Literaturstichprobe Weiss et al. 2021-2023 [sek], aus der die registrierte Richtung stammt, liegt im Pilotbereich - eine
Uebergabe ist keine unabhaengige Bestaetigung (C.17); (3) die Nuisance der Power-Zeile stammt aus demselben Abschnitt.
Die Uebergabeschwelle kann durch den Pilot nur steigen; Fehlerraten und Power-Ziel des Tests sind unveraendert."

## 8. Entscheidungsvorlagen (C-4)

**An erster Stelle (A-9):** Beim einzigen belegten Prior (16,5 bp) uebergibt die Route mit ~2,7 % / ~0,5 % (Fassung 1),
mit den Festlegungen mit 0,01 % / < 0,01 %; danach ist die Vorperiode verbraucht und A2 endet in GL-012 (Pilot). Ein
16,5-bp-Effekt ist auf 12-Monats-Fenstern unter C10 in keiner DEC-konformen Lesart testbar (MDE80prod >= 22,8 bp; mit
den Festlegungen 29,0 / 32,1). Teil B (Commit 363f3d9) traegt den Lage-Kanal B-2; die Blindheit der Vorperiode haengt an
Disziplin.

**EV-P0 Default bei Stille (empfohlen):** Vorbereitung ja - Review dieser Fassung, Bau des Code-Pakets (T0-T7) und der
Positivkontrolle, Trockenlauf nur auf synthetischen Daten; alles reversibel. **Registrierung und Pilotlauf erst nach
ausdruecklicher Zustimmung des Nutzers** (PRD Par. 8, wie DEC-99). Bis dahin bleibt A2 GL-012 vor der Registrierung.

| Option | Inhalt | Folge | Richtung |
|---|---|---|---|
| **P-0 (Default)** | Vorbereitung, keine Registrierung ohne Nutzer-OK | A2 GL-012 bis zur Entscheidung; nichts verbraucht | reversibel |
| P-1 | Pilot-Route registrieren (R0, nach Nutzer-OK und nach den Negativ-Panel-Daten) | Uebergabe erst ab ~32 bp Pilot-Kontrast; Vorperiode verbraucht | Lockerung |
| P-2 | A2 bleibt GL-012, nur Aufzeichnung | kein Verbrauch | Strenge |
| P-3 | blindes Fenster ab 2026-07-01 (Reihenfolge-Frage DEC-98 E4 (b)) | Kollision mit Blind-Siegel DEC-96 E3 | neutral, kostet Siegel-Zeit |
| P-4 | V-5b-Volltexte nachliefern | laut Nutzer nicht kostenfrei beschaffbar | - |

**Was fuer eine Registrierung (P-1) noch fehlt:**
1. **Negativ-Panel-Daten** XRPUSDT/BNBUSDT 1-min 2021-03-24..2026-06-28 (Datenauftrag DEC-103 E5); beta aus der
   Vorperiode fixiert; gemessener Gate-(4)-Faktor ersetzt 0,9025 (nur nach oben in c_A2).
2. **Code T0-T7:** Kalender/Klassen PIT, Mengen, r_pre, SE-Regel, J-(i)-Null mit Waechter und Skalierung, Gate
   (Konjunktion, Null-Bedingung, Gate (4), Produkt-Zuordnung), Pilot-Modus mit Schnitt <= 2024-05-31, Genau-ein-Pilot-
   Sperre mit Versuchsmarker, R0 als reine Funktion (T4), adversariales Fixture (Gate (6)), DEC-39-Trio, DEC-53-Artefakte;
   Vorgaben A-8 (Labelmatrix nur intern, Kanal-Test R-C12a auch dateiuebergreifend, tau95 exakt).
3. **Positivkontrolle** (Abschnitt 6) gebaut und synthetisch trocken gelaufen.
4. **YAML mit Pins:** sha256 der Kerzen, des Kalenders, beider Funding-Extrakte, des Negativ-Panels; Konstanten T3/T10;
   Seeds; R0 als Text = Code-Konstante; Schutzregel G-C8.
5. **Entscheidungen vor jeder Zahl mit Prior:** F-1..F-4 (Default F-1), G-C1..G-C10, P-G1..P-G8, Umgang mit B-2 und G-C9
   (Abweisungsliste, A-2).
6. Review dieser Fassung, Orchestrator-Nachrechnung, Gate-Review ohne offenes VETO, Nutzer-OK.

**Gabelungen der Pilot-Regel (mit Richtung):**

| Nr. | Gabelung | Default / Festlegung | Alternative | Richtung der Alternative |
|---|---|---|---|---|
| P-G1 | Prior-Lesart | A: pi = -x_P,P2'' fuer alle Bedingungen | OI: P3 mit pi / 0,842 (Schwelle auf x_P 31,3 statt 32,1) | Testbarkeit |
| P-G2 | k_pred | Festlegung (b): k_pred,W = SE_T,W / SD_null,W (U-4 woertlich, konsistent mit der skalierten Test-Null) | k = 1 (unskaliert, Fassung 1) | Testbarkeit (29,3 -> 27,2 ohne Gate (4)) |
| P-G3 | Null-Bedingung im Produkt | Festlegung (a): eigener Faktor | R1 bivariat (31,5) / R2 ohne (28,2) | Testbarkeit (Bericht) |
| P-G4 | Zielregime der Uebergabe | nur C10 | auch DEC-52-Zweig | Testbarkeit |
| P-G5 | Vorzeichen-Bedingung (i) | alle drei Pilot-Kontraste negativ | nur P2'' | Testbarkeit |
| P-G6 | W2-Wochen ohne P2''-Partner | F-1 | F-4 / F-3 | Testbarkeit / Strenge |
| P-G7 | t_min | 2,0 (redundant, t ~ 7,8) | entfaellt | neutral |
| P-G8 | Gate (4) auf der Pilotstufe | nein | ja | Strenge |
| P-G9 | Selektionsrobuste Schwelle | R0 | R5: x_P - 0,8416 SE_P >= c_A2 (35,6) | Strenge |
| P-G10 | Kalibrierung | Festlegung (c): stress | zentral (28,8) | Testbarkeit (Bericht) |

## 9. Was NICHT folgt

- Kein Verdikt, kein Prior, keine Pilot-Zahl; keine Registrierung; DEC-99/DEC-103 unveraendert.
- Die Pilot-Power-Zahlen sind keine Aussage ueber den Effekt, nur ueber Regel und Rauschboden.
- Der Gate-(4)-Faktor ist eine Annahme bis zu den Daten; c_A2 = 32,1 ist vorlaeufig und kann nur steigen.
- Eine Uebergabe waere keine Bestaetigung (Pilot nicht urteilstragend; Literaturstichprobe im Pilotbereich).
- Die PK ist ein Design, kein Bau; ihre erwartete PASS-Quote ist eine Modellzahl.

## 10. Reproduktion

`c3_pilot.py` liest nur `work/c1.json` (sha256 in `[aj-C:teil_C3.c1_sha256]`) und benutzt die Power-Funktionen aus
`c1_nullsim.py` und `power_p1.py`; keine Daten, kein Mittel. Zwei Laeufe bitgleich; `work/c3.json` 797b881c2c16338ae2f6b6bea6e0ecdd6b1f6894f2cefba6be8d12c6f7870375; **`a2_teilC.json` (Fassung 2) sha256 8c01d72ece18e1c607b7ef585a88bef2ea19bca87c422c9e229780354bd17687**; Skripte und Eingaben wie `NULL_SIMULATION_A2.md` Abschnitt 9.

## Aenderungen gegen Fassung 1

1. **A-9 / A-2:** Pilot-Power-Satz des Reviews und B-2-Befund an erster Stelle in Abschnitt 0, 7 und 8; G-C9 ergaenzt.
2. **Festlegungen (a)-(f):** R0 registrierbar mit Stress-Linie, skalierter Null (k_pred,W fensterweise, U-4 woertlich)
   und Gate-(4)-Faktor; c_A2 32,1 (vorlaeufig) statt 24,4; R1/R2 Bericht, R5 strengere Alternative; Pilot-Power fuer
   beide Linien; Fehlerraten neu; PK-Kriterium (b) 0,763 mit Gate (4) in der Kette; Gate (4) mechanisch (Abschnitt 6a).
3. **B-9 (b):** Tabelle T10 trennt die OI-Lesart (Schwelle auf x_P) von den Ereignis-Skala-MDE.
4. **A-7:** Funding-Termin an allen Pilot-Tagen belegt (NULL_SIMULATION Abschnitt 6).
5. Neue sha256 von `a2_teilC.json` (Fassung 1: 5741d90c..., verworfen).
