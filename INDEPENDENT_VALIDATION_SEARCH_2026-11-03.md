# Independent compact-companion validation search — 3 Nov 2026

## Scope

The supplied project contains a 95-object dynamical characterization subset, a 2,119-unique-source candidate table, SB2 crossmatches, and Gaia DR3 NSS records. SB2 catalogue matches are luminous-binary contamination evidence and are not counted as compact-companion confirmations.

## Evidence lead checked

The Gaia DR3 multiplicity paper (A&A, DOI `10.1051/0004-6361/202243782`) discusses Gaia DR3 source `5136025521527939072` as a dormant-neutron-star candidate. It reports primary mass about 1.2 M_sun, secondary mass about 1.5 M_sun, period 536 days, and one SOPHIE follow-up RV measurement (`40.603 ± 0.023 km/s` at BJD `2459541.389492`). The source is present in `realdata/dr3_nss_two_body_orbit_raw.csv`, but is absent from `realdata/dr3_candidates.csv`, `results/dr3_candidates_scored.csv`, `results/mechanism_scored.csv`, and the 95-object characterization file. It therefore cannot validate GAIA-FP's selected candidate sample. One follow-up RV point is not an independently measured orbital solution, and the paper's candidate interpretation is not a secure compact-object confirmation.

## Result

No defensible independent compact-companion confirmation was identified within the GAIA-FP 95-object validation sample in the files available in this snapshot. The evidence lead above is recorded for provenance but explicitly excluded from validation metrics. A complete literature/SIMBAD/orbit-catalogue crossmatch for all 95 IDs remains outstanding; the current runtime could not reach external catalogue services.

## Decision

**BLOCKED — independent validation sample unavailable.** Do not report precision, specificity, sensitivity, or a confirmed compact-companion discovery from the current SB2 crossmatches or this external literature lead.
