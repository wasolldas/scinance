# Analytische Power-Ueberschlaege nur aus Akten-Zahlen (keine Datenrechnung).
import math, datetime as dt
from statistics import NormalDist
N=NormalDist()
Z=1.6449+0.8416  # 2.4865 MDE-Faktor P-1
print("Zmde",Z)
# 1) Reversal (vorzeichengedrehter Pilot) auf blinden Fenstern, c=1, reale SD aus GL-035
pilot={"mom1":(0.03847,0.12351),"mom2":(0.05003,0.13015),"mom4":(0.04463,0.13415)}
start=dt.date(2026,10,5)
for v,(x,sd) in pilot.items():
    for f in (1.0,0.75,0.5):
        p=x*f; n=(Z*sd/p)**2
        full=start+dt.timedelta(weeks=2*math.ceil(n))-dt.timedelta(days=1)
        print(v,f,round(p,4),"Wochen/Fenster",round(n,1),"voll",full)
    ir=x/sd*math.sqrt(52); print(v,"impl. IR p.a.",round(ir,2),"t_pilot",round(x/sd*math.sqrt(114),2))
# Literatur-Werte
for p in (0.014,0.020,0.026):
    print("lit",p,round((Z*0.1235/p)**2,1),"Wochen")
# Power je 52-Wochen-Fenster bei Pilot-Magnitude
for v,(x,sd) in pilot.items():
    se=sd/math.sqrt(52); print(v,"Power52",round(N.cdf(x/se-1.6449),3), "MDE80_52",round(Z*se,4))
# Mehrfaktor-Hebel: SD auf Null-Niveau (0.044..0.066 v6b sd_week)
for sdn in (0.05,0.066):
    print("SD",sdn,"Faktor Zeit",round((sdn/0.1235)**2,3))
# 2) Oekonomie Reversal: R_LS = 3.51*IC*sigma_xs, sigma_xs 985 bp
for ic in (0.015,0.02,0.04,0.05):
    print("IC",ic,"R_LS bp/Woche",round(3.51*ic*985,1))
print("LS-SD bp/Woche bei SD_IC 0.1235:",round(3.51*0.1235*985,1))
# 3) A2: Jahre je Fenster fuer C10, MDE80 je 12 Monate skaliert 1/sqrt(Jahre)
for lab,m in (("Einzel",18.25),("Produkt zentral",23.4),("Produkt stress W1",26.1),("Produkt stress W2",27.2)):
    for p in (16.5,20,25,30):
        print("A2",lab,p,"Jahre/Fenster",round((m/p)**2,2))
# 4) H-20: MDE80 bei SE 12-13 bp
for se in (12,13): print("H20 MDE80",round(Z*se,1))
# 5) Weekly VRP Break-even-SD gegen ueberlappendes Tagesdesign: SE_1J = 18.6*sqrt(28.2/365)
se_d=18.6*math.sqrt(28.2/365); print("SE VRP 1J",round(se_d,2),"MDE80",round(Z*se_d,2))
print("Break-even SD_w (52 Wochen nicht ueberlappend):",round(se_d*math.sqrt(52),1))
print("Monatlich nicht ueberlappend SE",round(18.7/math.sqrt(12),2),"MDE80",round(Z*18.7/math.sqrt(12),2))
# 6) Cap-Treffer-Ereignis: N_cluster je Fenster bei SD 985 bp/Woche (sigma_xs als Naeherung)
for eff in (100,200,300,500):
    print("Cap eff",eff,"N_cluster",round((Z*985/eff)**2,1))
# 7) sigma30 Varianzverhaeltnisse
for a,b,n1,n2,lab in ((43.8,42.5,167,874,"Fr/MoDo"),(52.4,42.5,39,874,"MQ/MoDo"),(34.8,42.5,None,None,"WE/MoDo")):
    r=(a/b)**2; s=(a/b)
    out=f"{lab} SD-Verh {s:.3f} Var-Verh {r:.3f}"
    if n1:
        se=math.sqrt(2/(n1-1)+2/(n2-1)); out+=f" z(normal) {math.log(r)/se:.2f}"
    print(out)
# 8) A4: N Zyklen je Fenster
for k in (0.5,0.75,1.0): print("A4 prior/sigma",k,round((Z/k)**2,1))
