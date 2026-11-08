# GAIA-FP pre-DR4 audited package — 3 November 2026

This package consolidates the DR3 development state, the latest independent audit findings supplied by the project team, and the code/documentation corrections performed in this session.

## Read first
1. `audit/GAIAFP_MASTER_AUDIT_2026-11-03.md` — complete evidence-based project status and claim limits.
2. `audit/ISEF_EXECUTIVE_SUMMARY_2026-11-03.md` — concise science-fair summary.
3. `audit/TEST_RECONCILIATION_2026-11-03.md` — exact test execution scope and limitations.
4. `audit/final_completion/FINAL_PARTIALS_CLOSURE_REPORT_2026-11-03.md` — final disposition of every previously PARTIAL research stream, including new lineage, filter, selection, external-reference, and corrected-S1 analyses.
5. `docs/GAIA_ARCHIVE_EXPORT_HANDOFF.md` — missing 22,127-object export plan.
6. `PREREG_AMENDMENT_v0.6_DRAFT.md` and `DEVIATIONS_v0.6.md` — A28 A6 implementation reconciliation (draft, not represented as OSF-submitted).
7. `results/S1_ERRATUM_NOTICE.md` — retirement of the pre-erratum S1 column.

## Changes in this package
- DR4 v3.2 A6 now uses the registered secondary-to-primary flux ratio `ell=q**n >= 0.2`, not `beta=ell/(1+ell) >= 0.2`.
- Added a regression test for the interval where these conditions disagree.
- Added a guard that renames the historical pre-erratum S1 field to `S1_pre_erratum_DO_NOT_USE` in mechanism outputs.
- Preserved the original `results/mechanism_scored.csv` as `results/mechanism_scored_pre_erratum_original.csv`.
- Added export schema preflight, ADQL template, and a CSV validator.

## Current scientific status
The corrected S1 model does not beat the stronger B2+VB baseline in the audited H10 comparison. The 95-object dynamical subset is selected and non-representative. SB2 positive controls and APOGEE epoch RV provide partial checks only. GALAH/LAMOST epoch RV and Gaia DR4 blind evaluation remain pending. The final closure audit additionally reproduces the 746-ID set difference, narrows the 33/95 missing records to downstream filters, rejects an unsupported general-population correction for the selected 95 objects, and regenerates corrected S1 (AUC 0.776327; reference 0.776366).

Gaia DR4 is scheduled for 2 December 2026 according to an ESA posting dated 1 November 2026: https://jobs.esa.int/job/Noordwijk-Intern-in-the-Science-Engagement-and-Oversight-Office-A-Logarithmic-Map-of-the-Gaia-DR4-Universe/1452872333/ . ESA’s mission page also lists December 2026: https://www.esa.int/Science_Exploration/Space_Science/Gaia . The v0.6 preregistration file remains a local draft until submitted and timestamped on OSF.

## Test note
Final verification: `pytest -q` completed in one process with 125 passed in 23.57 s. This tests code, not the unavailable external survey observations.
