import numpy as np, pandas as pd
from rvs_phase_test import simulate_stat, K_sum_kms, auc
R='../../dl/GaiaForecasts/'; rng=np.random.default_rng(5)
im=pd.read_csv(R+'DR4_mock_planet_impostor_catalog.csv'); pl=pd.read_csv(R+'DR4_mock_exoplanet_catalog.csv').sample(1500,random_state=2)
M1,M2=im['Primary stellar mass [M_\\odot]'].values,im['Secondary stellar mass [M_\\odot]'].values
K=K_sum_kms(M1,M2,im['True period [days]'].values,im['True eccentricity'].values,im['True inclination [deg]'].values)
f=10**(-0.4*im['Secondary G-band mag'])/(10**(-0.4*im['Primary G-band mag'])+10**(-0.4*im['Secondary G-band mag']))
dm_imp=(im['Apparent G-band mag']-im['Primary G-band mag']).values
n_ep, sm = 40, 4.0
rb=np.array([simulate_stat(True,r['True period [days]'],r['True eccentricity'],r['True T_peri [days]'],r['True omega [deg]'],K[i],f.iloc[i],n_ep,sm,rng) for i,(_,r) in enumerate(im.iterrows())])
rp=np.array([simulate_stat(False,r['True period [days]'],r['True eccentricity'],r['True T_peri [days]'],r['True omega [deg]'],0,0,n_ep,sm,rng) for _,r in pl.iterrows()])
zr=lambda r: np.arctanh(np.clip(r,-.999,.999))*np.sqrt(n_ep-3)        # H_p altında ~N(0,1)
print(f"RVS: n_epoch={n_ep}, sigma_meas={sm} km/s")
print(" CMD scatter | AUC CMD | AUC RVS | AUC CMD+RVS (z cemi) | 95% planet saxlamada impostor atilma: CMD -> CMD+RVS")
for sc in (0.2,0.35,0.5,0.7):
    cb=-(dm_imp+rng.normal(0,sc,len(dm_imp)))/sc; cp=-(rng.normal(0,sc,len(rp)))/sc   # z_CMD: daha parlaq => böyük
    sb, sp = cb+zr(rb), cp+zr(rp)
    def rej(pos,neg): thr=np.quantile(neg,0.95); return np.mean(pos>thr)
    print(f"   {sc:4.2f}     |  {auc(cb,cp):.3f}  |  {auc(zr(rb),zr(rp)):.3f}  |  {auc(sb,sp):.3f}              |  {rej(cb,cp):.0%} -> {rej(sb,sp):.0%}")
