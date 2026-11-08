"""bjk_comparison.py: GAIA-FP vs Bailer-Jones & Kreidberg 2026 masses, exactly as BJK_COMPARISON_PLAN.md (hashed first)."""
import json, hashlib, numpy as np, pandas as pd
import dr3_study as S
from scipy.stats import rankdata
assert hashlib.sha256(open('../BJK_COMPARISON_PLAN.md', 'rb').read()).hexdigest().startswith('b55a1e7e9d1b435b'), 'plan changed: stop'
MJ80 = 0.0764

def auc(s, y):
    r = rankdata(s); n1 = int(y.sum()); n0 = len(y) - n1
    return (r[y == 1].sum() - n1*(n1 + 1)/2)/(n1*n0)

def compare(D, ycol, name):
    y = D[ycol].values.astype(int); i1, i0 = np.where(y == 1)[0], np.where(y == 0)[0]
    sc = dict(GAIA_FP=D.P_impostor.values, BJK_m2=D.m2.values, BJK_neg_log_flux_ratio=-D.log_flux_ratio.values)
    out = dict(label=name, n_pos=int(len(i1)), n_unlabelled=int(len(i0)), auc={k: float(auc(v, y)) for k, v in sc.items()})
    rng = np.random.default_rng(7); d = []
    for _ in range(2000):
        i = np.r_[rng.choice(i1, len(i1)), rng.choice(i0, len(i0))]
        d.append(auc(sc['GAIA_FP'][i], y[i]) - auc(sc['BJK_m2'][i], y[i]))
    lo, hi = np.percentile(d, [2.5, 97.5])
    out['dAUC_GAIAFP_minus_BJKm2'] = dict(est=out['auc']['GAIA_FP'] - out['auc']['BJK_m2'], ci95=[float(lo), float(hi)],
                                          verdict='GAIA-FP better' if lo > 0 else 'GAIA-FP worse' if hi < 0 else 'no detectable difference')
    return out

def main():
    sealed = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype=str).source_id.str.strip())
    B = pd.read_csv('../realdata/external/bjk2026_orbital300.csv', dtype={'source_id': str}); B = B[~B.source_id.isin(sealed)]
    C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str}); C = C[~C.source_id.isin(sealed)]
    D = C[['source_id', 'P_impostor', 'verdict']].merge(B, on='source_id')
    raw = pd.read_csv('../realdata/dr3_candidates.csv').drop_duplicates('source_id')
    R = lambda f: pd.read_csv('../realdata/' + f)
    lab = S.build_labels(raw, R('sb2_lamost.csv'), R('sb2_galah.csv'), R('sb2_apogee.csv'), R('lamost_cov.csv'))
    lab['source_id'] = lab.source_id.astype(str); lab['sb2'] = lab.sb2_lamost | lab.sb2_galah | lab.sb2_apogee
    A = pd.read_csv('../results/apogee_candidates.csv', dtype={'source_id': str})[['source_id', 'rv_incompatible']]
    res = dict(n_overlap=len(D), plan_sha='b55a1e7e9d1b435b…')
    DA = D.merge(A, on='source_id'); res['L1_APOGEE'] = compare(DA, 'rv_incompatible', 'APOGEE rv_incompatible (PU)')
    DS = D.merge(lab[['source_id', 'sb2']], on='source_id'); res['L2_SB2'] = compare(DS, 'sb2', 'survey SB2 (PU)')
    st = D.m2_lo > MJ80
    res['agreement'] = {v: dict(n=int((D.verdict == v).sum()), frac_BJK_m2lo_above_80MJ=float(st[D.verdict == v].mean()) if (D.verdict == v).any() else None)
                        for v in ('likely_impostor', 'ambiguous_followup_needed', 'likely_substellar')}
    json.dump(res, open('../results/bjk_comparison.json', 'w'), indent=1); print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
