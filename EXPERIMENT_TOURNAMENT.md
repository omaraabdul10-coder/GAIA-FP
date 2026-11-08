# Experiment tournament — results (9 October 2026)

- **Plan:** `TOURNAMENT_PLAN.md`. It was written and hashed **before** any result existed (SHA-256 `37d68faaf4cfbe95036ed35879c52571c5cf712aa51b2008ced52761373eb92d`).
- **Code:** `src/tournament.py`, `src/sim.py`, `src/lik.py`, `src/followup.py`, `src/x3_sens.py`.
- **Raw output:** `results/tournament_val.json`, `results/tournament_heldout.json`, `results/x3_sensitivity.json`.

**Everything below is simulated** (Lammers & Winn 2025 mock catalogues plus our observation model). No real-data claim is made here.

## Splits

| Split | Content | Used for |
|---|---|---|
| TRAIN | DR4 mocks: 3000 planets and 575 impostors | Training the ML baseline only |
| VALIDATION | A disjoint DR4 set: 3000 planets and 576 impostors | All tournament decisions |
| HELD-OUT | DR5 mocks: 4000 planets and 1500 impostors | Evaluated once, after all decisions |

The DR5 observation model differs: 3800-day span and 45–85 RVS epochs. The DR5 mocks were never used during development.

## Frozen baseline B0 = GAIA-FP v3 + EM (VALIDATION)

| Method | AUC | Impostors rejected at 95% planet retention | Brier |
|---|---|---|---|
| **B0: v3 + EM (no labels)** | **0.976** | **87%** | **0.040** |
| v3 with fixed prior π = 0.3 | 0.960 | 78% | 0.056 |
| ML (gradient boosting, trained on TRAIN) | 0.971 | 88% | — |

## X1 — competing hypothesis H_pw (planet host with an unresolved wide stellar companion)

**Setup.** On VALIDATION, 10% of planet hosts were given third light (q_w ~ U(0.3, 1)) and a constant extra line width with no phase locking.

| Model | AUC with H_pw present | AUC on clean set | H_pw with RVS called impostor (P > 0.5) | H_pw without RVS called impostor | Impostors with P > 0.5 |
|---|---|---|---|---|---|
| B0 | 0.9733 | 0.9761 | 10/182 = 5.5% | 22/100 = 22% | 83.7% |
| X1, w = 0.02 | 0.9733 | 0.9759 | 5.5% | 20% | 82.1% |
| **X1, w = 0.05 (pre-specified)** | 0.9731 | 0.9755 | **6/182 = 3.3%** | 18% | 80.7% |
| X1, w = 0.20 | 0.9707 | 0.9731 | 2.7% | 10% | 72.7% |

**Pre-stated criterion: formally met.** The relative reduction is 40% (needed ≥ 30%), and the clean-set AUC fell by 0.0006 (needed ≤ 0.005).

**But the evidence is weak:**
- 10/182 vs 6/182 is not statistically significant (Fisher p = 0.44).
- The price is a 3-point drop in impostors flagged at P > 0.5.
- Without RVS, H_pw and H_t are essentially indistinguishable; see `IDENTIFIABILITY_ANALYSIS.md`.

**Decision.** H_pw is **retained as a reported alternative explanation**: each candidate gets P(H_pw) next to P(H_t), with w = 0.05. It is **not claimed as a validated performance improvement**. On HELD-OUT (where no H_pw exists) it changes AUC from 0.9783 to 0.9778, i.e. negligibly.

**Not implemented: an instrumental/artefact hypothesis.** We have no realistic simulation of Gaia systematic false orbits. A likelihood based only on noise would merely restate the detection threshold, which is not evidence about real artefacts.

## X2 — three-way output with abstention

**Rule.**
- "Likely substellar" if P ≤ t.
- "Likely impostor" if P ≥ 1 − t.
- Otherwise "ambiguous — follow-up needed".

The largest t with decided-error ≤ 2% on VALIDATION is **t = 0.15**.

Coverage–error trade-off on VALIDATION:

| t | Coverage | Error among decided |
|---|---|---|
| 0.01 | 58% | 0.3% |
| 0.06 | 77% | 0.8% |
| 0.11 | 84% | 1.5% |
| **0.15** | **87%** | **1.9% (CI 1.4–2.4%)** |
| 0.26 | 93% | 2.9% |
| 0.46 | 99% | 4.8% |

**HELD-OUT, no re-tuning:** coverage **84%**, error **2.0% (92/4621; Clopper–Pearson 95% CI 1.6–2.4%)**.

**Criterion met** (coverage ≥ 60% at ≤ 2% error on VALIDATION, and it transfers to HELD-OUT). **Adopted.**

## X3 — expected-information-gain (EIG) follow-up ranking

**Setup.**
- 300 ambiguous VALIDATION candidates (0.1 < P < 0.9).
- Budget: 270 cost units. One unit is one night-equivalent; a 3-epoch RV run costs 3.
- Outcomes are drawn from the **true** mock parameters. The updates use only Gaia information.

Results: correctly resolved / wrongly resolved (P < 0.05 or > 0.95).

| Instrument assumption | EIG per cost (free choice of option) | Ambiguity-ranked, RV for all | Random, RV for all | **EIG-ranked, RV for all** |
|---|---|---|---|---|
| Nominal (SB2 if Δv > 8 km/s; metallicity spectrum gives CMD σ 0.12) | 261 / 0 | 50 / 3 | 62 / 1 | **74 / 1** |
| Δv > 15 km/s | 261 / 0 | 18 / 1 | 21 / 0 | 49 / 2 |
| Metallicity σ 0.20 | 231 / 4 | 51 / 0 | 60 / 3 | 72 / 2 |
| Both pessimistic | 212 / 2 | 17 / 0 | 20 / 1 | 44 / 2 |

**Criterion met.** EIG gives ≥ 1.2× more correct resolutions than ambiguity ranking with no more errors. With the same instrument (RV), EIG ranking resolves 74 vs 50 (Fisher p = 2×10⁻⁴), and the advantage grows under pessimistic assumptions (49 vs 18). **Adopted.**

**Caveat.** The very large free-choice gain comes mostly from the assumption that one metallicity spectrum shrinks the CMD scatter to 0.12–0.20 mag. That assumption is plausible but **not validated** by us. The EIG chooses the 1-spectrum option for about 90% of candidates. The robust, assumption-light result is the **ranking** gain at fixed instrument.

## X4 — contamination estimators

Truth vs estimate; the profile-likelihood 95% CI applies to the constant-π estimator.

| Scenario (VALIDATION) | True 0.05 | True 0.15 | True 0.30 | True 0.45 |
|---|---|---|---|---|
| Nominal: heterogeneous EM / constant EM | 0.057 / 0.045 | 0.159 / 0.139 | 0.312 / 0.283 | 0.455 / 0.431 |
| True CMD σ 0.36, assumed 0.30 | **0.081** / 0.070 | **0.183** / 0.165 | 0.325 / 0.297 | 0.453 / 0.424 |
| True CMD σ 0.24, assumed 0.30 | 0.045 / **0.028** | 0.149 / **0.117** | 0.309 / **0.271** | 0.465 / 0.433 |
| RVS noise 2× (not modelled) | 0.058 / 0.041 | 0.159 / 0.132 | 0.310 / 0.277 | 0.456 / 0.422 |
| 10% H_pw (not modelled) | 0.074 / 0.061 | **0.178** / 0.158 | 0.326 / 0.303 | 0.480 / 0.456 |

**HELD-OUT DR5:** true 0.273. Heterogeneous EM gives 0.281, constant EM gives 0.260, profile CI [0.246, 0.274].

**Criterion (|bias| ≤ 0.03 in every scenario): NOT met.** The contamination fraction is identifiable only if the CMD scatter is known to about ±20%:
- underestimating σ by 20% biases the estimate by up to +0.033;
- overestimating σ by 20% biases it by up to −0.033;
- unmodelled third-light hosts add about +0.02 to +0.03.

The two estimators bracket the truth in most scenarios: heterogeneous EM tends high and constant EM tends low. **Adopted reporting rule:** quote the pair (constant, heterogeneous) as a bracket, and propagate the measured uncertainty of the CMD scatter. A single number with a bootstrap CI is not enough.

## X5 — distribution-shift suite (VALIDATION populations)

Each cell is AUC / impostors rejected at 95% planet retention.

| Shift | v3 with fixed π | **B0 = v3 + EM** | ML |
|---|---|---|---|
| Nominal | 0.960 / 78% | **0.976 / 87%** | 0.971 / 88% |
| G < 12 | 0.981 / 89% | **0.989 / 96%** | 0.981 / 95% |
| G > 14 | 0.939 / 73% | 0.947 / 79% | 0.945 / 73% |
| d < 60 pc | 0.974 / 86% | **0.988 / 92%** | 0.979 / 94% |
| CMD scatter 0.45 | 0.909 / 54% | **0.953 / 70%** | 0.933 / 69% |
| RVS noise 2× | 0.958 / 77% | 0.975 / 87% | 0.973 / 88% |
| 10–20 RVS epochs | 0.955 / 74% | 0.975 / 86% | 0.972 / 85% |
| RVS missing | 0.948 / 74% | **0.970 / 83%** | 0.962 / 80% |
| Contamination 5% | 0.965 / 80% | 0.978 / 87% | 0.968 / 87% |
| Contamination 50% | 0.963 / 82% | 0.980 / 90% | 0.974 / 89% |

**Criterion met: 6 of 9 shifts.** B0's ΔAUC was no worse than ML's for G < 12, d < 60 pc, CMD 0.45, RVS missing, 5% and 50% contamination. In the other three (G > 14, RVS noise 2×, few epochs) B0 was worse by ≤ 0.003, which is within simulation noise.

The largest real degradations are for faint stars (G > 14: −0.03) and large CMD scatter (−0.02). Robustness to "RVS noise" and "few epochs" is partly because the simulated RVS signal is modest overall.

**Genuine robustness vs. shared assumptions.** All shifts are applied inside the same simulator family. They test sensitivity to observing conditions, not to wrong physics.

## Final HELD-OUT result (DR5 mocks, evaluated once)

| Method | AUC | Rejection at 95% retention | Brier |
|---|---|---|---|
| **B0 = v3 + EM (no labels)** | **0.978** | **88.3%** | 0.0488 |
| Final (B0 + H_pw reporting, w = 0.05) | 0.978 | 88.2% | 0.0491 |
| ML trained on DR4 simulator | 0.971 | 84.4% | — |
| v3 with fixed π = 0.3 | 0.963 | 80.0% | — |
| CMD-only physics LR | 0.956 | 76.3% | — |

Other HELD-OUT results:
- **Three-way output (t = 0.15):** 84% decided, 2.0% error.
- **Failure cases:** the 15 worst errors are 14 impostors scored as planets and 1 planet scored as an impostor.
  - Most of the impostors lack RVS (faint, G > 13) and have a CMD measurement scattered onto the main sequence (ΔM_G between −0.2 and +0.05).
  - The others have RVS but very long periods (P ≈ 1100–3100 d), where the phase-locked signal is weak.
  - The planet error is a 3.9σ CMD outlier.
  - These are exactly the regions mapped as weakly identifiable.

## Multiple comparisons

Five extensions were tested against pre-stated criteria, and HELD-OUT was used once. X1 passed its criterion only marginally, with a non-significant difference, and is therefore not claimed as an improvement.

## Post-tournament checks (9 October 2026, 03:40–04:10)

### C1 — Does the follow-up-selection advantage hold on independent data?

This answers an external reviewer's question: does X3 hold on independent simulations, and under realistic spectrograph limits?

**Protocol.** The script `src/x3_heldout.py` was written and hashed before it was run. It applies X3 with no re-tuning to the HELD-OUT DR5 mocks. This is the first time X3 has touched HELD-OUT.

**Criterion (unchanged from X3):** EIG-ranked RV follow-up must give ≥ 1.2× more correct resolutions than ambiguity-ranked follow-up, with no more wrong ones. The budget is the same for all policies.

Results, as correct / wrong resolutions:

| Setting | Ambiguous candidates | Ambiguity-ranked | Random | Brightest first | Most planet-like first | **EIG-ranked (RV)** | EIG per cost (free choice of option) |
|---|---|---|---|---|---|---|---|
| S1 nominal (SB2 if Δv > 8 km/s) | 400 | 58 / 3 | 66 / 1 | 78 / 3 | 77 / 3 | **91 / 0** | 351 / 1 |
| S2 small-telescope (G ≤ 11.5; SB2 if Δv > 12 km/s; metallicity σ 0.25) | 59 | 3 / 0 | 7 / 0 | 5 / 0 | 8 / 0 | **12 / 0** | 43 / 4 |

**Criterion met in both settings.**
- In S1, EIG-ranked gives 1.57× the ambiguity-ranked result, and also beats brightest-first and most-planet-like-first.
- In S2, the numbers are small (n = 59), so the 4× ratio is fragile.
- In S2 the free-choice policy produced 4 wrong resolutions, all from single-epoch spectra. With a small telescope we therefore recommend the **3-epoch RV option**, not single spectra.

### C2 — Per-candidate period uncertainty in the RVS template (realism fix)

The mock catalogues' own MCMC period errors have a median of **3.5%**, not the 1% assumed until now. The fixed 1% was **optimistic** for typical candidates.

VALIDATION results using each candidate's own σ_P (`results/sigp_validation.json`):

| Quantity | Fixed 1% | Own σ_P |
|---|---|---|
| AUC | 0.9761 | 0.9751 |
| Impostors rejected at 95% retention | 87.3% | 87.1% |
| Impostors with z > 2.33 | 37.6% | 34.4% |

**Adopted for v3.1**, because it is the correct model. The cost is small and honest.
