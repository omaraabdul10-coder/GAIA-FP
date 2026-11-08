"""
h11_control.py: H11 control group, rule registered in DR3_TO_DR4_PREDICTION_PLAN.md (OSF TBJGY), extracted from DR3 BEFORE DR4.

Rule (verbatim from the plan): DR3 nss_two_body_orbit astrometric solutions (Orbital, AstroSpectroSB1) whose implied
dark-companion mass is between 80 and 300 MJ. Each candidate is matched to one control by nearest neighbour in
(G, log P, significance), without replacement, seed 11.

Implementation choices fixed here (before any DR4 data exist):
  - implied mass: the same formula as the candidates (dr4_pipeline.features: m2 = (a0/plx)/a_rel * M / MJ, M from m1 if
    present, else the photometric relation); the same quality cuts as the candidate query (parallax/error > 10, parallax > 2 mas);
  - the matching space is standardised by the control pool's standard deviation;
  - greedy matching in a seed-11 random order of candidates; each candidate takes its nearest unused control;
  - sealed ids and candidate ids are removed from the pool first.
Input : a DR3 download with the columns of dr4_pipeline.SCHEMA (orbit_cols + source_cols), solution types Orbital/AstroSpectroSB1.
Output: results/h11_controls.csv (+ .sha256).
Run   : cd src && python h11_control.py <dr3_orbits.csv>
"""
import sys, hashlib, numpy as np, pandas as pd
import dr4_pipeline as D

def pool(raw, ridge_field):
    raw = raw[raw.nss_solution_type.isin(['Orbital', 'AstroSpectroSB1'])]
    raw = raw[(raw.parallax/raw.parallax_error > 10) & (raw.parallax > 2)].drop_duplicates('source_id')
    X = D.features(raw.reset_index(drop=True), D.fit_ms_ridge(ridge_field))
    m = np.isfinite(X[['mfit', 'G', 'P', 'significance']]).all(1) & (X.mfit >= 80) & (X.mfit <= 300)
    return X[m].reset_index(drop=True)

def match(cand, ctrl, seed=11):
    cols = lambda T: np.c_[T['G'].values, np.log10(T['P'].values), T['significance'].values]
    C, Q = cols(ctrl), cols(cand); s = C.std(0); s[s == 0] = 1; C, Q = C/s, Q/s
    used = np.zeros(len(C), bool); out = np.full(len(Q), -1)
    for i in np.random.default_rng(seed).permutation(len(Q)):
        d = np.sum((C - Q[i])**2, axis=1); d[used] = np.inf
        j = int(np.argmin(d))
        if np.isfinite(d[j]): out[i] = j; used[j] = True
    return out

def main(path, field='../realdata/dr3_field.csv'):
    raw = pd.read_csv(path, dtype={'source_id': str})
    sealed = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype={'source_id': str}).source_id.str.strip())
    cand = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str})
    raw = raw[~raw.source_id.str.strip().isin(sealed | set(cand.source_id.str.strip()))]
    ctrl = pool(raw, pd.read_csv(field))
    if len(ctrl) < len(cand):
        raise SystemExit(f'control pool ({len(ctrl)}) smaller than the candidate list ({len(cand)}): stop and log a deviation')
    j = match(cand, ctrl)
    out = ctrl.iloc[j].reset_index(drop=True); out.insert(0, 'matched_candidate', cand.source_id.values)
    out.to_csv('../results/h11_controls.csv', index=False)
    h = hashlib.sha256(open('../results/h11_controls.csv', 'rb').read()).hexdigest()
    open('../results/h11_controls.csv.sha256', 'w').write(f'{h}  h11_controls.csv\n')
    print(dict(n_pool=len(ctrl), n_matched=int((j >= 0).sum()), sha256=h))

if __name__ == '__main__':
    main(*sys.argv[1:])
