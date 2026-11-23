"""For every candidate the frozen DR3 model left 'ambiguous', which observation could settle it?
Exploratory planning aid; no registered test changes. Sealed ids are dropped first.

Uses the same physics as SHAMAKHY_FOLLOWUP_PLAN.md (followup/shamakhy_forward.py): a blended impostor moves its
line centroid with about the photocentre amplitude K_ast, so a K amplitude cannot separate the hypotheses.
What separates them is line doubling at the orbit extremes. Under the impostor hypothesis the companion mass ratio
q is solved from Gaia's a0; the two line systems are then K_sum apart at most (K_sum = K1 + K2).

Rule of thumb (no phase planning here, that is done per target in shamakhy_forward.py):
  G <= 11 and K_sum >= 2 x FWHM(R=56000)  -> two ShaFES spectra at the orbit extremes should show doubling
  G <= 11 and K_sum <  2 x FWHM            -> lines will not separate; only a width test is possible
  11 < G <= 13                             -> needs a larger telescope
  G > 13 or no stellar solution            -> Gaia DR4 epoch data only
"""
import numpy as np, pandas as pd
from shamakhy_forward import solve_q_imp, a_rel_AU, K_of, C_KMS

FWHM56 = C_KMS / 56000                                     # ~5.4 km/s instrumental FWHM
C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str})
S = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype=str).source_id.str.strip())
D = C[~C.source_id.isin(S) & (C.verdict == 'ambiguous_followup_needed')].copy()

def k_sum(r):
    q = solve_q_imp(r.a0 * r.d / 1000.0, r.M, r.P)
    return np.nan if q is None else K_of(a_rel_AU(r.M, q, r.P), r.P, r.e, r.inc)

D['K_ast_kms'] = [K_of(r.a0 * r.d / 1000.0, r.P, r.e, r.inc) for r in D.itertuples()]
D['K_sum_imp_kms'] = [k_sum(r) for r in D.itertuples()]
D['deciding_observation'] = np.select(
    [D.G.le(11) & D.K_sum_imp_kms.ge(2 * FWHM56),
     D.G.le(11) & D.K_sum_imp_kms.lt(2 * FWHM56),
     D.G.gt(11) & D.G.le(13) & D.K_sum_imp_kms.notna()],
    ['2 ShaFES spectra at orbit extremes (line doubling)',
     'width test only (lines do not separate)',
     'larger telescope'],
    default='Gaia DR4 epoch data only')
cols = ['source_id', 'G', 'P', 'mfit', 'P_impostor', 'K_ast_kms', 'K_sum_imp_kms', 'deciding_observation']
out = D[cols].sort_values('G')
out.round(3).to_csv('followup_triage.csv', index=False)
print(len(out)); print(out.deciding_observation.value_counts().to_string())
