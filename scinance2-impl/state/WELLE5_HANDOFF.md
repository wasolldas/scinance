# Welle 5 — Handoff für die Rückkehr

**An dich:** Kurzfassung dessen, was seit "Erst bugfix runde, dann gpu wave 5 start!"
autonom passiert ist, und was jetzt von dir gebraucht wird. Alles Folgende ist bereits
committed und auf `claude/subagent-prd-development-T16fE` gepusht.

## Was passiert ist (in einem Satz)

Zuerst wurden die 5 kritischen Befunde aus dem codebasisweiten Review behoben (Recorder,
S1/M15, OFI-SQL-Bug), dann sind die 5 GPU-Kandidaten aus deiner Forschungs-Shortlist
(PANEL-LAG, DSM-01, Time-Arrow-CNN, Venue-Fingerprint, GL-006-Power-Audit) vollständig als
Code implementiert, unabhängig geprüft und alle gefundenen Bugs behoben — bereit für deinen
ersten echten GPU-Lauf.

## Was du jetzt tun musst

1. Repo auf `claude/subagent-prd-development-T16fE` pullen.
2. Sicherstellen, dass `torch`/`torchvision`/`torchaudio` installiert sind (`pip install -e .[gpu]`,
   siehe `pyproject.toml`) und die RTX-GPU von PyTorch erkannt wird (`torch.cuda.is_available()`).
3. Read-only Harvester-Junction `data/harvest` wie gewohnt bereitstellen.
4. **Die 5 Runner NACHEINANDER starten** (keine Kohorten-Regel wie Welle 4 — VRAM-/
   Zeit-Konkurrenz um eine Karte). Empfohlene Reihenfolge nach GPU-Budget, günstigster zuerst:

   | Reihenfolge | Hypothese | Runner | Geschätztes Budget |
   |---|---|---|---|
   | 1 | H-18 (GL-006-Power-Audit) | `run_h18.{ps1,sh}` | ~1 Stunde |
   | 2 | H-16 (Time-Arrow-CNN) | `run_h16.{ps1,sh}` | Stunden (~145 Trainings) |
   | 3 | H-17 (Venue-Fingerprint) | `run_h17.{ps1,sh}` | ~1-2 Tage (~105 Trainings) |
   | 4 | H-15 (Trade-Tape-Grammatik) | `run_h15.{ps1,sh}` | Stunden (jetzt mit Resume) |
   | 5 | H-14 (PANEL-LAG) | `run_h14.{ps1,sh}` | ~2-3 Tage (~226 Trainings, teuerste) |

   Jeder Runner prüft zuerst per `--check-gpu-only`, ob CUDA verfügbar ist, und bricht sauber
   mit SKIP (exit 2) ab, falls nicht — kein stundenlanger, wertloser CPU-Smoke-Lauf.
5. Ergebnisse aus `handoff_local/results/h1X_<timestamp>/` in eine neue Session hochladen —
   die Auswertung gegen die Registry läuft dann automatisch.

**Wichtig — Checkpoint/Resume bei den zwei teuersten Läufen (H-14, H-15):** beide schreiben
Zwischenstände in einen STABILEN Checkpoint-Ordner (`results/h14_checkpoints/` bzw.
`results/h15_ckpt/`, env-überschreibbar). Ein Absturz/Timeout mitten im mehrtägigen Lauf
verliert dadurch NUR den gerade laufenden Job, nicht die bereits fertigen. Einfach denselben
Runner-Befehl erneut starten — er setzt automatisch fort. **Falls du vor dem produktiven Lauf
einen `--allow-cpu-fallback`/Mechanik-Smoketest machen willst: unbedingt einen ANDEREN
`--ckpt-dir` verwenden** (nicht den produktiven Ordner) — sonst würde der Provenienz-Check
(extra dafür eingebaut) den späteren echten Lauf zu Recht blockieren, weil er gemischte
CPU/GPU-Herkunft in den Checkpoints erkennt.

## Was inhaltlich passiert ist (Phasen A–E)

| Phase | Ergebnis |
|---|---|
| A — Registry-Brücke | H-14..H-18 wörtlich aus `GPU_RESEARCH_SCAN_2026-07-09.md` übernommen (DEC-24). |
| B — Bau | 5 Module, torch-optional (m18_patchtst-Muster), Compute-Gating gegen jeden CPU-Fallback-Pfad, T3-Runner, Tests — gegen synthetische Harvester-Bäume verifiziert. |
| C — Adversarial-Audit | 5 unabhängige, frische Fable-5-Prüfungen. Verdikte: H-14 PASS-WITH-NOTES (1 KRITISCH), H-15 "bedingt freigegeben" (2 HOCH), H-16 PASS (nur 2 NIEDRIG), H-17 PASS-WITH-NOTES (1 MEDIUM), H-18 PASS-WITH-NOTES (1 HOCH). Volltexte: `state/audit_h14.md`..`audit_h18.md`. |
| D — Fix-Loop | Alle Befunde behoben, erneut getestet, committed. |
| E — Konsolidierung | Vollregression (1095 Tests grün, keine neuen Regressionen), diese Handoff-Doku. |

## Der wichtigste Einzelbefund

H-14s Compute-Gating hatte eine kritische Lücke: beim Checkpoint-Resume wurde nie geprüft,
ob die zwischengespeicherten Trainingsergebnisse tatsächlich von echtem GPU-Training
stammten. Ein Lauf hätte `gate_valid=true` mit einem echten Verdikt liefern können, obwohl
die zugrunde liegenden ~226 Trainings teilweise aus einem CPU-Dummy-Testlauf im selben
(absichtlich stabilen) Checkpoint-Ordner stammten — der unabhängige Auditor hat das exakt
reproduziert. Genau die Frage, die diese Prüfrunde als höchste Priorität hatte ("darf ein
Lauf je verdikt-tragend sein ohne durchgängiges echtes CUDA-Training?"), war über diesen
Pfad verletzbar. Jetzt wird die `device`-Provenienz jedes einzelnen Checkpoints geprüft,
bevor ein Lauf als gate-gültig gilt.

## Bekannte offene Punkte (bewusst zurückgestellt, dokumentiert)

Keiner davon ist gate-relevant oder blockiert den ersten GPU-Lauf:

- H-16: `n_surrogates=0`-Randfall bei Fehlbedienung nicht explizit als methodisch-invalide
  markiert (betrifft nicht den Default-Pfad); capital_free-AST-Scan deckt nur das
  Modulverzeichnis ab, nicht Scripts/Runner (manuell verifiziert: sauber).
- H-17: Diagnose-Schwellenwert im Quantil-Normalisierungs-Test ist plausibel, aber nicht
  selbst als Registry-Zahl fixiert (rein informativ).

## Programmstand insgesamt

Vor Welle 5: 18 vorregistrierte Hypothesen (H-01..H-18, wobei H-18 ein Audit statt einer
neuen Hypothese ist), 9 DROP, 2 PARK, 2 kapitalfreie WEITER, 0 handelbare Kanten. Welle 4
(H-09..H-13) wartet weiterhin auf den ersten Datenlauf. Welle 5 fügt 5 neue, GPU-gebundene
Messfragen hinzu — der erste echte Lauf auf deiner RTX-Maschine liefert die ersten
Zahlen dazu.

## Vollständige Quellen

- `state/wave5_state.md` — Phasen-Log + Changelog mit allen Commit-Hashes.
- `state/audit_h14.md` .. `audit_h18.md` — volle Audit-Berichte.
- `state/decisions.md` — DEC-24 (Registry-Brücke).
- `state/GPU_RESEARCH_SCAN_2026-07-09.md` — die ursprüngliche Recherche-Shortlist.
- `handoff_local/README_H14.md` .. `README_H18.md` — technische Runner-Dokumentation je Modul.
