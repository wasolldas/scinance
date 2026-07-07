# CRITIQUE — Scoring aller 20 IC-Vorschläge

**Agent:** `critic` · **Stand:** 2026-07-07 · Grundlage: 6 Discipline-Scans + beide Pre-Screens
(`feasibility_screen.md`, `friction_audit.md`). Schwelle: **≥8/12 UND keine Dimension = 0.**

Dimensionen: **N**ovelty/Non-Redundanz · **D**aten-Passung · **F**riktions-Überlebensfähigkeit ·
**Fa**lsifizierbarkeit (je 0–3).

**Methodischer Hinweis vorab:** Für IC-RMT-1, IC-NET-1, IC-NET-2, IC-NET-3 hat der
`friction-tradability-auditor` die Selbst-Einstufung "Risiko-Overlay" auf "primär (c)
Mess-/Existenzfrage" korrigiert ("Overlay-über-Nichts": keine existierende Basis-Position benannt,
die moduliert würde — nach 0/13 handelbaren Kanten unbelegte Annahme). Als reine Mess-Fragen läge ihr
Signal-Zeitfenster (Sub-Tag/6h/24h bzw. Sub-Minute) in derselben Kategorie wie die 13 gefallenen
Mikrostruktur-Signale (80–500× unter der Wand) — ihr struktureller Ausweg über die Wand ist damit
entfallen. Das drückt Dimension F auf 1 bei allen vieren (nicht 0, da kein struktureller
Friction-DROP vom Auditor festgestellt wurde, nur eine Korrektur der Rollen-Einstufung). Alle vier
haben zusätzlich ein konkret behebbares Formulierungsproblem (Rollen-Feld korrigieren, Schwelle
schärfen) → REWORK statt PARK, trotz teilweise ≥8 Gesamtpunkten (das mechanische ≥8-Kriterium wird
hier bewusst durch den in CLAUDE.md §2 Regel 2 verankerten Mess-Gate/Tradability-Gate-Grundsatz
überstimmt: eine unbelegte Overlay-Behauptung ist ein struktureller Mangel, kein bloßes Randdetail).

---

## Ranking-Tabelle

| IC | N | D | F | Fa | Summe | Verdikt |
|---|---|---|---|---|---|---|
| IC-CLIM-1 | 3 | 2 | 3 | 3 | **11** | SHORTLIST |
| IC-CLIM-2 | 3 | 2 | 3 | 3 | **11** | SHORTLIST |
| IC-DEND-1 | 3 | 3 | 2 | 3 | **11** | SHORTLIST |
| IC-MECH-2 | 3 | 3 | 2 | 2 | **10** | SHORTLIST |
| IC-RMT-2 | 3 | 3 | 2 | 2 | **10** | SHORTLIST |
| IC-RMT-3 | 3 | 3 | 2 | 2 | **10** | Infrastruktur/Zulieferer (kein Alpha-Claim) |
| IC-CLIM-3 | 2 | 1 | 3 | 3 | **9** | PARK (Autor+Scout empfehlen PARK bei zu kleinem N für SRS) |
| IC-EVT-1 | 3 | 2 | 2 | 2 | **9** | SHORTLIST |
| IC-RMT-1 | 3 | 3 | 1 | 2 | **9** | REWORK (Runde 1/3) |
| IC-RMT-4 | 3 | 2 | 2 | 2 | **9** | SHORTLIST |
| IC-MECH-1 | 3 | 2 | 2 | 1 | **8** | REWORK (Runde 1/3) |
| IC-NET-2 | 3 | 3 | 1 | 1 | **8** | REWORK (Runde 1/3) |
| IC-NET-3 | 3 | 3 | 1 | 1 | **8** | REWORK (Runde 1/3, mild) |
| IC-EVT-2 | 2 | 2 | 2 | 1 | **7** | REWORK (Runde 1/3) |
| IC-EVT-3 | 3 | 1 | 2 | 1 | **7** | PARK (Entsperr-Bedingung: Manifest-Coverage) |
| IC-NET-1 | 3 | 2 | 1 | 1 | **7** | REWORK (Runde 1/3) |
| IC-MECH-3 | 3 | **0** | 2 | 1 | **6** | PARK (blockiert — adlAlert ungeklärt) |
| IC-MECH-4 | 2 | 1 | 2 | 1 | **6** | PARK (Autor-Selbsteinstufung, C-20-Analogie) |
| IC-DEND-2 | n/a | 3 | n/a | 3 | n/a | Infrastruktur (kein Alpha-Claim) |
| IC-DEND-3 | n/a | 3 | n/a | 2 | n/a | Infrastruktur (kein Alpha-Claim) |

**Shortlist (≥8, keine Dim=0, echte Alpha-Hypothese):** IC-CLIM-1, IC-CLIM-2, IC-DEND-1, IC-MECH-2,
IC-RMT-2, IC-EVT-1, IC-RMT-4 — **7 Kandidaten**, mehr als die 4–5-Deckelung aus CLAUDE.md §2 Punkt 6;
Kappung ist Aufgabe von DECONFLICT (Orchestrator + `registry-keeper`), nicht dieser Phase.

**REWORK-Kandidaten (Runde 1/3) mit Auflage:**
- **IC-RMT-1** — Rollen-Feld von "Risiko-Overlay" auf reine (c)-Existenzfrage zurückstufen; Overlay-
  Anwendung explizit als offene, separate Folge-Hypothese kennzeichnen (H-04→H-04b-Muster).
- **IC-NET-1 / IC-NET-2** — identische Auflage wie RMT-1 (Rolle (b)→(c)) PLUS scharfe numerische
  Schwelle vorregistrieren (z. B. Turnover-Rate-/λ₂-Z-Score bzw. Partitions-Distanz-Statistik über
  fixem Signifikanzniveau) statt "steigt/verändert sich messbar".
- **IC-NET-3** — mildeste Auflage: nur Rollen-Feld (b)→(c) umbenennen (Agent hat inhaltlich bereits
  vorweggenommen, dass das TE-Signal analog H-04 unter der Wand liegen dürfte).
- **IC-MECH-1** — scharfe numerische Schwelle vorregistrieren (z. B. Spread-Δ in bps oder Orderflow-
  Z-Score über ein fixes Vorlauf-Fenster vor der 30%/8h-Drawdown-Kante), sonst unverändert.
- **IC-EVT-2** — (a) numerische Schwelle für Extremal-Index θ fixieren (z. B. θ<X als
  Clustering-Nachweis); (b) schärfer von C-27/28/29 abgrenzen, warum θ (anders als Hawkes-ρ) nicht
  automatisch REFUTED-territorial ist.

**PARK (kein Rework, Entsperr-Bedingung vermerkt):** IC-CLIM-3, IC-EVT-3, IC-MECH-3, IC-MECH-4.

**Infrastruktur/Enabler (kein Alpha-Claim, nicht Shortlist-fähig, aber Werkzeug für Shortlist-ICs):**
IC-DEND-2, IC-DEND-3, IC-RMT-3.

---

## Begründungsblöcke je IC

### Critic-Score IC-RMT-1
Novelty/Non-Redundanz: 3 — echtes RMT/Spektral-Terrain, keine Überschneidung mit H-04/C-06/C-14.
Daten-Passung: 3 — Basis-Bestand, T/N≈122 (bzw. 36 im OI-gekappten Fall), sofort testbar.
Friktions-Überlebensfähigkeit: 1 — friction-tradability-auditor korrigiert Rolle (b)→(c):
"Overlay-über-Nichts", keine Basis-Position benannt; als reine Mess-Frage läge der Signal-Horizont
(rollierende Matrix, im Kern kurzfristig) in der Kategorie der 13 gefallenen Mikrostruktur-Signale.
Falsifizierbarkeit: 2 — Tracy-Widom + RIE ersetzen harte Schwelle durch datengetriebene
Referenzverteilung (GL-012-sicher), aber die Overlay-Sizing-Schwelle selbst ist nicht spezifiziert.
Gesamt: 9/12
Entscheidung: REWORK (Runde 1/3) — Rollen-Feld auf (c) zurückstufen, Overlay als separate
Folge-Hypothese kennzeichnen.

### Critic-Score IC-RMT-2
Novelty/Non-Redundanz: 3 — Cross-Exchange-Fragmentierung, orthogonal zu H-04 (gleichzeitig statt
zeitverschoben), keine C-06-Kollision.
Daten-Passung: 3 — T/N=240 je Tagesfenster, sofort testbar, ehrlich als capital_free (c) ohne
Overlay-Übertreibung deklariert.
Friktions-Überlebensfähigkeit: 2 — mittel: kapitalfreie Mess-Frage ohne Handelspfad, Tradability
sauber als separate Folge-Hypothese benannt (kein Overlay-über-Nichts-Fehler, da hier von Anfang an
korrekt als (c) deklariert).
Falsifizierbarkeit: 2 — IPR-Lokalisierungstest gegen MP-Nullverteilung, Markt- vs. Exchange-Restmodus
unterscheidbar, aber kein exakt vorfixierter Zahlenschwellenwert für "strukturelle Fragmentierung".
Gesamt: 10/12
Entscheidung: SHORTLIST.

### Critic-Score IC-RMT-3
Novelty/Non-Redundanz: 3 — Lévy-stabile RMT-Nullverteilung, bisher nicht getestet, klar von C-14
(Punktprozess) abgegrenzt.
Daten-Passung: 3 — T/N≈488 (bzw. ≈14 als Tagesfallback), sofort testbar.
Friktions-Überlebensfähigkeit: 2 — mittel, explizit als Methodik-Zulieferer ohne eigenen Handels-Claim
deklariert (Anti-Gaming: beide Nullmodelle werden berichtet, kein Cherry-Picking).
Falsifizierbarkeit: 2 — Modellvergleich Gaussian-Wishart vs. Lévy-stabil, Tail-Index-Fit, aber kein
einzelner harter Schwellenwert vorregistriert (Modellvergleichskriterium noch zu präzisieren).
Gesamt: 10/12
Entscheidung: Infrastruktur/Zulieferer, nicht Shortlist-Kandidat (korrigiert IC-RMT-1s
Referenzverteilung, kein eigener Alpha-Claim — CLAUDE.md-Vorgabe des Orchestrators).

### Critic-Score IC-RMT-4
Novelty/Non-Redundanz: 3 — erste RMT-Anwendung auf IV-Surface im gesamten Programm, orthogonal zu C-33.
Daten-Passung: 2 — data-gated (nur ~3 Wochen Live, 1 Marktregime, N unverifiziert), aber klare nahe
Entsperr-Bedingung (Fenster auf ≥3 Monate, N am Feed verifizieren).
Friktions-Überlebensfähigkeit: 2 — mittel, capital_free, Overlay nur als "potenziell" markiert (nicht
verfrüht behauptet wie RMT-1/NET-1-3).
Falsifizierbarkeit: 2 — MP-Bulk+IPR-Test (Level- vs. Skew-Modus), aber N-Unsicherheit schwächt die
Schärfe der Schwelle vor Feed-Verifikation.
Gesamt: 9/12
Entscheidung: SHORTLIST (schwächster Kandidat der Liste — Einzelregime-Caveat beachten).

### Critic-Score IC-EVT-1
Novelty/Non-Redundanz: 3 — Tail-FORM-Konsistenz (ξ vs. risikoneutrale Dichte), klar von C-33
(gemittelter Level-Spread) abgegrenzt.
Daten-Passung: 2 — Returns-Seite sofort testbar, Options-Seite data-gated (Disjunktheit der
Snapshot-Tage ungeprüft), aber klare Entsperr-/Selbstkill-Bedingung (<2 disjunkte Punkte).
Friktions-Überlebensfähigkeit: 2 — mittel, reine Konsistenzfrage per Definition ohne Round-Trip-Kosten.
Falsifizierbarkeit: 2 — POT/GPD-ξ-Vergleich mit Hill-Gegenprobe, Selbstkill-Kriterium vorab benannt,
aber exakter Divergenz-Schwellenwert (wie viel ξ-Abstand = "Divergenz") noch nicht numerisch fixiert.
Gesamt: 9/12
Entscheidung: SHORTLIST.

### Critic-Score IC-EVT-2
Novelty/Non-Redundanz: 2 — Extremal-Index θ ist eine andere Messgröße als Hawkes-ρ (C-14, REFUTED),
aber Autor selbst räumt ein, dass "andere Messgröße" laut Rollen-Definition nicht automatisch
entsperrt — Nähe zu C-27/28/29-Territorium bleibt Restrisiko.
Daten-Passung: 2 — data-gated, aber klare Analogie-Entsperrung (≥30 Kaskaden, Aug.–Okt. 2026, wie
C-27/28/29).
Friktions-Überlebensfähigkeit: 2 — mittel, capital_free, kein Handels-Claim.
Falsifizierbarkeit: 1 — "θ≪1 vs. θ nahe 1" ohne vorab fixierten Zahlenschwellenwert.
Gesamt: 7/12
Entscheidung: REWORK (Runde 1/3) — numerische θ-Schwelle fixieren, C-27/28/29-Abgrenzung schärfen.

### Critic-Score IC-EVT-3
Novelty/Non-Redundanz: 3 — Multi-Zyklen-Tail-Stabilität, neue Fragestellung.
Daten-Passung: 1 — data-gated OHNE klare nahe Entsperr-Bedingung (Backfill-Fortschritt für
BitMEX/Deribit/Tardis unbekannt, kein Manifest-Zugriff, kein fixes Datum wie bei EVT-2).
Friktions-Überlebensfähigkeit: 2 — mittel, capital_free.
Falsifizierbarkeit: 1 — "stabil vs. verschiebt sich" ohne vorab fixierten Toleranzschwellenwert für ξ.
Gesamt: 7/12
Entscheidung: PARK (Entsperr-Bedingung: Manifest-Coverage-Check bestätigt Backfill-Tiefe — externe
Bedingung, kein internes Formulierungsproblem, daher kein Rework, sondern PARK mit Wiedervorlage).

### Critic-Score IC-NET-1
Novelty/Non-Redundanz: 3 — Aggregatmetrik über volles 5-Knoten-Netz, orthogonal zu H-04/RMT.
Daten-Passung: 2 — Struktur sofort testbar, Stress-Ground-Truth (~3 Wochen) data-gated mit klarer
wachsender Entsperrung.
Friktions-Überlebensfähigkeit: 1 — Overlay-über-Nichts (s. Kopfhinweis); 6h/24h-Fenster liegt in der
Kategorie der gefallenen Mikrostruktur-Signale, falls je direkt gehandelt.
Falsifizierbarkeit: 1 — "steigt messbar VOR Stress" ohne vorab fixierten Zahlenschwellenwert.
Gesamt: 7/12
Entscheidung: REWORK (Runde 1/3) — Rolle (b)→(c), numerische Schwelle (z. B. Turnover-Rate-Z-Score)
vorregistrieren.

### Critic-Score IC-NET-2
Novelty/Non-Redundanz: 3 — Partitionsstruktur bei N≈13 (nicht degeneriert), orthogonal zu RMT-Spektrum.
Daten-Passung: 3 — sofort testbar, Funding-Dispersion als Basis-Bestand-lange Ground-Truth.
Friktions-Überlebensfähigkeit: 1 — Overlay-über-Nichts (s. Kopfhinweis), sub-Tages-Charakter.
Falsifizierbarkeit: 1 — "verändert sich messbar" ohne vorab fixierte Partitions-Distanz-Schwelle.
Gesamt: 8/12
Entscheidung: REWORK (Runde 1/3) — trotz mechanisch erreichter 8/12 wird die unbelegte
Overlay-Behauptung als struktureller Mangel gewertet (CLAUDE.md §2 Regel 2); Rolle (b)→(c) plus
scharfe Schwelle vorregistrieren, dann erneut vorlegen.

### Critic-Score IC-NET-3
Novelty/Non-Redundanz: 3 — Multiplex-Knotentyp-Aggregation, explizit von H-04-Einzelpaar abgegrenzt
(Selbstkill-Kriterium bei Kollaps auf Einzelpaar bereits vom Autor benannt).
Daten-Passung: 3 — sofort testbar im OI-gedeckelten ~30-Tage-Fenster.
Friktions-Überlebensfähigkeit: 1 — Overlay-über-Nichts, aber Autor hat selbst am ehrlichsten
vorweggenommen, dass das Signal analog H-04 (80× unter der Wand) ausfallen dürfte.
Falsifizierbarkeit: 1 — "systematisch höhere Zentralität" ohne fixierten Signifikanz-/Effektgrößen-Schwellenwert.
Gesamt: 8/12
Entscheidung: REWORK (Runde 1/3, mildeste Auflage) — nur Rollen-Feld (b)→(c) umbenennen und
Zentralitäts-Differenz-Schwelle (z. B. Wilcoxon-Test, α vorab fixiert) ergänzen.

### Critic-Score IC-MECH-1
Novelty/Non-Redundanz: 3 — ADL-Trigger-Antizipation, klar von C-27/28/29 (Kaskaden-FORM) abgegrenzt.
Daten-Passung: 2 — data-gated, aber klare Analogie-Entsperrung (Ereignisdichte, Aug.–Okt. 2026).
Friktions-Überlebensfähigkeit: 2 — mittel, ehrlich als (c) deklariert (kein Overlay-Etikett).
Falsifizierbarkeit: 1 — "verändert sich messbar" ohne vorab fixierten Zahlenschwellenwert.
Gesamt: 8/12
Entscheidung: REWORK (Runde 1/3) — numerische Schwelle (Spread-Δ in bps / Orderflow-Z-Score über
fixes Vorlauf-Fenster) vorregistrieren.

### Critic-Score IC-MECH-2
Novelty/Non-Redundanz: 3 — Bunching-an-Margin-Kink, spieltheoretisch/verhaltensökonomisch neu.
Daten-Passung: 3 — sofort testbar, einziger IC des Agenten ohne Live-Stream-Abhängigkeit.
Friktions-Überlebensfähigkeit: 2 — mittel, reiner Struktur-/Verhaltensfakt, kein Round-Trip-Claim.
Falsifizierbarkeit: 2 — etablierte Bunching-Estimator-Methodik (Excess-Mass-Statistik) an
dokumentierten, fixen Tier-Kanten — pre-registrierbar, auch wenn der genaue Signifikanz-Cutoff im
Vorschlag selbst noch nicht ausbuchstabiert ist.
Gesamt: 10/12
Entscheidung: SHORTLIST.

### Critic-Score IC-MECH-3
Novelty/Non-Redundanz: 3 — Adverse-Selection-Asymmetrie ADL vs. Orderbuch-Liquidation, neu.
Daten-Passung: 0 — `adlAlert` laut Audit "UNGEKLÄRT/möglicherweise defekt", Kern-Vergleichsseite nicht
nachweislich messbar (explizite 0-Vorgabe des Orchestrator-Prompts für diesen Fall).
Friktions-Überlebensfähigkeit: 2 — mittel in der Sache (capital_free zunächst).
Falsifizierbarkeit: 1 — Konzept vorhanden, aber ohne funktionierenden Datenstrom nicht sinnvoll
vorab schärfbar.
Gesamt: 6/12
Entscheidung: PARK (blockiert — Dimension Daten-Passung=0 schließt automatisch jedes Rework aus;
Entsperr-Bedingung: adl_alerts-Topic-Reparatur-WP + Ereignisdichte Aug.–Okt. 2026).

### Critic-Score IC-MECH-4
Novelty/Non-Redundanz: 2 — Autor selbst benennt Datenabhängigkeits-Überschneidung mit C-20.
Daten-Passung: 1 — data-gated an neue Listings gekoppelt, kein festes Datum, Autor selbst als
PARK/niedrige Priorität eingereicht.
Friktions-Überlebensfähigkeit: 2 — mittel, capital_free, kein Handels-Claim.
Falsifizierbarkeit: 1 — spekulativ, keine scharfe Schwelle ausformuliert.
Gesamt: 6/12
Entscheidung: PARK (Autor-Selbsteinstufung übernommen, Entsperr-Bedingung identisch mit C-20).

### Critic-Score IC-CLIM-1
Novelty/Non-Redundanz: 3 — nichtparametrisches Analog-Ensemble, klar von C-42/H-02 (parametrisches
Modell) abgegrenzt.
Daten-Passung: 2 — Basis-Fenster sofort nutzbar, aber zweites disjunktes OOS-Fenster (Teil der
eigenen vorregistrierten Schwelle) existiert noch nicht — klare, T-gebundene (nicht strukturelle)
Entsperr-Bedingung.
Friktions-Überlebensfähigkeit: 3 — bester Wert im gesamten Satz: ~25–75× ÜBER der Wand (3-Tage-
Horizont), vorbildlich sauber von Tradability getrennt (H-04→H-04b-Muster prospektiv angewendet).
Falsifizierbarkeit: 3 — CRPS_AnEn < CRPS_HAR-RV auf ≥2 disjunkten Fenstern, scharf, vorab fixiert.
Gesamt: 11/12
Entscheidung: SHORTLIST.

### Critic-Score IC-CLIM-2
Novelty/Non-Redundanz: 3 — Ereignis-getriggerte Tages-Teleconnection, klar von H-04 (Sekunden-Lead-Lag)
abgegrenzt.
Daten-Passung: 2 — data-gated (Ereigniszahl bei N≈100 Tagen zu klein für FDR-robuste Aussage über 20
Symbolpaare), aber explizit T-gebunden mit klarer, mit fortschreitendem Backfill wachsender Entsperrung.
Friktions-Überlebensfähigkeit: 3 — ~13–55× über der Wand; Autor + Feasibility-Scout einig, dass
Ereigniszahl (nicht Friktion) der Flaschenhals ist.
Falsifizierbarkeit: 3 — Permutationstest + FDR (Benjamini-Hochberg α=0.10), Schwelle/Perzentil vorab
zu fixieren (explizit als Pflicht benannt).
Gesamt: 11/12
Entscheidung: SHORTLIST.

### Critic-Score IC-CLIM-3
Novelty/Non-Redundanz: 2 — baut direkt auf IC-CLIM-1s Analog-Läufen auf, keine unabhängige neue
Datengrundlage (schärfere Metrik, aber dieselbe Basis).
Daten-Passung: 1 — GESCHEITERT bei aktuellem N (~100 Analog-Läufe) für eine robuste SRS-Bootstrap-
Sampling-Rausch-Korrektur; Literatur verlangt laut Autor "deutlich mehr" — sowohl Autor als auch
`data-feasibility-scout` empfehlen ausdrücklich PARK statt WEITER bei fortbestehend kleinem N.
Friktions-Überlebensfähigkeit: 3 — identisch zu IC-CLIM-1 (~25–75×).
Falsifizierbarkeit: 3 — SRS signifikant von 0 verschieden (Bootstrap-CI) auf ≥2 disjunkten Fenstern.
Gesamt: 9/12
Entscheidung: PARK — mechanisch zwar ≥8/keine 0, aber die doppelte fachliche Empfehlung (Autor +
Feasibility-Scout: SRS bei aktuellem N strukturell nicht belastbar) wiegt hier schwerer als das reine
Zahlenraster; Entsperr-Bedingung identisch zu IC-CLIM-1, zusätzlich eigenes Mindest-N für SRS separat
verifizieren.

### Critic-Score IC-DEND-1
Novelty/Non-Redundanz: 3 — Querschnitts-Pointer-Tag-Statistik über 34 Serien, strukturell nicht auf
eine Einzelserie reduzierbar, klar von C-08 (BOCPD, Einzelserie) abgegrenzt.
Daten-Passung: 3 — Basisversion sofort testbar (Serien-BREITE statt -TIEFE trägt die Statistik, 34≫5,
keine N-Degeneration); Multi-Regime-Robustheit separat data-gated, aber Kernschwelle bereits testbar.
Friktions-Überlebensfähigkeit: 2 — mittel: Mehrtage-Vorlauf (1–5 Tage) strukturell in der günstigen
CLIM-Kategorie plausibel, aber im Gegensatz zu den climatology-ICs fehlt eine explizite
Größenordnungs-Rechnung (Zielmetrik "RV-Drift/Funding-Krümmung" nicht auf einen Preis-Return
übersetzt) — von friction-tradability-auditor als offene Auflage vermerkt, nicht als Mangel bestraft.
Falsifizierbarkeit: 3 — |C_t|≥1.5 UND ≥60% der Serien, beide Zahlen explizit VOR Datensichtung fixiert.
Gesamt: 11/12
Entscheidung: SHORTLIST. Auflage an `registry-keeper`/`fable5-deep-validator`: Grobrechnung nach
IC-CLIM-2-Vorbild vor Pre-Registration einer Tradability-Folge-Hypothese nachreichen.

### Critic-Score IC-DEND-2
Typ: Infrastruktur-/Datenqualitäts-Beitrag, explizit KEIN Alpha-Claim (vom Autor selbst so verlangt).
Daten-Passung: 3 — sofort testbar (~8–9 Segmente über ~103 Tage).
Falsifizierbarkeit: 3 — Segment-Korrelation<0.5 in ≥2 aufeinanderfolgenden Segmenten, vorab fixiert.
Entscheidung: Infrastruktur (Voraussetzungs-Check für jede tagesgenaue Cross-Exchange-Hypothese,
priorisiert vor IC-DEND-1-Multi-Zyklen-Version laufen lassen — nicht gegen Novelty-Dimension gescort).

### Critic-Score IC-DEND-3
Typ: Infrastruktur-/methodischer Beitrag (Mindest-Serienzahl-Formel), explizit KEIN Alpha-Claim.
Daten-Passung: 3 — sofort testbar (nutzt IC-DEND-1s 34 Serien).
Falsifizierbarkeit: 2 — liefert eine Kennzahl (EPS je Kandidaten-N), aber bewusst kein hartes
Cutoff-Kriterium (0.85-Richtwert explizit als nicht unkritisch übertragbar verworfen) — das ist hier
kein Mangel, sondern methodisch korrekt (Autor vermeidet einen unbegründeten harten Schwellenwert).
Entscheidung: Infrastruktur (liefert Mindest-N direkt an IC-DEND-1/`fable5-deep-validator`).
