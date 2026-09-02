# Debatte: Funding / Settlement / Carry

**Cluster:** funding (Funding / Settlement / Carry)
**Phase:** 4 — DEBATE
**Claims:** C-22, C-23, C-24, C-32, C-37, C-38, CS-03 (PARTIAL/PENDING), CS-12
**Stand:** 2026-06-11

> Zielmarkt aller Cluster-Claims laut Quelle: **Futures (Perpetual)**. Das ist
> kein Defizit der Argumentation, sondern eine Eigenschaft des Mechanismus:
> Funding/Settlement existiert nur im Perpetual-Kontrakt. Spot und Optionen
> werden je Argument trotzdem separat bewertet — i. d. R. als „kein direkter
> Anwendungsfall, aber abgeleiteter Nutzen".

---

## Advocate

Grundhaltung dieses Parts: Dieser Cluster ist der einzige im gesamten Register,
der **real feuert und real misst** (CS-03: N=213 Trades, E-09). Alle anderen
Strategien sind entweder 0-Trade-Mess-Lücken (S4/S5, E-13/E-14), eine
REFUTED-Strategie (S2) oder reine Spezifikationen ohne jeden Replay. Der
empirische Vorsprung der Funding-Familie ist damit kein Bonus, sondern der
zentrale Hebel: Wir argumentieren hier nicht über einen Mechanismus, den noch
nie jemand ausgelöst hat, sondern über eine laufende Maschine, deren Verlust
forensisch **lokalisiert** ist (Exit + Friktion, E-07/E-08/E-10) und deren
Reparatur committet und in Messung ist (E-15).

---

### A-1 — CS-03 ist NICHT widerlegt, sondern an einer isolierten Bug-Stelle blockiert (Kerngeschäft des Clusters)

- **Futures:** CS-03 verliert netto (-16.81 bps, E-09), ABER der Verlust ist
  exit-/friktionsgetrieben, nicht entry-getrieben. Drei unabhängige Befunde
  stützen das: (1) Der zentrale Time-Stop feuerte wegen eines Wall-Clock-Bugs
  **1× statt 68×** (E-07) — die Exit-Policy, die 32 % der Trades (>120 s) hätte
  abschneiden sollen, **lief nie**. Das Testfenster ist für die Time-Stop-
  Hypothese ausdrücklich UNGEEIGNET (E-07). (2) Die schlechtesten Trades sind
  1.7–3.0× länger gehalten als der Durchschnitt (E-10) — der Verlust sitzt genau
  in der Haltedauer, die der defekte Time-Stop adressiert hätte. (3) Der real
  gemessene Hard-Stop feuerte nur 13× und ließ 33 Trades unter -30 bps
  durchlaufen, weil er friktions-unbewusst kalibriert war (E-08). Die Strategie
  verliert also an reparierbaren Stellen, die alle in iter-5 adressiert sind
  (E-15). Die Alignment-Matrix bestätigt: PARTIAL, **nicht** REFUTED, mit
  explizitem PENDING-Upgrade-Pfad.
- **Spot:** Kein direkter Anwendungsfall (kein Settlement im Spot). Abgeleiteter
  Nutzen: Spot-Bein als Hedge/Convergence-Anker (siehe A-6/C-37).
- **Optionen:** Kein direkter Anwendungsfall; INC-04 (kein IV-Archiv) blockiert
  ohnehin jede Options-Anwendung dieses Clusters.
- **Stärkstes Einzelargument:** Eine Strategie, deren Verlust nachweislich aus
  einer Zeile defektem Code stammt (`time.time()` statt Tick-Zeit, E-07), ist
  forensisch nicht widerlegt — sie ist ungetestet in genau der Dimension, die
  zählt.
- **Was ich zugestehe:** Selbst nach Bug-Fix bleibt die **Roh-Edge** -5.8 bps
  (E-09) und liegt damit unter der 11-bps-Friktion. Time-Stop kappt Verluste,
  erzeugt aber keine positive Roh-Edge. CS-03 wird nur ADOPT-fähig, wenn iter-5
  netto-positiv misst — und dafür reicht ein Exit-Fix allein wahrscheinlich
  nicht; es braucht zusätzlich A-6 (Friktion) oder A-2 (Entry-Schärfung).
- **Validierungs-Gate (PILOT):** E-15-Run muss aggregate mean pnl_bps netto > 0
  liefern; sonst PRD-Redesign. Härter formuliert für ADOPT: PRD-kestrel-Gate
  Sharpe ≥ 1.2 / WR ≥ 55 % / PF ≥ 1.3 über ≥ 200 Trades (C-22).

---

### A-2 — C-22 (Funding-Pressure-Entry) ist das einzige real feuernde Entry-Signal des Registers — sein Beitrag ist nie sauber negativ gemessen worden

- **Futures:** C-22 ist das Entry-Signal von S3 und feuert real (N=213). Die
  Matrix stuft es PARTIAL ein, weil sein Beitrag „weder als positiv noch als
  negativ isoliert nachgewiesen" ist (C-22-Begründung). Das ist ein
  Advocate-Argument: Der Mechanismus (Bybit clamped Funding bei ±0.05 %, der
  geklemmte Überdruck entlädt sich nach Settlement) ist **deterministisch** —
  die Clamp-Funktion ist API-Faktum, kein gefitteter Parameter. Anders als C-14
  (E-01: theoretischer Threshold 0.85 strukturell unerreichbar) hängt C-22 an
  keiner unkalibrierten Schwelle, deren Erreichbarkeit erst bewiesen werden muss.
- **Spot:** Nicht anwendbar (kein Funding im Spot).
- **Optionen:** Nicht direkt; Funding-Druck als Vol-Regime-Kontext denkbar, aber
  unbelegt und ohne Datengrundlage (INC-04).
- **Stärkstes Einzelargument:** Das Signal feuert messbar, basiert auf einem
  deterministischen Plattform-Mechanismus, und sein direktionaler Eigenbeitrag
  wurde durch die defekte Exit-Kette nie sauber gemessen — die naheliegendste
  Erklärung für den Strategieverlust ist Exit+Friktion (E-07/E-08), nicht das
  Entry.
- **Was ich zugestehe:** INC-03 ist real: Der Q90-Pressure-Threshold übertriggert
  massiv — S3 feuert 50–62 Trades/24 h, obwohl es nur 3 Settlements/Tag gibt
  (E-12). Der Filter trennt also NICHT auf Settlement-Qualitätsniveau, sondern
  schießt auf Mikro-Druck. Das ist ein echter Entry-Defekt: Die These „Pressure
  identifiziert die 3 echten Settlement-Releases" ist durch das Übertriggern
  empirisch beschädigt. Mein Argument reduziert sich darauf, dass die
  Filter-SCHÄRFE reparierbar ist (höheres Quantil, Settlement-Fenster-Bindung),
  nicht der Mechanismus.
- **Validierungs-Gate (PILOT):** Entry-Isolations-Test — Pressure-Threshold auf
  Q97/Q99 anheben + strikte Settlement-Fenster-Bindung; messen, ob Roh-Edge bei
  reduziertem N (Richtung 3–10 Trades/Tag) steigt. Erfolg: Roh-Edge > 0 vor
  Friktion auf ≥ 3 Symbolen.

---

### A-3 — Das ganze Settlement-Framing ist im aktuellen Replay nie fair getestet worden (Übertriggern als Mess-Artefakt, nicht als Mechanismus-Widerlegung)

- **Futures:** INC-03 (50–62 Trades/24 h statt ~3) und E-12 (`n_in_window`
  ~7–8 % der Ticks) zeigen zusammen: Die Strategie handelt überwiegend
  **innerhalb** breiter 30-min-Fenster auf jeden Q90-Druckspike, statt auf die
  drei diskreten Settlement-Momente. Damit misst der Replay gar nicht die
  Settlement-Pressure-Release-These, sondern eine entartete High-Frequency-
  Variante davon. Der eigentliche Claim (Druck entlädt sich AM Settlement) ist
  unterbestimmt geblieben. Das ist ein Advocate-Punkt: Negatives Ergebnis einer
  entarteten Implementierung ≠ Widerlegung des Konzepts (CLAUDE.md: Modul ≠
  Strategie).
- **Spot / Optionen:** N/A.
- **Stärkstes Einzelargument:** Der Replay testet 50× häufiger als das Konzept
  vorsieht — er prüft eine andere Strategie als die behauptete.
- **Was ich zugestehe:** Es ist möglich, dass der scharf gefilterte Settlement-
  Trade (nur 3×/Tag) schlicht zu selten ist, um nach 11–15 bps Friktion je
  Round-Trip profitabel zu sein — wenige Trades × kleine Edge − fixe Friktion
  kann strukturell negativ bleiben. Das Übertriggern könnte ein Versuch gewesen
  sein, überhaupt genug Trades für Edge zu sammeln. Dann wäre das Problem nicht
  Schärfe, sondern fundamentale Edge-Knappheit.
- **Validierungs-Gate:** identisch zu A-2 plus Bindung an `n_settlement_events`
  statt `n_in_window`.

---

### A-4 — C-37 (Bybit-native Spread-Execution) ist der einzige dokumentierte Hebel, der die Kernrelation „Friktion > Edge" kippen kann

- **Futures:** Die Kernrelation des gesamten Registers lautet: Round-Trip-
  Friktion 11 bps (taker) / 15 bps (inkl. Slippage) übersteigt jede gemessene
  Roh-Edge (max ~4–7 bps, Kostenbaseline). C-37 behauptet ~4 bps Maker-Round-
  Trip über den Bybit-Spread-Markt statt 11 bps Taker — eine Friktions-Reduktion
  um ~7 bps. Das ist nicht inkrementell: Bei einer S3-Roh-Edge von -5.8 bps
  (E-09) verschiebt eine Friktions-Senkung von 11 → 4 bps die Netto-Rechnung um
  7 bps; kombiniert mit dem Exit-Fix (A-1) ist das die plausibelste Route zu
  netto-positiv. C-37 ist der einzige Claim im Register, der **die
  Verlustursache direkt angreift** (Friktion), statt am Signal zu drehen.
- **Spot:** Indirekt relevant — der Spread-Markt koppelt Perp gegen Spot/quartals;
  Spot ist das natürliche Gegenbein einer Carry/Basis-Execution. C-37 macht Spot
  damit zum funktionalen Bestandteil, ohne dass Spot ein eigenes Alpha trägt.
- **Optionen:** N/A.
- **Stärkstes Einzelargument:** Jeder andere Cluster-Claim kämpft gegen die
  11-bps-Wand; C-37 ist der Versuch, die Wand selbst zu versetzen — der einzige
  strukturelle Friction-Killer im Material.
- **Was ich zugestehe:** Der 4-bps-Wert ist **ungemessen** („PRD-Referenz, nicht
  gemessen", Kostenbaseline + C-37-Note). Er hängt an einer Maker-Quote ≥ 70 %,
  die ebenfalls ungeprüft ist; verfehlte Maker-Fills fallen auf Taker-Kosten oder
  Queue-Risiko zurück. Es existiert kein Spread-Markt-Archiv, also nur Proxy-
  Backtest oder Live möglich. Das ist der schwächste Punkt des gesamten Clusters:
  Der wichtigste Hebel ist der am wenigsten validierte.
- **Validierungs-Gate (PILOT):** Live-Mikro-Pilot (kleines Notional) über den
  Spread-Markt: realisierte Maker-Fill-Quote messen; Gate Maker-Quote ≥ 70 % UND
  realisierter Round-Trip ≤ 6 bps über ≥ 100 Fills. Verfehlt → C-37 DROP, und
  der gesamte Cluster bleibt friction-bound.

---

### A-5 — C-32 (Funding-Contrarian, Extremwert) ist der billigste, sauber falsifizierbare Carry-Test im Cluster — auf einem Horizont, der die Friktion mathematisch schlägt

- **Futures:** C-32 ist mechanistisch von C-22 getrennt: nicht der kurzfristige
  Settlement-Trigger, sondern ein 24h-Contrarian auf Funding-Extremwerten (±2σ,
  30-Tage-Rolling). Entscheidend ist der Horizont: Auf 24h ist eine 11-bps-
  Round-Trip-Friktion eine niedrige Hürde (ein einziger Funding-Zyklus von
  0.05 % = 5 bps, ein Tagesmove von 1–3 % = 100–300 bps), während dieselbe
  Friktion auf dem Sekunden-/Minuten-Horizont von S2/S3 tödlich ist. C-32 ist
  zudem REST-only auf CONFIRMED-Datenströmen (Funding History, Premium-Index, OI
  — alle als verfügbar markiert, C-32-Abhängigkeiten) und braucht **keine**
  Aufzeichnungs-Vorlaufzeit. Es ist damit der schnellste echte OOS-Test des
  Clusters.
- **Spot:** Nicht anwendbar (Funding-Signal), aber Spot kann das Hedge-Bein
  stellen.
- **Optionen:** N/A.
- **Stärkstes Einzelargument:** C-32 trennt sauber Horizont von Mechanismus: Auf
  24h ist die Friktion eine Randnotiz, nicht die Wand — und der Test ist sofort
  laufbar, ohne neue Datenpipeline.
- **Was ich zugestehe:** Die Quelle selbst erwartet schnellen Signal-Zerfall
  unter dem aktuellen Carry-Kompressions-Regime seit 2024 (C-32-Note); INC-05
  drückt zusätzlich auf alle unkonditionalen Direktional-Ansprüche (Richtungs-AUC
  ≈ 0.50 mit klassischen Features). Es ist gut möglich, dass das Edge historisch
  existierte und heute weggearbitragt ist. C-32 ist UNTESTED — es gibt **null**
  Evidenz dafür, nur einen plausiblen Mechanismus und einen billigen Testpfad.
- **Validierungs-Gate (PILOT):** Der eigene Quell-Gate: mittlerer Contrarian-
  Return > 0 nach Kosten (> 0.11 %/Round-Trip) OOS in ≥ 2 × 180-Tage-Fenstern.
  Abbruch bei Return ≤ 0 in einem Fenster.

---

### A-6 — CS-12 (Funding-Uhr / K2) ist der bereits spezifizierte Reparatur-Bauplan für genau die zwei nachgewiesenen S3-Schwachstellen

- **Futures:** CS-12 ist kein neuer Wurf, sondern die Nachfolge-Architektur von
  CS-03 (beide C-22-zentriert, Matrix: „K2 verbessert genau die zwei
  Schwachstellen von S3"). Es kombiniert: (1) Execution über den Spread-Markt
  (C-37, ~4 statt 11 bps) — adressiert die Friktions-Wand (A-4); (2) BOCPD-
  Regime-Gate (C-08) — adressiert das Übertriggern (INC-03), indem nur in
  stabilen Regimes gehandelt wird. Damit hängt CS-12 indirekt am iter-5-Ausgang:
  Bestätigt E-15 eine reparierbare Entry-Edge, gewinnt CS-12 unmittelbar an
  Plausibilität (Matrix-Note CS-12). CS-12 ist die saubere Integration der
  Cluster-Lehren.
- **Spot:** Spread-Markt zieht Spot/Perp als Beine ein (siehe A-4).
- **Optionen:** N/A.
- **Stärkstes Einzelargument:** CS-12 ist nicht spekulativ — es ist die
  ingenieurmäßige Antwort auf zwei forensisch isolierte Defekte (Friktion via
  C-37, Übertriggern via C-08), beide aus diesem Cluster heraus belegt.
- **Was ich zugestehe:** CS-12 ist UNTESTED und erbt ALLE CS-03-Befunde als
  Hypotheken: friction-bound (E-09), Q90-Übertriggern (INC-03). C-08 (BOCPD) war
  in S3 ein No-Op — es feuerte im gesamten Fenster keinen einzigen Changepoint
  (E-12) — d. h. das Regime-Gate, auf das CS-12 baut, hat sich im einzigen
  vorhandenen Test als wirkungslos erwiesen (wenn auch im GM-6-kurzen Fenster
  ohne garantierten Regime-Bruch). Ich baue hier auf ein Modul, dessen einziger
  Praxistest „nichts getan" lautet.
- **Validierungs-Gate (PILOT):** Erst nach E-15-positiv + C-37-Pilot-positiv
  (A-4) aktivieren; dann BOCPD-Gate gegen ein Fenster MIT dokumentiertem Regime-
  Bruch testen (DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 %, C-08-Gate).

---

### A-7 — C-38 (TFT mit Known-Future-Funding) hat einen echten, seltenen Informationsvorteil — verdient aber strikte Nachrangigkeit

- **Futures:** Das funding-spezifische Argument für C-38: Der Funding-Settlement-
  Zeitpunkt und das Settlement-Intervall sind **deterministisch im Voraus
  bekannt** (Plattform-Fakt). Ein Temporal-Fusion-Transformer mit
  Known-Future-Inputs kann diese kalendarische Sicherheit nutzen — das ist
  selten in Finanz-Zeitreihen, wo „Zukunft" fast immer unbekannt ist. Wenn C-22
  einen realen Settlement-Effekt trägt, ist C-38 die natürliche
  Quantil-Kalibrierungs-Schicht darüber.
- **Spot / Optionen:** N/A.
- **Stärkstes Einzelargument:** Funding-Settlement ist eines der wenigen exakt
  vorab bekannten Ereignisse im Markt — ein TFT mit Known-Future-Funding nutzt
  einen echten, strukturellen Informationsvorsprung.
- **Was ich zugestehe:** C-38 ist UNTESTED, explizit erst nach C-22-Live-Proof
  vorgesehen (C-38-Begründung), und steht unter dem vollen INC-05-Revisionsdruck
  (Direktional-AUC > 0.55 ist der Anspruch, den klassische Features auf
  Münzwurf-Niveau verfehlen). Ein DL-Modell auf ein noch unbestätigtes Basissignal
  zu setzen, ist die schwächste Position des Clusters — C-38 ist erst sinnvoll,
  wenn A-1/A-2 geliefert haben.
- **Validierungs-Gate (PARK, nicht PILOT):** Gate erst öffnen nach C-22-Live-
  Proof; dann Quantil-Kalibrierung + Direktional-AUC > 0.55 OOS. Vorher: PARK.

---

### A-8 — C-23 / C-24 (Basis-Convergence, Kalman-Premium) sind nicht widerlegt, nur nie ausgeführt — und ihr Konvergenz-Mechanismus ist der robusteste des Clusters

- **Futures:** C-23 (Basis konvergiert gegen 0 vor Settlement) und C-24 (Kalman
  trennt Fair-Funding-Drift von Sentiment-Spike) sind beide UNTESTED, NICHT
  REFUTED. Wichtig: C-23 war in S3 ein No-Op — `sign(pressure) ≡ -sign(basis)`
  per Konstruktion (E-12), d. h. das Basis-Gate war redundant verdrahtet und trug
  per Design keine eigene Information. Das ist ein **Implementierungs**-Defekt,
  kein Konzept-Defekt: Das Basis-Gate wurde nie als eigenständiges Convergence-
  Signal getestet. Der zugrundeliegende Mechanismus — Basis = (Mark−Index)/Index
  zieht mechanisch gegen 0, weil Funding genau das erzwingt — ist die robusteste
  No-Arbitrage-Relation des ganzen Clusters; sie braucht keine Verhaltensannahme,
  nur die Plattform-Mechanik.
- **Spot:** Direkt relevant — Basis IST per Definition die Perp-Spot-Relation;
  ein Convergence-Trade ist strukturell ein Spot-Perp-Paar. Hier hat der Cluster
  seinen einzigen genuinen Spot-Touchpoint.
- **Optionen:** N/A.
- **Stärkstes Einzelargument:** Basis-Konvergenz vor Settlement ist eine
  erzwungene No-Arbitrage-Relation, kein gefittetes Edge — und sie wurde im
  einzigen Replay durch eine redundante Gate-Verdrahtung (E-12) gar nie auf
  ihren Eigenbeitrag geprüft.
- **Was ich zugestehe:** „Mechanisch erzwungen" heißt nicht „handelbar nach
  Kosten". Die Konvergenz kann real sein und trotzdem kleiner als 11–15 bps
  Friktion ausfallen (genau das friction-bound-Problem des Clusters). C-24
  (Kalman) ist zusätzlich rein spekulativ — kein einziger isolierter Befund
  (Matrix: „kein eigener Befund"). Beide sind heute Hypothesen, keine Kandidaten.
- **Validierungs-Gate (PARK→PILOT):** C-23 standalone als reines Basis-z-Score-
  Signal verdrahten (entkoppelt vom Pressure-Gate), Hit-Rate ≥ 58 % nach Kosten
  im Settlement-Fenster über ≥ 200 Events messen. C-24 erst nach C-23-Signal.

---

## Zusammenfassung Advocate — Tendenz je Ansatz × Markt

| Claim | Spot | Futures | Optionen |
|---|---|---|---|
| CS-03 (S3 Strategie) | n/a | **PILOT** (PENDING E-15) | n/a |
| C-22 (Funding-Pressure-Entry) | n/a | **PILOT** | n/a |
| C-37 (Spread-Execution) | indirekt (Hedge-Bein) | **PILOT** (Friction-Killer) | n/a |
| C-32 (Funding-Contrarian 24h) | n/a | **PILOT** (billigster OOS-Test) | n/a |
| CS-12 (Funding-Uhr K2) | indirekt | **PILOT** (nach E-15+C-37) | n/a |
| C-23 (Basis-Convergence) | **PARK→PILOT** (Spot-Perp-Paar) | PARK→PILOT | n/a |
| C-24 (Kalman-Premium) | n/a | PARK | n/a |
| C-38 (TFT Known-Future) | n/a | **PARK** (nach C-22-Proof) | n/a |

**Dreh- und Angelpunkt für den Judge:** Der gesamte Cluster steht und fällt mit
zwei ungemessenen Größen — (1) ob iter-5 (E-15) CS-03 netto-positiv hebt und
(2) ob C-37 die 4-bps-Maker-Friktion real liefert. Liefern beide, kippt die
Kernrelation „Friktion > Edge" für genau diesen Cluster, und C-22/CS-12 werden
ADOPT-fähig. Liefert keines, bleibt der gesamte Cluster friction-bound und fällt
auf PARK zurück. Das ist der einzige Cluster im Register, bei dem dieser Kipp-
Punkt überhaupt in Reichweite und billig testbar ist.

*Ende Advocate-Part — Skeptic antwortet Punkt für Punkt auf A-1 .. A-8.*

---

## Skeptic

Grundhaltung dieses Parts: Ich bestreite NICHT, dass dieser Cluster der einzige
ist, der real feuert und real misst (CS-03, N=213, E-09) — das ist ein echter
Vorsprung und ich lasse ihn dem Advocate stehen. Mein Angriff ist anderswo: Der
gesamte Advocate-Case ruht auf einer einzigen, nie geprüften Hilfsannahme — „der
Verlust sitzt im Exit/in der Friktion, nicht im Entry" — und auf zwei Größen, die
beide UNGEMESSEN sind (iter-5-Netto-Edge E-15, 4-bps-Maker-Friktion C-37). Beide
ungemessenen Größen werden gebraucht, damit der Cluster kippt (Advocate-Schluss
selbst, Zeile 280-286). Solange beide offen sind, ist „PILOT für alles" eine
Wette auf zwei unabhängige positive Coinflips, nicht ein Befund. Hinzu kommt: Die
gesamte Evidenz ist L0/in-sample (GM-1, 17×L0), unkorrigiert über 3 Iter × 5
Symbole × 5 Strategien × 2 Arme (GM-2), und jede Cross-Symbol-Aggregatzahl ist
faktisch das BTC-Ergebnis (GM-3). Das ist der Boden, auf dem hier „PILOT"
gefordert wird.

---

### S-1 → A-1 (CS-03: „Verlust sitzt im Exit", PARTIAL nicht REFUTED)

- **Steelman:** Der Advocate hat hier seinen stärksten Punkt des ganzen Clusters:
  Der Time-Stop feuerte wegen eines Wall-Clock-Bugs nachweislich 1× statt 68×
  (E-07), das Testfenster ist für die Time-Stop-Hypothese ausdrücklich UNGEEIGNET
  (E-07), und die Alignment-Matrix stuft CS-03 deshalb korrekt PARTIAL/PENDING,
  nicht REFUTED (CS-03-Status). „Eine defekte Variante verliert ≠ das Konzept ist
  widerlegt" ist regelkonform (CLAUDE.md, Modul ≠ Strategie). Das gestehe ich
  vollständig zu.

- **Futures (der einzige Markt hier):** Der Advocate beweist, dass der Exit
  defekt war — er beweist NICHT, dass der Verlust dort SITZT. Das ist ein
  Non-Sequitur. Drei harte Gegenbefunde:
  1. **Roh-Edge war schon VOR jedem Exit negativ.** Die Roh-Edge je Trade ist
     -5.8 bps aggregat (E-09) und liegt im iter-3-Band -3.31 … -20.09 bps je
     Symbol (E-09) — gemessen am Entry-Outcome, bevor irgendeine Exit-Policy
     greift. Der Time-Stop kappt Tail-Verluste, erzeugt aber per Konstruktion
     KEINE positive Roh-Edge (das gesteht der Advocate in A-1 selbst zu, Zeile
     53-57). Wenn die Roh-Edge negativ ist, ist der Verlust mindestens
     ko-lokalisiert im Entry, nicht „im Exit".
  2. **E-17 ist ungeklärt und zerstört die forensische Sauberkeit.** Die
     S3-Aggregate divergieren ~3.2× zwischen iter-3 (-2113 $) und iter-4
     (-6857 $) bei nur +9 Trades (E-17), und der Widerspruch ist „nicht eindeutig
     auflösbar ohne Roh-PnL-Export" (E-17). Eine der genannten Ursachen ist
     explizit, dass **Hard-Stop-Exits schlechtere Realisierungen erzeugen als
     natürliche Exits** (E-17, Hypothese b). Wenn niemand weiß, warum dieselbe
     Strategie sich pro Run verdreifacht, ist die Behauptung „der Verlust ist
     forensisch LOKALISIERT" (Advocate-Eingangsthese) schlicht nicht haltbar — er
     ist nicht einmal stabil reproduzierbar.
  3. **INC-03 trifft das Entry, nicht den Exit.** Das Übertriggern (50-62
     Trades/24 h statt 3 Settlements, E-12/INC-03) ist ein ENTRY-Defekt: der
     Q90-Pressure-Filter „trennt nicht auf Settlement-Qualitätsniveau" (C-22). Das
     ist genau die Dimension, die der Advocate dem Exit zuschreiben will — sie
     liegt aber im Entry. Der Advocate gesteht das in A-2 selbst zu.
- **Spot/Optionen:** Zustimmung — kein direkter Anwendungsfall; Optionen ohnehin
  durch INC-04 blockiert.
- **Härtester Einwand:** Der Exit-Bug (E-07) ist bewiesen, aber „der Verlust sitzt
  im Exit" ist ein unbewiesener Schluss — die Roh-Edge ist VOR jedem Exit negativ
  (E-09) und E-17 zeigt, dass nicht einmal die Verlusthöhe reproduzierbar ist.
- **Minimale Bedingung für PILOT (statt DROP):** Ich akzeptiere PILOT — aber NUR
  konditioniert auf E-15 mit einem schärferen Gate als der Advocate fordert: iter-5
  muss (a) aggregate mean pnl_bps netto > 0 liefern UND (b) den E-17-Widerspruch
  auflösen (Roh-PnL-Export beider Runs, damit der Sprung erklärt ist). Liefert
  E-15 nur netto-positiv ohne E-17-Klärung, bleibt das Ergebnis ein
  nicht-interpretierbarer Einzel-Run (L0, GM-1) → dann PARK, nicht ADOPT.

---

### S-2 → A-2 (C-22: einziges real feuerndes Entry, Beitrag nie negativ gemessen)

- **Steelman:** Korrekt — C-22 ist das einzige real feuernde Entry-Signal des
  Registers (N=213), der Clamp-Mechanismus ist ein API-Faktum und kein gefitteter
  Parameter (C-22), und sein direktionaler Eigenbeitrag wurde nie sauber isoliert
  (Matrix: „weder positiv noch negativ isoliert nachgewiesen", C-22-Begründung).
- **Futures:** „Nie sauber negativ gemessen" schneidet in BEIDE Richtungen — es
  ist genausowenig je positiv gemessen. Das ist kein Advocate-Argument, das ist
  die Definition von UNTESTED-im-relevanten-Sinn. Schärfer: Der Advocate gesteht
  in A-2 selbst zu, dass INC-03 „ein echter Entry-Defekt" ist und die These
  „Pressure identifiziert die 3 echten Settlement-Releases" empirisch beschädigt
  ist (Zeile 83-89). Damit kollabiert seine eigene Stützhypothese aus A-1 (Verlust
  liegt im Exit): Wenn das Entry auf Mikro-Druck statt Settlement schießt, ist die
  negative Roh-Edge (E-09) die naheliegendste Erklärung **Entry-seitig**, nicht
  exit-seitig. Der „deterministische Mechanismus" rettet nichts: Bybit clampt
  Funding deterministisch — dass sich der geklemmte Druck *handelbar und gerichtet*
  nach Settlement entlädt, ist die eigentliche Behauptung, und die ist UNTESTED.
  Determinismus des Mechanismus ≠ Determinismus des Trade-Outcomes.
- **Spot/Optionen:** Zustimmung (n/a).
- **Härtester Einwand:** „Beitrag nie negativ gemessen" ist symmetrisch — er wurde
  auch nie positiv gemessen, und der einzige Funnel-Befund (INC-03-Übertriggern)
  spricht GEGEN die Settlement-Selektivität, die das Signal angeblich trägt.
- **Minimale Bedingung für PILOT:** Der vom Advocate selbst vorgeschlagene
  Entry-Isolations-Test (Q97/Q99 + strikte Settlement-Fenster-Bindung, Roh-Edge > 0
  vor Friktion auf ≥ 3 Symbolen) ist akzeptabel — aber er MUSS gegen
  `n_settlement_events` gebunden werden (A-3), sonst misst er wieder die entartete
  HF-Variante. Und FDR-korrigiert über die getesteten Quantil-Varianten (GM-2),
  sonst ist „> 0 auf 3 Symbolen" ein unkorrigierter Mehrfach-Test.

---

### S-3 → A-3 (Settlement-Framing nie fair getestet; Übertriggern als Mess-Artefakt)

- **Steelman:** Der stärkste Punkt: Der Replay handelt auf ~7-8 % der Ticks
  innerhalb breiter 30-min-Fenster auf jeden Q90-Spike (E-12, `n_in_window`), statt
  auf die 3 diskreten Settlement-Momente — er testet also eine andere Strategie als
  die behauptete (E-12/INC-03). „Negatives Ergebnis einer entarteten Implementierung
  ≠ Widerlegung des Konzepts" ist regelkonform.
- **Futures:** Hier dreht sich das Argument gegen den Advocate, und er sieht es in
  A-3 selbst (Zeile 111-116): Wenn der scharfe Settlement-Trade nur 3×/Tag feuert,
  ist „wenige Trades × kleine Edge − fixe Friktion" strukturell negativ — dann ist
  das Übertriggern kein Bug, sondern ein verzweifelter Versuch, überhaupt genug
  Trades für Edge zu sammeln, und das eigentliche Problem ist **fundamentale
  Edge-Knappheit**, nicht Filter-Schärfe. Genau das ist die wahrscheinlichere
  Lesart: Die Roh-Edge ist auf JEDEM Symbol negativ (E-09), bei N=19…62 pro Symbol
  — das ist nicht „zu wenig getestet", das ist 5× konsistent negativ. Das
  „nie fair getestet"-Argument ist nicht falsch, aber es ist eine
  Unentscheidbarkeits-Behauptung (GM-6: Fenster kann Settlement-Claims nicht
  falsifizieren, nur Nicht-Feuern zeigen) — und eine Unentscheidbarkeit begründet
  keinen PILOT, sie begründet bestenfalls „messen, falls billig".
- **Härtester Einwand:** Das schärfere Settlement-Framing reduziert N auf ~3/Tag
  und macht die fixe Friktion pro Trade tödlicher — der Advocate kann nicht
  gleichzeitig „Übertriggern ist das Problem" (A-3) und „mehr Schärfe rettet es"
  behaupten, ohne zu zeigen, dass die 3-Trade-Edge die 11-15-bps-Friktion schlägt.
- **Minimale Bedingung für PILOT:** identisch zu S-2 — Settlement-Event-gebundener
  Isolationstest, aber das Gate muss explizit zeigen, dass die scharfe (N-arme)
  Variante netto > 0 ist; wenn Schärfe die Edge nicht über Friktion hebt, ist die
  Edge-Knappheit bestätigt → DROP.

---

### S-4 → A-4 (C-37 Spread-Execution, der „Friction-Killer")

- **Steelman:** Korrekt und wichtig: C-37 ist der EINZIGE Claim im Register, der
  die Verlustursache direkt angreift (Friktion 11 → ~4 bps), statt am Signal zu
  drehen — bei -5.8 bps Roh-Edge (E-09) ist eine 7-bps-Friktionssenkung der einzige
  dokumentierte Hebel, der die Kernrelation „Friktion > Edge" überhaupt kippen kann
  (C-37-Randbefund). Das lasse ich als den strategisch wertvollsten Punkt des
  Clusters stehen.
- **Futures:** Aber: Der wichtigste Hebel ist der am wenigsten validierte — das
  gesteht der Advocate selbst (Zeile 140-145: „4-bps-Wert ist ungemessen, PRD-
  Referenz"). Mein scharfer Zusatz, den der Advocate NICHT adressiert:
  **Adverse Selection kollabiert die Maker-Fill-Quote genau im falschen Moment.**
  C-37 hängt an einer Maker-Quote ≥ 70 % (C-37/A-4). Aber Maker-Fills sind nicht
  zufällig verteilt: In schnellen Märkten wird eine Limit-Order genau dann gefüllt,
  wenn der Preis gegen einen läuft (der informierte Flow nimmt die Maker-Liquidität),
  und genau dann NICHT, wenn der Trade funktioniert hätte. Das ist dieselbe Logik,
  die das Register an anderer Stelle als Kyle-λ/VPIN-Toxic-Flow führt (C-25). Für
  einen Settlement-/Druck-Release-Trade (C-22) ist das fatal: Die Pressure-Release-
  Bewegung IST der schnelle Markt — d. h. die Bedingung, unter der C-22 feuern soll,
  ist exakt die Bedingung, unter der die Maker-Quote einbricht und man auf
  Taker-Kosten (11 bps) oder Queue-Risiko zurückfällt (A-4 nennt das, unterschätzt
  aber die Korrelation). Die realisierte effektive Friktion ist dann nicht 4 bps,
  sondern ein gewichteter Mix, der bei adverser Selektion gegen die Taker-Wand
  zurückkonvergiert. Der 4-bps-Wert ist also nicht nur ungemessen — er ist in genau
  dem Regime, in dem der Cluster handeln will, optimistisch verzerrt.
- **Spot:** Zustimmung mit Einschränkung — Spot als Hedge-/Gegenbein ist ein
  funktionaler Einsatz ohne eigenes Alpha (A-4 sagt das selbst). Das ist kein
  Spot-Argument FÜR den Cluster, nur eine Mechanik.
- **Härtester Einwand:** Maker-Fill-Quoten sind adversariell selektiert — gefüllt
  wird man bevorzugt, wenn der Trade verliert; die 70-%-Annahme ist genau im
  schnellen Settlement-Regime (in dem C-22 feuert) am unwahrscheinlichsten, womit
  die effektive Friktion zur 11-bps-Wand zurückkonvergiert.
- **Minimale Bedingung für PILOT:** Der Live-Mikro-Pilot (A-4) ist richtig, aber
  das Gate muss die Maker-Quote KONDITIONAL messen — Maker-Quote ≥ 70 % UND
  realisierter Round-Trip ≤ 6 bps **speziell in den Pressure-Release-Fenstern**
  (nicht im Tagesdurchschnitt, wo ruhige Phasen die Quote schönen). Nur dann ist
  C-37 für diesen Cluster relevant. Verfehlt → C-37 DROP und der Cluster bleibt
  friction-bound (mit dem Advocate einig).

---

### S-5 → A-5 (C-32 Funding-Contrarian 24h, „billigster falsifizierbarer Test")

- **Steelman:** Der saubere Punkt: C-32 trennt Horizont von Mechanismus — auf 24h
  ist 11 bps Friktion eine Randnotiz statt eine Wand, und der Test ist REST-only auf
  CONFIRMED-Datenströmen, sofort laufbar ohne Aufzeichnungs-Vorlauf (A-5/C-32). Als
  *billiger* Test ist das real, und das gestehe ich zu.
- **Futures:** Aber „billig falsifizierbar" ≠ „verdient PILOT-Status jetzt". Drei
  Einwände:
  1. **Es gibt NULL Evidenz.** C-32 ist UNTESTED (Matrix), beruht ausschließlich
     auf einer PRD-Behauptung — der Advocate gesteht „null Evidenz, nur ein
     plausibler Mechanismus" zu (Zeile 171-176). Im Sinne der GRUNDHALTUNG
     („Evidenz schlägt Idee") rangiert C-32 damit hinter jedem belegten Befund.
  2. **Die Quelle selbst erwartet Signal-Zerfall.** C-32 erwartet „schnellen
     Signal-Zerfall unter dem Carry-Kompressions-Regime seit 2024" (C-32-Note), und
     INC-05 drückt auf alle unkonditionalen Direktional-Ansprüche (Richtungs-AUC
     ≈ 0.50). Das heißt: Die Quelle prognostiziert selbst, dass das Edge heute
     wahrscheinlich weggearbitragt ist. Ein Test, dessen eigener Autor das negative
     Ergebnis erwartet, ist kein vielversprechender Kandidat — er ist eine
     Pflicht-Falsifikation.
  3. **Multiple-Testing (GM-2) ist hier am gravierendsten.** C-32 ist eine von
     einer ganzen Familie von Kalender-/Carry-Regeln (C-22, C-23, C-24, C-32, C-38,
     CS-12 — alle auf demselben Funding-Settlement-Mechanismus). Plus die bereits
     verworfenen: S1/S2 REFUTED, S4/S5 Mess-Lücken. Wenn man genug Funding-Regeln auf
     denselben ~3 Settlements/Tag testet, findet man per Zufall eine, die in EINEM
     180-Tage-Fenster > 0 liefert. Ohne FDR-Korrektur über die gesamte
     Carry-Regel-Familie (die in KEINER Quelle existiert, GM-2) ist ein einzelnes
     „Return > 0 in 2 Fenstern" ein unkorrigierter Mehrfach-Treffer.
- **Härtester Einwand:** C-32 ist UNTESTED, die Quelle erwartet selbst Zerfall
  (Carry-Kompression + INC-05), und es ist eine von ≥ 6 Carry-Regeln auf demselben
  Mechanismus ohne jede FDR-Korrektur — der billigste Test ist nicht derselbe wie der
  aussichtsreichste.
- **Minimale Bedingung für PILOT:** Akzeptabel als *billiger Falsifikations-Lauf*
  (nicht als Edge-Kandidat), unter einer Bedingung, die der Advocate nicht nennt:
  das Erfolgs-Gate muss FDR-korrigiert über alle parallel getesteten
  Carry-/Funding-Regeln sein, und „Return > 0 nach Kosten in ≥ 2 × 180-Tage-Fenstern
  OOS" (C-32-Gate) muss das harte Abbruchkriterium behalten (ein Fenster ≤ 0 →
  DROP). Sonst PARK.

---

### S-6 → A-6 (CS-12 Funding-Uhr K2, „spezifizierter Reparatur-Bauplan")

- **Steelman:** Fair: CS-12 ist nicht spekulativ aus dem Nichts, sondern die
  ingenieurmäßige Integration zweier forensisch isolierter Defekte — Friktion via
  C-37, Übertriggern via C-08-Regime-Gate (A-6/Matrix CS-12).
- **Futures:** CS-12 ist eine Hypothek auf zwei andere Hypotheken. Es erbt ALLE
  CS-03-Befunde (friction-bound E-09, Q90-Übertriggern INC-03) UND baut auf zwei
  Bausteinen, die beide ungeprüft oder gescheitert sind:
  1. **C-37 ist ungemessen** (siehe S-4, adverse Selektion).
  2. **C-08 (BOCPD) war in S3 ein bewiesener No-Op** — feuerte im gesamten Fenster
     KEINEN einzigen Changepoint (E-12). Der Advocate gesteht das zu (Zeile 199-205:
     „ich baue auf ein Modul, dessen einziger Praxistest ‚nichts getan' lautet").
     Das Regime-Gate, das das Übertriggern fixen soll, hat in seinem einzigen Test
     genau nichts getan. Zwar im GM-6-kurzen Fenster ohne garantierten Regime-Bruch
     (E-12/Matrix C-08) — aber das macht C-08 UNTESTED, nicht „funktionsfähig". CS-12
     stapelt also: ungemessenes C-37 × No-Op-C-08 × friction-bound-C-22 × pending
     E-15. Vier offene Faktoren, deren Produkt positiv sein muss.
- **Spot:** wie A-4 (Spread-Markt-Beine), kein eigenständiges Argument.
- **Härtester Einwand:** CS-12 ist das Produkt von vier ungelösten Größen (E-15
  pending, C-37 ungemessen, C-08 No-Op, C-22 friction-bound) — das ist keine
  Reparatur, das ist eine Verkettung von vier Wetten.
- **Minimale Bedingung für PILOT:** Strikt sequenziell, wie der Advocate selbst sagt
  (Zeile 206-208): CS-12 wird ERST aktiviert nach (a) E-15-positiv UND (b)
  C-37-Pilot-positiv; dann C-08 gegen ein Fenster MIT dokumentiertem Regime-Bruch
  (DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 %, C-08-Gate). Vor diesen drei
  Vorbedingungen: PARK, nicht PILOT. CS-12 darf keine eigenen Ressourcen ziehen,
  bevor seine Bausteine stehen.

---

### S-7 → A-7 (C-38 TFT mit Known-Future-Funding)

- **Steelman:** Echter Punkt: Funding-Settlement-Zeitpunkt und -Intervall sind
  deterministisch vorab bekannt (Plattform-Fakt) — ein TFT mit Known-Future-Inputs
  nutzt einen seltenen, strukturellen Informationsvorsprung, der in Finanzzeitreihen
  fast nie existiert.
- **Futures:** Der Informationsvorteil ist real, aber er ist KALENDARISCH, nicht
  DIREKTIONAL. Zu wissen, *wann* das Settlement ist, sagt nichts darüber, *in welche
  Richtung* sich der Druck entlädt — und genau die Richtung ist das, was C-38
  prognostizieren müsste. INC-05 ist hier vernichtend: klassische Features liefern
  Richtungs-AUC ≈ 0.50 (Münzwurf), und C-38 beansprucht AUC > 0.55 (C-38/A-7). Ein
  DL-Modell auf ein noch unbestätigtes Basissignal (C-22, selbst nur PARTIAL/SUSPECT)
  zu setzen, ist das Stapeln von Modell-Komplexität auf Signal-Unsicherheit — der
  Advocate nennt es selbst „die schwächste Position des Clusters" (Zeile 225-230).
  Dem stimme ich vollständig zu.
- **Härtester Einwand:** Der Vorab-Vorteil ist kalendarisch (wann), die Aufgabe ist
  direktional (wohin) — und direktional ist die Baseline laut INC-05 ein Münzwurf.
- **Minimale Bedingung für PILOT:** Keine — **PARK ist korrekt** (mit dem Advocate
  einig, A-7). Gate erst öffnen nach C-22-Live-Proof; vorher zieht C-38 nur
  Ressourcen von A-1/A-2 ab (Opportunitätskosten). Ich gehe sogar weiter: C-38 ist
  ein DROP-Kandidat, falls C-22 in E-15 nicht netto-positiv wird, weil dann das
  Basissignal fehlt, auf dem C-38 überhaupt aufsetzt.

---

### S-8 → A-8 (C-23 Basis-Convergence / C-24 Kalman-Premium)

- **Steelman:** Der robusteste Mechanismus-Punkt des Clusters: Basis = (Mark−Index)/
  Index zieht mechanisch gegen 0, weil Funding genau das erzwingt — das ist eine
  No-Arbitrage-Relation, keine Verhaltensannahme, und C-23 wurde im einzigen Replay
  durch eine redundante Gate-Verdrahtung (`sign(pressure)≡-sign(basis)`, E-12) gar
  nie auf seinen Eigenbeitrag geprüft. „Implementierungs-Defekt ≠ Konzept-Defekt"
  ist hier am stärksten, weil die Redundanz code-reading-belegt ist (E-12).
- **Futures:** Aber der Advocate liefert die Widerlegung selbst (Zeile 258-260):
  „Mechanisch erzwungen ≠ handelbar nach Kosten." Die Konvergenz KANN real und
  trotzdem kleiner als 11-15 bps Friktion sein — und das ist im Settlement-Fenster
  der wahrscheinliche Fall: Eine Basis, die schon bei 0.08 % (C-23-Threshold) gegen
  0 zieht, hat schlicht nicht viel bps-Spielraum, bevor die Friktion sie auffrisst.
  Die No-Arbitrage-Relation ist genau deshalb robust, WEIL sie klein ist — ein
  großer, handelbarer Basis-Spread wäre selbst eine Arbitrage-Anomalie. C-24
  (Kalman) ist zudem rein spekulativ, „kein eigener Befund" (Matrix C-24) — der
  Advocate räumt das ein.
- **Spot:** Hier hat der Advocate seinen einzigen genuinen Spot-Touchpoint: Basis
  IST per Definition die Perp-Spot-Relation, ein Convergence-Trade ist strukturell
  ein Spot-Perp-Paar (A-8). Das lasse ich als korrekt stehen — ABER es ist ein
  Mechanik-Punkt, kein Edge-Punkt: Das Spot-Bein trägt kein eigenes Alpha, es ist
  das Hedge-Gegenbein. Und dasselbe Friktions-Argument gilt doppelt: zwei Beine =
  zwei Round-Trips = ~22 bps Friktion gegen eine sub-0.08-%-Konvergenz.
- **Härtester Einwand:** Die Basis-Konvergenz ist robust, WEIL sie klein ist — eine
  erzwungene No-Arbitrage-Relation lässt per Definition kaum bps übrig, und im
  Zwei-Bein-Spot-Perp-Trade verdoppelt sich die Friktion gegen einen ohnehin engen
  Spread.
- **Minimale Bedingung für PILOT:** C-23 standalone als reines Basis-z-Score-Signal
  verdrahten (entkoppelt vom Pressure-Gate, A-8), und das Gate MUSS die Konvergenz
  in bps gegen die effektive Round-Trip-Friktion messen — Hit-Rate ≥ 58 % nach
  Kosten im Settlement-Fenster über ≥ 200 Events (A-8/C-23-Gate). Solange nicht
  gezeigt ist, dass die Konvergenz > Friktion ist, bleibt C-23 PARK. C-24 strikt
  nachrangig zu C-23 (kein eigener Befund) → PARK/DROP.

---

## Zusammenfassung Skeptic — Gegen-Tendenz je Ansatz × Markt

| Claim | Spot | Futures | Optionen | Skeptic-Kern |
|---|---|---|---|---|
| CS-03 (A-1) | n/a | PILOT *nur* wenn E-15 netto>0 **und** E-17 geklärt; sonst PARK | n/a | „Verlust im Exit" unbewiesen; Roh-Edge schon vor Exit neg (E-09) |
| C-22 (A-2) | n/a | PILOT nur mit settlement-gebundenem, FDR-korr. Isolationstest | n/a | „nie negativ gemessen" ist symmetrisch; INC-03 trifft Entry |
| C-37 (A-4) | Mechanik | PILOT nur mit *konditionalem* Maker-Quoten-Gate im Release-Fenster | n/a | Adverse Selektion bricht Maker-Quote genau im C-22-Regime |
| C-32 (A-5) | n/a | PILOT nur als FDR-korr. Pflicht-Falsifikation; sonst PARK | n/a | UNTESTED, Quelle erwartet Zerfall, ≥6 Carry-Regeln (GM-2) |
| CS-12 (A-6) | Mechanik | PARK bis E-15+C-37 positiv; dann PILOT | n/a | Produkt aus 4 offenen Faktoren (C-08 war No-Op, E-12) |
| C-23 (A-8) | PARK | PARK→PILOT nur wenn Konvergenz>Friktion gezeigt | n/a | Robust WEIL klein; 2-Bein = ~22 bps gegen <0.08% |
| C-24 (A-8) | n/a | PARK/DROP | n/a | Kein eigener Befund (Matrix) |
| C-38 (A-7) | n/a | PARK (DROP falls C-22 in E-15 scheitert) | n/a | Vorteil kalendarisch, Aufgabe direktional (INC-05) |

**Kernbotschaft an den Judge:** Ich teile die Diagnose des Advocaten, dass dieser
Cluster der einzige mit echtem Kipp-Punkt in Reichweite ist — aber der Kipp-Punkt
hängt an ZWEI ungemessenen Größen (E-15 netto-Edge, C-37 4-bps-Maker), von denen
beide positiv ausfallen müssen, und eine dritte ungeklärte (E-17). „PILOT für alles"
übersetzt eine Hypothesen-Verkettung in einen Aktionsplan, ohne dass ein einziger
positiver L0-Befund (geschweige L1+) für irgendeinen der acht Claims existiert.
Mein Urteil: CS-03/C-22/C-37 verdienen je EINEN scharf konditionierten PILOT (die
drei messbaren, billigen Tests); C-32 nur als FDR-korrigierte Pflicht-Falsifikation;
CS-12/C-23/C-24/C-38 sind PARK bis ihre Vorbedingungen geliefert haben. Kein ADOPT
für irgendetwas in diesem Cluster, solange GM-1 (alles L0) gilt.

*Ende Skeptic-Part.*
