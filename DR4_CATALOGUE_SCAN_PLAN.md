# DR4 catalogue scan: plan (exploratory, written 24 Nov 2026, before Gaia DR4)

Status: exploratory. It is outside the Holm family and changes no registered test, score or threshold. It is written before DR4 so the outputs are fixed in advance and can't be chosen after seeing the data.

## What it produces on DR4 day

The tests (H1, H11, H21, H22, …) say whether GAIA-FP works. This scan says what GAIA-FP finds in the whole DR4 catalogue of astrometric companion candidates. Code: `src/dr4_catalogue_scan.py`; tests: `tests/test_dr4_catalogue_scan.py`.

1. **Impostor fraction.** For all DR4 candidates with fitted companion mass below 80 MJ, the mean frozen P_impostor (with the covariate prior) and the mean of expit(log_lr) (likelihood only, π = 0.5), each with a bootstrap 95% CI (B = 2000, seed 24). Both are reported. Neither is a measured prevalence: they are model estimates, and NOTE_PRIOR_DOMINANCE.md explains why they differ.
2. **Named list.** The 20 candidates with the highest log_lr (ties broken by P_impostor), after removing evolved primaries. This is the "most likely impostor" list for follow-up.
3. **Evolved primaries.** A primary more than 1.5 mag above the main sequence (dm < −1.5) is flagged and kept out of the list: for such a star the CMD term says nothing about a companion. In the DR3 dry run this rule removed 10 of 2102 stars, including the three highest-scoring ones (dm −5 to −8).
4. **Baseline-trap flags.** P ≥ 0.85 × the DR4 data baseline (H21's mechanism). The baseline is taken from the DR4 documentation on the day; the expected value is about 2010 d.
5. **Telescope subset.** Candidates with G ≤ 11 and Dec ≥ −10°, which a 2-m telescope at Shamakhy can reach.

Sealed evaluation objects are removed by id (`realdata/excluded_sealed_ids.csv`) before anything is computed.

## Dry run on DR3 (24 Nov 2026)

`python src/dr4_catalogue_scan.py results/dr3_candidates_scored.csv --baseline-days 1038 --out-dir exploratory/dr3_scan_dryrun`

| Output | DR3 value |
|---|---|
| Candidates (mfit < 80 MJ) | 2102 |
| Mean P_impostor, with prior | 0.940 [0.934, 0.946] |
| Mean expit(log_lr), likelihood only | 0.594 [0.585, 0.604] |
| P > 0.5, with prior / likelihood only | 2044 / 1358 |
| Baseline-trap flags (P ≥ 0.85 × 1038 d) | 108 |
| Evolved primaries flagged | 10 |

Most of the top of the DR3 list are main-sequence stars 0.8–1.1 mag brighter than a single star of their mass, with fitted companions of 30–80 MJ. A near-equal-mass binary is 0.75 mag brighter than one star and barely moves its photocentre (NOTE_BLIND_SPOT_MAP.md), so it looks exactly like this. The H11 probabilities frozen in v0.5 already contain the prediction for these objects; DR4 epoch data and RVS spectra will test it.

## Caveats

- These are model estimates, not counts of confirmed impostors. Bailer-Jones & Kreidberg 2026 call far fewer of these stars stellar (RESULTS_BJK_COMPARISON.md); the two approaches disagree, and DR4 will show which is closer.
- The list ranks by the prior-free score that H22 tests. If H22 fails on DR4, the list should be read with that in mind.
