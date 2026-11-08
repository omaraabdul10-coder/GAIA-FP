"""
dr4_evaluate.py: the unblinding step for the sealed labelled set and the DR4 dynamical labels (audit of 31 Oct 2026).

Implements, with the registered rules:
  H1  AUC of P_impostor on the sealed set (39 impostors vs 26 substellar), STRATIFIED bootstrap (prereg §7).
  H2  impostor rejection at 95 % substellar retention, objects with >= 15 RVS epochs, primary empirical score
      (A7: cmd_z + rvs_z) minus CMD-only (cmd_z); paired stratified bootstrap.
  H3  Brier score full model vs CMD-only model (real part; the pooled synthetic part is added if --synthetic is given).
  H5  label-free EM fraction (mean P_impostor over labelled objects) inside the Clopper-Pearson CI of the observed fraction.
  H8  (a) AUC vs DR4 dynamical labels (A3 rules), (b) recall at P >= 0.85; A5: dAUC(P_impostor - B2).
  Multiplicity: amendment v0.6 A18 (Holm, one-sided family-wise alpha = 0.025) over the conducted confirmatory hypotheses.
Status vocabulary (v0.6 A19): PASS, FAIL, NOT_CONDUCTED:<reason>. NOT_CONDUCTED is never reported as FAIL.

The catalogue must already be frozen: its SHA-256 is checked before the label file is opened.
Run: cd src && python dr4_evaluate.py --catalogue ../catalogue/gaiafp_dr4_catalogue.csv --frozen-sha <sha> \
        --labels ../sealed/labels_v2.json --idmap dr3_dr4_map.csv [--dyn ../results/dr4_dynamical_labels.csv]
"""
import argparse, hashlib, json, sys, numpy as np, pandas as pd
from scipy.special import expit, logit
from scipy.stats import rankdata, beta as beta_dist

SEED, NBOOT, ALPHA_FW = 7, 2000, 0.025
LABELS_V2_SHA = 'a8ccb9b6fd1b4bf97bd9669d8be866bb33bd83b3c630feb90933f9a05703d3aa'   # labels_v2r (v0.6 A38); v2 was d6b0aabb...
EXPECTED = dict(n_entries=76, impostor=39, substellar=26)
MIN_CLASS = 10                       # v0.6 A19: an AUC-type test needs >= 10 objects in each class
CONFIRMATORY = ('H1', 'H2', 'A5', 'H11a', 'H12')

# ------------------------------------------------------------------ helpers
def sha256(path): return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, int); r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1*(n1+1)/2)/(n1*n0))

def strat_boot(fn, y, n=NBOOT, seed=SEED):
    rng = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    return np.array([fn(np.r_[rng.choice(pos, len(pos)), rng.choice(neg, len(neg))]) for _ in range(n)])

def p_one_sided(bs, null, side):
    """bootstrap p-value: share of replicates on the null side (with +1 correction)."""
    k = np.sum(bs <= null) if side == 'greater' else np.sum(bs >= null)
    return float((k + 1)/(len(bs) + 1))

def clopper_pearson(k, n, a=0.05):
    lo = beta_dist.ppf(a/2, k, n-k+1) if k > 0 else 0.0
    hi = beta_dist.ppf(1-a/2, k+1, n-k) if k < n else 1.0
    return float(lo), float(hi)

def rejection_at_retention(s, y, retention=0.95, achieved=False):
    """Order-statistic threshold (audit A2-F5: np.quantile interpolates and under-delivers the retention):
    thr = the ceil(retention*n0)-th smallest substellar score, so at least `retention` of substellar objects are kept
    (score <= thr); returns the share of impostors with score > thr (and optionally the achieved retention)."""
    s0 = np.sort(s[y == 0]); k = int(np.ceil(retention*len(s0))) - 1; thr = s0[k]
    rej = float(np.mean(s[y == 1] > thr))
    return (rej, float(np.mean(s0 <= thr))) if achieved else rej

def holm(pvals, alpha=ALPHA_FW):
    """pvals: dict name -> p for CONDUCTED confirmatory hypotheses. Returns name -> (p, adjusted threshold, rejected)."""
    order = sorted(pvals, key=pvals.get); m = len(order); out = {}; still = True
    for k, h in enumerate(order):
        thr = alpha/(m - k); rej = still and pvals[h] <= thr; still = rej
        out[h] = dict(p=pvals[h], holm_threshold=thr, rejected=bool(rej))
    return out

HOLM_WEIGHTS = dict(H1=0.4, A5=0.2, H12=0.2, H2=0.1, H11a=0.1)     # v0.6 A31, fixed before DR4 from the DR3 power analysis

def weighted_holm(pvals, weights=HOLM_WEIGHTS, alpha=ALPHA_FW):
    """v0.6 A31: weighted Holm (Holm 1979). Weights of the CONDUCTED hypotheses are renormalised; at each step every remaining
    hypothesis with p <= alpha*w/sum(remaining w) is rejected and its weight is passed on; stop when none is rejected."""
    rem = {h: weights[h] for h in pvals}; out = {}
    while rem:
        tot = sum(rem.values()); thr = {h: alpha*w/tot for h, w in rem.items()}
        rej = [h for h in rem if pvals[h] <= thr[h]]
        for h in rem: out[h] = dict(p=pvals[h], weighted_threshold=thr[h], rejected=h in rej)
        if not rej: break
        for h in rej: del rem[h]
    return out

def not_conducted(reason): return dict(status=f'NOT_CONDUCTED:{reason}')

# ------------------------------------------------------------------ labels (opened only after the catalogue hash check)
def load_labels(path, expected_sha=LABELS_V2_SHA, expected=EXPECTED):
    h = sha256(path)
    if h != expected_sha: raise SystemExit(f'label file hash {h} != sealed hash {expected_sha}: stop')
    E = json.load(open(path))['entries']
    if len(E) != expected['n_entries']: raise SystemExit(f'{len(E)} label entries, expected {expected["n_entries"]}: stop')
    L = pd.DataFrame(E); L['source_id'] = L.source_id.astype(str).str.strip()
    if L.source_id.duplicated().any(): raise SystemExit('duplicate source_id in the label file: stop')
    L = L[L.label.isin(['impostor', 'substellar'])].copy(); L['y'] = (L.label == 'impostor').astype(int)
    n1, n0 = int(L.y.sum()), int((L.y == 0).sum())
    if (n1, n0) != (expected['impostor'], expected['substellar']):
        raise SystemExit(f'analysed counts {n1}/{n0} != registered {expected["impostor"]}/{expected["substellar"]}: stop')
    return L[['source_id', 'y']]

def map_ids(L, idmap):
    """DR3 ids in the label file -> DR4 ids. idmap: columns dr3_source_id, dr4_source_id (one row per DR3 id; nearest match)."""
    if idmap is None: L = L.copy(); L['dr4_source_id'] = L.source_id; return L
    M = pd.read_csv(idmap, dtype=str)
    need = {'dr3_source_id', 'dr4_source_id'}
    if not need <= set(M.columns): raise SystemExit(f'id map lacks columns {need - set(M.columns)}: stop')
    M = M.drop_duplicates('dr3_source_id')
    return L.merge(M, left_on='source_id', right_on='dr3_source_id', how='left')

# ------------------------------------------------------------------ hypotheses
def h1(D):
    y, s = D.y.values, D.P_impostor.values
    if min(y.sum(), (y == 0).sum()) < MIN_CLASS: return not_conducted('BELOW_MIN_N')
    bs = strat_boot(lambda i: auc(s[i], y[i]), y)
    return dict(status='CONDUCTED', n_imp=int(y.sum()), n_sub=int((y == 0).sum()), auc=auc(s, y),
                ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], p=p_one_sided(bs, 0.5, 'greater'),
                registered_pass=bool(np.percentile(bs, 2.5) > 0.5))

H20_COMPARATORS = {'DPAC_fluxratio': ('fluxratio', +1), 'DPAC_substellar_proba': ('dpac_substellar_proba', -1), 'BJK2026_m2': ('bjk_m2', +1)}

def h20(D):
    """v0.6 A35 (secondary): GAIA-FP vs published comparators on the sealed labels. For each comparator, on the objects where it
    exists: AUC of both and the paired stratified-bootstrap ΔAUC (GAIA-FP − comparator). 'better'/'worse' only if the 95% CI excludes 0."""
    res = {}
    for name, (col, sign) in H20_COMPARATORS.items():
        if col not in D: res[name] = not_conducted('COLUMN_ABSENT'); continue
        S = D[np.isfinite(D[col].astype(float))]; y = S.y.values
        if min(y.sum(), (y == 0).sum()) < MIN_CLASS: res[name] = not_conducted('BELOW_MIN_N'); continue
        a, b = S.P_impostor.values, sign*S[col].astype(float).values
        bs = strat_boot(lambda i: auc(a[i], y[i]) - auc(b[i], y[i]), y); lo, hi = np.percentile(bs, [2.5, 97.5])
        res[name] = dict(status='CONDUCTED', n_imp=int(y.sum()), n_sub=int((y == 0).sum()), auc_gaiafp=auc(a, y), auc_comparator=auc(b, y),
                         dauc=auc(a, y) - auc(b, y), ci95=[float(lo), float(hi)],
                         verdict='GAIA-FP better' if lo > 0 else 'GAIA-FP worse' if hi < 0 else 'no detectable difference')
    return res

def cmd_z(D): return -D.dm.values/D.sig_cmd.values

def h2(D, min_epochs=15):
    if 'nep' not in D or 'score_emp' not in D: return not_conducted('NO_RVS_COLUMNS')
    S = D[D.nep >= min_epochs]; y = S.y.values
    if min(y.sum(), (y == 0).sum()) < MIN_CLASS: return not_conducted('BELOW_MIN_N')
    a, b = S.score_emp.values, cmd_z(S)
    if not (np.isfinite(a).all() and np.isfinite(b).all()): raise SystemExit('H2: non-finite score_emp or CMD z: stop')
    f = lambda i: rejection_at_retention(a[i], y[i]) - rejection_at_retention(b[i], y[i])
    bs = strat_boot(f, y); d = f(np.arange(len(y)))
    return dict(status='CONDUCTED', n_imp=int(y.sum()), n_sub=int((y == 0).sum()), diff=d,
                rej_full=rejection_at_retention(a, y), rej_cmd=rejection_at_retention(b, y),
                achieved_retention=[rejection_at_retention(a, y, achieved=True)[1], rejection_at_retention(b, y, achieved=True)[1]],
                ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], p=p_one_sided(bs, 0.0, 'greater'),
                registered_falsified=bool(np.percentile(bs, 2.5) <= 0 and d <= 0))

def h3(D, synthetic=None):
    """CMD-only model in the v3 convention of the registered tournament code: the a0|CMD likelihood WITHOUT the RVS term
    (column llr_cmd) with the same prior (audit A2-F18: documented, not a pure-CMD model)."""
    p_full = D.P_impostor.values
    p_cmd = expit(D.llr_cmd.values + logit(np.clip(D.prior_pi.values, 1e-6, 1-1e-6)))
    y = D.y.values; out = dict(status='CONDUCTED', brier_full_real=float(np.mean((p_full-y)**2)), brier_cmd_real=float(np.mean((p_cmd-y)**2)))
    if synthetic is not None:
        Sx = pd.read_csv(synthetic); yy = np.r_[y, Sx.y.values]
        out['brier_full_pooled'] = float(np.mean((np.r_[p_full, Sx.P_full.values]-yy)**2))
        out['brier_cmd_pooled'] = float(np.mean((np.r_[p_cmd, Sx.P_cmd.values]-yy)**2))
        out['pass'] = out['brier_full_pooled'] < out['brier_cmd_pooled']
    else:
        out['pass_real_only'] = out['brier_full_real'] < out['brier_cmd_real']; out['note'] = 'pooled synthetic part not supplied'
    return out

def h5(D):
    y = D.y.values; k, n = int(y.sum()), len(y); lo, hi = clopper_pearson(k, n); em = float(D.P_impostor.mean())
    return dict(status='CONDUCTED', observed=k/n, ci95=[lo, hi], em_estimate=em, pass_=bool(lo <= em <= hi))

def h6(D):
    """H6 (secondary): AUC(ML trained on the Lammers & Winn DR4 simulator) - AUC(GAIA-FP), paired stratified bootstrap.
    The ML model is the tournament's (tournament.ml_model on tournament.splits()[0]); features P, e, mfit, d, G, dm, z."""
    try:
        import tournament
        ml = tournament.ml_model(tournament.splits()[0])
    except (FileNotFoundError, OSError):
        return not_conducted('DATA_ABSENT (simulator mocks)')
    miss = [c for c in tournament.COLS if c not in D]
    if miss: return not_conducted(f'SCHEMA_MISMATCH {miss}')
    y = D.y.values
    if min(y.sum(), (y == 0).sum()) < MIN_CLASS: return not_conducted('BELOW_MIN_N')
    s_ml = ml.predict_proba(D[tournament.COLS].values.astype(float))[:, 1]; s = D.P_impostor.values
    bs = strat_boot(lambda i: auc(s_ml[i], y[i]) - auc(s[i], y[i]), y)
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    # Preserve the current v0.6 ledger interpretation. A separate earlier
    # project note records a different -0.01 rule; do not merge the definitions.
    return dict(status='CONDUCTED', auc_ml=auc(s_ml, y), auc_gaiafp=auc(s, y), diff_ml_minus_gaiafp=auc(s_ml, y) - auc(s, y),
                ci95=[lo, hi], registered_falsified=bool(lo > 0))

def h8(Dd):
    y = Dd.label.values; s = Dd.P_impostor.values
    out = dict(n_imp=int((y == 1).sum()), n_gen=int((y == 0).sum()))
    k85 = int(np.sum(s[y == 1] >= 0.85)); n1 = int((y == 1).sum())
    out['recall_P>=0.85'] = [k85, n1, list(clopper_pearson(k85, n1))] if n1 else None
    out['recall_pass'] = bool(n1 and k85/n1 >= 0.80)
    if min(out['n_imp'], out['n_gen']) < MIN_CLASS:
        out['auc'] = not_conducted('BELOW_MIN_N'); out['A5'] = not_conducted('BELOW_MIN_N'); return out
    bs = strat_boot(lambda i: auc(s[i], y[i]), y)
    out['auc'] = dict(value=auc(s, y), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
    b2 = -Dd.dm.values/Dd.sig_cmd.values
    bd = strat_boot(lambda i: auc(s[i], y[i]) - auc(b2[i], y[i]), y)
    out['A5'] = dict(status='CONDUCTED', dAUC=auc(s, y) - auc(b2, y), ci95=[float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
                     p=p_one_sided(bd, 0.0, 'greater'))
    return out

# ------------------------------------------------------------------ main
REQUIRED = ['source_id', 'P_impostor', 'prior_pi', 'llr_cmd', 'dm', 'sig_cmd']

def evaluate(catalogue, frozen_sha, labels, idmap=None, dyn=None, synthetic=None, labels_sha=LABELS_V2_SHA, expected=EXPECTED,
             external_p=None, comparators=None, comparators_sha=None):
    h = sha256(catalogue)
    if h != frozen_sha: raise SystemExit(f'catalogue hash {h} != frozen hash {frozen_sha}: refuse to unblind')
    C = pd.read_csv(catalogue, dtype={'source_id': str}); C['source_id'] = C.source_id.str.strip()
    miss = [c for c in REQUIRED if c not in C]
    if miss: raise SystemExit(f'catalogue lacks columns {miss}: stop')
    if not ((C.P_impostor >= 0) & (C.P_impostor <= 1)).all(): raise SystemExit('P_impostor outside [0, 1]: stop')
    L = map_ids(load_labels(labels, labels_sha, expected), idmap)
    if C.source_id.duplicated().any(): raise SystemExit('duplicate source_id in the catalogue: stop')
    D = L.merge(C, left_on='dr4_source_id', right_on='source_id', how='inner', suffixes=('_dr3', ''))
    if D.dr4_source_id.duplicated().any(): raise SystemExit('two labelled DR3 sources map to one DR4 source: stop')
    for c in ('P_impostor', 'dm', 'sig_cmd'):
        if not np.isfinite(D[c]).all(): raise SystemExit(f'non-finite {c} among labelled objects: stop')
    out = dict(catalogue_sha256=h, n_labelled_registered=expected['impostor'] + expected['substellar'], n_labelled_in_catalogue=len(D),
               missing_from_catalogue=int(expected['impostor'] + expected['substellar'] - len(D)))
    out['H1'] = h1(D); out['H2'] = h2(D); out['H3'] = h3(D, synthetic); out['H5'] = h5(D); out['H6'] = h6(D)
    if comparators is not None:                       # v0.6 A35 (secondary): head-to-head on the same sealed labels
        if sha256(comparators) != comparators_sha: raise SystemExit('comparator file changed after hashing: stop')
        K = pd.read_csv(comparators, dtype={'source_id': str}); K['source_id'] = K.source_id.str.strip()
        out['H20'] = h20(D.merge(K, on='source_id', how='left'))
    else:
        out['H20'] = not_conducted('NO_COMPARATOR_FILE')
    if dyn is not None:
        Y = pd.read_csv(dyn, dtype={'source_id': str}); Y = Y[Y.label >= 0]
        out['H8'] = h8(Y.merge(C, on='source_id', how='inner'))
    else:
        out['H8'] = not_conducted('NO_DYNAMICAL_LABEL_FILE')
    pv = {}
    for k in ('H1', 'H2'):
        if out[k].get('status') == 'CONDUCTED': pv[k] = out[k]['p']
    a5 = out['H8'].get('A5', {}) if isinstance(out['H8'], dict) else {}
    if a5.get('status') == 'CONDUCTED': pv['A5'] = a5['p']
    for k, v in (external_p or {}).items():          # H11a, H12 come from their own runners as p-values
        if v is not None: pv[k] = v
    out['holm_family'] = dict(alpha_one_sided=ALPHA_FW, conducted=sorted(pv), not_conducted=[k for k in CONFIRMATORY if k not in pv],
                              result=weighted_holm(pv), weights=HOLM_WEIGHTS, sensitivity_equal_weight_holm=holm(pv))
    return out

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalogue', required=True); ap.add_argument('--frozen-sha', required=True); ap.add_argument('--labels', required=True)
    ap.add_argument('--idmap'); ap.add_argument('--dyn'); ap.add_argument('--synthetic')
    ap.add_argument('--p-h11a', type=float); ap.add_argument('--p-h12', type=float); ap.add_argument('--out', default='../results/dr4_evaluation.json')
    a = ap.parse_args(argv)
    out = evaluate(a.catalogue, a.frozen_sha, a.labels, a.idmap, a.dyn, a.synthetic, external_p={'H11a': a.p_h11a, 'H12': a.p_h12})
    json.dump(out, open(a.out, 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))

if __name__ == '__main__':
    main(sys.argv[1:])
