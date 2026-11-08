# GAIA-FP vs Bailer-Jones & Kreidberg 2026: result (8 Nov 2026, run once per `BJK_COMPARISON_PLAN.md`)

**Sample:** 1856 frozen DR3 candidates that are also in the BJK catalogue (sealed ids dropped first). File: `results/bjk_comparison.json`.

| Labels (positive vs unlabelled) | Positives | GAIA-FP AUC | BJK m2 AUC | ΔAUC (GAIA-FP − BJK) [95% CI] | Verdict (pre-specified rule) |
|---|---|---|---|---|---|
| Survey SB2 (LAMOST / GALAH / APOGEE) | 14 | 0.655 | 0.432 | **+0.224 [+0.078, +0.389]** | **GAIA-FP better** |
| APOGEE RV-incompatible | 7 | 0.684 | 0.717 | −0.033 [−0.191, +0.116] | no detectable difference |

**Agreement:**
- BJK puts the companion above 80 MJ (lower bound) for only **11%** of the candidates GAIA-FP calls likely impostors.
- For GAIA-FP's ambiguous and likely-substellar candidates, the figure is 0%.

The two methods therefore disagree on most of the ~1700 systems. DR4 decides between them: H1 (sealed labels), A5 (DR4 dynamical labels) and H11 (DR3→DR4 outcomes).

**Reading:**
- On survey SB2s, GAIA-FP is better.
- BJK's mass is *anti*-ranked there (AUC < 0.5). A plausible reason is that near-twin SB2s break a mass–flux relation that assumes a fainter companion. This is an interpretation, not a test.
- With 7 APOGEE positives nothing can be concluded.
- Both label sets are small and positive-vs-unlabelled, so these are development results, not proof.
