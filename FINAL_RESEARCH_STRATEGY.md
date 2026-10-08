# Final research strategy (9 October 2026)

## The chosen version: GAIA-FP v3.1

The output for each candidate has three parts:

1. **Calibrated probabilities from Gaia data only:** P(impostor), P(planet host with a wide companion) and P(substellar). They come from:
   - the joint a0 | CMD likelihood;
   - the physics-predicted, phase-locked RVS width likelihood;
   - a label-free EM population prior.
2. **A three-way verdict** with the pre-specified threshold t = 0.15: likely substellar, likely impostor, or ambiguous.
3. **For ambiguous candidates:** the follow-up observation with the highest expected information gain per cost.

**At population level**, the contamination fraction is reported as a bracket (constant-π EM, heterogeneous EM), together with its sensitivity to the CMD scatter.

## Retained, rejected and planned

| Feature | Decision | Reason |
|---|---|---|
| Joint a0 \| CMD (conditional) | Keep | Makes the likelihood ratios calibrated, which the contamination estimate requires. It does **not** improve ranking. |
| Physics-predicted RVS width test | Keep | The only Gaia observable that separates twins from third-light hosts. Power is mapped. |
| Label-free EM prior | Keep | Best AUC on validation and held-out sets. Robust to a shift in CMD scatter. Needs no labels. |
| Abstention (t = 0.15) | **Keep (validated)** | Held-out: 84% decided, 2.0% error |
| EIG follow-up ranking | **Keep (validated in simulation)** | Gives 1.5–2.7× more resolutions at a fixed instrument |
| H_pw competing hypothesis | Keep **as a reported alternative only** | Small, non-significant gain; makes the reasoning about the explanation honest |
| Artefact hypothesis | Reject (for now) | No validated model of real Gaia systematics |
| ML classifier as the main method | Reject | Needs labels or a trusted simulator; worse on held-out (0.971 vs 0.978) and under CMD shift |
| Single-number contamination with bootstrap CI | Reject | Not identifiable to ±0.03 without knowing σ_CMD |
| Per-candidate σ_P in the RVS template | **Do before the freeze** | Cheap; fixes a conservative bias at short P |
| Isochrone mass–flux relation | Do before the freeze if time allows | Aligns with Bailer-Jones & Kreidberg; better M-dwarf physics |

## Timeline to the freeze (before 2 December 2026)

1. Apply the σ_P fix. Re-run only VALIDATION to confirm nothing breaks; do not re-run held-out tuning.
2. Freeze v3.1 in PREREGISTRATION v0.3. Include:
   - the threshold t = 0.15;
   - the EIG instrument assumptions;
   - the contamination-bracket rule;
   - hashes of all code.
3. Make an independent timestamp (OSF or Zenodo DOI).
4. After 2 December: run the blind DR4 evaluation on the 65 labelled systems (H1–H6), then unblind, then report every hypothesis, including failures.

## Answers to the five questions

1. **Strongest result actually demonstrated.**
   - On real data: the independent pipeline reproduces the published Gaia BH3 orbit within 1σ, from DR4 pre-release epoch astrometry. That validates the pipeline, not the classifier.
   - In simulation: a label-free, calibrated GAIA-FP reaches AUC 0.978 and rejects 88% of impostors at 95% planet retention on a held-out DR5 mock set never used in development. The simulator-trained ML reaches 0.971 / 84%.
2. **Most valuable validated addition.** The three-way output, because it transferred unchanged from validation to the held-out set (2.0% error at 84% coverage). Next is EIG ranking of follow-up at a fixed instrument (74 vs 50 resolutions, p = 2×10⁻⁴).
3. **Tempting extensions not to implement.**
   - An artefact hypothesis without a systematics model.
   - Claiming a precise contamination fraction.
   - Replacing physics with a deep or ML classifier trained on simulations.
   - Claiming novelty for joint astrometry + photometry (Bailer-Jones & Kreidberg 2026 did it).
   - Announcing "new planets" from DR4 without RV confirmation.
4. **Evidence that would most improve competitiveness.**
   - (a) The DR4 blind result on the 65 sealed labels, with H1, H5 and H6 tested.
   - (b) A detection of phase-locked RVS broadening in at least one known SB2 impostor in real DR4 epoch data.
   - (c) An independent timestamp before 2 December.
   - (d) One real follow-up spectrum (for example from the Shamakhy 2-m telescope) of a top-ranked ambiguous DR4 candidate.
5. **What remains unproven.**
   - Every classification number on real data.
   - Real DR4 RVS width precision.
   - The real CMD scatter.
   - Whether the impostor population resembles the Lammers & Winn simulator.
   - The metallicity-correction assumption behind the EIG option choice.
   - Whether the method beats a Bailer-Jones & Kreidberg-style mass inference.
