"""
benchmark.py — GAIA-FP vs baselines on the independent Lammers & Winn (2025) DR4 mock catalogues,
with a more realistic observation model than combo_lr.py:

  * CMD over-luminosity measured with scatter SIG (astrophysical + photometric)
  * RVS epoch line widths only for bright stars (G <= G_RVS_LIM); per-epoch precision grows with G
  * n_RVS ~ U(25, 45) epochs
Baselines
  B1 RUWE proxy       : RUWE^2 = 1 + 0.5 (a0/sigma_AL)^2, sigma_AL(G) from a simple error model
  B2 CMD-only LR      : same physics LR as GAIA-FP, without RVS
  B3 ML (gradient boosting, 5-fold CV) on [P, e, M_fit, distance, G, dM_G, z_RVS(if any)]
  B4 random
GAIA-FP: log LR_CMD + log LR_RVS (physics priors, nothing fitted to the mocks).
"""
import sys, json, numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from rvs_phase_test import simulate_stat, K_sum_kms
from blind_eval import roc_auc, clopper_pearson

R = '../dl/GaiaForecasts/'; MJ = 9.546e-4
try:
    SIG = float(sys.argv[1]) if len(sys.argv) > 1 else 0.30
except ValueError:
    SIG = 0.30
G_RVS_LIM = 13.0
rng = np.random.default_rng(2026)

im = pd.read_csv(R+'DR4_mock_planet_impostor_catalog.csv')
pl = pd.read_csv(R+'DR4_mock_exoplanet_catalog.csv').sample(3000, random_state=7)

def sig_al(G):  # per-epoch along-scan precision [mas], rough Gaia-like curve
    return 0.10*np.sqrt(1 + 10**(0.4*(np.clip(G, 6, 21)-13)))

def sig_rvs(G):  # per-epoch line-width precision [km/s]
    return np.interp(G, [8, 10, 12, 13], [1.5, 2.5, 5.0, 8.0])

def a0_mas(mp, M, P, d):
    m = mp*MJ; a = ((M+m)*(P/365.25)**2)**(1/3); return a*(m/(M+m))*(1000/d)

def features(df, imp):
    n = len(df)
    G = (df['Apparent G-band mag'] if imp else df['G-band mag']).values
    M = (df['Apparent stellar mass [M_\\odot]'] if imp else df['Stellar mass [M_\\odot]']).values
    P = df['Best-fit period [days]'].values; e = df['Best-fit eccentricity'].values
    d = df['MCMC distance 50th [pc]'].values; mfit = df['Best-fit planet mass [M_J]'].values
    a0 = a0_mas(mfit, M, P, d)
    ruwe = np.sqrt(1 + 0.5*(a0/sig_al(G))**2/40)      # 40 ~ effective epochs averaging
    dm_true = (df['Apparent G-band mag'] - df['Primary G-band mag']).values if imp else np.zeros(n)
    dm = dm_true + rng.normal(0, SIG, n)
    has = G <= G_RVS_LIM
    z = np.full(n, np.nan); nep = rng.integers(25, 46, n)
    if imp:
        K = K_sum_kms(df['Primary stellar mass [M_\\odot]'].values, df['Secondary stellar mass [M_\\odot]'].values,
                      df['True period [days]'].values, df['True eccentricity'].values, df['True inclination [deg]'].values)
        L1 = 10**(-0.4*df['Primary G-band mag'].values); L2 = 10**(-0.4*df['Secondary G-band mag'].values); f = L2/(L1+L2)
    for i in np.where(has)[0]:
        r = df.iloc[i]
        s = simulate_stat(imp, r['True period [days]'], r['True eccentricity'], r['True T_peri [days]'], r['True omega [deg]'],
                          K[i] if imp else 0.0, f[i] if imp else 0.0, int(nep[i]), float(sig_rvs(G[i])), rng)
        z[i] = np.arctanh(np.clip(s, -.999, .999))*np.sqrt(nep[i]-3)
    inc = df['Best-fit inclination [deg]'].values; T0 = df['Best-fit T_peri [days]'].values; om = df['Best-fit omega [deg]'].values
    return pd.DataFrame(dict(P=P, e=e, mfit=mfit, d=d, G=G, dm=dm, z=z, ruwe=ruwe, M=M, inc=inc, T0=T0, om=om,
                             nep=np.where(has, nep, 0), srv=sig_rvs(G), a0=a0,
                             a0err=a0*np.maximum((df['MCMC planet mass 84th [M_J]'].values-df['MCMC planet mass 16th [M_J]'].values)/2/np.maximum(mfit,1e-3), 0.05),
                             y=int(imp)))

def main():
    global SIG
    X = pd.concat([features(pl, False), features(im, True)], ignore_index=True)
    y = X['y'].values

    qg = np.linspace(0.5, 1, 200); mu_cmd = -2.5*np.log10(1+qg**4); mu_z = np.linspace(0, 6, 200)
    def llr_cmd(dm, sc=SIG): return np.log(np.mean(norm.pdf(dm[:, None], mu_cmd[None, :], sc), axis=1)) - norm.logpdf(dm, 0, sc)
    def llr_rvs(z):
        out = np.zeros_like(z); m = np.isfinite(z)
        out[m] = np.log(np.mean(norm.pdf(z[m][:, None], mu_z[None, :], 1), axis=1)) - norm.logpdf(z[m], 0, 1)
        return out

    S = {}
    S['B1 RUWE proxy'] = X['ruwe'].values
    S['B2 CMD-only (physics LR)'] = llr_cmd(X['dm'].values)
    feat = X[['P', 'e', 'mfit', 'd', 'G', 'dm', 'z']].values
    S['B3 ML gradient boosting (5-fold CV)'] = cross_val_predict(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05),
                                             feat, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]
    S['B4 random'] = rng.random(len(y))
    S['GAIA-FP (CMD + RVS width, physics LR)'] = S['B2 CMD-only (physics LR)'] + llr_rvs(X['z'].values)

    def rej_at(score, y, keep=0.95):
        thr = np.quantile(score[y == 0], keep); k = int(np.sum(score[y == 1] > thr)); n = int(np.sum(y == 1))
        return k/n, clopper_pearson(k, n)

    def boot_auc(s, y, n=300, seed=1):
        r = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]; v = []
        for _ in range(n):
            i = np.r_[r.choice(pos, len(pos)), r.choice(neg, len(neg))]; v.append(roc_auc(s[i], y[i]))
        return np.percentile(v, [2.5, 97.5])

    bright = X['G'].values <= G_RVS_LIM
    res = dict(sig_cmd=SIG, n_planet=int((y == 0).sum()), n_imp=int(y.sum()), frac_rvs=float(bright.mean()), rows=[])
    print(f"CMD scatter {SIG} mag | {res['n_planet']} planets, {res['n_imp']} impostors | RVS available for {bright.mean():.0%}")
    print(f"{'method':42s} {'AUC all':>8s} {'95% CI':>15s} {'rej@95%':>8s} | {'AUC bright':>10s} {'rej@95% bright':>14s}")
    for k, s in S.items():
        a = roc_auc(s, y); ci = boot_auc(s, y); r, _ = rej_at(s, y)
        ab = roc_auc(s[bright], y[bright]); rb, _ = rej_at(s[bright], y[bright])
        print(f"{k:42s} {a:8.3f}  [{ci[0]:.3f},{ci[1]:.3f}] {r:8.0%} | {ab:10.3f} {rb:14.0%}")
        res['rows'].append(dict(method=k, auc=a, ci=list(ci), rej95=r, auc_bright=ab, rej95_bright=rb))
    json.dump(res, open(f'../results/benchmark_sig{SIG:.2f}.json', 'w'), indent=1)
    np.save(f'../results/llr_sig{SIG:.2f}.npy', np.c_[S['GAIA-FP (CMD + RVS width, physics LR)'], y, X['mfit'].values, X['P'].values, X['G'].values])

if __name__ == "__main__":
    main()
