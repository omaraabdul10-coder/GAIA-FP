# GALAH DR3 epoch-RV download guide for GAIA-FP

The public GALAH DR3 per-spectrum and VAC RV tables expose 678,423 spectrum-level records. Join the `spect` and `rv` tables with the GALAH observation key (`GALAH` / `sobject_id`), and retain `GaiaEDR3`, `RVgalah`, `e_RVgalah`, `f_RVgalah`, `HJD`, and `MJDlocal`.

## Download

Run from an internet-connected Python environment with `requests` and `pandas` installed:

```bash
python tools/qa_audits/download_galah_epoch_rv.py
```

The downloader uses the 22 pre-generated ADQL query chunks, resumes already-valid chunks, and writes:

- raw chunk CSVs to `realdata/galah_epoch_rv_chunks/`;
- concatenated observations to `realdata/galah_epoch_rv_crossmatch.csv`.

To run a partial set first:

```bash
python tools/qa_audits/download_galah_epoch_rv.py --start 1 --stop 3
```

After all 22 chunks are present, run the full command once to combine them, then:

```bash
python tools/qa_audits/summarize_galah_epoch_rv.py \
  --input realdata/galah_epoch_rv_crossmatch.csv \
  --outdir results/qa2/partial_completion/galah_epoch_rv
```

## Fixed quality rules

- Use method flags 0 and 1 only; exclude flag 2 (Gaia DR2 fallback) and flag 4 (no method).
- Require finite RV and finite positive uncertainty.
- Never mix HJD and MJDlocal within a source. Prefer HJD; use MJDlocal only if HJD is absent for the entire source.
- Report continuous weighted-RV scatter, range, MAD, constant-RV chi-square and number/time baseline of epochs. Do not apply an after-the-fact binary threshold.
- The GALAH target footprint and magnitude selection mean absence of a match is not evidence of RV constancy.

## Current execution limitation (re-audited 2026-11-03)

The official GALAH DR3 release page confirms a 678,423-spectrum `main_allspec` catalogue and a 67 MB per-spectrum `VAC_rv` product. The VizieR `spect` and `rv` tables expose the required Gaia DR3 ID, `sobject_id`, RV, uncertainty, method flag, HJD and MJD-local fields. The downloader and 22 ADQL chunks are present; syntax/self-tests pass. Actual VizieR rows were not downloaded in this runtime because the environment could not resolve the remote catalogue hostname. No observed epoch-RV counts are claimed. Status: PARTIAL (public source + query pipeline ready; empirical run pending download).

## Verified catalogue documentation

- [Official GALAH DR3 catalogue page](https://www.galah-survey.org/dr3/the_catalogues/) — describes the per-spectrum catalogue and the 67 MB `GALAH_DR3_VAC_rv_v2.fits` product.
- [Official GALAH DR3 table schema](https://www.galah-survey.org/dr3/table_schema/) — documents `sobject_id`, `rv_galah`, `e_rv_galah`, `use_rv_flag`, `heliocentricJD`, and `MJD_local`.
- [VizieR GALAH DR3 per-spectrum table](https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/MNRAS/506/150/spect) and [per-spectrum RV VAC table](https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/MNRAS/506/150/rv).
- [CDS ReadMe for J/MNRAS/506/150](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/MNRAS/506/150?format=html&tex=true) — confirms the 678,423-row `spect` and `rv` tables and the observation-level join field.
