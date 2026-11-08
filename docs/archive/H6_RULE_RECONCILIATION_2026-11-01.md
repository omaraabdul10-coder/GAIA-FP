# H6 rule reconciliation — 1 November 2026

## Resolution from recovered primary project source

The previously missing local `PREREGISTRATION.md` has been recovered from the earlier GAIA-FP v0.6 project archive and restored into this working QA2 tree. It identifies itself as **v0.3 DRAFT, dated 9 October 2026**. Its H6 wording is:

> On the real labelled set, GAIA-FP v3+EM has an AUC not lower than a gradient-boosting classifier trained on the Lammers & Winn simulator (paired bootstrap; falsified if the CI of AUC_ML − AUC_GAIA-FP lies entirely above 0).

The current `HYPOTHESIS_LEDGER.md`, `src/h6_runner.py`, and `src/dr4_evaluate.py` use the same comparator and subtraction direction. The implementation uses a paired, stratified bootstrap (2,000 replicates; seed 7) and marks H6 falsified only when the 95% interval for `AUC_ML − AUC_GAIA-FP` is entirely above zero.

**Therefore the `−0.01` lower-bound expression from earlier project context is not the H6 rule in this recovered v0.3 preregistration.** It uses a different comparison description and should not be substituted into this H6 endpoint. No scientific code, threshold, or preregistered outcome was changed in this audit.

## Provenance and remaining qualification

- Recovered source: `PREREGISTRATION.md` (v0.3 DRAFT, 9 Oct 2026).
- SHA-256: `2c0193bdb5d6dbbbc8dd311fe50203b69fe5be3b9271661353ad909a2357ebb8`.
- Related frozen DR3→DR4 plan: `DR3_TO_DR4_PREDICTION_PLAN.md`, SHA-256 `511eea20a8834ddd98c871aaf049f5880a2646c9d1dd173b38f93bcb3a7b8781`.
- The v0.3 local source is marked DRAFT. The public OSF registration/DOI record (referenced elsewhere in the project as `10.17605/OSF.IO/N5H4B`) was not independently fetched in this environment. If its immutable registered text differs from this recovered local source, the OSF registration controls and a dated deviation note is required.

## Action

This note supersedes the unresolved status in `H6_RULE_DISCREPANCY.md` for the working tree, but that historical file is retained for traceability. The H6 implementation remains unchanged pending any direct conflict found in the immutable OSF record.
