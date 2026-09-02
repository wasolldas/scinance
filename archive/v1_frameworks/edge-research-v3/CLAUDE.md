# EDGE RESEARCH FRAMEWORK v3 — Cross-Domain Track

> **Mission:** Autonome Recherche eines *erweiterten* Hypothesen-Sets für Scinance 2.0,
> ausschließlich über Methoden aus fachfremden Disziplinen ("andere Fachgebiete"),
> angewendet auf den neuen Daten-Harvester. **Kein Code, kein Backtest, kein Live-Bezug.**
> Endprodukt: `results/CROSSDOMAIN_PRD.md` — ein Pre-Registration-Dokument im Stil von
> `reference/FINAL_PRD.md`, das 3–5 formal vorregistrierte, feasibility-geprüfte
> Hypothesen für eine spätere Implementierungs-Welle übergibt.
>
> **Du (die Hauptsession) bist der ORCHESTRATOR.** Delegiere jede inhaltliche Arbeit an
> die Subagenten in `.claude/agents/`. Du triffst die Sequenzierungs- und
> Eskalationsentscheidungen selbst; siehe §6 „Autonomie ohne Rückfrage".

---

## 0. Warum dieses Framework existiert (Kontext, den jeder Subagent kennen muss)

`reference/PROGRAM_FINAL_REPORT.md` (Stand 2026-07-06) hat Scinance 2.0 nach drei
Wellen und 13 vorregistrierten Gates für **daten-gated statt arbeits-gated** erklärt:
9 DROP, 2 PARK, 2 kapitalfreie WEITER, **0 handelbare Kanten**. Zentralbefund: die
**Friction-Wand** (11 bps Taker / ~15 bps inkl. Slippage) hat *jede* gemessene Kante
geschlagen — auch zwei echte, surrogat-bestätigte Mikrostruktur-Signale (BTC→ETH-Lead-
Lag, inverses OFI auf SOL) lagen 80–500× darunter. Empfehlung des Berichts: **keine
Welle 4 auf Vorrat**, weil jeder verbliebene Pfad im bestehenden Quant-Werkzeugkasten
entweder tot, blockiert oder auf Monate hinaus daten-gated ist (§7/§8 dort).

**Warum dieses Framework der Empfehlung trotzdem nicht widerspricht:** „Keine Welle 4"
bezog sich auf *mehr vom Gleichen* — weitere Varianten des bereits erschöpften
Microstructure-/ML-Werkzeugkastens. Dieses Framework eröffnet stattdessen eine **neue
Suchachse**: Fachgebiete, die in keiner der bisherigen drei Wellen *und* im
Vorgänger-Scouting (`edge-research-v2`, Disziplinen: Geophysik, Bioinformatik,
Neurowissenschaft, Quantenmechanik, Informationstheorie) benutzt wurden. Die
Falsifikations-Disziplin (§2) bleibt zu 100 % erhalten — nur der Ideenraum wird erweitert,
nicht die Beweislast gesenkt.

**Zusätzlicher Rückenwind:** Der Harvester (`reference/DATASET.md`) liefert seit
2026-07-02 Daten, die es in den drei Wellen so noch nicht gab — lange Historie
(2014–2026, mehrere Marktzyklen/Crashes), volle Options-IV-Surface (Deribit dvol,
Tardis-Chains mit Greeks), Insurance-/ADL-/Liquidation-Streams. Jeder Fachgebiets-Agent
muss seine Hypothese explizit an einen konkreten Datenstrom aus DATASET.md §4/§6 binden.

---

## 1. Ausschlussliste — worüber NICHT geforscht wird

Automatisch aus `reference/FINAL_PRD.md` und `reference/PROGRAM_FINAL_REPORT.md`
abgeleitet. Der `data-feasibility-scout` prüft in Phase AUDIT jeden neuen
Hypothesen-Vorschlag gegen diese Liste; ein Treffer ohne nachweislich neue
Fragestellung ist ein automatischer Selbst-Kill (kein Rework-Versuch).

**Bereits REFUTED (nie wiederholen):** C-14 Hawkes-ρ-Schwelle, CS-01 Cascade-Detector,
CS-02 Entropie-Momentum (siehe FINAL_PRD §6).

**Bereits getestet, DROP/PARK (kein Re-Test ohne neues Signal):** H-01 S3-Entry,
H-02 C-42 Vol-RV-Anker (LightGBM/HAR — sperrt den gesamten Vol-Stack), H-03 CFAR
(Cyclostationary, radar-technisch), H-04/H-04b Lead-Lag + Tradability, H-05/H-05b/H-05c
OFI-Vorzeichen (positiv + invers) + Tradability, H-06 Permutation Entropy, H-07/H-08
Cross-Sectional-Z (absolut + Rang).

**Disziplinen, die bereits gescoutet UND in konkrete Claims übersetzt wurden — hier
wird nicht erneut gewildert:**
- **Seismologie/Statistische Physik kritischer Phänomene:** Hawkes/Branching-Ratio
  (C-14/C-27/C-28), Gutenberg-Richter+Omori (C-15), Avalanche-Shape-Collapse (C-29),
  Natural-Time κ₁ (C-30) — alle bereits im PARK-/REFUTED-Register, gebunden an den
  C-36-Recording-Vorlauf (frühestens Aug.–Okt. 2026).
- **Informationstheorie/Nichtlineare Dynamik:** Permutation Entropy (C-07, DROP),
  Transfer Entropy im Lead-Lag-Test (H-04).
- **Physiologie-nahe Signalverarbeitung:** TDA/Persistent Homology (C-11), RQA (C-12) —
  PARK, blockiert durch den gefallenen Vol-Stack-Anker (H-02).
- **Radartechnik/Signalverarbeitung:** Cyclostationary CFAR (C-31, DROP, „abgegrast"),
  CEEMDAN (C-35, blockiert durch H-02), Wavelet-Denoising (C-04, PARK).
- **Epidemiologie:** SIR/R₀-Kaskadenmodell (C-26) — in C-39 absorbiert, kein eigener
  Pilot.

**Konsequenz für dieses Framework:** Der Fachgebiets-Roster in §4 wurde bewusst so
gewählt, dass **keine** dieser sechs Cluster wiederholt wird. Falls ein Agent während
der Recherche doch in eines hineinläuft, muss er das explizit gegen diese Liste
prüfen und im Zweifel selbst droppen (siehe §6).

---

## 2. Methodische Verfassung (unverändert aus Scinance 2.0 übernommen)

Jeder Subagent ist an diese Regeln gebunden, unabhängig von seinem Fachgebiet:

1. **Feasibility-Check VOR Pre-Registration (GL-012-Lehre).** Vor jeder Schwellenfestlegung
   prüft `data-feasibility-scout`, ob die Schwelle auf der verfügbaren Datenbasis
   überhaupt erreichbar ist (Beispiel aus der Historie: max|z| = √(N−1) bei N=5 Symbolen
   macht bestimmte Schwellen strukturell unerreichbar). Ein struktureller DROP vor dem
   Datenlauf ist billiger und ehrlicher als ein leerer Lauf.
2. **Mess-Gate ≠ Tradability-Gate.** Jede Hypothese startet `capital_free=true`
   (reine Existenzfrage: ist das Muster real und OOS-stabil?). Erst danach, als
   **separate** Folge-Hypothese, prüft `friction-tradability-auditor` die Handelbarkeit
   gegen die Friction-Wand (11 bps Taker / ~15 bps inkl. Slippage, 300-ms-Latenz-Haircut).
   Ein Mess-WEITER ist NIE automatisch handelbar.
3. **FDR-Pflicht.** Benjamini-Hochberg α=0.10 über jede Familie parallel getesteter
   Varianten. Der `registry-keeper` weist jede Hypothese einer Familie zu, bevor sie
   getestet wird.
4. **Pre-Registration, keine Torpfosten-Verschiebung.** Schwelle, Fenster und
   Abbruchkriterium werden VOR der Prüfung wörtlich fixiert — in **keine** Richtung
   nachträglich verschoben (weder erleichtert noch erschwert).
5. **Hartes Ein-Fenster-Kriterium.** Verfehlt eine Schwelle in einem disjunkten Fenster,
   ist das DROP — kein Nachverhandeln, außer explizit als Graubereich vorregistriert.
6. **Single-Operator-Realismus.** Maximal **4–5 Hypothesen** verlassen diese
   Recherche-Runde in Richtung Pre-Registration. Alles andere geht ins
   `results/CROSSDOMAIN_PARK.md`-Register (mit Entsperr-Bedingung), nicht in den Papierkorb.
7. **Rechenaufwand taggen.** Jede Hypothese erhält ein Tag `Rechenaufwand: CPU |
   GPU-vorteilhaft`. Bekanntes Zielsystem für die spätere Umsetzung: Windows/WSL2,
   RTX 5060 Ti (Blackwell, CUDA 12.8+/PyTorch 2.7+), 82 GB RAM — GPU lohnt sich nur bei
   Deep-Learning-, großskaliger Matrix- oder Simulationslast; die meisten hier
   vorgeschlagenen Methoden sind CPU-only.

---

## 3. ID-Schema (Fortsetzung, keine Neuerfindung)

- **H-09, H-10, …** — formal vorregistrierte Hypothesen (Fortsetzung von H-08).
- **IC-01, IC-02, …** — „Interdisciplinary Claims": rohe Fachgebiets-Vorschläge vor
  Pre-Registration (parallel zur alten C-xx-Zählung, aber eigener Namensraum, damit
  nichts mit C-01…C-43 kollidiert).
- **GL-014, …** — Gate-Verdikte, sobald die erste echte Prüfung läuft (Fortsetzung von
  GL-013). Diese Runde selbst erzeugt noch keine GL-Einträge — nur Pre-Registrations.

---

## 4. Agenten-Roster

**Fachgebiets-Agenten (Phase DISCIPLINE-SCAN, parallel, je 2–4 IC-Vorschläge):**

| Agent | Fachgebiet | Warum neu (siehe §1) |
|---|---|---|
| `econophysics-rmt` | Random-Matrix-Theory / Spektral­analyse von Korrelationsmatrizen | Noch nie versucht; unterscheidet sich von Hawkes/Natural-Time |
| `evt-actuarial` | Extremwerttheorie + Versicherungsmathematik (Tail-Pricing) | Fragt Tail-*Form*-Konsistenz, nicht VRP-Level (C-33 bleibt unberührt) |
| `network-topology` | Netzwerktheorie/Graphentheorie über das volle Multi-Asset-Universum | Bisherige Lead-Lag-Tests waren paarweise (H-04); hier: volle Topologie |
| `mechanism-design` | Auktionstheorie/Spieltheorie für ADL- und Insurance-Fund-Mechanik | Krypto-spezifisches Marktdesign, bisher nicht angefasst |
| `climatology-ensemble` | Ensemble-/Analog-Forecasting, Teleconnection-Methoden | Einzige Disziplin, die bewusst auf Mehrtage-Horizont zielt (siehe §5) |
| `dendrochronology-crossdating` | Cross-Dating/Pointer-Year-Methodik aus der Dendrochronologie | Multi-Serien-Anomalie-Abgleich, orthogonal zu BOCPD (C-08, Einzelserie) |

**Unterstützungs-Agenten (fachgebietsübergreifend, erzwingen die Verfassung aus §2):**

| Agent | Rolle |
|---|---|
| `data-feasibility-scout` | Kartiert jeden Vorschlag auf DATASET.md; Feasibility-Check zuerst |
| `friction-tradability-auditor` | Die 11–15-bps-Wand-Prüfung; erzwingt capital_free vs. Tradability |
| `registry-keeper` | Pre-Registration-Text, FDR-Familien, ID-Vergabe (§3) |
| `critic` | Scoring 0–12 (siehe unten), max. 3 Rework-Runden pro IC-Vorschlag |
| `fable5-deep-validator` | Härtet die Shortlist zu bindenden H-xx-Einträgen; läuft auf Fable 5 |

**Werkzeugkasten ≠ Auftrag:** Die in jeder Agenten-Datei unter „Werkzeugkasten"
genannten Methoden sind bekannte, illustrative Startpunkte aus der Literatur — keine
vollständige Zuteilung. Jeder Fachgebiets-Agent recherchiert in einem verpflichtenden
Schritt 1 seines „Vorgehens" eigenständig zusätzliche Kandidatenmethoden aus seinem
Feld (WebSearch/WebFetch, bereits als Tool vorhanden), bevor er IC-Vorschläge
formuliert, und dokumentiert das im Feld `Erwogene Alternativen:`. Der Ideenraum wird
so von den Agenten selbst erweitert, nicht vom Orchestrator im Vorfeld eingeengt.
Stößt ein Agent dabei auf einen vielversprechenden, aber erkennbar fachfremden
Kandidaten, geht der als `Cross-Domain-Hinweis:` an den Orchestrator statt verloren
zu gehen (`registry-keeper` sammelt diese in DECONFLICT für eine mögliche spätere Runde).

**Critic-Scoring (0–12, vier Dimensionen à 0–3):** Novelty/Non-Redundanz ·
Daten-Passung (JETZT verfügbar, nicht data-gated) · Friktions-Überlebensfähigkeit ·
Falsifizierbarkeit (scharfe, vorregistrierbare Schwelle). Aufnahme in die Shortlist
ab **≥ 8/12 und keine Dimension bei 0**.

---

## 5. Warum `climatology-ensemble` eine Sonderrolle hat

Alle 13 bisherigen Gate-Verdikte betrafen entweder Sub-Minuten-Mikrostruktur (Lead-Lag,
OFI, CFAR — alle an der Friction-Wand gestorben) oder ein Einzelmodell-ML-Forecast
(C-42, R²-Anker gefallen). **Kein bisheriger Test hat je den Zeithorizont selbst als
Stellschraube benutzt.** Ein Mehrtage-Holding-Horizont ändert die Friktions-Arithmetik
grundsätzlich: 11–15 bps einmalig sind gegen eine mehrtägige erwartete Bewegung ein
anderes Verhältnis als gegen eine 1–3-Sekunden-Bewegung. `climatology-ensemble` ist
deshalb angewiesen, **ausschließlich** auf Halte-Horizonten ≥ 1 Tag zu suchen — nicht
als eine von vielen gleichwertigen Optionen, sondern als explizite Vorgabe.

---

## 6. Autonomie ohne Rückfrage

Kein Agent fragt den Menschen. Offene Fragen werden so aufgelöst:

1. **Bindender Präzedenzfall zuerst.** Ein REFUTED/DROP-Verdikt aus
   `reference/FINAL_PRD.md` oder `reference/PROGRAM_FINAL_REPORT.md` sticht jede neue
   Argumentation — ein Fachgebiets-Agent kann ihn nicht durch eine andere Herleitung
   „umgehen", nur durch nachweislich andere Messgröße widerlegen.
2. **Quantitative Fakten schlagen Meinungen.** Friction-Wand (11–15 bps),
   Feasibility-Mathematik (z. B. Erreichbarkeits-Checks) sind bindend, keine
   Verhandlungsmasse.
3. **Bei echtem Dissens zwischen zwei Fachgebiets-Agenten:** der Orchestrator
   entscheidet zugunsten der **konservativeren** (schwerer zu erfüllenden) Lesart —
   konsistent mit dem Falsifikations-Ethos des Gesamtprogramms.
4. **Bei Prioritäts-Gleichstand:** Vorrang für das Thema mit der geringsten
   Überschneidung zu bereits laufenden/daten-gated Pfaden (siehe PROGRAM_FINAL_REPORT §7
   Tabelle „Wecker").
5. **Rework-Deckel:** max. 3 Runden Critic → Fachgebiets-Agent pro IC-Vorschlag, danach
   automatisch PARK (kein viertes Nachbessern).

---

## 7. Ablauf (State Machine)

```
INIT
  → AUDIT               (data-feasibility-scout: Daten-Inventar + Ausschlussliste laden)
  → DISCIPLINE-SCAN      (6 Fachgebiets-Agenten PARALLEL: erst eigene
                           Methodenrecherche über die Beispiele der Agenten-Datei
                           hinaus, dann je 2–4 IC-xx-Vorschläge aus der erweiterten Liste)
  → PRE-SCREEN           (friction-tradability-auditor + data-feasibility-scout:
                           Struktur-Check pro IC-Vorschlag, kein Datenlauf)
  → CRITIQUE             (critic scort 0–12; ≤3 Rework-Runden über den Urheber-Agenten)
  → DECONFLICT           (Orchestrator + registry-keeper: Duplikate mergen, auf 4–5
                           Kandidaten deckeln, §6-Regeln bei Dissens)
  → DEEP-VALIDATION      (fable5-deep-validator härtet die Shortlist zu H-09+,
                           inkl. FDR-Familie, Fenster, Abbruchkriterium)
  → REGISTRY-WRITE       (registry-keeper schreibt results/CROSSDOMAIN_PRD.md +
                           results/CROSSDOMAIN_PARK.md im FINAL_PRD-Stil)
  → REVIEW               (critic: Schluss-Check gegen §2-Verfassung)
  → DONE
```

Start in Claude Code:

```
Starte den Cross-Domain-Research-Run gemäß CLAUDE.md. Arbeite autonom bis Phase DONE.
```

Zwischenstände landen nach jeder Phase in `results/` (z. B. `results/discipline_scan/
<agent>.md`), damit der Lauf jederzeit unterbrechbar und fortsetzbar ist.

## 8. Definition of Done (Grenze dieser Phase)

Diese Runde endet mit **Pre-Registrations-Text**, nicht mit Code. Kein Agent schreibt
Python/Backtests, zieht neue Live-Daten oder verändert `data/`, `state/` oder bestehende
Skripte. Erlaubt ist ausschließlich: lesender Zugriff auf Referenzdokumente und das
Manifest (Feasibility-Check), Web-Recherche zur Fachgebiets-Methodik, und das Schreiben
von Markdown-Artefakten unter `results/`. Die eigentliche Implementierung
(Backtest-Pipeline für H-09+) ist explizit eine spätere, separate Runde.
