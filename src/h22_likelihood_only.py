"""H22 (secondary, outside the Holm family; v0.6 addendum, 23 Nov 2026).
Score = frozen v3.2 log-likelihood ratio `log_lr` (already written by dr4_run.write), i.e. the frozen
posterior with the covariate prior removed (flat pi; monotone in log_lr). No new parameters, no refit.
H22a: AUC(log_lr) on the sealed set, stratified bootstrap exactly as H1; PASS if 2.5th pct > 0.5.
H22b (reported): paired dAUC = AUC(log_lr) - AUC(P_impostor) with 95% CI; 'better' only if CI excludes 0.
Uses only dr4_evaluate helpers; the frozen evaluator is not modified."""
import json, sys, numpy as np
import dr4_evaluate as E

def h22(D):
    y = D.y.values; s, p = D.log_lr.values.astype(float), D.P_impostor.values.astype(float)
    if min(y.sum(), (y == 0).sum()) < E.MIN_CLASS: return E.not_conducted('BELOW_MIN_N')
    if not np.isfinite(s).all(): return E.not_conducted('LOG_LR_NOT_FINITE')
    bs = E.strat_boot(lambda i: E.auc(s[i], y[i]), y)
    bd = E.strat_boot(lambda i: E.auc(s[i], y[i]) - E.auc(p[i], y[i]), y)
    lo, hi = np.percentile(bd, [2.5, 97.5])
    return dict(status='CONDUCTED', n_imp=int(y.sum()), n_sub=int((y == 0).sum()),
                H22a=dict(auc=E.auc(s, y), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                          p=E.p_one_sided(bs, 0.5, 'greater'), registered_pass=bool(np.percentile(bs, 2.5) > 0.5)),
                H22b=dict(auc_h1_score=E.auc(p, y), d_auc=E.auc(s, y) - E.auc(p, y), ci95=[float(lo), float(hi)],
                          verdict='better' if lo > 0 else 'worse' if hi < 0 else 'no_difference'))
