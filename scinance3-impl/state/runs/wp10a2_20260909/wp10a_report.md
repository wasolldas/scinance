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
- `basis_BTCUSDT` (perp_basis_proxy): status=OK, coverage={'n_days': 61, 'first': '2026-06-16', 'last': '2026-08-29'}
- `basis_ETHUSDT` (perp_basis_proxy): status=OK, coverage={'n_days': 61, 'first': '2026-06-16', 'last': '2026-08-29'}

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
- basis_BTCUSDT x basis_ETHUSDT (n_overlap=60):
  - stress: TOO_FEW (n=1)
  - quiet: rho=0.335, 95%-CI=[0.073, 0.568], n=59 (n_episodes=None), Bonett/Wright-SE=0.142

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
- funding_backfill_BTCUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_funding_backfill_BTCUSDT_daily.csv (n=2320, sha256=c8c7547f9bc0cded...)
- funding_backfill_ETHUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_funding_backfill_ETHUSDT_daily.csv (n=2110, sha256=0ad339a48c8b68ac...)
- funding_backfill_SOLUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_funding_backfill_SOLUSDT_daily.csv (n=1859, sha256=781f6f1dc3bf67df...)
- funding_backfill_XRPUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_funding_backfill_XRPUSDT_daily.csv (n=1906, sha256=d125c51324c8d034...)
- funding_backfill_BNBUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_funding_backfill_BNBUSDT_daily.csv (n=1859, sha256=cc5efdd5390b46a7...)
- ivrv_backfill_BTC: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_ivrv_backfill_BTC_daily.csv (n=1956, sha256=bb8adde02092a48d...)
- ivrv_backfill_ETH: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_ivrv_backfill_ETH_daily.csv (n=1956, sha256=f95147522cea33e8...)
- basis_BTCUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_basis_BTCUSDT_daily.csv (n=61, sha256=1d15006e09c37747...)
- basis_ETHUSDT: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_basis_ETHUSDT_daily.csv (n=61, sha256=3b945da43de3df59...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10a2_20260909\wp10a_coherence_bootstrap_fingerprint.json (62 Eintraege, sha256=53ba6b8fc1d0ed14...)

(Seed dieses Laufs: 53. Teil A ist deskriptiv -- kein PASS/FAIL, keine rho-Schwelle.)
