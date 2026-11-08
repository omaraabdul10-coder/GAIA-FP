# Data and provenance notes

The package contains derivative CSVs copied from the archived GAIA-FP project snapshot and a separate 22,127-row H10/B2 audit CSV. Gaia IDs are retained as decimal strings in audit scripts to avoid precision loss. The full 33,464-row VizieR–Gaia joined AstroSpectroSB1 parent dataset and H10 scored file are absent. The raw NSS extract and 10,118-row mechanism output are supplied for the limited lineage comparison. The APOGEE visit-level timestamp response bundle is not included; only per-object summary tables and the 46-object primary cohort table are provided.

The included 22,127-row B2 audit was used to test whether all 95 selected dynamical-label objects survived the H10 common colour/photometric filters. It does not contain the `vbroad` or transit fields required to identify the exact mechanism exclusion for each of the 33 objects absent from `mechanism_scored.csv`.
