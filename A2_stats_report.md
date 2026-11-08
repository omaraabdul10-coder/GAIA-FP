# A2: statistics, likelihoods, randomness and edge cases (audit of 31 Oct 2026)

**Snapshot.** At audit start every file in `FREEZE_MANIFEST_v0.5.sha256` and `FREEZE_MANIFEST_v0.6_DRAFT.sha256` verified OK. Files added during the audit were reviewed at these hashes:
- `dr4_run.py` 093f9631…
- `dr4_evaluate.py` 8affe1d3…
- `h11_outcomes.py` 508017f6…
- `dr4_mechanism.py` b2837337…

**How the work was done.** No file under GAIA-FP was modified. Nothing sealed or PRIVATE was opened, and neither was `dryrun/FAKE_labels.json`. All re-runs used copies in `audit/scratch/` (`src/`, the corrected copy `src_fix/`, `realdata/`, `results/`, `dryrun_copy/`), and the scripts are in `audit/scratch/work/`. Tests: `audit/tests_stats.py`.

**Verdict.** Three findings can make a DR4 verdict wrong without any warning: the physics RVS likelihood (F2–F4), the H2 operating point (F5), and the NaN handling (F6, F7).

## Findings

| # | Sev. | Where | Finding | Evidence | Effect on published results / DR4 |
|---|---|---|---|---|---|
| 1 | **critical** (already logged as F6 / `erratum_k_units.py`; independently confirmed) | `dark_companion.py:89`, `vbroad_v2.py:20` | `K_sum_kms` expects P in **days**, but these two calls pass P/365.25. K_sum is therefore 7.148× too large. | `K(1 M☉, P=1 "day")` = 212.9 vs 29.78 km/s; xfail `test_lr_vbroad_uses_days`. A re-run with the fix (`work/run_h10.py`) reproduces the erratum numbers exactly. | See the corrected numbers below the table. |
| 2 | **critical** | `rvs_predict.py:35-37` | **LLR_RVS(z) is not monotone in z.** The KDE bandwidth (0.5) is narrower than the null SD (1), and SB1 truncation removes high-K draws. Together they make a strong phase-locked signal count as **planet** evidence. | One candidate (P = 216 d, nep = 39): z = 2, 4, 6, 8, 10, 14 gives LLR = +0.9, +3.5, +7.8, +3.5, **−12.8, −30**. The same shape appears for 3 of 3 candidates (`work/llr_rvs_mc.json`); xfail `test_llr_rvs_monotone_in_z`. | DR4 secondary score, but P_impostor, the verdicts and H1/H3/H5/H8 use it. A real twin with a clear RVS signal can be labelled `likely_substellar`. |
| 3 | **critical** | `rvs_predict.py:18` (n_draw = 40) | **Monte Carlo noise of the 40-draw H_t KDE.** | Seed SD of log LR across 150 candidates: median 0.20 / 0.34 / **2.4** nats at z = 0 / 2 / 4, maximum 7.7. On the DR4 path (`dr4_run` logic, DR3 orbits as fake DR4, **null** RVS widths, `work/dr4_seed.py`), changing only the seed changes the verdict of **447 of 2102** candidates. With π held fixed it is 399 of 1238 RVS candidates (32%), and C* = 0.3 for every seed. Worst case: a candidate with z = −1.04 has log LR −7.0, −29.4, −1.6, −0.8, −20.8 across five seeds. | The DR4 catalogue verdicts are not reproducible beyond the seed. 40 draws are far too few. Use ≥ 2000 draws (or exact quadrature over (q, n)) plus a per-candidate seed. |
| 4 | major | `lik.py:17-19`, `dr4_pipeline.py:131-132` | **Order dependence.** One RNG is threaded through all rows, and it is restarted at the same seed for every `sig_cmd` group. A candidate's score therefore depends on which other candidates exist and on their order. | Same seed, reversed row order: median \|ΔLLR\| = 0.30, maximum 1.70 (z = 2); xfail `test_llr_rvs_order_independent`. | Adding or removing one DR4 source changes other candidates' P. Seed each candidate from its source_id. |
| 5 | **major** | `blind_eval.py:43`, `dr4_evaluate.py:51` (`rejection_at_retention`), also `tournament.rej95`, `hier_em.rej`, `benchmark.rej_at` | **H2 operating point.** `np.quantile(·, 0.95)` interpolates, so the achieved substellar retention is below 95% and the reported rejection is optimistic. | n_sub = 26: retention 24/26 = 92.3% (90% target → 88.5%). n_sub = 12: 91.7% / 83.3%. The DR4 dry run had n_sub = 13, i.e. 12/13 = 92.3%. xfail `test_operating_point_achieves_nominal_retention` (3 cases). | H2 confirmatory test. Use the order statistic `sort(s0)[ceil(0.95·n)−1]` and report the achieved retention. |
| 6 | major | `blind_eval.py:23-26`; `dr4_evaluate.py:51` | **NaN gives a finite wrong number.** In `roc_auc`, comparisons with NaN are False, so a NaN-scored positive counts as losing every pair (the example gives 0.8 instead of 1.0). In `rejection_at_retention`, `np.quantile` returns NaN when any substellar score is NaN, and the rejection is then 0.0. The `auc` functions in `dark_companion` and `dr4_evaluate` (rankdata) propagate NaN correctly. | xfail `test_roc_auc_nan_fails_loudly`, `test_rejection_at_retention_nan_fails_loudly`. | `dr4_evaluate` checks only P_impostor ∈ [0,1]. score_emp, dm and sig_cmd are not checked, and H2 uses score_emp. |
| 7 | major | `dr4_pipeline.py:131` | **Silent neutral LR.** `groupby(sig_cmd.round(2))` drops NaN keys, so rows with NaN sig_cmd (e.g. NaN bp_rp) keep L = 0 and get P = π. The run crashes only if such a row lands in the ambiguous band (inside EIG). | Demo (`work/dr4_nan_sig.py`): log_lr = 0.0, P = prior; xfail `test_score_nan_sigma_not_silently_neutral`. | The frozen `score` CLI has no finite filter. `dr4_run.score` adds one (line 34), so use only `dr4_run`; never call `dr4_pipeline score` on DR4. |
| 8 | major | `hier_em.phi` (`hier_em.py:41-43`) | **CMD evidence counted twice through the prior.** φ contains G and ln d, and M_G = G − (5/ln10)·ln d + 5 exactly, while ΔM_G = M_G − ridge(colour) is already in L. EM can therefore re-learn the CMD signal into π. | Toy with class-independent covariates: corr(logit π, ΔM_G) = −0.21. Brier 0.109 vs 0.105 for the true constant prior. Top bin predicts 0.941 against 0.898 observed (n = 413). On DR3, corr(logit π, M_G) = 0.68 and corr(logit π, log_lr) = −0.21. xfail `test_em_prior_does_not_relearn_cmd`. | H3 (calibration) and H5 (contamination) are biased in an unknown direction. Use colour-independent covariates, or remove the M_G direction. |
| 9 | minor | `rvs_phase_test.py`, `dr4_pipeline.rvs_z` | **Null calibration of z.** SD = 1.00 ± 0.02 and mean ≈ 0 for n = 6–40 (homoscedastic and heteroscedastic noise). But the upper tail is heavier than N(0,1) because σ² and the template are both skewed: P(z > 2.326) = 1.3–2.3% (nominal 1.0%) and P(\|z\| > 3) = 0.3–1.0% (nominal 0.27%). With epochs in pairs that have correlated noise (Gaia preceding/following FoV), SD = 1.23–1.30 and P(z > 2.326) ≈ 3.7%. The clip at \|r\| = 0.999 never acts under the null. | `work/z_null.json`; xfail `test_z_null_upper_tail_matches_normal`. | The physics LR and the z > 2.3 outcome O5 are slightly anti-conservative. score_emp ranks only, so it is barely affected. |
| 10 | major (method) | `lik.llr_t` + `rvs_predict` vs `joint_lr` | **Same latent q not shared across modalities.** The RVS term marginalises over the prior q ~ U(0.5, 1), independent of p(q \| a0, ΔM_G). joint_lr instead uses q ~ U(0.1, 1) conditioned on a0. The product is not p(ΔM, z \| a0, H_t). `dark_companion` does this correctly with posterior weights W1/W2. | Code inspection. | Physics LR. Unchanged by the K fix. |
| 11 | major (prereg) | `rvs_predict.py:31` | The H_t simulation uses **random uniform epoch times over 2000 d**, not the candidate's own epochs (`span` is always 2000; the real `t` is never passed). Prereg §6.3 says "with the candidate's own … epochs". | Code. | Physics LR on DR4. |
| 12 | major (fail-loud) | `hier_em.py:20` (also `eval_lib`, `prior_eval`, `tournament`) | `warnings.filterwarnings('ignore')` at import time **silences every warning process-wide**. `dr4_run` imports `hier_em`, so every RuntimeWarning (0/0, log of a negative, NaN) during DR4 scoring is hidden. | Subprocess test: 1 warning before the import, 0 after; xfail `test_import_does_not_silence_warnings`. | Reduces the chance of catching F6/F7-type errors on DR4 day. |
| 13 | minor | `dr4_pipeline.py:115` | All-equal widths (std = 0) return z = 0.0, i.e. "no phase signal" used as evidence, instead of NaN, i.e. "no information". The same happens for e = 1 (the template is constant). | xfail `test_rvs_z_constant_widths_not_finite_evidence`. | Fill values or quantised widths would give planet-leaning evidence. |
| 14 | minor | `rvs_predict.py:20,33-34` | Invalid input (e = NaN, M < 0, nep ≤ 2) → all draws NaN → returns 0.0 silently. With nep = 3, all zs = 0, so z = 2 gives LLR = −5.3. The `n_ml` argument is dead (overwritten in the loop). | xfail `test_llr_rvs_invalid_input_fails_loudly`. | `dr4_run.guards` covers e and M, but not nep or srv. |
| 15 | minor | `blind_eval.clopper_pearson`, `calibration` | `clopper_pearson(3, 2)` returns NaN and `(−1, 5)` returns NaN, without an error. `calibration` accepts scores outside [0, 1] (Brier 4.6 for a log LR). `tournament.abstain_curve` uses `clopper_pearson(err, max(n, 1))`, which gives the CI (0, 0.975) for zero decisions. | xfail tests. | None to date. |
| 16 | minor | `followup.py:62,69-70` | In O3, q and n are drawn with **independent** random indices, which breaks their posterior correlation (corr 0.69): the predictive SD of ΔM_G is 0.109 instead of 0.051. The CMD evidence is subtracted from the prior while the q posterior still conditions on the old ΔM_G (a partial double count). The MC EIG can be < 0 (min −0.016 bits, 1/120 candidates). The best-option choice flips with the seed in 1/120 candidates. | xfail `test_eig_nonnegative`. | Follow-up recommendations only. |
| 17 | minor | `mechanism.m3:107`, `dr4_mechanism.h13:25` | Non-finite bootstrap ratios are dropped. In M3 the dropped replicates are D = +∞ (13/2000 on DR3), so the upper bound shrinks from 6.67 to 6.26. The pass rule needs upper < 0.5, so this is anti-conservative. In h13, dropping values biases the lower bound downward (conservative). | `work/m3_probe.py`. | DR3 unchanged (M3 fails either way). DR4 M3 is secondary. |
| 18 | minor | `dr4_evaluate.h3` | The "CMD-only" model uses `llr_cmd`, which is the a0\|CMD joint LR without RVS, not a CMD-only LR, together with the **full** model's prior π. This is inconsistent with H11a (A20), which uses a pure CMD LR, and the CMD-only model is not given its own prior. | Code. | H3 secondary. |
| 19 | minor | `dr4_run.py:36-39` | `best_followup` is computed for the v3.1 ambiguous set (EM C = 1), but the published verdict is the A1 verdict. Candidates that are ambiguous only under A1 get no recommendation. | Code. | Catalogue content. |
| 20 | minor | `dr3_study.paired_diff:99` | The first element is the bootstrap mean, not the point estimate (`dauc_ci` returns the point estimate). | −0.0508 vs −0.0500. | Cosmetic. |
| 21 | minor | `blind_eval.bootstrap_ci`, `prior_eval:52`, `h11_outcomes.metrics:84` | Unstratified bootstrap that drops resamples with an empty class. This is conditional and biased for small classes (prereg §7 asks for stratified). The `dr4_evaluate` H1/H2/H8 bootstrap is stratified (correct). | n_pos = 1 of 30: CI [0.83, 1.0]. | prior_eval DR3 CIs (exploratory); H11a ΔBrier CI. |
| 22 | cosmetic | `tournament.py:58`, `x3_heldout.py:23` | The follow-up experiment defines "ambiguous" as 0.1 < p < 0.9, while the frozen threshold is t = 0.15. X2 t* is 0.15000000000000002 (from linspace). | | |

**Corrected numbers for Finding 1** (H10 with c = 1; published value → corrected):

| Quantity | Published | Corrected |
|---|---|---|
| S1 AUC | 0.800 | 0.776 |
| H10a ΔAUC(S1 − B2) | 0.068 [0.042, 0.095] | **0.044 [0.033, 0.055]** (still a pass) |
| S2 AUC | 0.779 | 0.832 |
| H10c ΔAUC | 0.047 | 0.100 |
| vbroad v2, V1 | 0.759 | 0.745 |
| vbroad v2, V3 | −0.016 | −0.025 (still a fail) |
| Physical v1 vbroad LR alone | **0.444** | **0.736** |

The last row is the important one. The published "v1 ranks in the wrong direction (0.444)", stated in RESULTS_DARK_COMPANION and in the "Why" of v0.5, is an artefact of this bug. That was the stated motivation for **A6 (SB1_TRUNCATE)**. The corrected physical vbroad LR is still below the naive B2 + VB combination (−0.019), so the A7 conclusion survives.

## Randomness inventory (src/)

Fixed means a literal seed in code. "Doc" = documented in a plan or prereg (✓) or not (–).

| File:line | Draw | Seed | Doc | Published number that depends on it |
|---|---|---|---|---|
| `rvs_predict.py:19,24` | q, n per H_t draw (40) | caller's rng; **default unseeded** if rng=None | – | P_impostor / verdicts on any data with RVS (DR4) — F3 |
| `rvs_phase_test.py:39,43,45-46` | epoch times, width noise, analyst orbit perturbations | caller's rng | – | every z in sims; H_t KDE |
| `lik.py:18` | default_rng(seed=0), threaded over rows | 0 | – | log_lr (DR4), tournament, prior_eval mocks |
| `dr4_pipeline.py:136` | EIG RNG | seed 0 | – | best_followup |
| `dr4_pipeline.py:158-172` | selftest | 5, 9, 1 | – | selftest only |
| `followup.py:33,37,41,61-64,80,91-92` | posterior draws, epochs, MC outcomes | caller | – | best_followup; X3, x3_heldout |
| `hier_em.py:28` | sets the global `benchmark.rng` | seed arg | – | hier_em, eval_v3, contam_bins mocks |
| `benchmark.py:28,54,56,90` | global module RNG (2026): CMD noise, nep, B4 | 2026, but **order-dependent global state** | – | benchmark_sig*.json, v3_results, contamination_bins |
| `benchmark.py:89,98` | CV folds; bootstrap (n = 300) | 0; 1 | – | benchmark CIs |
| `sim.py:28,32,56-64` | mock sampling, noise | seed arg | – | tournament, prior_eval, sigp_validation |
| `tournament.py:24,57-59,83,102,141,168,182,195` | splits, follow-up, contamination subsamples | 11, 4, 8, 5, 99, 3 | partly | tournament_val/heldout.json |
| `x3_heldout.py:22-24,44` | follow-up | 4 | ✓ | x3_heldout.json |
| `eval_v3.py:32-33,58,66`; `contam_bins.py:5-9`; `hier_em.py:62-107` | mock splits, bootstraps (30–500) | 11, 3, 9, 5, 1 | – | v3_results, contamination_bins, hier_em |
| `identifiability.py:20`; `realism.py:14`; `synth_demo.py:5`; `lw_validation.py:8,26`; `combo_*.py:5`; `rvs_phase_test.py:55-56` | sims | 12, 5, 42, 3, 5, 1/11 | – | identifiability.json, realism.json |
| `inj_rec.py:5,20,32-34` | null and injection draws | 2026 | prereg §7 (400 nulls) | inj_rec FAP threshold 24.51, completeness |
| `mcmc_orbit.py:29,34`; `gaia_orbit.simulate:114` | walker init, subsample | 0, 1; seed arg | – | H4 BH3/Gaia-4 orbit CIs |
| `dr3_study.py:90,96,139` | bootstrap AUC (2000), paired diff, B4 random | 2026 | ✓ | dr3_study.json P1/P2 CIs |
| `dark_companion.py:35,97-98` | stratified bootstrap (2000); ρ MC (n_mc = 200) | 7 | ✓ (bootstrap; ρ MC n not stated) | dark_companion.json, all H10 labels |
| `astrospectro_check.py:30-38` | ρ / m2 MC (400; 150 for m2) | 0 | ✓ | astrospectro_labels.csv |
| `mechanism.py:27,67,79-89,102,138,141` | ρ σ MC, bootstrap, forward model, permutations (200) | 7, 8 | ✓ | mechanism.json M1–M4, P0 |
| `m3_validation.py:10` | synthetic catalogue | 11 | – | mechanism_m3_validation.json |
| `prior_select.py:43` | CV folds | 0 | ✓ (A1) | C* (DR3: 0.3, stable for fold seeds 0–5) |
| `prior_eval.py:42,50` | permutation; bootstrap | 6, 1 | – | prior_eval.json |
| `dr4_mechanism.py:24,36` | bootstrap h13, H12 p | 7 | ✓ | dr4_mechanism_dryrun_dr3.json |
| `dr4_evaluate.py:36` | stratified bootstrap (2000) | 7 | ✓ | DR4 H1, H2, H8, A5 |
| `h11_outcomes.py:35,83` | mass MC (400, seed 0); ΔBrier bootstrap | 0, 7 | ✓ (A20) | DR4 H11 |
| `dr4_day.py:27-` | fake inputs | 3, 9, 1, 2 | dry run | dry run only |

## Seed dependence (actual re-runs)

| Quantity (published) | Replicates | Re-run, 5 seeds | MC spread | Enough? |
|---|---|---|---|---|
| (a) ρ labels, H10 (1186 lum / 2060 dark) | n_mc = 200 | 640–647 of 3246 labels change per seed; 1365 change across the 5 seeds; **no 0↔1 swaps**. Against an n_mc = 5000 reference, 464 labels differ (299 labelled→undetermined, 165 the reverse). | H10a ΔAUC(S1 − B2) = 0.068 / 0.057 / 0.063 / 0.064 / 0.049 (reference labels: 0.057). B2 AUC 0.732–0.748. | **No.** Label MC noise (SD ≈ 0.007 in ΔAUC) is comparable to the sampling SE (≈ 0.013) and is not included in the CI. Use n_mc ≥ 5000. The pass/fail verdict is stable. |
| (b) H_t z-KDE (the DR4 log LR) | 40 draws | DR4 path, null widths: **447 of 2102 verdicts change** across seeds; π fixed: 399 of 1238; maximum ΔP ≈ 0.99. Single-candidate seed SD at z = 0 / 2 / 4: median 0.20 / 0.34 / 2.4 nats. Injected-signal AUC 0.732–0.737. | | **No** (F3). |
| (c) inj_rec 1% FAP threshold (24.51) | 400 nulls | 24.51 (seed 2026, reproduced), 23.78, 23.02, 22.53, 25.95. Reference from 20,000 nulls: 24.07. | SD 1.08. The actual FAP of each 400-null threshold is 0.4–1.8%. | **No** for "1% FAP" to better than ×2. Use ≥ 5000 nulls. |
| (d) DR3 P2 GAIA-FP AUC CI [0.487, 0.788] | 2000 bootstraps | Lower bound 0.487, 0.492, 0.493, 0.497, 0.491; over 50 more seeds 0.474–0.498, **never > 0.5**. | SD 0.005 | Yes for the verdict (FAILURE is stable). Report to 2 decimals. |
| (d) H10 AUC CIs (S1, B2, VB) and H10a | 2000 | Bounds within ±0.002; H10a lower bound 0.041–0.043. | | Yes. |
| (d) M1 / M2b partial ρ CIs | 2000 | ±0.001 | | Yes. |
| (d) M4 ĉ upper bound 2.052 (pass needs ≥ 2) | 2000 | 2.024–2.053 over 65 seeds. Always ≥ 2, but the margin is only 0.024. | | Marginal. State that the verdict is MC-limited. |
| A1 C* (DR3) | 5 folds | 0.3 for fold seeds 0–5 | | Yes. |

## Edge cases

| Input | Where | Behaviour | OK? |
|---|---|---|---|
| NaN bp_rp → NaN sig_cmd | `dr4_pipeline.score` | log_lr = 0, P = π (silent); crash only via EIG | **no** (F7); OK in `dr4_run` (filter) |
| NaN TI errors | `dr4_pipeline.score` | raises (sklearn sample_weight NaN) | loud; filtered in `dr4_run` and `dr3_study` |
| zero TI errors | `joint_lr` | finite (mass-error floor) | ok |
| negative parallax | `features` | m2 < 0, dropped by `select_candidates` (silently, not counted) | ok / minor |
| NaN G mag | `features` | dropped silently | ok / minor |
| e NaN | `phi` | raises (cryptic) | loud |
| missing `period_error` | `features` | KeyError | loud; `dr4_schema.check` in `dr4_run` |
| non-RangeIndex input to `score` | `dr4_pipeline.score` | IndexError | loud |
| 1–5 RVS epochs | `rvs_z` | NaN → LLR 0 | ok |
| all-equal widths, e = 1 | `rvs_z` | z = 0.0 | **no** (F13) |
| NaN width | `rvs_z` | NaN | ok |
| nep = 3, e NaN, M < 0 | `llr_rvs_physics` | −5.3 / 0 / 0 silently | **no** (F14) |
| NaN score | `blind_eval.roc_auc`; `rejection_at_retention` | finite wrong (0.8; 0.0) | **no** (F6) |
| NaN score | `DC.auc`, `dr4_evaluate.auc` | NaN | ok |
| one class | all AUCs | NaN plus warning (hidden by F12) | weak |
| empty class in a resample | `DC.boot`, `strat_boot` (stratified) | cannot occur | ok |
| empty class in a resample | `bootstrap_ci`, `prior_eval` | resample skipped (biased) | minor (F21) |
| k > n, k < 0 | `clopper_pearson` | NaN | **no** (F15) |
| scores outside [0, 1] | `calibration` / Brier | accepted | **no** (F15) |
| P_impostor outside [0, 1] or NaN | `dr4_evaluate`, `dr4_run` | SystemExit / SchemaError | ok |
| \|r\| → 1 | `rvs_z` | clipped at 0.999 (max z = 3.8·√(n−3)); never hit under the null | ok |
| underflow in the KDE | `rvs_predict:35` | floor 1e-300 then clip ±30 (masks F2 rather than fixing it) | see F2 |
| ρ < 0 (noisy parallax draws) | `rho_labels` | enters percentiles, no flag | minor |
| m2 bisection bound | `mechanism.solve_m2` | capped at 200 M☉ silently | minor |

## Suggested physical-impossibility asserts

- `rvs_predict.py:20`: `assert row['nep'] >= 6 and row['srv'] > 0 and 0 <= row['e'] < 1 and row['M'] > 0`.
- `rvs_predict.py:33`: `assert np.isfinite(zs).sum() >= 0.5*n_draw or <return explicit NaN + flag>`.
- `rvs_predict.py:37`: monotonicity check of LLR(z) on a z grid per candidate (or cap: `LLR(z) = max_{z' <= z} LLR(z')`).
- `dr4_pipeline.py:115`: `return np.nan` (not 0.0) when `std(s2) == 0`.
- `dr4_pipeline.py:130`: `assert X.index.equals(pd.RangeIndex(len(X))) and np.isfinite(X.sig_cmd).all() and (X.sig_cmd > 0.02).all()`.
- `dr4_pipeline.py:133`: `assert np.isfinite(L).all()`.
- `blind_eval.py:25` and `dr4_evaluate.py:32,51`: `assert np.isfinite(score).all() and 0 < y.sum() < len(y)`.
- `blind_eval.py:37`: `assert 0 <= k <= n`.
- `blind_eval.py:50`: `assert ((score >= 0) & (score <= 1)).all()`.
- `dr4_evaluate.py:51`: use the order statistic `np.sort(s0)[int(np.ceil(retention*len(s0)))-1]`, and return the achieved retention.
- `dr4_evaluate.py:154`: `assert not D.dr4_source_id.duplicated().any()`.
- `dark_companion.py:89` and `vbroad_v2.py:20`: pass days; add `assert 1 < np.nanmedian(K) < 300`.
- `dark_companion.py:102`: flag systems with `np.nanmedian(rho) <= 0`.
- `mechanism.py:107` and `dr4_mechanism.py:25`: keep ±inf replicates (use `nanpercentile`, treating inf as an extreme value) instead of dropping them.
- `followup.py:62`: draw one index array j and use `q[j]**n[j]`.
- `followup.py:71`: `assert EIG >= -1e-3`.
- `hier_em.py:20`: delete the module-level `filterwarnings('ignore')`; scope it with `warnings.catch_warnings()` around the sklearn call only.

## Checked, no error found

- **AUCs.** `blind_eval.roc_auc`, `dark_companion.auc` and `dr4_evaluate.auc` all match sklearn with heavy ties (|Δ| < 1e-15).
- **Clopper–Pearson.** `blind_eval.clopper_pearson` and `dr4_evaluate.clopper_pearson` match `scipy.stats.binomtest(…).proportion_ci('exact')` for all k ≤ n < 80 (|Δ| < 4e-15).
- **Likelihood ratios are proper ratios of normalised densities:**
  - `joint_lr`: the weights are a proper posterior on a uniform (q, n) grid; logsumexp is stable; E_planet[LR] ≈ 1 (existing test);
  - `lik.llr_w` and `effective_llr` (correct mixture denominator);
  - `dark_companion.lr_cmd_only`, `q_weights` and `lr_vbroad`: S1 and S2 are correct chain-rule factorisations apart from F1;
  - the KDE density itself;
  - `lik.posterior`.
- **Previously fixed double count.** The a0 and CMD double count is resolved (conditional p(ΔM | a0)).
- **EM (`hier_em.em`)** on the DR3 L:
  - converges in 49–85 iterations to the same optimum from π0 = 0.05, 0.3, 0.7 and 0.95 (obs-LL 1630.04);
  - reproduces the published P_impostor to 8e-16;
  - outputs lie in [0, 1];
  - on a toy, it recovers the covariate prior (mean 0.366 vs 0.367, correlation with the true π 1.000).
- **L2 C.** sklearn C = 1 with the lbfgs solver; the intercept is not penalised; the duplicated-row weights sum to n.
- **`prior_select`.** The held-out score formula is correct, the tie rule is correct, and C* is stable across fold seeds.
- **Stratified bootstraps.** `dark_companion.boot`, `dr3_study.boot_auc`, `dr4_evaluate.strat_boot` and the paired ΔAUC use the same indices for both scores.
- **`dr4_evaluate.holm`** step-down is correct.
- **Three-way verdict.** t = 0.15 is used consistently (≤ 0.15 and ≥ 0.85; `1-0.15 == 0.85` holds in float) in `dr4_pipeline`, `dr4_run`, `dr3_study`, `prior_eval`, `h11_prepare` and `survey_xmatch` (exception: F22).
- **Brier and reliability table.** The arithmetic is correct.
- **`mechanism.pcorr`** (existing test plus a re-run); the M1/M2b bootstrap is stable.
- **Reproduction.** All published H10, P2, inj_rec-threshold and EM numbers were reproduced bit-for-bit from the scratch copy.
- **Existing test suite.** 23/23 pass.

## Not checked

- Correctness of the astrometric pipeline (`gaia_orbit`, `mcmc_orbit`, campbell beyond the existing test).
- The physics of the mass–luminosity relation and of β(q, n).
- Mock-catalogue realism.
- `dr4_schema`, `dr4_adapters` time and unit handling (only used, not audited).
- The `dr4_dynamical` and `h11_outcomes` outcome rules (O1–O5) beyond the statistics in `metrics`.
- Validity of the bootstrap p-values as Holm inputs (percentile p ≈ dual of the CI; not simulated).
- The tournament, eval_v3, x3 and benchmark simulation results, which were not re-run (they need long mock runs).
- `survey_xmatch`.
- Correlated Thiele–Innes errors (an acknowledged limitation).

## Tests

`audit/tests_stats.py`: **17 passed, 18 xfailed (strict)**, 31.8 s. Every xfail maps to one of findings 1–9 or 12–16.
