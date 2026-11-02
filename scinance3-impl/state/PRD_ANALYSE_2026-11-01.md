# PRD-Gesamtanalyse Scinance (2026-11-01): Fehler und Annahmen, Edge-Inventur, uebersehene Konzepte, Forschungsfelder, vollautomatische Institution

> **Orchestrator-Synthese** aus sechs Agentenanalysen (Regel- und Gate-Listen; Faktenblatt aller Hypothesen, Kandidaten,
> Datenstroeme und Warteregeln; PRD-Kritik; Edge-Inventur; Grundsatzanalyse zu Konzept und Forschungsfeldern;
> Architektur der Automation) und einem adversarischen Review der vier Analysen. Alle Teile liegen im Anhang
> `state/prd_analyse_2026-11-01/`. Nur Lesearbeit und analytische Rechnung aus Akten-Zahlen; **keine Marktdaten
> gerechnet, keine Siegeldatei geoeffnet, kein Fenster beruehrt.** Kein Verdikt, keine Registrierung, keine
> Regelaenderung: dieses Dokument ist eine **Vorlage**. Vorschlaege tragen ihre Richtung (Strenge / Testbarkeit /
> neutral) und ihren Entscheider (N = Nutzer, Programmfrage PRD Par. 8; O = Orchestrator per DEC ohne Rueckfrage).
> Die Review-Auflagen (Anhang C) sind eingearbeitet; wo eine Agentenanalyse im Anhang einer Zahl dieser Synthese
> widerspricht, gilt die Synthese (Begruendung in Anhang C). Anlass: Nutzerfrage vom 2026-11-01 (Fehler/Annahmen im
> PRD; Edge-Hinweise; Stand der Grundidee "Naturwissenschaft und Technik auf grosse Tradingdaten"; Uebersehenes; neue
> Forschungsfelder; Datenfenster weise nutzen; keine jahrelange Wartezeit; vollautomatische Analyseinstitution mit
> minimalem menschlichem Eingriff).

## 0. Antwort in Kuerze

1. **Wo wir stehen.** Seit dem PRD (2026-09-02, also in zwei Monaten 3.0) hat das Programm fuenf Gate-Eintraege erzeugt
   (GL-032..036; GL-035 ist der H-32-Pilot) und **keinen einzigen Test auf einem Urteilsfenster** gerechnet: alle sind
   "GL-012 vor dem Lauf / vor der Registrierung / im Pilot". Es gibt in 3.0 keinen Effektschaetzer mit
   Konfidenzintervall. Dein Eindruck einer Sackgasse stimmt; die Ursache ist weder Daten noch Code noch Rechenzeit
   (alle Datenauftraege wurden binnen Tagen erfuellt, Laufzeiten sind Minuten bis Stunden), sondern das **Produkt der
   Regeln** (Power 0,80 je Fenster x zwei starre 12-Monats-Fenster x REZENZ x Blind-Siegel x Einmal-Gut x
   Literatur-Punktprior) und eine Strenge-Ratsche, die nur in eine Richtung laeuft. [Faktenblatt T2/T4;
   Grundsatzanalyse T-1, T-11; Kritik K-5, K-6]
2. **Fehler im PRD, die etwas aendern.** (a) Die Horizont-Friktions-Kurve unterschaetzt die Kante eines Signals um den
   Faktor pi/2 = 1,57 (bei einem Rang-IC pi^2/6 = 1,65): sie rechnet die Korrelation in eine Trefferquote um und
   verliert, dass grosse Bewegungen oefter richtig getroffen werden. Der Mindesthorizont ist um den Faktor 2,5 zu lang
   (Wochen-IC 0,05: 1,1 statt 2,7 Tage), das oekonomische IC-Minimum 0,040 statt 0,062; dazu ein Rechenfehler im PRD
   selbst ("~7 h Maker" sind mit der PRD-Formel 8,7 h). Vom Orchestrator und vom Review unabhaengig nachgerechnet:
   korrekt. Der tiefere Fehler ist kategorial (ein Querschnitts-IC wird als Zeitreihenkorrelation eines einzelnen
   Assets gelesen) und wird durch die pi/2-Korrektur nicht geheilt. (b) "Praemie statt Sharpe" kauft keine Power: der
   Praemientest ist dieselbe Lo-Arithmetik; unter zwei 12-Monats-Fenstern braucht jede Praemie ein
   Brutto-Sharpe-Aequivalent von 2,49 je Fenster. Die Schwelle war am PRD-Tag bekannt; dass A1 und VRP sie
   verfehlen, zeigten erst die Nuisance-Messungen DEC-93/97 [V]. (c) Der WP-7-Rauschboden "SD_null(IC_t) per
   Permutation" ist eine Identitaet (Varianz exakt 1/(K-1)) und kann die effektive Breite gar nicht enthalten; der
   Feasibility-Befund B2 "Klasse W testbar" (PRD 4.1, DEC-67) war ein Falsch-Positiv. DEC-74 hat die Identitaet selbst
   festgehalten; wie viel der A3-Arbeit DEC-73..92 damit vermeidbar gewesen waere, ist Rueckschau [V]. Vom Orchestrator
   nachgerechnet: korrekt. (d) Das nominale Power-Ziel 0,80 je Fenster ist eine Entscheidungs-Power von 0,64; niemand
   kontrolliert die kumulierte Strenge: bei A2 stieg die Nachweisgrenze durch sieben einzeln begruendete Schritte von
   18,8 auf 32,1 bp (18,8 -> 19,7 -> 23,1 -> 24,4 -> 27,2 -> 29,3 -> 32,1; Datenbedarf x2,9). Der Produkt-Schritt
   mit der Null-Bedingung ist dabei nur zu 0,5..0,6 bp ein Rechenartefakt (die Akte fuehrt die exakte Bedingung
   bereits: 22,93 / 23,77 gegen Produkt 23,43 / 24,36); der Rest sind Festlegungen (Stress bindend +2,8, skalierte
   Null +2,1, Gate-(4)-Faktor +2,8), die der Orchestrator am 2026-10-31 selbst getroffen hat und die hier als
   Programmfrage vorgelegt werden (P-7). [Kritik K-1..K-5; Review B-1, B-10, B-11; Nachrechnung Abschnitt 1]
3. **Edge.** Nichts im Bestand belegt einen Edge im Sinne einer belegten, absehbar testbaren Ertragsquelle ueber der
   Wand. Drei Linien tragen einen Hinweis: beta-neutrales Kurzfrist-Reversal (eigener Pilot t -3,3..-4,1, Literatur
   fuer liquide Universen gegenlaeufig, implizite Informationsrate 2,3..2,8 p.a. hoch fuer liquide Universen),
   VRP (nur Literatur; mit dem gueltigen Prior 7,14 VP erst 2029-07..2033-01 pruefbar), Funding-Carry A1 (Zahler klar,
   theta offen, strukturell 85+ Wochen je Fenster). Die sechs kapitalfreien 2.0-Mess-WEITER sind echte
   Mikrostruktur-Signale 80..500x unter der Wand. Alle "Brutto"-Zahlen der L/S-Linien sind ohne Funding-Zahlungen
   gerechnet (Luecke, Abschnitt 4). [Edge-Inventur 0, 4; Review B-3, B-15]
4. **Die Grundidee.** Als **Pruefdisziplin** ist sie weitgehend realisiert (Vorregistrierung mit Hash, gemessener
   Rauschboden, Nullmodelle, Positivkontrollen, Blindheit). Als **Messinstitution** nicht: das Programm kennt nur
   PASS / DROP / GL-012, nie "Effekt = x mit Intervall". Es fehlen Ausschlussgrenzen als Standardausgabe, eine
   Operating-Characteristics-Simulation der ganzen Gate-Kette mit minimalen, je Familie validierten Nullwelten,
   Mess-Invarianten und Skalengesetze, Ereigniszeit, sequentielle Inferenz. (Ein umfassendes generatives Marktmodell
   waere dagegen schwere Modell-Infrastruktur vor validiertem Signal, Kompendium D.16, und braucht eine ausdrueckliche
   Nutzerentscheidung.) Die grossen Daten (309 GB Trades, 377 GB Orderbuecher, 387 GB Optionskette) werden von 3.0
   fast nicht benutzt; 3.0 rechnet auf wenigen tausend Tages- oder Wochenpunkten. [Grundsatzanalyse T-1..T-7;
   Review B-18]
5. **Strukturell uebersehen: die Horizont-Schere.** 2.0 testete Mikrostruktur auf Sekunden (Friktion toetet), 3.0 testet
   Praemien auf Jahren mit wenigen Beobachtungen (Power toetet). Der Tageshorizont wurde nie mit angemessener Power
   geprueft (Kompendium D enthaelt dort nur H-22, Nachweisgrenze IC 0,11). Zwei Spalten, die auseinanderzuhalten sind:
   **Exploration** auf der Vorperiode (BTC/ETH-Tage bis 2026-06, ~2.000 Tage, agentenbekannt, nur mit Konto): ein
   Tages-IC von 0,056 ist aufloesbar (11,6 bp/Tag brutto), gegen eine Taker-Grenze von IC 0,011..0,026 je nach
   Signal-Persistenz. **Konfirmation** unter geltenden Regeln nur prospektiv (BTC/ETH-Aggregate sind agentenbekannt,
   Praezedenz DEC-96 E1): 365 Tage je Jahresfenster loesen nur IC 0,13 auf. Der schnelle Weg zum Tageshorizont fuehrt
   deshalb ueber den **Querschnitt des vollen Perp-Panels** (F1): auf W1/W2 (je 365 Tage, K 300..600) liegt die
   Nachweisgrenze bei IC 0,013..0,019 je Fenster; der einzige Literatur-Prior (Ein-Tages-Reversal, Bianchi et al.,
   IC 0,090 gleichgewichtet / 0,023 wertgewichtet, [PDF], Werte nach Weg A abgeleitet) misst aber ein Design ohne
   Luecke und ohne Beta-Kontrolle, also nicht die Gap-Statistik, die F1 wegen des Bid-Ask-Bounce braucht. F1 ist das
   interessanteste neue Feld, aber **heute nicht registrierbar**. [Grundsatzanalyse T-8/T-9, Feld F1;
   Orchestrator-Vorrechnung; Review B-4, B-5, B-14]
6. **Zwoelf Forschungsfelder** sind tabelliert (Abschnitt 5), geordnet nach Testbarkeit heute und Passung zur Mission.
   **Keines ist heute ohne Programmentscheidung registrierbar**: F1 fehlt der Prior fuer die Gap-Statistik, F5
   (Listing-/Delisting-Ereignisse) jeder Prior, die BTC/ETH-Tagesfelder (F2, F3, F4, F6) sind nur prospektiv
   konfirmierbar, F8 (Optionsfluss/GEX) und F9 (Liquidationen) liegen fast vollstaendig im Siegel ab 2026-07. Sofort
   moeglich sind Zensen (Zaehlung, Streuung) und Explorationsmessungen mit Konto auf der Vorperiode. Mit
   Data-Harvest: F3 OI-Historie aller Perps, F12 Stablecoin-Angebot (frei), F10 Deribit-Futures-Historie (Probe),
   Inhaltsproben Optionskette und deribit/publicTrade.
7. **Datenfenster weise nutzen, ohne Jahre zu warten.** Die vier Warteregeln sind einzeln begruendet; ihr Produkt ist
   eine Kalenderuhr bis 2029..2033. Vorschlag beider Herleitungen (konvergent): ein **Drei-Zonen-Regime**
   (Exploration mit Konto / Validierung mit einem Blick / versiegelte Konfirmation, quartalsweise rollierend) mit
   institutionsweitem Fehlerbudget, Kohorten-Stichtagen statt Reihenfolge-Frage und gruppensequentiellen Blicken.
   Bei **gleicher Fehlerrate je Test** (alpha 0,0025 wie C.10 heute) braucht ein sequentieller Test unter H1 im
   Erwartungswert 0,87 der festen Fallzahl (Maximum 1,007); die Ersparnis von rund 31 % gilt gegen C.10 mit gemeinsamer
   Power 0,80, gegen die heutige Praxis (gemeinsam 0,64) nur rund 6 %. Das Regime ist an drei Stellen eine Lockerung
   (etikettiert; "neutral in alpha" nur bei festem alpha je Test) und an vier eine Verschaerfung. **Es verkleinert aber
   nicht die Datenmenge fuer einen Effekt gegebener Groesse (Wurzelgesetz):** A3-roh, VRP und A4 bleiben Jahre
   entfernt. Die drei Analysen schlagen fuer das Fehlerbudget drei unvereinbare Varianten vor; sie stehen als Optionen
   in P-2. [Grundsatzanalyse T-12; Architektur 3; Kritik K-7/K-8; Review B-7, B-8, W-1, W-2]
8. **Vollautomatische Institution.** Heute ist die Maschine nicht der Engpass (1..30 h je Befund); die Zeit geht in
   Nutzerfragen (eine seit 14 Tagen offen), in 17 Weiterleitungen an Data-Harvest in drei Wochen und in Prosa
   (Pflichtlektuere ~650 kB). Soll: zehn Bausteine (Ledger als einzige Wahrheit, Fensterregister mit K- und FDR-Buch,
   Datenzugangsschicht mit Statistikklassen und Kanal-Scan, Feasibility-Rechner auf Nuisance-Katalog, generischer
   Lauf-/Kontrollrahmen, Entscheidungswarteschlange mit Default und Frist). Fahrplan F0..F6 in ~90 Tagen, grob 120..180
   Agentenstunden. Zehn einmalige Nutzerentscheidungen, danach nur noch Geld, Daten, Recht, Programmrichtung.
   [Architektur 2, 5]
9. **Nicht-statistische Luecken.** Strenge-Ratsche ohne Gegenkraft (Reviews duerfen nur verschaerfen; keine
   Schleifen-Obergrenze); Zustand als Prosa statt Maschine (~220 kB bindende Nachtraege, keine konsolidierte Fassung);
   61 Akten-Verweise auf unversionierte Skripte (der Verlust des Arbeitsbereichs am 2026-10-31 hat das gezeigt); Siegel
   durch Disziplin statt Code (B-2-Kanal der A2-Vorperiode); der Nutzer als einziger Literaturkanal bei gesperrtem
   Netz; Defaults stets die strengste Option, also Drift in den Aufzeichnungsmodus; eine Lockerung (DEC-94) wurde vom
   Orchestrator ohne ausdrueckliche Nutzerzustimmung im Text beschlossen. [Grundsatzanalyse T-13..T-17; Faktenblatt
   T4.4; Architektur 1.3, 4]
10. **Was ich ohne dich sofort tun kann** (Abschnitt 9.2): Rechenkorrekturen als Errata (K-1-Konstante, Lo-Beispiel,
    K-0.6, exakte P2''-Bedingung als Doppelausweis neben dem Produkt), Pflicht-Berichtszeile "Schaetzer, 95-%-CI, obere
    Ausschlussgrenze" fuer jeden Lauf, Kanal-Scan als Test im Repo, Versionierung aller Herleitungs- und Pruefskripte
    (F0), Konto aller geoeffneten Statistik-x-Fenster-Paare, Bedarfsbilanz der knappen Blinddaten, Vorwissens-Register
    je Datenfamilie, Feasibility-Rechner und Klassen-Feasibility, Inhaltsproben (Optionskette bis 2026-06,
    Negativ-Panel aus Trades, L2 2023-2025), H-21-Lueckenliste, PRD-v3-Konsolidierung als Entwurf,
    Datenannahmen-Register. **Was nur du entscheiden kannst** (Abschnitt 9.1): Fehlerbudget und Power-Ziel auf der
    Entscheidungsregel (K-4/K-6), SESOI oder Prior-Verteilung statt Literatur-Punktprior (K-10, T-2), Drei-Zonen-Regime
    mit Kohorten und sequentiellen Blicken (T-12, E-1..E-5), nuisance-adaptive Designwahl als Nicht-Torpfosten (K-7),
    REZENZ als pruefbare Hypothese statt harter Schnitt (K-12), A2-Zuordnungsregel (P-7), Netzfreigabe fuer
    Volltextquellen, Budget.
11. **Was nicht folgt.** Kein Verdikt kippt, keine Kante entsteht, kein Siegel wird geoeffnet; alle Power-Zahlen sind
    Aufloesungsgrenzen aus Akten-Nuisance mit markierten Annahmen (Normalnaeherung; bei schweren Raendern und 40..52
    Clustern eher zu optimistisch); mehrere Vorschlaege sind Lockerungen und als solche etikettiert. Drei Korrekturen
    am eigenen Stand: H-26 ist nach der strengen Lesart der Aufzeichnungstage erst ab 2027-04-06 entsperrt (nicht
    "jetzt", wie am 2026-11-01 vormittags gesagt); H-21 ist wegen des 14-Tage-Ausfallmusters des Live-Sammlers in der
    registrierten Form vermutlich nicht entsperrbar [V bis zur Lueckenliste]; und W1/W2 sind fuer Klasse W **blind**
    (GL-035/036: ungeoeffnet; nur rev1 in W2 vorbelastet) - "durch Disziplin" blind ist allein die A2-Vorperiode.

---

## 1. Fehler und ungenaue Annahmen im PRD und in der Verfassung

Die Kritik (Anhang `KRITIK_PRD.md`, Befunde K-1..K-14) wurde vom Review gegen die Primaerquellen geprueft; die
Kernrechnungen K-1, K-2, K-3 und die Review-Korrekturen zu K-5 und K-7 hat der Orchestrator unabhaengig nachvollzogen
(`scripts/orch_review_check.py`). Tabelle: Befund, Beleg, Folge, Richtung der Korrektur, Entscheider. Markierungen:
[V] = Vermutung/Rueckschau, [R] = Rechnung.

| Nr. | Befund | Beleg (Kurz) | Folge | Korrektur / Richtung | Entscheider |
|---|---|---|---|---|---|
| K-1 | Horizont-Friktions-Kurve unterschaetzt die Kante um pi/2 (Rang-IC: pi^2/6) | Unter bivariater Normalitaet gilt E[r sign(s)] = IC x 0,798 sigma; PRD rechnet (2/pi) arcsin(IC) x 0,798 sigma. MC 4 Mio.: 0,0397 gegen PRD 0,0254. PRD 9.2 "~7 h Maker" sind mit der PRD-Formel 8,7 h; "Abstand halbiert" ist ein Drittel | Mindesthorizont x2,5 zu lang (Wochen-IC 0,05: 1,1 statt 2,7 Tage); IC_min 0,040 statt 0,062; Mission "kein Kandidat unter Tageshorizont" steht auf einer Zahl mit Fehlerfaktor 2,5 (Modell) x 4 (Kosten). Kategorialer Rest: Querschnitts-IC als Einzelasset-Zeitreihenkorrelation gelesen | Konstante K-0.1 als Kurvenschar neu fuehren, L-18-Vermerk (neutral, O). Stundenhorizonte zu oeffnen waere N und muesste D.4, D.12, D.14 als Nicht-Wiederholungs-Nachweis (C.1) adressieren | O; Mission/Stunden: N |
| K-2 | "Praemie statt Sharpe" verkuerzt nichts | t = mean/(sd/sqrt n) = SR sqrt(n); C.10 mit 12 Monaten verlangt SR_eff >= 2,49 je Fenster (1,76 bei 2, 1,44 bei 3 Jahren); A1 1,95; H-27 mit dem gueltigen Prior 7,14 VP (DEC-98 N2) 1,38 = 1.183 Tage je Fenster (mit dem ueberholten 9,47: 1,83 = 672) | Lo-Beispiel PRD 3.6 rechnet mit q = 12 statt 365 (1,80 statt 1,55 Jahre). Die Schwelle 2,49 war am PRD-Tag bekannt; die Nuisance (18,6 VP, 372,9 bp) erst mit DEC-93/97 [V] | Klassen-Feasibility vor jeder Herleitung (neutral); Fensterlaenge als abgeleitete Groesse (Testbarkeit) | O / N |
| K-3 | WP-7-Rauschboden ist eine Identitaet | Permutations-Spearman hat Var 1/(K-1) unabhaengig von der Renditestruktur (MC K 200 mit/ohne Faktor 0,0722 / 0,0718 gegen 0,0709); Breite wirkt nur ueber die Zeitreihenvarianz von IC_t (GL-035: 2,3..2,6x gegen die faktorerhaltende Null) | PRD 4.1 ("enthaelt die effektive Breite exakt") und DEC-67 B2 waren falsch; DEC-74 hielt die Identitaet fest; "DEC-73..92 vermeidbar" ist Rueckschau [V] | Feasibility auf der SD der Teststatistik selbst; L-2b operational (Zensus-Schaetzer muss auf Faktor-Null anders reagieren als auf iid-Panel); Null-Fixture mit Faktorstruktur (Strenge) | O |
| K-4 | Nominale Power 0,80 ist Entscheidungs-Power 0,64 | (1-beta)^2; gleiche Daten gepoolt bei alpha 0,0025: 0,76; DEC-52-Rate unter Abhaengigkeit ~0,99 % (ohne Screens) / 0,85 % (mit) statt 0,5 % | Regime-Robustheit seit DEC-99 doppelt kodiert | Power-Ziel auf der vollstaendigen Entscheidungsregel definieren; Datenfaktoren: C.10 gemeinsam 0,80 statt je 0,80 +36 %; gepoolt 0,0025 gegen C.10 je 0,80 +8 %; C.10 gemeinsam 0,80 gegen gepoolt +26 % (einheitliche Basis DEC-98 E1 (c)) | N |
| K-5 | Kumulierte Strenge ohne Gesamt-Operationscharakteristik | A2 W2: 18,8 -> 19,7 (P3fix bindend) -> 23,1 (drei Placebos) -> 24,4 (Null-Faktor im Produkt) -> 27,2 (Stress bindend) -> 29,3 (skalierte Null) -> 32,1 bp (Gate-(4)-Faktor); exakte gemeinsame Power zentral 22,3. Null-Bedingung und P2''-Bedingung sind korreliert (0,82 W2 / 0,91 W1), nicht identisch: zwei Bedingungen je 0,90 geben exakt 0,858 / 0,870 statt Produkt 0,81 [R]; Akte fuehrt die exakte P2''-Bedingung schon (22,93 / 23,77 gegen Produkt 23,43 / 24,36), Artefaktanteil 0,5..0,6 bp. UNBELEGT-Default 0,95 nur in Richtung Strenge; Maximum-Regeln stapeln Aufwaertsverzerrungen | Pilot-Route uebergibt praktisch nie; alpha-Seite ohnehin <= 0,25 %. Der Orchestrator hat die Festlegungen Null-Faktor, skalierte Null, Stress bindend, Gate (4) am 2026-10-31 selbst getroffen (DEC-103 N1 (8a-f), nach Kenntnis von REVIEW_A2_TEILC B-4) | (1) exakte P2''-Bedingung neben dem Produkt als Doppelausweis sofort (O); Umstellung der Zuordnungsgrundlage auf die exakte Bedingung ist eine Gabelung Richtung Testbarkeit, alpha unveraendert -> P-7; (2) exakte gemeinsame Power statt Produkt (aendert DEC-94 (6)) N; (3) OC-Zeile P(PASS bei 0), P(PASS bei SESOI), P(PASS bei Prior) als Pflicht (O als Bericht, N als Regel); (4) UNBELEGT symmetrisch aendert Arbeitsregel 4 -> N | (1) O + P-7; (2),(3),(4) N |
| K-6 | Fehlerbudget invertiert | PPV eines Mess-PASS bei Basisrate 10 %: C.10 0,97, gepoolt 0,0025 0,97, gepoolt 0,01 0,90, ein Fenster 0,05 0,64; ein PASS kauft nur den naechsten gegateten Schritt, ein GL-012 null Information | alpha 20x strenger als nominal, Power unkontrolliert: zwei Monate, fuenf Kandidaten, null Tests. "A3-Roh-IC testbar gegen 0,03" (MDE 0,024 gepoolt) haengt an einem Prior, den DEC-98 N2 als unbelegt einstuft - gegen welchen Wert, bleibt offen | Programm-Fehlerbudget (Optionen in P-2: gepoolt alpha 0,0025 + REZENZ-Screen; C.10 behalten mit GSD je Fenster; gepoolt 0,01 = Lockerung x4), gemeinsame Power 0,80, Pflicht-Bestaetigung auf neuen Daten vor jeder Tradability-Frage | N |
| K-7 | Power-/Prior-/Fensterlaengen-Wahlen sind je Test keine Torpfosten - mit drei Ausnahmen | Die Schwelle rechnet mit der Lauf-SE; nuisance-basierte Designwahl vor jedem Outcome aendert alpha des Tests nicht (Stein 1945; verblindete Fallzahl-Neuschaetzung). Ausnahmen: (i) A2: DEC-103 E4 bindet die Schwellen-SE an das Maximum aus Vorperiode und Null-Simulation, Nuisance-Wahlen verschieben dort das effektive alpha; (ii) Vorwissen der Agenten bei historischen Fenstern (DEC-96 E1; greift fuer A1, Formation in W1/W2 gesehen); (iii) Programmebene: mehr testbare Designs -> mehr Tests je Jahr -> mehr erwartete Falsch-Entdeckungen trotz FDR je Familie | Jede Designanpassung wird als Lockerung zum Nutzer getragen, ohne Validitaetsgewinn; H-27 waere auch mit angepasster Laenge nicht vor 2029-07 (oberer Prior-Rand 10,48 VP: 549 Tage je Fenster) bis 2033-01 (Referenz 7,14: 1.183 Tage) entscheidbar | Verfassungszeile "nuisance-adaptive Designwahl": registriertes Design-Menue + mechanische Auswahlregel nur auf Vorperioden-Nuisance und SESOI/Prior; C.17 bleibt; Ausnahmen (i)-(iii) ausdruecklich benennen; Vorwissens-Klasse je Datenfamilie (BTC/ETH-Aggregate: nur prospektiv) als Regel | N (Auslegung), Vorbereitung O |
| K-8 | Blind-Siegel hortet verderbliche Daten | Siegel sperrt alle Klassen ab 2026-07-01 fuer eine VRP, die vor 2029-07 nicht testbar ist; REZENZ macht ungenutzte Fenster verderblich; Blindheit durch Disziplin ist im oeffentlichen Repo bruechig (B-2-Kanal, nur A2-Vorperiode) | Reihenfolge-Frage seit 2026-10-18 offen; niemand rechnet auf den juengsten Daten; die Bedarfsbilanz der Blinddaten (Abschnitt 6) fehlte bisher | Gemeinsame Vorab-Registrierung aller Blindperioden-Designs (DEC-98 E1 (d) erlaubt es), GSD-Blicke, Lockbox je Design; Siegel nur fuer registrierte Statistiken (Testbarkeit, alpha neutral) | N |
| K-9 | Pilot-Route: Uebergabe nur bei voller Test-Staerke | P(Uebergabe bei mu = c) = 0,5 per Konstruktion; nicht uebergebene Varianten bleiben im BH-Nenner (doppelte Selektionsstrafe) | A2-Pilot: Uebergabe bei 16,5 bp 7e-5 (stress), bei 25 bp 0,04 | Assurance/praediktive Power (0,3..0,5) oder adaptiver Kombinationstest; Nenner-Regel korrigieren (Testbarkeit, alpha neutral) | N (DEC-99) |
| K-10 | Literatur-Prior-Pflicht ist eine Ressourcenregel | Ein Prior schuetzt keine Fehlerrate; publizierte Effekte sind nach oben verzerrt (McLean/Pontiff); Belegregel selektiv (IC 0,03 akzeptiert, 12 bp verworfen) | A1, A2, H-33, VRP enden bei UNBELEGT statt bei einer definitiven Aussage | SESOI (kleinste oekonomisch relevante Wirkung) als Feasibility-Massstab: A1 (MDE 129 bp gegen 36; 12,8 Jahre je Fenster) und VRP (12,9 gegen ~1,5 VP) **strukturell** geschlossen statt "UNBELEGT". **A2 ist damit nicht "heute registrierbar":** unter dem geltenden Placebosatz (DEC-103 E3) liegt die W2-MDE80 bei exakt 22,3 / Produkt 24,4 / stress 27,2 bp, alle ueber der Taker-SESOI 22 bp; darunter kommt nur der Einzel-Placebo P2'' (18,8) oder ein gepoolter Test (16,7 bei alpha 0,01 / 19,2 bei 0,0025), beides N; mit der Maker-SESOI (10,8 bp) in keiner Lesart. "Taker statt Maker" ist die Gabelung, die entscheidet (Testbarkeit, zu etikettieren); eine SESOI aus der Wand erbt deren Unsicherheit (K-1: Faktor 2,5 x 4; PRD 4.1/9.3 B-7 hatte die Feasibility deshalb von der Wand entkoppelt). C.2-Ausdehnung auf Feasibility-Kills zurueck (Klarheit) | N |
| K-11 | Pivot-Begruendung unvollstaendig | "2.0 starb an der Friktionswand" ist kein PRD-Zitat; PRD Par. 1 nennt Sekunden-/Minuten-Horizonte arithmetisch tot (1-s-Orakel 0,71 bp) - das gilt unabhaengig davon, dass H-03 (Surrogate-p ~1,0), H-09 (Rauschmuster), H-24 (Vorzeichen) am fehlenden Signal scheiterten; nur H-04b/H-05c starben an der Friktion; Wand = VIP0-Taker, ~4 bp Slippage ungemessen, Nutzer-Gebuehrenstufe nie erfragt | Der dominante 2.0-Fehlermodus "kein Signal" wird durch den Horizontwechsel nicht adressiert | PRD 1 ergaenzen; Wand als Parametersatz mit Sensitivitaet; Nutzer nennt Gebuehrenstufe (neutral) | O / N |
| K-12 | Klasse P endet per Verfassung in PARK; REZENZ nur in Richtung Strenge | PRD 3.6 Auflagen: bestes Ergebnis = PARK (L-12 verletzt); Stress 2021/22 bindet A2-Fenster 2024-26, waehrend Alt-Daten als Evidenz verboten sind | Klasse P doppelt leer | Klasse P als Mess-/Aufzeichnungsprogramm fuehren oder Kapitalregel ohne MinTRL; REZENZ als pruefbare Hypothese (gepoolt + Stabilitaetstest); Nuisance-Symmetrie (juengstes Vorfenster bindend) - fuer A2 ist das eine Lockerung des effektiven alpha Richtung Nominalwert (K-7 (i)), also N, nicht "neutral" | N |
| K-13 | Datenannahmen ueberholt | REST-Backfill-Plan ueberholt (Archiv hat kline1d/fundingRateAll ALL ab 2021); PIT-Roster rekonstruiert (DEC-100); OI-Probe still entfallen; `tardis/options_chain` 91 Monatsstichtage 2019-04..2026-10 (87 vor dem Siegel; D.17 stuetzt sich auf die Dichte "1 Tag je Monat", DATA_INVENTORY 2026-08-10, und bleibt fuer dichte Ketten-Kandidaten gueltig - neu ist nur die Tiefe); Negativ-Panel aus publicTrade baubar; H-21 in der registrierten Form nicht entsperrbar [V]; H-26 erst 2027-04 | Mehrere PRD-Zeilen falsch oder tot | Datenannahmen-Register; Inhaltsprobe Optionskette nur fuer Stichtage <= 2026-06-01; monatliche Skew-/Term-Designs als neue Hypothesen nach C.8-Inhaltsprobe, keine D.17-Revision; H-21-Lueckenliste (S0, im Siegel erlaubt) (neutral) | O |
| K-14 | Innere Widersprueche | A4 "8 Quartale" vs "12+ Monate"; SR-Decke in SR-Einheiten gegen bp-Statistik; MDE-Faktor als Schwelle (fuenf Wochen); STRESS_ABS liefert in den Fenstern 1..2 Tage (Design-Parameter nie auf Erreichbarkeit geprueft); Fehlerraten unter Unabhaengigkeit mal lockernd, mal verschaerfend; UNBELEGT asymmetrisch; "eine Datei, eine Wahrheit" gilt nicht fuer die Verfassung (~220 kB Nachtraege); Modellbezeichnungen im oeffentlichen Repo (PRD 3.9, CLAUDE.md) | Autonomer Betrieb auf dieser Textbasis riskant | PRD v3 konsolidiert, Errata, Erreichbarkeitspruefung je Design-Parameter, Rollen statt Modellnamen (neutral) | O (CLAUDE.md: N) |

**Orchestrator-Nachrechnung (eigener Code, nur Formeln; `scripts/orch_review_check.py`, Ausgabe
`scripts/orch_review_check.out`):** K-1: Faktor 1,571 bei IC 0,05 bestaetigt (E[r sign(s)] = rho x 0,798 sigma gegen
(2/pi) arcsin(rho) x 0,798 sigma); die eigene Vorrechnung vom 2026-11-01 (Tageshorizont, r_min = 2,4865/sqrt(n))
benutzte bereits die konsistente Form. K-2: SE(12 Monate) = 18,6 x sqrt(28,2/365) = 5,17 VP; Prior 7,14: SR_eff 1,381
-> 3,24 Jahre = 1.183 Tage je Fenster; Prior 10,48: 549 Tage; 9,47 (ueberholt): 673 Tage. K-3: Permutationsvarianz
des Spearman-rho 1/(K-1) exakt, unabhaengig von der Kovarianz der Renditen; die 2,3..2,6-fache reale IC-Streuung des
H-32-Piloten ist genau der fehlende Breiten-/Faktorterm. K-5 (a): zwei Bedingungen je Power 0,90 bei Korrelation
0,82 / 0,91 / 1,0 geben gemeinsam 0,858 / 0,870 / 0,900 gegen Produkt 0,810; "quadriert" ist nur der Grenzfall
Korrelation 1 - meine Formulierung vom 2026-11-01 vormittags ("Rechenartefakt, streichen") war ueberzogen, der Review
hat recht. K-4/K-6: Datenfaktoren 1,356 / 1,077 / 1,259; PPV-Tabelle identisch. GSD: OBF 4 Blicke, Maximum 1,034
(alpha 0,05) / 1,008 (0,0025), E[N bei H1] 0,814 / 0,872 (Monte Carlo 2 Mio. Pfade).

## 2. Edge-Inventur: was die bisherigen Ergebnisse hergeben

Quelle: Anhang `EDGE_INVENTUR.md` (32 Befunde E-1..E-32, Fensterkarte, Rangliste; Rechenskript `scripts/edge_calc.py`).
Zusammenfassung mit Review-Korrekturen:

- **Kein bestandenes Gate fuer eine Groesse oberhalb der Wand** - weder in 2.0 (31 Eintraege) noch in 3.0 (kein Lauf
  auf einem Urteilsfenster).
- **Echte Mikrostruktur-Signale (2.0):** Lead-Lag BTC->ETH auf 1-3 s (H-04/H-18), inverse OFI-Nachfuellung (H-05b),
  Trade-Tape-Grammatik (H-15), Venue-Fingerprint (H-23), permanenter Minuten-Impact mit stabil negativem Forward-IC
  ueber zehn Halbjahre (H-24, die einzige regime-invariante Groesse des Programms). Alle 80..500x unter der Wand oder
  ohne oekonomische Groesse; keine Horizontbruecke registriert (DAY-BRIDGE nie gebaut).
- **Strukturbefunde des 3.0-Zensus** (nie promovierbar, aber Kalibrierbasis): reale Wochen-IC-Streuung 2,3..2,6x der
  faktorerhaltenden Ein-Faktor-Null; Funding-Totzone 47 % (F = I); Stress-Kohaerenz der Praemien 0,6..0,7 gegen
  0,2..0,35; potenzgesetzartiger Nach-Schock-Zerfall; taeglicher Verfallskalender seit 2020-03-25; sigma30-Klassen
  (Freitag 43,8 bp Cluster, Wochenende 0,82x); OI-Verhaeltnis Freitag/Mo-Do 13x; Universum nach Umsatz liquide.
- **Genau ein preisprognostischer Querschnittsbefund mit |t| > 3:** der H-32-Pilot (beta-neutrales Momentum 2022-04..
  2024-06 negativ, t -3,3..-4,1, gegen die registrierte Richtung; Screening, Abschnitt verbraucht). Seine implizite
  Informationsrate (2,3..2,8 p.a.) ist hoch fuer liquide Universen (Literatur: 0,99..1,66 liquide, bis 3,09
  illiquide), nicht unplausibel an sich; die Variante mit maximalem |t| aus K = 4 traegt den Winner's Curse, DEC-99 (3)
  verlangt fuer Pilot-Priors den selektionsbereinigten Schaetzer.
- **Rangliste nach Erkenntniswert je Kalenderzeit** (keine Registrierungsempfehlung): R-1 Reversal auf blinden
  prospektiven Fenstern - Leitzahl **75 % des Pilot-Betrags: 74..113 Wochen je Fenster, voll ~2029-08..2031-02**
  (beim vollen Betrag 42..64 Wochen, 2028-05..2029-03, keine programmkonforme Obergrenze; beim halben Betrag 167..255
  Wochen, 2033+); blockiert durch fehlenden Literatur-Prior und Reihenfolge-Frage. R-2 VRP (2029-07..2033-01), R-3 A1
  (2030+ nur mit theta), R-4 A2 (nur fuer Effekte ab ~25-30 bp), R-5 A4, R-6 Listing-/Delisting-Ereignisse (neu), R-7
  Funding-Cap-Treffer (neu), R-8 Skew (gesperrt).
- **Drei Aktenbefunde, die bisher nirgends standen:** (i) H-21 (2.0) ist mit dem 14-Tage-Ausfallmuster des
  Live-Sammlers (allLiquidation 125 von 139 Tagen; dasselbe Muster bei deribit/markprice.options und deribit/orderbook)
  und der Lage beider Fenster in der Blindperiode in der registrierten Form (lueckenlose done_days in festen Fenstern,
  KOMP E.1) vermutlich nicht entsperrbar [V bis zur Lueckenliste; Nicht-Nachladbarkeit [V]]. (ii) `tardis/options_chain`
  liegt mit 91 Monatsstichtagen 2019-04..2026-10 vor (87 vor dem Siegel); D.17 bleibt unberuehrt (es beruht auf der
  Dichte, nicht auf "2 Tagen"), neu ist die Tiefe: monatliche Skew-/Term-/VRP-Designs waeren neue Hypothesen nach einer
  C.8-Inhaltsprobe. (iii) Die Kontaminations-Inventur des Blindbereichs fuehrt WP-10(B) (Mid-Renditen bis 2026-09-16)
  und H-24 W-R2 (bis 2026-07-31) nicht.
- **Wiederverwertung:** der Pilot darf Richtung und Streuung liefern, nie den Betrag als Prior (GL-035, DEC-102 E3);
  ob ein vorzeichengedrehter, vorab geschrumpfter Pilot-Betrag als Prior zulaessig sein soll, ist eine Programmfrage
  (S-5, Testbarkeit).
- **Luecke aller Edge-Zahlen:** die L/S-"Brutto"-Renditen (A3, F1, R-1) enthalten keine Funding-Zahlungen, keine
  Short-Restriktionen/Caps und keine Rendite am Delisting-Tag; bei Mehrtageshorizonten ueberlappen die Outcomes (c > 1).

## 3. Die Grundidee: wie weit sind wir?

Quelle: Anhang `KONZEPT_UND_FORSCHUNGSFELDER.md` (T-1..T-7). Urteil des Orchestrators nach eigener Lektuere:

- **Realisiert (Pruefdisziplin):** Registry mit Hash und Pins, Blind-Siegel mit Waechtern, gemessener Rauschboden,
  hypothesenspezifische Nullmodelle (faktorerhaltende Null, Peso-Fixture, Label-Permutation), Positivkontrolle in
  Produktionskonfiguration (fing DEC-89/91 vor der ersten realen Zahl), Power mit der SE des registrierten Tests,
  Stress-Kanon, Artefaktpflicht, adversarische Reviews, die in acht Wochen neun materielle Selbstkorrekturen erzwangen.
- **Nicht realisiert (Messinstitution):** kein Effektschaetzer mit Intervall in zwei Monaten 3.0; die Zustandsmaschine
  kennt nur ZENSUS -> REGISTRIERUNG -> LAUF -> GATE; der Zensus misst Nuisance, nie den Effekt. In der Physik ist die
  Standardausgabe ohne Entdeckung die obere Ausschlussgrenze ("Effekt < x bei 95 %"); auf den ~2.000 BTC-Tagen der
  Vorperiode (bis 2026-06; agentenbekannt, also nur als Explorationsmessung mit Konto) liegt sie bei beobachtetem IC 0
  bei 0,037 (rund 8 bp/Tag) - Wissen, das heute nicht erzeugt wird, weil Fenster fuer einen Bestaetigungstest
  aufgespart werden, der laut Bilanz vor 2029 nicht kommt.
- **Fehlende Instrumente, auf heutigen Daten sofort anwendbar:** Ausschlussgrenzen/CI als Pflichtausgabe; eine
  Operating-Characteristics-Simulation der Gate-Kette mit minimalen, je Familie auf der Vorperiode validierten
  Nullwelten (A3 baute seine Null sechsmal neu und mehrfach falsch) - ein umfassendes generatives Mehrsymbol-Marktmodell
  (stochastische Vol, Spruenge, Beta-Dispersion, Funding-Mechanik, Delisting-Hazard, Tageszeitprofil) waere dagegen
  Modell-Infrastruktur vor validiertem Signal (Kompendium D.16) und ist N; Mess-Invarianten und Skalengesetze
  (Vol-Skalierung ueber Horizonte, Volumen-Vol-Kopplung, Funding-OI-Liquidations-Kopplung; das 48-Slot-Tageszeitprofil
  entstand als Beifang); Ereigniszeit statt Kalenderzeit (ein 12-Monats-Fenster traegt je nach Jahr die halbe oder
  doppelte Information, Faktor 2,3 zwischen 2021 und 2023); Extremwerttheorie als Nullmodell; Informationstheorie und
  Lead-Lag auf Tagesbasis (nie geprueft). Verfassungsrelevant: sequentielle Inferenz mit Alpha-Spending als Ersatz
  (nicht Ergaenzung) von C.10/DEC-52 - nur mit festem alpha je Test.
- **Daten:** 2,3 TB in 29 Stroemen; 3.0 nutzt Tages-OHLCV plus Funding des Universums und 1-min-Kerzen zweier Symbole.
  Trades (5 Symbole, 2020-2026), Orderbuecher (2023-2026), Optionskette (2019-2026), Optionsticker und Liquidationen
  (ab 2026-06) werden von keinem 3.0-Kandidaten verwendet.

## 4. Was wir konzeptionell und strukturell uebersehen haben

1. **Horizont-Schere** (T-8/T-9, Kritik K-1, Review B-5/B-14): der Tageshorizont ist weder a priori tot noch geprueft.
   Zwei Spalten: **Exploration** auf der Vorperiode (BTC/ETH-Tage bis 2026-06, ~2.000 Tage, agentenbekannt, nur mit
   Konto): MDE80 IC 0,056 (11,6 bp/Tag brutto bei sigma 262 bp), Ausschlussgrenze 0,037. **Konfirmation** unter
   geltenden Regeln nur prospektiv (Vorwissens-Regel R-1, Praezedenz DEC-96 E1): 365 Tage je Jahresfenster -> MDE80
   0,130, Ausschlussgrenze 0,086; fuer IC 0,05 braeuchte ein Fenster ~2.470 Tage. Kostendeckung je Tag haengt an der
   Persistenz des Signals (Vorzeichenwechselrate eines AR(1): 0,50 / 0,33 / 0,21 bei phi 0 / 0,5 / 0,8): Maker 4 bp ->
   IC_min 0,0096 / 0,0064 / 0,0039; Taker 11 bp -> 0,026 / 0,018 / 0,011; gesamt 15 bp -> 0,036 / 0,024 / 0,015. Der
   Tageshorizont ist der einzige Horizont, auf dem ein kapitalfreies PASS nicht automatisch `unter_wand` waere; auf
   BTC/ETH allein ist er aber nur explorativ aufloesbar, konfirmatorisch fuehrt der Weg ueber den Querschnitt (F1).
   Preis des Querschnitts: Bid-Ask-Bounce (Gap-Design), Ueberlappung bei 1-3 Tagen (c > 1), faktorbedingte IC-Streuung.
   Erforderliche OOS-Disziplin: PIT-standardisierte Praediktoren, BTC+ETH ein Cluster, Praediktoren-Register mit K (bei
   K = 10 ist E[max z] 1,58 ~ z_krit), chronologische Zonen, Pflichtausgabe Schaetzer + CI + Ausschlussgrenze,
   Kostenetikett als Kurve (Persistenz, p_fill) statt Konstante.
2. **Fenster-Politik als Produkt** (T-11, Faktenblatt T4): Einmal-Gut x Blind-Siegel x REZENZ x zwei starre
   12-Monats-Fenster; jede neue Klasse braucht 24 Monate unberuehrter Daten nach dem Siegeldatum; das Siegeldatum wandert
   nur vorwaerts; jede Nuisance-Ausgabe bedroht es. Fuer die 12-Monats-Laenge existiert keine Herleitung (DEC-96 E2
   setzt nur das Menue {6, 9, 12}).
3. **Punktprior-Zwang** (T-2, K-10): die Institution kann nur replizieren, nicht entdecken; auf einem jungen Markt mit
   gesperrten Volltexten endet jede Kette bei UNBELEGT.
4. **Strenge-Ratsche** (T-13/T-14, K-5): jeder Review-Schritt ist einzeln begruendet, die Summe begrenzt niemand; es
   gibt keine Schleifen-Obergrenze und keinen symmetrischen Pruefauftrag ("ist der Test gegen den Prior noch sensitiv?").
5. **Fehlerkultur** (T-16): gut im Fangen, spaet im Fangen - alle neun Selbstkorrekturen kamen nach einem Lauf oder im
   Review, keine aus einer Simulation der Pipeline unter H0/H1 (Standard klinischer Studien).
6. **Nutzerrolle** (T-17, Architektur 1.3): "nie fragen" steht neben einer Praxis, in der jede Programmentscheidung beim
   Nutzer liegt und per Default streng ausfaellt; der Nutzer ist zugleich einziger Literaturkanal.
7. **Dokumentation** (T-15, K-14 g): Zustand als Prosa; eine neue Sitzung muss ~6.000 Zeilen lesen, um nichts zu
   verletzen; maschinenlesbar ist nur eine YAML.
8. **Reproduzierbarkeit** (Architektur 1, 4): 61 Akten-Verweise auf unversionierte Skripte; der Verlust des
   Arbeitsbereichs am 2026-10-31 hat gezeigt, dass "Ergebnis-sha256 im Text" nicht genuegt.
9. **Siegel durch Disziplin** (DEC-103 N1 (2)): Waechter nur paketweise, Kanal-Scan ausserhalb des Repos; betroffen ist
   die A2-Vorperiode, nicht W1/W2.
10. **Kosten** (T-18, Architektur 1.4): Die Daten sind nicht der Engpass; die Kosten sind Agentenzeit fuer Herleitung,
    Review und Prosa; ein Kostenbuch existiert nicht.

**Vom Review ergaenzte Luecken, die allen vier Analysen fehlten (Review Abschnitt 4):**

11. **Bedarfsbilanz der knappen Blinddaten.** Alle Vorschlaege konkurrieren um zwei Ressourcen: W1/W2 (2024-07..2026-06)
    und die Siegelperiode ab 2026-07-01. Erste Bilanz in Abschnitt 6; ohne sie ist die Reihenfolge-Frage nicht
    entscheidbar.
12. **Gesamt-Operationscharakteristik des Lockerungspakets.** Die Kritik verlangt eine OC fuer die gestapelte Strenge;
    niemand hat sie fuer das gestapelte Lockerungspaket (gepooltes alpha, SESOI, X-Screens, Kohorten, Budget-GSD, Zone X)
    gerechnet. Ueberschlag in Abschnitt 6; die volle Simulation ist Pflicht vor P-2/P-4 (9.2 Nr. 3).
13. **Schwere Raender und kleine Clusterzahlen.** Alle MDE-, Power- und GSD-Zahlen sind Normalnaeherungen mit bekannter
    Varianz. Akte: Exzess-Kurtosis 5..10 fuer r_pre (NUISANCE_SIGMA30), Merkposten 2,6 (DEC-98 N5); der stationaere
    Bootstrap bei 40..52 Clustern ist eher antikonservativ; Zwischenblicke mit geschaetzter Varianz brauchen t-artige
    Grenzen; Rang-IC gegen Pearson ~5 %. Folge: wahre Power niedriger, wahres alpha eher hoeher als hier angegeben.
14. **Ausfalltage der Live-Stroeme.** Das 14-Tage-Muster (allLiquidation 125/139; deribit/markprice.options;
    deribit/orderbook BNB/SOL/XRP 117/131; Luecken-Karte DEC-98 N4 (f)) trifft alle Live-Stroeme. Prospektive Designs
    auf Live-Stroemen (A4 `rest.tickers15m`, F8 GEX aus `deribit/tickers`, Optionsticker, F9) verlieren effektives N
    und koennen "lueckenlos"-Bedingungen verfehlen; kein Design budgetiert das. Rueckfuellbare REST-Stroeme sind
    lueckenlos.
15. **Perp-spezifische Renditebestandteile.** Funding-Zahlungen als Teil der L/S-Rendite, Short-Restriktionen/Caps,
    Rendite am Delisting-Tag (IPCW) im Tagespanel, Ueberlappung bei Mehrtageshorizonten.
16. **Vorwissen der Agenten als Regel statt Einzelfall.** Nur die Architektur (R-1) macht daraus eine Familienregel.
    Vorschlag: Vorwissens-Klasse je Datenfamilie im Fensterregister; BTC/ETH-Aggregate (Renditen, Vol, IV, Funding
    BTC/ETH): nur prospektiv konfirmierbar; Panel-Querschnitte: W1/W2 blind, soweit nicht per C.17 verbraucht.
17. **Veroeffentlichungs-Scan.** Struktur-Scan nach DEC-103 N1 (2c) und Pruefung auf Hostnamen/Modellnamen vor jedem
    Commit analytischer Dateien (hier durchgefuehrt, Anhang C).

## 5. Unentdeckte Forschungsfelder

Konsolidiert aus der Grundsatzanalyse (F1..F12) und der Edge-Inventur (R-6, R-7, S-4), korrigiert nach Review B-4, B-5,
B-14, B-17. Power-Spalte: analytische Aufloesungsgrenzen (MDE80 nach P-1) aus Akten-Nuisance mit markierten Annahmen,
**keine Effektgroessen**, getrennt nach **Exploration** (Vorperiode bis 2026-06 bzw. alle Tage, nur mit Konto, nie
Verdikt) und **Konfirmation unter geltenden Regeln** (W1/W2 fuer Panel-Querschnitte; nur prospektiv fuer
BTC/ETH-Aggregate; Siegel-Etikett DEC-96 E3 / DEC-98 E1 (b) fuer alles ab 2026-07-01). "Daten jetzt" nach dem
Dateninventar vom 2026-11-01. Rangfolge: Testbarkeit x Passung zur Mission (Wand irrelevant oder kapitalfreie Messung)
x Konflikt mit Kompendium D und verbrauchten Fenstern.

| Rang | Feld / Hypothesenfamilie | Mechanismus und Zahler | Daten jetzt | nachzubestellen | Power: Exploration / Konfirmation | Wand | Haupt-Risiko / Konflikt | Status unter heutigen Regeln |
|---|---|---|---|---|---|---|---|---|
| 1 | **F1 Tages-Querschnitts-Reversal (1-3 Tage, Gap-Design, beta-neutral) auf dem vollen USDT-Perp-Panel** | Liquiditaetsbereitstellung; Zahler: Fluss, der Positionen durchdrueckt, Liquidierte | `rest.kline1d` ALL 2021-01..2026-10 (2.130 Tage, K 300..600), `delisting_dates`, `rest.instruments` | nichts | Annahme SD(IC_t) = 2,5/sqrt(K-1) [V; GL-035 misst 2,3..2,6x gegen die faktorerhaltende Null, im Pilot ~1,8x gegen 1/sqrt(K-1)]. Exploration (alle 2.130 Tage, Konto): 0,0055..0,0078. **Konfirmation W1/W2 je Fenster (365 Tage): 0,0133 (K 600) / 0,0146 (500) / 0,0188 (300)**; Ueberlappung c > 1 bei 1-3 Tagen noch nicht eingerechnet | `unter_wand` beim Taker (Tagesumschlag); Maker-Pfad Bericht | Bid-Ask-Bounce (Gap-Design Pflicht); Universums-Zuordnung der Literatur (H-33-Lehre); Pilotabschnitt 2022-04..2024-06 fuer die Familie "vergangene Renditen" verbraucht (DEC-99 (5), C.17); W2 fuer rev1 vorbelastet (GL-036 (4)); Funding in der L/S-Rendite | Prior: Bianchi et al. [PDF; IC 0,090 EW / 0,023 VW nach Weg A abgeleitet] misst 1-Tages-Reversal **ohne Luecke, ohne Beta-Kontrolle**, Spot-Top-100 2017-22 -> fuer die Gap-Statistik UNBELEGT (Arbeitsregel 4) -> **heute nicht registrierbar**. Variante ohne Gap mit Bianchi-VW 0,023 als Prior-Kandidatin (ueber der W1/W2-MDE), dann Bounce-Kontrolle Pflicht - Programmfrage |
| 2 | **F5 Lebenszyklus-Ereignisse im Panel: Post-Listing-Drift, Delisting-Ankuendigung und letzter Handelstag** | Zwangsschliessung, Listing-Nachfrage; Zahler: Halter ohne Ausstieg | kline1d ALL inkl. Delisteter, `delisting_dates` (306), WP-12-Ankuendigungen (268), `rest.instruments` | nichts (Roster laeuft) | Alt-Tagesvol ~650 bp [V]: N 300 Delistungen MDE80 ~93 bp/Tag; N 800 Listungen ~79 bp/Tag; N_cluster UNGEMESSEN (Chargen). Konfirmation nur auf Ereignissen bis 2026-06 (Ereignis-CAR braucht BTC-Beta, ab 2026-07 gesperrt) | Delisting-Short praktisch unhandelbar; Listing offen | Ankuendigungs- vs. Handelsende-Datum (DEC-100); Chargen = ein Cluster; Reduce-only-Regel zu pruefen (Primaerquelle) | kein Prior in der Akte (Aktien-Delisting-Literatur [sek]) -> Registrierung braucht Prior-Entscheidung; Zaehl-Zensus und Explorationsmessung sofort; die PRD-"8-Wochen-Regel" unterstellt den Effekt ohnehin |
| 3 | **F2 Funding-Dynamik als Tages-Praediktor** (Zeitreihe BTC/ETH; Querschnitt Funding-z) und **R-7 Funding-Cap-Treffer / Auto-Switch als Ereignis** | Ueberhebelte Positionierung -> Abbau; Zahler: spaete Hebelhalter | `rest.fundingRateAll` 2021-01.., `rest.fundingRate` 5 Symbole ab 2024-03, kline1d | nichts | TS BTC/ETH: Exploration Vorperiode 0,056 (11,6 bp/Tag); Konfirmation nur prospektiv 0,13 je Jahr. XS wie F1. Cap-Treffer: 161 Laeufe in 8 Monaten, N_cluster UNBELEGT | TS Taker-Grenze IC 0,011..0,026 (phi 0,8..0), explorativ ueber der Grenze aufloesbar; XS `unter_wand` | Totzone 47 % (nullinflationierter Praediktor); Auto-Switch seit 2025-10-30 (Regimebruch); H-01 war intraday, A1 Wochen-Praemie | Prior UNBELEGT -> heute GL-012 vor Registrierung; als Explorations-Messung mit Ausschlussgrenze sofort |
| 4 | **F4 Mikro-zu-Makro: taeglich aggregierter Netto-Orderfluss -> gleichzeitige Tagesrendite (Kyle-lambda-Invariante) und Folgetag** | Permanenter Impact (B.14) aggregiert | `bybit/publicTrade` 5 Symbole 2020-03.., Bar-Cache (vol_buy/vol_sell) | nichts | Invariante trivial (Vorperiode ~2.000 Tage); Prognose Exploration 0,056; Konfirmation prospektiv 0,13 je Jahr | Prognose an der Wand | D.14 gilt fuer Minuten-Fortsetzung; Tagesaggregation ist andere Statistik (Etikett Pflicht) | Invariante: sofort (Zensus); Prognose: Prior UNBELEGT |
| 5 | **F6 Makro-Ereignisse (FOMC, CPI, NFP): 30-min- und 1-Tages-Fenster, Vor-Ankuendigungs-Drift** | Informationsfreigabe; Zahler: ungehedgte Vol-Verkaeufer, Spaetreagierer | `rest.kline1m` BTC/ETH | oeffentliche Terminkalender (frei) | Slot-SD ~74 bp (A2-Tageszeitprofil 12:30-14:00) [V]. Vorperiode: FOMC ~44 Termine -> MDE80 27,7 bp (1 Tag ~98 bp); CPI ~66 -> 22,6 bp. Konfirmation nur prospektiv (~8 FOMC je Jahr) | ein Trade je Ereignis: `ueber_wand` ab ~15 bp | Krypto-Prior UNBELEGT (Aktien-Vor-FOMC-Drift ~49 bp [sek], seit 2016 verblasst); Slots kontaminieren A2-P3; Termine ab 2026-07 im Siegel | Prior-Entscheidung noetig; Zensus der Slot-Streuung auf der Vorperiode sofort |
| 6 | **F8 Optionsfluss / GEX-Konditionierung der Verfallseffekte** (A2 nur Freitage mit OI im obersten Dezil; Netto-GEX-Vorzeichen) | Hedge-Fluss der Market-Maker skaliert mit ATM-OI (Weiss et al.) | `deribit/tickers` und `bybit/tickers` Optionen seit 2026-06-16 (OI, IV, Greeks je Strike); `tardis/options_chain` nur monatlich | nichts Neues (Strom irreversibel); historisches OI je Strike nicht nachladbar | **Strom liegt fast vollstaendig im Siegel**; die Zielstatistik (r_pre BTC/ETH an Freitagen) ist A2 im Siegel. Vor dem Reihenfolge-Entscheid nur S0 (Zeilen, Luecken, Zeitstempel). Nachrichtlich [V]: 52 GEX-Freitage bis 2027-06 -> 15,1 bp; 104 bis 2028-06 -> 10,7; oberstes OI-Dezil N 10 -> 34 bp | Ereignis, `ueber_wand` ab ~15 bp | Teilmenge klein; K-Inflation durch Konditionierung; Ausfalltage des Live-Stroms; Blindperiode | R3-K-32 war "nicht vor A2-PASS" vertagt; haengt an A2-Option P-3 und der Reihenfolge-Frage |
| 7 | **F3 OI-Dynamik -> Tagesrendite und Tagesvol** | Positionierungsmass; Zahler: Zwangsliquidierte | `rest.openInterest` BTC/ETH ab 2024-03 (970 Tage, davon ~120 im Siegel), 5 Symbole ab 2026-03 | OI-Historie aller Perps (Tiefe UNBELEGT, PRD 7.2 (3) still entfallen) | Exploration Vorperiode ~850 Tage: MDE80 0,085 (17,8 bp/Tag) - grenzwertig; Konfirmation prospektiv 0,13 je Jahr | wie F2 | Vol-Prognose muss gedresste HAR schlagen (B.9) | Prior UNBELEGT; Datenauftrag |
| 8 | **F12 Stablecoin-Angebot und Boersen-Netflows (Tages-/Wochen-Praediktor)** | Primaer-Liquiditaetszufluss; Zahler: Spaetkaeufer | keine | USDT/USDC-Gesamtangebot taeglich (frei, ab ~2021 [sek]); Netflows kommerziell | Exploration N ~1.800 Vorperiodentage: 0,059 / Wochen 0,083; Konfirmation prospektiv | Wochenhorizont `ueber_wand`-faehig ab IC 0,03 | Revisionen; Literatur aeltere Aera | einziges Feld ohne Datenbasis |
| 9 | **F10 Term-Struktur der Basis auf Deribit-Futures seit 2017 (A4-Vorlaeufer)** | Laufzeitsicherheit (Hedger zahlt) | `rest.settlements` ab 2017, `rest.deliveryPrices` ab 2016; Einstiegsbasis fehlt | Probe: historische Kurse abgelaufener Deribit-Futures (oeffentlich? UNBELEGT) | ~34 Quartale bis 2026-06: MDE80 0,43 sigma_w (statt 0,88 bei 8) | kapitalgebunden 90 Tage; `ueber_wand` laut R1 | sigma_w UNGEMESSEN; inverse Kontrakte (anderes Produkt als Bybit-A4) | Datenprobe zuerst |
| 10 | **F11 Zustandsabhaengigkeit (DVOL-Terzile, HMM) als Modellvergleich** statt zweier Tests | Praemien regimeabhaengig (WP-10(A2)) | `deribit/dvol` 2021-03.., RV aus kline1m | nichts | je Terzil N/3: MDE80 x1,73 des Basisfelds | wie Basisfeld | Forking paths (K); C-08 "Ockham-tot" nur als Konditionierung nicht einschlaegig | nur als registrierte Variante eines Basisfelds |
| 11 | **F7 Informationsfluss zwischen Venues/Instrumenten auf Tagesbasis** (Fluss-Anteile, Transfer-Entropie) | Informierte Venue-Wahl | `binance/publicTrade` BTC ab 2025-01 (610 Tage, ~540 vor dem Siegel), `deribit/publicTrade` ab 2025-08 (Inhalt ungeprueft), bitmex 2026 | Inhaltsprobe `deribit/publicTrade` | Exploration ~540 Tage: MDE80 0,107 - zu kurz; Konfirmation prospektiv | `unter_wand` | Preise arbitragegleich (nur Fluss traegt Information) | zu kurz, Prior UNBELEGT |
| 12 | **F9 Liquidations-Kaskaden** (Groessenverteilung, Branching, Nachlauf in Ereigniszeit; Insurance-Fund) | Zwangsverkaeufe erzeugen Zwangsverkaeufe | `allLiquidation` 5 Symbole ab 2026-06-16 (~139 Tage, davon ~124 im Siegel), `insurance` | Liquidations-Historie anderer Boersen (kommerziell) | **Fast vollstaendig im Siegel**; Zaehlungen/Groessenverteilungen von BTC/ETH-Liquidationen sind Vol-Stellvertreter (DEC-97 A-3) und beruehren die H-21-Fenster -> vor dem Reihenfolge-Entscheid nur S0 | Stunden: unter der Wand; Wert als Nullmodell/Kosten | D.2 (Branching-Schwelle): Erreichbarkeit vor jeder Schwelle; 14-Tage-Ausfallmuster | S0-Zensus (Zeilen, Luecken) zuerst |

**Querbefund (Edge-Inventur S-4, Grundsatzanalyse T-3):** der groesste ungepruefte Hebel der Klasse W ist eine
Mehrfaktor-Null fuer die reale, 2,3..2,6-fach hoehere IC-Streuung - erst messen, ob sie die Streuung reproduziert; nur
dann eine Mehrfaktor-Neutralisierung als Primaerstatistik herleiten (nur Nuisance, keine Lockerung). Dasselbe Paket
waere die Nullwelt der OC-Simulation (Abschnitt 3).

**Was die Felder-Tabelle nicht sagt:** keines dieser Felder hat eine belegte Effektgroesse; **keines ist unter den
heutigen Regeln ohne Programmentscheidung registrierbar** (F1: kein Prior fuer die Gap-Statistik; F5: kein Prior;
BTC/ETH-Felder: nur prospektiv; F8/F9: Siegel). Sofort moeglich sind Zensen (S0/S1) und Explorationsmessungen mit Konto
auf der Vorperiode. Alle Power-Zahlen sind vor einer Herleitung auf der Vorperiode zu messen (nur Streuung) und
Normalnaeherungen (Abschnitt 4, Nr. 13).

## 6. Fenster-Politik: weise nutzen, ohne Jahre zu warten

Zwei unabhaengige Herleitungen (Grundsatzanalyse T-12, Architektur 3) kamen zum selben Regime; der Review hat die
Zahlen nachgerechnet (Anhang C), der Orchestrator ebenfalls.

**Diagnose.** Heute: Einmal-Gut (DEC-98 E1 (d), DEC-99 (5)), Blind-Siegel programmweit (DEC-96 E3), REZENZ (juengstes
Fenster muss bestehen, DEC-99 (1)), zwei starre 12-Monats-Fenster (C.10) - jede neue Klasse braucht 24 Monate
unberuehrter Daten nach dem Siegeldatum; die Reihenfolge-Frage serialisiert alle Klassen hinter einer VRP, die vor
2029-07 nicht testbar ist; REZENZ macht ungenutzte blinde Fenster verderblich (Horten ist nicht kostenlos); Blindheit
durch Agentendisziplin ist im oeffentlichen Repo bruechig (B-2-Kanal der A2-Vorperiode). Statistisch notwendig sind
davon: Vorregistrierung vor dem Blick, Verbot der Nachsuche, Verbuchung aller Tests. Konvention sind: ein Blick mit
fester Fallzahl, Serialisierung, harte 12-Monats-Laenge, Siegel fuer unregistrierte Statistiken (Kritik, Tabelle vor
K-7).

**Bedarfsbilanz der knappen Blinddaten (Review-Luecke 1; erste Fassung, Orchestrator):**

| Ressource | Bestand | Nachfrager (Statistik) | Konflikt | Folge |
|---|---|---|---|---|
| W1/W2 (2024-07..2026-06), Panel-Querschnitte | blind fuer Klasse W (GL-035/036: fm8 ungeoeffnet; rev1 in W2 vorbelastet) | F1 (Tages-Reversal, Gap), A3-fm8, H-33-artige Reversals, F5-Ereignisse (Ereignisse bis 2026-06) | korrelierte Renditefamilien ("vergangene Renditen"); unter Einmal-Gut nur eine Statistik je Familie | nur mit gemeinsamer Vorab-Registrierung (DEC-98 E1 (d)) und BY ueber die Kohorte nutzbar; sonst Serialisierung |
| W1/W2, BTC/ETH-Tagesaggregate | fuer A2 (r_pre Freitage) blind nur durch Disziplin (B-2-Kanal der Vorperiode betrifft 2021-03..2024-05, nicht W1/W2); fuer Vol/RV offen (DEC-95 E2) | A2 (alle Optionen), F2/F3/F4/F6-Tageszeitreihen | A2-Formation und BTC/ETH-Tagesrenditen sind dieselbe Datenfamilie; Agenten kennen RV von W1/W2 | Vorwissens-Regel: BTC/ETH-Aggregate auf W1/W2 nur fuer A2 (registrierte Statistik), alles andere prospektiv |
| Siegelperiode ab 2026-07-01 (heute 4 Monate, waechst 1 Monat je Monat) | versiegelt fuer alle Klassen (DEC-96 E3, DEC-98 E1 (b)) | VRP (1.183 Tage je Fenster), A1 (85+ Wochen), R-1 (74..113 Wochen je Fenster), A2 P-3 (12 Monate), F8 (GEX), F9, H-21 (2026-07..12) | alle wollen dieselben ersten 12..24 Monate; VRP/A1 brauchen 3..6 Jahre und blockieren unter Serialisierung alles | Kohorten-Stichtag mit gemeinsamer Registrierung vor der ersten Rechnung oder Reihenfolge-Entscheid; H-21 vermutlich nicht erfuellbar [V] |
| Vorperiode 2021-01..2024-06 (Panel) und 2021-03..2024-05 (A2) | fuer Renditefamilie durch Pilot verbraucht (2022-04..2024-06, C.17); fuer A2 Nuisance veroeffentlicht | Exploration aller Felder, Nuisance-Zensen, Positivkontrollen | keiner (keine Verdikte) | Zone X mit Konto |

**Vorschlag: Drei-Zonen-Regime mit Konto, Kohorten und sequentiellen Blicken.**
- **Zone X (Exploration):** alles aelter als ~36 Monate, dazu die Abschnitte, die faktisch nicht mehr blind sind
  (Pilotabschnitt 2022-04..2024-06 fuer die Renditefamilie; A2-Vorperiode "durch Disziplin"). Freie, wiederholte
  Nutzung; **Pflicht-Konto** je Abfrage (Statistik x Fenster x Variante, Hash, Familie, K); Ausgaben sind Schaetzer mit
  CI und Ausschlussgrenzen, nie Verdikte. Piloten sind X-Abfragen. **W1/W2 gehoeren nicht dazu**: sie sind die einzigen
  historischen Blindfenster der Klasse W; sie zur Zone X zu erklaeren waere eine reine Lockerung mit genau diesem Preis
  (nicht empfohlen).
- **Zone V (Validierung):** 36..12 Monate alt; genau ein vorab registrierter Blick je Hypothesenfamilie; Blindheit
  mechanisch: eine Hypothese darf nur Quartale nutzen, die bei ihrer Registrierung noch in Zone K lagen.
- **Zone K (Konfirmation):** die juengsten 12 Monate, versiegelt; jedes Quartal wandert das aelteste K-Quartal nach V.
  Registrierte Hypothesen sammeln dort Information in **gruppensequentiellen Blicken** (O'Brien-Fleming, Spending-Plan
  im YAML; Abbruch wegen Wirksamkeit oder Futility; letzter Blick enthaelt das juengste Quartal = REZENZ). Ein Blick
  erzeugt (Verdikt, CI, Hash); die Outcome-Serie des Quartals wird fuer diese Statistik nie mehr geoeffnet.
- **Kohorten-Stichtage:** alle vor einem Quartalsstichtag registrierten Hypothesen teilen die Scheiben (Verallgemeinerung
  von DEC-98 E1 (d)); Multiplizitaet ueber die Kohorte im FDR-Buch. Das macht die Reihenfolge-Frage gegenstandslos.
- **Institutionsweites Fehlerbudget mit festem alpha je Test:** Jahresbudget (alpha-Spending oder FDR q 0,10 BY ueber
  alle Blicke des Jahres einschliesslich Validierung und Pilot-Uebergaben), **aber das alpha je Test bleibt
  festgelegt** (heute 0,0025 gemeinsam); ein Budget, das sich bei wenigen Registrierungen auf wenige Tests verteilt,
  waere sonst eine Lockerung bis Faktor 20.
- **Lockbox statt Agentenblindheit:** codegesicherter Einmalzugriff auf die Urteilsstatistik mit Registrierungs-Hash;
  die Validitaet haengt dann nicht mehr daran, was Agenten gesehen haben.
- **Vorwissens-Klasse je Datenfamilie** im Fensterregister (BTC/ETH-Aggregate: nur prospektiv; Panel-Querschnitte:
  W1/W2 blind, soweit nicht per C.17 verbraucht).

**Zahlen (analytisch; drei Analysen, Review und Orchestrator konsistent, einheitliche Definition: Power 0,80 mit
Maximumsinflation, OBF, 4 Blicke, einseitig):** alpha 0,05: Maximum 1,034..1,035, E[N bei H1] 0,814; **alpha 0,0025
(wie C.10 heute): Maximum 1,007..1,008, E[N bei H1] 0,871..0,872**; Futility (Z < 0 an den Blicken 1-3): E[N bei H0]
0,57..0,65, Maximum 1,20 (0,05) / 1,03 (0,0025). Ersparnis gegen die Zwei-Fenster-Regel: gegen C.10 mit gemeinsamer
Power 0,80 rund 31 %; gegen die heutige Praxis (gemeinsam 0,64) rund 6 % bei hoeherer Power; unter H0 ohne Futility
keine. Mehrkosten zweier Fenster gegen einen gepoolten Test alpha 0,0025 bei gemeinsamer Power 0,80: +26 % (einheitliche
Basis DEC-98 E1 (c)). Kohorten statt Serialisierung: der Datenfaktor 1,54 (vier Hypothesen, Bonferroni je Fenster) ist
eine Obergrenze unter einer Zusatzregel, die nicht gilt - die Akte korrigiert Mehrfachtests ohnehin ueber F-WEEK (BY,
DEC-99 (7)); der echte Mehrpreis des Teilens ist die Abhaengigkeit der Statistiken, die BY abdeckt. **Das Wurzelgesetz
bleibt:** die Mindestdatenmenge fuer einen Effekt gegebener Groesse aendert sich nicht; A3-roh (2 x 119 Wochen), VRP
(2 x 1.183 Tage) und A4 bleiben Jahre entfernt, solange Prior und Nuisance so sind.

**Gesamt-Operationscharakteristik (Review-Luecke 2; Ueberschlag, Normalnaeherung, unabhaengige Tests, Pflicht-Simulation
in 9.2 Nr. 3):**

| Regime | alpha je Test | Power (Entscheidung) | PPV bei Basisrate 10 % / 25 % | erwartete Falsch-PASS je Jahr bei 10 Null-Tests |
|---|---|---|---|---|
| C.10 heute (je Fenster 0,05 und 0,80) | 0,0025 | 0,64 | 0,966 / 0,988 | 0,025 |
| gepoolt 0,0025 + REZENZ-Screen, gemeinsame Power 0,80 | <= 0,0025 | 0,80 | 0,973 / 0,991 | <= 0,025 |
| GSD 4 Blicke OBF bei 0,0025 | 0,0025 | 0,80 (E[N bei H1] 0,87) | 0,973 / 0,991 | 0,025 |
| gepoolt 0,01 (Kritik-Variante) | 0,01 | 0,80 | 0,899 / 0,964 | 0,100 |
| ein Fenster 0,05 (zum Vergleich) | 0,05 | 0,80 | 0,640 / 0,842 | 0,500 |

Nicht in der Tabelle: X-Screens veraendern nicht das alpha der Konfirmation (disjunkte Zone), aber die Basisrate und
den Prior der ausgewaehlten Hypothesen (Winner's Curse -> Power ueberschaetzt); Kohorten-BY haelt die FDR je Kohorte;
schwere Raender und kleine Clusterzahlen erhoehen das wahre alpha. Die Zeile "erwartete Falsch-PASS je Jahr" skaliert
linear mit der Zahl der Tests - der Preis der Testbarkeit ist Zahl, nicht Rate.

**Etikett (Pflicht):**

| Punkt | gegen heute | Richtung | Entscheider |
|---|---|---|---|
| Wiederverwendung von Zone X ohne "Verbrauch" (Konto + K statt DEC-99 (5)) | Lockerung | Testbarkeit | N |
| Korrelierte, aber verschiedene Statistiken duerfen dasselbe Quartal nutzen (BY statt Sperre) | Lockerung | Testbarkeit | N |
| Interimsblicke mit Spending statt zwei Vollfenster (ersetzt C.10/DEC-52 durch EIN Regime) | Lockerung in der Zeit; alpha-neutral **nur bei festem alpha je Test 0,0025**; Wegfall der Zwei-Fenster-Regime-Robustheit (C.10-Zweck, PRD 3.5 (a)) ist eine weitere Lockerung, sofern sie nicht als REZENZ-Screen kodiert wird | Testbarkeit | N |
| Jahresweites Fehlerbudget ueber alle Blicke, Pilots und outcome-beruehrende Zensus | Verschaerfung | Strenge | N |
| Mechanische Blindheit (Registrierung vor Datenexistenz) statt Waechter und Disziplin | Verschaerfung | Strenge | O |
| Futility-Stopp | Verschaerfung | Strenge | N |
| Pflicht-Ausgabe Ausschlussgrenze auch bei GL-012 | Verschaerfung der Berichtspflicht | neutral | O |
| Vorwissens-Klasse je Datenfamilie (BTC/ETH-Aggregate nur prospektiv) | Verschaerfung/Kodifizierung der Praezedenz DEC-96 E1 | Strenge | O (Vorschlag), N bei Abweichung |

**Was der Nutzer dazu entscheiden muss:** Hoehe und Form des Jahresbudgets und das feste alpha je Test; Zonenlaengen
(36/12 Monate) und Freigabekadenz; Ersatz von C.10/DEC-52 durch das sequentielle Regime und Kodierung der
Regime-Robustheit (als REZENZ-Screen oder als zweites Fenster); Behandlung des Pilotabschnitts und der A2-Vorperiode
als Zone X (W1/W2 bleiben blind); ob Explorations-Schaetzer die Richtung einer Registrierung bestimmen duerfen (im
Konto-Regime der Normalfall, bezahlt ueber K).

## 7. Die vollautomatische Analyseinstitution: Ist, Soll, Fahrplan

Quelle: Anhang `ARCHITEKTUR_AUTOMATION.md`.

**Ist.** Automatisiert: Datenclient (Katalog, Laden, Luecken), `power_p1` (generisch, 32 Tests), die H-32-Pipeline mit
Pins, Pilot-Sperre, Schnitt-Waechter und skalierter Null (5.794 Zeilen fuer eine Hypothesenfamilie). Von Hand:
Spezifikationen, Abnahmen, Nachrechnungen, DEC-Texte, Commits, C.17-Listen, Dateninventar. Nutzer: Programmfragen (7 in
23 Tagen, 2 offen), 17 Weiterleitungen an Data-Harvest, Volltexte. Maschinenzeit je Feasibility-Befund 1..30 h;
Wartezeit kommt aus Nutzerlatenz (1-5 Tage je Frage) und Dokumentation (Pflichtlektuere ~650 kB). Kein Kostenbuch.
Reproduzierbarkeitsschuld: 61 unversionierte Skriptverweise. Registry-Linter (PRD 3.4) nie gebaut.

**Soll - zehn Bausteine:** (1) Ledger als einzige Wahrheit (Hash-Kette; Prosa als gerenderte Sicht); (2) JSON-Schema der
zwoelf Pflichtzeilen mit Linter (loud fail); (3) Fensterregister mit K- und FDR-Buch (Zonen, Kohorten, Verbrauch,
Vorwissens-Klasse je Datenfamilie, C.17-Generator); (4) Datenzugangsschicht mit Statistikklassen S0 (Zaehlung) / S1
(Streuung) / S2 (Screen, registriert) / S3 (Gate-Bit) und Kanal-Scan in der CI, Schluesseltrennung
Exploration/Konfirmation, Ausfalltage-Budget fuer Live-Stroeme; (5) Nuisance-Katalog und Feasibility-Rechner
(Klassen-Feasibility: SR-Aequivalent je Fensterlaenge, MDE80 gegen SESOI/Prior-Verteilung, zwei Spalten
Exploration/Konfirmation); (6) Hypothesen-Generator (Ideenkarten mit Mechanismus/Zahler/Horizont/Wand, Literatur-Suche
soweit Netz erlaubt, X-Screens mit Konto); (7) generischer Lauf-Rahmen (Manifest-Runner, Gate als Daten,
Artefakt-Writer DEC-53, Positiv-/Negativkontrolle, Nachrechnung als Code); (8) Pruefschleifen (adversarischer Reviewer
mit symmetrischem Mandat, Schleifen-Obergrenze, OC-Simulation >= 1.000 Seeds als T0); (9) Dokumentation generiert
(Registry, Gate-Log, Digest); (10) Entscheidungswarteschlange mit Default und Frist (Nutzer woechentlich gesammelt; auf
dem kritischen Pfad nur Geld und Recht).

**Fahrplan (90 Tage, grob 120..180 Agentenstunden; Schaetzung ohne Kostenbuch):** F0 Schadensbegrenzung (Woche 1:
Skripte versionieren, Kanal-Scan als Test, Kostenbuch) -> F1 Ledger/Schema/Linter -> F2 Register und Datenzugang ->
F3 Feasibility-Rechner (reproduziert GL-032..036 aus Katalog und Akte - **ohne Neulauf von Code, der Siegeldateien
schreibt**) -> F4 Lauf-Rahmen (H-32-Pilot bitgleich aus dem generischen Rahmen; Pilot-Artefakte stehen nicht auf der
Siegelliste) -> F5 Generator und Takt (erste Kohorte vor ihrem Stichtag registriert) -> F6 FDR-Buch, sequentielle
Blicke, Schluesseltrennung. Messgroessen nach 90 Tagen: 0 neue unversionierte Verweise; 100 % Datenzugriffe ueber die
Zugangsschicht; 0 neue Kanal-Befunde; Zeit Ideenkarte -> Feasibility-Befund <= 2 h fuer Standardfamilien; eine
Sammelvorlage je Woche an den Nutzer; **ausdruecklich keine Zielgroesse "PASS/Entdeckungen"** (Anreiz zum p-Hacking).

**Fehlerbilder und Schutz:** Agenten-p-Hacking (Gabelungsregister mit Quote), Siegel-Lecks (Zugangsschicht,
Klassenmatrix, Allowlist, globaler Scan), Spezifikationsdrift (Gate als Daten, generische Gate-Bibliothek),
Kosten-Explosion (Deckel je Hypothese: zwei Herleitungsrunden, dann GL-012 mit Grund), stille Defaults (Schema ohne
Defaults, Datenvertraege), Determinismusverlust (Umgebungs-Manifest, N >= 3), Scratch-Verlust ("keine Zahl ohne
versioniertes Skript" im Linter), Nutzerlatenz (Warteschlange mit Frist, Kohorten), Live-Strom-Ausfaelle
(Ausfalltage-Budget je Design).

**Einmalige Nutzerentscheidungen (E-1..E-10 der Architektur):** Fenster-Politik mit Zonen/Kohorten/Vorwissens-Regel;
Mehrfachtest-Verfahren ueber die Institution; Prior-Regel (X-Pilot/-Screen als Standardquelle, Literatur als Etikett -
Lockerung der PRD-Vorbedingung, FPR je Test unveraendert); Uebergaberegel nach erwartetem Ertrag; gruppensequentielle
Konfirmation; direkter Auftragskanal an Data-Harvest und Schluesseltrennung; versiegelte Zwischenstaende (privater
Speicher oder Hash-only); Netzfreigabe fuer offene Volltextquellen; Budget (Token/CPU je Monat und Hypothese,
Stoppregel bei Leerlauf); Regelaenderungs-Protokoll (Lockerungen nur mit Nutzer und ab naechster Kohorte,
Verschaerfungen durch den Orchestrator). Danach wiederkehrend nur: Geld, neue Datenquellen/Schluessel, Programmrichtung,
Recht. "Kein Live-Order-Code" bleibt unberuehrt.

## 8. Datenauftraege an Data-Harvest (priorisiert, konsolidiert)

| Prio | Auftrag | wofuer | Charakter |
|---|---|---|---|
| 1 | Marktkapitalisierung und Spot-Volumen je Coin, taeglich, Backfill ab 2021 (externe Quelle), kuenftig als PIT-Schnappschuss | Universums-Zuordnung jedes Querschnitts-Priors (H-33-Lehre, F1) | neu, teils irreversibel |
| 2 | Inhaltsprobe `tardis/options_chain` (Boerse, Felder, Stichtag je Monat, Strike-Abdeckung) - **nur Stichtage <= 2026-06-01** | A5/F8-Vorabcheck, Skew-/Term-Struktur-Historie 2019-2026 als neue monatliche Hypothesen (D.17 bleibt) | nur Pruefung |
| 3 | Inhaltsprobe `deribit/publicTrade` Symbole "BTC"/"ETH" (Optionstape? Perp?) | F7, F8, A5 | nur Pruefung |
| 4 | OI-Historie aller Perps (Bybit REST open-interest; Tiefe UNBELEGT - PRD 7.2 (3) still entfallen); Binance-OI-Backfill | F3, Hebelmasse im Querschnitt | Probe, dann Backfill |
| 5 | Stablecoin-Gesamtangebot USDT/USDC taeglich (freie API, ab ~2021) | F12 | neu, frei |
| 6 | Probe: oeffentliche Nachladbarkeit historischer Deribit-Futures-Kurse (abgelaufene Laufzeiten) und Deribit-Perp-Funding | F10 (A4-Analogon mit neun Jahren Historie) | Probe |
| 7 | Negativ-Panel XRP/BNB/SOL 1-min (Anfrage 2026-10-31) - alternativ Ableitung aus `bybit/publicTrade` im eigenen Haus (Trades ab 2021-05/06 lueckenlos) | A2 Gate (4) | laufende Anfrage; Alternative prueft der Orchestrator |
| 8 | Probe: L2-Orderbuch 2023-2025 fuer die benannten Stress-Tage (z. B. 2025-10-10) | WP-10(B)-Stresszelle (RAISE seit DEC-71) | Probe |
| 9 | Ausfalltage des Live-Sammlers: Ursache des 14-Tage-Musters (alle Live-Stroeme), kuenftige Vermeidung; H-21-Lueckenliste `allLiquidation` 2026-07-01..12-27 rechnet der Orchestrator aus dem Katalog (S0) | Entsperrbarkeit H-21; Ausfalltage-Budget prospektiver Designs | Pruefung |

Nicht noetig: HF-RV (DEC-98 N5), Binance-Panel fuer A3 (Bilanz B-6). Laufend und ausreichend: DVOL, kline1m BTC/ETH,
Panel-Strom, Funding aller Perps, A4-Quotes, Settlements, Options-Ticker, Liquidationen, Insurance.

## 9. Entscheidungsvorlage

### 9.1 Programmfragen (nur der Nutzer; mit Default-Vorschlag des Orchestrators)

| Nr. | Frage | Default-Vorschlag | Richtung | Quelle |
|---|---|---|---|---|
| P-1 | **Mission:** bleibt 3.0 eine Pruefinstitution fuer Literaturpraemien oder wird es eine Messinstitution, die Effektgroessen mit Intervallen und Ausschlussgrenzen produziert (und darauf Hypothesen registriert)? | Messinstitution; Verdikte bleiben konfirmatorisch nach Vorregistrierung | neutral (Zweck), Testbarkeit (Weg) | T-1, T-2, K-6 |
| P-2 | **Fehlerbudget und Power-Ziel auf der Entscheidungsregel** - drei Varianten: (a) gepoolter Test alpha 0,0025 plus REZENZ-Screen im juengsten Fenster, gemeinsame Power 0,80 (Fehlerrate je Test unveraendert, +8 % Daten gegen C.10 je 0,80); (b) C.10 behalten, gruppensequentielle Blicke je Fenster (alpha je Fenster 0,05, gemeinsam 0,0025; Regime-Robustheit bleibt); (c) gepoolt alpha 0,01 (Lockerung x4, PPV 0,90 statt 0,97). Dazu Pflicht-Bestaetigung auf neuen Daten vor jeder Tradability-Frage | (a); alpha je Test fest 0,0025 | (a) Testbarkeit Stufe 1 bei gleichem alpha; (b) neutral; (c) Lockerung | K-4, K-6, W-2 |
| P-3 | **Prior-Regel:** SESOI (kleinste oekonomisch relevante Wirkung aus gemessenen Kosten) oder Prior-Verteilung statt Literatur-Punktprior; UNBELEGT symmetrisch (keine Strenge-Defaults ohne Beleg; aendert Arbeitsregel 4) | SESOI als Feasibility-Massstab, Literatur als Etikett; A1 und VRP damit definitiv geschlossen. **A2 wird dadurch allein nicht registrierbar** (W2-MDE80 22,3..27,2 bp > 22 bp Taker-SESOI; Maker-SESOI 10,8 in keiner Lesart) - nur zusammen mit P-2 (a) oder dem Einzel-Placebo; Taker statt Maker ist eine Gabelung Richtung Testbarkeit | Testbarkeit (Feasibility), Klarheit (A1/VRP) | K-10, T-2, E-3, B-2 |
| P-4 | **Fenster-Politik:** Drei-Zonen-Regime mit Konto, Kohorten-Stichtagen, gruppensequentiellen Blicken, Lockbox, Vorwissens-Klasse je Datenfamilie; ersetzt Einmal-Gut, Reihenfolge-Frage und harte 12-Monats-Fenster; Zonenlaengen 36/12 Monate, Quartalstakt | annehmen; Pilotabschnitt 2022-04..2024-06 und A2-Vorperiode als Zone X; **W1/W2 bleiben blinde Klasse-W-Fenster** | gemischt, je Zeile etikettiert (Abschnitt 6) | T-12, Architektur 3, K-7/K-8, E-1/E-5, B-6 |
| P-5 | **Nuisance-adaptive Designwahl ist kein Torpfosten:** registriertes Design-Menue plus mechanische Auswahlregel nur aus Vorperioden-Nuisance und SESOI/Prior; der Orchestrator fuehrt sie autonom aus; Ausnahmen (A2-Schwelle, Vorwissen, Programmebene) ausdruecklich | annehmen | Testbarkeit, alpha je Test neutral | K-7, B-12 |
| P-6 | **REZENZ als pruefbare Hypothese** (gepoolter Schaetzer plus registrierter Stabilitaetstest) statt harter Schnitt; Nuisance-Symmetrie (juengstes Vorfenster bindend, aeltere nur Sensitivitaet) - fuer A2 eine Lockerung des effektiven alpha Richtung Nominalwert | annehmen | Testbarkeit + Strenge; A2-Nuisance: Lockerung | K-12, B-12 |
| P-7 | **A2-Zuordnung und Pilot-Uebergabe:** exakte gemeinsame Power statt Produkt (DEC-94 (6)); exakte P2''-Bedingung (22,93 / 23,77) statt Null-Faktor als Zuordnungsgrundlage (DEC-103 N1 (8a)); Pilot-Uebergabe ueber Assurance/praediktive Power statt "Pilotpunkt >= MDE80"; nicht uebergebene Varianten raus aus dem konfirmatorischen Nenner; Festlegungen Stress bindend / skalierte Null / Gate-(4)-Faktor je einzeln bestaetigen oder aufheben (Kette 24,4 -> 27,2 -> 29,3 -> 32,1) | annehmen (exakte Bedingung, Assurance); Stress bindend behalten; skalierte Null behalten; Gate-(4)-Faktor behalten bis Negativ-Panel | Testbarkeit, alpha neutral | K-5, K-9, B-1 |
| P-8 | **Reihenfolge der Blindperiode** (offen seit 2026-10-18) | wird mit P-4 (Kohorten) gegenstandslos; ohne P-4: gemeinsame Vorab-Registrierung aller Blindperioden-Designs vor der ersten Rechnung (DEC-98 E1 (d)), Bedarfsbilanz Abschnitt 6 als Grundlage | Testbarkeit | K-8, S-6 |
| P-9 | **A2 (P-0..P-3 vom 2026-10-31):** unter P-3 allein bleibt A2 bei MDE80 22,3..27,2 bp ueber der SESOI; registrierbar auf W1/W2 ohne Pilotroute nur mit P-2 (a) (gepoolt 0,0025: 19,2 bp beim Einzel-Placebo, mit drei Placebos hoeher) oder mit Einzel-Placebo P2'' (18,8; verwirft DEC-103 E3) | bis P-2/P-3 entschieden: P-0 | - | DEC-103 N1, B-2 |
| P-10 | **Klasse P:** reines Mess-/Aufzeichnungsprogramm (PARK ist das beste Ergebnis) oder Kapitalregel ohne MinTRL | Aufzeichnung | neutral | K-12 |
| P-11 | **Umgebung und Budget:** Netzfreigabe fuer offene Volltextquellen (arXiv, SSRN, Deribit-/CME-Doku), Budget fuer Volltexte, Token-/CPU-Deckel, direkter Auftragskanal an Data-Harvest, Schluesseltrennung, privater Speicher fuer versiegelte Zwischenstaende, Gebuehrenstufe/Kapital/Steuer (PRD 8.2) | Netzfreigabe ja; Rest nach Kostenbuch | neutral | T-17, E-6..E-9, K-11 |
| P-12 | **Regelaenderungs-Protokoll:** Lockerungen nur mit Nutzer und ab naechster Kohorte; Verschaerfungen durch den Orchestrator mit Strenge-Quotient-Ausweis; stehende Default-Politik je Fragetyp (auch Richtung Testbarkeit), damit Stille nicht immer Strenge heisst | annehmen | Strenge (Protokoll) | E-10, T-17 |

Empfehlung des Orchestrators: P-1..P-7 als **ein** Paket ("Verfassung 3.1") entscheiden, nicht einzeln - sie haengen
zusammen (SESOI braucht die korrigierte Wand; Zonen brauchen das Fehlerbudget mit festem alpha je Test; Kohorten
ersetzen die Reihenfolge-Frage; A2 haengt an P-2 und P-7). Vor der Entscheidung liefert der Orchestrator die
Gesamt-OC-Simulation des Pakets (9.2 Nr. 3). Bis zur Entscheidung gilt alles Bisherige unveraendert; der Orchestrator
bereitet vor (9.2).

### 9.2 Was der Orchestrator ohne Rueckfrage tut (reversibel, keine Regelwirkung)

1. **Errata (DEC):** K-0.1 als Kurvenschar mit Gauss-konsistenter Kante (Pearson pi/2, Rang pi^2/6) und gemessenen
   Kosten (IC_min 0,040 statt 0,062; "7 h Maker" -> 8,7 h; "Abstand halbiert" -> ein Drittel; L-18-Vermerk);
   Lo-Beispiel q = 365; K-0.6 Faktor 5,2; DEC-52-Rate unter Abhaengigkeit ~0,85..0,99 %; Taker-/Maker-IC_min als
   Persistenz-Tabelle (phi 0 / 0,5 / 0,8); A2-Kette mit skalierter Null als eigener Zeile und exakte P2''-Bedingung
   (22,93 / 23,77) als Doppelausweis neben dem Produkt (die Zuordnungsregel selbst bleibt bis P-7); VRP-Zeitlinie
   ueberall auf Prior 7,14 VP (2029-07..2033-01); PRD 1 "Pivot"-Begruendung ergaenzen; Datenannahmen-Register (K-13);
   A4-Fenster-Widerspruch; Modellbezeichnungen in Repo-Artefakten durch Rollen ersetzen (CLAUDE.md und PRD 3.9:
   Vorschlag an den Nutzer).
2. **Pflicht-Berichtszeile** in DEC-53: Schaetzer, 95-%-CI, obere Ausschlussgrenze (einseitig), Shrinkage - fuer jeden
   Lauf, auch GL-012; Spiegelklausel zur Null-Zensus-Klausel (keine Demotion aus einer Ausschlussgrenze).
3. **OC-Simulation als T0:** P(PASS bei 0), P(PASS bei SESOI), P(PASS bei Prior) der gesamten Kette vor jeder
   Registrierung; **Gesamt-OC des Lockerungspakets P-1..P-7** (erwartete Falsch-PASS je Jahr, PPV bei Basisraten
   5/10/25 %, mit X-Screens, Kohorten-BY, schweren Raendern, kleinen Clusterzahlen) als Vorlage vor der Entscheidung;
   Strenge-Quotient MDE80(alle Festlegungen)/MDE80(Grundfassung) als Pflichtzeile, ab 1,3 Nutzer-Vorlage.
4. **Review-Mandat symmetrisch:** Pflichtfrage "ist der Test gegen den Prior/SESOI nach allen Auflagen noch sensitiv?";
   Schleifen-Obergrenze zwei Fassungen, dann Nutzer-Vorlage.
5. **F0 Schadensbegrenzung:** alle Herleitungs-, Review- und Nachrechnungsskripte (A2 Teil A/B/C, Reviews, Orchestrator-
   Checks, Dateninventar, diese Analyse) ins Repo (`derivations/`, `verify/`, nach Pruefung auf Hostnamen/Schluessel);
   Kanal-Scan als Test ueber alle JSON; Kostenbuch beginnen; Umgebungs-Manifest.
6. **Konto-Inventar und Bedarfsbilanz:** alle bisher geoeffneten Statistik-x-Fenster-Paare aus den C.17-Listen
   (einschliesslich WP-10(B) und H-24 W-R2 im Blindbereich, Edge-Inventur S-2) als Tabelle; Bedarfsbilanz der
   Blinddaten (Abschnitt 6) je Kandidat fortschreiben; Vorwissens-Register je Datenfamilie; H-21-Lueckenliste aus dem
   Katalog (S0) und danach formal schliessen oder offen lassen (S-1).
7. **Feasibility-Rechner und Klassen-Feasibility** (F3): SR-Aequivalent je Fensterlaenge, MDE80 gegen SESOI-Band, zwei
   Spalten Exploration/Konfirmation, reproduziert GL-032..036 ohne Neulauf siegeldateierzeugenden Codes;
   Mehrfaktor-Null als Nuisance-Paket (S-4, nur Streuung).
8. **Inhaltsproben und Zensen ohne Outcome, nur Vorperiode:** `tardis/options_chain` (Stichtage <= 2026-06-01),
   `deribit/publicTrade`, L2 2023-2025 Stress-Tage, Negativ-Panel-Minutenbars aus Trades (Machbarkeit), Zaehl-Zensen
   (ATM-OI je Verfallstag, Listings/Delistings je Fenster, Cap-Treffer-Cluster), Slot-Streuung an Makro-Terminen (nur
   Streuung); S0-Zensen (Zeilen, Luecken, Zeitstempel) der Live-Stroeme auch im Siegel (DEC-96 E3 erlaubt Zaehlung).
9. **PRD v3 als Entwurf:** konsolidierte Fassung mit eingearbeiteten Nachtraegen, markierten Altzeilen, einer bindenden
   Fassung je Kandidat; Errata-Anhang. Beschluss durch den Nutzer.
10. **Monatlicher Stromcheck** (Vollstaendigkeit aller laufenden Stroeme, Ausfalltage-Budget) als geplante Aufgabe.

Nicht ohne Nutzer: jede Registrierung auf W1/W2 oder in der Blindperiode, jede Lockerung, jeder Pilot, jede Aenderung an
C.10/DEC-52/DEC-94/DEC-99/DEC-103 N1 (8), CLAUDE.md.

## 10. Was NICHT folgt

- Kein Verdikt ueber Momentum, Reversal, Carry, VRP, Verfallseffekt oder irgendeinen Markteffekt; kein GL kippt; keine
  2.0-Kante wird durch die pi/2-Korrektur handelbar (80..500x bleiben 50..300x).
- Kein Siegel wird geoeffnet; die Reihenfolge-Frage bleibt bis zur Nutzerentscheidung offen; A2 bleibt P-0. Keine
  Analyse und dieser Bericht haben eine Outcome-Statistik gerechnet.
- Alle Power-Zahlen sind Aufloesungsgrenzen aus Akten-Nuisance mit markierten Annahmen, keine Effektgroessen, und
  Normalnaeherungen; vor jeder Herleitung sind sie auf der Vorperiode zu messen (nur Streuung).
- Die Korrektur zu K-5 heisst nicht, dass die A2-Zuordnung richtig streng ist; sie heisst, dass der Artefaktanteil
  0,5..0,6 bp betraegt und der Rest Festlegung (Stress, skalierte Null, Gate (4)) beziehungsweise Nutzerfrage (P-7) ist.
- Die Vetos gegen "F1 heute registrierbar" und "A2 heute registrierbar" entwerten weder F1 noch die SESOI-Idee: F1
  bleibt der interessanteste neue Kandidat (braucht einen Prior fuer die Gap-Statistik und rechnet auf W1/W2), SESOI
  bleibt eine Programmfrage (P-3) - nur die Folgerung "sofort" faellt.
- Die Lehren C.1..C.19 und die Feststellungen GL-032..036 stehen; kritisiert werden die Kombination der Regeln, die
  fehlenden Mess-Ausgaben und einzelne Herleitungen (K-1..K-3), nicht einzelne Urteile.
- Automation macht kleine Effekte nicht frueher testbar (Wurzelgesetz); gewonnen werden Unabhaengigkeit vom
  Literatur-Prior, Parallelitaet statt Serialisierung, Wegfall der Nutzerlatenz und frueher Abbruch hoffnungsloser
  Hypothesen.
- Mehrere Vorschlaege sind Lockerungen (Zone X ohne Verbrauch, BY statt Sperre, Interimsblicke, SESOI/X-Prior,
  gepooltes alpha ohne festes alpha je Test); sie sind etikettiert, prospektiv und Programmfragen. Der Orchestrator hat
  am 2026-10-31 selbst die kritisierten Strenge-Festlegungen fuer A2 getroffen und legt sie hier mit P-7 zur
  Bestaetigung oder Aufhebung vor.
- Die Token- und Stundenzahlen des Fahrplans sind Schaetzungen ohne Messbasis.
- Nichts hier betrifft Kapital, Steuer oder Ausfuehrung (PRD 8.1/8.2); kein Live-Order-Code.

## Anhang A: Methode

Sechs Agenten mit getrennten Auftraegen und einer gemeinsamen Regel- und Leseliste (Anhang-Verzeichnis
`BRIEF_*.md`, `REGELN_UND_LESELISTE.md`): Listenagent (DEC/GL/D-Listen), Kartierungsagent (Faktenblatt),
Herleitungsagenten (PRD-Kritik; Edge-Inventur; Architektur), Grundsatzanalyst (Konzept und Forschungsfelder);
anschliessend ein adversarischer Reviewer ueber die vier Analysen gegen die Primaerquellen (57 Stichproben, 12 abweichend;
47 Nachrechnungen; 12 Widersprueche; 7 Luecken). Der Orchestrator hat K-1, K-2, K-3 unabhaengig nachgerechnet, seine
eigene K-5-(a)-Rechnung nach dem Review korrigiert, die Review-Kernzahlen (gemeinsame Power bei Korrelation, VRP
mit Prior 7,14, F1 auf W1/W2, prospektive Tageszeitreihe, Persistenz-IC_min, OBF-Erwartungswerte, PPV-Tabelle,
Datenfaktoren) mit eigenem Code reproduziert (`scripts/orch_review_check.py`), die Aufloesungsgrenze des
Tageshorizonts vor Lieferung der Analysen vorgerechnet (`ORCH_VORRECHNUNG_horizont.txt`), fuenf Fundstellen der
Grundsatzanalyse stichprobenartig geprueft und die Synthese geschrieben. Alle Analysen: nur lesen, keine Marktdaten,
keine Siegeldateien, kein Harvest-Client ausser dem Katalogabruf des Orchestrators fuer das Dateninventar. Die
Agentenanalysen im Anhang sind unveraendert, wie geliefert; Anhang C sagt, welche ihrer Aussagen diese Synthese nicht
uebernimmt.

## Anhang B: Dateninventar

`DATENINVENTAR_2026-11-01.md` (29 Stroeme, Zeitraeume, Symbole, Partitionen, Groesse, Abdeckung je Symbol; aus dem
Katalog, ohne Listing, ohne Hostname).

## Anhang C: Review-Auflagen und ihre Behandlung

Quelle: `REVIEW_PRD_ANALYSE.md` (Urteile: Kritik und Grundsatzanalyse Zustimmung mit Auflagen und Teil-Veto; Edge-Inventur
und Architektur Zustimmung mit Auflagen, kein Veto). Alle Vetos sind angenommen.

| Review | Gegenstand | Behandlung in dieser Synthese |
|---|---|---|
| B-1 (VETO) | Null-Bedingung ist dokumentierte Lesart, Korrelation 0,82/0,91, Artefakt 0,5..0,6 bp; Kette 27,2 -> 32,1 enthaelt skalierte Null +2,1 | angenommen; Kette korrigiert (0.2, K-5); "streichen" ersetzt durch Doppelausweis (O) und Zuordnungsfrage P-7 (N); eigene Nachrechnung 0,858/0,870 |
| B-2 (VETO) | "A2 heute registrierbar gegen 22 bp" gilt fuer kein festgelegtes Design; Taker/Maker-Gabelung | angenommen; K-10, P-3, P-9 umformuliert; A3 "gegen welchen Wert" offen |
| B-3 (VETO) | VRP-Prior 9,47 ueberholt (7,14); 1.183 statt 672 Tage; 2029-07..2033-01 | angenommen; K-2, K-7, 0.3, Abschnitt 6 umgestellt; eigene Nachrechnung |
| B-4 (VETO) | F1: 0,006..0,013 nutzt Pilot- und Siegeltage; W1/W2 0,0133..0,0188; Bianchi [PDF, Weg A, ohne Gap] passt nicht; c > 1 | angenommen; 0.5, 0.6, F1-Zeile, Bedarfsbilanz; F5 analog (BTC-Beta ab 2026-07 gesperrt) |
| B-5 (VETO) | BTC/ETH-Tagesfelder ohne Siegel- und Vorwissens-Etikett; prospektiv MDE 0,13 je Jahr | angenommen; zwei Power-Spalten in Abschnitt 5, Horizont-Schere neu gefasst (4.1), Vorwissens-Klasse als Regel (6) |
| B-6 (VETO) | "W1/W2 faktisch nicht blind" und DEC-95-E2-Lesart falsch | angenommen; alle Stellen korrigiert (0.11, 4.9, 6, P-4): W1/W2 blind fuer Klasse W; nur A2-Vorperiode durch Disziplin |
| B-7 (VETO) | "neutral in alpha" ohne festes alpha je Test unbelegt; -31 % nur gegen C.10-0,80 | angenommen; Etikett-Tabelle und Zahlen in 6; festes alpha je Test als Bestandteil des Regimes; P-2 als drei Varianten |
| B-8 | Kohortenfaktor 1,54 vergleicht Ungleiches | angenommen; als Obergrenze unter nicht geltender Zusatzregel gekennzeichnet |
| B-9 | D.17 beruht auf 1-Tag/Monat-Dichte, nicht "2 Tagen"; Tardis-Stichtage ab 2026-07 im Siegel | angenommen; K-13, 2 (ii), Datenauftrag 2 (nur <= 2026-06-01); D.17 unberuehrt |
| B-10 | K-1 bestaetigt; Rang-IC pi^2/6; PRD "7 h" = 8,7 h; Stundenhorizonte N (D.4/D.12/D.14) | uebernommen (0.2, K-1, 9.2 Nr. 1) |
| B-11 | K-2/K-3 bestaetigt; "vorhersagbar am PRD-Tag" und "4 Wochen vermeidbar" sind Rueckschau | als [V] gekennzeichnet (0.2, K-2, K-3) |
| B-12 | K-7 richtig je Test mit Ausnahmen A2-Schwelle, Vorwissen, Programmebene; K-5 (4) ist N | uebernommen (K-7, K-12, P-5, P-6); K-5 (4) nach N |
| B-13 | K-11: "Friktionswand" kein PRD-Zitat; "Pivot-Begruendung unvollstaendig" | uebernommen (K-11) |
| B-14 | Taker-IC_min je Persistenz 0,0263 / 0,0175 / 0,0108 | uebernommen (4.1, F2-Zeile, 9.2 Nr. 1); eigene Nachrechnung |
| B-15 | R-1: Leitzahl 75 % (74..113 Wochen) nach DEC-99 (3); "unplausibel hoch" abschwaechen | uebernommen (0.3, Abschnitt 2) |
| B-16 | H-21 nur "in registrierter Form" und [V] bis Lueckenliste; Pruefung ist S0 | uebernommen (0.11, 2 (i), K-13, 9.2 Nr. 6, Datenauftrag 9) |
| B-17 | F8/F9 Siegelabhaengigkeit | uebernommen (Felder-Tabelle: vor Reihenfolge-Entscheid nur S0) |
| B-18 | Generatives Modell: D.16 nur als Gegenargument; Zustaendigkeit N | uebernommen (0.4, Abschnitt 3): OC-Simulation mit minimalen Nullwelten O, umfassendes Modell N |
| B-19 | "14 Monate 3.0" -> zwei Monate; "sechs Gate-Eintraege" -> fuenf; GSD-Definitionen | korrigiert (0.1, 3); GSD einheitlich 0,814 / 0,871 |
| B-20 | F3 ohne Neulauf siegeldateierzeugenden Codes | uebernommen (Fahrplan, 9.2 Nr. 7) |
| B-21 | Veroeffentlichung: Struktur-Scan, EDGE-Verweis | Struktur-Scan: keine neuen JSON-/Nuisance-Dateien in diesem Paket (nur Markdown, Text, Skripte ohne Datenausgaben), Hygiene-Scan ASCII/Hostname/Modellnamen ohne Befund; EDGE-Skriptverweis auf `scripts/edge_calc.py` nachgezogen |
| W-1..W-12 | Widersprueche zwischen den Analysen | aufgeloest wie in der Review-Tabelle: GSD-Zahlen einheitlich; Fenster-Regime als drei Optionen (P-2); BTC/ETH-Aggregate nur prospektiv; VRP 7,14; A2 nach Edge/Architektur; Kette nach Grundsatzanalyse; H-21 mit Vorbehalt; D.17 nach Grundsatzanalyse; Reversal-Prior nach Edge (fuer Gap-Design unbelegt); +26 % als einheitliche Basis; Prior-Ersatz als P-3; Teilen von Blindfenstern: Mehrpreis ist Abhaengigkeit |
| Luecken 1-7 | Bedarfsbilanz, Gesamt-OC, schwere Raender, Ausfalltage, Funding/Caps/IPCW/Ueberlappung, Vorwissens-Klasse, Veroeffentlichungs-Scan | ergaenzt in 4.11-4.17, 6 (Bedarfsbilanz, OC-Tabelle), 7, 9.2 |

Nicht uebernommene Aussagen der Agentenanalysen (Anhang unveraendert): Kritik K-5 (1) "streichen", K-10 "A2 heute
registrierbar", K-7/Abschnitt 8 VRP "~2030 / L ~22 Monate", K-11 "Pivot-Diagnose falsch", K-13 "91 Monate
rekonstruierbar" ohne Siegel-Grenze; Grundsatzanalyse 0.4/F1 "registrierbar heute", T-8/T-9 Power ohne Etikett,
T-5/T-12 (4) Blindheitsbegruendungen, T-12 "neutral in alpha", T-3 Zustaendigkeit, "14 Monate", "sechs Gate-Eintraege";
Edge-Inventur E-25 "D.17 revidieren", Kurzfassung 9 ohne Vorbehalt, "unplausibel hoch"; Architektur 3.5 VRP-Zeitlinie,
3.4 Faktor 1,54 als Vergleich.

---

## Nachtrag 1 (2026-11-02): Methoden-Sweep "Naturwissenschaft und Technik x Datenstroeme" - Antwort auf die Nutzerfrage, ob neue Forschungsansaetze systematisch abgegrast wurden

**Anlass.** Nutzer 2026-11-02: "Haben wir denn auch den Auftrag abgearbeitet, nochmal komplett neue Forschungsansaetze
abzugrasen?" Ehrliche Antwort des Orchestrators: nein, nicht systematisch - F1..F12 sind hypothesengetriebene Finanzfelder
im heutigen Klassenschema. Nachgeholt mit einem eigenen Herleitungsauftrag (`prd_analyse_2026-11-01/BRIEF_methoden_sweep.md`),
Ergebnis `prd_analyse_2026-11-01/METHODEN_SWEEP_2026-11-02.md` (945 Zeilen; Rechenweg `scripts/sweep_calc.py`). Nur Lesearbeit und
Formeln; keine Marktdaten, keine Siegeldatei. Literaturwerte dort durchgehend [sek] (aus dem Gedaechtnis, Primaerquellen zu
beschaffen).

**Abnahme durch den Orchestrator (eigener Code `scripts/orch_sweep_check.py`, Ausgabe `.out`):** alle Kernzahlen reproduziert -
IK-10 Zone-V-MDE80 0,0148 / 0,0162 / 0,0209 (K 600 / 500 / 300; gepoolt 0,0025 + REZENZ-Screen W2, Korrelation sqrt(1/2)),
Zone K 12 Monate 0,0197..0,0278, Zone X (K ~200, 1.277 Tage) 0,0123; Taker-/Maker-SESOI im Dezil-L/S-Rahmen (3,51 x IC x
sigma_xs 370 bp [V]) 0,0169 / 0,0062 (gesamt 15 bp 0,0231); schwere Raender: Kurtosis 5 / 10 bei 40..52 Clustern senkt die
effektiven Freiheitsgrade der SE auf 15..7, hebt den kritischen Wert zu alpha 0,0025 von 2,807 auf 3,29..4,12 und die MDE um
1,14..1,38 (bei 365 Clustern <= 1,03); Schiefe -0,5 / -1 hebt das effektive einseitige alpha auf ~0,0040 / ~0,0057
(Edgeworth, Groessenordnung); Marchenko-Pastur-Kante 1,95 / 2,64 (K 200 / 500, T 1.277), noetiger Eigenwert 6,25 (volle
Ausrichtung) bzw. 11,5 fuer die 2,5-fache IC-Streuung; Drift-SE von BTC nach 6,6 Jahren 19,5 % p.a. unabhaengig von der
Abtastrate. Ein Punkt des Auftrags war fehlerhaft und ist vom Agenten richtig nach DEC-104 aufgeloest: BTC/ETH-Daten aus
W1/W2 sind Zone V, nicht X (der Brief sprach von "agentenbekannten Aggregaten bis 2026-06 in Zone X").

**Befund in Kuerze (uebernommen, [U]):**
1. Die Methoden der Naturwissenschaft tragen auf unseren Daten **Mess-, Kosten- und Nullwelt-Programme, kaum neue
   Praemienquellen**. Grund ist Arithmetik, nicht Methodenmangel: hohe Abtastrate kauft Praezision fuer Varianzen, Kosten und
   Strukturen, nicht fuer Tagesmittel (Merton). 37 Methodenfamilien x 13 Stromgruppen; elf Ideenkarten IK-01..IK-11 (neun
   Messprogramme, zwei Hypothesen), Platz zwoelf bewusst frei gelassen.
2. **Die SESOI-Kurve nach DEC-104 E3 existiert noch nicht** - die Wand ist eine Konstante, die Slippage ungemessen, der
   Maker-Pfad ein Band. Die Kostenkurven **IK-01** (Taker-Impact, Kyle-Obizhaeva-Invarianz auf ~20 GB Trades, 2,7 h Transfer)
   und **IK-02** (Maker-Warteschlange auf ~34 GB L2, besser auf dem Nutzer-PC oder per Vorextraktion) sind damit **Vorbedingung
   jeder 3.1-Registrierung**, nicht Beifang. Taker gegen Maker entscheidet um den Faktor 2,7, ob ein Querschnittsdesign testbar ist.
3. **IK-04** (Skalengesetze, Ereigniszeit, schwere Raender -> minimale Nullwelt) liefert die Momente, die die Gesamt-OC vor
   Kohorte 1 braucht; Permutationstests unter Austauschbarkeit (A2) halten alpha, verlieren nur Power; Tests mit geschaetzter
   SE und Normal-Kritik (Bootstrap-SE, gepoolte z-Tests) brauchen t-artige Grenzen.
4. **IK-05** instrumentiert den groessten ungeprueften Hebel der Klasse W (S-4): ob eine Faktorstruktur die 2,5-fache
   IC-Streuung erklaert, ist in Zone X per Zufallsmatrixtheorie entscheidbar (Eigenwert >= 6 gegen Rauschkante 2,0..2,6).
5. **IK-10** (verzoegerte Marktreaktion im Perp-Querschnitt) ist der einzige neue Querschnittskandidat und liegt genau an der
   Kante: Zone-V-Blick in Kohorte 1 loest 0,015..0,021 auf gegen Taker-SESOI 0,017; a priori geringe Plausibilitaet fuer liquide
   Perps; die Ausschlussgrenze aus Zone X (0,008 bei K ~200) ist auch ohne PASS informativ. F1 und IK-10 sind ueber die
   Renditefamilie korreliert und muessen in dieselbe Kohorte (ein V-Blick je Familie, E4 (d)).
6. Weitere Karten: IK-03 Leland-Kurve (Hedge-Kosten Klasse P), IK-06 Optionsketten-Invarianten (Datenfund: die Tardis-Kette
   hat ~58 Mio Zeilen je Stichtag, also Intraday an 63 Zone-X-Stichtagen -> implizite Basis-Terminstruktur seit 2019 als
   F10-Einstiegsbasis, [V] bis zur Inhaltsprobe), IK-07 Demografie des Perp-Lebenszyklus (ersetzt die unbewiesene
   8-Wochen-Regel), IK-08 Metrologie der Datenstroeme (Ausfallbudget, Kalibrierbuch; S0 auch im Siegel), IK-09
   Delisting-Hazard mit Kovariaten (IPCW fuer jeden Querschnittstest), IK-11 Funding-Regelkreis (Reserve).
7. **Groesste Luecke der Felderliste F1..F12:** Erst-Moment-Hypothesen auf ungemessenen Zweit-Moment- und Kosteneingaben; nur
   F4 enthaelt eine Invarianz; die 1,07 TB Trades/L2/Kette werden nirgends dort eingesetzt, wo sie einen komparativen Vorteil
   haben (Kosten, Nullwelten, Invarianten).
8. **Sofort in Zone X (Minuten CPU):** IK-04, IK-05, IK-07, IK-09, IK-10, IK-03, IK-11 auf Tages-/Minutenkerzen und Funding;
   IK-08 als S0 auch im Siegel; IK-01 nach Trade-Stichprobe; IK-06 nach Tardis-Inhaltsprobe. **Innerhalb 12 Monaten
   konfirmierbar:** IK-01, IK-02 (Gesetzeshypothesen in TOST-Form), IK-06 Teil b, IK-07, IK-09, IK-10.
9. **Neue Datenauftraege** (Abschnitt 6 des Sweeps, ergaenzen Abschnitt 8 oben): Tardis-Inhaltsprobe erweitert (Feldliste,
   gefiltertes Laden; nur Stichtage <= 2026-06-01); Index- und Mark-Preis-Tageskerzen aller linearen Perps ab 2021-01 inkl.
   Delisteter; Tagesaggregate (Tradezahl, Buy/Sell-Volumen, Groessenquantile) aus dem Trade-Archiv fuer alle Perps;
   L2-Vorextraktion fuer eine Stichtagsliste; Ausfall- und Wartungsregister des Live-Sammlers; Kontraktspezifikations-Historie.
10. **Neue Programmfrage P-13 (Lockerung, N):** DEC-104 E4 laesst BTC/ETH-Trades und -Orderbuecher 2024-07..2026-06 fuer jede
    Nicht-A2-Statistik weder explorieren noch konfirmieren ("Brachland"). Fuer Nicht-Rendite-Mikrostruktur (Tradezahlen,
    Groessenverteilungen, Queue-Intensitaeten, Zeitstempel) ist der Schutzzweck schwach, weil die W1/W2-Vol ohnehin bekannt ist
    (DEC-95 E2). Vorschlag des Sweeps: diese Statistiken mit A2-Maske (Ausschluss der Freitags-Slots 07:30-08:00) als Zone X
    fuehren. Preis: weiteres Agentenwissen ueber W1/W2-Aktivitaet. Default bis zum Entscheid: nein (IK-01/IK-02 rechnen auf
    2020..2024-06 und ab 2026-07).
11. **Fuer PRD v3:** Aequivalenzform (TOST) fuer Gesetzeshypothesen (Skalengesetze, Invarianzen) neben dem einseitigen
    Ueberlegenheitstest; Enrichment-Design fuer Querschnitte (N).

**Was nicht folgt:** kein Verdikt, keine Registrierung, keine Kostenzahl ist gemessen (alle SESOI-Werte beruhen auf der
PRD-Wand und sigma_xs 370 bp [V]); alle Streuungs-Nuisancen der neuen Groessen sind in Zone X erst zu messen (Konto).
Reihenfolge der naechsten Orchestrator-Schritte daraus: (1) Gesamt-OC (laeuft) mit IK-04-Korrekturen; (2) Zone-X-Programm
IK-05 und IK-04 auf dem Tages-Panel (Konto-Eintraege 1 und 2); (3) IK-01-Stichprobe (Trades 2020..2024-06) als erste
Kostenkurve; (4) Feasibility-Rechner (F3) mit SESOI-Kurve in beiden Rahmen (Dezil-L/S fuer Klasse W, Einzelposition fuer
Klasse E/P).

## Nachtrag 2 (2026-11-02): Gesamt-Operationscharakteristik des Pakets 3.1 - Korrektur an Abschnitt 1 (K-4), 6 und 9.1 (P-2)

Die OC (`prd_analyse_2026-11-01/OC_VERFASSUNG31_2026-11-02.md`, vom Orchestrator nachgerechnet, DEC-104 Nachtrag 2) bestaetigt
die Fehlerseite des Pakets (alpha_eff 0,0019 bei zwei Fenstern, PPV 0,98 bei Basisrate 0,10) und korrigiert zwei Aussagen
dieser Synthese: (1) der Datenfaktor der Regel "gepoolt 0,0025 + REZENZ-Screen" gegen C.10 je 0,80 ist **+23 %** (zwei
Fenster), nicht +8 % - die Synthese hatte den Screen weggelassen; (2) der Screen auf einem festen 12-Monats-Fenster bei 0,05
setzt einen **Boden von 2,4865 SE_12**: die Regel macht keinen Effekt testbar, den ein einzelnes 12-Monats-Fenster nicht sieht,
und schliesst A2 (Boden 24,3 bp gegen SESOI 22) sowie Klasse W bei Wochen-IC-SD 0,13 (Boden 0,0448 gegen 0,040) dauerhaft
aus. Die in Abschnitt 6 beschriebene Lockerung "Interimsblicke statt zwei Vollfenster" wirkt daher nur in der Zeit, nicht in
der Aufloesung. Die P-6-Lesart (gepoolt + registrierter Stabilitaetstest, kein Boden, +9 % Daten) ist als neuer Default
fuer P-2 vorgelegt (DEC-104 N2 (4)); bis zum Entscheid gilt die beschlossene Variante. Alle uebrigen Zahlen der Synthese
bleiben; die Aussagen zu Selektion (Power-Planung nur gegen SESOI) und schweren Raendern (t-Grenzen Pflicht) sind als
Verschaerfungen festgehalten.
