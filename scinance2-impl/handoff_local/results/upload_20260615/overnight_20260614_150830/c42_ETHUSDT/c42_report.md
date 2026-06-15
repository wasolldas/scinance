# C-42-Reproduktion (H-02 · Vol-Regression)

- **Hypothese:** H-02 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-14T15:13:51+00:00 (UTC)
- **Symbol:** ETHUSDT · **Modell:** `lightgbm` · Seed 42
- **Daten:** 51700 saubere Zeilen, 3 purged-WF-Fenster, Purge=60+Embargo 1440 Bars
- **Features:** 36 (1 DOCUMENTED, 35 ASSUMED)

## H-02-Kriterien (einzeln; Gate-Urteil faellt der gate-auditor)

| Kriterium (Registry, woertlich) | Operationalisierung | Messwert | erfuellt |
|---|---|---|---|
| OOS-R^2 >= 0.15 in ALLEN Fenstern | min Fold-R^2 >= 0.15 | -0.1470 (min) | nein |
| QLIKE schlaegt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold | 0.8989 vs 0.6203; 0.4532 vs 0.5862; 0.3421 vs 0.3546 | nein |
| purged Walk-Forward, >=2 disjunkte OOS-Fenster | Splitter deterministisch-chronologisch | 3 Fenster | ja |
| FDR BH alpha=0.10 ueber 36 Features (F-VOL) | BH step-up ueber Permutations-p | 0/36 signifikant | n/a (Reporting) |

**Pre-Check (nicht bindend):** DROP/PARK

## Fenster-Metriken

| Fold | n_train | n_test | model R^2 | HAR R^2 | model QLIKE | HAR QLIKE | QLIKE<HAR | R^2>=0.15 |
|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 0 | 11425 | 12925 | 0.2494 | 0.3704 | 0.89887 | 0.62030 | nein | ja |
| 1 | 24350 | 12925 | 0.1184 | 0.1135 | 0.45322 | 0.58623 | ja | nein |
| 2 | 37275 | 12925 | -0.1470 | 0.0481 | 0.34206 | 0.35457 | ja | nein |

## FDR (F-VOL, BH alpha=0.10) — signifikante Features

- keine Features ueberleben BH alpha=0.10

---
*Erzeugt von `scripts/c42_repro.py` (WP-4, read-only auf kline_1min). Endgueltiges Gate-Urteil: gate-auditor gegen H-02.*
