# C-01 OFI-Vorzeichen-Mess-Gate (H-05 · INC-02-Anker, KAPITALFREI)

- **Hypothese:** H-05 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-17T09:09:42+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::trades` (Symbole: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT)
- **Fenster:** 2 · **Surrogates:** 200 · **Seed:** 42 · **BH-FDR alpha:** 0.1
- **Grid:** 1000 ms · **delta-Lags:** [1, 5, 15, 60, 300] s · **Tick-Cap/Fenster:** 150000
- **KAPITALFREI:** ja — reiner Vorzeichen-/Korrelations-Mess-Test, KEINE bps/Edge/PnL/Sharpe/Friction-Metrik.

> Der Report liefert jedes Gate-Kriterium EINZELN je Fenster/delta/Symbol. `sign_direction` (+/-/0) und `inverse_significant` sind NEUTRAL gemeldet — ein signifikant INVERSES Vorzeichen ist KEIN H-05-Bestehen, sondern Ausloeser fuer eine separate H-05b (MM-Replenishment). Das GATE-URTEIL (WEITER/DROP/H-05b) faellt der gate-auditor gegen H-05 (hartes Ein-Fenster-Kriterium, PRD §8.5).

**F-OFI BH-FDR p_crit:** 0.0050 · **FDR-signifikante Varianten:** 3
**Beobachtung (NEUTRAL):** inverse Richtung irgendwo signifikant: ja · nicht-positives Vorzeichen in >=1 Fenster: ja

| Symbol | Fenster | delta (s) | n | corr | sign | \|corr\| | Hit-Rate | Surr p | FDR sig | Magnitude-Floor | pos.+konsistent | inverse_sig |
|---|---:|---:|---:|---:|:--:|---:|---:|---:|:--:|:--:|:--:|:--:|
| BTCUSDT | 0 | 1 | 3977 | -0.0101 | - | 0.0101 | 0.495 | 0.5075 | nein | nein | nein | nein |
| BTCUSDT | 0 | 5 | 3973 | -0.0355 | - | 0.0355 | 0.480 | 0.0249 | nein | nein | nein | nein |
| BTCUSDT | 0 | 15 | 3963 | -0.0287 | - | 0.0287 | 0.497 | 0.0896 | nein | nein | nein | nein |
| BTCUSDT | 0 | 60 | 3918 | -0.0235 | - | 0.0235 | 0.495 | 0.1144 | nein | nein | nein | nein |
| BTCUSDT | 0 | 300 | 3678 | 0.0008 | + | 0.0008 | 0.501 | 0.9701 | nein | nein | nein | nein |
| BTCUSDT | 1 | 1 | 3977 | 0.0072 | + | 0.0072 | 0.537 | 0.5871 | nein | ja | nein | nein |
| BTCUSDT | 1 | 5 | 3973 | 0.0044 | + | 0.0044 | 0.525 | 0.7662 | nein | nein | nein | nein |
| BTCUSDT | 1 | 15 | 3963 | 0.0134 | + | 0.0134 | 0.510 | 0.3881 | nein | nein | nein | nein |
| BTCUSDT | 1 | 60 | 3918 | 0.0011 | + | 0.0011 | 0.500 | 0.9403 | nein | nein | nein | nein |
| BTCUSDT | 1 | 300 | 3678 | -0.0098 | - | 0.0098 | 0.514 | 0.4826 | nein | nein | nein | nein |
| ETHUSDT | 0 | 1 | 3874 | -0.0550 | - | 0.0550 | 0.490 | 0.0050 | ja | ja | nein | ja |
| ETHUSDT | 0 | 5 | 3870 | -0.0291 | - | 0.0291 | 0.492 | 0.0597 | nein | nein | nein | nein |
| ETHUSDT | 0 | 15 | 3860 | -0.0366 | - | 0.0366 | 0.498 | 0.0199 | nein | nein | nein | nein |
| ETHUSDT | 0 | 60 | 3815 | -0.0306 | - | 0.0306 | 0.516 | 0.0547 | nein | nein | nein | nein |
| ETHUSDT | 0 | 300 | 3575 | -0.0125 | - | 0.0125 | 0.520 | 0.4129 | nein | nein | nein | nein |
| ETHUSDT | 1 | 1 | 3875 | -0.0299 | - | 0.0299 | 0.545 | 0.0448 | nein | ja | nein | nein |
| ETHUSDT | 1 | 5 | 3871 | -0.0305 | - | 0.0305 | 0.501 | 0.0697 | nein | nein | nein | nein |
| ETHUSDT | 1 | 15 | 3861 | -0.0196 | - | 0.0196 | 0.499 | 0.2139 | nein | nein | nein | nein |
| ETHUSDT | 1 | 60 | 3816 | -0.0053 | - | 0.0053 | 0.497 | 0.7413 | nein | nein | nein | nein |
| ETHUSDT | 1 | 300 | 3576 | -0.0398 | - | 0.0398 | 0.488 | 0.0249 | nein | nein | nein | nein |
| SOLUSDT | 0 | 1 | 21116 | 0.0160 | + | 0.0160 | 0.511 | 0.0249 | nein | nein | nein | nein |
| SOLUSDT | 0 | 5 | 21112 | 0.0093 | + | 0.0093 | 0.496 | 0.1393 | nein | nein | nein | nein |
| SOLUSDT | 0 | 15 | 21102 | -0.0110 | - | 0.0110 | 0.496 | 0.1343 | nein | nein | nein | nein |
| SOLUSDT | 0 | 60 | 21057 | 0.0018 | + | 0.0018 | 0.491 | 0.7711 | nein | nein | nein | nein |
| SOLUSDT | 0 | 300 | 20817 | -0.0162 | - | 0.0162 | 0.504 | 0.0348 | nein | nein | nein | nein |
| SOLUSDT | 1 | 1 | 21115 | -0.0081 | - | 0.0081 | 0.508 | 0.2139 | nein | nein | nein | nein |
| SOLUSDT | 1 | 5 | 21111 | -0.0054 | - | 0.0054 | 0.497 | 0.4677 | nein | nein | nein | nein |
| SOLUSDT | 1 | 15 | 21101 | -0.0089 | - | 0.0089 | 0.485 | 0.2239 | nein | nein | nein | nein |
| SOLUSDT | 1 | 60 | 21056 | -0.0022 | - | 0.0022 | 0.489 | 0.7363 | nein | nein | nein | nein |
| SOLUSDT | 1 | 300 | 20816 | -0.0005 | - | 0.0005 | 0.503 | 0.9552 | nein | nein | nein | nein |
| BNBUSDT | 0 | 1 | 59834 | 0.0441 | + | 0.0441 | 0.601 | 0.0050 | ja | ja | ja | nein |
| BNBUSDT | 0 | 5 | 59830 | 0.0204 | + | 0.0204 | 0.556 | 0.0050 | ja | ja | ja | nein |
| BNBUSDT | 0 | 15 | 59820 | 0.0051 | + | 0.0051 | 0.524 | 0.2289 | nein | nein | nein | nein |
| BNBUSDT | 0 | 60 | 59775 | 0.0000 | + | 0.0000 | 0.510 | 1.0000 | nein | nein | nein | nein |
| BNBUSDT | 0 | 300 | 59535 | -0.0031 | - | 0.0031 | 0.502 | 0.3980 | nein | nein | nein | nein |
| BNBUSDT | 1 | 1 | 59835 | 0.0075 | + | 0.0075 | 0.662 | 0.0597 | nein | ja | nein | nein |
| BNBUSDT | 1 | 5 | 59831 | -0.0066 | - | 0.0066 | 0.591 | 0.1393 | nein | ja | nein | nein |
| BNBUSDT | 1 | 15 | 59821 | -0.0095 | - | 0.0095 | 0.544 | 0.0398 | nein | ja | nein | nein |
| BNBUSDT | 1 | 60 | 59776 | -0.0016 | - | 0.0016 | 0.529 | 0.7164 | nein | nein | nein | nein |
| BNBUSDT | 1 | 300 | 59536 | 0.0026 | + | 0.0026 | 0.509 | 0.5124 | nein | nein | nein | nein |
| XRPUSDT | 0 | 1 | 21002 | -0.0009 | - | 0.0009 | 0.509 | 0.9154 | nein | nein | nein | nein |
| XRPUSDT | 0 | 5 | 20998 | 0.0039 | + | 0.0039 | 0.504 | 0.5423 | nein | nein | nein | nein |
| XRPUSDT | 0 | 15 | 20988 | -0.0067 | - | 0.0067 | 0.498 | 0.3134 | nein | nein | nein | nein |
| XRPUSDT | 0 | 60 | 20943 | 0.0111 | + | 0.0111 | 0.502 | 0.1194 | nein | nein | nein | nein |
| XRPUSDT | 0 | 300 | 20703 | 0.0078 | + | 0.0078 | 0.505 | 0.2836 | nein | nein | nein | nein |
| XRPUSDT | 1 | 1 | 21043 | -0.0065 | - | 0.0065 | 0.501 | 0.2886 | nein | nein | nein | nein |
| XRPUSDT | 1 | 5 | 21039 | -0.0062 | - | 0.0062 | 0.502 | 0.3881 | nein | nein | nein | nein |
| XRPUSDT | 1 | 15 | 21029 | -0.0043 | - | 0.0043 | 0.510 | 0.5522 | nein | nein | nein | nein |
| XRPUSDT | 1 | 60 | 20984 | 0.0017 | + | 0.0017 | 0.507 | 0.8259 | nein | nein | nein | nein |
| XRPUSDT | 1 | 300 | 20744 | 0.0072 | + | 0.0072 | 0.513 | 0.2537 | nein | nein | nein | nein |

---
**Gate-Schwellen (registriert, NICHT hier beurteilt):** Surrogate p <= 0.05 (BH-FDR alpha 0.1 ueber F-OFI) UND Vorzeichen = + (Aggression-Folge) UND (\|corr\| >= 0.05 ODER Hit-Rate >= 0.53) in >= 2 disjunkten Fenstern. Vorzeichen <= 0 in >=1 Fenster ODER Magnitude verfehlt ODER FDR-p > 0.05 = DROP. Signifikant INVERS = H-05b-Ausloeser, kein Bestehen.

*Erzeugt von `scripts/c01_ofi_sign.py` (Welle-2-WP, read-only Driver, DEC-11, eigener OFI-Schaetzer — `m2_ofi.py` unberuehrt). KAPITALFREI. Endgueltiges Gate-Urteil: gate-auditor gegen H-05.*
