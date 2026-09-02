# CROSSDOMAIN_PARK — PARK-Register des Cross-Domain-Tracks

**Phase:** REGISTRY-WRITE
**Stand:** 2026-07-07
**Erstellt von:** `registry-keeper`
**Maßgebliche Quellen:** `results/deconflict.md` (Orchestrator-Entscheidung, Entsperr-Bedingungen), `results/critique/scores.md` (Scoring/Verdikt je IC), `results/discipline_scan/*.md` (Original-Vorschläge), `results/CROSSDOMAIN_PRD.md` (die 5 aufgenommenen Hypothesen H-09..H-13).

> Geparkte Ansätze sind weder verworfen noch aktiv — sie warten auf eine Entsperr-Bedingung. Nichts hier startet ohne erfüllten Trigger (Stilvorbild: `reference/FINAL_PRD.md` §5). Von 20 gescorten IC-Vorschlägen (`critique/scores.md`) sind 5 in `CROSSDOMAIN_PRD.md` (H-09..H-13); die verbleibenden **15** stehen unten.

---

## (a) Shortlist-würdig, aber am Deckel gescheitert

Beide Einträge erreichten die Critic-Shortlist-Schwelle (≥8/12, keine Dimension 0), fielen aber am Single-Operator-Deckel (max. 4–5, CLAUDE.md §2.6) bzw. an Disziplin-/Datenquellen-Diversität in `deconflict.md` heraus.

| Eintrag | Score | Park-Grund | Entsperr-Bedingung |
|---|---|---|---|
| **IC-CLIM-2** — Ereignis-getriggerte Tages-Teleconnection | 11/12 (SHORTLIST-fähig) | Climatology-Diversitäts-Deckel: IC-CLIM-1 (→ H-11) besetzt bereits den einen Climatology-Slot der 5; zwei Climatology-Einträge in den Top-5 hätten gegen die §6.4-Regel „geringste Überschneidung bevorzugen" verstoßen (`deconflict.md`). | Eigene Folge-Runde ODER: sobald IC-CLIM-1 (H-11) das WEITER-Gate erreicht, geht Teleconnection als direkte Folge-Hypothese in die nächste Pre-Registration. |
| **IC-RMT-4** — RMT auf IV-Surface-Korrelationsspektrum (Level- vs. Skew-Modus) | 9/12 (schwächster Shortlist-Kandidat) | IV-Doppelbindung mit IC-EVT-1 (→ H-13): beide hängen am selben knappen Flaschenhals (Deribit-Options-IV, nur ~3 Wochen Live) und sind beide data-gated; `deconflict.md` dedupliziert zugunsten IC-EVT-1 (Disziplin-Diversitäts-Gewinn: EVT/Aktuarmathematik ist 5. eigenständige Disziplin, RMT ist bereits über IC-RMT-2/H-12 vertreten). | ≥3 Monate Live-IV-Historie (Mehrregime-Abdeckung statt nur ~3 Wochen/1 Regime; `critique/scores.md` Daten-Passung-Begründung). |

---

## (b) Overlay-über-Nichts (Rolle (b)→(c) korrigiert)

Der `friction-tradability-auditor` hat bei diesen vier ICs die Selbst-Einstufung „Risiko-Overlay" auf „primär (c) Mess-/Existenzfrage" korrigiert: keiner benennt eine existierende Basis-Position, die moduliert würde (`critique/scores.md`, Kopfhinweis). Als reine Mess-Fragen läge ihr Signal-Zeitfenster (Sub-Tag/6h/24h bzw. Sub-Minute) in derselben Kategorie wie die 13 bereits gefallenen Mikrostruktur-Signale (80–500× unter der Wand) — ihr struktureller Ausweg über die Wand ist damit entfallen (Friktions-Dimension auf 1 gedrückt). Alle vier blieben im Rework-Zyklus (Runde 1/3), wurden aber durch den 5er-Deckel nicht mehr eingelöst und gehen laut `deconflict.md` als „REWORK-nicht-eingelöst → PARK" hierher (Deckel bindet, nicht Score).

| Eintrag | Score | Park-Grund | Entsperr-Bedingung |
|---|---|---|---|
| **IC-RMT-1** — RMT-Overlay auf Portfolio-Risiko (Tracy-Widom/RIE-Sizing) | 9/12 | Overlay-über-Nichts; Rework-Auflage (Rolle (b)→(c), Overlay als separate Folge-Hypothese) durch Deckel nicht mehr eingelöst. | Sobald eine positive Basis-Strategie existiert, die ein Overlay modulieren könnte — nach 0/13 handelbaren Kanten im Gesamtprogramm nicht absehbar. |
| **IC-NET-1** — Netzwerk-Aggregatmetrik (Turnover-Rate/λ₂) als Stress-Frühindikator | 7/12 | Overlay-über-Nichts; zusätzlich fehlende scharfe numerische Schwelle. | Positive Basis-Strategie (wie IC-RMT-1) UND vorregistrierte Turnover-Rate-/λ₂-Z-Score-Schwelle. |
| **IC-NET-2** — Netzwerk-Partitionsstruktur (Funding-Dispersion-Cluster) | 8/12 | Overlay-über-Nichts (mechanisch ≥8, aber unbelegte Overlay-Behauptung als struktureller Mangel gewertet, CLAUDE.md §2 Regel 2); fehlende Partitions-Distanz-Schwelle. | Positive Basis-Strategie UND vorregistrierte Partitions-Distanz-Statistik über fixem Signifikanzniveau. |
| **IC-NET-3** — Multiplex-Knotentyp-Zentralität | 8/12 | Overlay-über-Nichts (mildeste Auflage: nur Rollen-Feld-Umbenennung fehlte noch); Autor selbst erwartet Kollaps auf H-04-Niveau (80× unter der Wand). | Positive Basis-Strategie UND vorregistrierte Zentralitäts-Differenz-Schwelle (z. B. Wilcoxon, α fixiert). |

---

## (c) Data-gated / blockiert

| Eintrag | Score | Park-Grund | Entsperr-Bedingung |
|---|---|---|---|
| **IC-MECH-1** — ADL-Trigger-Antizipation (Spread-/Orderflow-Vorlauf vor Drawdown-Kante) | 8/12 | Data-gated (Ereignisdichte); Rework-Auflage (numerische Schwelle: Spread-Δ in bps / Orderflow-Z-Score) durch Deckel nicht mehr eingelöst. | Ereignisdichte Aug.–Okt. 2026 (wie C-27/28/29, `PROGRAM_FINAL_REPORT.md`-Analogie). |
| **IC-MECH-3** — Adverse-Selection-Asymmetrie ADL vs. Orderbuch-Liquidation | 6/12 | **Blockiert:** Daten-Passung=0 — `adlAlert`-Topic laut Audit ungeklärt/möglicherweise defekt; automatischer Selbstkill jedes Reworks bei Dimension=0. | `adl_alerts`-Topic-Reparatur-Workpaket abgeschlossen UND Ereignisdichte Aug.–Okt. 2026. |
| **IC-MECH-4** — Zero-Shot-Analogie auf neu gelistete Symbole (C-20-Nachbarschaft) | 6/12 | Autor-Selbsteinstufung als niedrige Priorität; teilt Datenabhängigkeit mit C-20 (Neu-Listing-Ereignis, nicht terminiert). | Identisch zu C-20: nächstes Neu-Listing-Ereignis auf Bybit/Binance. |
| **IC-EVT-2** — Extremal-Index θ (Cluster-Tail-Abhängigkeit) | 7/12 | Rework-Auflage (numerische θ-Schwelle, schärfere Abgrenzung zu C-27/28/29) durch Deckel nicht mehr eingelöst; data-gated. | Genug Kaskaden-Events (analog C-27/28/29-Entsperrung, Aug.–Okt. 2026). |
| **IC-EVT-3** — Multi-Zyklen-Tail-Stabilität (ξ über mehrere Marktregime) | 7/12 | Data-gated ohne nahe Entsperr-Bedingung (Backfill-Fortschritt BitMEX/Deribit/Tardis unbekannt, kein Manifest-Zugriff in dieser Sandbox); fehlende Toleranzschwelle für „ξ stabil vs. verschiebt sich". | Manifest-Coverage-Check bestätigt ausreichende Backfill-Tiefe (externe Bedingung, kein internes Formulierungsproblem — daher PARK statt Rework). |
| **IC-CLIM-3** — SRS-Bootstrap-Rauschkorrektur (auf IC-CLIM-1-Analogläufen) | 9/12 | Baut direkt auf IC-CLIM-1 auf (keine unabhängige neue Datengrundlage); Autor UND `data-feasibility-scout` empfehlen ausdrücklich PARK statt WEITER — aktuelles N (~100 Analogläufe) für robuste SRS-Bootstrap-Korrektur strukturell zu klein (überstimmt das mechanische ≥8-Kriterium). | Entsperr identisch zu IC-CLIM-1 (H-11-Entsperrung, siehe `CROSSDOMAIN_PRD.md`), zusätzlich eigenes Mindest-N für SRS separat verifizieren. |

---

## (d) Infrastruktur/Enabler (kein Alpha-Claim, keine H-xx)

Diese drei Einträge sind Werkzeuge für andere Hypothesen dieser Runde bzw. für spätere Ausbaustufen, keine eigenständigen Alpha-Claims — sie wurden von `critic` explizit nicht gegen die Novelty-/Falsifizierbarkeits-Dimensionen gescort.

| Eintrag | Rolle | Bezug |
|---|---|---|
| **IC-RMT-3** — Lévy-stabile RMT-Nullverteilung (Modellvergleich Gaussian-Wishart vs. Lévy-stabil) | Methoden-Zulieferer: liefert die korrekte Nullverteilung für IC-RMT-1/IC-RMT-2 (Fat-Tail-Robustheit der Referenzverteilung), kein eigenständiger Alpha-Claim. | Vorbedingung/Robustheitscheck für H-12 (falls Lévy-Null von der Gauss-Null der urteilstragenden Ein-Faktor-Null abweicht — mitzuberichten, nicht urteilstragend). |
| **IC-DEND-2** — COFECHA-Cross-Dating-Ausrichtungsprüfung (Zeitachsen-Integrität Bybit/Binance/Deribit) | Voraussetzungs-Check: Segment-Korrelation<0,5 in ≥2 aufeinanderfolgenden Segmenten als vorab fixiertes Warnsignal für Uhren-/Zeitachsen-Drift. | Sollte VOR dem Lauf von H-10 UND H-12 ausgeführt werden (beide sind explizit als Vorbedingung in den jeweiligen Selbstkill-Risiken von H-10/H-12 vermerkt, `CROSSDOMAIN_PRD.md`). |
| **IC-DEND-3** — EPS/SNR-Mindest-Serienzahl-Formel | Methodischer Beitrag: liefert eine Mindest-N-Kennzahl (kein hartes Cutoff-Kriterium — 0,85-Richtwert bewusst nicht unkritisch übernommen). | Direkter Zulieferer für H-10 (nutzt IC-DEND-1s 30/34-Serien-Konstruktion). |

---

## Bilanz

**15 PARK-Einträge** nach Kategorie: (a) 2 shortlist-würdig/gedeckelt, (b) 4 Overlay-über-Nichts, (c) 6 data-gated/blockiert, (d) 3 Infrastruktur/Enabler. Zusammen mit den 5 Einträgen in `CROSSDOMAIN_PRD.md` (H-09..H-13) sind damit alle 20 gescorten IC-Vorschläge aus `results/critique/scores.md` vollständig zurückverfolgbar — keiner verschwindet ohne dokumentierten Grund und Entsperr-Bedingung.

---

## Cross-Domain-Hinweise für eine mögliche Folge-Runde

Diese vier Hinweise sind während der Discipline-Scan-Phase von Fachgebiets-Agenten aufgefallen, passen aber in kein aktuelles Fachgebiet des Rosters (`CLAUDE.md` §4) und wurden explizit nicht verworfen (`registry-keeper` sammelt sie laut Rollen-Definition für eine mögliche spätere Runde, `deconflict.md` §„Cross-Domain-Hinweise"):

- **Ruin-Theorie/aktuarische Reservierung** auf den Insurance Fund — Brücke `evt-actuarial` → `mechanism-design`.
- **DebtRank/rekursive Feedback-Zentralität** auf ADL-Exposure-Struktur — Brücke `network-topology` → `mechanism-design`.
- **Bayesian Model Averaging + Schaake Shuffle** — Brücke `climatology-ensemble` → spätere ML-/Netzwerk-Runde.
- **GLK-/Event-Synchronization-Matrix** — Brücke Dendrochronologie ↔ Netzwerktheorie; bei einer Multi-Symbol-Erweiterung von H-10 zwingend gegen Redundanz zu prüfen (deduplizieren), bevor daraus ein eigener IC-Vorschlag wird.

**Rework-Runden-Bilanz dieser Runde:** 0 von 3 verbraucht (`deconflict.md`). Die 5 Shortlist-Picks (Score 9–11) lagen klar über den Rework-Kandidaten (7–8); ein Rework hätte die Kandidatenzahl nur über den 5er-Deckel getrieben, den der Orchestrator danach wieder hätte schneiden müssen. Die offenen Rework-Auflagen aus `critique/scores.md` (z. B. Rolle (b)→(c) bei IC-RMT-1/NET-1/2/3, numerische Schwellen bei IC-MECH-1/IC-EVT-2) sind oben als Bestandteil der jeweiligen Entsperr-Bedingung dokumentiert, nicht verloren gegangen.

*Ende CROSSDOMAIN_PARK.md*
