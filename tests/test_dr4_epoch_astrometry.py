"""Round trip: the real Gaia-4 pre-release table -> fake DR4 transit rows with 10-element arrays -> adapter -> identical table."""
import sys, os, numpy as np, pandas as pd, pytest
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_epoch_astrometry as EA
from dr4_adapters import JD_2010, REF_EPOCH_JD
from dr4_schema import SchemaError

def ref():
    return pd.read_csv(os.path.join(HERE, '..', 'data', 'gaia4.csv'), comment='#', header=None, names=['t', 'psi', 'w', 'err', 'fp'])

def as_dr4(R, per=9):
    rows = []
    for i in range(0, len(R) - len(R) % per, per):
        g = R.iloc[i:i+per]; tn = float((g.t.values.mean() - JD_2010 + REF_EPOCH_JD['J2017.5'])*86400e9); L = lambda a: str([float(x) for x in a])
        rows.append(dict(obs_time_tcb=L([tn]*10), obs_time_bary_corr=0.0, scan_pos_angle=L([g.psi.values[0]] + list(g.psi.values)),
                         centroid_pos_al=L([-999.0] + list(g.w.values)), centroid_pos_error_al=L([1.0] + list(g.err.values)),
                         parallax_factor_al=L([0.0] + list(g.fp.values)), used_by_agis_al=str([False] + [True]*per)))
    return pd.DataFrame(rows)

def test_round_trip_drops_sky_mapper_and_keeps_values():
    R = ref(); D = as_dr4(R); T = EA.to_fit_table(D); n = len(D)*9
    assert len(T) == n and not (T.w_mas == -999.0).any()
    assert np.allclose(np.sort(T.w_mas.values), np.sort(R.w.values[:n])) and np.allclose(np.sort(T.f_plx.values), np.sort(R.fp.values[:n]))

def test_wrong_time_unit_and_missing_columns_stop():
    D = as_dr4(ref())
    with pytest.raises(SchemaError): EA.to_fit_table(D.drop(columns=['parallax_factor_al']))
    D2 = D.copy(); D2['obs_time_tcb'] = D2.obs_time_tcb.str.replace('e', 'e-9', regex=False)
    with pytest.raises(Exception): EA.to_fit_table(D2)
