# Welle 1 (Scinance 3.0) - Laufreihenfolge auf der Nutzer-Maschine

Alle Runner: PowerShell 5.1, ASCII, oeffentliche Endpunkte, keine Keys,
keine Orders, kein Schreiben unter `data\harvest`. Jeder Runner endet mit
rc=0 (ok) oder rc!=0 (Vorbedingung verletzt - Ausgabe an den Orchestrator).
Vorher immer: `git pull origin claude/subagent-prd-development-T16fE`.

| Schritt | Befehl | Dauer | Liefert | Hochladen |
|---|---|---|---|---|
| 0 | `powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\vorfragen_v1_v4.ps1` | ~10 min | V-1 Funding-Tiefe, V-2 datierte Futures, V-3 Funding-Anker, V-5a Deribit-Verfallskalender (V-4 manuell aus dem Konto) | `handoff_local\results\vorfragen_*.txt` |
| 1 | `powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\run_wp9_dvol.ps1` | Minuten | DVOL-Tiefe (F1) und Quellen-Austauschbarkeit (F2, Befund a/b/nicht entscheidbar) | `scinance3-impl\state\wp9_<datum>\` |
| 2 | `powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\run_wp7_universe.ps1` | ~10 min Download + ~1 h Rechnen | K, SD_null, N_eff, sigma_xs, sigma_LS, rho(BTC,ETH), Spread je Dezil; Befund B1..B5 | Report-Verzeichnis laut Ausgabe (JSON+MD, NICHT den Panel-Store) |
| 3 | `powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\run_wp10a.ps1` | Minuten | Kohaerenz-Matrizen Stress/Ruhe, STRESS_REL/STRESS_ABS-Fixtures, Portfolio-Nulleffekt + Selektions-Decke | Report-Verzeichnis laut Ausgabe |
| 4 | `run_wp10b.ps1` (folgt nach Bau) | Stunden | Fill-Rate-Kurven, adv_sel | Report-Verzeichnis |

Reihenfolge ist Empfehlung, nicht Zwang - die Pakete sind unabhaengig.
Jeder Runner beginnt mit einer Probe (Feldnamen, Tiefe); bricht die Probe
ab, ist das ein Ergebnis (Ausgabe hochladen), kein Fehler des Nutzers.

Was NACH Welle 1 passiert, entscheidet der Orchestrator nach den Befunden
(PRD 3.0 Abschnitt 4 und 9.3): erst dann wird ein Alpha-Kandidat
registriert - niemals vorher.
