# Deviations after amendment v0.5

Entries 1–12 live in `DR3_STUDY_DEVIATIONS.md`. That file is frozen in the v0.5 manifest, so the log continues here, starting at 13.

## 13. The mechanism plan's timestamp
`MECHANISM_PLAN.md` claims it was written at "~23:30 UTC+4". Wrong. The timestamp in `MECHANISM_PLAN.sha256` shows the SHA-256 stored on 30 Oct 2026 at 18:55 UTC, which is 22:55 UTC+4, and the text was never edited after that.

No consequence follows. The file times (UTC) line up cleanly: plan hashed at 18:55:53, `src/mechanism.py` saved at 18:56:48, the M3 validation (which uses no vbroad) written at 18:57:41, and the first run of the pre-registered tests written at 18:58:25. The only later run is the identical re-run in entry 15.

## 14. What we added to the mechanism tests after seeing the results
E1–E3 in `RESULTS_MECHANISM.md` came after the pre-registered results were in. They carry an exploratory label and leave every pass/fail verdict alone.

E3, the forward model of RV-centroid dilution, ran once. Its resolution scale was fixed in advance at 26 km/s, the RVS FWHM at R = 11 500. No tuning.

## 15. A small-sample guard for M3, added after the DR3 run
A smoke test of the DR4 path crashed. We had built a fake 3000-row "DR4" table out of DR3 rows with new ids, and on it the small-separation bin of M3 held no bright companions at all. Every bootstrap ratio blew up to infinity.

`mechanism.m3` and `dr4_mechanism.h13` now return "no verdict" (NaN, pass = false) whenever fewer than half of the bootstrap ratios are finite. DR3 is untouched by this: after the fix we re-ran `mechanism.py`, and the content of `results/mechanism.json` matched byte for byte.

## 16. Two files frozen in the v0.4 manifest were later changed in place
`FREEZE_MANIFEST.sha256` (OSF N5H4B) lists `src/rvs_predict.py` (a0405a88…) and `DR3_STUDY_DEVIATIONS.md` (5708c1e6…). Neither hash matches any more.

For `rvs_predict.py` the explanation is benign. The change is amendment v0.5 A6, which is registered (OSF TBJGY), and the v0.4 version survives byte for byte in `repo_push/src/rvs_predict.py`.

`DR3_STUDY_DEVIATIONS.md` is a real lapse. Deviations 5–12 were appended to the frozen file instead of going into a new one. The v0.4 bytes (5708c1e6…) are nowhere in this workspace; the zip and git copies disagree. The user's GitHub history or Downloads folder may still have them.

The rule from here on is simple: never append to a frozen file. New logs get new files, this one included. We caught the problem in the 31 Oct 2026 audit with `sha256sum -c FREEZE_MANIFEST.sha256`. `FREEZE_MANIFEST_v0.5.sha256`, by contrast, verifies completely.

## 17. Units bug F6 (K_sum fed the period in years) and the corrected re-analysis
Found on 31 Oct 2026, during the audit, by tracing every caller of `K_sum_kms`. That function expects days.

The damage is large; the ERRATUM in `RESULTS_DARK_COMPANION.md` lays it out. Registered H10 and V1–V3 results stay as registered, and `results/erratum_k_units.json` carries the corrected numbers beside them.

The bug also knocks out a premise. `MECHANISM_PLAN.md` §1 says: "Our first physical model predicted broadening in the wrong direction … adding the SB1 selection fixed it". That sentence is false. The mechanism tests escape, though. `mechanism.py` never calls the buggy function; it gets K from a1 sin i, with P in years and its own correct constant, so M1–M4 stand.

All of this happened before any DR4 data existed. Which way a fix pushed a result played no part in any decision about it.

## 18. Pre-DR4 obligations of the H11 plan, met on 31 Oct 2026
Second prediction set (v0.4 A1): `results/dr3_candidates_scored_A1.csv`, SHA-256 d8c9b2e27bef04e6…, C* = 0.3. Deterministic; a re-run reproduces the hash.

The H11a Brier baseline needs a CMD-only probability, now frozen as `results/dr3_candidates_B2prob.csv`, SHA-256 d86774c7… (v0.6 A20). Getting there took two tries. EM with a constant π saturated at π = 0.9999 and turned B2 into a near-constant "all impostors" predictor, which is useless as a baseline. So the primary became GAIA-FP's own frozen prior combined with the pure-CMD likelihood, and the EM version dropped to a sensitivity analysis. Only DR3 predictions informed this; outcome data don't exist.

The control-group code is ready (`src/h11_control.py`). It needs a DR3 download of Orbital and AstroSpectroSB1 solutions, still pending, and that requires the user's permission.

## 19. Mechanism code corrected after the independent audit (31 Oct 2026)
Two fixes. `mechanism.py` now takes 4096 phase samples for pavg and smax (audit A1-F6); the old 64 samples, "as in vbroad_v2.py", could miss by a factor of up to 2.7 at e = 0.95. And M3 and H13 stopped discarding bootstrap replicates that come out +∞ (audit A2-F17).

Re-run on DR3 development data:

| Test | Before | After |
|---|---|---|
| M1 | 0.218 [0.199, 0.237] | unchanged |
| M2a | | unchanged within 0.001 |
| M2b | | unchanged within 0.001 |
| M4 | | unchanged within 0.001 |
| M3 | D upper 6.26 | D upper 6.62, still FAIL |
| H13 | 2.66 [1.87, 3.90] | 2.59 [1.82, 3.80] |

The plan does say "as in vbroad_v2.py". We read the fix as better precision on the same quantity, not a switch to a different one.

## 20. What the audit read from the sealed label file
Field names, the label vocabulary, aggregate counts. Nothing else. We needed exactly that much to write the runner's assertion (39 impostor + 26 substellar of 76). No individual label, no Gaia value for any sealed object.

## 21. 1 Nov 2026: the H11 DR3 control set, regenerated independently from the bundled DR3 NSS source
We re-ran the control builder on `realdata/dr3_nss_two_body_orbit_raw.csv` plus the frozen candidate and field inputs. Out of an eligible pool of 31,349 systems it picked 2,102 one-to-one controls. The new `results/h11_controls.csv` was byte-identical to the archived file: SHA-256 `cd56e49a6d1ae0baccfd7b334780bee29c351fff3b0751fa803d246570d3b42d`.

That settles reproducibility of the DR3 control construction and makes the "download not yet done" note in entry 18 obsolete. Don't over-read it, though. It is not an H11 DR4 outcome, and it says nothing astrophysical about the classifier.

## 2026-11-03: reconciling the A6 light-ratio threshold (pre-DR4)
Two files disagreed. A code audit found that `src/rvs_predict.py` applied the registered A6 threshold to the secondary-to-primary flux ratio, `ell = q**n >= 0.2`, while `src/rvs_v32.py` applied it to the secondary's share of total light, `beta = ell/(1+ell) >= 0.2`. The second is stricter (`ell >= 0.25`). The registered text says "light ratio >= 0.2" and the original registered code uses `q**n`, so v3.2 now uses `ell = q**n` as well. `beta` still serves as the blend fraction in the registered `f(1-f)` variance term; it plays no role in A6 selection. A regression test targets the interval where the definitions part ways, `0.2 <= ell < 0.25`. No result drove this, and no DR4 data were touched.

## 22. Merging the parallel work sessions (6 Nov 2026)
This session hit a rate limit between 1 and 3 Nov, and work continued in other sessions on copies of the 31 Oct package. We merged the latest copy (`GAIA-FP_REVISED_DATA_PIPELINES_2026-11-03`) into this tree, checking every change with `diff` before accepting it.

That copy had appended to the frozen `DR3_STUDY_DEVIATIONS.md` again, as a duplicate "13" and a "final completion" note. We restored the file byte for byte (v0.5 manifest: all 56 OK) and moved the content here. On 1 Nov, `tools/fetch_realdata.py` was changed to ask for the full LAMOST-MRS coverage catalogue (`COUNT(*)`, `AVG(RAJ2000)`, `AVG(DEJ2000)`, grouped by Gaia id) rather than 300-id chunks; it has never run against VizieR, and we claim no new `lamost_cov.csv`. On 3 Nov came evidence-only lineage tables, APOGEE allVisit and exact-cadence injection scripts, and a per-spectrum RV pipeline for LAMOST DR9 (`results/final_completion/`, `FINAL_COMPLETION_REPORT.md`).

Both copies had caught the A28 error on their own: A6 must use the light ratio ℓ = qⁿ, not β = ℓ/(1+ℓ). The merged code goes through `rvs_v32.sb1_keep_mask`. The pre-erratum S1 is retired; its column in the mechanism output is now `S1_pre_erratum_DO_NOT_USE`.

The H11 control group (pool 31 349, 2102 of 2102 matched, SHA-256 cd56e49a…) came from `realdata/dr3_nss_two_body_orbit_raw.csv` (71 759 rows). We rebuilt it in this session with `src/h11_control.py` and matched it bit for bit. After the merge: 127 tests passed.

## 23. 6 Nov 2026: parallel scoring, the H15 runner, a bug the dry run caught
`dr4_run.score(workers=…)` computes the RVS term in parallel now, and a test confirms the parallel and serial catalogues are identical. Two cores cut the scoring step from 642 s to 293 s. On eight, DR4 scale should take 15–20 minutes.

`src/h15_purity.py` is the H15 runner. Descriptive (A29), 2 tests.

Then the bug. The A27 wrapper, `dr4_mechanism.rho_labels_chunked`, called the monkeypatched `DC.rho_labels` and recursed until Python gave up (RecursionError). Passing the original function in explicitly fixed it. The full dry run then completed, 12/12 steps, in 318 s. 130 tests passed.

## 24. 6 Nov 2026: external APOGEE data, H16 pre-registered, the H4 adapter
We downloaded the APOGEE DR17 multi-visit catalogue; provenance is in `realdata/PROVENANCE.md`, the exploratory analyses in `RESULTS_APOGEE.md` and `RESULTS_FP_CHARACTERIZATION.md`.

H16 entered v0.6 (A30) after we had seen its DR3 development value, AUC 0.73 with 8 positives. That is not a problem for the test, because H16 runs only on DR4 candidates, and those don't exist yet. The DR3 number is development data, just as it is for H12–H14.

`src/dr4_epoch_astrometry.py` is the H4 epoch-astrometry adapter, tested with a round trip on the Gaia-4 pre-release data. 132 tests passed.

## 25. 7 Nov 2026: ESA's draft DR4 data model, read; four breaking differences, handled
The user fetched `gaia-dr4-prerelease-draft-data-model_2026-06-26.zip` from ESA's anonftp in their built-in browser, and a copy sits in `docs/dr4_datamodel/`. `src/dr4_release_map.py` now handles four differences, with 4 tests:
1. `solution_type` replaces `nss_solution_type`.
2. No `c_thiele_innes` or `h_thiele_innes`. We rebuild a1 sin i from `semi_amplitude_primary`; against DR3 it is exact.
3. `dr3_neighbourhood.angular_distance` is in mas, not arcsec.
4. Epoch RVS time is `obs_time_rv` (days since 2010) plus `obs_time_bary_corr` (ns), and only valid vbroad transits count.

It is a draft, so the schema guard still stops on any further change. One more fix the same day: the solution-type count query in `dr4_fetch.py` was still asking DR4 for `nss_solution_type`. It asks for `solution_type` now.

## 26. 7 Nov 2026: power analysis, and the switch to weighted Holm (A31)
`audit/power_h1.py` simulated H1 with 39 impostors and 26 substellar. True AUCs of 0.65 / 0.70 / 0.73 / 0.80 are detected with probability 0.28 / 0.58 / 0.75 / 0.97 at α/5 = 0.005, and 0.56 / 0.82 / 0.90 / 1.00 at α = 0.025. Lose a quarter of the labelled objects to missing DR4 orbits and each figure drops by roughly 0.1.

Those numbers made the case. A18 became weighted Holm (A31) before v0.6 was registered and before any DR4 data existed, with equal-weight Holm kept as a sensitivity analysis. No sealed label and no DR4 value went into the decision.

## 27. 7 Nov 2026: three secondary hypotheses (H17–H19, A32–A34)
The aim was to ask a bigger question. Not just "how many planet candidates are impostors?" but "how many of Gaia's invisible companions are?", a question that reaches black-hole and neutron-star searches and the brown-dwarf desert. We also wanted a second, independent data channel, and Gaia epoch photometry provides one. All three hypotheses are secondary and stay outside the weighted-Holm family, so H1 loses no power.

H18 and H19 were written after we computed their DR3 development values (0.96 and 0.94). They will be judged only on systems new in DR4, so the DR3 values are development data, the same arrangement as H12–H16. H17 has no development value.

Before writing H18 we checked Gaia BH2. ρ = 0.92: not flagged as luminous, as it shouldn't be. Gaia BH1 isn't in our DR3 AstroSpectroSB1 table.

Code: `src/new_hypotheses.py` (5 tests), `dr4_release_map.epoch_photometry` (1 test), `dr4_fetch.epoch_photometry` (not yet tested against the live archive). H18/H19 run inside `dr4_mechanism.py`.

## 28. 8 Nov 2026: development numbers re-checked (no DR4 data, no sealed labels)
H18 with n_mc = 5000 labels (`audit/h18_h19_dev_mc5000.py`): 80/81 = 0.99 [0.93, 1.00], up from 80/83 with the stored n_mc = 200 labels. Two labels changed. H19 holds at 33/35. A33 is updated to match.

H1 power, computed directly at α = 0.01 (`audit/power_h1_weighted.py`): 0.82 for AUC 0.73 with 39 + 26 objects, 0.69 if only 30 + 20 remain, 0.39 for AUC 0.65. These replace the interpolated "≈ 0.85".

How badly are the candidates' own masses underestimated? `audit/candidate_mass_bias.py` (exploratory) gives a first answer. 95 of the 2102 candidates also have a combined orbit, and 42 of those are impostors under the 9 Oct label rules. For them, the dynamical companion mass runs at a median 4.0× [3.5, 5.5] the catalogue, dark-assumed mass: 252 against 64 MJ. The "2.4×" we quoted earlier belongs to another sample entirely (1186 luminous combined-orbit systems, `RESULTS_FP_CHARACTERIZATION.md`) and must not be pinned on the candidates. One caution. The label rule itself uses m2_dyn > 80 MJ, so "every impostor is above 80 MJ" is partly circular. The ratio is not.

Small correction: Gaia DR3 holds about 1.8 billion sources, not "over 2 billion".

## 29. 8 Nov 2026: the DR4-day chain finished after an external review (no DR4 data, no sealed labels)
A second, external AI review on 7 Nov found real gaps. We checked each claim against the code before fixing anything.

`dr4_day.py` only knew how to do a dry run. It now has `prepare` and `run`, and the dry run calls the same `run_chain` the DR4 run uses (COMPLETED, 13 steps, 352 s).

Nobody had ever downloaded the DR3→DR4 id map. Without it, the sealed labels could not have been matched in DR4 at all. `dr4_fetch.py` now fetches `dr3_neighbourhood` for the DR3 candidates, the sealed ids (ids only), the DR3 AstroSpectroSB1 sources and the H11 controls, and also the H11 orbits, the D3 combined orbits and the D2 field vbroad sample.

Above 2000 candidates, the RVS query joined the entire NSS table. It now sends candidate ids in chunks of at most 2000.

The DR3-mode field query carried the DR4 table name (`dr4_pipeline.SCHEMA`). The 24 Nov "DR3" test would quietly have queried DR4. Every query is now built for the release actually chosen.

DR4 puts `non_single_star` in `all_source_flags`, not `gaia_source`, so the field queries join it. A name changes; the criteria don't.

The a1 sin i error derived from `semi_amplitude_primary` now includes the eccentricity term e·σe/(1−e²).

We also measured H1 power with the registered bootstrap test itself (`audit/power_h1_bootstrap.py`, 400 simulations per cell, α = 0.01):

| Sample | AUC 0.5 (false positive) | 0.65 | 0.70 | 0.73 | 0.80 |
|---|---|---|---|---|---|
| 39 + 26 | 0.015 | 0.41 | 0.67 | **0.83** | 0.99 |
| 30 + 20 | 0.010 | 0.33 | 0.58 | 0.71 | 0.93 |

They agree with the Mann–Whitney approximation (0.82). The bootstrap p-value also sits close to nominal, 0.015 ± 0.006 against a nominal 0.01, which closes the calibration question audit A2 had left open.

The wording got tighter too. The README and summaries now state that the 91% is a model classification, not a confirmed prevalence; that the primary score uses the empirical vbroad term (the physical S1 trails CMD + empirical vbroad by −0.019); and that the APOGEE AUC is positive-versus-unlabelled. Prior work (Bailer-Jones & Kreidberg 2026; Hadad et al.; Marcussen et al. 2026) was already in `NOVELTY_AND_PRIOR_ART.md` and now appears in the README as well.

The review got one thing wrong. A mean prior equal to the mean posterior (0.940) is simply EM's fixed point; it doesn't show that the prior dominates. Its conclusion, that the 91% is a model estimate, is nonetheless correct.

Still open: the 1927 vs 1926 sample count (H10 vs mechanism), the live-archive test (24 Nov), and a direct comparison with the Bailer-Jones & Kreidberg masses (their VizieR table J/A+A/708/A249). 146 tests passed.

## 30. 8 Nov 2026: Bailer-Jones & Kreidberg 2026 comparison (exploratory; plan hashed before the run)
Plan: `BJK_COMPARISON_PLAN.md`, SHA-256 b55a1e7e…, stored at 12:01 UTC, before the run. The catalogue came from MPIA that day (`realdata/external/bjk2026_orbital300.csv`).

`RESULTS_BJK_COMPARISON.md` has the outcome. On survey SB2 labels GAIA-FP wins, ΔAUC +0.22 [+0.08, +0.39]. On APOGEE labels, no detectable difference, with only 7 positives. And BJK calls just 11% of GAIA-FP's likely impostors stellar.

Two frozen development results stay exactly as they were: the 95-object combined-orbit check and the DR3 × SB2 test (P2). Re-fitting the model to beat them, after seeing them, would be post hoc.

## 31. 8 Nov 2026: an attempt to enlarge the RV label set with Gaia DR3 RV amplitudes (plan hashed first)
Plan: `GAIA_RV_LABEL_PLAN.md`, SHA-256 5f50bac9…. It produced 2 positives among 487 candidates. The minimum is 5, so the test is NOT CONDUCTED (`RESULTS_GAIA_RV_LABELS.md`). We left the rule exactly as written after seeing the count.

## 32. 8 Nov 2026: final review before registration
One serious omission surfaced. DR4 publishes primary masses in `nss_masses`, its version of the DR3 `binary_masses` table the frozen DR3 predictions relied on, and `dr4_fetch.py` wasn't downloading it. DR4 scoring would have fallen back on the photometric relation for every single star, silently. The masses are now fetched for the candidates and the combined orbits; `prepare` merges them, falls back to the photometric relation row by row, and logs the count. This is A36.

We also added H20 (A35, secondary): a head-to-head on the sealed labels against Gaia DR4's own flux ratio and substellar probabilities, and against Bailer-Jones & Kreidberg 2026. Comparator scores are hashed before unblinding.

Dry run: COMPLETED, 14 steps. The fake-archive test exercises the masses and the fallback.

## 33. 8 Nov 2026: wording edited for readability in the OSF files
After the hashes above were stored, we rewrote the eight Markdown files in this package (`OSF_REGISTRATION_v0.6.md`, `CURRENT_RULES.md`, `PREREG_AMENDMENT_v0.6.md`, `DEVIATIONS_v0.6.md`, `HYPOTHESIS_LEDGER.md`, `DR4_READINESS.md`, `BJK_COMPARISON_PLAN.md`, `GAIA_RV_LABEL_PLAN.md`) so they read more easily. No rule, number, threshold, sample, hash or file name changed. `original/` keeps the files exactly as hashed. The stored hashes of the two exploratory plans (`BJK_COMPARISON_PLAN.sha256`, `GAIA_RV_LABEL_PLAN.sha256`) match those original copies, which are the versions that existed before the runs. `FREEZE_MANIFEST_v0.6.sha256` has been updated for the edited files.
