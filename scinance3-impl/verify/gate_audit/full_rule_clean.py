"""Full DEC-77 rule under a variant of the simulated market column (simulation only, no real data).
mode 'clean': r_btc := f (sim BTC column reproduces measured sigma_f and rho_f).
mode 'conv' : documented convention (BTC column = (1+s z) f + e), for reference with the synthetic mask.
sigma_e = artifact's sigma_e_used (unchanged), bounds = artifact's bounds (unchanged)."""
import sys, json, math, time
sys.path.insert(0, '/home/user/scinance/src')
import numpy as np
from bybit_edge.research.wp13_xsec import nulls, characteristics

art = json.load(open(sys.argv[1])); wn = sys.argv[2]; mode = sys.argv[3]
methods = sys.argv[4].split(','); n_reps = int(sys.argv[5])
w = art['windows'][wn]; st = w['beta_control_method_study']
sigma_f, sigma_e = st['sigma_f'], st['sigma_e_used']
ks = [r['k'] for r in w['factor_calibration']['factor_share']['per_week']]
n_weeks = len(ks); n_sym = 1138
symbols = ['BTCUSDT'] + [f's{i}' for i in range(n_sym - 1)]
alive = np.zeros((n_weeks, n_sym), dtype=bool)
for t, k in enumerate(ks):
    alive[t, :k] = True
dec = w['beta_control_decision']; mb, cb = dec['null_mean_bound'], dec['ceiling_bound']
orig_sim = nulls.simulate_factor_panel
if mode == 'clean':
    def sim_mod(*a, **k):
        out = orig_sim(*a, **k); r = out['returns'].copy(); r[:, 0] = out['f']; out['returns'] = r; return out
    nulls.simulate_factor_panel = sim_mod
nulls.window_sigma_f_sigma_e = lambda *a, **k: {'sigma_f': sigma_f, 'sigma_e_total': sigma_e,
                                                 'sigma_e_idiosyncratic': sigma_e, 'sigma_e_used': sigma_e}
print(f'{wn} mode={mode} sigma_f={sigma_f:.5f} sigma_e={sigma_e:.5f} null_mean_bound={mb:.5f} ceiling_bound={cb:.5f}', flush=True)
res = {}
for cal in ('measured', 'stress'):
    c = st['calibrations'][cal]; rho, target = c['rho_f'], c['target_factor_share']
    t0 = time.time()
    s = nulls.calibrate_beta_sd_to_observed_share(target, rho_f=rho, sigma_f=sigma_f, sigma_e=sigma_e,
                                                  n_weeks=n_weeks, n_symbols=n_sym, symbols=symbols,
                                                  seed=53, mask=alive)
    bsd = s['beta_sd_calibrated']
    print(f' {cal}: rho={rho:.5f} target={target:.5f} beta_sd={bsd:.4f} conv={s["converged"]} '
          f'achieved={s["achieved_share"]:.5f} true={s["true_share"]:.5f} ({time.time()-t0:.0f}s)', flush=True)
    for m in methods:
        t0 = time.time()
        r = nulls.beta_controlled_factor_null(np.zeros((n_weeks, n_sym)), alive, symbols, method=m,
                                              n_reps=n_reps, seed=53, rho_f=rho, drift_f=0.0, beta_sd=bsd)
        vs = r['variants']
        worst = max(vs, key=lambda v: abs(vs[v]['mean_ic_draws_mean']))
        x = vs[worst]; se_mc = x['mean_ic_draws_sd'] / math.sqrt(x['n_reps_finite'])
        mean_ok = abs(x['mean_ic_draws_mean']) <= mb; ceil_ok = r['ceiling_mean_of_max'] <= cb
        res.setdefault(m, {})[cal] = (mean_ok and ceil_ok)
        print(f'   {cal:8s} {m:16s} worst={worst:8s} {x["mean_ic_draws_mean"]:+.5f} ({(abs(x["mean_ic_draws_mean"])-mb)/se_mc:+.1f} SE) '
              f'mean_ok={mean_ok} ceiling={r["ceiling_mean_of_max"]:.5f} ceil_ok={ceil_ok} ({time.time()-t0:.0f}s)', flush=True)
print(' PASS per method (measured AND stress):', {m: all(v.values()) for m, v in res.items()}, flush=True)
