# Deviations after amendment v0.5 (continues `DR3_STUDY_DEVIATIONS.md` 1–12, which is frozen in the v0.5 manifest and is not edited)

## 13. Mechanism plan: written time
- **What is wrong:** `MECHANISM_PLAN.md` says it was written at "~23:30 UTC+4".
- **Correct time:** the SHA-256 was stored at 30 Oct 2026, 18:55 UTC (22:55 UTC+4), per the timestamp in `MECHANISM_PLAN.sha256`. The text was not edited after hashing.
- **Effect:** none. File times (UTC):
  - plan hashed at 18:55:53;
  - `src/mechanism.py` saved at 18:56:48;
  - the M3 validation, which uses no vbroad, written at 18:57:41;
  - the first run of the pre-registered tests, written at 18:58:25. The only later run is the identical re-run in deviation 15.

## 14. Mechanism tests: what was added after seeing the results
- E1–E3 in `RESULTS_MECHANISM.md` were added after the pre-registered results were known. They are labelled exploratory. They do not change any pass/fail verdict.
- E3 (the RV-centroid dilution forward model) was run **once**, with the resolution scale fixed in advance at 26 km/s, the RVS FWHM at R = 11 500. Nothing was tuned.

## 15. Small-sample guard added to M3 after the DR3 run
- **What happened:** a smoke test of the DR4 path showed a crash. On a fake 3000-row "DR4" table (DR3 rows with changed ids), M3 crashed because the small-separation bin had no bright companions. Every bootstrap ratio was then infinite.
- **Fix:** `mechanism.m3` and `dr4_mechanism.h13` now return "no verdict" (NaN, pass = false) when fewer than half of the bootstrap ratios are finite.
- **Effect on DR3:** none. `mechanism.py` was re-run after the fix, and `results/mechanism.json` is byte-for-byte identical in content.

## 16. Two files frozen in the v0.4 manifest were later changed in place
- **What happened:** `FREEZE_MANIFEST.sha256` (OSF N5H4B) lists `src/rvs_predict.py` (a0405a88…) and `DR3_STUDY_DEVIATIONS.md` (5708c1e6…). Both now have different hashes.
- **rvs_predict.py:** the change is amendment v0.5 A6, which is registered (OSF TBJGY). The v0.4 version survives byte-for-byte in `repo_push/src/rvs_predict.py`.
- **DR3_STUDY_DEVIATIONS.md:** deviations 5–12 were appended to the frozen file instead of a new file. The v0.4 bytes (5708c1e6…) were **not found** in this workspace (zip and git copies differ). They may exist in the user's GitHub history or Downloads.
- **Rule from now on:** frozen files are never appended to; new logs go into new files (this file).
- **Found:** audit of 31 Oct 2026 (`sha256sum -c FREEZE_MANIFEST.sha256`). `FREEZE_MANIFEST_v0.5.sha256` verifies completely.

## 17. Units bug F6 (K_sum with the period in years) and a corrected re-analysis
- **Found:** 31 Oct 2026, during the audit, by tracing every caller of `K_sum_kms` (it expects days).
- **Effect:** large. See the ERRATUM in `RESULTS_DARK_COMPANION.md`. Registered H10 and V1–V3 results are kept as registered. Corrected numbers are reported next to them in `results/erratum_k_units.json`.
- **Premise affected:** the premise sentence in `MECHANISM_PLAN.md` §1 ("Our first physical model predicted broadening in the wrong direction … adding the SB1 selection fixed it") is false. The mechanism tests themselves do not use the buggy function. `mechanism.py` computes K from a1 sin i with P in years and its own correct constant, so M1–M4 are unaffected.
- **Timing:** found and corrected before any DR4 data exist. No decision about the fix depended on which direction it moved a result.

## 18. Pre-DR4 obligations of the H11 plan done on 31 Oct 2026
- **Second prediction set (v0.4 A1):** `results/dr3_candidates_scored_A1.csv`, SHA-256 d8c9b2e27bef04e6…, C* = 0.3. Deterministic (re-run gives the same hash).
- **CMD-only probability for the H11a Brier baseline:** `results/dr3_candidates_B2prob.csv`, SHA-256 d86774c7…, v0.6 A20.
  - A first attempt used a constant-π EM. It saturated at π = 0.9999, which makes B2 a near-constant "all impostors" predictor, so the primary was changed to GAIA-FP's own frozen prior with the pure-CMD likelihood. The EM version is kept as a sensitivity analysis.
  - This choice was made on DR3 predictions only; no outcome data exist.
- **Control group:** code ready (`src/h11_control.py`). It needs a DR3 download of Orbital + AstroSpectroSB1 solutions. That download has not been done yet and needs the user's permission.

## 19. Mechanism code corrected after the independent audit (31 Oct 2026)
- **Phase sampling:** `mechanism.py` now uses 4096 phase samples for pavg and smax (audit A1-F6). The 64 samples "as in vbroad_v2.py" were up to ×2.7 off at e = 0.95.
- **Bootstrap replicates:** M3 and H13 no longer drop +∞ bootstrap replicates (audit A2-F17).
- **Re-run, DR3 development:**

  | Test | Before | After |
  |---|---|---|
  | M1 | 0.218 [0.199, 0.237] | unchanged |
  | M2a | | unchanged within 0.001 |
  | M2b | | unchanged within 0.001 |
  | M4 | | unchanged within 0.001 |
  | M3 | D upper 6.26 | D upper 6.62, still FAIL |
  | H13 | 2.66 [1.87, 3.90] | 2.59 [1.82, 3.80] |
- The plan text says "as in vbroad_v2.py". This is a precision fix, not a different quantity.

## 20. Sealed label file: what was read during the audit
- Only the field names, the label vocabulary and aggregate counts were read, to write the runner's assertion (39 impostor + 26 substellar of 76).
- No per-object label and no Gaia value of any sealed object was looked at.

## 21. 1 Nov 2026 — H11 DR3 control set independently regenerated from the included DR3 NSS source
- The H11 control builder was rerun against `realdata/dr3_nss_two_body_orbit_raw.csv` and the frozen candidate and field inputs.
- The eligible control pool contained 31,349 systems; 2,102 one-to-one controls were selected.
- The regenerated `results/h11_controls.csv` was byte-identical to the archived file: SHA-256 `cd56e49a6d1ae0baccfd7b334780bee29c351fff3b0751fa803d246570d3b42d`.
- This reproduces the DR3 control-construction artifact. It supersedes the earlier “download not yet done” status note in section 18. It is **not** an H11 DR4 outcome or an independent astrophysical validation of the classifier.


## 2026-11-03 — A6 light-ratio threshold reconciliation (pre-DR4)

A code audit found that `src/rvs_predict.py` implemented the registered A6 threshold as the secondary-to-primary flux ratio `ell = q**n >= 0.2`, while `src/rvs_v32.py` had used the secondary fraction of total light `beta = ell/(1+ell) >= 0.2`. These are not equivalent: the latter is stricter (`ell >= 0.25`). The registered wording is “light ratio >= 0.2”, and the legacy registered implementation uses `q**n`; therefore v3.2 has been corrected to use `ell = q**n` as well. The `beta` value remains the blend fraction in the registered `f(1-f)` variance term and is not used for A6 selection. A regression test explicitly checks the disagreement interval `0.2 <= ell < 0.25`. This is a pre-DR4 implementation reconciliation, not a result-driven change; no DR4 data were accessed.

## 22. Merge of the parallel work sessions (6 Nov 2026)
- **Why there were parallel copies:** between 1 and 3 Nov, while this session was rate-limited, the work was continued in other sessions on copies of the 31 Oct package.
- **What was merged:** the latest of those copies (`GAIA-FP_REVISED_DATA_PIPELINES_2026-11-03`) was merged into this tree. Each change was reviewed (`diff`) before it was taken.
- **Frozen file restored:** the other copy had again appended to the frozen `DR3_STUDY_DEVIATIONS.md` (as a duplicate "13" and a "final completion" note). That file is restored byte-for-byte (v0.5 manifest: all 56 OK). The appended content is recorded here instead:
  - **1 Nov:** `tools/fetch_realdata.py` was corrected to request the full LAMOST-MRS coverage catalogue (`COUNT(*)`, `AVG(RAJ2000)`, `AVG(DEJ2000)`, grouped by Gaia id) rather than 300-id chunks. It is not run against VizieR; no new `lamost_cov.csv` is claimed.
  - **3 Nov:** evidence-only lineage tables, APOGEE allVisit / exact-cadence injection scripts and a LAMOST DR9 per-spectrum RV pipeline were added (`results/final_completion/`, `FINAL_COMPLETION_REPORT.md`).
- **A28 (A6 uses the light RATIO ℓ = qⁿ, not β = ℓ/(1+ℓ)):** the error was found independently in both copies; the merged code uses `rvs_v32.sb1_keep_mask`.
- **Pre-erratum S1 retired:** the column is renamed `S1_pre_erratum_DO_NOT_USE` in mechanism output.
- **H11 control group:** pool 31 349, 2102 of 2102 matched, SHA-256 cd56e49a… It was built from `realdata/dr3_nss_two_body_orbit_raw.csv` (71 759 rows). It was **independently re-run in this session with `src/h11_control.py` and reproduced bit-for-bit**.
- **Tests after the merge:** 127 passed.

## 23. 6 Nov 2026: parallel scoring, H15 runner, and a bug caught by the dry run
- **Parallel scoring:** `dr4_run.score(workers=…)` computes the RVS term in parallel. A test shows the parallel and serial catalogues are identical. On 2 cores the scoring step went from 642 s to 293 s; on 8 cores it is expected to take ~15–20 min at DR4 scale.
- **H15 runner:** `src/h15_purity.py`, descriptive (A29), with 2 tests.
- **Bug caught by the dry run:** the A27 wrapper (`dr4_mechanism.rho_labels_chunked`) called the monkeypatched `DC.rho_labels`, which recursed forever (RecursionError). Fixed by passing the original function explicitly.
- **Full dry run after the fix:** COMPLETED, 12/12 steps OK, 318 s. Tests: 130 passed.

## 24. 6 Nov 2026: external APOGEE data, H16 pre-registered, H4 adapter
- **APOGEE DR17 multi-visit catalogue downloaded** (provenance in `realdata/PROVENANCE.md`). Exploratory analyses: `RESULTS_APOGEE.md` and `RESULTS_FP_CHARACTERIZATION.md`.
- **H16 written into v0.6 (A30) after seeing the DR3 development value** (AUC 0.73, 8 positives). H16 is evaluated only on DR4 candidates, which do not exist yet, so the DR3 value is development data, as for H12–H14.
- **H4 epoch-astrometry adapter:** `src/dr4_epoch_astrometry.py`, tested by a round trip on the Gaia-4 pre-release data.
- **Tests:** 132 passed.

## 25. 7 Nov 2026: ESA's draft DR4 data model read; four breaking differences handled
- **Source:** `gaia-dr4-prerelease-draft-data-model_2026-06-26.zip`, downloaded from ESA anonftp in the user's built-in browser. Copy in `docs/dr4_datamodel/`.
- **Differences found and handled** (in `src/dr4_release_map.py`, with 4 tests):
  1. `solution_type` replaces `nss_solution_type`.
  2. There are **no `c_thiele_innes`/`h_thiele_innes`**. a1 sin i is rebuilt from `semi_amplitude_primary`, and is exact against DR3.
  3. `dr3_neighbourhood.angular_distance` is in **mas**, not arcsec.
  4. Epoch RVS time is `obs_time_rv` (days since 2010) plus `obs_time_bary_corr` (ns), and only valid vbroad transits are used.
- **Draft status:** the data model is a draft. The schema guard still stops on any further change.
- **Also fixed (7 Nov):** the solution-type count query in `dr4_fetch.py` still used `nss_solution_type` on DR4; it now uses `solution_type`.

## 26. 7 Nov 2026: power analysis and weighted Holm (A31)
- **Power simulation** (`audit/power_h1.py`): with 39 impostors and 26 substellar, a true AUC of 0.65 / 0.70 / 0.73 / 0.80 is detected with probability 0.28 / 0.58 / 0.75 / 0.97 at α/5 = 0.005, and 0.56 / 0.82 / 0.90 / 1.00 at α = 0.025. If a quarter of the labelled objects have no DR4 orbit, these fall by about 0.1.
- **Decision:** A18 changed to weighted Holm (A31) before registration of v0.6 and before any DR4 data exist. Equal-weight Holm stays as a sensitivity analysis. No sealed label or DR4 value was used.

## 27. 7 Nov 2026: three secondary hypotheses added (H17–H19, A32–A34)
- **Why:** to widen the question from "planet impostors" to "impostors among all invisible Gaia companions" (black-hole and neutron-star searches; the brown-dwarf desert), and to add a second independent data channel (Gaia epoch photometry).
- **Status:** all secondary, outside the weighted-Holm family, so they do not reduce the power of H1.
- **What was seen first:** H18 and H19 were written after computing their DR3 development values (0.96 and 0.94). They are evaluated only on NEW DR4 systems, so, as for H12–H16, the DR3 values are development data. H17 has no development value.
- **Gaia BH2 check:** run before writing H18; ρ = 0.92, not flagged luminous. Gaia BH1 is not in our DR3 AstroSpectroSB1 table.
- **Code:** `src/new_hypotheses.py` (5 tests), `dr4_release_map.epoch_photometry` (1 test), `dr4_fetch.epoch_photometry` (untested against the live archive), and H18/H19 run inside `dr4_mechanism.py`.

## 28. 8 Nov 2026: development numbers checked and firmed up (no DR4 data; no sealed label)
- **H18/H19 with n_mc = 5000 labels** (`audit/h18_h19_dev_mc5000.py`): H18 80/81 = 0.99 [0.93, 1.00] (was 80/83 with the stored n_mc = 200 labels; 2 labels changed); H19 unchanged, 33/35. A33 text updated.
- **H1 power computed directly at α = 0.01** (`audit/power_h1_weighted.py`): 0.82 for AUC 0.73 with 39 + 26 objects; 0.69 if only 30 + 20 remain; 0.39 for AUC 0.65. This replaces the interpolated "≈ 0.85".
- **Mass under-estimate for the candidates themselves** (`audit/candidate_mass_bias.py`, exploratory): 95 of the 2102 candidates also have a combined orbit; 42 are impostors by the 9 Oct label rules. Their dynamical companion mass is a median **4.0× [3.5, 5.5]** the catalogue (dark-assumed) mass: 252 vs 64 MJ. The earlier "2.4×" figure refers to a different sample (1186 luminous combined-orbit systems, `RESULTS_FP_CHARACTERIZATION.md`) and must not be attributed to the candidates. Note: the label rule itself uses m2_dyn > 80 MJ, so "all impostors are above 80 MJ" is partly by definition; the ratio is not.
- **Wording fix:** Gaia DR3 has ~1.8 billion sources (not "over 2 billion").

## 29. 8 Nov 2026: DR4-day chain completed after an external review (no DR4 data; no sealed label)
A second, external AI review (7 Nov) found real gaps. Each was checked against the code and fixed:
- **`dr4_day.py` ran only the dry run.** It now has `prepare` and `run`, and the dry run calls the same `run_chain` as the DR4 run. Dry run: COMPLETED, 13 steps, 352 s.
- **The DR3→DR4 id map was never downloaded.** Without it the sealed labels could not be matched in DR4. `dr4_fetch.py` now downloads `dr3_neighbourhood` for the DR3 candidates, the sealed ids (ids only), the DR3 AstroSpectroSB1 sources and the H11 controls. It also downloads the H11 orbits, the D3 combined orbits and the D2 field vbroad sample.
- **The RVS query** joined the whole NSS table when there were more than 2000 candidates. It now queries the candidate ids in chunks of ≤ 2000.
- **The DR3-mode field query used the DR4 table name** (`dr4_pipeline.SCHEMA`), so the 24 Nov DR3 test would have queried DR4. Fixed: every query is built for the chosen release.
- **DR4 data model:** `non_single_star` is in `all_source_flags`, not in `gaia_source`. The field queries now join it. The criteria are unchanged; only a name is mapped.
- **a1 sin i error from `semi_amplitude_primary`:** the eccentricity term e·σe/(1−e²) has been added.
- **H1 power with the registered bootstrap test itself** (`audit/power_h1_bootstrap.py`, 400 simulations per cell, α = 0.01):

  | Sample | AUC 0.5 (false positive) | 0.65 | 0.70 | 0.73 | 0.80 |
  |---|---|---|---|---|---|
  | 39 + 26 | 0.015 | 0.41 | 0.67 | **0.83** | 0.99 |
  | 30 + 20 | 0.010 | 0.33 | 0.58 | 0.71 | 0.93 |

  - These agree with the Mann–Whitney approximation (0.82).
  - The bootstrap p-value is close to nominal (0.015 ± 0.006 at a nominal 0.01). This answers audit A2's open calibration item.
- **Wording:** README and summaries now say that the 91% is a model classification (not a confirmed prevalence), that the primary score uses the empirical vbroad term (the physical S1 is weaker than CMD + empirical vbroad, −0.019), and that the APOGEE AUC is positive-vs-unlabelled. Prior art (Bailer-Jones & Kreidberg 2026; Hadad et al.; Marcussen et al. 2026) was already in `NOVELTY_AND_PRIOR_ART.md` and is now also in the README.
- **One point of the review is not right:** mean prior = mean posterior (0.940) is the fixed-point property of EM, not evidence that the prior dominates. The conclusion drawn from it (91% is a model estimate) is right.
- **Still open:** the 1927 vs 1926 sample count (H10 vs mechanism); the live-archive test (24 Nov); a direct comparison with Bailer-Jones & Kreidberg masses (their VizieR table J/A+A/708/A249).
- **Tests:** 146 passed.

## 30. 8 Nov 2026: comparison with Bailer-Jones & Kreidberg 2026 (exploratory; plan hashed before the run)
- **Plan:** `BJK_COMPARISON_PLAN.md`, SHA-256 b55a1e7e…, stored 12:01 UTC before the run. The catalogue was downloaded the same day from MPIA (`realdata/external/bjk2026_orbital300.csv`).
- **Result:** `RESULTS_BJK_COMPARISON.md`.
  - Survey SB2 labels: GAIA-FP better, ΔAUC +0.22 [+0.08, +0.39].
  - APOGEE labels: no detectable difference (7 positives).
  - BJK flags only 11% of GAIA-FP's likely impostors as stellar.
- **What is NOT changed:** the 95-object combined-orbit check and the DR3 × SB2 test (P2) are frozen development results. They are not re-tuned, because re-fitting the model to win them after seeing them would be post hoc.

## 31. 8 Nov 2026: attempt to enlarge the RV label set with Gaia DR3 RV amplitudes (plan hashed first)
- **Plan:** `GAIA_RV_LABEL_PLAN.md`, SHA-256 5f50bac9…
- **Result:** 2 positives among 487, so the test is NOT CONDUCTED (minimum 5). Reported in `RESULTS_GAIA_RV_LABELS.md`. The rule was not loosened after seeing the count.

## 32. 8 Nov 2026: final pre-registration review
- **Found:** DR4 publishes primary masses in `nss_masses` (the DR4 equivalent of DR3 `binary_masses`, which the frozen DR3 predictions used). `dr4_fetch.py` did not download it, so DR4 scoring would silently have used the photometric relation for every star.
- **Fixed:** the masses are now fetched for the candidates and combined orbits. `prepare` merges them with a per-row photometric fallback and logs the count. Recorded as A36.
- **Added:** H20 (A35, secondary), a head-to-head on the sealed labels against Gaia DR4's own flux ratio and substellar probabilities and against Bailer-Jones & Kreidberg 2026. The comparator scores are hashed before unblinding.
- **Dry run:** COMPLETED, 14 steps. The fake-archive test covers the masses and the fallback.
