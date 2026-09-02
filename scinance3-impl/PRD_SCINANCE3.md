> **ORCHESTRATOR-FASSUNG v2 - angenommen 2026-09-02.** Entwurf v1 (`prd/PRD_SCINANCE3_ENTWURF_v1.md`) wurde adversarisch geprueft (`prd/REVIEW_ENTWURF_v1.md`, 8 Blocker), nach den Orchestrator-Entscheidungen zu v2 ueberarbeitet und die Umsetzung aller Korrekturpunkte verifiziert (`prd/VERIFY_v2.md`). Bindend sind zusaetzlich `state/decisions.md` (DEC-51..57) und `CLAUDE.md`; bei Widerspruch gilt die DEC. Offene Nutzer-Entscheidungen: Abschnitt 8 (Default (b)).

# PRD SCINANCE 3.0 - ENTWURF v2

**Phase:** 4 - PRD-Ausarbeitung, zweite Fassung nach adversarischem Review
**Stand:** 2026-09-02
**Erstellt von:** prd-architect (Opus)
**Bindende Vorlage:** `scinance3-impl/PROGRAMMENTWURF_3.0.md` (Orchestrator-Entscheidung) plus die Orchestrator-Entscheidungen zur v2-Ueberarbeitung. Die dortigen Festlegungen sind gesetzt; dieses Dokument fuellt sie aus und aendert sie nicht.
**Massgebliche Quellen:** `state/decisions.md` (DEC-51..DEC-57, beschlossen), `state/RETROCHECK_DEC52.md`, `scratchpad/prd/REVIEW_PRD3.md` (Gate-Audit zu v1), `research/REVIEW_R1_R4.md`, `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F), `research/R1..R4`, `scinance2-impl/FINAL_PRD_SCINANCE2.md` (Struktur- und Praezisionsvorbild).

> **Belegregel.** Keine Zahl ohne Herleitung oder Quelle. Sekundaerbelege sind mit `[sek]` markiert und nennen ihre Quelle; ein `[sek]` ohne benennbare Quelle wird als **UNBELEGT** gefuehrt. Wo ein Wert fehlt, steht **UNBELEGT - Vorfrage V-x** bzw. **UNGEMESSEN - WP-x**. Gesetzte Zahlen, die weder hergeleitet noch gemessen sind, tragen ausdruecklich das Etikett **Design-Parameter (keine Schwelle)** mit vorab fixierter Konsequenz.
> **Statusregel.** Dieses PRD registriert NICHTS. Alle Kandidaten in Par. 5 sind Registrierungs-ENTWUERFE. Die Registrierung erfolgt ausschliesslich durch den Orchestrator, nach Welle 1.
> **Aenderungen gegenueber v1** sind in Par. 10 protokolliert, jede mit Review-Referenz.

---

## 1. Executive Summary

**Bilanz 2.0.** 31 Gate-Eintraege, 0 Torpfosten-Verschiebungen, **0 handelbare Kanten**. Das Kompendium zaehlt sieben kapitalfreie Mess-WEITER und nennt sechs namentlich (H-04, H-05b, H-11 [mit Etiketten], H-15, H-16 [korrigierte Lesart], H-23) - die Diskrepanz ist im Kompendium angelegt und wird hier unveraendert wiedergegeben, nicht stillschweigend geglaettet. Jedes dieser WEITER ist in der eigens dafuer registrierten Tradability-Pruefung PARK oder nie getestet (E.10). Rund 350 GPU-Stunden (R4 K-0.7: 309-357 h) haben null registrierte Tradability-Folge erzeugt. Der einzige noch aktive Strategie-Pfad ist die gesperrte VRP-Messung H-26.

**Die vier Zahlen, die 3.0 regieren** (Entwurf 3.0 Par. 1; Herleitungen in Par. 3.6 und 9.2):

| Groesse | Wert | Konsequenz |
|---|---|---|
| Horizont-Friktions-Kurve (R4 K-0.1) | Mindesthorizont bei p=0,55: **6,6 h** Taker / **53 min** Maker; bei Wochen-IC 0,05: **2,7 Tage** Taker | Kein 3.0-Kandidat unter Tageshorizont, ausser als reine Kosten- oder Zensus-Messung |
| Sharpe-Nachweisdauer (Lo 2002, R4 K-0.2) | `T_min ~= 6,18/SR^2` Jahre (Naeherung, s. 3.6); SR 0,5 -> **24,7 Jahre**, SR 1,0 -> 6,19 Jahre (mit realistischer Schiefe 11,3) | Sharpe ist NIE urteilstragend; urteilstragend ist die Praemie selbst |
| IC-Rauschboden (R4 K-0.5) | N=5: **0,098**; die Breite hilft nur bis zur Decke `N_eff` | Das breite Universum ist Existenzbedingung der Klasse W; **`SD_null(IC_t)` ist die bindende, UNGEMESSENE Zahl - WP-7 misst sie direkt** |
| Kosten des harten Ein-Fenster-DROP (R4 K-0.6) | Bei Per-Fenster-Power 0,5 ueberleben `0,5^2 = 0,25` der echten Effekte | DEC-52 ist **beschlossen** (Retro-Check liegt vor, Etikett "Verbesserung"); sie greift nur, wo die Power-Zeile VOR dem Lauf Power < 0,60 ausweist |

**Der Pivot.** 2.0 hat sechsmal dieselbe Friktions-Arithmetik auf Sekunden- und Minuten-Horizonten gemessen (H-03, H-04b, H-05c, H-09, H-24 - alle 80-500x unter der Wand, R4 6.1b). R4 K-0.1 zeigt, dass das arithmetisch vorgezeichnet war: ein PERFEKTES 1-Sekunden-Orakel verdient 0,71 bp gegen eine 11-bp-Wand. 3.0 sucht deshalb ausschliesslich dort, wo die Wand irrelevant wird: bei **Risikopraemien** (Cashflow statt Prognose, Klasse P) und auf **Tages- bis Wochen-Horizont mit breitem Universum** (Klasse W), plus einer kalendarisch exogenen **Ereignis-Klasse** (E). Welle 1 ist reiner Zensus (WP-7, WP-9, WP-10, V-1..V-5), verbraucht **null Alpha-Slots** und beantwortet die Feasibility-Frage **rein statistisch**: kann das Design den registrierten A-priori-Effekt ueberhaupt sehen? Die Friktionswand ist in 3.0 **Etikett in der Entscheidungsrelevanz-Zeile, nie PASS-Bedingung eines Mess-Gates** (C.2).

---

## 2. Lehren aus 2.0, die 3.0-Regeln erzeugen

| # | Lehre | Vorfall | 3.0-Regel |
|---|---|---|---|
| L-1 | Eine importierte Schwelle ohne Erreichbarkeitspruefung ist wertlos | C-14: rho-Median 2e-7 gegen importierte Schwelle 0,85, sechs Groessenordnungen (D.2) | Feasibility-Zeile (C.12) bleibt Pflicht; jede 3.0-Schwelle traegt eine Herleitungs-Referenz statt eines nackten Skalars (3.4). **Jede importierte Materialitaets- oder Toleranzschranke braucht ihre eigene Erreichbarkeitspruefung** (angewendet in WP-9, 4.2) |
| L-2 | Der strukturelle Nulleffekt ist vor der Schwelle auszurechnen UND zu messen | H-11/GL-022: Schwelle CRPSS>=0,05 lag Faktor 4-5 unter dem Dressing-Geschenk 0,21-0,29 (B.9) | C.4 bleibt; der Nulleffekt wird zusaetzlich am Null-Fixture GEMESSEN (R4 1.0) |
| L-2b | Ein Schaetzer, der die gesuchte Groesse gar nicht enthaelt, ist schlimmer als kein Schaetzer | v1 dieses PRD: der paarweise `rho_quer`-Schaetzer ist wegen `sum_i e_{i,t} = 0` bei gleichen Varianzen identisch `-1/(K-1)` und bei ungleichen ein Vol-Heterogenitaets-Artefakt (Review PRD3 1.1a) | **Jede Pflicht-Messgroesse wird vor dem Bau daraufhin geprueft, ob ihr Schaetzer unter der Null informativ ist** - Nachweis am Null-Fixture mit realistischer Heterogenitaet, nicht nur mit gleichen Varianzen |
| L-3 | Ein N=5-Panel traegt keine Querschnitts-Statistik | GL-012/H-07: `max\|z\| = sqrt(N-1) = 2,0 < 2,5` | Klasse W existiert nur auf einem breiten Panel; `SD_null(IC_t)` ist vor jeder Registrierung zu messen (WP-7, 4.1) |
| L-4 | Mess-Gate != Tradability-Gate; die Kostenwand gehoert NICHT in die PASS-Bedingung | H-04 (kapitalfrei WEITER) -> H-04b (PARK); R4s "oekonomische Mindestmagnitude" haette H-04 zum DROP gemacht (Review R1-R4 4.5) | C.2 unangetastet. **Keine PASS-Bedingung und kein Befundzweig eines Mess-Gates darf eine Handelskostenzahl als Ausloeser haben** (Review PRD3 2.1: drei v1-Verstoesse behoben) |
| L-5 | Ein Gate ohne Power-Rechnung kann nicht zwischen "kein Effekt" und "kein Nachweis" trennen | 26 Registrierungen ohne Power-Zeile; H-20 (p=0,17 bei erreichter Magnitude), H-22 (IC 0,0665 gegen 0,10) bleiben ungeklaert (R4 6.2d) | Power-Zeile als Pflichtzeile, Konvention DEC-51 (3.3.1). **Die Anwendungsbedingung einer Regel wird gerechnet, nicht behauptet** (Review PRD3 2.3) |
| L-6 | Korrelierte Beobachtungen sind keine unabhaengigen Beobachtungen | Review R1-R4 2.3/2.5: drei Kandidaten poolen Symbole mit identischen Ereignistagen (BTC/ETH rho~0,8 [sek, ungemessen]; K-34 "180 Dezil-Tage" real ~40; K-07 N-Floor 15 real 3,6) | Cluster-Einheit-Zeile; N-Floor gilt fuer `N_cluster` (R4 1.3c, Kolari/Pynnoenen 2010 [sek]) |
| L-7 | Ein Panel-Mitglied ist eine Beobachtung, keine Hypothese | H-06/H-08/H-09/H-22 zaehlten Symbol-Zellen als eigene Tests; bei N=200 zerstoert das die Power (R4 1.2f) | FDR-Familien bestehen aus Hypothesen-VARIANTEN; Panel-Mitglieder werden zu EINER Teststatistik gepoolt |
| L-8 | Zwei uebereinstimmende Laeufe beweisen keinen Determinismus | GL-024, DEC-34 | Determinismus-Nachweis mit N>=3 Laeufen plus Fingerprint (T2) |
| L-9 | Negative Behauptungen brauchen eine Inhaltsprobe | DEC-46: "kein Bybit-Options-Strom" war falsch | C.8; operativ: Inhaltsprobe auf `bybit/tickers` VOR jedem Spread-/OI-Zensus-Bau (WP-7) |
| L-10 | Eine daten-gated-Sperre ohne Nachladbarkeits-Probe kostet Jahre | H-26 wartet auf 210 `done_days`; die oeffentliche Deribit-API haelt DVOL ab ~2021-04 (R4 3.4) | Irreversibilitaets-Regel (3.3.7) |
| L-11 | Teure Maschinerie vor der Positivkontrolle ist die teuerste Form, nichts zu lernen | H-14: 2-3 GPU-Tage, danach an der Positivkontrolle gescheitert (GL-020) | Positivkontroll-Vorschaltung bei > 1 h Laufzeit (3.3.8), angewendet auf WP-10(B) |
| L-12 | Eine Hypothese, deren bestmoegliches Ergebnis nichts entscheidet, darf nicht eingeplant werden | H-14..H-17: 350 GPU-h; E.10 fuehrt H-15b/H-16b als NICHT registriert | Entscheidungsrelevanz-Zeile (3.3.2); GPU-Default 0 (3.7) |
| L-13 | Ein undefinierter Gate-Begriff ist ein offener Torpfosten | "Stress-Episode" war Gate-Bedingung ohne operationale Definition (Review R1-R4 6.6) | Stress-Kanon **DEC-55 und DEC-56, beschlossen** (`STRESS_REL` = Abdeckungs-Nachweis, `STRESS_ABS` = Liquiditaets-Definition); die Parameter sind Design-Parameter, keine Gate-Schwellen (3.3.10) |
| L-14 | Ein Kostenmodell mit stillen Defaults ist Torpfosten-Verschiebung mit Extraschritt | Delivery-/Exercise-Gebuehr blockiert H-26b (E.6a) | `constants_hash` im Ergebnis; ungemessene Konstanten RAISEN (3.3.6, Par. 6) |
| L-15 | Ein Ertrag ohne Kapitalbasis ist nicht vergleichbar, ein Netto-Ertrag ohne Steuer keine Netto-Aussage | In vier Berichten nie gerechnet (Review R1-R4 6.1-6.3) | Kapital-, Steuer- und Venue-Zeile (3.3.9) |
| L-16 | Die REZENZ-Klausel wird formal, nicht inhaltlich angewendet | Kein Bericht fragt, ob der ZAHLER nach dem Spot-ETF-Start noch existiert (Review R1-R4 6.5) | Zahler-Zeile (3.3.9c) |
| L-17 | Ein Retro-Check ist nur moeglich, wenn der alte Lauf seine Cluster-Serien gespeichert hat | DEC-52-Retro-Check konnte Auflage (iii) nicht nachrechnen: keiner der drei Ergebnis-JSONs speichert Roh-Serien je Cluster oder Bootstrap-Replikate; ersatzweise Stouffer/Fisher als **Obergrenze der Evidenz** | **DEC-53 (beschlossen): Ergebnis-Artefakt-Pflicht** - elfte Pflichtzeile (3.3.11), YAML-Feld `artifacts`, Teststufe T7 |
| L-18 | Ein zu pessimistischer Faktor darf nicht spaeter als Kantenverbesserung verkauft werden | Review R1-R4 2.7: der Dezil-Spreadfaktor ist exakt `2*E[z \| oberstes Dezil] = 3,51`, nicht 2,0 - R2 ist um Faktor 1,75 zu pessimistisch, die einzige Stelle, an der ein Fehler gegen den eigenen Kandidaten laeuft | Der Faktor **3,51** wird in Par. 9.2 als Programm-Konstante gefuehrt und ab sofort verwendet; die Korrektur ist hiermit dokumentiert und ist keine spaetere Verbesserung |

---

## 3. Verfassung 3.0

### 3.1 Unveraendert uebernommen: C.1-C.19

Die 19 Methoden-Lehren des Kompendiums (Abschnitt C) gelten unveraendert und vollstaendig; der Wortlaut im Kompendium ist normativ. Kurzform mit erzwingendem Vorfall:

| ID | Regel | Vorfall |
|---|---|---|
| C.1 | Registry-Disziplin, Pre-Registration, append-only, kein Torpfosten-Verschieben - symmetrisch auch fuer unliebsame PASS | 31 GL-Eintraege, H-11/DEC-31 |
| C.2 | **Mess-Gate != Tradability-Gate** | H-04 -> H-04b, H-05b -> H-05c |
| C.3 | Anti-Gaming-Klausel: Wand, Latenz-Haircut, Fill-Annahme vorab fixiert, nie absenkbar | DEC-13/16 |
| C.4 | Struktureller Nulleffekt VOR der Schwellenfestlegung | H-11/GL-022, DEC-31/33 |
| C.5 | Positives UND negatives Fixture (DEC-39) | H-24 |
| C.6 | Materialitaets-Schranke statt Bit-Identitaet gegen lebende Speicher, plus SHA-256 | H-11c, DEC-32 |
| C.7 | N=2 beweist keinen Determinismus | GL-024, DEC-34 |
| C.8 | Inhaltsprobe statt Namensschluss | DEC-46 |
| C.9 | Keine n=1-Extrapolation ohne Kontrolle der erzeugenden Achse | WP-5, DEC-44 |
| C.10 | Hartes Ein-Fenster-Abbruchkriterium | PRD 2.0 Par. 8.5, H-20 |
| C.11 | Modul != Strategie | CS-01/CS-02 |
| C.12 | Struktureller A-priori-DROP vor jedem Datenlauf pruefen (GL-012) | H-07 |
| C.13 | Positivkontrolle als Pflichtbestandteil komplexer Maschinerien | H-14/GL-020 |
| C.14 | Loud-Fail-Doktrin | GL-018, GL-029, DEC-46 |
| C.15 | Checkpoint-Round-Trip, nicht nur Rechenpfad | GL-030 |
| C.16 | Zweistufige FDR (Familie -> Ueber-Familie) | DEC-22 |
| C.17 | Data-Snooping-Offenlegung + Entdeckungszellen-Ausschluss | H-05b |
| C.18 | REZENZ-Klausel | Welle-6-Querbefund, DEC-38 |
| C.19 | Reversibelste-Option-Prinzip, nie fuer Gate-Schwellen | DEC-03..DEC-18 |

**Bestaetigung zu C.2 (Entwurf 3.0 Par. 2.1; Review R1-R4 4.5).** R4s Vorschlag, eine oekonomische Mindestmagnitude in die PASS-Bedingung des Mess-Gates aufzunehmen, wird **ABGELEHNT**: unter dieser Regel waere H-04 ein DROP gewesen, und DROP ist endgueltig und append-only. **v2-Verschaerfung nach Review PRD3 2.1:** die Regel gilt nicht nur fuer PASS-Bedingungen, sondern auch fuer **Befundzweige von Zensus-Paketen** und fuer **Feasibility-Kill-Bedingungen**. Ein Ausloeser, der eine Handelskostenzahl ist, ist ein Tradability-Kriterium, gleichgueltig, wie das Feld heisst. Konkret behoben: WP-7-Befund B1 (jetzt rein statistisch, 4.1), WP-7-Befund B5 (jetzt Etikett ohne Streichungsoption, 4.1), A4-Gate (jetzt Rauschboden statt `w_min`, 5.4).

### 3.2 Die drei Hypothesen-Klassen

- **Klasse P - Praemien-Ernte.** Ertragsquelle ist ein Erwartungswert-Keil zwischen zwei beobachtbaren Preisen. Urteilstragend ist `mean(prem)`, nie der Sharpe (3.6). Nulleffekt-Katalog: Jensen-/Konvexitaets-Term, Ueberlappung, Peso-Term, Selektions-Decke, MaxDD-Boden, Tail-Ratio-Richtungsfehler (R4 1.1b).
- **Klasse W - Wochen-Horizont-Querschnittsfaktoren.** Urteilstragend ist der Querschnitts-Rank-IC. Nicht ueberlappend messen (R4 1.2a, DEC-51 Punkt 5). Nulleffekt-Katalog: Querschnitts-Permutations-Null, Persistenz-Null (Valkanov 2003 / Boudoukh-Richardson-Whitelaw 2008 [sek via R4 1.2b]), Selektions-Decke.
- **Klasse E - Ereignis-Studien.** `CAR` ueber genau EIN vorregistriertes Fenster, kein Fenster-Scan. Nulleffekt ist die Placebo-Verteilung auf Zufallsterminen mit identischer Kalenderverteilung. Resampling-Einheit ist das Kalender-Cluster (R4 1.3).

### 3.3 Die zwoelf Pflichtzeilen jeder 3.0-Registrierung

Zehn Zeilen aus Entwurf 3.0 Par. 2.2, dazu die Ergebnis-Artefakt-Zeile aus DEC-53 und die Test-Pflichten. Eine Registrierung ohne vollstaendige Zeilen ist kein gueltiger Registry-Eintrag; ein Lauf darauf ist kein gueltiger Lauf.

**3.3.1 Power-Zeile.** Welchen Effekt sieht das registrierte Fenster mit Power 0,80? Die Zeile nennt alpha, Seitigkeit, Power, Richtung, Cluster-Einheit, effektives N und die detektierbare Effektgroesse mit Rechenweg.

> **DEC-51 - Programmweite Power-Konvention (BESCHLOSSEN, `state/decisions.md`).**
> 1. Mess-Gates: **alpha = 0,05 einseitig in Hypothesenrichtung**; **die Richtung ist Teil der Registrierung** (YAML-Feld `richtung`). **Zweiseitige Fragen (META/Zensus) laufen bei alpha = 0,05 zweiseitig und werden ausdruecklich so etikettiert** - das betrifft WP-7, WP-9 und WP-10 unmittelbar.
> 2. **Power-Ziel 0,80** fuer den in der Power-Zeile benannten Mindesteffekt. Liegt die A-priori-Erwartung darunter, ist die Registrierung ein GL-012-Fall (Feasibility-DROP vor dem Lauf) oder braucht ein anderes Design.
> 3. **Cluster-Einheit** ist die groesste Einheit, innerhalb derer Beobachtungen gemeinsame Schocks teilen: Symbol-Panels -> Kalendertag bzw. Kalenderwoche; Ereignisstudien -> das Ereignis (alle Symbole desselben Verfalls = ein Cluster); Fenster-Designs -> das Fenster. `N_eff` wird mit **gemessenem** rho ausgewiesen; **rho = 0 ist nie Default**.
> 4. **Selektions-K** steht in jeder Registrierung; die Schwelle liegt ueber der Bailey/Lopez-de-Prado-Decke fuer dieses K (R4 K-0.3).
> 5. **Ueberlappende Renditen zaehlen nicht als unabhaengige Beobachtungen**; effektives N ueber Blocklaenge = Ueberlappung (R3-K-37-Lehre, Review R1-R4 2.4).
>
> Zahlenwerte: einseitig `z = 1,6449 + 0,8416 = **2,4865**`; zweiseitig `z = 1,9600 + 0,8416 = **2,8016**`; einseitig bei alpha = 0,01 (DEC-52 (iv), gepoolter Zweig) `z = 2,3263 + 0,8416 = **3,1680**`.

**3.3.2 Entscheidungsrelevanz-Zeile.** Was aendert ein PASS konkret - naechster Schritt, Kapitalpfad, Tradability-Folge? Was schliesst ein DROP? Die Zeile enthaelt die **oekonomische Mindestmagnitude** aus der Horizont-Friktions-Kurve als **ETIKETT, nicht als Gate** (C.2). Ein Kandidat, dessen bester Fall unter der Wand liegt, ist registrierbar, traegt aber das Etikett und verbraucht bewusst einen Alpha-Slot.

**3.3.3 Cluster-Einheit-Zeile.** Resampling-Einheit und effektives N; Pooling korrelierter Symbole ueber dieselben Kalendertage zaehlt als EIN Cluster. Der registrierte N-Floor gilt fuer `N_cluster`, nie fuer `N_events`. Die Umrechnung `N_eff = N_c/(1+(N_c-1)*rho)` wird mit benanntem, **gemessenem** rho gerechnet.

**3.3.4 Selektions-Deflation.** `K` (Zahl gerechneter Varianten) vorab registriert; Schwelle ueber der Bailey/LdP-Decke: `E[max SR] ~= sigma_SR * ((1-g)*Phi^-1(1-1/K) + g*Phi^-1(1-1/(K*e)))`, `g = 0,5772`, `sigma_SR ~= 1/sqrt(T)`. Bei T=5 a: K=5 -> 0,53; K=20 -> 0,85; K=50 -> 1,02; K=100 -> 1,13. Zusaetzlich wird die Decke **empirisch am Null-Fixture gemessen** (R4 1.1d - genau dieser Schritt fehlte bei H-11).

**3.3.5 Drittes, adversariales Fixture.** Je Klasse vorgeschrieben: Klasse P **Peso-Fixture** (Nullpraemie plus Merton-Spruenge, Rate 1/3 Jahre, Hoehe -35 %; ein 5-Jahres-Fenster ist mit `p = e^-1,67 = 0,19` sprungfrei und zeigt dann eine scheinbar hochsignifikante Praemie - **das Gate MUSS durchfallen**); Klasse W ein Faktor, der mechanisch mit dem Markt-Beta korreliert, auf einem Panel mit dominantem Marktfaktor; Klasse E Ereignisse, die auf vergangenen Renditen selektiert werden, auf einem Random Walk (Fehlerklasse H-20).

**3.3.6 Kostenmodell-Bindung.** `constants_hash` (SHA-256 ueber `tradability3/constants.py`) im Ergebnis. Ein Lauf mit abweichendem Hash ist **kein gueltiger Lauf**. Ungemessene Konstanten RAISEN.

**3.3.7 Irreversibilitaets-Regel.** Vor jeder daten-gated-Sperre eine dokumentierte Probe auf oeffentliche Nachladbarkeit; umgekehrt rechtfertigt nur Irreversibles einen Dauerstrom (7.2).

**3.3.8 Positivkontroll-Vorschaltung.** Bei jeder Maschinerie mit > 1 h Laufzeit laeuft die Positivkontrolle ZUERST und allein; ihr PASS ist Vorbedingung der Einplanung (R4 4.4.5). **Angewendet auf WP-10(B)** (86 min je Fenster, 4.3).

**3.3.9 Kapital-, Steuer- und Venue-Zeile.** (a) Rendite auf **gebundenes Kapital**, nicht auf Notional; Kapital-Multiplikator `m` **UNGEMESSEN** (eigener Margin-WP), Pflicht-Sensitivitaet. (b) Steuerliche Behandlung der Cashfluesse; Funding = laufender Ertrag; Eingangswerte vom Nutzer - **UNBELEGT, Par. 8.2**. (c) Venue-Ereignis (ADL auf dem gewinnenden Bein, Auszahlungsstopp; bei 5-10 % p.a. Kante ist 1 %/Jahr Totalverlustwahrscheinlichkeit ein Abschlag von 10-20 % auf den Erwartungswert, Review R1-R4 6.3) **und Zahler-Bestand nach 2024**.

**3.3.10 Stress-Episode.**

> **DEC-55 - Stress-Kanon als Fixture (BESCHLOSSEN, `state/decisions.md`).** Deterministisch erzeugte Tagesliste aus dem WP-0-Bar-Cache: alle UTC-Tage, deren realisierte Tagesvol (BTC oder ETH) ueber dem **97,5-Perzentil der juengsten 24 Monate** liegt, plus der **2026-08-19** als Referenz-Ereignis; zusammenhaengende Tage mit hoechstens einem Nicht-Stress-Tag Luecke bilden EINE Episode. Fixture mit SHA-256, je Kalendermonat append-only fortgeschrieben.
> **Etikett (bindend):** 97,5 %, 24 Monate und die Luecken-Regel sind **DESIGN-PARAMETER, keine Gate-Schwellen**. Keine Hypothese darf sie variieren oder eine eigene Stress-Definition einfuehren; wer eine andere braucht, registriert sie als **neue DEC vor dem Lauf**.

> **DEC-56 - Stress-Kanon praezisiert (BESCHLOSSEN, `state/decisions.md`).** Anlass war der Befund, dass ein **rollierender** 97,5-Perzentil-Schnitt per Konstruktion ~2,5 % Stress-Tage in **jedem** Fenster erzeugt: die Klausel ">= 1 Stress-Episode je urteilstragendem Fenster" kann damit **nie binden** und waere als Filter ein Schein-Gate; zweitens misst ein relativer Vol-Schnitt Vol-Regime, nicht die Liquiditaets-Crashs, die WP-10(A) braucht (Review PRD3 W-10).
> **(1)** Die DEC-55-Liste heisst **`STRESS_REL`** und ist ausdruecklich ein **Abdeckungs-Nachweis** (das Fenster enthaelt nachweislich seine Regime-Extreme) - **nie ein Filter oder Gate**.
> **(2)** Eine zweite, **absolute** Liste **`STRESS_ABS`** wird als Fixture eingefuehrt: alle UTC-Tage, deren realisierte Tagesvol (BTC oder ETH) ueber dem **99-Perzentil der GESAMTEN WP-0-Historie** liegt, plus namentlich **2025-10-10** und **2026-08-19**. **`STRESS_ABS` ist die Stress-Definition fuer WP-10(A) (Praemien-Kohaerenz) und fuer jede Liquiditaets- und Fill-Frage.**
> **(3)** Das 99-Perzentil und die zwei benannten Tage sind **DESIGN-PARAMETER** (kein Gate, nicht variierbar); Ergaenzungen der Namensliste nur per neuer DEC.
> **Zuordnung in diesem PRD:** Klasse-P-Registrierungen weisen die `STRESS_REL`-Abdeckung ihrer Fenster nach (A1, A4); WP-10(A) und jede Fill-/Slippage-Frage rechnen auf `STRESS_ABS`.

**3.3.11 Ergebnis-Artefakt-Zeile.**

> **DEC-53 - Ergebnis-Artefakt-Pflicht (BESCHLOSSEN, `state/decisions.md`).** Jeder 3.0-Treiber schreibt neben dem Summary (a) die **urteilstragende Serie auf Cluster-Ebene** (je Kalendertag/Woche/Ereignis gemaess DEC-51 Punkt 3) als Parquet/CSV mit SHA-256, und (b) die **Bootstrap-Replikate** des Gate-Schaetzers (mindestens die 1.000 Ziehungen) oder Seed plus Generator-Fingerprint, aus dem sie bit-identisch reproduzierbar sind. **Ein Lauf ohne (a)+(b) ist KEIN VERDIKT** (loud fail im Treiber, Test gepinnt).
> *Entstehungsgrund, woertlich aus dem Retro-Check:* Auflage DEC-52 (iii) - gepoolter, fenster-geclusterter Bootstrap - war fuer die 2.0-Laeufe **nicht nachrechenbar**, weil keiner der drei Ergebnis-JSONs Roh-Serien je Cluster oder Bootstrap-Replikate speichert; der Retro-Check nutzte Stouffer/Fisher-Kombinationen der Fenster-p als **Obergrenze der Evidenz**. Ohne DEC-53 waere der naechste Regel-Retro-Check wieder nicht nachrechenbar.

**3.3.12 Test-Pflichten je 3.0-Research-Modul.**

| Stufe | Inhalt | Vorfall |
|---|---|---|
| T0 | Unit-Tests der reinen Funktionen auf synthetischen Eingaben | Standard |
| T1 | Drei Fixtures als echte Tests: positiv, null, adversarial | DEC-39, erweitert (3.3.5) |
| T2 | Determinismus mit **N>=3** Laeufen plus Fingerprint | DEC-34 / C.7 |
| T3 | Checkpoint-Round-Trip: schreiben, abbrechen, laden, bit-identisch fortsetzen | GL-030 |
| T4 | Gate-Arithmetik-Test auf einem konservierten Ergebnis-Payload | macht das Gate maschinell pruefbar |
| T5 | Kosten-Konstanten-Pin (`constants_hash`) | DEC-13/16 |
| T6 | Legacy-Import-Sperre fuer 3.0-Module | UMBAU_SPEZIFIKATION / DEC-54 |
| **T7** | **Artefakt-Round-Trip: der Treiber schreibt Cluster-Serie und Replikate/Seed; der Test laedt sie und reproduziert den Gate-Schaetzer bit-identisch. Fehlt eines von beiden, meldet der Treiber KEIN VERDIKT (loud fail)** | **DEC-53** |

### 3.4 Registrierungs-Template mit YAML-Block

Der Markdown-Eintrag bleibt der **normative Text**; in ihn wird ein gezaunter YAML-Block eingebettet. **Eine Datei, eine Wahrheit.** Die 2.0-Registry wird **NICHT migriert** (append-only und urteilstragend; R4 5.3, Review R1-R4 4.3).

> **DEC-58 (Entwurf) - Registry-Format 3.0**, mit den drei Review-Auflagen woertlich: (a) Der Linter unterliegt selbst der Loud-Fail-Doktrin (C.14) - er darf nie still durchwinken, wenn er den Block nicht parsen kann. (b) **Pflichtfelder duerfen keine Haekchen werden:** `structural_null: 0` erfuellt einen naiven Parser und ist schlimmer als nichts; der Linter verlangt fuer jede Schwelle und jeden Nulleffekt eine **Herleitungs-Referenz** (Dateipfad + Test-ID), nie einen nackten Skalar. (c) Die append-only-Eigenschaft wird **mechanisch erzwungen** (Test, der die Bytes aller Alt-Eintraege hash-pinnt).
> *Nummer:* Im Log sind DEC-54 der Repo-Umbau, DEC-55/DEC-56 der Stress-Kanon und DEC-57 der GPU-Default (alle beschlossen); die beiden noch offenen Werkzeug-Entscheidungen bekommen deshalb **DEC-58** (Registry-Format) und **DEC-59** (Kostenkonstanten-Modul).

```yaml
id: <A1|A2|...>
klasse: <P|W|E>
capital_free: true
hypothese: <ein Satz, falsifizierbar>
ertragsquelle: <Praemie|Prognose|Ereignis|Struktur> + Zahler
metric: <Name>                       # genau eine urteilstragende Groesse
richtung: <positiv|negativ>          # DEC-51 Punkt 1: Teil der Registrierung
windows:
  - {id: W1, von: <YYYY-MM-DD>, bis: <YYYY-MM-DD>, rolle: <urteilstragend|aera-profil>}
  - {id: W2, von: <YYYY-MM-DD>, bis: <YYYY-MM-DD>, rolle: urteilstragend}
fenster_regel: <C10_hart | DEC52>    # vorab fixierte Zuordnung, s. power.zuordnungsregel
threshold: {wert: <Zahl|Formel>, ref: <pfad#test_id>}
structural_null: {komponenten: [...], wert: <Zahl>, ref: <pfad#test_id>}
power:
  alpha: 0.05
  sided: <one|two>                   # two fuer META-/Zensusfragen (DEC-51 Punkt 1)
  power: 0.80
  z: <2.4865 | 2.8016 | 3.1680>
  cluster_unit: <kalendertag|kalenderwoche|ereignis|fenster>
  n_eff: <Zahl, mit gemessenem rho>
  a_priori_effekt: <Zahl + Beleg>    # der Effekt, gegen den die Power gerechnet wird
  detectable_effect: <Zahl>
  per_fenster_power: <Zahl>          # entscheidet ueber DEC-52 (i)
  zuordnungsregel: <vorab fixierter Text>
  ref: <pfad#test_id>
selection: {K: <Zahl>, ceiling_analytic: <Zahl>, ceiling_measured_ref: <pfad#test_id>}
economic_minimum: {wert: <Zahl>, ref: <pfad>, label: <ueber_wand|unter_wand>}   # ETIKETT
decision_relevance: {on_pass: <...>, on_drop: <...>}
capital_tax_venue: {kapitalbasis: <...>, steuer: <...>, venue_event: <...>, zahler_post_2024: <...>}
stress_episode: {liste_ref: <pfad#fixture_id>, rolle: abdeckungsnachweis, n_episoden: <Zahl>}
irreversibility_probe: {ergebnis: <nachladbar|irreversibel>, ref: <...>}
positive_control: {laufzeit_geschaetzt_h: <Zahl>, vorgeschaltet: <true|false>, ref: <...>}
fixtures: {positive: <...>, null: <...>, adversarial: <...>}
artifacts:                           # DEC-53, Pflicht
  cluster_series_ref: <pfad + sha256>
  bootstrap_replicates_ref: <pfad + sha256 ODER seed + generator_fingerprint>
fdr_family: <F-...>
over_family: <F-...>
feasibility_verdict: <bestanden|verfehlt>
constants_hash: <sha256 | "n/a - kapitalfrei ohne Kostenmodell">
data_fingerprints: [...]
stats3_version: <x.y.z>
bedingung_welle_1: [<WP-7|WP-9|WP-10|V-1..V-5>]
```

### 3.5 Die Ein-Fenster-Regel: DEC-52 (BESCHLOSSEN)

**Ausgangslage.** C.10 kostet nach R4 K-0.6 bei Per-Fenster-Power 0,5 drei von vier echten Effekten; das Programm fuhr dadurch unbemerkt bei einem effektiven alpha von `0,05^2 = 0,25 %` statt 5 %. Gegenrechnung: bei wahrem Per-Fenster-t = 1,4 ist `P(Vorzeichen richtig) = Phi(1,4) = 0,919`, `P(beide) = 0,845` gegen `0,42^2 = 0,18` - **Faktor 4,7 mehr Retention**.

**Gegenargumente, die im Beschlusstext stehen bleiben** (Review R1-R4 4.1): (a) Der Zweck der Regel war Regime-Robustheit, nicht alpha-Kontrolle - ein gepoolter Schaetzer mittelt genau darueber hinweg. (b) Vorzeichen ist ein 1-Bit-Test. (c) Eine Regelaenderung, die ein bestehendes Verdikt umdreht, waere per Definition eine Lockerung.

> **DEC-52 - Ein-Fenster-Regel fuer Klassen mit Per-Fenster-Power < 0,6 (BESCHLOSSEN, Nachtrag 2026-09-02).**
> **(i)** Nur anwendbar, wo die **Power-Zeile VOR dem Lauf** Per-Fenster-Power **< 0,60** ausweist; Zensus-artige, hoch-gepowerte Fragen behalten C.10 unveraendert.
> **(ii)** Je Fenster: Punktschaetzer mit **hypothesiertem Vorzeichen UND >= 0,5x der registrierten Schwelle**; Magnituden-Band **[0,5x; 2,0x]**.
> **(iii)** Signifikanz **ausschliesslich auf dem GEPOOLTEN Schaetzer** mit fenster-geclustertem stationaerem Bootstrap.
> **(iv)** Gepooltes **alpha = 0,01**, weil der Zwei-Fenster-Filter das alpha nicht mehr traegt.
> **(v)** Retro-Check veroeffentlicht.
> **Sequenz-Zwang:** nie kandidatenspezifisch; die Regel steht VOR der Registrierung des ersten Kandidaten, der sie braucht.

**Ergebnis des Retro-Checks** (`state/RETROCHECK_DEC52.md`, veroeffentlicht): **kein Verdikt kippt.** H-06 verfehlt den 0,5x-Screen in beiden Fenstern und beiden Metriken (7-62 % der halben Schwelle); H-22 faellt am Vorzeichenwechsel in BTC W-L2-2 (IC +0,067 -> -0,011); H-20 ist der einzige knappe Fall (OOS-1 +4,83 bp gegen 5-bp-Screen, Abstand 0,17 bp), waere aber auch bei bestandenem Screen an der gepoolten Signifikanz gescheitert (Proxy-Obergrenzen p ~0,20-0,34 gegen alpha 0,01). **Etikett: Verbesserung, nicht Lockerung.** **Einschraenkung, woertlich uebernommen:** Auflage (iii) war fuer die 2.0-Laeufe **nicht nachrechenbar**, weil keiner der drei Ergebnis-JSONs Roh-Serien je Cluster oder Bootstrap-Replikate speichert; der Retro-Check nutzt Stouffer/Fisher als **Obergrenze der Evidenz**. Da selbst diese Obergrenzen alpha 0,01 um Faktor > 20 verfehlen, ist der Schluss robust. **Aus dieser Einschraenkung folgt DEC-53** (3.3.11).

**Praezisierung zur Falsch-Positiv-Rate (Review PRD3 K-4).** Vor DEC-52 lag die gemeinsame Rate bei `0,05^2 = 0,25 %`. Nach DEC-52 ist sie `P(Vorzeichenfilter) x alpha_gepoolt ~= 0,5 x 0,01 = 0,5 %` - also **Faktor 2 hoeher**, nicht unveraendert. Das ist die bewusst in Kauf genommene Groesse; ohne die Absenkung auf alpha 0,01 waere sie 2,5 %, also Faktor 10. Der Restfaktor 2 wird hier benannt, damit "keine Lockerung" praezise bleibt: er ist der Preis fuer Faktor 4,7 Retention.

**Anwendung je Kandidat wird GERECHNET, nicht behauptet** (Review PRD3 2.3/B-5). Fuer jeden Kandidaten steht in Par. 5 eine Zahl fuer die Per-Fenster-Power gegen den registrierten A-priori-Effekt, und eine **vorab fixierte Zuordnungsregel**, die vor der Registrierung ausgewertet wird - nie nach dem Lauf.

### 3.6 Praemie statt Sharpe

Urteilstragende Groesse der Klasse P ist die **Praemie** (`mean(prem)`). **Sharpe, MaxDD und Tail-Ratio werden BERICHTET, nie geurteilt**, jeweils mit hergeleitetem Rauschboden.

*Herleitung.* Lo (2002, FAJ 58(4)) [sek via R4 K-0.2]: `Var(SR_p) = (1 + SR_p^2/2)/n`, annualisiert `SE(SR_ann) = sqrt((1 + SR_ann^2/(2q))/T)`. Mit DEC-51 (`z = 2,4865`) folgt exakt `T_min = 2,4865^2 * (1 + SR^2/(2q))/SR^2`; **die im Programm zitierte Kurzform `T_min ~= 6,18/SR^2` ist eine Naeherung, die den Term `SR^2/(2q)` streicht.** Bei Tagesdaten (`q = 365`) ist der Fehler klein und die Naeherung **zu optimistisch**: SR 2,0 ergibt exakt 1,80 statt 1,55 Jahre. Werte (Naeherung): SR 1,0 -> 6,19 a; SR 0,75 -> 11,0 a; SR 0,5 -> **24,7 a**. Mit der Mertens-Erweiterung (monatliche Schiefe g3 = -2, Exzess-Kurtosis 10, SR_ann = 1,0; monatlicher SR 0,2887) ist der Varianzfaktor 1,827, also `T_min = 11,3` statt 6,2 Jahre. **Der Bestand reicht 5-6 Jahre** (B.16).

*Auflagen (Review R1-R4 4.2), woertlich bindend:* (1) Jeder P-A-PASS traegt das Etikett **"Praemien-EXISTENZ; die risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER"**, im PASS-Text selbst. (2) **Kein Kapitalschritt folgt aus einem P-A-PASS.** (3) Die Beobachtungszahl wird nicht ueberzeichnet: "1.095 Funding-Beobachtungen" sind bei Blocklaenge ~30 Tagen effektiv ~12 unabhaengige Beobachtungen pro Jahr; der reale Power-Gewinn ist Faktor ~12, nicht ~219. (4) Fuer das RISIKO ist das effektive N die Zahl der **Stress-Episoden**, nicht die Zahl der Funding-Intervalle.

**Degradierte Gates:** `SR_block >= 0,60` (R1 G3) wird **Bericht, nicht Gate** (bei `N_eff = 12` und `SE(SR) = 0,31` ein Gate mit ~50 % Power je Fenster). `TR = |CVaR_1%|/mean <= 250 Tage` (R1 G4) wird **Deskriptor mit Untergrenze** (eine echte Praemie hat strukturell Tail-Ratio < 1; die Kennzahl hat den Mittelwert im Nenner und bestraft kleine Praemien: 0,5 bps/Tag mit CVaR 200 bps ergibt TR=400 - getoetet; 2 bps/Tag mit CVaR 400 bps ergibt TR=200 - bestanden). MaxDD-Schwellen werden aus `E[MaxDD] = 1,2533*sigma_ann*sqrt(T)` hergeleitet (Magdon-Ismail et al. 2004 [sek]): sigma 20 %, T=5 a -> 56 %; eine importierte Schwelle "MaxDD < 30 %" waere strukturell unerreichbar.

### 3.7 GPU-Default 0

> **DEC-57 - GPU-Standardbudget je Hypothese = 0 (BESCHLOSSEN, `state/decisions.md`).** Ein GPU-Lauf braucht eine registrierte Begruendung, warum die CPU-Fassung die Frage nicht beantworten kann, UND eine Entscheidungsrelevanz-Zeile mit Tradability-Pfad. Grundlage: ~350 GPU-Stunden in 2.0, Ertrag 2 kapitalfreie WEITER, **0 registrierte Tradability-Folgen**. Die Regel kostet nichts, weil keine der drei 3.0-Klassen GPU braucht (R4 4.2).
> **Die 24-h-Wall-Clock-Kappe wird NICHT als Schwelle uebernommen** (Review R1-R4 4.4: importierte Zahl ohne Herleitung; H-15 lief 180 h checkpointet und lieferte ein gueltiges WEITER). Sie wird **Budget-Meldegrenze**: ein Lauf ueber 24 h wird vor dem Start gemeldet und begruendet, nicht verboten. Das wirksame Instrument ist die Positivkontroll-Vorschaltung (3.3.8).

### 3.8 Kein Live-Order-Code - und der benannte Preis

"Kein Live-Order-Code" bleibt Verfassung. Der Preis wird benannt statt hingenommen (R4 6.3): Fill-Wahrscheinlichkeiten sind nie direkt messbar, jede Maker-Annahme bleibt unfalsifizierbar - und Maker ist nach K-0.1 der Unterschied zwischen 53 Minuten und 6,6 Stunden Mindesthorizont. Mittelweg ohne Regelbruch: die **kapitalfreie Quote-Schatten-Messung** (WP-10 Teil B, 4.3) - Rekonstruktion der Warteschlangen-Position einer hypothetischen eigenen passiven Quote aus rein oeffentlichen Daten. Keine Order, kein Kapital, kein Key. Der Widerspruch "bester Kandidat / kein Live-Order-Code" (Review R1-R4 6.4) wird nicht still entschieden - Par. 8.1.

### 3.9 Modell- und Teampolitik

| Rolle | Modell | Auftrag |
|---|---|---|
| Orchestrator | **Fable 5.1** (immer) | Entscheidungen, Registrierungstexte, Gate-Urteile, Verfassung |
| Zensus-/Backfill-Bau (WP-7, WP-9, WP-10) | **Sonnet** | Bau nach Spezifikation, mit Test-Abnahme (T1 Fixtures, T2 Determinismus, T7 Artefakte) |
| Gate-Design und Registrierungs-Herleitungen | **Opus**, danach adversarischer Review durch einen **zweiten Opus-Agenten** | Fable 5.1 entscheidet nur bei Widerspruch zwischen beiden |
| Kartierung, Inventur, Dokumentpflege | **Sonnet** (ggf. Haiku fuer reine Listen) | - |

**Bindend: kein Agent registriert eine Hypothese.** Das tut ausschliesslich der Orchestrator, nach Review.

---

## 4. Welle 1: Zensus zuerst, kein Alpha-Slot ohne Feasibility

**Prinzip.** Die Reihenfolge ist bindend. Jedes Paket folgt dem **WP-4-Muster**: eine Frage, ein binaerer Befund, und die Konsequenz **jedes** Ausgangs steht VORAB im Dokument. Welle 1 verbraucht **null Alpha-Slots**. Nach DEC-51 Punkt 1 sind WP-7, WP-9 und WP-10 **Zensus-/META-Fragen und laufen zweiseitig bei alpha = 0,05** (`z = 2,8016`), soweit sie eigene Teststatistiken tragen; die von ihnen berechneten Power-Zeilen der Kandidaten uebernehmen deren einseitige Konvention und weisen das aus.

**Laufort.** `api.bybit.com`, `bybit.com` und `bybit-exchange.github.io` sind vom Egress-Proxy der Sandbox geblockt (R1 0.5); die Sandbox hat kein torch und keine GPU (B.17). Daraus: alle REST-Downloads und Primaerquellen-Pruefungen auf der **Nutzer-Maschine**; T0/T1 (Fixtures, synthetische Eingaben) in der **Sandbox**; T2/T3/T7 (Echtdaten, Determinismus, Artefakt-Round-Trip) auf der **Nutzer-Maschine**.

| # | Paket | Beantwortet | Aufwand | Laufort |
|---|---|---|---|---|
| WP-7 | Universums-Zensus (R2-V-0 + R4-WP-8 vereinigt) | Ist die Querschnitts-Klasse **statistisch** testbar? Welches K, welches `SD_null(IC_t)`, welches `sigma_xs`, `sigma_LS`, welcher Alt-Symbol-Spread? | 1d-Klines ~10 min Download; Tickers-Inhaltsprobe Minuten; ~1 Personentag Code | Nutzer-PC (Fixtures: Sandbox) |
| WP-9 | DVOL-Backfill + Quellen-Kreuzvalidierung | Sind ~5,4 Jahre IV-Historie verfuegbar und mit dem Harvester konsistent? | Sekunden Download, ~1 h Abgleich | Nutzer-PC |
| WP-10 | Praemien-Kohaerenz (deskriptiv) + Maker-Fill-Schattenmessung | Wie sieht die Praemien-Korrelationsstruktur im Stress aus? Wie sieht die Fill-Raten-Kurve aus, und was kostet adverse Selektion? | (A) Minuten; (B) 86 min je Fenster (WP-4-Erfahrungswert) | Nutzer-PC |
| V-1..V-5 | Fuenf 10-Minuten-Vorfragen, oeffentlich, keyfrei | Vorbedingungen fuer A1, A2, A4, A5 | Minuten je Frage | Nutzer-PC (zwingend) |

### 4.1 WP-7 - Universums-Zensus (Rang 1 des gesamten Feldes)

**Ziel.** Die Groessen messen, an denen die gesamte Klasse W haengt: **K** (Zahl durchgehend handelbarer Perps), **`SD_null(IC_t)`** (der Rauschboden des Querschnitts-IC, direkt und annahmefrei gemessen), **`sigma_xs`** (wochenweise Querschnitts-Streuung), **`sigma_LS`** (Wochen-SD der Dezil-L/S-Rendite, Nuisance-Parameter fuer A1) und **`PERP_SPREAD_BP` je Symbol-Dezil**. Vereinigt R2-V-0 mit R4-WP-8 (Review R1-R4 5.1 Rang 1).

**Der Schaetzerwechsel gegenueber v1 (Review PRD3 B-1, Orchestrator-Entscheidung).** Der in v1 vorgesehene **paarweise `rho_quer`-Schaetzer wird ERSATZLOS gestrichen.** Begruendung, nachgerechnet und numerisch verifiziert: fuer die querschnittlich demeanten Residuen gilt in jeder Woche `sum_i e_{i,t} = 0`, also `Var(sum_i e_i) = 0`, also `sum_i Var(e_i) + sum_{i!=j} Cov(e_i,e_j) = 0`. Bei gleichen Varianzen ist die mittlere paarweise Korrelation damit **identisch `-1/(K-1)` fuer jede Datenlage** - im Aequikorrelationsmodell exakt und **unabhaengig von der wahren Korrelation rho**. Bei realistischer Vol-Heterogenitaet (lognormale Vol-Streuung `sigma_log = 0,6`, K = 170) misst derselbe Schaetzer **+0,045 bei wahrer Sektorkorrelation NULL**: ein Vol-Heterogenitaets-Artefakt des gleichgewichteten Demeanings, praktisch unabhaengig von der Groesse, die er messen soll. Ein Rang-1-Paket, das die gesamte Klasse W an dieser Zahl entscheidet, haette entweder eine algebraische Identitaet oder ein Artefakt gemessen. **Die Korrekturformel aus v1 ist damit ebenfalls gestrichen** - der Bias ist kein additiver Offset auf einem sonst informativen Schaetzer, er ist der ganze Schaetzer.

**Was stattdessen gemessen wird: der Rauschboden direkt.**

```
Fuer jede Woche t des point-in-time-Universums U_t:
  ziehe 1.000 zufaellige Querschnittssignale (Permutation der Charakteristik
  innerhalb der Woche ueber die Symbole von U_t)
  berechne je Ziehung IC_t = Spearman(Signal, Folgewochenrendite)
=> empirische Verteilung von IC_t unter der Null
=> SD_null(IC_t) = SD dieser Verteilung, gemittelt ueber die Wochen des Fensters
```

Dieser Schaetzer **enthaelt die tatsaechliche effektive Breite exakt**, ohne dass irgendeine Korrelation geschaetzt werden muss (R4 1.2b(1)), er laeuft auf dem **realen** Wochen-Renditepanel und ist damit annahmefrei gegenueber Vol-Heterogenitaet, Sektorstruktur und Marktfaktor. Rechenaufwand: Sekunden.

**Deskriptiv zusaetzlich, ohne Urteilslast:** die Partizipationszahl der Residual-Kovarianzmatrix `N_eff = (sum_i lambda_i)^2 / sum_i lambda_i^2` (Eigenwertspektrum nach Querschnitts-Demeaning). Sie beschreibt, wie viele unabhaengige Richtungen das Panel traegt, und wird berichtet, damit die Zahl `SD_null` interpretierbar bleibt. **Nachrichtlich** kann daraus `1/N_eff` als Analogon zur alten Groesse angegeben werden; es traegt kein Urteil.

**Die Feasibility-Frage ist ausschliesslich statistisch (C.2, Review PRD3 2.1(ii)).** Sie lautet: **"Kann das registrierte Design den registrierten A-priori-Effekt mit Power 0,80 sehen?"** - **nicht** "liegt der detektierbare Effekt ueber der Friktionswand". Registrierter A-priori-Effekt der Klasse W: **`IC_prior = 0,03`** [sek: R2 0.3C setzt 0,03 als "realistisch angesetzten" Wochen-Rank-IC; Primaerliteratur Liu/Tsyvinski/Wu 2022 nur ueber Suchtreffer, Volltext egress-gesperrt]. Die Friktionswand (`IC_min = 0,062` im Einzelpositionsrahmen der Kurve K-0.1 bzw. `0,102` im Portfoliorahmen mit 18 bps Wochenkosten) ist **ausschliesslich Etikett in der Entscheidungsrelevanz-Zeile**. Damit entfaellt der v1-Kostenbasis-Widerspruch (Review PRD3 1.1b: Faktor 23 zwischen vier Lesarten desselben Dokuments) vollstaendig, weil keine Lesart mehr eine Feasibility-Entscheidung traegt.

**Die Feasibility-Arithmetik.** Mit `SE(mean IC) = SD_null/sqrt(W)` und DEC-51:

```
per Fenster (W = 52,  z = 2,4865, alpha 0,05 einseitig):
    detektierbar = 2,4865 * SD_null / sqrt(52)  = 0,344886 * SD_null
    feasibel <=> 0,344886 * SD_null <= 0,03  <=>  SD_null <= 0,08699

gepoolt (W = 104, z = 3,1680, alpha 0,01 einseitig nach DEC-52 (iv)):
    detektierbar = 3,1680 * SD_null / sqrt(104) = 0,310648 * SD_null
    feasibel <=> 0,310648 * SD_null <= 0,03  <=>  SD_null <= 0,09657
```

Zur Orientierung, was das an Breite bedeutet - **Bestfall `N_eff = K`** (keine Restkorrelation), `SD_null = 1/sqrt(K-1)`:

| K (= `N_eff`, Bestfall) | `SD_null` | detektierbar per Fenster | detektierbar gepoolt | reicht fuer `IC_prior = 0,03`? |
|---|---|---|---|---|
| 117 | 0,0928 | 0,0320 | 0,0288 | nur gepoolt |
| 134 | 0,0867 | 0,0299 | 0,0269 | ja, beide |
| 170 | 0,0769 | 0,0265 | 0,0239 | ja, beide |
| 300 | 0,0578 | 0,0199 | 0,0180 | ja, beide |

Daraus die **notwendigen** Breitenbedingungen (weil stets `N_eff <= K`): **`K >= 134`** fuer das Per-Fenster-Design, **`K >= 109`** fuer den gepoolten Zweig. Der vom Orchestrator aus der B-4-Korrektur fixierte Floor **`K_min = 117`** liegt dazwischen: er ist eine **notwendige, nicht hinreichende** Untergrenze und traegt das Design nur im gepoolten Zweig und nur, wenn die **gemessene** `SD_null` die 0,09657 einhaelt. **Bindend ist ausschliesslich die Messung**, nicht die Tabelle - die Tabelle zeigt den Bestfall.

**Datenquellen mit Endpunkt.**
- `GET /v5/market/instruments-info?category=linear` (Universum, `status`, Cursor-Paginierung [sek: Bybit-Doku-Repo `raw.githubusercontent.com/bybit-exchange/docs`, Primaerquelle fuer die Schnittstelle, nicht fuer die Historientiefe]).
- `GET /v5/market/kline?category=linear&interval=D`, `limit` 1-1000, Default 500 [sek: dieselbe Quelle]. Rate-Limit **600 Requests je 5 s je IP = 120 Req/s** [sek]; Selbst-Drossel **5 Req/s = 4,2 % des Limits**. Arithmetik: 5,5 Jahre = 2.008 Handelstage; das `panel_1d`-Schema fuehrt daneben 2.190 Kalendertage als Partitionsraster (6 Jahre) - **beide Zahlen sind korrekt und bezeichnen Verschiedenes**; 3 Calls/Symbol, ~1.000 Symbole inkl. delisteter -> **~3.000 Calls, ~10 min, ~1,7 Mio Zeilen, 40-80 MB**.
- **Zuerst: Inhaltsprobe (C.8) auf den vorhandenen `bybit/tickers`-Strom** (3.751 Symbole, 43 Tage, F.1) auf `bid1Price`/`ask1Price`/`openInterest`/`fundingRate`. Findet die Probe sie, ist der Spread-Zensus auf Bestandsdaten in Minuten rechenbar und **es wird nichts neu gesammelt**; sonst ueber `GET /v5/market/tickers` (ein Request je Kategorie).
- **Zusaetzlich, aus dem WP-0-Bar-Cache:** die 30-Minuten-Renditekorrelation **rho(BTC, ETH)** wird GEMESSEN (Eingang der A2-Power-Zeile, bisher [sek] 0,8 aus Review R1-R4 2.3, dort selbst ungemessen).
- **Nicht in Welle 1:** der 1h-Panel-Store. Erst nach bestandener Feasibility und nur in der Aufloesung, die die ueberlebende Feasibility braucht (Review R1-R4 5.2 Punkt 2).

**Determinismus- und Fingerprint-Pflicht.** Jahres- statt Tages-Partitionen (`panel_1d/source=/category=/symbol=/year=`; Tages-Partitionen waeren 3,3 Mio Verzeichnisse). `frozen/` (abgeschlossene Jahre, unveraenderlich, fingerprint-tragend) vs. `open/` (laufendes Jahr); ein urteilstragender Lauf nutzt nur `frozen/`-Jahre ODER pinnt den `open/`-Fingerprint zur Laufzeit und zitiert ihn (C.19). Eigenes `panel_manifest.sqlite` mit `status in {DONE, PARTIAL, EMPTY, FAILED}`; **DONE** verlangt `n_rows == expected_days` aus Listing-Datum und Jahresende, **Loud-Fail (C.14) bei Abweichung**. `panel_fingerprint(source, category, symbol, year)` = SHA-256 ueber die exakten Wertbytes in kanonischer Reihenfolge, plus ein **Bereichs-Fingerprint** ueber (Symbolmenge, Jahresbereich), den jede Registrierung zitiert. Pflichtspalte **`funding_n`** (Zahl der Funding-Abrechnungen je Symbol-Tag): Bybit fuehrt 8h- UND 1h-Symbole, Intervalle aendern sich ueber die Historie - ohne die Zaehlung addiert man Aepfel und Birnen (dieselbe Fehlerklasse wie die zwei `publicTrade`-Dialekte, die 19 von 50 H-12-Tagen entwertet hat). **T2:** N>=3 Laeufe, Fingerprint-Vergleich. **T7 (DEC-53):** die Wochen-Serie der IC-Nullverteilung und der Permutations-Seed werden als Artefakt geschrieben; ohne sie KEIN VERDIKT. **Provenienz (Review R1-R4 6.9):** monatliche **1-%-Zufallsstichprobe** eingefrorener Partitionen wird neu gezogen und gegen die Fingerprints geprueft; Abweichung ist ein lautes Alarm-Ereignis.

**Binaerer Befund mit VORAB fixierter Konsequenz.**

| Befund | Vorab fixierte Konsequenz |
|---|---|
| **B1:** Die gemessene `SD_null` verletzt bei erreichbarem K beide Schranken (per Fenster > 0,08699 UND gepoolt > 0,09657) | **Klasse W ist statistisch nicht testbar.** Keine Registrierung von A3 und keine Registrierung des Querschnitts-Arms von A1. **Nie auf N=5 zurueckskalieren** - das waere D.7/H-07 zum zweiten Mal. Rein statistischer Ausloeser, keine Kostenzahl (C.2). |
| **B2:** `SD_null <= 0,08699` bei `K >= 134` (Per-Fenster-Design feasibel) ODER `SD_null <= 0,09657` bei `K >= 117` (gepoolter Zweig feasibel) | **Klasse W testbar.** A3-Registrierung erlaubt; welches Fenster-Regime gilt, entscheidet die gerechnete Per-Fenster-Power nach der in 5.3 vorab fixierten Zuordnungsregel. |
| **B3:** `instruments-info` liefert keine Zeilen mit `status != Trading`, ODER `kline` liefert fuer delistete Symbole keine Historie | Kein Survivorship-freies Universum aus Bybit-Bordmitteln. Konsequenz vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture eine Verzerrung **kleiner als die halbe registrierte Schwelle** zeigt; sonst nicht registrierbar. Externes Delisting-Register (Announcement-Scraping) ist **keine** Welle-1-Aufgabe. |
| **B4:** `sigma_xs` unterschreitet `sigma_xs_min` (Formel unten) | **Konsequenz ausschliesslich: alle Klasse-W-Kandidaten tragen das Etikett `unter_wand`.** Keine Streichung, kein DROP, keine Aenderung einer PASS-Bedingung (C.2, Review PRD3 2.1(iii)). Der Befund ist eine Tradability-Information, kein Mess-Verdikt. |
| **B5:** `PERP_SPREAD_BP` je Symbol-Dezil gemessen | Ergebnis wird als DEC registriert, **bevor** ein Kandidat davon profitiert (Review R1-R4 3.6). Bis dahin **RAISED `tradability3.perp`** (Par. 6). Klarstellung (Review PRD3 W-8): 15 bps ist die **Gesamtwand** (11 bp Gebuehr + ~4 bp Slippage), nicht eine "Majors-Slippage-Konstante"; eine Spread-Messung korrigiert die Konstante um **hoechstens ~27 %** und kann sie **nie unter 11 bps Taker** druecken (Review R1-R4 1-R3-K-35, woertlich). Ein Schwellenwert fuer "Alt-Spread zu breit" wird deshalb **nicht** gesetzt - der v1-Faktor `3x` war unhergeleitet und ist gestrichen. |

**`sigma_xs_min` als Formel statt als gesetzte 500** (Review PRD3 W-7). Im Portfoliorahmen gilt `R_LS = f * IC * sigma_xs` mit dem **exakten** Dezilfaktor `f = 3,51` (Review R1-R4 2.7; R2s 2,0 ist um Faktor 1,75 pessimistisch - die Korrektur ist in L-18 dokumentiert und ist keine spaetere Kantenverbesserung). Mit der Etikett-Bedingung "Bruttokante >= 2x Wochenkosten":

```
sigma_xs_min = 2 * Kosten_Woche / (f * IC_prior)
  A3-M (18 bps, f = 3,51, IC_prior 0,03):  36 / 0,1053 = 342 bps/Woche
  A3-M (18 bps, f = 2,00, konservativ):    36 / 0,0600 = 600 bps/Woche
```

Registriert wird die **Formel**; die Zahl ergibt sich nach WP-7 aus dem gemessenen `sigma_xs`. Die v1-Zahl 500 bps/Woche lag zwischen beiden Konventionen und war gesetzt; sie entfaellt.

**Definition of Done.** (1) Inhaltsprobe auf `bybit/tickers` dokumentiert (Felderliste, Takt, Abdeckung, JA/NEIN je Feld). (2) `panel_1d` gebaut, `panel_manifest.sqlite` ohne `PARTIAL`/`FAILED` in den urteilstragenden Fenstern, Bereichs-Fingerprint notiert. (3) Berichtet, jeweils mit CI: `K` je Kalendermonat, **`SD_null(IC_t)`** je Fenster, deskriptiv `N_eff` (Partizipationszahl), `sigma_xs` (Median und Quartile), `sigma_LS`, `PERP_SPREAD_BP` je Dezil, `rho(BTC,ETH)` auf 30-Minuten-Renditen, sowie die **Autokorrelation des Funding-Sortierschluessels ueber eine Woche** (Eingang A1). (4) Survivorship-Bauplan implementiert und getestet: point-in-time-Universum - ein Symbol ist in Woche t drin, wenn es zu Wochenbeginn **>= 8 Wochen** Bars hat (**Design-Parameter, keine Schwelle**: die Grenze schneidet das Listing-Pump-Artefakt ab; Konsequenz vorab fixiert - sie wird nie variiert, und ihre Wirkung wird als Sensitivitaet bei 4 und 12 Wochen **berichtet**, nicht geurteilt) UND in Woche t noch handelt; ein delistetes Symbol wird **nicht rueckwirkend entfernt**, sondern bis zum letzten Bar gehalten und zum letzten Schlusskurs geschlossen (ein "-100 %"-Ansatz waere falsch und gegenlaeufig verzerrt). (5) T2 (N>=3) gruen, T7-Artefakte geschrieben. (6) Befund B1..B5 mit der vorab fixierten Konsequenz dokumentiert.

**Testpflichten (T1).**
- **Positiv:** Panel mit injiziertem Querschnitts-IC 0,04 bei realistischer Korrelationsstruktur; der IC-Schaetzer muss den Wert im CI wiederfinden, und die gemessene `SD_null` muss die Detektion bei diesem Effekt erlauben.
- **Null (der entscheidende, weil v1s Schaetzer genau hier scheiterte):** Panel aus **unabhaengigen** Reihen mit **realistischer Vol-Heterogenitaet** (lognormale Vol-Streuung, `sigma_log = 0,6`). Anforderung: `SD_null` muss `~ 1/sqrt(K-1)` liefern, die deskriptive Partizipationszahl `N_eff ~ K`. **Ein Schaetzer, der hier einen Wert liefert, der von der Vol-Heterogenitaet statt von der Korrelationsstruktur abhaengt, ist untauglich und wird nicht gebaut** (L-2b).
- **Adversarial (Survivorship-Fixture):** signalfreies Panel, aus dem 30 % der Symbole nach einem simulierten Drawdown-Trigger geloescht werden. Der **unkontrollierte** Schaetzer MUSS eine scheinbare Momentum-Praemie ausweisen, der **kontrollierte** nicht. Faellt der Test durch, ist die Panel-Maschinerie methodisch invalide (H-14-Muster, C.13) - dann kein Befund, sondern "methodisch invalide". Bias-Richtung vorab: verschwundene Perps sind ueberwiegend solche nach langem Drawdown; ihr Fehlen macht die Short-Seite eines Momentum- und die Long-Seite eines Reversal-Portfolios kuenstlich gut [sek: Grobys/Sandretto, "On survivor cryptocurrency momentum"; Host geblockt, Prozentzahl nicht primaer verifizierbar].

**Aufwand.** ~1 Personentag Code + ~10 min Download + ~1 h Rechnen. CPU-only.

### 4.2 WP-9 - DVOL-Backfill und Quellen-Kreuzvalidierung

**Ziel.** Aus 112 harvesteten DVOL-Tagen (F.1) ~1.980 machen und die Gleichwertigkeit der neuen Quelle **beweisen statt annehmen**.

**Datenquelle.** Deribit `/public/get_volatility_index_data`, Parameter `currency`, `start_timestamp`, `end_timestamp`, `resolution`; Antwort OHLC je Bucket [sek via Suchtreffer]. **DVOL-Historie ab ~2021-04-01** [sek: Amberdata-Doku; Deribit-eigene Doku nicht erreichbar]. < 20 Requests, Sekunden, ~4.000 Zeilen, < 1 MB. `resolution`-Werte und Punkte-Limit je Aufruf: **UNBELEGT - Probe-Pflicht** (ein Request klaert es auf der Nutzer-Maschine).

**Speicherdisziplin.** Eigener Speicher wie der WP-0-Bar-Cache (SCHEMA_VERSION, SHA-256-Sidecar, Manifest-Gate, Loud-Fail bei "Rohzeilen > 0, geparst = 0"). **Backfills schreiben NIE in den Harvest-Baum** (Schutzgut, read-only, CLI-Guard). Monatliche 1-%-Reverifikation wie WP-7.

**Materialitaet - hergeleitet aus der H-26-Gate-Arithmetik, mit vorgeschalteter Erreichbarkeitspruefung** (Review PRD3 B/W-4, L-1). Die v1-Schranke `3/250 = 0,012 Vol-Punkte` ist **gestrichen**: die 250 war ein aus DEC-32 uebernommenes Verhaeltnis fuer einen anderen Vergleich (interne Reproduzierbarkeit gegen einen eigenen Speicher), ihre Erreichbarkeit war ungeprueft, und der Ausgang "Quellen nicht austauschbar" war damit faktisch vorbestimmt - ein C-14-Wiedergaenger.

*Neue Herleitung.* Eine Quellenabweichung ist **material**, wenn sie das **90-Tage-Mittel der Praemie um >= 10 % der C-33-Schwelle von 3 Vol-Punkten, also um >= 0,3 Vol-Punkte**, verschieben kann. Zerlegt in die zwei Wege, auf denen sie das tun kann:

```
systematischer Anteil b = Mittel der Tagesdifferenzen (REST - Harvest)
    verschiebt das 90-Tage-Mittel um b            -> material ab |b| >= 0,30 Vol-Punkte
zufaelliger Anteil    s = SD der Tagesdifferenzen
    verschiebt das 90-Tage-Mittel um ~ s/sqrt(90) -> material ab s >= 0,30*sqrt(90) = 2,85 Vol-Punkte
```

*Erreichbarkeitspruefung ZUERST (L-1).* Bevor die Schranke angewendet wird, wird die **Verteilung der Tagesdifferenzen auf den 112 Ueberlappungstagen gemessen und berichtet** (Mittel, SD, Median, IQR, Anteil |Differenz| > 0,3), zusammen mit einer Kontrollrechnung an 10 Tagen, welche Abweichung allein die **Bucket-Konvention** (Bucket-Anfang vs. Bucket-Ende) erzeugt. Erst danach wird das Verdikt gesprochen.

**Binaerer Befund mit VORAB fixierter Konsequenz.**

| Befund | Vorab fixierte Konsequenz |
|---|---|
| **B1:** Historie reicht bis >= 2021-04 UND `|b| < 0,30` UND `s < 2,85` Vol-Punkte | Die **H-27-Klasse** (VRP auf REST-Backfill-Basis) wird als neue, eigens vorzuregistrierende Hypothese eroeffnet. |
| **B2:** Historie reicht, aber `|b| >= 0,30` oder `s >= 2,85` **und** die Konventions-Kontrollrechnung erklaert die Abweichung **nicht** | Die Quellen sind **nicht austauschbar**. Der Backfill traegt ausschliesslich eine eigene, getrennt registrierte Hypothese und wird **nie** mit Harvester-DVOL in einer Reihe gemischt. |
| **B2b:** Die Abweichung wird **durch die Bucket-Konvention erklaert** | Nicht "Quellen nicht austauschbar", sondern **konventionsbereinigt neu messen**; die Schranke wird auf die bereinigte Reihe angewendet. |
| **B3:** Historie reicht nicht zurueck | Der Fund ist wertlos, Aufwand ~1 h, kein Schaden. |

**In allen Faellen unveraendert bindend:** WP-9 **entsperrt H-26 NICHT** und erfuellt die C-33-12-Monats-Uhr **NICHT**. H-26 ist gegen `done_days` des Harvesters vorregistriert und bleibt es (R4 3.4, Review R1-R4 3.3, E.2/E.7).

**Definition of Done.** Backfill-Speicher gebaut und fingerprinted; Verteilungsbericht der 112 Tagesdifferenzen; Konventions-Kontrollrechnung; Befund B1/B2/B2b/B3; explizite Zeile "H-26 und C-33 bleiben unveraendert gesperrt"; T7-Artefakte (Differenzserie + Seed).

**Testpflichten.** *Positiv:* synthetische Antwort mit bekannten OHLC-Werten, exakt reproduziert. *Null:* leere Antwort und Antwort ohne die erwarteten Felder - beide muessen **laut scheitern** (C.14). *Adversarial:* Antwort mit korrektem Schema, aber **verschobener Zeitachse** (Bucket-Ende statt Bucket-Anfang) - der Vergleich MUSS das als Abweichung melden und die Konventions-Kontrollrechnung MUSS sie als solche identifizieren.

**Aufwand.** Sekunden Download, ~1 h Abgleich, ~2 h Code. Nutzer-PC.

### 4.3 WP-10 - Praemien-Kohaerenz (deskriptiv) und Maker-Fill-Schattenmessung

**Teil A - Kohaerenz der Praemien im Stress: DESKRIPTIV, kein PASS/FAIL** (Orchestrator-Entscheidung; Review PRD3 1.11/W-5). Die v1-Fassung machte den Befund an `rho_stress = 0,70` und `rho_ruhig = 0,45` fest - zwei **frei gesetzte** Zahlen ohne Quelle, die den N-Floor vollstaendig bestimmten (bei 0,80/0,40 waere er 27, bei 0,65/0,50 waere er 141). Beide sind **gestrichen**, und mit ihnen die Befundzweige A-B1/A-B2.

*Was WP-10(A) stattdessen liefert.* Die **Korrelationsmatrix der taeglichen Praemien-Proxy-PnLs** (Funding-Carry, Perp/Future-Wedge, Short-Skew, Short-Vol), getrennt fuer Stress-Episoden nach **`STRESS_ABS` (DEC-56)** - die absolute Liste, weil hier Liquiditaets-Crashs und nicht Vol-Regime die relevante Groesse sind - und Ruhephasen, jeweils mit **Bootstrap-CI**; Spearman-Standardfehler nach Bonett/Wright **`SE(z) = 1,06/sqrt(n-3)`** [sek] - der v1-Wert `1/sqrt(n-3)` galt fuer Pearson und unterschaetzt den SE. Bei der aus `STRESS_ABS` zu erwartenden kleinen Episodenzahl (Groessenordnung 6-10 ueber die urteilstragenden Fenster) ist `SE(z) = 1,06/sqrt(5) = 0,474`, das 95-%-CI auf `rho` also ueber weite Teile des Wertebereichs offen - **das ist der Befund und er wird so berichtet**, nicht in ein Gate gezwungen.

*Struktureller Nulleffekt (C.4).* Korrelationen steigen in Extremstichproben **mechanisch** (Selektion auf gemeinsame Groesse). Der Nulleffekt wird per Block-Bootstrap aus unkorrelierten Surrogaten mit identischer Randverteilung erzeugt, **nicht** mit 0 angesetzt.

*Die Konstante, die WP-10(A) an das Programm liefert.* Aus denselben Surrogaten wird der **Portfolio-Nulleffekt** gemessen: die empirische Verteilung des Sharpe einer Gleichgewichtung von `K` Rauschsignalen mit identischer Rand- und Korrelationsstruktur (R4 6.2a). Diese Verteilung ist die Schwellen-Basis eines spaeteren, getrennt zu registrierenden **Portfolio-Gates** - ohne sie waere jede Portfolio-Aussage ein DEC-31-Wiedergaenger in einer weiteren Metrik.

*Zusaetzlicher Deskriptor (Review R1-R4 6.7, zweite Haelfte - in v1 uebersehen).* Berichtet wird auch die Korrelation zwischen Praemien-PnL und der **Handlungsfaehigkeit des Betreibers** (Margin-Auslastungs-Proxy, ADL-Ereignisse, Auszahlungsstopp-Proxy). Nach Review 6.7 ist das die eigentlich relevante Groesse: die Frage ist nicht, ob zwei PnL-Reihen gemeinsam fallen, sondern ob sie fallen, waehrend man handlungsunfaehig ist.

*Wirkung auf die FDR-Struktur der Welle, vorab fixiert.* Solange die Kohaerenzfrage nur deskriptiv beantwortet ist - und das ist bei 6-10 Episoden der Dauerzustand - **kann nicht ausgeschlossen werden, dass F-PREM1, F-PREM2 und F-XSEC1 dieselbe Ertragsquelle messen.** Konsequenz, vorab fixiert: die Ueber-Familien-Korrektur wird in der **abhaengigkeitsrobusten** Form gefahren, nicht in der BH-Form, die Unabhaengigkeit unterstellt (Review R1-R4 6.7: die Kohaerenzmessung ist Vorbedingung fuer die Gueltigkeit der FDR-Struktur, nicht nur fuer eine Portfolio-Aussage).

**Teil B - Maker-Fill-Schattenmessung.** WP-4 hat gemessen, dass der Top-of-Book exakt ein Tick breit ist - aber nicht, mit welcher Wahrscheinlichkeit eine Order dort gefuellt wird und welchen Adverse-Selection-Abschlag der Fill traegt. Ohne diese Zahl ist jedes Maker-Kostenmodell im Options- und Hedge-Pfad eine Annahme (R1 0.4: Maker-Rehedging ist Existenzbedingung, nicht Optimierung).

*Was gemessen wird - eine KURVE, keine Schwelle* (Orchestrator-Entscheidung; Review PRD3 W-6). Die v1-Schwelle `p_fill(60s) >= 0,70` ist **gestrichen** (gesetzt, unhergeleitet). Gemessen wird die **Fill-Raten-Kurve** `p_fill(tau)` ueber ein Raster von Haltefristen; die Stuetzstellen **10 s und 60 s sind DESIGN-PARAMETER (keine Schwellen)** und werden ausdruecklich so etikettiert. Die Kurve wandert als **Konstante in das Kostenmodell** (`tradability3`), damit jedes spaetere Maker-Szenario mit einer gemessenen statt einer angenommenen Fill-Rate rechnet.

*Adverse Selektion - Schwelle mit Faktor 2 wie ueberall sonst.* Der Maker-Vorteil ist `FEE_TAKER - FEE_MAKER = 5,5 - 2,0 = **3,5 bp je Bein**` (B.3) - das ist der **Break-even**, an dem passive Ausfuehrung null Vorteil traegt. Da das Programm an jeder anderen Stelle den Faktor 2 ueber Break-even verlangt (R4 1.1c), gilt konsistent:

```
adv_sel_max = (FEE_TAKER - FEE_MAKER) / 2 = 3,5 / 2 = 1,75 bp je Bein
```

Die v1-Schwelle 3,5 bp lag exakt am Break-even und war damit inkonsistent zum Rest des Dokuments; R1s urspruengliche 1,5 bp waren zwar zufaellig nahe, aber falsch hergeleitet (Review R1-R4 2.8) - beides ist damit erledigt.

*Cluster-Einheit.* Kalendertag; zwei disjunkte REZENZ-konforme Halbjahre, ~180 Cluster je Fenster. Teil B ist damit gut gepowert.

*Positivkontroll-Vorschaltung (3.3.8, in v1 uebersehen).* Ein Ein-Pass-Replay dauert **86 min je Fenster** (WP-4-Erfahrungswert) und liegt damit ueber der 1-h-Grenze: **`positive_control.vorgeschaltet: true`**. Die Positivkontrolle (bekannte Fill-Sequenz auf einem synthetischen Buch) laeuft zuerst und allein; ihr PASS ist Vorbedingung der Einplanung.

**Datenquelle.** Vollstaendig aus dem Bestand, kein Nachladen: WP-0-Bar-Cache (10.054 Cache-Tage), `bybit/publicTrade` (lueckenlos ab 2020-03-25), `deribit/dvol` (112 Tage), `bybit/orderbook` L2 BTC/ETH (961/530 Tage) plus die gebaute, hash-gepinnte WP-2/WP-4-Replay-Maschinerie. Funding-Serie aus dem Backfill (V-1/A1).

**Definition of Done.** (A) Korrelationsmatrizen stress/ruhig mit Bootstrap-CI und `n_cluster`; Portfolio-Nulleffekt-Verteilung als Konstante abgelegt; Betreiber-Handlungsfaehigkeits-Deskriptor berichtet; ausdrueckliche Zeile "kein PASS/FAIL". (B) `p_fill(tau)`-Kurve mit CI; `adv_sel` je Fenster mit CI gegen 1,75 bp; Positivkontrolle vorab gruen; T2 (N>=3) gruen; T7-Artefakte; Nachweis, dass die WP-2/WP-4-Stores unberuehrt sind.

**Testpflichten.** (A) *Positiv:* vier synthetische PnL-Serien mit gemeinsamem Crash-Faktor - die Stress-Korrelation muss ausschlagen. *Null:* vier unabhaengige Serien mit identischen Randverteilungen inklusive fetter Tails - sie darf nicht ausschlagen. *Adversarial:* vier unabhaengige Serien, deren Stress-Auswahl auf der gemeinsamen Groesse erfolgt - der mechanische Anstieg muss vom echten getrennt werden. (B) *Positiv:* Buch mit hoher Queue-Rotation. *Null:* Buch ohne Fills. *Adversarial:* Buch, in dem der Touch **nur bei adverser Bewegung** geraeumt wird - `p_fill` hoch, `adv_sel` toedlich; die Messung muss den zweiten Fall trennen.

**Aufwand.** (A) Minuten Rechenzeit, ~0,5 Personentage Code. (B) 86 min je Fenster plus Positivkontrolle. CPU, kein GPU.

### 4.4 V-1 bis V-5 - fuenf 10-Minuten-Vorfragen

Alle laufen **auf der Nutzer-Maschine** (Egress-Sperre), sind oeffentlich und keyfrei, und **jede kann einen Kandidaten vorab toeten**.

| ID | Frage und Endpunkt | Vorab fixierte Konsequenz | Betroffen |
|---|---|---|---|
| **V-1** | **Tiefe von `/v5/market/funding/history` je Symbol.** `category=linear`, `symbol`, `startTime`+`endTime` (nur `startTime` allein ist ein Fehler), `limit` 1-200 Default 200 [sek: Bybit-Doku-Repo]. Probe: BTCUSDT rueckwaerts paginieren bis zur ersten leeren Antwort, dann Stichprobe ueber 20 Alt-Symbole. Zusaetzlich aus `instruments-info`: **ist der Zins-Term `I` und das Funding-Intervall ueber die Kontraktklassen identisch?** | Reicht die Historie fuer **< 117 Symbole** ueber beide Fenster: A1 in der Breitenform tot. Traegt `I` je Kontraktklasse verschiedene Werte: A1s Nulleffekt ist nicht 0, sondern `I_A - I_B`, und die Sortierung laeuft nur **innerhalb** einer Klasse (Review R1-R4 3.2). Der Zins-Term fuer 1h-Symbole ist **UNBELEGT** und Teil dieser Probe. | A1 |
| **V-2** | **`turnover24h` der datierten Bybit-Futures.** Ein `GET /v5/market/tickers`-Call je Kategorie; `contractType` `LinearFutures` (USDC-Futures, `BTC-24MAR23`) und `InverseFutures` (Quartale `BTCUSDH/M/U/Z<yy>`, live `BTCUSD_Q`/`BTCUSD_BIQ`) sind belegt [sek: Doku-Repo]. Zusaetzlich: liefert `/v5/market/kline` fuer ein bereits **verfallenes** Symbol noch Historie? | `turnover24h` des vordersten datierten Kontrakts **unter ~1 % des Perp-Umsatzes** (Design-Parameter, keine Schwelle; Konsequenz vorab fixiert): der Quote-Spread ist der bindende Kostenblock -> **A4 wird zum RECORDING-FIRST-Kandidaten**, nicht gestrichen. Keine durchgehende Quartalsleiter: `N_cluster >= 8` unerreichbar -> ebenfalls Recording-First. Keine Klines verfallener Symbole -> kein rueckblickendes Gate, Vertagung auf 12+ Monate Recording. | A4 |
| **V-3** | **Median(Ist-Funding - I).** Aus `bybit/rest.fundingRate` gegen `I = 0,01 %/8h = 3,0 bp/Tag = 10,95 % p.a.` (R1 0.2 [sek]). *Bewusste Abweichung von Vorlage und Review, die von "43 Harvest-Tagen" sprechen:* der Strom hat nach F.1 **113 Tage ab 2026-03-19** - die groessere Zahl wird verwendet und die Abweichung hier vermerkt. | Median nahe 0 (im Messrauschen): der mechanische Anker ist bestaetigt und A1s Kuerzungs-Argument (5.1) empirisch untermauert. Systematische Abweichung: die Anker-Herleitung ist fuer Bybit falsch und **jede** Funding-Rechnung wird neu aufgesetzt, bevor A1 registriert wird. **113 Tage schliessen die 10.10.2025-Episode aus - V-3 ist Plausibilitaets-, keine Stress-Aussage.** | A1, A4 |
| **V-4** | **Delivery-/Settlement-Gebuehr an der PRIMAERQUELLE**, Optionen UND datierte Futures. R1 traegt fuer Optionen `min(1,5 bp Index; 12,5 % des Intrinsic)`, nur bei ITM-Auto-Exercise, 2 bp fuer SOL/XRP/DOGE/MNT ein - **[sek], Primaerseite egress-blockiert**. R1-K-03 unterstellt fuer datierte Futures ein **gebuehrenfreies** Settlement - **ohne jede Quelle**. | R1s Zahl darf **nicht** nach `constants.py`; sie ist ausschliesslich zweiseitige Sensitivitaetsgrenze (Review R1-R4 3.4). Bleibt die Gebuehr ungemessen, **RAISED** jeder Halte-bis-Verfall-Pfad (Optionen) und jeder Settlement-Pfad (datierte Futures). | A4, A5, H-26b |
| **V-5** | **Effektgroessen-Beleg fuer die gewaehlte A2-Ereignismenge** (neu in v2). Zwei Teilfragen: (a) **Verfallskalender an der Primaerquelle**: fuehrt Deribit woechentliche Freitags-Verfaelle neben Monats- und Quartalsverfaellen, und seit wann? Die Behauptung ist bisher **UNBELEGT** und traegt den gesamten A2-P1-Befund. (b) **Gibt es eine bezifferte Effektgroesse fuer WOECHENTLICHE Verfaelle?** Die im Programm zitierten 16,5 bps (Ni/Pearson/Poteshman 2005 [sek]) und die Blasco-et-al.-Befunde (2023 [sek]) stammen aus **Monats**verfaellen mit hohem Open Interest. | Ohne belegte Effektgroesse fuer die registrierte Ereignismenge ist A2 ein **GL-012-Fall** (C.12) und **kein Alpha-Slot** - unabhaengig davon, wie gut die Datenlage ist. Ergibt (a), dass es keine woechentlichen Verfaelle gibt, faellt Variante (a) des A2-P1-Punktes ersatzlos weg und Placebo P1 lebt (5.2). | A2 |

**Ausgabeform.** Je Vorfrage ein Einzeiler (PowerShell/`curl`) plus eine Zeile Befund im Welle-1-Befunddokument, mit Zeitstempel und rohem Antwort-Ausschnitt als Beleg. Keine Interpretation ohne Rohbeleg (C.8).

---

## 5. Alpha-Kandidaten A1-A5 - REGISTRIERUNGS-ENTWUERFE

> **Statuszeile, fuer alle fuenf gueltig: NOCH NICHT REGISTRIERT.** Diese Abschnitte sind Entwuerfe im 3.0-Template (3.4). Die Registrierung erfolgt durch den Orchestrator nach Welle 1. Jede Schwelle, die "nach WP-7" heisst, ist bis dahin bewusst offen und wird aus einer gemessenen Groesse hergeleitet, nie gesetzt. **Jede Fenster-Regel-Zuordnung (C.10 hart vs. DEC-52) wird gerechnet, nicht behauptet, und einmalig VOR der Registrierung schriftlich festgestellt** (Review PRD3 B-5).

### 5.1 A1 - Querschnitts-Funding-Carry, perp-only (aus R2-K-02), Klasse P

**Hypothese.** Ein dollarneutrales Dezil-Long-Short-Portfolio auf Bybit-Linear-Perps, sortiert nach dem **intervall-normierten** Funding-Satz der letzten 3-7 Tage (long das niedrigste, short das hoechste Dezil), erzielt ueber eine Wochen-Halteperiode eine Gesamtrendite, die nicht vollstaendig durch die kompensierende Preisdrift aufgezehrt wird - und die auch nach Orthogonalisierung gegen Momentum und Reversal ein Residuum behaelt. **Richtung: positiv** (DEC-51 Punkt 1).

**Ertragsquelle: Praemie.** Der Funding-Satz ist eine explizite, mehrfach taeglich ausgezahlte Kompensation dafuer, die unbeliebte Seite eines Perp zu halten. **Zahler:** der gehebelte Long im Bullenmarkt (bzw. der gehebelte Short im Ausverkauf), der Sofort-Exposure ohne Kapitaleinsatz kauft. **Zahler-Bestand nach 2024 (3.3.9c):** Der Mechanismus ist gebuehren- und produktseitig unveraendert. Die in R2 zitierten Erosions-Indizien - "Basis- und Spread-Abweichungen fallen im Mittel ~11 % pro Jahr" und "der delta-neutrale Carry ist 2025 negativ geworden" - stehen dort als `[sek]` **ohne benennbare Sekundaerquelle** und werden hier deshalb als **UNBELEGT** gefuehrt (Review PRD3 6.6). Sie duerfen die Registrierung weder stuetzen noch toeten; die REZENZ-Klausel bleibt unabhaengig davon zwingend, weil sie aus C.18 folgt und nicht aus diesen Zitaten.

**Warum dieser Kandidat.** Er ist der einzige im Feld, bei dem Mechanismus, Zahler, Friktion (kein Spot-Bein) und ein **exakt ausrechenbarer** Nulleffekt gleichzeitig stimmen (Review R1-R4 5.1 Rang 2). Das Spot-Bein wegzulassen ist keine Kosmetik: Spot kostet **10 bp je Bein und ist nicht durch passive Ausfuehrung verbilligbar (Maker == Taker)** - 20 bp von 31 bp eines Spot/Perp-Round-Trips (R1 0.3). Jede Praemien-Struktur ohne Spot-Bein spart ~65 % ihrer Friktion.

**Struktureller Nulleffekt - vier Komponenten.**

*(a) Der Zinsanker `I` kuerzt sich im Querschnitt heraus.* Bybit rechnet `F = P + clamp(I - P, +/-0,05 %)`; `I` ist fuer Standard-USDT-Perps auf **0,03 %/Tag = 0,01 % je 8h** gesetzt [sek, R1 0.2]. Solange `|I - P| <= 0,05 %`, ist `F = P + (I - P) = I` **exakt** - der Erwartungswert der Funding-Rate ist mechanisch bei **+10,95 % p.a. = 3,0 bp/Tag** verankert, nicht bei 0. **Daran stirbt R1-K-01** (Spot/Perp-Form): dort ist `r_excess = (I - Kostendrift) - (I - r_USD) = r_USD - Kostendrift`; mit `r_USD = 0` - einer **Annahme**, die R1 als konservativ setzt und die dieselbe oekonomische Groesse betrifft wie `r_opp` in Par. 8.2, weshalb sie hier ausdruecklich als **Annahme** etikettiert und mit 8.2 verlinkt wird - und der 30-Tage-Drift 3,77 % p.a. ist `r_excess = -3,77 % p.a.`; die Schwelle +4,0 % haette >= 18,7 % p.a. Ist-Funding verlangt (Review R1-R4 2.1).
Im **Querschnitt** faellt `I` exakt heraus. Mit `F_k = I + d_k` (`d_k` = symbolspezifische Abweichung) ist die Funding-Zahlung des Portfolios

```
CF = mean_{j in Dezil_hoch}(F_j) - mean_{i in Dezil_niedrig}(F_i)
   = ( I + mean_hoch(d) ) - ( I + mean_niedrig(d) )
   = mean_hoch(d) - mean_niedrig(d)
```

`I` kuerzt sich **identisch heraus**, weil alle Standard-USDT-Perps **dasselbe** `I` tragen. Der Anker-Beitrag zum Nulleffekt ist **exakt 0** - vorbehaltlich der Verifikation, dass `I` und das Funding-Intervall ueber die einbezogenen Kontraktklassen identisch sind (**V-1**). Traegt eine Klasse ein anderes `I`, ist der Nulleffekt `I_A - I_B` und die Sortierung laeuft nur **innerhalb** einer Klasse. *Weder R1 noch R2 haben diesen Zusammenhang hergestellt.*

*(b) Funding-Intervall-Heterogenitaet (1h vs. 8h).* Bybit fuehrt Symbole mit 8h- UND 1h-Funding; bei Anschlag der Cap-Grenze springt die Frequenz auf stuendlich [sek, R1 0.2]. R1s Anker und R2s Record-Zahl (5,5 a x 3/Tag = 6.023) setzen ein konstantes 8h-Intervall voraus (Review R1-R4 2.9). **Ohne Normierung sortiert der Schluessel nach Abrechnungsfrequenz statt nach Rate** - ein 1h-Symbol mit gleichem Wert je Intervall zahlt 8-fach pro Tag. Verbindlich: `f_taeglich_i = funding_sum_i / n_Tage`, unter Verwendung der Pflichtspalte `funding_n` (WP-7). Der Zins-Term fuer 1h-Symbole ist **UNBELEGT - V-1**; solange er offen ist, laeuft A1 nur auf der homogenen 8h-Klasse und weist die ausgeschlossene Symbolmenge namentlich aus.

*(c) Die No-Arbitrage-Null.* Unter der Null ist der Funding-Cashflow exakt durch die Preisdrift kompensiert, die Gesamtrendite 0. **Urteilstragend ist die SUMME** aus Funding-Akkumulation und Preisbein, nie der Cashflow allein; die Zerlegung wird verpflichtend mitberichtet.

*(d) Die versteckte Reversal-Ladung.* Das Short-Bein sind per Konstruktion die Perps mit dem staerksten juengsten Preisanstieg (Funding korreliert mechanisch mit Momentum) - A1 ist ohne Orthogonalisierung ein **verstecktes Reversal-Portfolio**. **Urteilstragend ist das Residual-Alpha** nach Regression gegen die A3-Faktoren. Bleibt kein Residuum, ist A1 ein verpacktes A3 und wird nicht als eigener Kandidat gefuehrt.

**Daten.** `GET /v5/market/funding/history` [sek]: 5,5 a x 3/Tag = 6.023 Records = 31 Calls/Symbol; bei K~300 also **~9.300 Calls, bei 5 Req/s ~31 min** (die v1-Angabe "~15 min" war falsch, Review PRD3 W-13). Plus das `panel_1d` aus WP-7 fuer das Preisbein. Der Harvest-Bestand reicht nicht: `bybit/rest.fundingRate` hat 113 Tage ab 2026-03-19 und schliesst die 10.10.2025-Episode aus. Historische Tiefe je Symbol: **UNBELEGT - V-1**.

**Fenster (REZENZ, C.18).** W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-30, beide urteilstragend, je 52 Wochen; Historie vor 2024-07 ist Aera-Profil. **Stress-Abdeckung (`STRESS_REL`, DEC-55/DEC-56, 3.3.10):** die Fenster werden auf enthaltene Stress-Episoden geprueft und die Zahl berichtet; die Klausel ist nach DEC-56 (1) ein **Abdeckungs-Nachweis**, kein Filter.

**Metrik.** Nicht-ueberlappende Wochen-Gesamtrendite des Dezil-L/S-Portfolios in bps, zerlegt in Funding-Akkumulation und Preisbein; urteilstragend der Mittelwert der Summe sowie das Residual-Alpha nach (d).

**Power-Zeile (DEC-51: alpha 0,05 einseitig, Power 0,80, Richtung positiv).** Cluster-Einheit: **nicht-ueberlappende Kalenderwoche**; `N_eff` = 52 je Fenster, 104 gepoolt, korrigiert um die Autokorrelation ueber den stationaeren Bootstrap (Politis/Romano 1994; Blocklaenge nach Politis/White 2004 [sek]).

```
detektierbarer Mittelwert:
  C.10-Zweig  (W=52,  z=2,4865): 0,344886 * sigma_LS
  DEC-52-Zweig(W=104, z=3,1680): 0,310648 * sigma_LS
```

`sigma_LS` (Wochen-SD der Dezil-L/S-Rendite) ist ein **Nuisance-Parameter, kein Effekt**, und wird in WP-7 GEMESSEN; ebenso der **A-priori-Effekt `prem_prior`** (der gemessene Dezil-Funding-Spread je Woche). Beide sind heute **UNGEMESSEN - WP-7**.

**Fenster-Regel: EIN registriertes Design, eine vorab fixierte Zuordnungsregel** (Orchestrator-Entscheidung; Review PRD3 B-5). Registriert wird **C.10 hart als Default**. Die Ausnahme wird nach WP-7, **vor** der Registrierung und **vor** jedem Lauf, einmalig ausgewertet und schriftlich festgehalten:

```
P_fenster = Phi( prem_prior / (sigma_LS/sqrt(52)) - 1,6449 )
  P_fenster >= 0,60  ->  registriertes Regime: C.10 hart
  P_fenster <  0,60  ->  registriertes Regime: DEC-52 (i)-(iv), gepoolt bei alpha 0,01
  zusaetzlich: ist 3,1680 * sigma_LS/sqrt(104) > prem_prior  ->  GL-012-DROP, keine Registrierung
```

Das ist zulaessig, weil **WP-7 dem Kandidaten vorausgeht** und die Zahl damit nicht aus dem Lauf des Kandidaten stammt. Es gibt kein zweites Design im Text und keine Wahl nach dem Lauf.

**Oekonomisches Etikett (nicht bindend, C.2).** Setzt man als Referenzwert die oekonomische Mindestmagnitude ein - Wochenkosten bei Turnover 0,6 und 2x Brutto **18 bps**, Faktor 2 nach R4 1.1c also **36 bps/Woche** -, waere das Design nur fuer `sigma_LS <= 36/0,344886 = **104 bps/Woche**` (C.10-Zweig) bzw. `<= 36/0,310648 = **116 bps/Woche**` (DEC-52-Zweig) wirtschaftlich interessant. **Diese Zahlen sind Etikett, nicht Feasibility-Kriterium**; die Feasibility entscheidet sich an `prem_prior` (oben).

**Selektions-K.** `K = 3` (Lookback 3/5/7 Tage). Analytische Decke (R4 K-0.3) bei `sigma_SR = 1/sqrt(2)`, T = 2 Jahre: `0,7071*(0,4228*0,4307 + 0,5772*1,1614) = **0,60**`. Verbindlich ist die **am Null-Fixture gemessene** Decke (3.3.4).

**Schwelle.** Nach WP-7 hergeleitet als `mean_min = max( obere CI-Grenze des gemessenen Nulleffekts ; z * sigma_LS/sqrt(W) )` mit dem `z` des registrierten Fenster-Regimes; registriert als **Herleitungs-Referenz** (Pfad + Test-ID), nie als Skalar (DEC-58b).

**Gate-Text (woertlich).**

> **A1 gilt als kapitalfrei BESTANDEN, wenn:** (1) der Mittelwert der nicht-ueberlappenden Wochen-Gesamtrendite des Dezil-L/S-Portfolios die registrierte Schwelle nach dem **registrierten Fenster-Regime** erreicht (C.10 hart in beiden Fenstern, oder - falls die vorab ausgewertete Zuordnungsregel es ergeben hat - DEC-52 (ii) je Fenster plus gepoolte Signifikanz bei alpha 0,01); (2) das Ergebnis oberhalb der **am Null-Fixture gemessenen** Selektions-Decke fuer K = 3 liegt; (3) das **Residual-Alpha** nach Orthogonalisierung gegen Momentum und Reversal das Urteil traegt, nicht die Rohrendite; (4) die Funding-Buchhaltung intervall-normiert ist (`funding_n`) und die einbezogene Symbolmenge namentlich ausgewiesen ist; (5) die Cluster-Serie und die Bootstrap-Replikate bzw. Seed nach DEC-53 geschrieben sind - fehlen sie, ist der Lauf **KEIN VERDIKT**; (6) das Gate auf dem adversarialen Peso-Fixture nachweislich durchfaellt.
> **Ein PASS ist ein kapitalfreies WEITER und traegt verpflichtend das Etikett: "Praemien-EXISTENZ; die risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER." Kein Kapitalschritt folgt daraus.** Sharpe, MaxDD und Tail-Ratio werden mit hergeleiteten Rauschboeden BERICHTET und tragen kein Urteil.

**Entscheidungsrelevanz.** *Bei PASS:* genau ein Schritt - die getrennt zu registrierende Tradability-Pruefung **A1b** (symbolspezifische Slippage aus WP-7, Kapitalbindung 3.3.9a, Steuerbehandlung 8.2, Ausfuehrbarkeit 8.1). Kein Kapital, keine Order, kein Live-Code. *Bei DROP:* die Praemien-Klasse P ist auf Perp-Funding im Querschnitt erschoepft. *Oekonomische Mindestmagnitude (Etikett):* 36 bps/Woche.

**Etiketten.** `Klasse P`; `kapitalfrei`; `Praemien-EXISTENZ / Tradability PARK`; `Zahler-Erosion UNBELEGT`; `Steuerregime UNBELEGT (8.2)`; `Kapital-Multiplikator m UNGEMESSEN`; `r_USD = 0 ist eine Annahme (8.2)`.

**Feasibility-Kill-Bedingungen.** (1) WP-7-Befund B1 -> der Querschnitts-Arm faellt weg. (2) Die Zuordnungsregel oben ergibt GL-012-DROP. (3) V-1: Funding-Historie fuer < 117 Symbole ueber beide Fenster. (4) Die in WP-7 gemessene **Autokorrelation des Funding-Sortierschluessels ueber eine Woche** liegt unter **0,30** - **Design-Parameter (keine Schwelle)**, vorab fixierte Konsequenz: darunter ist der Sortierschluessel zum Handelszeitpunkt bereits verfallen und A1 misst eine andere Groesse als die Hypothese behauptet; die Registrierung unterbleibt, und der gemessene Wert wird berichtet. (5) Kein Residuum nach Orthogonalisierung.

**DEC-39-Fixtures.** *Positiv:* Panel, in dem der Funding-Cashflow zu 50 % nicht durch das Preisbein kompensiert wird. *Null:* Panel mit **exakter** Kompensation, das **8h- und 1h-Symbole nebeneinander enthaelt** - prueft die Funding-Buchhaltung und die Intervall-Normierung. *Adversarial (Peso):* Nullpraemie plus Merton-Spruenge (Rate 1/3 Jahre, -35 %); ein 5-Jahres-Fenster ist mit `p = e^-1,67 = 0,19` sprungfrei und zeigt dann eine scheinbar hochsignifikante Praemie - **das Gate MUSS durchfallen**.

**FDR.** `F-CARRY1` = die 3 Lookback-Varianten, BH alpha = 0,10; Ueber-Familie `F-PREM` in der **abhaengigkeitsrobusten** Form (Vorbehalt aus WP-10(A), 4.3).

**Bedingung aus Welle 1.** WP-7 (`SD_null`, `K`, `sigma_LS`, `prem_prior`, Funding-Autokorrelation, `PERP_SPREAD_BP`), V-1, V-3, WP-10.

### 5.2 A2 - EXP-CLOCK, Verfallskalender als Ereignistakt (aus R3-K-31), Klasse E

**Hypothese.** Im mechanisch erzwungenen Settlement-Fenster der Krypto-Options-Verfaelle (30-Minuten-Index-TWAP 07:30-08:00 UTC) tritt hedge-getriebener, preis-unelastischer Fluss konzentriert auf; das erzeugt eine gegen Placebos abgegrenzte Renditeverzerrung auf dem Bybit-Perp. **Richtung: wird mit der Ereignismenge zusammen registriert** (die Literatur beschreibt eine V-foermige Umkehr; das Vorzeichen von `r_pre` ist damit negativ zu registrieren, sobald V-5 die Ereignismenge festlegt).

**Ertragsquelle: Ereignis.** Options-Market-Maker sind im Aggregat netto short Gamma auf kurzlaufenden Kontrakten; ihr Delta-Hedge ist vor dem Verfall maximal preis-sensitiv und faellt um 08:00 UTC auf null. **Zahler:** Options-Halter/-Schreiber ueber den Vermoegenstransfer am Settlement und Liquiditaetsnehmer ueber den temporaeren Impact.
*Evidenz:* Ni/Pearson/Poteshman (2005, JFE 78(1)): Renditen optionierter Aktien an Verfallstagen im Mittel um **>= 16,5 bps** verzerrt - **Monats**verfaelle mit hohem Open Interest [sek, Volltext egress-gesperrt]. Blasco/Corredor/Satrustegui (2023, IREF 85): signifikante Aenderungen um Bitcoin-**Monats**verfaelle, nicht homogen ueber Boersen [sek, Groesse unbelegt]. Finance Research Letters (Juni 2026): V-foermige Umkehr um Deribit-Verfaelle, am staerksten bei negativem Netto-GEX [sek; **R3 vermerkt ausdruecklich: Autoren nicht ermittelbar, Volltext gesperrt** - dieser Vorbehalt gehoert zum Zitat]. *Gegen-Evidenz, die zitiert wird:* Max-Pain-"Pinning" ist empirisch mehrfach gescheitert; A2 misst die Umkehr, nicht einen Strike-Magneten.

**Genau EINE urteilstragende Statistik** (Orchestrator-Entscheidung; Review PRD3 W-1). Urteilstragend ist **`r_pre` = log-Rendite in `[07:30, 08:00)` UTC (30 min)**. `r_post` (`[08:00, 09:00)`, 60 min) wird **nur berichtet** und traegt kein Urteil; damit ist `K = 1` und die FDR-Familie besteht aus einem Test. Grund: bei `SD = 51 bps` (60-Minuten-Fenster) liegt die Per-Fenster-Power fuer `r_post` bei 0,51 und damit in einem anderen Fenster-Regime als `r_pre` - zwei Statistiken mit verschiedenen Regimen in einer Registrierung waeren ein offener Torpfosten.

**Die Volatilitaetskette, vollstaendig ausgeschrieben** (Review PRD3 W-2; in v1 fehlte sie):

```
BTC-Tagesvol 2,5 %  ->  Stunden-SD = 250 bps / sqrt(24) = 51 bps
                    ->  30-Minuten-SD = 51 / sqrt(2)    = 36 bps
```

Die 36 bps sind damit **BTC-only**. ETH wird gesondert gemessen; die in der Power-Zeile zu verwendende SD ist die **gepoolte** SD aus dem WP-0-Bar-Cache, nicht die BTC-Zahl. Ebenso wird **`rho(BTC, ETH)` auf 30-Minuten-Renditen in WP-7 GEMESSEN**; bis dahin gilt der Arbeitswert **0,8 `[sek: Review R1-R4 2.3, dort selbst ungemessen]`**, und jede damit gerechnete Zahl traegt diesen Vorbehalt.

**Cluster-Einheit.** Das **Verfallsereignis ueber beide Symbole** (BTC und ETH am selben Termin sind EIN Cluster) - DEC-51 Punkt 3. Bootstrap-Einheit ist der ganze Handelstag; N-Floor gilt fuer `N_cluster`.

**Placebo-Bindung.** Drei vorregistrierte Placebos: (P1) Nicht-Verfalls-Freitage im selben Uhrzeit-Fenster; (P2) **Nicht-Freitags-08:00-UTC-Slots** - zwingend, weil Bybits USDT-Perp-Funding um 00:00/08:00/16:00 UTC abgerechnet wird; ohne P2 misst A2 H-01 neu, und H-01 ist DROP; (P3) alle uebrigen Tagesstunden als unbedingte Baseline. **Bindend fuer die Rauschboden-Rechnung ist der Placebo mit dem GROESSTEN SE** (Orchestrator-Entscheidung) - das Gate verlangt Signifikanz gegen **alle** Placebos gleichzeitig, also entscheidet der ungenaueste.

**A2-P1: die beiden Ereignismengen nebeneinander, jede mit EIGENER Effektherleitung und EIGENEM Placebosatz** (Orchestrator-Entscheidung, Review PRD3 Abschnitt 4). Der v1-Vergleich hielt den Effekt ueber beide Varianten konstant und bevorzugte damit systematisch die breitere, verduennte Menge - der Mechanismus (Hedgebedarf proportional zum verfallenden Open Interest) skaliert mit dem OI des Termins.

| | **Variante (a): woechentliche Verfaelle** | **Variante (b): Monatsverfaelle (letzter Freitag)** |
|---|---|---|
| Ereignisse je Symbol/Fenster | 52 | 12 |
| `N_eff` (BTC+ETH = ein Cluster, rho 0,8 [sek]) | `52 * 2/(1+0,8) = 57,8` -> 58 | `12 * 1,111 = 13,3` |
| `SE(Ereignis) = 36/sqrt(N_eff)` | **4,73 bps** | **9,86 bps** |
| Placebosatz | P1 **faktisch leer** (nahezu jeder Freitag ist Verfallstag), also nur P2 und P3 | P1 **lebt** (~40 Nicht-Verfalls-Freitage je Fenster), plus P2, P3 |
| groesster Placebo-SE | P2: `36/sqrt(348) = 1,93 bps` | P1: `36/sqrt(44,4) = 5,40 bps` |
| `SE(Delta)` | `sqrt(4,73^2+1,93^2) = **5,11 bps**` | `sqrt(9,86^2+5,40^2) = **11,24 bps**` |
| belegte Effektgroesse fuer **diese** Menge | **KEINE - UNBELEGT, Vorfrage V-5** | **16,5 bps** [sek, Ni/Pearson/Poteshman 2005, Monatsverfaelle] |
| Per-Fenster-Power gegen die eigene Effektgroesse | nicht berechenbar (Effekt unbelegt); bei hypothetisch 12 bps: `Phi(12/5,11-1,6449) = 0,76` | `Phi(16,5/11,24 - 1,6449) = Phi(-0,177) = **0,43**` |
| Fenster-Regel nach DEC-52 (i) | bei 0,76: C.10 hart | bei 0,43: DEC-52-Zweig anwendbar |
| gepoolt (W=2 Fenster, `SE/sqrt(2)`, z=3,1680) | `3,1680 * 3,61 = 11,4 bps` detektierbar | `3,1680 * 7,95 = **25,2 bps** detektierbar` |
| Feasibility gegen die eigene Effektgroesse | offen bis V-5 | **VERFEHLT: 16,5 < 25,2** - gepoolte Power `Phi(16,5/7,95 - 2,3263) = 0,40` |

**Befund, der daraus folgt.** Variante (b) ist gegen ihre **eigene belegte** Effektgroesse ein **GL-012-Fall** - weder per Fenster (Power 0,43) noch gepoolt (Power 0,40) erreichbar. Variante (a) hat **ueberhaupt keine belegte Effektgroesse**; die in R3 registrierten 12 bps stammen aus dem monatsverfalls-basierten Aktien-Analogon und gehoeren damit zu R3s Literatur, nicht zu R3s Ereignismenge. **A2 ist bis zur Beantwortung von V-5 ein GL-012-Fall und kein Alpha-Slot; A2 verliert den in v1 behaupteten Status "fruehester laufbereiter Kandidat".**

**Die Schwelle: die zirkulaere Herleitung wird offengelegt** (Review PRD3 B-8). Die 12 bps stammen aus R3 und sind dort **gegen die Friktionswand** gewaehlt ("bewusst unter der 15-bps-Wand"), nicht aus einem Rauschboden hergeleitet; die Angabe "2,35 SE" ist die **Folge** dieser Wahl, nicht ihre Herleitung. Registriert wird stattdessen:

```
Schwelle = max( oberes 95-%-Quantil der gemessenen Placebo-Verteilung ; 2,4865 * SE(Delta) )
   Variante (a): 2,4865 * 5,11  = 12,7 bps
   Variante (b): 2,4865 * 11,24 = 28,0 bps
endgueltig gesetzt nach der Placebo-Messung, als Herleitungs-Referenz.
```

**Etiketten-Korrektur (Review PRD3 B-8).** 12 bps liegen **UEBER** der 11-bp-Taker-Round-Trip-Wand und **unter** der 15-bp-Gesamtwand - nicht unter beiden (so stand es faelschlich in v1) und nicht "zwischen 4 und 11 bps". Gegen die Maker-Wand (4 bp RT) liegen sie klar darueber. Das Pflicht-Etikett lautet daher: **"Der beste Fall liegt ueber der Taker-Gebuehrenwand (11 bp) und unter der Gesamtwand inkl. Slippage (~15 bp); eine Handelsperspektive besteht nur bei passiver Ausfuehrung, deren Fill-Rate WP-10(B) misst. Eine Tradability-Folge ist NICHT impliziert und NICHT registriert."**

**Struktureller Nulleffekt = die Placebo-Verteilung** (R4 1.3b): die gesamte Pipeline laeuft auf **Zufallsterminen mit identischer Kalenderverteilung** (gleiche Anzahl, Wochentags-, Tageszeit- und Cluster-Struktur), 1.000-fach; Mittelwert und Quantile sind der Nulleffekt.

**Gate-Text (woertlich).**

> **A2 gilt als kapitalfrei BESTANDEN, wenn:** (1) `|Delta(r_pre)|` die registrierte Schwelle in **beiden** urteilstragenden 12-Monats-Fenstern mit dem **registrierten Vorzeichen** erreicht, nach dem fuer die gewaehlte Ereignismenge vorab festgestellten Fenster-Regime; (2) `Delta` gegen **alle** vorregistrierten Placebos signifikant ist, wobei der Placebo mit dem groessten SE bindet, Block-Bootstrap p auf Kalender-Clustern; (3) `Delta` bestehen bleibt, nachdem BTC und ETH zu **einer** Teststatistik gepoolt wurden (L-7); (4) das **Negativ-Panel aus Realdaten** (XRP/BNB ohne liquide Optionskette) kein vergleichbares Delta zeigt; (5) die DEC-53-Artefakte geschrieben sind, sonst **KEIN VERDIKT**; (6) das Gate auf dem adversarialen Fixture (auf vergangenen Renditen selektierte Ereignisse auf einem Random Walk) durchfaellt.
> **Vorbedingung der Registrierung: V-5 belegt eine Effektgroesse fuer die gewaehlte Ereignismenge. Ohne diesen Beleg ist A2 ein GL-012-Fall und wird nicht registriert.**

**Fenster (REZENZ).** W1 = 2024-09-01..2025-08-31, W2 = 2025-09-01..2026-08-31; 2020-2024 ist Aera-Profil.

**Entscheidungsrelevanz.** *Bei PASS:* (i) der Ereignis-Mechanismus ist erstmals im Programm nachgewiesen und wird **Pflicht-Eingang in jede spaetere Halte-bis-Verfall-Rechnung** von A5 - R1s Options-Kandidaten settlen sonst systematisch in die Verzerrung hinein (Review R1-R4 3.5); (ii) **erst dann** darf ein Harvester-Auftrag fuer ein Options-Taker-Tape (R3-K-32/GEX) gestellt werden - vorher waere das eine Datenpipeline fuer den Term zweiter Ordnung eines unvalidierten Terms erster Ordnung (Review R1-R4 5.2 Punkt 1). *Bei DROP:* der Verfallskalender ist als Ereignistakt erledigt; K-32 entfaellt.

**Etiketten.** `Klasse E`; `kapitalfrei`; `Ereignismenge und Effektgroesse offen bis V-5`; `kein Nachladeaufwand`; `Negativ-Panel aus Realdaten`; `nur eine urteilstragende Statistik (r_pre); r_post ist Bericht`.

**Feasibility-Kill-Bedingungen.** (1) V-5 liefert keine belegte Effektgroesse -> GL-012, keine Registrierung. (2) P2 erklaert den Effekt vollstaendig -> es ist der Funding-Settlement-Takt und damit H-01, tot. (3) Vorzeichenwechsel zwischen W1 und W2 im geltenden Fenster-Regime. (4) `Delta` lebt nur im Aera-Profil vor 2024 (REZENZ, wie H-22). (5) Das Negativ-Panel zeigt denselben Effekt -> Wochentags-/Uhrzeit-Artefakt.

**DEC-39-Fixtures.** *Positiv:* injizierter CAR +50 bps an bekannten, stark geclusterten Terminen. *Null:* dieselben Termine ohne Effekt. *Adversarial:* Ereignisse, die auf **vergangenen Renditen** selektiert werden, auf einem Random Walk - erzeugt scheinbare Mean-Reversion, exakt die Fehlerklasse H-20; nach Placebo-Kalibrierung MUSS der Effekt verschwinden. *Zusaetzlich gratis aus Realdaten:* XRP/BNB (und SOL vor 2025) ohne liquide Optionskette - dort MUSS `Delta ~ 0` sein.

**FDR.** `F-EXPCLOCK` = **1 Test** (`r_pre`); Ueber-Familie `F-EVENT`. **Korrektur gegenueber R3:** R3 rechnete 8 Zellen (2 Symbole x 2 Fenster x 2 Fenstertypen). Panel-Mitglieder sind keine Hypothesen (L-7), die zwei Fenster sind die Zwei-Fenster-Regel, und `r_post` traegt kein Urteil mehr.

**Bedingung aus Welle 1.** **V-5** (zwingend), WP-7 (gemessenes `rho(BTC,ETH)` und gepoolte 30-Minuten-SD), DEC-55/DEC-56-Fixtures, Verifikation der Funding-Settlement-Zeiten (Teil von V-1).

### 5.3 A3 - Kohorte F-XSEC1: Momentum, Reversal, Vol-Anomalie (aus R2-K-01/K-04/K-05), Klasse W

**Status: streng konditional.** A3 wird nur registriert, wenn WP-7 den Befund **B2** liefert (statistische Testbarkeit). Andernfalls wird die Kohorte gestrichen und **nie auf N=5 zurueckskaliert**. **Richtung je Faktor registriert** (A3-M positiv, A3-R negativ auf der Formationsrendite, A3-V negativ auf dem Vol-Rang).

**Die drei Faktoren mit je eigener Ertragsquelle und Null.**

| Faktor | Ertragsquelle / Zahler | Struktureller Nulleffekt |
|---|---|---|
| **A3-M** Querschnitts-Momentum (Formation 1/2/4 Wochen, Halten 1 Woche) | Prognose; Zahler: der spaet einsteigende Momentum-Chaser und der aus einer Verlustposition getriebene Halter | Querschnitts-Permutation **innerhalb** jeder Woche, 1.000-fach, ganze Pipeline (R4 1.2b(1)) - identisch mit dem WP-7-Rauschbodenschaetzer; plus Vol-Drag-Differenz und Rebalancing-Effekt; plus Persistenz-Null (AR(1) unter der Null simulieren; Valkanov 2003 / BRW 2008 [sek]) |
| **A3-R** Kurzfrist-Reversal (Formation 1 Woche, Halten 1 Woche) | Praemie (Liquiditaetsbereitstellung); Zahler: der Fluss, der eine grosse Positionsaenderung durchdruecken muss, und der liquidierte gehebelte Halter | **Bid-Ask-Bounce** erzeugt auch ohne oekonomische Reversion einen positiven Reversal-IC. **Verbindlich: das Gap-Design (Formation und Halteperiode um einen Tag getrennt) ist die PRIMAERE Fassung**, nicht die Alternative - es eliminiert den Bounce strukturell, statt ihn zu schaetzen |
| **A3-V** Vol-/Beta-/MAX-Anomalie (Halten 1 Woche, vol-gewichtet) | Praemie (Lotterie-Nachfrage; die BAB-Hebelbeschraenkungs-Begruendung traegt in Krypto **nicht**, weil 25-100x Hebel verfuegbar sind) | **Vol-Drag:** `E[r_arith] - E[r_geom] = sigma^2/2`; bei sigma_taeglich 5 % vs. 2 % ist `(0,05^2-0,02^2)/2 = 0,105 %/Tag = **73,5 bps/Woche**` - groesser als jede erwartete Kante. Verbindlich: (i) vol-gewichtete Konstruktion, (ii) Rest-Drag vorab analytisch abgezogen, (iii) Permutations-Null auf **identisch vol-geschichteten** Zufallsportfolios |

**Vorbehalt zu A3-V.** Die urteilstragende Groesse ist ein **Residuum nach Abzug eines Terms, der groesser ist als es selbst** - schaetzfehler-dominiert. Die Registrierung weist **vor** dem Lauf das Verhaeltnis Nullterm/Erwartungseffekt aus und besteht einen Feasibility-Check, dass das Residuum in der beanspruchten Genauigkeit schaetzbar ist; sonst keine Registrierung.

**Daten.** Vollstaendig aus dem WP-7-`panel_1d`; Zusatzkosten null.

**Fenster.** W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-30 (REZENZ).

**Metrik.** Mittlerer wochentlicher Spearman-Rank-IC zwischen Charakteristik und Folgewochenrendite auf dem point-in-time-Universum; als Nicht-Trivialitaets-Anker die Dezil-L/S-Bruttorendite. **Nicht ueberlappend** (DEC-51 Punkt 5).

**Power-Zeile und Fenster-Regel - gerechnet, nicht behauptet** (Review PRD3 B-5). A-priori-Effekt `IC_prior = 0,03` [sek, R2 0.3C]; Cluster-Einheit Kalenderwoche; `SE = SD_null/sqrt(52)` mit dem in WP-7 **gemessenen** `SD_null`.

```
P_fenster = Phi( 0,03 / (SD_null/sqrt(52)) - 1,6449 )
Bestfall N_eff = K:  K=117 -> 0,75 | K=134 -> 0,80 | K=170 -> 0,88 | K=300 -> 0,98
```

Zum Vergleich die Rechnung mit den Arbeitswerten des Reviews (SE 0,0267 bei K=170, wahrer Effekt = oekonomisches Minimum 0,062): **0,72 (K=110) bis 0,78 (K=300)**. **Beide Rechenwege liegen ueber 0,60. DEC-52 (i) ist damit fuer A3 NICHT erfuellt: A3 laeuft unter C.10 hart.** Die Rechnung wird nach WP-7 mit dem gemessenen `SD_null` wiederholt und die Zuordnung vor der Registrierung schriftlich festgestellt; ergibt sie Power < 0,60, ist der DEC-52-Zweig zulaessig - die Entscheidung faellt an dieser Stelle, nie nach dem Lauf.

**Selektions-K.** `K = 7` (A3-M drei Formationslaengen, A3-R eine, A3-V drei Varianten). Analytische Decke bei T = 2 a: `0,7071*(0,4228*1,0676 + 0,5772*1,6207) = **0,98**`. Verbindlich ist die am Null-Fixture gemessene Decke.

**Schwelle.** `IC_min = 2,4865 * SD_null/sqrt(52)` - erst nach WP-7 gesetzt, aus dem gemessenen Rauschboden, nie als importierte Literaturzahl (D.2).

**Gate-Text (woertlich).**

> **Ein A3-Faktor gilt als kapitalfrei BESTANDEN, wenn:** (1) der mittlere Wochen-Rank-IC in **beiden** urteilstragenden Fenstern die registrierte Schwelle mit dem registrierten Vorzeichen erreicht (C.10 hart); (2) das Ergebnis oberhalb der **Querschnitts-Permutations-Null** (1.000 Permutationen innerhalb jeder Woche, vollstaendige Pipeline) UND oberhalb der **Persistenz-Null** (AR(1)-Simulation) liegt; (3) BH-FDR bei alpha = 0,10 innerhalb `F-XSEC1` bestanden, danach die Ueber-Familie in der abhaengigkeitsrobusten Form; (4) fuer A3-R zusaetzlich: der IC bleibt **im Gap-Design** erhalten UND ueberlebt den Ausschluss des untersten Liquiditaetsdezils - faellt er dort weg, ist der Befund eine Illiquiditaets-Artefakt-Messung und wird als solche etikettiert (H-16-Muster: Verdikt steht, Lesart eingeschraenkt); (5) fuer A3-V zusaetzlich: Spearman gegen die Size-/Volumen-Achse **< 0,60** - importierte Redundanzschwelle aus B.13/H-23, deren **Erreichbarkeit vor dem Lauf am tatsaechlichen Panel geprueft wird** (L-1); (6) die DEC-53-Artefakte geschrieben sind, sonst **KEIN VERDIKT**; (7) das Gate auf dem adversarialen Beta-Fixture durchfaellt.
> **Panel-Mitglieder sind Beobachtungen, keine Hypothesen: die K Symbole werden zu EINER Teststatistik gepoolt, nie als K Tests gezaehlt (L-7).**

**Entscheidungsrelevanz.** *Bei PASS eines Faktors:* getrennte Tradability-Registrierung mit **symbolspezifischer, gemessener Slippage** aus WP-7. *Bei DROP aller drei:* die Klasse W ist auf Bybit-Perps im Wochenhorizont erschoepft - das 2.0-Ergebnis (D.7) waere auf breiter Basis bestaetigt statt auf N=5. *Oekonomische Mindestmagnitude (Etikett):* `IC = 0,062` im Einzelpositionsrahmen bzw. `0,102` im Portfoliorahmen mit 18 bps Wochenkosten - **beide sind Etikett, keines ist PASS-Bedingung**. Wochenkosten: A3-M ~18 bps (Turnover 0,6), A3-R ~30 bps (Turnover ~1,0), A3-V ~4,5-7,5 bps (Turnover 0,15-0,25 - der friktionsfreundlichste Faktor, wegen Signalpersistenz, nicht wegen des Horizonts).

**Etiketten.** `Klasse W`; `kapitalfrei`; `C.10 hart (Power > 0,60)`; `zweistufige FDR, abhaengigkeitsrobust`; `A3-R: Bounce-Kontrolle urteilstragend`; `A3-V: schaetzfehler-dominiert`; `Alt-Symbol-Spread UNGEMESSEN bis WP-7`; ggf. `unter_wand` nach WP-7-Befund B4.

**Feasibility-Kill-Bedingungen.** (1) WP-7-Befund B1. (2) `K` unter dem fuer das gewaehlte Regime notwendigen Floor (134 bzw. 117). (3) Befund B3 (Survivorship nicht rekonstruierbar UND Fixture-Verzerrung >= halbe Schwelle). (4) A3-R: der Bounce-Abzug allein erklaert den IC. (5) A3-V: der Vol-Drag ueberschreitet die plausible Kante um mehr als Faktor 2 und laesst sich durch Vol-Gewichtung nicht unter ein Viertel druecken. **Nicht in dieser Liste: `sigma_xs`** - Befund B4 erzeugt ausschliesslich ein Etikett (C.2).

**DEC-39-Fixtures.** *Positiv:* Panel mit injiziertem Querschnitts-IC 0,06 inklusive gemeinsamem BTC-Beta-Faktor und Sektor-Bloecken. *Null:* Faktor innerhalb jeder Woche permutiert. *Adversarial:* ein Faktor, der **mechanisch mit dem Markt-Beta korreliert**, auf einem Panel mit dominantem Marktfaktor - in Krypto ist praktisch alles Beta zu BTC, und ein "Querschnitts"-Befund, der Markt-Timing ist, ist DIE Fehlerklasse dieser Familie. *A3-R-spezifisch:* Panel ohne Reversion, aber **mit** realistischem Bid-Ask-Bounce - das Gate darf nicht feuern. *A3-V-spezifisch:* Panel mit identischer Vol-Dispersion ohne jeden Zusammenhang.

**Nicht-Wiederholungs-Nachweis (C.1, woertlich in die Registrierung).** A3 wiederholt **nicht** D.7 (C-06/H-07/H-08): H-07 starb an `max|z| = sqrt(N-1) = 2,0 < 2,5` bei N=5; bei K=150 ist `max|z| = 12,2`. H-08 starb empirisch auf **demselben** 5-Symbol-Panel; das nachweislich neue Signal ist dreifach: (i) Breite K >= 117 statt N=5 - der Rauschboden faellt von `SD(IC) = 0,50` (N=5) auf den in WP-7 **gemessenen** Wert (Bestfall 0,077 bei K=170, also Faktor ~6,5; die in v1 zitierten "Faktor 44" stammten aus R2s `rho_quer = 0`-Rechnung und werden nicht uebernommen); (ii) Horizont Woche statt Stunden; (iii) explizite Bounce- bzw. Drag-Kontrolle, die in H-08 nicht existierte.

**FDR.** `F-XSEC1` = 7 Tests, BH alpha = 0,10; Ueber-Familie `F-WEEK`, darueber die Wellen-Ueber-Familie abhaengigkeitsrobust.

**Bedingung aus Welle 1.** WP-7 vollstaendig (Befund B2, `SD_null`, `K`, `sigma_xs`, `PERP_SPREAD_BP`, Survivorship-Fixture bestanden), WP-10 (FDR-Struktur).

### 5.4 A4 - Perp gegen datierten Bybit-Future (aus R1-K-03), Klasse P

**Hypothese.** Der realisierte **Wedge** `w` = (implizierter Terminzins des datierten Futures beim Einstieg) minus (ueber die Laufzeit akkumulierte Funding-Rate des Perps), annualisiert, ist ueber >= 8 vollstaendige Verfallzyklen systematisch von `w_null` verschieden. **Richtung: positiv.**

**Ertragsquelle: Praemie/Struktur.** Ein datierter Future preist einen **festen** Terminzins bis zum Verfall; ein Perp preist denselben Zins fortlaufend neu ueber Funding. **Zahler:** Marktteilnehmer, die Laufzeitsicherheit kaufen (Hedger, strukturierte Produkte). Keine Konvergenz-Wette - die Konvergenz ist am Verfall mechanisch garantiert.

**Warum nur Rang 4.** Die Headline "billigster Fall des Auftrags" (3 Fills statt 4; Taker 16,5 bp / Maker 6 bp) steht auf **zwei unbelegten, je einzeln toedlichen Annahmen**: (i) das Future-Bein settle gebuehrenfrei gegen den Index - genau die Kostenklasse, die E.6(a) fuer Optionen als blockierend fuehrt (Review R1-R4 3.4); (ii) die datierten Kontrakte seien liquide. Beide klaeren **V-2** und **V-4**.

**Daten.** Instrumente belegt vorhanden: `LinearFutures` (USDC, `BTC-24MAR23`) und `InverseFutures` (`BTCUSDH/M/U/Z<yy>`, live `BTCUSD_Q`, `BTCUSD_BIQ`) [sek: Doku-Repo]. Klines **verfallener** Symbole vermutlich nicht abfragbar - **UNBELEGT, Teil von V-2**. Belegbar rekonstruierbar: `/v5/market/delivery-price` (historische Settlement-Preise; "200 je Seite, Cursor-Paginierung" ist **[sek]** aus demselben Doku-Repo und nicht unabhaengig verifiziert) plus der `bybit/tickers`-Strom fuer aktuell gelistete datierte Kontrakte. **Vorab fixierte Konsequenz:** sind historische Klines nicht abrufbar, wird A4 ein **RECORDING-FIRST-Kandidat** wie H-21/H-26 (15-min-Sampler ueber `mark(Future)/mark(Perp)/index` je Verfall, ~10 MB/Monat, Gate-Lauf in 12+ Monaten).

**Fenster.** >= 8 vollstaendige Verfallzyklen (Quartale = 2 Jahre) ueber zwei disjunkte Haelften; REZENZ: die juengste Haelfte endet am Laufdatum. Stress-Abdeckung nach `STRESS_REL` (DEC-55/DEC-56) wird berichtet.

**Metrik.** `w` je Zyklus, annualisiert, gemessen gegen die **ex-ante-implizierte** Terminkurve (nicht gegen den Nachhinein-Mittelwert - ein positiver Ex-post-Mittelwert kann reine Jensen-Kruemmung sein).

**Struktureller Nulleffekt `w_null`.** Die **Margin-Bindungsdifferenz** zwischen beiden Beinen mal dem Opportunitaetszins, vorab aus den `instruments-info`-Margin-Parametern auszurechnen; die Bybit-Margin-Regeln sind **UNGEMESSEN** (eigener WP). Zweite Komponente: die Jensen-Kruemmung der Terminkurve.

**Power-Zeile.** Cluster-Einheit: **Verfallzyklus**; `N_cluster = 8` bei Quartalen ueber 2 Jahre. `detektierbar = 2,4865 * sigma_w/sqrt(8) = 0,879 * sigma_w`. `sigma_w` ist **UNGEMESSEN**; die Power-Zeile ist erst nach V-2 und einer ersten deskriptiven Messung ausfuellbar. **Bis dahin ist A4 nicht registrierbar** (C.12). Fenster-Regel: **C.10 hart als Default**; die Zuordnungsregel ist identisch zu A1 (Per-Fenster-Power gegen den registrierten A-priori-Effekt, ausgewertet einmalig vor der Registrierung). **Die v1-Regel "Vorzeichenkonsistenz in >= 6 von 8 Zyklen" ist gestrichen** - sie waere eine dritte, unhergeleitete Fenster-Regel neben C.10 und DEC-52 gewesen (Review PRD3 B-6).

**Schwelle - statistischer Rauschboden, nicht Kostenwand** (Orchestrator-Entscheidung; Review PRD3 2.1(i)/B-6). Die v1-PASS-Bedingung `w >= w_min = 0,49 % p.a. + m*r_opp` war **vollstaendig** eine oekonomische Groesse und damit ein C.2-Bruch - unter dieser Konstruktion waere H-04 ein DROP gewesen. Registriert wird stattdessen:

```
PASS-Bedingung (kapitalfreies Mess-Gate):
   w ist gegen w_null signifikant, Bootstrap-CI auf Zyklus-Clustern,
   mit registrierter Schwelle  w >= 2,4865 * sigma_w / sqrt(N_cluster),
   sobald sigma_w gemessen ist (Herleitungs-Referenz, kein Skalar).
```

Die oekonomische Groesse wandert vollstaendig in das Etikett und in das getrennt zu registrierende Tradability-Gate **A4b**:

```
w_min (ETIKETT, kein Gate) = 2 * Zyklus-Kosten + m * r_opp
   Zyklus-Kosten Maker = 6 bp je 90-Tage-Zyklus = 0,243 % p.a.
   Faktor 2 (R4 1.1c)                          = 0,487 % p.a.
   plus m * r_opp   (m UNGEMESSEN, r_opp UNBELEGT - Par. 8.2)
```

R1s gesetzte 2,0 % p.a. ("ich setze bewusst hoeher") bleiben abgelehnt: eine architect-gesetzte Gate-Schwelle verstoesst gegen C.19.

**Gate-Text (woertlich).**

> **A4 gilt als kapitalfrei BESTANDEN, wenn:** (1) `w` gegen den vorab ausgerechneten `w_null` signifikant ist, Bootstrap-CI auf Zyklus-Clustern, und die registrierte Rauschboden-Schwelle `2,4865*sigma_w/sqrt(N_cluster)` in beiden Haelften erreicht wird (C.10 hart, sofern die Zuordnungsregel nichts anderes ergibt); (2) `N_cluster >= 8` vollstaendige Verfallzyklen; (3) der Test gegen die **ex-ante-implizierte** Terminkurve laeuft; (4) die DEC-53-Artefakte geschrieben sind, sonst **KEIN VERDIKT**; (5) das Gate auf dem Peso-Fixture durchfaellt.
> **Solange V-4 die Settlement-Gebuehr des datierten Futures nicht an der Primaerquelle geklaert hat, RAISED der Settlement-Pfad (Loud-Fail, C.14) und A4 ist nicht laufbar.** `w_min` ist Etikett und Bestandteil des getrennt zu registrierenden A4b, nie der PASS-Bedingung.

**Entscheidungsrelevanz.** *Bei PASS:* A4 ist die **Entsperr-Bedingung von C-23** (PARK-Register: "Standalone-Verdrahtung + Nachweis Konvergenz > Friktion"); der alte Park-Grund ("2-Bein ~22 bps gegen < 0,08 % Konvergenz") war eine Rechnung auf kurzem Horizont - auf 90 Tagen kehrt sich die Arithmetik um (74 bp brutto gegen 6-16,5 bp, R1 0.3). *Bei DROP:* der Wedge ist erledigt; Klasse P reduziert sich auf A1 und den gesperrten Options-Block. *Oekonomische Mindestmagnitude (Etikett):* `0,49 % p.a. + m*r_opp`.

**Etiketten.** `Klasse P`; `kapitalfrei`; `moeglicherweise RECORDING-FIRST (V-2)`; `Settlement-Gebuehr UNBELEGT bis V-4 -> RAISE`; `m UNGEMESSEN`; `r_opp UNBELEGT (8.2)`; `Kapitalbindung ueber 90 Tage ist die eigentliche Kostenstelle`.

**Feasibility-Kill-Bedingungen.** (1) V-2: keine durchgehende Quartalsleiter -> `N_cluster >= 8` unerreichbar -> Recording-First. (2) V-2: Klines verfallener Symbole nicht abrufbar -> kein rueckblickendes Gate -> Recording-First. (3) `sigma_w` so gross, dass `2,4865*sigma_w/sqrt(8)` groesser ist als jede plausible Wedge-Groesse -> GL-012-DROP. (4) `w_null` nicht von `w` trennbar. **Nicht in dieser Liste: Liquiditaet unter 1 % des Perp-Umsatzes** - das ist eine Tradability-Information und fuehrt zu Recording-First plus Etikett, nicht zu einem Mess-DROP (C.2).

**DEC-39-Fixtures.** *Positiv:* synthetische Terminkurve mit konstantem +3-%-p.a.-Aufschlag ueber den simulierten Funding-Pfad. *Null:* Terminkurve, die exakt dem Erwartungswert des Funding-Pfads entspricht, mit zufaelliger Realisation - das Gate muss `w ~ 0` finden und die Realisationsstreuung **nicht** als Praemie lesen. *Adversarial (Peso):* wie A1, plus ein Szenario, in dem alle 8 Zyklen in eine Contango-Phase fallen.

**FDR.** `F-PREM1` gemeinsam mit A1; Ueber-Familie `F-PREM`.

**Bedingung aus Welle 1.** V-2 und V-4, plus die Margin-Regel-Verifikation (eigener WP, nicht Teil von Welle 1).

### 5.5 A5 - Skew-Praemie (25d-Risk-Reversal) und Options-Block (aus R1-K-04), Klasse P, GESPERRT

**Status: GESPERRT.** Die Reihenfolge aus E.6 ist bindend: (a) Delivery-/Exercise-Gebuehr an der Primaerquelle verifiziert (**V-4**), UND (b) ein Options-Spread-Zensus mit durchgaengiger Bybit-Aufzeichnung liegt vor, UND (c) **H-26 selbst ist gemessen**. Wer die Reihenfolge umdreht, setzt die Schwelle nach dem Sehen der Zahl. **Hinweis (Review PRD3 W-15):** Bedingung (b) setzt faktisch die **tagesgenaue Ketten-Luecken-Karte (R3-K-37 Stufe 1)** voraus, die dem Programm komplett fehlt - siehe 9.1.

**Hypothese.** Wer den 25-Delta-Put verkauft und den 25-Delta-Call kauft (delta-gehedgt auf dem USDT-Perp, 7-21 DTE, Halten bis Verfall), wird fuer das Tragen der Crash-Asymmetrie bezahlt. **Richtung: positiv.**

**Ertragsquelle: Praemie.** Krypto-Halter kaufen systematisch Abwaertsschutz; Optimisten kaufen Aufwaerts-Hebel billiger auf Perps. **Zahler:** der Hedger. **Abgrenzung zu H-26/C-33:** die VRP ist das **Niveau** (IV vs. RV), die Skew-Praemie die **Schiefe**; ein Risk Reversal ist bei symmetrischen Deltas naeherungsweise vega-neutral - er handelt genau das, was die VRP-Messung herauskuerzt.

**Daten.** `deribit/tickers` ~38 Tage, `deribit/markprice.options` 43 Tage, Bybit-Options-Ticker im `tickers`-Strom (F.1). **Das reicht fuer kein urteilstragendes Fenster.** Ein durchgaengiger Bybit-Quote-Datensatz existiert nicht (E.9).

**Schwelle - der Punkt, der jetzt schon feststeht.** R1 kalibriert `1,5 Vol-Punkte` gegen die **C-33-Schwelle** von 3 Vol-Punkten - aber C-33 wurde fuer das Vol-**NIVEAU** einer Einzeloption definiert; ein importierter Massstab fuer eine andere Groesse ist die D.2-Fehlerklasse. **Verbindlich: die Schwelle wird aus der GEMESSENEN Skew-Verteilung hergeleitet**, mit GL-012-Vorabcheck (Median-25d-Skew auf den verfuegbaren Tagen), nie aus C-33.

**Gemessener Kostenrahmen** (B.4-B.8, DEC-44/45): Options-Maker 2 bp / Taker 3 bp **des Index** je Fill; `vega/S` 5,28 (BTC) / 5,10 (ETH) bp Index je Vol-Punkt; volle Quote-Breite im Bein-Band 0,14 / 0,26 Vol-Punkte. Abgeleitet (R1 0.1): 1 Maker-Fill = 0,379 / 0,392 Vol-Punkte, 1 Taker-Fill 0,568 / 0,588, 1 Delivery (nur ITM) 0,284 / 0,294. **Delta-Hedge-Kasse (R1 0.4):** ein Risk Reversal hat weitgehend aufhebende Gammas, Rest ~0,2 Vol-Punkte plus statischer Hedge 1,04 (Taker) bzw. 0,38 (Maker) ueber 14 Tage. **Maker-Rehedging ist Existenzbedingung, keine Optimierung** - genau das misst WP-10(B).

**Pflicht-Eingang aus A2** (Review R1-R4 3.5). A5 haelt bis zum Verfall und wird am **30-Minuten-Settlement-TWAP** abgerechnet - exakt im Fenster, in dem A2 eine hedge-getriebene Verzerrung vermutet. Wenn A2 recht hat, settlen A5s Positionen **systematisch in die Verzerrung hinein**; das A2-Ergebnis ist Pflicht-Eingang in jede Halte-bis-Verfall-Kostenrechnung.

**Feasibility-Kill-Bedingungen.** (1) V-4 klaert die Delivery-Gebuehr nicht -> Halte-bis-Verfall-Pfad RAISED, A5 bleibt gesperrt. (2) GL-012-Vorabcheck zeigt einen Median-25d-Skew unter dem hergeleiteten Rauschboden -> struktureller DROP ohne Datenlauf. (3) H-26 liefert kein Verdikt -> Reihenfolge nicht erfuellt.

**Entscheidungsrelevanz.** *Bei PASS (fruehestens 2027):* der erste Options-Praemien-Pfad mit tragbarer Hedge-Kasse. *Bei DROP:* zusammen mit den bereits toten R1-K-05/K-06 waere die verallgemeinerbare Programm-Lehre bestaetigt, dass **jede Bybit-Options-Struktur, deren Nutzen eine Greek-DIFFERENZ ist, gebuehren-strukturell benachteiligt ist.**

**Etiketten.** `Klasse P`; `GESPERRT (E.6-Reihenfolge)`; `Schwelle aus gemessener Skew-Verteilung, nicht aus C-33`; `Delivery-Gebuehr UNBELEGT -> RAISE`; `A2-Ergebnis ist Pflicht-Eingang`; `setzt R3-K-37 Stufe 1 voraus`.

**FDR.** `F-PREM2`; Ueber-Familie `F-PREM`.

**Bedingung aus Welle 1.** V-4; im Uebrigen nicht Welle 1, sondern die E.6-Reihenfolge.

---

## 6. Tradability 3.0 - das Kostenmodell-Modul

**Grundsatz.** Das Kostenmodell ist ein **Mess-Artefakt, kein Parametersatz**. Jede Konstante ist entweder (a) gemessen und eingefroren, (b) ungemessen und dann als **zweiseitige Pflicht-Sensitivitaet** ausgewiesen, oder (c) ungemessen und dann ein **harter Abbruch** (Loud-Fail, C.14). **Stille Defaults sind verboten** - sie waeren die Torpfosten-Verschiebung, die DEC-13/16 verhindern soll.

**Umfangs-Entscheidung** (Entwurf 3.0; Review R1-R4 5.2 Nachruecker). R4 schlaegt ein `tradability3/`-Modul mit sieben Dateien vor - **bevor** ein einziger 3.0-Kandidat ein Verdikt hat, und mit **vier von sieben Modulen auf UNGEMESSENEN Konstanten** (Impact-`k`, Margin-Regeln, Delivery-Gebuehr, Alt-Spreads). Das ist die Methodik-Variante der S4/S5-Falle (D.16). **Gebaut werden jetzt nur die beiden Dateien, die pinnen, was gemessen IST; alles andere ist ein Stub mit `raise NotImplementedError`** - was zugleich der Loud-Fail-Doktrin entspricht.

> **DEC-59 (Entwurf) - Kostenkonstanten-Modul und `constants_hash`.** `tradability3/constants.py` und `tradability3/report.py` werden gebaut; die uebrigen fuenf Module bleiben RAISE-Stubs, bis die jeweils bindende Konstante gemessen ist. Jede Konstanten-Ersetzung ist eine eigene DEC, **bevor** ein Kandidat davon profitiert (Review R1-R4 3.6). Nummer 59, weil DEC-54..DEC-57 im Log bereits belegt und beschlossen sind und DEC-58 das Registry-Format traegt (3.4).

`src/bybit_edge/research/tradability3/`

| Datei | Status | Inhalt bzw. Abbruchgrund |
|---|---|---|
| `constants.py` | **BAUEN** | Gemessene Programm-Konstanten mit Quellen-Tag und Unit-Test-Pin: `FEE_MAKER = 2,0 bp`, `FEE_TAKER = 5,5 bp` je Bein (DEC-42/WP-4); `FEE_OPTION_MAKER_OF_INDEX = 2 bp`, `FEE_OPTION_TAKER_OF_INDEX = 3 bp` (DEC-45); `VEGA_OVER_S = {BTC: 5,28, ETH: 5,10}` bp Index je Vol-Punkt (WP-5/DEC-44); `PERP_TOB_SPREAD_BP = {BTC: 0,0157, ETH: 0,0537}` (WP-4/DEC-42); `OPT_QUOTE_WIDTH_VOLPTS` je (DTE-Bucket, \|Delta\|-Bucket) aus WP-5; `STRESS_EPISODE_STATS` aus WP-6; **`STRESS_REL` und `STRESS_ABS` nach DEC-55/DEC-56**; **`FILL_RATE_CURVE` aus WP-10(B)**, sobald gemessen. Plus `assert_constants_unmodified()` und `constants_hash()` (SHA-256 ueber die Datei). |
| `report.py` | **BAUEN** | `CostReport`-Dataclass, die JEDES Tradability-Gate emittiert: `fee_bp, spread_bp, impact_bp_k0, impact_bp_k1, funding_bp, delivery_bp, total_bp_k0, total_bp_k1, capital_multiplier, fill_rate, adv_sel_bp, regime, constants_hash`. Damit vergleicht ein Gate-Auditor Gleiches mit Gleichem. |
| `perp.py` | **RAISE-STUB** | Braucht `PERP_SPREAD_BP` je Symbol-Dezil fuer das breite Universum - **UNGEMESSEN bis WP-7 (Befund B5)**. Alle gemessenen Kostenkonstanten stammen von BTC/ETH-Majors; ohne den Zensus ist jede Broad-Universe-Tradability-Aussage wertlos (R4 2.5). |
| `impact.py` | **RAISE-STUB** | Funktionalform Wurzelgesetz `k * sqrt(notional/ADV) * daily_vol_bp` belegt (Almgren et al. 2005 [sek]); **`k` fuer Bybit UNKALIBRIERT**. Faellt der Stub spaeter, gilt: jedes Ergebnis wird bei `k=0` (optimistisch) UND `k=1` (realistisch) berichtet - **nie ein Einzelwert**. |
| `option.py` | **RAISE-STUB** | `delivery_fee_of_index` hat Default `None`; jeder Halte-bis-Verfall-Pfad ohne gesetzten Wert **RAISED**. Die Delivery-/Exercise-Gebuehr ist die einzige bindende, noch ungemessene Options-Kostenkomponente (E.6a) und trifft ausgerechnet das beste DEC-45-Szenario. **Vorfrage V-4.** R1s Sekundaerzahl `min(1,5 bp Index; 12,5 % Intrinsic)` darf **nicht** in `constants.py`, sondern ausschliesslich als zweiseitige Sensitivitaetsgrenze auftreten. |
| `funding.py` | **RAISE-STUB** | Braucht das Funding-Panel mit `funding_n` (WP-7) und die Intervall-Klaerung (V-1); ohne beides addiert es 8h- und 1h-Symbole zusammen. |
| `capital.py` | **RAISE-STUB** | **Bybit-Margin-Regeln sind fuer dieses Programm UNGEMESSEN.** Eine echte Kapital-Aussage braucht einen eigenen WP (Regel-Verifikation). Bis dahin: Kapital-Multiplikator `m` **nur** in einer zweiseitigen Sensitivitaet, nie als stiller Default. |
| `episode.py` | **RAISE-STUB** | Stress-Overlay setzt die DEC-55/DEC-56-Fixtures voraus und rechnet Liquiditaets-Szenarien auf `STRESS_ABS`. **Zwangsregel beim Bau:** eine Strategie, deren Einstieg AUF ein Schock-Signal hin erfolgt, wird per Konstruktion in Stress-Minuten bepreist - daran ist reaktives Long-Vol gestorben (WP-6/DEC-47/48). |

**Einheiten-Bruecke.** Perp-Kosten in bp des **Notionals**; Options-Kosten in bp des **Index** (nicht des Notionals - DEC-45) und ueber `VEGA_OVER_S` in **Vol-Punkten**. Beide Einheiten werden gefuehrt, ihre Umrechnung per Unit-Test gepinnt (5,28/5,10 sind skalen-invariant trotz 31-fach unterschiedlichem Basiswert-Niveau, WP-5).

**Anti-Gaming-Bindung.** `constants_hash` im `CostReport` ist der SHA-256 ueber `constants.py`. **Ein Tradability-Lauf, dessen Hash nicht dem in der Registrierung zitierten entspricht, ist kein gueltiger Lauf** (Teststufe T5). Das macht C.3 maschinell pruefbar.

**Klarstellung zur Wand** (Review PRD3 W-8). **15 bps ist die Gesamtwand** (11 bp Gebuehr + ~4 bp Slippage), nicht eine "Majors-Slippage-Konstante". Woertlich aus Review R1-R4 1-R3-K-35: eine Spread-/Slippage-Messung **korrigiert die Konstante um hoechstens ~27 % und kann sie nie unter 11 bps Taker druecken.** Jede Erwartung, ein Spread-Zensus koenne die Wand wesentlich senken, ist damit vorab widerlegt; der Zensus dient der **symbolspezifischen Differenzierung**, nicht der Absenkung.

---

## 7. Daten- und Rechenplan

### 7.1 Einmal-Backfill im Scinance-Repo (nicht im Harvester)

Kriterium: alles **beliebig Nachladbare** gehoert in einen einmaligen Backfill, nicht in einen Dauerstrom. **Backfills schreiben NIE in den Harvest-Baum** (Schutzgut, read-only, per CLI-Guard erzwungen); sie gehen in einen eigenen Speicher unter derselben Disziplin wie der WP-0-Bar-Cache.

**Rate-Limit-Arithmetik, korrigiert** (Review PRD3 W-13; v1 rechnete hier zweimal falsch). Das belegte Public-Limit ist **600 Requests je 5 s je IP = 120 Req/s** [sek: Bybit-Rate-Limit-Doku via Suchtreffer]. Die Selbst-Drossel von **5 Req/s** ist damit **4,2 % des Limits** (nicht 0,4 %) - immer noch sehr sicher, aber die Aussage "extrem sicher" wird auf "sicher, Faktor 24 Reserve" praezisiert.

| Backfill | Endpunkt | Requests | Zeit @ 5 Req/s | Volumen | Zweck |
|---|---|---|---|---|---|
| **1d-Klines, gesamtes Universum** | `/v5/market/kline?interval=D` | ~3.000 | **10 min** | 1,7 Mio Zeilen, 40-80 MB | WP-7 |
| **Funding-Historie, K~300 Symbole** | `/v5/market/funding/history` | ~9.300 | **31 min** | ~2 Mio Zeilen, ~25 MB | A1 (v1 nannte faelschlich "~15 min") |
| **Deribit DVOL 1d, BTC+ETH** | `/public/get_volatility_index_data` | < 20 | Sekunden | ~4.000 Zeilen, < 1 MB | WP-9 |
| **Summe Welle 1** | | **~12.300** | **~41 min** | **~110 MB** | |
| Funding-Historie, gesamtes Universum (~1.500 Symbole) | dito | ~25.500 | 1,4 h | ~60 MB | erst nach bestandener Feasibility (R4 3.2) |
| 1h-Klines, gesamtes Universum | `/v5/market/kline?interval=60` | ~40.500 | 2,3 h | 0,6-1,2 GB | **NICHT in Welle 1** (Review R1-R4 5.2 Punkt 2) |
| 1m-Klines, gesamtes Universum | - | ~4,7 Mio | **260 h** | ~100 GB | **NIE**: der Horizont liegt nach K-0.1 ohnehin unter der Wand (D.16) |

**Provenienz-Regel fuer REST-Backfills - gilt fuer JEDEN neuen Speicher** (Review R1-R4 6.9; in v1 nur bei WP-7 ausgefuehrt). Der Harvest-Baum ist lokal und unveraenderlich; ein REST-Backfill nicht - Boersen revidieren historische Klines gelegentlich. Deshalb: ein geplanter Job zieht **monatlich eine 1-%-Zufallsstichprobe** eingefrorener Partitionen neu und vergleicht die Fingerprints. **Abweichung ist ein lautes Alarm-Ereignis, kein stilles Ueberschreiben.** Das gilt ausdruecklich fuer das `panel_1d` (WP-7), fuer den **Funding-Backfill** (an dem A1 und A4 haengen) und fuer den **DVOL-Backfill** (WP-9).

### 7.2 Was in den Harvester gehoert - nur Irreversibles

Kriterium: **Irreversibilitaet** (Anti-Data-Lake, PRD 2.0 Par. 9; Pflichtzeile 3.3.7).

1. **Taegliches Point-in-Time-Instrument-Roster** (`instruments-info` je Kategorie, 1-3 Requests/Tag, wenige hundert kB). **Hoechste Prioritaet.** Einzige Verteidigung gegen Survivorship, **grundsaetzlich nicht nachholbar**; jeder Tag ohne Lauf ist unwiederbringlich verloren.
2. **Universums-Ticker-Panel** (`tickers` je Kategorie, 15-min-Takt) - Spread, OI, Funding-Rate, Turnover fuer alle Symbole. **Zuerst die Inhaltsprobe auf den bereits existierenden `bybit/tickers`-Strom** (C.8, WP-7); ist er ausreichend, wird nichts Neues gesammelt. Volumen bei getrimmten Spalten ~2,5-5 GB/Jahr.
3. **Open Interest** nur, falls die Tiefen-Probe eine flache Historie zeigt - dann irreversibel. Die OI-Tiefe ist **UNBELEGT** und der kritischste offene Datenpunkt (R4 3.1).
4. **Beizubehalten:** Deribit `dvol`, `markprice.options`, `tickers`; Bybit-Options-Ticker.
5. **NICHT in den Harvester:** Klines und Funding-Historie jeder Aufloesung - beliebig nachladbar, also ein Dauerstrom ohne Gegenwert.

### 7.3 Rechenbudget - CPU-first

Die gesamte 3.0-Methodik der Klassen P, W und E ist **CPU-Arbeit in Minuten** (R4 4.1). Der 82-GB-RAM-Rechner ist grosszuegig dimensioniert, nicht knapp.

| Aufgabe | Groesse | Laufzeit |
|---|---|---|
| Faktorberechnung auf dem Daily-Panel | 1.500 Sym x 2.190 Kalendertage = 3,3 Mio Zeilen | Sekunden (numpy/polars) |
| Querschnitts-IC + 1.000 Permutationen je Woche (WP-7-Rauschboden) | 250 Wochen x bis 1.500 Sym x 1.000 | < 1 min |
| Stationaerer Block-Bootstrap, 10.000 Replikate, 200 Varianten | | Minuten |
| Placebo-Verteilung Ereignis-Studie, 1.000 Laeufe | | Minuten |
| L2-Replay je Fenster (WP-10 Teil B) | | **86 min** (WP-4-Erfahrungswert) - ueber 1 h, daher Positivkontroll-Vorschaltung (3.3.8) |
| Welle-1-Backfill gesamt | | **~41 min**, netz- nicht CPU-gebunden |

**Zwei Historienlaengen, einmal benannt** (Review PRD3 K-7): **2.008** ist die Zahl der Handelstage in 5,5 Jahren (Grundlage der Kline-Call-Arithmetik); **2.190** ist das Kalendertags-Partitionsraster ueber 6 Jahre im `panel_1d`-Schema. Beide sind korrekt und bezeichnen Verschiedenes.

**GPU: 0** (3.7). Keine der Metriken (IC, Praemie, CAR, Bootstrap, Permutation, FDR) ist GPU-gebunden. **Nicht machbar auf diesem PC und deshalb nicht geplant:** L2-Buchrekonstruktion oder Tick-Analysen ueber ein breites Universum (die Daten existieren nicht - L2 nur BTC/ETH, `publicTrade` nur 5 Symbole), Minutenbars fuer das gesamte Universum, ein zweiter gleichzeitiger Grosslauf (ein Betreiber, eine Maschine; die knappe Ressource ist **Kalenderzeit**, nicht FLOPS).

---

## 8. Offene Nutzer-Entscheidungen

> Diese drei Punkte kann nur der Nutzer entscheiden. **Das PRD ist unter dem Orchestrator-Default (b) bei 8.1 vollstaendig** - er aendert heute keinen Code und keine Regel. 8.2 und 8.3 blockieren keinen Welle-1-Schritt.

### 8.1 Ausfuehrungsfrage - der Verfassungswiderspruch (Review R1-R4 6.4)

**Der Widerspruch.** Der beste Kandidat (A1) ist ein woechentlicher Dezil-Long-Short ueber 100-300 Perps: ~60 Positionen, **~30-60 Orders je Woche**. Fuer einen Einzelbetreiber manuell unrealistisch - und **"kein Live-Order-Code" ist Verfassung**. Damit ist die billigste zu MESSENDE Klasse die teuerste zu BETREIBENDE, und das Programm hat sich ihre Ausfuehrung selbst verboten.

| Option | Inhalt | Preis |
|---|---|---|
| (a) | Verfassung bleibt, 3.0 bleibt reines Messprogramm; A1 wird gemessen, aber nie betrieben | Ehrlich, aber der Pfad vom WEITER zum ersten Euro bleibt undefiniert (Review R1-R4 6.8) |
| **(b) - DEFAULT** | Eine spaetere, **getrennt gegatete Ausfuehrungs-Spur** wird als Phase vorgesehen, die erst nach Mess-PASS **und** Tradability-PASS **und** expliziter Nutzer-Freigabe gebaut wird | Aendert heute keinen Code und keine Regel; haelt die Option offen, ohne sie einzuloesen |
| (c) | Kandidaten werden auf "manuell betreibbar" (wenige Positionen) eingeschraenkt | Streicht die Klasse W praktisch - und damit A1 und A3 |

**Umsetzung unter Default (b), verbindlich.** Die Ausfuehrungs-Spur wird als **Phase 4** benannt und bleibt bis zur ausdruecklichen Freigabe leer. Kein Welle-1-Paket, kein Kandidaten-Entwurf und keine Verfassungsregel dieses PRD haengt an ihr. Die Entscheidungsrelevanz-Zeilen in Par. 5 nennen deshalb ausnahmslos nur den naechsten **Mess-** oder **Tradability-**Schritt, nie einen Kapitalschritt.

### 8.2 Kapitalbasis, Steuerregime und der Opportunitaetszins

Benoetigt werden: (i) die **Groessenordnung des einsetzbaren Kapitals**; (ii) die **steuerliche Behandlung** von Funding-Ertraegen und Options-Praemien in der Jurisdiktion des Nutzers; (iii) der **Opportunitaetszins `r_opp`** auf gebundenes Kapital.

**Warum das nicht kosmetisch ist** (Review R1-R4 6.2): Spot- und Derivate-Bein einer delta-neutralen Position werden steuerlich unterschiedlich behandelt; eine steuerlich asymmetrische Konstruktion kann bei einer Bruttokante von 5-10 % p.a. den Grossteil des Ertrags kosten.

**Die eine Groesse, zwei Behandlungen - hier zusammengefuehrt** (Review PRD3 W-16). `r_opp` ist offen, waehrend A1s Nulleffekt-Herleitung `r_USD = 0` verwendet. Das ist **dieselbe oekonomische Groesse**. Festlegung fuer v2: **`r_USD = 0` ist eine ausdrueckliche, konservative ANNAHME** (sie macht R1-K-01s Nulleffekt maximal ungueltig und ist damit gegen den eigenen Kandidaten gerichtet), sie ist in 5.1 als solche etikettiert und **hier verlinkt**; sobald der Nutzer `r_opp` benennt, wird derselbe Wert an beiden Stellen verwendet, und A4s `w_min`-Etikett wird numerisch bestimmbar.

**Wirkung auf dieses PRD:** keine Blockade. Bis zur Antwort tragen alle Praemien-Entwuerfe die Zeile **"Steuerregime UNBELEGT - Par. 8.2"**, und **keine** "netto"-Aussage wird ohne diesen Vorbehalt gefuehrt.

### 8.3 Sunset-Review der Recording-Engine F0

Faellig seit ~2026-09-11 laut PRD 2.0 Par. 9, **nie gelaufen**. Die Engine schreibt Stroeme, die kein Treiber liest (DEC-43); mindestens ein Ziel ist anderweitig abgedeckt (DEC-46).
**Empfehlung des Orchestrators:** Review planmaessig durchfuehren; danach **nur behalten, was eine registrierte 3.0-Hypothese namentlich braucht**. Nicht pauschal abschalten - die Anti-Data-Lake-Regel steht im PRD, sie wurde nur nie vollzogen.
**Wirkung:** keine Blockade. Zu beachten ist die Wechselwirkung mit 7.2: das **Point-in-Time-Roster ist irreversibel** und muss laufen, unabhaengig vom Ausgang der Review.

---

## 9. Anhang

### 9.1 Kandidaten und Vorschlaege, die NICHT aufgenommen wurden

| Kandidat / Vorschlag | Grund (ein Satz) | Referenz |
|---|---|---|
| **R1-K-01** Funding-Carry Spot/Perp | Stirbt am eigenen Nulleffekt: `r_excess = r_USD - Kostendrift`, mit der Annahme `r_USD = 0` also **-3,77 % p.a.**; die Schwelle +4,0 % verlangte real >= 18,7 % p.a. Ist-Funding. | Review R1-R4 2.1, 3.2 |
| **R1-K-02** Intra-Venue-Funding-Spread | Groessenordnung vollstaendig unbelegt - kein Kandidat, sondern eine Vorfrage (in V-1 aufgegangen). | Review R1-R4 1-R1-K-02 |
| **R1-K-05** Kalender-/Forward-Vol-Praemie | Gebuehren-strukturell tot: 2,51 Vol-Punkte Netto-Vega-Kosten gegen eine Forward-Vol-Praemie ohne jede Evidenz; erforderlich waeren >= 5,0 Vol-Punkte. | Review R1-R4 1-R1-K-05 |
| **R1-K-06** ETH-vs-BTC-Relative-Vol | ~3,9 Vol-Punkte Maker-Kosten gegen einen Praemienanteil, den der Autor selbst auf < 2 Vol-Punkte schaetzt; der Dispersions-Mechanismus existiert in dieser Marktstruktur nicht. | Review R1-R4 1-R1-K-06 |
| **R2-K-03** Time-Series-Momentum (Portfolio-Sharpe-Form) | Eigene Power-Rechnung: SR 2,80 je 12-Monats-Fenster noetig, bester unabhaengiger Literaturwert 1,6. Die Driscoll-Kraay-Panel-Form ist eine ANDERE Hypothese und braucht zuerst die Persistenz-Null. | Review R1-R4 1-R2-K-03 |
| **R2-K-06** Kalender-Interaktion | Nachweisgrenze unter REZENZ: 33 bps/Tag bei n~104 Wochenendtagen je Fenster; die Session-Achse ist inhaltlich **kein** Kalendereffekt (die einzige zitierte Evidenz ist ein FLUSS-Signal) und muesste umbenannt werden. | Review R1-R4 1-R2-K-06 |
| **R2-K-07** Vol-Targeting | Nie eigenstaendiger Kandidat; nur als **vorab fixierte Variante** eines bestehenden Kandidaten zulaessig, mit gemessener (nicht angenommener) Geschenk-Verteilung. | Review R1-R4 1-R2-K-07 |
| **R3-K-32** GEX-KOND | S4/S5-Falle: verlangt einen neuen Harvester-Strom plus Warten bis ~2027-05 - eine Datenpipeline fuer den Term zweiter Ordnung eines unvalidierten Terms erster Ordnung. **Kein Options-Tape-Auftrag vor einem A2-PASS.** | Review R1-R4 5.2 Punkt 1 |
| **R3-K-33** X-PULL **Stufe 2** | Der eigene A-priori (Median 1-3 bps) impliziert, dass der N-Floor reisst, und die auftretenden Ereignisse fallen per Konstruktion in Kaskadenminuten, in denen die 15-bps-Annahme nachweislich falsch ist. | Review R1-R4 1-R3-K-33 |
| **R3-K-33 Stufe 1** (billiger binaerer Zensus) | **Bewusst vertagt, nicht verworfen** (Review PRD3 W-15). Er ist billig, aber "billig ist kein Registrierungsgrund" (DEC-38); Welle 1 ist bereits durch WP-7/WP-9/WP-10 und fuenf Vorfragen belegt. **Vertagungsbegruendung:** er beantwortet keine Vorbedingung eines Welle-1-Kandidaten. Neubewertung nach WP-7. | Review R1-R4 1-R3-K-33; DEC-38 |
| **R3-K-34** LEV-STATE | Einziger R3-Kandidat **ohne hergeleiteten Rauschboden**; poolt zusaetzlich 5 Symbole zu "~180 Dezil-Tagen", obwohl der Hebelzustand an denselben Kalendertagen auftritt (effektiv ~40). | Review R1-R4 1-R3-K-34, 2.5 |
| **R3-K-35** SLIP-ZENSUS | Nachrangig: nur ~2,5 Monate rezenz-konforme `orderbook.1000` und nur BTC/ETH - kann die Frage, die die Klasse W blockiert (Alt-Symbol-Slippage), **prinzipiell nicht** beantworten; WP-7 laeuft zuerst. | Review R1-R4 1-R3-K-35, 3.6 |
| **R3-K-36** VRP-KOND (Terzil-Gate) | Faellt an der eigenen Power-Rechnung: `SE(Terzil-Differenz) ~ 4,1` Vol-Punkte gegen eine 3-Punkte-Schwelle = **0,73 SE**; beide angebotenen Auswege sind verboten. Der **Datenfund** ist als WP-9 uebernommen. | Review R1-R4 1-R3-K-36, 3.3 |
| **R3-K-37** SKEW-VORLAEUFER **Stufe 2** | Rauschboden aus 60 **ueberlappenden** Tagesbeobachtungen hergeleitet; effektives N ~6, Rauschboden ~0,41 - die 0,25-Schwelle ist strukturell unerreichbar. | Review R1-R4 1-R3-K-37, 2.4 |
| **R3-K-37 Stufe 1** (tagesgenaue Ketten-Luecken-Karte) | **Vertagt mit ausdruecklicher Begruendung, aber als naechstes Options-Paket vorgemerkt** (Review PRD3 W-15). Der Review R1-R4 verlangt sie "sofort - sie fehlt dem Programm komplett und wird von jedem Options-Kandidaten gebraucht"; **A5s Sperrbedingung (b) setzt sie faktisch voraus** (5.5). Sie steht **nicht** in Welle 1, weil der gesamte Options-Block hinter H-26 gesperrt ist (E.6) und Welle 1 keine Vorbedingung eines gesperrten Kandidaten baut. **Vorab fixiert: sie wird gebaut, sobald H-26 ein Verdikt hat oder V-4 die Gebuehrenfrage klaert - je nachdem, was zuerst eintritt.** | Review R1-R4 1-R3-K-37; Review PRD3 W-15 |
| **R4** oekonomische Mindestmagnitude in der PASS-Bedingung | Bricht C.2: unter dieser Regel waere H-04 ein DROP gewesen und die Information "gerichtete Information existiert" geloescht. Verschoben in Entscheidungsrelevanz + Tradability. | Review R1-R4 4.5 |
| **R4** harte 24-h-GPU-Wall-Clock-Kappe | Importierte Schwelle ohne Herleitung (warum 24 und nicht 12 oder 72?) und redundant; ersetzt durch die Positivkontroll-Vorschaltung. | Review R1-R4 4.4 |
| **R1** `SR_block >= 0,60` und `TR <= 250 Tage` als Gates | Ein Gate mit ~50 % Power je Fenster; die Tail-Ratio bestraft strukturell kleine Praemien. Beide zu Deskriptoren degradiert. | Review R1-R4 3.7, 3.8 |
| **R4** `tradability3/` in voller Sieben-Datei-Form | Vier von sieben Modulen stehen auf ungemessenen Konstanten, vorgeschlagen bevor ein Kandidat ein Verdikt hat; nur `constants.py` und `report.py` werden gebaut. | Review R1-R4 5.2 Nachruecker |
| **Migration der 2.0-Registry** | Sie ist append-only und urteilstragend; sie nachtraeglich anzufassen waere ein schwererer Fehler als jeder Komfortgewinn. | Review R1-R4 4.3; R4 5.3/7 |
| **v1: paarweiser `rho_quer`-Schaetzer** | Wegen `sum_i e_{i,t} = 0` bei gleichen Varianzen **identisch `-1/(K-1)` fuer jede Datenlage**, bei ungleichen Varianzen ein Vol-Heterogenitaets-Artefakt (+0,045 bei wahrer Korrelation null) - er kann die gesuchte Groesse nicht enthalten. Ersatzlos gestrichen, ersetzt durch die direkte Messung von `SD_null(IC_t)`. | Review PRD3 B-1; v2 Par. 4.1 |
| **v1: `rho_stress = 0,70` / `rho_ruhig = 0,45` und der N-Floor 46/51** | Zwei frei gesetzte Zahlen ohne Quelle, die den Floor vollstaendig bestimmten (bei 0,80/0,40 waere er 27, bei 0,65/0,50 waere er 141). WP-10(A) ist jetzt deskriptiv ohne PASS/FAIL. | Review PRD3 1.11, W-5 |
| **v1: `p_fill(60s) >= 0,70` als Schwelle** | Gesetzt und unhergeleitet; ersetzt durch die gemessene Fill-Raten-**Kurve** als Kostenmodell-Konstante, mit 10 s / 60 s als etikettierten Design-Parametern. | Review PRD3 W-6 |
| **v1: WP-9-Materialitaet `3/250 = 0,012 Vol-Punkte`** | Importiertes DEC-32-Verhaeltnis fuer einen anderen Vergleich, Erreichbarkeit ungeprueft, Ausgang faktisch vorbestimmt - ein C-14-Wiedergaenger. Ersetzt durch die H-26-Gate-Herleitung mit vorgeschalteter Erreichbarkeitspruefung. | Review PRD3 1.14, W-4 |
| **v1: `sigma_xs < 500` mit Streichungsoption; Alt-Spread-Faktor `3x`; A4 "6 von 8"** | Gesetzte Skalare bzw. - im Fall der Streichungsoption und der Fenster-Regel - C.2- und Torpfosten-Probleme. Ersetzt durch eine Formel (`sigma_xs_min`), gestrichen (`3x`), gestrichen (`6 von 8`). | Review PRD3 3, B-6, W-7 |

### 9.2 Programm-Konstanten-Tabelle

**A - Gemessene Programm-Konstanten aus 2.0** (Kompendium B; ohne Neuherleitung zitierbar).

| # | Groesse | Wert | Quelle |
|---|---|---|---|
| B.1 | Round-Trip-Friktionswand | **11 bps** (Taker), **~15 bps** inkl. Slippage | verdict.md Par. 2, FINAL_PRD Par. 1 |
| B.2 | Perp-Top-of-Book-Spread | **exakt ein Tick**: BTC 0,0157 bp (RECENT) / 0,0196 (2024Q1), ETH 0,0537 bp; Dispersion p90-p10 nur 0,8-2,7 % des Medians | WP-4, DEC-42 |
| B.3 | Perp-Gebuehren | `FEE_MAKER` = **2,0 bp/Bein** (4,0 bp RT), `FEE_TAKER` = **5,5 bp/Bein** (11 bp RT); Maker-Vorteil = **3,5 bp/Bein** | DEC-42, WP-4 |
| B.4 | Options-Gebuehren (auf den **Index**) | Maker **2 bp**, Taker **3 bp**; kein Rabatt aktiv | DEC-45 |
| B.5 | `vega/S` | **5,28** bp Index je Vol-Punkt (BTC), **5,10** (ETH); skalen-invariant, per Unit-Test gepinnt | WP-5, DEC-44 |
| B.6 | Options-Quote-Breite (7-14 DTE, \|Delta\| 0,15-0,30) | voll **0,14** Vol-Punkte (BTC) / **0,26** (ETH) | WP-5, DEC-44 |
| B.7 | Break-even gegen die C-33-Schwelle (3 Vol-Punkte) | passiv + Halten bis Verfall frisst 25 %/26 %; Taker-RT frisst 85 %/96 % | DEC-45 |
| B.8 | Options-Quote-Breite im Stress (19.08.2026) | haelt in **97-99 %** der Minuten; Verbreiterung episodisch (BTC 0,66 %, ETH 2,82 % der Minuten) | WP-6, DEC-47/48 |
| B.9 | Dressing-Artefakt (CRPSS gegen Dirac) | **0,21-0,29** theoretisch, 26,3-30,3 % empirisch | GL-022/GL-024 |
| B.10 | AnEn schlaegt gedresste HAR nicht | 0 von 4 Zellen, kein p unter 0,29 | GL-024 |
| B.11 | Querschnitts-z-Deckel | `max\|z\| = sqrt(N-1)`; bei N=5 also **2,0** | GL-012 |
| B.12 | Zeit-Irreversibilitaets-Signatur | AUC bis 0,7353, aber 85-106 % des Ueberschusses aus dem Aktivitaets-Envelope | GL-015-Nachtrag, DEC-30 |
| B.13 | Venue-Fingerprint / Redundanzschwelle | gepoolt 0,8944/0,8914; Redundanzschwelle **Spearman 0,6** (Erreichbarkeit je Anwendung zu pruefen, L-1) | GL-019, GL-031 |
| B.14 | Minuten-Fluss-Impact | gleichzeitiger IC ~+0,53..+0,61, Forward-IC30 ~-0,011..-0,022, ueber zehn Halbjahre stabil | H-24 |
| B.15 | Numerischer Rauschboden des Lesepfads | **3,8e-9** relative Lauf-zu-Lauf-Streuung | DEC-32/34 |
| B.16 | Datenreichweite | `bybit/publicTrade` lueckenlos ab 2020-03-25 (BTC) / 2021-06-29 (SOL/BNB), 5 Symbole, 5-6 Jahre | DATA_INVENTORY 2026-08-10 |
| B.17 | Hardware | RTX 5060 Ti (16 GB), CUDA 12.8+, 82 GB RAM, Windows; **Sandbox ohne torch/GPU und mit Egress-Sperre** | INFRA_OPS_MAP, F.3 |

**B - Neue Programm-Konstanten aus R4 K-0.1 bis K-0.7** (hergeleitet, vom Gate-Audit nachgerechnet und bestaetigt).

| # | Groesse | Wert | Herleitung |
|---|---|---|---|
| K-0.1 | Horizont-Friktions-Kurve | `edge_h = (2p-1)*0,798*sigma_h`; BTC `sigma_1d = 262 bp`. **Perfektes 1-s-Orakel: 0,71 bp.** Mindesthorizont gegen 11 bp bei p=0,55: **6,6 h**; gegen 4 bp (Maker): **53 min**; bei Wochen-IC 0,05: **2,7 Tage** (Taker) / **7 h** (Maker) | `E\|r_h\| = 0,798*sigma_h` bei Normalitaet |
| K-0.2 | Sharpe-Nachweisdauer (Lo 2002 [sek]) | exakt `T_min = 2,4865^2*(1+SR^2/(2q))/SR^2`; **Kurzform `6,18/SR^2` ist eine Naeherung und zu optimistisch** (SR 2,0: 1,80 statt 1,55 a). SR 1,0 -> 6,19 a; SR 0,5 -> **24,7 a**; mit Schiefe g3=-2, Exzess-Kurtosis 10 (monatlicher SR 0,2887) Faktor 1,827 -> **11,3 a** | R4 K-0.2 plus Korrekturterm |
| K-0.3 | Selektions-Decke (Bailey/Lopez de Prado [sek]) | `E[max SR]` ueber K Varianten bei T=5 a: K=5 -> 0,53; K=20 -> 0,85; K=50 -> **1,02**; K=100 -> 1,13 | `sigma_SR*((1-g)*Phi^-1(1-1/K)+g*Phi^-1(1-1/(Ke)))`, g=0,5772 |
| K-0.4 | MaxDD-Boden | `E[MaxDD] = 1,2533*sigma_ann*sqrt(T)`; sigma 20 %, T=5 a -> **56 %** | Magdon-Ismail et al. 2004 [sek] |
| K-0.5 | IC-Rauschboden und Breiten-Decke | `SD(IC_t) ~ 1/sqrt(N_eff-1)`; N=5: detektierbar **0,098**. **Die Breite hilft nur bis zur Decke `N_eff`; in 3.0 wird `SD(IC_t)` DIREKT gemessen statt ueber eine Korrelation geschaetzt** (v2 Par. 4.1) | R4 K-0.5 plus v2-Schaetzerwechsel |
| K-0.6 | Kosten des harten Ein-Fenster-DROP | `P(beide bestehen) = (1-beta)^2`: Power 0,8 -> 0,64; **Power 0,5 -> 0,25**; Power 0,35 -> 0,12. Vorzeichen-Konsistenz bei t=1,4: 0,845 gegen 0,18 - **Faktor 4,7** | Binomialarithmetik, Phi(1,4)=0,919 |
| K-0.7 | GPU-Bilanz 2.0 | ~**350 GPU-Stunden** (309-357), Ertrag 2 kapitalfreie WEITER, **0 registrierte Tradability-Folgen** | INFRA_OPS_MAP 6, E.10 |

**C - In diesem PRD hergeleitete bzw. korrigierte Groessen.**

| Groesse | Wert | Ort |
|---|---|---|
| DEC-51-Konstanten | einseitig `z = 1,6449+0,8416 = **2,4865**`; zweiseitig `1,9600+0,8416 = **2,8016**`; einseitig bei alpha 0,01 `2,3263+0,8416 = **3,1680**` | 3.3.1 |
| **Dezil-Spreadfaktor** | exakt `2*E[z \| oberstes Dezil] = **3,51**`, nicht 2,0; R2 ist um Faktor **1,75 zu pessimistisch**. Hiermit dokumentiert, damit die Korrektur nie als Kantenverbesserung verkauft wird | L-18; Review R1-R4 2.7 |
| WP-7-Feasibility-Schranken (`IC_prior = 0,03`) | `SD_null <= **0,08699**` (per Fenster) bzw. `<= **0,09657**` (gepoolt, alpha 0,01) | 4.1 |
| Notwendige Breite | `K >= **134**` (per Fenster) bzw. `K >= **109**` (gepoolt); Orchestrator-Floor `K_min = **117**` ist notwendig, nicht hinreichend | 4.1 |
| `sigma_xs_min` | Formel `2*Kosten/(f*IC_prior)`: **342 bps/Woche** (f=3,51) bzw. **600 bps/Woche** (f=2,0); die v1-Zahl 500 war gesetzt und entfaellt | 4.1 |
| A1-Feasibility (Etikett) | `sigma_LS <= **104** bps/Woche` (C.10-Zweig) bzw. `<= **116**` (DEC-52-Zweig, z=3,1680); v1s 148 war mit falschem alpha gerechnet | 5.1; Review PRD3 B-4 |
| A1-Selektions-Decke (K=3, T=2 a) | **0,60** | 5.1 |
| A2-Vol-Kette | Tagesvol 2,5 % -> Stunden-SD **51 bps** -> 30-Minuten-SD **36 bps** (BTC-only; gepoolte SD aus WP-7) | 5.2 |
| A2 Variante (a) woechentlich | `N_eff = 57,8`; `SE(Ereignis) = 4,73`; groesster Placebo-SE (P2) 1,93; `SE(Delta) = **5,11 bps**`; Schwelle `2,4865*5,11 = **12,7 bps**`; **Effektgroesse UNBELEGT (V-5)** | 5.2 |
| A2 Variante (b) monatlich | `N_eff = 13,3`; `SE(Ereignis) = 9,86`; groesster Placebo-SE (P1) 5,40; `SE(Delta) = **11,24 bps**`; Power je Fenster **0,43**, gepoolt detektierbar **25,2 bps** > 16,5 -> **GL-012** | 5.2 |
| A3-Per-Fenster-Power | **0,75 (K=117) bis 0,98 (K=300)** unter dem neuen statistischen Rahmen; **0,72-0,78** unter den Arbeitswerten des Reviews. Beide > 0,60 -> **C.10 hart, kein DEC-52** | 5.3 |
| A3-Selektions-Decke (K=7, T=2 a) | **0,98** | 5.3 |
| A3-V Vol-Drag-Null | `(0,05^2-0,02^2)/2 = 0,105 %/Tag = **73,5 bps/Woche**` - groesser als jede erwartete Kante | 5.3 |
| A4-Schwelle | statistisch: `w >= 2,4865*sigma_w/sqrt(N_cluster)`, `sigma_w` UNGEMESSEN. Etikett: `w_min = 0,49 % p.a. + m*r_opp` | 5.4 |
| WP-9-Materialitaet | systematisch `\|b\| >= **0,30 Vol-Punkte**`; zufaellig `s >= 0,30*sqrt(90) = **2,85 Vol-Punkte**`; Erreichbarkeitspruefung vorgeschaltet | 4.2 |
| WP-10(B) `adv_sel` | `**1,75 bp je Bein**` = `(FEE_TAKER-FEE_MAKER)/2` - Faktor 2 ueber Break-even, konsistent zum Rest des Dokuments | 4.3 |
| WP-10(A) Spearman-SE | `SE(z) = **1,06/sqrt(n-3)**` (Bonett/Wright [sek]); bei 6-10 Episoden `1,06/sqrt(5) = 0,474` - CI weitgehend offen, deshalb deskriptiv | 4.3 |
| Falsch-Positiv-Rate nach DEC-52 | `~0,5 * 0,01 = **0,5 %**` gegen vorher 0,25 % (Faktor 2), statt 2,5 % ohne die alpha-Absenkung (Faktor 10) | 3.5 |
| Rate-Limit-Reserve | 5 Req/s sind **4,2 %** von 120 Req/s (v1: faelschlich 0,4 %) | 7.1 |
| Funding-Backfill K~300 | ~9.300 Calls, **~31 min** bei 5 Req/s (v1: faelschlich ~15 min) | 7.1 |

### 9.3 Beschluss- und Bau-Reihenfolge (bindend)

**Bereits beschlossen** (`state/decisions.md`, keine offene Handlung): **DEC-51** (Power-Konvention), **DEC-52** (Ein-Fenster-Regel; **Retro-Check liegt vor**, `state/RETROCHECK_DEC52.md`, kein Verdikt kippt, Etikett **Verbesserung**), **DEC-53** (Ergebnis-Artefakt-Pflicht), **DEC-54** (Repo-Umbau), **DEC-55** (Stress-Kanon als Fixture), **DEC-56** (Stress-Kanon praezisiert: `STRESS_REL` = Abdeckungs-Nachweis, `STRESS_ABS` = 99-Perzentil der Gesamthistorie plus 2025-10-10 und 2026-08-19, fuer WP-10(A) und alle Liquiditaets-Fragen), **DEC-57** (GPU-Default 0, 24-h-Grenze als Meldegrenze). **Der Retro-Check ist NICHT mehr durchzufuehren** - die entsprechende v1-Anweisung haette einen vollzogenen Beschluss zurueckgenommen (Review PRD3 B-3).

1. **Beide Stress-Fixtures erzeugen** (`STRESS_REL` nach DEC-55, `STRESS_ABS` nach DEC-56; deterministisch aus dem WP-0-Bar-Cache, SHA-256-gepinnt) - `STRESS_REL` ist Vorbedingung jeder Klasse-P-Registrierung, `STRESS_ABS` Vorbedingung von WP-10(A) und jeder Fill-/Slippage-Frage.
2. **V-1 bis V-5** auf der Nutzer-Maschine beantworten (Minuten je Frage) - koennen A1, A2, A4, A5 vorab toeten. **V-5 ist neu und blockiert A2.**
3. **WP-7** spezifizieren, bauen, laufen lassen - entscheidet ueber die gesamte Klasse W und liefert `SD_null`, `K`, `sigma_xs`, `sigma_LS`, `prem_prior`, `PERP_SPREAD_BP`, `rho(BTC,ETH)`, Funding-Autokorrelation.
4. **WP-9** und **WP-10** (parallel moeglich, unabhaengig); WP-10(B) mit vorgeschalteter Positivkontrolle.
5. **DEC-58** (Registry-Format) und **DEC-59** (`constants.py`/`report.py` mit `constants_hash`) als die beiden verbleibenden Werkzeug-Entscheidungen beschliessen; DEC-57 (GPU-Default 0) ist bereits beschlossen.
6. **Fenster-Regel-Zuordnung je Kandidat schriftlich feststellen** (A1 und A4 nach WP-7 bzw. nach der `sigma_w`-Messung; A3 mit dem gemessenen `SD_null`) - **vor** jeder Registrierung, nie nach einem Lauf.
7. **Erst danach Registrierungen:** A3 nur bei WP-7-Befund B2; A1 nur bei bestandener Zuordnungsregel; **A2 nur bei belegter Effektgroesse aus V-5**; A4 nur nach V-2/V-4 und gemessenem `sigma_w`. A5 bleibt hinter der E.6-Reihenfolge gesperrt.
8. **R3-K-37 Stufe 1** bauen, sobald H-26 ein Verdikt hat oder V-4 die Gebuehrenfrage klaert (9.1).

---

## 10. Aenderungsprotokoll v1 -> v2

Jede Zeile nennt die Review-Referenz bzw. die Orchestrator-Entscheidung, die sie erzwungen hat.

### 10.1 Blocker

| # | Aenderung | Referenz |
|---|---|---|
| B-1 | **Der paarweise `rho_quer`-Schaetzer ist ERSATZLOS gestrichen** (samt Korrekturformel, Schwelle 0,03 und den darauf gebauten Befundzweigen). WP-7 misst stattdessen `SD_null(IC_t)` direkt ueber 1.000 Querschnitts-Permutationen je Woche auf dem realen Panel; deskriptiv zusaetzlich die Partizipationszahl `N_eff = (sum lambda)^2/sum lambda^2`. Die Feasibility-Frage ist **rein statistisch** (`IC_prior = 0,03`), die Wand nur noch Etikett. Neue Schranken: `SD_null <= 0,08699` (per Fenster) / `<= 0,09657` (gepoolt); notwendige Breite `K >= 134` / `109`. | Review PRD3 B-1, 1.1a, 1.4; Orchestrator-Entscheidung B-1 |
| B-2 | **DEC-Nummern gegen den Log gezogen und DEC-53 aufgenommen.** Stress-Kanon = **DEC-55/DEC-56** (nicht DEC-53), GPU-Default = **DEC-57** - alle drei beschlossen; die verbleibenden Entwuerfe sind Registry-Format = **DEC-58** und Kostenmodul = **DEC-59** (DEC-54 ist der Repo-Umbau). **DEC-53 (Ergebnis-Artefakt-Pflicht)** ist als elfte Pflichtzeile (3.3.11), YAML-Feld `artifacts` und **Teststufe T7** aufgenommen; sie erscheint in jedem Gate-Text als KEIN-VERDIKT-Bedingung. | Review PRD3 B-2, 2.2, 2.4, K-3 |
| B-3 | **DEC-51 und DEC-52 als BESCHLOSSEN gefuehrt**, nicht als Entwurf; die v1-Anweisung "Retro-Check noch durchfuehren" ist gestrichen und durch das vorliegende Ergebnis ersetzt (kein Verdikt kippt; H-06 7-62 % der halben Schwelle, H-22 Vorzeichenwechsel, H-20 +4,83 gegen 5 bp; Etikett Verbesserung). Die **Einschraenkung des Retro-Checks** (Auflage (iii) nicht nachrechenbar, Stouffer/Fisher als Obergrenze) steht woertlich in 3.5, weil sie der Entstehungsgrund von DEC-53 ist. | Review PRD3 B-3, 2.4 |
| B-4 | **Gepoolter Zweig durchgaengig mit `z = 3,1680`** statt 2,4865 (DEC-52 (iv), alpha 0,01). Folgekorrekturen: A1-Etikettschranke `sigma_LS <= 116` statt 148; Breiten-Floor `K_min = 117` statt 110; alle gepoolten Detektierbarkeiten neu. | Review PRD3 B-4, 1.3; Orchestrator-Entscheidung B-4 |
| B-5 | **DEC-52-Anwendbarkeit wird je Kandidat gerechnet.** A3: Power 0,72-0,78 (Review-Arbeitswerte) bzw. 0,75-0,98 (neuer Rahmen) -> **C.10 hart, kein DEC-52**. A1: **EIN** registriertes Design (C.10 als Default) plus **eine vorab fixierte Zuordnungsregel**, ausgewertet nach WP-7 und vor der Registrierung; die v1-Doppeltabelle zweier Designs ist gestrichen. A4 analog. A2: Regel je Ereignismenge aus der gerechneten Power. | Review PRD3 B-5, 2.3; Orchestrator-Entscheidung DEC-52-Anwendung |
| B-6 | **A4s `w_min` ist aus der PASS-Bedingung entfernt.** Neue PASS-Bedingung: statistischer Rauschboden (`w` gegen `w_null`, Bootstrap-CI auf Zyklus-Clustern, Schwelle `2,4865*sigma_w/sqrt(N_cluster)`); `w_min = 0,49 % p.a. + m*r_opp` ist Etikett und Bestandteil von A4b. **Die Regel "Vorzeichenkonsistenz 6 von 8" ist gestrichen** (dritte, unhergeleitete Fenster-Regel). | Review PRD3 B-6, 2.1(i), 3; Orchestrator-Entscheidung C.2 (i) |
| B-7 | **Der Kostenbasis-Widerspruch entfaellt**, weil die Feasibility nicht mehr an der Wand haengt (B-1). Die vier Lesarten (11 bp / 18 bp / Dezilrahmen f=2,0 / f=3,51) werden als **Etiketten** gefuehrt, und **Review R1-R4 2.7 (Dezilfaktor 3,51 statt 2,0, Faktor 1,75)** ist als Lehre L-18 und als Programm-Konstante in 9.2 aufgenommen. | Review PRD3 B-7, 1.1b; Orchestrator-Entscheidung B-1 |
| B-8 | **A2-Schwelle: die zirkulaere Herleitung ist offengelegt.** Die 12 bps stammen aus R3 und sind dort gegen die Wand gewaehlt; registriert wird `max(oberes 95-%-Quantil der Placebo-Verteilung; 2,4865*SE(Delta))` = 12,7 bps (Variante a) bzw. 28,0 bps (Variante b). **Etikett korrigiert:** 12 bps liegen **ueber** der 11-bp-Taker-Wand und unter der 15-bp-Gesamtwand - nicht unter beiden. | Review PRD3 B-8, 2.5 |

### 10.2 Wichtig

| # | Aenderung | Referenz |
|---|---|---|
| W-1 | **`r_post` traegt kein Urteil mehr** (Power 0,51, anderes Fenster-Regime als `r_pre`); A2 hat genau **eine** urteilstragende Statistik, `K = 1`, FDR-Familie mit einem Test. | Review PRD3 W-1, 1.10; Orchestrator-Entscheidung A2 |
| W-2 | **Die 36-bps-Kette steht im Text** (Tagesvol 2,5 % -> 51 bps/h -> 36 bps/30 min), BTC-only ausgewiesen; die gepoolte SD und `rho(BTC,ETH)` werden in WP-7 aus dem WP-0-Bar-Cache **gemessen**, Arbeitswert 0,8 als `[sek]` markiert. | Review PRD3 W-2, 6.1, 6.3 |
| W-3 | **Bindend ist der Placebo mit dem groessten SE** (das Gate verlangt Signifikanz gegen alle). SEs je Placebo explizit gerechnet. | Review PRD3 W-3; Orchestrator-Entscheidung A2 |
| W-4 | **WP-9: Erreichbarkeitspruefung vorgeschaltet** (Verteilung der 112 Tagesdifferenzen plus Bucket-Konventions-Kontrollrechnung), Materialitaet aus der H-26-Gate-Arithmetik hergeleitet (`\|b\| >= 0,30`; `s >= 2,85` Vol-Punkte); neuer Befundzweig B2b "konventionsbereinigt neu messen". | Review PRD3 W-4, 1.14; Orchestrator-Entscheidung WP-9 |
| W-5 | **WP-10(A) ist deskriptiv, kein PASS/FAIL**: Korrelationsmatrix stress/ruhig mit Bootstrap-CI, Spearman-SE `1,06/sqrt(n-3)`; liefert den Portfolio-Nulleffekt als Konstante. `rho_stress`/`rho_ruhig` und der N-Floor sind gestrichen. | Review PRD3 W-5, 1.11; Orchestrator-Entscheidung WP-10(A) |
| W-6 | **`adv_sel <= 1,75 bp`** (Faktor 2 ueber Break-even 3,5 bp); **`p_fill`-Schwelle gestrichen**, stattdessen wird die **Fill-Raten-Kurve** gemessen und als Kostenmodell-Konstante uebernommen; 10 s / 60 s als Design-Parameter etikettiert. | Review PRD3 W-6, 1.12; Orchestrator-Entscheidung WP-10(B) |
| W-7 | **WP-7-Befund zu `sigma_xs`: keine Streichungsoption.** Konsequenz vorab fixiert = Etikett `unter_wand` fuer alle Klasse-W-Kandidaten, sonst nichts; die 500 ist durch die Formel `sigma_xs_min = 2*Kosten/(f*IC_prior)` ersetzt. | Review PRD3 W-7, 2.1(iii), 3; Orchestrator-Entscheidung C.2 (iii) |
| W-8 | **15 bps ist die Gesamtwand**, nicht eine Slippage-Konstante; Review R1-R4 1-R3-K-35 woertlich uebernommen (Korrektur hoechstens ~27 %, nie unter 11 bps Taker). Der Alt-Spread-**Faktor `3x` ist gestrichen**. | Review PRD3 W-8 |
| W-9 | **WP-10(A) berichtet zusaetzlich die Korrelation zwischen Praemien-PnL und Handlungsfaehigkeit des Betreibers** (Margin-Auslastung, ADL, Auszahlungsstopp-Proxy) - nach Review R1-R4 6.7 die eigentlich relevante Groesse. | Review PRD3 W-9 |
| W-10 | **Der Befund ist als DEC-56 beschlossen:** ein rollierender 97,5-Perzentil-Schnitt erzeugt per Konstruktion ~2,5 % Stress-Tage je Fenster, die Klausel ">= 1 Episode je Fenster" kann nie binden - `STRESS_REL` ist deshalb **Abdeckungs-Nachweis**, nie Filter. Die absolute Zweitliste **`STRESS_ABS`** (99-Perzentil der Gesamthistorie plus 2025-10-10 und 2026-08-19) ist eingefuehrt und ist die Stress-Definition fuer WP-10(A) und alle Liquiditaets-/Fill-Fragen. | Review PRD3 W-10; DEC-56 |
| W-11 | **DEC-51 vollstaendig wiedergegeben** inklusive Punkt 1 (zweiseitig fuer META-/Zensusfragen, ausdrueckliche Etikettierung - betrifft WP-7/9/10) und Punkt 5 (Ueberlappung); **YAML um `richtung` erweitert**, `sided` kann `one` oder `two` sein. | Review PRD3 W-11, 2.2; Orchestrator-Entscheidung DEC-51 |
| W-12 | **Positivkontroll-Vorschaltung auf WP-10(B) angewendet** (86 min > 1 h): `vorgeschaltet: true`. | Review PRD3 W-12 |
| W-13 | **Rechenfehler korrigiert:** 5 Req/s = **4,2 %** des Limits (nicht 0,4 %); Funding-Backfill ~9.300 Calls = **~31 min** (nicht ~15 min); Welle-1-Backfill gesamt ~41 min. | Review PRD3 W-13, 1.21, 1.22 |
| W-14 | **`T_min`-Formel als Naeherung gekennzeichnet**, exakte Form mit `(1+SR^2/(2q))` und `q` mitgefuehrt (SR 2,0: 1,80 statt 1,55 a). | Review PRD3 W-14, 1.20 |
| W-15 | **R3-K-37 Stufe 1 und R3-K-33 Stufe 1 mit ausdruecklicher Vertagungsbegruendung in 9.1** aufgenommen; fuer K-37 Stufe 1 ist der Ausloeser vorab fixiert (H-26-Verdikt oder V-4), und A5s Sperrbedingung (b) verweist darauf. | Review PRD3 W-15 |
| W-16 | **`r_USD = 0` als konservative ANNAHME etikettiert und mit 8.2 verlinkt**; dieselbe Groesse wie `r_opp`, kuenftig an beiden Stellen derselbe Wert. | Review PRD3 W-16, 5 |

### 10.3 Kosmetik und Belege

| # | Aenderung | Referenz |
|---|---|---|
| K-1 | "Sieben kapitalfreie Mess-WEITER" mit sechs Namen: die Diskrepanz ist im Kompendium angelegt und wird jetzt ausdruecklich vermerkt statt geglaettet. | Review PRD3 K-1 |
| K-2 | Ueberschrift auf **zwoelf Pflichtzeilen** angepasst (zehn plus DEC-53 plus Test-Pflichten). | Review PRD3 K-2 |
| K-4 | Falsch-Positiv-Rate nach DEC-52 mit **0,5 % gegen vorher 0,25 %** beziffert; der Restfaktor 2 ist benannt, damit "keine Lockerung" praezise bleibt. | Review PRD3 K-4 |
| K-5 | Placebo-Term in A2-Variante (b) mitgerechnet (`SE(Delta) = 11,24`). | Review PRD3 K-5 |
| K-6 | V-3 nutzt **113 Tage** (F.1) statt der in Vorlage und Review genannten 43; die bewusste Abweichung ist vermerkt, ebenso dass 113 Tage die 10.10.2025-Episode ausschliessen. | Review PRD3 K-6 |
| K-7 | **2.008 Handelstage** gegen **2.190 Kalendertage** einmal erklaert (7.3). | Review PRD3 K-7 |
| K-8 | **FRL (2026) mit R3s Vorbehalt** zitiert ("Autoren nicht ermittelbar, Volltext gesperrt"). | Review PRD3 K-8, 6.8 |
| Bel-1 | **"Deribit fuehrt woechentliche Freitags-Verfaelle"** ist als **UNBELEGT** gefuehrt und mit einem Verifikationsauftrag in **V-5** hinterlegt; die gesamte A2-P1-Konstruktion haengt daran. | Review PRD3 6.4 |
| Bel-2 | **"~11 % Zerfall p.a."** und **"2025 negativer Carry"** sind als **UNBELEGT** gefuehrt (in R2 `[sek]` ohne benennbare Quelle); sie duerfen A1 weder stuetzen noch toeten. | Review PRD3 6.6 |
| Bel-3 | **Endpunktparameter ohne unabhaengige Quelle als `[sek]`** markiert (`instruments-info`-Cursorpaginierung, `delivery-price` "200/Seite, Cursor", Deribit-`resolution`). | Review PRD3 6.5 |
| Bel-4 | **`rho(BTC,ETH) = 0,8` als `[sek]` markiert** und als Messauftrag in WP-7 aufgenommen. | Review PRD3 6.3 |
| Bel-5 | Gesetzte Skalare, die bleiben, tragen jetzt ausdruecklich **"Design-Parameter (keine Schwelle)"** mit vorab fixierter Konsequenz: Listing-Ausschluss 8 Wochen (mit Sensitivitaet 4/12 Wochen als Bericht), Funding-Autokorrelation 0,30, V-2-Liquiditaetsmarke 1 %, WP-10(B)-Stuetzstellen 10 s/60 s, die DEC-55-Parameter (97,5 %, 24 Monate, Luecken-Regel) und die DEC-56-Parameter (99 %, die zwei benannten Tage). | Review PRD3 3, 6.7 |

*Ende PRD_SCINANCE3_v2.md - prd-architect, 2026-09-02. Kein Abschnitt dieses Dokuments ist eine Registrierung; alle Kandidaten-Abschnitte sind Entwuerfe und ersetzen keine Vorregistrierung durch den Orchestrator.*
