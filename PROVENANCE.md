# Real-data provenance (Gaia DR3 study, H7-DR3)

All files here are **real archive data**, retrieved on 9 Oct 2026 in a browser session (the analysis workspace has no archive access) and transferred unchanged, except as noted below.

| File | Source | Query / table | Rows |
|---|---|---|---|
| dr3_candidates.csv | Gaia Archive TAP async, job e89e051c-c3b2-11f1-826d-bc97e148b76b-O | nss_two_body_orbit ⋈ binary_masses ⋈ gaia_source ⟕ dr2_neighbourhood, implied m2 < 80 MJ (full ADQL in provenance_gaia.txt) | 2209 returned; **71 rows of sealed objects removed in the browser before saving**; 2138 kept (2119 unique sources) |
| dr3_field.csv | Gaia Archive TAP sync | SELECT TOP 20000 phot_g_mean_mag, bp_rp, parallax FROM gaiadr3.gaia_source WHERE parallax_over_error>20 AND ruwe<1.2 AND non_single_star=0 AND parallax>5 AND random_index<3000000 | 2541 |
| sb2_lamost.csv | VizieR J/MNRAS/527/521/tableb1 (Kovalev+2024) | GaiaDR3 | 12426 |
| sb2_galah.csv | VizieR J/A+A/638/A145/catalog (Traven+2020) | GaiaDR2 | 12760 |
| sb2_apogee.csv | VizieR J/AJ/162/184/table1 (Kounkel+2021) | ID, RAJ2000, DEJ2000, SBn | 8105 |
| lamost_cov.csv (not committed, 13 MB; regenerate with tools/fetch_realdata.py) | VizieR J/ApJS/244/27/lamostMRS (Wang+2019) | Gaia, COUNT(*), AVG(RAJ2000), AVG(DEJ2000) GROUP BY Gaia | 292534 |

The only edit to the files: the requester IP address and browser user-agent lines were removed from provenance_gaia.txt (privacy).
A code check confirmed that **0** sealed source_ids are present in dr3_candidates.csv.

## SHA-256
```
53422f95c4606aedd52c123ba7e1b6b5ae6c532b37372fb03fd76a54965e3b0a realdata/dr3_candidates.csv
a0abe9525b964544004168739d760f5ea5175e35b2c02df4ccd014c6bf0890d0 realdata/dr3_field.csv
950de4a65ca62deb1a3300d4eafca35a8d9fa9e3e64b745dbd185379b7b8dca8 realdata/excluded_sealed_ids.csv
cc57e5909c05d2153f8793d823ed1904d366b202e79ffe5e49b8baa2d6a15dc1 realdata/lamost_cov.csv
6ca6743bd9578e47814fbd4a973bc8fb6e12776e73c26255b872ff90e77377cd realdata/sb2_apogee.csv
8ff5d67f86783afeea7d0481c5d33a37f19b8c32a911bdd1b6881496bc1677b8 realdata/sb2_galah.csv
4c8c54907e2e5a69f6f5106e380e0063f2e35050d3078ea58403d3c208b9ecb3 realdata/sb2_lamost.csv
e1f3425bc4a7b6e9699497f76ed8f11c7d6c28f5878fa90bd788d0e89177ab15 results/dr3_study.json
```
Data: ESA/Gaia/DPAC; CDS VizieR.

## APOGEE DR17 multi-visit (6 Nov 2026)
- **Source:** VizieR III/286/catalog via the CfA mirror (vizier.cfa.harvard.edu), queried with ASU-TSV.
- **Selection and columns:** Nvis ≥ 2, GaiaEDR3 > 0. Columns GaiaEDR3, Nvis, HRV, s_HRV, e_HRV, Ncomp, SNR, Teff, logg, Tel.
- **Processing:** downloaded in the user's built-in browser, staged to the analysis workspace, then deduplicated to one row per Gaia id (highest Nvis).
- **Result:** 485 709 rows. `external/apogee_dr17_multivisit.csv`, SHA-256 a942246a499aabacd9353316c74d71b607aaedffaec5164cbc8267c218a4765c.
