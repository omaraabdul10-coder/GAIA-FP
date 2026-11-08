# GAIA-FP — completion and ablation hand-off

Audit snapshot: 1 November 2026.

## Main verified additions

- Independent DR3 catalogue cross-match audited on 2,102 scored candidates: 16 unique SB2 catalogue matches across LAMOST-MRS, GALAH FGK and APOGEE. The remaining 2,086 are unlabelled, not verified negatives.
- Selected real-data characterization completed for the 95 AstroSpectroSB1 subset, including 50,000-draw sensitivity over seeds 0, 1 and 17; 94/95 labels stable across all three.
- H10 archived baseline comparison reconciled after the K-sum period-unit correction. Physical `vbroad` S1 improves over CMD-only B2 by +0.044 AUC [0.033, 0.055], but is below the stronger additive CMD+VB comparator by 0.019 AUC [0.007, 0.031]. Raw 33,463-row H10 source input is absent, so the archived result was not independently re-run here.
- DR3 2×2 component ablation, prior sensitivity and label-free v3.2 prior-selection bridge completed on the limited 16-positive / 2,086-unlabelled SB2 proxy. The frozen full model does not win this proxy ablation.
- Epoch-RVS phase mechanism injection/recovery completed synthetically under exact project A6 SB1 filtering, with six epoch/noise settings × three independent seeds = 18 runs. Mean ΔAUC across runs +0.081; 17/18 paired-bootstrap intervals above zero. The phase-scrambled negative control returns close to CMD-only. This is a synthetic mechanism test, not observed Gaia evidence.
- GALAH epoch-RV acquisition pipeline (22 query chunks, resumable downloader, quality-aware summarizer) is prepared. Actual external epoch rows could not be fetched in this runtime due DNS/network resolution failure.

## Validation

- `PYTHONPATH=src pytest -q`: 112 passed.
- `PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py`: 65 passed, 35 xfailed, 14 warnings (edge-case/degenerate-input warnings; no test failures).
- RVS injection script compiles and produces reproducible JSON/Markdown outputs.

## Remaining items that must not be claimed complete

1. Actual GALAH epoch-RV measurements and empirical RV variability cross-match.
2. H10 raw 33,463-row data/input bundle needed to rerun its archived baseline comparison from source rows.
3. Real Gaia DR4 schema/unit validation and DR4 epoch-RVS ablation after data release.
4. Full ablation of the empirical epoch-RVS component on observed epoch rows.

See `GAIA-FP_COMPLETION_AND_ABLATION_AUDIT_2026-11-01.md` for detailed methods, caveats and tables. New/updated reproducible scripts are under `tools/qa_audits/`.
