"""8 Nov 2026: dr4_fetch (DR4 names, chunked id queries, no unrestricted joins) and dr4_day.prepare, against a fake archive."""
import sys, os, re, json, numpy as np, pandas as pd
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_fetch as F, dr4_day
REAL = os.path.join(HERE, '..', 'realdata')

class _Job:
    def __init__(self, df): self.df = df; self.jobid = 'fake'
    def get_results(self): return self
    def to_pandas(self): return self.df

class FakeGaia:
    """Answers the queries of dr4_fetch with small DR3-derived tables renamed to the DR4 data model."""
    def __init__(self):
        c = pd.read_csv(os.path.join(REAL, 'dr3_candidates.csv'), dtype={'source_id': str}).drop_duplicates('source_id').head(60)
        self.cand = c.rename(columns={'nss_solution_type': 'solution_type'}).assign(semi_amplitude_primary=np.nan,
                                                                                    semi_amplitude_primary_error=np.nan, ref_epoch=2017.5)
        self.cand.loc[self.cand.index[:10], ['solution_type', 'semi_amplitude_primary', 'semi_amplitude_primary_error']] = ['AstroSpectroSB1', 12.0, 0.5]
        self.queries = []
    def launch_job_async(self, q):
        self.queries.append(q); Q = q.upper()
        if 'TAP_SCHEMA' in Q:
            need = {'gaia_source': F.SRC_COLS + F.RVS_COLS + ['parallax_over_error', 'random_index', 'parallax'], 'nss_two_body_orbit': F.NSS_COLS_DR4,
                    'all_source_flags': ['source_id', 'non_single_star'], 'dr3_neighbourhood': ['source_id', 'dr3_source_id', 'angular_distance'],
                    'nss_masses': F.MASS_COLS_DR4}
            return _Job(pd.DataFrame([dict(table_name=f'gaiadr4.{t}', column_name=c, unit='') for t, cs in need.items() for c in cs]))
        if 'TOP 1 REF_EPOCH' in Q: return _Job(pd.DataFrame(dict(ref_epoch=[2017.5])))
        if 'COUNT(*)' in Q: return _Job(pd.DataFrame(dict(solution_type=['Orbital'], n=[1])))
        if 'DR3_NEIGHBOURHOOD' in Q:
            ids = re.findall(r'\d{6,}', q); return _Job(pd.DataFrame(dict(source_id=ids, dr3_source_id=ids, angular_distance=12.0)))
        if 'NSS_MASSES' in Q:                                   # archive m1 for half of the sources only (tests the fallback)
            ids = sorted(set(re.findall(r'\d{6,}', q)))[::2]
            return _Job(pd.DataFrame(dict(source_id=ids, m1=0.9, m1_lower=0.8, m1_upper=1.0, fluxratio=0.1, combination_method='Orbital',
                                          exoplanet_candidate_hrd_proba=0.2, lowmass_candidate_hrd_proba=0.3)))
        if 'SOURCE_ID IN' in Q and 'NSS_TWO_BODY_ORBIT' in Q:
            ids = set(re.findall(r'\d{6,}', q)); C = self.cand[self.cand.source_id.isin(ids)]
            return _Job(C[[c for c in F.NSS_COLS_DR4 if c in C]])
        if 'SOURCE_ID IN' in Q:
            ids = set(re.findall(r'\d{6,}', q)); C = self.cand[self.cand.source_id.isin(ids)]
            return _Job(C[['source_id']].assign(grvs_mag=12.0, vbroad=9.0, vbroad_error=1.0, vbroad_nb_transits=10))
        if "= 'ASTROSPECTROSB1'" in Q:
            return _Job(self.cand.head(10)[[c for c in F.NSS_COLS_DR4 if c in self.cand] + ['phot_g_mean_mag', 'bp_rp', 'ruwe']]
                        .assign(vbroad=9.0, vbroad_error=1.0, vbroad_nb_transits=10, grvs_mag=12.0))
        if 'VBROAD IS NOT NULL' in Q: return _Job(pd.read_csv(os.path.join(REAL, 'dr3_field_vbroad.csv')).head(500))
        if 'TOP 200000' in Q: return _Job(pd.read_csv(os.path.join(REAL, 'dr3_field.csv')).head(500).assign(source_id='1'))
        if "IN ('ORBITAL'" in Q:
            return _Job(self.cand[[c for c in F.NSS_COLS_DR4 if c in self.cand] + ['phot_g_mean_mag', 'bp_rp', 'ruwe', 'ref_epoch']])
        raise AssertionError('unexpected query: ' + q[:200])

def test_fetch_dr4_names_chunks_and_prepare(tmp_path):
    G = FakeGaia(); raw, std = tmp_path/'raw', tmp_path/'std'
    st = F.main(['--release', 'gaiadr4', '--out', str(raw), '--skip-rvs'], Gaia=G)
    assert st == 'OK', st
    for q in G.queries:
        assert 'nss_solution_type' not in q                       # DR4 name
        if ' IN (' in q and 'solution_type IN' not in q: assert len(re.findall(r'\d{6,}', q)) <= F.CHUNK
        if 'non_single_star' in q: assert 'all_source_flags' in q
    nbh = [q for q in G.queries if 'dr3_neighbourhood' in q]
    assert len(nbh) >= 2                                          # DR3 candidates + sealed + AstroSpectroSB1 + controls, chunked
    ids = set(sum((re.findall(r'\d{6,}', q) for q in nbh), []))
    sealed = set(pd.read_csv(os.path.join(REAL, 'excluded_sealed_ids.csv'), dtype=str).source_id.str.strip())
    assert sealed <= ids                                          # sealed ids are mapped (ids only), so H1 can be evaluated
    prov = json.load(open(raw/'provenance.json')); assert prov['status'] == 'OK'
    info = dr4_day.prepare(str(raw), str(std))
    C = pd.read_csv(std/'candidates.csv'); M = pd.read_csv(std/'dr3_dr4_map.csv'); A = pd.read_csv(std/'dr4_combined.csv')
    assert {'nss_solution_type', 'c_thiele_innes', 'h_thiele_innes', 'grvs_mag', 'vbroad'} <= set(C.columns)
    assert set(M.columns) == {'dr3_source_id', 'dr4_source_id', 'angular_distance_arcsec'} and (M.angular_distance_arcsec == 0.012).all()
    assert len(A) >= 10 and A.c_thiele_innes.notna().sum() == 10     # only the rows that carry semi_amplitude_primary
    assert info['n_candidates'] == 60
    assert C.m1.notna().all() and set(C.m1_source) == {'archive', 'photometric'} and 0 < info['n_m1_photometric_fallback'] < 60
    assert (std/'dpac_masses.csv').exists()

def test_print_queries_has_no_unrestricted_rvs_join(capsys):
    F.main(['--release', 'gaiadr4', '--print-queries'])
    out = capsys.readouterr().out
    assert 'all_source_rvs' not in out and 'JOIN gaiadr4.nss_two_body_orbit' not in out
