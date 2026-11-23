"""Exploratory (task B): where can Gaia-only data NOT separate a luminous-companion
impostor from a dark substellar companion?  Uses only the photocentre relation
a0 = a_rel (B - beta) plx and the CMD excess dMG = -2.5 log10(1+q^n).
Key fact: the equivalent dark mass depends on (M1, q, n) only - P and plx cancel."""
import json, numpy as np, pandas as pd
from scipy.optimize import brentq
MJ=9.546e-4
def m_eq(M1,q,n):
    beta=q**n/(1+q**n); B=q/(1+q)
    lhs=(M1*(1+q))**(1/3)*abs(B-beta)          # a_rel*(B-beta)/P^(2/3)
    f=lambda m:(M1+m)**(1/3)*m/(M1+m)-lhs
    if lhs<=0: return 0.0
    return brentq(f,1e-8,10)/MJ
M1s=np.linspace(0.15,1.4,126); qs=np.linspace(0.30,1.0,141)
d=pd.read_csv('results/dr3_candidates_scored.csv')
sig=float(d.sig_cmd.median())
out={"sig_cmd_median_mag":sig,"by_n":{}}
for n in (3.5,4.0,4.5):
    grid=np.array([[m_eq(M,q,n) for q in qs] for M in M1s])
    hidden=grid<80
    # lowest q that still masquerades below 80 MJ, per M1
    qlo=[float(qs[h].min()) if h.any() else None for h in hidden]
    dmg=-2.5*np.log10(1+np.array([q for q in qlo if q is not None])**n)
    out["by_n"][str(n)]={"q_lo_at_M1":{f"{M:.2f}":ql for M,ql in zip(M1s[::25],qlo[::25])},
        "CMD_excess_range_mag":[float(dmg.max()),float(dmg.min())],
        "CMD_excess_in_sigma":[float(-dmg.max()/sig),float(-dmg.min()/sig)]}
    if n==4.0: G4=grid
# fraction of DR3 candidates whose own sig_cmd leaves twins < 2 sigma in the CMD
out["frac_candidates_twin_below_2sigma"]=float(np.mean(0.75/d.sig_cmd<2))
out["frac_candidates_twin_below_3sigma"]=float(np.mean(0.75/d.sig_cmd<3))
json.dump(out,open('exploratory/blind_spot_map.json','w'),indent=1); print(json.dumps(out,indent=1))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6.4,4.4),dpi=150)
lv=[1,5,13,30,80,200,1000]
cs=ax.contour(qs,M1s,G4,levels=lv,colors='#3b4a6b',linewidths=0.9)
ax.clabel(cs,fmt=lambda v:f"{v:g} MJ",fontsize=7)
ax.contourf(qs,M1s,G4,levels=[0,80],colors=['#e8a33d'],alpha=0.35)
ax.set_xlabel('mass ratio q = M2/M1 of a LUMINOUS companion'); ax.set_ylabel('primary mass M1 [Msun]')
ax.set_title('Gaia-only blind spot: luminous twins that look like <80 MJ dark companions\n(L∝M^4; period and parallax cancel)',fontsize=8.5)
ax.text(0.955,0.3,'blind\nspot',ha='center',fontsize=8,color='#8a5a10')
fig.tight_layout(); fig.savefig('exploratory/blind_spot_map.png')
