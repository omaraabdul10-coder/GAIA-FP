#!/usr/bin/env python3
"""Real-DR3 component ablation for GAIA-FP, restricted to the archived SB2 PU proxy.

Ablations:
  1) full conditional a0|CMD likelihood + EM-C1 demographic prior (frozen model)
  2) same likelihood + fixed pi=0.3 (remove learned demographic prior)
  3) CMD-marginal likelihood (remove a0-conditioning) + EM-C1 prior
  4) CMD-marginal likelihood + fixed pi=0.3

SB2 labels are positive-unlabelled, not ground-truth binary labels. This is a
sensitivity/ablation benchmark, not a representative estimate of true FP AUC.
No historical output is overwritten.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit, logit, logsumexp
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'results'
OUT = RES / 'qa2' / 'partial_completion'
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261101
N_BOOT = 20000


def auc(s, y):
    s = np.asarray(s, float); y = np.asarray(y, int)
    p, n = s[y == 1], s[y == 0]
    if len(p) == 0 or len(n) == 0:
        return float('nan')
    r = rankdata(np.r_[p, n], method='average')
    return float((r[:len(p)].sum() - len(p)*(len(p)+1)/2) / (len(p)*len(n)))


def cmd_marginal_loglr(df, nq=400, nn=9):
    """log p(dm|H_t) / p(dm|H_p), integrating q,n without astrometric a0 conditioning."""
    q = np.linspace(0.1, 1.0, nq)
    n = np.linspace(2.0, 6.0, nn)
    qq, nv = np.meshgrid(q, n)
    mu = -2.5 * np.log10(1.0 + qq.ravel() ** nv.ravel())
    dm = df['dm'].to_numpy(float)[:, None]
    sig = df['sig_cmd'].to_numpy(float)[:, None]
    # Gaussian log densities. Marginalize over the same uniform q,n grids as joint_lr.py.
    log_t = -0.5*((dm-mu[None,:])/sig)**2 - np.log(sig) - 0.9189385332046727
    log_p = -0.5*(dm/sig)**2 - np.log(sig) - 0.9189385332046727
    return np.clip(logsumexp(log_t, axis=1) - np.log(mu.size) - log_p[:,0], -30, 30)


def boot_metrics(score_dict, y, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1); neg = np.flatnonzero(y == 0)
    names = list(score_dict)
    point = {k: auc(v, y) for k, v in score_dict.items()}
    draws = {k: np.empty(n_boot, float) for k in names}
    # Common stratified resamples preserve pairing across every ablation.
    for b in range(n_boot):
        ix = np.r_[rng.choice(pos, len(pos), replace=True), rng.choice(neg, len(neg), replace=True)]
        yy = y[ix]
        for k, v in score_dict.items():
            draws[k][b] = auc(np.asarray(v)[ix], yy)
    out = {'n_boot': n_boot, 'seed': seed, 'auc': {}, 'paired_delta': {}}
    for k in names:
        out['auc'][k] = {'point': point[k], 'percentile_95_ci': [float(v) for v in np.quantile(draws[k], [.025,.975])]}
    for k in names:
        if k == 'FULL_joint_EM_C1':
            continue
        dd = draws['FULL_joint_EM_C1'] - draws[k]
        out['paired_delta']['FULL_minus_'+k] = {
            'point': point['FULL_joint_EM_C1'] - point[k],
            'percentile_95_ci': [float(v) for v in np.quantile(dd, [.025,.975])]}
    return out


def main():
    from hier_em import em, phi
    df = pd.read_csv(RES/'dr3_candidates_scored.csv')
    if len(df) != 2102 or df.source_id.nunique() != 2102:
        raise AssertionError('Expected frozen 2,102 unique DR3 scored candidates')
    y = df['sb2_any'].astype(int).to_numpy()
    if int(y.sum()) != 16:
        raise AssertionError(f'Expected the archived 16 SB2 positives, found {int(y.sum())}')
    L_full = df['log_lr'].to_numpy(float)
    F = phi(df)
    # Refit the registered EM-C1 prior from the archived evidence and covariates.
    p_full, pi_full = em(L_full, F, C=1.0)
    p_full_fixed = expit(L_full + logit(.3))
    # Component ablation: marginalize over q,n without letting a0 select q.
    L_cmd = cmd_marginal_loglr(df)
    p_cmd_em, pi_cmd = em(L_cmd, F, C=1.0)
    p_cmd_fixed = expit(L_cmd + logit(.3))
    # Pure B2 CMD diagnostic comparator, not treated as a GAIA-FP ablation.
    b2 = -df['dm'].to_numpy(float)
    scores = {
        'FULL_joint_EM_C1': p_full,
        'joint_fixed_prior_pi0.3': p_full_fixed,
        'CMD_marginal_EM_C1': p_cmd_em,
        'CMD_marginal_fixed_prior_pi0.3': p_cmd_fixed,
        'B2_CMD_only': b2,
    }
    metrics = boot_metrics(scores, y)
    thresholds = {}
    for k, s in scores.items():
        thresholds[k] = {
            'recall_at_score_ge_0.85': int(np.sum((y==1) & (s>=.85))) / int(y.sum()),
            'sb2_positives_recalled': int(np.sum((y==1) & (s>=.85))),
            'n_candidates_score_ge_0.85': int(np.sum(s>=.85)),
            'n_candidates_score_le_0.15': int(np.sum(s<=.15)),
        }
    # A strict integrity check: the refit should reproduce frozen posterior values.
    max_abs_diff = float(np.max(np.abs(p_full - df['P_impostor'].to_numpy(float))))
    if max_abs_diff > 2e-6:
        raise AssertionError(f'Full model reproduction mismatch: max abs diff {max_abs_diff}')
    result = {
        'status': 'COMPLETED REAL-DR3 COMPONENT ABLATION ON SB2 POSITIVE-UNLABELLED PROXY; LIMITED VALIDATION',
        'sample': {'n':len(df), 'positive_sb2':int(y.sum()), 'non_sb2_unlabelled':int((y==0).sum()),
                   'interpretation':'The 2,086 non-SB2 rows are not verified true negatives; AUC is a positive-unlabelled lower-bound/proxy diagnostic.'},
        'design': {
            'FULL_joint_EM_C1':'Frozen GAIA-FP conditional p(dm|a0,Ht)/p(dm|Hp) likelihood + covariate EM prior C=1.',
            'joint_fixed_prior_pi0.3':'Same conditional joint likelihood; removes learned demographic prior, uses constant pi=0.3.',
            'CMD_marginal_EM_C1':'Removes a0-conditioning from the likelihood by marginalizing q,n uniformly; refits same EM-C1 prior.',
            'CMD_marginal_fixed_prior_pi0.3':'CMD-marginal likelihood and constant pi=0.3.',
            'B2_CMD_only':'-delta_MG comparator, included for context; not a component ablation.',
            'bootstrap':'20,000 paired, stratified (positive/negative) bootstrap resamples, same resamples across variants.'},
        'frozen_model_reproduction': {'max_abs_posterior_difference':max_abs_diff, 'pass':True},
        'metrics':metrics,
        'threshold_diagnostic_at_0.85':thresholds,
        'prior_means': {'full_EM_C1':float(np.mean(pi_full)), 'CMD_marginal_EM_C1':float(np.mean(pi_cmd)), 'fixed_prior':.3},
        'limitations': [
            'SB2-only validation is positive-unlabelled: non-SB2 does not imply genuine substellar companion.',
            'Only 16 independent SB2 positives; confidence intervals are wide and class-sensitive.',
            'This is a real DR3 ablation of available astrometric/CMD/prior components; RVS-phase component cannot be ablated on DR3 because epoch RVS widths were not retrieved.',
            'The ablation does not prove the full model is superior; variants are descriptive diagnostic comparisons.'
        ]}
    (OUT/'ablation_dr3_component_results.json').write_text(json.dumps(result,indent=2,default=float))
    outcsv = df[['source_id','sb2_any','dm','sig_cmd','log_lr','prior_pi','P_impostor']].copy()
    for k,v in scores.items(): outcsv[k] = v
    outcsv.to_csv(OUT/'ablation_dr3_candidate_scores.csv',index=False)
    lines = [
        '# GAIA-FP real-DR3 component ablation (1 Nov 2026)', '',
        '## Scope',
        f"- N={len(df)}; SB2 positives={int(y.sum())}; non-SB2 rows={int((y==0).sum())} (unlabelled, not verified negatives).",
        '- The SB2 endpoint is therefore a positive-unlabelled proxy. Do not call these AUCs definitive real false-positive classification performance.',
        '- 20,000 paired stratified bootstrap resamples were used for percentile intervals.', '',
        '## Ablation definitions',
        '- FULL: frozen conditional astrometric-amplitude/CMD likelihood + EM-C1 demographic prior.',
        '- joint + fixed prior: same evidence, but remove learned demographic prior (constant pi=0.3).',
        '- CMD-marginal + EM-C1: remove astrometric a0-conditioning in the evidence likelihood; integrate over q,n without a0.',
        '- CMD-marginal + fixed prior: both changes above.',
        '- B2 CMD-only is context baseline, not a GAIA-FP ablation.', '',
        '## AUC results',
        '| Variant | AUC | 95% percentile CI | Recall of 16 SB2 at score ≥0.85 |',
        '|---|---:|---:|---:|'
    ]
    for k in scores:
        a=metrics['auc'][k]
        lo,hi=a['percentile_95_ci']
        r=thresholds[k]['sb2_positives_recalled']
        lines.append(f"| {k} | {a['point']:.3f} | [{lo:.3f}, {hi:.3f}] | {r}/16 |")
    lines += ['', '## Paired differences against FULL', '| Contrast | ΔAUC (FULL − variant) | 95% percentile CI |', '|---|---:|---:|']
    for k,v in metrics['paired_delta'].items():
        lines.append(f"| {k.replace('FULL_minus_','')} | {v['point']:+.3f} | [{v['percentile_95_ci'][0]:+.3f}, {v['percentile_95_ci'][1]:+.3f}] |")
    lines += ['', '## Interpretation',
      f"- Refitting the full pipeline reproduces the frozen posterior to max absolute difference {max_abs_diff:.2e}.",
      f"- The full EM prior mean is {np.mean(pi_full):.3f}; the CMD-marginal EM prior mean is {np.mean(pi_cmd):.3f}; fixed prior is 0.300.",
      '- If fixed-prior AUC exceeds the full EM-C1 AUC on this SB2 proxy, that indicates the learned demographic prior may hurt ranking on this particular endpoint; it does not establish fixed prior as universally better.',
      '- If removing a0 conditioning reduces AUC, it is only evidence on this small SB2 proxy, not proof of causal/physical component necessity.',
      '- DR3 has no retrieved epoch-RVS widths, so the phase-locked RVS feature is not empirically ablated here.', '',
      '## Reproducibility',
      '- Run: `PYTHONPATH=src python tools/qa_audits/run_ablation_dr3.py`',
      '- Machine-readable results: `results/qa2/partial_completion/ablation_dr3_component_results.json`',
      '- Per-object scores: `results/qa2/partial_completion/ablation_dr3_candidate_scores.csv`',
      '- No historical frozen outputs are modified.', '']
    (OUT/'ABLATION_DR3_COMPONENT_REPORT_2026-11-01.md').write_text('\n'.join(lines))
    print(json.dumps(result,indent=2,default=float))

if __name__ == '__main__':
    main()
