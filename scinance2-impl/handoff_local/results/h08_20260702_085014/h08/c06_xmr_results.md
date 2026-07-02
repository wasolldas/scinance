# C-06 Cross-Sectional Ergodic Mean-Reversion — H-08 Mess-Gate (KAPITALFREI)

- **Hypothese:** H-08 — `scinance2-impl/state/hypothesis_registry.md`
- **Über-Dehnungs-Modus:** rank — Achse A = Rang-1-Symbol je Bar (argmax |z|, schwellen-frei, DEC-18)
- **Erzeugt:** 2026-07-02T08:51:23+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade (windows 2026-04-15 + 2026-05-15)` (Panel: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT)
- **Fenster (vorregistriert):** A@2026-04-15, B@2026-05-15 · Bars/Fenster: [576, 576]
- **L=12 Bars · Z_THRESH=entfällt (Rang-Modus) · Crash-Dezil=0.9 · Panel-RV=3 Bars · Horizonte=[1, 3, 6] Bars**
- **Surrogates=200 · Bootstrap=1000 · N-Floor=30 · Seed=42**
- **FDR-Familie:** F-XMR-RANK · **BH-FDR α:** 0.1 · **p_crit:** 0.0000
- **KAPITALFREI:** ja — reiner Mess-/Verstärkungs-Test, keine bps/Edge/PnL/Sharpe.

> Gate-Urteil fällt der gate-auditor gegen H-08. WEITER verlangt (ALLE gemeinsam): konditioniert μ_rev>0 UND p≤0.05 (BH-FDR F-XMR-RANK) UND ≥2-Fenster-Konsistenz UND nicht-überlappende 95%-Bootstrap-CIs (konditioniert > Baseline) für ≥1 Horizont in ≥2 Fenstern UND N≥30/Fenster. Nicht-Trivialitäts-Anker: konditioniert MUSS echt stärker revertieren als der unkonditionierte Baseline (E-04-/§6-verbotene Trivial-MR zählt NIE als Erfolg). Hartes Ein-Fenster-DROP, kein GRAUBEREICH.

## Verstärkungs-Rollup je Horizont (Gate-Kern)

| Horizont (Bars) | Fenster gemessen | bestehende Fenster | amplified_consistent (≥2) |
|---:|---:|---|---|
| 1 | 2 | [] | nein |
| 3 | 2 | [] | nein |
| 6 | 2 | [] | nein |

**any_amplified_consistent:** nein · **FDR-signifikante Zellen:** 0

## Detail je Fenster × Horizont × {konditioniert | Baseline}

| Fenster | h | Art | μ_rev | CI_low | CI_high | N | surr_p | FDR-sig | Δμ | CI-nicht-überlappend | N-Floor |
|---|---:|---|---:|---:|---:|---:|---:|:---:|---:|:---:|:---:|
| A@2026-04-15 | 1 | kond | 0.000089 | -0.000029 | 0.000202 | 504 | 0.1542 | nein | 0.000081 | nein | ja |
| A@2026-04-15 | 1 | base | 0.000007 | -0.000036 | 0.000051 | 2815 | — | — | — | — | — |
| A@2026-04-15 | 3 | kond | 0.000222 | -0.000058 | 0.000482 | 504 | 0.0796 | nein | 0.000164 | nein | ja |
| A@2026-04-15 | 3 | base | 0.000058 | -0.000025 | 0.000144 | 2805 | — | — | — | — | — |
| A@2026-04-15 | 6 | kond | 0.000230 | -0.000466 | 0.000850 | 501 | 0.2537 | nein | 0.000108 | nein | ja |
| A@2026-04-15 | 6 | base | 0.000123 | -0.000002 | 0.000252 | 2790 | — | — | — | — | — |
| B@2026-05-15 | 1 | kond | 0.000036 | -0.000039 | 0.000118 | 508 | 0.3881 | nein | 0.000018 | nein | ja |
| B@2026-05-15 | 1 | base | 0.000018 | -0.000018 | 0.000056 | 2815 | — | — | — | — | — |
| B@2026-05-15 | 3 | kond | 0.000066 | -0.000119 | 0.000239 | 508 | 0.6219 | nein | -0.000026 | nein | ja |
| B@2026-05-15 | 3 | base | 0.000093 | 0.000019 | 0.000168 | 2805 | — | — | — | — | — |
| B@2026-05-15 | 6 | kond | -0.000076 | -0.000462 | 0.000261 | 505 | 0.9453 | nein | -0.000221 | nein | ja |
| B@2026-05-15 | 6 | base | 0.000145 | 0.000047 | 0.000244 | 2790 | — | — | — | — | — |

*Erzeugt von `c06_xmr/driver.py` (read-only Harvester-Backfill, DEC-15/DEC-17/DEC-18). capital_free=true. Endgültiges Gate-Urteil: gate-auditor gegen H-08.*