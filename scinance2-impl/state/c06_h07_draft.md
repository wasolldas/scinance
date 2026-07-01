# ENTWURF H-07 — C-06 NICHT-triviale Cross-Sectional Ergodic Mean-Reversion (KAPITALFREI)

> **Status dieses Dokuments:** ENTWURF eines Research-Analysten. **NICHT registriert.**
> Der Orchestrator/gate-auditor prüft und entscheidet über die Aufnahme in
> `hypothesis_registry.md`. Dieses Dokument fasst NUR ein `c06_h07_draft.md` an;
> es ändert KEINE Registry, KEIN gate_log, KEINE decisions, KEINEN Code.
> **Sprache Deutsch, Erstellt 2026-07-01.**
>
> Vorlektüre-Quellen durchgängig: `scinance2-impl/state/wave3_survey.md §2.3`,
> `FINAL_PRD.md §4 (Z.129) / §6 (Z.197-205) / §7`, `edge-reconciliation/input/FINAL_PRD.md
> Z.437-454 (M13) + Z.1055-1072 (Strategie 5, §7.5)`,
> `edge-reconciliation/input/PRD_VS_REALITY_SYNTHESIS.md §7.5-Absatz (Z.159-174) + §2.1
> Friction (Z.180-184)`, `edge-reconciliation/input/research_notes.md Z.93-100 (XRP-April-
> Survivorship) / Z.155 (sub-10bp-Warnung)`, Stil-/Disziplin-Vorlagen
> `hypothesis_registry.md §H-06 / §H-05b / §H-04b + Registry-Disziplin §1-8`.

---

## 0. Kernbefund vorweg (für den eiligen Leser)

**H-07 ist ehrlich registrierbar — als KAPITALFREIES Cross-Sectional-Mess-Gate mit
NICHT-Trivialitäts-Anker (konditionale Verstärkung gegen einen unkonditionierten
Panel-Baseline), mit ≤ 3 vorab fixierten Konditionierungs-Achsen und OHNE Schwellen-
oder Horizont-Suche.** Der ehrliche A-priori (research_notes-Survivorship + PRD-§6-
REFUTED-Historie) ist **DROP**. Das Gate ist bewusst so gebaut, dass es DROP ehrlich
zulässt und WEITER schwer macht. Ein voller Tradability-Test wäre eine spätere,
NICHT hier registrierte und NICHT implizierte **H-07b** (analog H-04→H-04b,
H-05b→H-05c).

Die Registrierbarkeit hängt an genau einer Bedingung, die dieser Entwurf erfüllt:
Alle Freiheitsgrade (Panel, Bar-Länge, Lookback L, Z_THRESH, Crash-Dezil, Horizont-
Menge, FDR-Familie, Fenster) werden **hier, VOR jedem Datenanfassen, gebunden** und
stammen aus PRD/Literatur — es gibt **keine Suche** über sie. Bräuchte eine ehrliche
Formulierung eine Schwellen-/Achsen-Suche, wäre H-07 **nicht** registrierbar (Variante-A-
Forking-Paths-Risiko, Survey §2.3). Dieser Fall tritt hier NICHT ein — siehe
Ehrlichkeits-Check (§B).

---

## H-07 · C-06 NICHT-triviale Cross-Sectional Ergodic Mean-Reversion (Welle-3-Pilot, KAPITALFREI)

- **Registriert:** ENTWURF, 2026-07-01 (WP-0 Welle 3, VOR Lauf-Start; Gate aus
  PRD §4 Z.129 wörtlich + PRD §6 Z.203-205 REFUTED-Verbot + edge-reconciliation
  FINAL_PRD §7.5 / M13 Entry-Bedingung wörtlich, konservativ abgeleitet wo PRD stumm.)
  *Der Registrierungs-Datumseintrag wird vom Orchestrator gesetzt, nicht hier.*

- **Quelle / Herkunft:** PRD §4 Z.129 wörtlich: „**C-06 (NICHT-triviale MR) … nach
  Welle 1 … FDR-korrigiertes Gate für separates Folge-Signal (simple Sign-Flip-MR
  durch E-04 bereits widerlegt) … trivial-MR-Lesart verboten; ohne neue Hypothese
  kein PILOT.**" PRD §6 (Z.203-205) verbietet die Sign-Flip-Rehabilitierung explizit:
  „**Die simple Sign-Flip-MR-Rehabilitierung von C-06 ist durch E-04 bereits
  gescheitert … ein C-06-PILOT braucht ein nachweislich anderes Signal … kein Re-Test
  der S2-Richtungsthese und keine simple Invertierung.**" Die konkrete Signal-Definition
  (Cross-Sectional-z, Ergodizitätsverletzung, |z|>2.5, Renyi-TE-Filter, HMM-Crash-Veto)
  stammt wörtlich aus edge-reconciliation FINAL_PRD M13 (Z.437-454) + Strategie 5 §7.5
  (Z.1055-1072). Das ist **KEIN Data-Snooping in Welle-1/2-Daten**: die Hypothese ist
  aus dem PRD-Literatur-Text abgeleitet (Lo & MacKinlay 1990, M13-Herkunft), NICHT aus
  einem in Welle-1/2 post-hoc beobachteten Effekt (anders als H-05b). Es gibt daher
  keine „Entdeckungszelle" zu exkludieren; der Data-Snooping-Guard ist hier ein
  **Forking-Paths-Guard** (Parameter vorab gebunden, keine Achsen-/Schwellen-Suche),
  nicht ein Entdeckungszellen-Ausschluss.

- **Hypothese:** Auf dem 5-Symbol-Perp-Panel (BTC/ETH/SOL/BNB/XRP) ist die
  Cross-Sectional-Reversion (die reversions-signierte Forward-Rendite eines über-
  dehnten Symbols) **im vorab fixierten Über-Dehnungs-/Nicht-Crash-Regime signifikant
  STÄRKER als im unkonditionierten Panel-Baseline**. Formal: die konditionale
  reversions-signierte Forward-Rendite ist (a) positiv, (b) FDR-signifikant von Null
  verschieden gegen eine Surrogate-Null, (c) über ≥ 2 disjunkte Fenster konsistent,
  UND (d) **magnitude-mäßig echt größer als der unkonditionierte Baseline** (der
  Nicht-Trivialitäts-Anker). Punkt (d) ist das, was H-07 kategorial von der durch
  E-04 widerlegten unkonditionierten Sign-Flip-MR trennt: die These ist NICHT „MR
  existiert" (trivial, E-04-verboten), sondern „**die Reversion wird durch das vorab
  fixierte Regime signifikant verstärkt**". **Ausschließlich Mess-Gate für Existenz +
  Verstärkung** — KEINE Behauptung über Handelbarkeit (siehe KAPITALFREIHEIT).

- **NICHT-Trivialitäts-Konstruktion (zentral — der Unterschied zu E-04):**
  E-04 hat die **unkonditionierte** Sign-Flip-MR widerlegt („Symbol weit vom Ensemble-
  Mittel → revertiert", ohne Regime-Konditionierung). Diese Lesart ist PRD-§6-verboten.
  H-07 misst NICHT diese unkonditionierte MR als Pass-Kriterium, sondern die
  **Differenz** zwischen konditionierter und unkonditionierter Reversions-Magnitude.
  Der unkonditionierte Panel-Baseline ist ausdrücklich Teil der Messung — er ist der
  **Null-Anker**, gegen den die Verstärkung getestet wird. Fällt die Verstärkung weg
  (konditioniert ≈ unkonditioniert), ist H-07 **DROP** — selbst wenn eine schwache
  unkonditionierte MR existiert (denn genau die ist die E-04-verbotene Trivial-Lesart,
  hier NICHT als Erfolg zählbar).

- **Panel & Datenbasis (vorab fixiert):**
  - **Panel:** 5-Symbol-Perp **BTC/ETH/SOL/BNB/XRP** (Programm-Standardpanel, H-01/
    H-05/H-05b-Konvention; identisch zum iter-3-Panel der research_notes §7.5).
    **Bewusste Abweichung von M13-„Top-20":** das PRD-M13-Top-20-Universum ist NICHT
    verfügbar (Harvester-Backfill deckt nur diese 5 Symbole), und die research_notes
    §7.5 (Z.173) warnt selbst, dass 5 BTC-korrelierte Symbole „too tightly constrained"
    sein können, um |z|>2.5 überhaupt zu produzieren. Das ist ein bekanntes,
    **ehrlich benanntes Power-Risiko** (nicht ein Forking-Path): wenn |z|>2.5 auf 5
    Symbolen zu selten feuert, fällt H-07 an mangelnder N-Zahl → DROP (harte
    Mindest-Ereigniszahl, s.u.). Es wird KEIN Symbol nachgeladen, um N zu erreichen.
  - **Datenbasis:** read-only Harvester-Backfill (Junction `data/harvest/`, Quelle
    `data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/`, Schema-validiert),
    identisch zu H-05b/DEC-15. Der Harvester hat KEIN fertiges `kline` — daher wird
    aus `publicTrade` der **Last-Price pro Bar** gebildet (letzter Trade-Preis im Bar-
    Intervall) und daraus der Bar-Return. Read-only, keine neue Aufzeichnung.
  - **Bar-Länge:** **5 min** vorab fixiert. Begründung (konservativste, forking-paths-
    ärmste Wahl): (1) Die M13/§7.5-Ergodizitäts-Reversion ist ein L3-Konzept auf
    „recent time-average" (M13 nutzt „Rolling 1h Returns"), also klar sub-täglich aber
    NICHT sub-Sekunde; 5-min-Bars sind grob genug, um den Mikrostruktur-/Queue-Jump-
    Tax-Bereich (E-03/E-04, sub-10-Sekunden, PRD_VS_REALITY §85) zu MEIDEN — genau
    dort lebt die E-04-widerlegte Trivial-MR, die H-07 NICHT wiederholen darf. (2)
    5-min-Bars liefern über ein 300k-Tick-Fenster (≈ 1-2 Tage je Symbol, DEC-15-Export)
    genügend Bars für Cross-Sectional-z + Forward-Horizonte. (3) Es wird **nur EINE**
    Bar-Länge getestet (keine {1,5,15}-Bar-Suche) — jede zusätzliche Bar-Länge wäre
    ein Freiheitsgrad. Wo das PRD zur Bar-Länge stumm ist, wählen wir konservativ 5 min
    und markieren sie als vorab fixiert.

- **z-Definition (vorab fixiert, aus M13 wörtlich):**
  - Zeit-Mittel je Symbol über Lookback **L = 12 Bars = 60 min** (M13 Z.449 wörtlich
    „Rolling 1h Returns pro Symbol", auf 5-min-Bars = 12 Bars). L ist aus M13-Literatur
    übernommen, **NICHT gesucht**. Formal (M13 Z.442-444):
    `E_t[X_i] = (1/L) Σ_{s=t-L..t} R_{i,s}` (Zeit-Mittel Symbol i über die letzten L
    Bar-Returns), `⟨X⟩_t = (1/N) Σ_j E_t[X_j]` (kontemporäres Ensemble-Mittel der N=5
    Symbol-Zeitmittel), `z_{i,t} = (E_t[X_i] − ⟨X⟩_t) / σ_cross,t` mit σ_cross,t =
    Cross-Sectional-Std der 5 E_t[X_j] zum Zeitpunkt t.
  - **Über-Dehnungs-Schwelle Z_THRESH = 2.5** (PRD §7.5 Z.1060 + M13 Z.446/451
    wörtlich „|z| > 2.5"). Vorab fixiert, **NICHT gesucht**.

- **Konditionierungs-Achsen (GENAU 2 vorab fixiert — bewusst nicht 3):**
  1. **Achse A — Über-Dehnung `|z_{i,t}| ≥ 2.5`** (M13/§7.5 wörtlich). Der Kern-
     Trigger. Ohne ihn keine Konditionierung.
  2. **Achse B — Nicht-Crash-Regime (HMM-Crash-Veto-Proxy):** Das Panel-realized-vol
     zum Zeitpunkt t liegt **NICHT im obersten Dezil** (Top-10 %) der Panel-realized-vol-
     Verteilung im jeweiligen Fenster. Panel-realized-vol = Summe der quadrierten
     kontemporären 5-Symbol-Bar-Returns über ein vorab fixiertes 15-min-Fenster
     (= 3 Bars), analog zur c07_pe-`forward_realized_vol`-Definition (DEC-12, „[t,
     t+15min]"). **Dezil-Schwelle vorab fixiert (oberstes Dezil = Crash-Proxy),
     NICHT gesucht.** Das ersetzt das schwere M9-HMM (§7.5 Z.1062 „HMM-State ≠
     High-Vol-Crash") durch einen kapitalfreien, deterministischen Vol-Dezil-Filter —
     die konservativste, freiheitsgrad-ärmste Operationalisierung des „Nicht-Crash"-
     Regimes, wo das PRD nur „HMM-State ≠ Crash" sagt und die HMM-State-Definition
     stumm lässt.
  - **KEINE dritte Achse.** Der **Renyi-TE-Filter (M17, §7.5 Z.1061 „Renyi-TE(BTC→Alt)
    > 0.05")** wird **bewusst WEGGELASSEN**. Begründung (Forking-Paths-Minimierung):
    (a) Renyi-TE ist ein schweres Modul (eigener Schätzer, Bandbreiten-/α-Parameter,
    Surrogate) — es brächte MEHR freie Parameter, nicht weniger; (b) jede TE-Variante
    (α, Lag, Bin) würde die FDR-Familie F-XMR aufblähen; (c) H-04/GL-006 hat gerichtete
    BTC→Alt-Information bereits als messbar-aber-nicht-tradable-über-30-60s befunden —
    ihn als DRITTE Konditionierungs-Achse einzuziehen erhöht die Freiheitsgrade ohne
    klaren Nicht-Trivialitäts-Gewinn. **Weniger Achsen = ehrlicher** (Survey §2.3:
    „max 2-3 vorab fixierte Regimes, sonst ist das Gate fingiert"). Wir bleiben bei 2.
    Ein späteres H-07c könnte den TE-Filter als eigene, vorregistrierte Achse prüfen —
    hier NICHT, und durch das WEITER NICHT impliziert.

- **Reversion-Messung (nicht-direktional, kapitalfrei, vorab fixiert):**
  - **Forward-Return** je über-dehntem (i,t)-Ereignis über Horizonte **h ∈ {1, 3, 6}
    Bars** (= 5 min, 15 min, 30 min bei 5-min-Bars). Kleine, vorab fixierte Menge;
    **jeder Horizont zählt einzeln in die FDR-Familie F-XMR**. (Menge aus M13-Skala
    abgeleitet: sub-täglich, oberhalb der Mikrostruktur-Zone; h=6 Bars = 30 min bleibt
    deutlich unter dem §7.5-Time-Stop von 24 h. KEINE Horizont-Suche über diese 3
    hinaus.)
  - **Reversions-Signierung:** `rev_ret_{i,t,h} = −sign(z_{i,t}) · R_{i, t→t+h}` — die
    Forward-Rendite in Reversions-Richtung (über-gedehntes Symbol positiv-z → erwartete
    negative Forward-Rendite zählt als positive Reversion). Nicht-direktional im Sinne
    von „keine Long/Short-Position, kein PnL" — nur die vorzeichenbereinigte Mess-Größe.
  - **Statistik je Zelle (Symbol × Fenster × h × {konditioniert | Baseline}):**
    mittlere reversions-signierte Forward-Rendite `μ_rev`. **Surrogate-Null:**
    Block-Shift/Permutation der Forward-Renditen gegen die z-Serie (Zerstörung der
    z→forward-Kopplung, Erhalt der marginalen Autokorrelation via Block-Bootstrap,
    `n_surrogates = 200` analog H-03-Nachtrag/H-06), Permutations-p für „μ_rev > 0".
  - **Baseline (Nicht-Trivialitäts-Anker):** dieselbe `μ_rev`-Statistik über ALLE
    (i,t)-Bars des Panels OHNE Konditionierung (kein |z|≥2.5-Filter, kein Vol-Dezil-
    Filter) — das ist die unkonditionierte, E-04-verbotene Trivial-MR-Lesart, hier NUR
    als Vergleichs-Nullanker geführt, NIE als Pass-Kriterium.

- **Gate (vorregistriert, wörtlich, mit Nicht-Trivialitäts-Anker):**
  - **WEITER (konditionale Verstärkung nachgewiesen):** ALLE folgenden Bedingungen
    gemeinsam:
    1. **Vorzeichen/Existenz:** konditionierte `μ_rev` **> 0** (echte Reversion, kein
       Momentum) UND
    2. **Signifikanz:** Surrogate-`p ≤ 0.05` nach **BH-FDR α = 0.10** über die NEUE
       Familie **F-XMR** (alle h × Fenster × ggf. Zellen) UND
    3. **≥ 2-Fenster-Konsistenz:** konditionierte `μ_rev > 0` UND FDR-signifikant in
       **≥ 2 disjunkten Fenstern** (DEC-15-Fenster A@2026-04-15 + B@2026-05-15) UND
    4. **NICHT-Trivialitäts-Anker (PFLICHT):** die konditionierte Reversions-Magnitude
       ist **signifikant größer als der unkonditionierte Panel-Baseline** — konkret:
       **Δμ = μ_rev,kond − μ_rev,baseline > 0 UND die 95 %-Block-Bootstrap-CIs von
       μ_rev,kond und μ_rev,baseline überlappen NICHT** (in ≥ 2 disjunkten Fenstern,
       für mindestens einen Horizont h, der auch Kriterien 1-3 erfüllt). Nicht-
       überlappende Bootstrap-CIs sind das primäre Verstärkungs-Kriterium (verteilungs-
       frei, kein zusätzlicher Schwellen-Freiheitsgrad); die reine Differenz Δμ>0 ist
       notwendig, aber allein NICHT hinreichend.
  - **DROP (jede EINE Bedingung reißt → DROP, hartes Ein-Fenster-Kriterium):**
    - Nicht-Trivialitäts-Anker verfehlt (CIs überlappen / keine konditionale
      Verstärkung) — **das ist der wahrscheinlichste DROP-Pfad und genau die
      E-04-/PRD-§6-verbotene Trivial-Lesart** — ODER
    - Vorzeichen falsch (konditionierte `μ_rev ≤ 0`: keine Reversion / Momentum) ODER
    - FDR-bereinigtes `p > 0.05` in ≥ 1 der ≥ 2 Fenster ODER
    - Verstärkung nur in **1** Fenster (Ein-Fenster-Zufall) ODER
    - **Mindest-Ereigniszahl verfehlt:** weniger als **30 über-dehnte (i,t)-Ereignisse
      pro Fenster** nach Konditionierung (harter N-Floor gegen das research_notes-§7.5-
      Power-Risiko „5 Symbole zu eng gekoppelt für |z|>2.5"; N<30 → DROP, kein
      Nachladen von Symbolen, keine Z_THRESH-Absenkung).
    - **Kein GRAUBEREICH.** Kein Nachverhandeln, keine Schwellen-Verschiebung.
  - **A-priori (ehrlich benannt):** Der starke A-priori ist **DROP**. research_notes
    (Z.155) markiert die XRP-April-Mean-Reversion-Winner explizit als
    **Survivorship-Bias** („no structural reason to expect them to keep doing so …
    would need to be verified on multiple months … per-trade edge sub-10 bp") — und
    das DEC-15-Fenster A liegt in genau diesem April-Regime. PRD §6 (E-04) hat die
    unkonditionierte MR widerlegt. Das Gate ist bewusst NICHT so gebaut, dass es ein
    WEITER erzwingt: der Nicht-Trivialitäts-Anker (nicht-überlappende CIs) + der
    ≥ 2-Fenster-über-Regimes-Zwang (April UND Mai) + der N-Floor machen ein WEITER
    schwer und ehrlich. **WEITER muss schwer und ehrlich sein** (H-04b-Doktrin).

  - **KAPITALFREIHEIT (verbindlich):** Dieses Gate prüft ausschließlich **Mess-Existenz
    einer regime-konditionierten Reversions-Verstärkung**, NICHT Tradability. Es darf
    **KEIN** Friction-Wand-Vergleich (11 bps), **KEINE** Edge-bps-/Slippage-Schwelle,
    **KEINE** Sharpe-/PnL-/Netto-Edge-Aussage nachregistriert werden. Das nimmt der
    research_notes-Survivorship-/sub-10bp-Warnung den Zahn: **wir behaupten KEINE
    handelbare Kante, nur eine Mess-Existenz plus Verstärkung.** Tradability wäre eine
    **NEUE H-07b** (eigener Registry-Eintrag, eigener Lauf, Friction-Wand + Latenz-
    Haircut + Bootstrap-Netto-Edge, analog H-04→H-04b / H-05b→H-05c) — hier NICHT
    registriert und durch das WEITER **NICHT impliziert**. Der A-priori für ein
    späteres H-07b wäre nach research_notes noch stärker DROP/PARK (sub-10bp-Edge unter
    15-bps-Friction-Wand).

- **Fenster/Datenbasis (vorab fixiert, aus DEC-15 übernommen):** **≥ 2 disjunkte
  Fenster**, deterministisch-chronologisch, keine diskretionäre Wahl. **Fenster A:**
  je Symbol die ersten Bars ab **2026-04-15 00:00:00 UTC**; **Fenster B:** ab
  **2026-05-15 00:00:00 UTC** (identisch zu H-05b/DEC-15 — dieselben sauberen,
  vollständig-DONE, weit-vor-der-Backfill/Live-Grenze liegenden Fenster; ~30 Tage
  Abstand, disjunkt). **WICHTIG (Panel-Synchronisation):** anders als H-05b (per-Symbol
  head(300k)) braucht Cross-Sectional-z eine **kontemporär synchronisierte Bar-Achse
  über alle 5 Symbole**. Daher werden je Fenster die Bars **über ein festes Kalender-
  Zeitfenster** (Fenster A: 2026-04-15..04-16 UTC; Fenster B: 2026-05-15..05-16 UTC;
  identische Bar-Timestamps über alle Symbole, fehlende Bars per forward-fill des
  Last-Price bis max. 1 Bar, sonst Bar verworfen) gebildet — NICHT per-Symbol-Tick-Zahl.
  Das ist die Panel-Replayer-Anforderung, die research_notes §7.5 (Z.171) als
  Infrastruktur-Voraussetzung benennt. Kalender-Fenster-Länge (2 Kalendertage je
  Fenster) vorab fixiert, keine diskretionäre Wahl.

- **FDR-Familie:** **F-XMR** (NEU, eigenständig — „Cross-sectional Mean-Reversion").
  Alle (Horizont h × Fenster × ggf. Konditionierungs-Zelle)-Varianten bilden EINE
  Familie. **BH-FDR α = 0.10** innerhalb F-XMR. **Über-Familien-Entscheidung:** Läuft
  H-07 allein, greift NUR die Familien-interne BH-FDR über F-XMR. **F-WAVE2 ist
  abgeschlossen und wird NICHT erweitert** (append-only, GL-006/007/008/010/011). Liefe
  H-07 später gemeinsam mit anderen neuen Pilots in einer Kohorte, wäre eine neue
  Über-Familie (analog F-WAVE2: erst Familien-intern BH-FDR, dann zweite BH-FDR über die
  Survivor) VOR jenem Lauf separat zu registrieren (identisch zur H-05b/H-04b-Regel).

- **Peso/L0-Regel:** Nicht-anwendbar (kapitalfrei). Stabilität über ≥ 2 disjunkte
  Fenster (über zwei verschiedene Kalendermonate/Regime, April UND Mai) plus der
  Surrogate-Test ersetzen den L2-Walk-Forward. Der ≥ 2-Fenster-über-Regime-Zwang ist
  hier zusätzlich der Survivorship-Guard (research_notes Z.155: „verified on multiple
  months") — ein reiner April-Effekt (XRP-Regime) reißt Fenster B (Mai) und fällt auf
  DROP.

- **Friction-Wand-Referenz:** ENTFÄLLT (kapitalfrei — siehe KAPITALFREIHEIT).

- **Status:** ENTWURF, NICHT registriert, Lauf NICHT gestartet. Lauf = Welle-3-WP für
  das C-06-Mess-Gate (Code-Bedarf-Vermerk unten — neues Modul `research/c06_xmr/`
  empfohlen). Urteil durch gate-auditor gegen den (nach Orchestrator-Prüfung)
  registrierten Eintrag; hartes Ein-Fenster-DROP-Kriterium, kein GRAUBEREICH.

---

## Data-Snooping- / Forking-Paths-Offenlegung (PFLICHT-Abschnitt)

**Vorab fixierte Parameter (VOR jedem Datenanfassen gebunden, KEINE Suche darüber):**

| Parameter | Wert | Quelle | Gesucht? |
|---|---|---|---|
| Panel | BTC/ETH/SOL/BNB/XRP | Programm-Standard (H-01/H-05); iter-3-Panel §7.5 | NEIN |
| Datenbasis | Harvester-Backfill `publicTrade`, read-only | DEC-15 / H-05b | NEIN |
| Bar-Länge | 5 min (Last-Price/Bar) | konservativ, meidet E-04-Mikro-Zone | NEIN (nur 1 Wert) |
| Lookback L | 12 Bars = 60 min | M13 „Rolling 1h Returns" | NEIN (aus Literatur) |
| Z_THRESH | 2.5 | PRD §7.5 / M13 wörtlich | NEIN (aus Literatur) |
| Achse A | \|z\| ≥ 2.5 | M13/§7.5 wörtlich | NEIN |
| Achse B (Crash-Veto) | Panel-RV NICHT oberstes Dezil (15-min-RV) | §7.5 „HMM≠Crash" + c07_pe-RV | NEIN (Dezil fix) |
| Renyi-TE-Achse | WEGGELASSEN | Forking-Paths-Minimierung | — (bewusst nicht) |
| Horizont-Menge | h ∈ {1,3,6} Bars | M13-Skala, sub-24h | NEIN (fixe 3er-Menge) |
| N-Floor | ≥ 30 Ereignisse/Fenster | Power-Guard research_notes §7.5 | NEIN |
| FDR-Familie | F-XMR, BH-FDR α=0.10 | Registry-Disziplin §4 | — |
| Fenster | A@2026-04-15, B@2026-05-15 (2 Kalendertage) | DEC-15 | NEIN |
| n_surrogates | 200 | H-03/H-06-Konvention | NEIN |
| Verstärkungs-Kriterium | nicht-überlappende 95%-Bootstrap-CIs | verteilungsfrei, kein Schwellen-FG | NEIN |

**KEINE Suche** erfolgt über Bar-Länge, L, Z_THRESH, Crash-Dezil, Horizont-Menge,
Panel, Fenster oder Verstärkungs-Schwelle. Es gibt **genau 2 Konditionierungs-Achsen**
(A, B). Jede Abweichung von einem dieser Werte wäre eine **NEUE H-07-Zeile** (z.B.
H-07 mit TE-Filter = H-07c), NICHT eine Variation innerhalb dieses Laufs (Registry-
Disziplin §2/§8.3, DEC-09/DEC-12-Muster).

**Kein Data-Snooping in Welle-1/2-Daten:** H-07 ist aus PRD/Literatur abgeleitet
(M13, Lo & MacKinlay 1990), NICHT aus einem post-hoc in Welle-1/2 beobachteten Effekt.
Es gibt keine Entdeckungszelle. Der einzige Snooping-Vektor wäre die Forking-Paths-
Freiheit bei der Konditionierungs-Wahl — und die ist durch die obige Tabelle (2 fixe
Achsen, keine Schwellen-Suche) neutralisiert. **Variante-A-Risiko (Survey §2.3)
adressiert:** die Konditionierungs-Achsen sind VOR dem Lauf gebunden und aus dem PRD
zitiert; sie wurden NICHT durch Suche über Regime-Kandidaten gefunden.

---

## Code-Bedarf-Vermerk (KEIN Code jetzt gebaut — nur Bewertung, künftiges Build-WP)

**Wiederverwendbar (Bibliotheks-Import, NICHT dupliziert):**
- `src/bybit_edge/research/c01_ofi_sign/oos.py` → **`load_harvest_window`** (read-only
  Hive-Tree-Loader für `data/harvest/raw/bybit/publicTrade/…`, `WINDOW_MAX_TICKS`,
  Midnight-ms-Filter, Schema-validiert). Der Kalender-synchronisierte Panel-Load lässt
  sich darauf aufsetzen (5× `load_harvest_window` über dasselbe Kalender-Fenster,
  dann auf gemeinsame 5-min-Bar-Achse resamplen).
- `src/bybit_edge/research/c07_pe/pre_gate.py` → **`forward_realized_vol`** (Summe
  quadrierter Returns über „[t, t+15min]", DEC-12) als Vorlage für die Panel-realized-
  vol-Definition der Achse B (Crash-Veto-Dezil).
- Surrogate-/BH-FDR-Bausteine aus dem c01/c07-Bestand (Permutations-p, `n_surrogates`,
  BH-FDR α=0.10) sind konzeptuell nachnutzbar.

**NEU nötig:**
- Cross-Sectional-z-Schätzer (`E_t[X_i]`, `⟨X⟩_t`, `σ_cross`, `z_{i,t}`, M13-Formeln)
  auf der synchronisierten 5-Symbol-5-min-Bar-Achse.
- Panel-Synchronisierung (Kalender-Fenster, gemeinsame Bar-Timestamps, forward-fill
  ≤ 1 Bar) — der research_notes-§7.5-„panel replayer".
- Konditionierung (Achse A + B) + reversions-signierte Forward-Return-Statistik.
- **Baseline-Vergleich** (unkonditioniert) + nicht-überlappende Bootstrap-CIs
  (Nicht-Trivialitäts-Anker).
- N-Floor-Check (≥ 30 Ereignisse/Fenster) + gate-neutrale Ausgabe je (h × Fenster ×
  {kond|baseline}), damit der gate-auditor gegen H-07 urteilt (das Modul fällt KEIN
  Gesamturteil, meldet nur μ_rev, p, fdr_sig, ΔCI-Überlappung, N).

**Empfehlung (reversibelster Pfad, analog DEC-03/DEC-05-Konvention):** NEUES,
eigenständiges Modul **`src/bybit_edge/research/c06_xmr/`** (ein Verzeichnis löschen =
vollständiger Rückbau; hält das kapitalfreie Mess-Gate sauber von einer späteren
Tradability-H-07b getrennt). **KAPITALFREIHEIT im Modul strikt:** kein bps/Edge/PnL/
Sharpe/Friction-Code (reiner Mess-/Verstärkungs-Test). **KEIN Code jetzt, KEINE Tests,
Lauf NICHT gestartet.**

---

## A. Ehrlichkeits-Check

**Ist H-07 wirklich nicht-trivial (≠ E-04-Sign-Flip)?** **JA.** Das Pass-Kriterium ist
NICHT „unkonditionierte MR existiert" (das ist die E-04-widerlegte, PRD-§6-verbotene
Trivial-Lesart), sondern „**konditionierte Reversions-Magnitude signifikant > unkondi-
tionierter Baseline** (nicht-überlappende Bootstrap-CIs)". Der unkonditionierte Baseline
ist explizit als Null-Anker mit-gemessen; ohne Verstärkung ist H-07 DROP — selbst wenn
eine schwache unkonditionierte MR da ist. Damit ist die Trivial-Lesart strukturell aus
dem Erfolgspfad ausgeschlossen. Zusätzlich meidet die 5-min-Bar-Länge bewusst die
sub-10-Sekunden-Mikro-Zone, in der E-03/E-04 den „Queue-Jump-Tax"-Verlust lokalisiert
haben.

**Sind es ≤ 3 vorab fixierte Achsen ohne Suche?** **JA — genau 2** (A: |z|≥2.5;
B: Nicht-oberstes-Vol-Dezil). Der Renyi-TE-Filter ist bewusst weggelassen (weniger
Freiheitsgrade = ehrlicher). Alle Schwellen/Horizonte/L/Bar-Länge/Fenster sind aus
PRD/Literatur bzw. konservativ fixiert (Offenlegungs-Tabelle oben) — **keine Suche**.

**Ist eine ehrliche H-07 registrierbar?** **JA** — aber NUR in dieser strengen,
kapitalfreien, verstärkungs-verankerten Form und mit einem ehrlich benannten **DROP-
A-priori**. Der einzige Weg, an dem H-07 unehrlich/nicht-registrierbar würde, wäre:
(a) den Baseline-Anker weglassen (→ Trivial-MR, verboten), (b) mehr Achsen / eine
Schwellen- oder Horizont-Suche zulassen (→ Forking Paths, Variante-A-Falle), oder
(c) eine Tradability-/bps-Aussage in dieses Gate ziehen (→ Kapitalfreiheits-Bruch,
Survivorship-/sub-10bp-Falle). Keiner dieser drei Wege wird hier beschritten. **Fazit:
H-07 ist ehrlich registrierbar; das ehrliche erwartete Ergebnis ist DROP.**

**Verbleibendes ehrliches Rest-Risiko (offen benannt):** das research_notes-§7.5-
Power-Problem — 5 BTC-korrelierte Symbole könnten |z|>2.5 zu selten produzieren
(N-Floor reißt → DROP an mangelnder Power, nicht an Widerlegung der Reversion selbst).
Das ist kein Forking-Path, sondern eine ehrliche Möglichkeit, dass H-07 an der
Datenlage (5-statt-20-Symbol-Panel) scheitert. Der N-Floor macht diesen Ausgang
sichtbar und verbietet das „Retten" durch Z_THRESH-Absenkung oder Symbol-Nachladen.

---

## B. Vorschlag DEC-Eintrag (analog DEC-12/DEC-16 — vom Orchestrator zu setzen)

> **### DEC-17 · C-06 Cross-Sectional Ergodic Mean-Reversion Mess-Gate: Methoden-/
> Parameter-Festlegung (H-07, KAPITALFREI)**
>
> - **Frage:** Wie wird die PRD-§4-Z.129-C-06-„NICHT-triviale MR" ehrlich (nicht-trivial
>   ≠ E-04-Sign-Flip, forking-paths-frei) als kapitalfreies Mess-Gate operationalisiert,
>   wo PRD/Register zu Bar-Länge, L, Crash-Regime-Operationalisierung, Horizont-Menge
>   und Verstärkungs-Kriterium stumm sind?
> - **Optionen:** (1) unkonditionierte MR messen — VERWORFEN (E-04-/PRD-§6-verboten,
>   trivial). (2) Regime-Konditionierung mit Achsen-/Schwellen-Suche — VERWORFEN
>   (Variante-A-Forking-Paths, Survey §2.3). (3) 2 vorab fixierte Achsen + Baseline-
>   Verstärkungs-Anker + kapitalfrei + DROP-A-priori — GEWÄHLT.
> - **Entscheidung / vorab fixierte Parameter:** Panel BTC/ETH/SOL/BNB/XRP; Bar-Länge
>   5 min (Last-Price/Bar aus `publicTrade`); L=12 Bars (M13 „1h"); Z_THRESH=2.5
>   (§7.5 wörtlich); Achse A |z|≥2.5, Achse B Panel-15min-RV nicht oberstes Dezil
>   (HMM-Crash-Proxy); Renyi-TE WEGGELASSEN; Horizonte h∈{1,3,6} Bars; N-Floor ≥30
>   Ereignisse/Fenster; Surrogate n=200; Fenster A@2026-04-15 + B@2026-05-15 (DEC-15,
>   Kalender-synchronisiert); FDR-Familie F-XMR BH-FDR α=0.10.
> - **Gate-Schwellen UNVERÄNDERT wie in H-07 registriert:** WEITER = kond. μ_rev>0 UND
>   p≤0.05 FDR über F-XMR UND ≥2-Fenster-Konsistenz UND nicht-überlappende Bootstrap-CIs
>   (kond > baseline) für ≥1 h in ≥2 Fenstern; sonst DROP; hartes Ein-Fenster-Kriterium,
>   kein GRAUBEREICH. — DEC-17 fixiert NUR vorher unspezifizierte Methoden-/Scoping-
>   Parameter, KEINE Torpfosten-Verschiebung (DEC-09/DEC-12-Muster, Registry-Disziplin
>   §8.3).
> - **Begründung:** reversibelste Optionen wo PRD stumm (konservativste Bar-Länge/L/
>   Dezil/Horizonte, verteilungsfreies CI-Kriterium ohne zusätzlichen Schwellen-FG);
>   Renyi-TE weggelassen minimiert Freiheitsgrade; KAPITALFREIHEIT strikt (kein bps/
>   Edge/PnL/Friction). Tradability wäre H-07b (nicht impliziert).
> - **Rückbauweg:** H-07-Registry-Eintrag + DEC-17-Block + CHANGELOG-Zeile entfernen =
>   Festlegung wieder offen; da JETZT KEIN Code gebaut wird, kein Code-Rückbau nötig;
>   Bestands-Code (c01_ofi_sign, c07_pe) bleibt unberührt.

---

## C. Kurzfassung (≤ 30 Zeilen)

(a) **Ehrlich registrierbar? JA** — als kapitalfreies Cross-Sectional-Mess-Gate mit
    Verstärkungs-Anker, ≤ 3 (genau 2) vorab fixierten Achsen, KEINE Schwellen-/
    Horizont-/Achsen-Suche. Unehrlich/nicht-registrierbar nur, wenn man Baseline-Anker
    weglässt, Achsen-Suche zulässt oder eine bps-Aussage hineinzieht — alle drei hier
    vermieden.
(b) **Die 2 fixierten Konditionierungs-Achsen:** (A) Über-Dehnung |z|≥2.5 (Cross-
    Sectional-z des 60-min-Zeitmittels gegen das Ensemble-Mittel der 5 Symbole, M13/
    §7.5 wörtlich); (B) Nicht-Crash-Regime = Panel-15min-realized-vol NICHT im obersten
    Dezil (HMM-Crash-Veto-Proxy). Renyi-TE bewusst weggelassen (Forking-Paths-Minimierung).
(c) **Nicht-Trivialitäts-Anker (ein Satz):** H-07 besteht nur, wenn die konditionierte
    reversions-signierte Forward-Rendite **signifikant größer** ist als der
    unkonditionierte Panel-Baseline (nicht-überlappende 95%-Bootstrap-CIs in ≥2
    Fenstern) — die reine unkonditionierte MR (E-04-/PRD-§6-verboten) zählt NIE als
    Erfolg.
(d) **A-priori-Urteil: erwartet DROP** — research_notes markiert die XRP-April-MR als
    Survivorship-Bias (sub-10bp, nur ein Monat); DEC-15-Fenster A liegt in genau diesem
    April-Regime, Fenster B (Mai) zwingt Cross-Regime-Konsistenz; E-04/PRD §6 haben die
    unkonditionierte MR bereits widerlegt. Zusätzliches ehrliches Rest-Risiko: N-Floor
    (≥30 Ereignisse/Fenster) kann an der 5-statt-20-Symbol-Panel-Power scheitern → DROP.
(e) **Pfad zur Datei:** `/home/user/scinance/scinance2-impl/state/c06_h07_draft.md`
