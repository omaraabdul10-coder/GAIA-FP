"""gaia_rv_labels.py: exactly GAIA_RV_LABEL_PLAN.md (hashed first). Exploratory DR3 development."""
import json, hashlib, numpy as np, pandas as pd
from rvs_phase_test import K_sum_kms
from scipy.stats import rankdata
assert hashlib.sha256(open('../GAIA_RV_LABEL_PLAN.md', 'rb').read()).hexdigest().startswith('5f50bac9b1a6afc6'), 'plan changed: stop'
MJ = 9.546e-4
def auc(s, y):
    r = rankdata(s); n1 = int(y.sum()); n0 = len(y) - n1; return (r[y == 1].sum() - n1*(n1 + 1)/2)/(n1*n0)
def boot(f, y, B=2000, seed=7):
    rng = np.random.default_rng(seed); i1, i0 = np.where(y == 1)[0], np.where(y == 0)[0]
    return np.array([f(np.r_[rng.choice(i1, len(i1)), rng.choice(i0, len(i0))]) for _ in range(B)])

def main():
    sealed = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype=str).source_id.str.strip())
    C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str}); C = C[~C.source_id.isin(sealed)]
    R = pd.read_csv('../realdata/dr3_candidates_vbroad_raw.csv', dtype={'source_id': str}).drop_duplicates('source_id')
    D = C.merge(R[['source_id', 'rv_amplitude_robust', 'rv_nb_transits', 'radial_velocity_error']], on='source_id')
    D = D[(D.rv_nb_transits >= 6) & np.isfinite(D.rv_amplitude_robust) & np.isfinite(D.radial_velocity_error)].reset_index(drop=True)
    e = D.e.clip(0, 0.95).values; M = D.M.values
    K80 = K_sum_kms(M, 80*MJ*np.ones_like(M), D.P.values, e, D.inc.values)*(80*MJ)/(M + 80*MJ)
    sig = D.radial_velocity_error*np.sqrt(2*D.rv_nb_transits/np.pi)
    D['pos'] = (D.rv_amplitude_robust > 2*K80 + 5*sig + 1.0).astype(int); y = D.pos.values
    out = dict(n_with_rv=len(D), n_positive=int(y.sum()), K80_median_kms=float(np.median(K80)))
    if y.sum() < 5 or (y == 0).sum() < 5: out['status'] = 'NOT_CONDUCTED:BELOW_MIN_N'
    else:
        s = D.P_impostor.values; bs = boot(lambda i: auc(s[i], y[i]), y)
        out['GAIA_FP_auc'] = [float(auc(s, y)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        out['primary_pass'] = bool(np.percentile(bs, 2.5) > 0.5)
        b2 = D.P_B2.values; d = boot(lambda i: auc(s[i], y[i]) - auc(b2[i], y[i]), y)
        out['CMD_only_auc'] = float(auc(b2, y)); out['dAUC_vs_CMD'] = [float(auc(s, y) - auc(b2, y)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
        B = pd.read_csv('../realdata/external/bjk2026_orbital300.csv', dtype={'source_id': str})
        DB = D.merge(B[['source_id', 'm2']], on='source_id'); yb = DB.pos.values
        if yb.sum() >= 5:
            sb, mb = DB.P_impostor.values, DB.m2.values; d2 = boot(lambda i: auc(sb[i], yb[i]) - auc(mb[i], yb[i]), yb)
            out['vs_BJK'] = dict(n=len(DB), n_pos=int(yb.sum()), GAIA_FP_auc=float(auc(sb, yb)), BJK_m2_auc=float(auc(mb, yb)),
                                 dAUC=[float(auc(sb, yb) - auc(mb, yb)), float(np.percentile(d2, 2.5)), float(np.percentile(d2, 97.5))])
        out['verdicts_of_positives'] = D[D.pos == 1].verdict.value_counts().to_dict()
    json.dump(out, open('../results/gaia_rv_labels.json', 'w'), indent=1); print(json.dumps(out, indent=1))
if __name__ == '__main__':
    main()
