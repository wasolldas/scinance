# Audit H-11 (F-ANEN, c11_anen) — adversarial code audit

- **Auditor:** unabhaengiger Adversarial-Auditor (nicht der Builder), 2026-07-08
- **Gepruefte Artefakte:** `src/bybit_edge/research/c11_anen/{__init__,features,analog,baseline,stats,driver}.py`,
  `scripts/c11_anen.py`, `scinance2-impl/handoff_local/{run_h11.ps1,run_h11.sh,README_H11.md}`,
  `tests/unit/test_c11_anen.py`
- **Ground Truth:** `edge-research-v3/results/deep_validation/hardened_hypotheses.md` §H-11,
  `scinance2-impl/state/hypothesis_registry.md` (Welle 4, H-11, GESPERRT),
  `edge-research-v3/CLAUDE.md` §2/§5, `edge-research-v3/reference/DATASET.md` §7

---

## Verdict: **FAIL**

Ein kritischer Spec-Fidelity-Defekt (registrierte CRPS-Metrik nicht implementiert) plus zwei
High-Findings. Die Unlock-Gate-Mechanik selbst ist ehrlich und funktioniert (heute: sauberer
SKIP, Exit 2, kein Datenlauf, kein Verdikt) — im **gesperrten** Zustand richtet der Code in den
2 Wochen keinen Schaden an. Aber der Modul-Daseinszweck ist der Lauf NACH Entsperrung, und in
diesem Zustand wuerde er (a) nicht die registrierte Methode messen und (b) auf echten Tickdaten
voraussichtlich OOM/Timeout laufen. Vor einem entsperrten Lauf MUSS Bug 1 (und 2, 3) gefixt sein.

Pytest real ausgefuehrt: `PYTHONPATH=src python3 -m pytest tests/unit/test_c11_anen.py -q`
→ **18 passed in 4.2 s** (2026-07-08, diese Maschine). Die Tests sind gruen — aber sie
zementieren Bug 1 (sie testen die implementierte, nicht die registrierte Metrik).

---

## Spec-Fidelity-Check

| Konstante / Regel | Registriert (Registry/hardened) | Code | Match? |
|---|---|---|---|
| k (Analog-Pool) | 20 | `analog.py:29 K_ANALOGS=20` | JA |
| Embargo | 30 Tage, Kandidat t' ≤ t−30 | `analog.py:32/50` (inkl. Obergrenze t−30) | JA |
| Feature-Vektor | 5 Features: log RV_1d/5d/20d, Funding-Tagesmittel, Funding-5d-Trend; OI EXKLUDIERT | `features.py:41-48,248-270` | JA |
| Distanz | gewichtet-euklidisch auf z-standardisierten Features | `analog.py:100-105` (dist² statt dist — ordnungs-invariant) | JA |
| z-Standardisierung | expanding bis t−30 | `analog.py:58-68` (nur Kandidaten-Bibliothek ≤ t−30) | JA |
| Gewichts-Grid | {0; 0,5; 1; 1,5; 2}⁵, **normiert**, danach eingefroren | `analog.py:35` Grid ok, eingefroren ok; **Normierung fehlt** (folgenlos: Skalierung aendert argsort nicht) | JA (Anm.) |
| LOO-CRPS-Tuning nur auf L | L = 2024-03-27..2025-09-30 | `driver.py:67,218-225`; Kandidaten ≤ t−30 ⇒ kein W1/W2-Leak | JA |
| **AnEn-Vorhersage** | **empirische VERTEILUNG der log-RV(t'+1..t'+3) der 20 Analoga**; entartetes CRPS gilt nur fuer die HAR-Punktprognose | Ensemble wird auf den **Mittelwert kollabiert**, gescort mit \|mean−obs\| (`analog.py:107`, `stats.py:33-41`, `driver.py:258`) | **NEIN — kritisch (Bug 1)** |
| RV-Basis | 1-min-Returns ("publicTrade (1-min-RV)", Ziel "1-min-Returns") | Tick-zu-Tick-Returns aller Trades (`features.py:113-149`) | **NEIN (Bug 2)** |
| Ziel | log annualisierte RV ueber t+1..t+3, strikt Zukunft | `features.py:273-293` (t+1..t+3, Tag t exkludiert) | JA (bis auf 1-min-Basis) |
| Horizont | 3 Tage | `features.py:46` | JA |
| HAR-Baseline | OLS log-RV (RV_1d, RV_5d, RV_22d), expanding ≤ t−30, monatlicher Refit, CRPS=\|Prognose−Beobachtung\| | `baseline.py:39-96` | JA |
| Fenster | L 2024-03-27..2025-09-30 · W1 2025-10-01..2026-03-26 · W2 2026-03-27..2026-06-30 | `driver.py:67-69` woertlich | JA |
| Symbole | BTC, ETH | `driver.py:64` BTCUSDT/ETHUSDT | JA |
| Null/Bootstrap | Block-Bootstrap, Blocklaenge 5, 1000 Reps, DM-artig, H0 mean(HAR−AnEn) ≤ 0, je Symbol×Fenster | `stats.py:29-98`, `driver.py:262-264` | JA |
| Seed | nicht registriert | fest 42 (deterministisch) | JA (ok) |
| Gate-Schwellen | CRPSS ≥ 0,05 UND p ≤ 0,05 nach BH-FDR α=0,10 | Konstanten korrekt (`stats.py:21-30`); **`cell_pass` prueft p ≤ 0,05 NICHT** (`driver.py:289`) | **TEILS (Bug 3)** |
| FDR-Familie | F-ANEN, 4 Zellen (2 Sym × 2 Fenster), α=0,10, eigene BH-Kopie | `driver.py:61,284-289`, `stats.py:101-126` (eigene Kopie, korrektes BH) | JA |
| PIT/Rank-Histogramm | nicht-urteilstragend **mitberichtet** | fehlt komplett | **NEIN (Bug 5)** |
| Entsperr-Bedingung | Manifest (DATASET.md §7) lueckenlose done_days, publicTrade + rest.fundingRate, BTC+ETH, 2024-03-27..2026-03-26, ≥730 Tage | `driver.py:82-137`: echter Scan, aber Partitions-Ordner-Proxy statt Manifest | TEILS (Bug 4) |
| capital_free | true, keine Kostenrechnung | Payload `capital_free: true`; keine Kosten-Groessen | JA |
| Rechenaufwand-Tag | CPU | numpy/DuckDB, GPU-los | JA |

Zahl 730 verifiziert: `date_range("2024-03-27","2026-03-26")` = 730 Tage (Test `test_check_unlock_true_...` prueft das explizit).

---

## Bugs found

### BUG 1 — KRITISCH: AnEn wird als Punktprognose gescort, nicht als Verteilung
- **Ort:** `src/bybit_edge/research/c11_anen/analog.py:107` (Forecast = `mean(targets[sel])`),
  `stats.py:3-6,33-41` (`crps_point` als einzige CRPS-Implementierung),
  `driver.py:258` (`crps_point(anen_arr[paired], obs)`), Tuning ebenso (`analog.py:134,193`).
- **Befund:** Die Registry fixiert: "AnEn-Vorhersageverteilung = **empirische Verteilung** der
  log-RV(t'+1..t'+3) der 20 Analoga". Das entartete CRPS (=\|Prognose−Beobachtung\|) ist im
  Registry-Text ausschliesslich der **Baseline**-Klausel zugeordnet ("Baseline: HAR-RV ... CRPS
  der Punktprognose = ... entartete Verteilung"). Der Code kollabiert das 20er-Ensemble auf
  seinen Mittelwert und scort \|mean−y\| — damit ist H-11 de facto ein k-NN-Punktschaetzer vs.
  OLS (MAE vs. MAE), exakt die "Einzelmodell-Punktprognose"-Konstellation, von der sich die
  Pre-Registration ausdruecklich abgrenzt ("Verteilungsmass CRPS, kein R²"; Hypothese: "besser
  **kalibrierte Verteilungsvorhersage**"). Der stats.py-Docstring behauptet faelschlich, die
  Registry fixiere "EXACTLY this simplified variant" — das ist eine Fehllesung der Quelle;
  README_H11.md (Z. 41-42) wiederholt sie. Auch das LOO-Gewichtstuning optimiert dadurch das
  falsche Ziel. Ein Lauf mit dieser Metrik waere gegen das registrierte Gate NICHT adjudizierbar
  (Verfassungsregel §2.4: keine Torpfosten-Verschiebung — in keine Richtung).
- **Fix:** Ensemble-CRPS implementieren: CRPS(F̂,y) = (1/k)Σ|xᵢ−y| − (1/(2k²))ΣᵢΣⱼ|xᵢ−xⱼ|;
  `analog_forecast` gibt die k Member-Targets zurueck (tut es via `sel` schon); Tuning und
  Driver auf Ensemble-CRPS umstellen; HAR bleibt \|Prognose−Beobachtung\|. Tests (Positiv/Null)
  auf die korrigierte Metrik nachziehen.

### BUG 2 — HOCH: RV aus Tick-Returns statt registrierter 1-min-Returns + fetchall-Blowup
- **Ort:** `src/bybit_edge/research/c11_anen/features.py:113-149` (`load_daily_rv`).
- **Befund:** (a) Registriert ist 1-min-RV ("bybit publicTrade (1-min-RV)"; "Ziel: ...
  (1-min-Returns)"). Der Code summiert quadrierte Log-Returns **konsekutiver Trades** —
  tick-level RV ist durch Microstructure-Noise (Bid-Ask-Bounce) systematisch aufgeblaeht und
  ein anderer Messgegenstand. (b) Praktisch fataler: `con.execute(sql).fetchall()` zieht ALLE
  Ticks von ~825 Tagen × 2 Symbolen als Python-Tupel in den RAM. Bei realem BTCUSDT-Volumen
  (Groessenordnung 10⁶+ Trades/Tag) sind das ≥10⁸-10⁹ Zeilen je Symbol → sicherer OOM (82-GB-
  Maschine) bzw. Timeout weit ueber dem 60-min-Runner-Budget (`TmoStep=3600`). Das
  c01-Vorbild laedt nur ~100-Tage-Fenster — das Muster skaliert nicht auf die H-11-Range.
- **Fix:** Aggregation in DuckDB: 1-min-Last-Price-Bars (`ts_exchange_ms/60000`), daraus
  Tages-RV = sqrt(Σ r²_1min) per SQL `GROUP BY date` — es kommen nur ~825 Zeilen je Symbol
  zurueck. Erfuellt gleichzeitig die 1-min-Registrierung.

### BUG 3 — HOCH: `cell_pass` erzwingt Bootstrap-p ≤ 0,05 nicht
- **Ort:** `src/bybit_edge/research/c11_anen/driver.py:289`
  (`c["cell_pass"] = bool(c["crpss_ge_min"] and rej)`).
- **Befund:** Gate (woertlich): "CRPSS ≥ 0,05 UND Block-Bootstrap-p ≤ 0,05 nach BH-FDR α=0,10".
  BH-Rejection bei α=0,10 impliziert NICHT p ≤ 0,05: Familie {0,01; 0,02; 0,04; 0,09} → BH
  verwirft alle 4, die 0,09-Zelle bekaeme `cell_pass=True`. Die verdiktfoermigen Flags
  (`cell_pass`, `both_windows_pass`, `any_symbol_both_windows_pass`) koennten den gate-auditor
  in Richtung WEITER fehlleiten. Die Schwester-Module machen es richtig:
  `c09_bunch/driver.py:178-186` (`boot_p_le_max AND fdr_significant`),
  `c10_pointer/driver.py:194` (`rej and p <= SURROGATE_P_MAX`). `BOOTSTRAP_P_MAX` wird in
  c11 zwar in `gate_thresholds` reportet, aber nie angewandt.
- **Fix:** `cell_pass = crpss_ge_min AND fdr_significant AND bootstrap_p <= BOOTSTRAP_P_MAX`
  (+ Feld `boot_p_le_max` wie in c09), Test ergaenzen.

### BUG 4 — MITTEL: Unlock-Check ist Partitions-Ordner-Proxy statt Manifest-done_days
- **Ort:** `src/bybit_edge/research/c11_anen/driver.py:109-128` (`check_unlock`).
- **Befund:** Registrierte Entsperr-Bedingung: "Manifest-Abfrage (DATASET.md §7) bestaetigt
  lueckenlose done_days". Das reale Manifest ist `harvest_manifest.sqlite` (Tabelle
  `partitions`, Status DONE/EMPTY/FAILED/PENDING); ein Lese-Muster existiert bereits im Repo
  (`scinance2-impl/handoff_local/harvest_coverage.py`). `check_unlock` prueft stattdessen
  `date=`-Ordner mit ≥1 `*.parquet` — akzeptiert dabei sogar 0-Byte-Dateien (die Tests nutzen
  `.touch()`!). Waehrend des laufenden Deep-Backfills kann eine Partition auf der Platte
  liegen, deren Manifest-Status noch FAILED/RUNNING ist → der Proxy kann FRUEHER entsperren
  als die registrierte Bedingung (anti-konservativ). Umgekehrt wuerden EMPTY-Tage den Proxy
  sperren (konservativ, fuer BTC/ETH-publicTrade praktisch irrelevant). Positiv: Der Check ist
  ein ECHTER, korrekter Scan (kein Stub), verlangt alle 730 Tage × 2 Streams × 2 Symbole,
  einzelner Fehltag sperrt wieder, und der README legt den Proxy offen.
- **Fix:** Wenn `harvest_manifest.sqlite` existiert: done_days-Query (read-only, `mode=ro`) als
  primaere Quelle, Partitions-Scan nur als Fallback; mindestens aber Dateigroesse > 0 fordern.

### BUG 5 — MITTEL: registriertes Sekundaer-Diagnostikum (Rank-Histogramm/PIT) fehlt
- **Ort:** `driver.py` (Payload/Markdown) — nirgends vorhanden.
- **Befund:** Registry: "Rank-Histogramm/PIT als nicht-urteilstragende Kalibrierungs-
  Sekundaerdiagnose **mitberichtet**." Nicht implementiert — und mit dem Mean-Kollaps aus
  Bug 1 auch nicht implementierbar (PIT braucht die Ensemble-Verteilung). Nicht
  urteilstragend, aber Bestandteil der Pre-Registration des Reports.
- **Fix:** Nach Bug-1-Fix: PIT = Rang der Beobachtung im 20er-Ensemble je Prognosetag,
  Histogramm (z.B. 21 Bins) je Zelle in Payload + Markdown.

### Minor / Notizen (keine Gate-Relevanz)
- `analog.py`: Gewichte nicht "normiert" (Registry-Wort) — folgenlos, da Distanz-Skalierung
  die k-NN-Auswahl nicht aendert; als Kommentar dokumentieren.
- `baseline.py:24`: `MIN_FIT_SAMPLES=30` ist eine unregistrierte (aber deterministische,
  konservative) Guard-Konstante.
- `scripts/c11_anen.py`: exponiert Overrides fuer k/Embargo/Grid/Fenster (Fixture-Zweck ist
  dokumentiert; Runner nutzt registrierte Defaults) — Restrisiko Fehlbedienung.
- `driver.py:157-158`: SKIP-Reason "Manifest-Coverage <730 Tage lueckenlos" ist bei
  Luecken-trotz-voller-Spanne sprachlich unpraezise (kosmetisch).
- `analog.py:178`: `ValueError` aus dem Tuning wuerde im CLI als Traceback enden (Exit 1,
  aber kein sauberer FAIL-Text); nur nach Entsperrung mit pathologischen Daten erreichbar.
- LOO-Interpretation: "Leave-one-out" ist als walk-forward-Embargo implementiert (Kandidaten
  nur ≤ t−30, keine Zukunfts-Kandidaten innerhalb L). Das ist STRENGER als klassisches LOO
  und deckt sich mit der registrierten Kandidatenregel ("expanding, walk-forward, kein
  Lookahead") — vertretbar, kein Defekt.
- `skip_unlock_check` (driver.py:181) wird nirgends benutzt (weder CLI noch Runner noch
  Tests) — toter, aber harmloser Parameter; kein Backdoor-Pfad erreichbar.

---

## Look-ahead / Kausalitaet / Embargo (Code + Tests)

Kein Leak gefunden:
- Features t nutzen nur Tage ≤ t (`features.py:208-268`); Ziel nutzt strikt t+1..t+3
  (`features.py:286-292`). Bit-Identitaets-Test gegen Zukunfts-Korruption vorhanden
  (`test_features_are_causal_no_lookahead`, `test_target_uses_only_strictly_future_days`).
- Analog-Kandidaten strikt ≤ t−30; Kandidaten-Target endet ≤ t−27 < t; z-Statistiken nur aus
  der Kandidaten-Bibliothek. Embargo-Test pflanzt ein perfektes Duplikat bei t−10 und verlangt
  dessen Ablehnung (`test_embargo_rejects_near_analog_candidate`) — gut konstruiert.
- HAR-Fit nur auf Samples ≤ t−30 (Sample-Target endet ≤ t−27); Kausalitaets-Test korrumpiert
  t−29.. und verlangt identische Prognose (`test_har_fit_is_causal_wrt_embargo`).
- Tuning nur auf L; wegen Kandidatenregel ≤ t−30 kein W1/W2-Kontakt; Gewichte danach
  eingefroren (Determinismus-Test vorhanden).

---

## Test coverage assessment

18 Tests, alle gruen (real ausgefuehrt, 4,2 s). Abdeckung: Feature-Wert-Korrektheit,
No-Lookahead (Features/Target/HAR), Embargo (geplantes Duplikat), HAR-Recovery auf AR-Prozess,
CRPS/CRPSS/Bootstrap/BH-Eigenkopie, Positiv-Detektion (Regime-Muster, CRPSS ≥ 0,05 UND
p ≤ 0,05), Null-Kontrolle (AR(1) ohne Struktur), capital_free (AST-Identifier-Scan + Payload-
Flag), Unlock beide Zweige (kurz→locked; 730 Tage→unlocked; Ein-Tages-Loch→wieder locked;
kurze Range trotz lueckenlos→locked), E2E-CLI auf synthetischem Hive-Parquet-Baum (≥800 Tage
→ rc 0, 4 Zellen; ~100 Tage → rc 2 SKIP), sh-Runner E2E (SKIP-Zweig, SUMMARY-Datei).

Luecken:
1. **Die Positiv-/Null-/Tuning-Tests validieren die implementierte (degenerate) Metrik und
   zementieren damit Bug 1** — nach dem Fix muessen sie auf Ensemble-CRPS umgestellt werden.
2. Kein Test, dass `cell_pass` p ≤ 0,05 verlangt (haette Bug 3 gefangen).
3. capital_free-Scan prueft AST-Identifier, nicht den erzeugten JSON/Markdown-TEXT (manueller
   Grep in diesem Audit: sauber).
4. Kein PIT-Test (Feature fehlt, Bug 5). Kein ps1-Test (plattformbedingt; sh-Zwilling getestet).
5. Kein Unlock-Test gegen ein echtes/gefaktes `harvest_manifest.sqlite` (Bug 4).

---

## capital_free check result: **PASS**

Grep ueber Modul + CLI (`bps|pnl|sharpe|friction|edge_|slippage`, case-insensitiv): einziger
Treffer ist die narrative Docstring-Zeile `driver.py:24` ("25-75x friction-magnitude ...
no cost quantity ... is computed here") — keine Kostenrechnung, kein Payload-Feld. Der
JSON-Payload und der gerenderte Markdown enthalten keinerlei bps/pnl/sharpe/friction/edge_-
Groessen; `capital_free: true` steht in JEDEM Payload (auch SKIP; testabgesichert). Die
Runner-SUMMARY enthaelt den Programm-Standardsatz "KEINE bps/Edge/PnL/Sharpe/Friction-
Rechnung" (Negativ-Deklaration, identisch in run_h07/h08/h12 — Konvention, kein Verstoss).

---

## T2 runner check result: **PASS** (mit einer Budget-Notiz)

`run_h11.ps1` gegen alle bekannten Bug-Klassen geprueft:
- Skript-Pfad ist ERSTES CmdArg vor allen --flags (Z. 147-153, 168-181; run_h05c-Bug vermieden,
  explizit kommentiert). ✓
- `$null = $p.Handle` Handle-Cache (Z. 99) + ExitCode-null-Quirk-Fallback rc=−2 (Z. 107). ✓
- BelowNormal fuer Runner-Prozess (Z. 57) UND Kind-Prozess (Z. 100). ✓
- Encoding: reines ASCII (verifiziert mit `file`), PS-5.1-sicher; Summary via
  `[System.IO.File]::WriteAllText` (ASCII-Inhalt). ✓
- Kein `Read-Host`/`pause`, keine Pflicht-Parameter, `HANDOFF_DRY_RUN`-Pfad vorhanden. ✓
- Timeouts: 300 s Unlock-Check, 3600 s Voll-Lauf, `WaitForExit` + Kill, Timeout → rc 124 → FAIL. ✓
- `SUMMARY_<datum>.md` wird IMMER geschrieben (locked- und unlocked-Zweig), plus `steps.tsv`. ✓
- Exit deterministisch: fail>0→1, sonst skip>0→2, sonst 0. Unlock-Check-Fehler (≠0/2) fuehrt zu
  Exit 1 OHNE Datenlauf; Locked → SKIP-Kette → Exit 2. ✓
- Junction-Warnung, HARVEST_DIR/H11_RESULTS_DIR/PYTHON-Overrides wie Geschwister-Runner. ✓
- `run_h11.sh` ist ein treuer Zwilling (timeout-Kommando, gleiche Exit-Semantik) und ist per
  Unit-Test E2E im Locked-Zweig abgedeckt (SUMMARY-Inhalt "H11_ANEN | SKIP" verifiziert). ✓

Notiz: `TmoStep=3600` ist mit dem heutigen Tick-fetchall-Loader (Bug 2) auf realen Daten
sicher zu knapp — nach dem DuckDB-Aggregations-Fix realistisch.

---

## Unlock-Gate-Korrektheit (hoechste Prioritaet): **funktional korrekt & ehrlich, mit Proxy-Abweichung (Bug 4)**

- **Kein Stub:** `check_unlock` iteriert real ueber alle 730 Kalendertage × {publicTrade,
  rest.fundingRate} × {BTCUSDT, ETHUSDT} und verlangt fuer JEDEN Tag eine `date=`-Partition
  mit ≥1 Parquet; zusaetzlich Range-Span ≥ 730. Kein hartkodiertes True/False; Tests beweisen
  BEIDE Zweige inkl. Wieder-Sperrung durch ein einzelnes Tagesloch.
- **Verweigerung ist wasserdicht verdrahtet:** Reihenfolge Unlock-Check ZUERST (driver.run
  Z. 192-200: locked → `status="SKIP"`-Payload mit Diagnose-Tabelle, `results: []`, KEIN
  Datenzugriff, kein `cells`-/Gate-Material); CLI: `--check-unlock-only` rc 0/2, Voll-Lauf bei
  locked rc 2 mit ehrlicher GESPERRT-Meldung; Runner: Schritt 1 Unlock-Check, Voll-Lauf NUR
  nach OK, locked → SUMMARY "H-11 gesperrt — ... Entsperr-Bedingung nicht erfuellt", Exit 2.
  Der `skip_unlock_check`-Parameter ist von CLI/Runnern aus NICHT erreichbar (nirgends
  referenziert). Bei heutiger Datenlage (Backfill ~2026-03-20, Basis-Bestand ab 2026-03-27)
  meldet das System korrekt GESPERRT und produziert kein Verdikt.
- **Abweichung:** Der Scan ist ein Raw-Tree-Proxy der registrierten Manifest-done_days-Abfrage
  und akzeptiert 0-Byte-Parquets → kann waehrend des laufenden Deep-Backfills FRUEHER
  entsperren als das Manifest (Details Bug 4). Vor dem ersten echten Lauf auf die
  `harvest_manifest.sqlite`-Query umstellen (Muster liegt in `harvest_coverage.py` bereit).

---

## Fix-Reihenfolge vor einem entsperrten Lauf

1. Bug 1 (Ensemble-CRPS ueberall: Forecast, Tuning, Scoring, Tests) — ohne das ist jeder Lauf
   nicht adjudizierbar.
2. Bug 2 (1-min-RV in DuckDB aggregieren) — sonst OOM/Timeout auf realen Daten.
3. Bug 3 (`cell_pass` + p ≤ 0,05) — sonst fehlleitende Verdikt-Flags.
4. Bug 4 (Manifest-Query statt Ordner-Proxy) + Bug 5 (PIT-Report).
