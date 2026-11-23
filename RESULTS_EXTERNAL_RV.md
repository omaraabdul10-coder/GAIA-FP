# External ground-based RV validation: results (exploratory)

Plan: `EXTERNAL_RV_VALIDATION_PLAN.md` (SHA-256 965f2784…) and amendment 1 (af03b95d…), both hashed before any data were
fetched or labels computed. Code: `src/external_rv_validation.py`. Output: `results/external_rv_validation.json`.
Sealed ids were removed before every cross-match.

## What was searched
| Source | Non-sealed candidates matched |
|---|---|
| SB9 (Pourbaix et al. 2004) | 5 systems |
| SBX (Merle et al. 2026, successor of SB9) | the same 5 systems, no new one |
| NASA Exoplanet Archive (RV masses, d < 520 pc, P > 20 d) | 0 |

Ground-based RV orbits exist for very few of the 2102 candidates. The obvious known systems are in the sealed set.

## E1 and E2: NOT_CONDUCTED
4 positives and 0 negatives, below the registered minimum (5 + 5). No AUC and no baseline comparison can be computed.

## E3: independent characterisation of real false positives
| SB9 | Gaia P (d) | Catalogue m2 (MJ) | RV K1 (km/s) | K80 (km/s) | m2 from RV, Gaia i (MJ) | Ratio | Double-lined | GAIA-FP P_impostor | GAIA-FP verdict |
|---|---|---|---|---|---|---|---|---|---|
| 3744 | 145.6 | 77.7 | 20.10 | 3.13 | 745 | 9.6× | yes | 0.999 | likely impostor |
| 3807 | 95.5 | 45.7 | 6.79 | 3.08 | 229 | 5.0× | yes | 0.985 | likely impostor |
| 2550 | 297.5 | 78.7 | 4.98 | 2.44 | 172 | 2.2× | no | 0.397 | ambiguous, follow-up |
| 2203 | 268.3 | 68.7 | 2.91 ± 0.24 | 2.63 | 89 | 1.3× | no | 0.594 | ambiguous, follow-up |
| 2188 | 1009 | 16.1 | — | — | — | — | — | 0.062 | excluded: SB9 period 3977 d is a different (outer) orbit |

Reading the table honestly:
- All four period-matched systems are stellar companions, confirmed by ground-based spectroscopy that does not use Gaia.
  Their median true / catalogue mass ratio is **3.6×**, consistent with the 4.0× [3.5, 5.5] found from Gaia's combined orbits.
- GAIA-FP rated none of them "likely substellar". The two double-lined systems (bright companion, the case the
  light-blending model is built for) get 0.999 and 0.985.
- The two single-lined systems get "ambiguous, follow-up needed", with scores in the lowest ~3% of the candidate list.
  2203 is barely stellar (89 MJ, K1 is ~1σ above K80). 2550 has a faint companion, and faint companions are
  exactly the case where Gaia-only light blending gives little signal. This is a real limitation, not a success.
- 2188 may be a hierarchical triple (Gaia 1009 d, ground-based 3977 d). It was excluded by the period rule.
  A second explanation should be checked before any telescope time is spent on it: Gaia's 1009 ± 138 d period is
  close to the DR3 baseline (~1038 d), so the "1009 d dark companion" could be a partial fit of the 3977 d stellar
  orbit seen over too short a window. This star (Gaia DR3 1878822452815621120) is the only "likely substellar"
  Shamakhy target. Latham et al. (2002) fitted 79 CfA velocities over 4875 d with rms 0.45 km/s and found only the
  3977 d orbit; comparing that velocity curve with the K_ast = 0.41 km/s expected from the 1009 d solution would
  show whether the short orbit is real.

n = 4 is too small for any statistical claim. This is a descriptive check only.

## Note added 22 Nov 2026: effect of line blending on the K rule
`SHAMAKHY_FOLLOWUP_PLAN.md` (11 Nov 2026) points out that when the two stars' lines are blended, the measured
velocity centroid moves with K_sum (B − f), close to the photocentre amplitude, and not with the true K1 = K_sum B.
A blended single-lined K1 is therefore a lower bound on the true K1. Consequences for this analysis:
- The impostor rule "K1 ≥ K80" can only err on the conservative side: a measured K1 above K80 means the true K1 is
  above K80 too. The two single-lined positives (2550, 2203) stay valid; the two double-lined ones are unaffected.
- m2_RV in the table is likewise a lower bound for the single-lined systems, so the 3.6× median ratio is conservative.
- A "substellar" label from K1 < K80 would NOT be reliable for a blended system. No such label occurred here.
This note changes no number above.
