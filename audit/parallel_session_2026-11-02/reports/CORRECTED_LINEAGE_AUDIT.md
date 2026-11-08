# GAIA-FP — Corrected data-lineage audit

Date: 2026-11-01  
Scope: existing archived project files plus public VizieR catalogue metadata. No original project files modified.

## Executive correction

The earlier statement that the 746 `mechanism_scored.csv` IDs absent from `dr3_nss_two_body_orbit_raw.csv` represent an unexplained mismatch was too strong. The two files are **not the same upstream population extract**.

The archived `realdata/provenance_gaia.txt` records that `dr3_nss_two_body_orbit_raw.csv` was created by a Gaia Archive TAP query joining `gaiadr3.nss_two_body_orbit` to `gaiadr3.binary_masses` and `gaiadr3.gaia_source`, requiring `a_thiele_innes IS NOT NULL`, `parallax > 0`, `binary_masses.m1 > 0`, and an inferred companion-mass cut `m2 < 80 M_J`. It contains 71,759 rows, including 22,127 `AstroSpectroSB1` rows and 49,632 `Orbital` rows.

By contrast, `src/dark_companion.py` documents the H10 source as `realdata/dr3_astrospectro_all.csv`, rebuilt from VizieR `I/357/tboasb1c` joined to `I/355/gaiadr3`. The archived fetcher query also applies `parallax/parallax_error > 10`. Its expected pre-sealed row count is 33,464. The source-code comments and saved `results/dark_companion.json` report 33,464 queried rows, 33,463 after sealed-ID exclusion, and 19,506 after H10 cuts. The actual `dr3_astrospectro_all.csv` and `dark_companion_scored.csv` are absent from the archive.

The mechanism script reads `results/dark_companion_scored.csv`, then applies its own finite-physics and line-width/transit requirements before writing `mechanism_scored.csv`. Thus comparing its output against the separate, companion-mass-filtered Gaia Archive extract is not a valid parent-table integrity test.

VizieR's current catalogue page lists `I/357/tboasb1c` as 33,467 rows (the full catalogue; the project fetch query has an additional parallax-SNR filter). This supports the distinct-source explanation, but it does not independently prove the identity of each of the 746 records because the actual full upstream D3 CSV is not archived. Public catalogue metadata: https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=I%2F357%2Ftboasb1c .

## Reproduced local counts

- Raw Gaia Archive extract: **71,759** rows, 71,759 unique IDs.
- Solution types: **{'Orbital': 49632, 'AstroSpectroSB1': 22127}**.
- Mechanism output: **10,118** rows, 10,118 unique IDs.
- Mechanism IDs present in the Gaia Archive extract: **9,372 (92.63%)**.
- Mechanism IDs absent from that extract: **746 (7.37%)**.
- Selected 95 labels in mechanism output: **62/95**; absent: **33/95**.

## Why the 746 should not be called corrupt IDs

The comparison file was built with additional joins and a physical selection cut that are not part of the VizieR AstroSpectroSB1 input contract. A row missing from that filtered extract may simply lack a joined `binary_masses` row, fail its positive-mass condition, fail the companion-mass ceiling, or otherwise not be included in that candidate extract. The available archive does not include the binary-mass join results for these 746 sources, so the exact per-source reason cannot be resolved here.

The prior exact-ID comparison is still a valid statement of overlap with **that particular candidate extract**. It is not evidence of 746 invalid source identifiers, nor evidence that the mechanism input came from a different Gaia release.

## Important selection difference

The unmatched-to-raw group is not exchangeable with the matched group. See `MATCHED_UNMATCHED_SELECTION_DIAGNOSTICS.csv` for medians, standardized mean differences, KS D and Mann–Whitney p-values. For example, the archived descriptive audit reports median parallax about 1.70 mas in the unmatched group versus 4.38 mas in the matched group. This difference is consistent with the fact that the raw extract was a separate filtered candidate set; it must not be interpreted as a biological/astrophysical effect of the mechanism model.

## The 33 selected labels absent from mechanism output

The mechanism code (`src/mechanism.py`) explicitly filters its upstream `dark_companion_scored.csv` on:
- finite `vbroad`;
- `vbroad_nb_transits >= 5`;
- finite `vb_med`;
- `vb_sig > 0`;
- finite `VB`;
- finite `b`, `k`, `beta`, `Kmax`, `grvs_mag`, `bp_rp`, `logP`, `eccentricity`, `dm`, and `rho_sig`.

Those conditions can explain why a selected label may not appear in the final 10,118-row mechanism output. But because `dark_companion_scored.csv` is absent, the individual 33 rows cannot be classified by exact exclusion reason. The crosswalk in `SELECTED_95_MEMBERSHIP_CROSSWALK.csv` records only what can be verified.

## Scientific impact

1. The 746-ID finding is downgraded from “unexplained lineage mismatch” to “non-overlap with a differently selected Gaia Archive extract; source-level reasons unresolved.”
2. The prior sensitivity analysis on matched versus unmatched rows is still a descriptive sensitivity analysis, but its groups are defined by membership in the separate candidate extract, not by a verified data-corruption status.
3. The earlier observation that M1/M2b persist in the 9,372-row subset remains numerically descriptive. It should not be presented as proof that excluding “bad IDs” leaves the scientific result intact.
4. M4's difference between the groups may reflect the strong upstream population-selection difference, not necessarily ID corruption. Its full-sample estimate remains as in the frozen mechanism output, but transport/generalization claims require care.
5. The 95-label-to-mechanism gap (33 objects) remains unresolved at row level until the upstream `dark_companion_scored.csv` is recovered.

## What is still needed to close lineage

- Exact `realdata/dr3_astrospectro_all.csv` used by the H10 run (pre-sealed VizieR × Gaia join, with provenance/hash).
- Exact `results/dark_companion_scored.csv` generated by `dark_companion.py`.
- The Gaia `binary_masses` join output or a reproducible query for the 746 IDs, to distinguish no join, non-positive mass, and `m2 >= 80 M_J` exclusions.
- Then rerun `mechanism.py` from the exact frozen upstream file and verify row counts and hashes.

No approximate-ID matching was used. No original data were overwritten.

## Source evidence

- Local `realdata/provenance_gaia.txt`: Gaia Archive query, joins and `m2 < 80 M_J` filter.
- Local `realdata/PROVENANCE.md`: source and row-count description for the DR3 candidate extract.
- Local `tools/fetch_dr3_astrospectro.py`: VizieR `I/357/tboasb1c` × `I/355/gaiadr3` query and `parallax/parallax_error > 10` filter; expected 33,464 rows.
- Local `src/dark_companion.py`: H10 consumes `dr3_astrospectro_all.csv`, drops sealed IDs, and writes `dark_companion_scored.csv`.
- Local `src/mechanism.py`: mechanism consumes `dark_companion_scored.csv` and applies the finite VB/physics filter before writing `mechanism_scored.csv`.
- Public VizieR catalogue metadata: I/357/tboasb1c lists 33,467 catalogue rows (catalogue page accessed 2026-11-01).

