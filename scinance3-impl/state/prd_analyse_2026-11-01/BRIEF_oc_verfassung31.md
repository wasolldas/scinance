# Auftrag: Gesamt-Operationscharakteristik (OC) des Pakets "Verfassung 3.1" (2026-11-02)

Rolle: Herleitung mit eigenem Code (Simulation und Formeln, keine Marktdaten). Du schreibst Volltexte in Dateien; an
den Orchestrator geht eine Kurzfassung (<= 12 Zeilen). Du aenderst nichts im Repo, committest nichts, oeffnest keine
Siegeldatei, laedst keine Marktdaten.

## Anlass

Der Nutzer hat am 2026-11-02 das Paket "Verfassung 3.1" angenommen (`scinance3-impl/state/PRD_ANALYSE_2026-11-01.md`,
Abschnitt 9.1, P-1..P-7 mit den Default-Vorschlaegen). Der Review der PRD-Analyse (Luecke 2) und die Synthese (9.2
Nr. 3) verlangen vor der ersten Registrierung unter 3.1 eine **Gesamt-OC des Pakets**: erwartete Falsch-PASS je Jahr,
PPV bei realistischen Basisraten, Power der Entscheidungsregel, Wirkung von Selektion in Zone X, schweren Raendern,
kleinen Clusterzahlen und Ueberlappung. Ein Ueberschlag steht in PRD_ANALYSE Abschnitt 6 (Tabelle "Gesamt-OC"); er ist
Normalnaeherung ohne Selektion, ohne Screen-Korrelation, ohne schwere Raender. Du ersetzt ihn durch eine belastbare
Rechnung mit Code.

## Das Paket (so beschlossen; Default-Vorschlaege der Synthese)

- **P-2 (a):** Konfirmation = gepoolter einseitiger Test ueber alle Konfirmationsdaten bei alpha 0,0025 **plus**
  REZENZ-Screen: das juengste 12-Monats-Fenster (bzw. die letzten vier Quartale) muss einseitig bei 0,05 bestehen
  (Z_recent > 1,645). Power-Ziel 0,80 fuer die **gemeinsame** Entscheidungsregel an der MDE. Heutiger Vergleich: C.10
  (zwei 12-Monats-Fenster je alpha 0,05, je Power 0,80 nominal -> gemeinsam 0,0025 / 0,64) und DEC-52 (gepoolt 0,01
  + Screen, nur bei Per-Fenster-Power < 0,80, DEC-94).
- **P-4:** Drei Zonen (X Exploration mit Konto, V Validierung mit einem Blick, K Konfirmation versiegelt, 36/12 Monate,
  Quartalstakt); gruppensequentielle Blicke in K (O'Brien-Fleming, 4 Blicke, alpha 0,0025 einseitig, letzter Blick
  enthaelt das juengste Quartal = REZENZ), optional Futility (Z < 0 an den Blicken 1-3); Kohorten-Stichtage mit BY
  (q 0,10) ueber die Kohorte; festes alpha je Test 0,0025 bleibt.
- **P-3:** SESOI als Feasibility-Massstab; Explorations-Schaetzer aus Zone X (K Varianten, beste wird registriert)
  duerfen Richtung und Groessenordnung einer Registrierung bestimmen; DEC-99 (3) verlangt fuer Pilot-Priors den
  selektionsbereinigten (bedingt median-unverzerrten) Schaetzer.
- **P-7:** A2: exakte Konjunktionsbedingung statt Produkt; Pilot-Uebergabe ueber Assurance.
- Unveraendert: Blind-Siegel, Vorwissens-Regel, C.17, Stress-Kanon, Nuisance aus der Vorperiode.

## Rechenauftrag (analytisch + Monte Carlo >= 200.000 Pfade je Zelle, feste Seeds, Laufzeit <= 20 min CPU)

(a) **Entscheidungsregel P-2 (a) gegen C.10 und DEC-52:** alpha_eff und Power als Funktion des Effekts (0, 0,5 MDE,
    MDE, 1,5 MDE), des Anteils des juengsten Fensters an den Konfirmationsdaten (1/2, 1/3, 1/4), mit korrekter
    Korrelation zwischen gepoolter Statistik und Screen (gemeinsame Daten). Ausweis: alpha_eff <= 0,0025? Datenfaktor
    fuer Power 0,80 gegen C.10 je 0,80 und gegen gepoolt ohne Screen. Regime-Robustheit: Power, wenn der Effekt nur
    in der aelteren Haelfte existiert (Screen soll dann ablehnen) - P(PASS) in diesem Fall ist die relevante
    Falsch-PASS-Groesse der REZENZ-Logik.
(b) **GSD** O'Brien-Fleming 4 Blicke, alpha 0,0025 einseitig, Power 0,80: Grenzen, Maximum/fix, E[N bei H0], E[N bei H1],
    mit und ohne Futility; dazu die Kombination "GSD + REZENZ-Screen am letzten Blick". Vergleich mit den Zahlen der
    Analyse (0,871 / 1,007).
(c) **Selektion in Zone X:** K Varianten (K = 4, 10, 25) werden auf disjunkten X-Daten gescreent, die beste registriert.
    (i) Winner's Curse: E[Schaetzer | ausgewaehlt] gegen wahren Effekt bei Anteil pi echter Varianten (0, 0,1, 0,25,
    0,5) und Effekt echter Varianten delta in SE-Einheiten der X-Messung (1, 2, 3); (ii) P(ausgewaehlte Variante ist
    echt | K, pi, delta) = Basisrate der Konfirmation; (iii) Power-Ueberschaetzung, wenn die MDE aus dem rohen
    X-Schaetzer gesetzt wird, gegen den selektionsbereinigten Schaetzer (bedingt median-unverzerrt, Formel angeben);
    (iv) alpha der Konfirmation bleibt 0,0025 (disjunkte Daten) - zeigen.
(d) **Programmebene je Jahr:** m Registrierungen (4, 8, 12), Basisrate pi_K der Konfirmation aus (c) oder fest
    (0,05 / 0,10 / 0,25): erwartete Falsch-PASS, wahre PASS, PPV, realisierte FDR unter festem alpha 0,0025 und unter
    BY q 0,10 je Kohorte (BY ueber m); Vergleich mit heute (C.10, m faktisch ~0 Tests je Jahr).
(e) **Schwere Raender und kleine Clusterzahlen:** Innovationen t(4) (Exzess-Kurtosis 6) und t(3), Clusterzahlen 40 /
    52 / 104, Teststatistik mit geschaetzter Varianz (stationaerer Bootstrap wie `power_p1` bzw. t-Grenzen): wahres
    alpha bei nominal 0,0025 und 0,05; Power-Verlust gegen die Normalnaeherung; Empfehlung fuer Zwischenblicke
    (t-artige Grenzen?).
(f) **Ueberlappung:** 1-3-Tages-Horizont mit taeglichem Schritt, Varianzinflation c (Bartlett/Newey-West-Ueberschlag)
    fuer MDE und Fallzahl.
(g) **Strenge-Quotient und A2 unter 3.1:** Definition MDE80(alle Festlegungen)/MDE80(Grundfassung); fuer A2 W2 die
    Kette unter 3.1 (exakte Konjunktion 22,93 / 23,77 statt Produkt 23,43 / 24,36; Stress bindend; skalierte Null;
    Gate-(4)-Faktor 0,9025) aus den Akten-Zahlen in `scinance3-impl/state/herleitung_a2/PILOT_ROUTE_A2.md`,
    `NULL_SIMULATION_A2.md`, `state/decisions.md` DEC-103 Nachtrag 1 (6), (8), (9). Nur Akten-Zahlen, keine Daten.
(h) **Gegenueberstellung heute / 3.1** in einer Tabelle: alpha je Test, Entscheidungs-Power, E[N bei H1], PPV bei
    pi 0,05 / 0,10 / 0,25, erwartete Falsch-PASS je Jahr bei m 8, fruehester Konfirmationszeitpunkt fuer eine am
    naechsten Kohorten-Stichtag registrierte Hypothese mit MDE am SESOI (Beispiel: Klasse W Wochen-IC, Klasse E A2).

## Quellen (Pfade unter /home/user/scinance/)

- `scinance3-impl/state/PRD_ANALYSE_2026-11-01.md` (Abschnitte 1, 6, 9; Anhang C).
- `scinance3-impl/state/prd_analyse_2026-11-01/KRITIK_PRD.md` (K-4..K-9), `REVIEW_PRD_ANALYSE.md` (B-7, B-8, B-12, Luecken),
  `ARCHITEKTUR_AUTOMATION.md` (Abschnitt 3), `KONZEPT_UND_FORSCHUNGSFELDER.md` (T-12).
- Skripte: `scinance3-impl/state/prd_analyse_2026-11-01/scripts/orch_review_check.py`, `review_calc.py`, `kritik_calc.py`,
  `gsd_fut.py` (Vorarbeiten; reproduziere ihre Zahlen zuerst).
- `scinance3-impl/state/decisions.md`: DEC-51, DEC-52, DEC-94, DEC-99, DEC-103 (+ Nachtrag 1).
- `scinance3-impl/state/herleitung_a2/PILOT_ROUTE_A2.md`, `NULL_SIMULATION_A2.md` (nicht versiegelt).
- `scinance3-impl/src/` oder `scinance3-impl/scripts/`: `power_p1` (Bootstrap-Konvention), nur lesen.
Nicht oeffnen: `scinance3-impl/state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`.

## Lieferung

- `<scratchpad>/oc/OC_VERFASSUNG31.md`
  (ASCII, Deutsch, Rollen statt Modellnamen; Markierungen [R] Rechnung, [U] Urteil, [V] Vermutung; Abschnitte (a)-(h),
  dann "Was folgt / Was nicht folgt", dann Kurzfassung <= 12 Zeilen).
- `oc/calc/oc_sim.py` (deterministisch, Seeds im Code, `python3 -I` lauffaehig, nur numpy/scipy) und
  `oc/calc/oc_results.json` (nur Simulationsergebnisse) und `oc/calc/oc_sim.out` (Konsolenausgabe).
- Jede Zahl im Text muss in `oc_results.json` oder in `oc_sim.out` stehen.

## Regeln

Keine Marktdaten, keine Siegeldateien, keine Registrierung, kein Verdikt ueber Markteffekte. Sag, wo die Rechnung
Annahmen braucht (z. B. Korrelationsstruktur zwischen Fenstern) und rechne die Alternativen. ASCII, keine Hostnamen,
keine Modellnamen.
