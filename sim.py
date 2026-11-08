"""
sim.py — configurable observation model on top of the Lammers & Winn (2025) mock catalogues.
SIMULATED DATA ONLY. Generalises benchmark.features() so that distribution shifts can be applied:

cfg keys (defaults = DR4-like):
  sig_cmd      : CMD over-luminosity scatter [mag]                          (0.30)
  g_rvs_lim    : faintest G with RVS epoch line widths                      (13.0)
  nep          : (lo, hi) number of RVS epochs                              ((25, 46))
  span         : time span of RVS epochs [d]                                (2000)
  rvs_noise    : multiplier on per-epoch line-width precision               (1.0)
  drop_rvs     : remove RVS modality entirely                               (False)
  wide_frac    : fraction of PLANET hosts given an unresolved wide stellar companion (H_pw)   (0.0)
  own_sigP     : use each candidate's own MCMC period uncertainty in the RVS template (v3.1); else fixed 1%  (False)

Every row also carries TRUE quantities (prefixed t_) used only by the follow-up simulator to generate
outcomes; the scorer never reads them.
"""
import numpy as np, pandas as pd
from rvs_phase_test import simulate_stat, K_sum_kms
from benchmark import sig_rvs, a0_mas, MJ

DEFAULT = dict(sig_cmd=0.30, g_rvs_lim=13.0, nep=(25, 46), span=2000.0, rvs_noise=1.0, drop_rvs=False, wide_frac=0.0)
G_GRAV = 2.959122e-4

def load(release='DR4', n_planets=None, seed=0, R='../dl/GaiaForecasts/'):
    im = pd.read_csv(R+f'{release}_mock_planet_impostor_catalog.csv')
    pl = pd.read_csv(R+f'{release}_mock_exoplanet_catalog.csv')
    if n_planets: pl = pl.sample(n_planets, random_state=seed)
    return pl.reset_index(drop=True), im.reset_index(drop=True)

def features(df, imp, cfg=None, seed=0):
    c = dict(DEFAULT); c.update(cfg or {}); rng = np.random.default_rng(seed)
    n = len(df)
    G = (df['Apparent G-band mag'] if imp else df['G-band mag']).values.astype(float)
    M = (df['Apparent stellar mass [M_\\odot]'] if imp else df['Stellar mass [M_\\odot]']).values
    P = df['Best-fit period [days]'].values; e = df['Best-fit eccentricity'].values
    d = df['MCMC distance 50th [pc]'].values; mfit = df['Best-fit planet mass [M_J]'].values
    a0 = a0_mas(mfit, M, P, d)
    a0err = a0*np.maximum((df['MCMC planet mass 84th [M_J]'].values - df['MCMC planet mass 16th [M_J]'].values)/2/np.maximum(mfit, 1e-3), 0.05)
    Pt, et, it, Tt, wt = (df['True period [days]'].values, df['True eccentricity'].values, df['True inclination [deg]'].values,
                          df['True T_peri [days]'].values, df['True omega [deg]'].values)
    dtrue = df['True distance [pc]'].values
    sigP = np.clip((df['MCMC period 84th [days]'].values - df['MCMC period 16th [days]'].values)/2/P, 1e-4, 0.5) if c.get('own_sigP', False) else np.full(n, 0.01)
    cls = np.full(n, 'p') if not imp else np.full(n, 't')
    if imp:
        M1, M2 = df['Primary stellar mass [M_\\odot]'].values, df['Secondary stellar mass [M_\\odot]'].values
        K = K_sum_kms(M1, M2, Pt, et, it)
        L1 = 10**(-0.4*df['Primary G-band mag'].values); L2 = 10**(-0.4*df['Secondary G-band mag'].values); f = L2/(L1+L2)
        dm_true = (df['Apparent G-band mag'] - df['Primary G-band mag']).values
        arel = (G_GRAV*(M1+M2)*Pt**2/(4*np.pi**2))**(1/3)
    else:
        K = np.zeros(n); f = np.zeros(n); dm_true = np.zeros(n)
        Ms = df['Stellar mass [M_\\odot]'].values; mp = df['True planet mass [M_J]'].values*MJ
        arel = (G_GRAV*(Ms+mp)*Pt**2/(4*np.pi**2))**(1/3)
        # H_pw: planet host with an unresolved, wide (non-orbiting on DR4 timescales) stellar companion
        wide = rng.random(n) < c['wide_frac']
        qw = rng.uniform(0.3, 1.0, n); nw = rng.uniform(2, 6, n)
        dm_true = np.where(wide, -2.5*np.log10(1+qw**nw), 0.0)
        G = G + dm_true
        cls = np.where(wide, 'w', 'p')
        sig0_extra = np.where(wide, rng.uniform(0, 30, n), 0.0)   # constant extra line width from the companion
    dm = dm_true + rng.normal(0, c['sig_cmd'], n)
    has = (G <= c['g_rvs_lim']) & (not c['drop_rvs'])
    nep = rng.integers(c['nep'][0], c['nep'][1], n)
    srv = sig_rvs(G)*c['rvs_noise']
    z = np.full(n, np.nan)
    for i in np.where(has)[0]:
        if imp:
            s = simulate_stat(True, Pt[i], et[i], Tt[i], wt[i], K[i], f[i], int(nep[i]), float(srv[i]), rng, span=c['span'], dP=float(sigP[i]))
        else:
            sig0 = np.sqrt(11.0**2 + 0.25*sig0_extra[i]**2)
            s = simulate_stat(False, Pt[i], et[i], Tt[i], wt[i], 0.0, 0.0, int(nep[i]), float(srv[i]), rng, sig0=sig0, span=c['span'], dP=float(sigP[i]))
        z[i] = np.arctanh(np.clip(s, -.999, .999))*np.sqrt(nep[i]-3)
    X = pd.DataFrame(dict(P=P, e=e, mfit=mfit, d=d, G=G, dm=dm, z=z, M=M,
                          inc=df['Best-fit inclination [deg]'].values, T0=df['Best-fit T_peri [days]'].values,
                          om=df['Best-fit omega [deg]'].values, nep=np.where(has, nep, 0), srv=srv, span=c['span'],
                          a0=a0, a0err=a0err, sigP=sigP, y=int(imp), cls=cls,
                          t_K=K, t_f=f, t_dm=dm_true, t_arel=arel, t_plx=1000/dtrue, t_P=Pt, t_e=et, t_inc=it))
    ok = np.isfinite(X[['P', 'e', 'mfit', 'd', 'G', 'dm', 'a0']].values).all(1) & (X['P'] > 0) & (X['d'] > 0) & (X['a0'] > 0)
    return X[ok].reset_index(drop=True)

def build(pl, im, cfg=None, seed=0):
    return pd.concat([features(pl, False, cfg, seed), features(im, True, cfg, seed+1)], ignore_index=True)
