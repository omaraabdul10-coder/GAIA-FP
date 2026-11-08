#!/usr/bin/env python3
"""Cross-validated selection-overlap diagnostics for the 95-labelled subset.

No class-prevalence correction is produced: labels are unavailable for the
other 2,024 candidates and many are a different NSS solution type. The IPW
weights are reported only as a diagnostic of covariate transport feasibility.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold,cross_val_predict

FEATURES=['logP','eccentricity','phot_g_mean_mag','bp_rp','parallax','log_parallax_snr','log_ruwe','log_significance','a0_snr','log_a0']

def smd(a,b,wa=None,wb=None):
    ma=np.average(a,weights=wa);mb=np.average(b,weights=wb)
    va=np.average((a-ma)**2,weights=wa);vb=np.average((b-mb)**2,weights=wb)
    den=np.sqrt((va+vb)/2)
    return float((ma-mb)/den) if den>0 else 0.0

def main(root,outdir):
    root=Path(root).resolve();out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(root/'realdata/dr3_candidates.csv',dtype={'source_id':'string'}).drop_duplicates('source_id').copy()
    c=pd.read_csv(root/'results/qa2/partial_completion/astrospectro_95_object_characterization.csv',dtype={'source_id':'string'})
    sample_ids=set(c.source_id.dropna().astype(str));y=d.source_id.astype(str).isin(sample_ids).astype(int).to_numpy()
    # Reconstruct orbital-scale covariates from Gaia Thiele-Innes columns, without outcome/label information.
    num=['period','eccentricity','phot_g_mean_mag','bp_rp','parallax','parallax_error','ruwe','significance']
    for col in num+['a_thiele_innes','b_thiele_innes','f_thiele_innes','g_thiele_innes','a_thiele_innes_error','b_thiele_innes_error','f_thiele_innes_error','g_thiele_innes_error']:
        d[col]=pd.to_numeric(d[col],errors='coerce')
    A=d[['a_thiele_innes','b_thiele_innes','f_thiele_innes','g_thiele_innes']].to_numpy(float)
    u=np.sum(A*A,axis=1)/2;v=A[:,0]*A[:,3]-A[:,1]*A[:,2]
    a0=np.sqrt(np.maximum(u+np.sqrt(np.maximum(u*u-v*v,0)),0))
    ea=np.sqrt(np.nanmean(d[['a_thiele_innes_error','b_thiele_innes_error','f_thiele_innes_error','g_thiele_innes_error']].to_numpy(float)**2,axis=1))
    d['a0_snr']=a0/ea;d['logP']=np.log10(np.maximum(d.period.to_numpy(float),1e-9))
    d['log_parallax_snr']=np.log10(np.maximum((d.parallax/d.parallax_error).to_numpy(float),1e-9))
    d['log_ruwe']=np.log10(np.maximum(d.ruwe.to_numpy(float),1e-9));d['log_significance']=np.log10(np.maximum(d.significance.to_numpy(float),1e-9));d['log_a0']=np.log10(np.maximum(a0,1e-9))
    X=d[FEATURES].replace([np.inf,-np.inf],np.nan)
    cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=20261103)
    sensitivity=[];primary_p=None;primary_w=None;primary_balance=None
    for C in [0.01,0.1,1.0,10.0]:
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=C,max_iter=10000,random_state=20261103))
        p=cross_val_predict(model,X,y,cv=cv,method='predict_proba')[:,1]
        psel=p[y==1];w=(1-psel)/np.maximum(psel,1e-8);w=w/np.mean(w)
        ess=float(w.sum()**2/(w@w))
        before={};after={}
        for col in FEATURES:
            z=X[col].to_numpy(float);sel=z[y==1];control=z[y==0];pop=z
            before[col]=abs(smd(sel[np.isfinite(sel)],control[np.isfinite(control)]))
            keep=np.isfinite(sel);keepall=np.isfinite(pop)
            after[col]=abs(smd(sel[keep],pop[keepall],wa=w[keep],wb=np.ones(keepall.sum())))
        item={'C':C,'selection_auc_5fold':float(roc_auc_score(y,p)),
          'selected_propensity_quantiles':[float(v) for v in np.quantile(psel,[0,.25,.5,.75,1])],
          'nonselected_propensity_quantiles':[float(v) for v in np.quantile(p[y==0],[0,.25,.5,.75,1])],
          'nonselected_below_min_selected_propensity_fraction':float(np.mean(p[y==0]<psel.min())),
          'transport_weight_ess_of_95':ess,'max_abs_smd_before':float(max(before.values())),
          'max_abs_smd_after_diagnostic_ipw':float(max(after.values())),
          'smd_before':before,'smd_after_diagnostic_ipw':after,
          'warning':'Weights are diagnostics only. Do not use to estimate a corrected label rate because the 2,024 nonselected candidates do not have compatible rho-based labels.'}
        sensitivity.append(item)
        if C==0.1:primary_p=p;primary_w=w;primary_balance=(before,after)
    d['is_95_characterization_sample']=y.astype(bool)
    d['sample_propensity_oof_logit_C0p1']=primary_p
    d['transport_weight_diagnostic_only']=np.nan
    d.loc[y==1,'transport_weight_diagnostic_only']=primary_w
    d.to_csv(out/'SELECTION_PROPENSITY_DIAGNOSTIC_C0p1.csv',index=False)
    type_counts=d.loc[y==1,'nss_solution_type'].value_counts().to_dict()
    parent_type_counts=d.nss_solution_type.value_counts().to_dict()
    label_counts=c.label.value_counts(dropna=False).to_dict()
    mass={'mfit_min_Mj':float(c.mfit.min()),'mfit_median_Mj':float(c.mfit.median()),'mfit_max_Mj':float(c.mfit.max()),
      'm2dyn_median_Mjup':float(c.m2_dyn.median()),'m2dyn_min_Mjup':float(c.m2_dyn.min()),'m2dyn_max_Mjup':float(c.m2_dyn.max()),
      'label_counts':{str(k):int(v) for k,v in label_counts.items()},'criterion_reason_counts':c.criterion_reason.value_counts().to_dict()}
    astro_parent=int((d.nss_solution_type=='AstroSpectroSB1').sum())
    astro_sample=int(((d.nss_solution_type=='AstroSpectroSB1') & (y==1)).sum())
    otsv_parent=int((d.nss_solution_type=='OrbitalTargetedSearchValidated').sum())
    otsv_sample=int(((d.nss_solution_type=='OrbitalTargetedSearchValidated') & (y==1)).sum())
    report={'parent_candidate_unique_ids':len(d),'characterization_ids':len(c),'sample_membership_reproduced':int(y.sum()),
      'n_remaining_parent_ids_without_95_characterization':int((y==0).sum()),
      'AstroSpectroSB1_parent_count':astro_parent,'AstroSpectroSB1_in_95_sample':astro_sample,
      'AstroSpectroSB1_parent_coverage_fraction':float(astro_sample/astro_parent) if astro_parent else None,
      'AstroSpectroSB1_is_census_in_95_sample':bool(astro_sample==astro_parent),
      'OrbitalTargetSearchValidated_parent_count':otsv_parent,'OrbitalTargetSearchValidated_in_95_sample':otsv_sample,
      'sample_solution_type_counts':{str(k):int(v) for k,v in type_counts.items()},'parent_solution_type_counts':{str(k):int(v) for k,v in parent_type_counts.items()},
      'sample_mass_and_label_characterization':mass,'propensity_sensitivity':sensitivity,
      'conclusion':'NO DEFENSIBLE GENERAL-POPULATION LABEL CORRECTION. The 95-object characterization is a near-census of the parent AstroSpectroSB1 subgroup (94/94), plus one OrbitalTargetSearchValidated object, within a 2,119-object candidate set. The remaining 2,024 candidates lack compatible rho-based outcome labels in the archive and are predominantly different NSS solution types. Cross-validated propensity diagnostics show severe feature separation and weak effective sample size; propensity weighting cannot create missing outcomes or restore positivity.'}
    (out/'SELECTION_BIAS_95_REPRODUCED_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'parent_candidate_unique_ids':len(d),'n_sample':int(y.sum()),'sample_solution_type_counts':type_counts,
      'label_counts':mass['label_counts'],'propensity_summary':[{k:q[k] for k in ('C','selection_auc_5fold','nonselected_below_min_selected_propensity_fraction','transport_weight_ess_of_95','max_abs_smd_before','max_abs_smd_after_diagnostic_ipw')} for q in sensitivity],
      'conclusion':report['conclusion']},indent=2));return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--outdir',default='results/final_completion');a=p.parse_args();main(a.root,a.outdir)
