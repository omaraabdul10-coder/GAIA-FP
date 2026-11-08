"""
prior_eval.py — compares three population priors on (1) SIMULATED validation mocks and (2) REAL Gaia DR3 (development data).
  fixed : constant pi = 0.3, not fitted (ranking = likelihood ratio)
  EM-C1 : covariate EM, C = 1 (frozen v3.1 method)
  CV    : prior_select (label-free choice of C, C = 0 allowed)
The DR5 held-out mocks are NOT used (already spent once). The DR4 evaluation set is NOT touched.
Writes results/prior_eval.json.
"""
import json, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.special import expit, logit
import sim, lik
from hier_em import em, phi
from blind_eval import roc_auc
import prior_select as PS
from tournament import splits, SIG

def three(L, F):
    out = {'fixed': (expit(L + logit(0.3)), np.full(len(L), 0.3), None)}
    p, pi = em(L, F); out['EM-C1'] = (p, pi, 1.0)
    p, pi, C, sc = PS.posterior(L, F); out['CV'] = (p, pi, C)
    return out

def mock_block(X, sig, name):
    y = X['y'].values; Lt, r = lik.llr_t(X.assign(mfit=X['mfit']), sig, 0); L = lik.effective_llr(Lt, None, 0.0); F = phi(X)
    res = {}
    for k, (p, pi, C) in three(L, F).items():
        res[k] = dict(auc=float(roc_auc(p, y)), brier=float(np.mean((p-y)**2)), contam_est=float(p.mean()),
                      contam_true=float(y.mean()), pi_mean=float(pi.mean()), C=C,
                      err_decided=float(np.mean(((p >= .85) & (y == 0)) | ((p <= .15) & (y == 1)))/max(np.mean((p >= .85) | (p <= .15)), 1e-9)))
    print(name, {k: (round(v['auc'], 3), round(v['brier'], 3), round(v['contam_est'], 3), v['C']) for k, v in res.items()}, 'true', round(y.mean(), 3), flush=True)
    return res

def main():
    R = {'mocks': {}}
    _, val = splits()
    Xv = sim.build(*val, seed=21)
    R['mocks']['nominal'] = mock_block(Xv, SIG, 'nominal')
    R['mocks']['cmd_scatter_0.45'] = mock_block(sim.build(*val, cfg=dict(sig_cmd=0.45), seed=41), 0.45, 'cmd0.45')
    R['mocks']['rvs_missing'] = mock_block(sim.build(*val, cfg=dict(drop_rvs=True), seed=44), SIG, 'rvs_missing')
    Xd = sim.build(*val, cfg=dict(drop_rvs=True, sig_cmd=0.45), seed=45)
    Xs = Xd.copy(); perm = np.random.default_rng(6).permutation(len(Xs))
    for c in ('G', 'P', 'e', 'd', 'mfit'): Xs[c] = Xs[c].values[perm]      # covariates carry no information (DR3-like)
    R['mocks']['uninformative covariates, no RVS, sig 0.45'] = mock_block(Xs, 0.45, 'uninformative-x')
    Xh = Xd[Xd['mfit'] >= Xd['mfit'].median()].reset_index(drop=True)
    R['mocks']['heavy half (m2 >= median), no RVS, sig 0.45'] = mock_block(Xh, 0.45, 'heavy-half')
    # REAL DR3 (development data; exploratory)
    S = pd.read_csv('../results/dr3_candidates_scored.csv')
    L = S['log_lr'].values; F = phi(S); y = S['sb2_any'].astype(int).values
    rng = np.random.default_rng(1); real = {}
    for k, (p, pi, C) in three(L, F).items():
        b = [roc_auc(p[j], y[j]) for j in (rng.integers(0, len(y), len(y)) for _ in range(2000)) if 0 < y[j].sum() < len(j)]
        real[k] = dict(pu_auc=float(roc_auc(p, y)), ci=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                       pi_mean=float(pi.mean()), contam_est=float(p.mean()), C=C,
                       verdicts={'impostor': int((p >= .85).sum()), 'ambiguous': int(((p > .15) & (p < .85)).sum()), 'substellar': int((p <= .15).sum())},
                       recall85=[int((p[y == 1] >= .85).sum()), int(y.sum())])
    _, sc = PS.select(L, F); real['cv_scores'] = {str(k): v for k, v in sc.items()}
    print('DR3', {k: v for k, v in real.items()}, flush=True)
    R['DR3_real_exploratory'] = real
    json.dump(R, open('../results/prior_eval.json', 'w'), indent=1, default=float)

if __name__ == '__main__':
    main()
