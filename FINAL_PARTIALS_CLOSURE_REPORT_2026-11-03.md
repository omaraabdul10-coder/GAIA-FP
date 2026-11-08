# GAIA-FP — Final PARTIAL-work closure audit

**Audit date:** 3 November 2026  
**Scope:** Complete every analysis or reproducibility task that can be completed from the supplied GAIA-FP archive; distinguish completed forensic/code work from observations that require external survey data not present in the archive.

## Executive outcome

The locally reproducible audit work is now complete and the full repository test suite has been run in one process: **125 passed in 23.57 s**. The corrected S1 score has been independently regenerated from the archived inputs and reproduces the erratum reference AUC to an absolute difference of `3.84e-05`.

The remaining empirical epoch-RV tasks could not honestly be marked complete. The archive does not contain the required source-ID/visit crosswalks or visit-level tables, and this execution environment could not resolve the SDSS, CDS/VizieR, or LAMOST data hosts. The project now contains verified catalogue schemas, download/query recipes, resumable acquisition code, parsers, timing/quality rules, and tests, but **no new APOGEE, GALAH, or LAMOST observational rows were downloaded**. Synthetic self-tests are not treated as survey evidence.

Gaia DR4 blind evaluation is also not yet executable: ESA lists DR4 as expected in December 2026, after this audit date. A local hash freeze is prepared, but it is not an OSF registration or a completed blind test.

## Status table

| Workstream | Work completed in this closeout | Final status |
|---|---|---|
| APOGEE epoch-RV | Verified the DR17 visit-level fields and quality semantics; corrected/extended the extraction path to retain true `JD`, `VHELIO`, `VRELERR`, visit flags, and a stricter persistence-flag sensitivity subset. Added unit tests. | **PARTIAL — no target visit table downloaded** |
| Exact APOGEE cadence | Built the per-source mapping/extraction and cadence-conditioned injection workflow. The injector uses each observed JD and its reported error, rather than the previous matched-epoch-count/baseline proxy. | **PARTIAL — cannot execute without exact visits and Gaia↔APOGEE mapping** |
| GALAH epoch-RV | Prepared 22 exact-ID query chunks covering 2,102 candidate source IDs, a resumable VizieR downloader, a per-source RV summarizer, and synthetic parser tests. | **PARTIAL — no survey rows retrieved** |
| LAMOST epoch-RV | Verified DR9 v2.0 Multiple Epoch Catalog fields and prepared exact `obsid_list`/`midmjm_list` expansion, per-spectrum join, Gaia DR3 matching, and reject logging. | **PARTIAL — no catalogue tables retrieved** |
| 746 lineage | Recomputed set membership from archived inputs and isolated exactly which population subtraction yields 746 IDs. | **Forensic computation complete; historical discrepancy unresolved** |
| 33/95 filter reasons | Reconstructed all available pre-VB H10 filters and confirmed all 33 missing IDs pass them. | **PARTIAL — downstream exclusion cause not identifiable** |
| 95-object selection correction | Reproduced the 95-object sample and tested propensity overlap/sensitivity against its 2,119-object parent. | **Closed as non-estimable: no defensible correction** |
| Independent compact-companion confirmation | Cross-matched the available literature RV-followed NS reference set and inspected the one scored overlap. | **BLOCKED as formal validation; one out-of-domain sanity check only** |
| DR4 blind evaluation | Rechecked and preserved the local pre-release configuration/hash freeze and blind-evaluation boundary. | **PARTIAL — no DR4 data; local freeze only** |

## 1. APOGEE and exact cadence

The official SDSS DR17 guide specifies visit-level `VHELIO` (barycentric-corrected despite the historical column name), `VRELERR`, and the visit midpoint Julian Date. The integer `MJD` field is not an adequate substitute for the actual cadence timestamp. The guide also documents the primary bad-visit flags and recommends additional persistence cuts for the highest-quality subset.

The project now has:
- Gaia DR3 `source_id` to APOGEE ID mapping instructions using allStarLite;
- a visit extractor using actual visit `JD`, `VHELIO`, and `VRELERR`;
- a strict-quality sensitivity output excluding the persistence flags;
- an exact-cadence injection script with fixed grid/seed controls and tests.

**No real epoch-RV result is added in this closeout.** The archive lacks the original visit-level rows and a complete verified source-ID/APOGEE-ID mapping for the 46 previously analysed targets. A previous audit's 414k simulations matched epoch count and baseline only and remain labelled a proxy, not exact cadence. Runtime DNS resolution for `data.sdss.org` failed, so the official allVisit/allStarLite files could not be downloaded.

## 2. GALAH epoch-RV

The project contains 22 query chunks for the 2,102-object candidate parent and a resumable acquisition program. The pipeline joins the source-level Gaia-to-GALAH mapping to per-spectrum GALAH observations, retains the per-spectrum RV, uncertainty, method flag and epoch, and emits source-level continuous variability diagnostics. The summarizer's self-test passed, but it uses synthetic rows only.

No empirical query result, matched-object count, epoch count, or variability count is reported. The VizieR host did not resolve in the runtime. GALAH non-matches must not be interpreted as RV-constant controls; only valid per-spectrum measurements with approved RV method flags can enter the analysis.

## 3. LAMOST epoch-RV

Official LAMOST DR9 v2.0 documentation confirms a Multiple Epoch Catalog with aligned `obsid_list`, `midmjm_list`, and `rv_list` entries, and identifies the corresponding spectrum-level catalogue fields. The implementation uses the spectrum `obsid` to join to per-spectrum A/F/G/K rows and uses the spectrum-level Gaia DR3 identifier for cross-match; it does not assume that the multi-epoch `gp_id` is always a Gaia ID.

The processor checks list lengths and `obs_number`, preserves rejected/misaligned rows for audit, and converts modified Julian minutes to MJD days. No DR9 catalogue data were downloaded because LAMOST host DNS resolution failed. Thus there are no empirical LAMOST matches or RV-variability results in this package.

## 4. 746 lineage: two numerically equal but distinct discrepancies

The archived inputs establish:

- raw NSS: 71,759 rows / 71,759 unique IDs;
- mechanism-scored: 10,118 rows / 10,118 unique IDs;
- intersection: 9,372 IDs;
- mechanism-scored-only: **746 IDs**;
- raw-NSS-only: 62,387 IDs.

The 746 mechanism-only IDs are not members of the archived 2,119 candidate parent, the 95-object C/H subset, or the 95-object characterisation subset.

Separately, a historical H10 count difference was reported as `2,672 - 1,926 = 746`. The original historical row-level inputs/IDs needed to prove whether those 746 are the same objects are absent. **The equal number is not proof of equal identity.** These are maintained as two separate lineage questions. The exact raw-vs-mechanism set subtraction is now fully reproducible; the historical H10 discrepancy remains unresolved.

## 5. 33 of 95: maximum identifiable filter explanation

All 95 characterisation IDs exist in raw NSS, the candidate table, and the C/H table. Of them, 62 appear in `mechanism_scored`; 33 do not.

For each of the 33, the reconstructed pre-VB H10 screen found:
- colour failures: 0;
- `dm` failures: 0;
- positive finite primary-mass failures: 0;
- non-finite required `TI` failures: 0;
- already sealed: 0.

Therefore all 33 pass every reconstructed early filter. The exact downstream exclusion reason cannot be identified without the absent `dark_companion_scored.csv`, VBroad calibration inputs, and complete 33,464-row source-query export. The audit explicitly leaves the final cause unknown rather than guessing. The primary-mass reconstruction uses the same H10 `mass_from_MG` fallback because the archived 95-row table does not contain `binary_masses.m1`.

## 6. 95-object selection correction: tested and rejected as non-identifiable

The 95-object sample membership was exactly reproduced from the 2,119-object candidate parent. It is a census of the parent `AstroSpectroSB1` subgroup (94/94) plus one `OrbitalTargetedSearchValidated` object, not a representative draw from the full parent. The other 2,024 candidates lack compatible `rho`-based outcome labels in the archived data and are mainly from other NSS solution types.

The 95-object label counts are 42 luminous-impostor, 2 dark-compatible, and 51 undetermined. A diagnostic propensity model separates selected and nonselected objects strongly (cross-validated selection AUC approximately 0.94–0.95). In the C=0.1 sensitivity, 63.8% of nonselected candidates fall below the minimum selected propensity and the weighted effective sample size is only 27.6/95. Across C=0.01–10, overlap and balance remain problematic; the maximum post-weighting absolute standardised mean difference remains about 1.8, driven in part by photometric magnitude/colour.

**Conclusion: no defensible general-population prevalence/label correction can be estimated.** The weights are diagnostic only. They cannot create missing outcomes or restore positivity. This is a completed negative audit finding, not a successful correction.

A unit check also confirmed that the archived `m2_dyn` values are in Jupiter masses, not solar masses; the audit output and labels were corrected accordingly.

## 7. External compact-object evidence

The cross-match of 21 published RV-followed neutron-star candidate systems yields 6 in raw NSS, 0 in the GAIA-FP 2,119-object candidate parent, 1 in `mechanism_scored`, and 0 in the 95-object physical-characterisation sample. The sole scored overlap is Gaia DR3 `1801110822095134848`; its H10 label is undetermined (`-1`). It lies in a low/dark-consistent score tail, but is not an independently confirmed positive/negative label in the GAIA-FP validation cohort.

This is an out-of-domain, one-object sanity check only. It cannot estimate sensitivity, specificity, false-positive rate, or AUC. The reference literature also discusses remaining white-dwarf alternatives, so this match is not treated as definitive compact-object ground truth.

## 8. Corrected S1 score recomputation and reconciliation

The corrected S1 score was regenerated for all 10,118 mechanism-scored rows from the archived input. On the 1,926 available labelled rows (841 luminous and 1,085 dark-consistent):

| Score | Recomputed AUC |
|---|---:|
| B2 | 0.731832 |
| VB | 0.754815 |
| B2 + VB | 0.795541 |
| Corrected S1, c=1 | **0.776327** |

The erratum reference AUC is 0.776366; the absolute difference is `0.00003844`, within the project's reproduction tolerance. S1 improves on B2 alone, but it does **not** outperform B2+VB. The corrected output and input/output SHA-256 hashes are preserved in `results/final_completion/S1_CORRECTED_c1_VALIDATION.json`.

One unresolved historical count mismatch remains: the prior baseline reconciliation records 1,927 labelled observations (841 positive, 1,086 negative), while the recoverable row-level files provide 1,926 (841 + 1,085). The missing extra negative cannot be identified without the old H10 input. Accordingly, no claim is made that the exact historical 1,927-row analysis was fully reconstructed.

## 9. DR4 blind-evaluation readiness

The local freeze records the v3.2 primary model, v3.1 registered comparator, A6 implementation/threshold state, configuration hash, and evaluation boundary. The freeze is labelled **LOCAL_PRE_RELEASE_HASH_FREEZE_NOT_OSF_REGISTERED**. The v0.6 amendment remains a local draft; it must not be described as OSF-registered. The actual DR4 blind test has not been run. ESA's current schedule lists Gaia DR4 as expected in December 2026.

## 10. Test and code verification

A single-process complete repository run was executed after the latest changes:

```text
pytest -q
125 passed in 23.57s
```

This supersedes the earlier file-by-file-only/timeout note. `test_final_epoch_rv.py` contains the new epoch-RV unit coverage, including the APOGEE strict-quality subset. The GALAH summarizer synthetic self-test also passed; it is a parser/logic check only, not evidence from GALAH observations. Relevant audit and epoch-RV scripts compile successfully with `py_compile`.

## 11. Files added/updated in this closeout

- `APOGEE_EXACT_CADENCE_GUIDE_2026-11-03.md`
- `GALAH_EPOCH_RV_DOWNLOAD_GUIDE_2026-11-03.md`
- `LAMOST_EPOCH_RV_DOWNLOAD_GUIDE_2026-11-03.md`
- `tools/epoch_rv/process_apogee_allvisit.py`
- `tools/epoch_rv/process_lamost_dr9_lrs.py`
- `tools/qa_audits/download_galah_epoch_rv.py`
- `tools/qa_audits/summarize_galah_epoch_rv.py`
- `tools/qa_audits/audit_selection_bias_95.py` (units/solution-type audit output corrected)
- `tools/qa_audits/reconstruct_95_filter_stages.py`
- `tools/qa_audits/audit_lineage_746.py`
- `tools/qa_audits/build_external_compact_object_validation.py`
- `tools/qa_audits/recompute_corrected_s1.py`
- `tests/test_final_epoch_rv.py`
- `results/final_completion/` (row-level lineage, corrected scores, external reference cross-match, and audit JSON/CSVs)

## Final claim boundary

The GAIA-FP package is now materially more reproducible and its archive-level forensic questions are narrowed with explicit evidence. However, the outstanding observational work remains outstanding because actual external epoch data were not available to this runtime. No APOGEE/GALAH/LAMOST variability discoveries, no corrected parent-population rate, no independently validated compact companion, and no Gaia DR4 blind-test performance are claimed. These limits must be preserved in any ISEF submission, paper, poster, or presentation.

## Official data references

- SDSS DR17 APOGEE visit-level radial velocities and quality flags: https://www.sdss4.org/dr17/irspec/use-radial-velocities/
- LAMOST DR9 v2.0 catalogue description (includes epoch-list fields): https://lamost.org/dr9/v2.0/doc/lr-data-production-description
- LAMOST DR9 v2.0 catalogue downloads: https://www.lamost.org/dr9/v2.0/catalogue
- GALAH DR3 data schema: https://www.galah-survey.org/dr3/table_schema/
- ESA Gaia archive release schedule: https://www.esa.int/Science_Exploration/Space_Science/Gaia/%28archive%29/0
