import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np, pandas as pd, pytest
import gaiafp_qa_extensions as Q

def test_epoch_adapter_ns_and_ref_epoch():
    # 2017.5 epoch JD, observations around 2016-2019
    jd0=2455197.5; jd=np.array([2457000.,2457500.,2458000.]); ns=(jd-jd0)*86400e9
    d=pd.DataFrame({'sid':['1']*3,'t':ns,'al':[1.,2.,3.],'err':[.1,.1,.1]})
    r=Q.epoch_astrometry_to_relative_days(d,source_id='sid',time_col='t',time_unit='ns_since_2010',ref_epoch_jyear=2017.5,along_scan_col='al',uncertainty_col='err')['1']
    assert np.allclose(r['t_days'], jd-(2451545+(2017.5-2000)*365.25))

def test_epoch_adapter_requires_explicit_ccd_index_for_arrays():
    d=pd.DataFrame({'sid':['1'],'t':[[2457000.,2457001.,2457002.]],'al':[[1.,2.,3.]],'err':[[.1,.1,.1]]})
    with pytest.raises(Q.QAInputError):
        Q.epoch_astrometry_to_relative_days(d,source_id='sid',time_col='t',time_unit='jd',ref_epoch_jyear=2017.5,along_scan_col='al',uncertainty_col='err')

def test_correlated_ti_draws_uses_covariance():
    row={}
    for k,v in zip('abfg',[1.,2.,3.,4.]): row[f'{k}_thiele_innes']=v; row[f'{k}_thiele_innes_error']=.1
    cov=np.eye(4)*.01; cov[0,1]=cov[1,0]=.008; row['ti_covariance']=cov
    x,meta=Q.draw_thiele_innes(row,50000,seed=3)
    assert meta['full_covariance_used'] and abs(np.corrcoef(x.T)[0,1]-.8)<.02

def test_covariance_rejects_non_psd():
    row={}
    for k,v in zip('abfg',[1.,2.,3.,4.]): row[f'{k}_thiele_innes']=v; row[f'{k}_thiele_innes_error']=.1
    row['ti_covariance']=np.array([[.01,.02,0,0],[.02,.01,0,0],[0,0,.01,0],[0,0,0,.01]])
    with pytest.raises(Q.QAInputError): Q.draw_thiele_innes(row)

def test_mass_relation_sensitivity_no_extrapolation():
    r=Q.mass_relation_sensitivity([4.,5.,20.],{'iso_A':([3,5,7],[1.2,.8,.5])})
    assert np.isfinite(r['iso_A']['mass_solar'][0]) and np.isnan(r['iso_A']['mass_solar'][2])

def test_bootstrap_null_calibration_is_reproducible():
    a=Q.bootstrap_null_calibration(n_rep=100,n_each_class=20,n_boot=100,seed=5)
    b=Q.bootstrap_null_calibration(n_rep=100,n_each_class=20,n_boot=100,seed=5)
    assert a==b and 0<=a['type1_at_0.05']<=1
