# Research opportunities, ranked (9 October 2026)

## How the list is ranked

Each extension is scored on scientific value × feasibility before the deadline × strength of evidence obtainable.

The "status" column records what was **actually done**. Validation figures refer to `EXPERIMENT_TOURNAMENT.md` and come from simulation unless stated otherwise.

## Summary table

| Rank | Extension | Status |
|---|---|---|
| 1 | B. Abstention / three-way output | Implemented; validated on held-out simulation |
| 2 | C. EIG follow-up ranking | Implemented; validated in a truth-based simulation; instrument assumptions not validated |
| 3 | D. Identifiability map | Done (analytic + simulation) |
| 4 | G. Contamination estimator: identifiability and sensitivity | Done; criterion failed, which is an informative negative result |
| 5 | E. Independent benchmark | Held-out DR5 mock set done; real labelled set (65) awaits DR4 |
| 6 | F. Distribution-shift suite | Done |
| 7 | A. Competing hypotheses (H_pw implemented; artefact hypothesis not) | Partly done; weak evidence |
| 8 | I. Discovery prioritisation | Pipeline ready (P + EIG); deployment needs DR4 |
| 9 | H. Simulation realism | Partly done (cadence, σ_P, noise checks); one fix identified, not applied |
| 10 | J. Reproducible package | Scripts plus a `run_all.sh`; pip packaging not done |
| 11 | K. Isochrone mass–flux relation instead of slope marginalisation | Not done |
| 12 | L. Per-candidate orbit uncertainty in the RVS template | Not done; identified by R2 |

## Details

### 1. B — Abstention / three-way output

- **Problem:** A forced binary decision mislabels the stars for which the data are uninformative.
- **Closest methods:** Reject-option classification. Exoplanet vetting tools report a probability, not an abstention.
- **Gap filled:** A validated coverage–error trade-off for Gaia impostor vetting.
- **Why it matters:** Follow-up resources go to the right stars, and the result reports honestly what Gaia cannot decide.
- **Resources:** Trivial computation.
- **Complexity:** Low.
- **Validation:** Threshold chosen on VALIDATION, applied once to the DR5 held-out set. Result: 84% decided at 2.0% error (CI 1.6–2.4%).
- **Main risk:** Calibration on real DR4 data may differ from the simulation.
- **Value:** High.
- **Feasible before deadline:** Done.

### 2. C — EIG follow-up ranking

- **Problem:** Which ambiguous candidate to observe, and with what?
- **Closest methods:** Loredo 2004; Ford 2008; Ishida 2019.
- **Gap filled:** Not found for Gaia impostor vetting.
- **Why it matters:** Telescope time is the bottleneck. RV follow-up of Gaia candidates is exactly what Barbato and Marcussen did, by hand.
- **Resources:** Light computation.
- **Complexity:** Medium.
- **Validation:** Truth-based outcome simulation. At fixed instrument, EIG ranking gives 74 vs 50 correct resolutions (Fisher p = 2×10⁻⁴), and the gain holds under pessimistic assumptions.
- **Main risk:** The option-choice gain relies on an assumed metallicity correction of the CMD scatter (σ → 0.12–0.20).
- **Value:** Medium–high.
- **Feasible before deadline:** Done; the real-data replay is not done.

### 3. D — Identifiability map

- **Problem:** Where Gaia data cannot decide.
- **Closest methods:** Bailer-Jones & Kreidberg discuss the degeneracy qualitatively. Our power maps for the RVS test are new.
- **Why it matters:** It prevents over-claiming and defines where abstention is mandatory.
- **Resources:** Light computation.
- **Complexity:** Low–medium.
- **Validation:** Analytic and simulation checks. The cadence realism check used the real DR4 pre-release cadence.
- **Main risk:** RVS precision on real DR4 data is unknown.
- **Value:** High (scientific honesty and judging).
- **Feasible before deadline:** Done.

### 4. G — Contamination estimator

- **Problem:** Is the impostor fraction identifiable without labels?
- **Closest methods:** FDR regression; VESPA-style population priors.
- **Finding:** Bias stays within about 0.012 if the CMD scatter is correct, but reaches about ±0.03 for a 20% error in σ, and about +0.025 for 10% unmodelled third light. The pre-stated criterion (≤ 0.03 everywhere) **failed**.
- **Rule adopted:** Report a bracket (constant EM, heterogeneous EM) together with the uncertainty in σ.
- **Value:** Medium–high. It is a calibrated, limited measurement rather than an over-claim.
- **Feasible before deadline:** Done.

### 5. E — Independent benchmark

- **Done now:** Held-out DR5 mocks (a different population and cadence), never touched during development. Result: AUC 0.978 vs 0.971 for ML.
- **The real benchmark:** 65 labelled systems, sealed, usable only after 2 December 2026.
- **Not done, and why:** A DR3-based real benchmark is ruled out because it would require looking at Gaia features of labelled objects, which breaks blinding. Reusing other labelled systems would shrink the blind set.
- **Main risk:** n = 65 gives wide confidence intervals.

### 6. F — Distribution-shift suite

- **Done.** B0 is no worse than ML in 6 of 9 shifts. The largest losses are for faint stars and large CMD scatter.
- **Limitation:** All shifts are within the same simulator family.

### 7. A — Competing hypotheses

- **H_pw (planet host with a wide companion):** Implemented. It halves false "impostor" calls for such hosts when RVS is available (not statistically significant), and is reported as P(H_pw).
- **Artefact hypothesis:** Rejected for now. There is no validated model of Gaia systematic false orbits, and a noise-only likelihood would just restate the detection threshold.
- **Hierarchical triples:** Behave like H_pw on the CMD. Listed, not modelled.

### 8. I — Discovery prioritisation

- **Pre-defined ranking criteria:**
  - Confirmation list: P(substellar) ≥ 0.85, then by EIG of RV per cost.
  - Vetting list: ambiguous candidates, ranked by EIG per cost.
- **Reported per candidate:** the evidence, P(H_t), P(H_pw), whether P is calibrated in simulation, the main reason it could be a false positive, and the best next observation.
- **Deployment:** DR4 only, labelled future work. **No candidate will be called a planet without RV confirmation.**

### 9. H — Simulation realism

- **Checked:**
  - Real cadence vs uniform cadence: power difference of at most about ±0.1.
  - Real per-transit astrometric errors: 0.028 mas vs 0.11 mas in the RUWE proxy model. This affects only the RUWE baseline.
- **Found:** The fixed 1% period uncertainty in the template suppresses short-period power (0.33 vs 0.96 at P = 50 d).
- **Fix:** Use the per-candidate posterior σ_P (item L). Not applied yet.

### 10. J — Reproducibility

- **Available:** All scripts, a fixed-seed `run_all.sh`, and a requirements file.
- **Redistribution:** The derived synthetic datasets can be shared (Lammers & Winn catalogues are MIT-licensed).
- **Never published:** The private labels.
- **Not done:** A pip package with tests.

### 11. K — Isochrone mass–flux relation

- **Why:** This is what Bailer-Jones & Kreidberg use. It would replace the n ~ U(2, 6) slope marginalisation and improve calibration for M dwarfs.
- **Complexity:** Medium. It needs isochrone tables (PARSEC/MIST).
- **Feasibility:** Possible before the freeze, if downloadable.

### 12. L — Per-candidate σ_P in the RVS template

- **Complexity:** Low.
- **Value:** Raises short-period power (simulation shows 0.33 → 0.96 at 50 d).
- **Status:** **Should be done before the freeze.**
