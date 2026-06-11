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
