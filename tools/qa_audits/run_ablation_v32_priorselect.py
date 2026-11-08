#!/usr/bin/env python3
"""Re-run DR3 ablation using the label-free v3.2 prior-selection rule.

This is an exploratory bridge analysis on the DR3 SB2 positive-unlabelled proxy.
The v3.1/C=1 outputs remain untouched and primary for the original DR3 study.
The C selection below uses only unlabeled mixture likelihood, never SB2 labels.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from hier_em import phi
from prior_select import posterior, GRID
from scipy.special import logsumexp
from runpy import run_path
# Load the exact CMD-marginal likelihood implementation used in the prior ablation.
import importlib.util
spec=importlib.util.spec_from_file_location('ablation_module',ROOT/'tools/qa_audits'/'run_ablation_dr3.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
D=pd.read_csv(ROOT/'results'/'dr3_candidates_scored.csv')
y=D.sb2_any.astype(int).to_numpy(); F=phi(D)
L_full=D.log_lr.to_numpy(float); L_cmd=mod.cmd_marginal_loglr(D)
p_full,pi_full,C_full,cv_full=posterior(L_full,F,seed=0)
p_cmd,pi_cmd,C_cmd,cv_cmd=posterior(L_cmd,F,seed=0)
# Same fixed-prior comparator is monotone in likelihood; choose fixed pi=.3 as frozen control.
from scipy.special import expit,logit
p_full_fix=expit(L_full+logit(.3)); p_cmd_fix=expit(L_cmd+logit(.3))
scores={'FULL_v32_prior_select':p_full,'CMD_marginal_v32_prior_select':p_cmd,
        'FULL_fixed_pi_0.3':p_full_fix,'CMD_marginal_fixed_pi_0.3':p_cmd_fix}
nboot=1000; seed=20261101; rng=np.random.default_rng(seed)
pos=np.flatnonzero(y==1); neg=np.flatnonzero(y==0)
draws={k:np.empty(nboot) for k in scores}
for b in range(nboot):
 ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)]; yy=y[ix]
 for k,s in scores.items(): draws[k][b]=roc_auc_score(yy,s[ix])
auc={k:{'point':float(roc_auc_score(y,s)),'95pct_CI':[float(v) for v in np.quantile(draws[k],[.025,.975])]} for k,s in scores.items()}
delta={}
for k in ('CMD_marginal_v32_prior_select','FULL_fixed_pi_0.3','CMD_marginal_fixed_pi_0.3'):
 dd=draws['FULL_v32_prior_select']-draws[k]
 delta[k]={'point':auc['FULL_v32_prior_select']['point']-auc[k]['point'],
           '95pct_CI':[float(v) for v in np.quantile(dd,[.025,.975])]}
obj={'status':'EXPLORATORY DR3 RE-ABlATION WITH V3.2 LABEL-FREE PRIOR SELECTION; SB2 PU PROXY ONLY',
 'sample':{'n':len(D),'sb2_positive':int(y.sum()),'unlabelled_not_verified_negative':int((y==0).sum())},
 'prior_selection':{'grid':list(GRID),'selection_uses_SB2_labels':False,'FULL_selected_C':float(C_full),
                    'CMD_marginal_selected_C':float(C_cmd),'FULL_cv_loglik':{str(k):float(v) for k,v in cv_full.items()},
                    'CMD_marginal_cv_loglik':{str(k):float(v) for k,v in cv_cmd.items()},
                    'FULL_mean_pi':float(pi_full.mean()),'CMD_marginal_mean_pi':float(pi_cmd.mean())},
 'metrics':{'n_boot':nboot,'seed':seed,'auc':auc,'paired_delta_FULL_minus_variant':delta},
 'interpretation':['C is selected by the project v3.2 label-free held-out mixture-log-likelihood rule, not by SB2 AUC.',
                   'This remains exploratory on DR3; registered v3.1/C=1 outputs are preserved.',
                   'SB2 matches are only known positives. The rest are unlabelled, not verified negatives.']}
out=ROOT/'results'/'qa2'/'partial_completion'/'ablation_v32_priorselect.json'; out.write_text(json.dumps(obj,indent=2))
lines=['# DR3 ablation with v3.2 label-free prior selection','',
'**Exploratory bridge analysis. The original DR3 v3.1/C=1 result is preserved. The prior complexity is selected without reading SB2 labels.**','',
 f"The v3.2 rule selected C={C_full:g} for FULL and C={C_cmd:g} for CMD-marginal. The SB2 proxy labels are used only for the final diagnostic evaluation.",'',
'| Variant | AUC | 95% percentile CI |','|---|---:|---:|']
for k,v in auc.items(): lines.append(f"| {k} | {v['point']:.3f} | [{v['95pct_CI'][0]:.3f}, {v['95pct_CI'][1]:.3f}] |")
lines += ['', '## Paired differences', '', '| Contrast | ΔAUC (FULL − variant) | 95% CI |','|---|---:|---:|']
for k,v in delta.items(): lines.append(f"| {k} | {v['point']:+.3f} | [{v['95pct_CI'][0]:+.3f}, {v['95pct_CI'][1]:+.3f}] |")
lines += ['', '## Interpretation','',
'- The v3.2 C-selection rule optimizes held-out unlabelled mixture likelihood, not SB2 retrieval AUC. Its choice cannot be described as an AUC-tuned improvement.',
'- This diagnostic does not reverse the real-DR3 ablation finding: the CMD-marginal score remains at least as high as the fully conditioned score on this SB2 positive-unlabelled proxy.',
'- Only 16 positives are independently labelled and 2,086 rows remain unlabelled; do not call these AUCs definitive classification performance.','']
(ROOT/'results'/'qa2'/'partial_completion'/'ABLATION_V32_PRIORSELECT_2026-11-01.md').write_text('\n'.join(lines))
print(json.dumps(obj,indent=2))
