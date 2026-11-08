# GAIA-FP — Alternative signal audit (2 Nov 2026)

## Scope
Exploratory re-analysis of the currently available files: `apogee_object_variability_all_h10.csv` (1,926 objects), `apogee_primary_3plus.csv` (46 objects), `apogee_per_object_diagnostics.csv` (1,926 objects), and `dr3_candidates_scored.csv` (2,102 candidates). This is not an independent validation set.

## Main positive empirical result
Among the 46-object primary APOGEE cohort (at least 3 distinct integer-MJD epochs), **30/46 objects (65.2%) remain nominally variable at p < 0.05 even after applying the 0.5 km/s uncertainty-floor sensitivity scenario**. This is a more conservative sensitivity result than the nominal 42/46 detections. It supports the presence of substantial RV variability in a subset of the observed cohort, but it does not identify the physical cause and does not prove compact companions.

The 30 robust-floor detections comprise 12 H10-positive and 18 H10-negative objects. The corresponding 2x2 Fisher exact test gives p=1.0; therefore this variability screen does **not** distinguish the H10 labels in this small cohort.

A follow-up-priority table of those 30 objects is provided in `GAIA_FP_robust_RV_followup_candidates.csv`, including Gaia source ID, H10 label, B2/VB, epoch count, time baseline, RV range, weighted RMS, conservative-floor p-value, and median SNR.

## Important diagnostic: observing coverage dominates the apparent signal
Within the 46 objects, RV range correlates with:
- distinct epoch count: Spearman rho=0.527, p=1.65e-4;
- time baseline: Spearman rho=0.600, p=1.06e-5.

Weighted RMS shows nearly identical relationships (rho=0.527 with epoch count; rho=0.604 with baseline). The conservative-floor p-value is also strongly associated with epoch count (rho=-0.550, p=7.62e-5) and baseline (rho=-0.634, p=2.26e-6). This means longer/more numerous observations make variability easier to detect. It is a major cadence/power confound, not evidence that longer-baseline systems are intrinsically more variable.

## B2/VB alternative check
Across all 1,926 H10 objects, B2 and VB are associated with the H10 label (AUCs reproduced descriptively as 0.732 and 0.755, respectively). In the 46-object APOGEE subset, their apparent label AUCs are 0.887 and 0.815. However, these labels/features are not an independent astrophysical truth set, and the APOGEE subset is selected. They must not be interpreted as independent confirmation of hidden companions.

Repeated stratified 4-fold CV (100 repeats; logistic regression) in the 46-object subset produced mean AUC 0.889 for B2, 0.816 for VB, and 0.895 for B2+VB. The paired mean gain from adding VB to B2 was only 0.0067; the 2.5–97.5 percentile range of fold-level gains was -0.071 to +0.086. This is unstable and does not establish incremental value.

B2 and VB did not show convincing monotonic associations with the RV metrics in the 46-object cohort. For example, B2 vs RV range rho=0.182 (p=0.225), VB vs RV range rho=-0.081 (p=0.593). Median-split tests of B2 or VB versus conservative-floor RV detection were also non-significant.

## Interpretation and next experiment
The best defensible new direction is **cadence-aware spectroscopic validation**, not another attempt to optimize the H10 classifier. Prioritize the 30 conservative-floor RV-variable objects, then obtain or reconstruct their individual visit times and uncertainties, fit a model that explicitly accounts for cadence and heteroscedastic errors, and compare observed variability against cadence-matched constant-RV simulations. Only after that should orbital/companion interpretations be attempted. A positive result would be an excess of variability beyond the cadence- and error-conditioned null model, not merely p<0.05 under the current chi-square screen.

## Claim boundary
- Positive: 30/46 pass the 0.5 km/s uncertainty-floor chi-square screen in this selected APOGEE cohort.
- Not established: these are compact companions, dark companions, or representative of all H10 objects.
- Negative: current data do not show that the RV variability screen separates H10-positive from H10-negative objects.
- Pending: cadence-matched null simulations and independent astrophysical confirmation.
