"""
dr4_fetch.py: every network download for DR4 day. Runs on a computer with internet and a REGISTERED Gaia archive account.

    python dr4_fetch.py --release gaiadr3 --out dr3_fetch_test --user <login>   # test BEFORE 25 Nov 2026, 12:00 CET
    python dr4_fetch.py --release gaiadr4 --out dr4_raw --user <login>          # 2 Dec 2026
    python dr4_fetch.py --release gaiadr3 --control-group --out h11_ctrl --user <login>
    python dr4_fetch.py --release gaiadr4 --print-queries                       # show every ADQL query, no network

Writes into --out (raw, archive column names; dr4_day.py prepare converts them):

| File | Contents |
|---|---|
| candidates.csv | frozen candidate selection (v0.4) |
| field.csv | frozen CMD field query |
| dr3_neighbourhood_raw.csv | DR3 -> DR4 id map for DR3 candidates, sealed ids and DR3 AstroSpectroSB1 ids (DR4 only) |
| h11_orbits.csv | every DR4 orbit (any type) of the DR4 counterparts of the DR3 candidates and of the H11 controls |
| combined_orbits.csv | all AstroSpectroSB1 orbits with parallax_over_error > 10, plus source columns (D3 of DARK_COMPANION_PLAN) |
| field_vbroad.csv | D2 field vbroad calibration |
| nss_masses.csv | archive primary masses m1 (DR4 nss_masses; DR3 binary_masses) + DPAC flux ratio for candidates and combined orbits |
| rvs_mean.csv | grvs/vbroad of the candidates only |
| rvs_epochs_raw.csv | per-transit RVS (DataLink), candidates with G_RVS <= 14 |
| epoch_photometry_raw.csv | H17, secondary; failure does not stop the run |
| provenance.json | row counts, SHA-256, ADQL, job ids, schema snapshot |

Design rules (v0.6 A22, DR4_READINESS.md):
- The schema is checked first; a missing table or column STOPS the run.
- Every id list is sent in chunks of <= 2000 ids. No query joins an unrestricted DR4 table to another (8 Nov fix).
- DR4 data model (draft of 26 Jun 2026):
  - `solution_type` replaces `nss_solution_type`;
  - there are no c/h_thiele_innes (semi_amplitude_primary is used instead);
  - `non_single_star` is in `all_source_flags`, not in `gaia_source`.
  The selection criteria are unchanged; only the table and column names are mapped (deviation 29).
"""
import argparse, getpass, hashlib, json, os, sys, time
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); REAL = os.path.join(HERE, '..', 'realdata')
TABLES = {'gaiadr3': dict(source='gaiadr3.gaia_source', nss='gaiadr3.nss_two_body_orbit', flags=None, nbh=None, ref_epoch=2016.0, masses='gaiadr3.binary_masses',
                          tcol='nss_solution_type'),
          'gaiadr4': dict(source='gaiadr4.gaia_source', nss='gaiadr4.nss_two_body_orbit', flags='gaiadr4.all_source_flags', masses='gaiadr4.nss_masses',
                          nbh='gaiadr4.dr3_neighbourhood', ref_epoch=2017.5, tcol='solution_type')}
NSS_COLS_DR4 = ['source_id', 'solution_type', 'period', 'period_error', 'eccentricity', 'eccentricity_error', 't_periastron',
                'a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes', 'a_thiele_innes_error', 'b_thiele_innes_error',
                'f_thiele_innes_error', 'g_thiele_innes_error', 'semi_amplitude_primary', 'semi_amplitude_primary_error',
                'parallax', 'parallax_error', 'significance']
NSS_COLS = ['source_id', 'nss_solution_type', 'period', 'period_error', 'eccentricity', 'eccentricity_error', 't_periastron',
            'a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes', 'c_thiele_innes', 'h_thiele_innes',
            'a_thiele_innes_error', 'b_thiele_innes_error', 'f_thiele_innes_error', 'g_thiele_innes_error',
            'c_thiele_innes_error', 'h_thiele_innes_error', 'parallax', 'parallax_error', 'significance']
SRC_COLS = ['source_id', 'phot_g_mean_mag', 'bp_rp', 'ruwe', 'ref_epoch']
RVS_COLS = ['source_id', 'grvs_mag', 'vbroad', 'vbroad_error', 'vbroad_nb_transits']
CHUNK = 2000
PROV = dict(started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), files={}, queries=[])

class FetchError(RuntimeError): pass

def sha(path): return hashlib.sha256(open(path, 'rb').read()).hexdigest()
def save(df, path): df.to_csv(path, index=False); PROV['files'][os.path.basename(path)] = dict(rows=len(df), sha256=sha(path))
def chunks(x, n=CHUNK): x = list(x); return [x[i:i+n] for i in range(0, len(x), n)]
def nss_cols(T): return NSS_COLS_DR4 if T['tcol'] == 'solution_type' else NSS_COLS

def run(Gaia, q, name):
    t0 = time.time(); job = Gaia.launch_job_async(q); df = job.get_results().to_pandas()
    PROV['queries'].append(dict(name=name, adql=q, job_id=getattr(job, 'jobid', None), rows=len(df), seconds=round(time.time()-t0, 1)))
    return df

def run_in(Gaia, ids, build, name):
    """Run build(id_list_sql) for every chunk of ids and concatenate."""
    frames = [run(Gaia, build(', '.join(str(int(i)) for i in ch)), f'{name} [{k+1}/{len(chunks(ids))}]') for k, ch in enumerate(chunks(ids))]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ------------------------------------------------------------------ queries (frozen criteria; only names differ by release)
def q_candidates(T):
    import dr4_pipeline as D
    s = D.SELECTION; types = ', '.join(f"'{t}'" for t in s['solution_types'])
    return (f"SELECT {', '.join('o.'+c for c in nss_cols(T))}, {', '.join('g.'+c for c in SRC_COLS[1:])} FROM {T['nss']} AS o "
            f"JOIN {T['source']} AS g USING (source_id) WHERE o.{T['tcol']} IN ({types}) "
            f"AND o.parallax/o.parallax_error > {s['min_parallax_over_error']} AND o.parallax > {1000.0/s['max_dist_pc']}")

def q_field(T, n=200000):
    """dr4_pipeline.adql_field_stars criteria. DR4: non_single_star lives in all_source_flags."""
    crit = "g.parallax_over_error > 20 AND g.ruwe < 1.2 AND g.parallax > 2 AND {nss} = 0 AND g.random_index < 5000000"
    if T['flags']:
        return (f"SELECT TOP {n} g.source_id, g.phot_g_mean_mag, g.bp_rp, g.parallax FROM {T['source']} AS g "
                f"JOIN {T['flags']} AS f USING (source_id) WHERE " + crit.format(nss='f.non_single_star'))
    return f"SELECT TOP {n} g.source_id, g.phot_g_mean_mag, g.bp_rp, g.parallax FROM {T['source']} AS g WHERE " + crit.format(nss='g.non_single_star')

def q_field_vbroad(T, n=30000):
    """DARK_COMPANION_PLAN D2: vbroad not null, non_single_star = 0, RUWE < 1.2, parallax_over_error > 10, random_index order."""
    cols = 'g.bp_rp, g.grvs_mag, g.vbroad, g.vbroad_error, g.vbroad_nb_transits, g.phot_g_mean_mag, g.parallax'
    crit = "g.vbroad IS NOT NULL AND {nss} = 0 AND g.ruwe < 1.2 AND g.parallax_over_error > 10 ORDER BY g.random_index"
    if T['flags']:
        return f"SELECT TOP {n} {cols} FROM {T['source']} AS g JOIN {T['flags']} AS f USING (source_id) WHERE " + crit.format(nss='f.non_single_star')
    return f"SELECT TOP {n} {cols} FROM {T['source']} AS g WHERE " + crit.format(nss='g.non_single_star')

def q_combined(T):
    """DARK_COMPANION_PLAN D3: every AstroSpectroSB1 orbit with parallax_over_error > 10, with source and RVS columns."""
    return (f"SELECT {', '.join('o.'+c for c in nss_cols(T))}, g.phot_g_mean_mag, g.bp_rp, g.ruwe, g.vbroad, g.vbroad_error, "
            f"g.vbroad_nb_transits, g.grvs_mag FROM {T['nss']} AS o JOIN {T['source']} AS g USING (source_id) "
            f"WHERE o.{T['tcol']} = 'AstroSpectroSB1' AND o.parallax/o.parallax_error > 10")

def q_nbh(T, idlist): return f"SELECT source_id, dr3_source_id, angular_distance FROM {T['nbh']} WHERE dr3_source_id IN ({idlist})"
def q_orbits_by_id(T, idlist): return f"SELECT {', '.join(nss_cols(T))} FROM {T['nss']} WHERE source_id IN ({idlist})"
MASS_COLS = ['source_id', 'm1', 'm1_lower', 'm1_upper', 'fluxratio', 'combination_method']
MASS_COLS_DR4 = MASS_COLS + ['exoplanet_candidate_hrd_proba', 'lowmass_candidate_hrd_proba']
def mass_cols(T): return MASS_COLS_DR4 if T['tcol'] == 'solution_type' else MASS_COLS
def q_masses_by_id(T, idlist): return f"SELECT {', '.join(mass_cols(T))} FROM {T['masses']} WHERE source_id IN ({idlist})"
def q_rvs_by_id(T, idlist): return f"SELECT {', '.join(RVS_COLS)} FROM {T['source']} WHERE source_id IN ({idlist})"

# ------------------------------------------------------------------ steps
def check_schema(Gaia, T):
    need = {T['source']: SRC_COLS + RVS_COLS[1:] + ['parallax_over_error', 'random_index', 'parallax'], T['nss']: nss_cols(T)}
    if T['flags']: need[T['flags']] = ['source_id', 'non_single_star']
    else: need[T['source']] = need[T['source']] + ['non_single_star']
    if T['nbh']: need[T['nbh']] = ['source_id', 'dr3_source_id', 'angular_distance']
    need[T['masses']] = mass_cols(T)
    schema = T['source'].split('.')[0]; problems = []
    cols = run(Gaia, f"SELECT table_name, column_name, unit FROM TAP_SCHEMA.columns WHERE table_name LIKE '{schema}.%'", 'schema')
    cols['t'] = cols.table_name.astype(str).str.split('.').str[-1]
    short = {k.split('.')[1]: v for k, v in need.items()}
    PROV['schema_snapshot'] = {t: g[['column_name', 'unit']].astype(str).values.tolist() for t, g in cols.groupby('t') if t in short}
    for t, cs in short.items():
        have = set(cols.loc[cols.t == t, 'column_name'].astype(str))
        if not have: problems.append(f'table {schema}.{t} missing')
        elif [c for c in cs if c not in have]: problems.append(f'{schema}.{t}: missing columns {[c for c in cs if c not in have]}')
    if problems: raise FetchError('SCHEMA MISMATCH (stop; map names only as a logged deviation):\n' + '\n'.join(problems))

def dr3_ids_of_interest():
    """DR3 ids whose DR4 counterparts are needed: candidates (H11), sealed (H1/H2; ids only, no features), AstroSpectroSB1 (H12 exclusion)."""
    rd = lambda f: pd.read_csv(os.path.join(REAL, f), dtype={'source_id': str}, usecols=['source_id']).source_id.str.strip()
    ctrl = pd.read_csv(os.path.join(HERE, '..', 'results', 'h11_controls.csv'), dtype={'source_id': str}, usecols=['source_id']).source_id.str.strip()
    ids = pd.concat([rd('dr3_candidates.csv'), rd('excluded_sealed_ids.csv'), rd('dr3_astrospectro_all.csv'), ctrl]).drop_duplicates()
    return ids[ids.str.fullmatch(r'\d+')].tolist()

def rvs_epochs(Gaia, ids, out):
    types = Gaia.load_data(ids=ids[:3], retrieval_type='ALL', data_structure='DATAMODEL_STANDARD', verbose=False)
    names = sorted({k.split('-')[0] for k in types})
    rt = [n for n in names if 'RVS' in n.upper() and 'EPOCH' in n.upper() and 'SPECTRUM' not in n.upper()]
    PROV['datalink_types_seen'] = names
    if not rt: raise FetchError(f'no per-transit RVS DataLink product among {names}')
    frames = []
    for ch in chunks(ids, 5000):
        d = Gaia.load_data(ids=ch, retrieval_type=rt[0], data_structure='DATAMODEL_STANDARD', format='votable', verbose=False)
        for v in d.values():
            for tab in (v if isinstance(v, list) else [v]):
                frames.append(tab.to_table().to_pandas() if hasattr(tab, 'to_table') else tab.to_pandas())
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    save(df, f'{out}/rvs_epochs_raw.csv'); PROV['rvs_retrieval_type'] = rt[0]

def epoch_photometry(Gaia, ids, out):
    types = Gaia.load_data(ids=ids[:3], retrieval_type='ALL', data_structure='DATAMODEL_STANDARD', verbose=False)
    names = sorted({k.split('-')[0] for k in types}); rt = [n for n in names if n.upper() == 'EPOCH_PHOTOMETRY']
    PROV['datalink_types_seen_phot'] = names
    if not rt: raise FetchError(f'no EPOCH_PHOTOMETRY DataLink product among {names}')
    frames = []
    for ch in chunks(ids, 5000):
        try: d = Gaia.load_data(ids=ch, retrieval_type=rt[0], data_structure='DATAMODEL_GAIA', format='csv', verbose=False)
        except Exception: d = Gaia.load_data(ids=ch, retrieval_type=rt[0], data_structure='DATAMODEL_STANDARD', format='votable', verbose=False)
        for v in d.values():
            for tab in (v if isinstance(v, list) else [v]):
                frames.append(tab.to_table().to_pandas() if hasattr(tab, 'to_table') else tab.to_pandas())
    save(pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(), f'{out}/epoch_photometry_raw.csv')

def fetch_all(Gaia, T, out, skip_rvs=False):
    check_schema(Gaia, T)
    ep = run(Gaia, f"SELECT TOP 1 ref_epoch FROM {T['source']}", 'ref_epoch'); PROV['ref_epoch'] = float(ep.ref_epoch.iloc[0])
    if abs(PROV['ref_epoch'] - T['ref_epoch']) > 1e-6: raise FetchError(f"ref_epoch {PROV['ref_epoch']} != expected {T['ref_epoch']}")
    PROV['solution_types'] = run(Gaia, f"SELECT {T['tcol']}, COUNT(*) AS n FROM {T['nss']} GROUP BY {T['tcol']}", 'types').values.tolist()
    C = run(Gaia, q_candidates(T), 'candidates (frozen selection)'); save(C, f'{out}/candidates.csv')
    save(run(Gaia, q_field(T), 'field CMD (frozen criteria)'), f'{out}/field.csv')
    if T['nbh']:                                              # DR4: DR3 -> DR4 id map, then the H11 orbits of the counterparts
        N = run_in(Gaia, dr3_ids_of_interest(), lambda s: q_nbh(T, s), 'dr3_neighbourhood'); save(N, f'{out}/dr3_neighbourhood_raw.csv')
        cand3 = set(pd.read_csv(os.path.join(REAL, 'dr3_candidates.csv'), dtype={'source_id': str}).source_id.str.strip()) | \
                set(pd.read_csv(os.path.join(HERE, '..', 'results', 'h11_controls.csv'), dtype={'source_id': str}).source_id.str.strip())
        dr4_ids = N.loc[N.dr3_source_id.astype(str).isin(cand3) & (N.angular_distance.astype(float) <= 1000.0), 'source_id'].astype('int64').unique()
    else:                                                     # DR3 test: ids are unchanged
        dr4_ids = pd.concat([pd.read_csv(f, dtype={'source_id': str}).source_id.str.strip() for f in
                             (os.path.join(REAL, 'dr3_candidates.csv'), os.path.join(HERE, '..', 'results', 'h11_controls.csv'))]).astype('int64').unique()
    save(run_in(Gaia, dr4_ids, lambda s: q_orbits_by_id(T, s), 'H11 orbits of DR3-candidate counterparts'), f'{out}/h11_orbits.csv')
    CO = run(Gaia, q_combined(T), 'combined orbits (D3)'); save(CO, f'{out}/combined_orbits.csv')
    mids = pd.concat([C.source_id, CO.source_id]).astype('int64').unique()     # archive m1 (registered: 'DR4 equivalent' of binary_masses)
    save(run_in(Gaia, mids, lambda s: q_masses_by_id(T, s), 'primary masses (nss_masses)'), f'{out}/nss_masses.csv')
    save(run(Gaia, q_field_vbroad(T), 'field vbroad (D2)'), f'{out}/field_vbroad.csv')
    rv = run_in(Gaia, C.source_id.astype('int64').unique(), lambda s: q_rvs_by_id(T, s), 'candidate RVS means'); save(rv, f'{out}/rvs_mean.csv')
    if not skip_rvs:
        rvs_epochs(Gaia, rv.loc[rv.grvs_mag <= 14, 'source_id'].astype('int64').unique().tolist(), out)
        try: epoch_photometry(Gaia, C.source_id.astype('int64').unique().tolist(), out)        # H17 is secondary
        except Exception as e: PROV['epoch_photometry'] = f'NOT FETCHED: {type(e).__name__}: {e}'

def main(argv, Gaia=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--release', required=True, choices=list(TABLES)); ap.add_argument('--out')
    ap.add_argument('--user'); ap.add_argument('--control-group', action='store_true'); ap.add_argument('--skip-rvs', action='store_true')
    ap.add_argument('--print-queries', action='store_true')
    a = ap.parse_args(argv); T = TABLES[a.release]
    if a.print_queries:
        for n, q in [('candidates', q_candidates(T)), ('field', q_field(T)), ('combined', q_combined(T)), ('field_vbroad', q_field_vbroad(T)),
                     ('neighbourhood (chunk)', q_nbh(T, '<ids>') if T['nbh'] else '-'), ('orbits by id', q_orbits_by_id(T, '<ids>')),
                     ('rvs by id', q_rvs_by_id(T, '<ids>'))]:
            print(f'-- {n}\n{q}\n')
        return
    if not a.out: ap.error('--out is required')
    os.makedirs(a.out, exist_ok=True)
    if Gaia is None:
        import astroquery; from astroquery.gaia import Gaia
        PROV['astroquery_version'] = astroquery.__version__
        if a.user: Gaia.login(user=a.user, password=getpass.getpass('Gaia archive password: '))
        else: print('WARNING: anonymous access (row and DataLink limits): register an account for DR4 day')
        Gaia.ROW_LIMIT = -1
    PROV['release'] = a.release
    try:
        if a.control_group:
            q = (f"SELECT {', '.join('o.'+c for c in NSS_COLS)}, {', '.join('g.'+c for c in SRC_COLS[1:])} FROM {T['nss']} AS o "
                 f"JOIN {T['source']} AS g USING (source_id) WHERE o.nss_solution_type IN ('Orbital', 'AstroSpectroSB1') "
                 f"AND o.parallax/o.parallax_error > 10 AND o.parallax > 2")
            save(run(Gaia, q, 'H11 control pool'), f'{a.out}/dr3_orbits_for_controls.csv')
        else:
            fetch_all(Gaia, T, a.out, a.skip_rvs)
        status = 'OK'
    except Exception as e:
        status = f'STOPPED: {type(e).__name__}: {e}'
    PROV['status'] = status; PROV['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(PROV, open(f'{a.out}/provenance.json', 'w'), indent=1, default=str); print(status)
    return status

if __name__ == '__main__':
    main(sys.argv[1:])
