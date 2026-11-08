"""
h11_prepare.py: pre-DR4 obligation of DR3_TO_DR4_PREDICTION_PLAN.md (registered in OSF TBJGY):
"the v0.4 prior-selection variant (A1) is scored on DR3 now, on the same rows, and its file hash is added before DR4
as a second prediction set."

Input : results/dr3_candidates_scored.csv (frozen, SHA-256 141734677a64942e...); only log_lr and the prior covariates are used.
Output: results/dr3_candidates_scored_A1.csv (+ .sha256). No label of any kind is read.
Rule  : prior_select.posterior(log_lr, hier_em.phi(X), seed=0)  (amendment v0.4 A1, seed 0), verdict threshold t = 0.15.
Run   : cd src && python h11_prepare.py
"""
import hashlib, json, numpy as np, pandas as pd
import prior_select as PS
from hier_em import phi

FROZEN_SHA = '141734677a64942e38fc8512611c7653eaaa024a2d375524cc7f50b40200a7fc'
T = 0.15

def main(path='../results/dr3_candidates_scored.csv', out='../results/dr3_candidates_scored_A1.csv'):
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    if sha != FROZEN_SHA:
        raise SystemExit(f'frozen prediction file changed: {sha} != {FROZEN_SHA}')
    X = pd.read_csv(path, dtype={'source_id': str})
    L = X['log_lr'].values; F = phi(X)
    assert np.isfinite(L).all() and np.isfinite(F).all(), 'non-finite log_lr or prior covariates'
    p, pi, C_star, cv = PS.posterior(L, F, seed=0)
    assert ((p >= 0) & (p <= 1)).all() and ((pi >= 0) & (pi <= 1)).all(), 'probability outside [0, 1]'
    verdict = np.where(p <= T, 'likely_substellar', np.where(p >= 1 - T, 'likely_impostor', 'ambiguous_followup_needed'))
    Y = pd.DataFrame(dict(source_id=X.source_id, P_impostor_A1=p, prior_pi_A1=pi, verdict_A1=verdict))
    Y.to_csv(out, index=False)
    h = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    open(out + '.sha256', 'w').write(f'{h}  {out.split("/")[-1]}\n')
    info = dict(C_star=C_star, cv_scores={str(k): v for k, v in cv.items()}, n=len(Y), sha256=h,
                verdicts=pd.Series(verdict).value_counts().to_dict(), mean_P=float(p.mean()))
    json.dump(info, open(out.replace('.csv', '_info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))

def b2_probability(path='../results/dr3_candidates_scored.csv', out='../results/dr3_candidates_B2prob.csv'):
    """v0.6 A20: H11a needs a Brier score for baseline B2 (CMD excess), which is a score, not a probability.
    Fixed now, label-free. Primary: P_B2 = expit(LR_cmd + logit(prior_pi)), i.e. the pure-CMD likelihood ratio
    dark_companion.lr_cmd_only(dm, sig_cmd) (no a0, no RVS) with GAIA-FP's own frozen prior, so the two differ only in the
    likelihood. Sensitivity: P_B2_em = constant-pi EM on LR_cmd (on DR3 this saturates at pi = 0.9999, i.e. ~ "all impostors")."""
    from scipy.special import expit, logit
    import dark_companion as DC
    if hashlib.sha256(open(path, 'rb').read()).hexdigest() != FROZEN_SHA: raise SystemExit('frozen prediction file changed')
    X = pd.read_csv(path, dtype={'source_id': str})
    Lc = DC.lr_cmd_only(X.dm.values, X.sig_cmd.values); assert np.isfinite(Lc).all()
    p = expit(Lc + logit(np.clip(X.prior_pi.values, 1e-6, 1-1e-6)))
    pi = PS.em_fit(Lc, np.zeros((len(Lc), 1)), 0.0)(np.zeros((len(Lc), 1)))
    pe = expit(Lc + logit(np.clip(pi, 1e-6, 1-1e-6)))
    assert ((p >= 0) & (p <= 1)).all() and ((pe >= 0) & (pe <= 1)).all()
    Y = pd.DataFrame(dict(source_id=X.source_id, llr_cmd_pure=Lc, P_B2=p, pi_B2_em=pi, P_B2_em=pe)); Y.to_csv(out, index=False)
    h = hashlib.sha256(open(out, 'rb').read()).hexdigest(); open(out + '.sha256', 'w').write(f'{h}  {out.split("/")[-1]}\n')
    print(dict(file=out, sha256=h, mean_P_B2=float(p.mean()), pi_B2_em=float(pi[0]), mean_P_B2_em=float(pe.mean()),
               mean_P_GAIA_FP=float(X.P_impostor.mean())))

if __name__ == '__main__':
    main(); b2_probability()
