"""Bayes FP skorunu Lammers & Winn (2025) müstəqil DR4 mock kataloqlarında yoxlayır."""
import numpy as np, pandas as pd
import fp_score
from fp_score import p_binary
from blind_eval import roc_auc, bootstrap_ci, operating_point, calibration
R = '../../dl/GaiaForecasts/'
pl = pd.read_csv(R+'DR4_mock_exoplanet_catalog.csv'); im = pd.read_csv(R+'DR4_mock_planet_impostor_catalog.csv')
MJ = 9.546e-4; rng = np.random.default_rng(3); import sys; SCAT = float(sys.argv[1]); fp_score.SIG_CMD = SCAT
def a0_mas(mp_MJ, Mstar, P_day, dist_pc):
    m = mp_MJ*MJ; a_rel = ((Mstar+m)*(P_day/365.25)**2)**(1/3)
    return a_rel*(m/(Mstar+m))*(1000.0/dist_pc)
def obs_rows(df, is_imp):
    rows=[]
    for _,r in df.iterrows():
        P = r['Best-fit period [days]']; d = r['MCMC distance 50th [pc]']
        M1 = r['Apparent stellar mass [M_\\odot]'] if is_imp else r['Stellar mass [M_\\odot]']
        mp = r['Best-fit planet mass [M_J]']; a0 = a0_mas(mp, M1, P, d)
        lo, hi = r['MCMC planet mass 16th [M_J]'], r['MCMC planet mass 84th [M_J]']
        a0_err = a0*max((hi-lo)/2/max(mp,1e-3), 0.03)
        dMG_true = (r['Apparent G-band mag'] - r['Primary G-band mag']) if is_imp else 0.0
        rows.append(dict(a0_obs=a0, a0_err=a0_err, P_day=P, plx=1000.0/d, M1=M1, M1_err=0.08,
                         dMG_obs=dMG_true + rng.normal(0, SCAT), r_rvs=None, n_rvs=0, label=int(is_imp)))
    return rows
rows = obs_rows(pl.sample(2000, random_state=0), False) + obs_rows(im, True)
y = np.array([r['label'] for r in rows]); F=[{k:v for k,v in r.items() if k!='label'} for r in rows]
s = np.array([p_binary(f, prior_binary=0.3, n_mc=1500, rng=np.random.default_rng(i)) for i,f in enumerate(F)])
auc = roc_auc(s,y); ci = bootstrap_ci(roc_auc,s,y,n=300)
print(f"Lammers&Winn DR4 mock: {len(y)-y.sum()} planet, {y.sum()} impostor (RVS YOX)")
print(f"AUC = {auc:.3f}  95% CI [{ci[0]:.3f}, {ci[1]:.3f}]")
for ret in (0.90, 0.95):
    op = operating_point(s,y,ret); kb,nb,cib = op['binary_rejection']; kp,npl,_=op['planet_retention']
    print(f"  {kp/npl:.0%} planet saxlama -> impostor atilma {kb}/{nb} = {kb/nb:.0%} (CI {cib[0]:.0%}-{cib[1]:.0%})")
cal, br = calibration(s,y); print("  Brier=%.3f"%br, [(c[0],c[2],round(c[3],2),round(c[4],2)) for c in cal])
dMG = np.array([f['dMG_obs'] for f in F]) 
print(f"Baseline (yalniz CMD izafi parlaqliq): AUC = {roc_auc(-dMG,y):.3f}")
imp_dm = im['Apparent G-band mag']-im['Primary G-band mag']
print(f"Impostorlarin heqiqi izafi parlaqligi: median {imp_dm.median():.2f} mag, {np.mean(imp_dm>-0.2)*100:.0f}% -0.2 mag-dan zeif")
