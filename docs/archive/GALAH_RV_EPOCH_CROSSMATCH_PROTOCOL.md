# GALAH DR3 epoch-RV cross-match protocol — GAIA-FP

**Status (2026-11-01): query package and summarizer prepared; external epoch rows not downloaded in this runtime.** This is a reproducible data-acquisition protocol, not a completed RV-variability result.

## Why this cross-match

The local GAIA-FP package contains published SB2 cross-matches to GALAH, LAMOST-MRS and APOGEE. Those flags identify systems in selected SB2 catalogues; they do not constitute a general per-epoch radial-velocity (RV) variability test. GALAH DR3 makes per-spectrum measurements available through `J/MNRAS/506/150/spect` and per-observation RV data through `J/MNRAS/506/150/rv`. The `spect` table carries the Gaia EDR3 source identifier and GALAH `sobject_id`; the RV table contains `RVgalah`, `e_RVgalah`, `f_RVgalah`, `HJD`, and `MJDlocal`. The cross-table join key is `GALAH` / `sobject_id`. See the official GALAH DR3 catalogue schema and VizieR ReadMe for field definitions.

## Query package

- Target list: `results/qa2/partial_completion/galah_adql/candidate_source_ids.txt` (2,102 unique scored Gaia source IDs).
- Query files: `results/qa2/partial_completion/galah_adql/galah_epoch_rv_chunk_01.adql` onward; each query is chunked to 100 Gaia IDs to avoid excessively long ADQL statements.
- TAP service: VizieR TAP, catalogue tables `J/MNRAS/506/150/spect` and `J/MNRAS/506/150/rv`.
- Selected output fields: `source_id`, `galah_id`, `rv_kms`, `rv_error_kms`, `rv_method_flag`, `hjd`, `mjd_local`.

Each query joins the per-spectrum Gaia-to-GALAH mapping to the per-observation RV catalogue using the GALAH identifier. After downloading each CSV/VOTable response, concatenate the rows without changing numeric values, units, or method flags, and save as:

`realdata/galah_epoch_rv_crossmatch.csv`

## Prespecified quality handling

1. Keep method flags `0` and `1` only (GALAH-observed RV solutions). Exclude flags `2` (Gaia DR2 fallback) and `4` (no usable method) from the epoch-variability analysis.
2. Require finite RV and finite positive `e_RVgalah`.
3. Use one epoch scale per Gaia source: HJD is preferred if any usable HJD values exist for that source; otherwise use MJDlocal only if HJD is absent entirely. Do not mix HJD and MJDlocal within one source. If a source has a mixture of missing and present HJD, rows lacking HJD are excluded from time-series calculations.
4. Report per Gaia source: number of accepted epochs, baseline in days, inverse-variance weighted mean RV, weighted RMS about the mean, peak-to-peak RV range, robust MAD scatter, constant-RV chi-square, degrees of freedom, and chi-square survival probability.
5. Do not define a binary cutoff after viewing candidate outcomes. First report continuous metrics. Any binary threshold must be justified and frozen independently before it is used as a confirmatory endpoint.
6. A single epoch is not evidence for RV constancy; mark it as insufficient for variability assessment.

## Reproduce

From the project root:

```bash
python tools/qa_audits/summarize_galah_epoch_rv.py \
  --input realdata/galah_epoch_rv_crossmatch.csv \
  --outdir results/qa2/partial_completion/galah_epoch_rv
```

A synthetic-only parser check can be run with:

```bash
python tools/qa_audits/summarize_galah_epoch_rv.py --selftest
```

The self-test validates parsing/statistic calculations only; it is not astronomical evidence. The external file was not retrieved in this execution because the runtime could not resolve external catalogue hosts. Therefore no epoch-RV match count, variability significance, or RV-confirmed binary count is reported in this audit.

## Limitations

- GALAH is a magnitude-, footprint-, and target-selection-limited survey; non-matches are not evidence of RV constancy.
- RV epoch correlations / shared systematics may make a simple chi-square approximation optimistic; treat it as a diagnostic pending a more complete covariance model.
- Repeated spectra from one night may not be independent epochs; the output preserves individual measurements and the baseline so this can be assessed.
- This protocol does not replace APOGEE/LAMOST epoch RV products or a properly calibrated multi-survey RV meta-analysis.
