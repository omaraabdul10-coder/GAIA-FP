"""external_rv_validation.py: exactly as EXTERNAL_RV_VALIDATION_PLAN.md + amendment 1 (both hashed before data)."""
import json, hashlib, numpy as np, pandas as pd
H = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
assert H('../EXTERNAL_RV_VALIDATION_PLAN.md').startswith('965f2784abd3cf54'), 'plan changed: stop'
assert H('../EXTERNAL_RV_VALIDATION_PLAN_AMENDMENT_1.md').startswith('af03b95d071184a7'), 'amendment changed: stop'
MJ = 9.546e-4
S = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype=str).source_id.str.strip())
C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str}); C = C[~C.source_id.isin(S)]
M = pd.read_csv('../realdata/external/sb9_matches.csv', dtype={'source_id': str})
O = pd.read_csv('../realdata/external/sb9_orbits.csv')
O['year'] = O.bibcode.str[:4].astype(int)
def K(m2_MJ, r):   # km/s, primary semi-amplitude for companion mass m2 with the Gaia orbit
    m2 = m2_MJ*MJ
    return 28.4329*m2_MJ*np.sin(np.radians(r.inc))*(r.M + m2)**(-2/3)*(r.P/365.25)**(-1/3)/np.sqrt(1 - min(r.e, .95)**2)/1000
def m2_from_K(K1, r):   # solve K(m2)=K1 for m2 (MJ) by bisection
    lo, hi = 0.01, 1e5
    for _ in range(200):
        mid = np.sqrt(lo*hi); lo, hi = (mid, hi) if K(mid, r) < K1 else (lo, mid)
    return mid
rows = []
for _, m in M.iterrows():
    r = C[C.source_id == m.source_id].iloc[0]
    o = O[(O.sb9_seq == m.sb9_seq) & ((O.P_days - r.P).abs()/r.P <= 0.20)].sort_values('year')
    base = dict(source_id=m.source_id, sb9=int(m.sb9_seq), P_gaia=round(float(r.P), 2), mfit_MJ=round(float(r.mfit), 1),
                inc_deg=round(float(r.inc), 1), P_impostor=round(float(r.P_impostor), 3), verdict=r.verdict)
    if o.empty:
        rows.append(dict(base, label='excluded_different_orbit', P_ext=O[O.sb9_seq == m.sb9_seq].P_days.tolist())); continue
    o = o.iloc[-1]; k80 = K(80, r); sb2 = pd.notna(o.K2_kms)
    lab = 'impostor' if (sb2 or o.K1_kms >= k80) else 'substellar'
    m2rv = m2_from_K(o.K1_kms, r)
    rows.append(dict(base, label=lab, P_ext=float(o.P_days), K1=float(o.K1_kms), K2=None if not sb2 else float(o.K2_kms),
                     K80=round(float(k80), 3), K_sub=round(float(K(r.mfit, r)), 3), m2_RV_MJ=round(float(m2rv), 1),
                     m2_RV_over_mfit=round(float(m2rv/r.mfit), 2), bibcode=o.bibcode))
T = pd.DataFrame(rows); npos, nneg = (T.label == 'impostor').sum(), (T.label == 'substellar').sum()
res = dict(plan_sha='965f2784abd3cf54…', amendment_sha='af03b95d071184a7…', n_matched=len(T), n_pos=int(npos), n_neg=int(nneg),
           E1='NOT_CONDUCTED: fewer than 5 positives and 5 negatives' if (npos < 5 or nneg < 5) else 'see below',
           E2='NOT_CONDUCTED: same labels as E1', E3=T.to_dict('records'))
json.dump(res, open('../results/external_rv_validation.json', 'w'), indent=1, default=str)
print(T.drop(columns=['source_id']).to_string()); print(res['E1'])
