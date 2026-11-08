"""RVS epoch adapter: three formats must give identical arrays; wrong time units / ambiguous columns must stop the run;
an injected phase-locked signal must survive the adapter + frozen rvs_z with a z that matches the direct computation."""
import sys, os, numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_adapters as A
from dr4_schema import SchemaError
from dr4_pipeline import rvs_z

def synth(n=30, seed=0):
    rng = np.random.default_rng(seed); t2010 = np.sort(rng.uniform(1700, 3600, n))       # days since 2010-01-01
    P, e, T0, om = 400.0, 0.3, 50.0, 70.0                                                 # T0 relative to J2017.5
    t_rel = t2010 + A.JD_2010 - A.REF_EPOCH_JD['J2017.5']
    from rvs_phase_test import true_anomaly
    nu = true_anomaly(t_rel, P, e, T0); tmpl = (np.cos(nu + np.radians(om)) + e*np.cos(np.radians(om)))**2
    w = np.sqrt(10**2 + 0.25*(40**2)*tmpl) + rng.normal(0, 1, n)
    return t2010, w, np.full(n, 1.0), (P, e, T0, om), t_rel

def test_formats_agree_and_signal_survives():
    t, w, e, (P, ecc, T0, om), t_rel = synth()
    fa = pd.DataFrame(dict(source_id='123', rv_obs_time=t, vbroad=w, vbroad_error=e))
    fa2 = fa.assign(ccd_array=[[1, 2, 3]]*len(t))
    fb = pd.DataFrame(dict(source_id=['123'], obs_time_tcb=['(' + ', '.join(repr(float(x)) for x in t*86400e9) + ')'], line_broadening=[list(w)], vbroad_error=['[' + ', '.join(repr(float(x)) for x in e) + ']']))
    ra = A.standardise(fa, 'days_since_2010', 'J2017.5')['123']; ra2 = A.standardise(fa2, 'days_since_2010', 'J2017.5')['123']
    rb = A.standardise(fb, 'ns_since_2010', 'J2017.5')['123']
    for r in (ra2, rb):
        assert np.allclose(r['t'], ra['t'], atol=1e-6) and np.allclose(r['width'], ra['width'])
    assert np.allclose(ra['t'], t_rel)
    z, n = rvs_z(ra['t'], ra['width'], P, ecc, T0, om); z0, _ = rvs_z(t_rel, w, P, ecc, T0, om)
    assert n == 30 and abs(z - z0) < 1e-9 and z > 3

def test_wrong_reference_epoch_loses_signal():
    t, w, e, (P, ecc, T0, om), _ = synth(seed=1)
    fa = pd.DataFrame(dict(source_id='1', rv_obs_time=t, vbroad=w, vbroad_error=e))
    good = A.standardise(fa, 'days_since_2010', 'J2017.5')['1']; bad = A.standardise(fa, 'days_since_2010', 'J2016.0')['1']
    assert rvs_z(good['t'], good['width'], P, ecc, T0, om)[0] > rvs_z(bad['t'], bad['width'], P, ecc, T0, om)[0]

def test_wrong_time_unit_stops():
    t, w, e, *_ = synth()
    fa = pd.DataFrame(dict(source_id='1', rv_obs_time=t*86400e9, vbroad=w, vbroad_error=e))
    with pytest.raises(SchemaError): A.standardise(fa, 'days_since_2010', 'J2017.5')

def test_ambiguous_or_missing_columns_stop():
    t, w, e, *_ = synth()
    with pytest.raises(SchemaError): A.standardise(pd.DataFrame(dict(source_id='1', rv_obs_time=t, obs_time=t, vbroad=w, vbroad_error=e)), 'days_since_2010', 'J2017.5')
    with pytest.raises(SchemaError): A.standardise(pd.DataFrame(dict(source_id='1', rv_obs_time=t, vbroad=w)), 'days_since_2010', 'J2017.5')
