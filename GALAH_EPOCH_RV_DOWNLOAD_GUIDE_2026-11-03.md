# GALAH DR3 per-spectrum radial-velocity analysis — GAIA-FP

## Data model and schema cross-check

GALAH DR3 provides repeated spectra indexed by `sobject_id`; the main all-spectra catalogue supplies Gaia DR3 `dr3_source_id`, while the radial-velocity value-added catalogue supplies the per-spectrum RV, uncertainty, method flag and epoch. The official GALAH schema identifies `sobject_id` as the catalogue join key and describes `use_rv_flag` values 0 (`rv_obst`), 1 (`rv_sme_v2`), 2 (Gaia DR2 fallback), and 4 (no usable method). It defines `rv_galah`/`e_rv_galah` in km/s and `heliocentricJD` / `MJD_local` as exposure-midpoint times.

The packaged VizieR cross-match uses the corresponding public catalogue tables `J/MNRAS/506/150/spect` and `J/MNRAS/506/150/rv`, joining on the GALAH identifier (`GALAH`). Its column names are the VizieR representation (`GaiaEDR3`, `RVgalah`, `e_RVgalah`, `f_RVgalah`, `HJD`, `MJDlocal`) rather than the Data Central FITS names above. The query files alias them to a stable lower-case CSV schema. Do not mix VizieR and Data Central column names in the same query.

Official schema: [GALAH DR3 table schema](https://www.galah-survey.org/dr3/table_schema/). VizieR source/catalogue family: `J/MNRAS/506/150`.

## Query package and target scope

The archive includes 22 ADQL chunks for **2,102 unique source IDs** from `results/dr3_candidates_scored.csv` / `candidate_source_ids.txt`, 100 IDs per chunk except the final partial chunk. Each query returns:

`source_id, galah_id, rv_kms, rv_error_kms, rv_method_flag, hjd, mjd_local`

The chunks join per-spectrum Gaia-to-GALAH identifiers to per-observation RVs through `GALAH`. Query files live in `results/qa2/partial_completion/galah_adql/`.

## Download and analyse

```bash
# Resumable; downloads and header-checks each of the 22 VizieR TAP chunks.
python tools/qa_audits/download_galah_epoch_rv.py \
  --raw-dir realdata/galah_epoch_rv_chunks \
  --combined realdata/galah_epoch_rv_crossmatch.csv

# Continuous per-source RV diagnostics; no post-hoc binary cut.
python tools/qa_audits/summarize_galah_epoch_rv.py \
  --input realdata/galah_epoch_rv_crossmatch.csv \
  --outdir results/final_completion/galah_epoch_rv
```

The downloader is resumable: it skips previously downloaded chunks with the expected output columns and combines all chunk responses after a complete 1–22 run. The summarizer keeps only `rv_method_flag` 0 and 1, finite RV and finite positive errors. It prefers HJD for each source; if HJD exists for any row, missing-HJD rows are not filled from MJDlocal. If HJD is wholly absent, it uses MJDlocal. It collapses exact duplicate GALAH ID/epoch rows by inverse-variance weighting and reports number of epochs, baseline, weighted mean/RMS, peak-to-peak range, robust MAD, constant-RV chi-square and p-value.

Synthetic parser check only:

```bash
python tools/qa_audits/summarize_galah_epoch_rv.py --selftest
```

The self-test does not create observational evidence. A low chi-square p-value is a variability diagnostic under reported errors, not proof of a compact companion. Repeated same-night spectra and correlated systematics should be inspected before a confirmatory inference.

## Status

**PARTIAL — 22 exact-ID query files, resumable downloader, summarizer and synthetic self-test are prepared; no observational CSV was retrieved.** The runtime could not resolve `tapvizier.cds.unistra.fr`. Therefore the archive contains no empirical GALAH match count, epoch count, or RV-variable count from this query package.
