# Pre-registration amendment v0.6: mechanism, label blindness, multiplicity and DR4-day rules (registered on OSF before Gaia DR4)

Three revisions sit on top of the first draft of 30 Oct 2026. The audit of code and registration (`AUDIT_REPORT.md`) forced the first one, on 31 Oct. On 7 Nov came A31 (weighted Holm), A32–A34 (the secondary hypotheses H17–H19) and the mapping to the DR4 data model. The last round, on 8 Nov, followed the completion of the DR4-day download and run chain: A35 (H20), A36 (m1 on DR4), A37 (operational definitions), A38 (sealed labels v2r) and deviations 28–32. We froze the text for OSF registration that same day, 8 Nov 2026; the matching code state is the GitHub commit named in `OSF_REGISTRATION_v0.6.md`.

Gaia DR4 arrives on 2 Dec 2026. All of the dates above precede it. `DEVIATIONS_v0.6.md` holds the full change log.

The amendment builds on [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B) and [10.17605/OSF.IO/TBJGY](https://doi.org/10.17605/OSF.IO/TBJGY). No DR4 data exist yet.

Where does the content come from? Two places only: Gaia DR3, our development data, and a close reading of our own code. The key documents are `MECHANISM_PLAN.md` (SHA-256 bc327170…, hashed before the run), `RESULTS_MECHANISM.md` and `AUDIT_REPORT.md`.

## Why we are amending

**The mechanism.** Line broadening in DR3 follows each system's blend term, and three tests pin that down. M1 returns a partial ρ_s of +0.22 [+0.20, +0.24]. M2b says the companion has to contribute light. M2a rules out the obvious alternative, since the primary's own orbital motion leaves the lines unbroadened. All of this is development data; DR4 provides the confirmatory test (H12).

**Label blindness.** M3 was supposed to reveal an SB2-resolution selection signature, which we had specified in advance. It didn't. What the exploration suggests instead is simpler and less flattering to the labels: unresolved lines drag the measured RV toward the light centroid, and ρ drifts toward 1. We call this label blindness.

**What the audit found.** The worst finding was a units bug. That bug produced the "wrong-direction" result we had cited as the reason for v0.5 A6 (see A23), so a stated rationale in a registered amendment rested on an error. The audit turned up four further problems. Some registered hypotheses had no DR4 runner. Two registered amendments, v0.4 A1 and v0.5 A7, never made it into the day-1 pipeline. H11a lacked a defined Brier baseline. And we had no rule at all for multiple comparisons.

This amendment repairs every one of these before DR4 data exist. We did not pick any change because it would help a result we expect. The audit ran on the opposite principle: if something is wrong, fix it, even when the fix makes our expected result look worse.

## Changes

### A10. H12, the mechanism (confirmatory) — hypothesis
M1, M2a and M2b of `MECHANISM_PLAN.md` get rerun on systems new in DR4, with the same code (`src/mechanism.py`) and the same pass rules. H12 holds only if all three pass (intersection–union). P0 is reported alongside.

### A11. H13, label blindness (secondary) — hypothesis
Only the trend is on trial here. The ratio is f(β̂ ≥ 0.2 \| K_sum·smax ≥ 50 km/s) / f(β̂ ≥ 0.2 \| K_sum·smax < 30 km/s), and H13 passes if its 95% lower bound exceeds 1. DR3 gave 2.59 [1.82, 3.80] after the phase-sampling fix, 2.66 before it. The level is a different story, and we make no claim about it. On DR3 the dilution model overshoots the bright-companion fraction by a factor of 7–10. We report that failure; we don't get to test it a second time.

### A12. H14, the amplitude (secondary) — hypothesis
ĉ is the median of (vbroad² − field median²)/b over b ≥ 25 (km/s)². If its 95% CI overlaps [1.4, 2.3], H14 "reproduces DR3", where the value was 1.79 [1.66, 2.05]. The theoretical c = 4 counts as rejected if the upper bound falls below 4. Why theory and data differ by a factor of 2, we can't say, and we say so.

### A13. M3 — criterion
M3 (depletion by SB2 resolution) leaves the confirmatory set. It is now secondary.

### A14. A power rule for H12–H14 — criterion
No test without data. H12–H14 run only if DR4 delivers at least 668 new systems with line broadening; otherwise they are NOT CONDUCTED (insufficient n).

### A15. The DR4 sample for H12–H14 — data
Start with DR4 combined astrometric + single-lined solutions, ϖ/σ > 10, under the H10 cuts. Then strip out (i) every source whose DR3 counterpart (official DR3–DR4 cross-match, nearest within 1″) sits in the DR3 AstroSpectroSB1 table, and (ii) every sealed id. The exclusion runs through the cross-match, not through matching source_ids, because ids can change between releases. vbroad must rest on at least 5 transits, and the field calibration uses a DR4 query identical to D2b.

### A16. A limitation — reporting
At small RV separation, label blindness can hide luminous blends among systems labelled "dark". The effect drags M1 toward zero.

### A17. The day-1 runner applies registered rules the frozen code skips — implementation
Several registered rules never made it into the frozen `dr4_pipeline.score`. The wrapper `src/dr4_run.py` applies them and leaves the frozen files alone: v0.4 A1 (label-free prior selection), v0.5 A7 (score_emp = cmd_z + rvs_z), loading the RVS epochs (the frozen `score` CLI passes `rvs=None`), and fetching the Thiele–Innes C and H for H8. The frozen functions run unchanged.

### A18. Multiplicity — criterion
See the multiplicity section below.

### A19. Status words, and when a test applies — criterion
Three outcomes exist: PASS, FAIL, or NOT CONDUCTED with a reason (DATA_ABSENT, SCHEMA_MISMATCH, BELOW_MIN_N, CODE_ERROR). NOT CONDUCTED never gets reported as FAIL or as "not supported". Minimum sizes: 10 objects per class for AUC-type tests; for H2, 10 impostors and 10 substellar objects with 15 or more RVS epochs; for H11a, 30 labelled objects with at least 5 per class; for H12–H14, the rule in A14.

### A20. Clarifying H11 — clarification
The registered text leaves room for interpretation, so we close it now, before DR4.

(a) B2's Brier score uses `P_B2` = expit(pure-CMD LR + logit(GAIA-FP's frozen prior)), frozen in `results/dr3_candidates_B2prob.csv` (SHA-256 d86774c7…). The constant-π EM variant is a sensitivity analysis only; on DR3 it saturates at π = 0.9999.
(b) Despite its name, the `llr_cmd` column in the prediction file isn't CMD-only. On DR3 it equals log_lr. It is not a baseline.
(c) An O1 period match means \|P4/P3 − k\| ≤ 0.3k for k ∈ {½, 1, 2}.
(d) O2/D mass bounds come from a Monte Carlo over the Thiele–Innes and parallax errors (n = 400, seed 0).
(e) H11b pools high-confidence errors across classes; each class is also shown separately.
(f) Sources with no DR4 counterpart within 1″ are reported, then dropped.
(g) The second prediction set (v0.4 A1) is frozen as of now: `results/dr3_candidates_scored_A1.csv`, SHA-256 d8c9b2e2…, C* = 0.3.
(h) `src/h11_control.py` extracts the control group from DR3 before DR4, by the registered rule, and its hash goes into the v0.6 manifest.

### A21. Fallback for the H8 primary mass — clarification
No m1 with bounds in DR4? Then m1 comes from the photometric relation, with a 10% one-sigma error. `src/dr4_dynamical.py` reproduces the DR3 labels exactly (regression test).

### A22. A schema guard — implementation
Before doing anything, the day-1 runner compares every required table, column, unit and dtype with `src/dr4_schema.py`. One mismatch and it stops. A mapping to new DR4 names can be added, but only as a logged deviation, and only before any score is computed.

### A23. An erratum to v0.5, and the fate of A6 — erratum / criterion
v0.5 claimed our physical line-width model "ranked systems in the wrong direction because it ignored Gaia's single-/double-lined selection". It didn't. The audit traced the real cause to a units bug (finding F6): a period in years went into a function that expects days, inflating K by a factor of 7.15. Correct K, and the model ranks properly even without SB1 truncation (AUC 0.736). M3 didn't back an SB2-resolution selection either. On the already-used TEST half, an exploratory comparison shows the truncation doing nothing at c = 1 (−0.007 [−0.018, +0.005]) and helping at c = 4 (+0.022 [+0.006, +0.039]).

A6 stays as registered. We made that call before DR4, without DR4 data. The error sat in our stated reason, not in the rule, and the evidence on the rule cuts both ways. Every hypothesis that uses P_impostor also gets the A6-off posterior (`P_impostor_noA6`) as a sensitivity analysis. A7 is unaffected: V3 still fails after the fix (−0.025 [−0.039, −0.009]).

### A24. Fallbacks, fixed now (`DR4_READINESS.md` §4) — criterion
(a) Without `dr3_neighbourhood`, we match by position: propagate DR3 positions to J2017.5 with DR3 proper motions and take the nearest source within 1″.
(b) Without per-transit widths, H2 is NOT CONDUCTED and P_impostor uses a neutral RVS term.
(c) Without combined solutions, H8, A5 and H12–H14 are NOT CONDUCTED.

### A25. The primary DR4 score is "v3.2" — method (error correction)
v3.2 is v3.1 as registered, plus the audit's error corrections, every one decided before DR4 (`src/dr4_run.py`, `src/rvs_v32.py`). The registered v3.1 output (`P_impostor_v31`) is reported next to it for every hypothesis. Why demote v3.1? Its RVS term flips 447 of 2102 verdicts when you change nothing but the random seed. The corrections:

1. the RVS likelihood is monotone in z (KDE bandwidth = null SD = 1, plus a monotone envelope);
2. 8000 H_t draws, seeded per candidate from source_id, so results are reproducible and order-independent;
3. (q, n) drawn from p(q, n \| a0, ΔM_G), the posterior the a0/CMD term already uses;
4. each candidate's own epoch times and width errors, as prereg §6.3 requires;
5. σ_a0 = a0/significance (Gaia's full covariance) in place of the rms of the four Thiele–Innes errors;
6. population-prior covariates log P, e and log m_fit, without G and ln d, which rebuild M_G and would count the CMD evidence twice;
7. colours outside the CMD ridge range excluded and counted, not clamped;
8. invalid or uninformative RVS input returns "no information" with a reason, never a silent number.

A1 (prior selection), A6 and A7 carry over unchanged.

### A26. Sensitivity to companion mass — reporting
The frozen candidate rule (first-order m2 < 80 MJ) stays. As a sensitivity check, we report how many candidates have an exact mass above 80 MJ (27% on DR3) and recompute H1 without them.

### A27. Monte Carlo sizes — method / reporting
ρ labels for H12–H14 use n_mc = 5000. DR3 used 200, which lets the seed change about 20% of labels, though never between luminous and dark. H8 keeps the registered 400 (A3), with the spread over 5 seeds reported. The 400-null injection threshold supports no false-alarm-probability claim; its real FAP is 0.4–1.8%.

### A28. Reconciling the A6 implementation (pre-DR4) — implementation clarification
The registered A6 light-ratio threshold is the secondary-to-primary flux ratio, ℓ = L2/L1 = q^n ≥ 0.2, combined with K_sum(1+e) ≥ 30 km/s. It is not the total-light fraction β = ℓ/(1+ℓ). The DR4 v3.2 code now follows the registered ℓ, and a regression test covers 0.2 ≤ ℓ < 0.25, where the two definitions disagree. No DR4 data were inspected.

### A29. H15, the purity of Gaia's substellar yield (secondary, descriptive; written before DR4) — hypothesis (descriptive)
(a) The impostor fraction among all DR4 substellar candidates is estimated as the mean P_impostor (v3.2), with a bootstrap 95% CI. Registered labels play no part.
(b) The companion-mass histogram (13–80 MJ, 6 log bins) appears twice, raw and weighted by 1 − P_impostor. Where weighted and raw counts differ by more than their bootstrap CI, the bin is flagged "contamination-dominated".
(c) H15 describes; it doesn't decide. No pass, no fail, no role in any headline claim. Its calibration rides on H11a and H3, and if H11a fails, H15 appears only with that warning attached.

### A30. H16, a test with an independent instrument (secondary; written before DR4) — hypothesis (secondary)
(a) Data: APOGEE DR17 multi-visit RVs, already downloaded and hashed (`realdata/external/apogee_dr17_multivisit.csv`, SHA-256 a942246a…). GAIA-FP was never built or tuned on them.
(b) Sample: DR4 candidates matched to APOGEE through the DR3 cross-match.
(c) Positive: RV scatter > K₈₀(1+e) + 1 km/s, impossible for a companion of 80 MJ or less. Negative: every other candidate with at least 2 visits. Calling them negative doesn't make them substellar, and we don't claim it does.
(d) Statistic: AUC of P_impostor (v3.2), stratified bootstrap. Pass if the lower 95% bound exceeds 0.5. NOT CONDUCTED below 10 positives or 10 negatives.
(e) Development result (exploratory, on the DR3 predictions frozen 9 Oct): AUC 0.73 [0.58, 0.88], 8 positives among 61 candidates (`RESULTS_APOGEE.md`). Code: `src/apogee_validation.h16`.

### A31. Weighted Holm — criterion
Holm's weighted procedure (Holm 1979) replaces equal-weight Holm in A18, decided before any DR4 data exist. The reason is power. `audit/power_h1.py` (binormal scores, 3000 runs) shows that with 39 + 26 labelled objects and a true AUC of 0.73, our DR3/APOGEE development value, H1 is detected with probability 0.90 at α = 0.025 but only 0.75 at the equal-weight Holm floor, α/5. H1 is the headline test and rests on independent literature labels, so it carries weight 0.4. A5 and H12, with large DR4 samples, take 0.2 each; H2 and H11a, 0.1 each. Weights of NOT CONDUCTED hypotheses are redistributed, and a rejected hypothesis hands its weight on. Family-wise error stays at or below 0.025. Code: `dr4_evaluate.weighted_holm`, with tests.

### A32. H17 (secondary): Gaia epoch photometry, an independent channel — criterion
Every DR4 candidate with at least 20 accepted G transits (DataLink EPOCH_PHOTOMETRY) gets two fits: a weighted 2-harmonic Fourier model at the known orbital period, and a constant. An F-test compares them. Fluxes are normalised by the median, and points more than 5 MAD out are dropped. Flag: p < 10⁻³. The prediction is that flagged candidates carry a higher frozen DR4 P_impostor, i.e. AUC > 0.5, judged by whether the 2.5th percentile of the stratified bootstrap (B = 2000, seed 7) clears 0.5. That makes it a one-sided 97.5% bound, as coded in `new_hypotheses.h17` (wording corrected; see A37). Minimum: 5 flagged, 10 unflagged. Sensitivity: rerun the AUC without periods within 10% of 1 yr or of 63 d, the scanning-law aliases. Code: `new_hypotheses.h17`, adapter `dr4_release_map.epoch_photometry`. There is no DR3 development value, since our data hold no epoch photometry for these stars.

### A33. H18 (secondary): compact-object impostors — criterion
Take the new DR4 combined orbits (same exclusions as H12) whose dynamical companion mass is m₂ ≥ 1.4 M☉. Among those with a resolved ρ label (A27, n_mc = 5000), we predict a luminous fraction above 0.5, by a one-sided 97.5% Clopper–Pearson bound. At least 10 must be resolved. DR3 development value: 80/81 = 0.99 [0.93, 1.00] with n_mc = 5000 labels (`results/new_hypotheses_dev_dr3_mc5000.json`); 80/83 with the stored n_mc = 200 labels. As a sanity check, Gaia BH2 (DR3 5870569352746779008), a confirmed black hole, gets ρ = 0.92 and is correctly not called luminous.

### A34. H19 (secondary): contamination of the brown-dwarf desert — criterion
Now take the new DR4 combined orbits whose astrometry alone, assuming a dark companion, implies 13–80 MJ. Prediction: a luminous fraction above 0.5 among the resolved ones, by the same test as H18. We also report the median dynamical mass of the luminous systems. DR3 development value: 33/35 = 0.94 [0.81, 0.99], median true mass 273 MJ. One caveat travels with every one of these numbers: combined solutions require a detectable RV orbit, and that tilts the sample toward heavy companions.

### A35. H20 (secondary): head-to-head with published methods on the sealed labels — criterion
Three comparators, fixed and hashed at DR4 run time before unblinding (`comparators.csv`): Gaia DR4's own `nss_masses.fluxratio` (higher means more likely an impostor); DR4 `exoplanet_candidate_hrd_proba + lowmass_candidate_hrd_proba` (higher means more likely substellar); and Bailer-Jones & Kreidberg 2026 m2, via the DR3 counterpart.

For each, on the H1 objects where it exists, we compute both AUCs and the paired stratified-bootstrap ΔAUC (GAIA-FP − comparator), B = 2000, seed 7. "Better" or "worse" requires a 95% CI that excludes 0, and at least 10 objects per class. DR3 development value, BJK only, survey-SB2 labels: ΔAUC +0.22 [+0.08, +0.39] (`RESULTS_BJK_COMPARISON.md`). Code: `dr4_evaluate.h20`.

### A36. Primary mass m1 on DR4 — criterion
m1 comes from DR4 `nss_masses`, the successor to the DR3 `binary_masses` table the frozen DR3 predictions drew on. If a source has several rows, the first `combination_method` alphabetically wins. If DR4 has no m1, the registered photometric relation (`dr4_pipeline.mass_from_MG`) steps in, and the number of fallbacks is logged (`prepare` info). The rule covers both the candidates and the H12 combined orbits.

### A37. Operational definitions — clarification
This describes the code as of commit `f6144c6`. It changes no rule and no code.

**(a) Weighted Holm (A18/A31).** The family F holds the confirmatory hypotheses with status CONDUCTED, a subset of {H1, A5, H12, H2, H11a}, weighted w = (0.4, 0.2, 0.2, 0.1, 0.1). A NOT_CONDUCTED hypothesis leaves F, and the remaining weights are renormalised.

Each p_i is the one-sided bootstrap p-value of its own test, p = (k + 1)/(B + 1), with k the number of replicates on the null side. That side is AUC ≤ 0.5 for H1; a difference ≤ 0 for A5 and H2; a Brier difference ≥ 0 for H11a. H12 uses intersection–union, p = max(p_M1, p_M2b, p_M2a).

Set R = F. Reject every H_i in R with p_i ≤ α·w_i / Σ_{j∈R} w_j, α = 0.025. Nothing rejected? Stop. Otherwise remove the rejected hypotheses from R and repeat. This is Holm's (1979) weighted step-down, and it holds the family-wise error rate at 0.025 under any dependence between tests.

A confirmatory hypothesis is PASS if and only if the procedure rejects it, FAIL otherwise. Per-hypothesis CIs are reported but don't decide confirmatory status. Equal-weight Holm runs as a sensitivity analysis. Calibration was checked by simulation for H1: a false-positive rate of 0.015 over 400 simulations, nominal 0.01 (deviation 29).

**(b) Why H18 and H19 are independent of their development data.** The DR3 development sample is every DR3 AstroSpectroSB1 orbit with ϖ/σϖ > 10 that passes the H10 cuts: colour within the main-sequence ridge range, dm > −2, finite positive m1, finite A, C, H and errors. That sample shaped H10, the mechanism tests and the ρ labels, and H18 and H19 were written after their DR3 values were seen (deviation 27). So those values are development data. They aren't evidence. The DR4 test uses new DR4 combined orbits only; any DR4 source whose DR3 counterpart (dr3_neighbourhood, ≤ 1″) is a DR3 AstroSpectroSB1 or sealed source is removed up front (A15). The test runs on systems we never touched during development.

**(c) H17.** Eligible: in the hashed DR4 catalogue, with an orbital period, and with at least 20 G transits of finite positive flux and `g_n_obs` > 0, still at least 20 after removing points more than 5 MAD from the median. Denominator: eligible sources with a finite F-test p. Sources lacking epoch photometry are excluded and counted. Flag: p < 10⁻³ for a 2-harmonic fit at the known period. Minimum: 5 flagged, 10 unflagged.

**(d) H18 and H19.** Sample: the H12 sample, after exclusion and the H10 cuts. H18 needs m₂,dyn ≥ 1.4 M☉, with m₂,dyn from a1 sin i, inclination and m1 (`mechanism.physics`). H19 needs a dark-assumed m₂, from a0, ϖ, P and m1, in [13, 80) M_J. Denominator: systems with a resolved ρ label, luminous or dark, n_mc = 5000. Unresolved systems are counted and reported but kept out of the denominator; non-finite masses are excluded and counted. Rule: one-sided 97.5% Clopper–Pearson lower bound above 0.5, with at least 10 resolved.

**(e) H20.** Sample: the H1 analysis set, sealed labels mapped to the DR4 catalogue through the nearest dr3_neighbourhood match, exactly as in H1. Per comparator, the objects with a finite value, at least 10 per class. The DPAC substellar probability is exoplanet plus low-mass probability, missing only if both are. Multiple `nss_masses` rows per source: first `combination_method` alphabetically. BJK m2 comes through the DR3 counterpart in the same id map. Rule: paired stratified bootstrap, B = 2000, seed 7; "better" or "worse" only if the 95% CI excludes 0. The comparator file is written and hashed before unblinding.

### A38. The lost label file and how we rebuilt it — criterion
Written 8 Nov 2026, before the rebuild and before DR4.

The sealed file `labels_v2.json` (SHA-256 d6b0aabb…) is gone. Its hash is all that survives. We rebuild it as `labels_v2r.json` under constraints tight enough to leave no choice about objects or labels:

1. **Same objects.** Exactly the 76 Gaia DR3 ids frozen on 9 Oct 2026 in `realdata/excluded_sealed_ids.csv`. Nothing added, nothing removed.
2. **Same sources and rules (PREREGISTRATION §5).** Labels only from the 11 listed papers, and only from ground-based spectroscopy, RV or imaging. Conflicting or low-confidence objects become unresolved and are excluded. Gaia-4 becomes excluded_inspected.
3. **Consistency checks, reported whatever they show.** (a) The 33 entries of the hash-verified v1 file (44f30e22…), ids resolved, must carry the same labels in v2r; any disagreement gets listed. (b) The v2r counts are compared with the registered v2 counts (39 impostors, 26 substellar, 10 unresolved, 1 excluded).
4. **Frozen before DR4.** The v2r SHA-256 is registered before DR4, and the DR4 runner checks it in place of the v2 hash.
5. **Labels only.** No Gaia DR3 or DR4 feature of these objects gets looked at during the rebuild, and no score is computed on them before DR4.

**Outcome (8 Nov 2026).** `labels_v2r` (SHA-256 `a8ccb9b6fd1b4bf97bd9669d8be866bb33bd83b3c630feb90933f9a05703d3aa`) replaces `labels_v2`, whose file was not kept. Same 76 objects, same sources and rules, identical label counts: 39 impostors, 26 substellar, 10 unresolved, 1 excluded_inspected. Rebuilt before DR4; no score computed on these objects. The checks came out clean. Additions were 21/18/5, with the same confidence split as the 9 Oct build log. The 26 v1 entries kept their v1 labels apart from the two changes the original rules demand (Gaia-4 → excluded_inspected; HD 68638 → unresolved by conflict). The DR4 runner checks the v2r hash.

## Multiplicity (A18)

Five hypotheses make up the confirmatory family. They face a weighted Holm step-down (A31) at a one-sided family-wise α of 0.025; one-sided because the registered tests are one-sided 95% bounds. Weights: H1 0.4, A5 0.2, H12 0.2, H2 0.1, H11a 0.1. Plain equal-weight Holm is reported as a sensitivity analysis. The nulls:

| Hypothesis | Null hypothesis |
|---|---|
| H1 | AUC ≤ 0.5 |
| H2 | Δ rejection ≤ 0 |
| A5 | ΔAUC(GAIA-FP − B2) ≤ 0 on the H8 labels |
| H11a | ΔBrier ≥ 0 |
| H12 | intersection–union of M1, M2b, M2a |

p-values are one-sided bootstrap values, p = (1 + number of replicates on the null side)/(B + 1), B = 2000, seed 7. AUC-type tests use a stratified bootstrap, the rest a paired one. For H12, p = max(p_M1, p_M2b, p_M2a).

A NOT CONDUCTED hypothesis drops out and m shrinks. Data availability alone decides this, before any outcome is computed.

Both verdicts get reported for each hypothesis: the registered one (unadjusted 95% bounds) and the Holm one. Headlines use Holm. Nothing else.

Secondary hypotheses are reported unadjusted and never headlined as confirmed: H3, H5, H6, H7, H8 (a) and (b), H11b, H13, H14, H16, H17, H18, H19, H20, M3, P0. H15 is descriptive, as are H4 (a pipeline check) and H11c. H9, H10, V1–V3 and M1–M4 already ran on DR3, for development only.

## Keeping the blind test blind

Suppose someone on the team sees DR4 data, pre-release or not, for a sealed object, an H11 candidate or control, or an H12 system, before the DR4 run. That object is out, and the exclusion is logged with its date. Published papers on an object leave its sealed label unchanged.

Nobody looks at a DR4 value until the hash of the scored catalogue is committed. Row counts and schema checks are the only exceptions.

## What doesn't change

H1–H11 keep their definitions and thresholds. v0.3–v0.5 stand, A7 included, so the empirical RVS score remains primary. The sealed labels and their hashes are untouched.

## Order of work on DR4 day (fixed)
1. `python dr4_day.py fetch`: downloads, the schema guard (A22), row counts and nothing more.
2. Drop DR3-matched and sealed ids for H12–H14; drop sealed ids for H11.
3. `dr4_day.py score`. The catalogue's SHA-256 is committed before anything else happens.
4. Then, in order: `h11_outcomes.py`, `dr4_dynamical.py`, `dr4_mechanism.py`, `dr4_evaluate.py` (unblinding and Holm), `survey_xmatch.py`.
5. Publish every output, whatever it says.
