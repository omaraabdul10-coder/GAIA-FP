# H6 decision-rule discrepancy — audit note (1 Nov 2026)

## Finding
The supplied GAIA-FP v0.6 / QA2 snapshot contains two non-equivalent H6 descriptions.

1. `HYPOTHESIS_LEDGER.md` describes H6 as `AUC(ML trained on L&W simulator) - AUC(GAIA-FP)` and says GAIA-FP non-inferiority holds when the paired-bootstrap 95% confidence interval is **not entirely above zero**. The matching current code in `src/h6_runner.py` and `src/dr4_evaluate.py` marks the claim falsified when the lower CI bound is greater than zero.
2. Earlier project context records a separate non-inferiority criterion `LCL95%(AUC_ML - AUC_Baseline) >= -0.01`. This has a different numerical margin and its comparison direction must be checked against the exact registered H6 wording before use in this v0.6 implementation.

The canonical `PREREGISTRATION.md` named by the ledger (v0.3 source for H1–H7) is absent from the supplied QA2 archive, although it is referenced by the snapshot's draft checksum manifest. The exact registered source text therefore could not be re-opened in this package.

## Action taken
- No frozen registration or scientific threshold was changed.
- The implementation in this working snapshot was restored to the v0.6 ledger's own interpretation (`CI not entirely above 0`).
- Regression tests now lock that current snapshot behaviour so it cannot drift silently.
- The historical `-0.01` formulation is retained here as a version-reconciliation issue, not silently applied to v0.6.

## Required evidence to close
Recover the exact registered `PREREGISTRATION.md`/OSF v0.3 text and verify (a) which model is the comparator, (b) the subtraction direction, (c) whether the margin is zero or 0.01, and (d) the one-sided/two-sided CI definition. Then issue a dated, documented amendment if the working v0.6 implementation differs from the registered rule. Do not choose the version based on which outcome looks better.

## Superseding resolution (1 Nov 2026)
The missing archived `PREREGISTRATION.md` was recovered from the earlier v0.6 project archive. It specifies `AUC_ML − AUC_GAIA-FP`, with H6 falsified only when the paired-bootstrap 95% CI is entirely above zero. The `−0.01` expression is not the H6 endpoint in that recovered local v0.3 draft. See `H6_RULE_RECONCILIATION_2026-11-01.md`. The immutable OSF record was not independently fetched here; if it differs, that registered record controls.
