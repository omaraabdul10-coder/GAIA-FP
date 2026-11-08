# GAIA-FP — B2 provenance and independent SB2 crossmatch audit

Date: 2 November 2026

## Question
Does the strong B2–H10 association represent an independent validation result, and does B2/GAIA-FP identify independently catalogued SB2 impostors in the 2,102-candidate list?

## 1. H10 label provenance: what is and is not leakage

The inspected H10 implementation (`dark_companion.py`) defines the H10 class from the astrometric ratio

`rho = (a0 / parallax) * sin(inclination) / hypot(C, H)`,

where `a0, inclination` are derived from Thiele–Innes A/B/F/G and C/H are the other Thiele–Innes terms. The label is assigned from the Monte-Carlo interval for rho relative to 0.9. **B2 is not directly used in this rho-label formula.** B2 is `-dm/sigma_CMD`, with `dm = M_G - main-sequence ridge`.

However, the H10 sample is not independent of CMD information: before labels are created, the code restricts colour to the calibrated ridge range, requires `dm > -2`, and requires a finite positive primary-mass estimate (which may itself be derived from `M_G`). Thus B2 shares the CMD quantities used in sample eligibility and is being evaluated inside a CMD-selected population. This is a selection/construct coupling, not proof of direct target leakage.

**Interpretation:** the round-2/round-3 B2 AUCs against H10 labels are descriptive associations with the H10 dynamical label. They are not an independent external validation, and the 46/31/1,849 strata are subdivisions of the same 1,926-object cohort. The H10 B2 association is physically plausible because CMD overluminosity is expected to track luminous companions, but it must not be sold as a new independent discovery.

## 2. Independent survey-SB2 crossmatch on the 2,102 candidate list

The 2,102-row candidate table was joined one-to-one by `source_id` to the recomputed crossmatch table. There were no duplicate candidate IDs. The recomputed flags contain **16 unique SB2 matches**: APOGEE 13, GALAH 2, LAMOST 1. These are independent catalogue flags; the scoring code does not use these SB2 flags as input. Literature describes survey SB2 detections as direct evidence of two visible spectral components, while non-detection is not equivalent to a true single-star/compact-companion label.

### Results among the 16 SB2-positive matches

- **14/16 (87.5%)** were assigned `likely_impostor` by the frozen candidate score (P_impostor ≥ 0.85).
- **2/16 (12.5%)** were `ambiguous_followup_needed`.
- **0/16** were assigned `likely_substellar`.
- **15/16** had B2 > 0 (CMD-overluminous direction).
- Median B2 among the 16 SB2 matches: **2.399**.
- Median B2 among the other 2,086 candidates without an SB2 catalogue match: **0.935**.
- Median difference (SB2 minus unmatched): **1.464**; bootstrap 95% percentile interval: **[0.261, 2.142]**.
- Mann–Whitney one-sided p-value for higher B2 in the SB2 group: **0.00063**; rank-sum permutation p-value: **0.00045** (20,000 permutations; seed 20261102).

For orientation only, the rank statistic corresponds to an SB2-versus-unmatched reference AUC of **0.734**, bootstrap 95% interval **[0.606, 0.845]**. This is **not a conventional validated AUC**, because the 2,086 unmatched objects are unlabelled, not confirmed negatives. The permutation and bootstrap calculations compare catalogue-positive SB2s with the unmatched reference pool; they do not establish specificity or population-level precision.

The 14/16 recovery proportion has a Clopper–Pearson 95% interval of **[0.617, 0.984]**. This interval is wide because the positive sample is small.

### By survey

- APOGEE: 13 matches (B2 values range -0.133 to 5.273).
- GALAH: 2 matches (B2 values 2.335, 3.420).
- LAMOST: 1 match (B2 1.486).

The catalogue mix is dominated by APOGEE, so cross-survey replication is not established. GALAH and LAMOST counts are too small for separate inference.

## 3. What is genuinely positive

A defensible positive finding is: **in the 2,102-object candidate list, the frozen GAIA-FP CMD-based score flagged 14 of 16 independently crossmatched survey-SB2 systems as likely luminous-binary impostors, with the remaining two abstained as ambiguous; none was classified as likely substellar.** The B2 score was also shifted upward among these SB2-positive systems relative to the unmatched candidate pool.

This is a small-sample, positive-control validation of the impostor-rejection side of the pipeline. It is not validation of compact companions, not an estimate of specificity, and not a full H7 AUC test. The unmatched candidates must remain unlabelled.

## 4. Next decisive test

The next test should add a matched comparison set of candidates with documented survey coverage and at least three usable epochs but no SB2 flag, while retaining the possibility of missed SB2s. Then report (i) SB2 recall, (ii) lower-bound AUC against this coverage-defined reference set, (iii) survey-specific results, and (iv) sensitivity to crossmatch radius/epoch propagation. A truly independent compact-companion validation still requires positive substellar/RV-confirmed controls.

## 5. Reproducibility

Inputs: `dr3_candidates_scored.csv`; `sb2_crossmatch_recomputed_2102.csv` from the GAIA-FP epoch/RV audit bundle. Join key: Gaia `source_id`. B2 recomputed as `-dm/sig_cmd`. Bootstrap: 10,000 stratified resamples of 16 SB2-positive and 2,086 unmatched objects, seed 20261102. Permutation: 20,000 random assignments preserving group size, seed 20261102.

## References for interpretation

- Bashi et al. (2022), Gaia DR3 spectroscopic orbit validation using LAMOST and GALAH RVs; discusses limitations of sparse RV confirmation and independent survey evidence.
- GALAH DR3 catalogue documentation, which distinguishes single-entry main catalogue from per-observation catalogue and describes its RV/spectroscopic products.
