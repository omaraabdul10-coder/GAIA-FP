"""vbroad_v2.py: VBROAD_V2_PLAN.md (hashed before running). REAL DATA: Gaia DR3 AstroSpectroSB1.
SB1-truncated, saturating blend model; c chosen on TRAIN (even source_id), tested once on TEST (odd)."""
import json, numpy as np, pandas as pd
from scipy.stats import norm
from scipy.special import logsumexp
import dark_companion as DC
from rvs_phase_test import K_sum_kms, true_anomaly

CGRID = (0.05, 0.1, 0.2, 0.5, 1, 2, 4); DVMAX = 30.0; LMIN = 0.2

def maxsep_shape(e, om_deg, n=64):
    M = np.linspace(0, 2*np.pi, n, endpoint=False); w = np.radians(om_deg)
    nu = true_anomaly(M[None, :], 2*np.pi, np.minimum(e, 0.95)[:, None], 0.0)
    return np.max(np.abs(np.cos(nu + w[:, None]) + e[:, None]*np.cos(w)[:, None]), axis=1)

def lr_v2(Y, c):
    QG, NG = DC.QG, DC.NG; lq = QG**NG; f = lq/(1+lq)
    M1 = Y.m1.values[:, None]/(1+lq)**(1/NG); M2 = QG*M1
    e = Y.eccentricity.fillna(0).values
    K = K_sum_kms(M1, M2, Y.period.values[:, None]/365.25, np.minimum(e, 0.95)[:, None], Y.inc.values[:, None])
    pavg = DC.phase_avg(e, Y.om.values); smax = maxsep_shape(e, Y.om.values)
    W = DC.q_weights(Y.dm.values, Y.sig.values)
    sb2 = (lq[None, :] >= LMIN) & (K*smax[:, None] >= DVMAX)
    Wt = np.where(sb2, 0.0, W); s = Wt.sum(1, keepdims=True)
    fallback = np.zeros_like(W); fallback[np.arange(len(Y)), np.argmin(np.where(sb2, np.inf, 0) + lq[None, :]*0 + (K*smax[:, None]), axis=1)] = 1.0
    Wt = np.where(s > 0, Wt/np.where(s > 0, s, 1), fallback)
    dv2 = np.minimum(K**2*pavg[:, None], DVMAX**2)
    med, sig = Y.vb_med.values, Y.vb_sig.values; sd = np.sqrt(sig**2 + Y.vbroad_error.fillna(0).values**2)
    vpred = np.sqrt(med[:, None]**2 + c*f*(1-f)*dv2)
    lt = logsumexp(np.log(np.clip(Wt, 1e-300, None)) + norm.logpdf(Y.vbroad.values[:, None], vpred, sd[:, None]), axis=1)
    return lt - norm.logpdf(Y.vbroad.values, med, sd)

def main():
    X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
    m = (X.label >= 0) & np.isfinite(X.VB) & (X.vbroad_nb_transits >= 5) & (X.vb_sig > 0)
    Y = X[m].reset_index(drop=True); tr = Y.source_id.str.strip().map(lambda z: sum(int(ch) for ch in z) % 2 == 0).values; te = ~tr   # deviation 12: digit-sum parity
    out = {'n_train': int(tr.sum()), 'n_test': int(te.sum()), 'train_auc_by_c': {}}
    for c in CGRID:
        L = lr_v2(Y[tr], c); out['train_auc_by_c'][str(c)] = DC.auc(L, Y.label.values[tr])
    c_star = max(CGRID, key=lambda c: out['train_auc_by_c'][str(c)]); out['c_star'] = c_star
    T = Y[te].reset_index(drop=True); y = T.label.values
    L = lr_v2(T, c_star); S1v2 = T.CMDLR.values + L; naive = T.B2.values + T.VB.values
    out['V1_vbLR_v2_auc'] = [DC.auc(L, y)] + DC.auc_ci(L, y); out['V1_pass'] = out['V1_vbLR_v2_auc'][1] > 0.5
    out['S1v2_auc'] = [DC.auc(S1v2, y)] + DC.auc_ci(S1v2, y)
    out['V2_dAUC_S1v2_minus_B2'] = DC.dauc_ci(S1v2, T.B2.values, y); out['V2_pass'] = out['V2_dAUC_S1v2_minus_B2'][1] > 0
    out['V3_dAUC_S1v2_minus_naive'] = DC.dauc_ci(S1v2, naive, y); out['V3_pass'] = out['V3_dAUC_S1v2_minus_naive'][1] > 0
    out['test_reference'] = {'B2': DC.auc(T.B2.values, y), 'VB': DC.auc(T.VB.values, y), 'naive': DC.auc(naive, y), 'S1_v1': DC.auc(T.S1.values, y),
                             'vbLR_v1': DC.auc(T.S1.values - T.CMDLR.values, y)}
    json.dump(out, open('../results/vbroad_v2.json', 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))

if __name__ == '__main__':
    main()
