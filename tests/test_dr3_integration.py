"""End-to-end test of dr3_study.main() on SYNTHETIC files with the exact real-data schema (no real data involved).
Planted truth: 'impostor' rows are over-luminous; some are listed in the synthetic SB2 tables. Checks that the whole
chain runs, sealed ids are dropped first, one row per source is kept, and the planted signal gives AUC > 0.5."""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr3_study as S

def _ti(a0, inc, om, Om):
    i, w, W = np.radians(inc), np.radians(om), np.radians(Om)
    return (a0*(np.cos(w)*np.cos(W)-np.sin(w)*np.sin(W)*np.cos(i)), a0*(np.cos(w)*np.sin(W)+np.sin(w)*np.cos(W)*np.cos(i)),
            -a0*(np.sin(w)*np.cos(W)+np.cos(w)*np.sin(W)*np.cos(i)), -a0*(np.sin(w)*np.sin(W)-np.cos(w)*np.cos(W)*np.cos(i)))

def test_dr3_study_end_to_end(tmp_path):
    rng = np.random.default_rng(7); n = 600
    imp = rng.random(n) < 0.3
    plx = rng.uniform(5, 30, n); P = rng.uniform(200, 1500, n); m1 = rng.uniform(0.4, 1.0, n)
    a_rel = (m1*(P/365.25)**2)**(1/3); m2 = rng.uniform(5, 60, n)*9.546e-4
    a0 = a_rel*m2/m1*plx
    A, B, F, G = _ti(a0, rng.uniform(10, 170, n), rng.uniform(0, 360, n), rng.uniform(0, 360, n))
    MG_ms = np.interp(m1, [0.4, 1.0], [9.7, 4.6])[::1]
    MG = MG_ms + np.where(imp, -0.7, 0.0) + rng.normal(0, 0.3, n)
    bp_rp = 0.5 + 0.3*(MG_ms-3.0)
    sid = np.arange(10**15, 10**15+n)
    cand = pd.DataFrame(dict(source_id=sid, ra=rng.uniform(0, 360, n), dec=rng.uniform(-60, 60, n), pmra=rng.normal(0, 50, n), pmdec=rng.normal(0, 50, n),
                             phot_g_mean_mag=MG + 5*np.log10(1000/plx/10), bp_rp=bp_rp, ruwe=rng.uniform(1, 3, n), nss_solution_type='Orbital',
                             period=P, period_error=0.02*P, eccentricity=rng.uniform(0, 0.6, n), eccentricity_error=0.05, t_periastron=rng.uniform(-500, 500, n),
                             a_thiele_innes=A, b_thiele_innes=B, f_thiele_innes=F, g_thiele_innes=G,
                             a_thiele_innes_error=0.05*a0, b_thiele_innes_error=0.05*a0, f_thiele_innes_error=0.05*a0, g_thiele_innes_error=0.05*a0,
                             parallax=plx, parallax_error=0.02*plx, significance=rng.uniform(5, 50, n), m1=m1, m1_lower=m1*0.9, m1_upper=m1*1.1,
                             dr2_source_id=sid+7, dr2_angular_distance=rng.uniform(0, 50, n)))
    dup = cand.iloc[:5].copy(); dup['nss_solution_type'] = 'OrbitalAlternative'; cand = pd.concat([cand, dup])   # duplicates
    sealed = sid[-10:]
    nf = 4000; c = rng.uniform(0.5, 3.5, nf); MGf = 3 + (c-0.5)*10/3 + rng.normal(0, 0.3, nf)
    field = pd.DataFrame(dict(phot_g_mean_mag=MGf + 5*np.log10(50/10), bp_rp=c, parallax=20.0))
    lam_obs = rng.random(n) < 0.5
    lam_sb2 = sid[imp & lam_obs & (rng.random(n) < 0.6)]
    d = tmp_path; (d/'realdata').mkdir(); (d/'results').mkdir(); R = str(d/'realdata')+'/'; O = str(d/'results')+'/'
    cand.to_csv(R+'dr3_candidates.csv', index=False); field.to_csv(R+'dr3_field.csv', index=False)
    pd.DataFrame(dict(gaia_dr3_source_id=lam_sb2)).to_csv(R+'sb2_lamost.csv', index=False)
    pd.DataFrame(dict(gaia_dr2_source_id=[])).to_csv(R+'sb2_galah.csv', index=False)
    pd.DataFrame(dict(ID=[], ra=[], dec=[], SBn=[])).to_csv(R+'sb2_apogee.csv', index=False)
    pd.DataFrame(dict(gaia_dr2_source_id=(sid+7)[lam_obs], n_epochs=3)).to_csv(R+'lamost_cov.csv', index=False)
    pd.DataFrame(dict(source_id=sealed)).to_csv(R+'excluded_sealed_ids.csv', index=False)
    res = S.main(real=R, out=O)
    assert res['qa']['n_unique_sources'] == n
    assert res['qa']['n_sealed_dropped'] == 10
    p1 = res['P1_LAMOST_population']
    assert p1['n_pos'] >= 10 and p1['auc']['GAIA-FP'] > 0.6
    assert os.path.exists(O+'dr3_study.json')
