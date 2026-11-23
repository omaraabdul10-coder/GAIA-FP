"""h21_baseline.py: H21, the baseline trap (H21_BASELINE_TRAP_PLAN.md, written before Gaia DR4).

usage (DR4 day):
  python h21_baseline.py --pred ../results/dr3_candidates_scored.csv --idmap STD/dr3_dr4_map.csv \
                         --orbits STD/dr4_orbits.csv --out OUT/H21.json
  python h21_baseline.py --freeze-groups ../results/h21_dr3_groups.json     (DR3 only; done before DR4)
"""
import sys, json, argparse
import numpy as np, pandas as pd
from scipy.stats import fisher_exact
import h11_outcomes as H

T3 = 1038.0                      # days, Gaia DR3 data span
X_NEAR, X_SHORT = 0.85, 0.5
R_UP = 1.5
MIN_N, MIN_S = 20, 100


def groups(pred):
    x = pred.P / T3
    return np.where(x >= X_NEAR, 'N', np.where(x < X_SHORT, 'S', 'M'))


def drop_sealed(pred, path=None):
    import os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'realdata', 'excluded_sealed_ids.csv')
    try:
        s = set(pd.read_csv(path, dtype=str).iloc[:, 0].str.strip())
    except FileNotFoundError:
        s = set()
    return pred[~pred.source_id.astype(str).isin(s)].copy()


def match(pred, idmap, orbits):
    """One row per DR3 object: DR4 id, has astrometric orbit, has any NSS solution, m2_DR4, P_DR4."""
    M = idmap[idmap.angular_distance_arcsec <= 1.0].sort_values('angular_distance_arcsec').drop_duplicates('dr3_source_id')
    P = pred.merge(M[['dr3_source_id', 'dr4_source_id']], left_on='source_id', right_on='dr3_source_id', how='left')
    O = orbits.copy()
    astro = O[O.a_thiele_innes.notna()].copy()
    if 'significance' in astro:
        astro = astro.sort_values('significance', ascending=False)
    astro = astro.drop_duplicates('source_id')
    m1 = P.set_index('dr4_source_id')['M']
    astro = astro[astro.source_id.isin(m1.index)].copy()
    astro['m1'] = astro.source_id.map(m1)                 # m1 fixed to the frozen DR3 value: only the orbit changes
    if 'phot_g_mean_mag' not in astro:
        astro['phot_g_mean_mag'] = np.nan
    _, med, _ = H.mass_bounds(astro) if len(astro) else (None, np.array([]), None)
    astro['m2_dr4'] = med
    P = P.merge(astro[['source_id', 'm2_dr4', 'period']].rename(columns={'source_id': 'dr4_source_id', 'period': 'P_dr4'}),
                on='dr4_source_id', how='left')
    P['any_nss'] = P.dr4_source_id.isin(set(O.source_id))
    P['has_orbit'] = P.m2_dr4.notna()
    P['r'] = P.m2_dr4 / P.mfit
    P['up'] = P.r >= R_UP
    P['group'] = groups(P)
    return P


def compare(P, col='up', seed=21, B=2000):
    n = P[P.group == 'N']; s = P[P.group == 'S']
    kN, nN, kS, nS = int(n[col].sum()), len(n), int(s[col].sum()), len(s)
    out = dict(n_N=nN, k_N=kN, n_S=nS, k_S=kS)
    if nN == 0 or nS == 0:
        return out
    pN, pS = kN / nN, kS / nS
    _, p = fisher_exact([[kN, nN - kN], [kS, nS - kS]], alternative='greater')
    rng = np.random.default_rng(seed); a, b = n[col].values.astype(float), s[col].values.astype(float)
    d = [rng.choice(a, nN).mean() - rng.choice(b, nS).mean() for _ in range(B)]
    out.update(p_N=pN, p_S=pS, diff=pN - pS, fisher_p_one_sided=float(p), diff_lower95_one_sided=float(np.percentile(d, 5)))
    return out


def run(pred, idmap, orbits):
    P = match(drop_sealed(pred), idmap, orbits)
    prim = P[P.has_orbit]
    res = dict(plan='H21_BASELINE_TRAP_PLAN.md', counts=dict(
        N=int((P.group == 'N').sum()), S=int((P.group == 'S').sum()), unmatched=int(P.dr4_source_id.isna().sum()),
        N_with_orbit=int((prim.group == 'N').sum()), S_with_orbit=int((prim.group == 'S').sum())))
    if res['counts']['N_with_orbit'] < MIN_N or res['counts']['S_with_orbit'] < MIN_S:
        res['H21'] = 'NOT_CONDUCTED: too few DR4 astrometric orbits (need >= %d in N and >= %d in S)' % (MIN_N, MIN_S)
    else:
        c = compare(prim); res['primary'] = c
        res['H21'] = 'PASS' if (c['fisher_p_one_sided'] < 0.05 and c['diff_lower95_one_sided'] > 0) else 'FAIL'
    # reported only
    P['up_b'] = P.up.fillna(False).astype(bool) | (~P.has_orbit & P.any_nss)
    res['H21b_unresolved_counts_as_revised'] = compare(P[P.dr4_source_id.notna()], 'up_b')
    res['below_40MJ'] = compare(prim[prim.mfit < 40])
    res['period_ratio_median'] = {g: float(np.nanmedian(prim[prim.group == g].P_dr4 / prim[prim.group == g].P))
                                  for g in ('N', 'S') if (prim.group == g).any()}
    res['period_change_gt_3sigma'] = {g: float(np.mean(np.abs(prim[prim.group == g].P_dr4 - prim[prim.group == g].P)
                                                        > 3 * prim[prim.group == g].sigP * prim[prim.group == g].P))
                                      for g in ('N', 'S') if (prim.group == g).any()}
    nn = prim[prim.group == 'N']
    if nn.up.nunique() == 2:
        from sklearn.metrics import roc_auc_score
        res['auc_Pimpostor_for_revised_up_in_N'] = float(roc_auc_score(nn.up, nn.P_impostor))
    return res, P


def freeze_groups(pred, out):
    pred = drop_sealed(pred); g = groups(pred)
    summ = {k: dict(n=int((g == k).sum()), sigP_median=float(np.median(pred.sigP[g == k])),
                    mfit_median=float(np.median(pred.mfit[g == k])),
                    verdicts=pred.verdict[g == k].value_counts().to_dict()) for k in ('N', 'M', 'S')}
    summ['T3_days'] = T3; summ['ids_N'] = sorted(pred.source_id[g == 'N'].astype(str))
    json.dump(summ, open(out, 'w'), indent=1)
    return summ


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--pred', default='../results/dr3_candidates_scored.csv')
    ap.add_argument('--idmap'); ap.add_argument('--orbits'); ap.add_argument('--out'); ap.add_argument('--freeze-groups')
    a = ap.parse_args(argv)
    pred = pd.read_csv(a.pred, dtype={'source_id': str})
    if a.freeze_groups:
        s = freeze_groups(pred, a.freeze_groups); print({k: s[k]['n'] for k in 'NMS'}); return
    idmap = pd.read_csv(a.idmap, dtype={'dr3_source_id': str, 'dr4_source_id': str})
    orbits = pd.read_csv(a.orbits, dtype={'source_id': str})
    res, P = run(pred, idmap, orbits)
    json.dump(res, open(a.out, 'w'), indent=1, default=str)
    P.to_csv(a.out.replace('.json', '_objects.csv'), index=False)
    print(res['H21'])


if __name__ == '__main__':
    main(sys.argv[1:])
