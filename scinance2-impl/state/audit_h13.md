# Audit H-13 (F-TAILSHAPE, c13_tailshape) — unabhängiger adversarialer Code-Audit

- **Auditor:** unabhängige Audit-Session (nicht der Builder), 2026-07-08
- **Geprüft:** `src/bybit_edge/research/c13_tailshape/*` (7 Dateien, vollständig gelesen),
  `scripts/c13_tailshape.py`, `scinance2-impl/handoff_local/run_h13.ps1` + `run_h13.sh`,
  `README_H13.md`, `tests/unit/test_c13_tailshape.py`
- **Ground Truth:** `edge-research-v3/results/deep_validation/hardened_hypotheses.md` §H-13,
  `scinance2-impl/state/hypothesis_registry.md` §"H-13 · Tail-Form-Konsistenz" (Welle 4, GESPERRT),
  `edge-research-v3/CLAUDE.md` §2/§6

---

## Verdict: **PASS-WITH-NOTES**

Kern-Mathematik (POT/GPD-MLE, Hill, Block-Bootstrap, SVI, Breeden-Litzenberger,
GPD-PWM nach Hosking/Wallis, kombinierter Bootstrap-p, BH-FDR) ist korrekt
implementiert; Unlock-Gating ist eine echte Rechnung gegen den Manifest-Baum;
capital_free ist sauber; der T2-Runner erfüllt alle Repo-Konventionen; die
Test-Suite (13 Tests) läuft **grün** (selbst ausgeführt, 3.9 s).

ABER: Es gibt **eine anti-konservative Spec-Abweichung mit Verdikt-Relevanz**
(Bug 1: variable FDR-Familiengröße durch Je-Symbol-Entsperrung — Registry
definiert F-TAILSHAPE fix als 4 Zellen) und drei mittelschwere Punkte
(fehlende vorregistrierte Mixture-Sensitivität; kein Butterfly-Arbitrage-Check
mit stillem Density-Clipping; stiller Snapshot-Fallback entgegen README-Zusage).
Bug 1 sollte vor dem unbeaufsichtigten Lauf gefixt werden (Einzeiler, s.u.);
mildernd: das Payload trägt alle Roh-p-Werte, der gate-auditor kann BH mit
m=4 nachrechnen.

---

## Spec-Fidelity-Check (Konstante → registriert → Code → Match?)

| Konstante | Registriert (Registry/Hardened) | Code | Match |
|---|---|---|---|
| POT-Schwelle u_P | 99,5%-Quantil der 1-min-Verluste, FIX | `returns_tail.POT_QUANTILE = 0.995` | JA |
| Trailing-Fenster | 60 Handelstage strikt vor Snapshot-Tag | `TRAILING_DAYS = 60`, `trailing_dates()` strikt davor | JA |
| GPD-Schätzer (P-Seite) | GPD-MLE (scipy genpareto) | `genpareto.fit(exc, floc=0)` | JA |
| Block-Bootstrap | 60-min-Blöcke, 500 Reps | `BLOCK_LEN_MIN = 60`, `N_BOOTSTRAP = 500` | JA |
| Hill-Gegenprobe | k = #Exzedenzen über u_P | `hill_estimator` mit demselben u_P | JA |
| SVI | Raw-SVI-Fit auf IV-Smile | `svi_total_variance` (a,b,ρ,m,σ), LSQ-Multistart | JA |
| RND | Breeden-Litzenberger d²C/dK² | `rnd_from_svi` (Black-76, r=0) | JA |
| GPD-Schätzer (Q-Seite) | PWM (Hosking/Wallis) | `gpd_fit_pwm` — Formeln verifiziert (k̂=b0/(b0−2b1)−2, ξ=−k̂) | JA |
| RND-Tail-Quantil | unterhalb 5%-RND-Quantil | `TAIL_ALPHA = 0.05` | JA |
| Strike-Bootstrap | Resampling mit Zurücklegen, 500 Reps | `svi_rnd.N_BOOTSTRAP = 500` | JA |
| Tenor-Band | 20–45 DTE | `TENOR_DTE = (20, 45)` | JA |
| Delta-Band | 0,01 ≤ \|Δ\| ≤ 0,5 | `DELTA_BAND = (0.01, 0.5)` | JA |
| Strike-Floor (iii) | ≥ 12 Strikes je Tag/Symbol | `MIN_STRIKES = 12` | JA |
| RV-Ratio (i) | \|log(RV_5d(D1)/RV_5d(D2))\| ≥ log(1,5) | `LOG_RV_RATIO_MIN = math.log(1.5)` | JA |
| Tagesabstand (ii) | ≥ 10 Kalendertage | `MIN_GAP_DAYS = 10` | JA |
| RV-Fenster | 5 Tage strikt vor Snapshot-Tag | `RV_WINDOW_DAYS = 5` | JA (aber min_days=3-Toleranz, Bug 6) |
| Δξ-Floor | \|Δξ\| ≥ 0,15, nicht verhandelbar | `DELTA_XI_FLOOR = 0.15` | JA |
| Bootstrap-p | ≤ 0,05 nach BH-FDR | `BOOTSTRAP_P_MAX = 0.05`, `fdr_significant = BH-reject AND p≤0.05` | JA |
| FDR | BH α=0,10 über F-TAILSHAPE | `FDR_ALPHA = 0.10`, eigene BH-Kopie | JA (α) |
| **FDR-Familie** | **fix 2 Symbole × 2 Tage = 4 Zellen** | **variabel: nur Zellen entsperrter Symbole (2..4)** | **NEIN → Bug 1** |
| D1/D2-Wahl | deterministisch, frühester Tag, kein Cherry-Picking | `select_days`: frühester (iii)-Tag, frühester (i)+(ii)+(iii)-Folgetag | JA (je Symbol, s. Bug 1) |
| Snapshot-Zeit | 08:00 UTC deterministisch fixiert | `SNAPSHOT_HOUR_UTC = 8`, ±30-min-Fenster + Closest-Tick-Fallback | TEILS (Fallback still, Bug 4) |
| Nullhypothese/p | kombinierte Bootstrap-Verteilung (Block × Strike, unabhängig) | `combined_bootstrap_p`: äußeres Produkt, Null-Shift, zweiseitig, +1-Korrektur | JA |
| Gate-Kriterien | sign identisch D1/D2 ∧ \|Δξ\|≥0,15 ∧ p≤0,05 (FDR) ∧ Hill widerspricht nicht | `evaluate_gate` exakt so (beide Tage Pflicht, sign≠0) | JA |
| Mixture-Sensitivität | Lognormal-Weibull-Mixture-RND **mitberichtet** (nicht-urteilstragend) | **nirgends implementiert** | **NEIN → Bug 3** |
| Mean-Excess-Diagnostik | mitberichtet, wählt NICHT die Schwelle | `mean_excess_diagnostic`, "secondary" im Payload | JA |
| Seed / Determinismus | (nicht registriert) | Seed 42 fix in Runnern/CLI, dokumentiert | OK |
| Rechenaufwand-Tag | CPU | reine CPU-Pfade (scipy/numpy) | JA |
| capital_free | true, keine Friction-Wand-Referenz | `capital_free: true` im Payload, keine Kostenrechnung | JA |
| data_gated / GESPERRT | Entsperr-Bedingung Teil der Pre-Registration | `data_gated: true`, programmatische D1/D2-Suche, SKIP rc=2 | JA (Interpretation s. Bug 1) |
| Lookahead | Returns-Fenster strikt vor Snapshot | `trailing_dates` strikt davor; Options-Snapshot 08:00 desselben Tages; RV_5d strikt davor | JA — kein Lookahead gefunden |

## Bugs found

**Bug 1 — HIGH (Spec-Fidelity, anti-konservativ):**
`driver.py:67-96` (`check_unlock`: `unlocked = any(...)`) + `driver.py:204-225`
(Zellen nur für Symbole mit eigenem D1/D2-Paar) + `stats.py:103-133`
(`evaluate_gate` BH über die tatsächlich gemessenen Zellen).
Die Registry definiert F-TAILSHAPE **fix** als "2 Symbole × 2 Snapshot-Tage =
4 Zellen" und formuliert die Entsperr-Bedingung über EIN Tagespaar D1<D2 mit
(iii) "je Tag/Symbol". Der Code entsperrt je Symbol separat (ggf. verschiedene
Tagespaare) und läuft, sobald EIN Symbol ein Paar hat → BH ggf. über m=2 statt
m=4. Das ist strikt lenienter (Rang-Schwellen 0,05/0,10 statt 0,025/0,05) und
ist eine nach-registrierte Interpretationswahl in die NICHT-konservative
Richtung (verstößt gegen CLAUDE.md §6.3 "konservativere Lesart" und §2.4
Torpfosten-Regel; README_H13 dokumentiert die Wahl, ersetzt aber keine
Registrierung). **Fix (Einzeiler-Klasse):** Familie auf 4 Zellen auffüllen —
für jedes nicht gemessene (Symbol, Tag)-Paar eine Dummy-Zelle mit p=1,0 (und
`delta_floor_met=False`) in die BH-Familie geben; alternativ konservativ erst
laufen, wenn BEIDE Symbole ein gemeinsames Paar haben. Mildernd: Payload trägt
Roh-p-Werte, der gate-auditor kann m=4 nachrechnen.

**Bug 2 — MEDIUM (numerische Validierung):**
`svi_rnd.py:121-150`. Kein Butterfly-Arbitrage-Check (Gatheral g(k) ≥ 0) auf
dem SVI-Fit; negative BL-Dichte wird still bei 0 geclippt und renormalisiert
(`q = np.clip(q, 0, None)`), ohne Diagnose im Payload (z. B. geclippte
Massefraktion). Ein arbitrage-verletzender Fit auf einem verrauschten realen
Smile verformt so unbemerkt genau den linken Tail, der ξ_Q trägt. Positiv:
w>0 wird auf Smile UND Grid geprüft, Null-Masse wirft `RndError`, degenerierte
Tails werfen statt NaN zu liefern. **Fix:** g(k)-Check nach dem Fit (Reject →
`RndError`), mindestens aber `clipped_mass_fraction` ins `options_side`-Payload.

**Bug 3 — MEDIUM (fehlender vorregistrierter Report-Teil):**
Die Registry schreibt vor: "Lognormal-Weibull-Mixture-RND als
nicht-urteilstragende Sensitivität mitberichtet (Anti-Gaming: kein
Methoden-Wechsel nach Ergebnis)". Grep über das gesamte Modul: **nicht
implementiert**, nicht im Payload, nicht im README erwähnt. Nicht
urteilstragend, aber ein registriertes Anti-Gaming-Artefakt fehlt.
**Fix:** Mixture-RND-Fit + ξ_Q-Sensitivität als `sensitivity`-Block ins
Payload (oder als datierter Registry-Nachtrag explizit deferren — nicht still
weglassen).

**Bug 4 — MEDIUM (Doku/Code-Mismatch, stiller Fallback):**
`options_loader.py:207-210` vs. `README_H13.md` Punkt 3. README behauptet, der
Closest-Tick-Fallback (leeres ±30-min-Fenster um 08:00 UTC) sei "im Payload
sichtbar via Tageswahl-Diagnostik" — es gibt **keine** solche Diagnose. Der
Fallback kann still einen Tick weit weg von 08:00 (auch 23:xx) als "Snapshot"
verwenden, obwohl die Registry "08:00 UTC deterministisch fixiert" vorschreibt.
**Fix:** `snapshot_fallback_used` + `snapshot_ts_ms` ins Smile-/Zell-Payload;
optional Fallback auf max. ±N Stunden begrenzen.

**Bug 5 — LOW-MED (unregistrierte Daten-Toleranz):**
`returns_tail.py:42` `MIN_TRAILING_DAYS = 30`: ein "trailing 60 Tage"-Fenster
wird noch mit nur 30 vorhandenen Tagen gefittet. Keine solche Toleranz
registriert; README erwähnt sie nicht. Richtung: lenient (dünne Datenlage wird
geurteilt statt invalidiert; vgl. H-12s expliziten 35-Tage-Floor). **Fix:**
Floor dokumentieren oder konservativ auf ~55/60 anheben; bei Unterschreitung
Zelle invalidieren.

**Bug 6 — LOW:** `snapshot_selection.py:151` — RV_5d wird mit
`min_days=max(2, 5-2)=3` toleriert; "RV_5d" kann faktisch RV_3d sein und
über die Regime-Bedingung (i) mitentscheiden. **Fix:** min_days=5 (oder
dokumentieren).

**Bug 7 — LOW:** `stats.py:86-100` `hill_contradicts` — NaN-Hill oder
exakter Null-Sign gilt als neutral (kein Widerspruch); die Registry-Formel
verlangt Vorzeichen-GLEICHHEIT. De facto unerreichbar (u_P>0 praktisch immer,
k≥20 durch den GPD-Fit erzwungen), aber die leniente Operationalisierung ist
nur im README, nicht in der Registry fixiert.

**Bug 8 — LOW-MED (Portabilität, Crash-Risiko am Zielsystem):**
`svi_rnd.py:147` nutzt `np.trapezoid` (existiert erst ab NumPy 2.0), aber
`pyproject.toml:15` pinnt nur `numpy>=1.26`. Auf einer lokalen 1.26.x-Umgebung
crasht der volle Lauf mit `AttributeError` (→ Runner-FAIL, kein Falsch-Urteil).
Sandbox hat 2.4.6, Tests grün. c13 ist das einzige Modul mit `trapezoid`.
**Fix:** `numpy>=2.0` pinnen oder `np.trapz`-Fallback.

**Bug 9 — LOW (Footgun):** `driver.py:95` — `check_unlock` gibt den nicht
JSON-serialisierbaren Schlüssel `"_selections"` zurück; beide Aufrufer poppen
ihn korrekt, jeder künftige dritte Aufrufer crasht beim Serialisieren.

**Kein Befund:** Lookahead/Kausalität sauber (Returns-/RV-Fenster strikt vor
dem Snapshot-Tag; Tenor liegt in der Zukunft, wird aber nur als Preisobjekt
des Snapshots benutzt); DuckDB-Zugriffe read-only mit Symbol-/Datums-Regex-
Validierung; 1-min-Return-Bildung schließt Minuten-Lücken korrekt aus;
BH-Implementierung (Step-up) korrekt; PWM-Formeln gegen Hosking/Wallis 1987
verifiziert; kombinierter Bootstrap-p (Null-Shift, zweiseitig, +1) korrekt;
DATASET.md-Payload-Form (`params.channel/data[].instrument_name/mark_iv`)
stimmt mit dem Loader überein; keine Hardcodierung von D1/D2 oder Daten.

## Test coverage assessment

`PYTHONPATH=src python3 -m pytest tests/unit/test_c13_tailshape.py -q` →
**13 passed in 3.91 s** (selbst ausgeführt, 2026-07-08). Abgedeckt:

- ξ_P-Recovery an bekanntem wahren ξ (threshold-stabiler GPD-Fixture) — JA
- Hill-Konsistenz mit GPD auf denselben Daten — JA
- Instrument-Parser inkl. **Regression für den 0d6535-Bug** (lowercase-`d`-
  Strike UND komplett-lowercase-Name) — JA
- SVI-Refit-Exaktheit + BL-RND-Sanity (nicht-negativ, Einheitsmasse, Peak
  nicht am Grid-Rand) — JA
- GPD-PWM-Recovery — JA
- Deterministische D1/D2-Selektion (gefunden + sauber nicht-gefunden + leer) — JA
- Gate-Positiv-Detektion, Null-Kontrolle, Hill-Widerspruch-Blockade — JA
  (auf `evaluate_gate`-Ebene mit fabrizierten p-Werten)
- capital_free-Wächter (AST-Identifier-Scan über alle Moduldateien) — JA
- End-to-End CLI gegen synthetischen Harvester-Baum (Bybit-Returns UND
  Deribit-Options-Chain): Unlock gefunden → rc=0, voller Lauf → rc=0 +
  JSON/MD-Artefakte; gesperrter Baum → rc=2 SKIP beide Pfade — JA

**Lücken (keine davon blockierend):** (a) keine direkten Tests für
`benjamini_hochberg` und `combined_bootstrap_p` (nur indirekt via
`evaluate_gate`/E2E); (b) Put-Call-Paritäts-Forward-Fallback und
Closest-Tick-Snapshot-Fallback ungetestet (die zwei fragilsten Loader-Pfade);
(c) der E2E-Positivfall assertet keine bekannte Gate-RICHTUNG (Δξ-Vorzeichen)
durch die volle Pipeline; (d) der capital_free-Scan prüft Identifier, nicht
den emittierten JSON-Text; (e) kein Test, dass ein Sign-Flip zwischen D1/D2
das Symbol-Gate blockt (nur indirekt über die Null-Kontrolle).

## capital_free check result

**SAUBER.** Eigenes Grep (case-insensitive) über alle 7 Moduldateien + CLI auf
`bps|pnl|sharpe|friction|edge_`: **0 Treffer** (auch in Docstrings/Strings).
Payload-Konstruktion (`driver.py`) enthält keine Kosten-/Ertragsfelder;
`capital_free: true` + `data_gated: true` in Voll-, SKIP- und
Unlock-Only-Payload; Tests erzwingen beides zusätzlich per AST-Scan.

## T2 runner check result

**run_h13.ps1: BESTANDEN** gegen alle bekannten Bug-Klassen:
Skript-Pfad ist ERSTES CmdArg vor allen `--flags` (Z. 138-144/146-152, mit
explizitem run_h05c-Kommentar Z. 137); `$null = $p.Handle` Handle-Cache
(Z. 89) inkl. rc=null-Quirk-Behandlung (Z. 97 → rc=-2 FAIL); BelowNormal für
Runner (Z. 47) und Kindprozess (Z. 90); reine ASCII-Datei (byte-geprüft: 0
Non-ASCII, PS-5.1-sicher); kein interaktiver Prompt (kein Read-Host/pause);
Timeouts 900 s/3600 s via `WaitForExit` + Kill; `SUMMARY_<datum>.md` wird
immer geschrieben; Exit deterministisch 0/1/2 (rc 2 des CLI → SKIP, nicht
FAIL); Pfad-Vorprüfung beider Datenseiten → sauberer SKIP statt Crash;
Dry-Run-Pfad vorhanden. **run_h13.sh: BESTANDEN** (spiegelgleich, `timeout`-
Nutzung mit Fallback, exit 0/1/2, SUMMARY, keine unescaped Backticks).
Kosmetik: `.ps1` hat LF-Zeilenenden ohne BOM — für den reinen ASCII-Body
unkritisch.

## Unlock-gate correctness

Die Entsperr-Prüfung ist eine **echte Berechnung gegen den Manifest-Baum**:
`list_snapshot_dates` enumeriert reale `date=`-Partitionen,
`scan_and_select` zählt je Tag die tenor-/delta-gefilterten Strikes über den
echten Smile-Builder und rechnet RV_5d aus echten Bybit-Returns; nichts ist
hartcodiert (kein D1/D2, kein Datum). Vor Entsperrung liefert der Driver
`skip=true, cells=[], gate=None`, das CLI rc=2, der Runner SKIP/exit 2 —
**kein verdikt-tragendes Ergebnis vor Entsperrung** und kein Fit wird
gerechnet. Schwellen (log 1,5 / 10 Tage / 12 Strikes) exakt registriert.
EINSCHRÄNKUNG: die Je-Symbol-/Beliebig-ein-Symbol-Interpretation der
Entsperrung ist die leniente Lesart der Registry (→ Bug 1).

## SVI/RND numerical-stability assessment

Solide Grundhygiene: deterministischer Multistart-LSQ mit Bounds
(b≥0, |ρ|<0,999, σ>0), w>0-Check auf Smile UND RND-Grid (Reject via
`RndError` statt NaN), dichtes fixes 801-Punkte-Grid, Null-Masse-/Degenerat-
Checks in Quantil- und Excess-Sample-Bildung, Bootstrap-Replikate mit <5
distinkten Strikes oder Fit-Fehlern werden gezählt verworfen (NaN, nie still
weitergereicht), PWM statt MLE auf der Q-Seite (robust, korrekt
implementiert). **Schwachstellen:** kein Butterfly-Arbitrage-(g(k))-Check und
stilles Clipping negativer BL-Dichte ohne Diagnose (Bug 2); Grid-Trunkierung
bei log-moneyness −2,5 (~8 % des Forwards) biast ξ_Q minimal nach unten —
dokumentiert, für realistische 30-Tage-Vols vernachlässigbar und für alle
Zellen/Reps identisch.

## Instrument-name-parsing bug fix — BESTÄTIGT

`options_loader.py:71`: Zeichenklasse `[.dD]` im Strike-Pattern, und
`options_loader.py:102`: `.replace("d", ".").replace("D", ".")` — die
Kombination macht den dokumentierten Fix vollständig: `.strip().upper()`
(Z. 95) hebt kleinschreibige `d`-Dezimaltrenner auf `D`, das Pattern matcht
beide, die Normalisierung führt beide auf `.` zurück.
Regressionstest vorhanden: `test_parse_instrument_name_examples` prüft exakt
den Bug-Fall `XRP_USDC-1JAN27-0d6535-P` → strike ≈ 0,6535 UND den
Komplett-Lowercase-Fall `btc-27jun26-70000-c`, plus Negativfälle (Garbage,
falscher Monat, falsches C/P). Test läuft grün.

---

## Empfohlene Reihenfolge vor dem 2-Wochen-Lauf

1. **Bug 1** fixen (Familien-Padding auf 4 Zellen mit p=1 für ungemessene
   Zellen — konservativ, klein, testbar) — einziger Punkt mit
   Verdikt-Arithmetik-Relevanz.
2. **Bug 8** (`numpy>=2.0` pinnen oder trapz-Fallback) — verhindert einen
   harten Crash auf einer 1.26-Umgebung.
3. Bug 2/4 (Diagnose-Felder `clipped_mass_fraction`, `snapshot_fallback_used`)
   — billig, erhöhen die Auditierbarkeit des ersten echten Laufs erheblich.
4. Bug 3 (Mixture-Sensitivität) nachreichen oder als datierten
   Registry-Nachtrag explizit deferren.
