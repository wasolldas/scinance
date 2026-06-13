# C-42-Reproduktion (H-02 · Vol-Regression)

- **Hypothese:** H-02 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-13T01:16:44+00:00 (UTC)
- **Symbol:** BTCUSDT · **Modell:** `har` · Seed 42
- **Daten:** 51700 saubere Zeilen, 2 purged-WF-Fenster, Purge=60+Embargo 1440 Bars
- **Features:** 36 (1 DOCUMENTED, 35 ASSUMED)

## H-02-Kriterien (einzeln; Gate-Urteil faellt der gate-auditor)

| Kriterium (Registry, woertlich) | Operationalisierung | Messwert | erfuellt |
|---|---|---|---|
| OOS-R^2 >= 0.15 in ALLEN Fenstern | min Fold-R^2 >= 0.15 | 0.0126 (min) | nein |
| QLIKE schlaegt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold | 0.8172 vs 0.7255; 0.3229 vs 0.3507 | nein |
| purged Walk-Forward, >=2 disjunkte OOS-Fenster | Splitter deterministisch-chronologisch | 2 Fenster | ja |

**Pre-Check (nicht bindend):** BASELINE-ONLY

## Fenster-Metriken

| Fold | n_train | n_test | model R^2 | HAR R^2 | model QLIKE | HAR QLIKE | QLIKE<HAR | R^2>=0.15 |
|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 0 | 15733 | 17233 | 0.0126 | 0.0795 | 0.81721 | 0.72548 | nein | nein |
| 1 | 32966 | 17234 | 0.1926 | 0.1316 | 0.32294 | 0.35075 | ja | ja |

---
*Erzeugt von `scripts/c42_repro.py` (WP-4, read-only auf kline_1min). Endgueltiges Gate-Urteil: gate-auditor gegen H-02.*
