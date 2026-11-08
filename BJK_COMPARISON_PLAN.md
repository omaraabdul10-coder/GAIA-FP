# Comparison with Bailer-Jones & Kreidberg 2026 (plan, written before any comparison was computed)

**Written:** 8 Nov 2026, before any AUC was computed on this catalogue. The SHA-256 of this file is stored in `BJK_COMPARISON_PLAN.sha256` before the run. Exploratory: it does not change any DR4 test.

**Data:**
- Bailer-Jones & Kreidberg 2026 (A&A 708, A249), Table 1: `output_mass_catalogue_Orbital300.csv`, downloaded 8 Nov 2026 from bailer-jones.www3.mpia.de. Stored as `realdata/external/bjk2026_orbital300.csv` (SHA-256 9acd0ba16103ece3…; 20 334 rows).
- Its columns are m1, m2 (with intervals), ap, period and log_flux_ratio.

**Sample:**
1. GAIA-FP's frozen DR3 candidates (`results/dr3_candidates_scored.csv`, OSF TBJGY) that are in the catalogue.
2. Sealed ids are dropped **first**.

**Scores:**
- **GAIA-FP:** the frozen P_impostor.
- **BJK, primary:** m2 in M☉ (a larger companion mass means more likely stellar).
- **BJK, secondary:** −log_flux_ratio (a brighter companion means more likely an impostor).

**Labels** (both are positive-vs-unlabelled):

| Label | Positive | Unlabelled | Source |
|---|---|---|---|
| L1 | APOGEE rv_incompatible = 1 | other candidates with APOGEE data | `results/apogee_candidates.csv` |
| L2 | survey SB2 (LAMOST, GALAH or unique APOGEE match) | other candidates | `dr3_study.build_labels`, frozen rules |

**Statistics:**
- AUC of each score.
- Paired ΔAUC = AUC(GAIA-FP) − AUC(BJK m2): stratified bootstrap, B = 2000, seed 7, 95% CI.
- GAIA-FP is called better only if the 95% CI of ΔAUC lies above 0; worse only if it lies below 0; otherwise "no detectable difference". With 8 and ~16 positives this is expected to be underpowered, and that is reported as it is.

**Agreement (descriptive):** among GAIA-FP's likely_impostor and likely_substellar verdicts, the fraction with BJK m2 lower bound > 80 MJ (0.0764 M☉).

**Result:** reported in `RESULTS_BJK_COMPARISON.md` whatever it is, and run once.
