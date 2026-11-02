"""Open arithmetic for BELEGE_AUS_PDF_2026-10-20 (no data access; inputs are paper values)."""
import math
from statistics import NormalDist
N = NormalDist()
def k(q):  # E[x|top q]-E[x|bottom q] in SD units for normal x
    z = N.inv_cdf(1 - q); return 2 * N.pdf(z) / q
kq, kt, kd = k(0.2), k(1/3), k(0.1)
print('k quintile %.3f tercile %.3f decile %.3f' % (kq, kt, kd))
# sigma anchors
sx_fic_LL = (0.245 + 0.169) / kq
sx_fic_SI = (0.330 + 0.279) / kq
sx_bia_w = 0.06889 * math.sqrt(7)
print('sigma_x Ficura L&L %.4f  S/I %.4f  Bianchi daily->weekly sqrt7 %.4f' % (sx_fic_LL, sx_fic_SI, sx_bia_w))
sig = [0.10, 0.148, 0.182, 0.20, 0.25, 0.30]
print('\nWeg A: IC = S/(k*sigma)')
for name, S, kk in [('LTW 1W VW quint S', 0.027, kq), ('LTW 1W VW quint CAPM-alpha', 0.028, kq),
                    ('LTW 1W VW tercile S', 0.041, kt), ('LTW 2W VW quint', 0.033, kq), ('LTW 3W VW quint', 0.041, kq),
                    ('Ficura L&L 1W EW quint', 0.0136, kq), ('Ficura L&L 1W BTC-alpha', 0.0131, kq),
                    ('Ficura M>10M,V>1M 1W EW', 0.0144, kq)]:
    print('  %-30s' % name, ' '.join('s%.3f:%.4f' % (s, S / (kk * s)) for s in sig))
print('\nWeg A* (gleiche Quelle, sigma_r ~ sigma_x): IC ~ S_r/S_x')
for name, Sr, Sx in [('Ficura L&L 1W', 0.0136, 0.414), ('Ficura L&L 1W alpha', 0.0131, 0.414), ('Ficura S/I 1W', -0.0391, 0.609)]:
    print('  %-24s %.4f' % (name, Sr / Sx))
print('\nWeg FM: IC = b*sqrt(2)/sigma (Regressor Quintilsnummer 1..5)')
for name, b in [('LTW FM >10mil r1,0', 0.005), ('LTW FM >10mil r2,0', 0.007), ('LTW FM >10mil r3,0', 0.007), ('LTW FM >1mil r1,0', -0.002)]:
    print('  %-22s' % name, ' '.join('s%.3f:%.4f' % (s, b * math.sqrt(2) / s) for s in sig))
print('\nWeg B: IC_aequiv = t/sqrt(N) * SD_prog')
for name, t, n in [('LTW 1W VW LS', 1.994, 260), ('LTW 1W CAPM alpha', 2.012, 260), ('LTW 2W VW LS', 2.442, 260),
                   ('LTW 3W VW LS', 2.742, 260), ('LTW 1W tercile', 3.719, 260), ('LTW FM >10mil r1,0', 1.668, 260),
                   ('Ficura L&L 1W', 2.332, 291), ('Ficura L&L 1W BTC-alpha', 2.603, 291), ('Ficura M>10M,V>1M 1W', 2.075, 291)]:
    ir = t / math.sqrt(n)
    print('  %-26s IR %.4f  SD0.0511: %.4f  SD0.0425: %.4f' % (name, ir, ir * 0.0511, ir * 0.0425))
for n in (260, 291):
    print('  t fuer IC 0.020: N=%d -> %.2f (SD 0.0511), %.2f (SD 0.0425)' % (n, 0.020 / 0.0511 * math.sqrt(n), 0.020 / 0.0425 * math.sqrt(n)))
print('  implizite SD(IC_t) Ficura L&L = IC_A*/IR = %.3f' % ((0.0136 / 0.414) / (2.332 / math.sqrt(291))))
print('\nVRP-Umrechnung')
sn = 0.6155
for name, Q, P, V in [('v1 BVIX overall', 0.71, 0.57, 0.14), ('v1 Q-dens overall', 0.63, 0.57, 0.07),
                      ('v1 BVIX HV', 0.88, 0.76, 0.12), ('v1 BVIX LV', 0.50, 0.33, 0.17), ('v2 BVIX overall', 0.72, 0.58, 0.14)]:
    iv, rv = math.sqrt(Q), math.sqrt(P); L = 0.5 * math.log(Q / P)
    pi2 = sn * (math.exp(L) - 1); pi1 = math.sqrt(sn ** 2 + V) - sn
    print('  %-18s sqrtQ %.4f sqrtP %.4f VP %.2f L %.4f pi-2 %.2f pi-1(V=%.2f) %.2f  Q-P %.2f' % (name, iv, rv, 100 * (iv - rv), L, 100 * pi2, V, 100 * pi1, Q - P))
# ann. 27d: what VRP in vol points at mean IV 0.82 Table 1
for iv in (0.82, 0.843, 0.73):
    print('  IV %.3f, V 0.14 -> RV %.4f, VP %.2f; V 0.07 -> VP %.2f' % (iv, math.sqrt(iv**2 - 0.14), 100 * (iv - math.sqrt(iv**2 - 0.14)), 100 * (iv - math.sqrt(iv**2 - 0.07))))
