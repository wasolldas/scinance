# Nachrechnung des Orchestrators (unabhaengiges Skript, 2026-10-21): HF-RV-Nuisance, BTC, S1

Skript `scratchpad/orch_check/hfrv_spot.py` (nicht im Repo): eigene Extraktion von IV (DVOL-Stundenkerze 23:00 UTC, close/100),
RV_day aus 1-min-Schluessen (roh, mit Uebernacht-Anschluss an den letzten Schluss des Vortags) und close-to-close
(letzter 1-min-Schluss des UTC-Tags), RV_fwd30 = sqrt((365/30) sum_{k=1..30} RV_day(t+k)), S1 = 100 x (IV - RV_fwd30),
IV-Tage 2021-03-24..2024-05-01, Preise <= 2024-05-31 (assert). Kein Mittel ausgegeben.

| Groesse | Orchestrator | Herleitung (NUISANCE_HFRV.md) | H-27 (feasibility.json) |
|---|---:|---:|---:|
| n | 1.135 | 1.135 | 1.135 |
| SD S1, close-to-close | 18,597 | 18,60 | 18,60 |
| SD S1, 1-min roh | 18,579 | 18,58 | - |
| ACF 1 / 30 / 120, cc | 0,955 / -0,158 / 0,014 | - | 0,955 / -0,155 / 0,012 |
| ACF 1 / 30 / 120, 1-min | 0,967 / -0,043 / -0,002 | (-0,04..-0,05 bei Lag 30) | - |
| c cc: Bartlett 60/90/120; Batch-Means 60/90/120 | 16,9 / 17,4 / 17,8; 19,2 / 28,2 / 15,2 | - | 16,9 / 17,5 / 17,8; 19,2 / 28,2 / 15,2 |
| c cc nach Regel P-3 (max) | 28,2 | - | 28,17 |
| c 1-min: Bartlett 60/90/120; Batch-Means 60/90/120 | 20,4 / 21,6 / 21,2; 25,6 / 31,6 / 23,4 | - | - |
| c 1-min nach Regel P-3 (max) | 31,6 | 30,7..31,6 (je Variante) | - |
| rms RV30 cc (Niveau, zulaessig) | 61,55 % | - | 61,55 % |

Befund: Die Kernzahlen der Herleitung reproduzieren sich (SD auf 0,02 VP, c auf 0,1). Die HF-RV senkt die Streuung der
Praemie nicht (18,58 gegen 18,60) und hebt den Varianzfaktor (31,6 gegen 28,2), weil die negative Autokorrelation bei
Lag 30 der close-to-close-RV wegfaellt. Die UNBELEGT-Annahme "SD 15,1" (Review H-27 B-1, Bilanz Option 3) ist damit
widerlegt; Fensterlaengen aus der Bilanz (443 / 292 Tage) sind hinfaellig.
