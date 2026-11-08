"""
erratum_k_units.py: corrected re-analysis for audit finding F6 (31 Oct 2026).

BUG: rvs_phase_test.K_sum_kms(M1, M2, P, e, inc) expects P in DAYS (G = 2.959e-4 AU^3 Msun^-1 day^-2, 1 AU/day = 1731 km/s).
dark_companion.lr_vbroad (H10) and vbroad_v2.lr_v2 pass P/365.25 (YEARS). K_sum is therefore too large by 365.25^(1/3) = 7.148,
and the predicted blend variance by 51x. Not affected: VB, B2, AMRF, JOINT, CMD-LR, mechanism.py (own, correct K), H13.

The frozen files are not edited. This script replaces K_sum_kms inside those two modules by a wrapper that converts the years
they pass back to days, then repeats exactly the registered procedures:
  H10: dark_companion.h10 with c = 1 (primary) and c = 4 (sensitivity), same data, same bootstrap.
  vbroad v2: c chosen on TRAIN from the same grid, TEST evaluated once, same V1-V3 rules.
Outputs go to results/erratum_k_units.json; the registered results files are not touched.
"""
import json, numpy as np, pandas as pd
import rvs_phase_test as R
import dark_companion as DC
import vbroad_v2 as V2

def K_days(M1, M2, P_years, e, inc):            # callers pass years; convert back to the days K_sum_kms expects
    return R.K_sum_kms(M1, M2, np.asarray(P_years)*365.25, e, inc)

def run_h10():
    field_cmd = pd.read_csv(DC.REAL+'dr3_field.csv'); ridge = DC.D.fit_ms_ridge(field_cmd)
    field = pd.read_csv(DC.REAL+'dr3_field_vbroad.csv')
    MGf = field.phot_g_mean_mag + 5*np.log10(field.parallax/100)
    msf = (field.bp_rp >= ridge['color'].min()) & (field.bp_rp <= ridge['color'].max()) & (MGf > np.interp(field.bp_rp, ridge['color'], ridge['ridge']) - 2.0)
    cal = DC.vb_field(field[msf]); d3 = pd.read_csv(DC.REAL+'dr3_astrospectro_all.csv')
    r1, X = DC.h10(d3, field_cmd, cal, c=1.0); r4, _ = DC.h10(d3, field_cmd, cal, c=4.0)
    return r1, r4, X

def run_v2(X):
    m = (X.label >= 0) & np.isfinite(X.VB) & (X.vbroad_nb_transits >= 5) & (X.vb_sig > 0)
    Y = X[m].reset_index(drop=True); Y['source_id'] = Y.source_id.astype(str)
    tr = Y.source_id.str.strip().map(lambda z: sum(int(ch) for ch in z) % 2 == 0).values; te = ~tr
    out = {'n_train': int(tr.sum()), 'n_test': int(te.sum()), 'train_auc_by_c': {}}
    for c in V2.CGRID: out['train_auc_by_c'][str(c)] = DC.auc(V2.lr_v2(Y[tr], c), Y.label.values[tr])
    c_star = max(V2.CGRID, key=lambda c: out['train_auc_by_c'][str(c)]); out['c_star'] = c_star
    T = Y[te].reset_index(drop=True); y = T.label.values
    L = V2.lr_v2(T, c_star); S1v2 = T.CMDLR.values + L; naive = T.B2.values + T.VB.values
    out['V1_vbLR_v2_auc'] = [DC.auc(L, y)] + DC.auc_ci(L, y); out['V1_pass'] = out['V1_vbLR_v2_auc'][1] > 0.5
    out['V2_dAUC_S1v2_minus_B2'] = DC.dauc_ci(S1v2, T.B2.values, y); out['V2_pass'] = out['V2_dAUC_S1v2_minus_B2'][1] > 0
    out['V3_dAUC_S1v2_minus_naive'] = DC.dauc_ci(S1v2, naive, y); out['V3_pass'] = out['V3_dAUC_S1v2_minus_naive'][1] > 0
    out['test_vbLR_v1_auc'] = DC.auc(T.S1.values - T.CMDLR.values, y)
    return out

def main():
    DC.K_sum_kms = K_days; V2.K_sum_kms = K_days      # the fix, applied in memory only
    r1, r4, X = run_h10()
    lab = X.label.values; hv = np.isfinite(X.vbroad) & (X.vbroad_nb_transits >= 5) & np.isfinite(X.vb_med) & (X.vb_sig > 0)
    mv = (lab >= 0) & hv.values; y = lab[mv]
    vbLR = (X.S1 - X.CMDLR).values[mv]
    out = dict(finding='F6: P in years passed to K_sum_kms (expects days); K_sum x7.148 too large',
               H10_corrected_c1={k: r1[k] for k in ('vbroad_subset_auc', 'H10a_dAUC_S1_minus_B2', 'H10a_pass', 'H10b_VB_auc', 'H10b_pass', 'H10c_dAUC_S2_minus_B2')},
               H10_corrected_c4={k: r4[k] for k in ('vbroad_subset_auc', 'H10a_dAUC_S1_minus_B2', 'H10a_pass')},
               physical_vbLR_alone_corrected_c1=[DC.auc(vbLR, y)] + DC.auc_ci(vbLR, y),
               naive_B2_plus_VB=[DC.auc((X.B2 + X.VB).values[mv], y)],
               S1_minus_naive_corrected_c1=DC.dauc_ci(X.S1.values[mv], (X.B2 + X.VB).values[mv], y),
               vbroad_v2_corrected=run_v2(X))
    json.dump(out, open('../results/erratum_k_units.json', 'w'), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))

if __name__ == '__main__':
    main()
