# PRD SCINANCE 3.0 - ENTWURF

**Phase:** 4 - PRD-Ausarbeitung (Opus-Entwurf, vor adversarischem Review) **Stand:** 2026-09-02 **Erstellt von:** prd-architect (Opus) **Bindende Vorlage:** `scinance3-impl/PROGRAMMENTWURF_3.0.md` (Orchestrator-Entscheidung, Abschnitte 0-7). Die dortigen Entscheidungen sind gesetzt; dieses Dokument fuellt sie aus und aendert sie nicht. **Massgebliche Quellen:** `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F), `research/REVIEW_R1_R4.md` (adversarischer Gate-Audit, vollstaendig), `research/R1..R4` (Kandidaten- und Methodik-Bloecke), `scinance2-impl/FINAL_PRD_SCINANCE2.md` (Struktur- und Praezisionsvorbild, Inhalte nicht uebernommen).

> **Belegregel dieses Dokuments.** Keine Zahl ohne Herleitung oder Quelle. Sekundaerbelege sind mit `[sek]` markiert. Wo ein Wert fehlt, steht **UNBELEGT - Vorfrage V-x** bzw. **UNGEMESSEN - WP-x**; es wird nichts geschaetzt, nichts geraten und nichts aus einem Bericht uebernommen, das der Review als fehlhergeleitet nachgewiesen hat. **Statusregel.** Dieses PRD registriert NICHTS. Alle Kandidaten in Par. 5 sind Registrierungs-ENTWUERFE. Die Registrierung erfolgt ausschliesslich durch den Orchestrator, nach Welle 1 und nach Beschluss von DEC-51/DEC-52.

---

## 1. Executive Summary

**Bilanz 2.0.** 31 Gate-Eintraege, 0 Torpfosten-Verschiebungen, **0 handelbare Kanten** (Kompendium, Programm-Bilanz). Sieben kapitalfreie Mess-WEITER (H-04, H-05b, H-11, H-15, H-16, H-23), jedes davon in der eigens dafuer registrierten Tradability-Pruefung PARK oder nie getestet (Kompendium E.10). Rund 350 GPU-Stunden (R4 K-0.7: 309-357 h) haben null registrierte Tradability-Folge erzeugt. Der einzige noch aktive Strategie-Pfad ist die gesperrte VRP-Messung H-26.

**Die vier Zahlen, die 3.0 regieren** (Entwurf 3.0 Par. 1; Herleitungen in Par. 3.6):

| Groesse | Wert | Konsequenz |
|---|---|---|
| Horizont-Friktions-Kurve (R4 K-0.1) | Mindesthorizont bei p=0,55: **6,6 h** Taker / **53 min** Maker; bei Wochen-IC 0,05: **2,7 Tage** Taker | Kein 3.0-Kandidat unter Tageshorizont, ausser als reine Kosten- oder Zensus-Messung |
| Sharpe-Nachweisdauer (Lo 2002, R4 K-0.2) | `T_min = 6,18/SR^2` Jahre; SR 0,5 -> **24,7 Jahre**, SR 1,0 -> 6,19 Jahre (mit realistischer Schiefe 11,3) | Sharpe ist NIE urteilstragend; urteilstragend ist die Praemie selbst (10^3-10^4 Beobachtungen statt 5 Jahresrenditen) |
| IC-Nachweisgrenze (R4 K-0.5) | N=5: **0,098**; N=50 bei rho_quer 0,05: 0,053; N=200 bei rho_quer 0,10: 0,064 | Das breite Universum ist Existenzbedingung der Klasse W; `rho_quer` ist die bindende, **UNGEMESSENE** Zahl (WP-7) |
| Kosten des harten Ein-Fenster-DROP (R4 K-0.6) | Bei Per-Fenster-Power 0,5 ueberleben `0,5^2 = 0,25` der echten Effekte - **3 von 4 werden verworfen** | Regelaenderung nur als eigenstaendige DEC-52 VOR jedem Kandidaten, mit den fuenf Review-Auflagen (Par. 3.4) |

**Der Pivot.** 2.0 hat sechsmal dieselbe Friktions-Arithmetik auf Sekunden- und Minuten-Horizonten gemessen (H-03, H-04b, H-05c, H-09, H-24 - alle 80-500x unter der Wand, R4 6.1b). R4 K-0.1 zeigt, dass das arithmetisch vorgezeichnet war: ein PERFEKTES 1-Sekunden-Orakel verdient 0,71 bp gegen eine 11-bp-Wand. 3.0 sucht deshalb ausschliesslich dort, wo die Wand irrelevant wird: bei **Risikopraemien** (Cashflow statt Prognose, Klasse P) und auf **Tages- bis Wochen-Horizont mit breitem Universum** (Klasse W), plus einer kalendarisch exogenen **Ereignis-Klasse** (E). Und 3.0 misst VORHER, ob die Klasse ueberhaupt testbar ist: Welle 1 ist reiner Zensus (WP-7, WP-9, WP-10, V-1..V-4), **kein Alpha-Slot ohne bestandene Feasibility**.

---

## 2. Lehren aus 2.0, die 3.0-Regeln erzeugen

Aufgenommen ist nur, was in 3.0 eine Regel erzwingt. Jede Zeile traegt den Vorfall.

| # | Lehre | Vorfall | 3.0-Regel |
|---|---|---|---|
| L-1 | Eine importierte Schwelle ohne Erreichbarkeitspruefung ist wertlos | C-14: rho-Median 2e-7 gegen importierte Schwelle 0,85, sechs Groessenordnungen (Kompendium D.2) | Feasibility-Zeile (C.12) bleibt Pflicht; **jede** 3.0-Schwelle traegt eine Herleitungs-Referenz statt eines nackten Skalars (Par. 3.3, Review 4.3b) |
| L-2 | Der strukturelle Nulleffekt der Metrik ist vor der Schwelle auszurechnen UND zu messen | H-11/GL-022: Schwelle CRPSS>=0,05 lag Faktor 4-5 unter dem Dressing-Geschenk 0,21-0,29 (Kompendium B.9) | C.4 bleibt; neu: der Nulleffekt wird zusaetzlich am Null-Fixture GEMESSEN, nicht nur hergeleitet (R4 1.0) |
| L-3 | Ein N=5-Panel traegt keine Querschnitts-Statistik | GL-012/H-07: `max\|z\| = sqrt(N-1) = 2,0 < 2,5`, DROP ohne Datenlauf | Klasse W existiert nur auf einem breiten Panel; K und rho_quer sind vor jeder Registrierung zu messen (WP-7, Par. 4.1) |
| L-4 | Mess-Gate != Tradability-Gate; die Kostenwand gehoert NICHT in die PASS-Bedingung | H-04 (kapitalfrei WEITER) -> H-04b (PARK); R4s "oekonomische Mindestmagnitude" haette H-04 zum DROP gemacht und die Information geloescht (Review 4.5) | C.2 unangetastet. Die oekonomische Mindestmagnitude wandert in die **Entscheidungsrelevanz-Zeile** (Etikett) und in das Tradability-Gate (Par. 3.3.2) |
| L-5 | Ein Gate ohne Power-Rechnung kann nicht zwischen "kein Effekt" und "kein Nachweis" trennen | 26 Registrierungen ohne eine einzige Power-Zeile; H-20 (p=0,17 bei erreichter Magnitude), H-22 (IC 0,0665 gegen Schwelle 0,10) bleiben ungeklaert (R4 6.2d) | Power-Zeile als Pflichtzeile, mit programmweit fixierter Konvention DEC-51 (Par. 3.3.1) |
| L-6 | Korrelierte Beobachtungen sind keine unabhaengigen Beobachtungen | Review 2.3/2.5/1-R1-K-07: drei Kandidaten poolen Symbole, deren Ereignis- bzw. Zustandstage identisch sind (BTC/ETH rho~0,8; K-34 "180 Dezil-Tage" real ~40; K-07 N-Floor 15 real 3,6) | Cluster-Einheit-Zeile: Resampling-Einheit ist das Kalender-Cluster; der N-Floor gilt fuer `N_cluster` (R4 1.3c, Kolari/Pynnoenen 2010) |
| L-7 | Ein Panel-Mitglied ist eine Beobachtung, keine Hypothese | H-06/H-08/H-09/H-22 zaehlten Symbol-Zellen als eigene Tests ("0 von 10 Zellen"); bei N=200 zerstoert das die Power vollstaendig (R4 1.2f) | FDR-Familien bestehen aus Hypothesen-VARIANTEN; Panel-Mitglieder werden zu EINER Teststatistik gepoolt |
| L-8 | Zwei uebereinstimmende Laeufe beweisen keinen Determinismus | GL-024: dritter Lauf traf den urspruenglichen abweichenden Wert; Ursache paralleler Float-Summation + Tie-Break in vier Loadern (DEC-34) | Determinismus-Nachweis mit N>=3 Laeufen plus Fingerprint (Testpflicht T2, Par. 3.3.11) |
| L-9 | Negative Behauptungen brauchen eine Inhaltsprobe, keine Namenskonvention | DEC-46: "kein Bybit-Options-Strom vorhanden" war falsch - die Daten lagen im `tickers`-Strom neben den Perp-Tickern (3.751 Symbole waren das Indiz) | C.8 bleibt; operativ: **Inhaltsprobe auf `bybit/tickers` VOR** jedem Spread-/OI-Zensus-Bau (WP-7, Par. 4.1) |
| L-10 | Eine daten-gated-Sperre ohne Nachladbarkeits-Probe kostet Jahre | H-26 wartet auf 210 `done_days` DVOL; die oeffentliche Deribit-API haelt DVOL ab ~2021-04, also ~1.980 statt 112 Tage (R4 3.4) | Irreversibilitaets-Regel: vor jeder daten-gated-Sperre eine dokumentierte Probe auf oeffentliche Nachladbarkeit (Par. 3.3.7) |
| L-11 | Teure Maschinerie vor der Positivkontrolle ist die teuerste Form, nichts zu lernen | H-14: 2-3 GPU-Tage verbrannt, danach an der Positivkontrolle gescheitert (GL-020) | Positivkontroll-Vorschaltung bei jeder Maschinerie mit > 1 h Laufzeit (Par. 3.3.8) |
| L-12 | Eine Hypothese, deren bestmoegliches Ergebnis nichts entscheidet, darf nicht eingeplant werden | H-14..H-17: 350 GPU-h; E.10 fuehrt H-15b/H-16b explizit als NICHT registriert und NICHT impliziert | Entscheidungsrelevanz-Zeile (Par. 3.3.2); GPU-Default 0 (Par. 3.5) |
| L-13 | Ein undefinierter Gate-Begriff ist ein offener Torpfosten | "Stress-Episode" ist in R1 G5 Gate-Bedingung mit Ausgang KEIN VERDIKT, wird aber nirgends operational definiert (Review 6.6) | Kanonische Stress-Tage-Liste, deterministisch erzeugt und als Fixture gepinnt (Par. 3.3.10) |
| L-14 | Ein Kostenmodell mit stillen Defaults ist Torpfosten-Verschiebung mit Extraschritt | Delivery-/Exercise-Gebuehr blockiert H-26b (E.6a); R1 traegt eine Sekundaerzahl ein und rechnet mit ihr (Review 3.4) | Kostenmodell-Bindung: `constants_hash` im Ergebnis; ungemessene Konstanten RAISEN statt Default (Par. 3.3.6, Par. 6) |
| L-15 | Ein Ertrag ohne Kapitalbasis ist nicht vergleichbar, und ein Netto-Ertrag ohne Steuer ist keine Netto-Aussage | In allen vier Berichten kein einziges Mal Kapitalbindung oder Steuern gerechnet (Review 6.1/6.2/6.3) | Kapital-, Steuer- und Venue-Zeile bei jeder Praemien-Registrierung (Par. 3.3.9) |
| L-16 | Die REZENZ-Klausel wird formal, nicht inhaltlich angewendet | Alle vier Berichte legen Fenster hinter Mitte 2024, keiner fragt, ob der ZAHLER nach dem Spot-ETF-Start noch existiert (Review 6.5) | Zahler-Zeile: jede Praemien-Registrierung benennt den Zahler und den Grund, warum er nach 2024 noch zahlt (Par. 3.3.9c) |

---

## 3. Verfassung 3.0

### 3.1 Unveraendert uebernommen: C.1-C.19

Die 19 Methoden-Lehren des Kompendiums (Abschnitt C) gelten unveraendert und vollstaendig. Sie werden hier nur benannt, nicht neu formuliert; der Wortlaut im Kompendium ist normativ.

| ID | Regel (Kurzform) | Erzwingender Vorfall |
|---|---|---|
| C.1 | Registry-Disziplin, Pre-Registration, append-only, kein Torpfosten-Verschieben - symmetrisch auch fuer unliebsame PASS | 31 GL-Eintraege, H-11/DEC-31 |
| C.2 | **Mess-Gate != Tradability-Gate** | H-04 -> H-04b, H-05b -> H-05c |
| C.3 | Anti-Gaming-Klausel: Wand, Latenz-Haircut, Fill-Annahme vor dem Lauf fixiert, nie absenkbar | DEC-13/16 |
| C.4 | Struktureller Nulleffekt VOR der Schwellenfestlegung | H-11/GL-022, DEC-31/33 |
| C.5 | Positives UND negatives synthetisches Fixture (DEC-39-Pflicht) | H-24 |
| C.6 | Materialitaets-Schranke statt Bit-Identitaet gegen lebende Speicher, plus SHA-256-Fingerabdruck | H-11c, DEC-32 |
| C.7 | N=2 beweist keinen Determinismus | GL-024, DEC-34 |
| C.8 | Inhaltsprobe statt Namensschluss bei negativen Behauptungen | DEC-46 |
| C.9 | Keine n=1-Extrapolation ohne Kontrolle der erzeugenden Achse | WP-5, DEC-44 |
| C.10 | Hartes Ein-Fenster-Abbruchkriterium | PRD 2.0 Par. 8.5, H-20 |
| C.11 | Modul != Strategie (Forensik-Disziplin) | CS-01/CS-02 |
| C.12 | Struktureller A-priori-DROP vor jedem Datenlauf pruefen (GL-012-Check) | H-07 |
| C.13 | Positivkontrolle als Pflichtbestandteil komplexer Mess-Maschinerien | H-14/GL-020 |
| C.14 | Loud-Fail-Doktrin | GL-018, GL-029, DEC-46 |
| C.15 | Checkpoint-Round-Trip, nicht nur Rechenpfad | GL-030 |
| C.16 | Zweistufige FDR ueber Kohorten (Familie -> Ueber-Familie) | DEC-22 |
| C.17 | Data-Snooping-Offenlegung + Entdeckungszellen-Ausschluss | H-05b |
| C.18 | REZENZ-Klausel: urteilstragende Fenster decken das juengste Regime ab | Welle-6-Querbefund, DEC-38 |
| C.19 | Reversibelste-Option-Prinzip bei Unterspezifikation, nie fuer Gate-Schwellen | DEC-03..DEC-18 |

**Ausdrueckliche Bestaetigung zu C.2 (Entwurf 3.0 Par. 2.1, Review 4.5):** R4s Vorschlag, eine oekonomische Mindestmagnitude in die PASS-Bedingung des Mess-Gates aufzunehmen (`mean >= max(strukturelle Null, oekonomische Mindestmagnitude)`, R4 1.1c), wird **ABGELEHNT**. Unter dieser Regel waere H-04 (BTC->ETH-Lead-Lag, kapitalfrei WEITER, Tradability PARK) ein DROP gewesen - und DROP ist endgueltig und append-only; die Information "gerichtete Information existiert" waere geloescht worden. Die Mindestmagnitude wandert vollstaendig in die Entscheidungsrelevanz-Zeile (3.3.2) und in das Tradability-Gate (Par. 6).

### 3.2 Die drei Hypothesen-Klassen von 3.0

3.0 kennt genau drei Klassen; jede Registrierung nennt ihre Klasse, weil Gate-Form, Nulleffekt-Katalog und Fixture-Katalog daran haengen (R4 1.1-1.3).

- **Klasse P - Praemien-Ernte.** Ertragsquelle ist ein Erwartungswert-Keil zwischen zwei beobachtbaren Preisen (Funding, VRP, Skew, Term-Wedge), kein Vorzeichen-Forecast. Urteilstragend ist `mean(prem)`, nie der Sharpe (Par. 3.5). Nulleffekt-Katalog: Jensen-/Konvexitaets-Term, Ueberlappung, Peso-Term, Selektions-Decke, MaxDD-Boden, Tail-Ratio-Richtungsfehler (R4 1.1b).
- **Klasse W - Wochen-Horizont-Querschnittsfaktoren.** Urteilstragend ist der Querschnitts-Rank-IC bzw. die Dezil-L/S-Rendite. Nicht ueberlappend messen (R4 1.2a); Nulleffekt-Katalog: Querschnitts-Permutations-Null, Persistenz-Null (Valkanov 2003 / Boudoukh-Richardson-Whitelaw 2008), Selektions-Decke (R4 1.2b).
- **Klasse E - Ereignis-Studien.** `CAR` ueber genau EIN vorregistriertes Fenster, kein Fenster-Scan. Nulleffekt ist die Placebo-Verteilung auf Zufallsterminen mit identischer Kalenderverteilung. Resampling-Einheit ist das Kalender-Cluster (R4 1.3).

### 3.3 Die zehn neuen Pflichtzeilen jeder 3.0-Registrierung

Jede der zehn Zeilen ist durch einen konkreten Programm-Vorfall erzwungen (Par. 2). Eine Registrierung ohne vollstaendige zehn Zeilen ist kein gueltiger Registry-Eintrag und ein Lauf darauf ist kein gueltiger Lauf.

**3.3.1 Power-Zeile.** Welchen Effekt kann das registrierte Fenster mit Power 0,80 ueberhaupt sehen? Die Zeile nennt ausdruecklich alpha, Seitigkeit, Power, die Cluster-Einheit und die detektierbare Effektgroesse mit Rechenweg.

> **DEC-51 (Entwurf) - Programmweite Power-Konvention.** Weil R1-R4 drei verschiedene Konventionen benutzen (Review 3.10: R2 zweiseitig alpha=0,05 -> z=2,802; R4 einseitig -> z=2,4865; R3 "~2 Rauschboeden" ohne genannte Power; `(2,4865/2,802)^2 = 0,79`, also wuerde R2s K>=169 unter R4s Konvention zu K>=134) gilt ab sofort und fuer alle 3.0-Mess-Gates:
> - **alpha = 0,05, EINSEITIG** (die Richtung des Effekts ist bei jedem 3.0-Kandidaten vorab aus dem Mechanismus festgelegt und wird mitregistriert; ein Vorzeichenwechsel ist damit ein Falsifikator, kein halber Erfolg),
> - **Power = 0,80**,
> - daraus `z_krit + z_power = 1,6449 + 0,8416 = 2,4865`,
> - **Cluster-Einheit und effektives N werden benannt** (3.3.3); die Power-Rechnung laeuft auf `N_eff`, nie auf dem Roh-N.
> - Fuer FDR-Familien mit mehr als einem Test wird die Power zusaetzlich nach BH auf der registrierten Familiengroesse ausgewiesen.
> - **Gueltigkeitsbereich:** Mess-Gates der Klassen P, W, E. Tradability-Gates behalten ihre eigenen, in der jeweiligen Registrierung hergeleiteten Konventionen.

**3.3.2 Entscheidungsrelevanz-Zeile.** Was aendert ein PASS konkret - naechster Schritt, Kapitalpfad, Tradability-Folge? Was schliesst ein DROP? Die Zeile enthaelt die **oekonomische Mindestmagnitude** aus der Horizont-Friktions-Kurve (R4 K-0.1) als **ETIKETT, nicht als Gate** (C.2, Review 4.5). Ein Kandidat, dessen bester Fall unter der Wand liegt, ist registrierbar, traegt aber das Etikett und verbraucht bewusst einen Alpha-Slot - das ist eine Entscheidung, keine Nebensache (Fall A2 / R3-K-31, Par. 5.2).

**3.3.3 Cluster-Einheit-Zeile.** Resampling-Einheit und effektives N. Verbindlich: **Pooling korrelierter Symbole ueber dieselben Kalendertage zaehlt als EIN Cluster** (Kolari/Pynnoenen 2010 [sek] via R4 1.3c; Review 2.3/2.5 - drei Kandidaten hatten das falsch). Der registrierte N-Floor gilt fuer `N_cluster`, nie fuer `N_events`. Die Umrechnung wird explizit gerechnet: `N_eff = N_c / (1 + (N_c - 1) * rho)` mit benanntem und belegtem `rho`.

**3.3.4 Selektions-Deflation.** Die Zahl der gerechneten Varianten `K` wird VOR dem Lauf registriert; die Schwelle liegt ueber der Bailey/Lopez-de-Prado-Decke fuer dieses K (R4 K-0.3): `E[max SR] ~= sigma_SR * ((1-g)*Phi^-1(1-1/K) + g*Phi^-1(1-1/(K*e)))`, `g = 0,5772`, `sigma_SR ~= 1/sqrt(T)`. Bei T=5 Jahren: K=5 -> 0,53; K=20 -> 0,85; K=50 -> **1,02**; K=100 -> 1,13. Zusaetzlich wird die Decke **empirisch am Null-Fixture gemessen**: die komplette Selektions-Pipeline ueber alle K Varianten laeuft auf dem Null-Fixture, ihre Bestwert-Verteilung ist die gemessene Decke (R4 1.1d - genau dieser Schritt fehlte bei H-11).

**3.3.5 Drittes, adversariales Fixture.** Neben Positiv- und Null-Fixture (DEC-39) ein drittes, das ein BEKANNTES Artefakt so praesentiert, dass die Metrik positiv aussieht. Je Klasse vorgeschrieben:
- Klasse P: **Peso-Fixture** - Nullpraemie plus Merton-Spruenge, Rate 1/3 Jahre, Hoehe -35 %. Ein 5-Jahres-Fenster ist mit `p = e^-1,67 = 0,19` sprungfrei und zeigt dann eine scheinbar hohe, hochsignifikante Praemie. **Das Gate MUSS hier durchfallen** (R4 1.1d).
- Klasse W: ein Faktor, der mechanisch mit dem Markt-Beta korreliert, auf einem Panel mit dominantem Marktfaktor - in Krypto ist praktisch alles Beta zu BTC (R4 1.2e).
- Klasse E: Ereignisse, die auf VERGANGENEN Renditen selektiert werden, auf einem reinen Random Walk - erzeugt scheinbare Mean-Reversion; exakt die Fehlerklasse H-20 (R4 1.3d).

**3.3.6 Kostenmodell-Bindung.** Jedes Ergebnis traegt den `constants_hash` (SHA-256 ueber `tradability3/constants.py`) der verwendeten Kostenkonstanten. Ein Lauf, dessen Hash nicht dem in der Registrierung zitierten entspricht, ist **kein gueltiger Lauf**. Das macht C.3 maschinell pruefbar. **Ungemessene Konstanten RAISEN, sie erhalten keinen stillen Default** (Par. 6).

**3.3.7 Irreversibilitaets-Regel.** Vor jeder daten-gated-Sperre eine dokumentierte Probe auf oeffentliche Nachladbarkeit (H-26/DVOL-Lehre, L-10). Umgekehrt gilt fuer den Harvester: **nur Irreversibles rechtfertigt einen Dauerstrom** (Anti-Data-Lake, Par. 7.2). Eine Sperre, die ohne Nachladbarkeits-Probe gesetzt wurde, ist zu protokollieren und die Probe nachzuholen; das Verdikt selbst bleibt unberuehrt (append-only).

**3.3.8 Positivkontroll-Vorschaltung.** Bei jeder Maschinerie mit > 1 h Laufzeit laeuft die Positivkontrolle **ZUERST und allein**, als billiger T1-Schritt; ihr PASS ist Vorbedingung fuer die Einplanung des teuren Laufs (R4 4.4.5; haette H-14s 2-3 GPU-Tage verhindert, eine Stundengrenze haette es nicht).

**3.3.9 Kapital-, Steuer- und Venue-Zeile** (Pflicht bei jeder Praemien-Registrierung):
- (a) **Rendite auf gebundenes Kapital**, nicht auf Notional. Jede Ertragsangabe traegt ihre Kapitalbasis (Review 6.1). Solange die Bybit-Margin-Regeln fuer dieses Programm ungemessen sind, wird als Kapital-Multiplikator `m` mit Pflicht-Sensitivitaet gerechnet - **UNGEMESSEN, eigener WP** (R4 2.2 `capital.py`).
- (b) **Steuerliche Behandlung der Cashfluesse.** Funding ist laufender Ertrag; Spot- und Derivate-Bein einer delta-neutralen Position werden unterschiedlich behandelt (Review 6.2). Eingangswerte kommen vom Nutzer - **UNBELEGT, offene Nutzer-Entscheidung Par. 8.2**; bis dahin wird die Zeile mit "Steuerregime UNBELEGT" gefuehrt und jede "netto"-Aussage traegt diesen Vorbehalt.
- (c) **Venue-Ereignis und Zahler-Bestand.** Boersen-/ADL-/Auszahlungsstopp-Risiko wird benannt; bei einer Kante von 5-10 % p.a. ist eine Ereigniswahrscheinlichkeit von 1 %/Jahr fuer Totalverlust ein Abschlag von 10-20 % auf den Erwartungswert (Review 6.3, Rechnung dort). Zusaetzlich: **existiert der ZAHLER nach 2024 noch?** (Review 6.5 - Spot-ETF-Start und zugefuehrtes Basis-Arbitragekapital).

**3.3.10 Stress-Episode - kanonische Definition.** "Stress-Episode" war in R1 G5 Gate-Bedingung mit Ausgang KEIN VERDIKT und nirgends operational definiert - ein offener Torpfosten mitten in der Verfassung (Review 6.6). Verbindliche Definition, vorab fixiert und als Fixture gepinnt:

> **DEC-53 (Entwurf) - Stress-Tage-Kanon.** Ein Kalendertag ist ein **Stress-Tag**, wenn seine aus dem WP-0-Bar-Cache berechnete Tages-RV ueber dem **97,5-Perzentil der juengsten 24 Monate** liegt (rollierend, jeweils gegen das Fenster, das am Vortag endet - keine Vorwaertsschau). Zusaetzlich sind die namentlich benannten Ereignisse **10.10.2025** und **19.08.2026** immer Stress-Tage. Eine **Stress-Episode** ist eine maximale Kette von Stress-Tagen mit hoechstens einem Nicht-Stress-Tag Unterbrechung; die Episode ist die Cluster-Einheit (3.3.3). Die Liste wird EINMAL deterministisch erzeugt, SHA-256-gepinnt und als Fixture abgelegt; sie wird nie nach dem Sehen eines Ergebnisses veraendert. Groessenordnung: 24 Monate = ~730 Tage, 2,5 % = **~18 Tage**, wegen der RV-Persistenz zu erwarten in **~6-10 Episoden** (die Episodenzahl ist die urteilsrelevante Groesse, nicht die Tageszahl - siehe WP-10, Par. 4.3).

Ein urteilstragendes Fenster einer Klasse-P-Registrierung muss **>= 1 Stress-Episode** enthalten; fehlt sie, ist das Verdikt **KEIN VERDIKT**, nicht WEITER (R1 G5, R4 1.1d).

**3.3.11 Zusatz: Test-Pflichten je 3.0-Research-Modul** (R4 5.4, unveraendert uebernommen, weil jede Stufe durch einen Vorfall erzwungen ist):

| Stufe | Inhalt | Vorfall |
|---|---|---|
| T0 | Unit-Tests der reinen Funktionen auf synthetischen Eingaben | Standard |
| T1 | Drei Fixtures als echte Tests: positiv, null, adversarial | DEC-39, erweitert (3.3.5) |
| T2 | Determinismus mit **N>=3** Laeufen plus Fingerprint-Vergleich | DEC-34 / C.7 |
| T3 | Checkpoint-Round-Trip: schreiben, abbrechen, laden, bit-identisch fortsetzen | GL-030 |
| T4 | Gate-Arithmetik-Test: die Gate-Entscheidungsfunktion liefert auf einem konservierten Ergebnis-Payload das registrierte Urteil | neu - macht das Gate maschinell pruefbar |
| T5 | Kosten-Konstanten-Pin (`constants_hash`) fuer jedes Tradability-Modul | DEC-13/16 |
| T6 | Legacy-Import-Sperre fuer 3.0-Module | UMBAU_SPEZIFIKATION |

### 3.4 Registrierungs-Template mit YAML-Block

**Format-Entscheidung (Entwurf 3.0 Par. 2.4).** Der Markdown-Eintrag bleibt der **normative Text**; in ihn wird ein gezaunter YAML-Block eingebettet, der die maschinenlesbare Teilmenge haelt. **Eine Datei, eine Wahrheit.** Die 2.0-Registry wird **NICHT migriert** (sie ist append-only und urteilstragend; sie nachtraeglich anzufassen waere ein schwererer Fehler als jeder Komfortgewinn - R4 5.3, Review 4.3).

> **DEC-54 (Entwurf) - Registry-Format 3.0**, mit den drei Review-Auflagen (4.3a-c): (a) Der Linter unterliegt selbst der Loud-Fail-Doktrin (C.14): er darf **nie still durchwinken**, wenn er den Block nicht parsen kann. (b) **Pflichtfelder duerfen keine Haekchen werden.** `structural_null: 0` erfuellt einen naiven Parser und ist schlimmer als nichts. Der Linter verlangt fuer jede Schwelle und jeden Nulleffekt eine **Herleitungs-Referenz** (Dateipfad + Test-ID des Fixtures), nicht einen nackten Skalar - sonst erzeugt das Format DEC-31-Wiedergaenger im Formatgewand. (c) Die append-only-Eigenschaft wird **mechanisch erzwungen**: ein Test hash-pinnt die Bytes aller Alt-Eintraege.

**Template (Pflichtschluessel; `<...>` sind auszufuellen, `ref:` verlangt einen Pfad plus Test-ID, nie einen Skalar allein):**

```yaml
id: <A1|A2|...>                      # eindeutig, genau ein Treiber je id
klasse: <P|W|E>
capital_free: true                   # 3.0-Mess-Gates sind ausnahmslos kapitalfrei
hypothese: <ein Satz, falsifizierbar>
ertragsquelle: <Praemie|Prognose|Ereignis|Struktur> + Zahler
metric: <Name>                       # urteilstragende Groesse, genau eine
windows:                             # REZENZ-Klausel C.18
  - {id: W1, von: <YYYY-MM-DD>, bis: <YYYY-MM-DD>, rolle: <urteilstragend|aera-profil>}
  - {id: W2, von: <YYYY-MM-DD>, bis: <YYYY-MM-DD>, rolle: urteilstragend}
threshold:
  wert: <Zahl mit Einheit>
  ref: <pfad#test_id>                # Herleitung, nicht Skalar (DEC-54b)
structural_null:
  komponenten: [<Name>, ...]         # je Komponente eigene Herleitung
  wert: <Zahl mit Einheit>
  ref: <pfad#test_id>                # Messung am Null-Fixture, nicht nur Herleitung
power:                               # Pflichtzeile 3.3.1 / DEC-51
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: <Kalendertag|Kalender-Cluster|Woche|Verfallsereignis>
  n_eff: <Zahl>                      # mit Rechenweg im Prosateil
  detectable_effect: <Zahl mit Einheit>
  ref: <pfad#test_id>
selection:                           # Pflichtzeile 3.3.4
  K: <Zahl gerechneter Varianten>
  ceiling_analytic: <Zahl>           # Bailey/LdP fuer dieses K
  ceiling_measured_ref: <pfad#test_id>   # Bestwert-Verteilung auf dem Null-Fixture
economic_minimum:                    # Pflichtzeile 3.3.2 - ETIKETT, NICHT GATE
  wert: <Zahl mit Einheit>
  ref: <pfad#herleitung>
  label: <ueber_wand|unter_wand>
decision_relevance:                  # Pflichtzeile 3.3.2
  on_pass: <naechster Schritt, Kapitalpfad, Tradability-Folge>
  on_drop: <was ausgeschlossen wird>
capital_tax_venue:                   # Pflichtzeile 3.3.9
  kapitalbasis: <gebundenes Kapital / Multiplikator m, Sensitivitaet>
  steuer: <Regime oder "UNBELEGT - Nutzer-Entscheidung Par. 8.2">
  venue_event: <benanntes Ereignisrisiko + Abschlag>
  zahler_post_2024: <Begruendung, warum der Zahler noch zahlt>
stress_episode:                      # Pflichtzeile 3.3.10 / DEC-53
  liste_ref: <pfad#fixture_id>
  n_episoden_im_fenster: <Zahl>
irreversibility_probe:               # Pflichtzeile 3.3.7
  ergebnis: <nachladbar|irreversibel>
  ref: <pfad oder WP-id>
positive_control:                    # Pflichtzeile 3.3.8
  laufzeit_geschaetzt_h: <Zahl>
  vorgeschaltet: <true|false>        # true zwingend bei > 1 h
  ref: <pfad#test_id>
fixtures:                            # Pflichtzeile 3.3.5 / DEC-39 erweitert
  positive: <pfad#test_id>
  null: <pfad#test_id>
  adversarial: <pfad#test_id>        # Peso (P) / Beta-Faktor (W) / Selektion (E)
fdr_family: <F-...>
over_family: <F-...>
feasibility_verdict: <bestanden|verfehlt> # GL-012-Check, C.12
constants_hash: <sha256 oder "n/a - kapitalfrei ohne Kostenmodell">
data_fingerprints: [<bereichs-fingerprint>, ...]
stats3_version: <x.y.z>
bedingung_welle_1: [<WP-7|WP-9|WP-10|V-1|...>]
```

### 3.5 Die kontrollierte Entschaerfung des Ein-Fenster-DROP: DEC-52 (Entwurf)

**Ausgangslage.** C.10 (hartes Ein-Fenster-Abbruchkriterium) kostet nach R4 K-0.6 bei Per-Fenster-Power 0,5 drei von vier echten Effekten (`0,5^2 = 0,25`). Das Programm faehrt dadurch unbemerkt bei einem effektiven alpha von `0,05^2 = 0,25 %` statt 5 % - das war nie beschlossen (Review 4.1b). Gegenrechnung: bei einem echten Effekt mit Per-Fenster-t = 1,4 ist `P(Vorzeichen richtig) = Phi(1,4) = 0,919`, also `P(beide) = 0,845` gegenueber `P(beide signifikant bei t>1,645) = 0,42^2 = 0,18` - **Faktor 4,7 mehr Retention** (R4 K-0.6, vom Review nachgerechnet und bestaetigt).

**Gegenargumente, die im Beschlusstext stehen bleiben** (Review 4.1, "Gegen die Aenderung"): (a) Der Zweck der Regel war nie alpha-Kontrolle, sondern **Regime- Robustheit** - C.18/DEC-38 existiert, weil H-22s IC "nur 2023/24 lebt" und H-20s Vorzeichen zwischen Aeren kippt (BTC -16 -> +36, ETH +32 -> -12); ein gepoolter Schaetzer mittelt genau darueber hinweg. (b) Vorzeichen ist ein 1-Bit-Test und traegt als Filter faktisch nichts (unter der Null bestehen zwei Fenster mit 0,5). (c) H-20 haette unter der neuen Regel plausibel bestanden - eine Regelaenderung, die ein bestehendes Verdikt umdreht, ist per Definition eine **Lockerung**.

> **DEC-52 (Entwurf) - Ein-Fenster-Regel fuer die Klassen P und W.** Beschluss als eigenstaendige DEC **VOR** jeder Kandidaten-Registrierung und niemals kandidatenspezifisch. Die fuenf Review-Auflagen gelten woertlich:
>
> **(i)** Nur zulaessig, wo die **Power-Zeile vor dem Lauf** eine Per-Fenster-Power **< 0,6** ausweist. Fuer Zensus-artige, hoch-gepowerte Fragen bleibt C.10 hart und unveraendert.
>
> **(ii)** Je Fenster muessen beide Punktschaetzer **das gleiche Vorzeichen UND jeweils >= 0,5x die registrierte Schwelle** erreichen. Reines Vorzeichen reicht nicht; das Magnituden-Band wird von [0,4x; 2,5x] auf **[0,5x; 2,0x]** gestrafft.
>
> **(iii)** Das Signifikanzurteil liegt **ausschliesslich auf dem gepoolten Schaetzer** mit fenster-geclustertem stationaerem Bootstrap (Politis/Romano 1994, Blocklaenge nach Politis/White 2004 [sek]).
>
> **(iv)** Das **gepoolte alpha wird auf 0,01 gesenkt**, weil der Zwei-Fenster-Filter das alpha nicht mehr traegt. Sonst springt die gemeinsame Falsch-Positiv-Rate von 0,25 % auf 2,5 % - Faktor 10, und **das** waere die eigentliche Lockerung, nicht die Regelform.
>
> **(v)** **Pflicht-Retro-Check:** die neue Regel wird auf **H-06, H-20 und H-22** angewendet und das Ergebnis veroeffentlicht. Kippt sie ein Verdikt, heisst die Regel **"Lockerung", nicht "Verbesserung"**, und die alten Verdikte bleiben unveraendert stehen (append-only, C.1).
>
> **Reihenfolge, verbindlich:** Retro-Check -> Beschluss DEC-52 -> erst danach Registrierung eines Kandidaten, der die Regel braucht. Wird die Reihenfolge verletzt, ist die Aenderung fuer diesen Kandidaten gemacht und damit Torpfosten-Verschiebung (Review 4.1 Auflage 1). A3 (Kohorte F-XSEC1) braucht sie nachweislich (Par. 5.3), A1 braucht sie voraussichtlich (Par. 5.1) - beides aendert nichts an der Reihenfolge.

### 3.6 Praemie statt Sharpe

**Beschluss (Entwurf 3.0 Par. 2.4):** Urteilstragende Groesse der Klasse P ist die **Praemie** (`mean(prem)` in annualisierten bp bzw. Vol-Punkten). **Sharpe, MaxDD und Tail-Ratio werden BERICHTET, nie geurteilt** - jeweils mit hergeleitetem Rauschboden.

*Herleitung.* Lo (2002, FAJ 58(4)) [sek via R4 K-0.2]: `Var(SR_p) = (1 + SR_p^2/2)/n`; annualisiert `SE(SR_ann) = sqrt((1 + SR_ann^2/(2q))/T)`. Mit DEC-51 (`z = 2,4865`) folgt `T_min [Jahre] ~= 6,18 / SR_ann^2`: SR 2,0 -> 1,55 a; SR 1,0 -> **6,19 a**; SR 0,75 -> 11,0 a; SR 0,5 -> **24,7 a**. Mit der Mertens-Erweiterung (monatliche Schiefe g3 = -2, Exzess-Kurtosis 10, SR_ann = 1,0) ist der Varianzfaktor 1,827, also `T_min = 11,3` statt 6,2 Jahre. **Der Datenbestand reicht 5-6 Jahre** (Kompendium B.16). Ein Sharpe-Gate ist darauf entweder unerreichbar oder bedeutungslos.

*Auflagen des Reviews (4.2), woertlich bindend:*
1. Jeder P-A-PASS traegt verpflichtend das Etikett **"Praemien-EXISTENZ; die risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER"** - wie die H-11/H-16-Etiketten, und im PASS-Text selbst.
2. **Kein Kapitalschritt darf aus einem P-A-PASS folgen.**
3. Die Beobachtungszahl wird nicht ueberzeichnet: "1.095 Funding-Beobachtungen" sind bei Blocklaenge ~30 Tagen effektiv **~12 unabhaengige Beobachtungen pro Jahr**, der reale Power-Gewinn gegenueber Jahresrenditen ist Faktor ~12, nicht ~219. Der stationaere Bootstrap behandelt das korrekt; der Registrierungstext muss es auch tun.
4. Fuer das RISIKO ist das effektive N die Zahl der **Stress-Episoden** (6-10 in 24 Monaten nach DEC-53), nicht die Zahl der Funding-Intervalle.

**Degradierte Gates (aus R1 Par. 2, gegen R4 K-0.2/1.1b entschieden):**
- `SR_block >= 0,60` (R1 G3) wird **Bericht, nicht Gate** (Review 3.7: bei `N_eff = 12` und `SE(SR) = 0,31` ist das ein Gate mit ~50 % Power je Fenster und 25 % ueber zwei).
- `TR = |CVaR_1%|/mean <= 250 Tage` (R1 G4) wird **Deskriptor mit Untergrenze, nie Gate** (Review 3.8): eine echte Praemie hat strukturell Tail-Ratio < 1, und die Kennzahl hat den Mittelwert im Nenner, bestraft also kleine Praemien - eine exzellente Praemie mit 0,5 bps/Tag und CVaR 200 bps hat TR=400 (getoetet), eine mittelmaessige mit 2 bps/Tag und CVaR 400 bps hat TR=200 (bestanden).
- MaxDD-Schwellen werden aus `E[MaxDD] = 1,2533 * sigma_ann * sqrt(T_Jahre)` (Magdon-Ismail et al. 2004 [sek] via R4 K-0.4) hergeleitet, nie importiert: bei sigma_ann 20 % und T=5 a ist `E[MaxDD] = 56 %`, eine importierte Schwelle "MaxDD < 30 %" waere strukturell unerreichbar - der C-14-Fehler in neuem Gewand.

### 3.7 GPU-Default 0

> **DEC-56 (Entwurf).** Das GPU-Standardbudget je Hypothese ist **0**. Ein GPU-Lauf braucht eine registrierte Begruendung, warum die CPU-Fassung die Frage nicht beantworten kann, UND eine Entscheidungsrelevanz-Zeile mit ausformuliertem Tradability-Pfad. Empirische Grundlage: ~350 GPU-Stunden in 2.0 (R4 K-0.7: 180+57+48..72+24..48 = 309-357 h), Ertrag 2 kapitalfreie WEITER, **0 registrierte Tradability-Folgen** (Kompendium E.10 fuehrt H-15b und H-16b explizit als NICHT registriert). Die Regel kostet nichts, weil keine der drei 3.0-Klassen GPU braucht (R4 4.2: IC, Praemie, CAR, Bootstrap, Permutation, FDR sind saemtlich CPU-Arbeit in Minuten).
>
> **Die 24-h-Wall-Clock-Kappe aus R4 4.4.2 wird NICHT als Schwelle uebernommen** (Review 4.4: eine importierte Zahl ohne Herleitung - warum 24 und nicht 12 oder 72? H-15 lief 180 h, checkpointet, und lieferte ein gueltiges WEITER). Sie wird **Budget-Meldegrenze**: ein geplanter Lauf ueber 24 h Wall-Clock wird vor dem Start gemeldet und begruendet, nicht verboten. Das wirksame Instrument ist die Positivkontroll-Vorschaltung (3.3.8), nicht eine Stundenzahl.

### 3.8 Kein Live-Order-Code - und der benannte Preis

"Kein Live-Order-Code" bleibt Verfassung des FORSCHUNGSprogramms. Der Preis wird ausdruecklich benannt statt still hingenommen (R4 6.3): Fill-Wahrscheinlichkeiten sind nie direkt messbar, jede Maker-Annahme bleibt unfalsifizierbar - und Maker ist nach K-0.1 der Unterschied zwischen 53 Minuten und 6,6 Stunden Mindesthorizont. Der Mittelweg ohne Regelbruch ist die **kapitalfreie Quote-Schatten-Messung** (WP-10 Teil B, Par. 4.3): aus rein oeffentlichen Daten wird die Warteschlangen-Position einer hypothetischen eigenen passiven Quote rekonstruiert und die Fill-Rate geschaetzt. Keine Order, kein Kapital, kein Key. Der vom Review benannte Widerspruch (6.4: die billigste zu MESSENDE Klasse ist die teuerste zu BETREIBENDE) wird **nicht still entschieden** - siehe Par. 8.1.

### 3.9 Modell- und Teampolitik (Entwurf 3.0 Par. 5)

| Rolle | Modell | Auftrag |
|---|---|---|
| Orchestrator | **Fable 5.1** (immer) | Entscheidungen, Registrierungstexte, Gate-Urteile, Verfassung |
| Zensus-/Backfill-Bau (WP-7, WP-9, WP-10) | **Sonnet** | Bau nach Spezifikation des Orchestrators, mit Test-Abnahme (Fixtures DEC-39, Determinismus-Fingerprint T2) |
| Gate-Design und Registrierungs-Herleitungen (Rauschboeden, Power) | **Opus**, danach adversarischer Review durch einen **zweiten Opus-Agenten** | Fable 5.1 entscheidet nur bei Widerspruch zwischen beiden |
| Kartierung, Inventur, Dokumentpflege | **Sonnet** (ggf. Haiku fuer reine Listen) | - |

**Bindend: kein Agent registriert eine Hypothese.** Das tut ausschliesslich der Orchestrator, nach Review.

---

## 4. Welle 1: Zensus zuerst, kein Alpha-Slot ohne Feasibility

**Prinzip.** Die Reihenfolge ist bindend. Jedes Paket folgt dem **WP-4-Muster**: eine Frage, ein binaerer Befund, und die Konsequenz jedes Ausgangs steht **VORAB** im Dokument - nicht erst nach dem Sehen der Zahl. Welle 1 verbraucht **null Alpha-Slots**; kein Paket hat einen Ertrags-Claim.

**Laufort.** `api.bybit.com`, `bybit.com` und `bybit-exchange.github.io` sind vom Egress-Proxy der Sandbox **geblockt** (R1 0.5); die Sandbox hat ausserdem kein torch und keine GPU (Kompendium B.17/F.3). Daraus folgt verbindlich:
- **Alle REST-Downloads und alle Primaerquellen-Pruefungen laufen auf der Nutzer-Maschine.**
- **T0/T1 (Unit-Tests, Fixtures) laufen in der Sandbox**, weil sie nur synthetische Eingaben brauchen.
- **T2/T3 (Laeufe auf Echtdaten, Determinismus mit N>=3) laufen auf der Nutzer-Maschine**, weil dort die Daten liegen.

| # | Paket | Beantwortet | Aufwand | Laufort |
|---|---|---|---|---|
| WP-7 | Universums-Zensus (R2-V-0 + R4-WP-8 vereinigt) | Ist die Querschnitts-Klasse ueberhaupt testbar? Welches K, welche `sigma_xs`, welches `rho_quer`, welcher Alt-Symbol-Spread? | 1d-Klines ~10 min Download; Tickers-Inhaltsprobe Minuten; ~1 Personentag Code | Download + Lauf: Nutzer-PC; Fixtures: Sandbox |
| WP-9 | DVOL-Backfill + Kreuzvalidierung | Sind 5,4 Jahre IV-Historie verfuegbar und mit dem Harvester konsistent? | Sekunden Download, ~1 h Abgleich | Nutzer-PC |
| WP-10 | Praemien-Kohaerenz + Maker-Fill-Schattenmessung | Wie korrelieren die Praemienquellen im Stress? Wie wahrscheinlich ist ein passiver Fill, und was kostet die adverse Selektion? | Bestand + WP-2/WP-4-Replay, CPU-Stunden (WP-4 brauchte 86 min je Fenster) | Nutzer-PC |
| V-1..V-4 | Vier 10-Minuten-Vorfragen, oeffentlich, keyfrei | Vorbedingungen fuer A1, A4, A5 | Minuten je Frage | Nutzer-PC (zwingend, Egress-Sperre) |

### 4.1 WP-7 - Universums-Zensus (Rang 1 des gesamten Feldes)

**Ziel.** Die vier Zahlen messen, an denen die gesamte Klasse W und die Kostenrechnung jedes breiten Kandidaten haengen: **K** (Zahl durchgehend handelbarer Perps), **sigma_xs** (wochenweise Querschnitts-Streuung), **rho_quer** (Restkorrelation nach Querschnitts-Demeaning) und **PERP_SPREAD_BP je Symbol-Dezil**. Vereinigt R2-V-0 mit R4-WP-8 (Review 5.1 Rang 1).

**Datenquellen mit Endpunkt.**
- `GET /v5/market/instruments-info?category=linear` (Universum + `status`, Cursor- Paginierung) - Roster und Survivorship-Frage.
- `GET /v5/market/kline?category=linear&interval=D`, `limit` 1-1000, Default 500 [sek: Bybit-Doku via Suchtreffer]. Rate-Limit **600 Requests je 5 s je IP** [sek]; Selbst-Drossel **5 Req/s = 0,4 % des Limits**. Arithmetik: 5,5 Jahre = 2.008 Tage, 3 Calls/Symbol, ~1.000 Symbole inkl. delisteter -> **~3.000 Calls, ~10 min, ~1,7 Mio Zeilen, 40-80 MB Parquet** (R4 3.2 Zeile 1).
- **Zuerst: Inhaltsprobe (C.8) auf den bereits vorhandenen `bybit/tickers`-Strom** (3.751 Symbole, 43 Tage, Kompendium F.1) auf die Felder `bid1Price`/`ask1Price`/ `openInterest`/`fundingRate`. Findet die Probe sie, ist der Spread-Zensus auf Bestandsdaten in Minuten rechenbar und **es wird gar nichts neu gesammelt** (R4 3.6; DEC-46-Lehre). Findet sie sie nicht, wird der Spread-Teil ueber `GET /v5/market/tickers` (ein Request je Kategorie) frisch gemessen.
- **Nicht** in Welle 1: 1h-Panel-Store. Erst nach bestandener Feasibility und nur in der Aufloesung, die die ueberlebende Feasibility braucht (Review 5.2 Punkt 2: der Panel-Store ist das teuerste Einzelstueck des gesamten Berichtssatzes und wurde vorgeschlagen, bevor `rho_quer` gemessen ist).

**Determinismus- und Fingerprint-Pflicht.**
- Jahres-Partitionen statt Tages-Partitionen (`panel_1d/source=/category=/symbol=/year=`); bei 1.500 Symbolen x 2.190 Tagen waeren Tages-Partitionen 3,3 Mio Verzeichnisse (R4 3.5, Abweichung 1).
- `frozen/` (abgeschlossene Kalenderjahre, unveraenderlich, fingerprint-tragend) vs. `open/` (laufendes Jahr). Ein urteilstragender Lauf nutzt entweder nur `frozen/`-Jahre ODER pinnt den Fingerprint der `open/`-Partition zur Laufzeit und zitiert ihn in der Registrierung (C.19).
- Eigenes `panel_manifest.sqlite` mit `status in {DONE, PARTIAL, EMPTY, FAILED}`; **DONE** verlangt `n_rows == expected_days`, wobei `expected_days` aus dem Listing-Datum des Instruments und dem Jahresende abgeleitet wird. **Loud-Fail (C.14) bei Abweichung** - nie stilles Einfrieren eines Loch-Jahres.
- `panel_fingerprint(source, category, symbol, year)` = SHA-256 ueber die exakten Wertbytes aller Spalten in kanonischer Reihenfolge, plus ein **Bereichs-Fingerprint** ueber (Symbolmenge, Jahresbereich), den jede Registrierung zitiert.
- Pflichtspalte `funding_n` (Zahl der Funding-Abrechnungen je Symbol-Tag). Bybit fuehrt Symbole mit 8h- UND mit 1h-Funding, und Intervalle aendern sich ueber die Historie; ohne die Zaehlung addiert man Aepfel und Birnen - dieselbe Fehlerklasse wie die zwei `publicTrade`-Dialekte, die 19 von 50 H-12-Tagen entwertet hat (R4 3.5).
- **Determinismus T2:** N>=3 Laeufe auf identischem Input, Fingerprint-Vergleich (C.7 - N=2 beweist nichts).
- **Provenienz (Review 6.9):** monatliche **1-%-Zufallsstichprobe** eingefrorener Partitionen wird neu gezogen und gegen die Fingerprints geprueft; Abweichung ist ein lautes Alarm-Ereignis, kein stilles Ueberschreiben. Boersen revidieren historische Klines gelegentlich.

**Die genaue Herleitung von rho_quer.**

Sei `r_{i,t}` die Wochenrendite von Symbol `i` in Woche `t` auf dem point-in-time-Universum `U_t` mit `K_t = |U_t|`. Der Querschnitts-Demeaning-Schritt entfernt den gleichgewichteten Marktfaktor exakt je Woche:

```
r~_{i,t} = r_{i,t} - (1 / K_t) * sum_{j in U_t} r_{j,t}
```

`rho_quer` ist der Mittelwert der paarweisen Korrelationen der DEMEANTEN Reihen ueber das Fenster:

```
rho_quer = mean_{i != j} corr_t( r~_{i,t} , r~_{j,t} )
```

**Abgrenzung zu rho_bar (der Kern des Review-Befunds 0/3.1).** R2-V-0 Frage 4 misst `rho_bar`, die **rohe** paarweise Wochenrendite-Korrelation; in Krypto ist die von der BTC-Beta-Struktur dominiert und liegt erfahrungsgemaess bei 0,7-0,85 (**UNBELEGT**, R2 selbst). `rho_quer` misst, was **danach** uebrig bleibt: Sektor- und Beta-Restkorrelation. Das sind zwei verschiedene Groessen; R2s gesamte Breiten-Argumentation setzt implizit `rho_quer = 0` (Review 2.6), R4 rechnet als einziger mit `N_eff` und stellt gleichzeitig fest, dass `rho_quer` **UNGEMESSEN** ist. **Entscheidung des Orchestrators: R4 hat recht** (Entwurf 3.0; Review 3.1).

**Struktureller Nulleffekt des Schaetzers selbst (C.4, hier zwingend).** Fuer `K` unabhaengige Reihen mit gleicher Varianz haben die querschnittlich demeanten Residuen eine **exakte, mechanisch negative** paarweise Korrelation von `-1/(K-1)`. Bei K=110 ist das -0,0092, bei K=170 -0,0059, bei K=300 -0,0033 - **dieselbe Groessenordnung wie die Entscheidungsschwelle 0,03**. Der Schaetzer muss diese Verzerrung deshalb korrigieren:

```
rho_quer_hat = ( rho_resid_hat + 1/(K-1) ) / ( 1 - 1/(K-1) )
```

Wer den Rohwert `rho_resid_hat` gegen die Schwelle haelt, misst die Demeaning-Arithmetik und nennt sie Restkorrelation - die exakte Fehlerklasse DEC-31. Der Nulleffekt wird zusaetzlich am Null-Fixture GEMESSEN (3.3.5), nicht nur hergeleitet.

**Herleitung der Schwelle 0,03 aus R4 K-0.5.**

Bausteine (alle R4 K-0.5): `SD(IC_t) = 1/sqrt(N_eff - 1)`, `N_eff = N_c/(1 + (N_c - 1)*rho_quer)`, `SE(mean IC) = SD(IC_t)/sqrt(W)`.

1. **Breiten-Decke.** Fuer `N_c -> unendlich` gilt `N_eff -> 1/rho_quer`. Die Breite hilft also nur bis zu dieser Decke; `rho_quer` und nicht `K` ist die bindende Zahl. Das ist R4s Kernaussage und der harte Widerspruch zu R2.
2. **Fensterlaenge.** Das registrierte Design der Klasse W ist 2 x 12 Monate ab 2024-07-01 (REZENZ, C.18), also `W = 52` Wochen je urteilstragendem Fenster.
3. **Oekonomische Mindestmagnitude.** Aus R4 1.2.d: Netto-Kante bei Wochen-Rebalance und Taker-Wand ist `0,798*(2p-1)*693 bp - 11 bp` mit `p = 0,5 + arcsin(IC)/pi`; Break-even bei `IC = 0,031`, Faktor 2 darueber also **`IC_min = 0,062`**. (Diese Zahl ist nach C.2 **Etikett**, nicht PASS-Bedingung - sie dient hier ausschliesslich der Feasibility-Rechnung, also der Frage, ob ein wirtschaftlich relevanter Effekt ueberhaupt sichtbar waere.)
4. **Gleichsetzen.** Gesucht ist das groesste `rho_quer`, bei dem die per-Fenster detektierbare Effektgroesse unter DEC-51 die oekonomische Mindestmagnitude noch erreicht:

```
detektierbar = 2,4865 * (1/sqrt(N_eff - 1)) / sqrt(52)  <=  0,062
=> 1/sqrt(N_eff - 1) <= 0,062 * sqrt(52) / 2,4865 = 0,17980
=> N_eff - 1 >= 1/0,17980^2 = 30,93
=> N_eff >= 31,93
=> rho_quer <= 1/31,93 = 0,0313
```

**Registrierte Schwelle: `rho_quer <= 0,03`** (auf zwei Nachkommastellen konservativ abgerundet).

**Ehrliche Einschraenkung, die in den Befund gehoert.** Die 0,03 ist eine **asymptotische NOTWENDIGE Bedingung** (`K -> unendlich`), keine hinreichende. Bei endlichem K liegt `N_eff` unter der Decke:

| K | rho_quer | `N_eff` | `SD(IC_t)` | `SE` bei W=52 | detektierbar (DEC-51) |
|---|---|---|---|---|---|
| 110 | 0,03 | 25,8 | 0,2008 | 0,0279 | 0,0693 |
| 170 | 0,03 | 28,0 | 0,1925 | 0,0267 | 0,0664 |
| 300 | 0,03 | 30,1 | 0,1854 | 0,0257 | 0,0639 |
| Decke | 0,03 | 33,3 | 0,1760 | 0,0244 | 0,0607 |

Selbst bei K=300 verfehlt das **Per-Fenster**-Design die 0,062 knapp. Gepoolt ueber beide Fenster (`W = 104`) dagegen: bei K=170 und rho_quer=0,03 ist `SE = 0,1925/sqrt(104) = 0,0189`, detektierbar **0,0469** - klar unter der Mindestmagnitude. **Damit ist arithmetisch gezeigt, dass die Klasse W ohne DEC-52 (gepoolter Schaetzer, Vorzeichen-Konsistenz je Fenster) auch bei bestandenem WP-7 nicht registrierbar ist.** Das ist keine nachtraegliche Rettung, sondern der Grund, warum DEC-52 VOR jeder Registrierung beschlossen wird (Par. 3.5, Review 4.1 Auflage 1).

**Binaerer Befund mit VORAB fixierter Konsequenz (WP-4-Muster).**

| Befund | Vorab fixierte Konsequenz |
|---|---|
| **B1:** `rho_quer > 0,03` | **Klasse W in der 2x12-Monats-Form TOT.** A3 (Kohorte F-XSEC1) wird gestrichen und **nie auf N=5 zurueckskaliert** (das waere D.7/H-07 zum zweiten Mal). A1 wird auf die reine Praemien-Zerlegung reduziert und nur registrierbar, wenn seine eigene Power-Zeile (Par. 5.1) traegt. |
| **B2:** `rho_quer <= 0,03` UND `K >= 110` durchgehend in beiden Fenstern | Klasse W offen; A3 registrierbar **nach** DEC-52. |
| **B3:** `rho_quer <= 0,03` UND `K < 110` | Klasse W TOT (Power-DROP nach GL-012, kein Datenlauf noetig - dieselbe Struktur wie H-07). |
| **B4:** `instruments-info` liefert keine Zeilen mit `status != Trading`, ODER `kline` liefert fuer delistete Symbole keine Historie | **Kein Survivorship-freies Universum aus Bybit-Bordmitteln.** Konsequenz vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture (unten) zeigt, dass die Verzerrung **kleiner** als die halbe erwartete Kante ist; sonst nicht registrierbar. Ein externes Delisting-Register (Announcement-Scraping) ist **keine** Welle-1-Aufgabe. |
| **B5:** `sigma_xs` (Median ueber Wochen) < 500 bps/Woche | Bruttokante der Klasse W strukturell unter der Wand -> A3 traegt das Etikett "unter_wand" (3.3.2) und verbraucht damit bewusst einen Alpha-Slot, oder wird gestrichen. Entscheidung des Orchestrators nach dem Befund; **die Schwelle 500 steht vorher fest.** |
| **B6:** Alt-Symbol-Spread im obersten Symbol-Dezil > 3x der Majors-Konstante (0,0157/0,0537 bp, Kompendium B.2) | Die Majors-Slippage-Konstante 15 bps ist fuer das breite Universum ungueltig; jede Tradability-Aussage der Klasse W wartet auf `PERP_SPREAD_BP` je Dezil, und `tradability3.perp` RAISED bis dahin (Par. 6). |

**Definition of Done.**
1. Inhaltsprobe auf `bybit/tickers` dokumentiert (Felderliste, Takt, Abdeckung), mit Ergebnis JA/NEIN je gesuchtem Feld.
2. `panel_1d` gebaut, `panel_manifest.sqlite` ohne `PARTIAL`/`FAILED` in den beiden urteilstragenden Fenstern, Bereichs-Fingerprint notiert.
3. Vier Zahlen berichtet, jeweils mit CI: `K` je Kalendermonat, `sigma_xs` (Median und Quartile ueber Wochen), `rho_quer_hat` (bias-korrigiert, mit dem Rohwert und der `-1/(K-1)`-Korrektur getrennt ausgewiesen), `PERP_SPREAD_BP` je Symbol-Dezil.
4. Survivorship-Bauplan implementiert und getestet: point-in-time-Universum (Symbol in Woche t drin, wenn zu Wochenbeginn >= 8 Wochen Bars UND in Woche t noch handelnd; erste 8 Wochen ausgeschlossen wegen Listing-Pump-Artefakt); ein delistetes Symbol wird **nicht rueckwirkend entfernt**, sondern bis zum letzten vorhandenen Bar gehalten und zum letzten Schlusskurs geschlossen (ein "-100 %"-Ansatz waere falsch und in die andere Richtung verzerrt - R2 V-0).
5. Determinismus T2 (N>=3) gruen, Fingerprints identisch.
6. Binaerer Befund B1..B6 als Befunddokument mit der VORAB fixierten Konsequenz zitiert.

**Testpflichten (T1, drei Fixtures).**
- **Positiv:** synthetisches Panel mit injiziertem Querschnitts-IC von exakt 0,04 bei realistischer Korrelationsstruktur; der Schaetzer muss den Wert im CI wiederfinden, und `rho_quer_hat` muss den injizierten Wert treffen.
- **Null:** Panel mit identischer Vol-/Korrelationsstruktur, aber ohne jedes Signal und mit **unabhaengigen** Reihen; `rho_quer_hat` muss 0 im CI enthalten - dieser Fixture prueft direkt die `-1/(K-1)`-Bias-Korrektur.
- **Adversarial (Survivorship-Fixture):** signalfreies Panel, aus dem 30 % der Symbole nach einem simulierten Drawdown-Trigger geloescht werden. Der **unkontrollierte** Schaetzer MUSS darauf eine scheinbare Momentum-Praemie ausweisen, der **kontrollierte** nicht. Faellt dieser Test durch, ist die gesamte Panel-Maschinerie methodisch invalide (H-14-Muster, C.13) - dann kein Befund, sondern "methodisch invalide". Die Bias-Richtung ist vorab festzuhalten: verschwundene Perps sind ueberwiegend solche nach langem Drawdown; ihr Fehlen macht die **Short-Seite eines Momentum-Portfolios** und die **Long-Seite eines Reversal-Portfolios** kuenstlich gut - beides in Richtung "Kante existiert" [sek: Grobys/Sandretto zu Ueberlebenden-Momentum; Host geblockt, Prozentzahl nicht primaer verifizierbar].

**Aufwand.** ~1 Personentag Code (Sonnet, nach Spezifikation) + ~10 min Download (1d) + ~1 h Rechnen. CPU-only, keine GPU.

### 4.2 WP-9 - DVOL-Backfill und Quellen-Kreuzvalidierung

**Ziel.** Aus 112 harvesteten DVOL-Tagen (Kompendium F.1) ~1.980 machen und die Gleichwertigkeit der neuen Quelle **beweisen statt annehmen**.

**Datenquelle mit Endpunkt.** Deribit `/public/get_volatility_index_data`, Parameter `currency`, `start_timestamp`, `end_timestamp`, `resolution`; Antwort OHLC je Bucket [sek via Suchtreffer]. **DVOL-Historie ab ~2021-04-01** [sek: Amberdata-Doku; Deribit- eigene Doku nicht erreichbar]. Volumen: < 20 Requests, Sekunden, ~4.000 Zeilen, < 1 MB (R4 3.2). Die genauen `resolution`-Werte und das Punkte-Limit je Aufruf sind **UNBELEGT - Probe-Pflicht** (ein Request klaert es auf der Nutzer-Maschine).

**Determinismus-/Fingerprint-Pflicht.** Eigener Speicher unter derselben Disziplin wie der WP-0-Bar-Cache (SCHEMA_VERSION, SHA-256-Sidecar, Manifest-Gate, Loud-Fail bei "Rohzeilen > 0, geparst = 0"). **Backfills schreiben NIE in den Harvest-Baum** (Schutzgut, read-only, per CLI-Guard erzwungen - R4 3.4). Monatliche 1-%-Reverifikation wie WP-7.

**Binaerer Befund mit VORAB fixierter Konsequenz.**

| Befund | Vorab fixierte Konsequenz |
|---|---|
| **B1:** Historie reicht bis >= 2021-04 UND die 112 Ueberlappungstage stimmen innerhalb der Materialitaets-Schranke ueberein | Die **H-27-Klasse** (VRP auf REST-Backfill-Basis) wird als **neue, eigens vorzuregistrierende Hypothese** eroeffnet. |
| **B2:** Historie reicht, aber die Ueberlappung weicht ab | Die Quellen sind **nicht** austauschbar. Der Backfill darf ausschliesslich eine eigene, getrennt registrierte Hypothese tragen und wird **nie** mit Harvester-DVOL in einer Reihe gemischt. Ursachenanalyse ist ein eigener WP. |
| **B3:** Historie reicht nicht zurueck | Der Fund ist wertlos, Aufwand ~1 h, kein Schaden. H-26 bleibt unveraendert gesperrt. |

**In allen drei Faellen unveraendert bindend:** WP-9 **entsperrt H-26 NICHT** und erfuellt die C-33-12-Monats-Uhr **NICHT**. H-26 ist gegen `done_days` des Harvesters vorregistriert und bleibt es (R4 3.4, Review 3.3, Kompendium E.2/E.7). Wer das anders liest, verschiebt einen Torpfosten.

**Materialitaets-Schranke (C.6, hergeleitet statt gesetzt).** Bit-Identitaet gegen einen lebenden, revidierbaren Fremdspeicher ist strukturell unerfuellbar (H-11c-Lehre). Die Schranke wird aus der Gate-Arithmetik der Zielklasse abgeleitet: die C-33-Schwelle betraegt **3 Vol-Punkte**; das DEC-32-Praezedenz-Verhaeltnis ist eine Schranke **250x unter dem Gate-Abstand**. Daraus: `|DVOL_REST - DVOL_Harvest| <= 3/250 = 0,012 Vol-Punkte` auf **>= 99 %** der 112 Ueberlappungstage. Die 99 % (statt 100 %) tragen der Tatsache Rechnung, dass ein Tag mit Aufzeichnungsluecke im Harvester kein Quellenfehler ist; jeder verletzende Tag wird namentlich gelistet.

**Definition of Done.** Backfill-Speicher gebaut und fingerprinted; Ueberlappungs- Vergleich als Tabelle (Tag, REST, Harvest, Differenz, PASS/FAIL); Befund B1/B2/B3 dokumentiert; explizite Zeile "H-26 und C-33 bleiben unveraendert gesperrt".

**Testpflichten.** *Positiv:* synthetische Antwort mit bekannten OHLC-Werten - der Parser muss sie exakt reproduzieren. *Null:* leere Antwort und Antwort ohne die erwarteten Felder - beide muessen **laut scheitern** (C.14), nie stillschweigend 0 Zeilen liefern. *Adversarial:* Antwort mit korrektem Schema, aber verschobener Zeitachse (Bucket-Ende statt Bucket-Anfang) - der Ueberlappungs-Vergleich MUSS das als Abweichung melden, sonst misst die Kreuzvalidierung nichts.

**Aufwand.** Sekunden Download, ~1 h Abgleich, ~2 h Code. Nutzer-PC.

### 4.3 WP-10 - Praemien-Kohaerenz und Maker-Fill-Schattenmessung

**Ziel.** Zwei Fragen, die keinen Ertrags-Claim tragen, aber ueber die Gueltigkeit ganzer Kandidatenklassen entscheiden (Review 5.1 Rang 3; vereinigt R1-K-07 mit R4 6.2a/6.3).

**Teil A - Kohaerenz der Praemien im Stress.** Die Diversifikations-These ("mehrere kleine Praemien statt einer grossen") setzt voraus, dass die Praemien-PnLs im Stress **nicht** perfekt korrelieren. Die 10.10.2025-Evidenz legt das Gegenteil nahe: Funding kippt tief negativ, Basis kollabiert, IV explodiert, Buchtiefe -90 %, ADL greift - alle Praemienquellen sind Verkaeufer derselben Liquiditaets-/Crash-Versicherung [sek, mehrere unabhaengige Sekundaerquellen via R1]. **Das muss gemessen und nicht angenommen werden.**

*Metrik.* `rho_stress` = Spearman-Korrelation der taeglichen Praemien-Proxy-PnLs (Funding-Carry, Perp/Future-Wedge, Short-Skew, Short-Vol), konditioniert auf die Stress-Episoden nach DEC-53; `rho_ruhig` auf dem Rest.

*Struktureller Nulleffekt (C.4).* Korrelationen steigen in Extremstichproben **mechanisch** (Selektion auf gemeinsame Groesse). Der Nulleffekt wird per Block-Bootstrap aus unkorrelierten Surrogaten mit identischer Randverteilung erzeugt, **nicht** mit 0 angesetzt - die Dirac-vs-Verteilung-Lehre auf Korrelationen uebertragen.

*Cluster-Einheit und N-Floor, neu hergeleitet (Review 1-R1-K-07, R4 1.3c).* R1s urspruenglicher Floor ">= 15 gemeinsame Extremtage" ist ein **Roh-N**: die fuenf Symbole teilen dieselben Extremtage, bei rho~0,8 ist `N_eff = 15/(1 + 4*0,8) = 3,6`. Die Cluster-Einheit ist die **Stress-Episode** (DEC-53). Der Floor wird aus der Testarithmetik hergeleitet, nicht gesetzt: fuer den Vergleich zweier Spearman-Korrelationen ueber die Fisher-z-Transformation gilt `SE(z) = 1/sqrt(n-3)`; die Differenz `rho_stress = 0,70` (z = 0,8673) gegen `rho_ruhig = 0,45` (z = 0,4847) ist 0,3826 in z-Einheiten. Mit einer grossen Ruhe-Stichprobe (deren Term vernachlaessigbar ist) und DEC-51:

```
2,4865 / sqrt(n_cluster - 3) <= 0,3826
=> sqrt(n_cluster - 3) >= 6,499
=> n_cluster >= 45,2  ->  N-Floor: 46 Stress-Episoden
```

**Befund vorab (und er ist unangenehm):** DEC-53 liefert in 24 Monaten ~18 Stress-Tage in **~6-10 Episoden**. Selbst ueber die volle 5,5-jaehrige Historie sind das ~20-30 Episoden - **der Floor von 46 ist auf diesem Bestand nicht erreichbar.** Die vorab fixierte Konsequenz ist deshalb nicht "Schwelle senken" (das waere Torpfosten-Verschiebung), sondern:

| Befund | Vorab fixierte Konsequenz |
|---|---|
| **A-B1:** `n_cluster >= 46` und die obere CI-Grenze von `rho_stress` liegt unter 0,70 | Portfolio-These **gestuetzt**; F-PREM1/F-PREM2/F-XSEC1 duerfen als unabhaengige Familien mit zweistufiger BH-FDR gefuehrt werden (DEC-22/C.16). |
| **A-B2:** `n_cluster >= 46` und `rho_stress >= 0,70` UND `rho_stress - rho_ruhig >= 0,25` in beiden Fenstern | Portfolio-These **widerlegt**: ein "Portfolio aus Praemien" ist ein einziger gehebelter Trade mit vier Etiketten. |
| **A-B3:** `n_cluster < 46` (der arithmetisch erwartete Fall) | **KEIN VERDIKT** zur Portfolio-These, **nicht DROP** (H-10/H-13-Falle vermeiden). Vorab fixierte Folge: die Welle behandelt F-PREM1/F-PREM2/F-XSEC1 **als moeglicherweise abhaengige Familien**; die Ueber-Familien-Korrektur wird in der abhaengigkeitsrobusten Form gefahren, nicht in der BH-Form, die Unabhaengigkeit unterstellt. WP-10(A) laeuft trotzdem und liefert die Punktschaetzung mit CI als **Deskriptor** (Kosten: Stunden). |

Damit ist WP-10(A) auch im wahrscheinlichsten Ausgang entscheidungsrelevant: es legt die FDR-Struktur der ganzen Welle fest (Review 6.7 - die Kohaerenzmessung ist Vorbedingung fuer die Gueltigkeit der FDR-Struktur, nicht nur fuer eine Portfolio-Aussage).

**Teil B - Maker-Fill-Schattenmessung.** WP-4 hat gemessen, dass der Top-of-Book exakt ein Tick breit ist - aber **nicht**, mit welcher Wahrscheinlichkeit eine Order dort gefuellt wird und welchen Adverse-Selection-Abschlag der Fill traegt. Ohne diese Zahl ist jedes Maker-Kostenmodell im Options- und Hedge-Pfad eine Annahme (R1 0.4: Maker-Rehedging ist Existenzbedingung, nicht Optimierung).

*Metrik.* `p_fill(60s)` = Anteil simulierter Top-of-Book-Maker-Orders, die binnen 60 s gefuellt werden; `adv_sel` = mittlere Mid-Bewegung in den 10 s **nach** dem Fill, in bp. Kein Live-Order-Code, keine Order, kein Kapital, kein Key - reine Rekonstruktion der Warteschlangen-Position aus oeffentlichen L2-Daten (Par. 3.8).

*Schwellen, korrekt hergeleitet (Review 2.8).* `p_fill(60s) >= 0,70`. Fuer die adverse Selektion gilt: der Maker-Vorteil ist **`FEE_TAKER - FEE_MAKER = 5,5 - 2,0 = 3,5 bp je Bein`** (Kompendium B.3), nicht 1,5 bp. R1s Schwelle `adv_sel <= 1,5 bp` widerspricht ihrer eigenen Begruendung ("bei groesserem Abschlag uebersteigt der effektive Maker-Preis den Taker-Preis") und ist damit nach C.4/GL-012 nicht registrierbar. **Registrierte Schwelle: `adv_sel <= 3,5 bp je Bein`**, mit dem obigen Rechenweg als Herleitungs-Referenz. Ein strengerer Wert bliebe zulaessig, aber nur mit eigener Herleitung - nicht mit einer falschen.

*Cluster-Einheit.* Kalendertag; zwei disjunkte REZENZ-konforme Halbjahre, also ~180 Cluster je Fenster. Damit ist Teil B - anders als Teil A - gut gepowert.

**Datenquelle.** Vollstaendig aus dem Bestand, kein Nachladen: WP-0-Bar-Cache (10.054 Cache-Tage), `bybit/publicTrade` (lueckenlos ab 2020-03-25), `deribit/dvol` (112 Tage), `bybit/orderbook` L2 BTC/ETH (961/530 Tage) plus die bereits gebaute und hash-gepinnte WP-2/WP-4-Replay-Maschinerie. Fuer die Funding-Serie: der Funding-Backfill aus WP-7 bzw. V-1.

**Definition of Done.** `rho_stress`/`rho_ruhig` mit CI und `n_cluster` berichtet; Befund A-B1/A-B2/A-B3 mit der vorab fixierten FDR-Folge dokumentiert; `p_fill(60s)` und `adv_sel` je Fenster mit CI berichtet; Determinismus T2 (N>=3) gruen; Fingerprints der Replay-Fenster gepinnt; **Nachweis, dass die WP-2/WP-4-Stores unberuehrt sind** (eigener Pfad, wie beim WP-4-Aufbau).

**Testpflichten.**
- (A) *Positiv:* vier synthetische PnL-Serien mit gemeinsamem Crash-Faktor - `rho_stress` muss ausschlagen. *Null:* vier unabhaengige Serien mit identischen Randverteilungen inklusive fetter Tails - `rho_stress` darf **nicht** ausschlagen; genau hier stirbt ein naives Gate. *Adversarial:* vier unabhaengige Serien, aber die Stress-Auswahl erfolgt auf der gemeinsamen Groesse (Selektionseffekt) - das Gate muss den mechanischen Anstieg vom echten Kohaerenz-Anstieg trennen.
- (B) *Positiv:* synthetisches Buch mit hoher Queue-Rotation. *Null:* Buch ohne Fills. *Adversarial:* Buch, in dem der Touch **nur bei adverser Bewegung** geraeumt wird - `p_fill` hoch, `adv_sel` toedlich; das Gate muss den zweiten Fall trennen.

**Aufwand.** (A) Minuten Rechenzeit, ~0,5 Personentage Code. (B) ein Ein-Pass-Replay je Fenster; WP-4 brauchte dafuer 86 min bei rc=0. CPU, kein GPU, kein Overnight-Lauf.

### 4.4 V-1 bis V-4 - vier 10-Minuten-Vorfragen

Alle vier laufen **auf der Nutzer-Maschine** (Egress-Sperre), sind oeffentlich und keyfrei, und **jede kann einen Kandidaten vorab toeten**. Sie kosten Minuten und werden vor jeder Registrierung beantwortet.

| ID | Frage und Endpunkt | Vorab fixierte Konsequenz | Betroffen |
|---|---|---|---|
| **V-1** | **Tiefe von `/v5/market/funding/history` je Symbol.** `category=linear`, `symbol`, `startTime`+`endTime` (nur `startTime` allein ist ein Fehler), `limit` 1-200 Default 200 [sek: Bybit-Doku-Repo]. Probe: BTCUSDT rueckwaerts paginieren bis zur ersten leeren Antwort; danach Stichprobe ueber 20 Alt-Symbole. Zusaetzlich aus `instruments-info`: **ist der Zins-Term `I` und das Funding-Intervall ueber die Kontraktklassen identisch?** | Reicht die Historie fuer **< 110 Symbole** ueber beide urteilstragenden Fenster: A1 in der Breitenform TOT. Traegt `I` je Kontraktklasse **verschiedene** Werte: A1s Nulleffekt ist nicht 0, sondern `I_A - I_B`, und die Sortierung darf nur innerhalb einer Klasse laufen (R1-K-02-Vorbehalt via Review 3.2). Die Behandlung von 1h- vs. 8h-Symbolen ist damit **Registrierungsbedingung**, nicht Feintuning. | A1 |
| **V-2** | **`turnover24h` der datierten Bybit-Futures.** Ein `GET /v5/market/tickers`-Call je Kategorie; `contractType` `LinearFutures` (USDC-Futures, Symbolform `BTC-24MAR23`) und `InverseFutures` (Quartale `BTCUSDH/M/U/Z<yy>`, live `BTCUSD_Q`/`BTCUSD_BIQ`) sind belegt (R1 0.5). | Liegt `turnover24h` des vordersten datierten Kontrakts **unter ~1 % des Perp-Umsatzes**, ist der Quote-Spread der bindende Kostenblock und nicht die Gebuehr: **A4 TOT** (R1-K-03 "Was ihn a priori toetet", Punkt i). Listet Bybit die Kontrakte nur sporadisch (keine durchgehende Quartalsleiter), ist `N_zyklen >= 8` unerreichbar: **A4 TOT**. | A4 |
| **V-3** | **Median(Ist-Funding - I) auf den vorhandenen Harvest-Tagen.** Aus `bybit/rest.fundingRate` (113 Tage ab 2026-03-19, Kompendium F.1) gegen `I = 0,01 %/8h = 3,0 bp/Tag = 10,95 % p.a.` (R1 0.2, belegt). | Liegt der Median nahe 0 (innerhalb des Messrauschens), ist der mechanische Anker bestaetigt und A1s Kuerzungs-Argument (Par. 5.1) empirisch untermauert. Weicht er systematisch ab, ist die Anker-Herleitung fuer Bybit falsch und **jede** Funding-Rechnung des Programms wird neu aufgesetzt, bevor A1 registriert wird. **Wichtig:** 113 Tage schliessen die 10.10.2025-Episode **aus** - V-3 ist Plausibilitaets-, keine Stress-Aussage. | A1, A4 |
| **V-4** | **Delivery-/Settlement-Gebuehr an der PRIMAERQUELLE**, fuer Optionen UND datierte Futures. R1 traegt fuer Optionen `min(1,5 bp Index; 12,5 % des Intrinsic)`, nur bei ITM-Auto-Exercise, 2 bp fuer SOL/XRP/DOGE/MNT ein - **[sek], Primaerseite egress-blockiert**. R1-K-03 unterstellt fuer datierte Futures ein **gebuehrenfreies** Settlement - **ohne jede Quelle**. | **Entscheidung (Review 3.4, ohne Abstriche):** R1s Zahl darf **nicht** nach `constants.py`; sie ist ausschliesslich als zweiseitige Sensitivitaetsgrenze zulaessig. Bleibt die Gebuehr nach V-4 ungemessen, **RAISED** jeder Halte-bis-Verfall-Pfad (Optionen) und jeder Settlement-Pfad (datierte Futures) - A4 verliert damit sein Alleinstellungsmerkmal ("3 Fills statt 4") und A5 bleibt gesperrt. | A4, A5, H-26b |

**Ausgabeform.** Je Vorfrage ein Einzeiler (PowerShell/`curl`) plus eine Zeile Befund im Welle-1-Befunddokument, mit Zeitstempel und dem rohen Antwort-Ausschnitt als Beleg. Keine Interpretation ohne den Rohbeleg - C.8.

---

## 5. Alpha-Kandidaten A1-A5 - REGISTRIERUNGS-ENTWUERFE

> **Statuszeile, fuer jeden der fuenf gueltig: NOCH NICHT REGISTRIERT.** Diese Abschnitte sind Entwuerfe im 3.0-Template (Par. 3.4). Die Registrierung erfolgt durch den Orchestrator, **nach** Welle 1 und **nach** Beschluss von DEC-51 und DEC-52 - in dieser Reihenfolge (Review 4.1 Auflage 1). Jede hier genannte Schwelle, die "nach WP-7" heisst, ist bis dahin bewusst offen und wird aus einer gemessenen Groesse hergeleitet, nie gesetzt.

### 5.1 A1 - Querschnitts-Funding-Carry, perp-only (aus R2-K-02), Klasse P

**Hypothese.** Ein dollarneutrales Dezil-Long-Short-Portfolio auf Bybit-Linear-Perps, sortiert nach dem intervall-normierten Funding-Satz der letzten 3-7 Tage (long das niedrigste, short das hoechste Dezil), erzielt ueber eine Wochen-Halteperiode eine Gesamtrendite, die **nicht** vollstaendig durch die kompensierende Preisdrift aufgezehrt wird - und die auch nach Orthogonalisierung gegen Momentum und Reversal ein Residuum behaelt.

**Ertragsquelle: Praemie, nicht Prognose.** Der Funding-Satz ist eine explizite, mehrfach taeglich ausgezahlte Kompensation dafuer, den unbeliebten Seite eines Perp zu halten. **Zahler:** der gehebelte Long im Bullenmarkt (bzw. der gehebelte Short im Ausverkauf), der Sofort-Exposure ohne Kapitaleinsatz kauft. **Zahler-Bestand nach 2024 (3.3.9c):** der Mechanismus ist gebuehren- und produktseitig unveraendert, aber Basis- und Spread-Abweichungen fallen im Mittel ~11 % pro Jahr, konsistent mit zunehmendem Arbitragekapital [sek]; die REZENZ-Klausel ist deshalb zwingend, und ein 2025 negativ gewordener delta-neutraler Carry [sek] ist ein Erosions-Indiz, das im Registrierungstext stehen muss.

**Warum genau dieser Kandidat.** Er ist der einzige im gesamten Feld, bei dem Mechanismus, Zahler, Friktion (kein Spot-Bein) und ein **exakt ausrechenbarer** Nulleffekt gleichzeitig stimmen (Review 5.1 Rang 2). Das Spot-Bein wegzulassen ist keine Kosmetik: die Spot-Seite kostet **10 bp je Bein und ist nicht durch passive Ausfuehrung verbilligbar (Maker == Taker)** - sie ist 20 bp von den 31 bp eines Spot/Perp-Round-Trips (R1 0.3). Jede Praemien-Struktur ohne Spot-Bein spart ~65 % ihrer Friktion.

**Der strukturelle Nulleffekt - vier Komponenten, je einzeln hergeleitet.**

*(a) Der Zinsanker `I` und warum er sich im Querschnitt herauskuerzt.* Bybit rechnet `F = P + clamp(I - P, +/-0,05 %)` mit `P` = gewichteter Premium-Index und `I` = Zins-Term; `I` ist fuer Standard-USDT-Perps auf **0,03 % pro Tag = 0,01 % je 8h** gesetzt [sek, R1 0.2]. Solange `|I - P| <= 0,05 %` gilt, ist `F = P + (I - P) = I` **exakt** - der Erwartungswert der Funding-Rate ist damit mechanisch bei **+10,95 % p.a. = 3,0 bp/Tag** verankert, nicht bei 0. **An genau diesem Anker stirbt R1-K-01** (die Spot/Perp-Form): dort ist `r_excess = (I - Kostendrift) - (I - r_USD) = r_USD - Kostendrift`, mit dem vom Bericht selbst geforderten konservativen `r_USD = 0` und der 30-Tage-Drift 3,77 % p.a. also **-3,77 % p.a.**; die registrierte Schwelle +4,0 % p.a. haette ein realisiertes Funding von **>= 18,7 % p.a.** verlangt, 71 % ueber dem Anker, in zwei disjunkten Fenstern (Review 2.1).

Im **Querschnitt** faellt der Anker exakt heraus. Die Funding-Zahlung des Portfolios ist

```
CF = mean_{j in Dezil_hoch}(F_j) - mean_{i in Dezil_niedrig}(F_i)
```

und mit `F_k = I + d_k` (`d_k` = symbolspezifische Abweichung vom Anker) gilt

```
CF = ( I + mean_hoch(d) ) - ( I + mean_niedrig(d) ) = mean_hoch(d) - mean_niedrig(d).
```

`I` kuerzt sich **identisch heraus**, weil alle Standard-USDT-Perps **denselben** `I` tragen. Der Anker-Beitrag zum Nulleffekt ist damit **exakt 0** - vorbehaltlich der Verifikation, dass `I` und das Funding-Intervall ueber die einbezogenen Kontraktklassen tatsaechlich identisch sind (**V-1**). Traegt eine Klasse ein anderes `I`, ist der Nulleffekt `I_A - I_B` und die Sortierung darf nur **innerhalb** einer Klasse laufen (R1-K-02-Vorbehalt via Review 3.2). *Weder R1 noch R2 haben diesen Zusammenhang hergestellt: R1 findet den Anker und uebersieht, dass die Querschnittsform ihn neutralisiert; R2 baut die Querschnittsform und zitiert die 11 % p.a. als "typische" Rate statt als mechanischen Anker.*

*(b) Funding-Intervall-Heterogenitaet (1h vs. 8h) - der Sortierschluessel-Killer.* Bybit fuehrt Symbole mit 8h- UND mit 1h-Funding, und Intervalle aendern sich ueber die Historie; bei Anschlag der Cap-Grenze springt die Frequenz auf stuendlich [sek, R1 0.2]. R1s Anker und R2s Record-Zahl (5,5 a x 3/Tag = 6.023) setzen beide ein konstantes 8-Stunden-Intervall voraus (Review 2.9). **Ohne Intervall-Normierung sortiert der Schluessel Symbole nach Abrechnungsfrequenz statt nach Rate:** ein 1h-Symbol mit demselben Wert je Intervall zahlt **8-fach** so viel pro Tag. Verbindlich fuer A1:

```
f_taeglich_i = funding_sum_i / n_Tage        (nicht: mittlere Rate je Intervall)
```

unter Verwendung der Pflichtspalte `funding_n` aus WP-7 (R4 3.5). Der Zins-Term fuer 1h-Symbole (`I/8` je Stunde?) ist **UNBELEGT - Vorfrage V-1**; solange er offen ist, laeuft A1 ausschliesslich auf der homogenen 8h-Klasse und weist die ausgeschlossene Symbolmenge namentlich aus.

*(c) Die No-Arbitrage-Null.* Unter der Nullhypothese ist der Funding-Cashflow **exakt** durch die Preisdrift kompensiert; die Gesamtrendite ist 0. **Urteilstragend ist deshalb die SUMME** aus Funding-Akkumulation und Preisbein, nie der Cashflow allein - er ist trivial da. Die Zerlegung wird verpflichtend mitberichtet, weil ein positives Gesamtergebnis bei stark negativem Preisbein eine andere Aussage ist als eines mit neutralem Preisbein.

*(d) Die versteckte Reversal-Ladung.* Das Short-Bein sind per Konstruktion die Perps mit dem staerksten juengsten Preisanstieg (Funding korreliert mechanisch mit Momentum) - A1 ist ohne Orthogonalisierung ein **verstecktes Reversal-Portfolio**. **Urteilstragend ist das Residual-Alpha** nach Regression gegen die A3-Faktoren (Momentum, Reversal), nicht die Rohrendite. Bleibt kein Residuum, ist A1 nur ein teuer verpacktes A3 und wird **nicht** als eigener Kandidat weitergefuehrt.

**Daten.** `GET /v5/market/funding/history` (oeffentlich, `limit` 1-200 [sek]): 5,5 a x 3/Tag = 6.023 Records = 31 Calls/Symbol; bei K~300 also ~9.300 Calls, ~15 min. Plus das `panel_1d` aus WP-7 fuer das Preisbein. Der Harvest-Bestand allein reicht **nicht**: `bybit/rest.fundingRate` hat 113 Tage ab 2026-03-19 (Kompendium F.1) und schliesst die groesste bekannte Stress-Episode (10.10.2025) aus - der REST-Backfill ist Vorbedingung, nicht Komfort. Historische Tiefe je Symbol: **UNBELEGT - Vorfrage V-1**.

**Fenster (REZENZ, C.18/DEC-38).** W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-30, beide urteilstragend, je 52 Wochen. Historie vor 2024-07 ist ausschliesslich deskriptives Aera-Profil und **nie** urteilstragend. **Stress-Pflicht (DEC-53):** mindestens eine Stress-Episode je Fenster; die 10.10.2025-Episode liegt in W2.

**Metrik.** Nicht-ueberlappende Wochen-Gesamtrendite des Dezil-L/S-Portfolios in bps, zerlegt in (i) Funding-Akkumulation und (ii) Preisbein; urteilstragend ist der Mittelwert der Summe, sowie das Residual-Alpha nach (d).

**Power-Zeile (DEC-51: alpha 0,05 einseitig, Power 0,80, z = 2,4865).** Cluster-Einheit ist die **nicht-ueberlappende Kalenderwoche**; `N_eff` = 52 je Fenster, 104 gepoolt, korrigiert um die Autokorrelation der Wochenrenditen ueber den stationaeren Bootstrap (Politis/Romano 1994; Blocklaenge nach Politis/White 2004 [sek]).

```
detektierbarer Mittelwert = 2,4865 * sigma_LS / sqrt(W)
  je Fenster (W=52):  0,34489 * sigma_LS
  gepoolt   (W=104):  0,24384 * sigma_LS
```

`sigma_LS` (Wochen-SD der Dezil-L/S-Rendite auf dem breiten Panel) ist **UNGEMESSEN - WP-7**. Die oekonomische Mindestmagnitude (Etikett, nicht Gate) betraegt bei Turnover 0,6 und 2x Brutto **2 x 18 = 36 bps/Woche** (Kosten aus R2 0.1; Faktor 2 aus R4 1.1c). Daraus die vorab fixierte Feasibility-Bedingung:

| Design | Feasibility-Bedingung an das WP-7-Messergebnis |
|---|---|
| Per-Fenster (C.10 hart) | `sigma_LS <= 36 / 0,34489 = 104 bps/Woche` |
| Gepoolt (DEC-52) | `sigma_LS <= 36 / 0,24384 = 148 bps/Woche` |

Misst WP-7 ein groesseres `sigma_LS`, ist A1 in der jeweiligen Form ein struktureller A-priori-DROP nach GL-012 (C.12) - **ohne Datenlauf**, wie H-07.

**Selektions-K.** `K = 3` (Lookback-Laengen 3 / 5 / 7 Tage), vorab registriert. Analytische Decke nach R4 K-0.3 bei `sigma_SR = 1/sqrt(2)` (T = 2 Jahre urteilstragend): `E[max SR] = 0,7071 * (0,4228*0,4307 + 0,5772*1,1614) = 0,60`. Da Sharpe hier nur berichtet und nie geurteilt wird (Par. 3.6), dient die Decke als Kontext; die **gemessene** Decke am Null-Fixture (3.3.4) ist verbindlich.

**Schwelle.** Wird **nach WP-7** aus dem gemessenen `sigma_LS` hergeleitet als `mean_min = max( obere CI-Grenze des gemessenen Nulleffekts ; 2,4865 * sigma_LS/sqrt(W) )` und als **Herleitungs-Referenz** (Pfad + Test-ID) registriert, nie als nackter Skalar (DEC-54b). Eine importierte oder gesetzte Zahl waere ein C-14-Wiedergaenger.

**Gate-Text (woertlich, wie er in die Registry geht).**

> **A1 gilt als kapitalfrei BESTANDEN, wenn saemtliche Bedingungen erfuellt sind:** (1) Der Mittelwert der nicht-ueberlappenden Wochen-Gesamtrendite des Dezil-L/S- Portfolios erreicht in **beiden** urteilstragenden Fenstern das **gleiche Vorzeichen UND jeweils >= 0,5x die registrierte Schwelle** (DEC-52 (ii)); (2) der **gepoolte** Schaetzer ist mit fenster-geclustertem stationaerem Bootstrap bei **alpha = 0,01** signifikant (DEC-52 (iii)/(iv)); (3) das Ergebnis liegt oberhalb der am Null-Fixture GEMESSENEN Selektions-Decke fuer K = 3; (4) das **Residual-Alpha** nach Orthogonalisierung gegen Momentum und Reversal traegt das Urteil, nicht die Rohrendite; (5) die Funding-Buchhaltung ist intervall-normiert (`funding_n`) und die einbezogene Symbolmenge ist namentlich ausgewiesen; (6) jedes urteilstragende Fenster enthaelt **>= 1 Stress-Episode** nach DEC-53, sonst **KEIN VERDIKT**, nicht WEITER; (7) das Gate faellt auf dem adversarialen Peso-Fixture nachweislich durch. **Ein PASS ist ein kapitalfreies WEITER und traegt verpflichtend das Etikett: "Praemien-EXISTENZ; die risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER." Kein Kapitalschritt folgt daraus.** Sharpe, MaxDD und Tail-Ratio werden mit ihren hergeleiteten Rauschboeden BERICHTET und tragen kein Urteil.

**Entscheidungsrelevanz-Zeile.** *Bei PASS:* Es folgt genau ein Schritt - die getrennt zu registrierende Tradability-Pruefung **A1b** (symbolspezifische Slippage aus WP-7 statt der Majors-Konstante, Kapitalbindung nach Par. 3.3.9a, Steuerbehandlung nach Par. 8.2, Ausfuehrbarkeit nach Par. 8.1). Kein Kapital, keine Order, kein Live-Code. *Bei DROP:* Die Praemien-Klasse P ist auf Perp-Funding im Querschnitt erschoepft; A4 bleibt der einzige verbleibende Klasse-P-Pfad ausserhalb der Optionen. *Oekonomische Mindestmagnitude (Etikett):* 36 bps/Woche.

**Etiketten.** `Klasse P`; `kapitalfrei`; `Praemien-EXISTENZ / Tradability PARK`; `Zahler-Erosion belegt [sek] - REZENZ zwingend`; `Steuerregime UNBELEGT (Par. 8.2)`; `Kapital-Multiplikator m UNGEMESSEN`.

**Feasibility-Kill-Bedingungen (vorab fixiert).**
1. WP-7: `rho_quer > 0,03` -> A1 in der Breitenform tot (nur die reine Funding-Zerlegung bleibt, ohne Querschnitts-Anspruch).
2. WP-7: `sigma_LS` verletzt die Tabelle oben -> struktureller GL-012-DROP.
3. V-1: Funding-Historie reicht fuer < 110 Symbole ueber beide Fenster -> tot.
4. Die Autokorrelation des Funding-Sortierschluessels ueber eine Woche liegt **unter 0,30** -> das Signal ist bei Handelsbeginn bereits verfallen -> tot. (Diese Zahl wird in WP-7 mitgemessen.)
5. Nach Orthogonalisierung gegen Momentum/Reversal bleibt kein Residuum -> A1 ist ein verpacktes A3 und wird nicht als eigener Kandidat gefuehrt.

**DEC-39-Fixtures.**
- *Positiv:* synthetisches Panel, in dem der Funding-Cashflow zu 50 % **nicht** durch das Preisbein kompensiert wird; das Gate muss feuern und die injizierte Praemie im CI wiederfinden.
- *Null:* Panel mit **exakter** Kompensation; die Gesamtrendite muss statistisch 0 sein. Dieser Fixture prueft direkt die Buchhaltung der Funding-Akkumulation - der haeufigste Implementierungsfehler dieser Klasse - **und** die Intervall-Normierung: das Panel enthaelt 8h- und 1h-Symbole nebeneinander.
- *Adversarial (Peso, Pflicht fuer Klasse P):* Nullpraemie plus Merton-Spruenge, Rate 1/3 Jahre, Hoehe -35 %. Ein 5-Jahres-Fenster ist mit `p = e^-1,67 = 0,19` sprungfrei und zeigt dann eine scheinbar hohe, hochsignifikante Praemie. **Das Gate MUSS durchfallen**; besteht es, ist es kaputt.

**FDR.** Familie `F-CARRY1` = die 3 Lookback-Varianten von A1, BH bei alpha = 0,10. Ueber-Familie `F-PREM` ueber alle Praemien-Kandidaten der Welle (DEC-22, C.16, rein verschaerfend). **Vorbehalt aus WP-10:** faellt WP-10(A) auf A-B3 (kein Verdikt zur Kohaerenz), wird die Ueber-Familie in der abhaengigkeitsrobusten Form gefahren (Par. 4.3).

**Bedingung aus Welle 1.** WP-7 (`rho_quer`, `K`, `sigma_xs`, `sigma_LS`, `PERP_SPREAD_BP`), V-1 (Funding-Tiefe, `I`-Homogenitaet, Intervalle), V-3 (Anker- Plausibilitaet), WP-10 (FDR-Struktur). Zusaetzlich: **DEC-51 und DEC-52 beschlossen.**

**YAML-Block des Entwurfs** (Pflichtschluessel nach Par. 3.4; `TBD-WP7` markiert Werte, die erst aus einer Messung hergeleitet werden duerfen):

```yaml
id: A1
klasse: P
capital_free: true
hypothese: "Dezil-L/S auf intervall-normiertem Funding, perp-only, Wochenhalteperiode; Gesamtrendite nicht vollstaendig durch die Preisdrift kompensiert, Residuum nach Orthogonalisierung"
ertragsquelle: "Praemie; Zahler: gehebelter Long (bzw. Short im Ausverkauf), der Sofort-Exposure kauft"
metric: "mean(nicht-ueberlappende Wochen-Gesamtrendite Dezil-L/S, bps), plus Residual-Alpha"
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, rolle: urteilstragend}
  - {id: AERA, von: 2020-03-25, bis: 2024-06-30, rolle: aera-profil}
threshold: {wert: TBD-WP7, ref: "research/a1_carry/thresholds.py#test_threshold_from_sigma_ls"}
structural_null:
  komponenten: [zinsanker_kuerzt_sich, intervall_heterogenitaet, no_arbitrage_kompensation, reversal_ladung]
  wert: "0 fuer den Ankerterm (Beweis Par. 5.1a); Gesamtnull TBD-WP7"
  ref: "tests/test_a1_null_fixture.py#test_exact_compensation_and_interval_mix"
power: {alpha: 0.05, sided: one, power: 0.80, z: 2.4865, cluster_unit: kalenderwoche,
        n_eff: "52 je Fenster / 104 gepoolt (bootstrap-korrigiert)",
        detectable_effect: "0.34489*sigma_LS je Fenster; 0.24384*sigma_LS gepoolt",
        ref: "research/a1_carry/power.py#test_power_line"}
selection: {K: 3, ceiling_analytic: 0.60, ceiling_measured_ref: "tests/test_a1_selection_ceiling.py"}
economic_minimum: {wert: "36 bps/Woche", ref: "R2 0.1 Kostentabelle x Faktor 2 (R4 1.1c)", label: TBD-WP7}
decision_relevance:
  on_pass: "genau ein Schritt: getrennte Tradability-Registrierung A1b; kein Kapital"
  on_drop: "Klasse P auf Perp-Funding im Querschnitt erschoepft"
capital_tax_venue:
  kapitalbasis: "Margin beider Perp-Beine; Multiplikator m UNGEMESSEN, Pflicht-Sensitivitaet"
  steuer: "UNBELEGT - Nutzer-Entscheidung Par. 8.2; Funding = laufender Ertrag"
  venue_event: "ADL auf dem gewinnenden Bein; 1 %/Jahr Totalverlust = 10-20 % Abschlag (Review 6.3)"
  zahler_post_2024: "Basis-Kompression ~11 %/Jahr [sek] - Erosion belegt, REZENZ zwingend"
stress_episode: {liste_ref: "fixtures/stress_days.json#dec53", n_episoden_im_fenster: TBD-WP7}
irreversibility_probe: {ergebnis: nachladbar, ref: "V-1"}
positive_control: {laufzeit_geschaetzt_h: 0.2, vorgeschaltet: false, ref: "tests/test_a1_positive.py"}
fixtures: {positive: "tests/test_a1_positive.py", null: "tests/test_a1_null_fixture.py",
           adversarial: "tests/test_a1_peso.py"}
fdr_family: F-CARRY1
over_family: F-PREM
feasibility_verdict: TBD-WP7
constants_hash: "n/a - kapitalfreies Mess-Gate ohne Kostenmodell; A1b traegt den Hash"
data_fingerprints: [TBD-WP7]
stats3_version: TBD
bedingung_welle_1: [WP-7, V-1, V-3, WP-10, DEC-51, DEC-52]
```

### 5.2 A2 - EXP-CLOCK, Verfallskalender als Ereignistakt (aus R3-K-31), Klasse E

**Hypothese.** Im mechanisch erzwungenen Settlement-Fenster der Krypto-Options-Verfaelle (30-Minuten-Index-TWAP 07:30-08:00 UTC) tritt hedge-getriebener, preis-unelastischer Fluss konzentriert auf und verschwindet danach; das erzeugt eine messbare, gegen Placebos abgegrenzte Renditeverzerrung auf dem Bybit-Perp BTCUSDT/ETHUSDT.

**Ertragsquelle: Ereignis.** Options-Market-Maker sind im Aggregat netto short Gamma auf kurzlaufenden Kontrakten; ihr Delta-Hedge ist in den letzten Stunden maximal preis-sensitiv und faellt um 08:00 UTC schlagartig auf null. **Zahler:** die Options-Halter/-Schreiber ueber den Vermoegenstransfer am Settlement und die Liquiditaetsnehmer im Fenster ueber den temporaeren Impact. *Evidenz:* Ni/Pearson/Poteshman (2005, JFE 78(1)): Renditen optionierter Aktien an Verfallstagen im Mittel um **>= 16,5 bps** verzerrt [sek, Volltext egress-gesperrt]; Blasco/Corredor/Satrustegui (2023, IREF 85): signifikante Aenderungen um Bitcoin- Monatsverfaelle, nicht homogen ueber Boersen [sek, Groesse unbelegt]; FRL (2026): V-foermige Umkehr um Deribit-Verfaelle, am staerksten bei negativem Netto-GEX [sek]. **Gegen-Evidenz, die zitiert wird:** Max-Pain-"Pinning" ist empirisch mehrfach gescheitert; A2 misst die **Umkehr**, nicht einen Strike-Magneten.

**Daten.** **Nichts nachzuladen.** WP-0-Bar-Cache (5 Symbole, 10.054 Cache-Tage, 14,4 Mio Minutenbars) plus ein deterministisch erzeugter Verfallskalender. Optionsstroeme gehen ins Haupt-Gate **nicht** ein - die L2-Luecken und die ETH-Options-Luecke 22.-27.08. treffen A2 gar nicht.

**Fenster (REZENZ).** W1 = 2024-09-01..2025-08-31, W2 = 2025-09-01..2026-08-31, je 12 Monate; 2020-2024 ist reines Aera-Profil. Die 12-Monats-Laenge ist **vor** dem Lauf aus der Arithmetik begruendet (unten), nicht nachtraeglich waehlbar.

**Metrik.** `Delta = Mittel(Verfalls-Ereignisse) - Mittel(Placebo-Slots)` der log-Rendite in `[07:30, 08:00)` UTC (`r_pre`) und `[08:00, 09:00)` UTC (`r_post`). **Urteilstragend ist immer eine DIFFERENZ, nie ein Rohmittel.**

**Struktureller Nulleffekt = die Placebo-Verteilung** (R4 1.3b). Die gesamte Pipeline laeuft auf **Zufallsterminen mit identischer Kalenderverteilung** (gleiche Anzahl, Wochentags-, Tageszeit- und Cluster-Struktur), 1.000-fach; Mittelwert und Quantile dieser Verteilung sind der Nulleffekt, die Schwelle liegt darueber. Drei vorregistrierte Placebos: (P1) Nicht-Verfalls-Freitage im selben Uhrzeit-Fenster; (P2) **Nicht-Freitags-08:00-UTC- Slots** - zwingend, weil Bybits USDT-Perp-Funding um 00:00/08:00/16:00 UTC abgerechnet wird; ohne P2 misst A2 H-01 neu, und H-01 ist DROP; (P3) alle uebrigen Tagesstunden als unbedingte Baseline.

**Power-Zeile (DEC-51), mit der Review-Korrektur gerechnet.** R3 rechnete `SE = 36/sqrt(104) = 3,5 bps` und meldete "3,4 SE - Feasibility bestanden". Das poolt BTC und ETH als unabhaengige Ereignisse. Korrektur (Review 2.3): BTC- und ETH-Stundenrenditen korrelieren ~0,8, also

```
N_eff je Ereignis = 2 / (1 + (2-1)*0,8) = 2/1,8 = 1,111
effektive Ereigniszahl je Fenster = 52 * 1,111 = 57,8  ->  58
SE(Ereignismittel) = 36 / sqrt(58) = 4,73 bps
```

Zusaetzlich ist `Delta` eine **Differenz** gegen Placebos, deren SE hinzukommt. Fuer P2 (Nicht-Freitags-08:00-Slots, ~313 Tage/Jahr, ebenfalls BTC/ETH-geclustert: `N_eff = 348`, `SE_pl = 36/sqrt(348) = 1,93 bps`):

```
SE(Delta) = sqrt(4,73^2 + 1,93^2) = 5,11 bps
12 bps  =  2,35 SE
Per-Fenster-Power (DEC-51) = Phi(2,35 - 1,6449) = Phi(0,705) = 0,76
Ueber zwei Fenster (hartes C.10) = 0,58; nach BH innerhalb der Familie weniger.
```

Zum Vergleich unter R3s zweiseitiger Lesart: Power je Fenster 0,72, ueber zwei Fenster 0,52 (Review 2.3). **Die Behauptung "Feasibility bestanden (3,4 SE)" ist um rund ein Drittel zu optimistisch;** die 12-Monats-Fassung bleibt knapp tragfaehig, die 6-Monats-Fassung ist es klar nicht (`SE ~ 6,9 bps`, 12 bps = 1,7 SE). **Per-Fenster-Power 0,76 liegt ueber 0,60 - DEC-52 (i) ist damit fuer A2 NICHT anwendbar; C.10 gilt fuer A2 hart und unveraendert.**

> **Offener Konstruktionspunkt A2-P1 (vor der Registrierung zu entscheiden, vom Review nicht erfasst).** Deribit fuehrt woechentliche Freitags-Verfaelle; damit ist **nahezu jeder** Freitag ein Verfallstag und Placebo P1 ("Nicht-Verfalls-Freitage") faktisch leer. Die beiden vorab durchgerechneten Auswege: **(a)** Ereignismenge bleibt die woechentlichen Verfaelle (N = 52/Symbol/Fenster, Power wie oben 0,76) und P1 wird ersatzlos gestrichen, das Urteil traegt P2 und P3; **(b)** Ereignismenge wird auf Monatsverfaelle (letzter Freitag) verengt, dann `N = 12/Symbol/Fenster`, `N_eff = 13,3`, `SE = 36/sqrt(13,3) = 9,87 bps`, `12 bps = 1,22 SE`, Per-Fenster-Power `Phi(1,22-1,6449) = 0,34`, ueber zwei Fenster **0,11** - struktureller GL-012-DROP. **Arithmetisch ist nur (a) registrierbar.** Der Orchestrator entscheidet; das PRD dokumentiert die Rechnung, damit die Entscheidung nicht nach dem Sehen einer Zahl faellt.

**Cluster-Einheit.** Das **Verfallsereignis als Kalender-Cluster ueber beide Symbole** (BTC und ETH am selben Termin sind EIN Cluster, nicht zwei). Bootstrap-Einheit ist der ganze Handelstag; N-Floor gilt fuer `N_cluster`, nicht `N_events` (3.3.3).

**Selektions-K.** `K = 2` (die beiden vorregistrierten Fenstertypen `r_pre`, `r_post`). Kein Fenster-Scan, keine Sigma-Nachsuche, kein Freiheitsgrad im Ereigniszeitpunkt - das Ereignis ist exogen-kalendarisch und ex ante bekannt.

**Schwelle.** `|Delta| >= 12 bps` gegen **alle** Placebos gleichzeitig, gleiches Vorzeichen in beiden Fenstern, Block-Bootstrap-p <= 0,05 (Bloecke = ganze Handelstage, 1.000 Reps). Herleitung: 2,35 SE ueber dem korrigierten Rauschboden 5,11 bps (oben), **nicht** aus einer importierten Zahl. Die 12 bps liegen bewusst **unter** der 11-bp-Taker- und der 15-bp-Gesamtwand.

**Gate-Text (woertlich).**

> **A2 gilt als kapitalfrei BESTANDEN, wenn:** (1) `|Delta| >= 12 bps` in **beiden** urteilstragenden 12-Monats-Fenstern, mit **gleichem Vorzeichen** (C.10 hart, DEC-52 nicht anwendbar, weil die Per-Fenster-Power 0,76 > 0,60 betraegt); (2) `Delta` signifikant gegen **alle** vorregistrierten Placebos gleichzeitig, Block-Bootstrap p <= 0,05 auf Kalender-Clustern; (3) `Delta` bestehen bleibt, nachdem BTC und ETH zu **einer** Teststatistik gepoolt wurden (Panel-Mitglieder sind keine Hypothesen, L-7); (4) das **Negativ-Panel aus Realdaten** (XRP/BNB ohne liquide Optionskette) **kein** vergleichbares Delta zeigt; (5) das Gate auf dem adversarialen Fixture (auf vergangenen Renditen selektierte Ereignisse auf einem Random Walk) durchfaellt. **Pflicht-Etikett bei PASS, woertlich: "Der beste Fall (12 bps) liegt UNTER der Friktionswand (11 bps Taker-Round-Trip, ~15 bps inkl. Slippage). Ein PASS hat a priori keine Handelsperspektive als Taker; die Welle gibt diesen Alpha-Slot bewusst fuer eine wissentlich sub-Wand-Messung aus. Eine Tradability-Folge ist NICHT impliziert und NICHT registriert."**

**Entscheidungsrelevanz.** *Bei PASS:* (i) der Ereignis-Mechanismus ist erstmals im Programm nachgewiesen und wird **Pflicht-Eingang in jede spaetere Halte-bis-Verfall- Rechnung** des Options-Blocks (A5) - R1-K-04 settlet sonst systematisch in die Verzerrung hinein, ein Kostenposten, den R1s Tabelle nicht fuehrt (Review 3.5); (ii) **erst dann** darf ein Harvester-Auftrag fuer ein Options-Taker-Tape (R3-K-32/GEX) gestellt werden - vorher ist das eine Datenpipeline fuer den Term zweiter Ordnung eines unvalidierten Terms erster Ordnung (Review 5.2 Punkt 1, S4/S5-Falle). *Bei DROP:* der Verfallskalender ist als Ereignistakt erledigt; K-32 entfaellt ersatzlos. *Oekonomische Mindestmagnitude (Etikett):* 11 bps Taker-RT / 4 bps Maker-RT - der beste Fall liegt zwischen beiden.

**Etiketten.** `Klasse E`; `kapitalfrei`; `Alpha-Slot bewusst sub-Wand`; `kein Nachladeaufwand`; `Negativ-Panel aus Realdaten`.

**Feasibility-Kill-Bedingungen.** (1) P2 erklaert den Effekt vollstaendig -> es ist der Funding-Settlement-Takt und damit H-01, tot. (2) Vorzeichenwechsel zwischen W1 und W2 (C.10 hart, wie H-20). (3) `Delta` lebt nur im Aera-Profil vor 2024 (REZENZ, wie H-22). (4) Das Negativ-Panel zeigt denselben Effekt -> Wochentags-/Uhrzeit-Artefakt. (5) Konstruktionspunkt A2-P1 wird zugunsten der Monatsverfaelle entschieden -> Power 0,11, struktureller DROP ohne Datenlauf.

**DEC-39-Fixtures.** *Positiv:* injizierter CAR +50 bps an bekannten, absichtlich stark geclusterten Terminen; das Gate muss ihn finden. *Null:* dieselben Termine ohne Effekt. *Adversarial:* Ereignisse, die auf **vergangenen Renditen** selektiert werden ("grosse Bewegung"), auf einem reinen Random Walk - das erzeugt scheinbare Mean-Reversion im Ereignisfenster und ist exakt die Fehlerklasse H-20; nach Placebo-Kalibrierung MUSS der Effekt verschwinden. *Zusaetzlich, gratis und aus Realdaten:* XRP/BNB (und SOL vor 2025) haben ueber den Grossteil der Historie keine liquide Optionskette - dort MUSS `Delta ~ 0` sein.

**FDR.** `F-EXPCLOCK` = **2 Tests** (`r_pre`, `r_post`), BH bei alpha = 0,10. **Korrektur gegenueber R3:** R3 rechnete 8 Zellen (2 Symbole x 2 Fenster x 2 Fenstertypen). Nach L-7/R4 1.2f sind Panel-Mitglieder keine Hypothesen (BTC/ETH werden gepoolt) und die zwei Fenster sind die Zwei-Fenster-Regel, kein Multiple-Testing-Problem. Das Negativ-Panel ist NICHT Teil der Familie (Placebo-Konvention aus H-09). Ueber-Familie `F-EVENT`.

**Bedingung aus Welle 1.** Keine Datenbedingung (laeuft auf dem Bestand). Bedingungen: DEC-51 beschlossen; DEC-53 (Stress-Kanon) gepinnt; Konstruktionspunkt A2-P1 entschieden; Funding-Settlement-Zeiten gegen die Boersen-Doku verifiziert (Teil von V-1). **A2 ist damit der frueheste laufbereite Kandidat.**

### 5.3 A3 - Kohorte F-XSEC1: Momentum, Reversal, Vol-Anomalie (aus R2-K-01/K-04/K-05), Klasse W

**Status: streng konditional.** A3 wird **nur** registriert, wenn WP-7 `rho_quer <= 0,03` **UND** `K >= 110` liefert **UND** DEC-52 beschlossen ist. Andernfalls wird die Kohorte **gestrichen und nie auf N=5 zurueckskaliert** - das waere D.7/H-07 zum zweiten Mal, nur an der Korrelationsachse (Review 1-R2-K-01).

**Die drei Faktoren, mit ihrer je eigenen Ertragsquelle und Null.**

| Faktor | Ertragsquelle / Zahler | Struktureller Nulleffekt (vor der Schwelle auszurechnen) |
|---|---|---|
| **A3-M** Querschnitts-Momentum (Formation 1/2/4 Wochen, Halten 1 Woche) | Prognose; Zahler: der spaet einsteigende Momentum-Chaser und der aus einer Verlustposition getriebene Halter | Querschnitts-Permutation **innerhalb** jeder Woche, 1.000-fach, ganze Pipeline neu gerechnet - diese Verteilung enthaelt die tatsaechliche effektive Breite exakt, ohne dass `rho_quer` geschaetzt werden muss (R4 1.2b(1)). Plus Vol-Drag-Differenz und Rebalancing-Effekt. Plus Persistenz-Null (AR(1) unter der Null simulieren; Valkanov 2003 / BRW 2008 [sek]) |
| **A3-R** Kurzfrist-Reversal (Formation 1 Woche, Halten 1 Woche) | Praemie (Liquiditaetsbereitstellung); Zahler: der Fluss, der eine grosse Positionsaenderung durchdruecken muss, und der liquidierte gehebelte Halter | **Bid-Ask-Bounce**: ein 1-Wochen-Reversal auf Schlusskursen erzeugt auch **ohne jede oekonomische Reversion** einen positiven Reversal-IC. **Verbindlich: das Gap-Design (Formation und Halteperiode um einen Tag getrennt) ist die PRIMAERE Fassung**, nicht die Alternative - es eliminiert den Bounce strukturell, statt ihn zu schaetzen (Review 1-R2-K-04). |
| **A3-V** Vol-/Beta-/MAX-Anomalie (Halten 1 Woche, vol-gewichtet) | Praemie (Lotterie-Nachfrage; die BAB-Hebelbeschraenkungs-Begruendung traegt in Krypto **nicht**, weil 25-100x Hebel verfuegbar sind) | **Vol-Drag, die schaerfste Null des gesamten Feldes:** bei log-normalen Renditen ist `E[r_arith] - E[r_geom] = sigma^2/2`; bei sigma_taeglich 5 % vs. 2 % ist die Differenz `(0,05^2 - 0,02^2)/2 = 0,105 %/Tag = 0,735 %/Woche = 73,5 bps/Woche` - **groesser als jede erwartete Kante**. Verbindlich: (i) vol-gewichtete Konstruktion, (ii) Rest-Drag vorab analytisch abgezogen, (iii) Permutations-Null auf **identisch vol-geschichteten** Zufallsportfolios. |

**Wichtiger Vorbehalt zu A3-V (Review 1-R2-K-05).** Die urteilstragende Groesse ist ein **Residuum nach Abzug eines Terms, der groesser ist als es selbst** - also schaetzfehler-dominiert. Die Registrierung muss **vor** dem Lauf das Verhaeltnis Nullterm/Erwartungseffekt ausweisen und einen Feasibility-Check bestehen, dass das Residuum in der beanspruchten Genauigkeit ueberhaupt schaetzbar ist. Faellt der Check durch, wird A3-V nicht registriert.

**Daten.** Vollstaendig aus dem WP-7-`panel_1d`; Zusatzkosten null.

**Fenster.** W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-30 (REZENZ). Rollen nach DEC-52: je Fenster nur Vorzeichen-Konsistenz plus Magnituden-Band [0,5x; 2,0x], das Signifikanzurteil auf dem gepoolten Schaetzer bei alpha = 0,01.

**Metrik.** Mittlerer wochentlicher Spearman-Rank-IC zwischen Charakteristik und Folgewochenrendite auf dem point-in-time-Universum; als Nicht-Trivialitaets-Anker zusaetzlich die Dezil-L/S-Bruttorendite. **Nicht-ueberlappend** messen (R4 1.2a); ueberlappende Fassungen laufen ohne Urteilslast.

**Power-Zeile (DEC-51).** Cluster-Einheit ist die Kalenderwoche; `N_eff` aus `N_c/(1+(N_c-1)*rho_quer)` mit dem in WP-7 **gemessenen** `rho_quer`. Detektierbarkeit nach der Tabelle in Par. 4.1: bei `rho_quer = 0,03` und `K = 170` ist der Per-Fenster-Wert 0,0664, der gepoolte 0,0469, gegen eine oekonomische Mindestmagnitude von `IC_min = 0,062` (R4 1.2d). **Per-Fenster-Power liegt damit unter 0,60 - DEC-52 (i) ist fuer A3 anwendbar und notwendig.** Die Registrierung ist nur zulaessig, wenn der **Permutations-Rauschboden auf dem TATSAECHLICHEN Panel** unter der registrierten Schwelle liegt; sonst struktureller A-priori-DROP nach GL-012, ohne Datenlauf wie H-07.

**Selektions-K.** `K = 7` (A3-M drei Formationslaengen, A3-R eine, A3-V drei Varianten Vol/Beta/MAX). Analytische Decke nach R4 K-0.3 bei T = 2 Jahren: `E[max SR] = 0,7071 * (0,4228*1,0676 + 0,5772*1,6207) = 0,98`. Verbindlich ist die am Null-Fixture GEMESSENE Decke (3.3.4).

**Schwelle.** `IC_min = 2,4865 * SE(K_gemessen, rho_quer_gemessen)` - **erst nach WP-7** gesetzt, aus dem gemessenen K und `rho_quer`, nie als importierte Literaturzahl. Das ist die direkte Anwendung der C-14-Lehre (D.2).

**Gate-Text (woertlich).**

> **Ein A3-Faktor gilt als kapitalfrei BESTANDEN, wenn:** (1) beide urteilstragenden Fenster **gleiches Vorzeichen** zeigen und je >= 0,5x die registrierte Schwelle erreichen, mit Magnituden-Band [0,5x; 2,0x] des gepoolten Werts (DEC-52 (ii)); (2) der **gepoolte** Rank-IC nach fenster-geclustertem stationaerem Bootstrap bei **alpha = 0,01** signifikant ist (DEC-52 (iii)/(iv)); (3) das Ergebnis oberhalb der **Querschnitts-Permutations-Null** liegt (1.000 Permutationen innerhalb jeder Woche, vollstaendige Pipeline) UND oberhalb der Persistenz-Null (AR(1)-Simulation); (4) BH-FDR bei alpha = 0,10 innerhalb `F-XSEC1` bestanden, danach die Ueber-Familie `F-WEEK` (DEC-22); (5) fuer A3-R zusaetzlich: der IC bleibt **im Gap-Design** erhalten UND ueberlebt den Ausschluss des untersten Liquiditaetsdezils - faellt er dort weg, ist der Befund eine reine Illiquiditaets-Artefakt-Messung und wird als solche etikettiert (H-16-Muster: Verdikt steht, Lesart wird eingeschraenkt); (6) fuer A3-V zusaetzlich: Spearman gegen die Size-/Volumen-Achse **< 0,60** (Redundanz-Gate aus H-23/GL-031), sonst Redundanz-DROP; (7) das Gate faellt auf dem adversarialen Beta-Fixture durch. **Panel-Mitglieder sind Beobachtungen, keine Hypothesen: die K Symbole werden zu EINER Teststatistik gepoolt, nie als K Tests gezaehlt (L-7).**

**Entscheidungsrelevanz.** *Bei PASS eines Faktors:* getrennte Tradability-Registrierung mit **symbolspezifischer, gemessener Slippage** aus WP-7 - die Majors-Konstante 15 bps ist auf Rang-200-Perps **unbelegt** und vermutlich deutlich hoeher. *Bei DROP aller drei:* die Klasse W ist auf Bybit-Perps im Wochenhorizont erschoepft; das 2.0-Ergebnis (D.7) wird auf breiter Basis bestaetigt statt auf N=5. *Oekonomische Mindestmagnitude (Etikett):* `IC = 0,062`; Kosten je Woche: A3-M ~18 bps (Turnover 0,6), A3-R ~30 bps (Turnover ~1,0), A3-V ~4,5-7,5 bps (Turnover 0,15-0,25 - der friktionsfreundlichste Faktor, wegen der Signalpersistenz, nicht wegen des Horizonts).

**Etiketten.** `Klasse W`; `kapitalfrei`; `zweistufige FDR`; `A3-R: Bounce-Kontrolle urteilstragend`; `A3-V: schaetzfehler-dominiert, Nullterm > Erwartungseffekt`; `Alt-Symbol-Slippage UNGEMESSEN bis WP-7`.

**Feasibility-Kill-Bedingungen.** (1) `rho_quer > 0,03` -> Kohorte gestrichen. (2) `K < 110` -> Power-DROP nach GL-012, kein Datenlauf. (3) `sigma_xs < 500 bps/Woche` -> Bruttokante strukturell unter der Wand, Etikett "unter_wand" oder Streichung. (4) Survivorship nicht rekonstruierbar UND das Survivorship-Fixture zeigt eine Verzerrung in der Groessenordnung der erwarteten Kante -> nicht registrierbar. (5) A3-R: der Bounce-Abzug allein erklaert den IC. (6) A3-V: der Vol-Drag ueberschreitet die plausible Kante um mehr als Faktor 2 und laesst sich durch Vol-Gewichtung nicht unter ein Viertel der Kante druecken.

**DEC-39-Fixtures.** *Positiv:* Panel mit injiziertem Querschnitts-IC 0,06 inklusive gemeinsamem BTC-Beta-Faktor und Sektor-Bloecken. *Null:* Faktor innerhalb jeder Woche zufaellig permutiert; das Gate darf nicht feuern. *Adversarial (Pflicht fuer Klasse W):* ein Faktor, der **mechanisch mit dem Markt-Beta korreliert** (Vol- oder Groessen-Proxy), auf einem Panel mit dominantem Marktfaktor - in Krypto ist praktisch alles Beta zu BTC, und ein "Querschnitts"-Befund, der in Wahrheit Markt-Timing ist, ist DIE Fehlerklasse dieser Familie. Faellt das Gate hier nicht durch, ist die Neutralisierung defekt. *Zusaetzlich, A3-R-spezifisch und laut R2 der wichtigste Fixture des ganzen Berichts:* Panel ohne Reversion, aber **mit** realistischem Bid-Ask-Bounce - das Gate darf nicht feuern. *Zusaetzlich, A3-V-spezifisch:* Panel mit identischer Vol-Dispersion, aber ohne jeden Zusammenhang - prueft den Drag-Artefakt direkt.

**Nicht-Wiederholungs-Nachweis (C.1, muss woertlich in der Registrierung stehen).** A3 wiederholt **nicht** D.7 (C-06/H-07/H-08): H-07 starb an `max|z| = sqrt(N-1) = 2,0 < 2,5` bei N=5; bei K=150 ist `max|z| = 12,2`, die strukturelle Sperre ist aufgehoben. H-08 starb empirisch auf **demselben** 5-Symbol-Panel; das nachweislich neue Signal ist dreifach: (i) Breite K>=110 statt N=5 (Rauschboden `SE(IC)` 0,50 bei N=5 gegen ~0,19 hier - Faktor ~2,6 bei gemessenem `rho_quer`, gegen Faktor 44 in R2s `rho_quer=0`-Rechnung), (ii) Horizont Woche statt Stunden, (iii) explizite Bounce-Kontrolle (A3-R) bzw. Drag-Kontrolle (A3-V), die in H-08 nicht existierten. Ohne diese drei Punkte waere A3 eine unzulaessige Wiederholung.

**FDR.** `F-XSEC1` = {A3-M (3 Formationslaengen), A3-R, A3-V (3 Varianten)} = 7 Tests, BH bei alpha = 0,10. Ueber-Familie `F-WEEK`, darueber die Wellen-Ueber-Familie (DEC-22), in der abhaengigkeitsrobusten Form, falls WP-10(A) auf A-B3 faellt.

**Bedingung aus Welle 1.** WP-7 (vollstaendig: `rho_quer`, `K`, `sigma_xs`, `PERP_SPREAD_BP`, Survivorship-Fixture bestanden), WP-10 (FDR-Struktur), **DEC-51 und DEC-52 beschlossen** - DEC-52 zwingend VOR der Registrierung, weil A3 sie nachweislich braucht (Review 4.1 Auflage 1).

### 5.4 A4 - Perp gegen datierten Bybit-Future (aus R1-K-03), Klasse P

**Hypothese.** Der realisierte **Wedge** `w` = (implizierter Terminzins des datierten Futures beim Einstieg) minus (ueber die Laufzeit tatsaechlich akkumulierte Funding-Rate des Perps), annualisiert, ist ueber >= 8 vollstaendige Verfallzyklen systematisch positiv.

**Ertragsquelle: Praemie/Struktur.** Ein datierter Future preist einen **festen** Terminzins bis zum Verfall; ein Perp preist denselben Zins **fortlaufend neu** ueber Funding. **Zahler:** Marktteilnehmer, die Laufzeitsicherheit kaufen (Hedger, strukturierte Produkte). Es ist **keine** Konvergenz-Wette auf den Spot - die Konvergenz ist am Verfall mechanisch garantiert.

**Warum er trotzdem nur Rang 4 ist.** Die Headline "billigster Fall des Auftrags" (3 Fills statt 4, Taker 16,5 bp / Maker 6 bp) steht auf **zwei unbelegten, je einzeln toedlichen Annahmen**: (i) das Future-Bein settle gebuehrenfrei gegen den Index - genau die Kostenklasse, die E.6(a) fuer Optionen als blockierend fuehrt und die R4 mit `RAISE` belegt (Review 3.4); (ii) die datierten Kontrakte seien liquide. Beide sind in einem Call bzw. einem Primaerquellen-Blick klaerbar: **V-2 und V-4.**

**Daten.** Instrumente belegt vorhanden: `contractType` `LinearFutures` (USDC-Futures, `BTC-24MAR23`) und `InverseFutures` (Quartale `BTCUSDH/M/U/Z<yy>`, live `BTCUSD_Q`, `BTCUSD_BIQ`) [R1 0.5, Doku-Repo als Primaerquelle fuer die Schnittstelle]. **Der schwierige Punkt:** Klines bereits **verfallener** Symbole sind ueber `/v5/market/kline` vermutlich nicht mehr abfragbar (`instruments-info` filtert auf `status=Trading`) - **UNBELEGT, Teil von V-2.** Belegbar rekonstruierbar ist `/v5/market/delivery-price` (historische Settlement-Preise, 200/Seite, Cursor) als Ankerpunkt-Serie, plus der `bybit/tickers`-Strom fuer die aktuell gelisteten datierten Kontrakte. **Vorab fixierte Konsequenz:** sind die historischen Klines nicht abrufbar, ist ein rueckblickendes Gate unmoeglich und A4 wird ein **RECORDING-FIRST-Kandidat** wie H-21/H-26 (15-min-Sampler ueber `mark(Future)/mark(Perp)/index` je Verfall, ~10 MB/Monat, Gate-Lauf in 12+ Monaten). Das ist kein Ausweichen, sondern der vorab benannte zweite Pfad.

**Fenster.** >= 8 vollstaendige Verfallzyklen (Quartale = 2 Jahre, Monatsverfaelle = 8 Monate) ueber zwei disjunkte Haelften; REZENZ: die juengste Haelfte endet am Laufdatum. **Stress-Pflicht (DEC-53):** >= 1 Zyklus mit dokumentierter Stress-Episode.

**Metrik.** `w` je Zyklus, annualisiert, nach einem **vor dem Lauf gepinnten** 6-bp-Maker- Kostenmodell (`constants_hash`).

**Struktureller Nulleffekt.** Zwei Komponenten. (a) `w_null = 0` gilt **nur** in einem arbitragefreien Markt mit reibungsfreiem Kapital. Real ist `w_null` die **Margin-Bindungsdifferenz** zwischen beiden Beinen mal dem Opportunitaetszins - vorab aus den `instruments-info`-Margin-Parametern auszurechnen; die Bybit-Margin-Regeln sind fuer dieses Programm **UNGEMESSEN** (eigener WP). (b) Der Wedge ist per Konstruktion **ex post** gemessen; ein positiver Mittelwert kann reine **Jensen-Kruemmung** sein (der Terminzins ist ein Erwartungswert unter dem Terminmass). Der Test laeuft deshalb gegen die **ex-ante-implizierte** Kurve, nie gegen den Nachhinein-Mittelwert.

**Power-Zeile (DEC-51).** Cluster-Einheit ist der **Verfallzyklus**; `N_cluster = 8` bei Quartalen ueber 2 Jahre. Bei 8 Clustern ist `detektierbar = 2,4865 * sigma_w / sqrt(8) = 0,879 * sigma_w`. `sigma_w` (Streuung des realisierten Wedge ueber Zyklen) ist **UNGEMESSEN**; die Power-Zeile ist damit **erst nach V-2 und einer ersten deskriptiven Messung** ausfuellbar. **Bis dahin ist A4 nicht registrierbar** (C.12).

**Selektions-K.** `K = 2` (Quartals- und Monatsleiter, falls beide existieren).

**Schwelle - neu hergeleitet, weil R1s Zahl per Federstrich gesetzt ist.** R1 setzt `w >= 2,0 % p.a.` mit der Begruendung "ich setze bewusst hoeher" statt der eigenen Herleitung 0,5 % - das ist eine **architect-gesetzte Gate-Schwelle** und verstoesst gegen C.19 (Review 1-R1-K-03). Korrekte Herleitung **aus der Kapitalbindung**:

```
Zyklus-Kosten Maker      = 6 bp je 90-Tage-Zyklus = 0,243 % p.a.
Faktor 2 (R4 1.1c)       = 0,487 % p.a.
Kapitalkosten            = m * r_opp   (m = Kapital-Multiplikator beider Margin-Beine)
Schwelle w_min           = 0,49 % p.a.  +  m * r_opp
```

`m` ist **UNGEMESSEN** (Bybit-Margin-Regeln, eigener WP); `r_opp` ist **UNBELEGT** und haengt an der Nutzer-Entscheidung Par. 8.2 (Kapitalbasis und Alternativverwendung). Die Schwelle wird als **Formel mit Herleitungs-Referenz** registriert, nicht als Skalar (DEC-54b), und ist erst mit beiden Eingangswerten numerisch bestimmt.

**Gate-Text (woertlich).**

> **A4 gilt als kapitalfrei BESTANDEN, wenn:** (1) `w >= w_min` (Formel oben, mit gemessenem `m` und benanntem `r_opp`) in **beiden** disjunkten Haelften; (2) `N_cluster >= 8` vollstaendige Verfallzyklen, mit Vorzeichenkonsistenz in >= 6 von 8; (3) der Test laeuft gegen die **ex-ante-implizierte** Terminkurve, nicht gegen den Nachhinein-Mittelwert; (4) `w_null` (Margin-Bindungsdifferenz mal Opportunitaetszins) ist vorab ausgerechnet und abgezogen; (5) mindestens ein Zyklus enthaelt eine Stress-Episode nach DEC-53, sonst **KEIN VERDIKT**; (6) das Gate faellt auf dem Peso-Fixture durch. **Solange V-4 die Settlement-Gebuehr des datierten Futures nicht an der Primaerquelle geklaert hat, RAISED der Settlement-Pfad (Loud-Fail, C.14) und A4 ist nicht laufbar.**

**Entscheidungsrelevanz.** *Bei PASS:* A4 ist die **Entsperr-Bedingung von C-23** (PRD-PARK-Register: "Standalone-Verdrahtung + Nachweis Konvergenz > Friktion"); der alte Park-Grund ("2-Bein ~22 bps gegen < 0,08 % Konvergenz") war eine Rechnung auf **kurzem** Horizont - auf 90 Tagen kehrt sich die Arithmetik um (74 bp brutto gegen 6-16,5 bp Friktion, R1 0.3). *Bei DROP:* der Perp-vs-Future-Wedge ist erledigt; die Klasse P reduziert sich auf A1 und den gesperrten Options-Block. *Oekonomische Mindestmagnitude:* `0,49 % p.a. + m*r_opp`.

**Etiketten.** `Klasse P`; `kapitalfrei`; `moeglicherweise RECORDING-FIRST (V-2)`; `Settlement-Gebuehr UNBELEGT bis V-4 -> RAISE`; `Margin-Multiplikator m UNGEMESSEN`; `Kapitalbindung ueber 90 Tage ist die eigentliche Kostenstelle`.

**Feasibility-Kill-Bedingungen.** (1) V-2: `turnover24h` des vordersten datierten Kontrakts < ~1 % des Perp-Umsatzes -> der Quote-Spread ist der bindende Kostenblock, tot. (2) V-2: keine durchgehende Quartalsleiter -> `N_zyklen >= 8` unerreichbar, tot. (3) V-2: historische Klines verfallener Symbole nicht abrufbar -> kein rueckblickendes Gate, Vertagung auf 12+ Monate Recording. (4) V-4: Settlement nicht gebuehrenfrei -> das Alleinstellungsmerkmal "3 Fills statt 4" faellt weg, die Schwelle steigt entsprechend und ist neu herzuleiten. (5) `w_null` in der Groessenordnung von `w_min` -> nicht trennbar.

**DEC-39-Fixtures.** *Positiv:* synthetische Terminkurve mit konstantem +3-%-p.a.-Aufschlag ueber den simulierten realisierten Funding-Pfad. *Null:* Terminkurve, die **exakt** dem Erwartungswert des Funding-Pfads entspricht, mit zufaelliger Realisation - das Gate muss `w ~ 0` finden und darf die Realisationsstreuung **nicht** als Praemie lesen. *Adversarial (Peso):* wie A1, plus ein Szenario, in dem alle 8 Zyklen zufaellig in eine Contango-Phase fallen.

**FDR.** `F-PREM1` gemeinsam mit A1; Ueber-Familie `F-PREM`.

**Bedingung aus Welle 1.** **V-2 und V-4 beide positiv**, DEC-51 beschlossen, plus die noch fehlende Margin-Regel-Verifikation (eigener WP, nicht Teil von Welle 1).

### 5.5 A5 - Skew-Praemie (25d-Risk-Reversal) und der Options-Block (aus R1-K-04), Klasse P, GESPERRT

**Status: GESPERRT.** Die Reihenfolge aus Kompendium E.6 ist bindend und wird hier **nicht** aufgeweicht: (a) Delivery-/Exercise-Gebuehr an der Primaerquelle verifiziert (**V-4**), UND (b) ein Options-Spread-Zensus mit durchgaengiger Bybit-Aufzeichnung liegt vor, UND (c) **H-26 selbst ist gemessen**. Erst dann ist A5 registrierbar. Wer die Reihenfolge umdreht, setzt die Schwelle nach dem Sehen der Zahl.

**Hypothese.** Wer den 25-Delta-Put verkauft und den 25-Delta-Call kauft (delta-gehedgt auf dem USDT-Perp, 7-21 DTE, Halten bis Verfall), wird fuer das Tragen der Crash-Asymmetrie bezahlt, gegen die alle anderen sich versichern.

**Ertragsquelle: Praemie.** Krypto-Halter kaufen systematisch Abwaertsschutz; Krypto-Optimisten kaufen Aufwaerts-Hebel billiger anderswo (auf Perps). **Zahler:** der Hedger. **Klar abgegrenzt von H-26/C-33:** die VRP ist das **Niveau** (IV vs. RV), die Skew-Praemie ist die **Schiefe** (IV_put vs. IV_call bei gleichem |Delta|). Ein Risk Reversal ist bei symmetrischen Deltas naeherungsweise **vega-neutral** - er handelt genau das, was die VRP-Messung herauskuerzt.

**Daten.** Bybit-Optionen BTC/ETH im gemessenen Bein-Band (7-14 DTE, |Delta| 0,15-0,30). Bestand: `deribit/tickers` ~38 Tage, `deribit/markprice.options` 43 Tage, Bybit-Options- Ticker im `tickers`-Strom (Kompendium F.1). **Das reicht fuer kein urteilstragendes Fenster.** Ein durchgaengiger Bybit-Quote-Datensatz existiert noch nicht (E.9).

**Schwelle - der eine Punkt, der jetzt schon feststeht.** R1 kalibriert `1,5 Vol-Punkte` gegen die **C-33-Schwelle** von 3 Vol-Punkten - aber C-33 wurde fuer das Vol-**NIVEAU** einer Einzeloption definiert; ein importierter Massstab fuer eine andere Groesse ist die D.2-Fehlerklasse (Review 1-R1-K-04). **Verbindlich: die Schwelle wird aus der GEMESSENEN Skew-Verteilung hergeleitet**, mit einem GL-012-Vorabcheck (Median-25d-Skew auf den verfuegbaren Tagen), nie aus C-33.

**Kostenrahmen, der bereits gemessen ist** (Kompendium B.4-B.8, DEC-44/45): Options-Maker 2 bp / Taker 3 bp **des Index** je Fill; `vega/S` = 5,28 (BTC) / 5,10 (ETH) bp Index je Vol-Punkt; volle Quote-Breite im Bein-Band 0,14 (BTC) / 0,26 (ETH) Vol-Punkte. Daraus (R1 0.1, abgeleitet): 1 Maker-Fill = 0,379 (BTC) / 0,392 (ETH) Vol-Punkte, 1 Taker-Fill 0,568 / 0,588, 1 Delivery (nur ITM) 0,284 / 0,294. **Delta-Hedge-Kasse (R1 0.4):** ein Risk Reversal hat weitgehend aufhebende Gammas, Rest ~0,2 Vol-Punkte plus statischer Hedge 1,04 (Taker) bzw. 0,38 (Maker) ueber 14 Tage. **Maker-Rehedging auf dem Perp ist damit Existenzbedingung, keine Optimierung** - und genau das misst WP-10(B).

**Pflicht-Eingang aus A2 (Review 3.5, bisher von keinem Bericht gesehen).** A5 haelt bis zum Verfall und wird am **30-Minuten-Settlement-TWAP** abgerechnet - exakt in dem Fenster, in dem A2 eine hedge-getriebene Preisverzerrung von 10-40 bps vermutet. Wenn A2 recht hat, settlen A5s Positionen **systematisch in die Verzerrung hinein**. **Verbindlich: das A2-Ergebnis ist Pflicht-Eingang in jede Halte-bis-Verfall-Kostenrechnung von A5.**

**Feasibility-Kill-Bedingungen.** (1) V-4 klaert die Delivery-Gebuehr nicht -> der Halte-bis-Verfall-Pfad RAISED, A5 bleibt gesperrt. (2) Der GL-012-Vorabcheck zeigt einen Median-25d-Skew unter dem hergeleiteten Rauschboden -> struktureller DROP ohne Datenlauf. (3) H-26 liefert kein Verdikt -> Reihenfolge nicht erfuellt, A5 bleibt gesperrt.

**Entscheidungsrelevanz.** *Bei PASS (fruehestens 2027):* der erste Options-Praemien-Pfad des Programms mit tragbarer Hedge-Kasse. *Bei DROP:* der Options-Block ist erledigt; in Verbindung mit den bereits toten R1-K-05/K-06 (Par. 9.1) waere die verallgemeinerbare Programm-Lehre bestaetigt, dass **jede Bybit-Options-Struktur, deren Nutzen eine Greek-DIFFERENZ ist, gebuehren-strukturell benachteiligt ist.**

**Etiketten.** `Klasse P`; `GESPERRT (E.6-Reihenfolge)`; `Schwelle aus gemessener Skew-Verteilung, nicht aus C-33`; `Delivery-Gebuehr UNBELEGT -> RAISE`; `A2-Ergebnis ist Pflicht-Eingang`.

**FDR.** `F-PREM2` (Options-Praemien), Ueber-Familie `F-PREM`.

**Bedingung aus Welle 1.** V-4; im Uebrigen NICHT Welle 1, sondern die E.6-Reihenfolge (H-26 zuerst).

---

## 6. Tradability 3.0 - das Kostenmodell-Modul

**Grundsatz.** Das Kostenmodell ist ein **Mess-Artefakt, kein Parametersatz**. Jede Konstante ist entweder (a) gemessen und eingefroren, (b) ungemessen und dann als **zweiseitige Pflicht-Sensitivitaet** ausgewiesen, oder (c) ungemessen und dann ein **harter Abbruch** (Loud-Fail, C.14). **Stille Defaults sind verboten** - sie waeren die Torpfosten-Verschiebung, die DEC-13/16 verhindern soll.

**Umfangs-Entscheidung (Entwurf 3.0 / Review 5.2 Nachruecker).** R4 schlaegt ein `tradability3/`-Modul mit sieben Dateien vor - **bevor** ein einziger 3.0-Kandidat ein Verdikt hat, und mit **vier von sieben Modulen auf UNGEMESSENEN Konstanten** (Impact-`k`, Margin-Regeln, Delivery-Gebuehr, Alt-Spreads). Das ist die Methodik-Variante derselben S4/S5-Falle (D.16). **Gebaut werden jetzt nur die beiden Dateien, die pinnen, was gemessen IST; alles andere ist ein Stub mit `raise NotImplementedError`** - was zugleich der Loud-Fail-Doktrin entspricht.

`src/bybit_edge/research/tradability3/`

| Datei | Status | Inhalt bzw. Abbruchgrund |
|---|---|---|
| `constants.py` | **BAUEN** | Alle gemessenen Programm-Konstanten mit Quellen-Tag und Unit-Test-Pin: `FEE_MAKER = 2,0 bp`, `FEE_TAKER = 5,5 bp` je Bein (DEC-42/WP-4); `FEE_OPTION_MAKER_OF_INDEX = 2 bp`, `FEE_OPTION_TAKER_OF_INDEX = 3 bp` (DEC-45); `VEGA_OVER_S = {BTC: 5,28, ETH: 5,10}` bp Index je Vol-Punkt (WP-5/DEC-44); `PERP_TOB_SPREAD_BP = {BTC: 0,0157, ETH: 0,0537}` (WP-4/DEC-42); `OPT_QUOTE_WIDTH_VOLPTS` je (DTE-Bucket, |Delta|-Bucket) aus WP-5; `STRESS_EPISODE_STATS` aus WP-6; **`STRESS_DAYS` nach DEC-53**. Plus `assert_constants_unmodified()` und `constants_hash()` (SHA-256 ueber die Datei). |
| `report.py` | **BAUEN** | `CostReport`-Dataclass, die JEDES Tradability-Gate emittiert: `fee_bp, spread_bp, impact_bp_k0, impact_bp_k1, funding_bp, delivery_bp, total_bp_k0, total_bp_k1, capital_multiplier, regime, constants_hash`. Damit vergleicht ein Gate-Auditor Gleiches mit Gleichem. |
| `perp.py` | **RAISE-STUB** | Braucht `PERP_SPREAD_BP` je Symbol-Dezil fuer das breite Universum - **UNGEMESSEN bis WP-7 (Befund B6)**. Alle gemessenen Kostenkonstanten stammen von BTC/ETH-Majors; ohne den Zensus ist jede Broad-Universe-Tradability-Aussage wertlos (R4 2.5). |
| `impact.py` | **RAISE-STUB** | Funktionalform Wurzelgesetz `k * sqrt(notional/ADV) * daily_vol_bp` ist belegt (Almgren et al. 2005 [sek]); **`k` fuer Bybit UNKALIBRIERT**. Wenn der Stub spaeter faellt, gilt: jedes Ergebnis wird bei `k=0` (optimistisch) UND `k=1` (realistisch) berichtet - **nie ein Einzelwert**. |
| `option.py` | **RAISE-STUB** | `delivery_fee_of_index` hat Default `None`; jeder Halte-bis-Verfall-Pfad ohne gesetzten Wert **RAISED**. Die Delivery-/Exercise-Gebuehr ist die einzige bindende, noch ungemessene Options-Kostenkomponente (E.6a) und trifft ausgerechnet das beste DEC-45-Szenario. **Vorfrage V-4.** |
| `funding.py` | **RAISE-STUB** | Braucht das Funding-Panel mit `funding_n` aus WP-7 und die Intervall-Klaerung aus V-1; ohne beides addiert es Aepfel und Birnen. |
| `capital.py` | **RAISE-STUB** | **Bybit-Margin-Regeln sind fuer dieses Programm UNGEMESSEN.** Eine echte Kapital-Aussage braucht vorher einen eigenen WP (Regel-Verifikation). Bis dahin: Kapital-Multiplikator `m` mit konservativem Wert **nur** in einer zweiseitigen Sensitivitaet, nie als stiller Default. |
| `episode.py` | **RAISE-STUB** | Stress-Overlay setzt DEC-53 (gepinnte Stress-Tage) voraus. **Zwangsregel, die beim Bau uebernommen wird:** eine Strategie, deren Einstieg AUF ein Schock-Signal hin erfolgt, wird per Konstruktion in Stress-Minuten bepreist - daran ist reaktives Long-Vol gestorben (WP-6/DEC-47/48). |

**Einheiten-Bruecke.** Perp-Kosten in bp des **Notionals**; Options-Kosten in bp des **Index** (nicht des Notionals - DEC-45) und ueber `VEGA_OVER_S` in **Vol-Punkten**. Beide Einheiten werden gefuehrt, ihre Umrechnung per Unit-Test gepinnt (`5,28`/`5,10` sind skalen-invariant trotz 31-fach unterschiedlichem Basiswert-Niveau - bereits getestet, WP-5).

**Anti-Gaming-Bindung (macht C.3 maschinell pruefbar).** `constants_hash` im `CostReport` ist der SHA-256 ueber `constants.py`. **Ein Tradability-Lauf, dessen Hash nicht dem in der Registrierung zitierten entspricht, ist kein gueltiger Lauf.**

**Konstanten-Ersetzung ist eine DEC.** Ersetzt eine Messung (WP-7 `PERP_SPREAD_BP`, ein spaeterer Slippage-Zensus, V-4) eine Konstante, wird das als eigene DEC registriert - **bevor** ein Kandidat davon profitiert (Review 3.6). Die bestehenden Verdikte H-04b und H-05c bleiben davon unberuehrt (Anti-Torpfosten-Klausel).

---

## 7. Daten- und Rechenplan

### 7.1 Einmal-Backfill im Scinance-Repo (nicht im Harvester)

Kriterium: alles, was **beliebig nachladbar** ist, gehoert in einen einmaligen Backfill und **nicht** in einen Dauerstrom. **Backfills schreiben NIE in den Harvest-Baum** (Schutzgut, read-only, per CLI-Guard erzwungen); sie gehen in einen eigenen Speicher unter derselben Disziplin wie der WP-0-Bar-Cache.

| Backfill | Endpunkt | Requests | Zeit @5 Req/s | Volumen | Zweck |
|---|---|---|---|---|---|
| **1d-Klines, gesamtes Universum** | `/v5/market/kline?interval=D` | ~3.000 | **10 min** | 1,7 Mio Zeilen, 40-80 MB | WP-7, Basis der Klasse W |
| **Funding-Historie, gesamtes Universum** | `/v5/market/funding/history` | ~25.500 | **1,4 h** | 5 Mio Zeilen, ~60 MB | A1; Tiefe UNBELEGT - V-1 |
| **Deribit DVOL 1d, BTC+ETH** | `/public/get_volatility_index_data` | < 20 | Sekunden | ~4.000 Zeilen, < 1 MB | WP-9 |
| 1h-Klines, gesamtes Universum | `/v5/market/kline?interval=60` | ~40.500 | 2,3 h | 40 Mio Zeilen, 0,6-1,2 GB | **NICHT in Welle 1** - erst nach bestandener Feasibility (Review 5.2 Punkt 2) |
| 1m-Klines, gesamtes Universum | - | ~4,7 Mio | **260 h** | ~100 GB | **NIE**: der Horizont liegt nach K-0.1 ohnehin unter der Wand (R4 3.2, D.16) |

Die Selbst-Drossel von 5 Req/s ist **0,4 %** des belegten Bybit-Limits (600 Requests je 5 s je IP [sek]) - extrem sicher, und der gesamte Welle-1-Backfill bleibt unter **~2 Stunden und ~150 MB**.

**Provenienz-Regel fuer REST-Backfills (Review 6.9, gilt fuer JEDEN neuen Speicher, nicht nur WP-7).** Der Harvest-Baum ist lokal und unveraenderlich; ein REST-Backfill nicht - Boersen revidieren historische Klines gelegentlich. Deshalb: ein geplanter Job zieht **monatlich eine 1-%-Zufallsstichprobe** eingefrorener Partitionen neu und vergleicht die Fingerprints. **Abweichung ist ein lautes Alarm-Ereignis, kein stilles Ueberschreiben.** Das gilt ausdruecklich auch fuer den Funding-Backfill, an dem A1 und A4 haengen.

### 7.2 Was in den Harvester gehoert - nur Irreversibles

Kriterium: **Irreversibilitaet** (Anti-Data-Lake, PRD 2.0 Par. 9). Nur was sich spaeter nicht nachladen laesst, rechtfertigt einen Dauerstrom.

1. **Taegliches Point-in-Time-Instrument-Roster** (`instruments-info` je Kategorie, 1-3 Requests/Tag, wenige hundert kB). **Hoechste Prioritaet.** Es ist die einzige Verteidigung gegen Survivorship und kann grundsaetzlich **nicht** nachgeholt werden; jeder Tag ohne Lauf ist unwiederbringlich verloren.
2. **Universums-Ticker-Panel** (`tickers` je Kategorie, 15-min-Takt) - Spread, OI, Funding-Rate, Turnover fuer alle Symbole. **Zuerst die Inhaltsprobe auf den bereits existierenden `bybit/tickers`-Strom** (C.8, WP-7); ist er ausreichend, wird nichts Neues gesammelt. Volumen bei getrimmten Spalten: ~2,5-5 GB/Jahr.
3. **Open Interest** nur, falls die Tiefen-Probe eine flache Historie zeigt - dann irreversibel. Die OI-Tiefe ist **UNBELEGT** und der kritischste offene Datenpunkt (R4 3.1).
4. **Beizubehalten:** Deribit `dvol`, `markprice.options`, `tickers`; Bybit-Options-Ticker.
5. **NICHT in den Harvester:** Klines und Funding-Historie jeder Aufloesung - beliebig nachladbar, also ein Dauerstrom ohne Gegenwert.

### 7.3 Rechenbudget - CPU-first

Die gesamte 3.0-Methodik der Klassen P, W und E ist **CPU-Arbeit in Minuten**. Der 82-GB-RAM-Rechner ist hier grosszuegig dimensioniert, nicht knapp (R4 4.1).

| Aufgabe | Groesse | Laufzeit |
|---|---|---|
| Faktorberechnung auf dem Daily-Panel | 1.500 Sym x 2.190 Tage = 3,3 Mio Zeilen | Sekunden (numpy/polars) |
| Querschnitts-IC + 1.000 Permutations-Nullen | 250 Wochen x 1.500 Sym x 1.000 | < 1 min |
| Stationaerer Block-Bootstrap, 10.000 Replikate, 200 Varianten | | Minuten |
| Placebo-Verteilung Ereignis-Studie, 1.000 Laeufe | | Minuten |
| L2-Replay je Fenster (WP-10 Teil B) | | ~86 min (WP-4-Erfahrungswert) |
| Voller Welle-1-Backfill | | ~2 h, netz- nicht CPU-gebunden |

**GPU: 0** (Par. 3.7). Keine der Metriken (IC, Praemie, CAR, Bootstrap, Permutation, FDR) ist GPU-gebunden. **Nicht machbar auf diesem PC und deshalb gar nicht erst geplant:** L2-Buchrekonstruktion oder Tick-Analysen ueber ein breites Universum (die Daten existieren nicht - L2 nur BTC/ETH, `publicTrade` nur 5 Symbole), Minutenbars fuer das gesamte Universum, ein zweiter gleichzeitiger Grosslauf (ein Betreiber, eine Maschine - Laeufe sind seriell, und die knappe Ressource ist **Kalenderzeit**, nicht FLOPS).

---

## 8. Offene Nutzer-Entscheidungen

> Diese drei Punkte kann nur der Nutzer entscheiden. **Das PRD ist unter dem Orchestrator-Default (b) bei Punkt 8.1 vollstaendig** - es aendert heute keinen Code und keine Regel. Die Punkte 8.2 und 8.3 blockieren keinen Welle-1-Schritt.

### 8.1 Ausfuehrungsfrage - der Verfassungswiderspruch (Review 6.4)

**Der Widerspruch, ausbuchstabiert.** Der beste Kandidat (A1) ist ein woechentlicher Dezil-Long-Short ueber 100-300 Perps: ~60 Positionen, **~30-60 Orders je Woche**. Fuer einen Einzelbetreiber manuell unrealistisch - und **"kein Live-Order-Code" ist Verfassung**. Damit ist die billigste zu MESSENDE Klasse die teuerste zu BETREIBENDE, und das Programm hat sich ihre Ausfuehrung selbst verboten.

| Option | Inhalt | Preis |
|---|---|---|
| (a) | Verfassung bleibt, 3.0 bleibt reines Messprogramm; A1 wird gemessen, aber nie betrieben | Ehrlich, aber der Pfad vom WEITER zum ersten Euro bleibt undefiniert (Review 6.8) |
| **(b) - DEFAULT** | Eine spaetere, **getrennt gegatete Ausfuehrungs-Spur** wird im PRD als Phase vorgesehen, die erst nach Mess-PASS **und** Tradability-PASS **und** expliziter Nutzer-Freigabe gebaut wird | Aendert heute keinen Code und keine Regel; haelt die Option offen, ohne sie einzuloesen |
| (c) | Kandidaten werden auf "manuell betreibbar" (wenige Positionen) eingeschraenkt | Streicht die Klasse W praktisch - und damit A1 und A3 |

**Umsetzung unter Default (b), verbindlich:** Die Ausfuehrungs-Spur wird als **Phase 4** benannt und bleibt bis zur ausdruecklichen Freigabe leer. Kein Welle-1-Paket, kein Kandidaten-Entwurf und keine Verfassungsregel dieses PRD haengt an ihr. Die Entscheidungsrelevanz-Zeilen in Par. 5 nennen deshalb ausnahmslos nur den naechsten **Mess-** oder **Tradability-**Schritt, nie einen Kapitalschritt.

### 8.2 Kapitalbasis und Steuerregime (Pflichtzeile 3.3.9)

Benoetigt werden: (i) die **Groessenordnung des einsetzbaren Kapitals** (bestimmt, ob eine Praemie von 5-10 % p.a. auf gebundenes Kapital ueberhaupt den Betreiberaufwand traegt); (ii) die **steuerliche Behandlung** von Funding-Ertraegen und Options-Praemien in der Jurisdiktion des Nutzers; (iii) der **Opportunitaetszins `r_opp`** auf gebundenes Kapital (geht direkt in A4s Schwelle ein, Par. 5.4).

**Warum das nicht kosmetisch ist (Review 6.2):** Spot- und Derivate-Bein einer delta-neutralen Position werden steuerlich unterschiedlich behandelt; eine steuerlich asymmetrische Konstruktion kann bei einer Bruttokante von 5-10 % p.a. den Grossteil des Ertrags kosten. **Wirkung auf dieses PRD:** keine Blockade. Bis zur Antwort tragen alle Praemien-Entwuerfe die Zeile **"Steuerregime UNBELEGT - Par. 8.2"**, und **keine** "netto"-Aussage wird ohne diesen Vorbehalt gefuehrt. A4s Schwelle bleibt als Formel registriert, nicht als Zahl.

### 8.3 Sunset-Review der Recording-Engine F0

Faellig seit ~2026-09-11 laut PRD 2.0 Par. 9, **nie gelaufen**. Die Engine schreibt Stroeme, die kein Treiber liest (DEC-43), und mindestens ein Ziel ist anderweitig abgedeckt (DEC-46). **Empfehlung des Orchestrators:** Review planmaessig durchfuehren; danach **nur behalten, was eine registrierte 3.0-Hypothese namentlich braucht**. Nicht pauschal abschalten - die Anti-Data-Lake-Regel steht im PRD, sie wurde nur nie vollzogen. **Wirkung auf dieses PRD:** keine Blockade. Zu beachten ist nur die Wechselwirkung mit Par. 7.2: das Point-in-Time-Roster ist **irreversibel** und muss laufen, unabhaengig vom Ausgang der Review.

---

## 9. Anhang

### 9.1 Kandidaten, die NICHT aufgenommen wurden

| Kandidat | Grund (ein Satz) | Referenz |
|---|---|---|
| **R1-K-01** Funding-Carry Spot/Perp | Stirbt am eigenen Nulleffekt: mit `r_excess = r_USD - Kostendrift` und konservativem `r_USD = 0` sind das **-3,77 % p.a.**, die Schwelle +4,0 % verlangte real >= 18,7 % p.a. Ist-Funding. | Review 2.1, 3.2 |
| **R1-K-02** Intra-Venue-Funding-Spread | Groessenordnung vollstaendig unbelegt - das ist kein Kandidat, sondern eine 10-Minuten-Vorfrage (in V-1 aufgegangen). | Review 1-R1-K-02 |
| **R1-K-05** Kalender-/Forward-Vol-Praemie | Gebuehren-strukturell tot: 2,51 Vol-Punkte Netto-Vega-Kosten gegen eine Forward-Vol-Praemie ohne jede Evidenz; erforderlich waeren >= 5,0 Vol-Punkte. | Review 1-R1-K-05 |
| **R1-K-06** ETH-vs-BTC-Relative-Vol | ~3,9 Vol-Punkte Maker-Kosten gegen einen Praemienanteil, den der Autor selbst auf < 2 Vol-Punkte schaetzt; der Dispersions-Mechanismus existiert in dieser Marktstruktur nicht. | Review 1-R1-K-06 |
| **R2-K-03** Time-Series-Momentum (Portfolio-Sharpe-Form) | Eigene Power-Rechnung: SR 2,80 je 12-Monats-Fenster noetig, bester unabhaengiger Literaturwert 1,6. Die Driscoll-Kraay-Panel-Form ist eine ANDERE Hypothese und braucht zuerst die Persistenz-Null. | Review 1-R2-K-03 |
| **R2-K-06** Kalender-Interaktion (Wochenende, Monatsende, letzter Freitag) | Nachweisgrenze unter REZENZ: 33 bps/Tag bei n~104 Wochenendtagen je Fenster - solche Effekte gibt es nicht; die Session-Achse ist inhaltlich **kein** Kalendereffekt (die einzige zitierte Evidenz ist ein FLUSS-Signal) und muesste umbenannt werden. | Review 1-R2-K-06 |
| **R2-K-07** Vol-Targeting | Nie eigenstaendiger Kandidat; nur als **vorab fixierte Variante** eines bestehenden Kandidaten zulaessig, mit gemessener (nicht angenommener) Geschenk-Verteilung. | Review 1-R2-K-07 |
| **R3-K-32** GEX-KOND | S4/S5-Falle: verlangt einen neuen Harvester-Strom plus Warten bis ~2027-05 - eine Datenpipeline fuer den Term zweiter Ordnung eines unvalidierten Terms erster Ordnung. **Kein Options-Tape-Auftrag vor einem A2-PASS.** | Review 5.2 Punkt 1 |
| **R3-K-33** X-PULL Stufe 2 | Der eigene A-priori (Median 1-3 bps) impliziert, dass der N-Floor reisst, und die auftretenden Ereignisse fallen per Konstruktion in Kaskadenminuten, in denen die 15-bps-Annahme nachweislich falsch ist. | Review 1-R3-K-33 |
| **R3-K-34** LEV-STATE | Einziger R3-Kandidat **ohne hergeleiteten Rauschboden**; zusaetzlich poolt er 5 Symbole zu "~180 Dezil-Tagen", obwohl der Hebelzustand an denselben Kalendertagen auftritt (effektiv ~40). | Review 1-R3-K-34, 2.5 |
| **R3-K-35** SLIP-ZENSUS | Nachrangig: nur ~2,5 Monate rezenz-konforme `orderbook.1000` und nur BTC/ETH - kann die Frage, die die Klasse W blockiert (Alt-Symbol-Slippage), **prinzipiell nicht** beantworten; WP-7 laeuft zuerst. | Review 1-R3-K-35, 3.6 |
| **R3-K-36** VRP-KOND (Terzil-Gate) | Faellt an der eigenen Power-Rechnung: `SE(Terzil-Differenz) ~ 4,1` Vol-Punkte gegen eine 3-Punkte-Schwelle = **0,73 SE**; beide angebotenen Auswege sind verboten (Ueberlappung kauft keine Power; 24-Monats-Fenster kollidieren mit REZENZ). Der **Datenfund** ist als WP-9 uebernommen. | Review 1-R3-K-36, 3.3 |
| **R3-K-37** SKEW-VORLAEUFER Stufe 2 | Rauschboden aus 60 **ueberlappenden** Tagesbeobachtungen hergeleitet; effektives N ~6, Rauschboden ~0,41 - die 0,25-Schwelle ist strukturell unerreichbar. (Stufe 1, die tagesgenaue Ketten-Luecken-Karte, bleibt ein sinnvoller spaeterer WP.) | Review 1-R3-K-37, 2.4 |
| **R4** oekonomische Mindestmagnitude in der PASS-Bedingung | Bricht C.2: unter dieser Regel waere H-04 ein DROP gewesen und die Information "gerichtete Information existiert" geloescht. Verschoben in Entscheidungsrelevanz + Tradability. | Review 4.5 |
| **R4** harte 24-h-GPU-Wall-Clock-Kappe | Selbst eine importierte Schwelle ohne Herleitung (warum 24 und nicht 12 oder 72?) und ausserdem redundant; ersetzt durch die Positivkontroll-Vorschaltung. | Review 4.4 |
| **R1** `SR_block >= 0,60` als Gate; `TR <= 250 Tage` als Gate | Ein Gate mit ~50 % Power je Fenster; die Tail-Ratio bestraft strukturell kleine Praemien und toetet jede echte Praemie. Beide degradiert zu Deskriptoren. | Review 3.7, 3.8 |
| **R4** `tradability3/` in voller Sieben-Datei-Form | Vier von sieben Modulen stehen auf ungemessenen Konstanten, vorgeschlagen bevor ein Kandidat ein Verdikt hat; nur `constants.py` und `report.py` werden gebaut. | Review 5.2 Nachruecker |
| **Migration der 2.0-Registry** | Sie ist append-only und urteilstragend; sie nachtraeglich anzufassen waere ein schwererer Fehler als jeder Komfortgewinn. | Review 4.3, R4 5.3/7 |

### 9.2 Programm-Konstanten-Tabelle

**A - Gemessene Programm-Konstanten aus 2.0** (Kompendium B; jede darf ohne Neuherleitung zitiert werden).

| # | Groesse | Wert | Quelle |
|---|---|---|---|
| B.1 | Round-Trip-Friktionswand | **11 bps** (Taker), **~15 bps** inkl. Slippage | verdict.md Par. 2, FINAL_PRD Par. 1 |
| B.2 | Perp-Top-of-Book-Spread | **exakt ein Tick**: BTC 0,0157 bp (RECENT) / 0,0196 (2024Q1), ETH 0,0537 bp; Dispersion p90-p10 nur 0,8-2,7 % des Medians | WP-4, DEC-42 |
| B.3 | Perp-Gebuehren | `FEE_MAKER` = **2,0 bp/Bein** (4,0 bp RT), `FEE_TAKER` = **5,5 bp/Bein** (11 bp RT) | DEC-42, WP-4 |
| B.4 | Options-Gebuehren (auf den **Index**) | Maker **2 bp**, Taker **3 bp**; kein Rabatt aktiv | DEC-45 |
| B.5 | `vega/S` | **5,28** bp Index je Vol-Punkt (BTC), **5,10** (ETH); skalen-invariant, per Unit-Test gepinnt | WP-5, DEC-44 |
| B.6 | Options-Quote-Breite (7-14 DTE, \|Delta\| 0,15-0,30) | voll **0,14** Vol-Punkte (BTC) / **0,26** (ETH); eng ueber neun Verfalltermine bis ~123 Tage | WP-5, DEC-44 |
| B.7 | Break-even-Gebuehr gegen die C-33-Schwelle (3 Vol-Punkte) | passiv + Halten bis Verfall frisst 25 %/26 %; Taker-RT frisst 85 %/96 % | DEC-45 |
| B.8 | Options-Quote-Breite im Stress (19.08.2026) | haelt in **97-99 %** der Minuten; Verbreiterung episodisch (BTC 0,66 % der Minuten, ETH 2,82 %); Renormalisierung binnen Minuten bis max. ~2 h | WP-6, DEC-47/48 |
| B.9 | Dressing-Artefakt (CRPSS gegen Dirac) | **0,21-0,29** theoretisch, 26,3-30,3 % empirisch | GL-022/GL-024 |
| B.10 | AnEn schlaegt gedresste HAR nicht | 0 von 4 Zellen, kein p unter 0,29 | GL-024 |
| B.11 | Querschnitts-z-Deckel | `max\|z\| = sqrt(N-1)`; bei N=5 also **2,0** | GL-012 |
| B.12 | Zeit-Irreversibilitaets-Signatur | AUC bis 0,7353, aber 85-106 % des Ueberschusses aus dem Aktivitaets-Envelope | GL-015-Nachtrag, DEC-30 |
| B.13 | Venue-Fingerprint / Redundanzschwelle | gepoolt 0,8944/0,8914; Redundanzschwelle **Spearman 0,6** | GL-019, GL-031 |
| B.14 | Minuten-Fluss-Impact | gleichzeitiger IC ~+0,53..+0,61, Forward-IC30 ~-0,011..-0,022, ueber zehn Halbjahre stabil | H-24 |
| B.15 | Numerischer Rauschboden des Lesepfads | **3,8e-9** relative Lauf-zu-Lauf-Streuung | DEC-32/34 |
| B.16 | Datenreichweite | `bybit/publicTrade` lueckenlos ab 2020-03-25 (BTC) / 2021-06-29 (SOL/BNB), 5 Symbole, 5-6 Jahre | DATA_INVENTORY 2026-08-10 |
| B.17 | Hardware | RTX 5060 Ti (16 GB), CUDA 12.8+, 82 GB RAM, Windows; **Sandbox ohne torch/GPU und mit Egress-Sperre** | INFRA_OPS_MAP, F.3 |

**B - Neue Programm-Konstanten aus R4 K-0.1 bis K-0.6** (alle hergeleitet, vom Review nachgerechnet und bestaetigt).

| # | Groesse | Wert | Herleitung |
|---|---|---|---|
| K-0.1 | Horizont-Friktions-Kurve | `edge_h = (2p-1)*0,798*sigma_h`; BTC `sigma_1d = 262 bp`. **Perfektes 1-s-Orakel: 0,71 bp.** Mindesthorizont gegen 11 bp bei p=0,55: **6,6 h**; gegen 4 bp (Maker): **53 min**; bei Wochen-IC 0,05: **2,7 Tage** (Taker) / **7 h** (Maker) | `E|r_h| = 0,798*sigma_h` bei Normalitaet |
| K-0.2 | Sharpe-Nachweisdauer (Lo 2002) | `T_min ~= 6,18/SR^2` Jahre; SR 1,0 -> 6,19 a, SR 0,5 -> **24,7 a**; mit g3=-2 und Exzess-Kurtosis 10 bei SR 1,0 Faktor 1,827 -> **11,3 a** | `SE(SR_ann) = sqrt((1+SR^2/(2q))/T)`, z = 2,4865 |
| K-0.3 | Selektions-Decke (Bailey/Lopez de Prado) | `E[max SR]` ueber K Varianten bei T=5 a: K=5 -> 0,53; K=20 -> 0,85; K=50 -> **1,02**; K=100 -> 1,13 | `sigma_SR*((1-g)*Phi^-1(1-1/K)+g*Phi^-1(1-1/(Ke)))`, g=0,5772 |
| K-0.4 | MaxDD-Boden | `E[MaxDD] = 1,2533*sigma_ann*sqrt(T)`; sigma 20 %, T=5 a -> **56 %** | Magdon-Ismail et al. 2004 [sek] |
| K-0.5 | IC-Rauschboden und Breiten-Decke | `N_eff = N_c/(1+(N_c-1)*rho_quer)`, `SD(IC_t)=1/sqrt(N_eff-1)`. N=5: detektierbar **0,098**; N=50/rho 0,05: 0,053; N=200/rho 0,10: 0,064. Decke: `N_eff -> 1/rho_quer` | T=104 Wochen, t=2 |
| K-0.6 | Kosten des harten Ein-Fenster-DROP | `P(beide bestehen) = (1-beta)^2`: Power 0,8 -> 0,64; **Power 0,5 -> 0,25**; Power 0,35 -> 0,12. Vorzeichen-Konsistenz bei t=1,4: 0,845 gegen 0,18 - **Faktor 4,7** | Binomialarithmetik, Phi(1,4)=0,919 |
| K-0.7 | GPU-Bilanz 2.0 | ~**350 GPU-Stunden** (309-357), Ertrag 2 kapitalfreie WEITER, **0 registrierte Tradability-Folgen** | INFRA_OPS_MAP 6, E.10 |

**C - In diesem PRD neu hergeleitete Groessen.**

| Groesse | Wert | Ort der Herleitung |
|---|---|---|
| DEC-51-Konstante | `z = z_0,95 + z_0,80 = 1,6449 + 0,8416 = **2,4865**` | Par. 3.3.1 |
| `rho_quer`-Schwelle | **0,03** (exakt 0,0313), als asymptotische NOTWENDIGE Bedingung | Par. 4.1 |
| Demeaning-Bias des `rho_quer`-Schaetzers | `-1/(K-1)`: -0,0092 (K=110), -0,0059 (K=170) | Par. 4.1 |
| A1-Feasibility an `sigma_LS` | `<= 104 bps/Woche` (per Fenster), `<= 148 bps/Woche` (gepoolt) | Par. 5.1 |
| A2-SE nach Cluster-Korrektur | `SE(Ereignismittel) = 4,73 bps`; `SE(Delta) = 5,11 bps`; 12 bps = **2,35 SE**; Per-Fenster-Power **0,76** | Par. 5.2 |
| A2 Monatsverfalls-Variante | `SE = 9,87 bps`, Power je Fenster 0,34, ueber zwei Fenster **0,11** -> nicht registrierbar | Par. 5.2 |
| WP-10(A) N-Floor | **`N_cluster >= 46`** Stress-Episoden; erwartet sind 6-10 je 24 Monate -> A-B3 ist der arithmetisch wahrscheinliche Ausgang | Par. 4.3 |
| WP-9-Materialitaets-Schranke | `<= 0,012 Vol-Punkte` auf >= 99 % der 112 Ueberlappungstage (3 Vol-Punkte / 250, DEC-32-Praezedenz) | Par. 4.2 |
| WP-10(B) `adv_sel`-Schwelle | **`<= 3,5 bp je Bein`** (`FEE_TAKER - FEE_MAKER`), statt R1s fehlhergeleiteter 1,5 bp | Par. 4.3 |
| A4-Schwelle | `w_min = 0,49 % p.a. + m*r_opp` (Formel, nicht Skalar), statt R1s gesetzter 2,0 % p.a. | Par. 5.4 |
| Selektions-Decken der Wellen-Familien | `F-CARRY1` (K=3): **0,60**; `F-XSEC1` (K=7): **0,98** (T=2 a) | Par. 5.1, 5.3 |

### 9.3 Beschluss- und Bau-Reihenfolge (Zusammenfassung, bindend)

1. **DEC-51** (Power-Konvention) beschliessen - blockiert jede Power-Zeile.
2. **DEC-53** (Stress-Tage-Kanon) erzeugen und als Fixture pinnen - blockiert jede Klasse-P-Registrierung und WP-10(A).
3. **Retro-Check auf H-06/H-20/H-22** durchfuehren und veroeffentlichen, danach **DEC-52** beschliessen - blockiert A1 und A3.
4. **V-1..V-4** auf der Nutzer-Maschine beantworten (Minuten) - kann A1, A4, A5 vorab toeten.
5. **WP-7** spezifizieren, bauen, laufen lassen - entscheidet ueber die gesamte Klasse W.
6. **WP-9** und **WP-10** (parallel moeglich, unabhaengig).
7. **DEC-54** (Registry-Format), **DEC-55** (`constants.py`/`report.py` mit `constants_hash`), **DEC-56** (GPU-Default 0) als Werkzeug-Entscheidungen.
8. **Erst danach:** Registrierung von A2 (frueheste Laufbereitschaft, kein Nachladen), dann A1, dann A3 (nur bei Befund B2), dann A4 (nur bei V-2/V-4 positiv). A5 bleibt hinter der E.6-Reihenfolge gesperrt.

*Ende PRD_SCINANCE3_DRAFT.md - prd-architect, 2026-09-02. Kein Abschnitt dieses Dokuments ist eine Registrierung; alle Kandidaten-Abschnitte sind Entwuerfe und ersetzen keine Vorregistrierung durch den Orchestrator.*
