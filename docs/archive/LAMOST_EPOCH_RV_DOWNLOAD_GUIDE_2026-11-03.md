# LAMOST DR9 v2.0 LRS exact-epoch RV analysis — GAIA-FP

## Verified public product

LAMOST DR9 v2.0 exposes both the LRS A/F/G/K per-spectrum stellar-parameter catalogue and a Multiple Epoch Catalog. The release documentation reports 1,962,095 sources in the Multiple Epoch Catalog. Its `obsid_list` and `midmjm_list` fields are aligned, hyphen-delimited lists: each `obsid` identifies one spectrum and each `midmjm` is the Modified-Julian-minute timestamp at the middle of that night's multiple exposures. Join each `obsid` to the per-spectrum A/F/G/K catalogue, which supplies the spectrum-level `gaia_source_id`, `rv`, `rv_err`, S/N, and fibre information.

The Multiple Epoch Catalog itself does **not** carry a guaranteed Gaia DR3 `source_id` in every record; use the spectrum-level AFGK table's `gaia_source_id` for the exact Gaia DR3 cross-match. Do not rely on the multiple-epoch `gp_id` field as if it were always a Gaia ID.

Official references: [LAMOST DR9 v2.0 LRS data description](https://lamost.org/dr9/v2.0/doc/lr-data-production-description), [catalogue download page](https://www.lamost.org/dr9/v2.0/catalogue), [DR9 v2.0 home](https://lamost.org/dr9/).

## Required downloads

From the official catalogue page, download both:
1. **LAMOST LRS Stellar Parameter Catalog of A, F, G and K Stars** (CSV or FITS); required fields include `obsid`, `gaia_source_id`, `rv`, and `rv_err`.
2. **LAMOST LRS Multiple Epoch Catalog** (CSV or FITS); required fields include `obs_number`, `obsid_list`, and `midmjm_list`.

Use the exact direct-download links provided by the official catalogue portal. The downloader intentionally does not guess catalogue URLs.

## Run exact timing path

```bash
python tools/epoch_rv/process_lamost_dr9_lrs.py \
  --input /path/LAMOST_DR9_LRS_AFGK.csv \
  --multi-epoch /path/LAMOST_DR9_LRS_Multiple_Epoch.csv \
  --candidates realdata/dr3_candidates.csv \
  --outdir results/final_completion/lamost_epoch_rv
```

The script verifies that the per-source `obsid_list` and `midmjm_list` have equal lengths (and match `obs_number` when present), expands the pairs, joins on `obsid`, then matches `gaia_source_id == source_id`. It converts `midmjm` minutes to MJD days as `midmjm / 1440`. Misaligned or conflicting pairs are written to a rejects file rather than silently repaired.

A fallback without `--multi-epoch` uses per-spectrum `mjd`; that is a less precise timing path and **must not be called the exact multi-epoch timestamp analysis**.

## Quality and interpretation

- Require finite RV, finite positive `rv_err`, finite epoch, and `fibertype=Obj` where the field is supplied.
- Preserve S/N and `fibermask` for audit; do not assume undocumented fibre-mask bit semantics.
- The catalogue has survey-specific target/SNR selection, so nonmatches are not RV-constant controls.
- A low constant-RV chi-square p-value is evidence of disagreement with a constant-RV model under the quoted formal errors; it is not proof of a compact companion.
- Deduplicate only identical `(Gaia DR3 source_id, obsid)` rows; no unreviewed averaging of distinct spectra.

## Status

**PARTIAL — exact obsid/MIDMJM processing code and synthetic tests complete; no LAMOST tables downloaded or measured in this run.** The local execution environment could not resolve the LAMOST hosts (`NameResolutionError`), so no empirical match count or RV-variability result is claimed.
