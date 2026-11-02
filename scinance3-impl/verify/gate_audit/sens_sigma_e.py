"""Sensitivity (simulation only, no real data): does the sigma_e level used in the
v5c method study (biased low by zero-return never-alive symbols) change the W2-stress
FM null mean of mom1 materially?  Synthetic alive mask with the real per-week K series."""
import sys, json, math, time
sys.path.insert(0, '/home/user/scinance/src')
import numpy as np
from bybit_edge.research.wp13_xsec import nulls

art = json.load(open(sys.argv[1]))
wn = sys.argv[2]
sigma_e_list = [float(x) for x in sys.argv[3].split(',')]
methods = sys.argv[4].split(',')
n_reps = int(sys.argv[5])
w = art['windows'][wn]
st = w['beta_control_method_study']
cal = st['calibrations']['stress']
sigma_f = st['sigma_f']; rho = cal['rho_f']; target = cal['target_factor_share']
ks = [r['k'] for r in w['factor_calibration']['factor_share']['per_week']]
n_weeks = len(ks); n_sym = 1138
symbols = ['BTCUSDT'] + [f's{i}' for i in range(n_sym - 1)]
alive = np.zeros((n_weeks, n_sym), dtype=bool)
for t, k in enumerate(ks):
    alive[t, :k] = True
mb = w['beta_control_decision']['null_mean_bound']
print(wn, 'n_weeks', n_weeks, 'K med', int(np.median(ks)), 'sigma_f', round(sigma_f, 5), 'rho_stress', round(rho, 5),
      'target', round(target, 5), 'bound', round(mb, 5), 'artifact beta_sd', round(cal['beta_sd_calibrated'], 5))
orig = nulls.window_sigma_f_sigma_e
for se in sigma_e_list:
    t0 = time.time()
    s = nulls.calibrate_beta_sd_to_observed_share(target, rho_f=rho, sigma_f=sigma_f, sigma_e=se,
                                                  n_weeks=n_weeks, n_symbols=n_sym, symbols=symbols,
                                                  seed=53, mask=alive)
    bsd = s['beta_sd_calibrated']
    print(f' sigma_e={se:.4f}: beta_sd={bsd:.4f} conv={s["converged"]} it={s["n_iter"]} achieved={s["achieved_share"]:.5f} '
          f'true_share={s["true_share"]:.5f} ({time.time()-t0:.0f}s)', flush=True)
    nulls.window_sigma_f_sigma_e = lambda *a, _se=se, **k: {'sigma_f': sigma_f, 'sigma_e_total': _se,
                                                             'sigma_e_idiosyncratic': _se, 'sigma_e_used': _se}
    for m in methods:
        t0 = time.time()
        r = nulls.beta_controlled_factor_null(np.zeros((n_weeks, n_sym)), alive, symbols, method=m,
                                              variants=('mom1', 'mom2', 'mom4'), n_reps=n_reps, seed=53,
                                              rho_f=rho, drift_f=0.0, beta_sd=bsd)
        out = []
        for v in ('mom1', 'mom2', 'mom4'):
            x = r['variants'][v]
            se_mc = x['mean_ic_draws_sd'] / math.sqrt(x['n_reps_finite'])
            out.append(f"{v} {x['mean_ic_draws_mean']:+.5f} ({(abs(x['mean_ic_draws_mean'])-mb)/se_mc:+.1f} SE)")
        print(f'   {m:16s} ' + ' | '.join(out) + f'  ({time.time()-t0:.0f}s)', flush=True)
    nulls.window_sigma_f_sigma_e = orig
