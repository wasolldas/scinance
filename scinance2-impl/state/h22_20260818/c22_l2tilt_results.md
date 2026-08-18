# H-22 — L2-TILT: Tages-Buchneigung vs. Folgetags-Rendite (KAPITALFREI)

- **Hypothese:** H-22 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-18T07:57:15+00:00 (UTC) · Status: RUN
- **Datenbindung:** WP-2-Tilt-Store + WP-0-Bar-Cache · `gate_valid=true`
- **Feature:** daily tilt = median of minute-sampled (B-A)/(B+A) within +-25 bp of mid (WP-2 store, frozen)
- **Null:** block bootstrap (5-day blocks, 1000 reps, seed 42), H0: IC <= 0, pairing broken under H0 with autocorrelation preserved
- **Gate:** BTC in BEIDEN L2-Fenstern IC >= 0.1 UND p <= 0.05 nach BH-FDR alpha=0.1 ueber F-L2; Abdeckungs-Floor 85%. Hartes Ein-Fenster-DROP. A-priori: DROP erwartet.

| Symbol | Fenster | urteilstragend | Tilt-Tage | Abdeckung | Floor | Paare | **IC** | >= 0,10 | boot-p | FDR | Zelle |
|---|---|:---:|---:|---:|:---:|---:|---:|:---:|---:|:---:|:---:|
| BTCUSDT | W-L2-1 | ja | 363 | 99.2% | ok | 363 | +0.0665 | nein | 0.0969 | nein | nein |
| BTCUSDT | W-L2-2 | ja | 340 | 93.2% | ok | 340 | -0.0112 | nein | 0.5704 | nein | nein |
| ETHUSDT | W-ETH | nein | 395 | 99.8% | ok | 395 | +0.0618 | nein | 0.1059 | — | — |

**BTC beide Fenster PASS:** nein · **Abdeckung ok:** ja

*Erzeugt von `c22_l2tilt/driver.py`. capital_free=true — die 1,7–2x-Notiz bleibt entkoppelt. Gate-Urteil: gate-auditor gegen H-22.*