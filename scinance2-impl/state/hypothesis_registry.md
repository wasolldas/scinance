# Hypothesen-Registry (PRD §8 — Pflicht vor jedem Gate-Lauf)

> Regel: Hypothese, Schwellwerte, Fenster und FDR-Familie werden HIER festgeschrieben,
> BEVOR der zugehörige Validierungslauf startet. Keine Post-hoc-Schwellenanpassung.
> Der gate-auditor hat Veto gegen jeden Lauf ohne registrierten Eintrag.

## Registrierte Hypothesen

### H-01 · E-15 / CS-03 (S3 Pre-Settlement, iter-5-Fixes)
- **Registriert:** 2026-06-10 (vor Lauf-Start; Tore aus verdict.md §Welle-1 wörtlich, im PRD §3 übernommen)
- **Hypothese:** Mit korrigiertem Time-Stop (Tick-Zeit) und friction-aware Hard-Stop steigt die S3-Netto-Edge messbar; die Tail-Verluste (E-10) verschwinden.
- **Gate (vorregistriert):**
  - time_stop_exceeded-Count: 1 → erwartet ~60-70 (Fix-Wirksamkeit)
  - n>120s-Trades: 68 → erwartet ~0
  - n<-30bps-Trades: 33 → erwartet ~0
  - **WEITER:** aggregierte Netto-Edge ≥ -5 bps UND E-17-Divergenz geklärt
  - **DROP:** aggregierte Netto-Edge ≤ -10 bps
  - **GRAUBEREICH:** dazwischen → ein (1) weiteres vorregistriertes Fenster, dann endgültig
- **Fenster:** 5 Symbole (BTC/ETH/SOL/BNB/XRP), ~24h-Replay, single-pass
- **FDR-Familie:** F-S3 (einzelner konfirmatorischer Test, keine Korrektur nötig — aber Folge-Tests an S3 zählen in diese Familie)
- **Status:** Lauf beim User in Arbeit; Ergebnis via handoff_local erwartet

### H-02 · C-42-Reproduktion (LightGBM/HAR-RV — Pilot 2)
- **Registriert:** 2026-06-11 (WP-0, VOR Lauf-Start; Gate wörtlich aus PRD §3 Pilot 2)
- **Hypothese:** Das LightGBM-Vol-Regressionsmodell (36-Feature-Snapshot, Target `log(realised_vol_60m)`) reproduziert den einzigen positiven OOS-Befund des Registers (Test-R² ≈ 0.249, research_notes/claims_register C-42) unter sauberem Testdesign — die Vorhersagekraft überlebt purged Walk-Forward + FDR und ist kein L1-Selbstauskunfts-Artefakt.
- **Gate (vorregistriert, PRD §3 wörtlich):**
  - **WEITER:** „**OOS-R² ≥ 0.15** UND QLIKE schlägt naive HAR-RV-Baseline." Operationalisierung (workplan WP-4-DoD, konsistent mit dem Ein-Fenster-Abbruch): beide Kriterien in ALLEN ≥2 OOS-Fenstern erfüllt.
  - **Abbruch (PARK/DROP):** „OOS-R² < 0.15 in einem Fenster ODER HAR-RV nicht geschlagen → der gesamte Vol-Stack verliert seinen Anker, C-42 fällt auf PARK/DROP, alle abhängigen Vol-Module bleiben gesperrt" (C-10/C-35/C-11/C-12/C-34/VRP-RV-Bein).
  - **Kein GRAUBEREICH** definiert — PRD §3 nennt nur Gate + Abbruch; konservativ wird KEIN Graubereich nachregistriert.
- **Fenster/Datenbasis:** purged Walk-Forward (≥ L2), **≥ 2 disjunkte OOS-Fenster** mit Purge+Embargo (PRD §3 Testdesign). Datenbasis = vorhandener Kline-Backfill (`kline_1min`, read-only; „keine neue Aufzeichnung", PRD §3). Fensterwahl deterministisch-chronologisch aus dem verfügbaren Kline-Bestand, keine diskretionäre Fensterwahl. Symbol-Universum: Futures-Perp, BTC/ETH/SOL/BNB/XRP — PRD stumm zu Symbolen; abgeleitet aus verdict.md §9 („alle echten Pilots sind Futures-Perp") + H-01-Konvention.
- **FDR-Familie:** **F-VOL** (Vol-Feature-Familie, PRD §8.2): alle **36 Features = EINE Familie**, Benjamini-Hochberg **α = 0.10**. Spätere ΔR²-Tests gegen die C-42-Baseline (C-10/C-35/C-11/C-12) zählen in dieselbe Familie.
- **Peso/L0-Regel (PRD §8.4):** Single-Pass „> Schwelle in 2 Fenstern" zählt NICHT als bestanden ohne Walk-Forward ≥ L2 — daher purged WF verpflichtend, kein Abkürzungsweg.
- **Status:** registriert, Lauf NICHT gestartet. Lauf = WP-4 (T2 Quick-Fit 1 Symbol → T3 Voll-WF multi-symbol via handoff_local); Urteil durch gate-auditor gegen DIESEN Eintrag.

### H-03 · C-31-CFAR (Cyclostationary CFAR — Pilot 4, einziger neuer Alpha-Test Welle 1)
- **Registriert:** 2026-06-11 (WP-0, VOR Lauf-Start; Gate wörtlich aus PRD §3 Pilot 4)
- **Hypothese:** Das zyklostationäre Spektrum der publicTrade-Inter-Arrival-Zeiten enthält CFAR-detektierbare, nicht durch Zufall (Surrogate-Null) erklärbare periodische Struktur, die prädiktive Lead-Information mit handelbarer Edge oberhalb der Friction-Wand trägt.
- **Gate (vorregistriert, PRD §3 wörtlich):**
  - **WEITER:** „**Surrogate p ≤ 0.05** in ≥ 2 Fenstern UND **Lead-Zeit > 50 ms** (über Retail-Latenz) UND **Edge > 11 bps** (über der Friction-Wand)."
  - **Abbruch (DROP):** „p > 0.05 ODER Lead-Zeit < 50 ms ODER Edge ≤ 11 bps in einem Fenster → DROP (adaptiver Gegner / abgegraste HFT-Anomalie, Hauptrisiko laut Quelle)."
  - **Hartes Ein-Fenster-Kriterium (PRD §8.5):** Schwelle in EINEM disjunkten Fenster verfehlt → DROP, kein Nachverhandeln. **Kein GRAUBEREICH.**
- **Fenster/Datenbasis:** **≥ 2 disjunkte Fenster**; Surrogate-Test = geshuffelte Inter-Arrivals gegen das gemessene Cyclic Spectrum (PRD §3 Testdesign). Datenbasis = publicTrade-Ticks aus der Bestands-`trades`-Tabelle (read-only; „keine Aufzeichnung nötig", PRD §3). Fensterwahl deterministisch-chronologisch aus dem verfügbaren Tick-Bestand, disjunkt, keine diskretionäre Wahl. Symbol-Universum: Futures-Perp, BTC/ETH/SOL/BNB/XRP — PRD stumm zu Symbolen; abgeleitet wie bei H-02. Friction-Wand-Referenz: 11 bps Round-Trip (Taker) — verdict.md §2 Kernrelation (im PRD-Gate als „> 11 bps" übernommen).
- **FDR-Familie:** **F-CFAR** — H-03 ist der konfirmatorische Einzeltest (keine Korrektur nötig). Werden Quantil-/Parametervarianten (CFAR-Schwellen, Fenster-Längen, Spektral-Parameter) parallel getestet, gehen ALLE Varianten als eine Familie in BH **α = 0.10** innerhalb F-CFAR (PRD §8.2-Prinzip; workplan WP-0/WP-3).
- **Status:** registriert, Lauf NICHT gestartet. Lauf = WP-3 (T0/T1 synthetisch in Sandbox; verbindlicher Surrogate-Lauf auf Echt-Ticks = T3 via handoff_local); Urteil durch gate-auditor gegen DIESEN Eintrag.

> **2026-06-15 Nachtrag (append-only, DEC-09 — Originaltext oben UNVERÄNDERT):** Fenster-Scoping spezifiziert. Je Fenster werden die **≤ 150 000 jüngsten Ticks** verwendet; konkret werden die jüngsten `windows × 150 000` Ticks der chronologisch sortierten Serie genommen und in **≥ 2 disjunkte, zusammenhängende Fenster** geteilt (deterministisch-chronologisch, keine diskretionäre Wahl — exakt im Wortlaut des Originaleintrags „deterministisch-chronologisch aus dem verfügbaren Tick-Bestand, disjunkt, keine diskretionäre Wahl"). **Begründung:** (1) Stationarität — Zyklostationarität setzt (Quasi-)Stationarität innerhalb des Fensters voraus; die tage-/wochentiefe Bestands-`trades`-Tabelle würde ungekappt Fenster über Tage spannen und diese Annahme verletzen. (2) Tractability — ungekappt lief der T3-Lauf auf allen 5 Symbolen in den 5400s-Timeout (overnight 2026-06-14). **Pass/Fail UNVERÄNDERT:** Die Gate-Schwellen bleiben identisch — **Surrogate p ≤ 0.05 in ≥ 2 Fenstern UND Lead > 50 ms UND Edge > 11 bps**, hartes Ein-Fenster-DROP-Kriterium (PRD §8.5), **`n_surrogates = 200`**, **BH-FDR α = 0.10** über die F-CFAR-Familie. Dies ist ein vorher unspezifizierter Daten-Scoping-Parameter, KEINE Post-hoc-Schwellen-Anpassung (Registry-Disziplin §8.3). Operationalisierung: CLI-Flag `--max-ticks-per-window` (Default 150 000), Konstante `WINDOW_MAX_TICKS` in `cyclic_spectrum.py`.

---

## Registry-Disziplin (verbindlich, PRD §8)

1. **Pre-Registration (§8.3):** Jede Hypothese, jeder Schwellwert, jedes Fenster wird HIER festgeschrieben, BEVOR der Run startet.
2. **Keine Post-hoc-Schwellenanpassung (§8.3):** Torpfosten vorab fixiert, kein Verschieben — die E-15-Tore (H-01) sind das Muster.
3. **Gate-Auditor-Veto:** Kein Validierungslauf ohne registrierten Eintrag; nach dem Lauf wird ausschließlich gegen das registrierte Gate geurteilt (WEITER / DROP / GRAUBEREICH → `state/gate_log.md`).
4. **FDR-Pflicht (§8.2):** Benjamini-Hochberg α = 0.10 über jede Familie parallel getesteter Varianten (hier: F-S3, F-VOL, F-CFAR).
5. **Peso/L0-Verschärfung (§8.4):** Ein Single-Pass-„> Schwelle in 2 Fenstern" zählt NICHT als bestanden ohne Walk-Forward (≥ L2).
6. **Hartes Ein-Fenster-Abbruchkriterium (§8.5):** Wo registriert (H-02, H-03): Schwelle in EINEM disjunkten Fenster verfehlt → DROP/PARK, kein Nachverhandeln.
7. **Ein-Fenster-Wiederholungsregel für GRAUBEREICH:** Nur wo ein GRAUBEREICH vorregistriert ist (z. B. H-01) gilt: genau EIN (1) weiteres, vorab registriertes Fenster, danach endgültiges Urteil. (Quelle: H-01-Registrierung / verdict.md §Welle-1; PRD §8 stumm zur Wiederholungszahl — konservativ genau eine Wiederholung.)
8. **Append-only:** Bestehende Einträge werden nie editiert; Korrekturen/Ergänzungen nur als neuer, datierter Nachtrag unter dem Eintrag.
