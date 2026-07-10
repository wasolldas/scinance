# Audit H-14 · PANEL-LAG (Conditional Cross-Venue-Lead-Lag-Graph via Node-Ablation-Cross-Attention)

**Auditor:** unabhängiger, frischer Code-Auditor (hat den Code NICHT geschrieben).
**Datum:** 2026-07-10. **Kontext:** einziges Qualitätsgate vor dem ersten
~2-3-GPU-Tage-Lauf auf der lokalen RTX-Maschine des Nutzers, der danach 2
Wochen nicht erreichbar ist. Geprüfte Artefakte: `hypothesis_registry.md`
§H-14, `GPU_RESEARCH_SCAN_2026-07-09.md` §1, `CLAUDE.md`,
`src/bybit_edge/research/c14_panellag/{__init__,panel,encoder,ablation,stats,driver}.py`,
`scripts/c14_panellag.py`, `scinance2-impl/handoff_local/run_h14.{ps1,sh}`,
`README_H14.md`, `tests/unit/test_c14_panellag.py`. Alle Behauptungen unten
sind durch eigenes Lesen und/oder eigene Reproduktions-Skripte verifiziert,
nicht nur aus Docstrings übernommen.

---

## Verdikt: **PASS-WITH-NOTES — mit ZWEI harten Compute-Gating-Fixes vor dem ersten echten GPU-Lauf**

Die Kausalitäts-/No-Lookahead-Konstruktion, die BH-FDR-Kopie, die
Familiengrößen-Rechnung, das Checkpoint/Resume-Grundprinzip, die
capital_free-Reinheit und die meisten T3-Runner-Konventionen sind solide und
durch Tests abgesichert (20/20 grün, echt nachgeprüft, siehe unten). ABER: es
wurden **zwei reproduzierbare Lücken im Compute-Gating** gefunden — genau der
höchste Prioritätspunkt dieser Prüfwelle —, die es erlauben, dass ein Lauf
ein verdikt-tragendes Ergebnis (`gate_valid=true`, `weiter_indication` = echter
Bool statt `null`) liefert, **ohne dass für alle zugrunde liegenden ~226
Trainings echtes CUDA-Training stattgefunden hat**, bzw. bei dem eine
methodisch-invalide Positivkontrolle fälschlich wie ein normales DROP
aussieht. Beide sind mit kleinen, lokalisierten Patches behebbar, BEVOR der
Nutzer den Lauf startet. Bis dahin: **kein produktiver GPU-Lauf, dessen
Ergebnis für ein Registry-Urteil verwendet wird**, ohne dass diese zwei Punkte
gefixt sind (oder der gate-auditor den JSON-Payload manuell auf sauberen
`device`-Provenienz aller Checkpoints prüft, was in der Praxis niemand tun
wird).

---

## Spec-Treue-Tabelle (gegen hypothesis_registry.md §H-14, wörtlich)

| Registry-Anforderung | Code-Fundstelle | Treue |
|---|---|---|
| 12-Node-Panel (BTC/ETH×{Bybit,Binance,Deribit}+SOL/BNB/XRP×{Bybit,Binance}) | `panel.DEFAULT_NODES` | ✅ exakt, Reihenfolge/Deribit-Notation stimmt |
| publicTrade auf 1s-Grid | `panel.load_seconds_last_price` + `GRID_SECONDS=1` | ✅ |
| Target = Vorzeichen der nächsten 10s-Rendite | `DEFAULT_TRAIN_PARAMS["horizon"]=10`, `target_sign_labels` | ✅ |
| PatchTST-Style-Encoder pro Node + Cross-Node-Attention | `encoder._NodeEncoder`, `encoder.PanelLagModel` | ✅, m18-Muster nachvollziehbar adaptiert |
| T(j→i) = OOS-Δ-Log-Loss, Retrain-Ablation (NICHT Attention-Weight-Lesen) | `driver.compute_window_edges`: `abl[j,i]-full[i]` | ✅ |
| ~100 All-Surrogat-Null-Retrainings/Fenster, zirkulärer Shift | `ablation.DEFAULT_N_NULL=100`, `circular_shift_rows` | ✅ |
| 2 disjunkte Fenster W1/W2 (identisch H-09/H-12) | `driver.DEFAULT_WINDOW_A/B` | ✅ Daten nicht nachprüfbar (out of scope), Konvention übernommen |
| Gate: ≥1 Non-BTC-Source-Kante > Null-q95 UND BH-FDR in BEIDEN Fenstern | `assemble_payload`: `all_windows_survivor` | ✅ Logik korrekt, SIEHE Bug #2 für Interaktion mit Positivkontrolle |
| Hartes Ein-Fenster-DROP, kein Graubereich | Gate-neutraler Payload, keine Interpretation im Code | ✅ (Adjudikation bleibt beim gate-auditor, korrekt delegiert) |
| F-PANELLAG: ~110 Non-BTC-Source-Kanten × 2 Fenster, BH-FDR α=0,10 | `stats.benjamini_hochberg`, exakt 99×2=198 Tests | ✅ präzise nachgerechnet (9 Non-BTC-Nodes × 11 Ziele), Abweichung von "~110" sauber dokumentiert (README + Code-Kommentar) als Registry-Schätzung, keine post-hoc Anpassung |
| Positivkontrolle BTC→ETH ausgeschlossen vom Pass, MUSS eigene Schwelle erreichen sonst methodisch invalide | `compute_window_edges` (btc_source getrennt geführt), `validity_status` | ⚠️ Zustand korrekt SEPARIERT, aber `weiter_indication` wird davon NICHT sauber entkoppelt — siehe **Bug #2** |
| GPU zwingend, kein Verdikt ohne echtes CUDA-Training | `driver.build_compute_gating`, `make_compute_info`, CLI-Abbruch bei `!gpu_ready` | ⚠️ Mechanismus für den EINZELNEN Lauf korrekt, aber Checkpoint-Wiederverwendung über mehrere Läufe hinweg IST NICHT geschützt — siehe **Bug #1 (kritischster Fund dieser Prüfung)** |
| Checkpoint/Resume bei Absturz | `ablation.run_window_plan`, atomic write, stabile Verzeichnisse | ✅ funktional korrekt UND getestet — Kehrseite ist Bug #1 |
| Kausalität: nur Daten bis Entscheidungszeitpunkt | `panel.valid_sample_indices`, `target_sign_labels` | ✅ durch dedizierte Mutations-Tests (Vergangenheit/Zukunft isoliert) verifiziert, sauber |
| Selbstkill: Architektur NICHT auf Testfenstern getuned | `DEFAULT_MODEL_PARAMS` als read-only-Konstanten, keine CLI-Knobs | ✅ |
| KAPITALFREI: kein bps/pnl/sharpe/friction/edge_ | s. eigener Abschnitt unten | ✅ verifiziert, auch im Quellcode (nicht nur Test-Payload) |

---

## Gefundene Bugs

### Bug #1 (KRITISCH) — Checkpoint-Provenienz wird beim Resume nicht verifiziert: ein Lauf kann `gate_valid=true` + echten `weiter_indication`-Bool liefern, obwohl die zugrunde liegenden Trainings aus einem `--allow-cpu-fallback`/Dummy-Lauf stammen

**Datei/Zeilen:**
- `src/bybit_edge/research/c14_panellag/ablation.py:157-166` (`_load_checkpoint` — prüft nur `RESULT_LOSS_KEY in payload`, NICHT das `device`-Feld)
- `src/bybit_edge/research/c14_panellag/ablation.py:173-267` (`run_window_plan` — reicht gecachte Ergebnisse unverändert durch, ohne Provenienz-Check)
- `src/bybit_edge/research/c14_panellag/driver.py:331-347` (`make_compute_info`/`build_compute_gating` — `gate_valid` ist EIN globales Flag für den GESAMTEN Lauf, basierend NUR auf dem CUDA-Status BEIM START des aktuellen Aufrufs, nicht auf der tatsächlichen Herkunft jedes einzelnen — evtl. aus einem alten Checkpoint wiederverwendeten — Trainingsergebnisses)

**Reproduktion (selbst ausgeführt, nicht nur behauptet):**
1. Schritt 1: `run_window_plan` mit `make_dummy_train_fn` (kein Torch) auf einem
   Checkpoint-Verzeichnis `ckpt/` laufen lassen → alle 18 Tasks je Fenster
   geschrieben, `device: "cpu-dummy"` in jedem JSON-Checkpoint.
2. Schritt 2: `driver.run(...)` mit **demselben** `ckpt/`-Verzeichnis erneut
   aufrufen, diesmal mit `compute_info = make_compute_info(ran_on_gpu=True)`
   (so wie es die CLI nach einem echten `torch.cuda.is_available()`-Check
   bauen würde) und einem `train_fn`, das bei Aufruf einen `AssertionError`
   wirft (Beweis, dass es NIE aufgerufen wurde).
3. Ergebnis: **alle Tasks werden aus den Dummy-Checkpoints resumed** (`0
   trained now`), das `train_fn` wird nie aufgerufen, und der resultierende
   Payload zeigt:
   ```
   compute_gating.gate_valid: True
   compute_gating.ran_on_gpu: True
   weiter_indication: False   (ein ECHTER Bool, kein null!)
   ```

**Warum das die höchste Priorität dieser Welle direkt verletzt:** Die Frage
lautete explizit "darf ein Lauf JEMALS ein verdikt-tragendes Ergebnis liefern,
ohne dass echtes CUDA-Training stattgefunden hat?" — Antwort: **Ja, über genau
diesen Pfad.** Das Szenario ist nicht konstruiert-unrealistisch: der Default-
Checkpoint-Pfad ist laut README/Runner-Skripten bewusst STABIL
(`results/h14_checkpoints/`, `NICHT aendern zwischen Aufruefen desselben
Laufs — sonst kein Resume!`) und der CLI-Default (`<out-dir>/c14_checkpoints`)
lädt aktiv dazu ein, dass ein Nutzer, der vor dem ~2-3-Tage-Lauf schnell mit
`--allow-cpu-fallback` die Pipeline "smoke-testet" (was das Skript selbst
als offiziellen Modus dokumentiert), versehentlich denselben Checkpoint-Pfad
trifft wie der spätere echte GPU-Lauf — und niemand wird das während 2
unbeaufsichtigter Wochen bemerken, weil der JSON-Payload ehrlich `gate_valid:
true` zeigt (nur eben fälschlich).

**Fix-Vorschlag:** Jeder Checkpoint trägt bereits ein `device`-Feld
("cuda"/"cpu"/"cpu-dummy"). `run_window_plan` bzw. `assemble_payload`/`run()`
sollte über ALLE (frisch trainierten UND resumed/gecachten) Tasks prüfen,
dass `device` mit `"cuda"` beginnt, BEVOR `gate_valid=True` gesetzt werden
darf — z. B. `all(r.get("device","").startswith("cuda") for r in
results.values())` als zusätzliche notwendige Bedingung in
`make_compute_info`/`build_compute_gating`, oder als harter `ValueError` beim
Laden eines Checkpoints mit inkompatiblem `device`, falls der aktuelle Lauf
`ran_on_gpu=True` beansprucht. Zusätzlich: dokumentierte Warnung, niemals
`--allow-cpu-fallback`-Testläufe auf denselben `--ckpt-dir` wie der
produktive GPU-Lauf zeigen zu lassen (oder technisch erzwingen, z. B. Suffix
im Verzeichnisnamen je nach Compute-Modus).

---

### Bug #2 (HOCH) — `weiter_indication` wird NICHT genullt, wenn die Positivkontrolle scheitert (`validity_status="ungueltig"`) — kollabiert auf einen echten `False`, der wie DROP aussieht

**Datei/Zeilen:** `src/bybit_edge/research/c14_panellag/driver.py:249-258`

```python
all_windows_survivor = all(w["any_family_survivor"] for w in window_records)
weiter_indication: bool | None
if not gate_valid:
    weiter_indication = None
else:
    weiter_indication = bool(pc_ok_all and all_windows_survivor)
```

**Reproduktion (selbst ausgeführt):** synthetischer Payload mit
`ran_on_gpu=True` (also `gate_valid=True`), positive-control-Kanten (BTC→ETH)
NICHT geboostet (→ Positivkontrolle scheitert in beiden Fenstern), aber eine
ECHTE Non-BTC-Kante (SOL→BNB) übersteht Null-q95 UND FDR in beiden Fenstern
(→ `all_windows_survivor=True`). Ergebnis:
```
positive_control_ok_all_windows: False
validity_status: ungueltig
all_windows_have_surviving_non_btc_source: True
weiter_indication: False   ← sollte None sein!
```

**Warum das ein Bug ist:** Die Registry ist hier wörtlich eindeutig:
"scheitert das Modell, [die BTC→ETH-Kante] zu recovern, gilt der Lauf als
methodisch invalide STATT informativ" — das ist explizit ein DRITTER Zustand
(kein Verdikt), nicht identisch mit DROP. Der eigene Docstring von
`driver.py` (Zeile ~19-24) behauptet sogar wörtlich: "`weiter_indication` is
`null` (non-verdict-bearing) in that case" — aber "that case" wird im Code
nur für `!gate_valid` behandelt, NICHT für `!pc_ok_all`. Ein automatisierter
oder eiliger Leser (der gate-auditor selbst, oder ein Skript, das später
`weiter_indication` als DAS Signalfeld liest, wie es README_H14.md explizit
nahelegt: "Pruefe im JSON zwingend ... `weiter_indication`") sieht `false`
und liest das als "Gate nicht bestanden" (DROP-artig) — obwohl der
tatsächliche, korrekte Befund "Lauf methodisch ungültig, komplett neu
aufsetzen" lautet. Der existierende Unit-Test
`test_positive_control_failure_marks_run_invalid_not_drop` prüft NUR
`validity_status`, nicht `weiter_indication` — die Bug-Lücke ist deshalb
durch die 20/20-grüne Suite nicht abgedeckt (siehe Test-Abdeckung unten).

**Fix-Vorschlag:**
```python
if not gate_valid or not pc_ok_all:
    weiter_indication = None
else:
    weiter_indication = bool(all_windows_survivor)
```
plus einen neuen Testfall, der genau dieses Feld (nicht nur
`validity_status`) im Invalid-Fall auf `None` prüft.

---

### Bug #3 (MITTEL) — `RC_DATA_MISSING` referenziert, aber nirgendwo definiert → `NameError`-Crash statt sauberem Skip

**Datei/Zeile:** `scripts/c14_panellag.py:183` (`return RC_DATA_MISSING`),
Konstanten nur `RC_OK/RC_ERROR/RC_SKIP_NO_COMPUTE` definiert (Zeilen 77-79).

**Reproduktion (selbst ausgeführt):**
```
PYTHONPATH=src python3 scripts/c14_panellag.py --base-dir /nonexistent/harvest --allow-cpu-fallback --out-dir /tmp/c14test
```
→ Traceback: `NameError: name 'RC_DATA_MISSING' is not defined`, faktischer
Exit-Code 1 (zufällig identisch mit dem im Docstring dokumentierten `1 =
error (incl. missing harvester data)`, aber über einen ungewollten Crash
statt eine kontrollierte Rückgabe — inklusive hässlichem Python-Traceback im
Log statt der sauberen, bereits vorher ausgegebenen `SKIP:
Harvester-Pfade fehlen...`-Meldung).

**Praktische Tragweite:** In der normalen T3-Runner-Kette (run_h14.sh/ps1)
wird dieser Pfad vermieden, weil der Runner die Node-Pfade selbst VORAB prüft
und die CLI dann gar nicht erst aufruft, wenn Pfade fehlen. Der Bug greift
nur, wenn die CLI direkt aufgerufen wird (z. B. manuelles Debugging auf der
RTX-Maschine) oder falls die zwei Prüf-Implementierungen (Runner-Skript vs.
`_nodes_present()` in Python) je divergieren. Kein Weg zu einem falschen
Verdikt, aber ein handwerklicher Fehler, der das dokumentierte "loggt Fehler
statt zu stoppen"-Prinzip (CLAUDE.md Testpyramide) verletzt.

**Fix-Vorschlag:** `RC_DATA_MISSING = 1` als Alias auf `RC_ERROR` definieren
(oder direkt `return RC_ERROR` verwenden, wie es der einzige andere
Fehlerpfad im selben Skript tut).

---

### Bug #4 (NIEDRIG) — Nicht-ASCII-Zeichen in `run_h14.ps1`/`run_h14.sh` widersprechen der eigenen "ASCII-Body"-Selbstbeschreibung

**Datei/Zeilen:** `run_h14.ps1:21`, `run_h14.sh:22,27,32` — jeweils ein
Em-Dash (`—`) in Kopfkommentaren. Datei hat KEIN BOM (verifiziert:
`run_h14.ps1` beginnt mit `# =`, `run_h14.sh` mit `#!/`), UTF-8-kodiert.

**Bewertung:** Alle Fundstellen liegen ausschließlich in
Kommentarzeilen (`#...`) im Kopf-Block, NICHT im ausführbaren Code — daher
funktional harmlos selbst wenn PowerShell 5.1 die Datei ohne BOM über die
System-Codepage statt UTF-8 liest (führt bestenfalls zu Zeichensalat im
Kommentartext, keinem Parse-Fehler). Der Header behauptet aber wörtlich
"PS 5.1-kompatibel (handle-cache + BelowNormal + **ASCII-Body**)" — das ist
für den Body streng genommen korrekt (Body ist tatsächlich ASCII), aber die
Formulierung suggeriert eine Garantie für die GANZE Datei, die nicht
eingehalten wird. Kosmetischer Fund, kein Blocker.

**Fix-Vorschlag:** Em-Dashes durch `-` ersetzen (wie es der Rest der Datei
konsequent tut — alle anderen ähnlichen Stellen nutzen bereits `-`).

---

### Beobachtung (kein Bug, Prozess-Hinweis) — GL-012-Feasibility-Check (Positivkontroll-Recoverability) ist laut Registry selbst "AUSSTEHEND" und hat kein dediziertes CLI-Tooling

Die Registry verlangt wörtlich: "der Builder MUSS vor dem echten GPU-Lauf
pruefen, ob die Positivkontroll-Kante (BTC->ETH) im
synthetischen/Kurz-Testlauf recoverbar ist, sonst methodische Invaliditaet
vor Ressourceneinsatz erkennen." Es gibt keinen eigenen CLI-Schalter für
einen kurzen, ECHTEN (Torch-basierten, nicht Dummy-)Recoverability-Vorlauf —
der Nutzer müsste dafür manuell `--window-a-start/--window-a-end` auf ein
kurzes Fenster setzen und einen Kurzlauf mit echtem Torch (nicht
`--allow-cpu-fallback`, sonst wieder `gate_valid=false`) durchführen. Das ist
technisch machbar, aber nirgendwo als fester Ablaufschritt operationalisiert
oder in `run_h14.{sh,ps1}` vorgeschaltet. Da die Registry diesen Punkt selbst
als offen markiert (kein Builder-Versäumnis im engeren Sinn), wird das hier
nur als Hinweis für den Nutzer vor dem Start dokumentiert, nicht als Bug
gewertet.

### Beobachtung (kein Bug) — keine `decisions.md`-DEC-Einträge für die builder-fixierten Hyperparameter (Lookback 120s, Patch-Länge/Stride, FFILL_CAP_SECONDS=60)

CLAUDE.md verlangt bei Registry-Stummheit einen `DEC-xx`-Eintrag mit
Optionen/Begründung/Rückbauweg. Diese Werte sind in `README_H14.md` und
Code-Kommentaren dokumentiert und begründet, aber nicht als formaler
`DEC-xx`-Eintrag in `state/decisions.md` erfasst. Geringes Risiko, da die
Werte klar als "builder-fixiert, NICHT auf Testfenstern getuned" markiert
sind und nicht nachträglich änderbar über CLI-Flags — reiner
Prozess-Compliance-Hinweis.

---

## Test-Abdeckung

`PYTHONPATH=src python3 -m pytest tests/unit/test_c14_panellag.py -q`
selbst ausgeführt: **20 passed in 31.50s — ECHT grün, verifiziert.**

Abgedeckt (bestätigt durch eigenes Lesen jedes Tests): 12-Node-Panel-Laden
gegen synthetischen Hive-Baum inkl. Deribit-Hyphen-Notation, Ffill-Cap-Test,
Kausalitäts-Isolationstests (Vergangenheit/Zukunft getrennt mutiert),
Zero-Forward-Return-Masking, Train/OOS-Embargo, Edge-Statistik +
BH-FDR-Familienkonstruktion mit Fake-Losses, volle Orchestrierung inkl.
Checkpoint/Resume (Second-Call-Zero-Retrain, Delete-One-Force-Retrain),
Compute-Gating-Ehrlichkeit (`check_gpu`, `make_compute_info`), volle CLI-Läufe
(`--check-gpu-only`, Abbruch ohne `--allow-cpu-fallback`, Ende-zu-Ende mit
`--allow-cpu-fallback`), capital_free-Token-Scan im JSON-Payload.

**Lücken, die zu den oben gefundenen Bugs geführt haben:**
- **Kein Test** deckt Checkpoint-Wiederverwendung ÜBER unterschiedliche
  Compute-Modi hinweg ab (Bug #1) — alle Checkpoint-Tests nutzen konsistent
  dieselbe (Dummy-)`train_fn` für Schreiben UND Resume.
- `test_positive_control_failure_marks_run_invalid_not_drop` prüft nur
  `validity_status`, NICHT `weiter_indication` — die eigentliche Payload-
  Konsequenz des Namens ("...marks run invalid not drop") wird nicht
  verifiziert (Bug #2).
- capital_free-Scan läuft nur gegen den JSON-Payload einer Testfunktion, nicht
  automatisiert als Quellcode-Grep in CI — hier zusätzlich manuell durch den
  Auditor verifiziert (siehe unten), aber kein Regressionsschutz im Repo.

## capital_free-Check

Manueller Grep über alle Quelldateien (`src/bybit_edge/research/c14_panellag/*.py`,
`scripts/c14_panellag.py`) nach `bps|pnl|sharpe|friction|edge_` (case-insensitive):
**alle Treffer sind ausschließlich Negations-Docstrings** ("KAPITALFREI: ...
no friction, bps, PnL, Sharpe logic anywhere" etc.), keine einzige
Vorkommen in ausführbarem Code oder Payload-Feldern. `capital_free: true` ist
im Payload hart auf `True` gesetzt (`driver.py:264`), nicht konfigurierbar.
**PASS.**

## T3-Runner-Check (`run_h14.ps1` / `run_h14.sh`)

| Kriterium | ps1 | sh | Befund |
|---|---|---|---|
| Skript-Pfad erstes CmdArg | ✅ | ✅ | explizit kommentiert "WICHTIG: Skript-Pfad ist das ERSTE CmdArg" |
| `$null=$p.Handle` | ✅ (Zeile 119) | n/a | korrekt |
| BelowNormal-Priorität | ✅ (Prozess + Kind) | ✅ (`renice -n 10`) | korrekt |
| ASCII/UTF-8-BOM-sicher | ⚠️ | ⚠️ | kein BOM (gut), aber Em-Dashes in Kommentaren — Bug #4, kosmetisch |
| nie interaktiver Prompt | ✅ | ✅ | `-NoNewWindow`/Redirects, kein `input()` im Python-Code (verifiziert per Grep) |
| Timeout mit Kill | ✅ (`WaitForExit`+`Kill`) | ✅ (`timeout`-Kommando) | korrekt, inkl. saubere TIMEOUT-Behandlung als "normal bei unvollständigem Plan" |
| `SUMMARY_<datum>.md` | ✅ | ✅ | korrekt benannt und geschrieben |
| deterministischer Exit-Code | ✅ (0/1/2 aus ok/fail/skip) | ✅ | korrekt, konsistent zwischen beiden Skripten |
| Resume-fähig über mehrere Aufrufe | ✅ dokumentiert und technisch korrekt | ✅ | siehe Checkpoint/Resume-Abschnitt — ABER siehe Bug #1 für die Kehrseite |

Ansonsten: beide Skripte sind praktisch 1:1-Übersetzungen voneinander
(gleiche Fenster, gleiche Defaults, gleiche Summary-Struktur), Prüfung der
12 Node-Pfade VOR jedem CLI-Aufruf korrekt implementiert und mit
`panel.DEFAULT_NODES`-Reihenfolge/-Notation synchron gehalten (manuell
gegenverglichen, exakte Übereinstimmung inkl. Deribit-`-PERPETUAL`-Suffix).

## Compute-Gating-Korrektheit (wichtigster Check dieser Welle)

**Für einen EINZELNEN, isolierten Lauf ohne vorbestehende Checkpoints ist der
Mechanismus korrekt und ehrlich:**
- `--check-gpu-only` macht nachweislich KEIN Training (nur `torch.cuda.is_available()`-Report).
- Ohne `--allow-cpu-fallback` bricht die CLI VOR jedem Training ab (rc=2),
  selbst verifiziert per Reproduktion.
- `--allow-cpu-fallback` markiert den Payload konsistent `gate_valid=false`,
  `weiter_indication=null` — für den EINMALIGEN, frischen Lauf korrekt (durch
  Unit-Test UND eigene Reproduktion bestätigt).
- Kein numpy-Trainingsersatz — ohne Torch wird ausschließlich die explizit
  als "KEIN Modell" deklarierte `make_dummy_train_fn` verwendet, die
  niemals `gate_valid=true` erzeugen kann (durch `synthetic_train_fn_used`
  hart verdrahtet).

**ABER über mehrere Läufe / Checkpoint-Resume hinweg ist die Kette
gebrochen (Bug #1, s. o.):** `gate_valid` wird als EINE globale Eigenschaft
des AKTUELLEN Aufrufs berechnet, nicht als Eigenschaft JEDES einzelnen der
226 zugrunde liegenden Trainingsergebnisse — obwohl genau diese Information
(`device`-Feld) in jedem Checkpoint bereits vorhanden ist und nur nicht
geprüft wird. Das ist der schwerwiegendste Fund dieser Prüfung, weil er
direkt und reproduzierbar zeigt, dass ein verdikt-tragendes Ergebnis OHNE
durchgängiges echtes CUDA-Training entstehen kann — exakt das, was diese
Prüfwelle als höchste Priorität verlangt hat zu verifizieren.

## Positivkontroll-Korrektheit

Die **Buchführung** ist sauber getrennt: `btc_source_edges` fließen
NICHT in die F-PANELLAG-Familie ein (`compute_window_edges`, verifiziert per
Zählung: `family_edges` hat exakt 99 Einträge/Fenster, `btc_source_edges`
exakt 33, `positive_control` filtert daraus die 9 BTC→ETH-Kanten). Der
`validity_status`-Zustand ("gueltig"/"ungueltig") existiert als EIGENER,
vom WEITER/DROP-Urteil getrennter Wert — das ist strukturell richtig
umgesetzt. Der Bruch liegt NICHT in dieser Buchführung, sondern darin, dass
`weiter_indication` (das Feld, das README_H14.md explizit als
DAS-zu-prüfende-Feld benennt) diese Trennung nicht respektiert — siehe
**Bug #2**. Ein Leser, der nur `weiter_indication` prüft (wie explizit
empfohlen), bekäme im Ungültig-Fall einen falschen DROP-Eindruck statt
"Lauf ungültig, kein Urteil möglich".

## Checkpoint/Resume-Korrektheit

Funktional korrekt und durch echte Tests abgesichert: atomic
tmp+rename-Schreiben (`os.replace`, plattformübergreifend atomar),
`_load_checkpoint` lädt vorhandene Ergebnisse und überspringt das
entsprechende Training, zweiter Aufruf mit identischem Checkpoint-Verzeichnis
löst nachweislich 0 neue Trainings aus, Löschen eines einzelnen Checkpoints
erzwingt genau 1 Retraining (`test_run_window_plan_executes_and_checkpoints`
— selbst nachvollzogen, Logik stimmt). Checkpoint-Verzeichnis ist
STABIL/nicht-zeitgestempelt in beiden Runner-Skripten
(`results/h14_checkpoints/`), getrennt vom zeitgestempelten Run-Ergebnis-
Ordner — genau wie für einen mehrtägigen, mehrfach unterbrochenen Lauf
nötig. **Die einzige Schwäche ist NICHT das Resume-Prinzip selbst, sondern
das Fehlen einer Provenienz-Prüfung beim Resume (Bug #1)** — technisch ist
"Checkpoint gefunden → Training überspringen" komplett korrekt, es fehlt nur
die zusätzliche Frage "war DIESER Checkpoint aus echtem GPU-Training?".

---

## Zusammenfassung für den Gate-Auditor / Nutzer

Vor dem ersten produktiven ~2-3-Tage-GPU-Lauf sollten Bug #1 und Bug #2
gefixt werden (beide sind kleine, lokale Patches in `driver.py`/`ablation.py`,
keine Architekturänderung). Bug #3 sollte ebenfalls gefixt werden (eine
Zeile). Bug #4 ist kosmetisch und kann warten. Danach: Code ist bereit für
den echten Lauf über `run_h14.sh`/`run_h14.ps1`. **Wichtigster operativer
Rat an den Nutzer:** falls vor dem produktiven Lauf ein
`--allow-cpu-fallback`-Smoke-Test gewünscht wird, UNBEDINGT einen anderen
`--ckpt-dir` als den produktiven `results/h14_checkpoints/` verwenden (bis
Bug #1 gefixt ist) oder diesen Ordner vor dem echten Start leeren.
