# WP-10 - Praemien-Kohaerenz (deskriptiv) und Maker-Fill-Schattenmessung

> Orchestrator 2026-09-02. Massgeblich: PRD 3.0 Abschnitt 4.3. Kein
> Alpha-Gate. Teil A ist rein deskriptiv (Review R1-R4: erfundene
> rho-Schwellen gestrichen); Teil B misst eine Kostenkonstante.

## Teil A - Praemien-Kohaerenz im Stress (deskriptiv, kein PASS/FAIL)
- Eingang: Tagesserien der heute messbaren Praemien-Proxys aus dem Bestand:
  (1) Funding-Cashflow BTC/ETH/SOL/XRP/BNB aus `bybit/rest.fundingRate`
  (113 Tage) bzw. nach V-1 aus dem Funding-Backfill; (2) IV-RV-Differenz
  aus `deribit/dvol` minus WP-0-RV (BTC/ETH); (3) Perp-Basis-Proxy aus
  `bybit/tickers` (markPrice vs indexPrice) soweit vorhanden. Jede Serie
  mit Herkunft und Abdeckung.
- Stress-Definition: **STRESS_ABS (DEC-56)**; Ruhe = alle anderen Tage.
- Ausgabe: Spearman-Korrelationsmatrix der Serien getrennt fuer STRESS_ABS
  und Ruhe, mit Bootstrap-CI (Cluster = Kalendertag; Spearman-SE nach
  Bonett/Wright 1,06/sqrt(n-3) als Plausibilitaetsanker); effektives N je
  Regime (Anzahl Cluster, bei Episoden: Episodenzahl) ausgewiesen.
- **Portfolio-Nulleffekt als Konstante:** erwarteter Sharpe einer
  Gleichgewichtung von k Rauschsignalen auf diesem Bestand (k = 2..5, je
  1.000 Ziehungen, blockweise permutiert) - das ist die Groesse, gegen die
  ein spaeteres Portfolio-Gate kalibriert wird (R4 6.2a). Keine Schwelle.
- DEC-53: Cluster-Serien, Ziehungs-Seeds und Replikate als Artefakte.

## Teil B - Maker-Fill-Schattenmessung (kapitalfrei, Bybit-Perp BTC/ETH)
- Frage: mit welcher Wahrscheinlichkeit waere eine hypothetische eigene
  passive Quote am Touch innerhalb von 10 s bzw. 60 s (Design-Parameter,
  so etikettiert) gefuellt worden, rekonstruiert aus oeffentlichem L2
  (`orderbook.1000`, rezenz-konformes Fenster ab ~2026-06-20) und
  `publicTrade`: Warteschlangen-Position = sichtbare Tiefe am Touch zum
  Zeitpunkt der Quote; Fill, wenn kumuliertes gegenlaeufiges Handelsvolumen
  am Touch die Position uebersteigt, bevor der Touch wegwandert.
- Maschinerie: WP-2/WP-4-Replay in `research/c22_l2tilt/extract.py`
  wiederverwenden (Snapshot+Delta-Rekonstruktion, deterministisch); eigener
  Store `fillshadow_1min` (WP-2-/WP-4-Stores nachweislich unberuehrt, per
  Test gepinnt wie bei WP-4).
- Ausgabe: Fill-Rate-KURVE p_fill(t) fuer t in {10 s, 60 s} je Symbol,
  getrennt STRESS_ABS vs Ruhe, je Stunde des Tages; adverse Selektion
  `adv_sel` = mittlere Mid-Bewegung gegen die Quote nach Fill (bp). Keine
  Schwelle fuer p_fill; `adv_sel <= 1,75 bp` (Faktor 2 unter dem Maker-
  Vorteil 3,5 bp) ist Etikett "Maker-Vorteil traegt" / "traegt nicht".
- **Positivkontroll-Vorschaltung (PRD 3.3.8):** vor dem 86-min-Fenster-Lauf
  laeuft eine 1-Stunden-Probe, in der eine synthetisch eingesetzte Quote
  mit bekannter Position bekannte Fills liefern muss.
- Ergebnis wird als DEC (Kostenkonstante `P_FILL_*`, `ADV_SEL_*`) registriert,
  BEVOR ein Kandidat davon profitiert; H-04b/H-05c bleiben unberuehrt.

## Deliverables
`src/bybit_edge/research/wp10_coherence/` (A) und `wp10_fillshadow/` (B),
`scripts/wp10_coherence.py`, `scripts/wp10_fillshadow.py`,
`scinance3-impl/handoff_local/run_wp10.ps1`, Tests mit DEC-39-Trio je Teil
(A: Serien mit bekannter Stress-Korrelation vs. unabhaengig vs. Serien mit
gemeinsamem Trend ohne Korrelation der Innovationen; B: synthetisches Buch
mit bekannter Warteschlange -> bekannte Fills; Buch ohne Trades -> p_fill 0;
Adversarial: Quote genau im Moment eines Touch-Wegzugs), Determinismus,
Store-Unberuehrtheit, DEC-53-Artefakte.

## Reihenfolge
Nach WP-7 und WP-9 (Builder-Kapazitaet); Teil A zuerst (Bestand, Minuten),
Teil B danach (Replay, Stunden auf dem Nutzer-PC).

## Nachtrag 2026-09-02 (Orchestrator): Praezisierung des Portfolio-Nulleffekts
Die Bau-Vorgabe "Sanity-Check: waechst mit sqrt(k)" war FALSCH und hat den
ersten Bau in eine Summe von k Einzel-Sharpes gezwungen - eine Groesse, die
kein Portfolio-Gate je vergleicht. Richtig (R4 6.2a): der Portfolio-
Nulleffekt ist die NULLVERTEILUNG des annualisierten Sample-Sharpe einer
GLEICHGEWICHTUNG von k reinen Rauschsignalen auf dem realen Panel (Block-
permutierte Vorzeichen, 1.000 Ziehungen je k), berichtet als Mittel, SD,
p95 und p99. Unter der Null ist die Erwartung ~0 und die SD ~1/sqrt(T)
(nach Autokorrelations-Anpassung), im Wesentlichen UNABHAENGIG von k -
das ist der Sanity-Check. Getrennt davon wird die SELEKTIONS-Decke
berichtet: E[max Sharpe ueber K unabhaengige Varianten] fuer K in
{5,10,20,50,100} (Bailey/Lopez de Prado, empirisch aus denselben Ziehungen
durch Maximum ueber K Draws), die mit log K waechst. sqrt(k)-Wachstum gilt
nur fuer ECHTE IC (Fundamentalgesetz IR ~ IC*sqrt(Breite)) und ist kein
Null-Merkmal. Beide Groessen sind Konstanten, keine Schwellen.

## Nachtrag 2026-09-03 (DEC-58): Teil B - Competing-Risk-Schaetzer und Gebuehren-Fussnote
Time-to-Fill wird als Competing Risk geschaetzt (Fill vs. Touch-Wegzug vs.
Zensierung durch L2-Abdeckungsluecken 74 %/41 %); der naive Anteil "Fills /
Quotes" ist wegen informativer Zensierung bis Faktor 2,0 verzerrt (S1 X-SURV-3,
Nulleffekt exakt herleitbar). `adv_sel_max = 1,75 bp` haengt an
FEE_TAKER-FEE_MAKER = 3,5 bp; nach einer Gebuehrenaenderung (V-4-Pruefung)
wird die Formel, nicht die Zahl, registriert.
