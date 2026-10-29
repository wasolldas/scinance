# A2-Vorarbeit: Entscheidungsvorlagen (Design, Gabelungen mit Richtung, was fuer eine A2-Feasibility fehlt)

> **Fassung 2 (2026-10-29) nach REVIEW_A2_VORARBEIT.md: Auflagen A-1..A-6 eingearbeitet.** Zahlen der
> Fassung 1 unveraendert (Rundung vereinheitlicht: SE zwei Stellen, MDE80 eine Stelle, W1 als Hauptwert, W2 in
> Klammern, wo die Rundung abweicht); Neues am Ende unter "Aenderungen gegen Fassung 1".
> ENTWURF der Herleitung, Stand 2026-10-29. Vorlagen fuer den Orchestrator; **nichts beschlossen, nichts registriert,
> kein Verdikt.** Optionsneutral: keine Vorlage setzt eine Reihenfolge der Blindperiode voraus. Zahlen aus
> `PLACEBO_DESIGN_A2.md` (Teil A), `NUISANCE_SIGMA30.md` (Teil B) und `a2_vorarbeit.json` (Kuerzel wie dort).
> Etikett wie Teil A/B: kein Mittel, kein Vorzeichen einer Verfallstag-Rendite.
> **C.17 (Fassung 2):** unzentrierte Betrags-Quantile und 1,4826 x MAD je Klasse/Jahr/Serie wurden gesehen und
> ausgegeben, in Fassung 1 auch fuer die gepaarte Differenz-Reihe r_pre - r[15:30] (in Fassung 2 aus dem JSON
> entfernt, A-6); daraus wurde kein Lagewert abgeleitet. **W1/W2-Inventur:** die 2.0-Hypothesen H-01..H-18 sahen
> Bybit/Deribit-Daten 2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter die
> 08:00-Slots 2026-03-27..2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al.
> (2021-2023) liegt vor W1.

## 0. Ausgangslage in drei Saetzen

Seit 2020-03-25 ist jeder Kalendertag ein Verfallstag mit TWAP 07:30-08:00 UTC; die PRD-Placebos "verfallsfrei" sind
leer, jeder registrierbare Kontrast ist ein Groessen-Kontrast (Teil A 2). Ein Freitag traegt das 6..13-fache der
gelieferten Kontrakte eines Mo-Do-Tages, ein Monats-/Quartalsfreitag das 3,2..3,8-fache eines Wochen-Freitags (Teil A 3). Die gemessene
Nuisance ist unguenstiger als die PRD-/Bilanz-Arbeitswerte (MDE80 woechentlich 18,2 (18,3) statt 12,8 bp, monatlich 49,0
statt 28,0 bp je 12-Monats-Fenster) (Teil B 6.2); gegen den ganzen Placebosatz steigt die woechentliche MDE80 auf 19,8
(gemeinsam) bzw. 21,9 bp (Produkt, Zuordnung) (Fassung 2, Teil B 6.5).

## EV-A Ereignismenge und urteilstragender Kontrast

| Option | Inhalt | SE / MDE80 P-1 je Fenster | Richtung | Empfehlung |
|---|---|---|---|---|
| **A-1 (D_i)** | alle Freitage (W+M+Q, 52) gegen Mo-Do [07:30, 08:00) (208 (207)); Placebosatz {P2', P3fix, P3all}, bindend P2' | 7,34 / 18,2 (18,3) bp; Satz: gemeinsam 19,8, Produkt 21,9 | Referenz | **empfohlen** |
| A-2 (D_i_W) | nur Wochen-Freitage (40) gegen Mo-Do | 8,06 / 20,0 (20,1); Satz: 21,6 / 24,2 | Strenge (+10 % SE), reinere Klasse | Alternative |
| A-3 (D_ii, PRD-Variante (b)) | Monat+Quartal (12) gegen Wochen-Freitage (40) | 19,70 / 49,0; Satz: 51,4 / 61,1 | Strenge gegen jede Freitags-Variante (N 12; P1' traegt selbst Wochenverfaelle, Abschwaechung 0,687) - in jeder Linie GL012 | nicht tragfaehig (GL012 auf jedem Gitterpunkt, auch 16,5 bp [sek]) |
| A-4 (PRD_a, PRD-Variante (a)) | alle Freitage gegen alle Nicht-Freitage inkl. Wochenende | 6,90 / 17,2; mit P3 (PRD: "P2 und P3"): 17,9 / 19,0 / 21,4 | Testbarkeit (-6 % SE) gegen A-1, mit Wochenend-Liquiditaetsregime im Placebo | nicht empfohlen |
| A-5 (D_iii) | OI-Quintile | 6,72 / 16,7 (Bericht) | ex post | nicht registrierbar |

Begruendung A-1: groesste kalenderfixierte Ereignismenge; Uhrzeit, TWAP-Mechanik und Bybit-Funding-Termin in Ereignis und
Placebo gleich; Kontrast-Prior nach OI-Proportionalitaet 0,84..0,92 des Ereignis-Effekts (wenig Verduennung); Wochenende
ausgeschlossen (SD 0,82x, andere Liquiditaet). **Default bei Stille: A-1**, mit Etikett "Groessen-Kontrast (Freitag gegen
Tagesverfall), Wochentagseffekte nicht getrennt".

## EV-B Placebosatz und bindende Regel

- B-1 (Default): PRD 5.2 woertlich - Signifikanz gegen alle Placebos, bindend der groesste SE (bei A-1: P2', SE 7,34).
- B-2 (Praezisierung, Richtung Strenge): bindend ist der Placebo mit der **kleinsten Fenster-Power** unter dem
  Kontrast-Prior (P2' traegt den abgeschwaechten Prior, P3 den vollen) - bei A-1 dasselbe Ergebnis (P2'), bei anderen
  Designs nicht zwingend. Empfohlen als Klarstellung, weil "groesster SE" gleiche Prioren unterstellt.
- B-3 (Richtung Strenge): gepaarter Freitags-Slot [15:30, 16:00) als zusaetzlicher Placebo (D_i_s) - kontrolliert
  Wochentagseffekte (P1 ist leer), SE 11,15, MDE80 27,7; selbst 25 bp GL012. Nur waehlen, wenn Wochentagseffekte als
  Hauptgefahr gelten; die Wahl des Paarungs-Slots (15:30 funding-gepaart gegen [05:30, 06:00) vol-aehnlich) ist vor
  jeder weiteren Zahl zu fixieren. Fassung 2 (A-4): an Monatsend-Freitagen ist 15:30 wegen des UNBELEGTEN
  CME-Referenzfensters nicht als Paarungs-Slot zu fixieren (EV-L).
- **B-4 (Fassung 2, A-1) Groesse des Placebosatzes - Gabelung, vor jeder weiteren Zahl zu fixieren.** D_i, MDE80
  Ereignis-Skala P-1 W1, Einzel / gemeinsam / Produkt: {P2'} 18,2 / 18,3 / 18,2; {P2', P3fix} 18,2 / 19,7 / 21,0;
  {P2', P3fix, P3all} 18,2 / 19,8 / 21,9 (abgeschwaecht 21,7 / 22,1 / 23,8) [aj-K:designs.D_i__S*]. Weniger Placebos =
  Richtung Testbarkeit; PRD 5.2 verlangt P2 und P3. **Default-Vorschlag: {P2', P3fix, P3all}** (Struktur der PRD,
  Richtung Strenge); {P2', P3all} oder {P2'} nur mit Etikett "Placebosatz nach Kenntnis der Konjunktions-Power verkleinert".
- **Festlegung des Orchestrators (uebernommen):** die Zuordnung (C10/DEC52/GL012) traegt analog DEC-94 (6) das
  **Produkt** der Einzel-Powers (Untergrenze); die gemeinsame Power ist Bericht; Richtung Strenge.

## EV-C Nuisance-Linie der Power-Zeile

- C-1 (Default, Strenge): Klassen-SD der Vorperiode 2021-03-24..2024-05-31 und c_bind nach P-3-Logik (Max-Regel); dazu
  bindend nach DEC-94 (5) die groessere SE aus Vorperiode und kalibrierter Null-Simulation (Null-Simulation **noch nicht
  gebaut**).
- C-2 (Testbarkeit): c = 1 (die iid-Referenz zeigt, dass c_bind 1,15..1,46 mit c ~ 1 vertraeglich ist): MDE80 A-1 16,8
  statt 18,2 (18,3). Eine Wahl jetzt waere nach Kenntnis der Zahlen (Gabelungsmuster DEC-93 H-1) - **nicht empfohlen**.
- C-3 (Strenge, Bericht): Stress-SD 2021: MDE80 A-1 24,6 bp.
- Merkposten: die Vorperiode ist ein anderes Vol-Regime (Faktor 2,3 zwischen 2021 und 2023); W1/W2-Streuung ist nicht
  gemessen (Auftragsgrenze).

## EV-D r_pre-Definition (V-5c-Datenteil)

- D-1 (Default): r_pre = ln(close[07:59] / close[07:29]) auf Bybit-1-min-Kerzen; teleskopiert, gleiche Konvention wie
  HF-RV R-3; deckt das TWAP-Fenster 07:30-08:00 exakt (Delivery 08:00:00 + 0,04 s).
- D-2: ln(close[07:59] / open[07:30]) - auf diesen Daten identisch (open = vorheriger close an 1.161/1.165 bzw.
  1.165/1.165 Tagen); kein Unterschied in Richtung oder Strenge, nur in der Abhaengigkeit von der Open-Konvention.

## EV-E Ausreisser-Tage

- E-1 (Default, vorab fixiert in R-4): Tage mit Options-Delivery > 60 s nach 08:00 (bis 2026-06-30: 2020-08-27,
  2024-08-19) aus Ereignis- und Placebo-Mengen ausschliessen; Folge W1 Mo-Do 208 statt 209. Richtung neutral (eine
  Placebo-Beobachtung weniger).
- E-2: einschliessen (Mittelungsfenster an diesen Tagen unbekannt) - nicht empfohlen.

## EV-F Gewichtung BTC/ETH in der Cluster-Statistik

- F-1 (Default, PRD-Gate (3)): gleichgewichtet in bp, x = (r_BTC + r_ETH)/2.
- F-2 (Testbarkeit): inverse Varianz oder BTC allein (BTC-Freitags-SD 40,2 gegen Cluster 43,8) - widerspricht der
  Gate-Bedingung (3) "BTC und ETH zu einer Teststatistik gepoolt" bzw. waere eine Wahl nach Kenntnis der SDs; nicht empfohlen.
- F-3 (Testbarkeit, Merkposten): robuste Lage-Statistik statt Mittel (1,4826 x MAD ~0,6 x SD, Exzess-Kurtosis 5..10) -
  aenderte die PRD-Statistik "Mittel von r_pre"; nur vor jeder Outcome-Zahl und als neue Hypothese zulaessig.

## EV-G Fensterlage, Blind-Siegel, REZENZ (Reihenfolge-Frage)

PRD 5.2 nennt W1 = 2024-09-01..2025-08-31 und W2 = 2025-09-01..2026-08-31 (reicht in den Blindbereich ab 2026-07-01);
fuer Registrierungen ab 2026-10-20 gilt DEC-99 (8) (W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28) - alle Zahlen
dieser Akte folgen DEC-99 (8) (Fassung 2, A-6).

| Option | Fenster | Folge | Richtung |
|---|---|---|---|
| G-1 (Default) | W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28 (DEC-99 (8)), Nuisance <= 2024-05-31 | Fenster blind fuer A2 (kein r_pre-Mittel in dieser Herleitung; W1/W2-Inventur 2.0 H-01..H-18 im C.17-Kopf), DEC-94 (5) (i) erfuellbar; C10 erst ab Kontrast ~18,2 (18,3) bp gegen den Einzel-Placebo, ~21,9 bp als Produkt gegen den Satz (zentral) | Referenz |
| G-2 | laengere Fenster rueckwaerts bis 2021-03 (max. 2,65 Jahre je Fenster) | Vorperiode liegt in den Fenstern (nur Null-Simulation als Nuisance), Literaturstichprobe 2021-2023 im Urteilsbereich (C.17), ab > 1,04 Jahren Ueberlappung; rechnerisch erst ab Kontrast ~11,2 bp fuellbar (L <= 2,65 Jahre, [abg.] 18,27 / sqrt(2,65)) | Testbarkeit, nach Kenntnis dieser Zahlen -> eigene DEC mit Etikett |
| G-3 | Fenster ab 2026-07-01 (blind, prospektiv; Recording-first) | kollidiert mit dem Blind-Siegel DEC-96 E3 (A2 rechnet BTC/ETH-Renditestreuung) -> gehoert in die offene Reihenfolge-Frage (DEC-98 E4 (b)); Options-Kalender ab 2026-08 nur ueber Ersatzquellen (DEC-98 N6) | neutral, kostet Siegel-Zeit |

Keine Option wird hier gewaehlt; G-2 und G-3 brauchen eine Nutzer-/Orchestrator-Entscheidung.

## EV-H Was fuer eine A2-Feasibility noch fehlt (Reihenfolge)

1. **V-5b - Effektgroesse fuer Freitags-/Wochenverfaelle (blockierend):** einzige Quelle mit Richtung ist Weiss et al.
   (FRL 2026, Deribit 2021-2023) [sek], Groesse UNBELEGT; Volltext nicht geliefert (DEC-102). Ohne Beleg: A2 GL-012 vor
   der Registrierung (PRD 5.2 Vorbedingung). Rechnerische Schwelle fuer C10 mit A-1/G-1: Kontrast >= ~18,2 (18,3) bp
   gegen den Einzel-Placebo (zentral), Ereignis-Effekt >= ~21,7 bp bei OI-Proportionalitaet; Stress >= ~24,6 / ~29,2 bp;
   gegen den Satz {P2', P3fix, P3all} als Produkt (Zuordnung) >= ~21,9 bp, abgeschwaecht ~23,8 bp (Fassung 2).
2. **Prior-Lesart fuer einen Groessen-Kontrast:** ein Literaturwert "Verfall gegen kein Verfall" muss in "Freitag gegen
   Tagesverfall" uebersetzt werden (OI-Proportionalitaet UNBELEGT; Faktor 0,84..0,92); die Uebersetzungsregel ist vor
   jeder Zahl festzulegen.
3. **Fensterlage / Blind-Siegel (EV-G)** und die Reihenfolge-Frage der Blindperiode (DEC-98 E4 (b), offen).
4. **Null-Simulation** des registrierten Tests (DEC-94 (5) (ii)) - die PRD-Null "Zufallstermine mit identischer
   Kalenderverteilung" ist unter taeglichen Verfaellen leer; neu definiert in EV-J (Fassung 2), nicht gebaut.
5. **Negativ-Panel** (XRP/BNB, Gate-Bedingung (4)): 1-min-Daten nicht geladen; Datenauftrag erst nach V-5b sinnvoll.
6. **Funding-Intervall BTCUSDT/ETHUSDT in W2** (Auto-Switch ab 2025-10-30, DEC-84): ungeprueft; betrifft die Lesart von
   P2' (gleicher Funding-Termin nur bei 8h-Intervall).
7. **Vorzeichen-Registrierung** (PRD 5.2: "negativ zu registrieren, sobald V-5 die Ereignismenge festlegt", DEC-58 E4):
   Richtung [sek] fuer 2021-2023; fuer einen Groessen-Kontrast ist die Richtung des Kontrasts (gross minus klein) aus
   der Literatur abzuleiten, nicht aus Daten.
8. **Placebosatz fixieren** (EV-B, B-4) und die Zuordnung nach Produkt (Festlegung) in den DEC-Nachtrag (Fassung 2).
9. **Futures-Tage in P2'** (EV-K) und **CME-Primaerbeleg** (EV-L) vor jeder Fixierung eines 15:30-Slots (Fassung 2).
10. **Gate-Bedingung (4) beta-residualisiert** formulieren (EV-M, Merkposten, Fassung 2).

## EV-J Null fuer den Groessen-Kontrast (Fassung 2, A-2; nur Definition)

**Etikett "Null neu definiert nach DEC-98 N5".** Die PRD-5.2-Null (Zufallstermine mit identischer Kalenderverteilung:
gleiche Anzahl, Wochentags-, Tageszeit- und Cluster-Struktur) ist seit 2020-03-25 leer bzw. mit dem Ereignis identisch -
jede wochentagstreue Ziehung von Freitagen um 07:30 zieht die Ereignisse selbst. Vorlagen (Teil A 4a):
- **J-(i) (Default bei Stille):** Label-Permutation Freitag <-> Mo-Do innerhalb derselben ISO-Woche (erhaelt
  Wochen-Cluster, Tageszeit, Funding-Termin, Vol-Regime, Anzahl); exakt unter Austauschbarkeit; Grenze: ein reiner
  Wochentagseffekt erscheint als Effekt (wie bei P2'; Richtung Testbarkeit bezueglich Wochentags-Konfundierung).
- J-(ii): Slot-Verschiebung bei festen Tagen (andere Halbstunde, ohne [07:00, 09:00) und ohne Funding-/Referenz-Slots);
  Richtung Strenge bezueglich Wochentag und Streuung (andere Slots streuen meist staerker); Grenze: fremde Termine in
  anderen Slots.
Nicht bauen, nicht rechnen, bis entschieden; die Schwelle "max(95-%-Quantil der Null; z SE)" (PRD 5.2) haengt daran.

## EV-K Futures-Verfallstage im Placebo P2' (Fassung 2, A-3)

Taegliche Deribit-Futures-Verfaelle ab 2026-04-04: in W2 48 von 207 Mo-Do-Tagen (36 beide Waehrungen), in W1 keiner
(Teil A 3a) - P2' ist zwischen W1 und W2 nicht homogen.
- **K-1 (Default-Vorschlag): P2'' = Mo-Do ohne Tage mit Futures-Delivery in mindestens einer Waehrung** (PIT aus dem
  Instrumentnamen): N_P W1 208, W2 159; SE W2 7,58 statt 7,34, MDE80 18,8 statt 18,3 bp (Einzel), Produkt gegen den Satz
  22,2 statt 21,9 (Teil B 6.7). Richtung: Reinheit und W1/W2-Homogenitaet (schuetzt Kill-Bedingung (3) und REZENZ)
  gegen +3 % SE in W2 (Strenge in der SE).
- K-2: P2' unveraendert (alle Mo-Do) - Richtung Testbarkeit der SE, Placebo traegt in W2 einen Teil des
  Ereignismechanismus (Kontrast kleiner) und wechselt zwischen W1 und W2 seine Zusammensetzung.
Vermerk: Freitags-OI zaehlt nur Optionen; Wochen-Futures-Verfaelle fehlen -> Abschwaechungsfaktor eher zu klein (Strenge).

## EV-L CME-Referenzfenster (Fassung 2, A-4)

In der P3-Kontaminationsliste als **UNBELEGT** gefuehrt (Hinweis des Reviews: Referenzrate der CME-BTC/ETH-Futures aus der
Stunde vor 16:00 London am letzten Monatsfreitag, in GMT-Monaten [15:00, 16:00) UTC; kein Primaerbeleg in der Akte, keine
Suche/kein Download in dieser Fassung). **Folge (Default):** ein Slot [15:30, 16:00) wird an Monatsend-Freitagen nicht
als Paarungs- oder Fix-Slot fixiert, bis ein Primaerbeleg vorliegt (betrifft D_i_s, DiD, P3fix an 12 Tagen je Fenster).

## EV-M Weitere Gabelungen (Fassung 2, A-5)

| Gabelung | Inhalt | Zahlen | Richtung |
|---|---|---|---|
| M-1 Differenz-in-Differenzen | [Freitag (r_pre - r[15:30])] - [Mo-Do (r_pre - r[15:30])]; kontrolliert Wochentag und Tageszeit zugleich | gepaarte Differenz-SD Freitag 76,67 (c 1,099), Mo-Do 73,28 (c 1,360); SE 12,62 (12,63), MDE80 31,4 bp P-1 / 42,0 A3 je Fenster (Ereignis-Skala abg. 37,3); GL012 auf jedem Gitterpunkt (Teil B 6.6) | Strenge (Identifikation) gegen D_i/D_i_s; 15:30-Slot an Monatsend-Freitagen nach EV-L |
| M-2 historische verfallsfreie Baseline | 07:30-08:00 an Tagen ohne jeden Verfall (Nicht-Freitage vor 2020-02-04) | auf den Programm-Instrumenten **nicht bildbar**: BTCUSDT-1-min erst ab 2020-03-25 (nach Beginn der BTC-Tagesverfaelle 2020-02-04), ETHUSDT ab 2021-03-15 (DEC-98 N4 (d), N5); nur ueber andere Instrumente (inverse Perps, Index), Datenlage **UNBELEGT**; Aera mit kleinem Options-OI | Strenge, nicht gate-faehig; nach DEC-99 hoechstens vorab registriertes Pilot-/Zusatzfenster, sonst nur Aera-Bericht "Verfall gegen kein Verfall" |
| M-3 Beta-Residualisierung des Negativ-Panels (Merkposten Gate-Bedingung (4)) | XRP/BNB tragen Beta-Spillover aus BTC/ETH; ein echter Verfallseffekt kann im Panel erscheinen und den Kandidaten als "Wochentags-Artefakt" toeten | - (nicht gerechnet; 1-min-Daten XRP/BNB nicht geladen) | ohne Residualisierung Strenge mit Falsch-negativ-Risiko; Gate (4) auf r_XRP - beta r_BTC (beta vorab aus einer Vorperiode) vor jeder Zahl formulieren |

## EV-I Default bei Stille (vollstaendig)

A-1 (D_i), B-1 mit Klarstellung B-2, Placebosatz B-4 {P2', P3fix, P3all} mit Zuordnung nach Produkt (Festlegung),
C-1, D-1, E-1, F-1, G-1, J-(i), K-1 (P2'' ohne Futures-Tage), L (15:30 an Monatsend-Freitagen nicht fixiert), M-1..M-3 als
offengelegte Gabelungen; A2 bleibt **gesperrt** (V-5b UNBELEGT, GL-012-Fall nach PRD 5.2), kein Bau, keine
Null-Simulation, keine Registrierung. Diese Vorarbeit aendert keine Regel und keinen Beschluss.

## Aenderungen gegen Fassung 1

1. **A-1:** EV-B um B-4 (Groesse des Placebosatzes, Default {P2', P3fix, P3all}) und die Festlegung "Zuordnung nach Produkt"
   ergaenzt; EV-A mit Konjunktions-MDE80 (D_i gemeinsam 19,8, Produkt 21,9 bp).
2. **A-2:** EV-J - Null neu definiert (J-(i) Label-Permutation in der ISO-Woche als Default, J-(ii) Slot-Verschiebung).
3. **A-3:** EV-K - P2'' ohne Futures-Tage als Default-Vorschlag (W2 N_P 159, SE 7,58, MDE80 18,8 bp).
4. **A-4:** EV-L - CME-Referenzfenster UNBELEGT; 15:30 an Monatsend-Freitagen nicht fixiert.
5. **A-5:** EV-M - DiD (MDE80 31,4 bp), historische Baseline (nicht bildbar, Aera-Bericht), Beta-Residualisierung (Merkposten).
6. **A-6:** C.17-Kopf und W1/W2-Inventur; Richtung D_ii; PRD-5.2-Fenster -> DEC-99 (8); Rundung vereinheitlicht.
   Neue sha256 `a2_vorarbeit.json`: `9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052`.
