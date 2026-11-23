"""Exploratory: can the 3977 d stellar orbit masquerade as a ~1000 d orbit in the
1038 d DR3 window? Photocentre of the long orbit minus best quadratic (what
proper motion + acceleration would absorb), over all orbital phases."""
import json, numpy as np
P,e,K,w=3977.,0.332,2.687,np.radians(260.)
M1,plx=0.82365,1000/62.3778
fm=1.0361e-7*K**3*P*(1-e*e)**1.5
from scipy.optimize import brentq
def m2_of(i): return brentq(lambda m:(m*np.sin(i))**3/(M1+m)**2-fm,1e-4,5)
def orbit_xy(tt,tp,i,Om=0.0):
    Mn=2*np.pi*(tt-tp)/P; E=Mn.copy()
    for _ in range(60): E=E-(E-e*np.sin(E)-Mn)/(1-e*np.cos(E))
    X=np.cos(E)-e; Y=np.sqrt(1-e*e)*np.sin(E)
    # Thiele-Innes for unit semi-major axis
    A=np.cos(w)*np.cos(Om)-np.sin(w)*np.sin(Om)*np.cos(i); B=np.cos(w)*np.sin(Om)+np.sin(w)*np.cos(Om)*np.cos(i)
    F=-np.sin(w)*np.cos(Om)-np.cos(w)*np.sin(Om)*np.cos(i); G=-np.sin(w)*np.sin(Om)+np.cos(w)*np.cos(Om)*np.cos(i)
    return A*X+F*Y, B*X+G*Y
tt=np.linspace(0,1038,300)
out={"f_m_Msun":fm}
for inc in [30,60,84]:
    i=np.radians(inc); m2=m2_of(i); Mt=M1+m2
    arel=(P/365.25)**(2/3)*Mt**(1/3); a0=arel*m2/Mt*plx   # dark-ish M dwarf: beta~0
    amps=[]
    for tp in np.linspace(0,P,200,endpoint=False):
        x,y=orbit_xy(tt,tp,i)
        r=[]
        for c in (x,y):
            co=np.polyfit(tt,c,2); r.append(c-np.polyval(co,tt))
        amps.append(a0*np.max(np.hypot(*r)))
    amps=np.array(amps)
    out[f"inc{inc}"]={"m2_Msun":m2,"a0_mas":a0,"nonquad_resid_mas_median":float(np.median(amps)),
      "frac_phases_resid_ge_0.3mas":float(np.mean(amps>=0.3)),"frac_ge_0.55":float(np.mean(amps>=0.55))}
print(json.dumps(out,indent=1)); json.dump(out,open('exploratory/sbx2188_alias.json','w'),indent=1)
