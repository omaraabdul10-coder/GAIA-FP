# GAIA-FP QA2 progress add-on — 1 Nov 2026

This add-on is layered over the supplied `GAIA-FP-v0_6-QA2` snapshot. It is a working engineering patch, **not** a replacement for the historical frozen manifest, not a new preregistration, and not evidence of Gaia DR4 scientific validation.

## Added

- `src/dr4_mechanism_guarded.py` — fail-closed preflight wrapper for H12–H14. Requires explicit DR3→DR4 ID mapping, the full DR3 AstroSpectroSB1 exclusion population, sealed IDs, valid orbit inputs, and valid field calibration before the unchanged mechanism scorer can run.
- `src/dr4_h12_prepare.py` — local, exact-ID join and provenance writer for separate candidate-orbit, candidate-RVS, field-CMD, and field-RVS tables.
- `tools/fetch_dr3_astrospectro.py` — asynchronous VizieR fetch for the D3 AstroSpectroSB1 population joined to Gaia DR3 source photometry/RVS measurements. The default 33,464-row guard is intended to stop an unexpected data revision or wrong query before overwriting the target.
- `tests/test_dr4_mechanism_guarded.py`, `tests/test_dr4_h12_prepare.py`, `tests/test_fetch_realdata.py` — synthetic/offline contract tests.
- `H6_RULE_DISCREPANCY.md` — explicit record of conflicting H6 definitions; no decision threshold was silently changed.
- `QA2_PROGRESS_REPORT_2026-11-01.md` — detailed status and reproducibility notes.

## Modified

- `tools/fetch_realdata.py` and `tools/ingest_queries.md` — full LAMOST-MRS coverage query with position columns, async timeout failure, validation, and SHA-256 provenance.
- `src/h6_runner.py`, `src/dr4_evaluate.py`, `tests/test_h6_runner.py` — document and test the behavior already present in the current v0.6 ledger; scientific behavior is unchanged.
- `DEVIATIONS_v0.6.md`, `DR3_STUDY_DEVIATIONS.md` — append dated reproduction/fetcher notes.

## Tests run

- `PYTHONPATH=src pytest -q`: **112 passed**.
- `PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py`: **65 passed, 35 xfailed, 14 warnings**.

The two suites were completed separately. A combined run reached the execution time limit, so no combined total is claimed.

## Important limits

- VizieR and Gaia network retrieval could not be completed in this runtime due to DNS/network resolution failure. The fetch scripts are query/schema tested offline, not live-fetched.
- `realdata/lamost_cov.csv`, `realdata/dr3_astrospectro_all.csv`, the official DR3–DR4 ID map, and actual DR4 candidate/field data remain absent.
- The 10,000-outer-iteration Monte Carlo remains not run.
- No DR4 results were generated; the H6 historical preregistration discrepancy remains open.
- The historical `FREEZE_MANIFEST_v0.6_DRAFT.sha256` was not rewritten to absorb this engineering add-on.


## Superseding scientific-audit addenda — 1 Nov 2026

The original “Important limits” block above is a snapshot from the earlier engineering add-on. The following later work supersedes only the relevant statuses:

- The 10,000-outer-iteration Monte Carlo null calibration **was completed**; see `QA2_SCIENTIFIC_AUDIT_2026-11-01.md` and its chunk summaries. It is synthetic null calibration, not Gaia validation.
- Local SB2 catalogue cross-matches were independently recomputed for all 2,102 scored candidates and exactly reconciled to archived flags; see `results/qa2/partial_completion/rv_crossmatch_audit.json`. This is not a general epoch-RV variability cross-match.
- Corrected H10 post-unit-fix baseline results were reconciled, including the stronger additive B2+VB baseline; GAIA-FP S1 is above CMD-only B2 but below B2+VB. See `results/qa2/partial_completion/baseline_comparison_reconciliation.json`.
- The selected 95-object AstroSpectroSB1 subset received expanded physical characterization and high-draw seed sensitivity analysis; this is not a representative population study.
- GALAH epoch-RV query and aggregation code are prepared, but external epoch rows have not been downloaded. No epoch-RV variability result is claimed.
- Injection–recovery and Gaia DR4 data processing/schema validation remain outstanding. A scoped real-DR3 2×2 ablation of the available joint astrometric/CMD likelihood and prior components has now been completed; the DR4 epoch-RVS component is not included because per-transit DR3/DR4 RVS rows are unavailable. See `results/qa2/partial_completion/ABLATION_DR3_COMPONENT_REPORT_2026-11-01.md`.

See `QA2_AUDIT_INDEX_2026-11-01.md` and `results/qa2/partial_completion/PARTIAL_ANALYSES_COMPLETION_REPORT_2026-11-01.md` for the complete addendum.
