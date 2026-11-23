"""Follow-up target list for the Shamakhy Astrophysical Observatory 2-m telescope (lat 40.77 N), from the FROZEN DR3
predictions (OSF TBJGY). Exploratory planning aid; it does not change any registered test. Sealed ids are dropped first.
For each candidate: the RV semi-amplitude if the companion has its catalogue (dark-companion) mass, K_sub, and if it
were the lightest possible star, 80 MJ, K80. An impostor must show K >= ~K80; a true substellar companion K ~ K_sub."""
import numpy as np, pandas as pd
C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str})
R = pd.read_csv('../realdata/dr3_candidates.csv', dtype={'source_id': str}).drop_duplicates('source_id')[['source_id', 'ra', 'dec']]
S = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype=str).source_id.str.strip())
D = C.merge(R, on='source_id'); D = D[~D.source_id.isin(S)]
MJ = 9.546e-4
def K(m2_MJ):
    m2 = m2_MJ*MJ; P_yr = D.P/365.25
    return 28.4329*(m2/MJ)*np.sin(np.radians(D.inc))*(D.M + m2)**(-2/3)*P_yr**(-1/3)/np.sqrt(1 - D.e.clip(0, .95)**2)/1000   # km/s
D['K_sub_kms'] = K(D.mfit); D['K80_kms'] = K(80.0); D['K_4x_kms'] = K(4.0*D.mfit)   # 4x = median true/catalogue mass of impostors (candidate_mass_bias.json)
D['max_alt_deg'] = 90 - abs(40.77 - D.dec)
lst_midnight = lambda month: (6.0 + 2.0*((month - 12) % 12)) % 24          # LST at local midnight, ~21st of each month
D['best_month'] = [min(range(1, 13), key=lambda m: min(abs(r/15 - lst_midnight(m)), 24 - abs(r/15 - lst_midnight(m)))) for r in D.ra]
ok = (D.max_alt_deg >= 30) & (D.G <= 11.0)
cols = ['source_id', 'ra', 'dec', 'G', 'P', 'e', 'mfit', 'P_impostor', 'verdict', 'K_sub_kms', 'K80_kms', 'K_4x_kms', 'max_alt_deg', 'best_month']
sub = D[ok & (D.verdict == 'likely_substellar')].sort_values('G')[cols]
imp = D[ok & (D.verdict == 'likely_impostor')].assign(r=lambda x: x.K80_kms).sort_values(['G'])[cols].head(15)
out = pd.concat([sub.assign(group='A_likely_substellar'), imp.assign(group='B_likely_impostor_brightest')])
for c in ['ra', 'dec']: out[c] = out[c].round(4)
for c in ['G', 'P', 'e', 'mfit', 'P_impostor', 'K_sub_kms', 'K80_kms', 'K_4x_kms', 'max_alt_deg']: out[c] = out[c].astype(float).round(3)
out.to_csv('shamakhy_targets.csv', index=False)
print(len(sub), len(imp)); print(out[['group', 'G', 'P', 'mfit', 'K_sub_kms', 'K_4x_kms', 'best_month']].round(2).to_string(index=False))
