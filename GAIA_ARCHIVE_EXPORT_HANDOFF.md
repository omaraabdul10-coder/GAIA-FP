# Gaia Archive export handoff — 3 November 2026

## Purpose
Retrieve the missing per-source spectroscopic and orbital fields for the 22,127-source supplementary scoring population described in the independent audit. This is a data-acquisition step, not a model validation result.

## Files
- `tools/gaia_archive_schema_preflight.adql` — check the live Gaia DR3 TAP schema first.
- `tools/gaia_archive_export_template.adql` — query template using a TAP upload table `gaiafp_ids`.
- `tools/validate_astrospectro_export.py` — validate row count, required columns, unique IDs, missingness and SHA-256.

## Required input
A one-column or two-column CSV containing the exact 22,127 Gaia `source_id` values from the independent audit population. That ID list was not present in the project archive inspected for this package. Do not recreate it from a different cohort or substitute the 2,102 candidate list.

## Procedure
1. In Gaia Archive, upload the exact ID table as `gaiafp_ids` with `source_id` stored as 64-bit integer.
2. Run `gaia_archive_schema_preflight.adql`. Confirm every required column is present in the exact DR3 table. If `corr_vec` or any other column is not present where expected, inspect `TAP_SCHEMA.columns`, identify the correct table/column, and log a dated mapping deviation before the full query.
3. Run the export query as CSV. The template is intentionally not represented as already validated; live schema verification is mandatory.
4. Save the original export unchanged and record query text, TAP job ID, retrieval timestamp, row count and SHA-256.
5. Run:
   `python tools/validate_astrospectro_export.py <export.csv> --expected-rows 22127`
6. Investigate any missing IDs, duplicates, null `vbroad`, and unmatched joins. Do not impute absent `vbroad` values for the primary score. Keep a coverage table by score.
7. Only after provenance and coverage pass, run the corrected scorer and compare S1 against the pre-specified B2+VB baseline using the paired test chosen before inspecting results.

## Known limitations
- The export query was not executed in this environment.
- The exact 22,127 ID file was not available in the inspected archive.
- This package does not claim full-population rescore completion.
- A Gaia Archive export can improve coverage, but it cannot replace independent labels or the DR4 blind evaluation.
