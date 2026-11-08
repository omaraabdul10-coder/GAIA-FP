"""CMD + RVS: sadə z-cəmi vs Bayes ehtimal nisbəti (LR). Priorlar FİZİKADAN gəlir, mock-dan tənzimlənmir."""
import numpy as np, pandas as pd
from scipy.stats import norm
from rvs_phase_test import simulate_stat, K_sum_kms, auc
R='../../dl/GaiaForecasts/'; rng=np.random.default_rng(5)
im=pd.read_csv(R+'DR4_mock_planet_impostor_catalog.csv'); pl=pd.read_csv(R+'DR4_mock_exoplanet_catalog.csv').sample(1500,random_state=2)
K=K_sum_kms(im['Primary stellar mass [M_\\odot]'].values,im['Secondary stellar mass [M_\\odot]'].values,im['True period [days]'].values,im['True eccentricity'].values,im['True inclination [deg]'].values)
f=(10**(-0.4*im['Secondary G-band mag'])/(10**(-0.4*im['Primary G-band mag'])+10**(-0.4*im['Secondary G-band mag']))).values
dm_imp=(im['Apparent G-band mag']-im['Primary G-band mag']).values
n_ep, sm = 40, 4.0
rb=np.array([simulate_stat(True,r['True period [days]'],r['True eccentricity'],r['True T_peri [days]'],r['True omega [deg]'],K[i],f[i],n_ep,sm,rng) for i,(_,r) in enumerate(im.iterrows())])
rp=np.array([simulate_stat(False,r['True period [days]'],r['True eccentricity'],r['True T_peri [days]'],r['True omega [deg]'],0,0,n_ep,sm,rng) for _,r in pl.iterrows()])
zr=lambda r: np.arctanh(np.clip(r,-.999,.999))*np.sqrt(n_ep-3)
# --- fiziki priorlar
qg=np.linspace(0.5,1,200); mu_cmd=-2.5*np.log10(1+qg**4)              # H_t: q~U(0.5,1)
mu_z=np.linspace(0,6,200)                                             # H_t: RVS effekti z vahidində U(0,6)
def loglr_cmd(dm,sc): return np.log(np.mean(norm.pdf(dm[:,None],mu_cmd[None,:],sc),axis=1))-norm.logpdf(dm,0,sc)
def loglr_rvs(z):     return np.log(np.mean(norm.pdf(z[:,None],mu_z[None,:],1),axis=1))-norm.logpdf(z,0,1)
def rej(pos,neg): thr=np.quantile(neg,0.95); return np.mean(pos>thr)
print(" scatter | AUC: CMD  z-cem  LR   | 95% planet saxlamada atilma: CMD  z-cem  LR")
for sc in (0.2,0.35,0.5,0.7):
    db=dm_imp+rng.normal(0,sc,len(dm_imp)); dp=rng.normal(0,sc,len(rp))
    cb,cp=loglr_cmd(db,sc),loglr_cmd(dp,sc)
    zb,zp=-db/sc+zr(rb), -dp/sc+zr(rp)
    lb,lpn=cb+loglr_rvs(zr(rb)), cp+loglr_rvs(zr(rp))
    print(f"  {sc:4.2f}   |      {auc(cb,cp):.3f} {auc(zb,zp):.3f} {auc(lb,lpn):.3f} |                    {rej(cb,cp):.0%}   {rej(zb,zp):.0%}   {rej(lb,lpn):.0%}")
