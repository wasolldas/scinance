# DECONFLICT — Orchestrator-Entscheidung (Phase DECONFLICT)

**Stand:** 2026-07-07 · Entscheider: Orchestrator (CLAUDE.md §6) · Input: `critique/scores.md`, beide Pre-Screens, alle 6 Scan-Dateien.

## Ausgangslage

Critic-Shortlist (≥8/12, keine Dim 0, echte Alpha-Hypothese): **7 Kandidaten** — IC-CLIM-1 (11), IC-CLIM-2 (11), IC-DEND-1 (11), IC-MECH-2 (10), IC-RMT-2 (10), IC-EVT-1 (9), IC-RMT-4 (9). Deckel laut Verfassung §2.6: **max. 4–5**. Zwei müssen ins PARK-Register.

## Merge-/Überschneidungs-Analyse (Cross-Domain-Hinweise berücksichtigt)

- **IV-Surface-Doppelbindung:** IC-EVT-1 (Tail-*Form* GPD-ξ vs. risikoneutrale Tail aus IV) und IC-RMT-4 (IV-Surface-Korrelations-Spektrum) teilen dieselbe knappe Datenquelle (Deribit-Options-IV, nur ~3 Wochen Live) und sind beide data-gated. Verschiedene Fragen, aber gleicher Flaschenhals → nur EINE der beiden in die Shortlist.
- **RMT-interne Überschneidung:** IC-RMT-2 (Cross-Exchange-Fragmentierungsmatrix, sofort testbar) vs. IC-RMT-4 (IV-Surface, data-gated). IC-RMT-2 ist der klar bessere RMT-Vertreter (sofort testbar, keine IV-Abhängigkeit).
- **Climatology-interne Überschneidung:** IC-CLIM-1 (AnEn-Vol-Regime) und IC-CLIM-2 (Teleconnection) sind beide Mehrtage-Horizont + beide data-gated + selbe Disziplin. Beide in die 5 zu nehmen hieße 2/5 Slots auf demselben Disziplin+Gating-Profil (§6.4-Verstoß: geringste Überschneidung bevorzugen). Nur EINE.
- **Dendro↔Netzwerk-Synchronizitätsmatrix:** betrifft nur die REWORK-Netzwerk-ICs (nicht Shortlist) — keine Kollision mit einem Shortlist-Kandidaten.

## Auswahl-Kriterien (§6)

Ich optimiere auf: (1) **Disziplin-Diversität** (max. 1 pro Fachgebiet in den Top-5, außer klar begründet), (2) **Balance sofort-testbar ↔ friktions-günstig** (die zentrale Spannung des Runs), (3) **konservative Lesart** bei Gleichstand (§6.3).

## ENTSCHEIDUNG — 5 Hypothesen für CROSSDOMAIN_PRD (→ H-09..H-13)

| Rang | IC | Disziplin | Profil | Warum in den 5 |
|---|---|---|---|---|
| 1 | **IC-MECH-2** Risk-Limit-Tier-Bunching | Mechanism Design | sofort testbar, `publicTrade`-only | Einziger Kandidat, der sofort-testbar UND strukturell nicht-wand-gebunden ist (Börsenmechanik-Befund, kein Mikrostruktur-Signal an der Wand). Höchste „jetzt prüfbar + nicht sofort wand-tot"-Kombination. |
| 2 | **IC-DEND-1** Cross-Stream-Pointer-Days | Dendrochronologie | sofort testbar, kapitalfrei | Genuin fachfremde Multi-Serien-Methode (Breite statt Tiefe → 34 Serien existieren im Basis-Bestand). Kapitalfreie Existenzfrage, scharf falsifizierbar. |
| 3 | **IC-CLIM-1** AnEn-Vol-Regime-Forecast | Climatology (§5) | data-gated, Friktion ~25–75× | Der §5-Flaggschiff-Kandidat: die EINZIGE Achse, die die Friktions-Arithmetik strukturell ändert (Mehrtage-Horizont). Das Framework existiert genau für diese Frage; Aufnahme trotz Data-Gating ist verfassungskonform (§5 explizite Vorgabe). |
| 4 | **IC-RMT-2** Cross-Exchange-Fragmentierungsmatrix | Econophysics/RMT | sofort testbar, kapitalfrei | Neue Korrelationsstruktur-Frage (Markt-Modus vs. Exchange-Restmoden), noch nie versucht, sofort testbar, T/N=240 solide. |
| 5 | **IC-EVT-1** Tail-Form-Konsistenz GPD-ξ | EVT/Aktuarmathematik | data-gated (IV-Fenster), kapitalfrei | 5. eigenständige Disziplin. Tail-*Form* statt VRP-Level (C-33 unberührt), kapitalfreie Divergenz-Messfrage. Gewählt vor IC-RMT-4 (dedupliziert die IV-Doppelbindung zugunsten des Disziplin-Diversitäts-Gewinns). |

**Disziplin-Abdeckung der 5:** Mechanism Design · Dendrochronologie · Climatology · RMT · EVT — fünf verschiedene Fachgebiete, keine Wiederholung. Balance: **3 sofort testbar** (MECH-2, DEND-1, RMT-2) + **2 data-gated aber hoch-wertig** (CLIM-1 = Friktions-Flaggschiff, EVT-1 = Tail-Form). Netzwerk-Topologie ist NICHT in den 5 — alle 3 Netzwerk-ICs scheiterten am „Overlay-über-Nichts"-Mangel (friction_audit) bzw. blieben unter 8; das ist die konservative Lesart (§6.3).

## Ins PARK-Register (`CROSSDOMAIN_PARK.md`), mit Entsperr-Bedingung

- **IC-CLIM-2** (11, Teleconnection) — shortlist-würdig, am Climatology-Diversitäts-Deckel ausgeschieden. Entsperr: eigene Runde ODER wenn IC-CLIM-1 WEITER erreicht (dann Teleconnection als Folge).
- **IC-RMT-4** (9, IV-Surface-Spektrum) — IV-Doppelbindung mit IC-EVT-1 dedupliziert. Entsperr: ≥3 Monate Live-IV-Historie (Mehrregime).
- **IC-RMT-3** (Lévy-RMT-Null) — Infrastruktur/Zulieferer für IC-RMT-1/2 (korrekte Nullverteilung), kein eigenständiger Alpha-Claim. Als Methoden-Baustein vermerkt.
- **REWORK-nicht-eingelöst → PARK** (Deckel bindet, nicht Score; §2.6): IC-RMT-1, IC-NET-1, IC-NET-2, IC-NET-3 (alle „Overlay-über-Nichts"; Entsperr: sobald eine positive Basis-Strategie existiert, die ein Overlay modulieren könnte — nach 0/13 Kanten nicht absehbar), IC-MECH-1 (ADL-Antizipation; Entsperr: Ereignisdichte Aug.–Okt. 2026 wie C-27/28/29), IC-EVT-2 (Extremal-Index Cluster-Tail; Entsperr: genug Kaskaden-Events).
- **PARK (Critic):** IC-CLIM-3 (Autor+Scout-PARK-Empfehlung), IC-EVT-3 (Multi-Zyklen, Deep-Backfill-gated), IC-MECH-3 (blockiert, adlAlert-Topic defekt), IC-MECH-4 (teilt C-20-Datenabhängigkeit).
- **Infrastruktur/Enabler (kein H-xx):** IC-DEND-2 (COFECHA-Cross-Dating-Prüfung), IC-DEND-3 (EPS/SNR-Mindest-Serienzahl) — Werkzeuge für die spätere Implementierung, keine Hypothesen.

## Cross-Domain-Hinweise für eine mögliche Folge-Runde (registry-keeper sammelt)

- Ruin-Theorie/aktuarische Reservierung auf den Insurance Fund (evt-actuarial → mechanism-design).
- DebtRank/rekursive Feedback-Zentralität auf ADL-Exposure-Struktur (network-topology → mechanism-design).
- Bayesian Model Averaging + Schaake Shuffle (climatology → spätere ML-/Netzwerk-Runde).
- GLK-/Event-Synchronization-Matrix (dendro ↔ network) — bei Multi-Symbol-Erweiterung deduplizieren.

**Rework-Runden verbraucht:** 0. Begründung: die 5 Shortlist-Picks (Score 9–11) liegen klar über den REWORK-Kandidaten (7–8); ein Rework könnte die Zahl nur über den 5er-Deckel treiben, den ich danach wieder schneiden müsste. Der Deckel bindet, nicht der Score-Floor (§2.6). Rework-Auflagen sind als Entsperr-Bedingungen im PARK-Register dokumentiert.
