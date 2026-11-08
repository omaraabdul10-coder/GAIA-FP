"""
identifiability.py — when can a substellar companion and a twin-binary impostor be told apart with Gaia data?
SIMULATION / ANALYTIC. Produces results/identifiability.json.

Maps
  A  CMD only     : AUC(impostor vs planet) as a function of mass ratio q and CMD scatter sigma (analytic, n ~ U(2,6))
  B  RVS only     : power of the phase-locked width test (z > 2.33, i.e. 1% false alarm for a planet) vs period and G
  C  RVS only     : power vs eccentricity and number of RVS epochs
  D  joint a0|CMD : AUC vs astrometric S/N of a0 and CMD scatter (does a poorly measured orbit blur the q constraint?)
  E  resolution   : projected separation of planet-mimicking twins vs distance and period (Gaia / AO resolvability)
  F  H_pw vs H_t  : planet host + wide companion vs twin impostor — CMD identical, only RVS phase-locking separates
"""
import json, numpy as np
from scipy.stats import norm
from rvs_phase_test import simulate_stat, K_sum_kms
from benchmark import sig_rvs
from joint_lr import llr_a0_cmd
from blind_eval import roc_auc

rng = np.random.default_rng(12)
out = {}

# ---- A
qs = [0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.99]; sigs = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
nn = np.linspace(2, 6, 41)
A = [[float(np.mean(norm.cdf(2.5*np.log10(1+q**nn)/(s*np.sqrt(2))))) for s in sigs] for q in qs]
out['A_cmd_auc'] = dict(q=qs, sigma=sigs, auc=A)

# ---- B, C
def power(P, G, e=0.3, nep=40, span=2000, q=0.95, M1=0.5, inc=60, n=4.0, N=150):
    K = K_sum_kms(M1, q*M1, P, e, inc); f = q**n/(1+q**n); z = []
    for _ in range(N):
        s = simulate_stat(True, P, e, rng.uniform(0, P), rng.uniform(0, 360), K, f, nep, float(sig_rvs(G)), rng, span=span)
        z.append(np.arctanh(np.clip(s, -.999, .999))*np.sqrt(nep-3))
    return float(np.mean(np.array(z) > 2.326)), float(K)
Ps = [50, 150, 400, 800, 1500, 2500, 4000]; Gs = [8, 9, 10, 11, 12, 13]
B = [[power(P, G)[0] for G in Gs] for P in Ps]
out['B_rvs_power_P_G'] = dict(P=Ps, G=Gs, power=B, K_sum=[power(P, 10, N=1)[1] for P in Ps], note='q=0.95, M1=0.5, e=0.3, i=60, 40 epochs over 2000 d')
es = [0.0, 0.2, 0.4, 0.6, 0.8]; neps = [10, 20, 40, 80]
C = [[power(500, 11, e=e, nep=k)[0] for k in neps] for e in es]
out['C_rvs_power_e_nep'] = dict(e=es, nep=neps, power=C, note='P=500 d, G=11')

# ---- D
def joint_auc(snr, sig, N=600):
    M, P, d = 0.5, 500.0, 50.0; plx = 1000/d
    # impostors: q such that the photocentre mimics a 3-10 MJ planet
    qg = np.linspace(0.85, 1.0, 3000); n_true = rng.uniform(2, 6, N)
    a0_imp, dm_imp = [], []
    for k in range(N):
        n = n_true[k]; lq = qg**n; M1 = M/(1+lq)**(1/n)
        a0g = ((M1*(1+qg))*(P/365.25)**2)**(1/3)*np.abs(qg/(1+qg)-lq/(1+lq))*plx
        target = rng.uniform(0.3, 1.2)  # mas, typical planet-like amplitude at 50 pc
        j = np.argmin(np.abs(a0g-target)); a0_imp.append(a0g[j]); dm_imp.append(-2.5*np.log10(1+qg[j]**n))
    a0_imp = np.array(a0_imp); dm_imp = np.array(dm_imp)
    a0_pl = rng.uniform(0.3, 1.2, N)
    a0_obs = np.r_[a0_pl, a0_imp]; a0_obs = a0_obs*(1 + rng.normal(0, 1/snr, 2*N))
    dm_obs = np.r_[np.zeros(N), dm_imp] + rng.normal(0, sig, 2*N)
    L = llr_a0_cmd(a0_obs, a0_obs/snr, np.full(2*N, P), np.full(2*N, M), np.full(2*N, d), dm_obs, sig)
    y = np.r_[np.zeros(N), np.ones(N)]
    Lc = np.log(np.mean(norm.pdf(dm_obs[:, None], -2.5*np.log10(1+np.linspace(0.5, 1, 200)**4)[None, :], sig), 1)) - norm.logpdf(dm_obs, 0, sig)
    return float(roc_auc(L, y)), float(roc_auc(Lc, y))
snrs = [3, 5, 10, 20, 50]; sigs_d = [0.2, 0.3, 0.45]
D = [[joint_auc(s, g) for g in sigs_d] for s in snrs]
out['D_joint_auc_snr_sigma'] = dict(snr=snrs, sigma=sigs_d, auc_joint_vs_cmdonly=D)

# ---- E
G_ = 2.959122e-4
def rho_mas(P, d, M=0.5, q=0.95):
    a = (G_*M*(1+q)*P**2/(4*np.pi**2))**(1/3); return a*1000/d
ds = [10, 25, 50, 100, 200]; PsE = [100, 300, 1000, 3000]
out['E_separation_mas'] = dict(d=ds, P=PsE, rho=[[round(rho_mas(P, d), 1) for d in ds] for P in PsE],
                               note='semimajor axis of the relative orbit in mas (projected separation is <= this); Gaia resolves pairs only above ~100-200 mas; speckle/AO ~30-50 mas')

# ---- F: wide-companion planet host vs twin: CMD AUC between them and the role of RVS
N = 2000; qw = rng.uniform(0.3, 1, N); nw = rng.uniform(2, 6, N); dm_w = -2.5*np.log10(1+qw**nw)
qt = rng.uniform(0.9, 1, N); nt = rng.uniform(2, 6, N); dm_t = -2.5*np.log10(1+qt**nt)
F = {}
for s in (0.1, 0.3):
    a = roc_auc(np.r_[dm_w, dm_t] + rng.normal(0, s, 2*N), np.r_[np.ones(N), np.zeros(N)])
    F[f'cmd_auc_wide_vs_twin_sigma{s}'] = float(max(a, 1-a))
zt = []
for _ in range(400):
    s_ = simulate_stat(True, 500, 0.3, rng.uniform(0, 500), rng.uniform(0, 360), K_sum_kms(.5, .475, 500, .3, 60), .45, 40, 2.5, rng)
    zt.append(np.arctanh(np.clip(s_, -.999, .999))*np.sqrt(37))
zw = rng.normal(0, 1, 400)
F['rvs_auc_wide_vs_twin_G10_P500'] = float(roc_auc(np.r_[zt, zw], np.r_[np.ones(400), np.zeros(400)]))
out['F_wide_vs_twin'] = F
json.dump(out, open('../results/identifiability.json', 'w'), indent=1)
for k, v in out.items(): print(k, json.dumps(v)[:900])
