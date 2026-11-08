# GAIA-FP — pre-DR4 development closeout audit

**Snapshot date:** 2 November 2026  
**Scope:** archived Gaia DR3 development work, available APOGEE visit-level analysis outputs, SB2 positive-control enrichment, mechanism data lineage, and locally re-executed software tests.  
**Status:** a useful DR3 development/reproducibility supplement can be archived; the project is **not yet a complete empirical validation of compact/dark companions**.

## Executive result

The work produced several defensible positive or informative results, but no result supports claiming that GAIA-FP has been independently validated as a compact-companion detector.

### Strongest positive-control finding

Among 2,102 candidates, 16 are independently cross-matched to survey SB2 catalogues (13 APOGEE, 2 GALAH, 1 LAMOST). A post-hoc CMD-marginal ranking places 10/16 known SB2 controls in the top 20% (421 objects), versus 3.20 expected under random ranking: 3.12x enrichment, nominal hypergeometric p=2.35e-4 and Holm-adjusted p=0.00118 across five tested variants. The original full joint score places 5/16 in the top 20% (Holm p=0.202). This is a positive-control concentration result, not a validated AUC/specificity/precision estimate: the other 2,086 objects are **unlabelled**, not confirmed non-SB2 stars, and the analysis reuses the same 16 positive controls across variants. The positives are also predominantly APOGEE, so cross-survey replication is not established.

The fixed prior does not itself improve ranking: mathematically it adds a constant to every object's log-odds, leaving ranks, AUC and top-k membership unchanged. The challenger should remain a follow-up ranking hypothesis, not a calibrated probability model or replacement for GAIA-FP.

### Real APOGEE radial-velocity evidence

The archived APOGEE audit reports 622 parsed response rows and 351 accepted visit records for 46 objects with at least three distinct integer-MJD epochs (18 H10-positive, 28 H10-negative). The Round-7 summary reports 42/46 nominal constant-RV detections and 30/46 under the 0.5 km/s uncertainty-floor scenario. A separate user-supplied H10 group audit reports no statistically significant difference between positive and negative groups in excess scatter, RV range or reduced chi-square. The observed variability does not establish a dark/compact companion and is strongly affected by epoch count and time baseline.

The exact 351-visit timestamp table/raw SQL response bundle was not located in the current deposit inputs. Therefore the audit's 46-object results are preserved as reported outputs, but this package cannot independently regenerate the visit-level chi-square analysis from the raw 351 rows.

### Injection–recovery boundary

Synthetic phase injection was run under six stipulated scenarios. An additional cadence-summary-matched experiment used the real objects' epoch counts and baselines, but randomized visit times within each baseline (1,380 object-scenario cells, 414,000 injections). This is a useful sensitivity proxy, **not exact observed-cadence injection–recovery**. Exact cadence still needs the actual JD/MJD timestamps. No Gaia DR4 epoch-RVS injection or real epoch-RVS ablation was performed.

### Corrected baseline comparison

The corrected 1,926-object H10 complete-case comparison reports B2 AUC=0.73191, VB=0.75500, B2+VB=0.79569, and physical S1=0.77637. S1 improves on B2 alone by +0.04446 (95% CI +0.03340 to +0.05510), but is below B2+VB by -0.01932 (95% CI -0.03149 to -0.00747). S1 therefore does **not** beat the stronger empirical B2+VB baseline. The previously registered 1,927-object H10 result is retained as a historical result; the 1,926 count belongs to the corrected complete-case re-analysis and should not be silently conflated with it.

An exploratory `vbroad_error` ablation reported gains over B2+VB within the same selected H10 sample, but `vbroad_error` is strongly related to `grvs_mag`, `vb_sig` and line width. That finding is hypothesis-generating only; it is not independent validation and should not replace the frozen baseline before a fresh, independently labelled test.

## New reproducible 95-object crosswalk

The new object-level crosswalk confirms:

- All **95/95** selected dynamical-label objects are present in the 22,127-row H10/B2 audit table.
- All **95/95** pass that table's H10 common colour/photometric filter (`exclusion_reason = included`).
- Only **62/95** appear in `mechanism_scored.csv`; **33** are absent at the later mechanism stage.
- Among the 33 absent objects, 12 have H8 label 1 (impostor), 2 label 0 (dark-compatible), and 19 label -1 (indeterminate).

This closes the earlier ambiguity about whether those 33 were missing from the broad H10 common-filter population: they were not. It does **not** identify the individual downstream exclusion reasons. The mechanism code requires finite `vbroad`, at least 5 `vbroad_nb_transits`, finite `vb_med`, positive `vb_sig`, and finite downstream physical variables. The exact upstream `dark_companion_scored.csv` that would permit per-object filter diagnosis is absent.

The 95-object subset is visibly selected relative to the remaining H10-common-filter population (n=17,117). Standardized mean differences are B2=+0.237, BP-RP=+1.824, MG=+1.428, and dm=+0.064. The strong colour and absolute-magnitude shifts confirm that the 95-object set is not representative of the broad H10 population. These are descriptive diagnostics, not a post-hoc weighting correction.

## Two different 746 counts — do not merge them

1. **2,672 input rows → 1,926 unique Gaia IDs:** the user clarified that 746 is the number of excess duplicate rows removed, not 746 distinct IDs. The original 2,672-row input is absent from the current snapshot, so the duplicate-frequency distribution and retained-row policy cannot be independently reconstructed here.
2. **Mechanism output vs. raw Gaia NSS extract:** 10,118 unique mechanism IDs were compared with a separate 71,759-row Gaia Archive extract; 9,372 overlap and 746 do not. The corrected lineage audit shows the source populations were created with different query/selection rules (including distinct joins and physical/parallax cuts). These are not shown to be corrupt IDs or a simple formatting error. The exact upstream `dark_companion_scored.csv` and original full AstroSpectroSB1 parent table are absent, so per-ID provenance remains unresolved. Do not describe these two 746 counts as the same phenomenon.

## Software verification performed in this runtime

The test files were executed in separate groups, not one single monolithic run:

- Main project suite: **112 passed** across split test groups.
- External APOGEE/GALAH/LAMOST epoch-RV ingestion and variability pipeline fixture tests: **30 passed**.
- Geometry audit: **48 passed, 17 expected xfailed**.
- Statistical audit: **17 passed, 18 expected xfailed**.

Total across separately executed groups: **207 passed, 35 expected xfailed**. A monolithic run exceeded the runtime time limit, so these counts should not be represented as one uninterrupted 207-test invocation. Expected xfails are documented edge cases, not passes. Warnings in degenerate numerical tests were retained as warnings, not treated as successful scientific outputs. Passing software tests verifies code contracts, not astrophysical validity.

## Open blockers that cannot be honestly completed from this archive

1. Recover the original 2,672-row input to reproduce the first deduplication audit exactly.
2. Recover `realdata/dr3_astrospectro_all.csv` and `results/dark_companion_scored.csv` to identify the exact downstream filters for each of the 33 missing labels and close source-level lineage.
3. Recover APOGEE raw accepted visits (351 rows with source ID and individual JD/MJD) to reproduce exact real-cadence injection–recovery.
4. Acquire usable per-epoch GALAH and LAMOST RV data. Catalogue SB2 flags alone are not epoch-level RV variability measurements.
5. Obtain a coverage-qualified external set with independently determined positive and negative labels. Do not call the 2,086 SB2-unmatched candidates negatives.
6. Obtain independent dynamical/ RV confirmation for compact or dark companion candidates. The 95-object Gaia self-consistency check is not an independent telescope confirmation.
7. Gaia DR4 real epoch-RVS validation, schema/unit audit and blind evaluation remain future work. The project runbook schedules the DR4 release for 2 December 2026; on this snapshot date (2 November 2026), it is not yet available.

The VizieR catalogue page currently lists 33,467 rows for Gaia DR3 `I/357/tboasb1c`, but catalogue availability is not the same as recovering the project's missing joined/filter-specific source file. LAMOST DR10 MRS provides exposure-level RV fields, and the local pipeline has fixture tests; no real LAMOST epoch table was retrieved in this runtime.

## Publication recommendation

A defensible release now is titled as a **Gaia DR3 development and reproducibility supplement**, with positive-control enrichment, APOGEE variability and limitations clearly distinguished. It should not be titled or abstracted as a validated compact-companion detector or a confirmed dark-companion discovery.

The main paper should be framed as a methods/development and audit report. The next confirmatory milestone should be the preregistered DR4 blind evaluation after the real DR4 schema and measurements are available. Keep all post-hoc SB2 ranking variants labelled exploratory.

## DOI status

The project README lists two existing OSF DOIs for pre-registration records: `10.17605/OSF.IO/N5H4B` and `10.17605/OSF.IO/TBJGY`. These are pre-registration/amendment records, not a DOI for this new software/data supplement. The present package is a **deposit draft**; no new DOI has been reserved or published in this runtime. A new Zenodo DOI requires the project owner's authenticated deposit and publication action. Zenodo says a DOI can be reserved in a draft, but it is only registered when the record is published; publication is a separate action.

## Files in this supplement

- `inputs/`: exact derivative/source CSVs used by this closeout, including the 22,127 H10/B2 audit, labels, mechanism output, ablation scores, SB2 crossmatch, and APOGEE per-object summaries.
- `reports/`: previous Round-5/6/7, SB2, provenance and lineage audit reports.
- `code/reproduce_closeout_audit.py`: relative-path script reproducing this closeout's selected-95 crosswalk, selection diagnostics and SB2 top-20 statistics.
- `recomputed/`: saved results from this turn, plus the local test-execution ledger.

**Not included because unavailable in the archived workspace:** full VizieR–Gaia joined AstroSpectroSB1 source file, upstream `dark_companion_scored.csv`, original 2,672-row dedup input, raw 351-visit APOGEE rows, per-epoch GALAH/LAMOST data, and Gaia DR4 data.
