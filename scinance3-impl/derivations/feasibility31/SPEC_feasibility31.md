# SPEC F3: Feasibility-Rechner fuer Verfassung 3.1 (`feasibility31`) - Entwurf des Orchestrators 2026-11-02

Rolle: Bau (nach Spezifikation), anschliessend Abnahme durch den Orchestrator (Tests, Fingerprints). Kein Marktdatenzugriff;
der Rechner arbeitet ausschliesslich auf Nuisance-Zahlen aus der Akte (JSON/YAML) und auf Formeln.

## Zweck

Vor jeder Herleitung und Registrierung beantwortet der Rechner mechanisch (DEC-104 E3, E5, E8): Ist eine Hypothese mit der
gemessenen Nuisance gegen ihre SESOI testbar, mit welcher Fensterlaenge, in welcher Zone und ab wann? Er ersetzt die
Hand-Rechnungen der Herleitungen (A1, H-27, A2, H-32/H-33) und reproduziert deren Zahlen als Tests (ohne Neulauf von Code,
der Siegeldateien schreibt - Review B-20).

## Eingaben (eine YAML/JSON je Kandidat, Schema im Code als dataclass, loud fail bei fehlenden Feldern)

- `statistic`: Name, Einheit (bp, IC, VP), Richtung (einseitig).
- `nuisance`: SE je Cluster-Einheit oder je 12 Monate (mit Quelle: Datei, Feld, sha256), Cluster-Einheit (Woche/Tag/Ereignis),
  Beobachtungen je Jahr, Autokorrelations-/Ueberlappungsfaktor c (>= 1), optional Stress-SE (Sensitivitaets-Zeile), optional
  Null-SD (skalierte Null, k = SE/Null-SD), optional Korrelation zwischen Konjunktionsbedingungen.
- `sesoi`: Kostenkurve: Seitenkosten (Maker/Taker/gesamt in bp), Horizont (Tage), Signal-Persistenz phi (Vorzeichenwechselrate
  arccos(phi)/pi), Kante-Faktor 0,798 x sigma (Gauss-konsistent, Pearson; Rang-Option 2 sin(pi IC/6)); fuer Praemien-Statistiken
  direkt in Einheiten der Statistik. Default Taker, Etikett im Output.
- `prior`: optional Verteilung (Median, Band) mit Quelle und Etikett (primaer / [sek] / UNBELEGT / Zone-X selektionsbereinigt).
- `data`: verfuegbare Beobachtungen je Zone (X: Vorperiode; V: W1/W2; K: ab 2026-07-01 prospektiv je Jahr), Vorwissens-Klasse
  (FENSTERREGISTER Abschnitt 2), Kohorten-Stichtag.
- `design_menu`: Fensterlaengen {6, 9, 12} Monate bzw. Blickzahl {1..4}, Placebosatz-Varianten (fuer Konjunktionen).

## Ausgaben (JSON + Markdown-Tabelle; Pflichtzeilen nach DEC-104 E8)

1. MDE80 je Regime: (a) C.10 je Fenster 0,05/0,80; (b) C.10 gemeinsam 0,80; (c) **3.1: gepoolt 0,0025 + REZENZ-Screen 0,05,
   gemeinsame Power 0,80** (Korrelation Screen/gepoolt ueber den Datenanteil des juengsten Fensters); (d) GSD O'Brien-Fleming
   4 Blicke bei 0,0025 (Maximum und E[N bei H1]); jeweils zentral, Stress-Zeile, mit c.
2. Zwei Spalten **Exploration** (Zone X: Aufloesung und Ausschlussgrenze mit den verfuegbaren X-Beobachtungen) und
   **Konfirmation** (Zone V ein Blick bzw. Zone K prospektiv: Beobachtungen bis zur Power 0,80 an der SESOI, fruehester
   Entscheidungszeitpunkt ab Kohorten-Stichtag).
3. SR-Aequivalent je Fensterlaenge (Klassen-Feasibility, Kritik K-2): SR_eff noetig 2,49 / 1,76 / 1,44 bei 1 / 2 / 3 Jahren je
   Fenster (C.10) und das 3.1-Pendant.
4. Konjunktionen: exakte gemeinsame Power (Monte Carlo mit geteiltem Term, Seeds fest) neben dem Produkt (Doppelausweis,
   DEC-105 (7)).
5. Strenge-Quotient MDE80(alle Festlegungen)/MDE80(Grundfassung) mit Zerlegung je Festlegung (Kette wie DEC-105 (7)).
6. OC-Zeile: P(PASS bei 0), P(PASS bei SESOI), P(PASS bei Prior-Median) der Entscheidungsregel (analytisch + MC >= 1.000 Seeds).
7. Verdikt der Feasibility (binaer, Konsequenz vorab): testbar (MDE80 <= SESOI in Konfirmation bis Datum X) / strukturell nicht
   testbar (mit Ausschlussgrenze und Datenbedarf) / nur Exploration.
8. Pflicht-Berichtszeile (DEC-105): Felder `estimate`-Platzhalter, `upper_limit95`-Formel, `n_eff`, `c_overlap`, `selection_k`, `zone`.

## Tests (T0, pytest; alle Zahlen aus der Akte, Toleranzen angeben)

- Reproduziert: GL-033 (A1: MDE80 gegen 36 bp, Jahre je Fenster 12,8 bei SESOI; SR_eff 1,95), GL-034 (H-27: SE12 5,17 VP, Prior
  7,14 -> 1.183 Tage je Fenster; 9,47 -> 673), A2 (Einzel-Placebo 18,8; Produkt 23,43 / 24,36; exakt 22,93 / 23,77; Kette
  bis 32,1; Pilot-Uebergabe 7,1e-5 bei 16,5 bp), H-32/H-33 (fm8 SD, MDE80 je Fenster; Zahlen aus GL-035/036 und
  `state/herleitung_h33/`), Datenfaktoren 1,356 / 1,077 / 1,259, OBF 0,814 / 0,871, Max 1,035 / 1,007 (Quelle:
  `state/prd_analyse_2026-11-01/scripts/orch_review_check.out`), Persistenz-IC_min 0,0263 / 0,0175 / 0,0108.
- Determinismus (T2): zwei Laeufe bitgleich (Seeds).
- Loud fail (C.14): fehlendes Feld, c < 1, SE <= 0, Zone-K-Daten vor 2026-07-01, UNBELEGT ohne Sensitivitaetsspanne.
- Kein Zugriff auf `state/runs/`, keine Marktdaten, keine Netzwerkzugriffe (Test prueft Importliste).

## Ort und Form

`scinance3-impl/src/bybit_edge/research/feasibility31.py` (neben `power_p1.py`, das fuer Bootstrap-Power weiter benutzt, nicht
nachgebaut wird), Tests unter `scinance3-impl/tests/test_feasibility31.py`; Beispielkandidaten-YAML unter
`scinance3-impl/state/feasibility/` (A1, H27, A2, H33 als Regressionsfaelle, Zahlen aus der Akte mit Quelle). Code und
Kommentare Englisch, ASCII; keine Modellnamen; keine Hostnamen. Die Baseline der Test-Suite wird erweitert, nie reduziert.

## Offen (vor dem Bau durch den Orchestrator zu fixieren)

- Formel fuer Korrelation Screen/gepoolt und ihre Validierung: aus der OC-Herleitung (oc/OC_VERFASSUNG31.md) uebernehmen.
- Behandlung schwerer Raender: t-Grenzen bei Zwischenblicken (OC-Empfehlung).
- Ob die GSD-Grenzen aus einer Tabelle oder per Simulation kommen (Determinismus).
