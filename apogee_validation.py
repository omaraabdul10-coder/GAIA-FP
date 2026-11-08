"""
apogee_validation.py: independent RV test with APOGEE DR17 multi-visit spectra (EXPLORATORY, DR3, 6 Nov 2026).
Data: VizieR III/286/catalog (CfA mirror), stars with >= 2 visits; Gaia EDR3 id = DR3 id. File realdata/external/apogee_dr17_multivisit.csv.
(A) H10 systems: do APOGEE's own spectra see the companion more often for rho-luminous than for rho-dark systems?
    Ncomp >= 2 (APOGEE detects a second set of lines) is an independent, spectroscopic sign of a luminous companion.
(B) DR3 substellar candidates: the RV scatter of a star with a companion <= 80 MJ cannot exceed K80 (1 + e), K80 being the
    semi-amplitude for an 80 MJ companion with the candidate's own P, e, i, M. A star with s_HRV > K80 (1 + e) + 1 km/s is
    'RV-incompatible with a substellar companion' -> an independent impostor label. Then: does the frozen DR3 P_impostor rank them?
"""
import json, numpy as np, pandas as pd
from rvs_phase_test import K_sum_kms
from dr4_evaluate import auc, strat_boot
from blind_eval import clopper_pearson
MJ = 9.546e-4

def main():
    A = pd.read_csv('../realdata/external/apogee_dr17_multivisit.csv', dtype={'source_id': str})
    out = dict(status='EXPLORATORY (DR3 development, external APOGEE DR17 data)', n_apogee_multivisit=len(A))
    H = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str}); H = H[H.label >= 0].merge(A, on='source_id')
    L, D = H[H.label == 1], H[H.label == 0]
    k1, n1, k0, n0 = int((L.Ncomp >= 2).sum()), len(L), int((D.Ncomp >= 2).sum()), len(D)
    out['A_H10_SB2_detection'] = dict(luminous=[k1, n1, clopper_pearson(k1, n1)], dark=[k0, n0, clopper_pearson(k0, n0)],
                                      median_s_HRV_luminous=float(L.s_HRV.median()) if n1 else None, median_s_HRV_dark=float(D.s_HRV.median()) if n0 else None)
    C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str}).merge(A, on='source_id')
    e = C.e.clip(0, 0.95).values; M = C.M.values
    K80 = K_sum_kms(M, 80*MJ*np.ones_like(M), C.P.values, e, C.inc.values) * (80*MJ)/(M + 80*MJ)   # primary's K for an 80 MJ companion
    C['K80'] = K80; C['rv_incompatible'] = C.s_HRV > K80*(1 + e) + 1.0
    C['rv_quiet'] = (C.s_HRV < 0.5) & (C.Nvis >= 3)
    out['B_candidates'] = dict(n_with_apogee=len(C), n_rv_incompatible_with_substellar=int(C.rv_incompatible.sum()),
                               n_rv_quiet=int(C.rv_quiet.sum()), K80_median_kms=float(np.median(K80)) if len(C) else None)
    y = C.rv_incompatible.astype(int).values
    if y.sum() >= 3 and (y == 0).sum() >= 3:
        for s in ('P_impostor', 'log_lr'):
            bs = strat_boot(lambda i: auc(C[s].values[i], y[i]), y, n=2000)
            out['B_candidates'][f'auc_{s}_vs_rv_incompatible'] = [auc(C[s].values, y), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        b2 = -C.dm.values/C.sig_cmd.values; bs = strat_boot(lambda i: auc(b2[i], y[i]), y, n=2000)
        out['B_candidates']['auc_B2_vs_rv_incompatible'] = [auc(b2, y), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        for v in ('likely_impostor', 'ambiguous_followup_needed', 'likely_substellar'):
            m = C.verdict == v; out['B_candidates'][f'rv_incompatible_rate_{v}'] = [int(C.rv_incompatible[m].sum()), int(m.sum())]
    C[['source_id', 'P', 'e', 'M', 'Nvis', 's_HRV', 'e_HRV', 'Ncomp', 'K80', 'rv_incompatible', 'rv_quiet', 'P_impostor', 'verdict']].to_csv('../results/apogee_candidates.csv', index=False)
    json.dump(out, open('../results/apogee_validation.json', 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))

def h16(catalogue, idmap, apogee='../realdata/external/apogee_dr17_multivisit.csv', min_pos=10, min_neg=10):
    """v0.6 A30, H16 (secondary): on DR4 candidates (ids mapped to DR3/EDR3 for APOGEE), label = RV-incompatible with a
    substellar companion [s_HRV > K80(1+e) + 1 km/s]; negatives = all other candidates with >= 2 APOGEE visits (NOT a claim
    that they are substellar). Statistic: AUC of P_impostor (v3.2), stratified bootstrap 2000, seed 7; pass if lower bound > 0.5.
    Applicability: >= 10 positives and >= 10 negatives, else NOT_CONDUCTED:BELOW_MIN_N."""
    A = pd.read_csv(apogee, dtype={'source_id': str})
    C = pd.read_csv(catalogue, dtype={'source_id': str}); C['source_id'] = C.source_id.str.strip()
    Mp = pd.read_csv(idmap, dtype=str); Mp = Mp[Mp.angular_distance_arcsec.astype(float) <= 1.0].sort_values('angular_distance_arcsec').drop_duplicates('dr4_source_id')
    C = C.merge(Mp[['dr4_source_id', 'dr3_source_id']], left_on='source_id', right_on='dr4_source_id').merge(A, left_on='dr3_source_id', right_on='source_id', suffixes=('', '_apo'))
    e = C.e.clip(0, 0.95).values; M = C.M.values
    K80 = K_sum_kms(M, 80*MJ*np.ones_like(M), C.P.values, e, C.inc.values)*(80*MJ)/(M + 80*MJ)
    y = (C.s_HRV > K80*(1 + e) + 1.0).astype(int).values
    out = dict(n=len(C), n_pos=int(y.sum()), n_neg=int((y == 0).sum()))
    if y.sum() < min_pos or (y == 0).sum() < min_neg: out['status'] = 'NOT_CONDUCTED:BELOW_MIN_N'; return out
    s = C.P_impostor.values; bs = strat_boot(lambda i: auc(s[i], y[i]), y, n=2000)
    out.update(status='CONDUCTED', auc=auc(s, y), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
               pass_=bool(np.percentile(bs, 2.5) > 0.5))
    return out

if __name__ == '__main__':
    main()
