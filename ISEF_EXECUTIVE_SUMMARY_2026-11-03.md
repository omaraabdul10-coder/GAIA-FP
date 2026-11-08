# GAIA-FP — ISEF executive summary (3 November 2026)

## Research question
Can Gaia DR3 astrometric compact-companion candidates be contaminated by unresolved luminous stellar companions whose photocentre motion and blended spectra mimic a dark or compact companion?

## Method
GAIA-FP combines astrometric orbit information, photometric displacement from a main-sequence ridge, empirical/synthetic line-width information, a luminous-binary photocentre model, survey SB2 crossmatches, and a planned phase-dependent Gaia RVS line-width likelihood. DR3 is the development dataset. Gaia DR4 is reserved for a pre-registered blind evaluation.

## Main result
On the corrected 1,926-object labelled H10 sample, CMD-only B2 achieved AUC 0.7318, empirical VB 0.7550, B2+VB 0.7957, and corrected physical S1 0.7764. S1 beat B2 alone but was below B2+VB by 0.0193 AUC (95% CI −0.0316 to −0.0075). The data therefore do not support the claim that S1 is superior to the strongest empirical baseline.

## Additional checks
The 2,102-candidate survey crossmatch yielded 16 SB2 positive controls, which is too small for a definitive independent validation; unmatched objects are unlabelled, not true negatives. APOGEE epoch RVs show variability but no separation between H10 classes under a conservative error floor. A 95-object dynamical subset is strongly selected by an implied-mass cut and is not population-representative. Synthetic null calibration and injection-recovery are useful method checks but do not establish real-Gaia false-positive rates.

## Contribution and status
The project's defensible contribution is an auditable, physically motivated assessment framework and a pre-registered DR4 validation plan. The A6 line-ratio implementation discrepancy was reconciled before DR4, and the old pre-erratum S1 output has been retired. Independent DR4 and external epoch-RV validation remain pending.

## Honest limitation
The project does not yet demonstrate confirmed compact-object discoveries or population-wide classifier superiority. The most important next scientific milestone is the complete Gaia Archive export and then the blind Gaia DR4 evaluation.
