"""Exploratory (not pre-registered): is Gaia DR3 1878822452815621120's 1009 d
'dark companion' (K_ast~0.41 km/s) visible in the 79 CfA RVs of SB9/SBX 2188?"""
import json, numpy as np, pandas as pd
from scipy.optimize import least_squares
d = pd.read_csv('realdata/external/sbx_2188_velocities.csv')
t, v, s = d.epoch_rjd.values, d.rv_kms.values, d.err_kms.values

def kep(t, P, e, T0, w, K):
    M = 2*np.pi*(t-T0)/P; E = M.copy()
    for _ in range(60): E = E-(E-e*np.sin(E)-M)/(1-e*np.cos(E))
    nu = 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))
    return K*(np.cos(nu+w)+e*np.cos(w))

def model(p, t, n2):
    P,e,T0,w,K,g = p[:6]; m = g+kep(t,P,e,T0,w,K)
    if n2: m = m + kep(t,*p[6:11])
    return m

def fit(p0, lo, hi, n2):
    r = least_squares(lambda p:(v-model(p,t,n2))/s, p0, bounds=(lo,hi))
    return r.x, np.sum(r.fun**2)

p0=[3977,0.33,47342,np.radians(260),2.69,-43.57]
lo=[3000,0,45000,-10,0.5,-50]; hi=[6000,0.9,50000,10,6,-38]
p1, c1 = fit(p0, lo, hi, False)
res = v-model(p1,t,False)
out = {"n":len(t),"span_d":float(np.ptp(t)),
 "single_orbit":{"P":p1[0],"e":p1[1],"K":p1[4],"gamma":p1[5],"chi2":c1,"rms":float(res.std(ddof=6)),
                 "median_err":float(np.median(s))}}

# GLS-style periodogram of residuals (sinusoid power) 300-3000 d
from astropy.timeseries import LombScargle
f = np.linspace(1/3000, 1/300, 20000)
pw = LombScargle(t,res,s).power(f)
out["resid_peak_period"] = float(1/f[pw.argmax()]); out["resid_peak_power"]=float(pw.max())
out["resid_FAP_peak"] = float(LombScargle(t,res,s).false_alarm_probability(pw.max(),minimum_frequency=f[0],maximum_frequency=f[-1]))

# Joint 2-Keplerian with Gaia companion: P~1009, e=0.446 fixed-ish; grid over phase
best=None
for P2 in np.linspace(871,1147,13):          # 1009 +- 1 sigma
  for T in np.linspace(0,P2,24,endpoint=False):
    for w2 in np.radians([352.19, 172.19]):  # Gaia omega (and pi-flip ambiguity)
      q=list(p1)+[P2,0.4456,47000+T,w2,0.3]
      lo2=lo+[P2-1e-6,0.4455,47000+T-1e-3,w2-1e-6,0]; hi2=hi+[P2+1e-6,0.4457,47000+T+1e-3,w2+1e-6,3]
      x,c=fit(q,lo2,hi2,True)
      if best is None or c<best[1]: best=(x,c)
out["two_orbit_best"]={"P2":best[0][6],"K2":best[0][10],"chi2":best[1],"dchi2":c1-best[1]}

# Injection–recovery upper limit: K at which a 1009 d, e=0.446 signal is detected
# (dchi2 > 99th pct of no-signal dchi2) in >=95% of random phases
rng=np.random.default_rng(52)
def dchi2_for(vsim):
    global v
    v0=v; v=vsim
    a,ca=fit(p1,lo,hi,False)
    bb=None
    for T in np.linspace(0,1009,12,endpoint=False):
        for w2 in np.radians([352.19,172.19]):
            q=list(a)+[1009.3,0.4456,47000+T,w2,0.3]
            lo2=lo+[1009.299,0.4455,47000+T-1e-3,w2-1e-6,0]; hi2=hi+[1009.301,0.4457,47000+T+1e-3,w2+1e-6,3]
            x,c=fit(q,lo2,hi2,True); bb=c if bb is None else min(bb,c)
    v=v0; return ca-bb
base = model(p1,t,False); jit=np.sqrt(max(out["single_orbit"]["rms"]**2-np.mean(s**2),0))
null=[dchi2_for(base+rng.normal(0,np.sqrt(s**2+jit**2))) for _ in range(60)]
thr=float(np.percentile(null,99)); out["null_dchi2_99"]=thr
rec={}
for K in [0.2,0.3,0.41,0.5]:
    det=0
    for i in range(30):
        T=rng.uniform(0,1009.3); w2=np.radians(352.19 if i%2 else 172.19)
        sim=base+kep(t,1009.3,0.4456,47000+T,w2,K)+rng.normal(0,np.sqrt(s**2+jit**2))
        det+= dchi2_for(sim)>thr
    rec[str(K)]=det/30
out["recovery_fraction"]=rec; out["jitter_kms"]=jit
out={k:(float(x) if isinstance(x,(np.floating,)) else x) for k,x in out.items()}
json.dump(out,open('exploratory/sbx2188_residuals.json','w'),indent=1,default=float)
print(json.dumps(out,indent=1,default=float))
