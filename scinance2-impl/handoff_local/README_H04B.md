# H-04b - Handoff-Runner (T2, ca. 10-30 min)

## WAS laeuft

`run_h04b.ps1` (Windows) / `run_h04b.sh` (Linux/WSL) faehrt den
**C-17/C-41 Lead-Lag-TRADABILITY-Backtest** (H-04b) auf dem Paar BTC/ETH.

Es ist ein **historischer Backtest mit Kostenmodell** auf dem read-only
`trades`-Bestand: die in H-04 (GL-006) messbar bestaetigte gerichtete
Lead-Lag-Information BTC->ETH (Survivor-Lags 1-3 s) wird gegen einen
realistischen Latenz-Haircut und die verbindliche 11-bps-Friction-Wand
gestellt - traegt sie eine handelbare Netto-Kante?

Bloecke (Reihenfolge fest; jeder einzeln gekapselt: try/catch + Timeout
1800 s + weitermachen, NIE ein offener Prompt):

1. **H04B_PRIMARY** - URTEILSTRAGEND. `latency=300ms`, `friction=11bps`,
   Taker, `windows=2`, `lags=1,2,3`, `bootstrap=200`, `seed=42`,
   `grid-ms=1000`, `max-ticks-per-window=150000`, `--db-copy`. Der EINZIGE
   Punkt, an dem das Pass-Urteil faellt (`gate_valid_assumptions=true`).
2. **H04B_LAT100** - ROBUSTHEIT (NICHT urteilstragend). Wie Primaer, aber
   `latency=100ms`.
3. **H04B_LAT500** - ROBUSTHEIT (NICHT urteilstragend). Wie Primaer, aber
   `latency=500ms`.
4. **H04B_MAKER** - SEKUNDAER (NICHT urteilstragend). Wie Primaer plus
   `--maker-secondary` (adverse-selection-vorbehaltlich).

## KAPITALFREIHEIT - die Umkehrung (zentraler Unterschied zu H-04)

H-04 (und H-05/H-06) waren **kapitalfrei** (`capital_free=true`) - reine
Mess-Gates ohne Friction-Vergleich. **H-04b ist die erste NICHT-kapitalfreie
Hypothese des Programms** (`capital_free=false`): das Gate **MUSS** die
Friction-Wand (11 bps Taker) und den Latenz-Haircut (300 ms) konfrontieren.

**Wichtig (CLAUDE.md Par.4 / Autonomie-Protokoll Par.3):** "capital_free=false"
markiert NUR, dass das Gate Edge-bps gegen Friction/Latenz misst -
**NICHT**, dass Kapital eingesetzt oder eine Live-Order gesendet wird. H-04b
bleibt ein historischer Backtest auf dem read-only `trades`-Bestand:
**KEIN Live-Order-Code, KEIN echtes Geld.** Es ist Falsifikations-Pipeline,
exakt PRD-/CLAUDE.md-konform.

## A-priori = PARK (PRD Paragraf 4)

Die Verfassungs-Vorhersage (PRD Par.4 Z.133, woertlich) lautet fuer das
C-17/C-41-Cross-Sectional-Gate: *"keine handelbare Kante (abgegraste
30-60s-HFT-Anomalie) -> bleibt PARK"*. Der **starke A-priori der Verfassung
ist DROP/PARK**; der erwartete Ausgang ist PARK. Das Gate ist bewusst NICHT
so konstruiert, dass es das WEITER von H-04 "nachbestaetigt" - **WEITER muss
schwer und ehrlich sein**.

DROP/PARK-Kriterium ist hart und Ein-Fenster (PRD Par.8.5): Netto-Edge
<= 0 in >= 1 Fenster ODER nicht statistisch > 0 (FDR-`p > 0.05`) -> PARK.
Kein GRAUBEREICH, kein Graubereich-Nachschieben.

## Anti-Gaming-Klausel (VERBINDLICH - Torpfosten-Schutz)

Das Pass-Urteil faellt **AUSSCHLIESSLICH am H04B_PRIMARY-Punkt**
(`latency=300ms`, `friction=11bps`, Taker, Latenz-Haircut angewandt) -
dem einzigen Lauf mit `gate_valid_assumptions=true`.

Die drei anderen Bloecke (H04B_LAT100, H04B_LAT500, H04B_MAKER) sind
**Robustheits-/Sekundaer-Laeufe - NICHT urteilstragend**. Sie sind als
Sensitivitaets-Spanne MIT-berichtet, setzen aber `gate_valid_assumptions=false`
im Output und **duerfen ein WEITER NICHT erzwingen**:

- Eine kuerzere Latenz (100 ms) darf das WEITER nicht erzwingen.
- Der Maker-Sekundaerfall ist adverse-selection-anfaellig (Maker-Fills auf
  einem 1-3s-Lead-Signal werden bevorzugt gefuellt, wenn man falsch liegt)
  und ist NIE das Primaer-Pass-Kriterium; ein Maker-WEITER bei Taker-DROP
  wird als "adverse-selection-vorbehaltlich, nicht handelbar bestaetigt"
  markiert.

Wer eine andere Latenz/Wand fuer plausibel haelt, registriert eine NEUE
Hypothese (H-04c) - er verschiebt NICHT dieses Gate (Registry-Disziplin Par.2).

## WIE LANGE

Ca. 10-30 min je nach Daten-Tiefe der lokalen DuckDB. Vier Laeufe a max.
30 min Timeout; der Daten-Cap (`max-ticks-per-window=150000`) deckelt die
Arbeitslast deterministisch, daher typischerweise deutlich schneller.

## Voraussetzungen

- Lokale DuckDB mit `trades`-Tabelle. Default-Pfad ist
  `data/bybit_edge.duckdb` relativ zum Repo-Root. Override:
  `HANDOFF_DUCKDB=<pfad>`.
- Python-Umgebung mit `numpy`, `scipy`, `duckdb` (Standard-Repo-`pyproject`
  zieht alles mit).
- Windows: vor laengeren Laeufen ggf. `powercfg /change standby-timeout-ac 0`.

## Aufruf

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\run_h04b.ps1
```

```bash
# Linux / WSL
bash run_h04b.sh
```

## WO Ergebnisse landen

`scinance2-impl/handoff_local/results/h04b_<timestamp>/`:

- `SUMMARY_<datum>.md` - Block-Tabelle mit Rolle (urteilstragend vs.
  Robustheit/Sekundaer), Status je Block, Anti-Gaming-Hinweis. Grundlage
  der Morgen-Auswertung.
- `h04b/c17_c41_tradability_results.json` + `.md` - URTEILSTRAGENDER
  Driver-Output (300ms/11bps/Taker), `gate_valid_assumptions=true`.
- `h04b_lat100/`, `h04b_lat500/`, `h04b_maker/` - die Robustheits-/Sekundaer-
  Outputs (`gate_valid_assumptions=false`), je `c17_c41_tradability_results.json` + `.md`.
- `steps.tsv` - eine Zeile je Block (Name, Status, Rc, Dauer, Detail).
- `summary.txt` - einzeilige Block-Zusammenfassung + Exit-Code.
- `<BLOCK>.log` / `<BLOCK>.err.log` - stdout/stderr je Schritt.

Exit-Code: 0 = alle OK, 1 = mind. ein FAIL, 2 = kein FAIL aber SKIP
(z.B. DuckDB fehlt).

**Ergebnisse hochladen -> gate-auditor gegen H-04b.** Den Inhalt von
`handoff_local/results/h04b_<ts>/` in die Session hochladen; der gate-auditor
wertet ihn gegen den registrierten H-04b-Eintrag aus (hartes Ein-Fenster-
PARK-Kriterium, Anti-Gaming-Klausel - WEITER nur am H04B_PRIMARY-Punkt).

## Dry-Run

Mechanik-Test ohne echte Laeufe (keine Python-Subprozesse):

```bash
HANDOFF_DRY_RUN=1 bash run_h04b.sh
HANDOFF_DRY_RUN=1 HANDOFF_DRY_RC=1 bash run_h04b.sh   # Mechanik mit FAILs
```

```powershell
$env:HANDOFF_DRY_RUN=1; powershell -ExecutionPolicy Bypass -File .\run_h04b.ps1
```
