# Strategie-Kandidaten nach Welle 7 — Entwurf, adversarial geprueft

> Orchestrator-Synthese aus zwei Design-Agenten (Sonnet) und einem
> adversarialen Pruefer (Opus), 2026-08-20. Rohentwuerfe und vollstaendige
> Maengelliste im Sitzungsarchiv. **Ehrlichkeits-Rahmen vorab:** Das
> Programm hat nach 31 Gate-Eintraegen **null gemessene handelbare
> Kanten**. Beide Kandidaten sind darum VOR-Hypothesen mit definiertem
> Validierungspfad, keine einsatzbereiten Strategien. Kapital fliesst
> erst nach bestandenen, vorregistrierten Gates (PRD §8; CLAUDE.md §4:
> kein Live-Order-Code im Programm).

## Kandidat 1 (Rang 1 des Pruefers) · VRP-ERNTE: Short-Vol auf BTC/ETH-Optionen mit Verteilungs-Envelope

**These:** Die literaturbekannte Varianz-Risiko-Praemie (IV > realisierte
Vol im Mittel) ist die Kandidaten-Kante; das Programm besitzt mit der
kalibrierten 3-Tage-RV-Verteilung (GL-022 E4: Dispersions-Ratio 0,72–0,74
nahe Optimum) ein GEMESSENES Risikomodell fuer das Sizing — ausdruecklich
NICHT fuer Lage oder Timing (GL-024-Zitierpflicht).

**Mechanik (Kurzform):** Kurzlaufende Short-Strangles/Iron Condors
(7–14 DTE) auf BTC/ETH; gekauftes Tail-Bein NICHT optional (PRD-Klausel:
Tail-Schutz ist bei Short-Vol Eintrittsbedingung). Delta-Hedge ueber Perp,
bandbasiert (jeder Rehedge kostet die 11–15-bps-Wand). Sizing so, dass das
95%-Quantil der RV-Verteilung den Maximalverlust auf einen fixen
Buchbruchteil begrenzt. Kill-Regel: nach 3,5-σ-Stunde 24 h keine neuen
Short-Vol-Positionen (Begruendung aus Payoff-Asymmetrie: die
Post-Schock-Kalibrierung des Envelopes ist UNGEMESSEN, und bei
asymmetrischem Payoff ist richtungs-unsichere Fehlkalibrierung wie die
gefaehrliche Richtung zu behandeln).

**Korrekturen aus der adversarialen Pruefung (bindend eingearbeitet):**
1. **Deribit messen, Bybit erst spaeter:** Bybit-`option_tickers` ist seit
   GL-004 NO_DATA, und das Recorder-Schema kennt KEIN bid/ask — es
   existiert keine Zeile Bybit-Options-Quotedaten. Die Messbasis ist
   DERIBIT (dvol 112 Tage, tickers-Kette wachsend); ein Bybit-Anspruch
   ist erst nach Recorder-Reparatur + eigenem Spread-Zensus zulaessig.
   Die C-33-Uhr (>=12 Monate IV-Recording + Stress-Periode) steht bei
   null; Deribit-Substitution waere eine Torpfosten-Verschiebung.
2. **Envelope-Baseline:** Nach GL-024 leistet eine dispersions-gedresste
   HAR dieselbe kalibrierte Breite zu Nullkosten. Der Envelope wird darum
   als "kalibrierte RV-Verteilung (dressed-HAR-Baseline, AnEn optional)"
   gefuehrt; die Registrierung laesst beide antreten.
3. **Der W1-PIT-Befund ist die toedliche Richtung:** BTC W1 zeigte
   UNTER-Prognose (mittlerer Rang 11,08; BTC W2 ist FDR-signifikant
   fehlkalibriert) — ein zu ENGES 95%-Quantil untersized den Tail. Das
   Envelope-Quantil erhaelt darum einen vorregistrierten
   Sicherheitsaufschlag, der aus genau dieser gemessenen
   Fehlkalibrierung abgeleitet wird (nicht frei gewaehlt).
4. **Gate-Arithmetik dimensionsehrlich:** (IV−RV) in Vol-Punkten ist
   nicht mit bps-vom-Nominal verrechenbar; das Tradability-Gate H-26b
   wird auf pfadabhaengige, dollar-gamma-gewichtete P&L nach GEMESSENEN
   Options-Spreads formuliert, nicht auf die Mittelwert-Differenz.
5. **DEC-39-Kontrollpaar statt Kategorienfehler:** Null-Pfad = Simulation
   mit IV ≡ wahrer Forward-Vol durch dieselbe Pipeline (muss ~0 ergeben;
   deckt Jensen-Verzerrung, Horizont-Mismatch dvol-30d vs. 7–14-DTE,
   Day-Count auf) UND Positiv-Pfad = injizierte 3%-Praemie (muss
   zurueckgewonnen werden). Beide als Fixtures gepinnt.

**Todesarten:** Gap ueber das Quantil (Analog-Bibliothek gerade in
Regimewechseln stale), Margin-Spirale (Optionsverlust + Hedge-Slippage
gleichzeitig), Funding auf dem Hedge (3x/Tag, in Trendphasen einseitig),
USDC/USDT-Basis + Depeg-Tail, Pin-Risk am Verfall (Roll ist der teuerste
Trade des Zyklus), junge Datenbasis = Peso-Problem per Definition,
Crowding einer breit geernteten Praemie auf duennem Markt.

**Validierungspfad:** **H-26** (kapitalfrei, data-gated): (IV−RV)-Messung
auf Deribit, Unlock bei >=90 zusammenhaengenden Tagen je Symbol
(Schwelle JETZT fixiert), Gate mittlere Praemie >=3% in >=2 disjunkten
Fenstern + Bootstrap-p<=0,05 + DEC-39-Kontrollpaar; ein PASS ist maximal
"kapitalfrei WEITER" — die C-33-12-Monats-Bedingung bleibt unabhaengig
bindend (fruehestens Mitte 2027 erfuellbar). Danach **H-26b** (Tradability)
erst nach Options-Spread-Zensus mit reparierter Aufzeichnung. §8.4:
Zwei-Fenster-PASS ohne Walk-Forward (>=L2) zaehlt nicht als bestanden.

## Kandidat 2 (Rang 2) · MAKER-SPREAD-CAPTURE auf Perpetuals — reduziert auf die Vorfrage

Der urspruengliche Entwurf (passives beidseitiges Quoting, Envelope-
gesteuerte Spread-Breite, 3,5-σ-Kill) hatte vier je fuer sich toedliche
Defekte: (1) Skalen-Luecke — der GL-028-Minuten-IC sagt nichts ueber den
bedingten Mark-out eines einzelnen Fills auf Sekundenskala (Adverse
Selection wird im Aggregat weggemittelt); (2) die zitierte
Maker-REBATE von −2,5 bps ist ein Code-Kommentar-Artefakt — die kanonische
Repo-Konstante ist FEE_MAKER = +2 bps je Bein (+4 bps Roundtrip), ein
~9-bps-Schwung auf einer Sub-bps-Bruttokante; (3) der Ertrag (der
Halbspread selbst) wurde nie gemessen, obwohl er auf dem WP-2-Store in
einem Nachmittag messbar ist; (4) die L2-Datenbasis fuer eine
Fill-Simulation existiert fuer 3 von 5 Symbolen nicht, und fuer BTC/ETH
nicht im Rezenz-Regime. Dazu: das terminale C-37-Gate ist per PRD ein
LIVE-Mikro-Pilot, den die Programm-Verfassung nicht baut; Quote-Pull bei
3,5-σ ist unter der programmeigenen 300-ms-Latenz-Konvention (GL-011)
strukturell zu langsam; ein deterministisch quotender Bot ist nach dem
H-23-Befund (Venue-Signaturen zu 97,7% lernbar) selbst ein Fingerabdruck.

**Konsequenz (Pruefer-Empfehlung uebernommen):** Der Kandidat wird auf die
eine billige, kapitalfreie Vorfrage reduziert — **WP-4 · Spread-Zensus:**
realisierter Quote-Spread (aus dem WP-2-L2-Store, BTC 2023–2025,
snapshot-validierte Buchrekonstruktion vorhanden) gegen den tatsaechlich
kontofuehrenden Maker-Satz. Faellt der Halbspread unter die Maker-Gebuehr,
ist der gesamte Ansatz OHNE weiteren Aufwand tot; liegt er darueber,
existiert erstmals die Zahl, die der Entwurf bisher nur behauptet, und
eine H-25-Registrierung (mit Fill-Nulleffekt-Kontrolle: naives
"Fill-bei-Beruehrung" erzeugt auf einem Random Walk mechanisch positive
Spread-Capture — Schwelle daran kalibrieren) wird diskutabel.

## Reihenfolge (Empfehlung)
1. **WP-4 Spread-Zensus** (CPU-Nachmittag, entscheidet Kandidat 2 binaer)
2. **H-26-Registrierung** (Deribit-VRP, data-gated; Lauf sobald Unlock
   erfuellt — die Streams wachsen von selbst)
3. Recorder-Reparatur `option_tickers` + bid/ask-Schema als
   Infrastruktur-WP, damit die Bybit-Options-Uhr ueberhaupt zu laufen
   beginnt (Voraussetzung fuer jede Bybit-Options-Tradability und C-33)
