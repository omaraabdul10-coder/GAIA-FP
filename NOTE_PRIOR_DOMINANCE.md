# Note: how much of P_impostor comes from the prior (DR3, written 23 Nov 2026)

Exploratory. No registered test or number changes.

GAIA-FP's posterior is P_impostor = expit(log_lr + logit(π)), where log_lr is the evidence from the data (CMD,
a0, RVS) and π is a covariate prior fitted by EM (`dr4_run.phi_v32`: log P, e, log mfit).

On the 2102 DR3 candidates (`results/dr3_candidates_scored.csv`):

| Catalogue mass (MJ) | n | median π | mean P_impostor | mean P with flat π = 0.3 | median log_lr |
|---|---|---|---|---|---|
| 5–13 | 13 | 0.79 | 0.65 | 0.31 | 0.22 |
| 13–30 | 117 | 0.89 | 0.88 | 0.49 | 0.58 |
| 30–50 | 422 | 0.95 | 0.92 | 0.46 | 0.38 |
| 50–80 | 1550 | 0.97 | 0.95 | 0.42 | 0.16 |

Candidates with P_impostor > 0.5: 2044 with the frozen prior, 606 with a flat prior of 0.3.

What this means:
- The high impostor probabilities (and the "1911 likely impostor" count) are driven mostly by π, i.e. by the EM
  estimate of the population impostor fraction, which rises with catalogue mass. The per-object data evidence is
  modest (median log_lr 0.16–0.58).
- The ranking of candidates, which is what H1 and A5 test, depends on log_lr and on π's covariates. Absolute
  probabilities should not be read as measured prevalences; the README already calls the 1911 a model
  classification.
- Population statements (e.g. how contaminated the brown-dwarf desert is) should come from labels that do not use
  the score: the dynamical labels of A5/H19, the APOGEE check and the SB9/SBX check. `H19_DESERT_PLAN.md` follows that.
