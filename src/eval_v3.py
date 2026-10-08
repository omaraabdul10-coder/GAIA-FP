"""eval_v3.py — GAIA-FP v1 (generic RVS prior), v2 (physics RVS), v3 (joint a0|CMD + physics RVS) and v3+EM vs an ML classifier trained on the simulator; stress tests; label-free contamination recovery. Lammers & Winn (2025) DR4 mocks."""
import json, sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import norm
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier
import benchmark as B, hier_em as H
from rvs_predict import llr_rvs_physics
from joint_lr import llr_a0_cmd

def llr_cmd(X, sig):
    dm = X['dm'].values
    return np.log(np.mean(norm.pdf(dm[:, None], H.mu_cmd[None, :], sig), axis=1)) - norm.logpdf(dm, 0, sig)
def llr_rvs_v1(X):
    z = X['z'].values; out = np.zeros(len(z)); m = np.isfinite(z)
    out[m] = np.log(np.mean(norm.pdf(z[m][:, None], H.mu_z[None, :], 1), axis=1)) - norm.logpdf(z[m], 0, 1); return out
def llr_rvs_v2(X, seed):
    rng = np.random.default_rng(seed); return np.array([llr_rvs_physics(r, rng=rng) for _, r in X.iterrows()])

def scores(X, sig, seed):
    c = llr_cmd(X, sig); r2 = llr_rvs_v2(X, seed)
    j = llr_a0_cmd(X['a0'].values, X['a0err'].values, X['P'].values, X['M'].values, X['d'].values, X['dm'].values, sig)
    return dict(cmd=np.clip(c, -30, 30), v1=np.clip(c + llr_rvs_v1(X), -30, 30), v2=np.clip(c + r2, -30, 30),
                v3_joint_a0=j, v3=np.clip(j + r2, -30, 30))

auc, rej = H.auc, H.rej
def em_const(L, pi=0.3):
    for _ in range(500):
        r = expit(L + logit(pi)); pi = float(np.clip(r.mean(), 1e-4, 1-1e-4))
    return expit(L + logit(pi))
out = {}
im = B.im.sample(frac=1, random_state=11).reset_index(drop=True); im_tr, im_te = im.iloc[:len(im)//2], im.iloc[len(im)//2:]
pl = pd.read_csv(B.R+'DR4_mock_exoplanet_catalog.csv').sample(6000, random_state=3).reset_index(drop=True); pl_tr, pl_te = pl.iloc[:3000], pl.iloc[3000:]

Xtr = H.build(pl_tr, im_tr, 0.30, 7)
cols = ['P', 'e', 'mfit', 'd', 'G', 'dm', 'z']
ml = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05).fit(Xtr[cols].values, Xtr['y'].values)

def evaluate(X, sig, tag, seed):
    y = X['y'].values; S = scores(X, sig, seed); r, _ = H.em(S['v3'], H.phi(X))
    S['v3+EM'] = r; S['ML (trained on simulator)'] = ml.predict_proba(X[cols].values)[:, 1]
    br = X['nep'].values > 0
    res = {k: dict(auc=auc(v, y), rej95=rej(v, y), auc_bright=auc(v[br], y[br]), rej95_bright=rej(v[br], y[br])) for k, v in S.items()}
    print(f"\n{tag}  (n_planet={int((y==0).sum())}, n_imp={int(y.sum())}, RVS for {br.mean():.0%})")
    for k, v in res.items():
        print(f"   {k:28s} AUC {v['auc']:.3f}  rej@95% {v['rej95']:.0%} | bright: AUC {v['auc_bright']:.3f} rej {v['rej95_bright']:.0%}")
    return res, S

Xte = H.build(pl_te, im_te, 0.30, 21)
out['a_same'], S_a = evaluate(Xte, 0.30, '(a) same distribution, CMD scatter 0.30', 1)
y = Xte['y'].values
for k in ('v1', 'v2', 'v3'):
    L = S_a[k]; print(f"   LR check {k}: E_planet[LR]={np.mean(np.exp(L[y==0])):.2f}  E_imp[1/LR]={np.mean(np.exp(-L[y==1])):.2f}")
# (b) demographic shift
dem = ['G', 'P', 'e', 'd', 'mfit']
clf = HistGradientBoostingClassifier(max_iter=200).fit(Xte[dem].values, y)
p = np.clip(clf.predict_proba(Xte[dem].values)[:, 1], 0.02, 0.98); w = ((1-p)/p)[y == 1]; w /= w.sum()
pick = np.random.default_rng(9).choice(np.where(y == 1)[0], int(y.sum()), p=w)
Xb = pd.concat([Xte[y == 0], Xte.iloc[pick]], ignore_index=True)
out['b_demog'], _ = evaluate(Xb, 0.30, '(b) demographic shift', 2)
Xc = H.build(pl_te, im_te, 0.45, 33)
out['c_noise'], _ = evaluate(Xc, 0.45, '(c) CMD scatter 0.45 (ML trained at 0.30)', 3)

# contamination recovery with v2 likelihoods
print("\nContamination recovery (EM, no labels), test half, CMD scatter 0.30")
L = S_a['v3']; F = H.phi(Xte); rs = np.random.default_rng(5); rows = []
pi_, ii_ = np.where(y == 0)[0], np.where(y == 1)[0]
for c in (0.05, 0.10, 0.20, 0.30, 0.45):
    n_i = len(ii_); n_p = int(round(n_i*(1-c)/c))
    if n_p > len(pi_): n_p = len(pi_); n_i = int(round(n_p*c/(1-c)))
    idx = np.r_[rs.choice(pi_, n_p, replace=False), rs.choice(ii_, n_i, replace=False)]
    r, _ = H.em(L[idx], F[idx]); r0 = em_const(L[idx])
    bo = []
    for b in range(30):
        j = rs.integers(0, len(idx), len(idx)); rb, _ = H.em(L[idx][j], F[idx][j], iters=60); bo.append(rb.mean())
    lo, hi = np.percentile(bo, [2.5, 97.5])
    print(f"   true {y[idx].mean():.3f} -> EM {r.mean():.3f} [{lo:.3f},{hi:.3f}]  (constant-pi EM {r0.mean():.3f})")
    rows.append(dict(true=float(y[idx].mean()), em=float(r.mean()), ci=[float(lo), float(hi)], em_const=float(r0.mean())))
out['contamination'] = rows
json.dump(out, open('../results/v3_results.json', 'w'), indent=1, default=float)
