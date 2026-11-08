"""
fetch_realdata.py — downloads the PUBLIC real data for the pre-registered DR3 study (DR3_STUDY_PLAN.md) on any computer
with internet access. Pure Python + requests (pip install requests pandas). No account or credentials are needed.

    python tools/fetch_realdata.py            # writes realdata/*.csv and realdata/PROVENANCE.md

Queries are exactly those in tools/ingest_queries.md. Sealed objects (realdata/excluded_sealed_ids.csv) are removed
from the candidate table before it is written, so no Gaia feature of a sealed object is ever stored.
"""
import io, os, sys, time, datetime, requests, pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'realdata')
GAIA = 'https://gea.esac.esa.int/tap-server/tap'
VIZ = 'https://tapvizier.cds.unistra.fr/TAPVizieR/tap'

def _m2_expr():
    A, B, F, G = 'o.a_thiele_innes', 'o.b_thiele_innes', 'o.f_thiele_innes', 'o.g_thiele_innes'
    u = f'(({A}*{A}+{B}*{B}+{F}*{F}+{G}*{G})/2.0)'; v = f'({A}*{G}-{B}*{F})'
    a0 = f'SQRT({u}+SQRT(ABS({u}*{u}-{v}*{v})))'
    return f'(1047.6*b.m1*({a0}/o.parallax)/POWER(b.m1*POWER(o.period/365.25,2),1.0/3.0))'

Q_CAND = ("SELECT o.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.phot_g_mean_mag, g.bp_rp, g.ruwe, o.nss_solution_type, "
          "o.period, o.period_error, o.eccentricity, o.eccentricity_error, o.t_periastron, o.a_thiele_innes, o.b_thiele_innes, "
          "o.f_thiele_innes, o.g_thiele_innes, o.a_thiele_innes_error, o.b_thiele_innes_error, o.f_thiele_innes_error, "
          "o.g_thiele_innes_error, o.parallax, o.parallax_error, o.significance, b.m1, b.m1_lower, b.m1_upper, "
          "n.dr2_source_id, n.angular_distance AS dr2_angular_distance "
          "FROM gaiadr3.nss_two_body_orbit AS o JOIN gaiadr3.binary_masses AS b ON b.source_id=o.source_id "
          "JOIN gaiadr3.gaia_source AS g ON g.source_id=o.source_id "
          "LEFT JOIN gaiadr3.dr2_neighbourhood AS n ON n.dr3_source_id=o.source_id "
          f"WHERE o.a_thiele_innes IS NOT NULL AND o.parallax>0 AND b.m1>0 AND {_m2_expr()} < 80")
Q_FIELD = ("SELECT TOP 20000 phot_g_mean_mag, bp_rp, parallax FROM gaiadr3.gaia_source WHERE parallax_over_error > 20 "
           "AND ruwe < 1.2 AND non_single_star = 0 AND parallax > 5 AND random_index < 3000000")
Q_SB2 = {'sb2_lamost': 'SELECT GaiaDR3 AS gaia_dr3_source_id FROM "J/MNRAS/527/521/tableb1"',
         'sb2_galah': 'SELECT GaiaDR2 AS gaia_dr2_source_id FROM "J/A+A/638/A145/catalog"',
         'sb2_apogee': 'SELECT ID, RAJ2000 AS ra, DEJ2000 AS dec, SBn FROM "J/AJ/162/184/table1"'}

# Full LAMOST-MRS coverage table, matching realdata/PROVENANCE.md.
# Candidate-only IN-lists are insufficient for the registered positional fallback
# (they also produced an incompatible two-column file in earlier fetcher drafts).
Q_LAMOST_COV = (
    'SELECT Gaia AS gaia_dr2_source_id, COUNT(*) AS n_epochs, '
    'AVG(RAJ2000) AS ra, AVG(DEJ2000) AS dec '
    'FROM "J/ApJS/244/27/lamostMRS" WHERE Gaia IS NOT NULL GROUP BY Gaia'
)

def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def sync(base, q, timeout=300):
    r = requests.post(base+'/sync', data=dict(REQUEST='doQuery', LANG='ADQL', FORMAT='csv', QUERY=q), timeout=timeout)
    r.raise_for_status(); return pd.read_csv(io.StringIO(r.text), dtype={'source_id': 'Int64', 'gaia_dr3_source_id': 'Int64', 'gaia_dr2_source_id': 'Int64', 'dr2_source_id': 'Int64'})

def async_(base, q, poll=10, max_wait=3600):
    r = requests.post(base+'/async', data=dict(REQUEST='doQuery', LANG='ADQL', FORMAT='csv', PHASE='RUN', QUERY=q), timeout=120)
    r.raise_for_status(); job = r.url; t0 = time.time()
    while time.time()-t0 < max_wait:
        ph = requests.get(job+'/phase', timeout=60).text.strip().upper()
        if ph == 'COMPLETED': break
        if ph in ('ERROR', 'ABORTED'): raise RuntimeError(f'{job}: {ph}')
        time.sleep(poll)
    else:
        raise TimeoutError(f'{job}: async TAP job did not complete within {max_wait} seconds')
    res = requests.get(job+'/results/result', timeout=300); res.raise_for_status()
    return pd.read_csv(io.StringIO(res.text), dtype={'source_id': 'Int64', 'dr2_source_id': 'Int64'}), job


def normalise_lamost_coverage(df):
    """Validate the full positional LAMOST-MRS coverage table.

    RA/Dec are required because the historical Gaia DR2 identifier column in
    this VizieR catalogue is not precise enough for exact integer matching.
    The real-data study therefore matches positions, testing both catalogue
    and propagated Gaia epochs and marking ambiguous matches as uncovered.
    """
    import numpy as np
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError('LAMOST-MRS coverage query returned no rows')
    aliases = {str(c).strip().lower(): c for c in df.columns}
    # VizieR returns the native catalogue column names unless aliases are
    # explicitly applied in its TAP endpoint. Accept both native and aliases.
    for native, alias in {'gaia': 'gaia_dr2_source_id', 'raj2000': 'ra', 'dej2000': 'dec'}.items():
        if native in aliases and alias not in aliases:
            aliases[alias] = aliases[native]
    required = {'gaia_dr2_source_id', 'n_epochs', 'ra', 'dec'}
    missing = sorted(required - set(aliases))
    if missing:
        raise ValueError(f'LAMOST-MRS result missing required columns: {missing}; got {list(df.columns)}')
    out = df[[aliases[k] for k in ('gaia_dr2_source_id','n_epochs','ra','dec')]].copy()
    out.columns = ['gaia_dr2_source_id','n_epochs','ra','dec']
    for col in ('n_epochs','ra','dec'):
        out[col] = pd.to_numeric(out[col], errors='coerce')
    if out[['n_epochs','ra','dec']].isna().any().any():
        raise ValueError('LAMOST-MRS coverage contains null/non-numeric epochs or coordinates')
    if (out['n_epochs'] < 1).any() or not np.allclose(out['n_epochs'], np.round(out['n_epochs'])):
        raise ValueError('LAMOST-MRS n_epochs must be positive integer counts')
    if ((out['ra'] < 0) | (out['ra'] >= 360)).any():
        raise ValueError('LAMOST-MRS RA values must be in [0, 360) degrees')
    if ((out['dec'] < -90) | (out['dec'] > 90)).any():
        raise ValueError('LAMOST-MRS Dec values must be in [-90, 90] degrees')
    # Gaia DR2 identifiers in this VizieR column can be floating-point rounded.
    # Keep the returned lexical values for provenance, but never use them as the
    # primary match key when coordinates are available.
    out['gaia_dr2_source_id'] = out['gaia_dr2_source_id'].astype('string')
    if out[['ra','dec']].duplicated().any():
        # Duplicate sky positions may be legitimate; positional_match() handles
        # them as ambiguous, so retain them and make no false uniqueness claim.
        pass
    out['n_epochs'] = out['n_epochs'].astype('int64')
    return out


def fetch_lamost_coverage():
    """Retrieve full 2019 LAMOST-MRS coverage catalogue asynchronously.

    The complete table is required by the pre-existing positional matching
    procedure documented in realdata/PROVENANCE.md (292,534 source rows).
    """
    raw, job = async_(VIZ, Q_LAMOST_COV, max_wait=3600)
    return normalise_lamost_coverage(raw), job

def main():
    os.makedirs(OUT, exist_ok=True); log = []
    now = lambda: datetime.datetime.utcnow().isoformat(timespec='seconds')+'Z'
    sealed = set(pd.read_csv(os.path.join(OUT, 'excluded_sealed_ids.csv'))['source_id'].astype('int64'))
    print('Gaia candidates (async, a few minutes)...'); cand, job = async_(GAIA, Q_CAND)
    n_raw = len(cand); cand = cand[~cand['source_id'].astype('int64').isin(sealed)]
    cand_path = os.path.join(OUT, 'dr3_candidates.csv')
    cand.to_csv(cand_path, index=False)
    log.append(f'| dr3_candidates.csv | Gaia Archive TAP async {job} | {now()} | {n_raw} rows returned, {n_raw-len(cand)} sealed rows dropped before saving, {len(cand)} kept; SHA-256 `{sha256_file(cand_path)}` |')
    print('Gaia field stars...'); field = sync(GAIA, Q_FIELD)
    field_path = os.path.join(OUT, 'dr3_field.csv'); field.to_csv(field_path, index=False)
    log.append(f'| dr3_field.csv | Gaia Archive TAP sync | {now()} | {len(field)} rows; SHA-256 `{sha256_file(field_path)}` |')
    for name, q in Q_SB2.items():
        print(name, '...'); d = sync(VIZ, q); data_path = os.path.join(OUT, name+'.csv'); d.to_csv(data_path, index=False)
        log.append(f'| {name}.csv | VizieR TAP: `{q}` | {now()} | {len(d)} rows (full catalogue); SHA-256 `{sha256_file(data_path)}` |')
    print('Full LAMOST-MRS positional coverage catalogue (async, potentially large)...')
    cov, cov_job = fetch_lamost_coverage()
    cov_path = os.path.join(OUT, 'lamost_cov.csv'); cov.to_csv(cov_path, index=False)
    log.append(f'| lamost_cov.csv | VizieR TAP J/ApJS/244/27/lamostMRS; full GROUP BY Gaia with COUNT(*), AVG(RAJ2000), AVG(DEJ2000); async job {cov_job} | {now()} | {len(cov)} rows; positional matching enabled; SHA-256 `{sha256_file(cov_path)}` |')
    with open(os.path.join(OUT, 'PROVENANCE.md'), 'w') as f:
        f.write('# Provenance of real data (all public)\n\n| File | Source / query | Retrieved (UTC) | Notes |\n|---|---|---|---|\n' + '\n'.join(log) + '\n')
    print('Done. Files in realdata/. Upload them to GitHub (realdata/) and re-run the analysis.')

if __name__ == '__main__':
    main()
