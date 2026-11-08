"""Adapter tests on SYNTHETIC fixtures (invented column names 'sid','tt','al','sg',... are NOT DR4 names)."""
import os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src')); sys.path.insert(0, os.path.dirname(__file__))
try: import pytest
except ImportError: import _minipytest as pytest
import numpy as np, pandas as pd, dr4_epoch_adapter as A

JD0 = 2455197.5
def mp(**kw):
    m = dict(layout='rows_per_observation', columns=dict(source_id='sid', time='tt', along_scan='al', uncertainty='sg', ccd=None, valid_flag=None),
             time_unit='ns_since_2010_tcb', ref_epoch='J2017.5', uncertainty_kind='sigma', min_observations=3)
    m.update(kw); return m
def table(n=6, ccd=False):
    jd = 2457500 + 100 * np.arange(n); d = pd.DataFrame(dict(sid=['11'] * n, tt=(jd - JD0) * 86400e9, al=np.arange(n) * .1, sg=np.full(n, .2)))
    if ccd: d['ccdid'] = np.arange(n) % 3
    return d, jd

def test_time_conversion_all_units():
    d, jd = table(); ref = 2457936.875
    r = A.adapt(d, mp())[0]['11']; assert np.allclose(r.t_days, jd - ref)
    d2 = d.assign(tt=jd - JD0); assert np.allclose(A.adapt(d2, mp(time_unit='days_since_2010_tcb'))[0]['11'].t_days, jd - ref)
    d3 = d.assign(tt=jd); assert np.allclose(A.adapt(d3, mp(time_unit='jd'))[0]['11'].t_days, jd - ref)
    assert np.allclose(A.adapt(d3, mp(time_unit='jd', ref_epoch=2016.0))[0]['11'].t_days, jd - 2457389.0, atol=1.0)

def test_wrong_time_unit_is_caught():
    d, _ = table(); with_raises = d.assign(tt=d.tt / 86400e9 * 86400)   # seconds mistaken for ns -> far outside mission
    with pytest.raises(A.EpochAdapterError): A.adapt(with_raises, mp())

def test_placeholder_and_missing_config_rejected():
    d, _ = table(); m = mp(); m['columns']['time'] = A.PLACEHOLDER
    with pytest.raises(A.EpochAdapterError, match='placeholder'): A.adapt(d, m)
    m = mp(); del m['ref_epoch']
    with pytest.raises(A.EpochAdapterError): A.adapt(d, m)
    with pytest.raises(A.EpochAdapterError): A.adapt(d, mp(time_unit='furlongs'))

def test_template_file_is_rejected_until_filled():
    p = os.path.join(os.path.dirname(__file__), '..', 'configs', 'dr4_epoch_astrometry_mapping.template.json')
    with pytest.raises(A.EpochAdapterError, match='placeholder'): A.load_mapping(p)

def test_unmapped_column_in_table_is_reported():
    d, _ = table(); with_raises = d.drop(columns='al')
    with pytest.raises(A.EpochAdapterError, match="'al'"): A.adapt(with_raises, mp())

def test_ccd_selection_rows():
    d, _ = table(6, ccd=True); m = mp(ccd_select=[0, 1], min_observations=2); m['columns']['ccd'] = 'ccdid'
    r, qc = A.adapt(d, m); assert len(r['11'].t_days) == 4 and qc['11']['n_other_ccd'] == 2 and set(r['11'].ccd) == {0., 1.}
    m2 = mp(ccd_select=[0]);
    with pytest.raises(A.EpochAdapterError, match='ccd'): A.adapt(d, m2)

def test_missing_values_sentinels_and_flags_dropped_and_counted():
    d, _ = table(8); d.loc[1, 'al'] = np.nan; d.loc[2, 'sg'] = -1.0; d.loc[3, 'al'] = -9999.; d['ok'] = [1, 1, 1, 1, 0, 1, 1, 1]
    m = mp(missing_sentinels=[-9999.], valid_flag_true_value=1); m['columns']['valid_flag'] = 'ok'
    r, qc = A.adapt(d, m); q = qc['11']; assert q['n_input'] == 8 and q['n_missing_or_bad_uncertainty'] == 3 and q['n_flagged_invalid'] == 1 and q['n_kept'] == 4
    assert np.isfinite(r['11'].al_mas).all() and (np.diff(r['11'].t_days) > 0).all()

def test_uncertainty_kinds_scale_floor_extra():
    s = A.sigma_from([0.2], 'variance'); assert np.allclose(s, np.sqrt(.2))
    assert np.allclose(A.sigma_from([4.0], 'inverse_variance'), 0.5)
    assert np.allclose(A.sigma_from([0.3], 'sigma', scale=2.0), 0.6)
    assert np.allclose(A.sigma_from([0.3], 'sigma', extra=0.4), 0.5)       # quadrature
    assert np.allclose(A.sigma_from([0.01], 'sigma', floor=0.1), 0.1)
    assert np.isnan(A.sigma_from([0.0], 'sigma')[0]) and np.isnan(A.sigma_from([-1.0], 'variance')[0])

def test_arrays_per_source_layout_with_nan_and_string_cells():
    jd = 2457500 + 100 * np.arange(5); t = ((jd - JD0) * 86400e9).tolist()
    d = pd.DataFrame(dict(sid=['7'], tt=[t], al=['[0.0, 0.1, NaN, 0.3, 0.4]'], sg=[[.2] * 5]))
    r, qc = A.adapt(d, mp(layout='arrays_per_source')); assert len(r['7'].t_days) == 4 and qc['7']['n_missing_or_bad_uncertainty'] == 1
    d2 = d.assign(sg=[[.2] * 4])
    with pytest.raises(A.EpochAdapterError, match='lengths'): A.adapt(d2, mp(layout='arrays_per_source'))

def test_too_few_observations_dropped_with_reason():
    d, _ = table(2); r, qc = A.adapt(d, mp(min_observations=3)); assert r == {} and 'fewer than' in qc['11']['dropped_source']
