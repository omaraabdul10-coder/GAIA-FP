# H9 / H10: is the companion dark? Our first real-data test of the line-width channel

**DATA: REAL.** Gaia DR3, run on 9 Oct 2026.

- **Plan:** `DARK_COMPANION_PLAN.md`, SHA-256 `6bc7c01a…`, hashed before any download.
- **Deviations:** 8–11 in `DR3_STUDY_DEVIATIONS.md`:
  - D2 was replaced by a faster random-sample query;
  - the main-sequence cut was applied to the calibration stars;
  - D3 came from the VizieR mirror, with m1 from the photometric relation;
  - one sealed row was deleted.
- **Code:** `src/dark_companion.py`.
- **Outputs:** `results/dark_companion.json`, `results/dark_companion_scored.csv`, `results/dark_companion_exploratory.json`.
- **Check:** the AUCs were recomputed independently with sklearn and are identical.

## Sample
- 33 464 AstroSpectroSB1 systems with ϖ/σ > 10. 19 506 remain after the main-sequence and quality cuts.
- Physical labels from ρ = a0 sin i / (a1 sin i):
  - **1186 luminous** (ρ 97.5% < 0.9);
  - **2060 dark-consistent** (ρ 2.5% > 0.9).
- With a usable vbroad (≥ 5 transits): **1927 labelled systems, of which 841 are luminous.**

## Pre-registered results (vbroad subset, n = 1927)
| Score | Uses a0? | AUC [95% CI] |
|---|---|---|
| B2: CMD only | no | 0.732 [0.708, 0.754] |
| VB: vbroad excess only | no | **0.755 [0.733, 0.776]** |
| **S1: CMD-LR + vbroad-LR (primary)** | no | **0.800 [0.780, 0.820]** |
| AMRF (Shahaf et al. style) | yes* | 0.788 [0.767, 0.807] |
| JOINT: a0\|CMD LR, no vbroad | yes* | 0.822 [0.802, 0.841] |
| S2: JOINT + vbroad-LR | yes* | 0.779 [0.756, 0.799] |

\*The label ρ is built from a0, so scores that use a0 share an input with the label. They are flagged, and none of them is the primary test.

- **H10a: PASS.** ΔAUC(S1 − B2) = **+0.068 [+0.042, +0.095]**.
- **H10b: PASS.** VB alone has AUC 0.755, with a lower bound > 0.5.
- **Sensitivity c = 4:** S1 has AUC 0.789, and H10a and H10b still pass.
- **H9 (the 2102 substellar candidates):** only 258 have vbroad, and only 6 of those are survey SB2. Exploratory only; no conclusion.

## Exploratory diagnosis (after the results; NOT pre-registered)
1. **The gain comes from the observed vbroad excess, not from our physical prediction.**
   - A naive sum B2 + VB gives AUC 0.796 [0.775, 0.815]. That is equal to S1: ΔAUC = +0.005 [−0.012, +0.022].
   - The per-system physical vbroad-LR *alone* has AUC **0.444 [0.418, 0.470]**, so it ranks in the wrong direction.
   - Adding it to JOINT lowers the AUC by 0.15.
2. **Why the physical prediction fails: a selection effect.**
   - Median vbroad is 14.9 km/s for luminous-companion systems, 8.1 km/s for dark-consistent ones and 8.2 km/s for the field. The real excess is about 7 km/s.
   - The model predicts f(1−f)·K² broadening of tens of km/s.
   - These systems were solved by Gaia as **single-lined** (SB1). Systems whose second set of lines was strong or well separated were removed from this class. The model does not include that selection, so it over-predicts the broadening and penalises exactly the luminous systems.
3. **The signal is strongest at intermediate periods.** For P = 100–500 d, S1 has AUC 0.829, against 0.726 for CMD only.

## What this means
- **Answer to the judge's question "what does your method add beyond CMD?" (real data, pre-registered):** the RVS line-width channel adds **+0.07 AUC** beyond the CMD in 1927 real systems. The relationship between vbroad and binarity itself was shown earlier at population level (Hadad, Mazeh et al. 2024). Our new element is the pre-registered, object-level test against physical ρ labels.
- **Negative finding, stated plainly:** our per-system physical broadening model is mis-calibrated on real data because it ignores the selection effect. That warns us about the DR4 RVS phase test too: its H_t simulations use the same physics.
- **Before DR4 (new dated amendment, before 2 Dec):**
  - add the SB1/SB2 classification selection to the H_t model;
  - or calibrate the RVS term empirically on DR3 ρ labels, using the DR3 data as a training set and keeping DR4 as the test.

  A model that already failed on real data must not be frozen as it stands.

## vbroad model v2: selection correction (plan `VBROAD_V2_PLAN.md`, SHA-256 4d51c373…, hashed before running; deviation 12 = split rule)
- **Model:** the SB1 truncation is applied, the blend is saturated at 30 km/s, and c is chosen on TRAIN (940 systems), then tested once on TEST (987 systems).
- **c chosen on TRAIN:** 4. This equals the rotational-kernel variance theory value, but it is the edge of the grid.

| Test on TEST | Result | Verdict |
|---|---|---|
| V1: v2 physical vbroad-LR alone | AUC **0.759 [0.727, 0.789]** (v1 was 0.430) | **PASS**: the selection correction fixed the inversion |
| V2: S1v2 vs CMD only | ΔAUC **+0.048 [+0.032, +0.064]** | **PASS** |
| V3: S1v2 vs naive B2 + VB | ΔAUC **−0.016 [−0.030, −0.002]** | **FAIL**: the physical model is not better than a simple empirical combination |

**Reading:**
- The physical line-broadening model now works in the right direction.
- Its strength matches theory (c ≈ 4).
- It still does not beat a naive empirical combination on real data.

**Mock check of the same correction in the DR4 RVS phase term (amendment A6):**
- Overall AUC on validation mocks: 0.976 → 0.972.
- RVS term alone: 0.850 → 0.809.
- Reason: the mock simulator does not include Gaia's SB2 selection. Real data show that the correction is needed. Both numbers are reported.

## ERRATUM (audit, 31 Oct 2026): the "wrong-direction" physical model was a units bug
**What was wrong:** `dark_companion.lr_vbroad` (H10) and `vbroad_v2.lr_v2` passed the period in **years** to `rvs_phase_test.K_sum_kms`, which expects **days**. As a result:
- the predicted RV separation K_sum was 365.25^(1/3) = **7.15× too large**;
- the predicted blend variance was **51× too large**.

The finding is F6 in `AUDIT_REPORT.md`. The frozen files were not edited. The corrected re-analysis is `src/erratum_k_units.py` → `results/erratum_k_units.json`, using the same data, rules and bootstrap.

| Quantity | Registered (bug) | Corrected |
|---|---|---|
| Physical vbroad-LR alone (v1, no SB1 truncation) | 0.444 [0.418, 0.470] | **0.736 [0.713, 0.759]** |
| S1 (primary) | 0.800 [0.780, 0.820] | 0.776 [0.755, 0.797] |
| **H10a** ΔAUC(S1 − B2) | +0.068 [+0.042, +0.095], PASS | **+0.044 [+0.033, +0.055], PASS** |
| H10a, c = 4 sensitivity | PASS | +0.075 [+0.057, +0.092], PASS |
| S2 (uses a0, flagged) | 0.779 | 0.832 [0.814, 0.850] |
| S1 − naive (B2 + VB) | +0.005 [−0.012, +0.022] | −0.019 [−0.031, −0.007] |
| v2 V1 (TEST) | 0.759, PASS | 0.745 [0.712, 0.776], PASS |
| v2 V2 | +0.048, PASS | +0.039 [+0.025, +0.054], PASS |
| v2 V3 | −0.016, FAIL | −0.025 [−0.039, −0.009], FAIL |
| v1 (no truncation) physical LR on the same TEST half | 0.430 | 0.724 |

H10b (VB alone, 0.755) is unchanged because VB does not use K.

**What this changes:**
1. The physical line-blend model was **never** ranking systems backwards. It did so only because of the units bug.
2. The explanation given above ("Why the physical prediction fails: a selection effect"), and repeated in amendment v0.5 and on the project website, is **wrong**. Ignoring Gaia's SB1 selection was not the cause.
3. With the correct K, the SB1 truncation of v2 adds only about +0.02 AUC on TEST (0.724 → 0.745).
4. The pre-registered conclusions still hold:
   - H10a passes, with a smaller gain;
   - V3 still fails, so amendment A7 (empirical RVS score primary) is still the rule.
5. The motivation for amendment A6 (SB1 truncation in the DR4 RVS physics term) has lost its main support. Its other premise, an SB2-resolution selection, was tested directly in `MECHANISM_PLAN.md` M3 and **not supported**. What to do with A6 before DR4 is proposed in amendment v0.6 (A23).
