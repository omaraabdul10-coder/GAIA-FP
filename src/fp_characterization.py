"""
fp_characterization.py: independent characterisation of REAL false-positive-type systems (EXPLORATORY, DR3, 6 Nov 2026).

Labels are Gaia's own dynamics (rho = a0 sin i / a1 sin i, H10 rules): luminous companion (impostor type) vs dark-consistent.
They use neither the CMD nor vbroad, so the CMD/vbroad/RUWE properties below are independent of how the labels were made.
Main question: how do real stellar binaries MASQUERADE as substellar companions? An astrometry-only analysis assumes a dark
companion and infers m2_dark from the photocentre a0; for a luminous companion a0 shrinks by (B - beta)/B, so m2_dark is too small.
"""
import json, numpy as np, pandas as pd
import mechanism as M
MJ = 9.546e-4

def main():
    X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
    X = M.physics(X)
    Pyr = X.period/365.25; arel = ((X.m1 + X.m2dyn)*Pyr**2)**(1/3)
    X['m2_true_MJ'] = X.m2dyn/MJ
    X['m2_dark_MJ'] = (X.a0/X.parallax)/((X.m1*Pyr**2)**(1/3))*X.m1/MJ      # first-order dark-companion mass (frozen candidate rule)
    L = X[X.label == 1]; Dk = X[X.label == 0]
    q = lambda s, p: float(np.nanpercentile(s, p))
    def summ(S):
        return dict(n=len(S), q_median=q(S.m2dyn/S.m1, 50), light_fraction_median=q(S.beta, 50), P_days_median=q(S.period, 50),
                    e_median=q(S.eccentricity, 50), dM_G_median=q(S.dm, 50), frac_overluminous_dm_lt_m0p3=float((S.dm < -0.3).mean()),
                    ruwe_median=q(S.ruwe, 50), frac_ruwe_gt_1p4=float((S.ruwe > 1.4).mean()),
                    vbroad_median=q(S.vbroad[S.vbroad_nb_transits >= 5], 50), m2_true_MJ_median=q(S.m2_true_MJ, 50),
                    m2_dark_MJ_median=q(S.m2_dark_MJ, 50))
    out = dict(status='EXPLORATORY, DR3 development data', labels='dynamical (rho), independent of CMD and vbroad',
               luminous_impostor_type=summ(L), dark_consistent=summ(Dk))
    mask = (L.m2_dark_MJ < 80) & (L.m2_true_MJ > 80)
    out['masquerade'] = dict(
        n_luminous=len(L), n_would_look_substellar=int((L.m2_dark_MJ < 80).sum()), n_look_substellar_but_true_stellar=int(mask.sum()),
        underestimate_factor_median=q(L.m2_true_MJ/L.m2_dark_MJ, 50),
        note='luminous-companion binaries whose astrometry-only (dark-companion) mass is < 80 MJ although the true companion is a star')
    out['masquerade_by_light_fraction'] = [dict(beta=f'{a}-{b}', n=int(((L.beta >= a) & (L.beta < b)).sum()),
                                                median_underestimate=q((L.m2_true_MJ/L.m2_dark_MJ)[(L.beta >= a) & (L.beta < b)], 50))
                                           for a, b in ((0, .05), (.05, .1), (.1, .2), (.2, .5))]
    json.dump(out, open('../results/fp_characterization.json', 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))

if __name__ == '__main__':
    main()
