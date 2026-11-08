import sys, os, numpy as np, pandas as pd, pytest
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_release_map as RM, dr4_adapters as A
from dr4_schema import SchemaError

def test_c_from_semi_amplitude_matches_dr3():
    # DR3 combined solutions give both C,H and (via K1) a1 sin i: rebuild hypot(C,H) from K1 and compare
    D = pd.read_csv(os.path.join(HERE, '..', 'realdata', 'dr3_astrospectro_all.csv')).head(500)
    e = D.eccentricity.fillna(0); a1 = np.hypot(D.c_thiele_innes, D.h_thiele_innes)
    K = a1*2*np.pi*RM.AU_KM/(D.period*86400*np.sqrt(1 - e**2))
    O = RM.nss(D.drop(columns=['c_thiele_innes', 'h_thiele_innes', 'c_thiele_innes_error', 'h_thiele_innes_error'])
               .assign(solution_type='AstroSpectroSB1', semi_amplitude_primary=K, semi_amplitude_primary_error=0.05*K)
               .drop(columns=[c for c in ('nss_solution_type',) if c in D]))
    assert np.allclose(np.hypot(O.c_thiele_innes, O.h_thiele_innes), a1, rtol=1e-10) and (O.nss_solution_type == 'AstroSpectroSB1').all()

def test_neighbourhood_mas_to_arcsec():
    M = RM.neighbourhood(pd.DataFrame(dict(source_id=['1'], dr3_source_id=['2'], angular_distance=[250.0])))
    assert M.angular_distance_arcsec.iloc[0] == 0.25

def test_rvs_epochs_feed_adapter_with_validity_and_bary():
    df = pd.DataFrame(dict(source_id='7', obs_time_rv=np.linspace(1800, 3500, 12), obs_time_bary_corr=np.full(12, 86400e9*0.004),
                           vbroad=np.linspace(8, 12, 12), vbroad_error=1.0, vbroad_validity_flag=[True]*10 + [False]*2))
    r = A.standardise(RM.rvs_epochs(df), 'days_since_2010', 'J2017.5')['7']
    assert len(r['t']) == 10 and abs(r['t'][0] - (1800.004 + A.JD_2010 - A.REF_EPOCH_JD['J2017.5'])) < 1e-6

def test_missing_columns_stop():
    with pytest.raises(SchemaError): RM.nss(pd.DataFrame(dict(source_id=['1'])))

def test_epoch_photometry_both_structures():
    import dr4_release_map as R
    g = pd.DataFrame(dict(source_id=[1, 1, 1], g_obs_time=[1.0, 2.0, 3.0], g_flux=[10.0, -1.0, 11.0], g_flux_error=[.1, .1, .1], g_n_obs=[9, 9, 0]))
    assert len(R.epoch_photometry(g)) == 1
    s = pd.DataFrame(dict(source_id=[1]*4, band=['G', 'BP', 'G', 'G'], time=[1.0, 1.0, 2.0, 3.0], flux=[10.0, 5.0, 11.0, 12.0],
                          flux_error=[.1]*4, rejected_by_photometry=[False, False, True, False]))
    out = R.epoch_photometry(s); assert list(out.g_obs_time) == [1.0, 3.0] and set(out.columns) == {'source_id', 'g_obs_time', 'g_flux', 'g_flux_error'}

def test_a1_error_includes_eccentricity():
    import dr4_release_map as R
    base = dict(source_id=['1'], solution_type=['AstroSpectroSB1'], period=[100.0], period_error=[0.0], eccentricity=[0.6],
                semi_amplitude_primary=[10.0], semi_amplitude_primary_error=[0.0])
    lo = R.nss(pd.DataFrame(base | dict(eccentricity_error=[0.0]))); hi = R.nss(pd.DataFrame(base | dict(eccentricity_error=[0.05])))
    assert lo.c_thiele_innes_error.iloc[0] == 0 and abs(hi.c_thiele_innes_error.iloc[0]/hi.c_thiele_innes.iloc[0] - 0.6*0.05/0.64) < 1e-9
