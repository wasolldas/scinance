# H-15 Audit (DSM-01 — Trade-Tape-Event-Grammatik jenseits Markov)

**Auditor:** frischer, unabhängiger adversarialer Code-Auditor (kein Autor des Codes).
**Datum:** 2026-07-10. **Scope:** end-to-end, Code + Tests + T3-Runner + README, gegen
`state/hypothesis_registry.md` §H-15 und `state/GPU_RESEARCH_SCAN_2026-07-09.md` §2 (DSM-01).
**Harte Randbedingung:** kein Nutzer-Review für 2 Wochen — dieser Bericht ist das einzige
Qualitätsgate vor dem ersten GPU-Lauf.

---

## 1. Verdikt

**BEDINGT FREIGEGEBEN — mit einem HIGH-Fix vor dem ersten echten T3-GPU-Lauf empfohlen.**

Kernbefund: Die drei sicherheitskritischsten Achsen — **Compute-Gating**,
**Quantil-Bucket-Leak-Disziplin** und **Saisonalitäts-Null (Block-Shuffle)** — sind
korrekt implementiert und durch Code-Nachvollzug (nicht nur Tests) verifiziert. Kein Pfad
wurde gefunden, in dem ein CPU-only-Lauf `gate_valid: true` erzeugen könnte. Die Purged-
Walk-Forward-Konstruktion (4 Folds, 1-Tag-Embargo) ist arithmetisch korrekt und mit
Assertions defensiv abgesichert. Die Pflicht-Differenzierung zum gesperrten
Informationstheorie-Cluster steht wörtlich im Code UND im README (nicht nur behauptet).
`pytest` ist **echt grün** (35/35, selbst ausgeführt, siehe §4).

Es wurden jedoch **zwei echte Lücken in der `gate_valid`-Verteidigungslinie** gefunden
(Architektur-/Hyperparameter-Drift wird NICHT gegen die registrierten Defaults geprüft;
Symbol-Panel-Identität wird nur über die Anzahl, nicht über die Identität geprüft) sowie
**eine falsche Betriebsdokumentation** im Bash-Runner (`run_h15.sh` behauptet inkrementelle
Persistenz/keinen Datenverlust bei Abbruch — das Gegenteil ist der Fall: ein einziger
Timeout/Crash nach Stunden GPU-Zeit verliert ALLES, kein Checkpoint existiert). Keiner
dieser drei Befunde kann für sich allein einen CPU-Lauf als verdikt-tragend ausgeben oder
einen echten Leak verursachen — aber sie untergraben genau die Disziplin, die die Registry
für diesen Piloten explizit als "hartes Kriterium, kein Graubereich" fordert, und die
Persistenz-Lüge ist im Kontext eines 2-Wochen-unbeaufsichtigten-Betriebs ein echtes
Risiko fürs GPU-Zeitbudget des Nutzers. Empfehlung: Fix #1 (Architektur-Gate) und #3
(Persistenz-Doku/-Checkpointing) vor dem ersten Overnight-Lauf beheben; Fix #2
(Symbol-Panel-Identität) ist ebenfalls günstig zu beheben, aber nicht blockierend, da
beide Runner-Skripte das korrekte Panel hartkodiert übergeben.

---

## 2. Spec-Treue-Tabelle

| Registry-Anforderung (H-15, wörtlich/paraphrasiert) | Code-Fundstelle | Treue |
|---|---|---|
| Tokenisierung: Side(2) × Signed-Size-Quantil(8, NUR Train-Fold) × Log-IAT(8) = Vocab 128, optional ×Tick-Dir→256 | `tokenizer.py:39-48,138-167,170-203` | ✅ exakt |
| Quantil-Grenzen NUR auf Train-Fold gefittet | `driver.py:308-312` (`prepare_fold`), `tokenizer.py:138-167` | ✅ verifiziert im Code, s. §6 |
| Baseline: KT-geglättetes Var-Order-Markov k≤4 + interpoliert, GLEICHER Train-Fold | `markov_baseline.py:112-226` | ✅ exakt |
| Transformer: Decoder-only causal, ~2-4M Params, Kontext 1024 | `transformer.py:61-140` (~3.5M, im Band) | ✅ |
| Purged Walk-Forward: 4 Folds, ~100 Tage, 1-Tag-Embargo, 3 Seeds | `stats.py:111-163`, `driver.py:113-114` (Grid exakt 100 Tage) | ✅ verifiziert, s. §8 |
| Null: ≥200 Within-Hour-of-Day-Block-Shuffle, Blocklänge 256 | `stats.py:170-215` | ✅ mathematisch verifiziert, s. §9 |
| Gate: ≥2% rel. CE-Vorteil UND Lücke > Surrogat-p95, BH-FDR α=0,10, ≥4/5 Symbole, hartes One-Window-DROP | `driver.py:426-455, 636-652` | ✅ Logik korrekt |
| FDR: eigene BH-Kopie, F-GRAMMAR über 5 Symbole | `stats.py:59-84` | ⚠️ Kopie korrekt, aber **Familiengröße nicht gegen exakt-5/Panel-Identität erzwungen** (Bug #2) |
| KAPITALFREI, keine Kapital-Metrik | `driver.py:58,461`, Tests `TestCapitalFree` | ✅ verifiziert |
| Differenzierungsabsatz Pflicht im Runner-Output/README | `driver.py:123-133,714-716`, `README_H15.md:44-63` | ✅ wörtlich vorhanden, s. §11 |
| "kein nachträgliches Vocab-/Kontext-/Architektur-Nachjustieren" | `driver.py:384-401` (Deviation-Checks) | ❌ **Architektur-Parameter NICHT geprüft** (Bug #1) |
| GPU zwingend; ohne CUDA kein Verdikt | `driver.py:355-401`, `transformer.py:57-104` | ✅ verifiziert, s. §7 (wichtigster Check) |
| T3-Runner-Disziplin (CLAUDE.md Testpyramide) | `run_h15.ps1/.sh` | ⚠️ PS1/Handle/BelowNormal/ASCII/Timeout/SUMMARY/Exit-Code korrekt, aber `.sh`-Header behauptet fälschlich Inkrementalpersistenz (Bug #3) |

---

## 3. Gefundene Bugs

### Bug #1 — HIGH: Architektur-/Hyperparameter-Drift wird von `gate_valid` NICHT erkannt

**Datei:Zeile:** `src/bybit_edge/research/c15_grammar/driver.py:384-401` (Deviation-Check-Block),
zusammen mit `scripts/c15_grammar.py:116-123` (freie CLI-Flags `--context-len`, `--d-model`,
`--n-heads`, `--n-layers`, `--epochs`, `--batch-size`, `--lr`).

**Befund:** Der `run()`-Deviation-Check prüft `n_folds`, `embargo_days`, `len(seeds)`,
`n_surrogates`, `block_len`, `events_capped`, `use_tick_direction` gegen die registrierten
Defaults und voidet `gate_valid` bei Abweichung. Er prüft **NICHT** `cfg.context_len`,
`cfg.d_model`, `cfg.n_heads`, `cfg.n_layers`, `cfg.epochs`, `cfg.batch_size`, `cfg.lr`
gegen die in `GrammarTransformerConfig()` (bzw. Registry/README) fixierten Defaults
(1024/256/4/4/3/32/3e-4). Die CLI exponiert genau diese Parameter als frei setzbare Flags.
Ein Re-Lauf mit z. B. `--n-layers 8 --d-model 512` nach einem ersten DROP würde
`gate_valid: true` erzeugen (sofern CUDA vorhanden und sonst alles registrierts-konform
ist) — genau das vom Registry-Eintrag wörtlich verbotene "nachträgliche
Vocab-/Kontext-/Architektur-Nachjustieren" (Registry H-15, DROP-Klausel) wird technisch
NICHT verhindert, nur durch Doku-Absicht ("NICHT auf Testfenstern getuned") behauptet.
`model_config` wird zwar in den Payload geschrieben, aber `gate_valid` selbst — das
einzige maschinenlesbare Signal, das die Runner-SUMMARYs als "nur bei gate_valid=true ist
ein Urteil zulässig" zitieren — bleibt blind dafür.

**Schweregrad:** HIGH (untergräbt die einzige harte Anti-Gaming-Klausel des Piloten;
kein Leak, aber ein Pfad zu einem scheinbar "sauberen" Verdikt auf einer nicht
registrierten Architektur).

**Fix-Vorschlag:** Im selben Block wie die bestehenden Deviation-Checks (`driver.py:384-401`)
ergänzen:
```python
_default_cfg = GrammarTransformerConfig()
for field in ("context_len", "d_model", "n_heads", "n_layers", "epochs",
              "batch_size", "lr", "dropout", "grad_clip"):
    if getattr(cfg, field) != getattr(_default_cfg, field):
        gate_valid_reasons.append(
            f"{field}={getattr(cfg, field)} != registered default "
            f"{getattr(_default_cfg, field)}")
```

### Bug #2 — MEDIUM: `gate_valid` prüft nur die Symbol-ANZAHL, nicht die Symbol-IDENTITÄT

**Datei:Zeile:** `src/bybit_edge/research/c15_grammar/driver.py:443-446`
(`family_complete = len(per_symbol) >= FAMILY_SIZE`).

**Befund:** `FAMILY_SIZE = 5` wird nur als Untergrenze (`>=`) geprüft, nicht als exakte
Übereinstimmung mit `DEFAULT_SYMBOLS` (BTCUSDT/ETHUSDT/SOLUSDT/BNBUSDT/XRPUSDT). Ein Lauf
mit `--symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT` (falsches Panel, aber Länge 5)
oder mit 6+ Symbolen würde keinen `gate_valid_reasons`-Eintrag erzeugen — abweichend von
JEDEM anderen registrierten Parameter (Folds, Embargo, Seeds-Anzahl, Surrogate, Blocklänge,
Tick-Direction, Event-Cap), die alle explizit gegen den Registry-Default geprüft werden.
Nicht ausnutzbar über die mitgelieferten Runner (beide hartkodieren das korrekte Panel),
aber eine Lücke in der Verteidigungslinie, falls die CLI je manuell/anders aufgerufen wird.

**Schweregrad:** MEDIUM.

**Fix-Vorschlag:** Ergänzen im selben Block:
```python
if tuple(sorted(symbols)) != tuple(sorted(DEFAULT_SYMBOLS)):
    gate_valid_reasons.append(
        f"symbols {symbols} != registered 5-symbol panel {DEFAULT_SYMBOLS}")
```

### Bug #3 — HIGH: `run_h15.sh` behauptet fälschlich inkrementelle Persistenz / "kein Datenverlust"

**Datei:Zeile:** `scinance2-impl/handoff_local/run_h15.sh:26-27`:
```
# Seeds seriell). EIN Block: H15_GRAMMAR. Ergebnisse werden laufend im
# JSON persistiert (kein Datenverlust bei Abbruch mitten im Lauf).
```

**Befund:** Diese Behauptung ist **nachweislich falsch**. `driver.run()`
(`driver.py:331-524`) berechnet ALLE 5 Symbole × 4 Folds × 3 Seeds vollständig im Speicher
und gibt EIN Dict zurück; `scripts/c15_grammar.py:200-207` schreibt `c15_grammar_results.json`
/`.md` erst NACH erfolgreichem Rückkehr von `run()` — es gibt KEINEN Zwischen-Write, kein
Checkpointing, keinen Resume-Mechanismus. Ein Timeout (der PS1/SH-Runner setzt
`$TmoStep`/`TMO = 43200` s = 12 h als hartes Budget für den GESAMTEN Block) oder ein Crash
(OOM, Treiber-Hänger, Stromausfall) NACH z. B. 4 von 5 Symbolen und mehreren GPU-Stunden
verliert **restlos alles** — keine JSON, kein Teilergebnis, nichts Wiederverwendbares.
Der Vergleich mit den Geschwister-Runnern bestätigt, dass dies ein Kopier-/Doku-Fehler ist:
`run_h17.sh`/`README_H17.md` dokumentieren für ein strukturell identisches Problem
korrekt und ehrlich **"persistiert KEINEN Zwischenstand — erneuter Aufruf startet den
GESAMTEN Lauf neu"**; `run_h14.ps1`/`.sh` implementieren demgegenüber ECHTES
Fold-/Job-Checkpointing ("RESUME-FÄHIG ... jeder Aufruf setzt aus den Checkpoints fort").
H-15 hat die H-14-Rhetorik übernommen, aber die H-17-Architektur (keine Persistenz) — mit
der falschen Doku daraus resultierend. `run_h15.ps1` enthält diese falsche Behauptung
NICHT (nur der Bash-Runner).

Das widerspricht CLAUDE.md Testpyramide wörtlich: "T3 ... bricht NIE mit offenem Prompt
ab, loggt Fehler statt zu stoppen" / "Timeouts und try/except um jeden Teilschritt: ein
fehlgeschlagener Teiltest darf den Nacht-Lauf nicht beenden" — hier beendet ein einziger
Timeout/Crash NICHT nur einen "Teiltest" (ein Symbol), sondern den gesamten mehrstündigen
Lauf inklusive aller bereits fertigen Symbole.

**Schweregrad:** HIGH (kein Falsifikations-/Leak-Risiko, aber echtes GPU-Zeit-/
Betriebsrisiko für exakt das 2-Wochen-unbeaufsichtigt-Szenario dieses Auftrags; die
Doku ist zudem aktiv irreführend, nicht nur unvollständig).

**Fix-Vorschlag:** Minimal: Kommentarzeile in `run_h15.sh:26-27` korrigieren analog zu
`README_H17.md` ("persistiert KEINEN Zwischenstand — erneuter Aufruf startet neu").
Besser (empfohlen angesichts "Stunden"-Laufzeit auf einer 12 h-Budget-Karte): echtes
Checkpointing in `driver.run()`/`scripts/c15_grammar.py` einbauen — z. B. nach jedem
abgeschlossenen Symbol das bisherige Teilergebnis nach `<out-dir>/c15_grammar_partial.json`
schreiben (analog H-14-Musters), damit ein Timeout/Crash höchstens das gerade laufende
Symbol verliert statt aller bereits fertigen.

### Bug #4 — LOW: `benjamini_hochberg` (eigene BH-Kopie) hat keinen dedizierten Unit-Test

Siehe §4 Test-Abdeckung.

### Bug #5 — LOW (Doku-Ungenauigkeit, kein Funktionsbug): "identisch zu `m18_patchtst.py`"-Behauptung

**Datei:Zeile:** `transformer.py:14-18`.

**Befund:** Der Import-Guard (`try: import torch ... except: _TORCH_AVAILABLE = False`)
ist tatsächlich strukturell identisch zu `m18_patchtst.py:39-49`. Das NACHGELAGERTE
Fallback-Verhalten unterscheidet sich aber: `m18_patchtst.fit()` gibt bei fehlendem Torch
ein degradiertes, aber definiertes Ergebnis zurück (`{"train_mse": inf, "epochs": 0}`,
No-Op), während `c15_grammar.transformer._require_torch()` eine `ComputeUnavailableError`
wirft. Das ist für ein verdikt-tragendes Gate sogar die strengere/bessere Wahl (fail-loud
statt fabrizierter Zahlen) — aber die Docstring-Formulierung "identical to
m18_patchtst.py pattern" überzeichnet die Parität. Kein Fix nötig außer Wortwahl.

### Geprüft, KEIN Bug: PowerShell `$Script` vs. `$Script:Results`

`run_h15.ps1` verwendet sowohl eine lokale Variable `$Script` (Pfad zu `c15_grammar.py`,
Zeile 126) als auch die scope-qualifizierte Variable `$Script:Results` (Zeilen 69, 74,
172-174, 195). Das sieht wie eine Namenskollision aus (bekannte T3-Bug-Klasse), ist aber
KEINE: `$Script:Results` wird von PowerShell als scope-qualifizierter Zugriff auf
`Results` im "script"-Scope geparst, nicht als `$Script` gefolgt von `:Results` — beide
Konstrukte koexistieren korrekt. Verifiziert durch Nachvollzug der PowerShell-Scoping-
Regeln; keine Änderung erforderlich (Umbenennung wäre nur ein Lesbarkeits-Nice-to-have).

---

## 4. Test-Abdeckung

**pytest wurde selbst ausgeführt** (nicht nur behauptet):

```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_c15_grammar.py -q
...................................                                      [100%]
35 passed in 22.43s
```

**Echt grün — 35/35, keine Skips, keine Warnings unterdrückt.**

Abgedeckt (6 Testklassen, siehe `tests/unit/test_c15_grammar.py`):
- `TestTokenizer` (5): Feature-Ableitung, Vocab-Grenzen, Roundtrip, Tick-Dir-Erweiterung,
  **Leak-Test** (kritischster Test — perturbiert Test-Fold-Daten massiv, verifiziert dass
  sich Tokenizer-Grenzen NICHT bewegen).
- `TestWalkForwardFolds` (6): 4-Fold-Konstruktion, kein Overlap, Embargo-Lücke exakt 1 Tag,
  expandierendes Trainingsfenster, disjunkte Test-Segmente, Fehlerfälle (zu kurzes Grid,
  unsortierte Tage).
- `TestMarkovBaseline` (6): Order-1-KT rekonstruiert wahre Entropierate eines bekannten
  Markov-Prozesses (±0,02 nats), Order-0 signifikant schlechter, interpolierte Baseline
  nahe fixer Ordnung, `best_baseline_ce` wählt korrekt das Minimum, KT-Degradation zu
  uniform bei ungesehenem Kontext, Ablehnung Out-of-Vocab.
- `TestBlockShuffleNull` (5): Marginalverteilung pro Stunde EXAKT erhalten, Langreichweiten-
  Struktur zerstört (Korrelationstest), Lokalstruktur innerhalb Block überwiegend erhalten,
  degenerierte Gruppe = Identität, Fehlerfälle.
- `TestComputeGate` (4): `torch_cuda_status()`-Ehrlichkeit, CLI `--check-gpu-only`,
  **`full`-Modus verweigert ohne CUDA** (`ComputeUnavailableError`), **`mechanics`-Modus
  ist NIE verdikt-tragend** (`gate_valid=False`, `ran_on_gpu=False`).
- `TestCapitalFree` (4) + `TestRegisteredConstants` (5): Forbidden-Token-Scan in JSON+MD,
  Differenzierungsabsatz-Präsenz, alle registrierten Konstanten (Vocab 128, MaxOrder 4,
  4 Folds/1-Tag-Embargo/3 Seeds, 200 Surrogate/Blocklänge 256, Gate-Schwellen 2%/95./4-5/
  0,10/F-GRAMMAR).

**Lücken (siehe Bug #4):**
- Kein dedizierter Test für `stats.benjamini_hochberg` (die vom Auftrag explizit verlangte
  "eigene BH-Kopie") — nur indirekt über einen 2-Symbol-Mechanics-Smoke-Run berührt, bei
  dem die p-Werte im Mechanics-Modus (kein Torch, `transformer_arm=False`) mutmaßlich
  NaN→1.0 sind und damit die eigentliche Rang-/Rejection-Logik gar nicht exerciert wird.
  Empfehlung: direkter Test mit bekannten p-Wert-Vektoren und erwarteten Rejection-Sets
  (inkl. m=5-Fall wie in F-GRAMMAR, Ties, alle-p=1, alle-p=0).
- Kein Test, der `run()` im `mode="full"` end-to-end mit echtem CUDA exerciert (erwartbar
  — diese Sandbox hat weder Torch noch GPU; korrekt als T3-only deklariert).
- Kein Test für die in Bug #1/#2 identifizierten `gate_valid`-Lücken (Architektur-Drift,
  Symbol-Panel-Identität) — konsistent damit, dass diese Prüfungen im Code schlicht fehlen.

---

## 5. capital_free-Check

**Sauber.** `payload["capital_free"]` ist in `driver.py:461` hartkodiert `True` (nicht
situativ/bedingt gesetzt — korrekt, da H-15 per Registry-Definition kapitalfrei ist, nicht
nur "meistens"). Verifiziert per Test (`TestCapitalFree.test_capital_free_flag_true`) UND
per Forbidden-Token-Scan über den vollständigen JSON-Payload UND das gerenderte Markdown
(`FORBIDDEN_TOKENS = ("bps", "edge_", "friction", "pnl", "sharpe", "tradab", " roi ")`,
Zeile 78 der Testdatei). Zusätzlich manuell gegen die Runner-Skripte und README geprüft:
keine der verbotenen Kapital-Token in `run_h15.ps1`, `run_h15.sh` oder `README_H15.md`
gefunden (README erwähnt `capital_free`-Token-Scan nur als Beschreibung des Tests selbst).

---

## 6. Quantil-Bucket-Leak-Check

**Kein Leak — im Code nachvollzogen, nicht nur im Testkommentar behauptet.**

Nachvollzogener Datenfluss: `driver.prepare_fold()` (`driver.py:282-324`) berechnet
`train_mask`/`test_mask` rein aus `fold.train_days`/`fold.test_days` (disjunkte
Tagesmengen aus der Purged-Walk-Forward-Konstruktion), ruft dann
`fit_tokenizer(feats["signed_size"][train_mask], feats["log_iat"][train_mask], ...)`
(Zeile 308-312) auf — **ausschließlich** mit train-maskierten Arrays. `tokenizer.py`s
`fit_tokenizer()` (Zeile 138-167) nimmt genau diese zwei Arrays entgegen, berechnet
Quantile (`np.quantile(ssz, qs)`) NUR aus ihnen und gibt ein `frozen`-Dataclass
`TokenizerSpec` zurück (`@dataclass(frozen=True)`, Zeile 55). `tokenize()` (Zeile
170-203) nimmt diesen bereits gefitteten, unveränderlichen `spec` entgegen und
berechnet NIRGENDS neue Quantile — es gibt in der gesamten Tokenizer-API keinen
Codepfad, über den Test-Fold-Daten in `fit_tokenizer()`/die Bucket-Grenzen einfließen
könnten (kein globaler State, keine Re-Fit-Methode, `frozen=True` verhindert nachträgliche
Mutation).

Der `test_leak_test_boundaries_fitted_train_fold_only`-Test (`test_c15_grammar.py:145-187`)
verifiziert das zusätzlich empirisch: identische Train-Events, aber Test-Fold-Events mit
1e6×-Ausreißer-Werten ersetzt → Tokenizer-Grenzen (`spec_a.size_edges == spec_b.size_edges`)
und Train-Tokens bleiben bitidentisch. Test bestanden (Teil der 35 grünen Tests).

---

## 7. Compute-Gating-Korrektheit (WICHTIGSTER CHECK)

**Korrekt in jedem nachvollzogenen Codepfad.** Detaillierte Pfadanalyse:

| Pfad | `mode` | CUDA | `device` | `ran_on_gpu` | `gate_valid` möglich? |
|---|---|---|---|---|---|
| A | `full` | nein | — | — | **Nein** — `ComputeUnavailableError` VOR jedem Fold/Symbol (`driver.py:367-372`), kein Payload wird erzeugt |
| B | `full` | ja, alle Registry-Defaults | `cuda` | `True` | Ja, wenn zusätzlich `family_complete` + alle CE/p definiert (korrekt) |
| C | `mechanics` | ja (torch+CUDA de facto vorhanden) | **`cpu`** (Zeile 377, hartkodiert, ignoriert tatsächliche GPU-Verfügbarkeit) | `False` | **Nein, IMMER** — `gate_valid = mode=="full" and ...` (Zeile 455) ist strukturell `False` für `mode="mechanics"`, unabhängig vom Rest |
| D | `mechanics` | nein | `cpu` | `False` | **Nein**, zusätzlich `transformer_arm=False` → CE bleibt NaN, würde selbst bei `mode="full"`-artiger Prüfung an den CE/p-Definiertheits-Checks scheitern |

Wichtige Detailbefunde, die die Robustheit stützen:
- `mode="full"` REFUSED to start ohne CUDA (`ComputeUnavailableError`, Zeile 362-372) —
  kein stiller CPU-Fallback, kein Teil-Payload wird geschrieben (CLI fängt die Exception ab
  und gibt `rc=1` zurück, `scripts/c15_grammar.py:193-195`).
- `mode="mechanics"` erzwingt `device="cpu"` UNBEDINGT (Zeile 377), auch falls eine
  CUDA-Karte technisch verfügbar wäre — verhindert Verwechslung zwischen einem
  absichtlichen Mechanik-Testlauf und einem echten GPU-Lauf.
- `gate_valid` wird als Konjunktion `mode=="full" AND ran_on_gpu AND not gate_valid_reasons`
  berechnet (Zeile 455) — die `mode=="full"`-Bedingung allein macht `mechanics` bereits
  strukturell unmöglich als verdikt-tragend, redundant abgesichert durch `ran_on_gpu`.
  Doppelte Absicherung, kein Single-Point-of-Failure.
- Der T3-Runner (`run_h15.ps1`/`.sh`) führt VOR dem Hauptlauf `--check-gpu-only` aus (reine
  Statusabfrage, immer `rc=0`, KEIN Lauf) und bricht bei `mode=full` ohne CUDA sauber mit
  `SKIP (exit 2)` ab, OHNE automatischen `mechanics`-Fallback (nur via explizitem
  `$env:MODE='mechanics'`-Override) — verifiziert in beiden Runnern (Zeile 154-157 PS1,
  104-107 SH).
- `--use-tick-direction` und `--max-events-per-day` (Debug-Komfort) voiden `gate_valid`
  explizit (Zeile 396-400) — verhindert, dass ein Debug-/Mechanik-Komfort-Flag
  versehentlich in einem verdikt-tragenden Lauf landet.

**Die einzige gefundene Lücke in dieser Achse ist NICHT das CPU/GPU-Flag selbst, sondern
die in Bug #1/#2 beschriebene fehlende Absicherung GEGEN Architektur- bzw.
Symbol-Panel-Drift innerhalb eines ansonsten korrekt auf CUDA laufenden `mode="full"`-Laufs.**
Ein CPU-Lauf kann also NIE fälschlich `gate_valid: true` tragen (das zentrale Risiko der
Aufgabenstellung) — aber ein GPU-Lauf mit stillschweigend geänderter Architektur oder
Symbol-Liste könnte es, was denselben Geist der Norm verletzt.

---

## 8. Purged Walk-Forward + 1-Tag-Embargo

**Korrekt, arithmetisch verifiziert.** Datengrid `DEFAULT_DATA_START="2026-03-27"` bis
`DEFAULT_DATA_END="2026-07-04"` (`driver.py:113-114`) = exakt 100 Kalendertage (nachgerechnet:
5+30+31+30+4 Tage über März–Juli). `walk_forward_folds()` (`stats.py:111-163`) teilt das
Grid in `n_folds+1=5` (nahezu) gleich große Segmente (`bounds = [round(i*n/n_seg) ...]`,
für n=100 → [0,20,40,60,80,100]); Fold i: Train = Segmente 0..i (expandierend), Embargo =
erster Tag von Segment i+1, Test = Rest von Segment i+1. Für Fold 0: Train=20 Tage,
Embargo=1 Tag, Test=19 Tage — plausibel und mit den registrierten "4 Folds über ~100 Tage,
1-Tag-Embargo" konsistent.

Defense-in-depth-Assertions in derselben Funktion (Zeile 149-160) erzwingen zur Laufzeit
zusätzlich zur reinen Konstruktion: `first_test <= last_train` → `FoldError`; Kalenderlücke
`< embargo_days+1` → `FoldError`; `set(train) & set(test)` nicht leer → `FoldError`. Das
bedeutet: selbst falls die Segmentierungs-Arithmetik durch eine künftige Änderung fehlerhaft
würde, würde der Lauf hart abbrechen statt ein leakendes Fold-Layout stillschweigend zu
verwenden.

Test-Abdeckung bestätigt dies empirisch für alle 4 Folds über ein 100-Tage-Grid (kein
Overlap zwischen Train/Test/Embargo, Embargo exakt 1 Tag, Kalenderkontinuität
Train→Embargo→Test, expandierendes Fenster, disjunkte Test-Segmente über alle Folds
hinweg) — Tests bestanden.

---

## 9. Saisonalitätserhaltende Block-Shuffle-Null (Blocklänge 256)

**Mathematisch korrekt implementiert**, nicht nur dem Namen nach getestet.

`hour_block_shuffle()` (`stats.py:170-215`): für jede Stunde-des-Tages `h∈0..23` werden
ALLE Events mit `hours==h` (über den gesamten Stream, ggf. über mehrere Kalendertage
hinweg, in Stream-Reihenfolge) extrahiert, in aufeinanderfolgende Blöcke der Länge 256
zerlegt (letzter Block ggf. kürzer), die BLOCKREIHENFOLGE wird permutiert
(`rng.permutation(n_blocks)`), und die Konkatenation wird an genau denselben Positionen
zurückgeschrieben, an denen die Original-Events standen.

Warum das die Stunden-Marginalverteilung EXAKT erhält: die Operation ist für jede
Stunden-Gruppe eine reine Permutation der Werte INNERHALB dieser Gruppe (Blockreihenfolge
vertauscht, aber jeder einzelne Token-Wert bleibt genau einmal in der Menge erhalten) —
`np.sort(tokens[idx]) == np.sort(surr[idx])` ist für jede Stunde `h` garantiert, weil
`out[idx] = np.concatenate(pieces)` eine Bijektion auf derselben Indexmenge `idx` ist.
Gleichzeitig wird Sequenzstruktur JENSEITS von 256 Events zerstört (Reihenfolge der Blöcke
zufällig), während Struktur INNERHALB eines Blocks (< 256 Events) erhalten bleibt — exakt
das registrierte Null-Design ("erhält Stunden-Marginalverteilung, zerstört
Sequenzstruktur").

Testabdeckung verifiziert genau diese drei Eigenschaften separat und nicht-trivial:
(a) `test_marginal_preserved_per_hour` — Marginalverteilung exakt erhalten (uniform-random
Fixture); (b) `test_sequence_structure_destroyed_beyond_block_len` — bei einer strikt
monoton steigenden Positions-Sequenz (perfekte Langreichweiten-Korrelation) fällt die
Korrelation nach Shuffle auf < 0,9 (echter, nicht-trivialer Zerstörungstest, nicht nur
"ist nicht mehr identisch"); (c) `test_local_structure_within_block_preserved` — "+1"-
Adjazenz-Kontinuität bleibt bis auf die (wenigen) Blockgrenzen erhalten; (d) degenerierter
Fall (Gruppe ≤ Blocklänge) = exakte Identität. Alle vier Tests bestanden.

Einzige Beobachtung (kein Bug): "innerhalb einer Stunde" bezieht sich auf ALLE Vorkommen
dieser Uhrzeit über den gesamten ~100-Tage-Stream hinweg (nicht pro Kalendertag separat) —
ein Block kann daher Events aus mehreren, nicht notwendig benachbarten Tagen mischen, sofern
sie hintereinander in der nach Stunde gefilterten Sequenz liegen. Das ist konsistent mit der
Registry-Formulierung ("Within-Hour-of-Day-Block-Shuffle") und dem erklärten Ziel
(Kurzreichweiten-Struktur erhalten, Langreichweiten-/Tages-Struktur zerstören) — keine
Fehlinterpretation, sondern die naheliegende und korrekt umgesetzte Lesart.

---

## 10. T3-Runner-Check (`run_h15.ps1` / `run_h15.sh`)

| Bekannte Bug-Klasse | `run_h15.ps1` | `run_h15.sh` |
|---|---|---|
| Skriptpfad als erstes CmdArg | ✅ `$Script` als Element 0 von `@($Script, ...)`, korrekt an `Start-Process -ArgumentList` übergeben (Zeile 159-167) | ✅ `"$SCRIPT" ... ` als erstes Positionsargument an `$PY` (Zeile 109-115) |
| Handle-Cache-Bug | ✅ `$null = $p.Handle` (Zeile 97) vor `WaitForExit` — klassischer PS-5.1-Workaround vorhanden | n/a (Bash) |
| BelowNormal-Priorität | ✅ Hauptprozess (Zeile 56) UND Kindprozess (Zeile 98) | n/a (keine PowerShell-Priorität in Bash-Äquivalent nötig) |
| ASCII-Body | ✅ verifiziert: 0 Nicht-ASCII-Zeichen im gesamten Skript (`grep -cP '[^\x00-\x7F]'` → 0) | ✅ (Bash, kein ASCII-Zwang, aber ebenfalls sauber) |
| Timeout | ✅ `WaitForExit($TimeoutSec*1000)`, bei Überschreitung `Kill()` + `rc=124` (Zeile 99-102), Budget `$TmoStep=43200` (12h) | ✅ `timeout "$TMO" ...` mit Fallback ohne `timeout`-Binary (Zeile 70-72), `TMO=43200` |
| SUMMARY-Datei | ✅ `SUMMARY_<datum>.md` mit Schritt-Tabelle, Gate-Text, A-priori-Hinweis (Zeile 178-207) | ✅ äquivalent (Zeile 120-147) |
| Exit-Code-Konvention 0/1/2 | ✅ `exit=0` außer `fail>0→1`, sonst `skip>0→2` (Zeile 175-176) | ✅ identisch (Zeile 119) |
| Sauberer SKIP statt CPU-Fallback bei fehlendem CUDA | ✅ `mode=full` + kein CUDA → SKIP (exit 2), kein automatischer `mechanics`-Fallback (Zeile 154-157) | ✅ identisch (Zeile 104-107) |
| Inkrementelle Persistenz / kein Datenverlust | n/a (keine solche Behauptung im PS1) | ❌ **Bug #3 — Behauptung falsch, kein Checkpointing existiert** |

Fazit T3-Runner: strukturell solide und mit den bekannten Bug-Klassen bereits
"geimpft" — bis auf die in Bug #3 dokumentierte, spezifisch im Bash-Runner vorhandene
Fehlbehauptung zur Persistenz.

---

## 11. Differenzierungs-Absatz-Präsenz

**Wörtlich vorhanden, nicht nur behauptet — an drei unabhängigen Stellen geprüft:**

1. **Registry** (`hypothesis_registry.md:370`): "Differenzierung zu den gesperrten
   Informationstheorie-Clustern (PE/TE, H-06/H-04) ist konzeptionell sauber (Event-Stream
   statt Renditen, CE als Scoring-Rule statt Entropie-Schaetzer, kein rho/Trading-Gate)
   — MUSS im Runner-Output/README woertlich dokumentiert werden".
2. **Code** (`driver.py:123-133`, Konstante `DIFFERENTIATION_NOTE`): enthält wörtlich alle
   drei Punkte (EVENT-STREAM statt Renditen; CROSS-ENTROPY als SCORING-RULE statt
   Entropie-Schätzer; KEIN ρ-/Trading-Gate) UND wird in JEDEN JSON-Payload
   (`payload["differentiation_note"]`, Zeile 522) sowie in den gerenderten Markdown-Report
   (`render_markdown()`, Zeile 714-716, eigene Überschrift "## Differenzierung zum
   gesperrten Informationstheorie-Cluster (Pflicht)") geschrieben.
3. **README** (`README_H15.md:42-63`): eigener Abschnitt "## Differenzierung zum gesperrten
   Informationstheorie-Cluster (Pflicht)", zitiert die Registry wörtlich als Blockquote UND
   führt die drei Punkte ausformuliert auf.

Zusätzlich testgesichert: `test_differentiation_note_present_and_verbatim_markers`
(`test_c15_grammar.py:531-538`) prüft programmatisch, dass "Event-Stream", "Scoring-Rule"
und "H-15b" im Payload UND "Differenzierung" im gerenderten Markdown vorkommen. **Kein
Blender-Befund — der Absatz ist tatsächlich, wörtlich, an allen drei geforderten Stellen
vorhanden.**

---

## Zusammenfassung der Handlungsempfehlung (vor erstem T3-Lauf)

1. **Vor dem ersten Lauf beheben (empfohlen, nicht blockierend, da Runner-Defaults
   korrekt sind):** Bug #3 (falsche Persistenz-Behauptung in `run_h15.sh:26-27`) —
   mindestens die Doku korrigieren, idealerweise echtes Per-Symbol-Checkpointing analog
   H-14 ergänzen, da ein Stunden-Lauf auf einer 12h-Budget-Karte ohne Checkpoint ein
   reales Risiko für das GPU-Zeitbudget des Nutzers ist.
2. **Vor dem ersten Lauf beheben (empfohlen):** Bug #1 (Architektur-Drift-Gate) —
   kleine, risikoarme Ergänzung im bestehenden Deviation-Check-Muster.
3. **Kann parallel/danach behoben werden:** Bug #2 (Symbol-Panel-Identität), Bug #4
   (BH-FDR-Unit-Test), Bug #5 (Docstring-Präzisierung).
4. Alle anderen elf geprüften Achsen (Compute-Gating, Quantil-Leak, Purged-WF+Embargo,
   Block-Shuffle-Null, capital_free, Differenzierungsabsatz, T3-Runner-Bugklassen
   PS1/SH, Kausalität Markov+Transformer nur auf Train-Fold, FDR-Eigenkopie,
   Torch-Optional-Muster, Testgrün) sind **ohne Beanstandung**.
