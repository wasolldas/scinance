# Adversarial-Audit H-12 (C-12-FRAG) — Cross-Exchange-Fragmentierungsmatrix (RMT/MP-IPR)

- **Auditor:** unabhaengige Fresh-Session (nicht der Builder; DEC-20-Kontext gelesen)
- **Datum:** 2026-07-08
- **Gepruefte Artefakte:** `src/bybit_edge/research/c12_frag/{__init__,panel,spectrum,nulls,stats,driver}.py`,
  `scripts/c12_frag.py`, `scinance2-impl/handoff_local/{run_h12.ps1,run_h12.sh,README_H12.md}`,
  `tests/unit/test_c12_frag.py` — alle vollstaendig gelesen; Ground Truth:
  `edge-research-v3/results/deep_validation/hardened_hypotheses.md` (H-12-Abschnitt, Z. 78-93),
  `scinance2-impl/state/hypothesis_registry.md` (Welle 4, Z. 278-293), `edge-research-v3/CLAUDE.md` §2.
- **Tests selbst ausgefuehrt:** `PYTHONPATH=src python3 -m pytest tests/unit/test_c12_frag.py -q`
  → **8 passed in 17.9 s** (2026-07-08, diese Sandbox). Zusaetzlich eigene MC-Gegenrechnung zur
  IPR(v2)-Frage ausgefuehrt (s.u.).

---

## Verdict: **PASS-WITH-NOTES**

Kein kritischer oder hoher Defekt gefunden. Die urteilstragende Statistik (Stufe-b-Null, FDR,
Gate-Kriterien, Validitaets-Vorbedingung) ist spec-treu implementiert; kein Look-ahead; kein
stiller Mock-/Fallback-Pfad; Payload kapitalfrei-sauber. Drei Low-Befunde und mehrere
Info-Notizen unten — keiner davon blockiert den unbeaufsichtigten Lokal-Lauf.

---

## Spec-Fidelity-Check (Registry H-12 / hardened_hypotheses.md → Code)

| Konstante / Schwelle | Registriert | Code | Match? |
|---|---|---|---|
| Panel: N = 6 Serien (BTC/ETH × bybit/binance/deribit) | 2 Symbole × 3 Boersen | `DEFAULT_SYMBOLS`, `DEFAULT_EXCHANGES` (panel.py:44-47); Runner fixiert identisch | JA |
| Deribit-Notation | `BTC-PERPETUAL`/`ETH-PERPETUAL` | `DERIBIT_SYMBOL_MAP` + `map_exchange_symbol` (panel.py:50-89) | JA |
| Minutenbar | Last-Price je [t, t+60s) auf `ts_exchange_ms` | `max_by(price, ts_exchange_ms)` je `minute_idx` in DuckDB (panel.py:154-167) | JA |
| Forward-Fill | ≤ 1 Minute, sonst Minute ungueltig | `MAX_FFILL_MINUTES = 1`, Cap-Logik korrekt (panel.py:59, 192-209; per Tag, kein Cross-Day-Fill) | JA |
| T = 1440, Tag = UTC-Analyseeinheit | ja | `MINUTES_PER_DAY = 1440`, `build_day_panels` splittet an UTC-Mitternacht (panel.py:56, 252-277) | JA |
| Tages-Gueltigkeit | ≥ 1380/1440 gueltige Minuten JE Serie | `MIN_VALID_MINUTES_PER_DAY = 1380`, `np.all(valid_minutes >= …)` (panel.py:62, 273-274) | JA |
| Fenster W1/W2 | 2026-03-27..05-15 / 2026-05-16..07-04 (identisch H-09) | `DEFAULT_WINDOW_A/B` (driver.py:51-52); Runner ps1/sh hart identisch | JA |
| z-Standardisierung | Log-Returns je Serie JE TAG | `day_zscored_returns` nur auf dem Tages-Panel (spectrum.py:27-46) | JA |
| IPR(v) = Σ v_i⁴ | ja | `ipr()` mit Normierung (spectrum.py:70-77) | JA |
| Stufe a: MC-Gaussian-Wishart, 1000 Ziehungen, NICHT urteilstragend | Q = T/N = 240, „6×1440" | `wishart_null_mc` (nulls.py:69-100), `"verdict_bearing": False`; ABER `t_obs` = Median-t_eff statt 1440 (driver.py:207) | TEILS — s. Befund B-1 |
| Stufe b: Ein-Faktor-Null je Tag aus (λ1, v1), 1000 Reps, urteilstragend | βᵢ = v1ᵢ·√max(λ1−1,0), Var(εᵢ)=1−βᵢ² | `one_factor_betas` + `one_factor_null_day` exakt so; gleiche Pipeline (z→C→eig) wie Beobachtung (nulls.py:103-142) | JA |
| Tages-p | P(λ2_sim ≥ λ2_obs) | `empirical_p_ge`, Add-one `(n_ge+1)/(n+1)` — Repo-Konvention, konservativ (nulls.py:145-152) | JA |
| MC-Zahl | 1000 (beide Stufen) | `DEFAULT_N_MC = 1000`; CLI-Default 1000; Runner `$NMc=1000`/`N_MC=1000` | JA |
| FDR-Familie F-FRAG | ALLE Tages-λ2-Tests BEIDER Fenster, EINE Familie, BH α=0,10 | eine `benjamini_hochberg`-Familie ueber `family_days` beider Fenster (driver.py:158-162); `FDR_ALPHA = 0.10` (stats.py:12) | JA |
| BH-Kopie | eigene Kopie, kein Cross-Import | `stats.py` eigenstaendig; c12_frag importiert NUR numpy/duckdb/stdlib + eigene Submodule (Import-Scan bestaetigt) | JA |
| Gate (a) | Anteil FDR-sig gueltiger Tage ≥ 20 % | `SIG_DAY_SHARE_MIN = 0.20` (driver.py:58, 179-181) | JA |
| Gate (b) | Median-IPR(v2) ueber den FDR-sig Tagen ≥ 0,40 | `IPR_V2_MEDIAN_MIN = 0.40`, Median NUR ueber `sig` (driver.py:59, 183-186) | JA |
| Gate (c) | groesste v2²-Boersenlast (Summe je Boerse) an ≥ 70 % der FDR-sig Tage auf DERSELBEN Boerse | `exchange_loads` = Σ v2ᵢ² je Boerse, `dominant_exchange` je Tag, Modal-Anteil ≥ `DOMINANT_EXCHANGE_SHARE_MIN = 0.70` (spectrum.py:80-97, driver.py:187-203) | JA |
| Hartes Ein-Fenster-Kriterium | (a)∨(b)∨(c) in EINEM Fenster verfehlt → DROP | Kriterien je Fenster einzeln + `all_criteria_met_all_windows = all(...)`; gate-neutral, Auditor urteilt (driver.py:238, 244) | JA |
| Validitaets-Vorbedingung (KEIN Gate-Teil) | IPR(v1) ≤ 0,25 an ≥ 90 % der gueltigen Tage UND ≥ 35 gueltige Tage je Fenster; verfehlt → UNGUELTIG, KEIN Verdikt, NICHT DROP | `IPR_V1_MAX=0.25`, `IPR_V1_SHARE_MIN=0.90`, `MIN_VALID_DAYS_PER_WINDOW=35`; eigener `validity_status` "gueltig"/"ungueltig", `VALIDITY_NOTE` woertlich (driver.py:63-72, 172-177, 243-246) | JA |
| capital_free = true | verbindlich | `"capital_free": True` im Payload; kein bps/pnl/sharpe/friction/edge_-Feld (driver.py:252) | JA |
| Seed | (Registry registriert KEINEN Seed) | 42 als Default, im Payload berichtet | JA (Info I-2: README nennt Seed faelschlich „vorregistriert") |
| MIN_RETURNS_PER_DAY = 10 | nicht registriert | explizit als TECHNISCHER Degenerations-Guard dokumentiert (spectrum.py:20-24) | JA — ehrlich, s. Bewertung unten |

**MIN_RETURNS_PER_DAY-Bewertung (explizit geprueft):** Der Guard relaxiert NICHTS. Die
registrierte 1380-Minuten-Schwelle wird vorher in `panel.build_day_panels` erzwungen
(`day.valid`), und `driver.run` analysiert NUR `day.valid`-Tage. Auf einem registriert-gueltigen
Tag hat der kontemporaere Schnitt aller 6 Serien ≥ 1440 − 6·60 = 1080 Minuten ≫ 10 — der Guard
kann dort nie greifen; er faengt nur degenerierte synthetische Inputs (Null-Varianz). Der
Kommentar im Code sagt genau das. Ehrlich, kein verstecktes Gate-Lockern. Degenerierte Tage
werden zudem separat gezaehlt (`n_days_degenerate`) und im Report als „degeneriert" ausgewiesen.

---

## Bugs / Befunde

### B-1 · LOW · driver.py:207-209 — Stufe-a-Wishart-Referenz nutzt Median-t_eff statt registriertem T=1440
Die Registry/hardened-Spec registriert Stufe a als „Q = T/N = 240 … 1.000 MC-Ziehungen (6×1440)".
Der Driver zieht stattdessen mit `t_med = Median(t_eff)` (real ~1080-1439, Q ≈ 180-240).
Mildernd: Stufe a ist ausdruecklich NICHT urteilstragend, wird nirgends als Gate-Kriterium
benutzt (verifiziert: `wishart_reference` wird nur gespeichert/gerendert), und der Payload
berichtet `q_aspect` ehrlich mit. Trotzdem ist es eine woertliche Abweichung von einer
vorregistrierten Konstante. **Fix-Vorschlag:** `wishart_null_mc(n, 1440, …)` fest verdrahten
(Q=240 exakt) und t_med-Variante hoechstens ZUSAETZLICH berichten — Einzeiler, kein Einfluss
auf das Verdikt.

### B-2 · LOW · panel.py:20-28/119-131 — Docstring-Behauptung zur Bybit-LIVE-Payload-Form ist irrefuehrend
Der Loader extrahiert `COALESCE($.price, $.p)` top-level. Laut DATASET.md §6 ist die Bybit-LIVE
`publicTrade`-Form aber ein Mehr-Trade-Envelope (`{"topic":…,"data":[{…,"p":…},…]}`) — top-level
`$.p` existiert dort NICHT; solche Zeilen fallen im `IS NOT NULL`-Filter heraus. Der Docstring
behauptet, `$.p` decke „the Bybit live per-trade (p)" ab. Konsequenzen real begrenzt:
(1) die registrierten Fenster sind Backfill-gebunden (Basis-Bestand bis 2026-07-04, flache
`price`-Form); (2) sollte ein W2-Randtag nur live-form vorliegen, wird der Tag mangels Minuten
UNGUELTIG — lauter, sichtbarer Ausfall (Tageszaehler sinkt), NIEMALS stille Falschdaten;
(3) identisches Muster in c01/c10/c11/c13 (Repo-Konvention, dort gelaufen). **Fix-Vorschlag:**
Docstring korrigieren; optional spaeter eine `$.data[]`-Explosion nachruesten (fuer den
registrierten Lauf nicht noetig). KEIN stiller Mock-/Fabrikations-Pfad existiert: fehlende
Partitionen → Tag ungueltig; komplett leere Serie → `DataError` + Exit 1 (panel.py:143-148,
180-183; scripts/c12_frag.py:100-103). Kritischer Befund „stille Ersatzdaten": **nicht vorhanden**.

### B-3 · LOW · README_H12.md:11-15 — Status-Notiz „KEIN Commit" ist veraltet
Commit `4700fd2` enthaelt alle 11 H-12-Dateien (inkl. Tests); Working Tree ist clean. Die
Notiz stammt aus der DEC-20-Uebergangsphase. Reiner Doku-Fehler; vor dem Lokal-Lauf egal,
sollte aber bei naechster Gelegenheit korrigiert werden (Verwechslungsgefahr bei der
Morgen-Auswertung: „ungetestet/uncommitted" stimmt nicht mehr).

### Info-Notizen (keine Defekte)
- **I-1:** Kriterium-(a)-Nenner = analysierte Tage (panel-gueltig UND nicht degeneriert).
  Auf Realdaten identisch mit „gueltige Tage" (Degeneration dort unmoeglich, s.o.);
  `n_days_panel_valid` und `n_days_degenerate` werden getrennt berichtet — transparent.
- **I-2:** README_H12 fuehrt „Seed | 42" unter „Vorregistrierte Parameter"; die Registry
  registriert keinen Seed. Harmlose Ueberbehauptung (Seed steht im Payload, reproduzierbar).
- **I-3:** Bei UNGUELTIGEM Lauf werden die (a)/(b)/(c)-Felder trotzdem berichtet (gate-neutral)
  und `weiter_indication=False` gesetzt; der Markdown-Report beschriftet das korrekt als
  „nur bei gueltigem Lauf". Der gate-auditor darf `weiter_indication=False` bei
  `validity_status="ungueltig"` NICHT als DROP lesen — Payload und Report sagen das explizit.
- **I-4:** Stufe-b-Seeds sind je Tag distinkt (`seed=(seed, wi, di)`, driver.py:116) — keine
  Common-Random-Numbers-Kopplung der Tages-p-Werte; Stufe-a-Seed separat (`seed+1000+wi`).
  Deterministisch reproduzierbar.

---

## Zweistufige-Null-Korrektheit (Prioritaets-Check) — **KORREKT**

1. **Stufe a (nicht urteilstragend):** `wishart_null_mc` zieht iid-N(0,1)-Panels, laeuft durch
   dieselbe Pipeline, liefert λ1/λ2-Quantile + MP-Bulk (λ± = (1±√(1/Q))²; fuer Q=240:
   λ+ ≈ 1,133 — Formel verifiziert). Der Rueckgabewert traegt `"verdict_bearing": False`;
   im Payload heisst das Feld `wishart_reference`, im Markdown „Stufe a — NICHT urteilstragend",
   im Methodenblock „NICHT urteilstragend". **Kein Codepfad benutzt Stufe-a-Quantile als
   Gate-Kriterium** — die Kriterien (a)/(b)/(c) haengen ausschliesslich an `fdr_significant`
   (aus Stufe-b-p-Werten), `ipr_v2` und `dominant_exchange_v2`. Grep-verifiziert. Einzige
   Abweichung: t_med statt 1440 (Befund B-1, Low).
2. **Stufe b (urteilstragend):** exakt spec-konform — βᵢ = v1ᵢ·√max(λ1−1,0) (v1 normiert,
   |β|-Clip 0,999 als rein technischer Positivitaets-Guard), r̃ = β·f + ε mit Var(ε)=1−β²
   (Gesamtvarianz 1, verifiziert), t_obs = t_eff des Tages, 1000 Replikationen durch die
   IDENTISCHE Pipeline (z-Standardisierung → Korrelationsmatrix → Eigenzerlegung),
   Tages-p = Add-one P(λ2_sim ≥ λ2_obs). IPR(v2)-Nullverteilung wird mitberechnet und als
   `p_ipr_v2_one_factor` explizit „NOT verdict-bearing" mitberichtet — Gate (b) bleibt, wie
   registriert, der Median ueber den FDR-signifikanten Tagen gegen die fixe 0,40-Schwelle.
3. **FDR:** EINE F-FRAG-Familie ueber alle Tages-Tests beider Fenster (Registry: „alle
   Tages-λ2-Tests beider Fenster"), eigene BH-Kopie, Step-up-Logik korrekt (groesstes k mit
   p(k) ≤ k/m·α, alle Raenge ≤ k verworfen), α=0,10.
4. **Look-ahead:** keiner. Minutenbar nutzt nur Trades in [t, t+60s); ffill nur rueckwaerts
   in die Vergangenheit, per Tag gekappt; z-Standardisierung, C, Eigenzerlegung und die
   Stufe-b-Kalibrierung nutzen ausschliesslich den jeweiligen Tag (Registry definiert den Tag
   als in sich geschlossene Analyseeinheit — Ganztages-Standardisierung ist dort spec-konform,
   kein Leck ueber Tagesgrenzen).

---

## capital_free-Check — **SAUBER**

- Grep ueber Modul + CLI: `bps|pnl|sharpe|friction|edge_` erscheinen NUR in
  Negations-Docstrings („No friction, bps, PnL, Sharpe") — nie in Payload-Konstruktion,
  Feldnamen oder Werten. Payload traegt `"capital_free": true`.
- Test (f) und der CLI-Test erzwingen den Token-Scan auf dem kompletten JSON-Blob (lowercased)
  — bestanden (selbst ausgefuehrt).
- Runner-SUMMARYs enthalten die Negationszeile „KEINE bps/PnL/Sharpe/Friction" — identische
  Konvention wie run_h07/h08/h11 (verifiziert), betrifft nicht den JSON-Payload.
- Keinerlei Kosten-/Ertrags-/Arbitrage-Rechnung im Modul; H-12b-Doktrin im Payload/Report
  woertlich wiederholt.

---

## T2-Runner-Check (run_h12.ps1 / run_h12.sh) — **BESTANDEN**

| Pruefpunkt | ps1 | sh |
|---|---|---|
| Skript-Pfad als ERSTES CmdArg (run_h05c-Bugklasse) | JA (Z. 139-146, mit explizitem Kommentar) | JA (Z. 74-88) |
| `$null = $p.Handle` Handle-Cache | JA (Z. 92) | n/a |
| BelowNormal-Prioritaet | JA (Parent Z. 51 + Kind Z. 93) | n/a (akzeptierte Konvention) |
| Encoding | reine ASCII (file/grep-verifiziert: 0 Non-ASCII-Bytes); Summary via `[IO.File]::WriteAllText` | ASCII |
| Kein interaktiver Prompt | JA (keine Read-Host/Pause; `-NoNewWindow`, `ErrorActionPreference=Continue`) | JA (`set -u`, kein `set -e`, kein read) |
| Timeout | JA (WaitForExit 2400 s, Kill + rc=124) | JA (`timeout 2400`, Fallback ohne timeout-Binary) |
| `SUMMARY_<datum>.md` | JA (Z. 156-185) | JA (Z. 92-119) |
| Exit 0/1/2 deterministisch | JA (fail→1, sonst skip→2, sonst 0) | JA (identische Logik) |
| Junction-/Pfad-Pruefung ALLER DREI Boersen vor Lauf, sauberer SKIP | JA | JA |
| Dry-Run (HANDOFF_DRY_RUN/RC) | JA | JA |
| ExitCode-null-Quirk abgefangen | JA (rc=-2 + Hinweis) | n/a |

Laufzeitbudget plausibel: ~100 Tage × 1000 Reps à (1440×6-Panel + 6×6-eigh) ≈ Sekundenbruchteile
pro Tag vektorisierten numpy — die 2400 s sind grosszuegig; groesster Posten ist der
DuckDB-Tick-Scan. Speicher je Tag ~80 MB (1000×1440×6 float64) — unkritisch bei 82 GB RAM.

---

## Test-Coverage-Bewertung — **ADAEQUAT mit benannten Luecken**

Vorhanden und selbst gruen gelaufen (8/8):
- (a) Spektrum-Korrektheit am bekannten Ein-Faktor-Fall (IPR(v1) ≈ 1/6, IPR(v2) < 0,40),
- (b) Stufe-b-Null-Kalibrierungs-Plausibilitaet (λ2-Band um MP-Bulk, IPR-Wertebereich),
- (c) End-to-End-NULL-Kontrolle ueber `driver.run` (2×40 Tage rein ein-faktoriell →
  a-Anteil < 20 %, `all_criteria_met=False`, `weiter_indication=False` — die Gate-Kriterien
  werden also WIRKLICH exerziert, kein Import-Smoke),
- (d) End-to-End-POSITIV-Detektion (Marktfaktor + lokalisierter bybit-Restfaktor →
  a/b/c alle erfuellt, dominante Boerse „bybit", `weiter_indication=True`),
- (e) Validitaets-Vorbedingung: 10 Tage/Fenster → `validity_status="ungueltig"`, NICHT „drop",
- (f) capital_free + Token-Scan,
- (g) voller CLI-Lauf gegen synthetischen 3-Boersen-Hive-Baum (echtes Parquet, echte
  `payload_json`-Backfill-Form, rc=0, valides JSON, „ungueltig" korrekt bei 2 Tagen/Fenster),
- plus MIN_WINDOWS-Guard.

Luecken (alle nicht blockierend, Nachruestung empfohlen):
1. Keine direkten Panel-Layer-Unit-Tests: ffill-Cap-Semantik (genau 1 Minute), die
   1380-Gueltigkeitsgrenze (1379 vs. 1380), `map_exchange_symbol` isoliert, `_date_list`-Fehler.
2. Der CLI-Test schreibt fuer ALLE drei Boersen die `price`-Backfill-Form — die `$.p`-Form
   (Binance aggTrades) wird nie exerziert (haengt mit B-2 zusammen).
3. Kein Test des „Panel-Luecke"-Pfads im Driver (Tag mit `valid=False` im Fenster) und des
   NULL-Kontroll-Ideals „exakt 0/40 FDR-sig" — der Test prueft `< 20 %` (bei n_mc=200 ist der
   Add-one-p-Boden 1/201 ≈ 0,005 > BH-Rang-1-Schwelle 0,00125; faktisch ist ~0 erwartbar,
   die schwaechere Assertion ist vertretbar, aber das Ideal waere scharf testbar gewesen).
4. Kriterium-(c)-Gegenfall (wechselnde dominante Boersen → c verfehlt) ungetestet.

---

## Unabhaengiges Urteil zur IPR(v2) ≈ 0,30-0,35-Frage — **LEGITIM, kein geloester Test**

Eigene Gegenrechnung (Pipeline des Moduls selbst, 200 Tage je T; plus 20k-Draw-Referenz):
- Rein ein-faktorielle Panels, N=6: Median IPR(v2) = **0,312** (T=500) bzw. **0,297** (T=1439);
  ~20 % der Null-Tage liegen sogar ≥ 0,40.
- Theorie: fuer einen Haar-zufaelligen Einheitsvektor in R^N gilt E[Σuᵢ⁴] = 3/(N+2) = **0,375**
  bei N=6; eingeschraenkt auf das 5-dim Orthogonalkomplement von v1 gemessen: Mittel 0,358,
  Median 0,338 (selbst simuliert). 1/N = 0,167 ist das MINIMUM (perfekt delokalisiert),
  NICHT der Erwartungswert eines zufaelligen Residual-Eigenvektors.
- Ein Test, der exakte 1/6-Gleichheit verlangte, waere also mathematisch FALSCH gewesen; die
  Bandpruefung 0,15 < Median < 0,40 ist die korrekte Erwartung. Die Builder-Begruendung
  („RMT-Selektionseffekt: groesster von nahe-entarteten Residual-Eigenwerten") ist
  richtungsrichtig; der dominante Treiber ist schlicht die Haar-Statistik zufaelliger
  Richtungen (3/(N+2)), der Selektionseffekt drueckt den Median von 0,338 leicht auf ~0,30-0,31
  bzw. verschiebt die obere Flanke. **Kein Red Flag.**
- Wichtige Konsequenz fuer die Gate-Interpretation (an den gate-auditor): die registrierte
  0,40-Schwelle liegt nur knapp ueber dem Zufalls-Erwartungswert 0,375 — Kriterium (b) ALLEIN
  waere schwach (~20 % Zufalls-Ueberschreitung). Es greift aber registriert NUR ueber den
  FDR-signifikanten Tagen (unter H0 ≈ 0 Tage), sodass das Komposit-Gate trennscharf bleibt.
  Das ist die registrierte Konstruktion (Schwellen unantastbar, §2-Regel 4) — hier nur als
  Interpretations-Kontext dokumentiert, KEINE Aenderungsempfehlung.

---

## Pytest-Ergebnis (selbst ausgefuehrt, nicht uebernommen)

```
PYTHONPATH=src python3 -m pytest tests/unit/test_c12_frag.py -q
8 passed, 1 warning in 17.90s        (Warnung: repo-weite asyncio_mode-Config, nicht H-12)
```

## Empfohlene Folgeaktionen (nicht blockierend, Reihenfolge = Prioritaet)
1. B-1: Stufe-a-Referenz auf T=1440 (Q=240) fixieren, t_med-Variante optional zusaetzlich.
2. B-2: panel.py-Docstring zur Bybit-Live-Form korrigieren.
3. B-3: README_H12-Status-Notiz („KEIN Commit") aktualisieren; „Seed 42" nicht als
   „vorregistriert" fuehren (I-2).
4. Test-Luecken 1-4 bei naechster Gelegenheit schliessen (insb. 1380-Grenzfall + `$.p`-Form).
