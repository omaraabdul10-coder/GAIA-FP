#!/usr/bin/env python3
"""Exploratory regularization sensitivity for the label-free EM prior.

The registered C=1 result is retained as primary. This sweep is descriptive and
must not be used to select a new C based on the SB2 proxy labels.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.special import expit, logit
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[2]; RES=ROOT/'results'; OUT=RES/'qa2'/'partial_completion'; OUT.mkdir(parents=True,exist_ok=True)
sys_path=ROOT/'src'
import sys; sys.path.insert(0,str(sys_path))
from hier_em import em, phi
D=pd.read_csv(RES/'dr3_candidates_scored.csv')
y=D.sb2_any.astype(int).to_numpy(); L=D.log_lr.to_numpy(float); F=phi(D)
rows=[]
for C in [0.01,0.03,0.1,0.3,1.0,3.0,10.0]:
 p,pi=em(L,F,C=C)
 rows.append({'C':C,'mean_pi':float(np.mean(pi)),'median_pi':float(np.median(pi)),
              'auc_sb2_positive_unlabelled_proxy':float(roc_auc_score(y,p)),
              'max_posterior':float(np.max(p)),'fraction_p_ge_0_85':float(np.mean(p>=.85))})
# top-k retrieval at frozen score ordering; unlabelled rows are not true negatives.
S=pd.read_csv(OUT/'ablation_dr3_candidate_scores.csv')
cols=['FULL_joint_EM_C1','joint_fixed_prior_pi0.3','CMD_marginal_EM_C1','CMD_marginal_fixed_prior_pi0.3','B2_CMD_only']
top={}
for frac in [.005,.01,.02,.05,.10,.20]:
 k=max(1,int(np.ceil(len(S)*frac))); top[str(frac)]={}
 for col in cols:
  ix=np.argsort(-S[col].to_numpy())[:k]; hit=int(S.iloc[ix].sb2_any.sum())
  top[str(frac)][col]={'top_k':k,'sb2_matches_captured':hit,'recall_of_16_known_sb2':hit/16,
     'match_fraction_in_top_k':hit/k,'enrichment_vs_global_sb2_rate':(hit/k)/(16/len(S)) if hit else 0.0}
obj={'status':'EXPLORATORY PRIOR-REGULARIZATION AND TOP-K SENSITIVITY; NOT A MODEL SELECTION',
 'registered_primary_C':1.0,'C_sweep':rows,'top_k_retrieval':top,
 'interpretation':['C=1 remains the registered primary; do not select C from this SB2 proxy.','Top-k metrics quantify retrieval of known SB2 matches among unlabelled candidates, not precision among true negatives.','A fixed prior changes posterior calibration but, for a constant prior, does not change ranking/AUC relative to the underlying likelihood ratio.']}
(OUT/'ablation_prior_sensitivity.json').write_text(json.dumps(obj,indent=2))
lines=['# Ablation supplementary sensitivity: EM regularization and top-k retrieval','',
'**Exploratory only. The registered C=1 model remains primary; this sweep is not a hyperparameter-selection exercise.**','',
'## EM prior regularization sweep','', '| C | Mean prior π | Median prior π | SB2 PU-proxy AUC | Fraction with P ≥ 0.85 |','|---:|---:|---:|---:|---:|']
for r in rows: lines.append(f"| {r['C']:.2g} | {r['mean_pi']:.3f} | {r['median_pi']:.3f} | {r['auc_sb2_positive_unlabelled_proxy']:.3f} | {r['fraction_p_ge_0_85']:.3f} |")
lines += ['', '## Top-k known-SB2 retrieval', '', '| Top fraction | k | Variant | Known SB2 matches captured | Recall of 16 | Enrichment vs full sample |','|---:|---:|---|---:|---:|---:|']
for frac,variants in top.items():
 for col,v in variants.items(): lines.append(f"| {float(frac):.1%} | {v['top_k']} | {col} | {v['sb2_matches_captured']} | {v['recall_of_16_known_sb2']:.3f} | {v['enrichment_vs_global_sb2_rate']:.2f}× |")
lines += ['', '## Interpretation','',
'- C=1 remains the registered primary. The grid is a sensitivity display, not permission to choose the C with the highest AUC after seeing labels.',
'- At a constant π, posterior is a monotone transform of the likelihood ratio; changing the constant prior alone cannot improve AUC. Learned covariate-dependent π can alter rankings.',
'- Top-k retrieval avoids treating every non-SB2 as a confirmed negative, but still only measures recovery of known catalogue matches.','']
(OUT/'ABLATION_PRIOR_SENSITIVITY_2026-11-01.md').write_text('\n'.join(lines))
print(json.dumps(obj,indent=2))
