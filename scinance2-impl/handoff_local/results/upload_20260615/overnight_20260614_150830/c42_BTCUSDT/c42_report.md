# C-42-Reproduktion (H-02 · Vol-Regression)

- **Hypothese:** H-02 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-14T15:11:21+00:00 (UTC)
- **Symbol:** BTCUSDT · **Modell:** `lightgbm` · Seed 42
- **Daten:** 51700 saubere Zeilen, 3 purged-WF-Fenster, Purge=60+Embargo 1440 Bars
- **Features:** 36 (1 DOCUMENTED, 35 ASSUMED)

## H-02-Kriterien (einzeln; Gate-Urteil faellt der gate-auditor)

| Kriterium (Registry, woertlich) | Operationalisierung | Messwert | erfuellt |
|---|---|---|---|
| OOS-R^2 >= 0.15 in ALLEN Fenstern | min Fold-R^2 >= 0.15 | -0.3212 (min) | nein |
| QLIKE schlaegt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold | 0.5566 vs 0.7477; 0.3876 vs 0.4921; 0.3321 vs 0.3275 | nein |
| purged Walk-Forward, >=2 disjunkte OOS-Fenster | Splitter deterministisch-chronologisch | 3 Fenster | ja |
| FDR BH alpha=0.10 ueber 36 Features (F-VOL) | BH step-up ueber Permutations-p | 0/36 signifikant | n/a (Reporting) |

**Pre-Check (nicht bindend):** DROP/PARK

## Fenster-Metriken

| Fold | n_train | n_test | model R^2 | HAR R^2 | model QLIKE | HAR QLIKE | QLIKE<HAR | R^2>=0.15 |
|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 0 | 11425 | 12925 | 0.4699 | 0.3350 | 0.55664 | 0.74771 | ja | ja |
| 1 | 24350 | 12925 | -0.0808 | 0.1780 | 0.38763 | 0.49212 | ja | nein |
| 2 | 37275 | 12925 | -0.3212 | 0.0656 | 0.33209 | 0.32752 | nein | nein |

## FDR (F-VOL, BH alpha=0.10) — signifikante Features

- keine Features ueberleben BH alpha=0.10

---
*Erzeugt von `scripts/c42_repro.py` (WP-4, read-only auf kline_1min). Endgueltiges Gate-Urteil: gate-auditor gegen H-02.*
