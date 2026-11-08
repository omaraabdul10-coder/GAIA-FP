# GAIA-FP DR3 development audit — deposit draft

This is a pre-DR4 **development and reproducibility supplement**, not a final claim of confirmed compact/dark companion detection.

## What's included

- The archived DR3 data products needed for the closeout analyses.
- A new object-level 95-row membership crosswalk and selection diagnostics.
- An independently recomputed SB2 positive-control top-20 ranking comparison.
- The Round-5/6/7 analysis reports and corrected mechanism-lineage report.
- Relative-path code to reproduce the three new analyses in `recomputed/`.

## Quick reproduction

Python 3.10+ is recommended. Install `numpy`, `pandas`, `scipy`, and `scikit-learn`, then run from this directory:

```bash
python code/reproduce_closeout_audit.py
```

The script reads only `inputs/` and writes the crosswalk, selection diagnostics, SB2 ranking summary and JSON summary into `recomputed/`.

## Critical scope limits

The upstream `dark_companion_scored.csv`, full VizieR–Gaia AstroSpectroSB1 joined source, original 2,672-row H10 input, the actual 351 APOGEE visit timestamp rows, GALAH/LAMOST epoch-level observations, and Gaia DR4 products are not included because they were not available in the audited archive. Consequently, exact per-object reasons for 33 missing mechanism rows, the first 746-row deduplication audit, exact real-cadence injection–recovery, and DR4 validation are not closed.

The 2,086 candidates without an SB2 catalogue match are **unlabelled**, not verified single stars. The CMD-marginal SB2 result is a post-hoc positive-control ranking test on only 16 positives, not a specificity/precision estimate.

## Attribution and citation

This work uses Gaia DR3 catalogue data. Credit and cite ESA/Gaia/DPAC and the specific Gaia DR3 catalogue papers/products used. The Gaia DR3 documentation states that Gaia data are free to use provided ESA/Gaia/DPAC is credited. The VizieR `I/357/tboasb1c` page lists the AstroSpectroSB1 table and its catalogue row count.

The project source README lists preregistration records `10.17605/OSF.IO/N5H4B` and `10.17605/OSF.IO/TBJGY`. Verify these records and the exact frozen text before using them as related identifiers in a public DOI deposit.

## Before public deposit

1. Confirm creator list, ORCID(s), affiliations and author order.
2. Select a code/data license only after confirming ownership and any source-data redistribution conditions. No license is imposed by this draft.
3. Review personal/institutional identifiers in the original source repository before linking it publicly. They have deliberately not been copied into this supplement's metadata template.
4. Review the paper title/abstract so it does not claim DR4 validation or confirmed compact companions.
5. Reserve and publish a DOI from the authenticated repository account. No DOI is minted by this zip itself.
