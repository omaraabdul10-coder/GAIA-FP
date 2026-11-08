# 95-object selection-bias audit — 3 Nov 2026

## Reproducible facts from the current archive

- `results/qa2/partial_completion/astrospectro_95_object_characterization.csv` contains 95 unique source IDs.
- All 95 IDs are present in `realdata/dr3_nss_two_body_orbit_raw.csv`, `realdata/dr3_candidates.csv`, and `realdata/dr3_astrospectro_ch.csv`.
- 62/95 are present in `results/mechanism_scored.csv`; 33/95 are absent.
- The 95-object set is a selected dynamical subset, not a random Gaia sample.
- `results/h11_controls.csv` is a separate 2,102-object one-to-one matched control set for the H11 DR3 exercise. Its matching covariates are G, log10(P), and significance; it is not a substitute for the non-selected population with measured dynamical companion masses.

## Previously reported selection diagnostics

The independent audit summary supplied with the project reported that the 95 objects were selected by an implied-mass threshold m2 < 80 M_J; the implied-mass rule reconstructed the selection with AUC about 0.9998. Its propensity analysis found poor common support: about 93% of non-selected objects had propensity below the minimum selected-object propensity, weighted ESS about 23/95, and maximum SMD 1.35 after weighting (1.69 before). These are supplied-audit values, not recomputed from raw data in this session; the source propensity table and full non-selected population design matrix are not present in the archive.

## Why no valid population correction is claimed

The current archive has companion-mass draws for the 95 selected objects, but does not include corresponding dynamical masses/selection covariates for the full non-selected comparison population. `h11_controls.csv` contains matched control-star observables and an approximate 80–300 M_J mass proxy, not verified dynamical labels for the 95-object selection process. A propensity model cannot repair absent overlap or absent outcome/selection covariates. Re-fitting weights from only the selected 95 and the H11 control set would answer a different question and risk target leakage.

## Defensible conclusion

The 95-object analysis supports descriptive inference about this selected subpopulation only. No general-population transport estimate is identified. Do not publish an inverse-probability-weighted corrected rate as if it represented the Gaia candidate population. Further work requires the full source-ID-level selection frame, measured covariates for selected and non-selected sources, and a pre-specified common-support/estimand definition.
