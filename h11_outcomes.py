"""
h11_outcomes.py: DR4 outcomes O1-O5 / D and the H11 metrics of DR3_TO_DR4_PREDICTION_PLAN.md (OSF TBJGY), audit of 31 Oct 2026.

Inputs (CSV; the release adapter writes them, column names fixed here):
  --pred     results/dr3_candidates_scored.csv (frozen, SHA-256 checked) [+ --pred2 results/dr3_candidates_scored_A1.csv]
  --idmap    dr3_source_id, dr4_source_id, angular_distance_arcsec   (official DR3->DR4 neighbourhood table, nearest within 1")
  --orbits   every DR4 two-body solution of the matched sources: source_id (DR4), nss_solution_type, period, period_error,
             a/b/f/g_thiele_innes(+_error), c/h_thiele_innes(+_error) where present, parallax, parallax_error,
             phot_g_mean_mag  [m1, m1_lower, m1_upper optional]
  --o5       optional: source_id (DR4), z  (frozen RVS phase statistic on DR4 epoch widths)
  --controls results/h11_controls.csv (frozen before DR4) + the same columns for the controls' DR4 solutions in --orbits
Fixed clarifications (v0.6 A20, written before DR4):
  * B2 "Brier" uses P_B2 from results/dr3_candidates_B2prob.csv (frozen before DR4 by h11_prepare.b2_probability: the
    pure-CMD likelihood ratio with GAIA-FP's own frozen prior; P_B2_em, a constant-pi EM variant, is a sensitivity analysis). dm/sig_cmd itself is not a probability. NOTE: the column llr_cmd of the prediction
    file is NOT a CMD-only quantity (it is the a0|CMD joint LR without RVS, equal to log_lr on DR3), so it must not be used here.
  * O2/D mass bounds: Monte Carlo over the Thiele-Innes and parallax errors, n = 400, seed 0; m1 fixed (release m1 if given,
    else the photometric relation); mass formula = dr4_pipeline.features (first order, dark companion).
  * O1 period match: |P4/P3 - k| <= 0.3 k for k in {0.5, 1, 2}.
  * H11b uses the pooled high-confidence errors (likely_impostor that are D, plus likely_substellar that are impostors);
    each class is also reported.
  * SB2-family solution types for O4: names containing 'SB2' (e.g. SB2, SB2C), case-insensitive.
"""
import argparse, hashlib, json, sys, numpy as np, pandas as pd
import dr4_pipeline as D
import dr4_dynamical as DD
from dr4_evaluate import auc, clopper_pearson, p_one_sided

FROZEN_PRED_SHA = '141734677a64942e38fc8512611c7653eaaa024a2d375524cc7f50b40200a7fc'
MJ = D.MJ; SEED, NBOOT = 7, 2000

def sha256(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def mass_bounds(O, n=400, seed=0):
    rng = np.random.default_rng(seed); lo, hi, med = [], [], []
    for _, r in O.iterrows():
        g = lambda k: r[k] + r[k+'_error']*rng.standard_normal(n)
        a0, _, _, _ = D.campbell(g('a_thiele_innes'), g('b_thiele_innes'), g('f_thiele_innes'), g('g_thiele_innes'))
        plx = r['parallax'] + r['parallax_error']*rng.standard_normal(n)
        m1 = r['m1'] if np.isfinite(r.get('m1', np.nan)) else D.mass_from_MG(r['phot_g_mean_mag'] + 5*np.log10(r['parallax']/100))
        arel = (m1*(r['period']/365.25)**2)**(1/3)
        m2 = np.where(plx > 0, (a0/plx)/arel*m1/MJ, np.nan)
        lo.append(np.nanpercentile(m2, 2.5)); hi.append(np.nanpercentile(m2, 97.5)); med.append(np.nanmedian(m2))
    return np.array(lo), np.array(med), np.array(hi)

def outcomes(pred, idmap, orbits, o5=None):
    M = idmap.copy(); M = M[M.angular_distance_arcsec <= 1.0].sort_values('angular_distance_arcsec').drop_duplicates('dr3_source_id')
    P = pred.merge(M, left_on='source_id', right_on='dr3_source_id', how='left')
    O = orbits.copy(); O['is_sb2'] = O.nss_solution_type.str.upper().str.contains('SB2')
    astro = O[O.a_thiele_innes.notna()].copy()
    lo, med, hi = mass_bounds(astro) if len(astro) else (np.array([]),)*3
    astro['m2_lo'], astro['m2_med'], astro['m2_hi'] = lo, med, hi
    comb = astro[astro.c_thiele_innes.notna()] if 'c_thiele_innes' in astro else astro.iloc[:0]
    rho = DD.labels(comb)[['source_id', 'rho_lo', 'rho_hi']] if len(comb) else pd.DataFrame(columns=['source_id', 'rho_lo', 'rho_hi'])
    rows = []
    for _, r in P.iterrows():
        s4 = r['dr4_source_id']
        if not isinstance(s4, str):                      # no DR4 counterpart within 1": reported, excluded from every metric
            rows.append(dict(source_id=r['source_id'], dr4_source_id=None, unmatched=True, O1=False, O2=False, O3=False, O4=False,
                             O5=False, D=False, label=-1)); continue
        sol = O[O.source_id == s4]
        ratio = sol.period.values/r['P'] if len(sol) else np.array([])
        match = any(abs(x - k) <= 0.3*k for x in ratio for k in (0.5, 1.0, 2.0))
        a = astro[astro.source_id == s4]; rr = rho[rho.source_id == s4]
        O1 = not match
        O2 = bool(len(a) and (a.m2_lo > 80).any())
        O3 = bool(len(rr) and (rr.rho_hi < 0.9).any())
        O4 = bool(len(sol) and sol.is_sb2.any())
        O5 = bool(o5 is not None and s4 in set(o5.source_id) and (o5.loc[o5.source_id == s4, 'z'] > 2.3).any())
        Dk = bool(len(a) and (a.m2_hi < 80).all() and (len(rr) == 0 or (rr.rho_lo > 0.9).all()) and not (O3 or O4 or O5))
        lab = 1 if (O2 or O3 or O4) else (0 if Dk else -1)
        rows.append(dict(source_id=r['source_id'], dr4_source_id=s4, unmatched=False, O1=O1, O2=O2, O3=O3, O4=O4, O5=O5, D=Dk, label=lab))
    return pd.DataFrame(rows)

def brier(p, y): return float(np.mean((p - y)**2))

def metrics(pred, out, pcol='P_impostor', vcol='verdict'):
    Z = pred.merge(out, on='source_id'); Z = Z[(Z.label >= 0) & ~Z.O1]; y = Z.label.values
    res = dict(n_labelled=len(Z), n_impostor=int(y.sum()), n_D=int((y == 0).sum()))
    if len(Z) < 30 or min(y.sum(), (y == 0).sum()) < 5:
        res['H11a'] = dict(status='NOT_CONDUCTED:BELOW_MIN_N'); return res
    p = Z[pcol].values; pc = Z['P_B2'].values           # v0.6 A20: frozen CMD-only probability (h11_prepare.b2_probability)
    rng = np.random.default_rng(SEED); n = len(y)
    bs = np.array([(lambda i: brier(p[i], y[i]) - brier(pc[i], y[i]))(rng.integers(0, n, n)) for _ in range(NBOOT)])
    d = brier(p, y) - brier(pc, y)
    res['M1'] = dict(brier=brier(p, y), brier_cmd_only=brier(pc, y),
                     reliability=[dict(bin=[a, b], n=int(m.sum()), mean_p=float(p[m].mean()), frac=float(y[m].mean()))
                                  for a, b in zip(np.linspace(0, .8, 5), np.linspace(.2, 1, 5))
                                  for m in [((p >= a) & ((p < b) if b < 1 else (p <= b)))] if m.sum()])
    if 'P_B2_em' in Z: res['H11a_sensitivity_B2_em'] = dict(dBrier=brier(p, y) - brier(Z.P_B2_em.values, y))
    res['H11a'] = dict(status='CONDUCTED', dBrier=d, ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                       p=p_one_sided(bs, 0.0, 'less'), registered_pass=bool(np.percentile(bs, 97.5) < 0))
    li, ls = Z[vcol] == 'likely_impostor', Z[vcol] == 'likely_substellar'
    e1, n1 = int(((y == 0) & li).sum()), int(li.sum()); e2, n2 = int(((y == 1) & ls).sum()), int(ls.sum())
    res['H11b'] = dict(pooled=[e1 + e2, n1 + n2, list(clopper_pearson(e1 + e2, n1 + n2))] if n1 + n2 else None,
                       likely_impostor_that_are_D=[e1, n1], likely_substellar_that_are_impostors=[e2, n2],
                       registered_pass=bool(n1 + n2 and clopper_pearson(e1 + e2, n1 + n2)[1] < 0.10))
    res['M3_auc'] = {k: auc(v, y) for k, v in dict(GAIA_FP=p, B1_RUWE=Z.ruwe.values, B2_CMD=-Z.dm.values/Z.sig_cmd.values,
                                                     B3_inv_significance=-Z.significance.values, log_lr=Z.log_lr.values).items()}
    return res

def main(argv):
    ap = argparse.ArgumentParser()
    for k in ('pred', 'idmap', 'orbits'): ap.add_argument('--'+k, required=True)
    ap.add_argument('--pred2'); ap.add_argument('--o5'); ap.add_argument('--controls'); ap.add_argument('--out', default='../results/h11_dr4.json')
    a = ap.parse_args(argv)
    if sha256(a.pred) != FROZEN_PRED_SHA: raise SystemExit('frozen DR3 prediction file changed: stop')
    pred = pd.read_csv(a.pred, dtype={'source_id': str})
    b2 = '../results/dr3_candidates_B2prob.csv'
    if sha256(b2) != open(b2 + '.sha256').read().split()[0]: raise SystemExit('B2 probability file changed: stop')
    pred = pred.merge(pd.read_csv(b2, dtype={'source_id': str})[['source_id', 'P_B2', 'P_B2_em']], on='source_id', how='left')
    idmap = pd.read_csv(a.idmap, dtype={'dr3_source_id': str, 'dr4_source_id': str})
    orbits = pd.read_csv(a.orbits, dtype={'source_id': str}); o5 = pd.read_csv(a.o5, dtype={'source_id': str}) if a.o5 else None
    for need in (['dr3_source_id', 'dr4_source_id', 'angular_distance_arcsec'],):
        if not set(need) <= set(idmap.columns): raise SystemExit(f'id map lacks {set(need) - set(idmap.columns)}: stop')
    out = outcomes(pred, idmap, orbits, o5); res = dict(outcome_counts={k: int(out[k].sum()) for k in ('unmatched', 'O1', 'O2', 'O3', 'O4', 'O5', 'D')})
    res['primary'] = metrics(pred, out)
    if a.pred2:
        P2 = pd.read_csv(a.pred2, dtype={'source_id': str}).merge(pred[['source_id', 'P_B2', 'P_B2_em', 'llr_cmd', 'prior_pi', 'ruwe', 'dm', 'sig_cmd', 'significance', 'log_lr']], on='source_id')
        res['second_prediction_set_A1'] = metrics(P2, out, 'P_impostor_A1', 'verdict_A1')
    if a.controls:
        C = pd.read_csv(a.controls, dtype={'source_id': str}); C['P'] = C['P'].astype(float)
        oc = outcomes(C.assign(source_id=C.source_id), idmap, orbits)
        res['M4'] = dict(O1_rate_candidates=float(out.O1.mean()), O1_rate_controls=float(oc.O1.mean()), n_controls=len(oc))
    out.to_csv(a.out.replace('.json', '_outcomes.csv'), index=False)
    json.dump(res, open(a.out, 'w'), indent=1, default=float); print(json.dumps(res, indent=1, default=float))

if __name__ == '__main__':
    main(sys.argv[1:])
