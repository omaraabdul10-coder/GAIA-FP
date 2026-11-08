import sys, os, numpy as np, pandas as pd, pytest
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_schema as S

def dr3_orbits():
    # Use only source data actually present in the distributed project:
    # the 71,759-row DR3 NSS export plus the 95-row C/H astrospectro subset.
    # The inner join is an explicit schema-test fixture, NOT a replacement for
    # the absent full dr3_astrospectro_all.csv population.
    root = os.path.join(HERE, '..', 'realdata')
    nss = pd.read_csv(os.path.join(root, 'dr3_nss_two_body_orbit_raw.csv'), dtype={'source_id': str})
    ch = pd.read_csv(os.path.join(root, 'dr3_astrospectro_ch.csv'), dtype={'source_id': str})
    out = nss.merge(ch, on='source_id', how='inner', validate='one_to_one')
    if len(out) != 95:
        raise RuntimeError(f'Expected the documented 95-row C/H fixture, got {len(out)}')
    return out

def test_dr3_table_passes():
    O = dr3_orbits(); assert S.check(O, S.ORBIT, 'orbits') and S.check(O, S.COMBINED, 'combined') and S.check_unit_plausibility(O)

def test_missing_column_stops():
    with pytest.raises(S.SchemaError): S.check(dr3_orbits().drop(columns=['period']), S.ORBIT, 'orbits')

def test_unit_errors_stop():
    O = dr3_orbits()
    with pytest.raises(S.SchemaError): S.check_unit_plausibility(O.assign(a_thiele_innes=O.a_thiele_innes/1000, b_thiele_innes=O.b_thiele_innes/1000,
                                                                           f_thiele_innes=O.f_thiele_innes/1000, g_thiele_innes=O.g_thiele_innes/1000))
    with pytest.raises(S.SchemaError): S.check_unit_plausibility(O.assign(period=O.period/365.25))
    with pytest.raises(S.SchemaError): S.check(O.assign(eccentricity=O.eccentricity*100), S.ORBIT, 'orbits')

def test_float_mangled_ids_stop():
    O = dr3_orbits(); O['source_id'] = O.source_id.astype(float).astype(str)
    with pytest.raises(S.SchemaError): S.check(O, S.ORBIT, 'orbits')

def test_empty_stops():
    with pytest.raises(S.SchemaError): S.check(pd.DataFrame(), S.ORBIT, 'orbits')
