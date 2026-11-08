# GAIA-FP — Mechanism score data-lineage audit

Date: 2026-11-01

## Scope

Compared the archived `results/mechanism_scored.csv` against `realdata/dr3_nss_two_body_orbit_raw.csv` using decimal-string source IDs. Also searched every available CSV in the extracted project snapshot for the 746 unmatched IDs and checked whether the raw NSS file contains the inputs required for full-population mechanism scoring. No original files were modified.

## Reproduced counts

- Raw NSS table: **71,759** rows, **71,759** unique IDs.
- Mechanism score table: **10,118** rows, **10,118** unique IDs.
- Mechanism IDs exactly present in raw NSS: **9,372 (92.63%)**.
- Mechanism IDs absent from raw NSS: **746 (7.37%)**.
- Selected 95 labels present in mechanism scores: **62/95**; absent: **33/95**.

## Critical lineage finding

The 746 unmatched IDs are not explained by a simple ID-format mismatch detectable from the archived files. For these 746 rows, **0** have an exact match in the raw NSS table on the ten shared orbital/astrometric fields at 8 decimal places; even rounding these fields to 2 decimal places gives **0** matches. The scan of all ID-named columns in all available CSVs found only the cross-file matches listed in `LINEAGE_AUDIT_SUMMARY.json` (not a second full population source).

Therefore the current archive does **not** establish the provenance of the 746 IDs. It would be scientifically unsafe to call them 746 rounded versions of valid NSS IDs, or to assert that they belong to a different release. The upstream input used to create `mechanism_scored.csv` (`results/dark_companion_scored.csv`, as specified in `src/mechanism.py`) is absent from the archived snapshot, and the full `realdata/dr3_astrospectro_all.csv` input expected by `src/dark_companion.py` is also absent. This prevents definitive lineage reconstruction.

## Selected-95 coverage

Only 62 of the selected 95 labels appear in `mechanism_scored.csv`. The remaining 33 cannot be assumed to be absent from the original AstroSpectroSB1 population: `mechanism_scored.csv` is a filtered output (the mechanism code applies vbroad/transit and finite-physics requirements). The missing upstream full scored file prevents identifying each exclusion reason.

## Full-population feature availability

The archived raw NSS file has 21 columns. It does not include the line-width fields (`vbroad`, `vbroad_error`, `vbroad_nb_transits`, `grvs_mag`), nor the full C/H Thiele-Innes terms and derived quantities needed by the mechanism/S1 pipeline. The archived `dr3_astrospectro_ch.csv` is only a 95-row selected-sample table. Hence the current archive cannot support a 22,127-object VB/S1/B2+VB re-score.


## Sensitivity of the pre-registered mechanism results to the 746 unmatched IDs

I recomputed the pre-registered partial-rank correlations separately in (a) the 9,372 rows whose IDs exactly match the archived raw NSS table and (b) the 746 unmatched rows. The same rank-transform / covariate-residualization procedure and 2,000 system-bootstrap resamples (seed 7) were used. These are a lineage sensitivity analysis, not a replacement for the registered full-sample result.

| Subset | n | M1: partial rho(VB,b) | M2b: rho(b)-rho(k) | M2a dark: partial rho(VB,k) | M4 median c, n(b>=25) |
|---|---:|---:|---:|---:|---:|
| All mechanism rows | 10,118 | +0.2180 [0.1991, 0.2369] | +0.1253 [0.1075, 0.1441] | See registered full result | 1.787, n=1,729 |
| Exact NSS-ID matches | 9,372 | **+0.2240 [0.2052, 0.2428]** | **+0.1291 [0.1097, 0.1485]** | -0.0903 [-0.1508, -0.0272] | **1.984, n=1,545** |
| Unmatched IDs | 746 | +0.1447 [0.0742, 0.2151] | +0.0682 [0.0050, 0.1292] | -0.4022 [-0.6107, -0.1589] | **0.755, n=184** |

Interpretation: the principal M1 and M2b positive associations remain present, and are slightly stronger, when restricted to the 9,372 exact NSS-ID matches. Thus the 746 unmatched rows do **not** appear necessary to obtain the main line-blending association. However, the M4 amplitude estimate is materially sensitive to the unmatched subset: its median is 1.984 in exact matches versus 0.755 in unmatched rows. The full-sample M4 estimate should therefore not be treated as fully lineage-secure until the 746 rows are explained.

The unmatched subset has 45 label-1, 45 label-0, and 656 label--1 rows. The exact-match subset has 796 label-1, 1,040 label-0, and 7,536 label--1 rows.

## What is established vs not established

**Established:** the 746 exact-ID mismatch exists; 9,372 mechanism IDs match; 62/95 selected labels occur in the mechanism output; the archived raw NSS schema is insufficient for full-population VB/S1 scoring.

**Not established:** the reason for the 746 mismatches; whether the mismatch arose upstream, from a different catalogue snapshot, an ID crossmatch, or a data-export issue; the exclusion reason for each of the 33 selected labels missing from the mechanism output.

## Required next action

Recover and audit the exact upstream `dark_companion_scored.csv` and `dr3_astrospectro_all.csv` used for the mechanism run, with `source_id` read and preserved as decimal strings/integers. Re-run the ID join against the exact NSS source snapshot used to generate them. Until then, do not merge the 746 IDs by nearest-neighbour or approximate matching and do not treat `mechanism_scored.csv` as a full-population companion table.
