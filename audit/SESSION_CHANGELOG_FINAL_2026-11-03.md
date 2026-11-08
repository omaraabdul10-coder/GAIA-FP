# Final completion-session changelog — 3 November 2026

## New source-derived outputs

- `tools/lineage/build_lineage_tables.py` generated `DATA_LINEAGE_746.csv`, `DATA_LINEAGE_RAW_NSS_vs_MECHANISM_FULL.csv`, `LINEAGE_33_OF_95.csv`, and `lineage_membership_summary.json` from the actual archived CSVs.
- `tools/epoch_rv/process_apogee_allvisit.py` added for SDSS DR17 allVisit extraction after a verified source_id/APOGEE_ID mapping is supplied.
- `tools/epoch_rv/run_exact_cadence_injection.py` added for actual-MJD Keplerian injections with per-visit uncertainties. No exact-cadence run was made because original timestamps are absent.
- `tools/epoch_rv/download_lamost_dr9_file.py` added to download an explicitly supplied official catalogue URL with SHA256 provenance; `process_lamost_dr9_lrs.py` added for exact Gaia DR3 source_id joins to LAMOST DR9 v2.0 per-spectrum AFGK RV data.
- `tests/test_final_epoch_rv.py` added; 5 tests pass, including synthetic fixture tests for the data-processing logic.
- `LAMOST_EPOCH_RV_DOWNLOAD_GUIDE_2026-11-03.md`, `APOGEE_EXACT_CADENCE_GUIDE_2026-11-03.md`, `INDEPENDENT_VALIDATION_SEARCH_2026-11-03.md`, and `SELECTION_BIAS_95_OBJECTS_FINAL_AUDIT_2026-11-03.md` added.
- `tools/freeze_dr4_plan.py` generated a local DR4 pre-release hash manifest. This is not OSF registration.
- `DR4_READINESS.md` updated to reflect that `src/dr4_fetch.py` exists but remains untested against the live archive.
- `FINAL_COMPLETION_REPORT.md` added; README points to all new outputs.

## Reproduced data facts

- Raw NSS: 71,759 rows, 71,759 unique source IDs.
- Candidate table: 2,138 rows, 2,119 unique source IDs.
- Mechanism output: 10,118 rows, 10,118 unique source IDs.
- Raw NSS/mechanism intersection: 9,372 IDs; raw-only 62,387; mechanism-only 746.
- All 95 characterization IDs are present in raw NSS, candidate table, and C/H subset; 62 are in mechanism output and 33 are absent.
- Original historical H10 2,672-row / 1,926-row source tables are not in the archive; no per-ID explanation for that separate 746-row excess is fabricated.

## Test/QA

- `pytest --collect-only -q tests`: 119 tests collected.
- All 119 tests passed across individual test-file runs (the 8 `test_dr3_study.py` tests were completed as 6 + 2 due command execution limits).
- `tests/test_final_epoch_rv.py`: 5 passed.
- Static compilation succeeded for the four new scripts.
- Lineage table generation succeeded after regeneration.
- External catalogue retrieval did not run: runtime DNS resolution failed for LAMOST, Zenodo and SDSS hosts. Therefore no external epoch-RV result is claimed.

## External schema sources reviewed

- SDSS DR17 APOGEE RV docs: https://www.sdss4.org/dr17/irspec/radialvelocities/ ; https://www.sdss4.org/dr17/irspec/use-radial-velocities/ ; https://www.sdss4.org/dr17/irspec/apogee-bitmasks/
- GALAH DR3 catalogue/schema: https://www.galah-survey.org/dr3/the_catalogues/ ; https://www.galah-survey.org/dr3/table_schema/
- LAMOST DR9 v2.0 LRS docs/catalogue: https://lamost.org/dr9/v2.0/doc/lr-data-production-description ; https://www.lamost.org/dr9/v2.0/catalogue
- Gaia DR4 schedule: https://www.cosmos.esa.int/web/gaia/data-release-4


## Final PARTIAL closure pass — 3 November 2026
- Re-ran full suite in one process: `125 passed in 23.57s` (supersedes older timeout-only note).
- Regenerated corrected S1 for 10,118 rows; corrected labelled AUC 0.776327, erratum reference 0.776366 (absolute delta 0.00003844).
- Recomputed raw-NSS/mechanism lineage: 746 mechanism-only IDs, distinct from the unreconciled historical H10 row-count difference of 746.
- Reconstructed the 33/95 cohort exclusions: all 33 pass available pre-VB filters; precise downstream filter cause remains unidentifiable from missing upstream inputs.
- Reproduced 95-object selection and tested propensity overlap; no defensible general-population correction is estimable because 2,024 parent candidates lack compatible outcomes and positivity is poor.
- Cross-matched 21 literature RV-followed neutron-star candidate references; only one scored overlap, outside the GAIA-FP candidate/95-object validation sample, and not ground-truth validation.
- Added/refined APOGEE exact-JD, GALAH per-spectrum, and LAMOST exact-obsid/MIDMJM acquisition/analysis pipelines. No observational epoch rows were downloaded due to missing source data and failed DNS resolution to external survey hosts.
- Added `audit/final_completion/FINAL_PARTIALS_CLOSURE_REPORT_2026-11-03.md` as the controlling status document.
