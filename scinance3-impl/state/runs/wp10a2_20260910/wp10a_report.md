# WP-10(A) - Praemien-Kohaerenz im Stress (deskriptiv, KEIN VERDIKT)

**Modus: backfill (WP-10(A2), DEC-62) -- nachgeladene Tagesserien bis zum STRESS_ABS-Kanon-Beginn. KEIN PASS/FAIL, keine rho-Schwelle -- rein deskriptiver Vergleich Bestand vs. Backfill.**

## Serien
- `funding_backfill_BTCUSDT` (funding_cashflow_backfill): status=OK, coverage={'n_days': 2320, 'first': '2020-03-25', 'last': '2026-07-31'}
- `funding_backfill_ETHUSDT` (funding_cashflow_backfill): status=OK, coverage={'n_days': 2110, 'first': '2020-10-21', 'last': '2026-07-31'}
- `funding_backfill_SOLUSDT` (funding_cashflow_backfill): status=OK, coverage={'n_days': 1859, 'first': '2021-06-29', 'last': '2026-07-31'}
- `funding_backfill_XRPUSDT` (funding_cashflow_backfill): status=OK, coverage={'n_days': 1906, 'first': '2021-05-13', 'last': '2026-07-31'}
- `funding_backfill_BNBUSDT` (funding_cashflow_backfill): status=OK, coverage={'n_days': 1859, 'first': '2021-06-29', 'last': '2026-07-31'}
- `ivrv_backfill_BTC` (iv_rv_diff_backfill): status=OK, coverage={'n_days': 1956, 'first': '2021-03-24', 'last': '2026-07-31'}
- `ivrv_backfill_ETH` (iv_rv_diff_backfill): status=OK, coverage={'n_days': 1956, 'first': '2021-03-24', 'last': '2026-07-31'}
- `basis_BTCUSDT` (perp_basis_proxy): status=OK, coverage={'n_days': 70, 'first': '2026-06-16', 'last': '2026-09-07'}
- `basis_ETHUSDT` (perp_basis_proxy): status=OK, coverage={'n_days': 70, 'first': '2026-06-16', 'last': '2026-09-07'}

## Stress-Kanon
- STRESS_ABS: n_days=30, n_episodes=19, sha256=b75fb7a08a6d5903...

## Kohaerenz (Spearman, STRESS_ABS vs. Ruhe)
- funding_backfill_BTCUSDT x funding_backfill_ETHUSDT (n_overlap=2109):
  - stress: rho=0.570, 95%-CI=[0.175, 0.839], n=28 (n_episodes=17), Bonett/Wright-SE=0.212
  - quiet: rho=0.351, 95%-CI=[0.307, 0.395], n=2081 (n_episodes=None), Bonett/Wright-SE=0.023
- funding_backfill_BTCUSDT x funding_backfill_SOLUSDT (n_overlap=1858):
  - stress: rho=0.349, 95%-CI=[-0.281, 0.858], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.220, 95%-CI=[0.173, 0.269], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_BTCUSDT x funding_backfill_XRPUSDT (n_overlap=1905):
  - stress: rho=0.663, 95%-CI=[0.210, 0.903], n=20 (n_episodes=10), Bonett/Wright-SE=0.257
  - quiet: rho=0.222, 95%-CI=[0.175, 0.269], n=1885 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_BTCUSDT x funding_backfill_BNBUSDT (n_overlap=1858):
  - stress: rho=0.059, 95%-CI=[-0.596, 0.661], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.105, 95%-CI=[0.058, 0.155], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_BTCUSDT x ivrv_backfill_BTC (n_overlap=1955):
  - stress: rho=-0.433, 95%-CI=[-0.746, 0.022], n=22 (n_episodes=12), Bonett/Wright-SE=0.243
  - quiet: rho=-0.012, 95%-CI=[-0.060, 0.035], n=1933 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_BTCUSDT x ivrv_backfill_ETH (n_overlap=1955):
  - stress: rho=-0.464, 95%-CI=[-0.765, -0.059], n=22 (n_episodes=12), Bonett/Wright-SE=0.243
  - quiet: rho=-0.022, 95%-CI=[-0.072, 0.028], n=1933 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_BTCUSDT x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.163, 95%-CI=[-0.533, 0.206], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_BTCUSDT x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=0.110, 95%-CI=[-0.235, 0.444], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_ETHUSDT x funding_backfill_SOLUSDT (n_overlap=1858):
  - stress: rho=0.724, 95%-CI=[0.294, 0.915], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.264, 95%-CI=[0.214, 0.309], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_ETHUSDT x funding_backfill_XRPUSDT (n_overlap=1905):
  - stress: rho=0.588, 95%-CI=[0.159, 0.847], n=20 (n_episodes=10), Bonett/Wright-SE=0.257
  - quiet: rho=0.241, 95%-CI=[0.194, 0.288], n=1885 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_ETHUSDT x funding_backfill_BNBUSDT (n_overlap=1858):
  - stress: rho=0.741, 95%-CI=[0.346, 0.943], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.168, 95%-CI=[0.120, 0.215], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_ETHUSDT x ivrv_backfill_BTC (n_overlap=1955):
  - stress: rho=-0.012, 95%-CI=[-0.478, 0.477], n=22 (n_episodes=12), Bonett/Wright-SE=0.243
  - quiet: rho=0.030, 95%-CI=[-0.013, 0.076], n=1933 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_ETHUSDT x ivrv_backfill_ETH (n_overlap=1955):
  - stress: rho=0.028, 95%-CI=[-0.420, 0.476], n=22 (n_episodes=12), Bonett/Wright-SE=0.243
  - quiet: rho=0.017, 95%-CI=[-0.027, 0.065], n=1933 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_ETHUSDT x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=0.106, 95%-CI=[-0.242, 0.453], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_ETHUSDT x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.010, 95%-CI=[-0.347, 0.336], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_SOLUSDT x funding_backfill_XRPUSDT (n_overlap=1858):
  - stress: rho=0.631, 95%-CI=[0.103, 0.938], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.301, 95%-CI=[0.253, 0.348], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_SOLUSDT x funding_backfill_BNBUSDT (n_overlap=1858):
  - stress: rho=0.651, 95%-CI=[0.120, 0.959], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.223, 95%-CI=[0.175, 0.270], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_SOLUSDT x ivrv_backfill_BTC (n_overlap=1858):
  - stress: rho=-0.174, 95%-CI=[-0.695, 0.431], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=-0.016, 95%-CI=[-0.061, 0.028], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_SOLUSDT x ivrv_backfill_ETH (n_overlap=1858):
  - stress: rho=-0.191, 95%-CI=[-0.628, 0.400], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=-0.013, 95%-CI=[-0.063, 0.032], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_SOLUSDT x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.227, 95%-CI=[-0.549, 0.166], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_SOLUSDT x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.039, 95%-CI=[-0.320, 0.264], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_XRPUSDT x funding_backfill_BNBUSDT (n_overlap=1858):
  - stress: rho=0.334, 95%-CI=[-0.205, 0.722], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.210, 95%-CI=[0.164, 0.254], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_XRPUSDT x ivrv_backfill_BTC (n_overlap=1905):
  - stress: rho=-0.291, 95%-CI=[-0.696, 0.277], n=20 (n_episodes=10), Bonett/Wright-SE=0.257
  - quiet: rho=0.014, 95%-CI=[-0.031, 0.061], n=1885 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_XRPUSDT x ivrv_backfill_ETH (n_overlap=1905):
  - stress: rho=-0.259, 95%-CI=[-0.686, 0.265], n=20 (n_episodes=10), Bonett/Wright-SE=0.257
  - quiet: rho=-0.003, 95%-CI=[-0.049, 0.046], n=1885 (n_episodes=None), Bonett/Wright-SE=0.024
- funding_backfill_XRPUSDT x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.192, 95%-CI=[-0.550, 0.212], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_XRPUSDT x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.370, 95%-CI=[-0.641, -0.018], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_BNBUSDT x ivrv_backfill_BTC (n_overlap=1858):
  - stress: rho=0.002, 95%-CI=[-0.585, 0.480], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.003, 95%-CI=[-0.040, 0.049], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_BNBUSDT x ivrv_backfill_ETH (n_overlap=1858):
  - stress: rho=0.064, 95%-CI=[-0.505, 0.546], n=14 (n_episodes=9), Bonett/Wright-SE=0.320
  - quiet: rho=0.012, 95%-CI=[-0.034, 0.056], n=1844 (n_episodes=None), Bonett/Wright-SE=0.025
- funding_backfill_BNBUSDT x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.173, 95%-CI=[-0.540, 0.203], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- funding_backfill_BNBUSDT x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.198, 95%-CI=[-0.537, 0.234], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- ivrv_backfill_BTC x ivrv_backfill_ETH (n_overlap=1955):
  - stress: rho=0.886, 95%-CI=[0.660, 0.983], n=22 (n_episodes=12), Bonett/Wright-SE=0.243
  - quiet: rho=0.875, 95%-CI=[0.860, 0.890], n=1933 (n_episodes=None), Bonett/Wright-SE=0.024
- ivrv_backfill_BTC x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=0.125, 95%-CI=[-0.295, 0.505], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- ivrv_backfill_BTC x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.173, 95%-CI=[-0.547, 0.220], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- ivrv_backfill_ETH x basis_BTCUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=0.016, 95%-CI=[-0.364, 0.393], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- ivrv_backfill_ETH x basis_ETHUSDT (n_overlap=33):
  - stress: TOO_FEW (n=0)
  - quiet: rho=-0.125, 95%-CI=[-0.505, 0.302], n=33 (n_episodes=None), Bonett/Wright-SE=0.194
- basis_BTCUSDT x basis_ETHUSDT (n_overlap=69):
  - stress: TOO_FEW (n=1)
  - quiet: rho=0.292, 95%-CI=[0.052, 0.503], n=68 (n_episodes=None), Bonett/Wright-SE=0.131

## Struktureller Nulleffekt der Stress-Zelle (Surrogate, keine Schwelle)
- funding_backfill_BTCUSDT x funding_backfill_ETHUSDT: real rho_stress=0.570, real Lift=0.218 | Null-Lift (unabhaengige Bloecke) mean=-0.000 [-0.323, 0.312], Rang(real Lift)=87.1% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.004 [-0.218, 0.236], Rang(real Lift)=93.1%
- funding_backfill_BTCUSDT x funding_backfill_SOLUSDT: real rho_stress=0.349, real Lift=0.129 | Null-Lift (unabhaengige Bloecke) mean=0.004 [-0.455, 0.459], Rang(real Lift)=66.7% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.006 [-0.457, 0.449], Rang(real Lift)=67.8%
- funding_backfill_BTCUSDT x funding_backfill_XRPUSDT: real rho_stress=0.663, real Lift=0.441 | Null-Lift (unabhaengige Bloecke) mean=-0.005 [-0.402, 0.371], Rang(real Lift)=97.6% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.013 [-0.327, 0.284], Rang(real Lift)=99.5%
- funding_backfill_BTCUSDT x funding_backfill_BNBUSDT: real rho_stress=0.059, real Lift=-0.046 | Null-Lift (unabhaengige Bloecke) mean=0.005 [-0.467, 0.468], Rang(real Lift)=44.0% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.012 [-0.407, 0.428], Rang(real Lift)=40.3%
- funding_backfill_BTCUSDT x ivrv_backfill_BTC: real rho_stress=-0.433, real Lift=-0.421 | Null-Lift (unabhaengige Bloecke) mean=0.007 [-0.345, 0.380], Rang(real Lift)=2.1% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.006 [-0.420, 0.388], Rang(real Lift)=5.0%
- funding_backfill_BTCUSDT x ivrv_backfill_ETH: real rho_stress=-0.464, real Lift=-0.442 | Null-Lift (unabhaengige Bloecke) mean=0.012 [-0.328, 0.378], Rang(real Lift)=2.2% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.002 [-0.388, 0.385], Rang(real Lift)=3.5%
- funding_backfill_BTCUSDT x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_BTCUSDT x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_ETHUSDT x funding_backfill_SOLUSDT: real rho_stress=0.724, real Lift=0.460 | Null-Lift (unabhaengige Bloecke) mean=0.001 [-0.467, 0.466], Rang(real Lift)=94.6% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.003 [-0.435, 0.413], Rang(real Lift)=96.5%
- funding_backfill_ETHUSDT x funding_backfill_XRPUSDT: real rho_stress=0.588, real Lift=0.347 | Null-Lift (unabhaengige Bloecke) mean=0.002 [-0.400, 0.418], Rang(real Lift)=92.3% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.022 [-0.323, 0.279], Rang(real Lift)=97.6%
- funding_backfill_ETHUSDT x funding_backfill_BNBUSDT: real rho_stress=0.741, real Lift=0.574 | Null-Lift (unabhaengige Bloecke) mean=-0.002 [-0.483, 0.462], Rang(real Lift)=98.3% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.007 [-0.366, 0.399], Rang(real Lift)=99.7%
- funding_backfill_ETHUSDT x ivrv_backfill_BTC: real rho_stress=-0.012, real Lift=-0.042 | Null-Lift (unabhaengige Bloecke) mean=-0.001 [-0.363, 0.372], Rang(real Lift)=44.2% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.002 [-0.377, 0.390], Rang(real Lift)=44.0%
- funding_backfill_ETHUSDT x ivrv_backfill_ETH: real rho_stress=0.028, real Lift=0.011 | Null-Lift (unabhaengige Bloecke) mean=-0.004 [-0.364, 0.372], Rang(real Lift)=53.7% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.000 [-0.387, 0.382], Rang(real Lift)=52.0%
- funding_backfill_ETHUSDT x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_ETHUSDT x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_SOLUSDT x funding_backfill_XRPUSDT: real rho_stress=0.631, real Lift=0.330 | Null-Lift (unabhaengige Bloecke) mean=0.008 [-0.448, 0.477], Rang(real Lift)=87.5% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.006 [-0.397, 0.416], Rang(real Lift)=89.7%
- funding_backfill_SOLUSDT x funding_backfill_BNBUSDT: real rho_stress=0.651, real Lift=0.428 | Null-Lift (unabhaengige Bloecke) mean=0.015 [-0.465, 0.461], Rang(real Lift)=93.4% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.006 [-0.462, 0.461], Rang(real Lift)=93.6%
- funding_backfill_SOLUSDT x ivrv_backfill_BTC: real rho_stress=-0.174, real Lift=-0.158 | Null-Lift (unabhaengige Bloecke) mean=0.008 [-0.473, 0.474], Rang(real Lift)=28.5% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.014 [-0.471, 0.485], Rang(real Lift)=30.6%
- funding_backfill_SOLUSDT x ivrv_backfill_ETH: real rho_stress=-0.191, real Lift=-0.178 | Null-Lift (unabhaengige Bloecke) mean=0.005 [-0.443, 0.473], Rang(real Lift)=26.2% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.002 [-0.496, 0.514], Rang(real Lift)=28.5%
- funding_backfill_SOLUSDT x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_SOLUSDT x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_XRPUSDT x funding_backfill_BNBUSDT: real rho_stress=0.334, real Lift=0.124 | Null-Lift (unabhaengige Bloecke) mean=0.009 [-0.461, 0.467], Rang(real Lift)=64.7% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.009 [-0.351, 0.366], Rang(real Lift)=68.7%
- funding_backfill_XRPUSDT x ivrv_backfill_BTC: real rho_stress=-0.291, real Lift=-0.305 | Null-Lift (unabhaengige Bloecke) mean=-0.001 [-0.384, 0.395], Rang(real Lift)=9.8% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.009 [-0.387, 0.405], Rang(real Lift)=10.8%
- funding_backfill_XRPUSDT x ivrv_backfill_ETH: real rho_stress=-0.259, real Lift=-0.257 | Null-Lift (unabhaengige Bloecke) mean=0.001 [-0.375, 0.403], Rang(real Lift)=13.6% | Null-Lift (Selektion auf gemeinsame Groesse) mean=0.010 [-0.393, 0.411], Rang(real Lift)=14.4%
- funding_backfill_XRPUSDT x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_XRPUSDT x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_BNBUSDT x ivrv_backfill_BTC: real rho_stress=0.002, real Lift=-0.001 | Null-Lift (unabhaengige Bloecke) mean=-0.008 [-0.480, 0.470], Rang(real Lift)=50.5% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.003 [-0.469, 0.485], Rang(real Lift)=51.9%
- funding_backfill_BNBUSDT x ivrv_backfill_ETH: real rho_stress=0.064, real Lift=0.052 | Null-Lift (unabhaengige Bloecke) mean=-0.003 [-0.450, 0.485], Rang(real Lift)=58.1% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.008 [-0.500, 0.486], Rang(real Lift)=56.3%
- funding_backfill_BNBUSDT x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- funding_backfill_BNBUSDT x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- ivrv_backfill_BTC x ivrv_backfill_ETH: real rho_stress=0.886, real Lift=0.011 | Null-Lift (unabhaengige Bloecke) mean=0.006 [-0.363, 0.374], Rang(real Lift)=50.1% | Null-Lift (Selektion auf gemeinsame Groesse) mean=-0.036 [-0.312, 0.240], Rang(real Lift)=61.5%
- ivrv_backfill_BTC x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- ivrv_backfill_BTC x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- ivrv_backfill_ETH x basis_BTCUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- ivrv_backfill_ETH x basis_ETHUSDT: TOO_FEW (n_stress=0, n_quiet=33)
- basis_BTCUSDT x basis_ETHUSDT: TOO_FEW (n_stress=1, n_quiet=68)

(Deskriptiv, KEINE Schwelle -- der Rang zeigt nur, wo der reale Lift innerhalb der jeweiligen Surrogat-Nullverteilung liegt (B=1.000 seedierte Surrogate je Variante); es folgt daraus KEIN VERDIKT und KEIN PASS/FAIL.)

## Bestand vs. Backfill (Ueberlappung)
- funding_BTCUSDT: n_overlap=882, max|diff|=0, n_Tage_diff(>1e-09)=0
- funding_ETHUSDT: n_overlap=883, max|diff|=0, n_Tage_diff(>1e-09)=0
- funding_SOLUSDT: n_overlap=128, max|diff|=0, n_Tage_diff(>1e-09)=0
- funding_XRPUSDT: n_overlap=128, max|diff|=0, n_Tage_diff(>1e-09)=0
- funding_BNBUSDT: n_overlap=128, max|diff|=0, n_Tage_diff(>1e-09)=0
- ivrv_BTC: n_overlap=165, max|diff|=0 vol.pts, Materialitaetsband=0.3 (within_band=True), n_Tage_ueber_Band=0
- ivrv_ETH: n_overlap=165, max|diff|=0 vol.pts, Materialitaetsband=0.3 (within_band=True), n_Tage_ueber_Band=0

## Portfolio-Nulleffekt (Konstanten, keine Schwelle)
### Gleichgewichtungs-Null (k=2..5, Diversifikation)
- k=2: mean_Sharpe=0.0251, sd=0.4034, p95=0.6645, p99=0.9118, n_bootstrap=1000, seed=53
- k=3: mean_Sharpe=-0.0311, sd=0.4084, p95=0.6287, p99=0.9701, n_bootstrap=1000, seed=53
- k=4: mean_Sharpe=-0.0152, sd=0.4100, p95=0.6481, p99=0.9731, n_bootstrap=1000, seed=53
- k=5: mean_Sharpe=-0.0178, sd=0.4124, p95=0.6618, p99=0.9520, n_bootstrap=1000, seed=53
### Selektions-Obergrenze (K=5..100, Bailey/Lopez de Prado)
- sigma_SR=0.3984 (Pool=5000, seed=53)
- K=5: E[max]_empirisch=0.4637, E[max]_Bailey/LdP=0.4752 (n_groups=1000)
- K=10: E[max]_empirisch=0.6141, E[max]_Bailey/LdP=0.6274 (n_groups=500)
- K=20: E[max]_empirisch=0.7384, E[max]_Bailey/LdP=0.7573 (n_groups=250)
- K=50: E[max]_empirisch=0.8830, E[max]_Bailey/LdP=0.9069 (n_groups=100)
- K=100: E[max]_empirisch=0.9693, E[max]_Bailey/LdP=1.0083 (n_groups=50)

## DEC-53-Artefakte
- funding_backfill_BTCUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_funding_backfill_BTCUSDT_daily.csv (n=2320, sha256=c8c7547f9bc0cded...)
- funding_backfill_ETHUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_funding_backfill_ETHUSDT_daily.csv (n=2110, sha256=0ad339a48c8b68ac...)
- funding_backfill_SOLUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_funding_backfill_SOLUSDT_daily.csv (n=1859, sha256=781f6f1dc3bf67df...)
- funding_backfill_XRPUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_funding_backfill_XRPUSDT_daily.csv (n=1906, sha256=d125c51324c8d034...)
- funding_backfill_BNBUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_funding_backfill_BNBUSDT_daily.csv (n=1859, sha256=cc5efdd5390b46a7...)
- ivrv_backfill_BTC: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_ivrv_backfill_BTC_daily.csv (n=1956, sha256=bb8adde02092a48d...)
- ivrv_backfill_ETH: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_ivrv_backfill_ETH_daily.csv (n=1956, sha256=f95147522cea33e8...)
- basis_BTCUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_basis_BTCUSDT_daily.csv (n=70, sha256=e2d3eeaf9291301f...)
- basis_ETHUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_basis_ETHUSDT_daily.csv (n=70, sha256=af2f1cb24a366263...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260910\wp10a_coherence_bootstrap_fingerprint.json (83 Eintraege, sha256=9256732b5c0c631c...)

(Seed dieses Laufs: 53. Teil A ist deskriptiv -- kein PASS/FAIL, keine rho-Schwelle.)
