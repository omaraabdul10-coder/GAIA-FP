# GAIA-FP — Round 7 consolidated completion audit
**Date:** 2 November 2026  
**Purpose:** reconcile completed Monte Carlo, spectroscopic cross-match, real APOGEE RV analysis, injection/recovery, and baseline comparisons using the files available in this workspace.

## Executive status

| Workstream | Result | Status boundary |
|---|---|---|
| 10,000-replicate null Monte Carlo | AUC null rejection 4.90%; paired ΔAUC null rejection 5.02% | Completed synthetic calibration diagnostic; not empirical Gaia performance |
| Independent SB2 catalogue cross-match | 2,102 candidates; 16 unique matches (13 APOGEE, 2 GALAH, 1 LAMOST); no survey overlap | Completed catalogue cross-match; not a full epoch-RV comparison |
| Real APOGEE epoch-RV analysis | 351 accepted visits; 46 objects with ≥3 integer-MJD epochs; 30/46 remain variable under 0.5 km/s floor | Completed for the selected APOGEE cohort; does not separate H10 labels |
| Synthetic phase injection–recovery | Six scenarios, three seeds each; CMD+phase ΔAUC positive in all six scenario means | Completed synthetic mechanism test; not real-cadence validation |
| Cadence-summary-matched injection–recovery | New 1,380 object-scenario cells | Exploratory proxy using actual epoch counts and baselines, but randomized visit times; not exact real cadence |
| Baseline comparison | Corrected S1 AUC 0.77637 vs B2+VB 0.79569; paired ΔAUC −0.01932 (95% CI −0.03149 to −0.00747) | Completed; S1 beats B2 alone but not B2+VB |

## 1. Monte Carlo null calibration — completed

The archived 10,000-replicate outputs were inspected:

- AUC: 490/10,000 null rejections at α=0.05 = **4.90%**; Wilson 95% interval **4.49–5.34%**; Monte Carlo SE 0.216 percentage points.
- Paired ΔAUC: 502/10,000 = **5.02%**; Wilson 95% interval **4.61–5.47%**; Monte Carlo SE 0.218 percentage points.
- Null p-value uniformity checks: KS p=0.475 (AUC) and 0.714 (paired ΔAUC).

**Interpretation:** the bootstrap/null test pipeline has approximately nominal 5% type-I behaviour under the simulated null. These runs use synthetic null scores (n_pos=39, n_neg=26); they do not establish classifier performance or false-positive rates in the Gaia population.

## 2. Independent SB2 catalogue cross-match — completed

The cross-match audit covers all **2,102** scored candidates:

- APOGEE: **13** unique SB2 matches
- GALAH: **2**
- LAMOST: **1**
- Total: **16 unique matches**
- Cross-survey overlap: **0**
- APOGEE ambiguous matches: **0**

This is an independent spectroscopic-catalogue positive-control match. It is not equivalent to obtaining epoch RV time series for all candidates.

## 3. Real APOGEE epoch-RV analysis — completed for the available cohort

The reconstructed visit audit reports **622 raw rows**, of which **351 accepted visits** remained after quality checks and duplicate handling. The primary cohort contains **46 objects** with at least three distinct integer-MJD epochs (18 H10-positive, 28 H10-negative).

- 42/46 pass the nominal constant-RV screen.
- 30/46 remain below p<0.05 under the conservative 0.5 km/s uncertainty-floor scenario.
- The conservative detections split 12/18 H10-positive and 18/28 H10-negative.
- The group comparison is not significant (Fisher exact p=1.0 for the conservative screen).

**Interpretation:** real APOGEE visit-level variability exists in a subset of this selected cohort. It does not currently discriminate H10-positive from H10-negative objects, and it does not by itself identify a compact or dark companion.

## 4. Injection–recovery

### 4a. Synthetic phase injection — completed

The existing reproducible experiment contains six combinations of 20/40 epochs and 2/4/8 km/s measurement error, with three independent seeds per scenario. Mean CMD+phase ΔAUC values versus CMD-only are:

| Epochs | RV error (km/s) | Mean ΔAUC | Replicates with bootstrap CI > 0 |
|---:|---:|---:|---:|
| 20 | 2 | +0.116 | 3/3 |
| 20 | 4 | +0.054 | 2/3 |
| 20 | 8 | +0.026 | 3/3 |
| 40 | 2 | +0.145 | 3/3 |
| 40 | 4 | +0.114 | 3/3 |
| 40 | 8 | +0.031 | 3/3 |

This supports recoverability under the specified synthetic signal model. It is not a real-data result.

### 4b. New cadence-summary-matched proxy — executed

I ran an additional injection/recovery sensitivity experiment using the **actual observed epoch count and total time baseline of each of the 46 APOGEE primary objects**, with a conservative 0.5 km/s measurement-error floor. For each object and each (K, P) pair, 300 injections were tested (1,380 object–parameter cells; 414,000 injected realizations total); visit times were drawn uniformly within that object's observed baseline. The constant-RV χ² test used p<0.01.

- Null false-positive fraction: **1.101%** over 13,800 null simulations.
- Mean recovery at K=2 km/s: P=2d: 77.0%, P=10d: 69.8%, P=30d: 64.6%, P=100d: 53.0%, P=365d: 41.2%, P=1000d: 29.4%.
- Mean recovery at K=5 km/s: P=2d: 94.7%, P=10d: 89.2%, P=30d: 81.0%, P=100d: 69.6%, P=365d: 54.5%, P=1000d: 43.1%.

**Critical limitation:** the currently available per-object CSVs contain epoch counts and total baselines, not the individual MJD/JD timestamps. Therefore the visit times in this additional experiment are randomized within each real baseline. This is a cadence-summary-matched sensitivity analysis, **not exact observed-cadence injection–recovery**. The full real-cadence test still requires the per-visit timestamp table (the 351 accepted visits with source_id, JD/MJD, RV, and uncertainty).

## 5. Baseline comparison — completed

The corrected H10 comparison on the 1,926 labelled objects (841 positive, 1,085 negative) reports:

| Score | AUC |
|---|---:|
| B2 | 0.73191 |
| VB | 0.75500 |
| B2+VB | 0.79569 |
| Corrected S1, c=1 | 0.77637 |
| Corrected S2 | 0.83238 |

For the primary S1 comparison:
- S1 − B2 = **+0.04446**, 95% CI **[+0.03340, +0.05510]**.
- S1 − (B2+VB) = **−0.01932**, 95% CI **[−0.03149, −0.00747]**.

Thus the physical S1 component adds discriminatory information over B2 alone in this H10-labelled sample, but the corrected S1 score does not outperform the raw B2+VB combination.

On the separate 46-object APOGEE-selected subset, repeated stratified 4-fold CV (100 repeats) gave mean fold AUCs B2=0.886, VB=0.818, B2+VB=0.894. The paired fold-level gain of B2+VB over B2 averaged +0.0073, with a 2.5–97.5 percentile range [−0.0714, +0.0857]. This small selected cohort does not establish robust incremental predictive value for VB.

## Final conclusion

Four major lines are already completed with positive or informative results: (1) 10k synthetic null calibration, (2) independent SB2 catalogue cross-match, (3) real APOGEE epoch-RV variability audit for the selected cohort, and (4) corrected baseline comparison. The synthetic phase injection is also complete. A new cadence-summary-matched proxy was executed and is useful for sensitivity planning.

The one item that must **not** be relabelled as complete is exact real-cadence injection–recovery: the visit-level timestamp rows are not present in the files available in this workspace. The aggregate cohort table cannot reconstruct the actual sampling window. The existing SDSS documentation specifies that APOGEE visit-level RVs should be analysed against their JD values and associated RV errors; the timestamp-bearing visit table is therefore required for the exact cadence experiment.

## Reproducibility files

- `GAIA_FP_round7_cadence_envelope_injection_2026-11-02.csv` — per-object injection recovery rates.
- `GAIA_FP_round7_cadence_envelope_summary_2026-11-02.csv` — summary by amplitude and period.
- `GAIA_FP_round7_completion_audit_2026-11-02.md` — this report.
