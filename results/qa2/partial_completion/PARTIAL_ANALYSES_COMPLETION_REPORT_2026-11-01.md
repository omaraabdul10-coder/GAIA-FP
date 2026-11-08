# GAIA-FP partial analyses — completion audit (1 Nov 2026)

This addendum completes all computations that can be reproducibly completed from the archived local snapshot. It does not pretend that unavailable remote RV epoch rows were downloaded.

## 1. Independent spectroscopic cross-match quality audit

- 2102 unique scored candidates reconciled exactly to the stored flags.
- LAMOST-MRS SB2: 1 exact Gaia DR3 ID matches.
- GALAH FGK SB2: 2 Gaia DR2 ID matches after the <1000 mas neighbourhood guard.
- APOGEE SB2: 13 unique matches within 2 arcsec after 2016-to-J2000 proper-motion propagation; ambiguous matches: 0.
- Combined unique SB2 positives: 16; multi-survey overlaps: 0.
- The 200-realisation local offset control produced a median 0.0 chance matches (95% empirical range 0.0–0.0). This is a diagnostic, not a formal posterior probability.

### What remains missing for a true epoch-RV cross-match

The present APOGEE/GALAH/LAMOST flags are cross-matches to published SB2 catalogues; they are not a general epoch-by-epoch RV-variability analysis. The official GALAH DR3 archive exposes per-spectrum (678,423-row) spectra and a matched radial-velocity VAC with `sobject_id`, `rv_galah`, uncertainty, HJD/MJD, and RV method flag. The public schema says catalogue joins use `sobject_id`; `rv_galah` is the best-per-spectrum velocity, with method flags identifying GALAH-observed vs Gaia-DR2 fallback. The files were not retrievable from this runtime because external DNS/network resolution failed. The companion `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md` records the exact inputs, filters, and aggregation code contract. No RV variability outcomes are claimed.

## 2. Independent baseline comparisons

- On the 44 historical determined AstroSpectroSB1 objects (42 positive / 2 negative), GAIA-FP AUC is 0.964 [0.905, 1.000], while CMD-only AUC is 0.988 [0.952, 1.000]. The paired GAIA-FP−CMD ΔAUC is -0.024 [-0.071, +0.000]. The two-negative-class limitation makes this AUC comparison unstable.
- On the larger H10 `vbroad` subset (n=1927; 841 luminous / 1086 dark-consistent), the corrected post-unit-fix S1 AUC is 0.776 [0.755, 0.797], against CMD-only B2 0.732 [0.708, 0.754]. The registered S1−B2 paired ΔAUC is +0.044 [+0.033, +0.055].
- But against the stronger simple B2+VB additive baseline (AUC 0.796), corrected S1 is lower: ΔAUC(S1−B2+VB) = -0.019 [-0.031, -0.007]. Therefore the model does not beat this stronger baseline.
- S2 and AMRF show higher corrected AUCs, but both use astrometric a0 information also involved in physical label construction; they remain secondary/shared-input comparisons, not clean independent proof.

## 3. Real-object physical characterization

- The historical 400-draw labels remain 42 impostors, 2 dark-compatible, 51 undetermined.
- The full-draw 50,000-sample sensitivity labels give seeds 0/1/17 respectively: {'impostor': 42, 'dark_compatible': 2, 'undetermined': 51}, {'impostor': 42, 'dark_compatible': 2, 'undetermined': 51}, {'impostor': 41, 'dark_compatible': 2, 'undetermined': 52} (counts shown as impostor/dark-compatible/undetermined).
- 94/95 source labels are stable across all three high-draw seeds. The one unstable source is listed in the machine-readable JSON/CSV.
- Of the 95 physical-validation objects, 1 also appears in the independent SB2 catalogues (LAMOST 1, GALAH 0, APOGEE 0).
- In full-draw seed 0, impostor rule attribution: {'undetermined': 51, 'both_mass_and_rho': 38, 'mass_only': 3, 'dark_compatible': 2, 'rho_only': 1}.
- High-draw seed-0 group medians: impostor-sensitivity group (n=42) rho=0.319, dynamical m2=245.4 MJ, RUWE=1.80; uncertain group (n=51) rho=0.835, m2=82.8 MJ, RUWE=2.00; dark-compatible group (n=2) rho=1.178, m2=58.4 MJ. The n=2 group is descriptive only.
- The object-level export contains all 95 source IDs, historical intervals and labels, 50k seed labels, frozen GAIA-FP posterior/verdict, CMD, RUWE, period and diagnostic rule attribution.

## 4. Real-DR3 component ablation (newly completed)

- A controlled 2×2 ablation was run on the same 2,102-candidate DR3 SB2 positive-unlabelled proxy, with 20,000 paired stratified bootstrap resamples.
- The full frozen model was reconstructed from the archived inputs with maximum absolute posterior difference 7.8×10⁻¹⁶ (numerically exact reproduction).
- Full conditional a0|CMD likelihood + EM-C1 prior: AUC 0.643 [0.488, 0.786].
- Same conditional likelihood + fixed π=0.3 (removing the learned demographic prior): AUC 0.722 [0.586, 0.837]; paired ΔAUC FULL−variant = −0.078 [−0.191, +0.017].
- CMD-marginal likelihood (removing a0-conditioning) + EM-C1: AUC 0.738 [0.634, 0.835]; paired ΔAUC FULL−variant = −0.095 [−0.245, +0.040].
- CMD-marginal + fixed π=0.3: AUC 0.733 [0.609, 0.844]; paired ΔAUC FULL−variant = −0.089 [−0.189, −0.002].
- B2 CMD-only context baseline: AUC 0.694 [0.571, 0.812].
- At the fixed score threshold 0.85, full EM-C1 recalled 14/16 SB2 positives; fixed-prior variants recalled 4/16, while CMD-marginal EM-C1 recalled 16/16. These are recall diagnostics among known SB2 matches, not precision estimates because non-SB2 objects are unlabelled.
- **Interpretation:** on this small SB2 proxy, the learned EM-C1 prior reduces ranking AUC relative to the fixed prior, and removing a0-conditioning does not reduce AUC. This does not prove the simpler variants are universally better: there are only 16 SB2 positives and 2,086 rows are unlabelled, not verified negatives.
- The DR3 epoch-RVS phase feature is not covered by this ablation because per-transit RVS widths were not retrieved. Therefore this is a completed ablation of the available astrometric/CMD likelihood and prior components, not an exhaustive ablation of every planned DR4 component.
- Full results and per-object scores: `ABLATION_DR3_COMPONENT_REPORT_2026-11-01.md`, `ablation_dr3_component_results.json`, and `ablation_dr3_candidate_scores.csv`.

## 5. Guardrails

- Historical frozen outputs were not overwritten.
- The 50,000-draw labels are supplementary precision/sensitivity diagnostics, not replacements for the registered 400-draw output.
- The 95 AstroSpectroSB1 objects are selected and not representative of the entire candidate population.
- No claim is made that the epoch-RV cross-match is finished or that GAIA-FP beats the strongest B2+VB baseline.

## Artifacts

- `results/qa2/partial_completion/rv_crossmatch_audit.json`
- `results/qa2/partial_completion/candidate_survey_crossmatch_audit.csv`
- `results/qa2/partial_completion/astrospectro_characterization.json`
- `results/qa2/partial_completion/astrospectro_95_object_characterization.csv`
- `results/qa2/partial_completion/baseline_comparison_reconciliation.json`
- `results/qa2/partial_completion/ABLATION_DR3_COMPONENT_REPORT_2026-11-01.md`
- `results/qa2/partial_completion/ablation_dr3_component_results.json`
- `results/qa2/partial_completion/ablation_dr3_candidate_scores.csv`
- `tools/qa_audits/run_ablation_dr3.py`
- `tools/qa_audits/complete_partial_analyses.py`
- `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md`
