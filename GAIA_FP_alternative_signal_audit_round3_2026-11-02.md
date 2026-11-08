# GAIA-FP — Alternative signal audit, round 3
Date: 2 November 2026

## Question
Does the B2–H10 association seen in the 46-object APOGEE primary cohort persist when the full 1,926-object H10 table is split by APOGEE epoch-coverage category?

## Data and groups
Source: `apogee_object_variability_all_h10.csv` (1,926 unique rows; 841 label=1, 1,085 label=0). The supplied `apogee_group` field partitions the table into:

- `primary_3plus`: 46 objects (18 positive, 28 negative)
- `exploratory_2`: 31 objects (17 positive, 14 negative)
- `other`: 1,849 objects (806 positive, 1,043 negative)

No labels were changed. B2 was used as supplied. These are strata of one H10 cohort, not independent external validation samples.

## Main result: B2 association is present in all three coverage strata

| APOGEE coverage stratum | N (positive / negative) | B2 AUC | Median B2, positive | Median B2, negative | Mann–Whitney p |
|---|---:|---:|---:|---:|---:|
| 3+ epochs (`primary_3plus`) | 46 (18 / 28) | **0.887** | 2.460 | 0.621 | 1.20e-5 |
| Exactly 2 epochs (`exploratory_2`) | 31 (17 / 14) | **0.824** | 2.486 | 0.648 | 0.00239 |
| Other (`other`) | 1,849 (806 / 1,043) | **0.726** | 2.263 | 0.965 | 1.71e-62 |

Stratified bootstrap percentile 95% intervals for AUC (1,000 resamples; within each class resampled separately):

- 3+ epochs: 0.778–0.964
- exactly 2 epochs: 0.630–0.971
- other: 0.704–0.749

The small 31- and 46-object strata have wide intervals. The `other` group dominates the full-sample result by size.

## Regression check
A logistic model on all 1,926 objects with B2 and coverage-group indicators gave a positive B2 coefficient of 0.493 (SE 0.035, p<0.001; odds ratio 1.64 per one-unit B2 increase), while group indicators alone were not significant after B2 adjustment.

An exploratory B2-by-group interaction model estimated a steeper B2 slope in the 3+ epoch group than in `other` (interaction coefficient +0.883, SE 0.396, nominal p=0.026). The interaction for exactly-2 epochs was not significant (p=0.244). This interaction is exploratory, uncorrected for multiple testing, and potentially sensitive to selection into APOGEE coverage; it must not be treated as a confirmed physical effect.

Separate within-group logistic fits also gave positive B2 slopes:
- `other`: coefficient 0.475, p=2.13e-41
- exactly 2 epochs: coefficient 0.909, p=0.0143
- 3+ epochs: coefficient 1.359, p=0.000565

## Interpretation
This is a stronger and more useful descriptive result than reporting the 46-object AUC alone:

> B2 is positively associated with the existing H10 label in each of the three APOGEE-coverage strata, including the large `other` group; the association is numerically strongest in the small multi-epoch strata.

It argues against the association being confined only to the 46 objects with at least three APOGEE epochs. However, the groups all come from the same 1,926-object H10 table and use the same pre-existing labels and B2 values. This is **coverage-stratified consistency, not independent replication**.

## Claim boundary
- Supported: B2 is associated with the existing H10 label in all three coverage strata in this supplied table.
- Not supported: B2 independently identifies compact companions, causes RV variability, or generalizes to a new survey/population.
- Not tested: whether H10 label construction itself uses B2 or variables mathematically coupled to B2. The original label-generation specification is needed to exclude circularity decisively.
- Next decisive test: freeze B2 and label definitions, obtain an independently assembled sample with independently determined labels, and evaluate B2 without tuning. Also audit the provenance of the H10 label before interpreting this as independent physical information.
