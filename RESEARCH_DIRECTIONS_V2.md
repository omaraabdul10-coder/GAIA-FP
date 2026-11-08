# Research directions v2: scored and selected (9 October 2026)

**Scoring scale:** 1–5 on five criteria: novelty potential (N), significance (S), feasibility for a solo student (F), independent validation possible (V), clarity of the expected result (C). The scores are not inflated; "done" refers to work actually completed in this repository.

## Summary scores

| # | Direction | N | S | F | V | C | Total |
|---|---|---|---|---|---|---|---|
| 1 | **Real-data validation benchmark with survey SB2 labels (DR3 now, DR4 confirmatory)** | 4 | 4 | 4 | **5** | 5 | **22** |
| 2 | Uncertainty-aware follow-up optimisation (EIG) | 3 | 3 | 5 | 3 | 4 | 18 |
| 3 | Selection-bias-aware contamination | 4 | 4 | 3 | 3 | 3 | 17 |
| 4 | Cross-survey evidence calibration | 3 | 3 | 3 | 4 | 3 | 16 |
| 5 | Multi-hypothesis inference | 2 | 3 | 4 | 2 | 3 | 14 |
| 6 | Identifiability maps | 3 | 3 | 5 | 2 | 4 | 17 |
| 7 | Distribution-shift robustness | 2 | 3 | 5 | 3 | 4 | 17 |
| 8 | Open benchmark package | 3 | 4 | 4 | 5 | 4 | 20 |
| 9 | Isochrone-based joint mass inference | 1 | 3 | 3 | 3 | 4 | 14 |

## Direction details

### 1. Real-data validation benchmark with survey SB2 labels

- **Question:** On real Gaia astrometric substellar candidates, does a Gaia-only impostor probability agree with independent spectroscopic evidence of stellar multiplicity?
- **Why it matters:** Every published Gaia-only vetting idea, including ours, is validated on simulations or on about 20 objects followed up by hand. Real independent labels at scale are missing.
- **Closest prior work:**
  - Bashi+2022 validated DR3 *spectroscopic* SB1 orbits with LAMOST/GALAH RVs.
  - Marcussen+2026, Barbato+2026 and Stefánsson+2025 used their own follow-up spectra, about 20 objects each.
- **Contribution:** The first validation of astrometric-impostor vetting against survey SB2 catalogues. The labelling rules, matching and metrics are public and frozen in advance.
- **Data:** Gaia DR3 archive; APOGEE SB2 (Kounkel+2021), GALAH (Traven+2020), LAMOST-MRS SB2 (Kovalev+2024), LAMOST-MRS RV coverage (Wang+2019). All are public and free.
- **Feasibility:** About 2200 candidates, all data via TAP, a laptop is enough. Difficulty: medium.
- **Failure modes:**
  - Too few overlaps, making the test underpowered (a pre-set rule handles this).
  - Survey SB2 detection depends on brightness and separation.
  - DR3 lacks epoch RVS, so only the astrometry + CMD part is tested.
- **Hypothesis:** AUC(GAIA-FP; survey-SB2 vs LAMOST-single) > 0.5, with the lower CI bound above 0.5.
- **Baselines:** RUWE, CMD excess alone, orbit significance, random.
- **Falsified if:** the CI includes 0.5.
- **What would make it important:** A strong AUC on real data. A clear failure would also be important: it would show that simulated performance does not transfer, which is valuable for DR4 planning.
- **Status: pre-registered, code and tests done; the real run is pending access.**

### 2. Uncertainty-aware follow-up optimisation (EIG)

- **Question:** Does ranking ambiguous candidates by expected information gain resolve more of them per unit of telescope time?
- **Closest prior work:** Loredo 2004 (Bayesian adaptive exploration); Ford 2008.
- **Contribution:** Applying EIG ranking to Gaia vetting.
- **Status:** Done in simulation, including the held-out check: 91 correctly resolved vs 58 for ambiguity ranking.
- **Real-data validation:** Only possible if follow-up outcomes are replayed (Marcussen and Barbato targets), and those targets are sealed. Hence V = 3.

### 3. Selection-bias-aware contamination

- **Question:** How much do magnitude limits and survey targeting distort the apparent impostor fraction?
- **Approach:** Weight the survey-SB2 fraction by the survey coverage function against GAIA-FP's label-free estimate.
- **Risk:** Survey SB2 completeness as a function of Δv and flux ratio is poorly known. Feasible only as a sensitivity analysis.

### 4. Cross-survey evidence calibration

- **Question:** Do APOGEE, GALAH and LAMOST SB2 flags agree on the same stars?
- **Value:** It measures how noisy the survey labels are, which is needed for direction 1.
- **Status:** Planned as a QA table inside the DR3 study. It is not a stand-alone contribution.

### 5. Multi-hypothesis inference

- **Status:** H_pw is implemented. Its gain is non-significant, and an artefact hypothesis cannot be validated.
- **Decision:** Keep as reporting only.

### 6. Identifiability maps

- **Status:** Done (simulation and analytic). Valuable for the honesty of the project and for answering judges, but not testable on independent data.

### 7. Distribution-shift robustness

- **Status:** Done within the simulator family. The real distribution shift is DR3 vs simulation, which direction 1 tests directly.

### 8. Open benchmark package

- **What:** The frozen real-data candidate table, the survey labels, the matching code and the metrics, so that others can test their vetting methods without leakage.
- **Dependency:** Follows directly from direction 1. The sealed labels stay private until DR4 unblinding.

### 9. Isochrone-based joint mass inference

- **Note:** This is what Bailer-Jones & Kreidberg already do. It is needed only to improve our m1 and β(q), not as a contribution.

## Selection

**Direction 1, with 8 as its packaging, is the central contribution.** Directions 2, 6 and 7 remain as supporting analyses.

Reason: direction 1 is the only one that turns GAIA-FP's key weakness (no real-data validation) into its main result. It can be done **now** on DR3 and repeated confirmatorily on DR4, and its success or failure criterion is unambiguous.

## Central research question

> Can calibrated impostor probabilities computed from Gaia observables alone reliably identify stellar-binary impostors among real astrometric substellar candidates, as judged by independent spectroscopic surveys, and where must they abstain?

## Primary hypotheses (at most three)

| ID | Hypothesis |
|---|---|
| H-A (DR3, pre-registered) | AUC > 0.5 vs survey-SB2 labels in the LAMOST-observed population |
| H-B (DR4, confirmatory) | The same test with the RVS phase term added: AUC improves over the DR3 version on the same objects |
| H-C | The label-free contamination bracket is consistent with the survey-based lower bound |
