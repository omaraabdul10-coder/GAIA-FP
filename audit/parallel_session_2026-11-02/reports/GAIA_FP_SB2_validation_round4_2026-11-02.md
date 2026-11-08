# GAIA-FP — SB2 validation robustness and ranking audit (Round 4)

Date: 2 November 2026

## Scope

Re-audited the 2,102-candidate DR3 table, the 16 independent survey-SB2 crossmatches, and the five score variants in `ablation_dr3_candidate_scores.csv`. The SB2-positive group contains 13 APOGEE, 2 GALAH, and 1 LAMOST matches. The remaining 2,086 candidates are **unlabelled**, not confirmed negatives.

## 1. Provenance: SB2 labels are appended after scoring

In `dr3_study.py`, the project first computes candidate features and calls `D.score(X, rvs=None, seed=0)`. Only afterwards does it call `build_labels(...)` and merge the survey SB2 flags into the scored table. Thus the SB2 flags are not direct inputs to the score-generation step in this implementation. This supports an independent positive-control interpretation, subject to the quality of the crossmatches and the frozen score code.

## 2. APOGEE positional-match sensitivity

Recomputed the APOGEE positional match after the project’s 2016.0-to-2000.0 proper-motion propagation. The 13 unique APOGEE matches remain exactly the same at radii 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, and 5.0 arcsec. There are zero ambiguous matches at all these radii. The nearest separations range from about 0.010 to 0.204 arcsec.

This is strong positional robustness for these 13 matches; it does not by itself prove that every catalogue row is a physically associated SB2 rather than a survey-level classification or catalogue contamination.

## 3. Threshold audit: the 14/16 headline is not enough

The original full-model output has 1,911/2,102 candidates (90.9%) with `P_impostor >= 0.85`, and its verdict distribution is 1,911 `likely_impostor`, 174 `ambiguous_followup_needed`, and 17 `likely_substellar`. It therefore recovers 14/16 known SB2 positives at the 0.85 threshold, but it also places almost the entire candidate list above that threshold. With 2,086 unlabelled objects, specificity cannot be computed; nevertheless, this threshold is too permissive to be a useful shortlist on its own.

The full-model positive–unlabelled proxy AUC is 0.643 (20,000 paired stratified bootstrap 95% interval approximately 0.488–0.785). The interval includes 0.5. This weakens any claim that the full score robustly ranks SB2 positives above the unlabelled pool.

## 4. Alternative score ranking

The fixed-prior CMD-marginal variant is a more promising *ranking candidate* than the current full EM score in this small positive-control audit:

| Score variant | PU proxy AUC | 95% bootstrap interval | SB2 in top 5% | top 10% | top 20% | SB2 above 0.85 | all candidates above 0.85 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FULL_joint_EM_C1 | 0.643 | [0.488, 0.784] | 3/16 | 4/16 | 5/16 | 14/16 | 1911/2,102 |
| joint_fixed_prior_pi0.3 | 0.722 | [0.589, 0.837] | 3/16 | 4/16 | 8/16 | 4/16 | 246/2,102 |
| CMD_marginal_EM_C1 | 0.738 | [0.635, 0.837] | 2/16 | 4/16 | 7/16 | 16/16 | 1720/2,102 |
| CMD_marginal_fixed_prior_pi0.3 | 0.733 | [0.610, 0.844] | 3/16 | 5/16 | 10/16 | 4/16 | 184/2,102 |
| B2_CMD_only | 0.694 | [0.571, 0.810] | 4/16 | 6/16 | 6/16 | 6/16 | 332/2,102 |

The fixed-prior CMD-marginal variant has AUC 0.733 versus 0.643 for the full model; the paired bootstrap difference (variant minus full) is +0.089, 95% interval approximately [+0.002, +0.188]. Its top 20% contains 10/16 SB2 positives versus 5/16 for the full model. This is a candidate for further testing, not a final model selection: it is a post-hoc comparison on the same 16 positive controls, and the 2,086 comparison objects remain unlabelled.

The CMD-marginal EM variant reaches 16/16 SB2 positives at the 0.85 threshold, but 1,720/2,102 candidates also exceed 0.85. That is not useful discrimination. The fixed-prior variant avoids that extreme threshold saturation, but still needs independent validation and calibration.

## 5. Recommended next experiment

Use the fixed-prior CMD-marginal score as a **pre-specified challenger**, not as a replacement already proven superior. On a new, untouched sample: (i) freeze its formula and threshold/ranking budget; (ii) build a coverage-defined reference group with documented APOGEE/GALAH/LAMOST observations; (iii) obtain independent multi-epoch SB1/SB2 labels where possible; (iv) report survey-specific recall, precision only where negatives are genuinely confirmed, and calibration; (v) keep SB2 non-detections unlabelled unless the survey's sensitivity and coverage support a negative label.

## 6. Scientific interpretation

A positive SB2 crossmatch is evidence for a luminous/spectroscopic binary contaminant, not evidence for a compact dark companion. Gaia and external-survey documentation also emphasize that spectroscopic-binary identification depends on the number and timing of observations and on whether both spectral components are resolved. Bashi et al. (2022) caution that even an RV measurement consistent with a Gaia orbit does not generally validate the full orbit; GALAH DR3 notes that its limited short-timescale repeat observations can miss many binaries.

## Verdict

- **Robust:** all 13 APOGEE matches persist over a broad 0.5–5 arcsec radius sweep; the SB2 labels are appended after scoring in the inspected code.
- **Not robust enough:** 14/16 at P>=0.85 is paired with 90.9% of all candidates above that threshold; full-model PU AUC interval includes 0.5.
- **Promising new direction:** fixed-prior CMD-marginal ranking improves the SB2 positive–unlabelled proxy and places 10/16 positives in the top 20%, but this remains exploratory and requires an untouched coverage-defined test set.

## Sources

- Bashi et al. (2022), *Gaia Spectroscopic Orbits Validated with LAMOST and GALAH Radial Velocities*, MNRAS: https://academic.oup.com/mnras/article/517/3/3888/6761415
- Gaia DR3 NSS input filtering documentation: https://gea.esac.esa.int/archive/documentation/GDR3/Data_analysis/chap_cu4nss/sec_cu4nss_intro/ssec_cu4nss_intro_inputfiltering.html
- GALAH DR3 caveats on binary detection and limited repeat observations: https://www.galah-survey.org/dr3/caveats/
