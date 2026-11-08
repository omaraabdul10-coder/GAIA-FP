# GAIA-FP — Final Research Completion & Audit Report

**Snapshot:** 3 November 2026  
**Scope:** supplied pre-DR4 repository and files available in the execution workspace  
**Integrity rule:** status is COMPLETE only when the empirical deliverable exists and is independently checkable. A working pipeline without downloaded observations is PARTIAL, not COMPLETE.

## Executive result

The project now contains reproducible ID-level lineage tables for the 746 mechanism-only records and the 33/95 missing mechanism outputs; APOGEE allVisit processing and exact-cadence injection code; a LAMOST DR9 v2.0 per-spectrum epoch-RV pipeline; an updated GALAH acquisition guide; a local pre-release DR4 hash freeze; and a consolidated completion report.

**No new real external APOGEE, GALAH, or LAMOST observations were downloaded in this workspace.** Requests to the public survey hosts failed at DNS resolution (`NameResolutionError`). Therefore the code and query pipelines are prepared, but the empirical epoch-RV tasks remain PARTIAL. No exact-cadence injection result is claimed.

## 1. Task-by-task status

| Task | Final status | What was completed in this session | What remains |
|---|---|---|---|
| APOGEE epoch-RV | PARTIAL | Added `tools/epoch_rv/process_apogee_allvisit.py`; documented DR17 `allVisit` fields and rejection bits; preserved the prior audit's 622 raw / 351 accepted / 46 ≥3-epoch summary as previously reported, not newly recomputed. | Need the verified 46-object `source_id`↔`APOGEE_ID` crosswalk and actual `allVisit` rows. |
| Exact APOGEE cadence injection | PARTIAL | Added `tools/epoch_rv/run_exact_cadence_injection.py`: Keplerian RV injections on input MJD timestamps, per-visit VERR, random phase/omega, fixed seed, null calibration, and recovery summaries. Synthetic unit tests pass. | Original 351 timestamp rows are absent. Run only after real visit table is supplied. Existing 414k proxy remains a distinct proxy analysis. |
| GALAH epoch-RV | PARTIAL | Verified official GALAH DR3 per-spectrum catalogue and per-spectrum VAC RV fields; retained the 22-chunk VizieR ADQL downloader and summarizer; updated download guide. | Actual epoch rows not downloaded because DNS failed. Run downloader on a networked machine. |
| LAMOST epoch-RV | PARTIAL | Identified official DR9 v2.0 LRS AFGK per-spectrum catalogue with Gaia DR3 source ID, obsid, MJD, RV, RV uncertainty and S/N; added exact-ID processing pipeline and tests. | Download the official catalogue and run the pipeline. No local empirical results yet. |
| Full 746-object lineage | PARTIAL | Generated a reproducible list of all 746 `mechanism_scored` IDs absent from raw NSS and a full raw-vs-mechanism membership table. | The separate old H10 `2,672-row` vs `1,926-row` duplicate-row lineage cannot be reconstructed because both original source tables/IDs are absent. |
| 33/95 exact filter reasons | PARTIAL | Generated `LINEAGE_33_OF_95.csv`; all 95 IDs are in raw NSS, candidate table and C/H input; 62 are in mechanism output and 33 are absent. | Exact first failed filter for each missing ID remains unknown because `results/dark_companion_scored.csv` and per-stage filter masks are absent. |
| 95-object selection correction | PARTIAL | Re-audited the available 95-object characterization and H11 controls; documented why H11 controls are not a valid replacement for the non-selected population with measured dynamical masses. | Full source frame and comparable selection covariates/outcomes are missing. Population transport is not identified. |
| Independent compact-companion confirmation | BLOCKED | Checked the published Gaia DR3 source `5136025521527939072` as a literature lead; it is in raw NSS but not in the 2,119-candidate or 95-object sample. It is not a confirmed compact object and not a validation case. | No defensible independent compact-object confirmation within the 95-object sample. A complete external literature/SIMBAD crossmatch is still needed. |
| DR4 blind evaluation | PARTIAL | Created local SHA-256 freeze record for preregistration draft, scoring code, thresholds and adapters; verified existing separate evaluator checks catalogue hash before opening labels. | No DR4 data exist in this pre-release snapshot; live schema/fetch remains untested. Local hash freeze is not OSF registration. |

## 2. Lineage results reproduced from current files

The script `tools/lineage/build_lineage_tables.py` was run successfully.

| Population | Rows | Unique source IDs |
|---|---:|---:|
| `realdata/dr3_nss_two_body_orbit_raw.csv` | 71,759 | 71,759 |
| `realdata/dr3_candidates.csv` | 2,138 | 2,119 |
| `results/mechanism_scored.csv` | 10,118 | 10,118 |
| `astrospectro_95_object_characterization.csv` | 95 | 95 |

Raw NSS and mechanism-scored intersection is 9,372 IDs. There are 62,387 raw-NSS-only IDs and 746 mechanism-only IDs. Thus, the 746 list is a source-population mismatch list, not the net difference between 71,759 and 10,118 rows. The full membership table is `results/final_completion/DATA_LINEAGE_RAW_NSS_vs_MECHANISM_FULL.csv`; the 746 mechanism-only IDs are in `results/final_completion/DATA_LINEAGE_746.csv`.

For the 95-object set, all 95 are `AstroSpectroSB1` records and are present in raw NSS, the candidate table and the C/H subset. Exactly 62 are present in `mechanism_scored.csv`; 33 are absent. The 33 CSV labels their first *observed missing output stage* as `mechanism_scored_output`; it deliberately does not guess the upstream reason.

The other `2,672 - 1,926 = 746` quantity is a historical excess-row count from an old H10 file. It is not the same ID set and cannot be converted into per-object lineage without the original 2,672-row and 1,926-row source tables.

## 3. Epoch-RV acquisition findings

### APOGEE

SDSS DR17 provides visit-level `MJD`, `VHELIO`, `VERR`, `STARFLAG`, and `RV_FLAG` in allVisit. The new processor rejects visits with the documented `BAD_PIXELS`, `VERY_BRIGHT_NEIGHBOR`, `LOW_SNR`, `RV_REJECT`, and `RV_FAIL` STARFLAG bits and `RV_REJECT` in RV_FLAG; it retains and marks `RV_SUSPECT`. It does not invent an APOGEE identifier mapping.

### GALAH

Official GALAH DR3 exposes 678,423 per-spectrum records and a per-spectrum radial-velocity VAC. The VizieR `spect` and `rv` tables join through `sobject_id` and contain Gaia DR3 IDs, RVs, uncertainties, method flags and HJD/MJD. Method flags 0 and 1 are GALAH-derived; 2 is Gaia DR2 fallback and 4 is no value. Existing scripts preserve these rules. No real rows downloaded in this session.

### LAMOST

Official LAMOST DR9 v2.0 LRS AFGK per-spectrum table documents Gaia DR3 `gaia_source_id`, unique `obsid`, `mjd`, heliocentric `rv` and `rv_err` in km/s. The new pipeline uses exact Gaia DR3 source-ID joins, retains `fibermask`/SNR, filters `fibertype=Obj` when present, and calculates weighted constant-RV diagnostics without converting non-matches into non-variable labels. No real rows downloaded in this session.

## 4. Selection-bias conclusion

The supplied independent audit reported that the 95-object sample is selected by an implied-mass cut `m2 < 80 M_J`, that the mass relation reconstructs selection with AUC about 0.9998, that about 93% of non-selected objects fall below the minimum selected propensity, that weighted ESS is about 23/95, and that maximum SMD remains about 1.35 after weighting (1.69 before). These values are cited as supplied-audit results, not recomputed in this session: the propensity design matrix and complete non-selected selection frame are absent.

`results/h11_controls.csv` is a separate 2,102-object H11 matched control set. Its matching is on G, log10(P), and significance and its control mass proxy is approximate (80–300 M_J), not a verified dynamical mass label. It cannot be repurposed as the non-selected population for the 95-object mass-cut propensity correction.

**Defensible inference:** the 95-object results apply to the selected subpopulation only. Do not publish a population-transported corrected rate.

## 5. Independent-validation result

The A&A Gaia DR3 multiplicity paper (DOI `10.1051/0004-6361/202243782`) discusses Gaia source `5136025521527939072` as a dormant-neutron-star candidate and reports a primary mass around 1.2 M_sun, secondary mass around 1.5 M_sun, period 536 days, and one SOPHIE follow-up RV point. The source is present in the raw NSS file but absent from the GAIA-FP candidate and 95-object subsets. One follow-up RV point and a candidate interpretation do not constitute independent compact-object confirmation. It is therefore recorded as an excluded literature lead in `results/final_completion/independent_validation_evidence.csv`.

## 6. DR4 freeze and readiness

Created:
- `audit/DR4_PRE_RELEASE_FREEZE_2026-11-03.json`
- `audit/DR4_PRE_RELEASE_FREEZE_2026-11-03.sha256`
- `tools/freeze_dr4_plan.py`

The freeze captures the v3.2 primary method, v3.1 comparator, A6-off sensitivity, verdict threshold 0.15, and A6 definition `ell=q**n >= 0.2` with `K_sum*(1+e) >= 30 km/s`, plus hashes of the preregistration drafts and DR4 code. It is explicitly a local hash record, not an OSF registration. `src/dr4_fetch.py` exists but has not been tested against the live archive in this workspace. ESA's current schedule is DR4 on 2 December 2026; the blind evaluation is therefore not yet conducted.

## 7. Tests and static checks

- New epoch-RV tests: 5 passed (`tests/test_final_epoch_rv.py`).
- Existing test modules were run separately; total 119 tests passed across the 20 test files. `test_dr3_study.py` was completed in two runs (6 tests in the initial run, then the final 2 separately). Some multi-module shell batches timed out at the tool execution limit, so the reported total is the sum of completed per-file/per-test runs, not a single monolithic run.
- The previous pre-DR4 closeout recorded that monolithic `pytest -q` timed out; no monolithic clean pass is claimed.
- Static compilation and lineage regeneration commands are recorded in `audit/SESSION_CHANGELOG_FINAL_2026-11-03.md`.

## 8. Reproducible commands

```bash
python tools/lineage/build_lineage_tables.py
pytest -q tests/test_final_epoch_rv.py
python tools/freeze_dr4_plan.py
python -m py_compile tools/epoch_rv/process_apogee_allvisit.py tools/epoch_rv/process_lamost_dr9_lrs.py tools/epoch_rv/run_exact_cadence_injection.py tools/lineage/build_lineage_tables.py
```

For actual external acquisition, follow `APOGEE_EXACT_CADENCE_GUIDE_2026-11-03.md`, `GALAH_EPOCH_RV_DOWNLOAD_GUIDE_2026-11-01.md`, and `LAMOST_EPOCH_RV_DOWNLOAD_GUIDE_2026-11-03.md`.

## 9. Scientific claim suitable for ISEF

GAIA-FP is a physically motivated and auditable framework for assessing luminous-companion contamination in Gaia DR3 compact-companion candidates, with a pre-release DR4 evaluation pipeline. The present data do not establish a validated compact-companion detector or a confirmed compact-object discovery. Epoch-RV acquisition, independent confirmation, population transport, and blind DR4 validation remain incomplete.
