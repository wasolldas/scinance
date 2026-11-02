"""Bounding sensitivity (simulation only): market column in the simulated panel set to the
factor itself (r_btc = f, as in the real data where sigma_f := SD(BTC)), instead of the
documented convention (BTC column = (1+s z) f + e, SD ~ sqrt(sigma_f^2+sigma_e^2)).
Most favourable case for beta-control methods (cleanest possible beta estimates)."""
import sys, json, math, time
sys.path.insert(0, '/home/user/scinance/src')
import numpy as np
from bybit_edge.research.wp13_xsec import nulls

art = json.load(open(sys.argv[1])); wn = sys.argv[2]
sigma_e_list = [float(x) for x in sys.argv[3].split(',')]
methods = sys.argv[4].split(','); n_reps = int(sys.argv[5]); cal_name = sys.argv[6]
w = art['windows'][wn]; st = w['beta_control_method_study']; cal = st['calibrations'][cal_name]
sigma_f = st['sigma_f']; rho = cal['rho_f']; target = cal['target_factor_share']
ks = [r['k'] for r in w['factor_calibration']['factor_share']['per_week']]
n_weeks = len(ks); n_sym = 1138
symbols = ['BTCUSDT'] + [f's{i}' for i in range(n_sym - 1)]
alive = np.zeros((n_weeks, n_sym), dtype=bool)
for t, k in enumerate(ks):
    alive[t, :k] = True
mb = w['beta_control_decision']['null_mean_bound']
orig_sim = nulls.simulate_factor_panel
def sim_clean(*a, **k):
    out = orig_sim(*a, **k)
    r = out['returns'].copy(); r[:, 0] = out['f']; out['returns'] = r
    return out
nulls.simulate_factor_panel = sim_clean
print(wn, cal_name, 'clean BTC column; bound', round(mb, 5), 'rho', round(rho, 5), 'target', round(target, 5))
for se in sigma_e_list:
    t0 = time.time()
    s = nulls.calibrate_beta_sd_to_observed_share(target, rho_f=rho, sigma_f=sigma_f, sigma_e=se,
                                                  n_weeks=n_weeks, n_symbols=n_sym, symbols=symbols,
                                                  seed=53, mask=alive)
    bsd = s['beta_sd_calibrated']
    print(f' sigma_e={se:.4f}: beta_sd={bsd:.4f} conv={s["converged"]} achieved={s["achieved_share"]:.5f} '
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
            x = r['variants'][v]; se_mc = x['mean_ic_draws_sd'] / math.sqrt(x['n_reps_finite'])
            out.append(f"{v} {x['mean_ic_draws_mean']:+.5f} ({(abs(x['mean_ic_draws_mean'])-mb)/se_mc:+.1f} SE)")
        print(f'   {m:16s} ' + ' | '.join(out) + f'  ({time.time()-t0:.0f}s)', flush=True)
