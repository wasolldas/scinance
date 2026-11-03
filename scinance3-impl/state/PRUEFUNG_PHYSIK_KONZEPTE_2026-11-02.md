# Pruefung der Nutzer-Konzepte "Physik-Transfer" vom 2026-11-02 (sechs Dokumente) - Orchestrator-Urteil

> Eingaben des Nutzers (nicht im Repo; nur Name, Umfang, sha256-Praefix): PRD_QUANT_PHYSICS_EDGE.md (540 Zeilen, 87582f07),
> research_seismology.md (770, 19b6e850), research_thermodynamics.md (945, adf1344c), research_biophysics.md (807, 7f763416),
> CRYPTO_CASCADE_INTELLIGENCE_PRD.pdf (36 Seiten, aae8a8f1), PRD_Interaktiver_KI_Trading_Edge_Konzept.pdf (2 Seiten, 510f61e1),
> step-2-0.pdf (6 Seiten Uebersicht von Dok 1, bba4e32d). Die Dateien bleiben ausserhalb des Repos, weil Dok 2 Kennzahlen und
> Payload-Beispiele eines versiegelten Tages enthaelt (Abschnitt 4) und die uebrigen unbelegte Zahlen tragen.
> Adversarischer Review: `prd_analyse_2026-11-01/REVIEW_PHYSIK_KONZEPTE_2026-11-02.md` (66 Vorschlaege klassifiziert, 30 Zahlen
> geprueft, sieben Skizzen); Orchestrator-Nachrechnung `scripts/orch_physics_check.py`. Nur Formeln, keine Marktdaten, keine
> Siegeldatei; Code aus den Eingaben nicht ausgefuehrt.

## 1. Urteil in Kuerze

1. **Horizont.** Fuenf der sechs Dokumente setzen auf Signale im Bereich 50 ms bis 5 s. Dort liefert ein **perfektes** Orakel
   0,2..0,7 bp je Trade gegen 11 bp Taker-Rundreise (Faktor 15..55; bei 1 min noch Faktor 2, Gleichstand erst bei ~5 min)
   [R `orch_physics_check.out`; F CLAUDE.md K-0.1, DEC-105 (1)]. Das ist die Horizont-Schere, an der 2.0 gestorben ist, und sie
   haengt nicht am Modell, sondern an der Vol-Skalierung sqrt(Horizont). Unter der Mission sind diese Horizonte nur als
   Kosten-, Nullwelt- oder Zensusmessung zulaessig.
2. **Daten.** Die behaupteten Vorlaeufe (80..260 ms Transfer-Entropie, 240..550 ms Lyapunov-Horizont, 100..450 ms Chirp) sind
   mit unseren Stroemen nicht einmal messbar: das Orderbuch liegt im ~200-ms-Takt, DVOL stuendlich [R Review calc I]. Liquidationen
   und Insurance-Fund gibt es erst seit 2026-06-16 und damit vollstaendig in Zone K (vor Kohorte 1 nur Zaehlungen SK0); Options-
   Ticker ebenso; Orderbuecher haben 18 Monate Zone X (2023-01..2024-06).
3. **Akte.** Was an den Dokumenten tragfaehig ist, steht bereits im Programm: Wurzelgesetz/Kostenkurve (IK-01), Queue/First-
   Passage (IK-02), Skalengesetze/Multifraktal (IK-04), ETAS/Liquidationen (F9, 2.0 C-27..C-29), Resilienz nach Schocks (WP-11,
   DEC-63). Was tot ist, ist dort tot und braucht nach C.1 einen Nicht-Wiederholungs-Nachweis: Lead-Lag (H-04/H-04b, D.11),
   Permutationsentropie (D.6), Entropie-Momentum (D.3), OFI (D.5), Spread-Capture (D.1), Branching-Schwellen (D.2),
   Tail-Reversion (D.12), Lotka-Volterra (Exkurs S2), Critical Slowing Down als Signal (N-6), TDA/RQA (N-20).
4. **Zahlen.** Die quantitativen Angaben (Lyapunov 1,8..4,2 s^-1, b 0,314, n 0,10..0,20, 88 % Absorption, 94 % Erkennung,
   GPU-Benchmarks, "Garcia Seuma (2026)") sind in der Akte nicht belegt (grep 0 Treffer) und teils in sich widerspruechlich:
   p < 1e-4 ist mit 1.000 Surrogaten unerreichbar (min 0,000999); Pareto-Index 0,723 passt nicht zu den eigenen Tageskennzahlen;
   16 CPCV-Pfade aus 6 Bloecken sind unmoeglich; das SNR-Optimum der stochastischen Resonanz ist falsch (Delta V/2 statt
   Delta V/sqrt 2); die GPU-Gesamtlatenz ist die Summe der Kerne [R Review 3.2/3.3]. Status: **UNBELEGT**.
5. **Governance.** Dok 1, 2, 3, 4 und 6 enthalten Ausfuehrungslogik (OMS, IOC-Orders, Kelly-Sizing, Meta-Alpha-Fusion ohne
   Vorregistrierung), GPU-Pflicht und Freigabe-/Deployment-Aussagen ("Approved", "Freigegeben", Live-Kapital ab 2027-01-06).
   Das kollidiert mit "kein Live-Order-Code", DEC-57 (GPU 0), Sequenz-Zwang und Registrierungsdisziplin. Nichts davon wird
   uebernommen; die Verfassung aendert nur der Nutzer.
6. **Dok 5 (Cascade Intelligence) ist anders:** kein Bot, Nicht-Ziele, Modelltreppe mit Poisson-Null, staerkste Baseline,
   Negativkontrollen, Label-Einfrieren, `ts_available`, Clauset-Protokoll. Es wird als **Methodenquelle** uebernommen, nicht als
   PRD: seine Gates haben kein alpha, keine Power, keine SESOI, kein Selektions-K und keine Positivkontrolle; ein Tradingnutzen-
   Gate verletzt C.2; seine Datenstroeme liegen fast vollstaendig in Zone K.

## 2. Was uebernommen wird (Orchestrator, reversibel)

| Nr. | Skizze (Review Abschnitt 4) | Status | Zone / Zeitpunkt | Aufwand |
|---|---|---|---|---|
| R-1 | Liquidations-Kaskaden: Groessenverteilung (Clauset), Omori-Kern, Branching n **ohne Schwelle**, Kreuzanregung Liq -> Trades; Abnehmer: Stress-Kostenfenster (DEC-63), STRESS_ABS-Zelle, H-21-Wiedervorlage als Messfrage | **neue Karte IK-12** (3.1-Nachfolge von H-21/F9) | SK0-Zensus sofort (Zeilen, Luecken, Meldesemantik); Registrierung Kohorte 1 (2027-01-01), K-Fenster mit Quartalsblicken, Ausfallbudget >= 10 % | SK0 < 1 h; Herleitung + Review 1..2 Agententage |
| R-2 | Hawkes/ETAS auf Bybit-Trades 2020..2024-06 als Positivkontrolle und Nullwelt fuer R-1 (Modelltreppe aus Dok 5) | bedingt (nur mit R-1) | Zone X (Konto), dieselbe Stichprobe wie IK-01 | CPU-Stunden |
| R-3 | First-Passage / Mehrstufen-Depletion und Rueckfuellzeit | Ausgabe von IK-02 | Zone X (L2 2023-01..2024-06) | auf der IK-02-Stichprobe |
| R-4 | Transfer-Entropie auf Tagesbasis | nur Nebenstatistik in IK-10/F7 (kein X-Anteil fuer Cross-Venue) | - | - |
| R-5 | Mehrskalen-Relaxation nach Schocks als Nullwelt-Kenngroesse (ohne Fruehwarn-Anspruch) | Teil von IK-04 / WP-11 | Zone X | gering |
| R-6 | Multifraktale Strukturfunktionen | Teilmodul IK-04 | Zone X | gering |
| R-7 | Luecken- und Inselstatistik des L2 statt Perkolation | Ergaenzung IK-01 (c) / IK-02 | Zone X | gering |

Aus Dok 5 in die Automations-Bausteine (F4 Lauf-Rahmen, F8 Pruefschleifen): Modelltreppe (Poisson -> univariat -> multivariat
-> markiert), Pflicht-Baseline "staerkstes einfaches Vergleichsmodell", Negativkontrollen und Ablationen, Label-Einfrieren
vor dem ersten Blick, `ts_available` als Pflichtfeld jeder Ereigniszeit.

## 3. Was nicht uebernommen wird und warum

| Vorschlag | Klasse | Grund |
|---|---|---|
| Epistemologisches Gate (IAAFT-Surrogate, Lyapunov, Kolmogorov, RQA) als "Beweis des Edge" | B, E | Nicht-Zufaelligkeit ist kein Edge (H-03: Surrogate-p ~1,0, D.4); Chaos-Metriken auf 200-ms-Frames nicht schaetzbar; p < 1e-4 mit 1.000 Surrogaten unmoeglich |
| Transfer-Entropie / MPE / Ising als ms-Signal | B, C | H-04/H-06/D.6/D.11; Horizont 80..400 ms unter der Wand (Faktor > 20) und unterhalb des Datentakts |
| LIGO-Chirp-Matched-Filter, Rayleigh-Plesset-Kavitation, Burgers-Stoss, Lindblad/Quantum Walk/Discord, STDP, stochastische Resonanz | E | Analogie ohne abgebildeten Mechanismus, keine falsifizierbare Vorhersage auf unseren Daten; teils falsche Formeln (SNR-Optimum) |
| TDA/Persistente Homologie, Perkolationsschwelle 0,5927 auf dem Buch | E, C | Gitter ohne Definition; N-20; Lueckenstatistik des L2 (R-7) leistet das Messbare |
| FitzHugh-Nagumo "Refraktaer-Sniping" (APRH), Lotka-Volterra | B | Spread-Capture D.1; Lotka-Volterra bereits verworfen (Exkurs S2) |
| Branching n > 1 als Ueberkritikalitaets-Signal | B | D.2; widerspricht Dok 2 (n 0,1..0,2) |
| Meta-Alpha-Fusion (8 Saeulen, Kelly, TFT), GPU-Pflicht, Live-Deployment | F | Verfassung: kein Live-Order-Code, DEC-57, Vorregistrierung, Selektions-K (acht ungetestete Saeulen = Mehrfachtest ohne Nenner) |

## 4. Fremdoeffnung und Offenlegung (Register)

- **O-981 (Fremdquelle, 2026-11-02):** Dok 2 nennt fuer einen Tag im August 2026 (Zone K) Anzahl, Mittel, Maximum, Quantil und
  b-Wert der BTCUSDT-Liquidationen sowie Payload-Beispiele mit Zeitstempeln und BTC-Preisniveaus aus Zone V und K. Ob echt, ist
  ohne Siegelbruch nicht pruefbar [V]. Buchung als Oeffnung durch Fremdquelle (Praezedenz DEC-97 A-3); der Tag kommt auf die
  C.17-Liste jeder kuenftigen Liquidations- oder BTC-Renditestatistik (IK-12); keine Rohwerte im Repo (Eingaben bleiben draussen,
  Rechenskript des Reviews mit den Rohangaben bleibt im Scratchpad).
- **O-982 (Review-Agent, 2026-11-02):** eine Namenssuche (grep -l nach "seuma") lief einmal auch ueber `state/runs/*_L_window_sealed.json`;
  0 Treffer, kein Inhalt angezeigt oder gelesen; wiederholt mit Ausschluss von `runs/`. Keine Oeffnung; dokumentiert.

## 5. Antwort an den Nutzer

Die Konzepte sind in der Formalistik grossteils korrekt (ETAS, Omori, Wurzelgesetz, Hawkes), aber als Handelsprogramm
nicht tragfaehig: Horizont unter der Wand, Daten im Siegel oder zu grob, Zahlen unbelegt, Governance im Konflikt. Ihr Wert
liegt in einer neuen Messkarte (IK-12 Liquidations-Kaskaden), in Praezisierungen bestehender Karten (IK-01, IK-02, IK-04) und in
der Methodik von Dok 5 fuer den Lauf-Rahmen. Nichts davon aendert ein GL, eine Regel oder die Reihenfolge der naechsten Schritte
(OC-Nachentscheid P-2, Kohorte 1, Zone-X-Programme).

## Nachtrag (2026-11-02, spaet): siebte Eingabe "SCINANCE-PHYSICS-EDGE v2.1: Kausalitaet, Herleitung & Edge" (step-3.pdf, 4 Seiten)

Inhalt: "Invarianz-Prinzip" (drei Axiome: absorbierende Randbedingung durch Liquidation, Erhaltung durch Matching, Latenz als
Transportgrenze -> "das Orderbuch gehorcht denselben PDEs wie Fluide, seismische und erregbare Medien") und eine Tabelle
Kausalmechanismus / Herleitung / Edge je Saeule mit denselben Behauptungen wie v2.0 (80..260 ms Lead-Lag, 120..400 ms Chirp,
94 % Iceberg-Erkennung, Exhaustion-Sniping bei n < 0,20, Momentum-Short bei n > 0,45, exakte Haltekante per Rankine-Hugoniot).
Urteil: keine neuen Inhalte gegenueber Dok 1; das Urteil oben gilt unveraendert. Zur Begruendung "keine blosse Metapher": die drei
Axiome sind richtig, aber aus ihnen folgt keine bestimmte PDE - jede Analogie (Reaktions-Diffusion, Burgers, FitzHugh-Nagumo,
Lindblad) ist eine zusaetzliche Modellannahme, die auf unseren Daten getestet werden muesste, und zwar auf Horizonten, die
die Mission nur als Messung zulaesst. Die Schwellen n < 0,20 / n > 0,45 sind UNBELEGT und widersprechen D.2 (Branching-Schwellen).
Die Datei bleibt ausserhalb des Repos (sha256-Praefix 86e95c9c; keine Siegelwerte enthalten).

## Nachtrag 2 (2026-11-03): achte Eingabe "PRD: Projekt Cross-Science Alpha" (4 Seiten, sha256-Praefix 46a999d0)

**Inhalt.** Minutenhorizont (1 bis 15 min) statt Millisekunden; drei Ansaetze: (A) Signatur-Methoden (Rough Paths) auf
L2-Deltas und Trades, 1..5-min-Fenster, iterierte Integrale 2. bis 4. Ordnung als Features fuer XGBoost, Ziel 5-min-Rendite;
(B) zeitliches Graph-Netz (TGNN) auf der Bybit-Optionskette plus Perp, Vorhersage der Perp-Bewegung im Minutenbereich;
(C) persistente Homologie (TDA) auf Funding, OI, Liquidationen als Regime-Fruehwarnung mit 15..30 min Vorlauf. Pipeline auf
dem GPU-PC (Spiegelung per LAN), rollierendes Training ueber 30 Tage, Maker-Ausfuehrung, pessimistisches Slippage-Modell,
Luecken-Fail-Safe, Paper-Trading ab Woche 8.

**Staerken [U].** Nuechterner als die Vorgaenger: Minuten- statt Millisekundenhorizont, Maker bevorzugt, pessimistisches
Fill-Modell aus den L2-Daten, Fail-Safe bei Datenluecken, keine erfundenen Kennzahlen. Das pessimistische Orderbuch-Modell
ist inhaltlich IK-02 (Maker-Kostenkurve) und wird dort ohnehin gebaut.

**Kostenwand auf Minutenhorizont [R, sigma_d 262 bp, Kante 0,798 sigma x IC]:**

| Horizont | perfektes Orakel | noetiger IC fuer Maker 4 bp | noetiger IC fuer Taker 11 bp | Kante bei IC 0,05 |
|---|---|---|---|---|
| 1 min | 5,5 bp | 0,73 | 2,0 (unmoeglich) | 0,28 bp |
| 5 min | 12,3 bp | 0,32 | 0,89 | 0,62 bp |
| 15 min | 21,3 bp | 0,19 | 0,52 | 1,07 bp |

Selbst mit reiner Maker-Ausfuehrung braucht das Ziel "5-min-Rendite" einen IC von 0,32; die besten bekannten Minuten-Signale
liegen um 0,05 und sind Faktor 6..15 darunter. Maker-Fills sind zudem adversely selected (WP-10(B)): gefuellt wird bevorzugt,
wenn der Preis gegen die Position laeuft. Der Minutenhorizont verschiebt die Wand, hebt sie nicht auf (CLAUDE.md K-0.1; DEC-105 (1)).

**Abgleich mit der Akte.**
- (A) Signaturen sind eine legitime Merkmalsmethode (Lyons; Sweep M01 fuehrt den Signaturplot). Die Inhalte, die sie hier
  kodieren sollen, sind aber exakt die toten Richtungen: Lead-Lag von Volumen auf Preis (D.11, H-04/H-14), OFI-Folge (D.5,
  H-05) und Minuten-Netto-Fluss (D.14, H-24: ueber zehn Halbjahre stabil **negativer** Forward-IC). Ein XGBoost auf 30 Tagen mit
  hunderten Signaturtermen ohne Vorregistrierung ist ein Mehrfachtest ohne Nenner. Status: unter der Wand, B (C.1-Nachweis fehlt).
- (B) Die Bybit-Optionskette liegt erst seit 2026-06-16 vor (116 Tage, 13.682 Instrumente) und damit vollstaendig in Zone K
  (versiegelt; vor Kohorte 1 nur Zaehlungen). Lernen auf diesen Daten verbraucht das einzige Blindfenster der Optionsfamilie.
  Kompendium D.16 (schwere Modell-Infrastruktur vor validiertem Basissignal) und D.17 (Options-Ketten-Kandidaten) gelten.
  Status: Siegelkonflikt, unter der Wand.
- (C) TDA steht in der Negativliste des Sweeps (N-20: kein Mechanismus, keine Nullverteilung mit bekannter Erreichbarkeit).
  Liquidationen liegen in Zone K, OI nur fuer 5 Symbole ab 2024-03. Als Risikoschalter ("Orders abziehen") ist es kein
  Alpha und braucht Ausfuehrungslogik. Status: E, Messwert ohne Abnehmer. Die Frage "zerfaellt die Funding-Verteilung ueber
  Assets vor Kaskaden?" ist als einfache Streuungsstatistik (Querschnitts-SD und Totzonen-Anteil des Fundings, Zone X) prueffaehig
  und liegt nahe an IK-11/F2; dafuer braucht es keine Topologie.
- **Governance:** GPU-PC-Pipeline und Spiegelung auf den PC widersprechen DEC-57 (GPU 0) und DEC-106 (keine Auftraege mehr
  an den Nutzer-PC); Paper-Trading ueber die Boersen-API ist Ausfuehrungsinfrastruktur und braucht eine Nutzerentscheidung
  (PRD 8.1). 30-Tage-Rolling-Training ohne Konfirmationsfenster widerspricht DEC-104 (Vorregistrierung, Zonen).

**Urteil.** Ablehnen als Programm; zwei Bausteine sind schon im Plan (pessimistisches Fill-Modell = IK-02; Signatur-Plot als
Skalengesetz-Werkzeug in IK-04). Neu aufgenommen als Zone-X-Kandidat (kein Alpha): Querschnitts-Streuung des Fundings vor
Kaskaden-Tagen, nur Streuung, als Teil von IK-11. Die Datei bleibt ausserhalb des Repos; sie enthaelt eine LAN-Portangabe
des Datendienstes und keine Siegelwerte.
