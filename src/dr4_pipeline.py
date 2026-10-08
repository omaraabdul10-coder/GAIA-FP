"""
dr4_pipeline.py — GAIA-FP "day-1" pipeline for Gaia DR4 (released 2 Dec 2026).

    python dr4_pipeline.py fetch   --out dr4_raw/        # ADQL queries against the Gaia archive (run on release day)
    python dr4_pipeline.py score   --raw dr4_raw/ --out catalogue/
    python dr4_pipeline.py selftest                       # end-to-end test on a mock DR4-like input (no network)

Layers
  1. ADAPTER   : DR4 table / column names live ONLY in SCHEMA below. They follow the DR3 data model and must be
                 checked against the DR4 data-model documentation on release day (marked CHECK-ON-RELEASE).
  2. SELECTION : pre-registered candidate rule (select_candidates) — frozen before release.
  3. FEATURES  : Thiele–Innes -> (a0, sigma_a0, P, sigma_P, e, i, omega, T0); photometric mass; CMD excess dM_G
                 relative to a main-sequence ridge measured from DR4 field stars (fit_ms_ridge), with its scatter.
  4. RVS       : per-transit line widths -> phase-locked statistic z (rvs_z) using the astrometric orbit only.
  5. SCORING   : lik.llr_t (joint a0|CMD + physics RVS), label-free EM prior, three-way verdict (t = 0.15),
                 best follow-up by EIG per cost.
Outputs: catalogue/gaiafp_dr4_catalogue.csv (+ summary.json). Labelled systems are NOT read here; the blind
evaluation is a separate step (blind_eval.py) after the catalogue is frozen and hashed.
"""
import sys, json, argparse, hashlib, numpy as np, pandas as pd
from scipy.special import expit

MJ = 9.546e-4
T_ABSTAIN = 0.15            # pre-specified (EXPERIMENT_TOURNAMENT.md, X2)
SELECTION = dict(max_m2_MJ=80.0, min_parallax_over_error=10.0, max_dist_pc=500.0,
                 solution_types=('Orbital', 'AstroSpectroSB1', 'OrbitalTargetedSearch', 'OrbitalTargetedSearchValidated'))

# ------------------------------------------------------------------ 1. adapter (CHECK-ON-RELEASE)
SCHEMA = dict(
    release='gaiadr4',
    orbit_table='gaiadr4.nss_two_body_orbit',
    source_table='gaiadr4.gaia_source',
    orbit_cols=['source_id', 'nss_solution_type', 'period', 'period_error', 'eccentricity', 'eccentricity_error',
                't_periastron', 'a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes',
                'a_thiele_innes_error', 'b_thiele_innes_error', 'f_thiele_innes_error', 'g_thiele_innes_error',
                'parallax', 'parallax_error', 'significance'],
    source_cols=['source_id', 'phot_g_mean_mag', 'bp_rp', 'ruwe', 'grvs_mag'],
    # epoch RVS line widths: DR4 provides per-transit RVS data via DataLink; product name to be confirmed
    rvs_epoch_product='EPOCH_RVS',  # CHECK-ON-RELEASE
)

def adql_candidates():
    s = SCHEMA
    oc = ', '.join('o.'+c for c in s['orbit_cols']); sc = ', '.join('g.'+c for c in s['source_cols'][1:])
    types = ', '.join(f"'{t}'" for t in SELECTION['solution_types'])
    return (f"SELECT {oc}, {sc} FROM {s['orbit_table']} AS o JOIN {s['source_table']} AS g USING (source_id) "
            f"WHERE o.nss_solution_type IN ({types}) AND o.parallax/o.parallax_error > {SELECTION['min_parallax_over_error']} "
            f"AND o.parallax > {1000.0/SELECTION['max_dist_pc']}")

def adql_field_stars(n=200000):
    s = SCHEMA
    return (f"SELECT TOP {n} source_id, phot_g_mean_mag, bp_rp, parallax FROM {s['source_table']} "
            f"WHERE parallax_over_error > 20 AND ruwe < 1.2 AND parallax > 2 AND non_single_star = 0 "
            f"AND random_index < 5000000")

def fetch(out):
    """Run on release day. Uses astroquery (pip install astroquery)."""
    from astroquery.gaia import Gaia
    import os; os.makedirs(out, exist_ok=True)
    for name, q in [('candidates', adql_candidates()), ('field', adql_field_stars())]:
        job = Gaia.launch_job_async(q); job.get_results().to_pandas().to_csv(f'{out}/{name}.csv', index=False)
    print('Fetched. Epoch RVS widths: download per candidate with Gaia.load_data(ids, retrieval_type=SCHEMA["rvs_epoch_product"])')

# ------------------------------------------------------------------ 3. features
# Approximate main-sequence absolute-G -> mass anchors (dwarfs). APPROXIMATE: replace with PARSEC/MIST isochrone before freeze.
_MG = np.array([2.5, 3.5, 4.4, 5.2, 6.0, 6.9, 7.8, 8.7, 9.7, 10.7, 11.7, 12.7, 13.7])
_M = np.array([1.45, 1.25, 1.05, 0.92, 0.82, 0.72, 0.62, 0.53, 0.43, 0.33, 0.24, 0.17, 0.12])
def mass_from_MG(MG): return np.interp(MG, _MG, _M)

def campbell(A, B, F, G):
    u = (A*A+B*B+F*F+G*G)/2; v = A*G-B*F; a0 = np.sqrt(u+np.sqrt(np.maximum((u+v)*(u-v), 0)))
    w_p_W = np.arctan2(B-F, A+G); w_m_W = np.arctan2(-B-F, A-G)
    om = (w_p_W + w_m_W)/2; Om = (w_p_W - w_m_W)/2
    inc = 2*np.arctan(np.sqrt(np.abs(((A-G)**2+(B+F)**2)/((A+G)**2+(B-F)**2))))
    return a0, np.degrees(inc), np.degrees(om) % 360, np.degrees(Om) % 360

def fit_ms_ridge(field, nbins=40):
    """Main-sequence ridge M_G(BP-RP) and its scatter per colour bin, from DR4 field stars (pre-registered sigma)."""
    MG = field['phot_g_mean_mag'] + 5*np.log10(field['parallax']/100.0); c = field['bp_rp']
    ok = np.isfinite(MG) & np.isfinite(c) & (c > 0.3) & (c < 4.0)
    edges = np.quantile(c[ok], np.linspace(0, 1, nbins+1)); rid, sig, mid = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = ok & (c >= a) & (c < b); x = MG[m]
        med = np.median(x); mad = 1.4826*np.median(np.abs(x-med))
        core = x[np.abs(x-med) < 3*mad]                 # clip unresolved binaries / giants
        rid.append(np.median(core)); sig.append(1.4826*np.median(np.abs(core-np.median(core)))); mid.append(np.median(c[m]))
    return dict(color=np.array(mid), ridge=np.array(rid), sigma=np.array(sig))

def features(cand, ridge):
    A, B, F, G = (cand[k].values for k in ('a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes'))
    a0, inc, om, _ = campbell(A, B, F, G)
    a0err = np.sqrt(np.mean([cand[k+'_thiele_innes_error'].values**2 for k in 'abfg'], axis=0))
    plx = cand['parallax'].values; d = 1000/plx
    MG = cand['phot_g_mean_mag'].values + 5*np.log10(plx/100.0); col = cand['bp_rp'].values
    ms = np.interp(col, ridge['color'], ridge['ridge']); sig = np.interp(col, ridge['color'], ridge['sigma'])
    M = mass_from_MG(MG); P = cand['period'].values
    a_rel = (M*(P/365.25)**2)**(1/3)                     # AU (companion mass negligible)
    m2 = a0/plx/a_rel*M/MJ                               # dark-companion mass in MJ (first order)
    return pd.DataFrame(dict(source_id=cand['source_id'].values, P=P, sigP=np.clip(cand['period_error'].values/P, 1e-4, .5),
                             e=cand['eccentricity'].values, T0=cand['t_periastron'].values, inc=inc, om=om, a0=a0, a0err=a0err,
                             d=d, G=cand['phot_g_mean_mag'].values, bp_rp=col, MG=MG, dm=MG-ms, sig_cmd=sig, M=M, mfit=m2,
                             ruwe=cand['ruwe'].values))

def select_candidates(X):
    return X[(X['mfit'] > 0) & (X['mfit'] < SELECTION['max_m2_MJ'])].reset_index(drop=True)

# ------------------------------------------------------------------ 4. RVS
def rvs_z(t, width, P, e, T0, om_deg):
    from rvs_phase_test import true_anomaly
    if len(t) < 6: return np.nan, len(t)
    nu = true_anomaly(np.asarray(t), P, e, T0); w = np.radians(om_deg)
    tmpl = (np.cos(nu+w) + e*np.cos(w))**2; s2 = np.asarray(width)**2
    if np.std(tmpl) == 0 or np.std(s2) == 0: return 0.0, len(t)
    r = np.corrcoef(tmpl, s2)[0, 1]; return float(np.arctanh(np.clip(r, -.999, .999))*np.sqrt(len(t)-3)), len(t)

# ------------------------------------------------------------------ 5. scoring
def score(X, rvs=None, seed=0):
    import lik, followup
    from hier_em import em, phi
    X = X.copy(); X['z'] = np.nan; X['nep'] = 0; X['srv'] = 5.0; X['span'] = 2000.0
    if rvs is not None:
        for i, r in X.iterrows():
            g = rvs.get(r['source_id'])
            if g is not None:
                z, n = rvs_z(g['t'], g['width'], r['P'], r['e'], r['T0'], r['om'])
                X.at[i, 'z'] = z; X.at[i, 'nep'] = n; X.at[i, 'srv'] = float(np.median(g['width_err']))
    # per-object CMD scatter: llr_t takes one sigma; group by rounded sigma to respect colour dependence
    L = np.zeros(len(X)); Lc = np.zeros(len(X))
    for s, idx in X.groupby(X['sig_cmd'].round(2)).groups.items():
        sub = X.loc[idx]; lt, r = lik.llr_t(sub, float(s), seed); L[idx] = lt; Lc[idx] = lt - r
    p, pi = em(L, phi(X))
    X['llr_cmd'] = Lc; X['log_lr'] = L; X['prior_pi'] = pi; X['P_impostor'] = p
    X['verdict'] = np.where(p <= T_ABSTAIN, 'likely_substellar', np.where(p >= 1-T_ABSTAIN, 'likely_impostor', 'ambiguous_followup_needed'))
    rng = np.random.default_rng(seed); best = []
    for i, r in X.iterrows():
        if r['verdict'] != 'ambiguous_followup_needed': best.append(''); continue
        e = followup.eig(r, p[i], float(r['sig_cmd']), rng); k = max(e, key=lambda kk: e[kk][0]/e[kk][1])
        best.append(f"{k} (EIG/cost {e[k][0]/e[k][1]:.2f} bits)")
    X['best_followup'] = best
    return X

def write(X, out):
    import os; os.makedirs(out, exist_ok=True)
    cols = ['source_id', 'G', 'bp_rp', 'd', 'P', 'e', 'a0', 'mfit', 'dm', 'sig_cmd', 'z', 'nep', 'P_impostor', 'verdict', 'best_followup']
    X[cols].to_csv(f'{out}/gaiafp_dr4_catalogue.csv', index=False)
    summ = dict(n=len(X), verdicts=X['verdict'].value_counts().to_dict(), contamination_bracket=[float(np.mean(X['P_impostor']))],
                sha256=hashlib.sha256(open(f'{out}/gaiafp_dr4_catalogue.csv', 'rb').read()).hexdigest())
    json.dump(summ, open(f'{out}/summary.json', 'w'), indent=1); print(json.dumps(summ, indent=1))

# ------------------------------------------------------------------ self-test on mock input
def selftest():
    """Build a DR4-like candidate table from the Lammers & Winn mocks (via sim.py), run the full chain, check sanity."""
    import sim
    from blind_eval import roc_auc
    from benchmark import a0_mas
    pl, im = sim.load('DR4', 1500, seed=5); X = sim.build(pl, im.sample(400, random_state=5), seed=9)
    # emulate DR4 columns from simulated quantities
    rng = np.random.default_rng(1)
    a0 = X['a0'].values; inc = np.radians(X['inc'].values); om = np.radians(X['om'].values); Om = rng.uniform(0, 2*np.pi, len(X))
    A = a0*(np.cos(om)*np.cos(Om)-np.sin(om)*np.sin(Om)*np.cos(inc)); B = a0*(np.cos(om)*np.sin(Om)+np.sin(om)*np.cos(Om)*np.cos(inc))
    F = -a0*(np.sin(om)*np.cos(Om)+np.cos(om)*np.sin(Om)*np.cos(inc)); G_ = -a0*(np.sin(om)*np.sin(Om)-np.cos(om)*np.cos(Om)*np.cos(inc))
    err = X['a0err'].values
    MGtrue = np.interp(X['M'].values, _M[::-1], _MG[::-1])
    cand = pd.DataFrame(dict(source_id=np.arange(len(X)), nss_solution_type='Orbital', period=X['P'], period_error=X['sigP']*X['P'],
                             eccentricity=X['e'], eccentricity_error=0.05, t_periastron=X['T0'],
                             a_thiele_innes=A, b_thiele_innes=B, f_thiele_innes=F, g_thiele_innes=G_,
                             a_thiele_innes_error=err, b_thiele_innes_error=err, f_thiele_innes_error=err, g_thiele_innes_error=err,
                             parallax=1000/X['d'], parallax_error=0.01*1000/X['d'], significance=20.0,
                             phot_g_mean_mag=MGtrue + X['dm'].values + 5*np.log10(X['d'].values/10), bp_rp=0.5 + 0.3*(MGtrue-3.0), ruwe=1.3, grvs_mag=np.nan))
    nf = 20000; cf = rng.uniform(0.5, 3.5, nf); MGf = np.interp(cf, [0.5, 3.5], [3.0, 13.0]) + rng.normal(0, 0.30, nf)
    field = pd.DataFrame(dict(phot_g_mean_mag=MGf + 5*np.log10(50/10), bp_rp=cf, parallax=20.0))
    ridge = fit_ms_ridge(field)
    Xd = select_candidates(features(cand, ridge))
    # put back the simulated z / epochs for the RVS-bright ones (stand-in for epoch widths)
    Xd = Xd.merge(X[['z']].reset_index().rename(columns={'index': 'source_id'}), on='source_id', how='left')
    Xs = score(Xd.drop(columns=['z']), rvs=None)
    y = X['y'].values[Xs['source_id'].values]
    print('selftest: n =', len(Xs), '| AUC (CMD+a0 only, recovered from DR4-like columns) =', round(float(roc_auc(Xs['P_impostor'].values, y)), 3),
          '| median |a0 recovered - true| =', round(float(np.median(np.abs(Xs['a0'].values - X['a0'].values[Xs['source_id'].values]))), 5))
    print(Xs['verdict'].value_counts().to_dict())
    write(Xs, 'selftest_catalogue')

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--out', default='catalogue'); ap.add_argument('--raw', default='dr4_raw')
    a = ap.parse_args()
    if a.cmd == 'fetch': fetch(a.out)
    elif a.cmd == 'selftest': selftest()
    elif a.cmd == 'score':
        cand = pd.read_csv(f'{a.raw}/candidates.csv'); field = pd.read_csv(f'{a.raw}/field.csv')
        X = select_candidates(features(cand, fit_ms_ridge(field))); write(score(X), a.out)
