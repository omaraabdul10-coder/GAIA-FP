# GAIA-FP Round 6 — prior invariance and score-mechanism audit

Date: 2026-11-02

## Scope
Reanalysed the same 2,102-row DR3 ablation table (16 known SB2 positive controls; 2,086 unlabelled objects). This is a diagnostic follow-up to Round 5, not an independent validation.

## 1. Reconstructing the CMD-marginal posterior
The stored `CMD_marginal_fixed_prior_pi0.3` values are exactly reproduced (maximum absolute numerical error 1.11e-16) by

`posterior(pi) = logistic(CMD_logLR + logit(pi))`,

where `CMD_logLR = logit(stored_posterior_at_0.3) - logit(0.3)`. This establishes that changing the fixed prior only adds a constant to every object's log-odds. Therefore it changes probability calibration and threshold counts, but **cannot change ranking, top-k membership, AUC, or enrichment** for this score.

## 2. Prior sensitivity
Across fixed priors from 0.05 to 0.90, the CMD-marginal score retains exactly 10/16 SB2 positives in its top 421 candidates (top 20%). Enrichment remains 3.12x. However, the number of all candidates assigned posterior >=0.85 changes from 71 to 1953, and SB2 positives above that threshold change from 1 to 16. Thus a fixed prior is not an improvement in discrimination; it is a choice of prior calibration.

## 3. What actually improved the ranking?
The CMD-marginal likelihood-ratio ranking has Spearman rho=0.939 with B2-only ranking. In the top-20% set, CMD-marginal contains 10/16 SB2 controls, compared with 6/16 for B2-only and 5/16 for the original full joint score. The CMD top-20 and B2-only top-20 overlap in 248/421; CMD and full top-20 overlap in 303/421.

Four SB2 positives are promoted into the CMD top-20 despite not appearing in the B2-only top-20. This suggests that the CMD likelihood model's uncertainty/scatter treatment contributes ranking information beyond raw CMD displacement alone. It does **not** prove that this contribution is astrophysically independent or generalizable: SB2 positives are only 16, and the unlabelled pool is not a true-negative set.

## 4. Interpretation and decision
- Keep `CMD_marginal_fixed_prior_pi0.3` as a **ranking challenger**, not a calibrated probability model and not a replacement for GAIA-FP yet.
- The positive-control enrichment signal is robust to prior changes because the ranking is mathematically invariant to the prior. This also means the apparent improvement is not caused by selecting pi=0.3.
- Do not describe posterior >=0.85 as a stable scientific class across priors; the threshold counts are strongly prior-dependent.
- The strongest next test is a frozen ranking evaluated on newly obtained, independently crossmatched SB2 labels (preferably a survey not used in this discovery analysis), with duplicate/source leakage checks and predeclared top-k budget.

## Limitations
This is a post-hoc model comparison on the same 16 SB2 positives. Holm correction in Round 5 addressed five top-20 model tests, but it does not erase broader model-selection bias from iteratively exploring variants on the same labels. No specificity, false-positive rate, or population-wide precision can be estimated from the 2,086 unlabelled rows.
