# GAIA-FP audit report (31 Oct 2026)

**Rule followed throughout:** the goal is flawless execution, not a positive result. Every error found is fixed, even when the fix makes an expected result worse, and every fix is logged. Frozen files were not edited: fixes live in new files, and the changes are proposed in amendment v0.6.

**Who checked what:**
| Area | Checked by | Report |
|---|---|---|
| Geometry, kinematics, units, angles | independent code auditor 1 | `audit/A1_geometry_report.md`, tests `audit/tests_geometry.py` |
| Statistics, likelihoods, randomness, edge cases | independent code auditor 2 | `audit/A2_stats_report.md`, tests `audit/tests_stats.py` |
| DR4 data model and archive limits | independent web research | `audit/C_dr4_datamodel.md` |
| Registration, hypotheses, multiplicity, wording, sample definitions, runners, dry run | lead auditor (AI code auditor) | this report |

The two code auditors did not write the code they checked.

> **What "no error found" means here.** It means only that this audit did not find one. The code base had five known bugs before this audit and this audit found more (below), so further undiscovered errors are likely. The protection against them is not this report. It is the frozen order of work, the regression tests, and publishing every result whatever it says.


## Summary
- **New errors found: 30.** By auditor 1: 10 (geometry/units). By auditor 2: 22 (statistics; 2 overlap with auditor 1). By the lead: 9 integrity, registration and runner gaps. Duplicates are merged below.
- **Critical (4):**
  1. A units bug that created the project's main "selection-effect" story (F6).
  2. A non-monotone RVS likelihood: a strong twin signal could count as planet evidence.
  3. Monte Carlo noise in the RVS term that flips 447 of 2102 verdicts with the seed.
  4. Registered hypotheses with no code able to decide them on DR4.
- **Every critical and major item is now either fixed in new code or proposed as a fix in amendment v0.6, decided before DR4.** None was fixed in a way chosen to help a result. Several fixes make results worse (F6 lowers H10a from +0.068 to +0.044; A20 makes H11a harder to pass).
- **Tests:** project suite 47 passed. Auditor suites: 48 passed + 17 strict xfail (geometry) and 17 passed + 18 strict xfail (statistics). Each xfail documents an error in a FROZEN file. Each fix lives in a new file with its own passing test.

## A. Code audit: errors found
Severity: **C** critical, **M** major, **m** minor. "Fix" says where the correction lives. Frozen files are never edited.

| # | Sev | What | Found by | Effect | Fix |
|---|---|---|---|---|---|
| F6 | C | `dark_companion.lr_vbroad` and `vbroad_v2.lr_v2` pass the period in **years** to `K_sum_kms` (expects days). K is ×7.148, the blend variance ×51. | lead + auditors 1 and 2, independently | The "physical model ranks backwards (AUC 0.444)" result was this bug. Corrected: 0.736. H10a: +0.068 → +0.044 (still PASS). V3 still FAILs. The v0.5 A6 rationale is wrong. | `erratum_k_units.py`; erratum in `RESULTS_DARK_COMPANION.md`; v0.6 A23 |
| S2 | C | RVS log LR **not monotone** in z (KDE bandwidth 0.5 < null SD 1, plus truncation). z = 10 gives −12.8, i.e. "planet". | auditor 2 | Wrong P_impostor for strong twins on DR4 (H1, H3, H5, H8) | `rvs_v32.py`: bandwidth 1 + monotone envelope; test `test_monotone_in_z` |
| S3 | C | 40 Monte Carlo draws per candidate. The seed alone flips **447 of 2102** verdicts (dry-run data). | auditor 2 | The DR4 catalogue is not reproducible | 8000 draws + per-candidate seed. Seed SD ≤ 0.1 nats for z ≤ 3 and ~0.2 at z ≈ 4 (test). ~1 nat in the far tail (LLR ≈ 10), which cannot change a verdict |
| R5 | C | No DR4 code existed for H1, H2, H5, H6, H8/A5, H11. Two pre-DR4 obligations of the registered H11 plan had not been done. | lead | These hypotheses could not have been decided on 2 Dec | `dr4_evaluate.py`, `h11_outcomes.py`, `h11_prepare.py`, `h11_control.py`, `dr4_dynamical.py`, `h7_xmatch.py` |
| R3 | M | The frozen `dr4_pipeline.score` CLI never loads RVS epochs (`rvs=None`); `fetch` downloads none | lead | H2 impossible with the frozen pipeline | `dr4_adapters.py`, `dr4_run.py`, `dr4_fetch.py` |
| R1/R2 | M | Registered v0.4 A1 (prior selection) and v0.5 A7 (score_emp) are not wired into `dr4_pipeline.score` | lead | DR4 would have used an unregistered prior (C = 1) and no A7 score | `dr4_run.py` |
| R4 | M | The frozen fetch lacks Thiele–Innes C, H | lead | H8 impossible | `dr4_fetch.py` |
| S4 | M | One RNG stream for all rows: a candidate's score depends on the other candidates and their order | auditor 2 | Adding one DR4 source changes others' P | per-candidate seed (`rvs_v32.seed_of`) |
| S10 | M | The RVS term draws q from the prior U(0.5, 1), not the posterior given a0 and ΔM_G | auditor 2 | Modalities do not share the latent q | `rvs_v32`: (q, n) drawn from `q_weights` with a0 |
| S11 | M | H_t simulation uses random epochs over 2000 d, not the candidate's own (prereg §6.3 says its own) | auditor 2 | Departure from the registered method | `rvs_v32`: own epochs and per-epoch errors |
| G8 | M | σ_a0 = rms of the four TI errors ignores correlations: a median **2.6× too large** vs Gaia's a0/significance | auditor 1 | DR3 re-run: 70 verdicts move (likely_substellar 17 → 26); P2 0.643 → 0.652. The frozen DR3 predictions carry it. | `dr4_run`: σ_a0 = a0/significance (v0.6 A25). The frozen DR3 predictions stay as registered |
| S8 | M | The EM prior uses G and ln d, which rebuild M_G, so CMD evidence is counted again in the prior | auditor 2 | Over-confident top bin (0.94 predicted vs 0.90 observed, toy); H3/H5 biased | `dr4_run.phi_v32`: (log P, e, log m_fit) only |
| S5 | M | H2 retention via interpolated `np.quantile`: achieved 92.3%, not 95% | auditor 2 | H2 rejection optimistic | order statistic in `dr4_evaluate`; achieved retention reported |
| S6/S7, G4 | M | NaN → finite wrong numbers: `roc_auc` (0.8 instead of 1.0); `rejection_at_retention` 0.0; `score` gives log LR = 0 to NaN-colour rows; the DR4 CLI has no finite filter | auditors 1 and 2 | Silent wrong verdicts | finite filters + SystemExit checks in `dr4_run`/`dr4_evaluate`; the frozen CLI must not be used on DR4 |
| G2 | M | No reconciliation of epoch-time zero point with T0. A J2010/J2016 offset drops the median twin z from 5.97 to −0.56 | auditor 1 (+ ESA: DR4 epoch J2017.5) | Would silently null H2, A7, O5 | `dr4_adapters.to_rel_days` with a declared reference epoch; test shows the signal is lost with the wrong epoch |
| S12 | M | `hier_em` silences **all** warnings process-wide at import | auditor 2 | Hides numerical problems on DR4 day | `dr4_run` records every warning (`warnings.catch_warnings(record=True)`) |
| G3 | M | First-order companion mass underestimates m2 by (1+q)^(-2/3) (8–24% near the cut). 27% of DR3 candidates have an exact mass > 80 MJ | auditor 1 | Candidate list (frozen rule) and H11 O2 ("same formula") | **kept as registered** (it defines the frozen candidate set). The exact-mass count is reported as a sensitivity analysis (v0.6 A26) |
| R6 | M | H11a's B2 "Brier" is undefined (B2 is a score); the column `llr_cmd` equals log_lr on DR3 | lead | H11a would compare GAIA-FP with itself (ΔBrier = 0 exactly) | v0.6 A20 + frozen `dr3_candidates_B2prob.csv` |
| R8/R9 | M | DR4 ids are independent of DR3 ids. `h10`'s sealed filter compares integer ids (a no-op with string ids). `survey_xmatch` corrupts 19-digit ids via float64 | lead + auditor 1 | Possible leakage of DR3/sealed objects into DR4 tests; wrong H7 labels | cross-match-based exclusion with string ids (`dr4_mechanism.exclusion_ids`); `h7_xmatch.py` |
| G5 | m | Colours outside the CMD ridge range are clamped (45 of 2102 DR3 candidates) | auditor 1 | Silent wrong ΔM_G | excluded and counted in `dr4_run.prepare` |
| G6 | m | `phase_avg`/`maxsep_shape` use 64 phase samples: wrong by up to ×2.7 at e = 0.95 | auditor 1 | Mechanism dev numbers: M1 unchanged (0.218), H13 2.66 → 2.59 | 4096 samples in `mechanism.py` (re-run; deviation 19) |
| S9 | m | The null tail of z is heavier than N(0,1): P(z > 2.33) = 1.3–2.3% instead of 1% | auditor 2 | O5 (z > 2.3) slightly anti-conservative | reported; O5 is one of four impostor routes |
| S13/S14 | m | Constant widths or invalid input → z = 0 or LLR 0 silently | auditor 2 | Planet-leaning pseudo-evidence | `rvs_v32` returns NaN + reason |
| S17 | m | M3/H13 bootstraps drop ±∞ replicates (anti-conservative for M3) | auditor 2 | DR3 M3 upper bound 6.26 → 6.62 (still FAIL) | fixed (only NaN dropped) |
| S16 | m | Follow-up EIG: q and n drawn independently; EIG can be < 0 | auditor 2 | Recommendations only | reported; not a hypothesis |
| G7, G9, G10, S15, S18–S22 | m / cosmetic | `gaia_orbit.campbell` Ω mod 180; no validation in `solve_m2`/`K_sum_kms`; Clopper–Pearson NaN for k > n; H3 "CMD-only" convention; unstratified bootstraps in exploratory code; others | auditors 1 and 2 | none on registered numbers | documented in the auditors' reports |

**Checked and found correct** (auditors' lists, abridged):
- **Geometry:** Campbell ↔ Thiele–Innes (round trip 4e-11, including i = 0, 90, 180°); Kepler solver; photocentre formula (checked against independent quadrature); ρ; mass solvers; ω → ω+π invariance everywhere; no degree/radian mismatch anywhere else.
- **Real DR3:** C, H are in AU (median ρ 0.977); t_periastron is relative to J2016.0.
- **Statistics:** AUC vs sklearn with ties; Clopper–Pearson vs scipy; LRs are proper normalised ratios; EM converges from 4 starts and reproduces the published P to 8e-16; Holm; stratified bootstraps; t = 0.15 used consistently.
- **Reproduction:** every published number the auditors re-ran reproduced bit-for-bit.

**Seed dependence** (auditor 2, actual re-runs):

| Quantity | Spread | Enough replicates? |
|---|---|---|
| ρ labels (n_mc = 200) | ~645 of 3246 labels change per seed (no luminous ↔ dark swaps); H10a 0.049–0.068 across seeds | **No.** v0.6 A27: n_mc ≥ 5000 for DR4 labels. Pass/fail is stable |
| inj_rec 1% FAP threshold (400 nulls) | real FAP 0.4–1.8% | **No.** ≥ 5000 nulls before any FAP claim |
| DR3 P2 lower bound | 0.474–0.498, never > 0.5 | Yes for the verdict |
| H10, M1/M2b CIs | ±0.002 | Yes |
| M4 upper bound | 2.024–2.053, always ≥ 2 | Margin only 0.024. **M4 is reported as MC-limited.** |

**Physical-impossibility guards added** (in the new code, not the frozen files):
- a0, σ_a0, d, M, P > 0;
- 0 ≤ i ≤ 180°; 0 ≤ e < 1; σ_CMD > 0.02;
- finite ΔM_G and log LR;
- every probability finite and in [0, 1];
- no duplicate ids; one DR4 source per labelled DR3 source;
- ρ not far below 0 and m2 > 0 in `dr4_dynamical`.

## B. Registration integrity
- **FREEZE_MANIFEST_v0.5:** all 56 hashes verify.
- **FREEZE_MANIFEST (v0.4):** 2 of 48 fail.
  - `src/rvs_predict.py`: registered change v0.5 A6; the old bytes survive in `repo_push/`.
  - `DR3_STUDY_DEVIATIONS.md`: appended in place. The v0.4 bytes were **not recoverable** here; please check your GitHub history. Logged as deviation 16. Frozen files are never appended to again.
- **Plan hashes:**
  - DARK_COMPANION, VBROAD_V2, DR3_TO_DR4, MECHANISM and the DR3 predictions all verify.
  - `DR3_STUDY_PLAN.sha256` fails for `dr3_study.py` and `dr4_pipeline.py`; both are already logged (deviations 1 and 5).
- **Deviation log completeness:**
  - Deviations 6, 11 and 12 lack a clock time. Dates are inferable (9 Oct), but the file is frozen, so this is noted here instead.
  - Every deviation states before/after results.
- **v0.6 timeline:** `DR4_READINESS.md` §6. Register on **19 Nov**. **The Gaia archive closes on 25 Nov 12:00 CET**, so the control-group download and the live fetch test must happen by 24 Nov.
- **Blind-test integrity:** rule in v0.6.
  - Any DR4 exposure of a sealed, H11 or H12 object before the run means exclusion, logged with its date.
  - Only row counts and schema checks are allowed before the catalogue hash is committed.
  - The sealed label file was opened in this audit **only for field names, the label vocabulary and aggregate counts** (to fix the runner's assertion 39/26/76). No per-object label was read.

## C. DR4 readiness
See `DR4_READINESS.md`.
- **Dry run:** completed end to end (log `dryrun/dryrun_log.json`).
- **Not tested:** the live fetch, which needs internet and a registered Gaia account (`dr4_fetch.py`, untested; test it on DR3 by 24 Nov).

## D. Hypothesis ledger
See `HYPOTHESIS_LEDGER.md`.
- **H13 tests the TREND only.** The level prediction failed on DR3 and is not claimed.
- **H8 power:** the DR3 analogue had only 2 genuine-consistent objects, so H8's AUC and A5 are likely NOT CONDUCTED (fewer than 10 per class). This is stated in advance.

## E. Multiple comparisons
v0.6 A18:
- Holm, one-sided family-wise α = 0.025, m = 5: H1, H2, A5, H11a, H12.
- Everything else is secondary or descriptive.
- NOT CONDUCTED hypotheses leave the family; m shrinks.
- Headlines use Holm only.

## F. Wording
Fixed in non-frozen documents:
- "mechanism supported" → "consistent with DR3 development data; confirmatory test on DR4";
- M4 described as "at the edge of the window, half the theory value, unexplained";
- "first" claims → "we did not find an earlier one";
- "confirmed impostors" → "impostors by Gaia's own dynamics (not RV-confirmed)";
- the selection-effect story corrected on the site and in the docs;
- poster curve labelled "DR3 — development" with an empty DR4 panel.

## G. Sample definitions
See the table in `HYPOTHESIS_LEDGER.md`. Every analysis names its sample and the file where it was fixed before the run.

## What this audit did NOT check
- Mass–luminosity relation and isochrones.
- Mock-catalogue realism.
- The real DR4 data model, which is not public yet; the draft PDF must be read by a person.
- The live archive fetch.
- `gaia_orbit`/`mcmc_orbit` beyond existing tests.
- Correlated Thiele–Innes errors in the ρ labels.
- The validity of bootstrap p-values as Holm inputs (not simulated).

