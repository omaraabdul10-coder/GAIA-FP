# H22: the frozen likelihood without the prior (secondary hypothesis)

Written 23 Nov 2026, before Gaia DR4 (2 Dec 2026). This is a secondary hypothesis. It sits outside the Holm family and does not change H1. The H1 score, the Holm weights and every frozen file stay as they are.

## Why we added it

NOTE_PRIOR_DOMINANCE.md shows that the covariate EM prior π dominates the v3.2 posterior.

We checked this on the public DR3 data (the 16 SB2 impostors against the other 2086 candidates; positive-unlabelled). None of the 76 sealed objects were used. On that data:
- the prior alone ranks impostors worse than chance (AUC 0.40);
- the frozen likelihood ratio `log_lr` reaches AUC 0.72 (95% CI 0.59–0.84);
- the full posterior `P_impostor` reaches 0.64.

The paired difference is +0.08 (95% CI −0.02 to +0.18), so it is not significant. Result file: `results/h22_dev_dr3_PU.json`.

We are open about the order: we chose H22 *after* seeing these DR3 numbers. That is why it is secondary. The DR4 sealed labels are what test it independently.

## The score

The score is `log_lr`. It is the frozen v3.2 log-likelihood ratio, the same value `dr4_run.write` already writes to the DR4 output. This is equal to the posterior with a flat prior, because the posterior is a monotone function of `log_lr`. We do not refit anything and add no new parameters. The DR4 pipeline does not change.

## Tests (on the H1 sealed set, with the same labels, matching and exclusions as H1)

- H22a: the AUC of `log_lr`, with a stratified bootstrap (B = 2000, seed 7), as in H1. PASS if the 2.5th percentile is above 0.5. We also report the one-sided p-value. It is not counted in the Holm family.
- H22b (reported only): the paired difference ΔAUC = AUC(`log_lr`) − AUC(`P_impostor`), with a 95% bootstrap CI.
  - "better" if the CI is entirely above 0;
  - "worse" if it is entirely below 0;
  - otherwise "no difference".
- NOT_CONDUCTED if either class has fewer than 10 objects (as in H1), or if `log_lr` is missing or not finite.

## Code

- `src/h22_likelihood_only.py` (reuses the helpers in `dr4_evaluate`; the frozen evaluator is not modified)
- `tests/test_h22.py`

## How we will report it

- If H22a passes and H1 does not, we will say exactly that. We will not present it as H1 passing.
- If H22b is "better", it supports the prior-dominance note. If it is "worse", the prior helped on DR4, and we will report that just as openly.
