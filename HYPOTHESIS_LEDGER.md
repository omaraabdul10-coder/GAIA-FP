# Hypothesis ledger (audit of 31 Oct 2026)

Each registered hypothesis gets one row. "Code" points to the file and function that produce the exact number. "Runner" answers a blunt question: on DR4 day, can a script take the downloaded tables to a verdict with nobody touching anything by hand?

On the morning of 31 Oct, when the audit started, the answer was no for H1, H2, H5, H6, H8/A5 and H11. That has changed. Every one of them now has a runner, and the last column records what we wrote. Three gaps are still open: the live fetch (`dr4_fetch.py`, never yet run against the archive), the download for the H11 control group, and the adapter for DR4 epoch astrometry (H4).

## Where the hypotheses come from
- PREREGISTRATION.md v0.3: H1–H7
- PREREG_AMENDMENT_v0.4.md: H8 and A5
- DARK_COMPANION_PLAN.md: H9 and H10
- DR3_TO_DR4_PREDICTION_PLAN.md: H11
- PREREG_AMENDMENT_v0.6 (draft): H12–H14

## Confirmatory family (Holm, m = 5; see amendment v0.6 A18) and secondary hypotheses
| H | Exact statistic | Threshold / pass | Failure criterion | Code | Test of that code | Power (n) | Family | DR4 runner (31 Oct) |
|---|---|---|---|---|---|---|---|---|
| **H1** | ROC AUC of P_impostor on the sealed set (39 impostor vs 26 substellar), stratified bootstrap with 2000 replicates | "AUC ≥ 0.80" describes what we expect; the test is lower bound > 0.5 | 95% CI includes 0.5 | `blind_eval.roc_auc`. For the bootstrap, note that `blind_eval.bootstrap_ci` is not stratified, although prereg §7 says it should be, so we use `dark_companion.boot` | `tests/test_dr4_evaluate.py` | n = 65, fixed. Power to exclude 0.5: at AUC 0.70, 76% unadjusted and 53% under Holm; at AUC 0.80, 99% and 97% | confirmatory | Written 31 Oct: `dr4_evaluate.h1` (stratified bootstrap, checks the label-file hash and counts) |
| **H2** | Impostor rejection at 95% substellar retention for objects with ≥ 15 RVS epochs; (CMD + empirical RVS, A7) minus CMD-only; paired bootstrap | Lower bound of the difference > 0 (under A7, judged on the primary empirical score) | CI includes 0 and point ≤ 0 (prereg wording); Holm p ≥ adjusted α | `blind_eval.operating_point(score, y, 0.95)` + `dr4_empirical.empirical_score` | `test_dr4_empirical` (score only) | Unknown, since it depends on how many of the 65 have ≥ 15 RVS epochs. With about 30 objects, low (< 50%) | confirmatory | Written 31 Oct: `dr4_adapters` + `dr4_run` (loads epochs, A7) + `dr4_evaluate.h2`. The frozen CLI path on its own couldn't compute H2 |
| H3 | Brier score of the full model vs CMD-only, synthetic and real pooled | full < CMD-only | full ≥ CMD-only | `blind_eval.calibration` | none | The synthetic part dominates the pooled number | secondary | `dr4_evaluate.h3` (real part; the pooled part needs a synthetic file) |
| H4 | P, e, a0 of Gaia BH3 and Gaia-4 recovered from DR4 epoch astrometry | each within 2σ | any outside 2σ | `fit_real.py`, `mcmc_orbit.py` (pre-release format) | `test_core` (orbit model) | n/a | descriptive (a pipeline check, not a test) | Needs the DR4 epoch-astrometry adapter |
| H5 | Label-free EM impostor fraction vs the observed fraction in the labelled set | agree within the 95% CI | disagree | `hier_em.em`, `prior_select.select` (A1) | `test_prior_select` | The CI of the labelled fraction is ±0.12 at n = 65 | secondary | Written 31 Oct: `dr4_evaluate.h5`; A1 wired into `dr4_run` (the frozen `score` used C = 1) |
| H6 | AUC(ML trained on the L&W simulator) − AUC(GAIA-FP), paired bootstrap | non-inferiority: CI not entirely above 0 | CI entirely above 0 | `tournament.ml_model` | none on DR4 features | n = 65 | secondary | Written 31 Oct: `dr4_evaluate.h6` (dry run OK) |
| H7 | AUC of survey-SB2 vs survey-single on matched DR4 candidates | lower bound > 0.5 | CI includes 0.5 | `survey_xmatch.main` (won't run unless the catalogue hash matches) | none | On DR3, P1 was underpowered (1 positive) and P2 had a small n | secondary (A4) | Exists; needs the DR3→DR4 id map |
| **H8 / A5** | (a) AUC of P_impostor against dynamical labels (A3 rules) on DR4 combined solutions; (b) recall at P ≥ 0.85; A5: ΔAUC(GAIA-FP − B2) | (a) lower > 0.5; (b) ≥ 80%; A5 lower > 0 | as stated | `astrospectro_check.main` (DR3 file layout), `dark_companion.dauc_ci` | none | DR3 had only 2 genuine-consistent systems against 42 impostors, so the AUC and ΔAUC could barely be estimated. Needs an applicability rule (≥ 10 per class) | A5 confirmatory; (a) and (b) secondary | Written 31 Oct: `dr4_dynamical` (reproduces the DR3 labels exactly) + `dr4_evaluate.h8`. The frozen fetch didn't get C and H |
| H9 | vbroad of substellar candidates vs survey SB2 | — | — | `dark_companion.h9` | — | 6 positives | done, exploratory (DR3) | n/a |
| H10 | ΔAUC(S1 − B2) on DR3 ρ labels | lower > 0 | — | `dark_companion.h10` | `test_dr3_integration` | n = 1927 | done (DR3 development, passed) | n/a |
| **H11a** | Brier(GAIA-FP) − Brier(B2) against DR4 outcome labels (O2–O4 vs D), paired bootstrap | CI excludes 0 (negative) | otherwise | none | none | n ≈ 2102 candidates; labelled fraction unknown | confirmatory | Written 31 Oct: `h11_outcomes`. Second prediction set frozen (d8c9b2e2…). B2 probability frozen (d86774c7…, A20). The control-group code is ready, but the DR3 download still has to happen before 24 Nov |
| H11b | Upper 95% (Clopper–Pearson) of the high-confidence error rate | < 10% | ≥ 10% | `blind_eval.clopper_pearson` | none | Depends on the 17 likely_substellar | secondary | `h11_outcomes.metrics` |
| H11c | O1 rate in candidates vs controls | descriptive | — | none | none | — | descriptive | `h11_outcomes` (needs the controls) |
| **H12** | M1, M2a and M2b of `MECHANISM_PLAN.md` on systems new in DR4 | all three pass (intersection–union) | any one fails | `mechanism.main` via `dr4_mechanism.main` | `test_mechanism` (physics), smoke run on a fake table | Needs n ≥ 668 (power rule, A14) | confirmatory | `dr4_mechanism` (cross-match exclusion, power rule, IUT p-value) |
| H13 | f(β̂ ≥ 0.2 \| Kmax ≥ 50) / f(β̂ ≥ 0.2 \| Kmax < 30) | Lower 95% > 1. Only the trend is tested. The dilution model got the level wrong on DR3 by a factor of 7–10, and we don't claim it | lower ≤ 1 | `dr4_mechanism.h13` | smoke run | DR3: 2.66 [1.87, 3.90] at n = 10 118 | secondary | exists |
| H14 | ĉ = median (vbroad² − med²)/b for b ≥ 25 | CI overlaps [1.4, 2.3]; c = 4 rejected if upper < 4 | no overlap | `mechanism.main` (M4) + `dr4_mechanism.main` | smoke run | DR3 n = 1731 | secondary | exists |

## How we checked this ledger
We opened every function listed under "Code" and read it. Where something is marked missing, we went looking first, grepping for the hypothesis id, the metric name and the outcome codes, and came up empty.

The sealed label file got far less scrutiny, on purpose. We read its field names and its label vocabulary. No object's value. Applying the analysis rule "label ∈ {impostor, substellar}" yields the registered counts, 39 + 26 = 65 of 76, and the runner must assert those counts and halt if they differ.

## Which sample each analysis uses (section G)
| Analysis | Sample | Where it was fixed | When |
|---|---|---|---|
| DR3 study (P1–P3, H7-DR3) | 2102 = 2138 rows − 19 duplicates − 17 without TI errors; sealed ids removed first | DR3_STUDY_PLAN.md + deviation 5 | plan before data; deviation 5 before labels |
| AstroSpectroSB1 check | 95 candidates with combined solutions | rules in astrospectro_check.py | before comparing with scores |
| H10 | 33 464 combined solutions with ϖ/σ > 10 → 19 506 after the MS and quality cuts → 1927 labelled with vbroad (≥ 5 transits) | DARK_COMPANION_PLAN.md + deviations 8–11 | plan before download |
| vbroad v2 | the same 1927, split by digit-sum parity into TRAIN 940 / TEST 987 | VBROAD_V2_PLAN.md + deviation 12 | before running |
| Mechanism (M1–M4) | the same 19 506, all of those with usable vbroad whether labelled or not = 10 118; the dark sample is label 0 within them (1085) | MECHANISM_PLAN.md §2 ("Sample V") | hashed before the run |
| H12–H14 (DR4) | v0.6 A15: DR4 combined solutions with ϖ/σ > 10, minus DR3 ids and sealed ids, same cuts as H10 | v0.6 draft | before DR4 |
| H17 (DR4) | DR4 candidates with ≥ 20 accepted G epoch-photometry transits | v0.6 A32 | before DR4 |
| H18, H19 (DR4) | the H12 sample (all labels, not just vbroad), with m₂,dyn ≥ 1.4 M☉ (H18) or a dark-assumed m₂ of 13–80 MJ (H19); resolved ρ labels only | v0.6 A33–A34 | before DR4; in DR3 development there were 83 and 35 resolved |

Why 10 118 and not 1927? Because M1–M4 test a physical relation between orbit quantities and vbroad, and a relation like that needs no ρ label. The plan therefore took every system with vbroad. M2a is the exception; it alone works on the labelled dark subset.
