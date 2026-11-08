# GAIA-FP — Round 5: SB2 ranking enrichment and survey-stratified audit

Date: 2 November 2026

## Question
Does the Round-4 fixed-prior CMD-marginal challenger genuinely concentrate the 16 external SB2 positive controls near the top of the 2,102-candidate ranking, and is that effect visible across survey sources?

## Data and method
Used the frozen 2,102-row ablation score table and recomputed SB2 crossmatch table from the epoch/RV completion bundle. Positive controls: 13 APOGEE, 2 GALAH, 1 LAMOST; 2,086 objects without an SB2 match remain **unlabelled**, not verified negatives. For each of five score variants, ranked all candidates and counted SB2 controls in the top 20% (421 objects). Compared this count with a random-ranking hypergeometric reference. Holm correction was applied across the five model-specific top-20 tests. Survey-stratified AUCs are explicitly PU proxy statistics, not conventional validated AUCs.

## 1. Top-20% enrichment

| Score | SB2 in top 20% | Expected under random ranking | Enrichment | Nominal p | Holm p (5 models) |
|---|---:|---:|---:|---:|---:|
| FULL_joint_EM_C1 | 5/16 | 3.20 | 1.56× | 0.201896 | 0.201896 |
| joint_fixed_prior_pi0.3 | 8/16 | 3.20 | 2.50× | 0.006856 | 0.027426 |
| CMD_marginal_EM_C1 | 7/16 | 3.20 | 2.18× | 0.026362 | 0.079085 |
| CMD_marginal_fixed_prior_pi0.3 | 10/16 | 3.20 | 3.12× | 0.000235 | 0.001177 |
| B2_CMD_only | 6/16 | 3.20 | 1.87× | 0.081371 | 0.162741 |

The CMD-marginal fixed-prior challenger places 10/16 SB2 positives in the top 421 candidates, versus 5/16 for the full model. Its top-20 enrichment remains unusual under the simple random-ranking null after correction across the five tested score variants (Holm-adjusted p ≈ 0.00118). This is evidence of positive-control concentration, **not** evidence of specificity or population-wide precision, because the comparison pool contains unlabelled objects.

## 2. Which surveys drive the result?

For the CMD-marginal fixed-prior challenger, the top 20% contains 8/13 APOGEE positives, 2/2 GALAH positives, and 0/1 LAMOST positives. For the full model, the corresponding counts are 4/13, 1/2, and 0/1. Thus the observed improvement is principally present among APOGEE positives; GALAH has only two objects and LAMOST one, so no survey-generalization claim is justified.

Among APOGEE positives compared with the 2,086 unlabelled pool, the positive–unlabelled proxy AUCs are: full model 0.658; CMD-marginal fixed-prior 0.708; B2-only 0.707. These are modest ranking differences, not strong separation. GALAH and LAMOST proxy AUCs are extremely unstable at n=2 and n=1.

## 3. Interpretation and limitations

- The fixed-prior CMD-marginal score is a promising *candidate ranking* for follow-up, not a validated replacement model.
- The top-20 result is post-hoc: the variants were explored on the same 16 positive controls. Holm correction addresses five model comparisons for this one budget, but does not erase selection bias from the wider analysis process.
- Survey composition is heavily imbalanced (13/16 APOGEE). The result is not replicated adequately across independent surveys.
- The 2,086 unmatched candidates cannot be called SB2-negative. No specificity, precision, false-positive rate, or calibrated probability can be estimated from this design.
- The 16 positives validate only the luminous/spectroscopic-binary impostor-rejection side, not compact dark companions.

## 4. Next decisive experiment

Freeze the CMD-marginal fixed-prior formula and top-20 follow-up budget before acquiring any new labels. Then evaluate on a newly assembled, coverage-defined cohort with independently documented multi-epoch spectroscopy and enough positive and genuinely sensitivity-qualified negative labels. Report survey-specific performance and calibration; retain non-detections as unlabelled when cadence or sensitivity is insufficient.

## Verdict

Round 5 strengthens the case that the CMD-marginal fixed-prior variant concentrates known SB2 controls better than the original full score in this particular dataset. The strongest defensible claim is **positive-control enrichment in a small, predominantly APOGEE sample**. External replication remains necessary before calling it a robust GAIA-FP improvement.
