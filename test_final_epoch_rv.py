import sys
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'epoch_rv'))
from process_lamost_dr9_lrs import process as process_lamost, load_exact_obs_times
from process_apogee_allvisit import process as process_apogee
from build_apogee_mapping import build as build_apogee_mapping
from run_exact_cadence_injection import true_anomaly,kepler_rv,detect

def test_lamost_exact_dr3_crossmatch_and_summary(tmp_path):
    c=tmp_path/'cand.csv'; pd.DataFrame({'source_id':['10','20']}).to_csv(c,index=False)
    x=tmp_path/'lam.csv'; pd.DataFrame({'gaia_source_id':['10']*3+['99'],'obsid':['1','2','3','4'],
      'mjd':[59000,59001,59002,59003],'rv':[1.,2.,1.5,99.],'rv_err':[.2]*4,'snrg':[20]*4,'fibertype':['Obj','Obj','Obj','F-std']}).to_csv(x,index=False)
    o=tmp_path/'out';s=process_lamost(x,c,o)
    assert s['matched_epoch_rows']==3 and s['sources_with_ge3_valid_epochs']==1
    q=pd.read_csv(o/'lamost_dr9_lrs_source_summary.csv')
    assert q.iloc[0].source_id==10 and q.iloc[0].n_epochs==3
    assert 'per_spectrum_mjd' in q.iloc[0].timestamp_source or 'MJD' in q.iloc[0].timestamp_source

def test_lamost_multi_epoch_minute_join(tmp_path):
    c=tmp_path/'cand.csv'; pd.DataFrame({'source_id':['10']}).to_csv(c,index=False)
    x=tmp_path/'lam.csv'; pd.DataFrame({'gaia_source_id':['10']*3,'obsid':['101','102','103'],
      'rv':[1.,2.,1.5],'rv_err':[.2]*3,'fibertype':['Obj']*3}).to_csv(x,index=False)
    me=tmp_path/'multi.csv';pd.DataFrame({'obs_number':[3],'obsid_list':['101-102-103'],
      'midmjm_list':['84960000-84961440-84962880']}).to_csv(me,index=False)
    out=tmp_path/'out';s=process_lamost(x,c,out,me)
    assert s['exact_multi_epoch_join_used'] is True and s['exact_midmjm_rows_matched']==3
    q=pd.read_csv(out/'lamost_dr9_lrs_source_summary.csv')
    assert abs(q.iloc[0].baseline_days-2.0)<1e-8

def test_lamost_multi_epoch_misaligned_lists_rejected(tmp_path):
    p=tmp_path/'multi.csv';pd.DataFrame({'obs_number':[2],'obsid_list':['1-2'],'midmjm_list':['100']}).to_csv(p,index=False)
    import pytest
    with pytest.raises(ValueError,match='No aligned numeric'):
        load_exact_obs_times(p)

def test_apogee_uses_jd_and_vrelerr_and_reject_masks(tmp_path):
    m=tmp_path/'map.csv';pd.DataFrame({'source_id':['123'],'APOGEE_ID':['starA']}).to_csv(m,index=False)
    v=tmp_path/'v.csv';pd.DataFrame({'APOGEE_ID':['starA']*4,'JD':[2459000.1,2459001.2,2459002.3,2459003.4],
      'MJD':[59000,59001,59002,59003],'VHELIO':[1,2,1,2],'VRELERR':[.1]*4,
      'STARFLAG':[0,0,1<<19,0],'RV_FLAG':[0,0,0,0]}).to_csv(v,index=False)
    o=tmp_path/'out';s=process_apogee(v,m,o)
    assert s['matched_rows']==4 and s['accepted_rows']==3 and s['timestamp_used'].startswith('JD')
    q=pd.read_csv(o/'apogee_allvisit_accepted.csv');assert np.allclose(q.JD,[2459000.1,2459001.2,2459003.4])
    assert 'VERR' in q

def test_apogee_emits_strict_persistence_sensitivity_subset(tmp_path):
    m=tmp_path/'map.csv';pd.DataFrame({'source_id':['123'],'APOGEE_ID':['starA']}).to_csv(m,index=False)
    v=tmp_path/'v.csv';pd.DataFrame({'APOGEE_ID':['starA']*4,'JD':[2459000.1,2459001.2,2459002.3,2459003.4],
      'VHELIO':[1,2,1,2],'VRELERR':[.1]*4,'STARFLAG':[0,0,1<<9,1<<12],'RV_FLAG':[0]*4}).to_csv(v,index=False)
    o=tmp_path/'out';s=process_apogee(v,m,o)
    assert s['accepted_primary_rows']==4 and s['accepted_strict_quality_rows']==2
    strict=pd.read_csv(o/'apogee_allvisit_high_quality.csv')
    assert len(strict)==2


def test_apogee_rejects_integer_mjd_as_exact_cadence(tmp_path):
    m=tmp_path/'map.csv';pd.DataFrame({'source_id':['123'],'APOGEE_ID':['starA']}).to_csv(m,index=False)
    v=tmp_path/'v.csv';pd.DataFrame({'APOGEE_ID':['starA']*3,'MJD':[59000,59001,59002],'VHELIO':[1,2,1],
      'VRELERR':[.1]*3,'STARFLAG':[0]*3}).to_csv(v,index=False)
    import pytest
    with pytest.raises(ValueError,match='integer-day only'):
        process_apogee(v,m,tmp_path/'out')

def test_build_apogee_mapping_exact_gaia_id_and_ambiguous_exclusion(tmp_path):
    s=tmp_path/'allstar.csv';pd.DataFrame({'GAIAEDR3_SOURCE_ID':['10','20','30','30'],'APOGEE_ID':['a','b','c','d']}).to_csv(s,index=False)
    c=tmp_path/'cand.csv';pd.DataFrame({'source_id':['10','20','30','40']}).to_csv(c,index=False)
    out=tmp_path/'map';r=build_apogee_mapping(s,c,out)
    mp=pd.read_csv(out/'apogee_gaia_dr3_mapping.csv',dtype={'source_id':'string'})
    assert set(mp.source_id)=={'10','20'} and r['ambiguous_source_ids']==1
    assert r['candidate_sources_unmapped_or_ambiguous']==2

def test_keplerian_rv_is_deterministic_and_zero_e_limit():
    t=np.array([0.,10.,20.,30.]);a=kepler_rv(t,20.,0.,5.,0.,0.);b=kepler_rv(t,20.,0.,5.,0.,0.)
    assert np.allclose(a,b) and np.isfinite(a).all()

def test_constant_data_not_detected_with_small_errors():
    y=np.array([1.,1.01,.99,1.]);e=np.array([.1]*4);assert not detect(y,e)

def test_exact_cadence_runner_refuses_mjd_only(tmp_path):
    from run_exact_cadence_injection import run
    import pytest
    p=tmp_path/'epochs.csv';pd.DataFrame({'source_id':['42']*3,'MJD':[59000.,59011.,59038.],'VERR':[.2,.25,.3]}).to_csv(p,index=False)
    with pytest.raises(ValueError,match='integer MJD is insufficient'):
        run(p,tmp_path/'inj',n_trials=4,seed=17)

def test_exact_cadence_runner_uses_true_jd_values(tmp_path):
    from run_exact_cadence_injection import run
    p=tmp_path/'epochs.csv';pd.DataFrame({'source_id':['42']*3,'JD':[2459000.2,2459011.3,2459038.4],'VERR':[.2,.25,.3]}).to_csv(p,index=False)
    out=tmp_path/'inj';s=run(p,out,n_trials=4,seed=17)
    assert s['targets_with_ge3_epochs']==1
    q=pd.read_csv(out/'exact_apogee_cadence_injection.csv')
    assert set(q.source_id.astype(str))=={'42'} and q.n_trials.eq(4).all()
    assert np.allclose(q.baseline_days,38.2)


def test_apogee_mapping_allows_same_gaia_source_in_multiple_fields(tmp_path):
    s=tmp_path/'allstar.csv';pd.DataFrame({
      'GAIAEDR3_SOURCE_ID':['10','10','20'], 'APOGEE_ID':['a','a','b'],
      'FIELD':['north','south','north']}).to_csv(s,index=False)
    c=tmp_path/'cand.csv';pd.DataFrame({'source_id':['10','20']}).to_csv(c,index=False)
    out=tmp_path/'map';r=build_apogee_mapping(s,c,out)
    mp=pd.read_csv(out/'apogee_gaia_dr3_mapping.csv',dtype={'source_id':'string'})
    assert len(mp)==3 and set(mp.loc[mp.source_id=='10','FIELD'])=={'north','south'}
    assert r['ambiguous_rows']==0 and r['multiple_fields_per_gaia_source_allowed'] is True


def test_apogee_process_aggregates_visits_across_fields(tmp_path):
    m=tmp_path/'map.csv';pd.DataFrame({
      'source_id':['123','123'],'APOGEE_ID':['starA','starA'],'FIELD':['f1','f2']}).to_csv(m,index=False)
    v=tmp_path/'v.csv';pd.DataFrame({
      'APOGEE_ID':['starA']*4,'FIELD':['f1','f1','f2','f2'],
      'JD':[2459000.1,2459001.1,2459002.1,2459003.1],
      'VHELIO':[1,2,3,4],'VRELERR':[.1]*4,'STARFLAG':[0]*4,'RV_FLAG':[0]*4
    }).to_csv(v,index=False)
    o=tmp_path/'out';summary=process_apogee(v,m,o)
    assert summary['matched_sources']==1 and summary['matched_rows']==4
    q=pd.read_csv(o/'apogee_allvisit_source_summary.csv')
    assert q.iloc[0].n_epochs==4 and set(q.iloc[0].FIELDS.split(';'))=={'f1','f2'}
