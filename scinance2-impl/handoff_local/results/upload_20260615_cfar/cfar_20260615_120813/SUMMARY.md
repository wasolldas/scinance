# H-03 Notausgang - C-31 CFAR Runner

- **Erzeugt:** 2026-06-15 14:01:07 UTC
- **Run-Dir:** `E:\Claude\Projects\scinance\scinance2-impl\handoff_local\results\cfar_20260615_120813``
- **DuckDB:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb``
- **Parameter:** windows=2, surrogates=200, --db-copy, timeout=1800s/symbol

| Symbol | Status | rc | Dauer | Detail |
|---|---|---:|---:|---|
| C31_CFAR_BTCUSDT | OK | 0 | 712s | rc=0 |
| C31_CFAR_ETHUSDT | OK | 0 | 661s | rc=0 |
| C31_CFAR_SOLUSDT | FAIL | 124 | 1800s | TIMEOUT nach 1800 s |
| C31_CFAR_BNBUSDT | FAIL | 124 | 1800s | TIMEOUT nach 1800 s |
| C31_CFAR_XRPUSDT | FAIL | 124 | 1800s | TIMEOUT nach 1800 s |

**Gesamt:** ok=2 fail=3 skip=0 -> exit 1

*H-03-Gate-Urteil faellt der gate-auditor gegen die Registry (Roh-JSONs je Symbol unter `c31_<symbol>/c31_cfar_results.json`).*
