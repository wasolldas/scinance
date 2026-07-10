# Audit H-18 · GL-006/H-04 Lead-Lag High-N-Surrogat-Auflösungs-Audit

**Auditor:** frischer, unabhängiger adversarialer Code-Auditor (kein Autor des Codes).
**Datum:** 2026-07-10. **Scope:** `src/bybit_edge/research/c18_leadlag_audit/` (alle Module),
`scripts/c18_leadlag_audit.py`, `scinance2-impl/handoff_local/run_h18.{sh,ps1}` +
`README_H18.md`, `tests/unit/test_c18_leadlag_audit.py`, gegen die Originalpipeline
`src/bybit_edge/research/c17_c41_lead_lag/` und die Ground Truth (`hypothesis_registry.md`
H-18, `gate_log.md` GL-006, `GPU_RESEARCH_SCAN_2026-07-09.md` §5).

---

## Verdikt

**Code ist auf CPU/Sandbox-Ebene korrekt und methodisch sauber, mit einem konkreten
HIGH-Bug im T3-Runner (beide Plattformen) und einem MEDIUM-Design-Gap bei der
Datenbindungs-Sichtbarkeit.** Kein Verstoß gegen die Append-only-Registry-Disziplin
gefunden — `gate_log.md`/`hypothesis_registry.md` werden von diesem Modul nirgends
geschrieben (Code-Lesen + `git diff` beide leer). Der Äquivalenzbeweis wurde von mir
selbst nachvollzogen (nicht nur den Tests geglaubt) und hält bei N=200/500 exakt,
mit einer offen dokumentierten, harmlosen ~1e-16-Abweichung in den *Surrogat-Statistiken*
(nicht den Offsets) durch Batch-Summationsreihenfolge — das ist ehrlich im Code
dokumentiert und ändert die p-Werte in allen getesteten Fällen nicht.

**Vor dem ersten GPU-Lauf zu fixen (empfohlen, nicht blockierend für einen ersten
Testlauf, aber blockierend für einen *unbeaufsichtigten* 2-Wochen-Lauf):**
1. **HIGH:** `run_h18.sh`/`run_h18.ps1` lassen `H18_AUDIT` (den vollen 100k-GPU-Lauf)
   laufen, selbst wenn `H18_SELFTEST` fehlschlägt — entgegen der eigenen
   Kopfkommentar-Spezifikation ("MUSS rc=0 liefern, sonst FAIL. Kein Audit-Lauf.").
2. **MEDIUM:** `data_binding_vs_gl006`/`all_windows_match_gl006` (die Prüfung, ob
   überhaupt auf denselben archivierten GL-006-Fenstern gemessen wurde) wird weder
   in der CLI-Einzeiler-Zusammenfassung noch im Runner-`SUMMARY_<datum>.md` angezeigt
   — nur im JSON/MD-Report-Körper. Bei einer weiterlaufenden Live-DB (Schutzgut
   „Collector nie anhalten") ist es sehr wahrscheinlich, dass der `--db`-Pfad (kein
   fixiertes Archiv, `_cap_tail` nimmt die *jüngsten* Ticks) am Laufdatum NICHT mehr
   die GL-006-Fenster vom 2026-06-17 trifft, sondern frischere Daten — das würde
   T1/T2 fälschlich als „Auflösung von GL-006" lesbar machen, obwohl in Wahrheit neue
   Daten gemessen wurden.

Beide Punkte sind unten im Detail begründet. Alles andere (TE-/WCOH-Formeln, Lag-Set,
BH-FDR-Wiederverwendung, Compute-Gating, KAPITALFREIHEIT, T1/T2-Feld-Korrektheit,
GL-006-Unversehrtheit) ist sauber.

---

## Spec-Treue-Tabelle (registry H-18 wörtlich vs. Code)

| Registry-Anforderung | Befund | Status |
|---|---|---|
| „byte-identische... Pipeline aus GL-006" — Fenster-Split, Grid-Alignment, Lag-Set, BH-FDR importiert statt reimplementiert | `driver.py` importiert `split_pair_windows`, `align_returns`, `DEFAULT_LAGS`, `DEFAULT_N_BINS`, `benjamini_hochberg`, `FDR_ALPHA`, `SURROGATE_P_MAX`, `MIN_WINDOWS`, `WINDOW_MAX_TICKS`, `DEFAULT_GRID_MS` **direkt aus `c17_c41_lead_lag`** (kein Reimplementieren) | **OK** |
| „EINZIGE Änderung: n_surrogates 200 → 100.000" | Bestätigt — `FULL_RESOLUTION_N_SURROGATES = 100_000`, sonst identische Variantenschleife/Reihenfolge/Seeds (`seed + vi`, identisch zum Original) | **OK** |
| Lags {1,2,3,5,10}, Grid 1000ms, Fenster F0/F1, 22-Varianten-Familie | `DEFAULT_LAGS`/`DEFAULT_GRID_MS`/`DEFAULT_N_BINS` importiert, nicht redefiniert; `n_variants = 2*len(lags)+1 = 11`/Fenster × 2 Fenster = 22, identisch zu GL-006 | **OK** |
| TE-Formel identisch | `te_batched.transfer_entropy_batch` repliziert Quantisierung (doppelter stabiler Argsort), Indexausrichtung, Plug-in-Schätzer 1:1 (nur vektorisiert) — direkt gegen Original verglichen (s. Äquivalenz-Abschnitt) | **OK** |
| WCOH-Formel identisch, inkl. Skalenzahl | `wcoh_batched.py` Kommentar korrigiert selbst den GPU-Scan-Fehler: „~50 Skalen" war eine Schätzung des Scan-Dokuments, Code behält bewusst die ORIGINALEN `n_scales=16` bei mit Verweis auf die Byte-Identität-Klausel | **OK, sogar explizit gegen das eigene Ausgangsdokument verteidigt** |
| Verdikt-tragende Null = zirkulärer Shift, RNG-Konsumption identisch | Verifiziert (s. Äquivalenz-Abschnitt) — bit-identisch bei N=3874 (echte GL-006-F0-Fenstergröße) | **OK** |
| Registry-benannte GPU-Primitive (Phase-Shuffle, Permutation) NUR diagnostisch, NIE verdikt-tragend | Docstrings + Code: `phase_shuffle_surrogates`/`permutation_surrogates` werden in `driver.run()`/`run_window()` NIRGENDS aufgerufen — nur in Tests direkt getestet | **OK** |
| KAPITALFREIHEIT | Kein `bps/friction/pnl/sharpe/tradab` Token im Code (eigener Grep zusätzlich zum Test-Regex durchgeführt) — nur in Docstring-Negationen | **OK** |
| Compute-Gating: `verdict_carrying=False` wenn Backend≠torch-cuda ODER n_surrogates<100000 | `_verdict_carrying()` implementiert exakt diese UND-Verknüpfung als ODER-Negation | **OK** |
| Modul schreibt NIE `gate_log.md`/`hypothesis_registry.md` | Einzige Schreibzugriffe im ganzen Package: `json_path.open("w")` und `md_path.write_text()` in `write_outputs()`, beide auf caller-kontrollierte Pfade mit fixen Dateinamen `c18_leadlag_audit_results.{json,md}` / `..._selftest.{json,md}` — nie auf `gate_log.md` oder `hypothesis_registry.md` | **OK, selbst verifiziert (s.u.)** |
| „Fenster identisch GL-006, archivierte Fenster, keine neuen Daten nötig" | Code lädt via `load_pair_duckdb`/`load_trades_file` aus der (potenziell weiterwachsenden) Live-DB und cappt auf die *jüngsten* Ticks — es gibt KEINEN Mechanismus, der die archivierten GL-006-Zeitstempel erzwingt; nur `data_binding_vs_gl006` *meldet* eine Abweichung nachträglich, ohne den Lauf zu blockieren oder zu markieren | **GAP — s. Bug M-1 unten** |

---

## Gefundene Bugs (nach Schweregrad)

### H-1 (HIGH) — T3-Runner führt den vollen GPU-Audit auch bei fehlgeschlagenem Selftest aus

**Ort:** `scinance2-impl/handoff_local/run_h18.sh` Zeilen 96–125 UND
`run_h18.ps1` Zeilen 125–158 (identischer Bug auf beiden Plattformen).

Der Kopfkommentar beider Skripte spezifiziert explizit eine dreistufige Kausalkette:

> „(1) H18_SELFTEST … **MUSS rc=0 liefern, sonst FAIL** (Regression). (2) H18_GPU_CHECK
> … (3) H18_AUDIT — **nur bei rc 0 aus (2)**"

Der tatsächliche Code prüft aber **nur** `GPU_RC` (Bash) bzw. `$rcGpu` (PowerShell)
vor dem Start von `H18_AUDIT` — der Rückgabewert von `H18_SELFTEST`
(`LAST_RC`/`$rcSelftest`) wird nach einer reinen `echo`/`Write-Host`-Warnung
**nie wieder abgefragt**:

```bash
step H18_SELFTEST ...
if [ "$LAST_RC" != "0" ] && [ "$DRY" != "1" ]; then
    echo "FAIL: H18_SELFTEST — ... Kein Audit-Lauf."   # <- nur eine Meldung, kein Abbruch
fi
step H18_GPU_CHECK ...
GPU_RC="$LAST_RC"
...
elif [ "$GPU_RC" = "0" ]; then
    step H18_AUDIT ...     # <- läuft unabhängig vom SELFTEST-rc
```

**Auswirkung:** Wenn die Methodik-Äquivalenz auf der Zielmaschine aus irgendeinem Grund
bricht (z. B. torch-/CUDA-Versionsunterschied, numerisches Randproblem, ein künftiger
Regressions-Bug), erkennt der Selftest das korrekt (rc≠0, `FN` steigt, Gesamt-Exit-Code
wird 1) — **aber der teure 100k-Surrogat-GPU-Lauf läuft trotzdem durch** und schreibt
ein scheinbar vollständiges `c18_leadlag_audit_results.json` mit `verdict_carrying:true`
(falls CUDA vorhanden ist), das ein Gate-Auditor 2 Wochen später ohne Kontext lesen
könnte, ohne zu bemerken, dass die Korrektheitsgrundlage (der Selftest) an diesem Tag
gebrochen war. Bei einem 2-Wochen-unbeaufsichtigten Lauf ohne den Nutzer als
Rückfrage-Instanz ist das genau das Szenario, vor dem ein Compute-Gating eigentlich
schützen soll — der Gate hier ist nur an CUDA-Verfügbarkeit gekoppelt, nicht an
Pipeline-Korrektheit.

**Fix (Vorschlag, nicht selbst durchgeführt — Audit ist Lesezugriff):** in beiden
Runnern `H18_AUDIT` zusätzlich an `SELFTEST_RC = 0` koppeln, z. B.
`elif [ "$GPU_RC" = "0" ] && [ "$SELFTEST_RC" = "0" ]; then ... else rec H18_AUDIT SKIP ... "Selftest fehlgeschlagen" ...`.

### M-1 (MEDIUM) — Datenbindungs-Status wird nicht in CLI-/Runner-Zusammenfassung gespiegelt

**Ort:** `scripts/c18_leadlag_audit.py` Zeilen 210–218 (Abschluss-Print),
`run_h18.sh` Zeilen 128–157 / `run_h18.ps1` Zeilen 167–199 (`SUMMARY_<datum>.md`-Body).

Der finale CLI-Einzeiler zeigt `mode`, `verdict_carrying`, `t1_holds`, `t2_holds` —
aber **nicht** `data_binding_vs_gl006.all_windows_match_gl006`. Der Runner-`SUMMARY`
verweist nur pauschal auf den JSON-Pfad, ohne den Wert zu extrahieren. Das ist
insofern real riskant, als die registrierte Prämisse „identisch GL-006, archivierte
Fenster, keine neuen Daten nötig" **vom Code selbst nicht erzwungen** wird: `run()`
lädt via `load_pair_duckdb` aus der Live-DB und `_cap_tail` (in `c17_c41_lead_lag.driver`)
nimmt bewusst die **jüngsten** Ticks — nicht die 2026-06-17-Ticks. Solange die
Collector-DB seit GL-006 weiter wächst (Schutzgut „Collector nie anhalten",
CLAUDE.md), wird ein H-18-Lauf, der Wochen später gegen `data/bybit_edge.duckdb`
läuft, mit hoher Wahrscheinlichkeit **andere** Fenster ziehen als GL-006, und
`all_windows_match_gl006` würde `False` sein. Der Code selbst behandelt das korrekt
ehrlich („mismatch does NOT abort the run — it is flagged honestly", `stats.py`
Docstring) — aber „geflaggt" heißt hier nur „steht im JSON-Report-Körper", nicht
„wird im Ein-Zeiler oder in der SUMMARY sichtbar". Ein Gate-Auditor, der nur die
CLI-Ausgabe oder `SUMMARY_<datum>.md` liest (der übliche schnelle Pfad), würde einen
Datenbindungsbruch übersehen und T1/T2 fälschlich als Auflösung der GL-006-Fenster
lesen, obwohl in Wahrheit auf verschobenen/neuen Daten gemessen wurde.

**Nicht** als Bug zu werten: das JSON/MD selbst berichtet den Status korrekt und
vollständig (`render_markdown` hat einen eigenen Abschnitt „Datenbindung vs. GL-006").
Das Problem ist reine Sichtbarkeits-/Ergonomie-Lücke, kein Korrektheitsfehler der
Kernpipeline.

### L-1 (LOW, informativ) — Surrogat-*Statistiken* sind nicht bit-identisch, nur die Shift-Offsets

Die Modul-Docstrings (`__init__.py`, `surrogate_gpu.py`) formulieren „surrogate
ensemble is bit-identical … regardless of backend" leicht zweideutig. Meine eigene
Nachrechnung (s. Äquivalenz-Abschnitt) zeigt: **die verschobenen Serien** (die
„ensemble"-Mitglieder) sind exakt bit-identisch — bestätigt bis auf Bit-Ebene bei
n=3874 (echte GL-006-F0-Größe). Die daraus **berechnete TE/WCOH-Statistik** weicht
wegen Batch-Summationsreihenfolge um bis zu ~1e-17 ab (143 von 200 Zellen im
Test-Fall marginal ungleich). `te_batched.py`s eigener Docstring benennt das bereits
korrekt und ehrlich als „the ONLY tolerated deviation … ~1e-16-level". In allen von
mir und den Tests geprüften Fällen ändert das den p-Wert NICHT (die Abweichung ist
viele Größenordnungen kleiner als der Abstand zum nächsten Vergleichswert). Bei
N=100.000 mit ~1e12 FLOPs ist ein extrem seltenes Flip-Risiko an der p_crit-Grenze
theoretisch nicht auf Null — aber das ist ein irreduzibles Restrisiko jeder
GPU-Batch-Vektorisierung, keine Nachlässigkeit des Codes. Empfehlung: keine
Code-Änderung nötig, aber der Docstring in `surrogate_gpu.py` Zeile 6–9 könnte
präziser sagen „die Shift-Offsets/verschobene Serien sind bit-identisch; die
Statistik darüber ist bis auf Summationsreihenfolge (~1e-16) identisch" statt
pauschal „surrogate ensemble is bit-identical". Reine Doku-Präzisierung, kein
Funktionsbug.

### Keine weiteren Bugs gefunden in:
- TE-/WCOH-Batch-Kernformeln (direkt gegen Original verglichen, s.u.)
- BH-FDR-Wiederverwendung (`benjamini_hochberg is orig_benjamini_hochberg` — dieselbe
  Funktion, kein Reimplement, per `is`-Identität geprüft)
- Compute-Gating-Logik (`_verdict_carrying`)
- T1/T2-Feld-Berechnung an konstruierten Beispielen (eigene Nachrechnung, s.u.)
- KAPITALFREIHEIT (statischer Grep + Payload-Key-Scan)
- Backend-Resolution (`resolve_backend`) — degradiert ehrlich ohne Torch, wirft bei
  explizitem `cuda`-Request ohne Device, downgraded nie stillschweigend

---

## GL-006-Unversehrtheit (WICHTIGSTER CHECK)

**Ergebnis: sauber. Kein Verstoß.**

1. **Statischer Code-Scan:** `grep -rn "gate_log\|hypothesis_registry"` über das
   gesamte `c18_leadlag_audit`-Package liefert ausschließlich String-Konstanten/
   Docstring-Erwähnungen (`GATE_LOG_PATH = "scinance2-impl/state/gate_log.md"`,
   `HYPOTHESIS_REGISTRY_PATH = "..."`, Non-Verdikt-Klausel-Text) — **niemals** als
   Ziel eines Schreibzugriffs. Ein zweiter, gezielter Grep nach
   `open(...)`/`.write(...)`/`write_text(...)` im ganzen Package findet exakt zwei
   Fundstellen, beide in `driver.write_outputs()`, beide auf caller-kontrollierte,
   fest benannte Ausgabepfade (`c18_leadlag_audit_results.{json,md}`) — nicht auf
   `gate_log.md` oder `hypothesis_registry.md`.
2. **Der Test `test_module_does_not_write_gate_log`** implementiert dieselbe
   Prüfung als automatisierten Guard (Zeilen-Scan nach `gate_log` kombiniert mit
   `open(`/`.write(`/`write_text(` in derselben Zeile) — grün.
3. **`git status`/`git diff --stat`** gegen beide Dateien: leer, keine
   uncommitteten Änderungen. `git log` bestätigt, dass der letzte Commit, der
   `gate_log.md`/`hypothesis_registry.md` berührt hat, der WP-0-Brücken-Commit
   „Welle 5 WP-0: bridge GPU research shortlist into hypothesis registry (H-14..H-18)"
   war — kein Commit danach (inkl. keiner der c18-Modul-Commits) hat diese Dateien
   angefasst.
4. Die **Non-Verdikt-Klausel** ist wörtlich im Payload (`non_verdict_clause`) und im
   Markdown-Report vorhanden und deckt sich exakt mit dem Registry-Sonderstatus-Text.
5. `stats.py`s `GL006_BASELINE` ist eine **read-only Transkription** der archivierten
   Werte (mit Kommentar „transcribed at FULL float precision from the archived,
   adjudicated GL-006 result") — kein Import/keine Live-Mutation der Originaldatei.

**Einzige indirekte Sorge** (kein Verstoß gegen die Append-only-Regel, aber ein
Betriebsrisiko): Bug M-1 oben — ein Gate-Auditor könnte bei unbemerkter
Datenbindungsabweichung fälschlich einen NEUEN GL-014-Eintrag auf Basis von Daten
schreiben, die gar nicht die archivierten GL-006-Fenster sind. Das würde **GL-006
selbst nicht verändern** (append-only bleibt gewahrt), aber die inhaltliche Aussage
des neuen GL-014-Eintrags wäre unter Umständen nicht das, was registriert wurde.

---

## Äquivalenz-Beweis-Verifikation (WICHTIGSTER METHODISCHER CHECK)

Ich habe den Äquivalenzbeweis **selbst nachgerechnet**, nicht nur den Tests/Docstrings
geglaubt:

**1) RNG-Konsumption der Shift-Offsets — bei der ECHTEN GL-006-Fenstergröße (n=3874,
nicht nur dem 900-Bar-Test-Fixture) geprüft:**

```python
rng = np.random.default_rng(seed)          # Original: serielle Schleife
orig_rows[k] = _circular_shift(rng, x)      # 500x
offsets = generate_shift_offsets(n, 500, seed)   # c18: vektorisiert erzeugt
batch_rows = batch_circular_shift(x, offsets, backend='numpy')
np.array_equal(orig_rows, batch_rows)  # -> True
```
**Ergebnis: `True` — bit-identisch**, auch bei n=3874 (nicht nur beim kleinen
Test-Fixture n=900). Das ist eine strengere Prüfung als die mitgelieferten Unit-Tests
(die nur n=500 testen) und bestätigt die zentrale Behauptung: `generate_shift_offsets`
+ `batch_circular_shift` reproduzieren exakt dieselbe verschobene Serie wie die
serielle Original-`_circular_shift`-Schleife, für beliebige `n`.

**2) `run_equivalence_selftest()` selbst ausgeführt** (nicht nur den Testcode
gelesen):

```
mode equivalence_selftest, backend numpy
all_point_match True, all_p_match True, equivalence_holds True
TE_fwd_lag2  diff=0.000e+00  p_orig=0.66169 p_batch=0.66169  p_exact=True  bit_identical=False
TE_rev_lag2  diff=1.735e-18  p_orig=0.58706 p_batch=0.58706  p_exact=True  bit_identical=False
TE_fwd_lag3  diff=2.220e-16  p_orig=0.00498 p_batch=0.00498  p_exact=True  bit_identical=False
TE_rev_lag3  diff=6.072e-18  p_orig=0.74129 p_batch=0.74129  p_exact=True  bit_identical=False
WCOH         diff=0.000e+00  p_orig=0.00498 p_batch=0.00498  p_exact=True  bit_identical=False
```

Auffällig: `surrogate_stats_bit_identical=False` in allen 5 Zeilen, obwohl die
Punktschätzer teils exakt (`diff=0.000e+00`) übereinstimmen. Das habe ich vertieft
(s. Bug L-1): die *Shift-Offsets/verschobenen Serien* sind bit-identisch, aber die
darüber batched berechnete TE-Statistik weicht durch Summationsreihenfolge um bis
zu ~1e-17 pro Zelle ab (143/200 Zellen in einer Stichprobe marginal ungleich). Das ist
korrekt als „einzig tolerierte Abweichung" in `te_batched.py` dokumentiert und ändert
in allen geprüften Fällen den p-Wert **nicht** — die p-Werte sind exakt gleich
(`p_original == p_batched`, nicht nur `approx`). Die behaupteten Zahlen im Builder-
Bericht (TE point_diff~1e-16, p-Werte exakt gleich) sind damit **bestätigt**, mit der
Präzisierung, dass „bit-identisch" korrekt für die Offsets/verschobenen Serien gilt,
nicht wortwörtlich für die daraus abgeleiteten TE-Werte.

**3) Direkter Formel-Vergleich TE/WCOH-Batch vs. Original**, eigenständig
nachgerechnet (nicht nur Test-Suite vertraut): `transfer_entropy_batch` über mehrere
Lags/Seeds mit `orig_transfer_entropy` verglichen (`abs=1e-9` Toleranz) — Test-Suite
deckt das bereits ab (`test_batched_te_matches_original_over_a_batch_of_rows`), von
mir stichprobenartig per Nachrechnung der Formeln in `te_batched.py`/
`transfer_entropy.py` Zeile für Zeile bestätigt: identische Quantisierung (doppelter
stabiler Argsort), identische Index-Ausrichtung (`t_next`/`t_now`/`s_past`), identische
Plug-in-TE-Summe (nur `for`-Schleife → `np.where`-Maske vektorisiert).

**Fazit:** Der Äquivalenzbeweis hält. Die einzige Einschränkung (bereits oben unter
L-1 vermerkt) ist, dass er nur bei kleinem N (200–500, synthetischer Input) gegen
die serielle Originalpipeline geprüft werden **kann** — bei N=100.000 auf der
Ziel-GPU wird die Originalpipeline aus Zeitgründen nie parallel mitgerechnet
(das ist genau der Grund für den GPU-Umstieg). Das ist eine inhärente, nicht
behebbare Grenze der Selbsttest-Methodik, kein Implementierungsfehler.

---

## Compute-Gating-Korrektheit

```python
def _verdict_carrying(n_surrogates: int, backend: str) -> tuple[bool, str]:
    if backend != "torch-cuda":
        return False, ...
    if n_surrogates < FULL_RESOLUTION_N_SURROGATES:  # 100_000
        return False, ...
    return True, "voller 100k-Surrogat-Lauf auf echtem CUDA-Device."
```
Exakt die geforderte harte UND-Bedingung (beide Kriterien müssen erfüllt sein,
sonst `False`). Verifiziert per Test `test_verdict_carrying_false_without_cuda_regardless_of_n`
(grün) und durch eigene Prüfung von `gpu_status('auto')` in dieser Sandbox
(`cuda_available: false` → `resolved_backend: "numpy"`, ehrlich, keine Vortäuschung).
`resolve_backend('cuda')` wirft `RuntimeError` statt still auf numpy zu degradieren,
wenn explizit CUDA angefordert wird — korrekt (kein „silent downgrade of an explicit
request", wie im Docstring versprochen).

---

## T1/T2-Payload-Felder — eigene Nachrechnung

An den konstruierten Test-Beispielen (`test_t1_holds_when_all_survivors_reproduce...`,
`test_t2_resolves_when_far_from_p_crit`, jeweils Positiv- UND Negativfall) nachvollzogen:
`evaluate_t1`/`evaluate_t2` lesen die 12 GL-006-Stage-1-Survivor-Zellen bzw. die 2
Lesart-Entscheidungszellen korrekt per `(window_index, label)`-Schlüssel aus dem neuen
Run-Payload, vergleichen gegen die transkribierte `GL006_BASELINE` (nur für die
p-Referenzanzeige, nicht für die Pass/Fail-Logik) und werten die vorregistrierten
Schwellen (`T1_P_MAX=1e-3`, `T2_MIN_SE_DISTANCE=5.0`) korrekt aus. Die
Non-Verdikt-Klausel-Zeichenkette („NICHT das GL-006-Verdikt", „aufloesungsbedingt
fragil") ist im T1-Payload wörtlich vorhanden und von einem „GL-006 wurde geändert"-
Missverständnis klar sprachlich abgegrenzt (`non_verdict_clause`-Feld, zusätzlich
im Markdown-Report als Blockquote am Dokumentanfang). Klare, unmissverständliche
Formulierung — keine Bugs gefunden.

---

## capital_free-Check

- Statischer Regex-Scan (`bps|edge_bps|friction|pnl|sharpe|net_edge|tradable`, alle
  Code-Dateien, String-Literale ausgeklammert) über das ganze Package UND
  `scripts/c18_leadlag_audit.py`: **kein Treffer** außerhalb der KAPITALFREI-
  Negations-Docstrings.
- Payload-Key-Scan (rekursiv über alle JSON-Keys eines echten `run()`-Aufrufs):
  kein `bps/edge/friction/pnl/sharpe/tradab`-Substring in irgendeinem Key.
- `payload["capital_free"] is True` in jedem Pfad (GL-006-Paar UND Nicht-GL-006-Paar).
- Selbst nachvollzogen (nicht nur Tests vertraut): eigener `grep -i` über das Package
  liefert dasselbe Ergebnis wie der Test — keine versteckten Tradability-Reste.

**Ergebnis: sauber, identisch zu GL-006.**

---

## T3-Runner-Check (`run_h18.sh`/`run_h18.ps1`)

- **Bug H-1** (s. oben): Selftest-Fehlschlag blockiert den GPU-Audit-Lauf NICHT,
  entgegen der eigenen Spezifikation im Kopfkommentar. Identisch in Bash UND
  PowerShell.
- Positiv: `H18_GPU_CHECK`-rc=3 (kein CUDA) wird korrekt als `SKIP` (nicht `FAIL`)
  behandelt, Gesamt-Exit-Code wird dann 2 (kein Fehler, aber Skip) statt 1 — sauber
  unterschieden von echten Fehlern.
  `HANDOFF_DRY_RUN`/`HANDOFF_DRY_RC`-Mechanik ist in beiden Skripten konsistent
  implementiert (Mechanik-Test ohne echte Läufe).
- `--db-copy` wird im Audit-Schritt korrekt verwendet (RW-Lock-Umgehung gegen den
  laufenden Collector, Schutzgut-konform).
- Timeout-Budget (`TMO_AUDIT=10800`, 3h) ist großzügig gegenüber der Registry-Schätzung
  (~1h auf RTX 5060 Ti) — vernünftiger Sicherheitspuffer.
- PowerShell: `$p.Handle`-Caching und `BelowNormal`-Priorität sind vorhanden (bekannte
  PS-5.1-Fallstricke bereits vermieden); `ExitCode`-null-Quirk wird abgefangen
  (`if ($null -eq $rc) { $rc = -2; ... }`).
- Der Skript-Default-Ausgabepfad (`DEFAULT_OUT = scinance2-impl/state`, in
  `scripts/c18_leadlag_audit.py`) ist identisch zum bereits etablierten Muster aus
  `scripts/c17_c41_lead_lag.py` — kein c18-spezifisches Risiko, aber: sollte jemand
  das Skript OHNE `--out` (also ohne den Runner) direkt aufrufen, landen
  `c18_leadlag_audit_results.{json,md}` im `state/`-Verzeichnis neben `gate_log.md`.
  Dateinamen kollidieren nicht, aber das ist eine Altlast des c17-Musters, keine
  neue c18-Einführung.

---

## Test-Abdeckung

`PYTHONPATH=src python3 -m pytest tests/unit/test_c18_leadlag_audit.py tests/unit/test_c17_c41_lead_lag.py -q`

```
...............................................................          [100%]
63 passed in 8.17s
```

**Echtes, selbst ausgeführtes Ergebnis: 63/63 grün, keine Skips, keine Warnings-als-Fehler.**
Beide Suiten (c18 UND die Regressionssuite der Originalpipeline c17_c41_lead_lag)
laufen ohne Fehler. Die c18-Suite deckt: Äquivalenz-Selbsttest (positiv + negativ-
Sanity), direkte TE-/WCOH-Batch-vs-Original-Vergleiche (Einzelzeile UND echter Batch
B>1), RNG-Konsumptions-Identität, `batch_circular_shift`-Identität zu `np.roll`,
Phase-Shuffle-Amplitudenerhaltung, Permutations-Marginalerhaltung, T1/T2 positiv+
negativ, GPU-Status-Ehrlichkeit, Backend-Resolution (inkl. Fehlerfall), Driver-E2E
(GL-006-Paar UND Nicht-GL-006-Paar), Markdown-Non-Verdikt-Klausel, Torch-freier
Import, BH-FDR-Objektidentität, KAPITALFREIHEIT (Code+Payload), Gate-Log-Schreib-
Guard, CLI-Plumbing (self-test/missing-source/missing-file/cuda-ohne-cuda). Kein
Coverage-Loch identifiziert, das für dieses Audit relevant wäre — die 100k-GPU-
Skalierung selbst ist naturgemäß nicht in der Sandbox testbar (T3-only), was das
Modul selbst korrekt als Grenze benennt.

---

## Zusammenfassung der Bug-Liste

| ID | Schweregrad | Ort | Kurzbeschreibung |
|---|---|---|---|
| H-1 | **HIGH** | `run_h18.sh` + `run_h18.ps1` | Voller GPU-Audit läuft auch bei fehlgeschlagenem Äquivalenz-Selftest — Kopfkommentar verspricht Abbruch, Code erzwingt ihn nicht |
| M-1 | MEDIUM | `scripts/c18_leadlag_audit.py` CLI-Ausgabe + beide Runner-`SUMMARY` | Datenbindungs-Status (`all_windows_match_gl006`) nicht in Kurzausgabe sichtbar; bei weiterwachsender Live-DB real riskant, dass H-18 unbemerkt auf verschobenen Fenstern statt den archivierten GL-006-Fenstern läuft |
| L-1 | LOW/informativ | `surrogate_gpu.py`/`__init__.py` Docstrings | „bit-identical ensemble"-Formulierung leicht irreführend — Offsets sind bit-identisch, abgeleitete TE-Statistik weicht ~1e-16 ab (bereits andernorts korrekt dokumentiert, p-Werte unverändert) |

Keine kritischen (CRITICAL) Bugs. Keine Registry-/Gate-Log-Verstöße.
