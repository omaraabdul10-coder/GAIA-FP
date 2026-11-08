# Pre-registration amendment v0.6: mechanism, label blindness, multiplicity and DR4-day rules (DRAFT, for OSF before Gaia DR4)

**Written:** 30 Oct 2026. **Revised:**
- 31 Oct 2026, after the code and registration audit (`AUDIT_REPORT.md`);
- 7 Nov 2026: A31 weighted Holm; A32–A34 secondary H17–H19; DR4 data-model mapping;
- 8 Nov 2026: DR4-day download and run chain completed; A35 (H20), A36 (m1 on DR4), A37 (operational definitions); deviations 28–32.

All dates are before Gaia DR4 (2 Dec 2026). The full change log is in `DEVIATIONS_v0.6.md`.

It extends [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B) and [10.17605/OSF.IO/TBJGY](https://doi.org/10.17605/OSF.IO/TBJGY). No DR4 data exist yet.

Sources: everything below was learnt on Gaia DR3 (development data) or from reading our own code:
- `MECHANISM_PLAN.md` (SHA-256 bc327170…, hashed before the run);
- `RESULTS_MECHANISM.md`;
- `AUDIT_REPORT.md`.

## Why
1. **Mechanism.** On DR3, line broadening follows the per-system blend term:
   - M1 partial ρ_s = +0.22 [+0.20, +0.24];
   - M2b: light is needed;
   - M2a: the primary's own orbital motion does not broaden the lines.

   This is development data. The confirmatory test is DR4 (H12).
2. **Label blindness.** The pre-specified SB2-resolution selection signature failed (M3). Exploration points to **label blindness**: unresolved lines make the RV follow the light centroid, so ρ → 1.
3. **Audit findings.** The audit also found a units bug that had produced the "wrong-direction" result used as the reason for v0.5 A6 (see A23). It further found:
   - registered hypotheses with no DR4 runner;
   - two registered amendments (v0.4 A1, v0.5 A7) not wired into the day-1 pipeline;
   - an undefined Brier baseline in H11a;
   - no rule for multiple comparisons.

   This amendment fixes these **before** any DR4 data exist. **None of these changes is chosen to improve an expected result.** The audit rule is: a fix is made even if it makes the expected result worse.

## Changes
| # | Change | Kind |
|---|---|---|
| A10 | **H12, mechanism (confirmatory):** M1, M2a, M2b of `MECHANISM_PLAN.md` on DR4-new systems, same code (`src/mechanism.py`), same pass rules. Supported only if all three pass (intersection–union). P0 is reported. | hypothesis |
| A11 | **H13, label blindness (secondary).** **H13 tests the TREND only**: ratio = f(β̂ ≥ 0.2 \| K_sum·smax ≥ 50 km/s) / f(β̂ ≥ 0.2 \| K_sum·smax < 30 km/s); pass if the 95% lower bound > 1 (DR3: 2.59 [1.82, 3.80] after the phase-sampling fix; 2.66 before). **The LEVEL is not claimed.** On DR3 the dilution model over-predicts the bright-companion fraction 7–10×, and that failure is reported, not tested again. | hypothesis |
| A12 | **H14, amplitude (secondary).** ĉ = median (vbroad² − field median²)/b over b ≥ 25 (km/s)². "Reproduces DR3" if the 95% CI overlaps [1.4, 2.3] (DR3: 1.79 [1.66, 2.05]). The theory value c = 4 is reported as rejected if the upper bound < 4. The factor-2 gap to theory is stated as unexplained. | hypothesis |
| A13 | M3 (SB2-resolution depletion) is no longer confirmatory. It is reported as secondary. | criterion |
| A14 | **Power rule for H12–H14:** they are conducted only if DR4 gives n ≥ 668 new systems with line broadening. Otherwise the status is NOT CONDUCTED (insufficient n). | criterion |
| A15 | **DR4 sample for H12–H14:** DR4 combined astrometric + single-lined solutions with ϖ/σ > 10, the same cuts as H10, minus (i) every source whose **DR3 counterpart** (official DR3–DR4 cross-match, nearest within 1″) is in the DR3 AstroSpectroSB1 table, and (ii) every sealed id. Exclusion uses the cross-match, **not** equality of source_id: ids can change between releases. vbroad comes from ≥ 5 transits. Field calibration uses a DR4 query identical to D2b. | data |
| A16 | **Limitation:** label blindness can hide luminous blends among "dark" labels at small RV separation. This biases M1 toward zero. | reporting |
| A17 | **Day-1 runner implements already-registered rules that the frozen `dr4_pipeline.score` does not apply** (wrapper `src/dr4_run.py`; frozen files untouched): v0.4 A1 (label-free prior selection), v0.5 A7 (score_emp = cmd_z + rvs_z), RVS epoch loading (the frozen `score` CLI passes `rvs=None`), and fetching Thiele–Innes C, H for H8. The frozen functions are called unchanged. | implementation |
| A18 | **Multiplicity.** See the section below. | criterion |
| A19 | **Status vocabulary and applicability.** Every hypothesis ends as **PASS**, **FAIL**, or **NOT CONDUCTED: reason** (DATA_ABSENT, SCHEMA_MISMATCH, BELOW_MIN_N, CODE_ERROR). NOT CONDUCTED is never reported as FAIL or as "not supported". Minimum sizes: AUC-type tests need ≥ 10 objects per class; H2 needs ≥ 10 impostors and ≥ 10 substellar with ≥ 15 RVS epochs; H11a needs ≥ 30 labelled objects with ≥ 5 per class; H12–H14 follow A14. | criterion |
| A20 | **Clarifications of H11** (written before DR4; the registered text is ambiguous):<br>(a) B2's Brier score uses `P_B2` = expit(pure-CMD LR + logit(GAIA-FP's frozen prior)), frozen now in `results/dr3_candidates_B2prob.csv` (SHA-256 d86774c7…). The constant-π EM variant is a sensitivity analysis; it saturates at π = 0.9999 on DR3.<br>(b) The column `llr_cmd` of the prediction file is **not** CMD-only: it equals log_lr on DR3. It is not used as a baseline.<br>(c) O1 period match is \|P4/P3 − k\| ≤ 0.3k for k ∈ {½, 1, 2}.<br>(d) O2/D mass bounds come from Monte Carlo over the Thiele–Innes and parallax errors (n = 400, seed 0).<br>(e) H11b uses pooled high-confidence errors; each class is also reported.<br>(f) Unmatched sources (no DR4 counterpart within 1″) are reported and excluded.<br>(g) The second prediction set (v0.4 A1) is frozen now: `results/dr3_candidates_scored_A1.csv`, SHA-256 d8c9b2e2…, C* = 0.3.<br>(h) The control group is extracted from DR3 before DR4 by `src/h11_control.py` (rule as registered); its hash is added to the v0.6 manifest. | clarification |
| A21 | **H8 primary mass fallback:** if DR4 publishes no m1 with bounds, m1 = photometric relation with a 10% one-sigma error. `src/dr4_dynamical.py` reproduces the DR3 labels exactly (regression test). | clarification |
| A31 | **Weighted Holm** (Holm 1979) replaces equal-weight Holm in A18, fixed before any DR4 data exist. Reason: a power simulation (`audit/power_h1.py`, binormal scores, 3000 runs) shows that with 39 + 26 labelled objects and a true AUC of 0.73 (the DR3/APOGEE development value), H1 is detected with probability 0.90 at α = 0.025 but only 0.75 at the equal-weight Holm floor α/5. H1 is the headline test on independent literature labels, so it gets weight 0.4; A5 and H12 (large DR4 samples) 0.2 each; H2 and H11a 0.1 each. Weights of NOT CONDUCTED hypotheses are redistributed; a rejected hypothesis passes its weight on. Family-wise error stays ≤ 0.025. Code: `dr4_evaluate.weighted_holm`, with tests. | criterion |
| A32 | **H17 (secondary): Gaia epoch photometry, an independent channel.** For every DR4 candidate with ≥ 20 accepted G transits (DataLink EPOCH_PHOTOMETRY), a weighted 2-harmonic Fourier model at the **known** orbital period is compared with a constant (F-test; fluxes normalised by the median; points > 5 MAD from the median removed). Flag = p < 10⁻³. Prediction: the frozen DR4 P_impostor is higher for flagged candidates: AUC > 0.5: the 2.5th percentile of the stratified bootstrap (B = 2000, seed 7) is > 0.5, i.e. a one-sided 97.5% bound (as coded in `new_hypotheses.h17`; corrected wording, see A37). Needs ≥ 5 flagged and ≥ 10 unflagged. Sensitivity: AUC without periods within 10% of 1 yr or of 63 d (scanning-law aliases). Code: `new_hypotheses.h17`, adapter `dr4_release_map.epoch_photometry`. No DR3 development value exists (no epoch photometry for these stars in our data). | criterion |
| A33 | **H18 (secondary): compact-object impostors.** Among NEW DR4 combined orbits (same exclusions as H12), systems with dynamical companion mass m₂ ≥ 1.4 M☉. Prediction: among those with a resolved ρ label (A27, n_mc = 5000), the luminous fraction is > 0.5 (one-sided 97.5% Clopper–Pearson bound). Needs ≥ 10 resolved. DR3 development value: 80/81 = 0.99 [0.93, 1.00] with n_mc = 5000 labels (`results/new_hypotheses_dev_dr3_mc5000.json`; 80/83 with the stored n_mc = 200 labels). Gaia BH2 (DR3 5870569352746779008), a confirmed black hole, gets ρ = 0.92 (not luminous), as it should. | criterion |
| A34 | **H19 (secondary): contamination of the brown-dwarf desert.** Among NEW DR4 combined orbits whose astrometry alone (dark-companion assumption) gives 13–80 MJ: prediction, the luminous fraction among resolved systems is > 0.5, same test as H18. The median dynamical mass of the luminous ones is reported. DR3 development value: 33/35 = 0.94 [0.81, 0.99]; median true mass 273 MJ. Caveat stated with every number: combined solutions need a detectable RV orbit, which favours heavy companions. | criterion |
| A35 | **H20 (secondary): head-to-head with published methods on the sealed labels.**
- **Comparators**, fixed and hashed at DR4 run time before unblinding (`comparators.csv`):
  - Gaia DR4's own `nss_masses.fluxratio` (higher = more likely an impostor);
  - DR4 `exoplanet_candidate_hrd_proba + lowmass_candidate_hrd_proba` (higher = more likely substellar);
  - Bailer-Jones & Kreidberg 2026 m2, taken from the DR3 counterpart.
- **Test:** for each comparator, on the H1 objects where it exists: AUC of both and the paired stratified-bootstrap ΔAUC (GAIA-FP − comparator), B = 2000, seed 7.
- **Verdict:** "better" or "worse" only if the 95% CI excludes 0. Needs ≥ 10 per class.
- **DR3 development value** (BJK only, survey-SB2 labels): ΔAUC +0.22 [+0.08, +0.39] (`RESULTS_BJK_COMPARISON.md`).
- **Code:** `dr4_evaluate.h20`. | criterion |
| A36 | **Primary mass m1 on DR4.**
- m1 is taken from DR4 `nss_masses` (the DR4 equivalent of DR3 `binary_masses`, as the frozen DR3 predictions used); one row per source, the first `combination_method` alphabetically.
- Where DR4 publishes no m1, the registered photometric relation (`dr4_pipeline.mass_from_MG`) is used.
- The number of fallbacks is logged (`prepare` info).
- This applies to candidates and to the H12 combined orbits. | criterion |
| A37 | **Operational definitions (clarification of the code as of `f6144c6`; no change to any rule or code).**

**(a) Weighted Holm (A18/A31).**
- **Family:** F = the confirmatory hypotheses with status CONDUCTED, a subset of {H1, A5, H12, H2, H11a}, with weights w = (0.4, 0.2, 0.2, 0.1, 0.1). A hypothesis that is NOT_CONDUCTED leaves F, and the weights of the rest are renormalised.
- **p-values:** each p_i is the one-sided bootstrap p-value of its own test, p = (k + 1)/(B + 1), where k is the number of replicates on the null side:
  - H1: AUC ≤ 0.5;
  - A5 and H2: difference ≤ 0;
  - H11a: Brier difference ≥ 0;
  - H12: intersection–union, p = max(p_M1, p_M2b, p_M2a).
- **Algorithm:** let R = F.
  1. Reject every H_i in R with p_i ≤ α·w_i / Σ_{j∈R} w_j, where α = 0.025.
  2. If none is rejected, stop.
  3. Otherwise remove the rejected hypotheses from R and repeat.

  This is Holm's (1979) weighted step-down procedure. It controls the family-wise error rate at 0.025 for any dependence between the tests.
- **Decision:** a confirmatory hypothesis is **PASS** if and only if it is rejected by this procedure; otherwise it is FAIL. The per-hypothesis CIs are reported but do not decide confirmatory status. Equal-weight Holm is reported as a sensitivity analysis.
- **Calibration:** checked by simulation for H1. The false-positive rate is 0.015 (400 simulations; nominal 0.01). See deviation 29.

**(b) Independence of H18/H19 from their development data.**
- **DR3 development sample:** all DR3 AstroSpectroSB1 orbits with ϖ/σϖ > 10 that pass the H10 cuts (inside the main-sequence ridge colour range; dm > −2; finite and positive m1; finite A, C, H and their errors). This sample was used to develop H10, the mechanism tests and the ρ labels, and H18/H19 were written after their DR3 values were seen (deviation 27). The DR3 values are therefore development data, not evidence.
- **DR4 test sample:** only NEW DR4 combined orbits. Every DR4 source whose DR3 counterpart (dr3_neighbourhood, ≤ 1″) is a DR3 AstroSpectroSB1 or sealed source is removed first (A15). The DR4 test is therefore on systems never used for development.

**(c) H17.**
- **Eligible:** sources in the hashed DR4 catalogue with an orbital period, ≥ 20 G transits with finite positive flux and `g_n_obs` > 0, and still ≥ 20 after removing points more than 5 MAD from the median.
- **Denominator:** eligible sources with a finite F-test p.
- **Missing data:** sources without epoch photometry are excluded and counted.
- **Flag:** p < 10⁻³ for a 2-harmonic fit at the known period.
- **Minimum:** ≥ 5 flagged and ≥ 10 unflagged.

**(d) H18/H19.**
- **Sample:** the H12 sample after exclusion and the H10 cuts.
- **H18:** m₂,dyn ≥ 1.4 M☉, with m₂,dyn from a1 sin i, inclination and m1 (`mechanism.physics`).
- **H19:** dark-assumed m₂ from a0, ϖ, P and m1 in [13, 80) M_J.
- **Denominator:** systems with a resolved ρ label (luminous or dark, n_mc = 5000). Unresolved systems are counted and reported but not in the denominator. Systems with non-finite masses are excluded and counted.
- **Rule:** one-sided 97.5% Clopper–Pearson lower bound > 0.5; ≥ 10 resolved.

**(e) H20.**
- **Sample:** the H1 analysis set (sealed labels mapped to the DR4 catalogue by the nearest dr3_neighbourhood match, exactly as for H1).
- **Per comparator:** the objects where the comparator value is finite; ≥ 10 per class.
- **Comparator details:**
  - DPAC substellar probability = exoplanet + low-mass probability, missing only if both are missing;
  - several `nss_masses` rows per source → the first `combination_method` alphabetically;
  - BJK m2 through the DR3 counterpart in the same id map.
- **Rule:** paired stratified bootstrap, B = 2000, seed 7; "better" or "worse" only if the 95% CI excludes 0.
- **Comparator file:** written and hashed before unblinding. | clarification |
| A38 | **Lost label file: reconstruction rule (written 8 Nov 2026, before reconstruction and before DR4).**

The sealed file `labels_v2.json` (SHA-256 d6b0aabb…) can no longer be found; only its hash survives. It is rebuilt as `labels_v2r.json` under fixed constraints, so there is no freedom to choose objects or labels.

**(1) Same objects.** Exactly the 76 Gaia DR3 ids frozen on 9 Oct 2026 in `realdata/excluded_sealed_ids.csv`. No object is added or removed.

**(2) Same sources and rules (PREREGISTRATION §5).**
- **Sources:** the 11 listed papers.
- **Labels:** only from ground-based spectroscopy, RV or imaging.
- **Exclusions:** conflicting or low-confidence → unresolved, excluded. Gaia-4 → excluded_inspected.

**(3) Consistency checks, reported whatever they show.**
- (a) The 33 entries of the hash-verified v1 file (44f30e22…), with ids resolved, must carry the same labels in v2r. Any disagreement is listed.
- (b) The v2r counts are compared with the registered v2 counts (39 impostors, 26 substellar, 10 unresolved, 1 excluded).

**(4) Freeze before DR4.** The v2r SHA-256 is registered before DR4. The DR4 runner checks the v2r hash in place of the v2 hash.

**(5) Labels only.** No Gaia DR3 or DR4 feature of these objects is looked at while rebuilding, and no score is computed on them before DR4.

**Result (8 Nov 2026).**
- `labels_v2r` (SHA-256 `a8ccb9b6fd1b4bf97bd9669d8be866bb33bd83b3c630feb90933f9a05703d3aa`) supersedes `labels_v2`, whose file was not retained.
- Same 76 objects, same sources and rules; label counts identical (39 impostors, 26 substellar, 10 unresolved, 1 excluded_inspected).
- Rebuilt before DR4; no score was computed on these objects.
- **Checks:**
  - additions 21/18/5 with the same confidence split as the 9 Oct build log;
  - the 26 v1 entries keep their v1 labels except the two changes the original rules require (Gaia-4 → excluded_inspected; HD 68638 → unresolved by conflict).
- The DR4 runner checks the v2r hash. | criterion |
| A22 | **Schema guard:** the day-1 runner checks every required table, column, unit and dtype against `src/dr4_schema.py` and **stops** on any mismatch. A mapping to new DR4 names may be added only as a logged deviation, before any score is computed. | implementation |

| A24 | **Fallbacks fixed now** (`DR4_READINESS.md` §4).<br>(a) If `dr3_neighbourhood` is unavailable: positional match after propagating DR3 positions to J2017.5 with DR3 proper motions, nearest within 1″.<br>(b) If per-transit widths are missing: H2 is NOT CONDUCTED, and P_impostor is computed with a neutral RVS term.<br>(c) If combined solutions are missing: H8, A5 and H12–H14 are NOT CONDUCTED. | criterion |

| A25 | **Primary DR4 score = "v3.2"**: the registered v3.1 with the error corrections of the audit, all decided before DR4 (`src/dr4_run.py`, `src/rvs_v32.py`). The registered v3.1 output (`P_impostor_v31`) is reported next to it for every hypothesis. Reason: v3.1's RVS term flips 447 of 2102 verdicts with the random seed alone, so it cannot be the primary. The corrections are:<br>(1) RVS likelihood monotone in z (KDE bandwidth = null SD = 1, plus a monotone envelope);<br>(2) 8000 H_t draws with a per-candidate seed from source_id (order-independent, reproducible);<br>(3) (q, n) drawn from p(q, n \| a0, ΔM_G), the posterior the a0/CMD term uses;<br>(4) the candidate's own epoch times and width errors (as prereg §6.3 says);<br>(5) σ_a0 = a0/significance (Gaia's full covariance) instead of the rms of the four Thiele–Innes errors;<br>(6) population-prior covariates (log P, e, log m_fit), without G and ln d, which rebuild M_G and so re-count the CMD evidence;<br>(7) colours outside the CMD ridge range are excluded and counted, not clamped;<br>(8) invalid or uninformative RVS input gives "no information" with a reason, never a silent number.<br>A1 (prior selection), A6 and A7 apply unchanged. | method (error correction) |
| A26 | **Companion-mass sensitivity:** the frozen candidate rule (first-order m2 < 80 MJ) is kept. The number of candidates whose exact mass exceeds 80 MJ (27% on DR3) is reported, together with H1 recomputed without them, as a sensitivity analysis. | reporting |
| A27 | **Monte Carlo sizes:** ρ labels for H12–H14 use n_mc = 5000 (DR3 used 200, which changes ~20% of labels with the seed but never luminous ↔ dark). H8 keeps the registered 400 (A3) and reports a 5-seed spread. No false-alarm-probability claim is made from the 400-null injection threshold (its real FAP is 0.4–1.8%). | method / reporting |
| A28 | **A6 implementation reconciliation (pre-DR4).** The registered A6 light-ratio threshold is the secondary-to-primary flux ratio ℓ = L2/L1 = q^n ≥ 0.2, together with K_sum(1+e) ≥ 30 km/s. It is not the total-light fraction β = ℓ/(1+ℓ). The DR4 v3.2 implementation is aligned to the registered ℓ definition; a regression test covers the interval 0.2 ≤ ℓ < 0.25 where the two definitions disagree. No DR4 data were inspected for this correction. | implementation clarification |\n| A23 | **Erratum to v0.5 and the fate of A6.** v0.5 said our physical line-width model "ranked systems in the wrong direction because it ignored Gaia's single-/double-lined selection". The audit found the real cause, a **units bug** (finding F6: the period was passed in years to a function that expects days, so K was 7.15× too large). With K corrected, the model without SB1 truncation already ranks correctly (AUC 0.736). M3 did not support an SB2-resolution selection either. In an exploratory comparison on the already-used TEST half, the truncation is neutral at c = 1 (−0.007 [−0.018, +0.005]) and helps at c = 4 (+0.022 [+0.006, +0.039]). **Decision, made before DR4 and not on DR4 data: A6 stays as registered**, because the error was in the stated reason, not in the rule, and the evidence on the rule is mixed. The A6-off posterior (`P_impostor_noA6`) is reported as a sensitivity analysis for every hypothesis that uses P_impostor. A7 is unaffected: V3 still fails after the fix (−0.025 [−0.039, −0.009]). | erratum / criterion |
| A29 | **H15, population purity of Gaia's substellar yield (secondary, descriptive; written before DR4).**<br>(a) The impostor fraction among all DR4 substellar candidates is estimated as the mean of P_impostor (v3.2), with a bootstrap 95% CI. The registered labels play no part in this estimate.<br>(b) The companion-mass histogram (13–80 MJ, 6 log bins) is reported twice: raw, and weighted by 1 − P_impostor. Bins where the weighted and raw counts differ by more than their bootstrap CI are reported as "contamination-dominated".<br>(c) H15 is descriptive: it has no pass/fail and enters no headline claim. Its calibration rests on H11a/H3. If H11a fails, H15 is reported only with that warning. | hypothesis (descriptive) |

| A30 | **H16, independent-instrument test (secondary; written before DR4).**<br>(a) **Data:** APOGEE DR17 multi-visit RVs, already downloaded and hashed (`realdata/external/apogee_dr17_multivisit.csv`, SHA-256 a942246a…). They were never used to build or tune GAIA-FP.<br>(b) **Sample:** DR4 candidates, matched to APOGEE through the DR3 cross-match.<br>(c) **Positive:** RV scatter > K₈₀(1+e) + 1 km/s, i.e. impossible for a companion ≤ 80 MJ. **Negative:** every other candidate with ≥ 2 visits. This is not a claim that the negatives are substellar.<br>(d) **Statistic:** AUC of P_impostor (v3.2), stratified bootstrap. Pass if the lower 95% bound > 0.5. NOT CONDUCTED if there are fewer than 10 positives or fewer than 10 negatives.<br>(e) **Development result** (exploratory, on the DR3 predictions frozen 9 Oct): AUC 0.73 [0.58, 0.88] with 8 positives among 61 candidates (`RESULTS_APOGEE.md`). Code: `src/apogee_validation.h16`. | hypothesis (secondary) |
## Multiplicity (A18)
- **Confirmatory family**, m = 5. **Weighted** Holm step-down (A31), one-sided family-wise α = 0.025 (the registered tests are one-sided 95% bounds). Weights: H1 0.4, A5 0.2, H12 0.2, H2 0.1, H11a 0.1. Plain equal-weight Holm is reported as a sensitivity analysis:

  | Hypothesis | Null hypothesis |
  |---|---|
  | H1 | AUC ≤ 0.5 |
  | H2 | Δ rejection ≤ 0 |
  | A5 | ΔAUC(GAIA-FP − B2) ≤ 0 on the H8 labels |
  | H11a | ΔBrier ≥ 0 |
  | H12 | intersection–union of M1, M2b, M2a |

- **p-values:** one-sided bootstrap, p = (1 + #replicates on the null side)/(B + 1), B = 2000, seed 7. Bootstrap type: stratified for AUC-type tests, paired otherwise. For H12, p = max(p_M1, p_M2b, p_M2a).
- **Not conducted:** a hypothesis that is NOT CONDUCTED leaves the family, and m shrinks. This is decided by data availability alone, before any outcome is computed.
- **Reporting:** both the registered per-hypothesis verdicts (unadjusted 95% bounds) and the Holm verdicts are reported. **Headline claims use only the Holm verdicts.**
- **Secondary (reported, not adjusted, never in headlines as confirmed):** H3, H5, H6, H7, H8 (a) and (b), H11b, H13, H14, H16, H17, H18, H19, H20, M3, P0. H15 is descriptive.
- **Descriptive:** H4 (pipeline check), H11c.
- **Already done on DR3, development only:** H9, H10, V1–V3, M1–M4 on DR3.

## Blind-test integrity
- **Exposure before the run:** if, before the DR4 run, any member of the team sees DR4 data (pre-release or otherwise) of a sealed object, an H11 candidate or control, or an H12 system, that object is excluded and the exclusion is logged with its date. Published papers about an object do not change its sealed label.
- **No early look:** no DR4 value is looked at before the hash of the scored catalogue is committed. The only allowed checks are row counts and schema checks.

## Not changed
- H1–H11 definitions and thresholds.
- v0.3–v0.5, including A7: the empirical RVS score stays primary.
- Sealed labels and their hashes.

## Order of work on DR4 day (fixed)
1. Run `python dr4_day.py fetch`: downloads, schema guard (A22), row counts only.
2. Drop DR3-matched and sealed ids for H12–H14; drop sealed ids for H11.
3. Run `dr4_day.py score`: catalogue → SHA-256 committed **before** anything else.
4. Run, in order:
   1. `h11_outcomes.py`;
   2. `dr4_dynamical.py`;
   3. `dr4_mechanism.py`;
   4. `dr4_evaluate.py` (unblinding, Holm);
   5. `survey_xmatch.py`.
5. Publish every output whatever it says.
