"""
hier_em.py — GAIA-FP v2: physics likelihoods + a population prior pi(x) learned WITHOUT labels.

Idea: for every candidate i we have a physics likelihood ratio LR_i = p(data_i | impostor) / p(data_i | planet)
(CMD over-luminosity + phase-locked RVS width). The prior probability of being an impostor depends on
demographics x_i = (G, log P, e, log d, log M_fit). We model logit pi(x) = w . phi(x) and fit w by EM on the
UNLABELLED candidate list:
    E-step  r_i = pi_i LR_i / (pi_i LR_i + 1 - pi_i)
    M-step  weighted logistic regression of r_i on phi(x_i)
Outputs: posterior P(impostor)_i = r_i, and the sample contamination  C = mean(r_i)  with bootstrap CI.

Experiments (Lammers & Winn 2025 DR4 mocks; impostors split 50/50 into train/test halves):
  E1  contamination recovery for true contamination 10–50%
  E2  stress tests, ML trained on the train half vs GAIA-FP on the test half:
        (a) same distribution
        (b) demographic shift: impostor demographics re-weighted to look like planets
        (c) noise shift: true CMD scatter 0.45 mag while ML was trained at 0.30
"""
import sys, json, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import norm
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
import benchmark as B   # reuse observation model (module runs its own benchmark at import -> guarded below)

def build(planets, imps, sig, seed):
    B.SIG = sig; B.rng = np.random.default_rng(seed)
    X = pd.concat([B.features(planets, False), B.features(imps, True)], ignore_index=True)
    ok = np.isfinite(X[['P', 'e', 'mfit', 'd', 'G', 'dm']].values).all(1) & (X['P'] > 0) & (X['d'] > 0)
    return X[ok].reset_index(drop=True)

qg = np.linspace(0.5, 1, 200); mu_cmd = -2.5*np.log10(1+qg**4); mu_z = np.linspace(0, 6, 200)
def llr(X, sig):
    dm = X['dm'].values; z = X['z'].values
    l = np.log(np.mean(norm.pdf(dm[:, None], mu_cmd[None, :], sig), axis=1)) - norm.logpdf(dm, 0, sig)
    m = np.isfinite(z)
    l[m] += np.log(np.mean(norm.pdf(z[m][:, None], mu_z[None, :], 1), axis=1)) - norm.logpdf(z[m], 0, 1)
    return np.clip(l, -30, 30)

def phi(X):
    F = np.c_[X['G'], np.log(X['P']), X['e'], np.log(X['d']), np.log(np.clip(X['mfit'], 0.1, None))]
    return (F - F.mean(0))/F.std(0)

def em(L, F, iters=200, pi0=0.3, C=1.0):
    pi = np.full(len(L), pi0); lr = LogisticRegression(C=C, max_iter=500)
    for _ in range(iters):
        r = expit(L + logit(np.clip(pi, 1e-4, 1-1e-4)))
        # soft-label logistic regression via duplicated rows with weights
        Xd = np.r_[F, F]; yd = np.r_[np.ones(len(F)), np.zeros(len(F))]; wd = np.r_[r, 1-r]
        lr.fit(Xd, yd, sample_weight=wd); new = lr.predict_proba(F)[:, 1]
        if np.max(np.abs(new-pi)) < 1e-5: pi = new; break
        pi = new
    r = expit(L + logit(np.clip(pi, 1e-4, 1-1e-4)))
    return r, pi

def auc(s, y): return B.roc_auc(s, y)
def rej(s, y, keep=0.95): thr = np.quantile(s[y == 0], keep); return float(np.mean(s[y == 1] > thr))

if __name__ == "__main__":
    out = {}
    im = B.im.sample(frac=1, random_state=11).reset_index(drop=True)
    im_tr, im_te = im.iloc[:len(im)//2], im.iloc[len(im)//2:]
    pl_all = pd.read_csv(B.R+'DR4_mock_exoplanet_catalog.csv').sample(6000, random_state=3).reset_index(drop=True)
    pl_tr, pl_te = pl_all.iloc[:3000], pl_all.iloc[3000:]

    # ---------------- E1: contamination recovery
    print("E1  contamination recovery (unlabelled EM), CMD scatter 0.30")
    Xte = build(pl_te, im_te, 0.30, 21); yte = Xte['y'].values; Lte = llr(Xte, 0.30); Fte = phi(Xte)
    rows = []
    rs = np.random.default_rng(5)
    for c_true in (0.10, 0.20, 0.30, 0.50):
        n_imp = int(round(c_true/(1-c_true)*(yte == 0).sum())); n_imp = min(n_imp, int(yte.sum()))
        idx = np.r_[np.where(yte == 0)[0], rs.choice(np.where(yte == 1)[0], n_imp, replace=False)]
        L, F, y = Lte[idx], Fte[idx], yte[idx]
        r, _ = em(L, F)
        boots = []
        for b in range(40):
            j = rs.integers(0, len(idx), len(idx)); rb, _ = em(L[j], F[j], iters=60); boots.append(rb.mean())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rf = expit(L + logit(0.3))
        print(f"   true {y.mean():.3f} | EM estimate {r.mean():.3f} [{lo:.3f},{hi:.3f}] | fixed-prior mean {rf.mean():.3f} | AUC EM {auc(r,y):.3f} fixed {auc(rf,y):.3f}")
        rows.append(dict(true=float(y.mean()), est=float(r.mean()), ci=[float(lo), float(hi)], fixed=float(rf.mean()), auc_em=auc(r, y), auc_fixed=auc(rf, y)))
    out['E1'] = rows

    # ---------------- E2: stress tests
    print("\nE2  ML trained on train half (CMD scatter 0.30) vs GAIA-FP, evaluated on the test half")
    Xtr = build(pl_tr, im_tr, 0.30, 7)
    cols = ['P', 'e', 'mfit', 'd', 'G', 'dm', 'z']
    ml = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05).fit(Xtr[cols].values, Xtr['y'].values)

    def evaluate(X, sig, tag):
        y = X['y'].values; L = llr(X, sig); r, _ = em(L, phi(X))
        s = dict(ML=ml.predict_proba(X[cols].values)[:, 1], fixed=L, em=r)
        line = {k: (auc(v, y), rej(v, y)) for k, v in s.items()}
        print(f"  {tag:34s} ML {line['ML'][0]:.3f}/{line['ML'][1]:.0%} | GAIA-FP fixed {line['fixed'][0]:.3f}/{line['fixed'][1]:.0%} | GAIA-FP v2 EM {line['em'][0]:.3f}/{line['em'][1]:.0%}")
        return {k: dict(auc=v[0], rej95=v[1]) for k, v in line.items()}

    print("   (AUC / impostor rejection at 95% planet retention)")
    E2 = {}
    E2['a_same'] = evaluate(Xte, 0.30, '(a) same distribution')
    # (b) demographic shift: re-weight impostors so their demographics match planets
    dem = ['G', 'P', 'e', 'd', 'mfit']
    clf = HistGradientBoostingClassifier(max_iter=200).fit(Xte[dem].values, yte)
    p = np.clip(clf.predict_proba(Xte[dem].values)[:, 1], 0.02, 0.98)
    w = ((1-p)/p)[yte == 1]; w /= w.sum()
    imp_idx = np.where(yte == 1)[0]; pick = np.random.default_rng(9).choice(imp_idx, len(imp_idx), p=w)
    Xb = pd.concat([Xte[yte == 0], Xte.iloc[pick]], ignore_index=True)
    E2['b_demographic_shift'] = evaluate(Xb, 0.30, '(b) demographic shift')
    # (c) noise shift
    Xc = build(pl_te, im_te, 0.45, 33)
    E2['c_noise_shift'] = evaluate(Xc, 0.45, '(c) CMD scatter 0.45 (ML saw 0.30)')
    out['E2'] = E2
    json.dump(out, open('../results/hier_em_results.json', 'w'), indent=1)
