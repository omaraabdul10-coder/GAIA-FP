# H11 DR3 control-group construction — execution record

**Status:** DR3 control-set construction completed; this is not a DR4 validation result.

## Frozen rule applied

- Source: Gaia DR3 `nss_two_body_orbit` export; solution types `Orbital` and `AstroSpectroSB1`.
- Quality cuts: parallax > 2 mas and parallax/parallax_error > 10.
- Approximate implied companion-mass proxy: 80–300 MJ.
- Exclusions: frozen DR3 candidate IDs and sealed IDs.
- Matching: greedy one-to-one nearest neighbour without replacement in `G`, `log10(P)`, and significance; standardization by control-pool SD; candidate random order seed 11.

## Recorded result

- Raw rows: 71,759; unique source IDs: 71,759.
- Solution types: 49,632 `Orbital`; 22,127 `AstroSpectroSB1`.
- Candidate list: 2,102.
- Sealed IDs excluded: 76.
- Eligible control pool before matching: 31,349.
- Matched controls: 2,102; unique control IDs: 2,102.
- Output SHA-256: `cd56e49a6d1ae0baccfd7b334780bee29c351fff3b0751fa803d246570d3b42d`.

## Balance (candidate minus control SMD)

| Variable | SMD |
|---|---:|
| G | +0.029290 |
| log10(P) | −0.011844 |
| Significance | +0.012846 |

## Interpretation and limitations

The matching output is balanced on the three registered matching variables by the reported standardized mean differences. The `mfit` field is an approximate first-order mass proxy from the project pipeline, not a dynamically measured companion mass. The supplied raw export has no `m1` column; the project pipeline therefore uses its photometric main-sequence mass relation. This control-set construction alone does not establish candidate validity, calibration, or any DR4 outcome. DR4 outcomes remain to be evaluated after the DR4 data and the preregistered cross-match are available.

## Files

- `results/h11_controls.csv`: matched control rows, in candidate-pair order.
- `results/h11_controls.csv.sha256`: checksum of the CSV.
- `results/h11_audit.json`: machine-readable counts, balance statistics, and validation flags.
- `src/h11_control.py`: project H11 matching implementation.
- `realdata/dr3_nss_two_body_orbit_raw.csv`: supplied 71,759-row source export used for this recorded run.

The original preregistration and prior freeze manifests are preserved. The H11 output entries are added only to `FREEZE_MANIFEST_v0.6_DRAFT.sha256`; do not represent this draft as an already registered immutable freeze.
