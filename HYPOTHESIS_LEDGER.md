# Hypothesis ledger (audit of 31 Oct 2026)

One row per registered hypothesis. "Code" names the file and function that compute the exact number. "Runner" says whether a script exists that, on DR4 day, goes from the downloaded tables to the verdict without hand work.

**At the start of the audit (31 Oct morning), H1, H2, H5, H6, H8/A5 and H11 had NO runner that could decide them on DR4.** All of them now have one; the last column says what was written. Remaining gaps: the live fetch (`dr4_fetch.py`, untested against the archive), the H11 control-group download, and the DR4 epoch-astrometry adapter (H4).

## Sources
- PREREGISTRATION.md v0.3: H1–H7.
- PREREG_AMENDMENT_v0.4.md: H8, A5.
- DARK_COMPANION_PLAN.md: H9, H10.
- DR3_TO_DR4_PREDICTION_PLAN.md: H11.
- PREREG_AMENDMENT_v0.6 (draft): H12–H14.

## Confirmatory family (Holm, m = 5; see amendment v0.6 A18) and secondary hypotheses
| H | Exact statistic | Threshold / pass | Failure criterion | Code | Test of that code | Power (n) | Family | DR4 runner (31 Oct) |
|---|---|---|---|---|---|---|---|---|
| **H1** | ROC AUC of P_impostor, sealed set (39 impostor vs 26 substellar), stratified bootstrap 2000 | claim "AUC ≥ 0.80" is descriptive; test: lower bound > 0.5 | 95% CI includes 0.5 | `blind_eval.roc_auc`; bootstrap: **`blind_eval.bootstrap_ci` is NOT stratified** (prereg §7 says stratified) → use `dark_companion.boot` | `tests/test_dr4_evaluate.py` | n = 65 fixed. Power to exclude 0.5: AUC 0.70 → 76% unadjusted, 53% Holm; AUC 0.80 → 99% / 97% | **confirmatory** | **written 31 Oct**: `dr4_evaluate.h1` (stratified bootstrap, label-file hash and count assertions) |
| **H2** | impostor rejection at 95% substellar retention, objects with ≥ 15 RVS epochs; (CMD + RVS empirical, A7) minus CMD-only; paired bootstrap | lower bound of difference > 0 (A7: judged on the primary empirical score) | CI includes 0 and point ≤ 0 (prereg wording); Holm p ≥ adjusted α | `blind_eval.operating_point(score, y, 0.95)` + `dr4_empirical.empirical_score` | `test_dr4_empirical` (score only) | unknown: depends on how many of the 65 have ≥ 15 RVS epochs. With ~30 objects: low (< 50%) | **confirmatory** | **written 31 Oct**: `dr4_adapters` + `dr4_run` (loads epochs, A7) + `dr4_evaluate.h2`. The frozen CLI path alone could not compute H2 |
| H3 | Brier score, full model vs CMD-only, pooled synthetic + real | full < CMD-only | full ≥ CMD-only | `blind_eval.calibration` | none | the synthetic part dominates the pooled number | secondary | `dr4_evaluate.h3` (real part; the pooled part needs a synthetic file) |
| H4 | P, e, a0 of Gaia BH3 and Gaia-4 recovered from DR4 epoch astrometry | each within 2σ | any outside 2σ | `fit_real.py`, `mcmc_orbit.py` (pre-release format) | `test_core` (orbit model) | n/a | descriptive (pipeline check, not a test) | needs DR4 epoch-astrometry adapter |
| H5 | EM impostor fraction (label-free) vs observed fraction in the labelled set | agreement within the 95% CI | disagreement | `hier_em.em`, `prior_select.select` (A1) | `test_prior_select` | CI of the labelled fraction is ±0.12 at n = 65 | secondary | **written 31 Oct**: `dr4_evaluate.h5`; A1 wired in `dr4_run` (the frozen `score` used C = 1) |
| H6 | AUC(ML trained on L&W simulator) − AUC(GAIA-FP), paired bootstrap | non-inferiority: CI not entirely above 0 | CI entirely above 0 | `tournament.ml_model` | none on DR4 features | n = 65 | secondary | **written 31 Oct**: `dr4_evaluate.h6` (dry run OK) |
| H7 | AUC survey-SB2 vs survey-single, matched DR4 candidates | lower bound > 0.5 | CI includes 0.5 | `survey_xmatch.main` (refuses to run unless the catalogue hash matches) | none | DR3: P1 underpowered (1 positive); P2 n small | secondary (A4) | exists; needs the DR3→DR4 id map |
| **H8 / A5** | (a) AUC of P_impostor vs dynamical labels (A3 rules) on DR4 combined solutions; (b) recall at P ≥ 0.85; **A5**: ΔAUC(GAIA-FP − B2) | (a) lower > 0.5; (b) ≥ 80%; A5 lower > 0 | as stated | `astrospectro_check.main` (DR3 file layout), `dark_companion.dauc_ci` | none | DR3 had **2** genuine-consistent vs 42 impostors → AUC/ΔAUC barely estimable. Applicability rule needed (≥ 10 per class) | **A5 confirmatory**; (a), (b) secondary | **written 31 Oct**: `dr4_dynamical` (reproduces the DR3 labels exactly) + `dr4_evaluate.h8`. The frozen fetch lacked C, H |
| H9 | vbroad of substellar candidates vs survey SB2 | — | — | `dark_companion.h9` | — | 6 positives | done, exploratory (DR3) | n/a |
| H10 | ΔAUC(S1 − B2) on DR3 ρ labels | lower > 0 | — | `dark_companion.h10` | `test_dr3_integration` | n = 1927 | done (DR3 development, passed) | n/a |
| **H11a** | Brier(GAIA-FP) − Brier(B2) against DR4 outcome labels (O2–O4 vs D), paired bootstrap | CI excludes 0 (negative) | otherwise | **none** | none | n ≈ 2102 candidates; labelled fraction unknown | **confirmatory** | **written 31 Oct**: `h11_outcomes`. Second prediction set frozen (d8c9b2e2…). B2 probability frozen (d86774c7…, A20). **Control group: code ready, DR3 download still needed before 24 Nov** |
| H11b | high-confidence error rate, upper 95% (Clopper–Pearson) | < 10% | ≥ 10% | `blind_eval.clopper_pearson` | none | depends on the 17 likely_substellar | secondary | `h11_outcomes.metrics` |
| H11c | O1 rate candidates vs controls | descriptive | — | none | none | — | descriptive | `h11_outcomes` (needs controls) |
| **H12** | M1, M2a, M2b of `MECHANISM_PLAN.md` on DR4-new systems | all three pass (intersection–union) | any fails | `mechanism.main` via `dr4_mechanism.main` | `test_mechanism` (physics), smoke run on a fake table | n ≥ 668 required (power rule A14) | **confirmatory** | `dr4_mechanism` (cross-match exclusion, power rule, IUT p-value) |
| H13 | f(β̂ ≥ 0.2 \| Kmax ≥ 50) / f(β̂ ≥ 0.2 \| Kmax < 30) | lower 95% > 1. **Trend only.** The level of the dilution model failed on DR3 by 7–10× and is NOT claimed | lower ≤ 1 | `dr4_mechanism.h13` | smoke run | DR3: 2.66 [1.87, 3.90] at n = 10 118 | secondary | exists |
| H14 | ĉ = median (vbroad² − med²)/b, b ≥ 25 | CI overlaps [1.4, 2.3]; c = 4 rejected if upper < 4 | no overlap | `mechanism.main` (M4) + `dr4_mechanism.main` | smoke run | DR3 n = 1731 | secondary | exists |

## Checks done for this ledger
- Every "Code" entry was opened and read. The ones marked MISSING were searched for (grep for the hypothesis id, metric name and outcome codes) and not found.
- **Sealed label file:** field names and label vocabulary only, no per-object values. The analysis rule "label ∈ {impostor, substellar}" reproduces the registered counts 39 + 26 = 65 of 76. The runner must assert these counts and stop if they differ.

## Sample definitions per analysis (section G)
| Analysis | Sample | Where it was fixed | When |
|---|---|---|---|
| DR3 study (P1–P3, H7-DR3) | 2102 = 2138 rows − 19 duplicates − 17 without TI errors; sealed ids dropped first | DR3_STUDY_PLAN.md + deviation 5 | plan before data; deviation 5 before labels |
| AstroSpectroSB1 check | 95 candidates with combined solutions | astrospectro_check.py rules | before comparison with scores |
| H10 | 33 464 combined solutions, ϖ/σ > 10 → 19 506 after MS/quality cuts → **1927** labelled with vbroad (≥ 5 transits) | DARK_COMPANION_PLAN.md + deviations 8–11 | plan before download |
| vbroad v2 | the same 1927, split into TRAIN 940 / TEST 987 by digit-sum parity | VBROAD_V2_PLAN.md + deviation 12 | before running |
| Mechanism (M1–M4) | the same 19 506, **all** with usable vbroad (labelled or not) = **10 118**; dark sample = label 0 within them (1085) | MECHANISM_PLAN.md §2 ("Sample V") | hashed before the run |
| H12–H14 (DR4) | A15 of v0.6: DR4 combined solutions, ϖ/σ > 10, minus DR3 ids and sealed ids, same cuts as H10 | v0.6 draft | before DR4 |
| H17 (DR4) | DR4 candidates with ≥ 20 accepted G epoch-photometry transits | v0.6 A32 | before DR4 |
| H18, H19 (DR4) | the H12 sample (all labels, not only vbroad), m₂,dyn ≥ 1.4 M☉ (H18) or dark-assumed m₂ in 13–80 MJ (H19); resolved ρ labels only | v0.6 A33–A34 | before DR4; DR3 dev: 83 and 35 resolved |

Why 10 118 and not 1927: M1–M4 test a physical relation between orbit quantities and vbroad. They need no ρ label, so the plan used every system with vbroad. Only M2a uses the labelled dark subset.
