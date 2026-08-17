# H-19 — DRIFT: Stationaritaet der Tape-Struktur (META/AUDIT, KAPITALFREI)

- **Hypothese:** H-19 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-17T08:35:01+00:00 (UTC) · Status: RUN
- **Semantik:** META/AUDIT (H-18-Muster): kein WEITER/DROP; DRIFT-BEFUND je Zelle loest die registrierte Regime-Splitting-Auflage aus
- **Datenbindung:** WP-0-Bar-Cache, Fingerabdruecke OK · `gate_valid=true`
- **Fenster:** L=2021-06-29..2022-12-31 (deskriptiv) | OOS1=2023-01-01..2024-06-30 | OOS2=2024-07-01..2025-12-31
- **Befund-Regel:** |rho_p| >= 0.3 in BOTH OOS windows, same sign (magnitude-driven; p report-only)

## Befunde (3 Deskriptoren x 5 Symbole)

| Symbol | Deskriptor | rho_p OOS1 | rho_p OOS2 | **DRIFT-BEFUND** |
|---|---|---:|---:|:---:|
| BTCUSDT | D1_lag1_ac | -0.0755 | +0.0804 | nein |
| BTCUSDT | D2_variance_signature | -0.0996 | +0.2524 | nein |
| BTCUSDT | D3_herfindahl | -0.3297 | +0.0561 | nein |
| ETHUSDT | D1_lag1_ac | -0.0857 | -0.0929 | nein |
| ETHUSDT | D2_variance_signature | -0.0691 | -0.0386 | nein |
| ETHUSDT | D3_herfindahl | -0.4650 | +0.0210 | nein |
| XRPUSDT | D1_lag1_ac | -0.1303 | +0.0795 | nein |
| XRPUSDT | D2_variance_signature | -0.1768 | +0.1383 | nein |
| XRPUSDT | D3_herfindahl | -0.0496 | -0.1585 | nein |
| SOLUSDT | D1_lag1_ac | -0.0578 | -0.0491 | nein |
| SOLUSDT | D2_variance_signature | -0.2071 | -0.0390 | nein |
| SOLUSDT | D3_herfindahl | -0.4872 | +0.0915 | nein |
| BNBUSDT | D1_lag1_ac | -0.1530 | +0.0454 | nein |
| BNBUSDT | D2_variance_signature | -0.1759 | +0.0562 | nein |
| BNBUSDT | D3_herfindahl | -0.2896 | -0.0942 | nein |

**DRIFT-Befunde gesamt: 0 von 15.** Jeder Befund loest die registrierte Regime-Splitting-Auflage fuer nachfolgende Welle-6-Auswertungen aus.

## Zellen (alle Fenster; p/KI nicht urteilstragend)

| Symbol | Deskriptor | Fenster | n | rho_p | >=0,30 | Rotations-p | KI90 | FDR-Report |
|---|---|---|---:|---:|:---:|---:|---|:---:|
| BTCUSDT | D1_lag1_ac | L | 551 | -0.1144 | nein | 0.3726 | [-0.090, +0.098] | — |
| BTCUSDT | D2_variance_signature | L | 551 | -0.0927 | nein | 0.4146 | [-0.080, +0.079] | — |
| BTCUSDT | D3_herfindahl | L | 551 | +0.2527 | nein | 0.0010 | [-0.087, +0.093] | — |
| BTCUSDT | D1_lag1_ac | OOS1 | 547 | -0.0755 | nein | 0.2527 | [-0.081, +0.076] | nein |
| BTCUSDT | D2_variance_signature | OOS1 | 547 | -0.0996 | nein | 0.5445 | [-0.090, +0.085] | nein |
| BTCUSDT | D3_herfindahl | OOS1 | 547 | -0.3297 | ja | 0.0070 | [-0.090, +0.087] | nein |
| BTCUSDT | D1_lag1_ac | OOS2 | 549 | +0.0804 | nein | 0.4076 | [-0.084, +0.085] | nein |
| BTCUSDT | D2_variance_signature | OOS2 | 549 | +0.2524 | nein | 0.0380 | [-0.084, +0.087] | nein |
| BTCUSDT | D3_herfindahl | OOS2 | 549 | +0.0561 | nein | 0.7493 | [-0.094, +0.084] | nein |
| ETHUSDT | D1_lag1_ac | L | 551 | -0.0259 | nein | 0.7453 | [-0.093, +0.092] | — |
| ETHUSDT | D2_variance_signature | L | 551 | -0.0439 | nein | 0.4106 | [-0.083, +0.083] | — |
| ETHUSDT | D3_herfindahl | L | 551 | +0.0042 | nein | 0.9940 | [-0.083, +0.087] | — |
| ETHUSDT | D1_lag1_ac | OOS1 | 547 | -0.0857 | nein | 0.1728 | [-0.077, +0.079] | nein |
| ETHUSDT | D2_variance_signature | OOS1 | 547 | -0.0691 | nein | 0.5005 | [-0.083, +0.081] | nein |
| ETHUSDT | D3_herfindahl | OOS1 | 547 | -0.4650 | ja | 0.0809 | [-0.109, +0.112] | nein |
| ETHUSDT | D1_lag1_ac | OOS2 | 549 | -0.0929 | nein | 0.2418 | [-0.090, +0.085] | nein |
| ETHUSDT | D2_variance_signature | OOS2 | 549 | -0.0386 | nein | 0.6264 | [-0.088, +0.085] | nein |
| ETHUSDT | D3_herfindahl | OOS2 | 549 | +0.0210 | nein | 0.8811 | [-0.101, +0.096] | nein |
| XRPUSDT | D1_lag1_ac | L | 551 | -0.2009 | nein | 0.0749 | [-0.091, +0.093] | — |
| XRPUSDT | D2_variance_signature | L | 551 | -0.1877 | nein | 0.0010 | [-0.077, +0.077] | — |
| XRPUSDT | D3_herfindahl | L | 551 | +0.3602 | ja | 0.0010 | [-0.099, +0.091] | — |
| XRPUSDT | D1_lag1_ac | OOS1 | 547 | -0.1303 | nein | 0.1918 | [-0.078, +0.084] | nein |
| XRPUSDT | D2_variance_signature | OOS1 | 547 | -0.1768 | nein | 0.2188 | [-0.084, +0.083] | nein |
| XRPUSDT | D3_herfindahl | OOS1 | 547 | -0.0496 | nein | 0.7682 | [-0.096, +0.083] | nein |
| XRPUSDT | D1_lag1_ac | OOS2 | 549 | +0.0795 | nein | 0.2048 | [-0.083, +0.084] | nein |
| XRPUSDT | D2_variance_signature | OOS2 | 549 | +0.1383 | nein | 0.0609 | [-0.081, +0.085] | nein |
| XRPUSDT | D3_herfindahl | OOS2 | 549 | -0.1585 | nein | 0.5774 | [-0.097, +0.089] | nein |
| SOLUSDT | D1_lag1_ac | L | 551 | +0.0110 | nein | 0.9481 | [-0.100, +0.097] | — |
| SOLUSDT | D2_variance_signature | L | 551 | +0.0108 | nein | 0.7912 | [-0.080, +0.074] | — |
| SOLUSDT | D3_herfindahl | L | 551 | +0.3803 | ja | 0.0330 | [-0.101, +0.108] | — |
| SOLUSDT | D1_lag1_ac | OOS1 | 547 | -0.0578 | nein | 0.5135 | [-0.093, +0.085] | nein |
| SOLUSDT | D2_variance_signature | OOS1 | 547 | -0.2071 | nein | 0.2667 | [-0.089, +0.082] | nein |
| SOLUSDT | D3_herfindahl | OOS1 | 547 | -0.4872 | ja | 0.0639 | [-0.106, +0.109] | nein |
| SOLUSDT | D1_lag1_ac | OOS2 | 549 | -0.0491 | nein | 0.4645 | [-0.092, +0.092] | nein |
| SOLUSDT | D2_variance_signature | OOS2 | 549 | -0.0390 | nein | 0.4535 | [-0.082, +0.081] | nein |
| SOLUSDT | D3_herfindahl | OOS2 | 549 | +0.0915 | nein | 0.3976 | [-0.087, +0.086] | nein |
| BNBUSDT | D1_lag1_ac | L | 551 | -0.0804 | nein | 0.5644 | [-0.094, +0.097] | — |
| BNBUSDT | D2_variance_signature | L | 551 | -0.1418 | nein | 0.2967 | [-0.078, +0.085] | — |
| BNBUSDT | D3_herfindahl | L | 551 | +0.4867 | ja | 0.0290 | [-0.113, +0.106] | — |
| BNBUSDT | D1_lag1_ac | OOS1 | 547 | -0.1530 | nein | 0.1828 | [-0.089, +0.083] | nein |
| BNBUSDT | D2_variance_signature | OOS1 | 547 | -0.1759 | nein | 0.1918 | [-0.097, +0.094] | nein |
| BNBUSDT | D3_herfindahl | OOS1 | 547 | -0.2896 | nein | 0.0380 | [-0.090, +0.093] | nein |
| BNBUSDT | D1_lag1_ac | OOS2 | 549 | +0.0454 | nein | 0.3766 | [-0.096, +0.091] | nein |
| BNBUSDT | D2_variance_signature | OOS2 | 549 | +0.0562 | nein | 0.2597 | [-0.082, +0.080] | nein |
| BNBUSDT | D3_herfindahl | OOS2 | 549 | -0.0942 | nein | 0.1848 | [-0.086, +0.079] | nein |

*Erzeugt von `c19_drift/driver.py` — liest AUSSCHLIESSLICH den WP-0-Bar-Cache. capital_free=true. META/AUDIT: der gate-auditor protokolliert den Befund; es gibt kein WEITER/DROP.*