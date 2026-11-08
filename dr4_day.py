"""
dr4_day.py: the DR4-day orchestrator (amendment v0.6, "Order of work on DR4 day"). Every step is timed and logged; the first
error stops the run with a clear message (no step continues on a partial result).

    python dr4_day.py dryrun  [--out DIR]   # full chain on FAKE DR4-like tables built from DR3 + synthetic RVS epochs and
                                             # SYNTHETIC labels (the sealed file is never opened); writes DIR/dryrun_log.json
    python dr4_fetch.py --release gaiadr4 --out RAW --user <login>                 # network (separate script)
    python dr4_day.py prepare --raw RAW --std STD                                  # archive names -> standard inputs
    python dr4_day.py run --std STD --labels labels_v2_PRIVATE.json --out OUT      # score, hash, H11, H8, H12, unblind, H15, H17

The dry run and the DR4 run use the SAME function (run_chain), so the dry run tests the real chain (8 Nov 2026).
"""
import argparse, json, os, sys, time, traceback, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
LOG = []

def step(name, fn):
    t0 = time.time()
    try:
        r = fn(); LOG.append(dict(step=name, status='OK', seconds=round(time.time() - t0, 1), info=r)); return r
    except BaseException as e:
        LOG.append(dict(step=name, status='FAILED', seconds=round(time.time() - t0, 1), error=f'{type(e).__name__}: {e}',
                        trace=traceback.format_exc()[-1500:]))
        raise

def build_fake(out, seed=3):
    """Fake DR4-like inputs. Ids of 5 % of sources are changed (as DR4 may do); 10 % of orbits vanish; RVS epochs in Format A
    with ns times since 2010 for 60 % of candidates; SYNTHETIC labels with the registered counts 39/26/10/1."""
    rng = np.random.default_rng(seed); R = os.path.join(HERE, '..', 'realdata')
    cand = pd.read_csv(os.path.join(R, 'dr3_candidates.csv'), dtype={'source_id': str}).drop_duplicates('source_id')
    ids = cand.source_id.str.strip().values
    new = np.array([s[:-3] + f'{(int(s[-3:]) + 7) % 1000:03d}' if rng.random() < 0.05 else s for s in ids])
    idmap = pd.DataFrame(dict(dr3_source_id=ids, dr4_source_id=new, angular_distance_arcsec=rng.uniform(0, 0.2, len(ids))))
    c4 = cand.assign(source_id=new, t_periastron=cand.t_periastron - 547.875)          # J2016.0 -> J2017.5 zero point
    c4.to_csv(f'{out}/candidates.csv', index=False); idmap.to_csv(f'{out}/dr3_dr4_map.csv', index=False)
    rows = []
    for s in new[rng.random(len(new)) < 0.6]:
        n = rng.integers(5, 40); t = np.sort(rng.uniform(1700, 3600, n))*86400e9
        rows += [dict(source_id=s, rv_obs_time=x, vbroad=max(0.5, rng.normal(10, 1.5)), vbroad_error=1.5) for x in t]
    pd.DataFrame(rows).to_csv(f'{out}/rvs_epochs.csv', index=False)
    sel = rng.choice(len(ids), 76, replace=False)
    labs = ['impostor']*39 + ['substellar']*26 + ['unresolved']*10 + ['excluded_inspected']
    J = dict(version='FAKE-DRYRUN', created='dryrun', rules='synthetic', entries=[dict(source_id=ids[i], label=l, name='fake', confidence='high',
             ref='-', origin='-', evidence=None, notes=None, companion_mass_MJ=None) for i, l in zip(sel, labs)])
    json.dump(J, open(f'{out}/FAKE_labels.json', 'w'))
    return dict(n_candidates=len(c4), n_rvs_rows=len(rows), n_ids_changed=int((new != ids).sum()))

# ------------------------------------------------------------------ prepare: raw archive tables -> standard inputs
STD = dict(candidates='candidates.csv', field='field.csv', idmap='dr3_dr4_map.csv', rvs='rvs_epochs.csv', orbits='dr4_orbits.csv',
           combined='dr4_combined.csv', mech='dr4_mech_input.csv', field_vbroad='field_vbroad.csv', phot='epoch_photometry.csv',
           dpac='dpac_masses.csv')

def prepare(raw, std):
    """Convert dr4_fetch.py output (archive names) into the standard inputs of run(). DR4 tables go through dr4_release_map;
    DR3 test tables (fetched with --release gaiadr3) already have the internal names."""
    import dr4_release_map as RM
    os.makedirs(std, exist_ok=True); rd = lambda f: pd.read_csv(os.path.join(raw, f), dtype={'source_id': str, 'dr3_source_id': str})
    dr4 = lambda df: 'solution_type' in df.columns
    nss = lambda df: RM.nss(df) if dr4(df) else df
    C = nss(rd('candidates.csv')); R = rd('rvs_mean.csv')
    MS = None
    if os.path.exists(os.path.join(raw, 'nss_masses.csv')):   # one row per source (deterministic: first combination_method alphabetically)
        MS = rd('nss_masses.csv'); MS = MS[np.isfinite(MS.m1.astype(float))].sort_values(['source_id', 'combination_method']).drop_duplicates('source_id')
        C = C.drop(columns=[c for c in ('m1', 'm1_lower', 'm1_upper') if c in C]).merge(MS[['source_id', 'm1', 'm1_lower', 'm1_upper']], on='source_id', how='left')
    C = C.merge(R[[c for c in R.columns if c not in C.columns or c == 'source_id']], on='source_id', how='left')
    import dr4_pipeline as DP
    def fill_m1(X):                                           # archive m1 where published, else the registered photometric relation
        if 'm1' not in X: X['m1'] = np.nan
        miss = ~np.isfinite(X.m1.astype(float)); MG = X.phot_g_mean_mag.astype(float) + 5*np.log10(X.parallax.astype(float)/100)
        X.loc[miss, 'm1'] = DP.mass_from_MG(MG[miss].values); X['m1_source'] = np.where(miss, 'photometric', 'archive'); return X, int(miss.sum())
    C, n_fb = fill_m1(C)
    C.to_csv(f'{std}/{STD["candidates"]}', index=False)
    rd('field.csv').to_csv(f'{std}/{STD["field"]}', index=False); rd('field_vbroad.csv').to_csv(f'{std}/{STD["field_vbroad"]}', index=False)
    if os.path.exists(os.path.join(raw, 'dr3_neighbourhood_raw.csv')):
        M = RM.neighbourhood(rd('dr3_neighbourhood_raw.csv')).sort_values('angular_distance_arcsec').drop_duplicates('dr3_source_id')
    else:                                                       # DR3 test: identity map
        ids = pd.concat([pd.read_csv(os.path.join(HERE, '..', f), dtype={'source_id': str}).source_id.str.strip() for f in
                         ('realdata/dr3_candidates.csv', 'realdata/excluded_sealed_ids.csv', 'realdata/dr3_astrospectro_all.csv', 'results/h11_controls.csv')]).drop_duplicates()
        M = pd.DataFrame(dict(dr3_source_id=ids, dr4_source_id=ids, angular_distance_arcsec=0.0))
    M.to_csv(f'{std}/{STD["idmap"]}', index=False)
    O = nss(rd('h11_orbits.csv')); O.to_csv(f'{std}/{STD["orbits"]}', index=False)
    src = [c for c in ('source_id', 'phot_g_mean_mag', 'bp_rp', 'ruwe', 'grvs_mag', 'vbroad', 'vbroad_error', 'vbroad_nb_transits',
                       'parallax', 'm1', 'm1_lower', 'm1_upper', 'm1_source') if c in C and (c == 'source_id' or c not in O)]
    A = O[O.nss_solution_type == 'AstroSpectroSB1'].merge(C[src], on='source_id', how='left'); A.to_csv(f'{std}/{STD["combined"]}', index=False)
    CO = nss(rd('combined_orbits.csv'))
    if MS is not None: CO = CO.drop(columns=[c for c in ('m1', 'm1_lower', 'm1_upper') if c in CO]).merge(MS[['source_id', 'm1', 'm1_lower', 'm1_upper']], on='source_id', how='left')
    CO, n_fb_co = fill_m1(CO); CO.to_csv(f'{std}/{STD["mech"]}', index=False)
    if MS is not None:                                        # H20 comparators (v0.6 A35), fixed before unblinding
        keep = [c for c in ('source_id', 'fluxratio', 'exoplanet_candidate_hrd_proba', 'lowmass_candidate_hrd_proba') if c in MS]
        MS[keep].to_csv(f'{std}/{STD["dpac"]}', index=False)
    info = dict(n_candidates=len(C), n_m1_photometric_fallback=n_fb, n_m1_photometric_fallback_combined=n_fb_co, n_idmap=len(M), n_orbits=len(O), n_combined_candidates=len(A))
    if os.path.exists(os.path.join(raw, 'rvs_epochs_raw.csv')):
        E = RM.rvs_epochs(rd('rvs_epochs_raw.csv')); E.to_csv(f'{std}/{STD["rvs"]}', index=False); info['n_rvs_rows'] = len(E)
    if os.path.exists(os.path.join(raw, 'epoch_photometry_raw.csv')):
        P = RM.epoch_photometry(rd('epoch_photometry_raw.csv')); P.to_csv(f'{std}/{STD["phot"]}', index=False); info['n_phot_rows'] = len(P)
    return info

# ------------------------------------------------------------------ run: the same chain for the dry run and for DR4
def run_chain(d, out, labels, labels_sha, time_unit, ref_epoch, mech_idmap=None, expected=None, h7=None):
    """d: directory with the STD files. Order: score -> hash -> H11 -> H8 -> H12-H14(+H18/H19) -> unblind + weighted Holm ->
    H15 -> H17. The catalogue is hashed before any outcome is computed; evaluate() refuses a catalogue whose hash changed."""
    import dr4_run, dr4_adapters, dr4_evaluate, subprocess
    os.makedirs(out, exist_ok=True); P = lambda k: os.path.join(d, STD[k])
    def sub(args):
        r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True, text=True)
        if r.returncode != 0: raise RuntimeError(r.stderr[-800:])
        return 'rc=0'
    cand = pd.read_csv(P('candidates'), dtype={'source_id': str}); field = pd.read_csv(P('field'))
    rv = None
    if os.path.exists(P('rvs')):
        rv = step('RVS epochs -> standard (time unit, reference epoch)', lambda: dr4_adapters.standardise(pd.read_csv(P('rvs'), dtype={'source_id': str}), time_unit, ref_epoch))
        LOG[-1]['info'] = dict(n_sources=len(rv))
    Xs, info = step('score v3.2 primary + v3.1 registered + A6-off + A7', lambda: dr4_run.score(cand, field, rvs=rv, workers=os.cpu_count()))
    LOG[-1]['info'] = info
    h = step('write + hash catalogue (before any outcome)', lambda: dr4_run.write(Xs, info, f'{out}/gaiafp_dr4_catalogue.csv'))
    def comparators():                                        # v0.6 A35: DPAC DR4 masses + BJK 2026 (DR3, via the id map), hashed now
        M = pd.read_csv(P('idmap'), dtype=str); B = pd.read_csv(os.path.join(HERE, '..', 'realdata', 'external', 'bjk2026_orbital300.csv'), dtype={'source_id': str})
        K = M.merge(B[['source_id', 'm2']].rename(columns={'source_id': 'dr3_source_id', 'm2': 'bjk_m2'}), on='dr3_source_id')[['dr4_source_id', 'bjk_m2']]
        K = K.rename(columns={'dr4_source_id': 'source_id'}).drop_duplicates('source_id')
        if os.path.exists(P('dpac')):
            Dp = pd.read_csv(P('dpac'), dtype={'source_id': str})
            if 'exoplanet_candidate_hrd_proba' in Dp:
                Dp['dpac_substellar_proba'] = Dp[[c for c in ('exoplanet_candidate_hrd_proba', 'lowmass_candidate_hrd_proba') if c in Dp]].sum(axis=1, min_count=1)
            K = K.merge(Dp, on='source_id', how='outer')
        K.to_csv(f'{out}/comparators.csv', index=False); import dr4_evaluate as E; return E.sha256(f'{out}/comparators.csv')
    hc = step('write + hash comparator scores (H20, before any outcome)', comparators)
    step('H11 outcomes (both prediction sets + controls)', lambda: sub(['h11_outcomes.py', '--pred', '../results/dr3_candidates_scored.csv', '--pred2',
         '../results/dr3_candidates_scored_A1.csv', '--controls', '../results/h11_controls.csv', '--idmap', P('idmap'), '--orbits', P('orbits'),
         '--out', f'{out}/h11.json']))
    step('H8 dynamical labels (DR4 combined solutions)', lambda: sub(['dr4_dynamical.py', P('combined'), f'{out}/dr4_dynamical_labels.csv']))
    def mech():
        sub(['dr4_mechanism.py', P('mech'), P('field'), P('field_vbroad'), '--idmap', mech_idmap or P('idmap')])
        for f in ('dr4_mechanism.json', 'dr4_mechanism_scored.csv', 'dr4_new_scored.csv'):
            os.replace(os.path.join(HERE, '..', 'results', f), f'{out}/{f}')
        o = json.load(open(f'{out}/dr4_mechanism.json'))
        return dict(n_input_rows=o['n_input_rows'], n_after_exclusion=o['n_after_exclusion'], n_V=o['n_V'], H12_status=o['H12_status'],
                    H18_H19={k: v.get('status') for k, v in o.get('H18_H19', {}).items() if isinstance(v, dict)})
    step('H12-H14 mechanism + H18/H19 (new combined orbits only)', mech)
    def unblind():
        o = json.load(open(f'{out}/dr4_mechanism.json')); h11 = json.load(open(f'{out}/h11.json'))
        p12 = o['H12_pvalue']['p_H12'] if o.get('H12_status') == 'CONDUCTED' else None
        kw = dict(expected=expected) if expected else {}
        e = dr4_evaluate.evaluate(f'{out}/gaiafp_dr4_catalogue.csv', h, labels, idmap=P('idmap'), dyn=f'{out}/dr4_dynamical_labels.csv',
                                  labels_sha=labels_sha, external_p={'H11a': h11['primary']['H11a'].get('p'), 'H12': p12},
                                  comparators=f'{out}/comparators.csv', comparators_sha=hc, **kw)
        json.dump(e, open(f'{out}/dr4_evaluation.json', 'w'), indent=1, default=float)
        return {k: (v.get('status') if isinstance(v, dict) and 'status' in v else None) for k, v in e.items() if k.startswith('H')} | {'holm': e['holm_family']}
    step('unblind + weighted Holm (H1, H2, A5, H11a, H12)', unblind)
    def h7step():
        if not h7: return 'NOT_CONDUCTED:NO_SB2_EPOCH_TABLES (run h7_xmatch.py by hand, DR4_READINESS.md)'
        import h7_xmatch
        o = h7_xmatch.main(['--catalogue', f'{out}/gaiafp_dr4_catalogue.csv', '--frozen-sha', h, '--sb2', *h7[0], '--epochs', h7[1],
                            '--map', P('idmap'), '--out', f'{out}/H7.json'])
        return dict(n_matched=o['n_matched'], n_sb2=o['n_sb2'], verdict=o['verdict_H7'])
    step('H7 survey SB2 (string ids)', h7step)
    import h15_purity
    step('H15 population purity (descriptive)', lambda: h15_purity.purity(pd.read_csv(f'{out}/gaiafp_dr4_catalogue.csv'))['impostor_fraction'])
    def h17():
        import new_hypotheses as NH
        if not os.path.exists(P('phot')): return 'NOT_CONDUCTED:NO_EPOCH_PHOTOMETRY'
        per = dict(zip(cand.source_id.str.strip(), cand.period.astype(float)))
        fl = NH.h17_flags(pd.read_csv(P('phot'), dtype={'source_id': str}), per); fl.to_csv(f'{out}/h17_flags.csv', index=False)
        C = pd.read_csv(f'{out}/gaiafp_dr4_catalogue.csv', dtype={'source_id': str}).assign(period=lambda x: x.source_id.map(per))
        r = NH.h17(C[['source_id', 'P_impostor', 'period']], fl); json.dump(r, open(f'{out}/h17.json', 'w'), indent=1, default=float)
        return r.get('status')
    step('H17 epoch photometry (secondary)', h17)
    return h

def dryrun(out):
    """The SAME run_chain as DR4 day, on FAKE DR4-like inputs and SYNTHETIC labels (the sealed file is never opened)."""
    os.makedirs(out, exist_ok=True)
    step('build fake DR4-like inputs', lambda: build_fake(out))
    R = os.path.join(HERE, '..', 'realdata')
    def fake_rest():
        c4 = pd.read_csv(f'{out}/candidates.csv', dtype={'source_id': str}); m = pd.read_csv(f'{out}/dr3_dr4_map.csv', dtype=str)
        ch = pd.read_csv(os.path.join(R, 'dr3_astrospectro_ch.csv'), dtype={'source_id': str})
        ch = ch.merge(m, left_on='source_id', right_on='dr3_source_id')[['dr4_source_id', 'c_thiele_innes', 'h_thiele_innes', 'c_thiele_innes_error', 'h_thiele_innes_error']]
        O = c4.merge(ch.rename(columns={'dr4_source_id': 'source_id'}), on='source_id', how='left')
        rng = np.random.default_rng(9); O = O[rng.random(len(O)) > 0.1]
        O = pd.concat([O, O.sample(frac=0.03, random_state=2).assign(nss_solution_type='SB2', a_thiele_innes=np.nan)])
        O.to_csv(f'{out}/{STD["orbits"]}', index=False); O[O.nss_solution_type == 'AstroSpectroSB1'].to_csv(f'{out}/{STD["combined"]}', index=False)
        S = pd.read_csv(os.path.join(R, 'dr3_astrospectro_all.csv'), dtype={'source_id': str}).sample(3000, random_state=1)
        S['source_id'] = [s[:-4] + '9999' if i % 2 else s for i, s in enumerate(S.source_id)]
        S.to_csv(f'{out}/{STD["mech"]}', index=False)
        pd.DataFrame(dict(dr3_source_id=S.source_id, dr4_source_id=S.source_id, angular_distance_arcsec=0.1)).to_csv(f'{out}/mech_idmap.csv', index=False)
        pd.read_csv(os.path.join(R, 'dr3_field.csv')).to_csv(f'{out}/{STD["field"]}', index=False)
        pd.read_csv(os.path.join(R, 'dr3_field_vbroad.csv')).to_csv(f'{out}/{STD["field_vbroad"]}', index=False)
        fake_rv = pd.read_csv(f'{out}/rvs_epochs.csv'); fake_rv.to_csv(f'{out}/{STD["rvs"]}', index=False)
        rng = np.random.default_rng(5); rows = []                 # synthetic epoch photometry: 20 % of candidates modulated
        for k, (s, P_) in enumerate(zip(c4.source_id[:300], c4.period[:300])):
            t = np.sort(rng.uniform(1700, 3600, 60)); amp = 0.004 if k % 5 == 0 else 0.0
            rows += [dict(source_id=s, g_obs_time=x, g_flux=1e5*(1 + amp*np.cos(4*np.pi*x/P_) + 1e-3*rng.standard_normal()), g_flux_error=100.0) for x in t]
        pd.DataFrame(rows).to_csv(f'{out}/{STD["phot"]}', index=False)
        r2 = np.random.default_rng(6)                             # fake DPAC comparator columns (H20)
        pd.DataFrame(dict(source_id=c4.source_id, fluxratio=r2.uniform(0, 1, len(c4)), exoplanet_candidate_hrd_proba=r2.uniform(0, .5, len(c4)),
                          lowmass_candidate_hrd_proba=r2.uniform(0, .5, len(c4)))).to_csv(f'{out}/{STD["dpac"]}', index=False)
        return dict(n_orbits=len(O), n_mech=len(S), n_phot_rows=len(rows))
    step('fake DR4 orbit, mechanism, field and photometry tables', fake_rest)
    def fake_h7():
        m = pd.read_csv(f'{out}/dr3_dr4_map.csv', dtype=str); rng = np.random.default_rng(4); ids = m.dr3_source_id.values
        pd.DataFrame(dict(gaia_dr3_source_id=rng.choice(ids, 60, replace=False))).to_csv(f'{out}/fake_sb2.csv', index=False)
        pd.DataFrame(dict(gaia_dr3_source_id=rng.choice(ids, 400, replace=False), n_epochs=rng.integers(1, 8, 400))).to_csv(f'{out}/fake_epochs.csv', index=False)
        return 'ok'
    step('fake SB2 survey tables', fake_h7)
    import dr4_evaluate
    return run_chain(out, out, f'{out}/FAKE_labels.json', dr4_evaluate.sha256(f'{out}/FAKE_labels.json'), 'ns_since_2010', 'J2017.5',
                     mech_idmap=f'{out}/mech_idmap.csv', h7=([f'{out}/fake_sb2.csv'], f'{out}/fake_epochs.csv'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='dryrun | prepare --raw RAW --std STD | run --std STD --labels FILE --out OUT')
    ap.add_argument('cmd', choices=['dryrun', 'prepare', 'run']); ap.add_argument('--out', default='../dryrun')
    ap.add_argument('--raw'); ap.add_argument('--std'); ap.add_argument('--labels')
    ap.add_argument('--time-unit', default='days_since_2010'); ap.add_argument('--ref-epoch', default='J2017.5')
    a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True)
    try:
        if a.cmd == 'dryrun': dryrun(a.out)
        elif a.cmd == 'prepare': LOG.append(dict(step='prepare', status='OK', info=prepare(a.raw, a.std)))
        else:
            import dr4_evaluate
            if not a.labels: raise SystemExit('run needs --labels (the sealed labels_v2 file; its SHA-256 is checked)')
            run_chain(a.std, a.out, a.labels, dr4_evaluate.LABELS_V2_SHA, a.time_unit, a.ref_epoch)
        status = 'COMPLETED'
    except BaseException as e:
        status = f'STOPPED: {type(e).__name__}: {e}'
    json.dump(dict(command=a.cmd, status=status, total_seconds=round(time.time() - t0, 1), steps=LOG), open(f'{a.out}/{a.cmd}_log.json', 'w'), indent=1, default=str)
    print(json.dumps(dict(status=status, total_seconds=round(time.time() - t0, 1), steps=[(s['step'], s['status'], s.get('seconds')) for s in LOG]), indent=1, default=str))
