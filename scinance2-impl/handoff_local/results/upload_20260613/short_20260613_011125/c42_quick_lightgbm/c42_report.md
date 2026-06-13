# C-42-Reproduktion (H-02 · Vol-Regression)

- **Hypothese:** H-02 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-13T01:17:48+00:00 (UTC)
- **Symbol:** BTCUSDT · **Modell:** `lightgbm` · Seed 42
- **Daten:** 51700 saubere Zeilen, 2 purged-WF-Fenster, Purge=60+Embargo 1440 Bars
- **Features:** 36 (1 DOCUMENTED, 35 ASSUMED)

## H-02-Kriterien (einzeln; Gate-Urteil faellt der gate-auditor)

| Kriterium (Registry, woertlich) | Operationalisierung | Messwert | erfuellt |
|---|---|---|---|
| OOS-R^2 >= 0.15 in ALLEN Fenstern | min Fold-R^2 >= 0.15 | -0.2035 (min) | nein |
| QLIKE schlaegt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold | 0.4524 vs 0.7255; 0.3473 vs 0.3507 | ja |
| purged Walk-Forward, >=2 disjunkte OOS-Fenster | Splitter deterministisch-chronologisch | 2 Fenster | ja |
| FDR BH alpha=0.10 ueber 36 Features (F-VOL) | BH step-up ueber Permutations-p | 0/36 signifikant | n/a (Reporting) |

**Pre-Check (nicht bindend):** DROP/PARK

## Fenster-Metriken

| Fold | n_train | n_test | model R^2 | HAR R^2 | model QLIKE | HAR QLIKE | QLIKE<HAR | R^2>=0.15 |
|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 0 | 15733 | 17233 | 0.2659 | 0.0795 | 0.45237 | 0.72548 | ja | ja |
| 1 | 32966 | 17234 | -0.2035 | 0.1316 | 0.34729 | 0.35075 | ja | nein |

## FDR (F-VOL, BH alpha=0.10) — signifikante Features

- keine Features ueberleben BH alpha=0.10

---
*Erzeugt von `scripts/c42_repro.py` (WP-4, read-only auf kline_1min). Endgueltiges Gate-Urteil: gate-auditor gegen H-02.*
