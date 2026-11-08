# GAIA-FP — follow-up data retrieval status (2026-11-03)

## Work completed in this continuation

1. Re-inspected the actual GAIA-FP closeout archive and its epoch-RV query/download code.
2. Verified that the project contains 2,138 rows in `realdata/dr3_candidates.csv`; the GALAH query package targets the distinct 2,102-source subset in its own `candidate_source_ids.txt`. These populations must not be silently conflated.
3. Reworked APOGEE crosswalk generation to preserve the `FIELD` key from official DR17 `allStar`. A Gaia DR3 source may legitimately have APOGEE reductions in multiple fields. The correct visit join key is `(APOGEE_ID, FIELD)` when available. Multiple fields for one Gaia source are retained; only duplicated mapping keys are excluded as ambiguous.
4. Reworked APOGEE visit processing so valid visits from multiple APOGEE fields can be aggregated at Gaia `source_id` level without falsely rejecting the source. The output now records all APOGEE IDs and fields contributing to a source summary.
5. Added two regression tests for multi-field APOGEE mappings and visit aggregation.
6. Ran the complete test suite: `127 passed in 24.11s`.

## External data sources verified

### APOGEE DR17
- Official DR17 `allStar` includes `GAIAEDR3_SOURCE_ID`, `APOGEE_ID`, and field-level products.
- `allVisit` has visit-level rows and the observation metadata needed for cadence analysis; the project processor expects exact `JD`, `VHELIO`, `VRELERR`, and quality flags.
- Official references: https://www.sdss4.org/dr17/irspec/dr_synopsis/ and https://outerspace.stsci.edu/spaces/SDSS/pages/286852482/APOGEE+Data+Products

### GALAH DR3
- Official `main_allspec_v2` is per-spectrum (678,423 spectra) and includes Gaia DR3 IDs and per-spectrum RVs.
- `VAC_rv_v2` (67 MB) is the per-spectrum RV value-added table; `sobject_id` is the required join key. `use_rv_flag` identifies valid RV method vs Gaia DR2 fallback/no value.
- Data Central exposes a SQL/ADQL query service. Existing VizieR chunks are still present, but the Data Central route is a viable alternative.
- Official references: https://www.galah-survey.org/dr3/the_catalogues/ and https://www.galah-survey.org/dr3/table_schema/ and https://datacentral.org.au/services/query/

### LAMOST DR9 v2.0
- Official DR9 LRS Multiple Epoch Catalog contains 1,962,095 targets and fields `obsid_list`, `midmjm_list`, and `rv_list`; `gaia_source_id` can be present in the catalogue schema described by the release docs, while the `gp_id` field must be interpreted according to its source namespace.
- NADC lists the multiple-epoch table at 790.95 MB. A smaller target-specific server-side query is preferable to bulk downloading.
- Official references: https://www.lamost.org/dr9/v2.0/doc/lr-data-production-description and https://nadc.china-vo.org/res/r100851/?lang=en

### Independent follow-up reference
- A 2026 CaltechDATA release contains `table1_radial_velocities.csv` and `spectrum_manifest.csv`; the latter maps Gaia DR3 source IDs to epoch, RV, RV uncertainty and spectrum path. The release reports 1,292 spectra for 75 sources, not 227 sources with full RV time series. The paper began with 227 candidates, but the downloadable epoch spectra described on the dataset page cover 75 sources.
- Dataset: https://data.caltech.edu/records/0jxb3-ny611
- Paper: https://arxiv.org/abs/2608.06453

## Retrieval attempt and hard limitation

The runtime was tested against the official endpoints `tapvizier.cds.unistra.fr`, `datacentral.org.au`, `dr17.sdss.org`, and `nadc.china-vo.org`. All failed DNS resolution from this execution environment. Browser/web search can read the public documentation and catalogue metadata, but it cannot submit the required authenticated/POST ADQL requests or transfer the FITS/CSV catalogue payloads into the local project container. Consequently, no new APOGEE, GALAH, or LAMOST observational rows were downloaded in this continuation, and no empirical epoch-RV statistics are claimed.

## Remaining scientific tasks

- Execute APOGEE DR17 `allStar` crosswalk and `allVisit` extraction on the actual 46 APOGEE target IDs; then run the exact-JD cadence injection on accepted epochs.
- Execute GALAH per-spectrum RV extraction for the 2,102-source project subset, joining by `sobject_id`, and summarize repeated epochs with method flags and times.
- Execute LAMOST DR9 LRS Multiple Epoch query for project source IDs; validate Gaia namespace and parse aligned observation/time/RV lists.
- Retrieve missing intermediate 95-object filter-stage files to identify the exact exclusion stage for the 33 objects. Current audit establishes their presence/absence across available files, not the final filter cause.
- Retrieve machine-readable 2026 compact-object follow-up tables and crossmatch exact Gaia DR3 `source_id` values. No independent compact-companion confirmation is claimed yet.
- Resolve historical H10 row-level lineage (2,672 vs 1,926) with the missing original source ID list; do not equate it with the separately computed 746-ID population difference.
- Gaia DR4 blind evaluation remains pending the actual DR4 release and must use the frozen protocol without tuning on blind labels.

## Reproducibility

The updated APOGEE code is in `tools/epoch_rv/build_apogee_mapping.py` and `tools/epoch_rv/process_apogee_allvisit.py`. The added tests are in `tests/test_final_epoch_rv.py`. Run:

```bash
pytest -q
```

Expected result in the current packaged environment: `127 passed`.
