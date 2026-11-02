# Builder-Auftrag DEC-101 (H-32): Universumsfilter, skalierte Null, technische Pilot-Sperre, Pins, q95-Regel, Power-Ausweis, PP3-Trockenprobe

Repo Scinance, Paket `bybit_edge` unter `src/`. Du arbeitest in einem eigenen git-worktree (der Orchestrator legt ihn an;
pruefe mit `git worktree list` und `pwd`). Tests IMMER mit `PYTHONPATH=$(pwd)/src python -m pytest ...` aus der
Worktree-Wurzel (einmal pruefen: `PYTHONPATH=$(pwd)/src python -c "import bybit_edge;print(bybit_edge.__file__)"` zeigt
in den Worktree).

## Verbindliche Texte (in dieser Reihenfolge; bei Widerspruch gilt die frueher genannte Quelle)
1. `scinance3-impl/state/decisions.md`: **DEC-101 Teil 1** (Entscheidungen 1-6, woertlich umzusetzen), DEC-99 (+N1), DEC-94,
   DEC-96 E3, DEC-100 (+N1).
2. `scinance3-impl/state/herleitung_h32/REVIEW_REGISTRIERUNG_H32.md` Befunde B-1..B-9 und Auflagen V-1, A-1..A-5 (Details).
3. `scinance3-impl/state/herleitung_h32/ERSTFASSUNG_H32_entwurf.md` Abschnitte 1, 2, 4, 5, 11 (unveraendert bindend, soweit
   DEC-101 nichts anderes sagt) und `REGISTRIERUNG_H32_entwurf.md` (Zielbild der YAML/Registry).
4. Bestehender Code: `src/bybit_edge/research/h32_fm8/` (constants, panel_cut, vorlauf, pnull, gate, testrun, pilot,
   checks, schema, estimators, artifacts, handover, fweek, positive_control, delisted_tree), `scripts/h32_fm8.py`, Tests
   `tests/unit/test_h32_*.py`, `tests/unit/h32_fixtures.py`.

## Harte Regeln
- Nicht committen, nicht pushen. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder
  `ic_series_*_UNION_REAL.csv` heissen. Nie unter `data/harvest` schreiben. KEIN Modus auf Realdaten (kein
  `--prelaunch/--pilot/--run/--positive-control/--pp3-dry-run` auf dem Scratchpad-Panel) - nur Fixture-Panels.
- Additiv: `wp13_xsec/`, `wp7_universe/`, `wp12_delisting/` NICHT aendern. Code/Kommentare Englisch, Docstrings mit
  "DEC-101". Keine Modellnamen. Bestehende Tests nie loeschen; wo DEC-101 das Verhalten aendert, Tests anpassen und
  den Grund im Docstring nennen. Jede Zahl, die der Lauf gegen die YAML prueft, ist eingefroren (T5-Pin).

## Bau (je Punkt mit Tests)
B-1 **Universumsfilter (DEC-101 E1).** Neues Modul `universe.py`: `is_linear_usdt_perpetual(symbol) -> bool` (endet auf
    `USDT`, enthaelt kein `-`), `classify_excluded(symbol) -> "usdc_perp" | "dated_future" | "other"` (`*PERP` ->
    usdc_perp; `-` im Namen -> dated_future), `apply_universe(panel) -> (panel, report)`: entfernt alle Nicht-Universum-
    Spalten aus dem Union-Panel-Dict (dieselben Schluessel wie `panel_cut.cut_panel_days` behandelt: symbols, close,
    turnover, funding_n, funding_sum, delisted_symbols, is_delisted, last_alive_day, n_symbols_survivors/delisted ...),
    report = {rule: "linear_usdt_perpetual", n_before, n_after, excluded: {usdc_perp: n, dated_future: n, other: n},
    excluded_symbols: sortierte Liste, excluded_sha256}. Anwendung in `scripts/h32_fm8.py` in `load_union_panel` NACH der
    Fingerprint-Messung (Fingerprints bleiben dateibasiert) und VOR jedem Schnitt/jeder Rechnung, in ALLEN Modi; Log-Zeile
    mit den Zahlen. Artefakte (Vorlauf, Pilot, Lauf, Positivkontrolle) tragen den Report unter `universe`; Vorlage/YAML
    bekommt den Block `universe: {rule: linear_usdt_perpetual, label: "Bereinigung (Strenge), beschlossen nach Kenntnis
    der v6-Nuisance, vor jeder Pilot-Zahl (DEC-101 E1)", excluded_at_prelaunch: {usdc_perp, dated_future, other}}`;
    Pilot/Test/Positivkontrolle pruefen den Pin `universe.rule` (Schema: Pflichtfeld). Tests: Klassifikation; Fixture mit
    einem USDC-Zwilling (`AAAPERP` neben `AAAUSDT`) und einem datierten Future (`AAAUSDT-25DEC26`) -> beide entfernt, K
    sinkt entsprechend, Report stimmt; Pin-Test (YAML ohne/mit falscher Regel -> loud fail).
B-2 **Skalierte Null im Testlauf (DEC-101 E2, Review A-1).** In `testrun.run_test` je Fenster W und Variante v:
    `sd_real = SD(IC_t,W, ddof 1)` der realen fm8-Wochenserie, `k = max(1, sd_real / sd_week_W,v)` (sd_week eingefroren),
    `m` = eingefrorenes Null-Mittel der bindenden Zelle (`pnull` cell), `q95_eff = max(0, m) + k * (q95_frozen - m)`;
    Gate-Bedingung (1c) nutzt `q95_eff`; bindendes p aus den transformierten Replikaten `d' = max(0, m) + k * (d - m)`
    (`pnull.replicate_pvalue(y, d')`); Payload (T4) traegt k, sd_real, sd_week, m, q95_frozen, q95_eff, p; Markdown/JSON
    weisen beides (eingefroren und effektiv) aus. YAML-Block `null_scaling: {enabled: true, rule: "k = max(1,
    SD(IC_t,W)/sd_week_W,v); q95_eff = max(0,m) + k*(q95 - m); p from max(0,m) + k*(d - m)", direction: strictness,
    ref: DEC-101 E2}` (Schema: Pflicht, enabled muss true sein). Tests: k = 1 reproduziert das alte Verhalten fuer m >= 0;
    m < 0 -> q95_eff >= q95 (keine negative Gutschrift); aufgeblasene reale SD -> hoeheres q95_eff und groesseres p;
    T4-Arithmetik auf dem Payload; F-WEEK nutzt das skalierte p.
B-3 **Genau-ein-Pilot technisch (DEC-101 E3, A-2).** YAML `pilot_window.out_dir` (repo-relativ, Vorlage setzt
    `scinance3-impl/state/runs/h32_pilot_v1`); `--pilot` verweigert jedes andere `--out` (Vergleich ueber aufgeloeste
    Pfade relativ zur Repo-Wurzel); zusaetzlich sucht `checks.check_rerun_lock` (oder eine neue Funktion) VOR dem Panel
    rekursiv unter `scinance3-impl/state/runs/` nach `h32_pilot*.json`, deren `registered_sha256` (bzw. das passende
    Feld des Pilot-JSON) gleich der uebergebenen sha ist -> Abbruch ohne `--pilot-rerun-dec`. Tests: neues Verzeichnis
    mit vorhandenem Pilot-JSON anderswo -> Abbruch; abweichendes --out -> Abbruch; mit DEC-Verweis erlaubt (Prefix wie bisher).
B-4 **Pins (DEC-101 E4, A-3, B-9.6).** Vorlage/YAML: `data_fingerprints.delisted_tree_sha256` und
    `delisting_register_sha256` aus dem Artefakt (Schema: Pflicht, hex64); `runner: {as_of, start_year, end_year,
    allow_partial}` aus den CLI-Argumenten des Vorlaufs; alle Modi pruefen vor dem Laden des Panels, dass ihre CLI-
    Argumente den `runner`-Pins entsprechen (loud fail mit beiden Werten). Tests.
B-5 **q95-Regel und Power-Ausweis (DEC-101 E5, A-4, B-6).** Im Vorlauf: eingefrorenes `q95` je Fenster/Variante =
    max(q95 der 1.000 Konstanten-Replikate wie bisher (extremere Zelle), empirisches 95-%-Quantil (numpy, Standard-
    Interpolation, dokumentieren) aller 10.000 p-Replikate der bindenden Zelle); beide Werte im Artefakt/Markdown
    (`q95_1000`, `q95_10000`, `q95`). Power-Zeile im Vorlauf-Artefakt (`power_line`, report-only): je Fenster/Variante
    MDE80_1b = z_krit*e_se_rule + z_80*se_mean + max(0, null_mean), MDE80_1c = q95 + z_80*se_mean, MDE80_W = max;
    MDE80* = max_W; m* (Regel U); Uebergabeschwelle auf x_P = MDE80*_U + m* (U-Formel unveraendert: max_W(z_krit*SE_T +
    z_80*SD_T)); Nachweis-Zeile "Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c (>= 0 ja/nein)"; Endpower nach
    F-WEEK fuer m = 1, 2, 3, 4, 11 am Punkt pi = Uebergabeschwelle: je Fenster P(Y >= max(z_eff*SE_T + max(0, m_W),
    q_{1-bound}(Replikate der bindenden Zelle))), Y ~ N(pi, SD_T^2), bound = alpha_BY/(m*H_m), z_eff = max(z_krit,
    Phi^-1(1-bound)); Produkt ueber W1/W2; `power_p1.Z_POWER` (kein gerundetes 0,8416). Neue Funktion
    `estimators.end_power_replicates(...)`; die alte `end_power` bleibt (report-only, Etikett "Normalnaeherung"). Tests
    gegen Monte Carlo (Toleranz) und gegen Handrechnung.
B-6 **PP3-Trockenprobe und Kennzeichnungen (DEC-101 E6, A-5, B-9.5).** Neuer Modus `--pp3-dry-run --registered Y
    --registered-sha256 H` (+ Panel-Argumente): Startsperre, Runner-Pins, Fingerprints, Universumsfilter, Panel-Schnitt auf
    `seal.panel_cut_pilot`, Wochenarrays, Fenster P: K_fm8-Reihe berechnen und ihren sha256 gegen
    `pilot_window.frozen_v6.k_fm8_series_sha256` pruefen, Fenster-Pins (`checks.check_window_pins`); zusaetzlich mit Schnitt
    `seal.panel_cut_test` die K-Reihen von W1/W2 gegen die Pins. KEINE IC-Berechnung (Waechter: der Modus importiert
    keine IC-Funktion; Test prueft, dass `ic.weekly_ic_series`/`apply_beta_control` nicht aufgerufen werden, z. B. per
    monkeypatch, der bei Aufruf raised). Ausgabe nur Log + kleines JSON (`h32_pp3_dry_run.json`, Hashes und ok-Flags), rc 0/1.
    `estimators.mu_sel`: an der Klammergrenze (|mu - (x_P - 40 SE_P)| klein) `None` zurueckgeben bzw. `solved: false`,
    Pilot-Markdown "keine Loesung (Platzhalter, report-only)". YAML-Kopf (Vorlage): "W1-Determinismus-Kontrolle gegen v5e:
    entfaellt (DEC-100 N1); Ersatz: Fixture-T2, Zweitlauf bitgleich, PP3-Trockenprobe".
B-7 **Tests gesamt:** alle `tests/unit/test_h32*.py` + `test_power_p1.py` gruen; CLI-E2E auf dem Fixture-Panel
    (prelaunch -> template -> pp3-dry-run -> pilot (gepinntes out_dir) -> positive-control -> run) mit den neuen Bloecken.
    Danach `tests/unit` gesamt (die 3 bekannten `test_execution_live.py`-Altfaelle nur melden).

## Rueckmeldung (hoechstens 12 Zeilen)
Dateien, Testzahlen, genaue CLI je neuem/geaendertem Modus, Abweichungen von DEC-101/Review mit Grund (strengere Lesart
bauen und melden), absoluter Worktree-Pfad.
