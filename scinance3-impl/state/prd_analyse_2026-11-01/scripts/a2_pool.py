import numpy as np
from scipy.stats import norm, multivariate_normal
Phi,Pinv=norm.cdf,norm.ppf
se1,se2=7.34,7.58           # P2'' SE per window (DEC-103 E7)
sep=np.sqrt(se1**2+se2**2)/2
print('pooled SE',round(sep,3))
for a in (0.01,0.0057,0.0025):
    print('pooled alpha',a,'MDE80',round((Pinv(1-a)+0.8416)*sep,2),'power at 16.5',round(Phi(16.5/sep-Pinv(1-a)),3))
# DEC-52 gate at 16.5: pooled z 2.5287 + screens 0.5*z*SEp per window
zc=2.5287; T=zc*sep; t=0.5*T
pp=Phi((16.5-T)/sep); s1=Phi((16.5-t)/se1); s2=Phi((16.5-t)/se2)
print('DEC52 product',round(pp*s1*s2,3),'pooled',round(pp,3),'screens',round(s1,3),round(s2,3))
# exact DEC52 gate (x1,x2 independent windows)
rng=np.random.default_rng(5); n=2_000_000
x1=rng.normal(16.5,se1,n); x2=rng.normal(16.5,se2,n)
print('DEC52 exact', round(((x1+x2)/2>=T)&(x1>=t)&(x2>=t)).mean() if False else round((((x1+x2)/2>=T)&(x1>=t)&(x2>=t)).mean(),3))
# class P required SR_eff per window under C10 (power .8 each, alpha .05 one-sided)
for L in (0.5,1,2,3):
    print('L years',L,'SR_eff needed',round(2.4865/np.sqrt(L),2))
# pooled two windows alpha 0.0025 equivalent: SR_eff needed with 2 windows of L years
for L in (1,2):
    print('pooled 2xL',L,'SR_eff needed',round((Pinv(1-0.0025)+0.8416)/np.sqrt(2*L),2),' (alpha .01:',round((Pinv(0.99)+0.8416)/np.sqrt(2*L),2),')')
