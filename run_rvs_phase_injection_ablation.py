#!/usr/bin/env python3
"""Synthetic-only injection/recovery ablation for the epoch-RVS phase component.

This test is separate from the real-DR3 SB2 proxy. It injects the unresolved
binary line-width law, adds single-star/planet nulls, perturbs the analyst orbit,
and measures incremental phase information. Synthetic mechanism test only.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'qa2'/'partial_completion'; OUT.mkdir(parents=True,exist_ok=True)
SEED=20261101; N_PER_CLASS=1000; N_BOOT=500; N_REPLICATES=3; SIG0=11.0
G=2.959122e-4; AU_KMS=1731.456

def true_anomaly_matrix(t,P,e,T0):
    M=np.mod(2*np.pi*(t-T0[:,None])/P[:,None],2*np.pi)
    E=M+e[:,None]*np.sin(M)
    for _ in range(18): E -= (E-e[:,None]*np.sin(E)-M)/(1-e[:,None]*np.cos(E))
    return 2*np.arctan2(np.sqrt(1+e[:,None])*np.sin(E/2),np.sqrt(1-e[:,None])*np.cos(E/2))

def z_rows(template,width):
    s2=np.square(width)
    a=template-template.mean(axis=1,keepdims=True); b=s2-s2.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
    corr=np.divide(np.sum(a*b,axis=1),den,out=np.zeros_like(den),where=den>0)
    return np.arctanh(np.clip(corr,-.999,.999))*np.sqrt(template.shape[1]-3)

def auc_ci(y,a,b,n_boot,seed):
    rng=np.random.default_rng(seed); pos=np.flatnonzero(y==1); neg=np.flatnonzero(y==0); draws=np.empty(n_boot)
    for j in range(n_boot):
        ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)]
        draws[j]=roc_auc_score(y[ix],a[ix])-roc_auc_score(y[ix],b[ix])
    return [float(v) for v in np.quantile(draws,[.025,.975])]

def simulate(n_epoch,sigma,seed):
    rng=np.random.default_rng(seed); n=2*N_PER_CLASS
    # Binary injections are rejection-sampled to represent the SB1-selected
    # population used by the physical RVS likelihood (A6): remove objects Gaia
    # would have resolved as SB2 under the registered light-ratio/K criterion.
    bp=[]; be=[]; bi=[]; bm=[]; bt0=[]; bw=[]; bq=[]; bn=[]; bK=[]; bf=[]
    n_attempted=0; n_sb2_rejected=0
    while sum(len(x) for x in bp)<N_PER_CLASS:
        rem=N_PER_CLASS-sum(len(x) for x in bp); m=max(500,2*rem)
        n_attempted += m
        P0=np.exp(rng.uniform(np.log(30),np.log(1500),m))
        e0=np.clip(rng.beta(1.5,5,m)*.85,0,.85)
        i0=np.degrees(np.arccos(rng.uniform(0,1,m)))
        M0=rng.uniform(.7,1.4,m); T00=rng.uniform(-1,1,m)*P0; om0=rng.uniform(0,360,m)
        q0=rng.uniform(.5,1,m); n0=rng.uniform(2,6,m)
        M10=M0/np.power(1+np.power(q0,n0),1/n0); M20=q0*M10
        a0=np.power(G*(M10+M20)*P0**2/(4*np.pi**2),1/3)
        K0=2*np.pi*a0*np.sin(np.radians(i0))/(P0*np.sqrt(1-e0**2))*AU_KMS
        f0=np.power(q0,n0)/(1+np.power(q0,n0))
        # Match src/rvs_predict.py exactly: q**n >= 0.2 AND K_sum*(1+e) >= 30 km/s.
        sb2_resolved=(np.power(q0,n0)>=.2)&(K0*(1+e0)>=30.0)
        n_sb2_rejected += int(sb2_resolved.sum())
        keep=np.flatnonzero(~sb2_resolved)[:rem]
        if len(keep):
            bp.append(P0[keep]); be.append(e0[keep]); bi.append(i0[keep]); bm.append(M0[keep]); bt0.append(T00[keep]); bw.append(om0[keep]); bq.append(q0[keep]); bn.append(n0[keep]); bK.append(K0[keep]); bf.append(f0[keep])
    Pp,ep,ip,Mp,T0p,omp,qp,np0,Kp,fp=[np.concatenate(v) for v in (bp,be,bi,bm,bt0,bw,bq,bn,bK,bf)]
    # Matched-size planet/null set. Period/eccentricity/inclination/mass/cadence
    # distributions are independently sampled from the same broad design priors.
    Pn=np.exp(rng.uniform(np.log(30),np.log(1500),N_PER_CLASS))
    en=np.clip(rng.beta(1.5,5,N_PER_CLASS)*.85,0,.85)
    inn=np.degrees(np.arccos(rng.uniform(0,1,N_PER_CLASS)))
    Mn=rng.uniform(.7,1.4,N_PER_CLASS); T0n=rng.uniform(-1,1,N_PER_CLASS)*Pn; omn=rng.uniform(0,360,N_PER_CLASS)
    P=np.r_[Pn,Pp]; e=np.r_[en,ep]; inc=np.r_[inn,ip]; Mphot=np.r_[Mn,Mp]; T0=np.r_[T0n,T0p]; omega=np.r_[omn,omp]
    q=np.r_[np.ones(N_PER_CLASS),qp]; nml=np.r_[np.full(N_PER_CLASS,4.0),np0]
    K=np.r_[np.zeros(N_PER_CLASS),Kp]; f=np.r_[np.zeros(N_PER_CLASS),fp]
    y=np.r_[np.zeros(N_PER_CLASS,dtype=int),np.ones(N_PER_CLASS,dtype=int)]
    t=np.sort(rng.uniform(0,2000,(n,n_epoch)),axis=1)
    nu=true_anomaly_matrix(t,P,e,T0); w=np.radians(omega)
    shape=np.cos(nu+w[:,None])+e[:,None]*np.cos(w[:,None])
    dv=K[:,None]*np.abs(shape)
    width_true=np.sqrt(SIG0**2+(f*(1-f))[:,None]*dv**2)
    width=np.clip(width_true+rng.normal(0,sigma,(n,n_epoch)),.2,None)
    # Imperfect analyst ephemeris, matching the registered model assumptions.
    Phat=P*(1+rng.normal(0,.01,n)); ehat=np.clip(e+rng.normal(0,.05,n),0,.95)
    T0hat=T0+rng.normal(0,.02*P,n); omegahat=omega+rng.normal(0,10,n); wh=np.radians(omegahat)
    nu_hat=true_anomaly_matrix(t,Phat,ehat,T0hat)
    template=(np.cos(nu_hat+wh[:,None])+ehat[:,None]*np.cos(wh[:,None]))**2
    z=z_rows(template,width)
    width_scr=np.vstack([rng.permutation(row) for row in width])
    zscr=z_rows(template,width_scr)
    dm_true=np.zeros(n); dm_true[N_PER_CLASS:]=-2.5*np.log10(1+np.power(q[N_PER_CLASS:],nml[N_PER_CLASS:]))
    dm=dm_true+rng.normal(0,.30,n)
    D=pd.DataFrame({'y':y,'dm':dm,'z_rvs':z,'z_phase_scrambled':zscr})
    split=next(StratifiedShuffleSplit(n_splits=1,test_size=.30,random_state=seed).split(D[['dm']],y)); tr,te=split
    def fit(cols):
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1500,solver='lbfgs'))
        model.fit(D.iloc[tr][cols].values,y[tr]); return model.predict_proba(D.iloc[te][cols].values)[:,1]
    p_cmd=fit(['dm']); p_joint=fit(['dm','z_rvs']); p_scr=fit(['dm','z_phase_scrambled'])
    yt=y[te]; az=float(roc_auc_score(yt,D.iloc[te].z_rvs)); ac=float(roc_auc_score(yt,p_cmd)); aj=float(roc_auc_score(yt,p_joint)); ash=float(roc_auc_score(yt,p_scr))
    return {'n_epoch':n_epoch,'sigma_meas_kms':sigma,'seed':seed,'n_train':int(len(tr)),'n_test':int(len(te)),
      'n_sb1_binary_injections':N_PER_CLASS,'SB2_rejected_by_A6':True,
      'A6_rejection_count_during_sampling':n_sb2_rejected,'A6_attempted_draws':n_attempted,
      'A6_rejection_fraction_of_attempted_draws':float(n_sb2_rejected/n_attempted),
      'selected_binary_median_K_sum_kms':float(np.median(Kp)),
      'selected_binary_median_flux_fraction':float(np.median(fp)),
      'auc_test':{'CMD_only':ac,'RVS_phase_only':az,'CMD_plus_RVS_phase':aj,'CMD_plus_phase_scrambled_negative_control':ash},
      'paired_delta_auc':{'CMD_plus_RVS_minus_CMD_only':{'point':aj-ac,'95pct_percentile_CI':auc_ci(yt,p_joint,p_cmd,N_BOOT,seed+1000)},
                          'CMD_plus_RVS_minus_scrambled_control':{'point':aj-ash,'95pct_percentile_CI':auc_ci(yt,p_joint,p_scr,N_BOOT,seed+2000)}},
      'warning':'SYNTHETIC INJECTION-RECOVERY ONLY; not Gaia DR3/DR4 data.'}

def main():
    res=[]
    for n_epoch in (20,40):
      for sigma in (2.,4.,8.):
        runs=[simulate(n_epoch,sigma,SEED+n_epoch*100+int(sigma*10)+rep*1009) for rep in range(N_REPLICATES)]
        first=dict(runs[0])
        deltas=np.array([x['paired_delta_auc']['CMD_plus_RVS_minus_CMD_only']['point'] for x in runs])
        positive_ci=sum(x['paired_delta_auc']['CMD_plus_RVS_minus_CMD_only']['95pct_percentile_CI'][0] > 0 for x in runs)
        first['replicate_runs']=runs
        first['replicate_summary']={
          'n_replicates':N_REPLICATES,
          'mean_auc':{k:float(np.mean([x['auc_test'][k] for x in runs])) for k in runs[0]['auc_test']},
          'mean_delta_auc_joint_minus_cmd':float(deltas.mean()),
          'delta_auc_range_across_replicates':[float(deltas.min()),float(deltas.max())],
          'replicates_with_95pct_bootstrap_CI_above_zero':int(positive_ci),
          'replicate_bootstrap_CIs':[x['paired_delta_auc']['CMD_plus_RVS_minus_CMD_only']['95pct_percentile_CI'] for x in runs]}
        res.append(first)
    obj={'status':'SYNTHETIC INJECTION-RECOVERY COMPLETED; NOT REAL GAIA VALIDATION',
      'design':{'n_per_class_per_replicate':N_PER_CLASS,'independent_replicates_per_scenario':N_REPLICATES,'train_test_split':'70/30 stratified',
       'period_days':'log-uniform 30-1500','eccentricity':'0.85*Beta(1.5,5)',
       'inclination':'isotropic; cos(i) uniform [0,1]','stellar_mass_msun':'uniform 0.7-1.4',
       'SB1_selection':'exact project A6 rule: exclude if q**n >=0.2 AND K_sum*(1+e)>=30 km/s; q**n is line-flux ratio, distinct from companion fraction q**n/(1+q**n)',
       'epochs':'uniform over 2000 days','instrumental_width_kms':SIG0,'measurement_error_kms':[2,4,8],
       'analyst_orbit_perturbation':'P 1%, e 0.05, T0 0.02P, omega 10 deg','CMD_scatter_mag':.30,
       'negative_control':'permute per-epoch widths across times before phase statistic','classifier':'standardized logistic regression C=1; fixed 70/30 split per replicate',
       'bootstrap_reps_per_replicate':N_BOOT},'scenarios':res,
      'interpretation':'Tests whether phase-aligned epoch-width data can add information under the assumed injected line-width law across independent random seeds. Not observed Gaia evidence.'}
    (OUT/'rvs_phase_injection_ablation.json').write_text(json.dumps(obj,indent=2))
    lines=['# Epoch-RVS phase component — synthetic injection/recovery ablation','',
      '**Status: completed synthetic mechanism test; NOT real Gaia validation.**','',
      f'Each scenario has {N_REPLICATES} independent data/split seeds, {N_PER_CLASS} objects per class per replicate, a 70/30 stratified split, and {N_BOOT} paired stratified bootstrap replicates per run.',
      'Known luminous-binary injections follow the project A6 SB1/SB2 rejection rule. The scoring ephemeris is perturbed (P 1%, e 0.05, T0 0.02P, omega 10°). Standardized logistic regression (C=1) compares CMD-only, RVS-phase-only, CMD+RVS-phase, and a phase-scrambled negative control.','',
      '| Epochs | RV error (km/s) | Mean CMD AUC | Mean RVS phase AUC | Mean CMD + phase AUC | Mean scrambled AUC | Mean ΔAUC vs CMD | Replicates with CI > 0 |','|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in res:
      a=r['replicate_summary']['mean_auc']; d=r['replicate_summary']['mean_delta_auc_joint_minus_cmd']
      pos=r['replicate_summary']['replicates_with_95pct_bootstrap_CI_above_zero']
      lines.append(f"| {r['n_epoch']} | {r['sigma_meas_kms']:.1f} | {a['CMD_only']:.3f} | {a['RVS_phase_only']:.3f} | {a['CMD_plus_RVS_phase']:.3f} | {a['CMD_plus_phase_scrambled_negative_control']:.3f} | {d:+.3f} | {pos}/{N_REPLICATES} |")
    lines += ['', '## Interpretation','',
      '- Synthetic positive injections apply the exact A6 rule in `src/rvs_predict.py`: remove systems with q^n ≥0.2 AND K_sum(1+e) ≥30 km/s. Here q^n is the line-flux ratio, not the companion flux fraction q^n/(1+q^n).',
      '- This tests mechanism recovery under the specified simulation assumptions; it is not evidence that real Gaia epoch-RVS widths carry the same signal.',
      '- The phase-scrambled control tests whether the information depends on correct epoch/orbit alignment.',
      '- DR3 empirical ablation remains limited to astrometric/CMD likelihood and population prior. Empirical DR4 RVS ablation requires released epoch rows and validated units.',
      '- Label all numbers synthetic; never merge them with real-DR3 AUC results.','',
      'Reproduce: `PYTHONPATH=src python tools/qa_audits/run_rvs_phase_injection_ablation.py`','']
    (OUT/'RVS_PHASE_INJECTION_ABLATION_2026-11-01.md').write_text('\n'.join(lines))
    print(json.dumps(obj,indent=2))
if __name__=='__main__': main()
