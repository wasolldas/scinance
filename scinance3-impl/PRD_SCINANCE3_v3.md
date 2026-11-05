# PRD SCINANCE 3 - Fassung v3 (konsolidierte Lesefassung) - BESCHLOSSEN

## 0. Kopf

**Status: v3 angenommen am 2026-11-04 (Nutzerentscheid, DEC-107 (2)); Entwurfsstand 2026-11-02 (`PRD_SCINANCE3_v3_ENTWURF.md`,
unveraendert als Akte).** Diese Datei ist die **bindende Lesefassung** der Verfassung: bei Widerspruch zwischen v3 und einer
**spaeteren** DEC gilt die DEC; bei Widerspruch zwischen v3 und PRD v2 oder aelteren DEC gilt v3 (Herkunft steht in jeder Zeile).
PRD v2 und `state/decisions.md` bleiben append-only unveraendert. Regelaenderungen laufen nach dem Protokoll DEC-107 (6) und
werden hier nachgefuehrt (Abschnitt 0.1).

### 0.1 Beschlussvermerk und Nachfuehrungen (DEC-107, 2026-11-04)

| Stelle | Entwurf (2026-11-02) | beschlossen / nachgefuehrt | Herkunft |
|---|---|---|---|
| 2b Entscheidungspunkt P-2; VR-b14; VR-e02; PZ-16; 3.3 YAML `decision_rule` | Variante (a) Screen 0,05 beschlossen, (c) vorgeschlagen | **Variante (c): gepoolt 0,0025 + registrierter Stabilitaetstest** (Welch-t einseitig 0,05 gegen Abfall des juengsten Teils, an jedem Wirksamkeits-Stopp, entfaellt bei <= 12 Monaten, Kostenquote q 0,95, kein Boden; Pflicht-Schutzzeile in der OC). Etikett: Lockerung gegen (a), Verschaerfung gegen gepoolt ohne Screen, alpha je Test unveraendert; N; ab K1 | DEC-107 (1); DEC-104 N4 |
| WD-01 (VR-a02, VR-c01, PZ-02) | offen | **aufgeloest (BE-03 ja):** C.2-Ausdehnung auf Feasibility-Kills gilt fort; SESOI ist Mess-Massstab, "MDE80 > SESOI" fuehrt zu GL-012 (kein Kill, kein DROP); keine Handelskostenzahl in PASS/DROP/Kill | DEC-107 (2) BE-03 |
| WD-02, WD-03 (VR-b10, VR-e03, VR-e07, VR-e12) | offen | **aufgeloest (BE-04 "juengstes Vorjahr"):** bindend SE/Schwelle aus dem juengsten Vorfenster (E6), DEC-94 (5) "groessere SE aus Vorperiode und Null" gilt fuer dieses Fenster; Stress 2021/22 Sensitivitaetszeile, auch fuer A2 (E7 (c)-Vorbehalt wird in der A2-Feasibility ausgewiesen) | DEC-107 (2) BE-04 |
| WD-04 (VR-c03, VR-c04) | offen | O-Default (BE-05 nicht einzeln entschieden): Klasse W im Dezil-L/S-Rahmen, beide Rahmen ausgewiesen; VR-c04 damit "gilt als Default, O" statt "vorgeschlagen" | DEC-107 (2) BE-05 |
| WD-05 (VR-d13, Geltung "ab K1") | offen | **aufgeloest (BE-06 ja):** vor dem 2027-01-01 fuer Kohorte 1 registrierte Hypothesen stehen unter 3.1 | DEC-107 (2) BE-06 |
| WD-12, P-10 (VR-f13) | Default Mess-/Aufzeichnungsprogramm | **aufgeloest (DEC-108 (2)):** VR-f13 in der Fassung 3.1 - Kapitalschritt nur ueber die registrierte Kapitalfunktion L* = 1[PASS] min(L_ruin, L_dd, L_str), bewertet am Bestaetigungsblick, plus getrennt registriertes Tradability-Gate; Nutzer-Defaults eps 0,01, dd_tol 0,30 (1 Jahr), stress_n_min 10, stress_loss_tol 0,20, s_scen 0,35, Notional brutto je Seite, CI-Basis Blickgrenze, Kosten Taker; neue Pflichtzeile PZ-31 `capital_rule`; kein Live-Kapital. Wortlaut: `state/herleitung_kapitalregel_p/` 6.1 mit Review B-1/B-3/B-5 | DEC-107 (5), N2; DEC-108 (2) |
| 4.2 A2, VR-e10/VR-e12 (Placebosatz) | DEC-103 E3 woertlich | **DEC-108 (1), G-02 (c):** P2'' auf W1/W2 unveraendert; in Zone K (ab 2026-10-01) Placebo P2' = alle Mo-Do (taegliche Futures-Deliveries seit 2026-04-04); mechanische Regel "< 50 % P2''-Tage -> P2'"; Verduennung f UNBELEGT, Pflicht-Sensitivitaet f 0 / 0,25 / 0,50 in der OC-Zeile | DEC-107 N3; DEC-108 (1) |
| 5.4 Datenauftrag PRD 1 (Marktkapitalisierung) | Nachfrage | Bezahlquelle fuer die Historie: nein; taeglicher PIT-Schnappschuss ja; Groessenproxy Umsatz-Dezile | DEC-108 (3) |
| WD-15, VR-h01, VR-h05 (P-12) | Selbstbindung | **P-12 beschlossen:** Regelaenderungs-Protokoll (Lockerungen nur N und ab naechster Kohorte; Verschaerfungen O mit Strenge-Quotient; Klarstellungen neutral; Vorlagen-Liste); CLAUDE.md Autonomie 3 ergaenzt | DEC-107 (6) |
| VR-h02 (Rollen), 5.2 "Rollen" | Ersetzung vorgemerkt | **BE-12 ja:** Rollen Orchestrator / Herleitung / Review / Bau / Kartierung in CLAUDE.md; PRD v2 3.9 historisch | DEC-107 (2) BE-12 |
| P-11 (5.2) | offen | Netzfreigabe ja; kein Token-/CPU-Deckel; privater Speicher fuer versiegelte Zwischenstaende ja (Bereitstellung durch den Nutzer; bis dahin Arbeitsverzeichnis + sha256-Pin); Rest offen | DEC-107 (3) |
| P-13 (5.2; VR-d08 Zonen; FENSTERREGISTER) | Default nein | **JA (Lockerung, N):** Nicht-Rendite-Mikrostruktur-Zaehlgroessen der BTC/ETH-Trades/Orderbuecher 2024-07..2026-06 mit A2-Maske als Zone X mit Konto (SK0/SK1) | DEC-107 (4) |
| 8.3 Sunset-Review (5.2) | offen | vollzogen: Recorder und Autopilot angehalten | DEC-106 |
| 4.9 / IK-12; Physik-Konzepte | Pruefung | bestaetigt: IK-12 offizielle Messkarte; Dok 1/3/6 abgelehnt; kein Live-Kapital, kein GPU-Pfad | DEC-107 (7) |
| 8.1 BE-07, BE-08, BE-09, BE-14 | offen | bleiben offen (WD-07, WD-10, WD-11; Datenauftraege beim Nutzer) | DEC-107 (2) |
| WD-06, WD-08, WD-09, WD-13, WD-14, WD-16 | O-Klaerung | weiterhin per DEC-Nachtrag (DEC-104 N5); WD-14 als Kopf-Nachtrag der Registry erledigt | DEC-107 (2) |

Der uebrige Text ist der Entwurf vom 2026-11-02; wo er "ENTWURF", "nicht beschlossen", "vorgeschlagen (P-2 (c))" oder "offen"
zu einer der obigen Stellen sagt, gilt die Tabelle 0.1. Rolle: PRD-Text (Herleitung). Auftrag: PRD_ANALYSE 9.2 Nr. 9
("PRD v3 als Entwurf: konsolidierte Fassung mit eingearbeiteten Nachtraegen, markierten Altzeilen, einer bindenden
Fassung je Kandidat; Errata-Anhang. Beschluss durch den Nutzer"); Kritik K-14 (g) ("eine Datei, eine Wahrheit" gilt
nicht fuer die Verfassung); DEC-104 E9 (Pflichtzeilen-Erweiterung "PRD v3, Entwurf durch den Orchestrator, Beschluss
durch den Nutzer"); DEC-105 ("Konsolidierung im PRD-v3-Entwurf").

**Verhaeltnis zu den Originalen.** Bis zum Beschluss gelten unveraendert `scinance3-impl/PRD_SCINANCE3.md` (v2,
angenommen 2026-09-02) und `scinance3-impl/state/decisions.md` (DEC-51..DEC-105 mit allen Nachtraegen); bei Widerspruch
gilt die DEC (PRD v2, Kopfzeile). Diese Datei ist eine **Lesefassung**: sie aendert keine Regel, fuehrt keine Lockerung
ein, registriert nichts und entscheidet keinen Widerspruch (offen gefuehrt in 5.3). Beide Originale bleiben append-only
unveraendert; v3 wird als **neue Datei** vorgeschlagen (Ablageort und Name entscheidet der Beschluss, Abschnitt 8).

**Lesehinweis.**
- Regelnummern **VR-xNN** (x = Gruppe a..h in Abschnitt 2; 2i ist ein Konstanten-Verweis ohne eigene Regeln); Pflichtzeilen **PZ-NN** (Abschnitt 3); Widersprueche
  **WD-NN** (5.3); Konkordanzzeilen **KO-NNN** (Anhang 7). Jede Regel steht genau einmal; andere Stellen verweisen.
- **Wortlaut:** verdichtet aus der Herkunft; massgeblich bleibt bis zum Beschluss die Quelle. Siegel- und
  Hygieneregeln stehen **woertlich** (Zitatblock). Zahlen tragen ihre Fundstelle in derselben Zeile.
- **Etikett:** L = Lockerung, V = Verschaerfung, n = neutral (Bestand, Klarstellung, Praezisierung, Erratum), jeweils mit
  Richtung, wo die Quelle sie nennt, und Entscheider **N** (Nutzer) / **O** (Orchestrator). "Bestand" = unveraendert aus
  PRD v2 bzw. Kompendium C/D.
- **Geltung:** **sofort** (in Kraft seit der Herkunfts-DEC); **ab K1** (Registrierungen ab Kohorte 1 = 2027-01-01,
  DEC-104 E0); **bis K1** (bestehende Eintraege und Registrierungen vor K1; derzeit keine offen, DEC-104 E0); **mit F6**;
  **vorgeschlagen** (nicht beschlossen; nur mit Entscheider).
- Quellenmarken bleiben: [sek] Sekundaerbeleg, [R] Rechnung, [U] Urteil, [V] Vermutung, UNBELEGT.
- Kuerzel: K1 = Kohorte 1; W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-28 (DEC-99 (8)); SE_12 = Standardfehler
  eines 12-Monats-Fensters (OC, Konventionen); SK0..SK3 = Statistikklassen Zaehlung / Streuung ohne Mittel / Screen /
  Gate-Bit (DEC-104 N1 (10)); OC = `state/prd_analyse_2026-11-01/OC_VERFASSUNG31_2026-11-02.md`; PRD_ANALYSE =
  `state/PRD_ANALYSE_2026-11-01.md`; Sweep = `state/prd_analyse_2026-11-01/METHODEN_SWEEP_2026-11-02.md`.
- Rollen statt Modellbezeichnungen: Orchestrator, Herleitung, Review, Bau, Kartierung (DEC-105 "vorgemerkt"; K-14 (j)).
- Pfade relativ zu `scinance3-impl/`.

---

## 1. Mission und Grundidee

### 1.1 Mission (PRD 1; CLAUDE.md Mission; DEC-105 (9); DEC-104 E1)

1. Scinance 3 ist ein Falsifikationsprogramm, das ausschliesslich dort sucht, wo die 11-15-bp-Friktionswand irrelevant
   wird - Risikopraemien (Klasse P), Tages- bis Wochenhorizont mit breitem Universum (Klasse W), kalendarisch exogene
   Ereignisse (Klasse E) - und vorher misst, ob eine Klasse ueberhaupt testbar ist (CLAUDE.md, Mission; PRD 1 "Der Pivot").
2. **Messinstitution vor Pruefinstitution.** Jeder Lauf erzeugt einen Effektschaetzer mit 95-%-Konfidenzintervall und
   oberer Ausschlussgrenze (VR-f01); Verdikte (PASS/DROP) bleiben konfirmatorisch und setzen Vorregistrierung voraus;
   Mess-Gate und Tradability-Gate bleiben getrennt (DEC-104 E1; C.2).
3. **Pivot-Begruendung (Ergaenzung nach DEC-105 (9)).** PRD 1 begruendet den Wechsel weg von Sekunden-/Minutenhorizonten
   mit der Friktions-Arithmetik (perfektes 1-s-Orakel 0,71 bp gegen 11 bp, PRD 1). Dazu gehoert: der dominante
   2.0-Fehlermodus "kein Signal" (H-03 Surrogate-p ~1,0, H-09 Rauschmuster, H-24 Vorzeichen) wird durch den
   Horizontwechsel nicht adressiert; an der Friktion starben nur H-04b/H-05c; die Wand ist VIP0-Taker mit ~4 bp
   ungemessener Slippage; die Gebuehrenstufe des Nutzers ist offen (P-11). "2.0 starb an der Friktionswand" ist kein
   PRD-Zitat (DEC-105 (9); Review B-13).
4. **Missionszeile Horizont.** "Kein 3.0-Kandidat unter Tageshorizont" (PRD 1) steht nach DEC-105 (1) auf einer Zahl mit
   Fehlerfaktor ~2,5 (Modell) x ~4 (Kosten); Stundenhorizonte zu oeffnen ist eine Nutzerfrage und muesste D.4, D.12,
   D.14 als Nicht-Wiederholungs-Nachweis (C.1) adressieren (DEC-105 (1)). Bis zur Nutzerentscheidung gilt die Zeile.

### 1.2 Bilanz (Stand 2026-11-02)

- 2.0: 31 Gate-Eintraege, 0 handelbare Kanten (PRD 1).
- 3.0: fuenf Gate-Eintraege GL-032..GL-036, alle GL-012 (vor dem Lauf, vor der Registrierung oder im Pilot); kein Test
  auf einem Urteilsfenster (PRD_ANALYSE 0.1; DEC-105 (13)). Klasse W auf den Fenstern bis 2026-06-28 ausgeschoepft,
  Programm im Aufzeichnungsmodus (DEC-102 N2). Verfassung 3.1 beschlossen (DEC-104, Nutzerentscheid 2026-11-02),
  prospektiv ab K1; Vorbedingung OC erfuellt, E2-Vorbehalt ausgeloest (DEC-104 N2).

### 1.3 Die vier regierenden Zahlen (PRD 1; korrigiert)

| Groesse | Stand v2 (PRD 1, 9.2 B) | Stand v3 | Quelle |
|---|---|---|---|
| Horizont-Friktions-Kurve | Mindesthorizont p 0,55: 6,6 h Taker / 53 min Maker; Wochen-IC 0,05: 2,7 Tage Taker | Kante Gauss-konsistent (Faktor pi/2 = 1,571 bei IC 0,05; Rang pi^2/6 = 1,645); p 0,55 Taker 2,72 h; Wochen-IC 0,05 Taker 1,11 Tage; oekonomisches IC-Minimum 0,040 statt 0,062; "~7 h Maker" mit PRD-Formel 8,67 h (Gauss-konsistent 3,5 h); gefuehrt als Kurvenschar (VR-c02, VR-c03) | DEC-105 (1), (8) |
| Sharpe-Nachweisdauer (Lo 2002 [sek]) | `T_min ~ 6,18/SR^2`; SR 0,5 -> 24,7 a | unveraendert; Lo-Beispiel mit q 365: SR 2,0 -> 1,55 a (nicht 1,80); der Praemientest ist dieselbe Arithmetik: C.10 mit 12 Monaten verlangt SR_eff >= 2,49 je Fenster (1,76 bei 2, 1,44 bei 3 Jahren) | DEC-105 (2) |
| IC-Rauschboden | "SD_null(IC_t) ist die bindende, UNGEMESSENE Zahl - WP-7 misst sie direkt" | Permutations-Spearman hat Varianz 1/(K-1) unabhaengig von der Renditestruktur (Identitaet); Breite wirkt nur ueber die Zeitreihen-SD von IC_t; reale fm8-IC-Streuung 2,3..2,6x der Ein-Faktor-Null; bindend ist die SD der Teststatistik (VR-b08) | DEC-105 (5); GL-035; DEC-94 (3) |
| Kosten des harten Ein-Fenster-DROP | Power 0,5 -> 0,25; Retention Faktor 4,7 | Faktor 5,2 (`Phi(1,4-1,6449)^2 = 0,163`); nominal 0,80 je Fenster ist Entscheidungs-Power 0,64; ab K1 Power 0,80 auf der gemeinsamen Regel (VR-b14) | DEC-105 (3); DEC-104 E2 |

### 1.4 Die drei Hypothesen-Klassen (PRD 3.2; Stand)

- **Klasse P - Praemien-Ernte.** Urteilstragend `mean(prem)`, nie Sharpe (VR-f13). Nulleffekt-Katalog: Jensen-/Konvexitaet,
  Ueberlappung, Peso, Selektions-Decke, MaxDD-Boden, Tail-Ratio-Richtungsfehler (PRD 3.2). Status: Programmfrage P-10
  (Default "Mess-/Aufzeichnungsprogramm", DEC-104 "Offen"); A1 und VRP strukturell geschlossen (DEC-104 E3 (e)).
- **Klasse W - Wochen-Horizont-Querschnitt.** Urteilstragend der Querschnitts-Rank-IC, nicht ueberlappend (PRD 3.2;
  DEC-51 (5)); Nulleffekte Querschnitts-Permutation (nur als Identitaet, VR-b08), Persistenz-Null, Selektions-Decke,
  faktorerhaltende Null mit skalierter Streuung (VR-e06). Status: Abschnitt 4.3.
- **Klasse E - Ereignis-Studien.** Genau ein vorregistriertes Fenster, kein Fenster-Scan; Resampling-Einheit Kalender-
  Cluster (PRD 3.2). Fuer A2 ist der Nulleffekt "Zufallstermine identischer Kalenderverteilung" durch die
  Label-Permutation ersetzt (VR-e12). Status: Abschnitt 4.2.

---

## 2. Verfassung 3.1 - Regeln

### 2a. Kompendium C.1..C.19 und D (`survey/ERKENNTNIS_KOMPENDIUM.md` Abschnitte C, D; Wortlaut dort normativ)

| Nr | Regel (Kurzform) | Herkunft | Etikett | Geltung / Status 3.1 |
|---|---|---|---|---|
| VR-a01 | C.1 Registry-Disziplin: Pre-Registration, append-only, kein Torpfosten-Verschieben in keine Richtung; symmetrisch auch fuer unliebsame PASS; Aenderung nur als neuer Eintrag (Rueckzug + Neufassung) | C.1; PRD 3.1; CLAUDE.md Autonomie 1; UEBERGABE 2026-10-09 Abschn. 1 | n, Bestand | sofort, unveraendert |
| VR-a02 | C.2 Mess-Gate != Tradability-Gate: keine Handelskostenzahl als PASS-Bedingung; v2-Verschaerfung: auch nicht als Befundzweig eines Zensus-Pakets und nicht als Feasibility-Kill-Bedingung; die Wand ist Etikett in der Entscheidungsrelevanz-Zeile | C.2; PRD 3.1 "Bestaetigung zu C.2" (Review PRD3 2.1); DEC-104 E1 | n, Bestand | sofort; der Teil "Feasibility-Kill" steht unter 3.1 gegen VR-c01 (SESOI aus Kosten) -> **WD-01 offen** |
| VR-a03 | C.3 Anti-Gaming: Wand, Latenz-Haircut, Fill-Annahme vorab fixiert, nie absenkbar | C.3 (DEC-13/16) | n, Bestand | sofort |
| VR-a04 | C.4 Struktureller Nulleffekt der Metrik VOR der Schwelle ausrechnen und zusaetzlich am Null-Fixture messen; jede Pflicht-Messgroesse wird vor dem Bau daraufhin geprueft, ob ihr Schaetzer unter der Null informativ ist (Nachweis am Null-Fixture mit realistischer Heterogenitaet, nicht nur mit gleichen Varianzen). Operationalisierung nach Kritik K-3 (Zensus-Schaetzer muss auf eine Faktor-Null anders reagieren als auf ein iid-Panel) ist vorgeschlagen, O | C.4; PRD L-2, L-2b; PRD_ANALYSE 1 (K-3) | n, Bestand; K-3-Zusatz vorgeschlagen | sofort |
| VR-a05 | C.5 Positives UND negatives Fixture (DEC-39); in 3.0 zusaetzlich adversariales Fixture (PZ-05) | C.5; PRD 3.3.5 | n, Bestand | sofort |
| VR-a06 | C.6 Materialitaets-Schranke statt Bit-Identitaet gegen lebende Speicher, plus SHA-256; jede importierte Materialitaets- oder Toleranzschranke braucht ihre eigene Erreichbarkeitspruefung | C.6; PRD L-1 | n, Bestand | sofort |
| VR-a07 | C.7 N=2 beweist keinen Determinismus; Nachweis N>=3 mit Fingerabdruck (T2) | C.7; PRD L-8 | n, Bestand | sofort |
| VR-a08 | C.8 Negative Behauptungen brauchen eine Inhaltsprobe, keine Namenskonvention | C.8; PRD L-9 | n, Bestand | sofort |
| VR-a09 | C.9 Keine n=1-Extrapolation ohne Kontrolle der erzeugenden Achse | C.9 | n, Bestand | sofort |
| VR-a10 | C.10 Hartes Ein-Fenster-Abbruchkriterium: Verfehlen in EINEM von >=2 disjunkten Fenstern ist DROP/PARK | C.10; PRD 3.5 | n, Bestand | bis K1 (Zuordnung VR-b11); fuer 3.1-Registrierungen **ersetzt** durch VR-b14 (DEC-104 E2, E10) |
| VR-a11 | C.11 Modul != Strategie | C.11 | n, Bestand | sofort |
| VR-a12 | C.12 Struktureller A-priori-DROP vor jedem Datenlauf (Feasibility; Ausgang GL-012) | C.12; DEC-51 (2) | n, Bestand | sofort; ab K1 Massstab SESOI (VR-c01) |
| VR-a13 | C.13 Positivkontrolle als Pflichtbestandteil komplexer Mess-Maschinerien; ohne bestandene Kontrolle "methodisch invalide", nicht DROP | C.13; PRD L-11 | n, Bestand | sofort; Ausfuehrung VR-f12 |
| VR-a14 | C.14 Loud-Fail-Doktrin | C.14 | n, Bestand | sofort |
| VR-a15 | C.15 Checkpoint-Round-Trip, nicht nur Rechenpfad | C.15 | n, Bestand | sofort |
| VR-a16 | C.16 Zweistufige FDR (Familie -> Ueber-Familie), nur verschaerfend | C.16 (DEC-22) | n, Bestand | sofort; ausgefuehrt in VR-b16, VR-b17, VR-d13 |
| VR-a17 | C.17 Data-Snooping-Offenlegung, Entdeckungszellen-Ausschluss; Konfirmation braucht andere Zellen/Fenster | C.17 | n, Bestand | sofort; Buchfuehrung VR-d18 |
| VR-a18 | C.18 REZENZ-Klausel: urteilstragende Fenster decken das juengste Marktregime ab | C.18 (DEC-38) | n, Bestand | Satz "aeltere Historie rein deskriptiv" **ersetzt** durch VR-d02/VR-d03 (DEC-99 (1)/(2), sofort) und ab K1 durch VR-e02 (DEC-104 E6) |
| VR-a19 | C.19 Reversibelste Option bei Unterspezifikation, dokumentiert als DEC, nie fuer Gate-Schwellen | C.19; CLAUDE.md Autonomie 2 | n, Bestand | sofort |
| VR-a20 | Kompendium D.1..D.17 (verworfene Ansaetze) sind programmweit erledigt; jede Wiederholung ohne nachweislich neues Signal verstoesst gegen die Registry-Disziplin (Nicht-Wiederholungs-Nachweis nach C.1, z. B. Klasse W nie auf N=5 zurueckskalieren, D.7). D.17 gilt fuer dichte Ketten-Kandidaten fort; neu ist nur die Tiefe der monatlichen Tardis-Kette | Kompendium D; PRD 4.1 B1; DEC-105 (10) | n, Bestand | sofort |

### 2b. Fehlerraten und Entscheidungsregel

| Nr | Regel (Wortlaut verdichtet, bindend) | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-b01 | Mess-Gates: alpha 0,05 einseitig je Fenster in registrierter Richtung; die Richtung ist Teil der Registrierung (YAML `richtung`); zweiseitige META-/Zensusfragen alpha 0,05 zweiseitig, ausdruecklich so etikettiert | DEC-51 (1) | n, Bestand, O | bis K1 fuer Fenster-Tests (ab K1 alpha je Test VR-b14); Richtungs- und Zensus-Konvention sofort |
| VR-b02 | Power-Ziel 0,80 fuer den in der Power-Zeile benannten Mindesteffekt; liegt die A-priori-Erwartung darunter: GL-012 oder anderes Design | DEC-51 (2) | n, Bestand, O | bis K1; ab K1 Power 0,80 der gemeinsamen Entscheidungsregel an der SESOI-MDE (VR-b14, VR-c01) |
| VR-b03 | Cluster-Einheit = groesste Einheit gemeinsamer Schocks (Symbol-Panel: Kalendertag bzw. -woche; Ereignisstudie: das Ereignis, alle Symbole desselben Verfalls = ein Cluster; Fenster-Design: das Fenster); `N_eff = N/(1+(N-1) rho)` mit GEMESSENEM rho, rho = 0 nie Default; N-Floor gilt fuer N_cluster, nie N_events; Bar-Cache-Pakete: Kalendertag, ein Schock-Tag = ein Cluster | DEC-51 (3); PRD 3.3.3; DEC-63 (2) | n, Bestand, O | sofort |
| VR-b04 | Selektions-K vorab registriert; Schwelle ueber der Bailey/Lopez-de-Prado-Decke fuer K, zusaetzlich am Null-Fixture gemessen; die Power-Zeile rechnet mit `max(z_krit, z_max(K))`, unter VR-b06 ab K >= 12 bindend (z-Einheiten statt SR-Einheiten) | DEC-51 (4); PRD 3.3.4; DEC-94 (7) | n, O | sofort |
| VR-b05 | Ueberlappende Renditen zaehlen nicht als unabhaengige Beobachtungen; N_eff ueber Blocklaenge; bei Ueberlappung ist der Varianzfaktor c >= 1 Pflicht | DEC-51 (5); DEC-104 N2 (7) | n / V, O | sofort |
| VR-b06 | **Kritischer Wert.** Jede urteilstragende Signifikanzbedingung lautet "Statistik in registrierter Richtung >= z_krit x SE", z_krit = Phi^-1(1-alpha): je Fenster 1,6449; DEC-52-Zweig gepoolt 2,5287 (alpha 0,0057); zweiseitige Zensusfragen 1,9600; Bootstrap-Grenzen und Null-Quantile derselben Bedingung auf Niveau 1-alpha. 2,4865 / 3,1680 / 2,8016 sind MDE-Faktoren (z_krit + 0,8416) und stehen nie als Schwelle; Feld- und Konstantennamen trennen `z_krit` und `mde_faktor`. Unter 3.1: gepoolt z_krit 2,8070 (alpha 0,0025), Screen 1,6449 | DEC-94 (1); DEC-104 E2 | L (Testbarkeit; Etikett DEC-94 "Lockerung"), O | sofort; bleibt ab K1 (DEC-104 E2, E10) |
| VR-b07 | Strengeres alpha nur explizit, vor jeder Feasibility-Zahl, als Zahl im YAML; Regime-Zuordnung immer mit Default-alpha 0,05 je Fenster und vollstaendiger Nuisance-Liste; ein Schwellenfaktor ohne zugehoeriges alpha ist ein ungueltiger Eintrag | DEC-94 (2) | n, O | bis K1; Stand ab K1 in DEC-104 nicht genannt -> **WD-06** |
| VR-b08 | **Eine SE fuer Test und Power.** Power-Zeile, MDE80, Zuordnung und GL-012-Pruefung mit genau der Entscheidungs- und SE-Regel des registrierten Gates: je Bedingung `P = Phi((prior - T)/SD)`, bei `T = z_krit x SE` also `Phi(prior/SE - z_krit)`; `MDE80 = max_Bedingungen (T + 0,8416 x SD)`; ist die SE-Regel datenabhaengig, die SD der getesteten Statistik, nie ein Rauschboden allein; dies gilt einschliesslich der faktorbedingten Streuung der Cluster-Statistik unter der kalibrierten Null | DEC-94 (3); DEC-92 Lehre | n, O | sofort; ab K1 inhaltsgleich in DEC-104 E2 ("SE des registrierten Tests") |
| VR-b09 | **Autokorrelation der Teststatistik.** Im Lauf `SE_W = max(SD(x)/sqrt(W), SE_stat(x))`, SE_stat aus dem stationaeren Bootstrap (Politis/Romano) der urteilstragenden Cluster-Serie, >= 1.000 Replikate, Seed registriert (DEC-53); Blocklaenge aus der gemessenen Autokorrelation statt fest (der Default "4 Wochen" aus DEC-94 (4) ist damit abgeloest); Power-Zeile mit `c = max(1, c_hat)` derselben Statistik, keine Gutschrift fuer negative Autokorrelation; DEC-67 E4 (W_eff = 0,41 W) nur fuer Statistiken mit nachgewiesen gleicher Autokorrelation, sonst deskriptiv; c ist Varianz-, sqrt(c) SD-Faktor | DEC-94 (4); DEC-104 N2 (7) | n / V, O | sofort |
| VR-b10 | **Herkunft der Nuisance.** SD und c der Teststatistik aus beiden Quellen, soweit verfuegbar: (i) Vorperiode vor dem ersten Urteilsfenster (nur Streuung und Autokorrelation, kein Mittel, Waechter im Code), (ii) kalibrierte Null-Simulation des registrierten Tests; ist die Vorperioden-Statistik versiegelt, nur (ii); bindend die groessere SE ueber Quellen und registrierte Kalibrierungen (stress, DEC-77 E1 (b)); die Positivkontrolle in Produktionskonfiguration ist NICHT BESTANDEN, wenn die SD ihrer Kontrollwelt mehr als 10 % ueber der SD der Power-Zeile liegt | DEC-94 (5) | n, O | sofort; ab K1 Konflikt mit VR-e03 -> **WD-02** |
| VR-b11 | **Regime-Zuordnung (Bestand).** Fenster-Power >= 0,80 in jedem urteilstragenden Fenster -> C.10 hart; sonst DEC-52-Zweig, wenn das Produkt der Einzel-Powers (gepoolte Bedingung, beide Fenster-Screens) >= 0,80; sonst GL-012 vor dem Lauf; einmal vor der Registrierung festgestellt, nie nach dem Lauf. DEC-52-Zweig: (ii) je Fenster Vorzeichen und `>= 0,5 x z_krit_gepoolt x SE_gepoolt`, Band-Obergrenze 2,0x nur Etikett; (iii) Signifikanz ausschliesslich gepoolt mit fenster-geclustertem stationaerem Bootstrap (bei zwei Fenstern stratifiziert je Fenster, Auslegung); (iv) z_krit 2,5287; (v) Retro-Check veroeffentlicht, kein Verdikt kippt, Etikett "Verbesserung" | DEC-52 (i)-(v) + Nachtrag 2026-09-02; DEC-94 (6) und "Nicht Teil von P-1" | L (DEC-94), O | bis K1; ab K1 **ersetzt** durch VR-b14 (DEC-104 E2) |
| VR-b12 | Power, MDE80 und Zuordnung berechnet eine getestete Funktion (T0; T4 auf konserviertem Payload reproduziert GL-032 und GL-033; Monotonie-Test: steigender Prior wechselt nie von testbar zu GL-012), die dieselben Schwellen- und SE-Funktionen wie der Lauf benutzt; Handrechnungen sind Gegenprobe, nie Quelle | DEC-94 (8); Werkzeug F3 `src/bybit_edge/research/feasibility31/` (PRD_ANALYSE Nachtrag 3) | n, O | sofort |
| VR-b13 | Doppelausweis: jede Registrierung unter DEC-94 weist ihr Regime zusaetzlich unter der A3-Praxis aus (Schwellenfaktor 2,4865 + DEC-87 (F), Produktrechnung); nur unter DEC-94 zulassungsfaehig -> Etikett "zugelassen nur durch DEC-94 (Lockerung)" in Registry und GL | DEC-94 (9) | n, O | bis K1; Stand ab K1 nicht genannt -> **WD-06** |
| VR-b14 | **Konfirmationsregel 3.1.** Konfirmationstest ist der gepoolte einseitige Test ueber alle Konfirmationsdaten der Registrierung bei alpha 0,0025 (z_krit 2,8070) **plus REZENZ-Screen**: das juengste 12-Monats-Fenster (bei Quartalsblicken die letzten vier Quartale) besteht einseitig bei alpha 0,05 (1,6449); PASS nur, wenn beides erfuellt. Power-Ziel 0,80 fuer die gemeinsame Entscheidungsregel an der registrierten MDE (= SESOI, VR-c01), gerechnet mit der SE des registrierten Tests (VR-b06, VR-b09 bleiben). alpha je Test fest 0,0025, nicht aus einem Budget verteilt; das Jahresbuch (VR-d14) kommt hinzu. Ersetzt C.10 / DEC-52 / DEC-94 (6) fuer 3.1-Registrierungen. Datenfaktor: +23 % (zwei Fenster), +59 % (drei), +103 % (vier) gegen C.10 je 0,80 bei gemeinsamer Power 0,80 (die "+8 %" der Synthese galten ohne Screen) | DEC-104 E2; DEC-104 N2 (2) | L in der Power (0,64 -> 0,80), alpha je Test unveraendert, N | ab K1; **Entscheidungspunkt P-2 offen** (unten) |
| VR-b15 | Pflicht-Bestaetigung auf neuen Daten (naechste Kohorte oder naechster K-Blick) vor jeder Tradability-Frage | DEC-104 E2 | V (Teil von E2), N | ab K1 |
| VR-b16 | FDR innerhalb der Familie: Einheit ist die Variante (Panel-Mitglieder sind Beobachtungen, keine Hypothesen, und werden zu EINER Teststatistik gepoolt, L-7); p-Wert = Max-p ueber die Fenster; BH alpha 0,10; K bleibt Nenner auch bei nicht gerechneten Varianten (p = 1). Ueber-Familie (F-WEEK, F-PREM u. a.) in der abhaengigkeitsrobusten Form (Benjamini-Yekutieli) am Wellen-/Kohortenschluss, solange Kohaerenz nicht ausgeschlossen ist (F-PREM1/F-PREM2 im Stress verbunden) | C.16; PRD L-7; PRD 4.3 (FDR-Wirkung); DEC-62 E3; DEC-65 (3); DEC-74 (e) (unveraendert nach DEC-99 (6)) | n, Bestand, O | sofort |
| VR-b17 | Zaehlregel: in eine Ueber-Familie gehen nur Hypothesen mit tatsaechlich berechnetem p; "GL-012 vor dem Lauf"/"nicht uebergeben" (p = 1) bleiben in der Selektionsdeflation ihrer Kohorte (festes K, BH-Nenner, Decke), nicht in m; Doppelausweis unter alter Zaehlung. K einer Registrierung = Varianten mit berechnetem Outcome (Pilot/Screen) plus registrierte, nicht gerechnete Varianten derselben Registrierung; Gabelungen ohne Datenblick zaehlen nicht in K und m, stehen aber im Gabelungsregister (Strenge-Quotient) | DEC-99 (7); DEC-104 N1 (9) | L (DEC-99 (7), N); Klarstellung (N1 (9), O) | sofort |

**ENTSCHEIDUNGSPUNKT P-2 (offen, Entscheider N) - Variante der Konfirmationsregel.** Die OC hat den Vorbehalt von
DEC-104 E2 ausgeloest ("Screen-Powerstrafe > 10 %"; DEC-104 N2 (2)); nach dem Wortlaut von E2 wird E2 "per Nachtrag
nachgefuehrt, bevor die erste Registrierung erfolgt". Struktureller Boden [R]: P(PASS) <= P(Z_rec > 1,6449); die
gemeinsame Power 0,80 verlangt einen Effekt >= 2,4865 SE_12 unabhaengig von der Konfirmationslaenge; "E2 in der
beschlossenen Form macht keinen Effekt testbar, den ein einzelnes 12-Monats-Fenster bei 0,05 nicht mit Power 0,80 sieht"
(DEC-104 N2 (3)). Gerechnete Varianten (zwei Fenster, r 1/2; DEC-104 N2 (4)):

| Variante | alpha_eff | Boden (SE_12) | Daten gegen gepoolt ohne Screen | P(PASS bei Effekt nur im aelteren Teil, 1 / 2 MDE) | A2 (SESOI 22 bp) | Klasse W, SD 0,13 (SESOI 0,040) | Status |
|---|---|---|---|---|---|---|---|
| (a) Screen 0,05 | 0,0019 | 2,49 | x1,14 | 0,039 / 0,05 | nie | nie | **beschlossen (DEC-104 E2); gilt bis zum Entscheid** |
| (a') Screen 0,20 | 0,0024 | 1,68 | x1,01 | <= 0,20 | Boden ~16,4 bp [R, Modell] | Boden 0,030 | gerechnet, nicht vorgeschlagen |
| (a'') Vorzeichen-Screen 0,50 | 0,0025 | 0,84 | x1,00 | <= 0,50 | - | - | gerechnet, nicht vorgeschlagen |
| (c) P-6-Lesart: gepoolt 0,0025 + registrierter Stabilitaetstest "juengster Teil faellt nicht ab" (einseitig 0,05, Power 0,95), unabhaengige Statistiken | 0,0024 | kein Boden | x1,09 (jede Fensterzahl) | 0,073 / 0,013 | 42 Monate: Lesart B 2028-01 | Lesart B 2027-07 | **vorgeschlagen, Entscheider N** (Orchestrator-Vorschlag als neuer Default; Herleitung der Stabilitaetsstatistik vor K1, DEC-104 N2 (4)) |

Jede Variante ausser (a) ist gegen den Wortlaut von E2 eine Lockerung in der REZENZ-Dimension (OC "Was folgt" 2).

### 2c. Prior und SESOI

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-c01 | **SESOI als Feasibility-Massstab.** Kleinste oekonomisch relevante Wirkung je Kandidat, vorab registriert aus dem registrierten Kostenmodell (`constants_hash`) als **Kurve ueber Horizont und Signal-Persistenz**, nicht als Konstante; Default-Kostenbasis Taker (VIP0) mit Etikett "Gabelung Richtung Testbarkeit gegen Maker". Testbar, wenn MDE80 (VR-b14) <= SESOI; sonst GL-012 "strukturell nicht testbar bei heutiger Nuisance und Fensterlaenge" (definitive Aussage statt UNBELEGT) | DEC-104 E3 (a) | L (Testbarkeit), N | ab K1; Vorbedingung "registriertes Kostenmodell" nicht erfuellt -> **WD-08**; Verhaeltnis zu C.2 -> **WD-01** |
| VR-c02 | **Kantenmodell.** Kante je Position unter bivariater Normalitaet `IC x 0,798 sigma` (Pearson) bzw. `2 sin(pi IC/6) x 0,798 sigma` (Rang); K-0.1 wird als Kurvenschar (Kante x Signal-Persistenz x Kosten) gefuehrt, nicht als Konstante; L-18-Vermerk: der zu pessimistische Faktor ist dokumentiert und wird nicht spaeter als Kantenverbesserung verkauft; nicht geheilt: der kategoriale Rest (Querschnitts-IC im Einzelpositionsrahmen als Zeitreihenkorrelation gelesen) | DEC-105 (1); DEC-104 E3 (a) | n (Erratum), O | sofort |
| VR-c03 | **Kostendeckung je Tag.** Vorzeichenwechselrate eines AR(1)-Signals `arccos(phi)/pi` = 0,500 / 0,333 / 0,205 bei phi 0 / 0,5 / 0,8; IC_min Taker 11 bp 0,0263 / 0,0175 / 0,0108; Maker 4 bp 0,0096 / 0,0064 / 0,0039; gesamt 15 bp 0,0359 / 0,0239 / 0,0147; "voller Tagesumschlag 0,053" entspricht phi = -1 und ist keine Obergrenze; gilt als SESOI-Kurve der Klasse W/Tageshorizont bis zur Messung der Persistenz je Praediktor | DEC-105 (8) | n (Erratum), O | sofort; Rahmenfrage -> **WD-04** |
| VR-c04 | **Zwei SESOI-Rahmen.** Einzelpositionsrahmen (0,0263 / 0,0175 / 0,0108, PRD K-0.1 korrigiert) fuer Klasse E/P; fuer Klasse W der Dezil-L/S-Rahmen (L-18, Dezilfaktor 3,51): persistenzbereinigt 0,0085 / 0,0056 / 0,0035 (Taker, phi 0 / 0,5 / 0,8); Persistenz je Praediktor in Zone X zu messen, bis dahin phi = 0 als Default (Etikett) | PRD_ANALYSE Nachtrag 3 [R, F3] | n, O (Praezisierung ohne DEC) | **vorgeschlagen bis Bestaetigung**; widerspricht VR-c03 -> **WD-04** |
| VR-c05 | **Literatur ist Etikett.** Pflichtzeile "Literatur: primaer belegt / [sek] / UNBELEGT" ohne Blockadewirkung; die PRD-Vorbedingung "belegter Literatur-Prior vor jeder Registrierung" entfaellt fuer 3.1. Bis K1 gilt: Prior-Pflicht (Arbeitsregel 4; DEC-102 E3; PRD 5.2 Vorbedingung V-5) | DEC-104 E3 (b); CLAUDE.md Arbeitsregel 4 | L (Lockerung der PRD-Vorbedingung, FPR je Test unveraendert), N | ab K1 (Bestand bis K1) |
| VR-c06 | **Prior als Verteilung.** Richtung und Groessenordnung einer Registrierung duerfen aus Zone-X-Schaetzern kommen (VR-d10), ausschliesslich selektionsbereinigt (bedingt median-unverzerrt nach DEC-99 (3)) und mit dem Selektions-K im Konto; der Pilot-Betrag als Punktprior bleibt verboten (GL-035, DEC-102 E3) | DEC-104 E3 (c) | L (Testbarkeit), N | ab K1; Verhaeltnis zu VR-f09 -> **WD-09** |
| VR-c07 | **UNBELEGT symmetrisch.** Eine unbelegte Nuisance- oder Designgroesse erzeugt eine registrierte Sensitivitaetsspanne in beide Richtungen, nie einen Worst-Case-Default als bindende Zahl; der Worst-Case nur als etikettierte Stress-Zeile (aendert Arbeitsregel 4 und die Default-Linie "0,95 Richtung Strenge", DEC-103 N1). Bis K1: "Fehlendes heisst UNBELEGT und blockiert die abhaengige Konstante (RAISE), nie ein Default" | DEC-104 E3 (d); CLAUDE.md Arbeitsregel 4 | n, N | ab K1 (Bestand bis K1) |
| VR-c08 | **Feststellungsform.** "Strukturell nicht testbar" ist ein Feasibility-Befund ohne Verdikt; Wiedervorlage nur bei veraenderter Nuisance, laengerem Horizont oder neuem Kostenmodell; angewandt auf A1 und VRP per Vermerk (4.1, 4.6) | DEC-104 E3 (e) | n (Feststellung), N | sofort (Vermerk) |

### 2d. Fenster-Politik: Zonen, Kohorten, Blicke, Konto

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-d01 | **Programmfenster.** W1 = 2024-07-01..2025-06-30 (53 Kalenderwochen, geurteilt 52; DEC-74, DEC-75 (1)); W2 = 2025-07-01..2026-06-28 (letzte vollstaendige Outcome-Woche vor dem Blind-Siegel, w_judged 50); Zone V fuer Tagesstatistiken 2024-07-01..2026-06-30 (die Tage 2026-06-29/30 gehoeren zu V). Pilotabschnitt der Renditefamilie: Datengrenze 2022-04-18..2024-06-30 (Panel-Schnitt), letzte Formationswoche 2024-06-17, letzte Outcome-Woche bis 2024-06-24 | DEC-99 (8); DEC-74 Anlass; DEC-104 N1 (3) | n, N/O | sofort |
| VR-d02 | **REZENZ als notwendige Bedingung.** Jede Registrierung hat ein urteilstragendes Fenster, das mit der letzten vollstaendigen Cluster-Einheit vor dem juengsten ergebnisblind nutzbaren Tag endet (bei einem Blind-Siegel: vor dem Siegel); dieses Fenster muss bestehen (C.10: alle Fensterbedingungen; DEC-52-Zweig: der Screen im juengsten Fenster) | DEC-99 (1) | L (Richtung Testbarkeit), N | sofort; ab K1 kodiert in VR-b14/VR-e02 |
| VR-d03 | **Aeltere Daten** nur vorab registriert: (a) als Pilot-Schaetzfenster (Prior und Nuisance fuer eine vorab fixierte, mechanische Uebergaberegel; nie urteilstragend; Etikett "Pilot, nicht urteilstragend; Screening, nie Konfirmation (C.17/C.18)"; GL-012 (Pilot) ist kein Verdikt) oder (b) als zusaetzliches Urteilsfenster unter C.10, nie als Ersatz des juengsten | DEC-99 (2) | L, N | sofort (Exploration ohne Registrierung: VR-d10) |
| VR-d04 | **Pilot-Bedingungen.** Uebergaberegel und Prior-Lesart vor dem Oeffnen registriert; letzte Pilot-Outcome-Woche endet vor dem ersten Tag des ersten Urteilsfensters; Panel vor jeder Pilot-Rechnung am letzten Pilot-Outcome-Tag geschnitten (Code-Waechter mit Test); genau ein Pilotlauf (Neulauf nur bei nachgewiesenem Code-/Datenfehler per DEC, beide Ergebnisse offengelegt, das korrigierte bindet in beide Richtungen); Pilot-Ergebnis mit sha256 vor jedem Testfenster; Pflicht-Doppelausweis des selektionsbereinigten Pilot-Schaetzers und der Power daran. K zaehlt alle Pilot-Varianten: bis K1 nicht uebergebene mit p = 1 im festen BH-Nenner der Kohorte; ab K1 im Selektions-K der Pilotstufe, nicht im konfirmatorischen BY-Nenner; ab K1 Uebergabe ueber Assurance (VR-e05) | DEC-99 (3); DEC-104 E7 (b) | L, N | sofort / ab K1 wie angegeben |
| VR-d05 | Ein Pilot-Schaetzfenster ist kein Zensus im Sinne von DEC-58 E2 (registrierte Stufe derselben Hypothese mit eigenem K) | DEC-99 (4) | n, N | sofort |
| VR-d06 | **Verbrauch.** Nach einem Pilot ist der Pilotabschnitt programmweit fuer jede mit der dort gerechneten Statistik korrelierte Statistik nicht mehr blind; weitere Piloten zaehlen alle frueheren Varianten kumulativ in K; spaetere Registrierungen fuehren das Pilot-Ergebnis als gesehen. Fuer Zone-X-Explorationen durch das Konto ersetzt (VR-d10); fuer jede Registrierung, die sich auf den Abschnitt stuetzt, wirkt die Regel bis K1 weiter | DEC-99 (5); DEC-104 E4 (c); DEC-104 N1 (7) | L (Konto statt Verbrauch), N | Konto sofort; Registrierungen bis K1 |
| VR-d07 | **Pilot und geltende Regeln.** Fuer Registrierungen mit Pilot-Schaetzfenster: der Pilot gibt das Mittel aus (Ausnahme zu DEC-94 (5) (i)); bestehende Siegeldateien bleiben geschlossen; Zuordnung nach der Pilotstufe und vor jedem Testfenster mechanisch nach der Uebergaberegel; die A-priori-Erwartung ist der Pilot-Punkt der registrierten Lesart; der Pilot ersetzt den Literatur-Prior. Unveraendert: alpha je Fenster, z_krit, Power 0,80, DEC-53, DEC-96 E3, DEC-74 (e); der Pilot aendert keine Fehlerrate des Tests | DEC-99 (6) | n (Praezisierung), N | bis K1; ab K1 Prior als Verteilung (VR-c06) |
| VR-d08 | **Drei Zonen.** X (Exploration) = alle Daten vor 2024-07-01 fuer alle Familien (einschliesslich Pilotabschnitt der Renditefamilie und A2-Vorperiode 2021-03..2024-05); V (Validierung) = W1/W2, blind fuer Klasse W (fm8 ungeoeffnet; fm8-Reversal-Familie vorbelastet, VR-d19) und fuer A2 (Disziplin); K (Konfirmation) = ab 2026-07-01, versiegelt fuer alle Statistiken ausser Zaehlungen (SK0). **Zone K ist nicht rein:** je Datenfamilie beginnt das reine K-Fenster erst nach der letzten Oeffnung - F1 BTC/ETH-Aggregate und F6 Mikrostruktur 2026-10-01; F3 Funding-Lage 2026-09-15 (OI/Umsatz 2026-07-01); F2 Panel-Querschnitte, F4 Optionskette, F5 Live-Stroeme 2026-07-01 (F2 mit Disziplinsetikett fuer die versiegelten IC-Serien bis 2026-09-14); ein 12-Monats-K-Fenster fuer BTC/ETH-Statistiken endet am 2027-09-30 | DEC-104 E4 (a); DEC-104 N1 (2); FENSTERREGISTER Abschn. 1, 6 | E4 (a) Zone X: L (bis 8 Monate Blindheit), N; N1 (2): V, O | sofort |
| VR-d09 | **Rollieren.** Ab 2027-07-01 wandert am ersten Tag jedes Quartals das aelteste K-Quartal nach V und jedes V-Quartal, das aelter als 36 Monate ist, nach X; Zielzustand K = juengste 12 Monate, V = 12..36 Monate, X = aelter; W1/W2 werden nicht zu X erklaert | DEC-104 E4 (b) | Teil von P-4 (N); in der Etikett-Tabelle von DEC-104 ohne eigene Zeile | ab 2027-07-01 |
| VR-d10 | **Zone X.** Freie, wiederholte Nutzung; Pflicht-Konto je Abfrage in `state/KONTO_ZONE_X.md` (append-only): vor der Rechnung Datum, Familie, Statistik, Fenster, Varianten (K), Code-Hash eines versionierten Skripts, Zweck; nach der Rechnung Schaetzer, 95-%-KI, obere Ausschlussgrenze, Shrinkage-Hinweis, kumuliertes K, Ausgabedatei mit sha256; nie ein Verdikt; Zone V/K duerfen im Konto nicht erscheinen; jede Registrierung, die Richtung oder Groessenordnung aus einer Konto-Zeile bezieht, zitiert die Zeilennummer | DEC-104 E4 (c); KONTO_ZONE_X Regeln 1-4 | L (Richtung Testbarkeit), N | sofort mit Konto |
| VR-d11 | **Zone V.** Genau ein vorab registrierter Blick je Hypothesenfamilie und Kohorte; mechanische Blindheit: eine Registrierung darf nur V-Quartale nutzen, die zum Zeitpunkt ihrer Registrierung ungeoeffnet waren; C.17-Liste je Familie Pflicht; fuer Registrierungen auf Zone V gilt VR-b14 ohne Zwischenblicke | DEC-104 E4 (d), (e) letzter Satz | V (Strenge), O | sofort |
| VR-d12 | **Zone K, gruppensequentiell.** Registrierte Hypothesen sammeln Information in Blicken nach O'Brien-Fleming, bis zu 4 Blicke = 4 Quartale je 12-Monats-Konfirmation, Spending-Plan und Blickzeitpunkte im YAML; alpha gesamt 0,0025 je Test; Wirksamkeitsabbruch am Blick k nur mit bestandenem REZENZ-Screen auf den juengsten vier Quartalen bis k; Futility-Stopp (Z < 0 an den Blicken 1-3) beendet die Hypothese als "GL-012 (Futility)" ohne Verdikt; ein Blick erzeugt (Statistik, CI, Hash), die Outcome-Serie des Quartals wird fuer diese Statistik nie mehr geoeffnet. Kennzahlen OBF 4 Blicke bei 0,0025: E[N bei H1] 0,871, Maximum 1,007 N_fix; mit Screen an jedem Stopp (r 1/2) 0,9125 / 1,0695; mit Futility E[N bei H0] 0,65 | DEC-104 E4 (e); DEC-104 N2 (5); DEC-105 (13) | GSD: L in der Zeit, N; Futility: V, N | ab K1 |
| VR-d13 | **Kohorten.** Stichtage am ersten Tag jedes Quartals, erstmals 2027-01-01; alle vor dem Stichtag registrierten Hypothesen teilen dieselben K- und V-Scheiben; Multiplizitaet ueber die Kohorte nach Benjamini-Yekutieli q 0,10 im FDR-Buch (nur getestete Hypothesen, VR-b17); die Reihenfolge-Frage DEC-98 E4 (b) ist damit gegenstandslos (P-8). BY ist neben dem festen alpha fuer m <= 12 nie bindend [R] | DEC-104 E4 (f); DEC-98 E1 (d); DEC-104 N2 (1) | L (Teilen korrelierter Quartale) / V (BY), N | ab K1; Beginn-Lesart -> **WD-05** |
| VR-d14 | **Jahresbuch.** Institutionsweites Buch aller Blicke, Pilot-Uebergaben und outcome-beruehrenden Zensus je Kalenderjahr mit erwarteten Falsch-PASS (Summe der alpha), ausgewiesen in jeder Registrierung; Ueberschreitung von 0,10 erwarteten Falsch-PASS je Jahr loest eine Nutzer-Vorlage aus | DEC-104 E4 (g) | V, N | sofort |
| VR-d15 | **Lockbox.** Codegesicherter Einmalzugriff auf die Urteilsstatistik mit Registrierungs-Hash (F6); bis dahin gelten Waechter und Disziplin unveraendert | DEC-104 E4 (h) | V, O | mit F6 |
| VR-d16 | **Vorwissens-Klasse je Datenfamilie.** BTC/ETH-Aggregate (Renditen, Vol, IV, Funding BTC/ETH) sind nur in Zone K prospektiv konfirmierbar; einzige Ausnahme A2 (r_pre an Freitagen) auf W1/W2 als registrierte Statistik mit Disziplinsetikett; Panel-Querschnitte sind auf W1/W2 blind, soweit nicht per C.17 verbraucht; Register `state/FENSTERREGISTER.md` | DEC-104 E4 (i) (Kodifizierung der Praezedenz DEC-96 E1) | V, O | sofort |
| VR-d17 | **Zonen-Lesart fuer K1 (Lesart B).** Eine am 2027-01-01 registrierte Hypothese darf Zone V (ein Blick, nur Quartale, die fuer ihre Statistik blind sind) zusammen mit den reinen K-Quartalen nutzen; fuer BTC/ETH-Statistiken beginnt K am 2026-10-01 | DEC-104 N2 (8) | n (Feststellung), O | sofort |
| VR-d18 | **Oeffnungsbuchfuehrung.** `state/KONTO_INVENTAR_2026-11-02.md` (O-001..O-133, O-901..O-905, O-980) ersetzt die verstreuten C.17-/KONTAMINATION-/S-2-Listen als massgebliche Oeffnungsliste; kuenftige Registrierungen zitieren ihre Zeilennummern; FENSTERREGISTER Abschnitt 4 wird nicht mehr fortgeschrieben | DEC-104 N1 (1); FENSTERREGISTER Nachtrag | V/Klarstellung, O | sofort |
| VR-d19 | **Vorbelastung W1/W2.** W1/W2 gelten fuer die gesamte fm8-Reversal-Familie (nicht nur rev1 in W2) als vorbelastet durch die Persistenz-Null; eine Registrierung dort traegt das C.17-Etikett und rechnet in derselben BY-Kohorte wie jede andere Statistik der Renditefamilie; ein PASS von rev1 auf W2 waere nicht konfirmatorisch, ein DROP bliebe aussagekraeftig | DEC-104 N1 (5); DEC-102 N1 (7); GL-036 (4) | V (Strenge), O | sofort |
| VR-d20 | **Funding-Lage auf W1/W2.** Die formationsseitig gesehene Funding-Lage (O-030) gilt als Verbrauch der Funding-Lage-Statistik auf W1/W2, nicht als Verbrauch von Preis-Outcomes | DEC-104 N1 (8) | V, O | sofort |

### 2e. Designwahl, REZENZ, A2-Regeln

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-e01 | **Nuisance-adaptive Designwahl.** Jede Registrierung traegt ein registriertes Design-Menue (Fensterlaenge aus {6, 9, 12} Monaten bzw. Blickzahl, Placebosatz, Neutralisierung, Universum) und eine mechanische Auswahlregel, die nur Vorperioden-Nuisance und SESOI/Prior-Verteilung liest; der Orchestrator fuehrt die Auswahl autonom aus, ohne Nutzerfrage. Ausnahmen, ausdruecklich: (i) A2-Schwelle (DEC-103 E4 bindet die Schwellen-SE an das Maximum aus Vorperiode und Null-Simulation; die Nuisance-Lesart ist vor der ersten A2-Zahl mit Prior zu fixieren und zu etikettieren); (ii) Vorwissen der Agenten (VR-d16); (iii) Programmebene (mehr testbare Designs = mehr Tests je Jahr; abgefangen durch VR-d14). C.17 bleibt | DEC-104 E5 | L (Testbarkeit), alpha je Test neutral, N | ab K1 |
| VR-e02 | **REZENZ doppelt.** Als Screen in der Entscheidungsregel (VR-b14) und als registrierter Stabilitaetstest (Bericht: Differenz juengstes Fenster gegen aeltere, mit CI); C.18/DEC-99 (1) sind damit erfuellt. Stabilitaetstest als Gate statt Screen = Variante P-2 (c), vorgeschlagen | DEC-104 E6; DEC-104 N2 (4) | L, N | ab K1 |
| VR-e03 | **Nuisance-Symmetrie.** Bindend fuer SE und Schwelle ist das juengste Vorfenster (12 Monate vor dem ersten Urteilsfenster); aeltere Vorfenster (einschliesslich Stress 2021/22) nur als Sensitivitaets-/Stress-Zeile; fuer A2 eine Lockerung des effektiven alpha Richtung Nominalwert gegenueber DEC-103 N1 (8c) "Stress bindend" | DEC-104 E6 | L, N | ab K1; Konflikt mit VR-b10 -> **WD-02**; A2 -> **WD-03** |
| VR-e04 | **Konjunktionen gleichrangiger Bedingungen** (Placebosatz): MDE80 je Bedingung nach VR-b08 ("max ueber Bedingungen"); Regime-Zuordnung bis K1 ueber das Produkt der Einzel-Powers (konservative Untergrenze), exakte gemeinsame Power als Bericht; ab K1 traegt die Zuordnung die exakte gemeinsame Power (Monte Carlo mit geteiltem Ereignis-Term; A2-Akte: MDE80 22,93 / 23,77 bp W1 / W2 zentral statt Produkt 23,43 / 24,36); Doppelausweis der exakten Konjunktion neben dem Produkt in jeder A2-Zahl ab sofort | DEC-98 N7 (4a); DEC-104 E7 (a); DEC-105 (7) | N7 (4a): V (Strenge), O; E7 (a): L (Testbarkeit, Artefaktanteil 0,5..0,6 bp), N; Doppelausweis: n, O | bis K1 / ab K1 / sofort |
| VR-e05 | **Assurance-Uebergabe.** Pilot-Uebergabe, wenn die praediktive Power der Konfirmation unter der selektionsbereinigten Prior-Verteilung aus dem Pilot >= 0,5 ist, statt "Pilotpunkt >= MDE80"; nicht uebergebene Varianten zaehlen im Selektions-K der Pilotstufe (VR-d04) | DEC-104 E7 (b) | L (Testbarkeit, alpha neutral), N | ab K1 |
| VR-e06 | **Skalierte Null.** Der Test skaliert seine Null: `k = max(1, Ist-Streuung / eingefrorene Null-Streuung)` (Klasse W: reale Wochen-SD der Serie gegen eingefrorene Null-Wochen-SD; A2: SE_Lauf / Null-SD), `q95_eff = max(0, m) + k x (q95 - m)`, p aus den entsprechend transformierten Replikaten, keine Gutschrift fuer negative Null-Mittel; Pflicht fuer jeden Test der Klasse W (die Ein-Faktor-Null unterschaetzt die reale Streuung um 2,3..2,6x) und fuer A2 | DEC-101 E2; DEC-101 Teil 3 (Nebenbefund); DEC-103 N1 (8b); DEC-104 E7 (c) | V (Strenge), O/N | sofort |
| VR-e07 | **A2-Festlegungen unter 3.1.** Null-Faktor im Produkt: aufgehoben durch VR-e04 (ab K1); skalierte Null: bleibt (VR-e06); Stress bindend: wird nach VR-e03 Sensitivitaetszeile, **ausser** die OC zeigt fuer A2 ein effektives alpha > 0,0025 unter Stress-Nuisance, dann bleibt Stress bindend (Nachtrag); Gate-(4)-Faktor 0,9025: bleibt, bis das Negativ-Panel vorliegt oder aus `bybit/publicTrade` abgeleitet ist; Pilot-Regel R0 und PK-Kriterium (Injektionsziel MDE80prod im bindenden Fenster; Kriterium erwartete PASS-Quote minus 2,3263 x Binomial-SE bei 200 Seeds; Gate (4) in der PK-Kette): bleiben | DEC-104 E7 (c); DEC-103 N1 (8a)-(8f) | gemischt (je Zeile), N | ab K1; Stress-Zeile -> **WD-03** |
| VR-e08 | **A2-Weg.** Feasibility unter 3.1 (VR-b14 gepoolt + Screen auf W1/W2 als Zone-V-Blick, exakte Konjunktion, MDE80 gegen Taker-SESOI 22 bp) rechnet der Orchestrator nach Vorlage der OC; ist MDE80 <= SESOI, folgt die Zustandsmaschine (Herleitungs-Nachtrag, Review, Registrierung, Positivkontrolle, Lauf) ohne weitere Nutzerfrage; sonst GL-012 "strukturell nicht testbar" mit Ausschlussgrenze; bis dahin kein A2-Code-Bau (P-0) | DEC-104 E7 (d) | Testbarkeit, N | sofort (OC liegt vor); Ergebnis haengt an P-2 (4.2) |
| VR-e09 | **A2-Ereignismenge.** Alle Freitage mit Deribit-Optionsverfall 08:00 UTC (Woche, Monat, Quartal; 52 je 12-Monats-Fenster), Klassenregel nach DEC-98 N5 (3) ergaenzt um den Futures-Kalender; Tage mit Options-Delivery > 60 s nach 08:00:00 aus Ereignis- und Placebo-Mengen ausgeschlossen (bis 2026-06-30: 2020-08-27, 2024-08-19); jeder registrierbare A2-Kontrast ist ein Groessen-Kontrast (OI-Proportionalitaet UNBELEGT, Faktor 0,84..0,92 nur Etikett) | DEC-103 E1 | n (Praezisierung, Strenge), N | sofort (Design); Registrierung siehe 4.2 |
| VR-e10 | **A2-Statistik.** `Delta = Mittel r_pre(Ereignis) - Mittel r_pre(P2'')`, `r_pre = ln(C[07:59]/C[07:29])` auf Bybit-1-min-Kerzen (deckt den TWAP [07:30, 08:00) exakt), Cluster = Kalendertag, `x = (r_BTC + r_ETH)/2`; `r_post` nur Bericht; Richtung des Kontrasts negativ aus der Literatur [sek], bindend erst mit einer Registrierung | DEC-103 E2; DEC-58 E4 | n, N | sofort (Design); Richtungsvorbedingung -> **WD-10** |
| VR-e11 | **A2-Placebosatz** (ersetzt P1/P2/P3 aus PRD 5.2): P2'' Mo-Do-Slots [07:30, 08:00) ohne Tage mit Futures-Delivery in mindestens einer Waehrung (W1 208, W2 159 Tage) - bindender Einzel-Placebo; P3fix Slot [15:30, 16:00) aller Tage ohne Monatsend-Freitage; P3all uebrige Halbstunden-Slots als Baseline; Wochenende in keiner Menge; Groesse des Satzes fixiert (drei Placebos), jede Aenderung ist eine Gabelung mit Etikett. Befund: P3fix ist die bindende Einzelbedingung (SE 7,93 > P2'' 7,34 / 7,58; Einzel-MDE80 19,7 / 19,7 bp) | DEC-103 E3; DEC-103 N1 (4) | n (Strenge), N | sofort (Design) |
| VR-e12 | **A2-Null und Schwelle.** Label-Permutation Freitag <-> Mo-Do innerhalb derselben ISO-Woche (J-(i)), >= 1.000 Replikate, fester Seed; Schwelle `max(oberes 95-%-Quantil der Null; z_krit x SE)`; bindende SE nach DEC-94 (5) die groessere aus Vorperiode und Null-Simulation (P2'' 7,34 / 7,58 bp bestaetigt); Etikett "Null neu definiert nach DEC-98 N5"; Grenze offengelegt: ein reiner Wochentagseffekt erscheint als Effekt; Gabelung F-1 (J-(i) woertlich, 12 nicht permutierbare W2-Wochen bleiben fest) | DEC-103 E4; DEC-103 N1 (3), (5) | n (Strenge), N/O | sofort (Design); SE-Bindung ab K1 -> **WD-02** |
| VR-e13 | **A2-Negativ-Panel (Gate (4)).** XRP/BNB beta-residualisiert (`r_sym - beta x r_BTC`, beta aus der Vorperiode, vorab fixiert); Bedingung "nicht ueber max(q95 eigene J-(i)-Null; z_krit x SE_sym) in registrierter Richtung", als Faktor in P_W mit angenommener Power 0,95 je Symbol (UNBELEGT bis zu Negativ-Panel-Daten) | DEC-103 E5; DEC-103 N1 (8f) | n, N/O | sofort (Design); Daten: Datenannahmen Nr. 5 |
| VR-e14 | **Fremde Referenzfenster.** CME-Referenzraten aus Trades 15:00-16:00 London [sek]; P3fix ohne Monatsend-Freitage; kein gepaarter 15:30-Slot; je nach GMT/BST liegen die CME-Slots in [15:00, 16:00) bzw. [14:00, 15:00) UTC und gehoeren an Monatsend-Freitagen in die Kontaminationsliste von P3all | DEC-103 E6 | n, N | sofort (Design) |
| VR-e15 | **A2-Fenster und Nuisance.** W1/W2 nach VR-d01 (blind fuer A2; Siegel unberuehrt); Vorperiode 2021-03-24..2024-05-31 nur als Nuisance-Quelle (Klassen-SD, c_bind, Null-Simulation); Schutzregel G-C8: Tage ohne 08:00-Funding in einem Symbol oder mit Termin in [07:30, 08:00) aus beiden Mengen (W2: 0 Tage; BTC/ETH an allen Tagen 3 Termine 00/08/16 UTC); Stress-Kalibrierung (2021-06..2022-05) mitregistriert, Bindung siehe VR-e07 | DEC-103 E7; DEC-103 N1 (7), (8c) | n, N/O | sofort (Design) |

### 2f. Berichts- und Pruefpflichten

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-f01 | **Messinstitution.** Jeder Lauf - auch ein GL-012, ein Zensus mit Outcome-Beruehrung und jede Zone-X-Abfrage - gibt Schaetzer, 95-%-Konfidenzintervall, obere einseitige Ausschlussgrenze (95 %) und einen Shrinkage-Hinweis aus (Ergaenzung der Artefaktpflicht DEC-53). Verdikte (PASS/DROP) bleiben konfirmatorisch und setzen Vorregistrierung voraus. **Spiegelklausel** zur Null-Zensus-Klausel: aus einer Ausschlussgrenze allein folgt keine Demotion und kein Verdikt, nur ein Feasibility-Befund | DEC-104 E1 | V (Berichtspflicht), neutral in alpha, O | sofort |
| VR-f02 | **Pflicht-Berichtszeile, Format.** Jedes Ergebnis-Artefakt (DEC-53-JSON) und jede GL-/DEC-Ergebniszeile fuehrt `estimate` (registrierte Einheit), `se`, `ci95` [low, high] (zweiseitig), `upper_limit95` (`estimate + 1,6449 se` bzw. Bootstrap-Quantil), `n_eff` (Cluster), `c_overlap`, `selection_k`, `shrinkage_note` (Herkunft des Schaetzers, bedingt median-unverzerrter Wert falls aus Screen/Pilot), `zone` (X/V/K); Textform "Effekt = x [CI95 a; b]; Effekt < u (95 %, einseitig); n_eff; K; Zone". Bestehende Artefakte werden nicht nachgerechnet | DEC-105 (Pflicht-Berichtszeile) | n, O | sofort fuer alle neuen Laeufe, Zensen mit Outcome-Beruehrung, Zone-X-Abfragen |
| VR-f03 | **Ergebnis-Artefakt-Pflicht.** Jeder Treiber schreibt neben dem Summary (a) die urteilstragende Serie auf Cluster-Ebene (je Kalendertag/Woche/Ereignis gemaess VR-b03) als Parquet/CSV mit SHA-256 und (b) die Bootstrap-Replikate des Gate-Schaetzers (mindestens 1.000 Ziehungen) oder Seed plus Generator-Fingerprint, aus dem sie bit-identisch reproduzierbar sind. **Ein Lauf ohne (a)+(b) ist KEIN VERDIKT** (loud fail im Treiber, Test gepinnt; T7) | DEC-53; PRD 3.3.11 | n, Bestand, O | sofort |
| VR-f04 | **OC-Zeile** je Registrierung: P(PASS bei Effekt 0), P(PASS bei SESOI), P(PASS bei Prior-Median) der gesamten Entscheidungsregel einschliesslich Screen und Blicken (Simulation >= 1.000 Seeds als T0) | DEC-104 E8 (a) | V, O | sofort |
| VR-f05 | **Strenge-Quotient** MDE80(alle Festlegungen) / MDE80(Grundfassung) als Pflichtzeile; ab 1,3 Nutzer-Vorlage vor der Registrierung. Praezisierung der Grundfassung (Primaerstatistik allein, zentrale Nuisance, dieselbe Entscheidungsregel und dasselbe alpha; Datenfaktor = Quotient^2) ist ein Vorschlag der OC (g) [U] | DEC-104 E8 (b); OC (g) | V, O; Definition: vorgeschlagen, O | sofort |
| VR-f06 | **Review-Mandat symmetrisch.** Jeder adversarische Review beantwortet die Pflichtfrage "Ist der Test gegen SESOI/Prior nach allen Auflagen noch sensitiv (Power >= 0,80)?"; Schleifen-Obergrenze zwei Fassungen je Herleitung, danach Nutzer-Vorlage mit beiden Fassungen | DEC-104 E8 (c) | V, O | sofort |
| VR-f07 | **Erreichbarkeitspruefung** je Design-Parameter: jede registrierte Schwelle, Clusterzahl oder Stress-Zelle weist aus, wie viele Beobachtungen sie in den Urteilsfenstern tatsaechlich erreicht; das Etikett "Design-Parameter (keine Schwelle)" ersetzt diese Pruefung nicht | DEC-104 E8 (d); Kritik K-14 (d), (i) | V, O | sofort |
| VR-f08 | **Inferenz bei schweren Raendern und kleinen Clusterzahlen.** t-artige Grenzen (Freiheitsgrade aus der Clusterzahl, df_eff nach Kurtosis) fuer jeden Test mit geschaetzter SE; Blocklaenge des Bootstraps aus der gemessenen Autokorrelation statt fest (VR-b09); c >= 1 Pflicht bei Ueberlappung (VR-b05); Permutationstests unter Austauschbarkeit bevorzugt, wo moeglich. Anlass [R]: Normal-Grenzen bei 40..52 Clustern GSD-alpha 0,0044 statt 0,0025; Schiefe gegen die Testrichtung 0,0114; AR(1) 0,3 mit Blocklaenge 4 0,0140 | DEC-104 N2 (7) | V, O | sofort |
| VR-f09 | **Fallzahlplanung nur gegen SESOI.** Die MDE einer Registrierung wird ausschliesslich gegen die SESOI geplant (VR-c01); Zone-X-Schaetzer bestimmen Richtung und Etikett, nie die Fallzahl; alpha der Konfirmation bleibt 0,0025 (disjunkte Daten). Anlass [R]: Planung am rohen X-Gewinner liefert Konfirmations-Power 0,09..0,72 statt 0,80, bedingt median-unverzerrt 0,35..0,74 | DEC-104 N2 (6) | V, O | sofort; Verhaeltnis zu VR-c06 -> **WD-09** |
| VR-f10 | **Null-Zensus-Klausel.** Ein Nulleffekt- oder Erreichbarkeits-Zensus darf niemals einen Kandidaten promoten; zulaessige Ausgaenge sind ein D-Eintrag oder "nicht ausgeschlossen"; jede Registrierung, die aus einem Zensus hervorgeht, braucht eine eigene, vorab formulierte Hypothese mit eigenem K | DEC-58 E2; PRD 11.1 | n, Bestand, O | sofort |
| VR-f11 | **Pseudo-Null-Vergleichszeile.** Jede deskriptive Messung braucht neben Positiv/Null/Adversarial die Pseudo-Null-Vergleichszeile in der Hauptausgabe (real vs. gematchte Null nebeneinander, nicht nur als Varianzverhaeltnis) | DEC-60 ("Lehre, aufgenommen in die Verfassung") | V, O | sofort |
| VR-f12 | **Positivkontrolle.** Bei jeder Maschinerie mit > 1 h Laufzeit laeuft die Positivkontrolle zuerst und allein; ihr PASS ist Vorbedingung der Einplanung. Praxis seit DEC-89 E2 und DEC-101 E8: Produktionskonfiguration mit der registrierten YAML, realer Fensterform, kalibrierter Null-Welt des registrierten Tests und kompletter Gate-Kette einschliesslich skalierter Null (VR-e06); NICHT BESTANDEN, wenn die SD der Kontrollwelt mehr als 10 % ueber der SD der Power-Zeile liegt (VR-b10); scheitert sie, kein Lauf, Ursachenanalyse, neue DEC | PRD 3.3.8; DEC-89 E2 (+ Nachtrag); DEC-94 (5); DEC-101 E8 (a) | n, O | sofort; allgemeine Pflicht der Produktionskonfiguration nur als Praxis belegt (Abschnitt 5.5) |
| VR-f13 | **Praemie statt Sharpe (Klasse P).** Urteilstragend `mean(prem)`; Sharpe, MaxDD und Tail-Ratio werden berichtet, nie geurteilt, jeweils mit hergeleitetem Rauschboden; `SR_block >= 0,60` und `TR <= 250 Tage` sind Deskriptoren; MaxDD-Boden `E[MaxDD] = 1,2533 sigma_ann sqrt(T)`; Ruin-Kapital `u(eps) = (sigma^2/2mu) ln(1/eps)` als zweite Berichtszeile. Auflagen woertlich: (1) jeder P-A-PASS traegt im PASS-Text "Praemien-EXISTENZ; die risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER"; (2) kein Kapitalschritt folgt aus einem P-A-PASS; (3) die Beobachtungszahl wird nicht ueberzeichnet; (4) fuer das Risiko ist das effektive N die Zahl der Stress-Episoden | PRD 3.6; DEC-58 E1 (e); PRD 11.4 | n, Bestand | sofort; Auflage (1) gegen L-12 -> **WD-12**, P-10 |

### 2g. Daten-, Siegel- und Kostenmodell-Regeln

**VR-g01 Oeffentliches Repository, Zugangsdaten, Harvest-Baum, Siegeldateien** (Herkunft: `CLAUDE.md` Repo-Wurzel,
"Harte Regeln"; n, Bestand; sofort). Woertlich:
> - Das Repository ist oeffentlich: nie Zugangsdaten, nie den Hostnamen des Heim-Datendienstes ins Repo, in Commits oder Logs.
> - Zugangsdaten nur aus Umgebungs-Secrets (`HARVEST_S3_*`), nie aus Chat oder hochgeladenen Dateien.
> - Nie unter `data/harvest` schreiben. Kein Live-Order-Code.
> - Versiegelte Dateien unter `scinance3-impl/state/runs/` (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`) nicht oeffnen.

Ergaenzend woertlich: "**Siegel:** Die reale Signal-gegen-Folgerendite-IC der A3-Kohorte ist bis zum registrierten Lauf
versiegelt. Nie oeffnen: `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`, `*_L_window_sealed.json` (alle unter
`state/runs/`)." (UEBERGABE_2026-10-09 Abschn. 1). "Zugangsdaten ausschliesslich ueber Umgebungs-Secrets `HARVEST_S3_*`;
nie aus Chat/Upload uebernehmen, nie Schluessel oder Hostname ins (oeffentliche) Repo." (DEC-80 E1). "Die Cloud liest nur
exakte Schluessel, prueft Groesse/SHA256, entpackt nie unter `data/harvest`." (DEC-83 E2). "Backfills schreiben NIE in den
Harvest-Baum (Schutzgut, read-only, CLI-Guard)." (PRD 4.2).

**VR-g02 Marktdaten ueber den Data-Harvest-Client** (Herkunft: `scinance3-impl/CLAUDE.md` Abschnitt "Marktdaten"; DEC-80
E1; n, Bestand; sofort). Woertlich:
> Rohdaten aus dem Data-Harvest-Archiv kommen ausschliesslich ueber dessen Client `harvest_data.py` (Bezug und Regeln:
> `UEBERGABE_2026-10-09.md` Abschnitt 4): `hd.configure()` -> `hd.catalog()` / `hd.load(stream, symbols, start, end, exchange=...)`.
> - Zugangsdaten nur aus den Umgebungs-Secrets `HARVEST_S3_ENDPOINT`, `HARVEST_S3_ACCESS_KEY`, `HARVEST_S3_SECRET_KEY`; nie aus Chat oder Datei, nie ins Repo, nie der Hostname ins (oeffentliche) Repo.
> - Der Thin Client serviert nur; gerechnet wird in der Sandbox (CPU) oder auf dem Nutzer-PC (Autopilot, DEC-79), nie auf dem Thin Client.
> - Nie den Bucket listen oder globben; was existiert, steht in `hd.catalog()`.
> - Endpunkt ~2 MB/s, geteilt: Zeitraeume klein, `columns=` nutzen; grosse Orderbuch-Laeufe auf dem Nutzer-PC.
> - Fehlende Tage (`hd.gaps`) nie interpolieren oder still auslassen - benennen.
> - Bekannte Besonderheiten: 2026-08-13 Bybit-Live-Stroeme doppelt (Client dedupliziert), 2026-08-14 Ausfalltag, Bybit-WS-Feldnamen ohne "1".

Daten aus dem Archiv nur in die Sitzung, nie ins Repo ("Panel-Kopie nur in der Sitzung, nie im Repo", DEC-84;
"Daten nur ueber `hd.load` in die Sitzung, nie ins Repo", DEC-95).

**VR-g03 Schutzgueter** (Herkunft: `scinance3-impl/CLAUDE.md` "Schutzgueter"; n, Bestand; sofort). Woertlich:
> - Data-Harvest-Baum `data/harvest` read-only; nie hineinschreiben, nie cachen. Manifest-Wahrheit ist `harvest_manifest.backup.sqlite` (`bar_cache.resolve_manifest_path`).
> - Recorder C-36 (`src/bybit_edge/recorder/`, Scheduled Task) laeuft weiter, bis die Sunset-Review (PRD Par. 8.3) entschieden ist.
> - Test-Suite (1.495 Tests, Baseline in `survey/BASELINE_TESTS.txt`) wird erweitert, nie reduziert; die vier Forensik-Tests bleiben byteidentisch; `_legacy_v1/` wird nicht importiert ausser von seinen eigenen Tests.
> - Lokale Kopplungen (drei Scheduled Tasks, Junction, `start.bat`, `scinance2-impl/handoff_local/*`): Pfade nie verschieben ohne Stub.

**VR-g04 Blind-Siegel** (Herkunft: DEC-96 E3; DEC-97 "Blind-Siegel bleibt bestehen"; DEC-98 E1 (b); DEC-104 E4 (a),
E10; n/V, O; sofort; Zone K nach VR-d08). Woertlich (DEC-96 E3):
> **Entscheidung 3 - Blind-Siegel (programmweit, bis zum registrierten H-27-Lauf):** Keine Niveau-, Streuungs- oder
> Verteilungsstatistik von DVOL (BTC/ETH) und keine realisierte Volatilitaet bzw. Renditestreuung von BTC oder ETH auf
> Tagen ab 2026-07-01 - auch nicht als Nebenprodukt anderer Pakete (z. B. Marktfaktor-SD in Zensus- oder Vorlauf-Laeufen:
> Panel dort bei 2026-06-30 abschneiden). Erlaubt: Vollstaendigkeitspruefungen (Zeilen je Tag, Luecken, Zeitstempel,
> Schema). Bekannt und offengelegt: Datum des STRESS_ABS-Tags 2026-08-19 (Kanon); ungeoeffnete Dateien mit Werten bis
> 2026-07-31 (WP-10(A2)) bzw. 2026-08-13 bleiben ungeoeffnet.

Reichweite: "die Fenster ab 2026-07-01 bleiben fuer jede kuenftige, neu vorab registrierte VRP-Hypothese blind" (DEC-97);
"Blind-Siegel DEC-96 E3 erfasst auch A3/A1-Fenster ab 2026-07-01" (DEC-98 E1 (b)); DEC-104 E4 (i) erweitert auf Funding
BTC/ETH; vor DEC-104 liegende Oeffnungen sind durch VR-d08 abgegolten (DEC-104 N1 (4)); Zone K versiegelt "fuer alle
Statistiken ausser Zaehlungen (S0)" (DEC-104 E4 (a)).

**VR-g05 Kanalverbot und Ausgaberegel fuer Nuisance-Dateien** (Herkunft: DEC-103 N1 (1), (2b), (2c); V (Strenge), O;
sofort). Woertlich (DEC-103 N1 (2)):
> (b) **Verbot** fuer alle Agenten und den Orchestrator, Klassen-Streuungen geschachtelter Klassen zu kombinieren oder
> Lage-Differenzen aus Nuisance-Ausgaben abzuleiten (Abweisungsliste kuenftiger Herleitungen und Reviews); (c)
> Ausgaberegel fuer alle kuenftigen Nuisance-Dateien: Streuungen nur fuer eine Partition disjunkter Klassen in voller
> Praezision, nie Elternklasse und Teilklassen zusammen, keine Vereinigungs-Streuung; Pruefpunkt jedes Reviews
> (Struktur-Scan `channel_scan.py`-Logik);

Dazu Regel R-C12 woertlich: "keine Streuung einer Vereinigung zweier ausgegebener Klassen derselben Werte und keine Groesse,
aus der sie mit Kalenderwissen folgt" (DEC-103 N1 (1)). Werkzeug: `tools/channel_scan.py` (F0b, UEBERGABE_2026-10-12
Abschn. 15). Praxis ohne DEC: Hygiene-Scan auf Hostnamen/Modellnamen vor jedem Commit analytischer Dateien
(PRD_ANALYSE 4.17, Anhang C B-21). KONTO_ZONE_X-Kopf woertlich: "Oeffentliches Repo: keine Hostnamen, keine
Zugangsdaten, keine Marktniveaus; Nuisance-Ausgaben nach DEC-103 N1 (2c)."

**VR-g06 A2-Vorperiode** (Herkunft: DEC-104 N1 (11); V (Strenge), O; sofort). Woertlich:
> (11) **A2-Vorperiode (W-19):** in Zone X frei fuer Nicht-A2-Statistiken; fuer A2 selbst Nuisance-Quelle unter
> Disziplin (B-2-Kanal): kein Mittel und kein Vorzeichen von r_pre-Kontrasten darf dort gebildet werden, auch nicht als
> Konto-Abfrage (Verbot, Strenge); eine etwaige Pilot-Route (DEC-103) bleibt Vorlage.

Hintergrund: Die committete `a2_vorarbeit.json` (Teil B Fassung 2) fuehrt geschachtelte Klassen; die Blindheit der
Vorperiode fuer A2 ist "seither durch Disziplin, nicht durch die Daten geschuetzt"; kein History-Rewrite (DEC-103 N1 (2), (2a)).

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-g07 | **Lesestatus.** "Berechnet, versiegelt, ungelesen" ist von "nie berechnet" zu unterscheiden; das Fensterregister fuehrt den Status je Datei (Abschnitt 7), jede Registrierung dokumentiert ihn | DEC-104 N1 (6); FENSTERREGISTER Abschn. 7 | V/Klarstellung, O | sofort |
| VR-g08 | **Kein Live-Order-Code.** Woertlich: "**Kein Live-Order-Code.** Keine Keys, keine privaten Endpunkte, keine Orders. Oeffentliche Endpunkte (Bybit v5, Deribit public) frei nutzbar." Der Preis wird benannt (Fill-Wahrscheinlichkeiten nie direkt messbar; Mittelweg kapitalfreie Quote-Schatten-Messung); die Ausfuehrungs-Spur ist Phase 4 und bleibt bis zur ausdruecklichen Freigabe leer; Entscheidungsrelevanz-Zeilen nennen nur den naechsten Mess- oder Tradability-Schritt | CLAUDE.md Autonomie 4; PRD 3.8; PRD 8.1 Default (b); DEC-73 E5; DEC-104 E10 | n, Bestand | sofort |
| VR-g09 | **Rechenort.** Cloud-first: gerechnet wird in der Cloud-Sitzung, Daten vom Thin Client; der Autopilot (DEC-79) bleibt nur Rueckfall; dort ein einziger Befehl je Runde, Ergebnisse vom Skript committet. Bybit-REST ist aus der Cloud geo-gesperrt (Fakt) | DEC-83 E1; DEC-79; DEC-76 Nachtrag (Nutzer-Auflage); DEC-81 E3 | n, N (Nutzer-Auflagen) | sofort |
| VR-g10 | **PIT-Universum und Survivorship.** Ein Symbol ist in Woche t im Universum, wenn es zu Wochenbeginn >= 8 Wochen Bars hat (Design-Parameter, keine Schwelle; Sensitivitaet 4/12 Wochen nur Bericht) und in Woche t noch handelt; ein delistetes Symbol wird nicht rueckwirkend entfernt, sondern bis zum letzten Bar gehalten und zum letzten Schlusskurs geschlossen; Ende der PIT-Maske = `last_trading_day` aus `bybit/delisting_dates` (Data-Harvest), Ankuendigungsdatum nur Etikett; `Relisted`-Symbole bleiben Ueberlebende; wiedergelistete/frisch delistete Symbole nach DEC-72 Formen b/c; Ueberlebenden-Baum und Register muessen vor jedem Union-Zensus dasselbe Stichdatum haben | PRD 4.1 DoD (4); DEC-100 E1, N1 (2); DEC-72 (+ Nachtraege) | n, O | sofort; 8-Wochen-Regel: Ersatz durch IK-07 vorgeschlagen (Sweep 3.0) |
| VR-g11 | **Manifest und Vollstaendigkeit.** DONE verlangt `n_rows == expected_days`, Loud-Fail bei Abweichung; "PARTIAL = Abbruch" wird nicht gelockert (Ausnahme nur bei dokumentierten Quellenluecken ohne `failure_reason` und mit reproduzierter Zeilenzahl, DEC-66); ein Tag gilt als geschlossen bei Manifest-DONE oder `_compacted.parquet` (DEC-68); identische Frames werden vor dem Replay dedupliziert, Duplikatzahl berichtet (DEC-76 E3); `discarded`/`not_manifest_done`-Partitionen sind nie resume-final | PRD 4.1; DEC-66 (3); DEC-68; DEC-76 E3 | n, O | sofort |
| VR-g12 | **Provenienz und Quellenreinheit.** Fuer jeden eigenen REST-Backfill-Speicher monatlich eine 1-%-Zufallsstichprobe eingefrorener Partitionen neu ziehen und gegen die Fingerprints pruefen; Abweichung ist ein lautes Alarm-Ereignis; Quellen einer Reihe werden nicht gemischt (DVOL: durchgehend eine Quelle) | PRD 7.1 (Provenienz-Regel); DEC-61; DEC-95 E1 | n, Bestand | sofort; fuer Data-Harvest-Stroeme gilt der monatliche Stromcheck (PRD_ANALYSE 9.2 Nr. 10; UEBERGABE_2026-10-12 Abschn. 15) |
| VR-g13 | **Stress-Kanon.** `STRESS_REL` (DEC-55): alle UTC-Tage mit Tagesvol (BTC oder ETH) ueber dem 97,5-Perzentil der juengsten 24 Monate plus 2026-08-19, Episoden bei hoechstens einem Nicht-Stress-Tag Luecke; Abdeckungs-Nachweis, nie Filter oder Gate. `STRESS_ABS` (DEC-56): 99-Perzentil der gesamten WP-0-Historie plus 2025-10-10 und 2026-08-19; Stress-Definition fuer Praemien-Kohaerenz und jede Liquiditaets-/Fill-Frage. Alle Parameter sind Design-Parameter (kein Gate, nicht variierbar); Fixture mit SHA-256, monatlich append-only; Ergaenzungen der Namensliste und abweichende Stress-Definitionen nur per neuer DEC vor dem Lauf | DEC-55; DEC-56; PRD 3.3.10 | n, Bestand | sofort; Erreichbarkeit nach VR-f07 (W1 2 / W2 1 STRESS_ABS-Tage, DEC-74 N (1)) -> **WD-13** |
| VR-g14 | **Kostenmodell `tradability3`.** Mess-Artefakt, kein Parametersatz: jede Konstante gemessen und eingefroren, oder zweiseitige Pflicht-Sensitivitaet, oder harter Abbruch; stille Defaults verboten; gebaut werden nur `constants.py` und `report.py`, uebrige Module RAISE-Stubs bis zur Messung; jede Konstanten-Ersetzung ist eine eigene DEC, bevor ein Kandidat davon profitiert; `constants_hash` im Ergebnis, abweichender Hash = kein gueltiger Lauf (T5); Impact nur bei k=0 UND k=1 berichtet. RAISE derzeit: `perp` fuer Umsatz-Dezile >= 3 (Snapshot-Spread > 4 bp), Altcoin-Maker bis zur Gebuehren-Primaerpruefung, Maker-Annahmen im Stress bis zu einer Messung mit >= 10 Stress-Tagen, Halte-bis-Verfall- und Settlement-Pfade bis V-4 | PRD 6; PRD 3.3.6; DEC-67 E4; DEC-58 E5; DEC-71 E2; PRD 4.4 V-4 | n, Bestand | sofort; Werkzeug-DEC unbeschlossen -> **WD-08** |
| VR-g15 | **Datenannahmen-Register** `state/DATENANNAHMEN_REGISTER.md` wird bei jedem Katalog-Refresh und jeder Data-Harvest-Antwort fortgeschrieben (datierte Zeilen, append-only) | DEC-105 | n, O | sofort |

### 2h. Automation, Rollen, Ablauf

| Nr | Regel | Herkunft | Etikett | Geltung |
|---|---|---|---|---|
| VR-h01 | **Autonomie-Protokoll.** Das PRD ist die Verfassung; kein Lauf ohne registrierten Eintrag; Urteil nur gegen das registrierte Gate; der Gate-Auditor hat Veto. Bestehende Repo-Konventionen schlagen Praeferenz; bei Stille entscheidet der Orchestrator fuer die reversibelste Option und protokolliert eine DEC. Den Nutzer nie fragen, ausser: fehlende Zugriffsrechte/Secrets, Aktionen mit Geldeinsatz, destruktive Operationen auf bestehenden Daten; offene Nutzer-Entscheidungen (PRD Par. 8) werden mit dokumentiertem Default weiterbearbeitet, nie still entschieden | CLAUDE.md Autonomie 1-3 | n, Bestand | sofort; Verhaeltnis zu den Nutzer-Vorlagen aus VR-d14, VR-f05, VR-f06 -> **WD-15** |
| VR-h02 | **Rollen.** Orchestrator: Entscheidungen, Registrierungstexte, Gate-Urteile, DEC-Eintraege, Verfassung. Herleitung: Gate-Design, Rauschboden-/Power-Herleitungen, PRD-Text; danach adversarischer Review durch eine zweite, unabhaengige Herleitungsrolle (Review). Bau: Zensus/Backfill/Treiber nach Spezifikation mit Test-Abnahme (T1, T2, T7). Kartierung: Inventur, Dokumentpflege, Listen. Der Orchestrator als Subagent nur bei einem Widerspruch zwischen Herleitung und Review, den er nicht selbst entscheiden kann. Subagenten schreiben Volltexte in Dateien, an den Orchestrator gehen Kurzfassungen (<= 10 Zeilen); jede Abnahme (Tests, Fingerprints, Diff-Grenzen) vollzieht der Orchestrator selbst nach, nie auf Zuruf. Modellzuordnung je Rolle: in PRD 3.9 und CLAUDE.md mit Modellbezeichnungen gefuehrt; Ersetzung durch Rollen vorgemerkt | PRD 3.9; CLAUDE.md "Modell- und Teampolitik"; UEBERGABE_2026-10-09 Abschn. 1; DEC-105 "Vorgemerkt" | n; Rollenfassung: vorgeschlagen, N | sofort (Rollen); Modellbezeichnungen: Entscheid N offen |
| VR-h03 | **Registrierung nur durch den Orchestrator**, nach Herleitung und Review; kein Agent registriert eine Hypothese | PRD 3.9; CLAUDE.md Sequenz-Zwang | n, Bestand | sofort |
| VR-h04 | **Sequenz-Zwang.** Regelaenderungen nie kandidatenspezifisch; sie stehen VOR der Registrierung des ersten Kandidaten, der sie braucht; keine Regelabweichung nach Kenntnis der Konsequenz zugunsten eines Kandidaten (Praezedenz DEC-92 E2, DEC-93 E3); Zensus vor jedem Alpha-Slot | DEC-52 Sequenz-Zwang; CLAUDE.md; DEC-92 E2; DEC-93 E3 | n, Bestand | sofort |
| VR-h05 | **Selbstbindung bis zum Entscheid P-12.** Lockerungen nur mit Nutzer und ab naechster Kohorte; Verschaerfungen mit Strenge-Quotient-Ausweis; stehende Default-Politik je Fragetyp in der Entscheidungswarteschlange | DEC-104 "Offen" (P-12) | V (Protokoll), O | sofort bis Entscheid P-12 |
| VR-h06 | **GPU-Default 0.** GPU-Budget je Hypothese 0; ein GPU-Lauf braucht eine registrierte Begruendung, warum CPU nicht reicht, UND eine Entscheidungsrelevanz-Zeile mit Tradability-Pfad; die 24-h-Grenze ist Meldegrenze (vor dem Start melden und begruenden), keine Schwelle; wirksames Instrument ist die Positivkontroll-Vorschaltung | DEC-57; PRD 3.7 | n, Bestand | sofort |
| VR-h07 | **Fahrplan der Automation.** F0 Skripte ins Repo (erledigt: F0/F0b), F1 Ledger/Schema/Linter, F2 Fensterregister und Datenzugang (Konto, Zonen, Vorwissens-Klassen), F3 Feasibility-Rechner (verfuegbar), F4 Lauf-Rahmen, F5 Generator und Takt, F6 FDR-Buch, sequentielle Blicke, Lockbox; bis F2 fuehrt der Orchestrator Konto und Register von Hand; Lockerungen gelten erst ab K1, Verschaerfungen sofort | DEC-104 E9; UEBERGABE_2026-10-12 Abschn. 15; PRD_ANALYSE Nachtrag 3 | n, O | sofort (Fahrplan) |
| VR-h08 | **Arbeitsregeln.** Kontext-Hygiene: Dateipfade statt Volltexte; Git: kleine Commits je Schritt, nie force-push, nie History-Rewrite; Doku Deutsch (ASCII-safe), Code und Kommentare Englisch; keine Modellbezeichnungen in Repo-Artefakten | CLAUDE.md Arbeitsregeln 1-3; UEBERGABE_2026-10-09 Abschn. 1 | n, Bestand | sofort |

**VR-h09 Zustandsmaschine mit Zonen (Lesefassung, keine neue Regel).** Zusammengesetzt aus CLAUDE.md "Zustandsmaschine",
DEC-104 E1, E3 (a), E4 (c)-(e), E7 (d), E8 und DEC-89 E2; Herkunft je Schritt in Klammern; Geltung ab K1 fuer
Registrierungen, die Zone-X-Schritte sofort:

```
ZONE X: Exploration mit Konto, nie Verdikt (VR-d10)                     -- Nuisance, Kosten, Nullwelten, Richtung
  -> HERLEITUNG: SESOI-Kurve (VR-c01), Design-Menue + Auswahlregel (VR-e01), Feasibility-Rechner (VR-b12)
  -> FEASIBILITY-BEFUND: MDE80 <= SESOI ? weiter : GL-012 "strukturell nicht testbar" + Ausschlussgrenze (VR-c01, VR-f01)
  -> REVIEW: adversarisch, symmetrisches Mandat, hoechstens zwei Fassungen, sonst Nutzer-Vorlage (VR-f06)
  -> REGISTRIERUNG: nur Orchestrator, YAML + sha256, vor dem Kohorten-Stichtag (VR-h03, VR-d13, Abschnitt 3)
  -> [BAU -> VERIFY (T0-T7)]* -> POSITIVKONTROLLE allein und zuerst (VR-f12)
  -> BLICK(E): Zone V genau ein Blick / Zone K gruppensequentiell mit Screen und Futility (VR-d11, VR-d12)
  -> GATE_CHECK nur gegen das registrierte Gate -> GL-Eintrag mit Pflicht-Berichtszeile (VR-f02)
  -> Pflicht-Bestaetigung auf neuen Daten (VR-b15) -> getrennt registriertes Tradability-Gate (C.2)
```
Die alte Zeile "ZENSUS(WP-7,WP-9,WP-10,V-1..V-5) -> ... -> LAUF (Nutzer-PC, T3-Runner)" (CLAUDE.md) ist historisch
(Welle 1 abgeschlossen, DEC-73; Rechenort VR-g09).

### 2i. Programm-Konstanten (Verweis; Konstanten, keine Schwellen)

| Gruppe | Inhalt (Kurz) | Quelle | Status v3 |
|---|---|---|---|
| 2.0-Konstanten B.1..B.17 | Wand 11 bp Taker / ~15 bp inkl. Slippage; Perp-Spread ein Tick; Gebuehren Maker 2,0 / Taker 5,5 bp je Bein; Options-Gebuehren 2/3 bp des Index; vega/S 5,28/5,10; Quote-Breiten; Querschnitts-z-Deckel `sqrt(N-1)`; Redundanzschwelle Spearman 0,6 (Erreichbarkeit je Anwendung) | PRD 9.2 A; Kompendium B | gilt; B.16 ("publicTrade als Voraussetzung fuer Tage bis Wochen") inhaltlich ueberholt (Kritik K-13); Wand als Parametersatz mit Sensitivitaet vorgeschlagen (K-11) |
| R4 K-0.1..K-0.7 | Friktionskurve, Lo-Dauer, Selektionsdecke, MaxDD-Boden, IC-Rauschboden, Ein-Fenster-Kosten, GPU-Bilanz | PRD 9.2 B | K-0.1 -> VR-c02/VR-c03 (DEC-105 (1), (8)); K-0.2 Lo-Beispiel q 365 (DEC-105 (2)); K-0.5 "direkt gemessen" -> Identitaet (DEC-105 (5)); K-0.6 Faktor 5,2 (DEC-105 (3)); K-0.3, K-0.4, K-0.7 unveraendert |
| PRD-hergeleitete Groessen | DEC-51-z-Werte 2,4865 / 2,8016 / 3,1680; Dezilfaktor 3,51; WP-9-Materialitaet `|b| >= 0,30` / `s >= 2,85` VP; adv_sel-Etikett 1,75 bp je Bein; Spearman-SE `1,06/sqrt(n-3)` | PRD 9.2 C | z-Werte sind MDE-Faktoren (DEC-94 (1)); Dezilfaktor gilt (L-18); WP-9 erfuellt (DEC-61); adv_sel-Etikett gilt (DEC-69 (3)); uebrige 9.2-C-Zeilen siehe Konkordanz |
| Welle-1-Zensus | rho(BTC,ETH) 30 min 0,815 [0,800; 0,828]; sigma_xs Median 9,85 %/Woche; sigma_LS 4,77 %; Funding-Wochen-AK lag1..4 0,42/0,24/0,18/0,15; PERP_SPREAD_BP je Umsatz-Dezil 1,6..30,6 bp (Ein-Snapshot 2026-09-14) | DEC-67 E4 | gilt mit Erratum-Etikett "unvollstaendiges Panel" (DEC-100); Funding-AK nach oben verzerrt durch Null-Auffuellung (DEC-93 Merkposten (c)) |
| Breite, Klumpen | N_eff 178,8 (52 W) / 101,2 (104 W) Ledoit-Wolf deskriptiv; Klumpen-Anteil ~12 %; negativer Anteil 76-87 %; Intervall-Wechsel 580/140/143/15 | DEC-70 E2 | gilt (Erratum-Etikett DEC-100) |
| Praemien-Kohaerenz | Ruhe: Funding 0,24-0,51, IV-RV BTC/ETH 0,907, Funding x IV-RV ~0; Stress: Funding 0,6-0,7 gegen 0,2-0,35, IV-RV 0,88, BTC-Funding x IV-RV -0,4; Portfolio-Nulleffekt k=2..5 E[SR] ~0, SD ~0,40, p95 ~0,65, p99 ~0,95; E[max SR] K=5..100 0,46..0,97 | DEC-62 E2; DEC-65 (1) | gilt |
| Nach-Schock-Regime | Tages-Skala, Omori-artiger Zerfall (Halbwertszeiten BTC/ETH 22-31 h); Stress-Kostenfenster >= 1 Kalendertag nach Schockstunde; RECOVERY_H_P90 auf STRESS_ABS kein Befund (27 < 30) | DEC-63 | gilt |
| Maker-Fill, adverse Selektion | p_fill(60 s) 0,06 (FIFO-Untergrenze) .. 0,35 (Pro-rata-Obergrenze); adv_sel FIFO ~0,7 bp je Bein in Ruhe; Maker-Nettovorteil ~2,8 bp je gefuelltem Bein gewichtet mit p_fill; Lauf 4 massgeblich | DEC-69; DEC-71 (1); DEC-78 | gilt; Stress: Taker-Pfad (VR-g14) |
| Funding-Mechanik | `I = 0,03 % / (24 / Intervall_h)` empirisch bestaetigt; Totzone 46,7 % der Symbol-Tage; Auto-Switch seit 2025-10-30 (1h-Laeufe Median 8 Tage) | DEC-84; DEC-67 Anlass | gilt |
| Options-Liefergebuehr | 0,015 % des Underlyings je Kontrakt, Cap 12,5 % des Optionswerts [sek]; `FEE_OPTION_DELIVERY_OF_INDEX` erst mit `tradability3` | DEC-74 Nachtrag (3) | [sek]; Nutzerbestaetigung an der Primaerquelle offen |
| A2-Nuisance | sigma30 Cluster Freitag 43,8 bp (BTC 40,2 / ETH 52,6), Mo-Do 42,5, Wochenende 34,8, Monat+Quartal 52,4; rho Freitag 0,78; c 1,15..1,46 | DEC-98 N7 (2) | gilt; ersetzt PRD-Vol-Kette 36 bp |
| VRP-Prior | Band 3,2..10,5 VP, Referenz pi-2 7,14 VP | DEC-98 N2 (2); DEC-105 (6) | gilt |
| Klasse-W-Streuung | reale Wochen-SD des fm8-IC im Pilot 0,116..0,134 = 2,3..2,6x der faktorerhaltenden Null; F2_real 0,0086..0,0131 | GL-035; DEC-101 Teil 3 | gilt (Etikett fuer Querschnitts-Designs) |
| Ausfalltage Live-Stroeme | 14 gemeinsame Fehltage seit 2026-06-16 (10,1 %); im Fenster 2026-07-01..10-31 13 von 123 | H21_LUECKENLISTE Abschn. 2 | Fakt; Budget-Regel nur vorgeschlagen (5.5) |

---

## 3. Registrierung unter 3.1: Pflichtzeilen und YAML

### 3.1 Grundsatz (PRD 3.3, 3.4)

Eine Registrierung ohne vollstaendige Pflichtzeilen ist kein gueltiger Registry-Eintrag; ein Lauf darauf ist kein
gueltiger Lauf (PRD 3.3). Der Markdown-Eintrag ist der normative Text, in den ein gezaunter YAML-Block eingebettet wird;
die 2.0-Registry wird nicht migriert (PRD 3.4). Linter-Auflagen (PRD 3.4, "Registry-Format 3.0", als Entwurf gefuehrt):
(a) der Linter unterliegt der Loud-Fail-Doktrin; (b) Pflichtfelder duerfen keine Haekchen werden - jede Schwelle und
jeder Nulleffekt braucht eine Herleitungs-Referenz (Dateipfad + Test-ID), nie einen nackten Skalar; (c) append-only
mechanisch erzwungen (Hash-Pin der Alt-Eintraege). Der Linter ist Baustein F1 (DEC-104 E9). Nummer und Beschluss dieser
Werkzeug-Entscheidung sind offen (**WD-08**).

### 3.2 Pflichtzeilen

| PZ | Zeile / YAML-Feld | Inhalt (bindend) | Herkunft | Geltung |
|---|---|---|---|---|
| PZ-01 | Power (`power`) | alpha, Seitigkeit, Power, Richtung, Cluster-Einheit, N_eff und detektierbare Effektgroesse mit Rechenweg; gerechnet mit genau der SE-Regel des Tests (VR-b08, VR-b09); ab K1 Power 0,80 der gemeinsamen Regel an der SESOI-MDE (VR-b14) | PRD 3.3.1; DEC-51; DEC-94 (3)/(4); DEC-104 E2 | sofort / ab K1 |
| PZ-02 | Entscheidungsrelevanz (`decision_relevance`, `economic_minimum`) | was ein PASS konkret aendert (nur naechster Mess- oder Tradability-Schritt, VR-g08), was ein DROP schliesst, was ein GL-012 bedeutet; oekonomische Mindestmagnitude als Etikett, nie Gate | PRD 3.3.2; C.2; PRD 8.1 | sofort (Verhaeltnis zu SESOI: **WD-01**) |
| PZ-03 | Cluster-Einheit (`cluster_unit`) | Resampling-Einheit und N_eff nach VR-b03 | PRD 3.3.3; DEC-51 (3) | sofort |
| PZ-04 | Selektions-Deflation (`selection`) | K vorab; Decke analytisch und am Null-Fixture gemessen; z-Einheiten (VR-b04) | PRD 3.3.4; DEC-94 (7) | sofort |
| PZ-05 | Drittes, adversariales Fixture (`fixtures.adversarial`) | Klasse P Peso-Fixture (Nullpraemie plus Merton-Spruenge, Rate 1/3 Jahre, -35 %; das Gate MUSS durchfallen); Klasse W Faktor mit mechanischer Markt-Beta-Korrelation auf Panel mit dominantem Marktfaktor; Klasse E auf vergangenen Renditen selektierte Ereignisse auf einem Random Walk | PRD 3.3.5 | sofort |
| PZ-06 | Kostenmodell-Bindung (`constants_hash`) | SHA-256 ueber `tradability3/constants.py` im Ergebnis; abweichender Hash = kein gueltiger Lauf; ungemessene Konstanten RAISEN (VR-g14) | PRD 3.3.6 | sofort |
| PZ-07 | Irreversibilitaets-Probe (`irreversibility_probe`) | vor jeder daten-gated-Sperre eine dokumentierte Probe auf oeffentliche Nachladbarkeit; umgekehrt rechtfertigt nur Irreversibles einen Dauerstrom | PRD 3.3.7 | sofort |
| PZ-08 | Positivkontroll-Vorschaltung (`positive_control`) | nach VR-f12 | PRD 3.3.8 | sofort |
| PZ-09 | Kapital, Steuer, Venue (`capital_tax_venue`) | (a) Rendite auf gebundenes Kapital, Kapital-Multiplikator m UNGEMESSEN, Pflicht-Sensitivitaet; (b) steuerliche Behandlung "UNBELEGT - Par. 8.2", keine Netto-Aussage ohne Vorbehalt, `r_USD = 0` ist Annahme; (c) Venue-Ereignis und Zahler-Bestand nach 2024 | PRD 3.3.9; PRD 8.2 | sofort |
| PZ-10 | Stress-Episode (`stress_episode`) | `STRESS_REL`-Abdeckung als Nachweis bzw. `STRESS_ABS` fuer Liquiditaets-/Fill-Fragen (VR-g13); mit Erreichbarkeit in den Urteilsfenstern (VR-f07) | PRD 3.3.10; DEC-55/56; DEC-104 E8 (d) | sofort |
| PZ-11 | Ergebnis-Artefakte (`artifacts`, `report_line`) | nach VR-f03 und VR-f02 | PRD 3.3.11; DEC-53; DEC-105 | sofort |
| PZ-12 | Test-Pflichten | T0 Unit; T1 drei Fixtures positiv/null/adversarial; T2 Determinismus N>=3 mit Fingerprint; T3 Checkpoint-Round-Trip; T4 Gate-Arithmetik auf konserviertem Payload; T5 Konstanten-Pin; T6 Legacy-Import-Sperre; T7 Artefakt-Round-Trip (fehlt etwas: KEIN VERDIKT) | PRD 3.3.12 | sofort |
| PZ-13 | `zone` | genutzte Abschnitte mit Zone (X/V/K), Datenfamilie und "rein ab"-Datum (VR-d08) | DEC-104 E9, E4 (a); N1 (2) | ab K1 |
| PZ-14 | `cohort` | Kohorten-Stichtag (VR-d13) | DEC-104 E9, E4 (f) | ab K1 |
| PZ-15 | `alpha_test` | fest 0,0025, z_krit 2,8070 (VR-b14) | DEC-104 E9, E2 | ab K1 |
| PZ-16 | `screen` / `stability_test` | Screen: juengstes 12-Monats-Fenster bei 0,05 (beschlossen); Stabilitaetstest als Gate nur bei P-2 (c) (vorgeschlagen, N); Stabilitaetstest als Bericht immer (VR-e02) | DEC-104 E9, E2, E6; N2 (4) | ab K1 |
| PZ-17 | `looks` | Zone V: ein Blick; Zone K: Blickzahl (<= 4), Zeitpunkte, O'Brien-Fleming-Spending-Plan, Screen an jedem Wirksamkeits-Stopp, Futility-Regel, t-artige Grenzen (VR-d11, VR-d12, VR-f08) | DEC-104 E9, E4 (d), (e); N2 (7) | ab K1 |
| PZ-18 | `sesoi_curve` | Kurve aus dem registrierten Kostenmodell ueber Horizont und Persistenz, Rahmen (Einzelposition / Dezil-L/S, **WD-04**), Kostenbasis Taker mit Gabelungs-Etikett (VR-c01..VR-c04) | DEC-104 E9, E3 (a); DEC-105 (1), (8) | ab K1 |
| PZ-19 | `prior_label` | "Literatur: primaer belegt / [sek] / UNBELEGT" (ohne Blockade, VR-c05); Prior-Verteilung aus Zone X mit Konto-Zeile, selektionsbereinigt (VR-c06) | DEC-104 E9, E3 (b), (c) | ab K1 |
| PZ-20 | `selection_k` | K nach VR-b17 (berechnete plus registrierte, nicht gerechnete Varianten), kumuliertes K der Familie aus Konto und Inventar | DEC-104 E9; N1 (9) | ab K1 (inhaltlich PZ-04) |
| PZ-21 | `oc_line` | P(PASS bei 0), P(PASS bei SESOI), P(PASS bei Prior-Median), >= 1.000 Seeds (VR-f04) | DEC-104 E9, E8 (a) | sofort |
| PZ-22 | `strictness_ratio` | Quotient, Zerlegung je Festlegung, Gabelungsregister; ab 1,3 Nutzer-Vorlage (VR-f05) | DEC-104 E9, E8 (b); N1 (9) | sofort |
| PZ-23 | `n_eff` | effektives N der Cluster mit gemessenem rho bzw. c (VR-b03) | DEC-51 (3); DEC-105 Berichtszeile | sofort |
| PZ-24 | `c_overlap` | Varianzfaktor >= 1 bei Ueberlappung (VR-b05) | DEC-104 N2 (7); DEC-105 Berichtszeile | sofort |
| PZ-25 | `lesestatus` | je genutzter Datei: nie berechnet / berechnet-versiegelt-ungelesen / gelesen (VR-g07) | DEC-104 N1 (6) | sofort |
| PZ-26 | `design_menu` | registriertes Design-Menue und mechanische Auswahlregel mit Ergebnis (VR-e01) | DEC-104 E5 | ab K1 |
| PZ-27 | `reachability` | erreichte Beobachtungen je Schwelle, Clusterzahl, Stress-Zelle in den Urteilsfenstern (VR-f07) | DEC-104 E8 (d) | sofort |
| PZ-28 | `annual_book` | erwartete Falsch-PASS des Kalenderjahres vor und mit dieser Registrierung (VR-d14) | DEC-104 E4 (g) | sofort |
| PZ-29 | `c17_refs` | Zeilen des Konto-Inventars (O-nnn), Vorbelastungen, gesehene Groessen (VR-d18, C.17) | DEC-104 N1 (1); C.17 | sofort |
| PZ-30 | `vorwissens_klasse` | Datenfamilie und Vorwissens-Klasse nach FENSTERREGISTER (VR-d16) | DEC-104 E4 (i) | sofort |

PZ-01..PZ-12 sind die zwoelf Zeilen aus PRD 3.3; PZ-13..PZ-25 sind die im Auftrag genannten neuen Felder (davon zehn
aus DEC-104 E9); PZ-26..PZ-30 sind Registrierungspflichten, die DEC-104 E4/E5/E8 und N1 bereits ausdruecklich verlangen,
ohne sie als Feld zu nennen.

### 3.3 YAML-Template 3.1 (neu; ersetzt PRD 3.4 fuer Registrierungen ab K1)

Felder und Kommentare nennen ihre Herkunft; `<...>` ist auszufuellen; jede Zahl mit Herleitungs-Referenz (PRD 3.4 (b)).
Grundlage: PRD 3.4 und die registrierte H-32-Datei (`state/registered/h32_v1.yaml`, Registry-Abschnitt H-32) als
Praezedenz fuer `z_krit`/`mde_faktor`, Pilot-, Pin- und Null-Felder.

```yaml
id: <H-34..>                                   # naechste freie Nummer H-34 (GL-036)
klasse: <P|W|E>                                # PRD 3.2
capital_free: true                             # C.2
hypothese: "<ein Satz, falsifizierbar>"        # PRD 3.4
ertragsquelle: "<Praemie|Prognose|Ereignis|Struktur> + Zahler"   # PRD 3.4; PZ-09 (c)
metric: "<genau eine urteilstragende Groesse>" # PRD 3.4
richtung: <positiv|negativ>                    # DEC-51 (1)
cohort: <YYYY-MM-DD>                           # PZ-14; erster Stichtag 2027-01-01 (DEC-104 E4 (f))
zone:                                          # PZ-13; DEC-104 E4 (a), N1 (2); FENSTERREGISTER Abschn. 6
  - {abschnitt: "<von..bis>", zone: <V|K>, datenfamilie: <F1..F6>, rein_ab: <YYYY-MM-DD>}
vorwissens_klasse: "<Datenfamilie: Regel>"     # PZ-30; DEC-104 E4 (i)
lesestatus:                                    # PZ-25; DEC-104 N1 (6)
  - {datei: <pfad>, status: <nie_berechnet|berechnet_versiegelt_ungelesen|gelesen>}
c17_refs: [<O-nnn>]                            # PZ-29; DEC-104 N1 (1)
windows:                                       # DEC-99 (1); DEC-104 E4 (d)/(e)
  - {id: <W1|W2|Kq..>, von: <YYYY-MM-DD>, bis: <YYYY-MM-DD>, zone: <V|K>, rolle: <urteilstragend|pilot_nicht_urteilstragend|aera_profil>}
decision_rule:                                 # PZ-15/PZ-16; DEC-104 E2 (Variante offen: P-2)
  alpha_test: 0.0025                           # fest je Test
  z_krit: 2.8070                               # gepoolt einseitig; DEC-94 (1)
  screen: {fenster: juengste_12_monate_bzw_4_quartale, alpha: 0.05, z_krit: 1.6449}   # Variante (a), beschlossen
  stability_test: null                         # nur bei P-2 (c) (vorgeschlagen, N); als Bericht immer (DEC-104 E6)
  power_target_gemeinsam: 0.80                 # DEC-104 E2
  mde_faktor: <Zahl>                           # nie Schwelle (DEC-94 (1))
looks:                                         # PZ-17; DEC-104 E4 (d)/(e); N2 (5)/(7)
  zone_v: {anzahl: 1}
  zone_k: {anzahl: <1..4>, plan: obrien_fleming, spending: <...>, zeitpunkte: [<...>], screen_an_jedem_stopp: true, futility: "Z < 0 an Blicken 1-3", grenzen: t_artig}
sesoi_curve:                                   # PZ-18; DEC-104 E3 (a); DEC-105 (1)/(8); Rahmen offen WD-04
  kostenmodell_constants_hash: <sha256>        # Vorbedingung offen WD-08
  rahmen: <einzelposition|dezil_ls>
  kostenbasis: taker_vip0                      # Etikett "Gabelung Richtung Testbarkeit gegen Maker"
  persistenz_phi: <gemessen (Konto-Zeile) | 0 als Default mit Etikett>
  ref: <pfad#test_id>
prior_label:                                   # PZ-19; DEC-104 E3 (b)/(c)
  literatur: <primaer|sek|UNBELEGT>            # Etikett ohne Blockade
  prior_verteilung_ref: <KONTO_ZONE_X Zeile | null>
  selektionsbereinigt: true                    # DEC-99 (3)
threshold: {regel: "Statistik in Richtung >= z_krit * SE", ref: <pfad#test_id>}   # DEC-94 (1)
structural_null: {komponenten: [<...>], skalierung: "k = max(1, Ist/Null)", ref: <pfad#test_id>}   # C.4; VR-e06
nuisance:                                      # DEC-94 (5) / DEC-104 E6 -> WD-02
  quellen: [vorperiode_nur_streuung, null_simulation]
  bindend: <juengstes_vorfenster | groessere_SE_ueber_quellen_und_stress>
  stress_zeile: <...>
power:                                         # PZ-01; DEC-94 (3)/(4)
  se_regel: "<identisch mit dem Lauf>"
  sd_teststatistik: {wert: <Zahl>, ref: <pfad>}
  c: "max(1, c_hat)"
  blocklaenge: "<aus gemessener Autokorrelation>"   # DEC-104 N2 (7)
  mde80: {wert: <Zahl>, ref: <pfad#test_id>}
  sesoi: <Zahl aus sesoi_curve>
  testbar: <true wenn mde80 <= sesoi>          # DEC-104 E3 (a); Planung nur gegen SESOI (N2 (6))
cluster_unit: <kalendertag|kalenderwoche|ereignis|fenster>   # PZ-03
n_eff: <Zahl, gemessenes rho>                  # PZ-23
c_overlap: <Zahl >= 1>                         # PZ-24
selection: {K: <Zahl>, K_kumuliert_familie: <Zahl>, z_max: <Zahl>, ceiling_ref: <pfad#test_id>}   # PZ-04/PZ-20
design_menu: {optionen: [<...>], auswahlregel: "<mechanisch, nur Vorperioden-Nuisance + SESOI/Prior>", gewaehlt: <...>}   # PZ-26
reachability: [{parameter: <...>, beobachtungen_in_urteilsfenstern: <Zahl>}]   # PZ-27
oc_line: {p_pass_0: <>, p_pass_sesoi: <>, p_pass_prior_median: <>, seeds: ">= 1000", ref: <T0-Test>}   # PZ-21
strictness_ratio: {wert: <>, zerlegung: [<...>], gabelungsregister_ref: <pfad>}   # PZ-22
annual_book: {jahr: <YYYY>, erwartete_falsch_pass_vorher: <>, mit_dieser_registrierung: <>}   # PZ-28
economic_minimum: {wert: <>, ref: <>, label: <ueber_wand|unter_wand>}   # PZ-02, Etikett (C.2)
decision_relevance: {on_pass: "<naechster Mess-/Tradability-Schritt>", on_drop: "<...>", on_gl012: "<kein Verdikt>"}   # PZ-02
capital_tax_venue: {kapitalbasis: <...>, steuer: "UNBELEGT - PRD 8.2", venue_event: <...>, zahler_post_2024: <...>}   # PZ-09
stress_episode: {liste_ref: <STRESS_REL|STRESS_ABS + sha256>, rolle: abdeckungsnachweis, tage_in_fenstern: <Zahl>}   # PZ-10
irreversibility_probe: {ergebnis: <nachladbar|irreversibel>, ref: <...>}   # PZ-07
positive_control: {vorgeschaltet: <true|false>, produktionskonfiguration: true, welt: "<kalibrierte Null-Welt>", kriterium: "<vorab>", ref: <...>}   # PZ-08
fixtures: {positive: <...>, null: <...>, adversarial: <...>}   # PZ-05
artifacts: {cluster_series_ref: "<pfad + sha256>", bootstrap_replicates_ref: "<pfad + sha256 | seed + generator_fingerprint>"}   # PZ-11
report_line: [estimate, se, ci95, upper_limit95, n_eff, c_overlap, selection_k, shrinkage_note, zone]   # DEC-105
fdr: {family: <F-...>, bh_alpha: 0.10, p: "Max-p ueber Fenster (Methode: WD-16)", over_family: <F-...>, kohorte_by_q: 0.10}   # VR-b16/b17; VR-d13
constants_hash: <sha256 | "n/a - kapitalfrei ohne Kostenmodell">   # PZ-06
data_fingerprints: [<...>]                     # Praezedenz H-32: Panel, Register, Code-Commit, registrierte YAML
feasibility_verdict: <testbar | "GL-012 strukturell nicht testbar">   # DEC-104 E3 (a)
etiketten: [<...>]                             # z. B. C.17, "zugelassen nur durch DEC-..", Gabelungen
```

---

## 4. Kandidaten und Felder - eine bindende Fassung je Kandidat

### 4.1 A1 - Funding-Carry (Klasse P; H-31 nur in der Herleitung benutzt, nicht registriert)

- **Status:** nicht registriert; GL-033 (GL-012 vor der Registrierung unter den geltenden Beschluessen; theta UNBELEGT,
  eigenstaendig blockierend; DEC-93). Feststellung DEC-104 E3 (e): **strukturell nicht testbar** (MDE80 ~129 bp gegen
  Taker-SESOI 36 bp; ~12,8 Jahre je Fenster); GL-033 traegt dieses Etikett per Vermerk; Wiedervorlage nur bei veraenderter
  Nuisance, laengerem Horizont oder neuem Kostenmodell. KEIN Verdikt ueber den Funding-Carry (DEC-93).
- **Bindende Konstruktion (fuer jede Wiedervorlage):** Long-Bein D1 (staerkste Unterschreitung von I) gegen den
  gleichgewichteten Universums-Hedge, nicht Dezil-Long-Short (DEC-70 E1); Sortierschluessel = Wochen-SUMME von (F - I)
  ueber alle Zahlungen, I je Intervall anteilig (`I = 0,03 %/(24/Intervall_h)`, DEC-84 (1)), Totzonen-Zahlungen tragen 0,
  kein Tie-Break (DEC-67 E2); Nulleffekt als Totzonen-Modell mit Klumpen bei I, "I kuerzt sich im Querschnitt heraus" nur
  notwendig, nicht hinreichend (DEC-59); Vergleichszeile Universums-Praemie Pflicht (DEC-70 E1); urteilstragend die
  Summe aus Funding-Akkumulation und Preisbein, Zerlegung Pflicht, und das Residual-Alpha nach Orthogonalisierung gegen
  Momentum/Reversal (PRD 5.1 (c), (d)); Kill "Dezil-Degeneration" fuer D1 (streng negativer Anteil < 10 % in der
  Median-Woche -> KEIN VERDIKT im Fenster; DEC-67 E3, DEC-70 E1); Kill-(4)-Parameter `k <= 2,333 w` statt 0,30 (DEC-58
  E1 (e)); N_eff im Stress-Fenster als Pflichtzeile, Power/Kill mit Stress-N_eff (DEC-65 (2)); schriftliche Feststellung
  der W1/W2-Inhomogenitaet (Auto-Switch ab 2025-10-30), Intervallklassen-Spalte, look-ahead-freier Symbol-Wochen-
  Ausschluss, Pflicht-Sensitivitaet mit intervall-normiert eingeschlossenen 1h-Symbolen (DEC-58 E3; DEC-84); W_eff = 0,41 W
  nur nach VR-b09.
- **Zonen/Vorwissen:** Funding-Lage auf W1/W2 verbraucht (VR-d20); Funding BTC/ETH ist BTC/ETH-Aggregat (VR-d16).
- **Etiketten (DEC-93):** Halbwochen-Funding-Analog gesehen; Nuisance-Funding-Bein-Mittel implizit offengelegt;
  W2-Schluessel-Autokorrelation an der Kill-(4)-Grenze; W1/W2-Inhomogenitaet.
- **Ersetzte Altzeilen:** PRD 5.1 (Konkordanz KO-052..KO-061).

### 4.2 A2 - EXP-CLOCK, Verfallskalender als Ereignistakt (Klasse E)

- **Bindende Fassung des Designs:** VR-e09 (Ereignismenge), VR-e10 (Statistik), VR-e11 (Placebosatz), VR-e12 (Null und
  Schwelle), VR-e13 (Negativ-Panel), VR-e14 (fremde Referenzfenster), VR-e15 (Fenster, Nuisance, G-C8), VR-e07
  (Festlegungen unter 3.1), VR-e04 (Konjunktion), VR-g06 (Vorperiode). Gate-Text nach PRD 5.2 (1)-(6) mit diesen
  Ersetzungen; Vorbedingung "V-5 belegt eine Effektgroesse" bis K1, ab K1 Literatur als Etikett (VR-c05; **WD-10**).
- **Status:** nicht registriert; unter Bestand GL-012 vor der Registrierung (V-5b UNBELEGT; Volltexte nicht beschaffbar;
  DEC-103). Unter 3.1 (VR-e08) nach DEC-104 N2 (3), (9): unter P-2 (a) strukturell nicht testbar (Boden 24,30 bp > Taker-
  SESOI 22 bp; Kette bei 24 Monaten 28,06 bp, Strenge-Quotient 1,355 > 1,3 -> Nutzer-Vorlage nach VR-f05); "GL-012 folgt,
  sobald (a) bestaetigt ist"; unter P-2 (c) bei Lesart B etwa 2028-01 bei 22 bp, 2027-04 bei 25 bp. **Haengt an P-2.** Bis
  dahin P-0: kein A2-Code-Bau.
- **Pilot-Route** (Vorperiode als Pilot-Schaetzfenster; Regel U-A2): Vorlage, nicht beschlossen; Lockerung; mit den
  Festlegungen uebergibt sie bei 16,5 bp [sek] praktisch nie (0,0001), bei 25 bp in 4 % (DEC-103 N1 (9), (10)); die
  Vorperiode ist fuer A2-Mittel/Vorzeichen gesperrt (VR-g06).
- **Daten:** 1-min-Kerzen BTC/ETH vorhanden; Negativ-Panel XRP/BNB/SOL fehlt (Anfrage 2026-10-31, Weiterleitung durch
  den Nutzer offen; Alternative Ableitung aus `bybit/publicTrade`) (DATENANNAHMEN Nr. 5; DEC-104 Hinweis).
- **Ersetzte Altzeilen:** PRD 5.2 Placebo-Bindung, struktureller Nulleffekt, Tabelle A2-P1, Fenster, Vol-Kette,
  Zuordnung (DEC-103 E8; Konkordanz KO-062..KO-072).

### 4.3 A3 / H-28..H-30 / H-32 / H-33 - Querschnitt (Klasse W)

- **Status:** H-28..H-30 Drittfassung registriert (`state/registered/h28_h30_v3.yaml`, sha256 `bd948f34...c299`); alle
  sieben Varianten GL-012 vor dem Lauf, kein Lauf (GL-032, DEC-92). H-32 registriert (`state/registered/h32_v1.yaml`,
  sha256 `0fadda78...`); Pilot genau einmal gelaufen, GL-012 (Pilot) fuer alle vier Varianten, kein Test (GL-035,
  DEC-101 Teil 3). H-33 nicht registriert, GL-012 vor der Registrierung (Prior UNBELEGT; Nutzerentscheid Option 1;
  GL-036, DEC-102 N2). Kein Verdikt ueber Momentum, Reversal oder Vol-Anomalie. Naechste freie Nummer H-34.
- **Bindende Praezedenzen fuer kuenftige Klasse-W-Designs:** Universum lineare USDT-Perpetuals (DEC-101 E1);
  Survivorship ueber Union-Panel und Register (VR-g10); Beta-Kontrolle durch die registrierte Methode `fm_neutral_8w`
  (DEC-86, DEC-88), Auswahl nur nach vorab fixierter Regel; skalierte Null Pflicht (VR-e06); Positivkontrolle in
  Produktionskonfiguration (VR-f12); p-Wert der Ueber-Familie aus faktorerhaltenden Null-Replikaten, Block-Permutation
  report-only (DEC-99 N1 (1); **WD-16**); ein anderes Design ist eine neue Hypothese mit eigenem K (DEC-58 E2, DEC-92).
- **Zonen und Vorbelastung:** W1/W2 fuer Klasse W blind (Zone V; fm8 ungeoeffnet; DEC-101 E12); die fm8-Reversal-
  Familie ist auf W1/W2 vorbelastet (VR-d19); der Pilotabschnitt 2022-04-18..2024-06-24 ist fuer fm8-korrelierte
  Statistiken verbraucht (DEC-99 (5); GL-035); IC-Rohserien berechnet, versiegelt, ungelesen (VR-g01).
- **Unter 3.1 (DEC-104 N2 (3)):** Wochen-IC-SD 0,13 (Stress-Lesart der Pilotmessung) gegen SESOI 0,040 nie (Boden 0,0448);
  SD 0,09: Boden 0,031, erreichbar ab 2027-01 (Lesart B); unter P-2 (c) mit SD 0,13 Lesart B 2027-07 (OC (h)). Der
  SESOI-Rahmen fuer Klasse W ist offen (**WD-04**).
- **Ersetzte Altzeilen:** PRD 5.3 (Konkordanz KO-073..KO-080).

### 4.4 A4 - Perp gegen datierten Future (Klasse P)

- **Status:** RECORDING-FIRST, nicht gestrichen (DEC-59); Quote-Aufzeichnung datierter Futures erst ab 2026-10-20 in
  `bybit/rest.tickers15m` (nicht 2026-06-16); sigma_w fruehestens ab 2027-10-20 messbar (DEC-98 N4 (a)); keine
  A4-Registrierung, bis der Fensterwiderspruch aufgeloest ist (DEC-105 (12)).
- **Offener Widerspruch WD-07:** PRD 5.4 ">= 8 vollstaendige Verfallzyklen (Quartale = 2 Jahre)", Power-Zeile mit N = 8 und
  Gate "in beiden Haelften", gegen PRD 5.4 / DEC-59 "Gate-Lauf in 12+ Monaten" bzw. "nach >= 12 Monaten Quote-Aufzeichnung
  registrierbar". **Vorschlag (DEC-105 (12)): Fensterlaenge als abgeleitete Groesse nach VR-e01 (Design-Menue,
  mechanische Auswahl aus Nuisance und SESOI) - vorgeschlagen, Entscheider N.**
- **Bindender Kern (PRD 5.4, mit Ersetzungen):** w = implizierter Terminzins beim Einstieg minus akkumulierte Funding-Rate,
  gegen die ex-ante-implizierte Terminkurve; Nulleffekt w_null aus Margin-Bindungsdifferenz x Opportunitaetszins plus
  Jensen-Kruemmung; Cluster = Verfallzyklus; Schwelle `z_krit x sigma_w / sqrt(N_cluster)` (VR-b06 statt 2,4865);
  `w_min = 2 x Zyklus-Kosten + m x r_opp` nur Etikett und Teil von A4b; Settlement-Pfad RAISED bis V-4
  (`deliveryFeeRate` ist ein instruments-info-Feld, DEC-59); Ausfalltage des Live-Stroms beachten (PRD_ANALYSE 4.14).
- **Verwandtes Feld:** F10 Deribit-Futures-Basis seit 2017 als A4-Vorlaeufer (Datenprobe zuerst; 4.9).

### 4.5 A5 - Skew-Praemie und Options-Block (Klasse P) - GESPERRT

- Reihenfolge bindend (E.6): (a) Delivery-/Exercise-Gebuehr an der Primaerquelle (V-4), (b) Options-Spread-Zensus mit
  durchgaengiger Aufzeichnung (setzt die tagesgenaue Ketten-Luecken-Karte voraus), (c) H-26 selbst gemessen (PRD 5.5).
- Stand: V-4 (a) Deribit-Liefergebuehr nur [sek] (DEC-74 N (3)); Luecken-Karte der Optionen als Etikett (14 Tage ohne
  Optionsdaten auf beiden Boersen; DEC-98 N4 (f)); H-26 gesperrt (4.8). Schwelle aus der gemessenen Skew-Verteilung, nie
  aus C-33; A2-Ergebnis ist Pflicht-Eingang jeder Halte-bis-Verfall-Rechnung (PRD 5.5). `tardis/options_chain` (ein
  Stichtag je Monat, 2019-04..2026-10) erlaubt nur neue monatliche Hypothesen nach C.8-Inhaltsprobe, Stichtage
  <= 2026-06-01 (DEC-105 (10); DATENANNAHMEN Nr. 4).
- Vorab fixiert: die tagesgenaue Ketten-Luecken-Karte (R3-K-37 Stufe 1) wird gebaut, sobald H-26 ein Verdikt hat oder V-4
  die Gebuehrenfrage an der Primaerquelle klaert (PRD 9.1, 9.3 Nr. 8); beides ist nicht eingetreten (4.8; DEC-74 N (3) nur [sek]).

### 4.6 H-27 / VRP (Klasse P)

- **Status:** nicht registriert; GL-034 (GL-012 vor der Registrierung; keine Fensterlaenge L in {6, 9, 12} testbar;
  DEC-97); DEC-104 E3 (e): **strukturell nicht testbar** (MDE80 12,9 VP gegen eine kostenbasierte SESOI von etwa 1,5 VP
  [U, Kritik K-10]). KEIN Verdikt ueber die Volatilitaets-Risikopraemie.
- **Bindend fuer jede kuenftige VRP-Hypothese:** blinde, prospektive Urteilsfenster ab 2026-07-01, W1/W2 nur Aera-Profil
  "nicht blind" (DEC-96 E1); Blind-Siegel (VR-g04); Prior-Band 3,2..10,5 VP, Referenz 7,14 VP (DEC-98 N2; DEC-105 (6));
  Hochfrequenz-RV bringt keinen Gewinn (Option 3 geschlossen, DEC-98 N5 (1)); "Ein VRP-Urteil ist auf keinem Datenweg vor
  2029 erreichbar" (DEC-98 N5 (2)); Fenster ueber 12 Monate sieht DEC-96 E2 nicht vor (DEC-97). Die Fensterlaengen-Regel
  DEC-96 E2 (kleinstes L aus {6, 9, 12}) betraf H-27; fuer Registrierungen ab K1 gilt VR-e01.

### 4.7 H-21 (2.0, LIQ-TAG)

- In der registrierten Form (lueckenlose `done_days` fuer `allLiquidation` und `publicTrade`, BTC und ETH, ueber
  W1 2026-07-01..09-28 und W2 2026-09-29..12-27) **nicht entsperrbar**: W1 hat 13 Fehltage `allLiquidation` (BTC und ETH)
  und einen Fehltag `publicTrade` ETHUSDT; W2 bisher 33/33; Nachladbarkeit [V] nicht gegeben (DEC-105 (11);
  H21_LUECKENLISTE Abschn. 1). Formale Schliessung ("GL-012 Daten, registrierte Form nicht erfuellbar") erst nach der
  Data-Harvest-Antwort zur Nachladbarkeit; eine Neuregistrierung mit anderen Fenstern waere eine neue Hypothese in K1.
  Kompendium E.1 ("GESPERRT bis 2026-12-27") ist ueberholt.

### 4.8 H-26 (2.0, VRP Deribit)

- Gesperrt (Default R-1, DEC-98 E2; DEC-104 E10). WP-9 entsperrt H-26 nicht (PRD 4.2). Die Lesart "Manifest-DONE live oder
  REST" ist durch PRD 4.2 ausgeschlossen; strenge Lesart (dvol DONE + Perp live mit Luecke <= 60 min) fruehestens
  2027-04-06, mit <= 30 min fruehestens 2027-05-11 (DEC-98 N4 (b); DEC-105 (11)); beide Lesarten liegen im Blindbereich;
  ein H-26-Lauf braucht eine neue DEC. Entsperrpfad nach Wegfall der Reihenfolge-Frage offen (**WD-11**). Kompendium E.2
  ("~Mitte November 2026") ist ueberholt.

### 4.9 Felder F1..F12 und Ideenkarten IK-01..IK-11 (nur Verweis)

Quelle Felder: PRD_ANALYSE Abschnitt 5 (Stand 2026-11-01, vor DEC-104); Quelle Karten: Sweep 3.0; Status unter 3.1 nach
VR-c05 (Literatur nur Etikett ab K1), VR-d08..VR-d16 (Zonen, Vorwissen), PRD_ANALYSE Nachtraege 1-3.

| Feld | Kurz | Zone / Siegel | Status |
|---|---|---|---|
| F1 | Tages-Querschnitts-Reversal 1-3 Tage, Gap, beta-neutral | W1/W2 (V), Renditefamilie; Pilotabschnitt verbraucht; rev1-Vorbelastung | Prior fuer die Gap-Statistik UNBELEGT; "heute nicht registrierbar"; mit IK-10 in dieselbe Kohorte (ein V-Blick je Familie) |
| F2 | Funding-Dynamik als Tages-Praediktor; R-7 Cap-Treffer | BTC/ETH nur prospektiv (K); Querschnitt wie F1 | Exploration in Zone X mit Konto; Prior UNBELEGT; Regimebruch 2025-10-30 |
| F3 | OI-Dynamik | BTC/ETH ab 2024-03 (Teil im Siegel) | Prior UNBELEGT; Datenauftrag OI aller Perps |
| F4 | Mikro-zu-Makro, Tages-Netto-Fluss | BTC/ETH-Aggregate nur prospektiv | Invariante als Zensus sofort; Prognose Prior UNBELEGT |
| F5 | Lebenszyklus-Ereignisse (Listing/Delisting) | Ereignisse bis 2026-06; ab 2026-07 BTC-Beta gesperrt | kein Prior; Zaehl-Zensus und Exploration sofort |
| F6 | Makro-Ereignisse (FOMC, CPI, NFP) | Termine ab 2026-07 im Siegel | Prior-Entscheidung noetig; Slot-Streuung als Zensus |
| F7 | Informationsfluss zwischen Venues (Tagesbasis) | zu kurz | Prior UNBELEGT |
| F8 | Optionsfluss/GEX | fast vollstaendig im Siegel | vor K1 nur S0; R3-K-32 vertagt bis A2-PASS |
| F9 | Liquidations-Kaskaden | fast vollstaendig im Siegel | S0-Zensus zuerst |
| F10 | Deribit-Futures-Basis seit 2017 (A4-Vorlaeufer) | X fuer Tage vor 2024-07-01 | Datenprobe zuerst |
| F11 | Zustandsabhaengigkeit (DVOL-Terzile, HMM) | wie Basisfeld | nur als registrierte Variante |
| F12 | Stablecoin-Angebot, Netflows | keine Datenbasis | Datenauftrag |

| Karte | Typ | Status |
|---|---|---|
| IK-01 Taker-Kostenkurve (Mikrostruktur-Invarianz) | Messprogramm | Zone X; "Vorbedingung jeder 3.1-Registrierung" [U, PRD_ANALYSE Nachtrag 1 (2)] |
| IK-02 Maker-Kostenkurve (Warteschlange) | Messprogramm | Zone X (L2 schwer); Maker-SESOI |
| IK-03 Leland-Kurve | Messprogramm | Zone X |
| IK-04 Skalengesetze, schwere Raender, minimale Nullwelt | Messprogramm | **Konto Nr. 2 eingetragen, Lauf ausstehend** (Datendienst) |
| IK-05 RMT-Faktorzahl, Netzwerk-Nullwelt | Messprogramm | **Konto Nr. 1 eingetragen, Lauf ausstehend** |
| IK-06 Optionsketten-Invarianten | Messprogramm (+ H) | nach Tardis-Inhaltsprobe |
| IK-07 Demografie des Perp-Lebenszyklus | Messprogramm (+ H) | Zone X; Ersatz der 8-Wochen-Regel vorgeschlagen |
| IK-08 Metrologie der Datenstroeme | Messprogramm | S0 auch im Siegel |
| IK-09 Delisting-Hazard | Hypothese | Zone X; IPCW fuer Querschnittstests |
| IK-10 Price Delay im Querschnitt | Hypothese | gegen persistenzbereinigte SESOI nicht testbar (PRD_ANALYSE Nachtrag 3; **WD-04**) |
| IK-11 Funding-Regelkreis | Reserve | teilweise Zone X |

---

## 5. Datenannahmen, offene Nutzerfragen, offene Widersprueche

### 5.1 Datenannahmen

Massgeblich ist `state/DATENANNAHMEN_REGISTER.md` (17 Zeilen, Stand 2026-11-02; Fortschreibung nach VR-g15); v3 dupliziert
es nicht. Fuer die Regeln dieses Entwurfs tragend: Nr. 1 (Tageskerzen und Funding aller Perps im Archiv; PRD-7.1/7.2-Plan
ueberholt), Nr. 5 (Negativ-Panel fehlt), Nr. 7 (14 gemeinsame Ausfalltage der Live-Sammler), Nr. 8 (H-21), Nr. 9 (H-26),
Nr. 10 (taegliche Verfaelle; PRD-Placebos leer), Nr. 13/14 (W2-Ende, Blind-Siegel), Nr. 15 (Datendienst-Verfuegbarkeit).

### 5.2 Offene Nutzerfragen (Entscheider N; bis zum Entscheid gilt der genannte Stand)

| Nr | Frage | geltend bis zum Entscheid | Quelle |
|---|---|---|---|
| 8.1 | Ausfuehrungsfrage (Widerspruch "bester Kandidat / kein Live-Order-Code") | Default (b): spaetere, getrennt gegatete Ausfuehrungs-Spur als Phase 4, leer bis Mess-PASS, Tradability-PASS und ausdrueckliche Freigabe (VR-g08) | PRD 8.1; DEC-73 E5 |
| 8.2 | Kapitalbasis, Steuerregime, Opportunitaetszins r_opp (dieselbe Groesse wie `r_USD = 0` in A1) | keine Blockade; Zeile "Steuerregime UNBELEGT - Par. 8.2"; keine Netto-Aussage ohne Vorbehalt; Gebuehrenstufe ebenfalls offen (P-11) | PRD 8.2; DEC-105 (9) |
| 8.3 | Sunset-Review der Recording-Engine (2.0, "F0" der 2.0-Akte; nicht zu verwechseln mit Fahrplanschritt F0, VR-h07) | faellig seit ~2026-09-11, offen (Faktenblatt `state/prd_analyse_2026-11-01/FAKTENBLATT_STATUS.md` E.13); Empfehlung des Orchestrators: durchfuehren, nur behalten, was eine registrierte Hypothese namentlich braucht; Recorder C-36 laeuft als Schutzgut weiter (VR-g03); das Point-in-Time-Roster ist davon unabhaengig | PRD 8.3; CLAUDE.md Schutzgueter |
| P-2 | Variante der Konfirmationsregel: (a) Screen 0,05 / (a') 0,20 / (a'') Vorzeichen 0,50 / (c) P-6-Lesart mit Stabilitaetstest | (a) beschlossen; Vorbehalt E2 verlangt Nachfuehrung vor der ersten Registrierung; Orchestrator schlaegt (c) vor (Entscheidungspunkt in 2b) | DEC-104 E2; N2 (2)-(4), (9) |
| P-8 | Reihenfolge der Blindperiode | gegenstandslos durch Kohorten (VR-d13); H-26-Folge offen (WD-11) | DEC-104 "Offen"; E4 (f) |
| P-9 | A2-Weg | nach VR-e08; Ergebnis haengt an P-2 | DEC-104 "Offen"; E7 (d) |
| P-10 | Klasse P: reines Mess-/Aufzeichnungsprogramm (PARK ist das beste Ergebnis) oder Kapitalregel ohne MinTRL | Default "Mess-/Aufzeichnungsprogramm" | DEC-104 "Offen"; PRD_ANALYSE 9.1; Kritik K-12 |
| P-11 | Umgebung und Budget: Netzfreigabe fuer offene Volltextquellen, Budget fuer Volltexte, Token-/CPU-Deckel, direkter Auftragskanal an Data-Harvest, Schluesseltrennung, privater Speicher fuer versiegelte Zwischenstaende, Gebuehrenstufe/Kapital/Steuer | offen; Default-Vorschlag der Synthese: Netzfreigabe ja, Rest nach Kostenbuch | DEC-104 "Offen"; PRD_ANALYSE 9.1 |
| P-12 | Regelaenderungs-Protokoll | Selbstbindung des Orchestrators (VR-h05) | DEC-104 "Offen" |
| P-13 | Nicht-Rendite-Mikrostruktur-Statistiken (Tradezahlen, Groessenverteilungen, Queue-Intensitaeten, Zeitstempel) auf W1/W2-BTC/ETH mit A2-Maske als Zone X fuehren (Lockerung, Richtung Testbarkeit) | Default nein: IK-01/IK-02 rechnen auf 2020..2024-06 (X) und ab 2026-07 (K) | PRD_ANALYSE Nachtrag 1 (10); Sweep 4.6 |
| TOST | Aequivalenzform (TOST) fuer Gesetzeshypothesen (Skalengesetze, Invarianzen; IK-01, IK-02, IK-06 b, IK-07) neben dem einseitigen Ueberlegenheitstest | vorgeschlagen (Etikett neutral; O-Vorschlag, Entscheider N); nicht beschlossen | Sweep 3.13; PRD_ANALYSE Nachtrag 1 (11) |
| Enrichment | Adaptive Enrichment fuer Querschnittsdesigns (am ersten K-Blick regelgebundene Einschraenkung auf eine Subpopulation) | vorgeschlagen (Lockerung in der Zeit, alpha-neutral bei korrekter Kombinationsregel), Entscheider N | Sweep 3.13 [sek: Simon/Simon 2013] |
| Horizont | Stundenhorizonte oeffnen | Nutzerfrage; Nicht-Wiederholungs-Nachweis D.4/D.12/D.14 noetig | DEC-105 (1) |
| Rollen | Modellbezeichnungen in CLAUDE.md und PRD 3.9 durch Rollen ersetzen; "eine Datei, eine Wahrheit" fuer die Verfassung (diese v3) | vorgemerkt, Entscheider N | DEC-105 "Vorgemerkt" |
| Pilot-Prior | darf ein vorzeichengedrehter, vorab geschrumpfter Pilot-Betrag Prior sein | Programmfrage (Testbarkeit); unter 3.1 teilweise durch VR-c06 beantwortet (Punktprior verboten) | PRD_ANALYSE 2 (S-5) |
| F1-Variante | F1 ohne Gap mit Bianchi-VW 0,023 als Prior-Kandidatin, dann Bounce-Kontrolle Pflicht | Programmfrage | PRD_ANALYSE 5 (F1) |
| Marktmodell | umfassendes generatives Mehrsymbol-Marktmodell | Entscheider N (D.16 als Gegenargument) | PRD_ANALYSE 0.4, Review B-18 |

### 5.3 Offene Widersprueche (zitiert, nicht entschieden)

| WD | Quelle A | Quelle B | betrifft | Entscheider |
|---|---|---|---|---|
| WD-01 | PRD 3.1: "die Regel gilt nicht nur fuer PASS-Bedingungen, sondern auch fuer Befundzweige von Zensus-Paketen und fuer Feasibility-Kill-Bedingungen. Ein Ausloeser, der eine Handelskostenzahl ist, ist ein Tradability-Kriterium, gleichgueltig, wie das Feld heisst." DEC-104 E10: C.1..C.19 unberuehrt ausser C.10 und C.18 | DEC-104 E3 (a): "Feasibility-Massstab ist die kleinste oekonomisch relevante Wirkung (SESOI) je Kandidat, vorab registriert aus dem registrierten Kostenmodell ... sonst GL-012"; Kritik K-10 schlug "C.2-Ausdehnung auf Feasibility-Kills zurueck (Klarheit)" als Teil der N-Korrektur vor, DEC-104 nennt es nicht | VR-a02, VR-c01 | N |
| WD-02 | DEC-94 (5): "Bindend ist die groessere SE ueber Quellen und registrierte Kalibrierungen (stress, DEC-77 E1 (b))"; DEC-104 E10: "Unberuehrt: ... DEC-94 (1), (4), (5)" | DEC-104 E6: "bindend fuer SE und Schwelle ist das juengste Vorfenster (12 Monate vor dem ersten Urteilsfenster), aeltere Vorfenster (einschliesslich Stress 2021/22) nur als Sensitivitaets-/Stress-Zeile" | VR-b10, VR-e03, VR-e12 | N |
| WD-03 | DEC-104 E7 (c): "Stress bindend -> wird nach E6 zur Sensitivitaets-Zeile, ausser die OC (E0) zeigt fuer A2 ein effektives alpha > 0,0025 unter Stress-Nuisance, dann bleibt Stress bindend (Nachtrag)" | PRD_ANALYSE 9.1 P-7 Default "Stress bindend behalten" (angenommen "mit den Default-Vorschlaegen", DEC-104 Anlass); OC (g): "die drei Festlegungen ... bleiben unter 3.1 stehen (P-7-Default)"; DEC-104 N2 (3) rechnet A2 "mit allen Festlegungen" (Stress +2,4 bp); N2 weist kein effektives alpha unter Stress-Nuisance fuer A2 aus | VR-e07, 4.2 | N (Nachtrag O) |
| WD-04 | DEC-104 E3 (a): "fuer die Klasse W rechnet die Kurve mit der Gauss-konsistenten Kante (K-1: E[r sign(s)] = IC x 0,798 sigma ...)"; DEC-105 (8): IC_min 0,0263 / 0,0175 / 0,0108 "gilt als SESOI-Kurve der Klasse W/Tageshorizont"; DEC-104 N2 (3): Klasse W "gegen SESOI 0,040" | PRD_ANALYSE Nachtrag 3: "Der Einzelpositionsrahmen (0,0263 / 0,0175 / 0,0108 ...) bleibt fuer Klasse E/P; fuer Klasse W ist der Dezil-Rahmen massgeblich" (0,0085 / 0,0056 / 0,0035); IK-10 danach "nicht testbar" statt "an der Kante" | VR-c03, VR-c04, 4.3, 4.9 | N (Auslegung E3), Vorschlag O |
| WD-05 | DEC-104 E0: "gilt prospektiv fuer Registrierungen ab dem ersten Kohorten-Stichtag 2027-01-01" | DEC-104 E9: "F5 Generator und Takt (erste Kohorte vor 2027-01-01 registriert)"; E4 (f): "alle vor dem Stichtag registrierten Hypothesen teilen dieselben K- und V-Scheiben"; N2 (8): "eine am 2027-01-01 registrierte Hypothese" | VR-d13, Geltung "ab K1" | N/O |
| WD-06 | DEC-104 E2: "(DEC-94 (1), (4) bleiben)"; E10: "DEC-94 (1), (4), (5)" unberuehrt; E2 ersetzt DEC-94 (6) | DEC-94 (2), (3), (7), (8), (9) sind fuer 3.1-Registrierungen nicht erwaehnt (insbesondere (9) Doppelausweis unter A3-Praxis; (2) strengeres alpha bei festem alpha_test) | VR-b07, VR-b13 (VR-b04, VR-b08, VR-b12 inhaltlich fortgefuehrt) | O (Klarstellung) |
| WD-07 | PRD 5.4: ">= 8 vollstaendige Verfallzyklen (Quartale = 2 Jahre) ueber zwei disjunkte Haelften"; Power-Zeile N_cluster = 8; Gate "in beiden Haelften" | PRD 5.4: "Gate-Lauf in 12+ Monaten"; DEC-59: "erst nach >= 12 Monaten Quote-Aufzeichnung registrierbar"; DEC-105 (12) | 4.4 | N (Vorschlag DEC-105 (12)) |
| WD-08 | PRD 3.4: "DEC-58 (Entwurf) - Registry-Format 3.0"; PRD 6: "DEC-59 (Entwurf) - Kostenkonstanten-Modul und constants_hash"; PRD 9.3 Nr. 5: beide "beschliessen" | `state/decisions.md`: DEC-58 = Wissenschafts-Exkurs, DEC-59 = Welle-1-Vorfragen; Registry H-28..H-30 Pflichtzeile 6: "die Werkzeug-DEC ist offen (PRD 3.4 nennt sie DEC-59, im Log ist DEC-59 anders belegt)"; VR-c01 setzt ein "registriertes Kostenmodell (constants_hash)" voraus, `tradability3` ist nicht gebaut | 3.1, VR-g14, VR-c01 | O (Nummer, Bau), N falls Regelwirkung |
| WD-09 | DEC-104 E3 (c): "Richtung und Groessenordnung einer Registrierung duerfen aus Zone-X-Schaetzern kommen" | DEC-104 N2 (6): "Zone-X-Schaetzer bestimmen Richtung und Etikett, nie die Fallzahl" (Verschaerfung, sofort) | VR-c06, VR-f09 | O (Klarstellung) |
| WD-10 | DEC-58 E4: "Ohne Primaerbeleg der Zeitlage der Umkehr relativ zu 08:00 UTC (V-5c) ist A2s Richtung nicht registrierbar"; PRD 5.2: "Vorbedingung der Registrierung: V-5 belegt eine Effektgroesse"; DEC-103 E2: Richtung negativ "[sek]" | DEC-104 E3 (b): "Literatur wird Etikett ... ohne Blockadewirkung; die PRD-Vorbedingung 'belegter Literatur-Prior vor jeder Registrierung' entfaellt fuer 3.1"; DEC-98 N2 (3): "V-5c primaer belegt" (Delivery-TWAP), Groesse von r_pre UNBELEGT | VR-e10, 4.2 | N |
| WD-11 | DEC-98 E2: "Kein H-26-Lauf ohne neue DEC nach der Reihenfolge-Entscheidung des Nutzers" | DEC-104 E4 (f): Reihenfolge-Frage "gegenstandslos (P-8)"; E10: "H-26 gesperrt (DEC-98 E2)"; Lueckengrenze 60/30 min offen (DEC-98 N4 (b)) | 4.8 | N |
| WD-12 | PRD 3.6 Auflage (1): jeder P-A-PASS ist "PARK, nicht WEITER"; "Kein Kapitalschritt folgt" | PRD L-12: "Eine Hypothese, deren bestmoegliches Ergebnis nichts entscheidet, darf nicht eingeplant werden"; Kritik K-12: "Klasse P endet per Verfassung in PARK (L-12 verletzt)" | VR-f13, P-10 | N |
| WD-13 | DEC-56 (3): 99-Perzentil und benannte Tage "DESIGN-PARAMETER (kein Gate, nicht variierbar)"; PRD 3.6 Auflage (4): "fuer das RISIKO ist das effektive N die Zahl der Stress-Episoden" | DEC-74 N (1): STRESS_ABS "W1 2, W2 1 Tag"; DEC-63 (3) "27 < 30"; DEC-71 Stress-Zelle leer; Kritik K-14 (d): "Der Design-Parameter wurde nie auf Erreichbarkeit geprueft"; DEC-104 E8 (d) verlangt die Pruefung | VR-g13, VR-f07, VR-f13 | O (Ausweis), N/DEC (neue Definition) |
| WD-14 | Registry-Kopf `state/hypothesis_registry.md`: "YAML-Block + die zehn Pflichtzeilen" | PRD 3.3: "Die zwoelf Pflichtzeilen"; DEC-104 E9 Erweiterung | 3.2 | O |
| WD-15 | CLAUDE.md Autonomie 3: "Niemals den Nutzer fragen, ausser: fehlende Zugriffsrechte/Secrets, Aktionen mit Geldeinsatz, destruktive Operationen" | DEC-104 E4 (g), E8 (b), E8 (c): Nutzer-Vorlagen; P-12-Selbstbindung "Lockerungen nur mit Nutzer"; PRD_ANALYSE 4.6 ("'nie fragen' steht neben einer Praxis, in der jede Programmentscheidung beim Nutzer liegt") | VR-h01 | N (CLAUDE.md) |
| WD-16 | DEC-74 (e): "p-Wert = Permutations-p des schwaecheren Fensters (Max-p), >= 10.000 Permutationen" (laut DEC-99 (6) unveraendert) | DEC-99 N1 (1): Block-Permutation "kontaminiert"; "Bindend wird deshalb vor dem Einfrieren: p_W,v aus den ... Replikaten der faktorerhaltenden Null ...; Block-Permutation ... report-only"; "Richtung: Programmkonvention (DEC-77)" - offen, ob programmweit oder nur H-32 | VR-b16, 4.3 | O |

### 5.4 Datenauftraege (Weiterleitung an Data-Harvest durch den Nutzer offen, UEBERGABE_2026-10-12 Abschn. 15)

| Quelle | Auftraege |
|---|---|
| PRD_ANALYSE 8 | (1) Marktkapitalisierung/Spot-Volumen je Coin taeglich ab 2021; (2) Inhaltsprobe `tardis/options_chain` nur Stichtage <= 2026-06-01; (3) Inhaltsprobe `deribit/publicTrade`; (4) OI-Historie aller Perps; (5) Stablecoin-Angebot; (6) Probe historische Deribit-Futures-Kurse und -Funding; (7) Negativ-Panel XRP/BNB/SOL 1-min (oder Ableitung aus `bybit/publicTrade`); (8) Probe L2 2023-2025 fuer benannte Stress-Tage; (9) Ursache des 14-Tage-Ausfallmusters, H-21-Nachladbarkeit |
| Sweep 6 | (1) Tardis-Inhaltsprobe erweitert; (2) Index-/Mark-Preis-Tageskerzen aller linearen USDT-Perps ab 2021 inkl. Delisteter; (3) Tagesaggregate aus dem Trade-Archiv fuer alle linearen Perps; (4) L2-Vorextraktion fuer eine Stichtagsliste; (5) Ausfall- und Wartungsregister; (6) Kontraktspezifikations-Historie; (7) Zusatzbegruendung fuer PRD_ANALYSE 8 Nr. 1 und 4 |
| DEC-103 E5 | `state/ANFRAGE_DATA_HARVEST_NEGATIVPANEL_2026-10-31.md` (identisch mit PRD_ANALYSE 8 Nr. 7) |

### 5.5 Nicht als Regel zuordenbar (nur Praxis, Vorschlag oder Werkzeug)

1. Ausfalltage-Budget ">= 10 % je Quartal" und Verbot von "lueckenlos"-Bedingungen ueber feste Kalenderfenster: Vorschlag
   in H21_LUECKENLISTE Abschn. 2, als "Folge" in DATENANNAHMEN Nr. 7; keine DEC.
2. Zwei SESOI-Rahmen (VR-c04): Orchestrator-Praezisierung in PRD_ANALYSE Nachtrag 3; keine DEC (WD-04).
3. Positivkontrolle in Produktionskonfiguration als allgemeine Pflicht (VR-f12): beschlossen nur fuer H-28..H-30 (DEC-89 E2)
   und H-32 (DEC-101 E8); DEC-94 (5) setzt sie voraus.
4. Hygiene-Scan auf Hostnamen/Modellnamen vor Commits analytischer Dateien: Praxis (PRD_ANALYSE 4.17, Anhang C B-21).
5. Definition der Grundfassung des Strenge-Quotienten: OC (g) [U] (VR-f05).
6. Regelmenue R1..R6 des Feasibility-Rechners F3: Werkzeug, keine Regel (PRD_ANALYSE Nachtrag 3).
7. "Erster Blick nicht vor ~26 Clustern": OC "Was folgt" 6 [U]; nicht beschlossen, nicht aufgenommen.
8. IK-01/IK-02 als "Vorbedingung jeder 3.1-Registrierung": [U] (PRD_ANALYSE Nachtrag 1 (2)); als Regel nur mittelbar ueber
   VR-c01 (registriertes Kostenmodell).
9. Liste "Nicht ohne Nutzer" (PRD_ANALYSE 9.2, Schlussabsatz): keine DEC; teilweise durch VR-h05 gedeckt.
10. Anwendbarkeit der Provenienz-Regel (VR-g12) auf Data-Harvest-Stroeme: nicht geregelt; Ersatzpraxis monatlicher
    Stromcheck (PRD_ANALYSE 9.2 Nr. 10).
11. 8-Wochen-Listing-Regel (VR-g10): Ersatz durch IK-07 nur vorgeschlagen (Sweep 3.0).
12. Unklarheiten des Konto-Inventars W-05/W-18 (Kalenderlage einiger 2.0-Fenster), W-20 (sigma_LS signal-agnostisch oder
    sortiert), W-21 (H-11-Backfill-Lesart), O-132 (WP-5-Snapshot): offen, "keine Entscheidung noetig vor Kohorte 1"
    (DEC-104 N1 (12)).
13. Sunset-Review (PRD 8.3): offen laut Faktenblatt E.13, kein DEC; Stand der monatlichen Fortschreibung des Stress-Kanons
    (DEC-55): in der gelesenen Akte kein Eintrag gefunden.

---

## 6. Anhang: Errata

### 6.1 DEC-105 vollstaendig (Rechen- und Lesartkorrekturen; neutral; Orchestrator; append-only, Originaltexte unveraendert)

| Nr | Fundstelle | alt | neu | Wirkung (laut DEC-105) |
|---|---|---|---|---|
| 1 | PRD 9.2 K-0.1; Review R4 1.2.d (Horizont-Friktions-Kurve) | Kante je Position `(2/pi) arcsin(IC) x 0,798 sigma`; Mindesthorizont p 0,55 Taker 6,65 h; Wochen-IC 0,05 Taker 2,73 Tage; Break-even Wochen-IC Taker 0,031; oekonomisches IC-Minimum 0,062; "~7 h (Maker)"; "Abstand zum Prior 0,03 halbiert" | unter bivariater Normalitaet `IC x 0,798 sigma` (Pearson) bzw. `2 sin(pi IC/6) x 0,798 sigma` (Rang); Faktor pi/2 = 1,571 bei IC 0,05 (Rang pi^2/6 = 1,645); Monte Carlo 4 Mio.: 0,0397 gegen PRD 0,0254 [R]; 2,72 h; 1,11 Tage; 0,020; 0,040; mit der PRD-eigenen Formel 8,67 h (Gauss-konsistent 3,5 h); ein Drittel (0,032 -> 0,010); K-0.1 als Kurvenschar (Kante x Signal-Persistenz x Kosten); L-18-Vermerk | Missionszeile "kein Kandidat unter Tageshorizont" steht auf Faktor ~2,5 (Modell) x ~4 (Kosten); Stundenhorizonte zu oeffnen bleibt Nutzerfrage (D.4, D.12, D.14); kategorialer Rest nicht geheilt |
| 2 | PRD 3.6 (Lo-Beispiel) | SR 2,0: "exakt 1,80 statt 1,55 Jahre" (gerechnet mit q = 12) | mit q = 365: T_min(SR 2) 1,55 Jahre; der Satz "Fehler klein" trifft mit 16 % zu | festgehalten: der Praemientest ist dieselbe Arithmetik (t = SR_eff x sqrt(n)); C.10 mit 12 Monaten verlangt SR_eff >= 2,49 je Fenster (1,76 bei 2, 1,44 bei 3 Jahren) [R] |
| 3 | PRD 9.2 K-0.6; PRD 3.5 | "0,42^2 = 0,18, Faktor 4,7" | `Phi(1,4 - 1,6449)^2 = 0,163`, Faktor 5,2 [R] | C.10 ist noch teurer als angegeben |
| 4 | DEC-52-Fehlerrate (PRD 3.5) | 0,5 % (Unabhaengigkeitsannahme) | H0-Rate des DEC-52-Gates (z 2,3263 gepoolt plus Screens) 0,99 % ohne / 0,85 % mit Screens [R] | kein Lauf betroffen (DEC-52 nie angewandt); mit z 2,5287 nach DEC-94 (1) 0,50 % (OC (0)) |
| 5 | PRD 4.1; DEC-67 B2 (WP-7-Rauschboden) | "SD_null per Permutation enthaelt die effektive Breite exakt" | Permutations-Spearman hat Varianz 1/(K-1) unabhaengig von der Renditestruktur (Identitaet; DEC-74 hielt sie fest; MC K 200 mit/ohne Faktor 0,0722 / 0,0718 gegen 0,0709 [R]); Breite wirkt nur ueber die Zeitreihen-SD von IC_t (GL-035: 2,3..2,6x gegen die faktorerhaltende Null) | Feasibility-Befund B2 "Klasse W testbar" war ein Falsch-Positiv; GL-032 steht als Feststellung |
| 6 | PROGRAMM_BILANZ 2.3 und Referenztabelle (H-27/VRP); ebenso KRITIK_PRD K-7, Abschn. 8; ARCHITEKTUR_AUTOMATION 3.5 | Prior pi-2 zentral 9,47 VP; 672 Tage je Fenster; "voll 2030-04-04" | 7,14 VP (Band 3,16..10,48; DEC-98 N2); 1.183 Tage (oberer Rand 549, unterer 6.040); Ende 2032 (oberer Rand 2029-07) [R] | GL-034 und die A1-Zeile unveraendert |
| 7 | DEC-103 N1 (9), Lesart der A2-Kette (W2) | Null-Faktor-Schritt "Rechenartefakt, zu streichen" (Formulierung des Orchestrators 2026-11-01 vormittags; zurueckgenommen) | Kette 18,8 -> 19,7 (P3fix bindend) -> 23,1 (drei Placebos) -> 24,4 (Null-Faktor im Produkt) -> 27,2 (Stress bindend) -> 29,3 (skalierte Null) -> 32,1 bp (Gate-(4)-Faktor); Null-Faktor-Schritt zu 0,5..0,6 bp Rechenartefakt der Produktregel bei Korrelation 0,82 (W2) / 0,91 (W1): exakt 22,93 / 23,77 gegen Produkt 23,43 / 24,36; zwei Bedingungen je Power 0,90: exakt 0,858 / 0,870 statt 0,81 [R] | Doppelausweis ab sofort (exakte Konjunktion neben dem Produkt in jeder A2-Zahl); Zuordnungsgrundlage wechselt mit DEC-104 E7 ab K1 |
| 8 | Kostendeckung je Tag (Grundsatzanalyse T-9; Orchestrator-Vorrechnung 2026-11-01) | "Umschlag 1,0 / 0,5 / 0,33"; "voller Tagesumschlag 0,053" | Vorzeichenwechselrate `arccos(phi)/pi` = 0,500 / 0,333 / 0,205 bei phi 0 / 0,5 / 0,8; IC_min Taker 11 bp 0,0263 / 0,0175 / 0,0108; Maker 4 bp 0,0096 / 0,0064 / 0,0039; gesamt 15 bp 0,0359 / 0,0239 / 0,0147 [R]; 0,053 entspricht phi = -1 und ist keine Obergrenze | gilt als SESOI-Kurve der Klasse W/Tageshorizont (DEC-104 E3 (a)) bis zur Messung der Persistenz je Praediktor (WD-04) |
| 9 | PRD Par. 1 (Pivot-Begruendung) | (fehlend) | zu ergaenzen: der dominante 2.0-Fehlermodus "kein Signal" (H-03 Surrogate-p ~1,0, H-09 Rauschmuster, H-24 Vorzeichen) wird durch den Horizontwechsel nicht adressiert; an der Friktion starben nur H-04b/H-05c; die Wand ist VIP0-Taker mit ~4 bp ungemessener Slippage; Gebuehrenstufe des Nutzers offen (P-11); "2.0 starb an der Friktionswand" ist kein PRD-Zitat (Review B-13) | eingearbeitet in 1.1 Nr. 3 |
| 10 | Kompendium D.17; Dateninventar | D.17: Options-Chain-Kandidaten "Tardis-Sampling nur 2 Tage/3 Monate, endgueltig tot" | `tardis/options_chain` mit 91 Monatsstichtagen 2019-04..2026-10 (87 vor dem Siegel); D.17 beruht auf der Dichte (1 Stichtag je Monat) und bleibt fuer dichte Ketten-Kandidaten gueltig; neu ist nur die Tiefe | monatliche Skew-/Term-/VRP-Designs waeren neue Hypothesen nach C.8-Inhaltsprobe (nur Stichtage <= 2026-06-01) |
| 11 | Eigene Aussagen des Orchestrators (Chat 2026-11-01 vormittags) | "H-26 datenseitig laengst entsperrt"; "H-21 nie entsperrbar" | H-26 nach DEC-98 N4 (b), strenge Lesart, erst 2027-04-06; H-21 "in der registrierten Form nicht entsperrbar" (W1: 13 Fehltage `allLiquidation` BTC und ETH 2026-07-06..07-16, 08-01, 08-14; einer in `publicTrade` ETHUSDT 2026-09-21; W2 bisher 33/33 bis 2026-10-31; Nachladbarkeit [V] nicht gegeben) | formale Schliessung nach Data-Harvest-Antwort (`state/H21_LUECKENLISTE_2026-11-02.md`) |
| 12 | PRD 5.4 (A4) | "8 Quartale" gegen "12+ Monate" | Widerspruch festgestellt; Aufloesung im PRD-v3-Entwurf (Vorschlag: Fensterlaenge als abgeleitete Groesse nach DEC-104 E5) | bis dahin keine A4-Registrierung moeglich (WD-07) |
| 13 | Zahlwoerter in den Anhang-Analysen | "14 Monate 3.0"; "sechs Gate-Eintraege"; uneinheitliche GSD-Erwartungswerte | zwei Monate (PROGRAMMENTWURF Stand 2026-09-02); fuenf (GL-035 ist der H-32-Pilot); E[N bei H1] 0,814 (alpha 0,05) / 0,871 (alpha 0,0025), Maximum 1,035 / 1,007 (O'Brien-Fleming, 4 Blicke, Power 0,80) [R] | - |

**DEC-105, weitere Teile:** "Vorgemerkt, nicht korrigiert (Nutzer): Modellbezeichnungen in `CLAUDE.md` (Modellpolitik) und
PRD 3.9 durch Rollen ersetzen (oeffentliches Repo); 'eine Datei, eine Wahrheit' fuer die Verfassung -> PRD v3" (5.2);
Pflicht-Berichtszeile (VR-f02); Datenannahmen-Register (VR-g15).

### 6.2 Weitere Errata in der Akte (Verweis; jeweils append-only gefuehrt)

| Fundstelle | Inhalt | Quelle |
|---|---|---|
| DEC-86 (W1-Gewinnerzahlen) | W1-Gewinnerlauf rechnete mit der W2-Kalibrierung; Zahlen ungueltig, Methodenentscheidung bleibt | DEC-86 Nachtrag |
| DEC-88 Power-Zuordnung | mit Boden-SE statt registrierter SE gerechnet; Power ueberschaetzt | DEC-91, DEC-92 |
| PROGRAMM_BILANZ 2.3, 2.7, 2.8, Teil C Option 3 (HF-RV) | Bilanz-Zeilen "HF-RV 442,9 / 292,4 Tage" mit SE_null 1,39; ersetzt durch die Messung | DEC-98 N5 (1) (A-4) |
| PROGRAMM_BILANZ 2.4, 2.7 (A2) | SE(Delta) 7,34 / MDE80 18,25 bp statt 5,13 / 12,8 (woechentlich); 19,70 / 49,0 statt 11,28 / 28,0 (monatlich) | DEC-98 N7 (6) |
| WP-7-Zensus, WP-12-Fixture, v5e-Kalibrierung, A1-/H-27-Nuisance | auf unvollstaendigem Panel gerechnet (45 delistete Perps fehlten); Erratum-Etikett, keine Neuberechnung | DEC-100; DEC-100 N1 (5) |
| DEC-100 N1 "Panel vollstaendig" | gilt nur fuer lineare USDT-Perps; USDC-Perps und datierte Futures im Ueberlebenden-Baum | DEC-100 N2; DEC-101 Teil 1 B-1; GL-Vermerk 2026-10-21 |
| H-32-Entwurf | K W1 +15/+21,5/+22; Null-Mittel richtungstragend; A3-Praxis-Schwellen; F-WEEK-Doppelausweis m = 7 + 4 + Welle | DEC-101 Teil 1 (Errata B-9) |
| H-32-Registrierung | v6b mit Commit 6e4b447, Registrierung 117dc02; A3-Praxis auf x_P mit Gutschrift; Endpower-Tabellen strenge Untergrenzen | DEC-101 Teil 2 (Errata N-5) |
| DEC-104 E2 / PRD_ANALYSE K-4, 9.1 P-2 | "+8 % Daten gegen C.10 je 0,80" galt ohne Screen; mit Screen +23 / +59 / +103 % | DEC-104 N2 (2); PRD_ANALYSE Nachtrag 2 |
| PRD_ANALYSE Nachtrag 1 (IK-10) | Dezil-SESOI 0,0169 / 0,0062 galt fuer vollen Tagesumschlag; persistenzbereinigt 0,0085 / 0,0056 / 0,0035 | PRD_ANALYSE Nachtrag 3 |
| WP-11 Report | Tabellen ohne Variablenspalte; im Code behoben, Werte unveraendert | DEC-63 |
| V-1-Empirie | letzter Lauf eines Ueberlebenden zaehlt als offen; Dauern unveraendert | DEC-84 (3) |
| DEC-94-Feststellung | Liste der gesehenen H-27-nahen Groessen um die realisierte BTC-Vol der Urteilsfenster ergaenzt | DEC-95 E2 |

---

## 7. Anhang: Konkordanz PRD v2 -> v3

### 7.1 Geaenderte Altzeilen

Art: **ersetzt** (Altzeile gilt fuer kuenftige Registrierungen nicht mehr bzw. ab dem genannten Zeitpunkt nicht mehr),
**Erratum** (Zahl/Lesart korrigiert, DEC-105), **ergaenzt** (Altzeile gilt, mit Zusatz), **offen** (Widerspruch, 5.3),
**historisch/ueberholt** (erledigt oder durch Fakten ueberholt, ohne Regelwirkung). Die Altzeilen bleiben im Original
stehen (append-only); "durchgestrichen" heisst hier: in v3 nicht mehr als geltende Zeile gefuehrt.

| KO | PRD v2 Fundstelle | Altzeile (Kurzinhalt) | v3 | ersetzende / aendernde Quelle | Art |
|---|---|---|---|---|---|
| KO-001 | Kopf | bindend zusaetzlich DEC-51..57 und CLAUDE.md; bei Widerspruch gilt die DEC | 0 | DEC-58..DEC-105 | ergaenzt |
| KO-002 | Kopf | "Erstellt von" mit Modellbezeichnung | VR-h02 | DEC-105 "Vorgemerkt" | ersetzt (Rolle; Entscheid N) |
| KO-003 | Kopf | offene Nutzer-Entscheidungen Abschnitt 8 (Default (b)) | 5.2 | DEC-104 "Offen" | ergaenzt |
| KO-004 | 1 Bilanz | "einziger noch aktiver Strategie-Pfad ist die gesperrte VRP-Messung H-26" | 1.2, 4.8 | DEC-98 E2, N4 (b); DEC-102 N2 | ueberholt |
| KO-005 | 1 Vier Zahlen | Horizont-Friktions-Kurve 6,6 h / 53 min / 2,7 Tage | 1.3, VR-c02 | DEC-105 (1) | Erratum |
| KO-006 | 1 Vier Zahlen | Sharpe-Nachweisdauer, "urteilstragend ist die Praemie selbst" | 1.3, VR-f13 | DEC-105 (2) (Praemientest gleiche Arithmetik) | ergaenzt |
| KO-007 | 1 Vier Zahlen | "SD_null(IC_t) ist die bindende, UNGEMESSENE Zahl - WP-7 misst sie direkt" | 1.3, VR-b08 | DEC-105 (5) | Erratum |
| KO-008 | 1 Vier Zahlen | "DEC-52 ... greift nur, wo die Power-Zeile VOR dem Lauf Power < 0,60 ausweist" | VR-b11, VR-b14 | DEC-94 (6); DEC-104 E2; DEC-105 (3) | ersetzt |
| KO-009 | 1 Pivot | Pivot-Begruendung ueber die Friktions-Arithmetik | 1.1 | DEC-105 (9) | ergaenzt |
| KO-010 | 1 Pivot | "Welle 1 ist reiner Zensus ... null Alpha-Slots" | 7.2 | DEC-73 | historisch |
| KO-011 | 1 Pivot | "Friktionswand ... nie PASS-Bedingung eines Mess-Gates (C.2)" | VR-a02 | DEC-104 E3 (a) | offen (WD-01) |
| KO-012 | 2 L-3 | "SD_null(IC_t) ist vor jeder Registrierung zu messen (WP-7)" | VR-b08 | DEC-105 (5); DEC-94 (3) | ersetzt |
| KO-013 | 2 L-5 | Power-Zeile, Konvention DEC-51 | VR-b02, VR-b14 | DEC-94; DEC-104 E2 | ergaenzt |
| KO-014 | 2 L-13 | Stress-Kanon DEC-55/56 als Design-Parameter | VR-g13 | DEC-104 E8 (d) | ergaenzt |
| KO-015 | 2 L-18 | Dezilfaktor 3,51 als Programm-Konstante | 2i, VR-c02, VR-c04 | DEC-105 (1) L-18-Vermerk | ergaenzt |
| KO-016 | 3.1 Tabelle | C.10 hartes Ein-Fenster-Kriterium | VR-a10 | DEC-104 E2, E10 | ersetzt (ab K1) |
| KO-017 | 3.1 Tabelle | C.18 "aeltere Historie rein deskriptives Aera-Profil" | VR-a18, VR-d02, VR-d03 | DEC-99 (1), (2); DEC-104 E6 | ersetzt |
| KO-018 | 3.1 Tabelle | C.16 zweistufige FDR | VR-a16, VR-b16, VR-b17, VR-d13 | DEC-99 (7); DEC-104 E4 (f) | ergaenzt |
| KO-019 | 3.1 | "Bestaetigung zu C.2 ... v2-Verschaerfung" (Feasibility-Kill-Bedingungen) | VR-a02 | DEC-104 E3 (a) | offen (WD-01) |
| KO-020 | 3.2 | Klasse P: urteilstragend `mean(prem)`, PASS = PARK | 1.4, VR-f13 | Kritik K-12; DEC-104 "Offen" P-10 | offen (WD-12) |
| KO-021 | 3.2 | Klasse E: "Nulleffekt ist die Placebo-Verteilung auf Zufallsterminen mit identischer Kalenderverteilung" | VR-e12 | DEC-103 E4 | ersetzt (fuer A2) |
| KO-022 | 3.3 | "Die zwoelf Pflichtzeilen" | 3.2 | DEC-104 E9 | ergaenzt |
| KO-023 | 3.3.1 | DEC-51 Punkt 1: alpha 0,05 einseitig je Fenster als Urteilsregel | VR-b01, VR-b14 | DEC-104 E2 | ersetzt (ab K1) |
| KO-024 | 3.3.1 | "Zahlenwerte: einseitig z = 2,4865; zweiseitig 2,8016; einseitig bei alpha 0,01 3,1680" als Schwellen-z | VR-b06 | DEC-94 (1) | ersetzt (MDE-Faktoren) |
| KO-025 | 3.3.2 | oekonomische Mindestmagnitude als Etikett, nie Gate | PZ-02 | DEC-104 E3 (a) | offen (WD-01) |
| KO-026 | 3.3.3 | `N_eff = N_c/(1+(N_c-1) rho)` | VR-b03 | DEC-63 (2) | ergaenzt |
| KO-027 | 3.3.4 | Decke `E[max SR]` in SR-Einheiten | VR-b04 | DEC-94 (7); Kritik K-14 (b) | ersetzt |
| KO-028 | 3.3.6 | `constants_hash` ueber `tradability3/constants.py` | PZ-06, VR-g14 | (Modul nicht gebaut) | offen (WD-08) |
| KO-029 | 3.3.8 | Positivkontroll-Vorschaltung bei > 1 h | VR-f12 | DEC-89 E2; DEC-94 (5); DEC-101 E8 | ergaenzt |
| KO-030 | 3.3.10 | Stress-Episode nach DEC-55/56 | VR-g13, PZ-10 | DEC-104 E8 (d) | ergaenzt (WD-13) |
| KO-031 | 3.3.11 | Ergebnis-Artefakt-Zeile DEC-53 | VR-f03, VR-f02 | DEC-104 E1; DEC-105 | ergaenzt |
| KO-032 | 3.4 | "DEC-58 (Entwurf) - Registry-Format 3.0"; Nummernvergabe DEC-58/DEC-59 | 3.1 | Log: DEC-58/DEC-59 anders belegt | offen (WD-08) |
| KO-033 | 3.4 | YAML-Template | 3.3 | DEC-94 (1), (2); DEC-99; DEC-104 E9 | ersetzt |
| KO-034 | 3.5 | DEC-52 (i) "< 0,60", (iv) "gepooltes alpha = 0,01" | VR-b11 | DEC-94 (1), (6) | ersetzt |
| KO-035 | 3.5 | "Faktor 4,7 mehr Retention" | 6.1 Nr. 3 | DEC-105 (3) | Erratum |
| KO-036 | 3.5 | Falsch-Positiv-Rate nach DEC-52 "~0,5 %" | 6.1 Nr. 4 | DEC-105 (4); DEC-94 (1) | Erratum |
| KO-037 | 3.5 | "Anwendung je Kandidat ... vorab fixierte Zuordnungsregel" | VR-b11 | DEC-94 (6); DEC-104 E2 | ersetzt |
| KO-038 | 3.6 | Lo-Beispiel "SR 2,0 ergibt exakt 1,80 statt 1,55 Jahre" | 6.1 Nr. 2 | DEC-105 (2) | Erratum |
| KO-039 | 3.6 | Auflage (1) "Praemien-EXISTENZ ... PARK, nicht WEITER" | VR-f13 | Kritik K-12; P-10 | offen (WD-12) |
| KO-040 | 3.6 | MaxDD-Boden als einzige Risiko-Berichtszeile | VR-f13 | DEC-58 E1 (e) (Ruin-Kapital) | ergaenzt |
| KO-041 | 3.9 | Modell- und Teampolitik mit Modellbezeichnungen | VR-h02 | DEC-105 "Vorgemerkt"; Kritik K-14 (j) | ersetzt (Lesefassung; Entscheid N) |
| KO-042 | 4 Laufort | Downloads auf der Nutzer-Maschine, Sandbox nur T0/T1 | VR-g09 | DEC-83 E1; DEC-81 E3 | ersetzt |
| KO-043 | 4 | Welle-1-Prinzip und Pakettabelle | 7.2 | DEC-73 | historisch |
| KO-044 | 4.1 | Schaetzerwechsel, Feasibility-Arithmetik, Schranken 0,08699 / 0,09657, Breiten 134 / 109 / 117 | 7.2 | DEC-105 (5) | Erratum |
| KO-045 | 4.1 DoD (4) | PIT-Universum, delistete Symbole bis zum letzten Bar | VR-g10 | DEC-100 E1; DEC-72 | ergaenzt |
| KO-046 | 4.1 B3 | Survivorship: "Klasse W laeuft nur, wenn das Survivorship-Fixture eine Verzerrung kleiner als die halbe registrierte Schwelle zeigt" | 4.3 | DEC-70 E3; DEC-73 E1; DEC-76 | ersetzt (Union-Panel; Etikett) |
| KO-047 | 4.1 | Manifest DONE / Loud-Fail, PARTIAL | VR-g11 | DEC-66 | ergaenzt |
| KO-048 | 4.2 | "WP-9 entsperrt H-26 NICHT" | 4.8 | DEC-61; DEC-98 N4 (b) | ergaenzt |
| KO-049 | 4.3 | WP-10(A) "Groessenordnung 6-10 Episoden" | 7.2 | DEC-62 (Erwartung falsch) | ueberholt |
| KO-050 | 4.3 | FDR-Wirkung abhaengigkeitsrobust | VR-b16 | DEC-62 E3; DEC-65 (3) | ergaenzt |
| KO-051 | 4.4 | V-1..V-5 | 4.1, 4.2, 4.4 | DEC-59; DEC-82; DEC-84; DEC-98 N2 (3); DEC-103 | historisch |
| KO-052 | 5.1 | Hypothese "dollarneutrales Dezil-Long-Short-Portfolio" | 4.1 | DEC-70 E1 | ersetzt |
| KO-053 | 5.1 (a) | "Der Anker-Beitrag zum Nulleffekt ist exakt 0" (I kuerzt sich heraus) | 4.1 | DEC-59 (Totzonen-Modell; notwendig, nicht hinreichend) | ergaenzt |
| KO-054 | 5.1 (b) | 1h/8h-Heterogenitaet; "A1 nur auf der homogenen 8h-Klasse" | 4.1 | DEC-59 (4h/8h); DEC-84 (1); DEC-58 E3 | ersetzt |
| KO-055 | 5.1 | Sortierschluessel "intervall-normierter Funding-Satz der letzten 3-7 Tage" | 4.1 | DEC-67 E2 | ersetzt |
| KO-056 | 5.1 | Fenster "je 52 Wochen" | VR-d01 | DEC-74 (W1 53 Wochen); DEC-99 (8) | ersetzt |
| KO-057 | 5.1 | Power-Zeile `N_eff` = 52 je Fenster, 104 gepoolt | 4.1 | DEC-67 E4; DEC-94 (4) | ersetzt |
| KO-058 | 5.1 | Zuordnungsregel `P_fenster`; "Schwelle ... mit dem z des registrierten Fenster-Regimes" | VR-b06, VR-b11 | DEC-94 (1), (6); Kritik K-14 (c) | ersetzt |
| KO-059 | 5.1 | Selektions-Decke K = 3: 0,60 (SR) | VR-b04 | DEC-94 (7) | ersetzt |
| KO-060 | 5.1 | Kill (4): Funding-Autokorrelation < 0,30 | 4.1 | DEC-58 E1 (e); DEC-67 E3; DEC-70 E1 | ersetzt |
| KO-061 | 5.1 | Etikett `sigma_LS <= 104 / 116`; "Bedingung aus Welle 1" | 4.1 | DEC-70; GL-033; DEC-104 E3 (e) | ersetzt |
| KO-062 | 5.2 | Richtung "wird mit der Ereignismenge zusammen registriert" | VR-e10 | DEC-103 E2; DEC-58 E4 | ergaenzt (WD-10) |
| KO-063 | 5.2 | Volatilitaetskette 2,5 % -> 51 bp -> 36 bp (BTC-only) | VR-e15, 2i | DEC-98 N7 (2) | ersetzt |
| KO-064 | 5.2 | `rho(BTC, ETH)` Arbeitswert 0,8 [sek] | 2i | DEC-67 E4 (0,815) | ersetzt |
| KO-065 | 5.2 | Placebo-Bindung P1/P2/P3 | VR-e11 | DEC-103 E3 | ersetzt |
| KO-066 | 5.2 | Tabelle A2-P1 (woechentlich / monatlich) | VR-e09 | DEC-103 E1, E8; DEC-98 N7 (3) | ersetzt |
| KO-067 | 5.2 | "Schwelle = max(95-%-Quantil; 2,4865 x SE(Delta))" | VR-e12 | DEC-103 E4; DEC-94 (1) | ersetzt |
| KO-068 | 5.2 | struktureller Nulleffekt = Zufallstermine identischer Kalenderverteilung | VR-e12 | DEC-103 E4 | ersetzt |
| KO-069 | 5.2 Gate (4) | Negativ-Panel XRP/BNB aus Realdaten | VR-e13 | DEC-103 E5 | ergaenzt |
| KO-070 | 5.2 | Fenster W1 2024-09-01..2025-08-31, W2 2025-09-01..2026-08-31 | VR-e15 | DEC-99 (8); DEC-103 E7, E8 | ersetzt |
| KO-071 | 5.2 | "Vorbedingung der Registrierung: V-5 belegt eine Effektgroesse" | VR-c05, 4.2 | DEC-104 E3 (b) | ersetzt (ab K1; WD-10) |
| KO-072 | 5.2 | "bindend ist der Placebo mit dem groessten SE"; Fenster-Regime je Ereignismenge | VR-e04, VR-e11 | DEC-98 N7 (4a); DEC-103 E3; DEC-104 E7 (a) | ersetzt |
| KO-073 | 5.3 | Status "streng konditional"; "A3 laeuft unter C.10 hart" | 4.3 | GL-032; DEC-92 | ersetzt |
| KO-074 | 5.3 | A3-R Gap-Design "um einen Tag getrennt" | 4.3 | DEC-87 (B) (eine Woche, registrierte Abweichung) | ersetzt |
| KO-075 | 5.3 | Schwelle `IC_min = 2,4865 x SD_null/sqrt(52)` | VR-b06 | DEC-74 (a); DEC-75 (1); DEC-94 (1) | ersetzt |
| KO-076 | 5.3 | Fenster W1/W2 je 52 Wochen | VR-d01 | DEC-74; DEC-99 (8) | ersetzt |
| KO-077 | 5.3 Gate (2), (3) | Persistenz-Null und BH als PASS-Bedingungen | 4.3 | DEC-75 (6) (report-only) | ersetzt |
| KO-078 | 5.3 | adversariales Beta-Fixture | 4.3 | DEC-75 (3); DEC-86 | ergaenzt |
| KO-079 | 5.3 Kill (3) | Survivorship nicht rekonstruierbar UND Fixture-Verzerrung >= halbe Schwelle | 4.3 | DEC-76 (Etikett, Union-Panel) | ersetzt |
| KO-080 | 5.3 | `IC_prior = 0,03` [sek: R2 0.3C] | VR-c05, 4.3 | DEC-98 N2 (1); DEC-104 E3 | ersetzt |
| KO-081 | 5.4 | Fenster ">= 8 vollstaendige Verfallzyklen" gegen "Gate-Lauf in 12+ Monaten" | 4.4 | DEC-59; DEC-105 (12) | offen (WD-07) |
| KO-082 | 5.4 | Schwelle `2,4865 x sigma_w/sqrt(N_cluster)` | 4.4, VR-b06 | DEC-94 (1) | ersetzt |
| KO-083 | 5.4 | Datenlage und "moeglicherweise RECORDING-FIRST" | 4.4 | DEC-59; DEC-98 N4 (a) | ersetzt |
| KO-084 | 5.5 | "deribit/tickers ~38 Tage ... reicht fuer kein urteilstragendes Fenster" | 4.5 | DEC-105 (10); DATENANNAHMEN Nr. 4 | ergaenzt |
| KO-085 | 5.5 (a) | Delivery-/Exercise-Gebuehr V-4 offen | 4.5 | DEC-74 N (3) [sek] | ergaenzt |
| KO-086 | 6 | "DEC-59 (Entwurf) - Kostenkonstanten-Modul" | VR-g14 | Log: DEC-59 anders belegt | offen (WD-08) |
| KO-087 | 6 | Konstantenliste `constants.py` | VR-g14, 2i | DEC-67 E4; DEC-71; DEC-78; DEC-74 N (3) | ergaenzt |
| KO-088 | 7.1 | Backfill-Tabelle, Rate-Limit-Arithmetik, Laufzeiten | 7.2 | DATENANNAHMEN Nr. 1; DEC-81 E3; DEC-83; DEC-84 | ueberholt |
| KO-089 | 7.1 | Provenienz-Regel (monatlich 1 %) | VR-g12 | - | ergaenzt (5.5 Nr. 10) |
| KO-090 | 7.2 | Harvester-Liste (PIT-Roster "grundsaetzlich nicht nachholbar"; OI-Probe) | 7.2 | DATENANNAHMEN Nr. 2, 3; DEC-98 E3 | ueberholt |
| KO-091 | 7.3 | Rechenbudget CPU-first; "Nicht machbar auf diesem PC" | VR-h06, VR-g09 | DEC-83 | ergaenzt |
| KO-092 | 8.1-8.3 | offene Nutzer-Entscheidungen | 5.2 | DEC-73 E5; DEC-104 "Offen" | ergaenzt |
| KO-093 | 9.1 | Tabelle nicht aufgenommener Kandidaten | 7.2 (Verweis) | - | unveraendert (Akte) |
| KO-094 | 9.2 A, B | Programm-Konstanten | 2i | DEC-105 (1)-(3), (5) | Erratum |
| KO-095 | 9.2 C | WP-7-Schranken, A1-Etikett, A2-Varianten, A3-Power, Falsch-Positiv-Rate, Rate-Limit, Backfill-Zeit | 2i, 7.2 | DEC-105 (4), (5); GL-032; DEC-98 N7 (6); DEC-83 | ueberholt |
| KO-096 | 9.3 | Beschluss- und Bau-Reihenfolge 1-8 | 7.2, 4.5 | DEC-73; WD-08 (Nr. 5); Nr. 8 in 4.5 | historisch (Nr. 5 offen, Nr. 8 uebernommen) |
| KO-097 | 10 | Aenderungsprotokoll v1 -> v2 | 7.2 | - | historisch |
| KO-098 | 11.1 | Null-Zensus-Klausel | VR-f10 | DEC-58 E2 | ergaenzt |
| KO-099 | 11.2, 11.3 | erweiterte Vorfragen, WP-7-Pflichtzeilen, Competing-Risk, WP-11 | 7.2, 4.1, 4.2 | DEC-59; DEC-60; DEC-63; DEC-82; DEC-84 | historisch |
| KO-100 | 11.4 | A1-/A2-Auflagen; Ruin-Kapital | 4.1, 4.2, VR-f13 | DEC-58 E1 (e), E3, E4 | ergaenzt |

### 7.2 In v3 nicht uebernommene v2-Passagen (Grund)

| PRD v2 | Grund |
|---|---|
| Par. 1 "Welle 1 ist reiner Zensus" und Par. 4 vollstaendig (Prinzip, Laufort, WP-7, WP-9, WP-10, V-1..V-5: Ziele, Endpunkte, DoD, Testpflichten, Aufwand, Befund-Tabellen) | Welle 1 abgeschlossen (DEC-73); Befunde DEC-59..DEC-72; dauerhafte Regeln daraus stehen in VR-g10, VR-g11, VR-b16, VR-f11; Rechengrundlage teils widerlegt (DEC-105 (5)) |
| Par. 2 Lehren L-1..L-18 als Tabelle | Lehren bleiben Akte; ihre Regeln: L-1 VR-a06, L-2/L-2b VR-a04, L-3 VR-b03/VR-b08, L-4 VR-a02, L-5 VR-b02/VR-b08, L-6 VR-b03, L-7 VR-b16, L-8 VR-a07, L-9 VR-a08, L-10 PZ-07, L-11 VR-a13/VR-f12, L-12 PZ-02/VR-h06, L-13 VR-g13, L-14 VR-g14, L-15/L-16 PZ-09, L-17 VR-f03, L-18 2i/VR-c02 |
| Par. 5 Herleitungs- und Begruendungstexte (Evidenz, Literatur, "Warum dieser Kandidat", Etiketten-Korrekturen, Rechentabellen) | bindend ist die Fassung je Kandidat in Abschnitt 4; die Herleitungen bleiben Akte |
| 7.1 Backfill-Plan, Rate-Limit; 7.2 Harvester-Prioritaeten | durch Datenlage ueberholt (DATENANNAHMEN Nr. 1-3; DEC-81 E3; DEC-83; DEC-84); Provenienz-Regel bleibt (VR-g12) |
| 9.1 nicht aufgenommene Kandidaten | als Verweis unveraendert gueltig (Begruendungen je Kandidat); keine Regel |
| 9.2 C (ausser in 2i genannten Groessen) | ueberholt (KO-095) |
| 9.3 Beschluss- und Bau-Reihenfolge | abgearbeitet (DEC-73); Nr. 5 offen (WD-08); Nr. 8 in 4.5 |
| Par. 10 Aenderungsprotokoll v1 -> v2 | historisch |
| 11.2, 11.3 | erledigt (DEC-59, DEC-60, DEC-63, DEC-82, DEC-84) |

---

## 8. Pruefliste fuer den Beschluss

### 8.1 Was der Nutzer mit je einem Satz bestaetigt oder entscheidet

| Nr | Satz zur Bestaetigung (oder Gegenentscheid) | Bezug |
|---|---|---|
| BE-01 | "PRD v3 wird als konsolidierte Lesefassung der Verfassung angenommen und als neue Datei abgelegt; PRD v2 und decisions.md bleiben unveraendert; bei Widerspruch zwischen v3 und einer spaeteren DEC gilt die DEC." | 0; K-14 (g) |
| BE-02 | "Fuer die Konfirmationsregel gilt Variante (a) / (a') / (a'') / (c)." (E2-Vorbehalt verlangt die Nachfuehrung vor der ersten Registrierung) | 2b P-2; DEC-104 N2 (4) |
| BE-03 | "Die C.2-Ausdehnung auf Feasibility-Kill-Bedingungen gilt fuer 3.1 fort / ist fuer die SESOI-Feasibility zurueckgenommen." | WD-01 |
| BE-04 | "Fuer 3.1-Registrierungen bindet das juengste Vorfenster (E6) / bleibt DEC-94 (5) (groessere SE inkl. stress) bindend; fuer A2 bleibt Stress bindend / wird Sensitivitaetszeile." | WD-02, WD-03 |
| BE-05 | "Die SESOI der Klasse W rechnet im Einzelpositionsrahmen (E3 (a), DEC-105 (8)) / im Dezil-L/S-Rahmen (PRD_ANALYSE Nachtrag 3)." | WD-04 |
| BE-06 | "Eine vor dem 2027-01-01 fuer Kohorte 1 registrierte Hypothese steht unter Verfassung 3.1 / unter 3.0." | WD-05 |
| BE-07 | "Die A4-Fensterlaenge ist eine abgeleitete Groesse nach E5 (Vorschlag DEC-105 (12)) / bleibt >= 8 Verfallzyklen." | WD-07 |
| BE-08 | "DEC-58 E4 (Richtungsbeleg V-5c) gilt fuer A2 unter 3.1 fort / ist durch E3 (b) zum Etikett geworden." | WD-10 |
| BE-09 | "H-26 bleibt gesperrt bis <Bedingung>; Lueckengrenze 60 / 30 min." | WD-11 |
| BE-10 | "Klasse P ist Mess-/Aufzeichnungsprogramm (P-10-Default) / bekommt eine Kapitalregel ohne MinTRL." | WD-12, P-10 |
| BE-11 | "CLAUDE.md Autonomie 3 wird um die Nutzer-Vorlagen aus DEC-104 (E4 (g), E8 (b), E8 (c), P-12) ergaenzt." | WD-15 |
| BE-12 | "Modellbezeichnungen in CLAUDE.md und PRD 3.9 werden durch die Rollen Orchestrator, Herleitung, Review, Bau, Kartierung ersetzt." | VR-h02; DEC-105 |
| BE-13 | "Zu P-11, P-12, P-13, TOST, Enrichment, PRD 8.2 und 8.3 gelten die in 5.2 genannten Defaults bis auf: <...>." | 5.2 |
| BE-14 | "Die Datenauftraege aus 5.4 werden an Data-Harvest weitergeleitet (ganz / teilweise: <...>)." | 5.4 |

Vom Orchestrator per DEC zu klaeren (Entscheider O nach 5.3; ergibt eine Klaerung eine Lockerung, geht sie nach VR-h05 an den Nutzer): WD-06 (Status
DEC-94 (2), (3), (7)-(9) ab K1), WD-08 (Nummer und Bau der Werkzeug-Entscheidungen Registry-Format/Kostenmodul), WD-09
(E3 (c) gegen N2 (6)), WD-13 (Ausweis der STRESS_ABS-Erreichbarkeit), WD-14 (Registry-Kopf), WD-16 (p-Wert-Methode Klasse W).

### 8.2 Was der Orchestrator nach dem Beschluss tut

1. **DEC-Eintrag** "PRD v3 angenommen" (Etikett neutral, Entscheider N) mit den Antworten BE-01..BE-14; je offener
   Klarstellung (WD-06, WD-08, WD-09, WD-13, WD-14, WD-16) ein DEC-Nachtrag; nach BE-02 der E2-Nachtrag (DEC-104 E2, Vorbehalt).
2. **CLAUDE.md-Kurzfassung** (`scinance3-impl/CLAUDE.md`; Aenderungen an CLAUDE.md sind Nutzerentscheidungen, PRD_ANALYSE
   9.2 Schlussabsatz) nachfuehren: Massgebliche Dokumente (v3 aufnehmen); "Die vier Zahlen" nach 1.3; Zeile "C.10 (hartes
   Ein-Fenster-DROP, ausser DEC-52 greift)" und Zeile "DEC-52 ... Per-Fenster-Power < 0,6, gepooltes alpha 0,01" nach
   VR-b11/VR-b14; "Zwoelf Pflichtzeilen" nach 3.2; Zustandsmaschine nach VR-h09; Modellpolitik nach BE-12; Arbeitsregel 4
   mit Geltung "bis K1" und VR-c07 ab K1; Testpyramide "Nutzer-PC: alle Netz-Backfills" nach VR-g09; Autonomie 3 nach BE-11.
   Einstiegszeiger der Repo-Wurzel-`CLAUDE.md` um v3 ergaenzen.
3. **Registry-Template:** Nachtrag im Kopf von `state/hypothesis_registry.md` (append-only): YAML 3.1 (3.3) und
   Pflichtzeilen PZ-01..PZ-30 (3.2) fuer Registrierungen ab K1; Kopfzeile "zehn Pflichtzeilen" per Vermerk berichtigen (WD-14).
4. **Linter F1:** JSON-Schema der Pflichtzeilen PZ-01..PZ-30 mit Loud-Fail, Herleitungs-Referenz statt nacktem Skalar,
   Hash-Pin der Alt-Eintraege (3.1); Tests T0; Abnahme durch den Orchestrator (VR-h02).
5. **Feasibility-Rechner F3** auf BE-02 (Regelvariante) und BE-05 (SESOI-Rahmen) einstellen; A2-Feasibility unter 3.1
   (VR-e08) und Klasse-W-Feasibility neu ausweisen; GL-012 fuer A2 nur, "sobald (a) bestaetigt ist" (DEC-104 N2 (9)).
6. **Fensterregister und Konto** verweisen auf die v3-Regelnummern (VR-d08..VR-d20); Zone-X-Lauf Konto Nr. 1/2 nach
   Rueckkehr des Datendienstes (UEBERGABE_2026-10-12 Abschn. 15).
7. **Vermerke** an ueberholten Stellen: Kompendium E.1/E.2 (H-21, H-26; 4.7, 4.8); GL-033/GL-034 tragen das Etikett
   "strukturell nicht testbar" (DEC-104 E3 (e)); `state/DATENANNAHMEN_REGISTER.md` fortschreiben (VR-g15); UEBERGABE-Nachtrag.
8. **Vor Kohorte 1:** Kostenmodell (`constants.py`, `constants_hash`) bauen oder die Vorbedingung von VR-c01 per DEC
   klaeren (WD-08); bei BE-02 = (c) Herleitung und Review der Stabilitaetsstatistik (DEC-104 N2 (4)).

*Ende v3 (Entwurf 2026-11-02, angenommen 2026-11-04, DEC-107). Kein Abschnitt dieses Dokuments ist eine Registrierung oder
ein Verdikt; Regelaenderungen nur nach DEC-107 (6) mit Nachfuehrung in 0.1; die Akte ist `state/decisions.md`.*
