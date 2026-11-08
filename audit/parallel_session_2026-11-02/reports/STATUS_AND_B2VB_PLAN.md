# GAIA-FP status and B2+VB plan

## Current status

The APOGEE DR17 raw epoch-level audit and exploratory H10 group comparison are complete.

- The 320-entry raw archive manifest verified with zero mismatches. The 20 APOGEE responses contained 622 rows; reconstruction retained 351 accepted visits.
- The reconstructed primary cohort has 46 H10 objects with at least 3 distinct integer-MJD epochs: 18 H10-positive and 28 H10-negative. The separate exactly-2-epoch cohort contains 31 objects (17 positive, 14 negative) and remains exploratory.
- The independent recomputation reproduced all 46 nominal constant-RV chi-square p-values. Forty-two had p<0.05 and 42 remained below BH-FDR q<0.05 across the 46 primary tests. Counts under 0.1 and 0.5 km/s uncertainty floors were 37 and 30.
- The positive versus negative groups did not show a resolved variability difference. Nominal screens were 15/18 versus 27/28 (two-sided Fisher exact p=0.284). Continuous effect estimates had broad bootstrap intervals and non-significant permutation tests.
- Results are conditional on APOGEE targeting, cross-match success, available visits, quality filters, cadence, and measurement errors. The cohort is not a representative sample of all 1,926 H10 objects. Variability screens do not identify a physical cause and are not companion or dark-companion evidence.
- No predictive-value model has been trained. The original H10 source copy remains unchanged.

See `apogee_independent_group_audit_report.md` for methods, caveats, and detailed sensitivity results. `gaia_fp_apogee_independent_group_bundle.zip` contains the reproducibility package.

## B2+VB: current decision

**NO-GO for an incremental predictive-value claim at this stage.** There are only 46 primary APOGEE objects (18 positive, 28 negative), no independent validation sample, and no adequate basis for stable leakage-safe validation. Do not report a tuned AUC or claim that RV features add value over B2+VB from this cohort.

Descriptive analysis of how B2 and VB relate to the observed RV metrics is acceptable if clearly labeled exploratory and if selection and measurement limitations are shown. Such association does not demonstrate prediction, causality, or generalization.

## Recommended next steps

1. **Freeze the analysis definition.** Preserve the current source hashes, cohort rules, RV quality filters, epoch definition, and primary/secondary outcomes before additional comparisons. Keep the exactly-2-epoch sample outside primary inference.
2. **Describe the observed sample.** Tabulate B2 and VB distributions by H10 label and by APOGEE coverage group (3+ epochs, exactly 2, and fewer than 2). Report sample sizes and uncertainty intervals; avoid interpreting the APOGEE subset as population prevalence.
3. **Check measurement and selection structure.** Summarize visit count, distinct-MJD count, time baseline, median RV uncertainty, and SNR alongside B2/VB and label. Identify overlap and imbalance. Any adjusted analysis should be explicitly exploratory because the sample is too small for a reliable multi-covariate model.
4. **Limit confirmatory tests.** If testing B2/VB associations with RV variability, declare one primary endpoint and a small set of hypotheses in advance, use rank-based or permutation methods with effect sizes and intervals, and control multiplicity across the declared family. Treat the 2-epoch and LAMOST results as separate exploratory checks.
5. **Seek independent data before predictive evaluation.** Expand the independently collected multi-epoch sample with comparable measurements and labels, ideally through a prespecified external archive/sample. Record the selection mechanism and harmonize RV quality/error definitions before pooling.
6. **Only then evaluate incremental value.** Lock the B2+VB baseline and any added RV features before validation. Use a leakage-safe split by object/source (and by survey or observing program where feasible), compare paired out-of-sample scores against the baseline, and report uncertainty and calibration. Keep model choice and thresholds separate from the held-out evaluation set.
7. **Maintain a claim boundary.** Even a future predictive association would not prove companions. Physical interpretation requires independent astrophysical validation and consideration of activity, blends, and instrumental or reduction systematics.

## Deliverables

- `apogee_independent_group_audit_report.md` — primary report.
- `apogee_primary_3plus.csv` and `apogee_exploratory_2epoch.csv` — per-object results for the separate cohorts.
- `apogee_h10_group_comparisons.csv` and `apogee_group_detection_test.json` — group contrasts and exact binary-screen comparison.
- `apogee_sensitivity_summary.csv` — uncertainty-floor, outlier, SNR, and minimum-epoch sensitivities.
- `analysis_validation.json`, `SHA256SUMS_followup.csv`, and the reproducibility ZIP — provenance and integrity records.
