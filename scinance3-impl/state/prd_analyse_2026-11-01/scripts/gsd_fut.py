import numpy as np
from scipy.stats import norm
Pinv=norm.ppf
rng=np.random.default_rng(53)
looks=4; t=np.arange(1,looks+1)/looks; dt=np.diff(np.r_[0,t])
nsim=400000
inc=rng.standard_normal((nsim,looks))*np.sqrt(dt)
def run(alpha,power,fut=0.0):
    # OBF efficacy, non-binding futility Z<fut at looks 1..3; calibrate c ignoring futility (non-binding)
    lo,hi=1.0,4.0
    Z0=np.cumsum(inc,axis=1)/np.sqrt(t)
    for _ in range(50):
        c=(lo+hi)/2
        if (Z0>=c/np.sqrt(t)).any(axis=1).mean()>alpha: lo=c
        else: hi=c
    c=(lo+hi)/2
    zfix=Pinv(1-alpha)+Pinv(power)
    def stats(theta,R):
        Z=np.cumsum(inc+theta*dt,axis=1)/np.sqrt(t)
        eff=Z>=c/np.sqrt(t)
        futm=np.zeros_like(eff); futm[:,:-1]=Z[:,:-1]<fut
        stop=eff|futm
        first=np.where(stop.any(axis=1),stop.argmax(axis=1),looks-1)
        win=eff[np.arange(nsim),first]
        return win.mean(),(t[first]*R).mean()
    lo,hi=1.0,1.6
    for _ in range(40):
        R=(lo+hi)/2
        pw,_=stats(zfix*np.sqrt(R),R)
        if pw<power: lo=R
        else: hi=R
    R=(lo+hi)/2
    pw1,en1=stats(zfix*np.sqrt(R),R)
    pw0,en0=stats(0.0,R)
    return dict(c=round(c,3),Rmax=round(R,3),power=round(pw1,3),EN_H1=round(en1,3),alpha_eff=round(pw0,5),EN_H0=round(en0,3))
for a in (0.05,0.0025):
    print('alpha',a,'nofut',run(a,0.8,fut=-99))
    print('alpha',a,'fut Z<0',run(a,0.8,fut=0.0))
