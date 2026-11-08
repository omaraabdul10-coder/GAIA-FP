**OSF pre-registration (public, frozen 9 Oct 2026, 08:52 UTC): https://osf.io/n5h4b — DOI [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B).** It freezes PREREGISTRATION.md v0.3, PREREG_AMENDMENT_v0.4.md, the plans, and the SHA-256 of every source file (`FREEZE_MANIFEST.sha256`). A file in this repository is the frozen version if and only if its hash matches the manifest.

**Amendment v0.5 (public, registered 10 Oct 2026, 04:43 UTC, before Gaia DR4): https://osf.io/tbjgy — DOI [10.17605/OSF.IO/TBJGY](https://doi.org/10.17605/OSF.IO/TBJGY).** It registers PREREG_AMENDMENT_v0.5.md (A6 SB1 truncation, A7 empirical-primary DR4 RVS score, A8 the H11 DR3→DR4 time-separated test, A9 label limitation), DR3_TO_DR4_PREDICTION_PLAN.md, VBROAD_V2_PLAN.md and `FREEZE_MANIFEST_v0.5.sha256` (SHA-256 1a6bce97…, 56 files, including the frozen DR3 predictions `results/dr3_candidates_scored.csv` 14173467…). All archived hashes were checked against the local files after registration.


# Competition pack (draft; update only with demonstrated results)

## Title

**Unmasking Stellar Impostors: Calibrated, Gaia-Only Vetting of Astrometric Planet Candidates, Validated Against Independent Spectroscopic Surveys**

Short form: GAIA-FP.

## Abstract (current, demonstrated results only)

### Problem

Up to half of the giant-planet and brown-dwarf candidates found by Gaia astrometry turn out, on spectroscopic follow-up, to be pairs of near-identical stars. I developed GAIA-FP, which gives every candidate a calibrated probability of being such an "impostor", using Gaia data alone. GAIA-FP abstains ("ambiguous") when the data cannot decide, and ranks follow-up observations by their expected information gain.

### Pipeline validated on real data

An independent orbit pipeline reproduces the published orbit of the black hole Gaia BH3 from Gaia DR4 pre-release epoch astrometry (P, e, a0 within 1σ).

### Simulation results

These results use independent mock catalogues and a held-out mock release (DR5) that was never used in development. GAIA-FP uses no training labels.
- It rejects 88% of impostors at 95% planet retention (AUC 0.978).
- A machine-learning classifier trained on the simulator reaches 84% (AUC 0.971).
- With the three-way output, 84% of candidates are decided at 2.0% error.

### Theory result

Blended spectral-line centroids reproduce the photocentre motion, so only line broadening that is phase-locked to the orbit carries independent evidence.

### Integrity

All methods, thresholds and a sealed set of 76 spectroscopically labelled systems (65 analysed) were pre-registered before Gaia DR4.

### Placeholders

- **DR3 real-data result (9 Oct 2026, pre-registered):**
  - Among 2102 Gaia DR3 astrometric candidates below 80 MJ, 33% are over-luminous at more than 1.5σ, against 10% of field stars. That is direct, label-free evidence of a large impostor population.
  - The pre-registered AUC against 16 survey-SB2 binaries was 0.64 [0.49, 0.79]. This is **not** significant, and the simple CMD baseline did as well.
  - Diagnosis: the survey labels are biased toward twins.
  - An independent dynamical check on 95 Gaia AstroSpectroSB1 systems (photocentre vs RV orbit) identified 42 impostors from Gaia's own dynamics (ρ or m2_dyn; not RV-confirmed). The frozen GAIA-FP flagged 40 of them (95% [84, 99]) and wrongly accused neither of the 2 genuine-looking brown dwarfs (n = 2 is far too small to measure a false-alarm rate).
- **[DR4 confirmatory result: after 2 Dec 2026.]**

## Contribution statement

| What is not new | What GAIA-FP adds |
|---|---|
| Joint astrometry + photometry (Bailer-Jones & Kreidberg 2026) | (i) A calibrated per-object impostor probability, conditioned on how candidates are selected |
| Line-width vs orbital phase as a concept (Marcussen & Albrecht 2023) | (ii) An explicit abstention output with a validated coverage–error trade-off |
| | (iii) Quantified identifiability limits |
| | (iv) A validation of astrometric-impostor vetting against independent survey SB2 catalogues (DR3 now, DR4 confirmatory); in the literature we searched (NOVELTY_AND_PRIOR_ART.md) we did not find an earlier one |
| | (v) A pre-registered, blind design |

## Plots and tables to generate from ACTUAL results

1. BH3 orbit fit: data, model and residuals (real).
2. Completeness heat map on the real Gaia-4 cadence (simulated signals).
3. ROC and PR curves: DR3 real data vs survey-SB2 labels, with baselines (after the real run).
4. Coverage–error curve of the three-way output, validation and held-out (simulation).
5. Identifiability maps: CMD AUC vs (q, σ); RVS power vs (P, G) (simulation).
6. Contamination: label-free bracket vs survey lower bound (real, after the run).
7. EIG follow-up resolutions vs budget, compared with baselines (simulation).
8. Per-candidate report card example: evidence, P, verdict, best next observation.

## Questions a skeptical judge may ask, with honest answers

**"Isn't this just Bailer-Jones & Kreidberg?"**
They infer masses from joint astrometry and photometry. I build a calibrated *decision*:
- the likelihood is conditioned on candidate selection;
- there is an abstention option and follow-up ranking;
- the method is validated against independent survey labels.
I also show that the joint coupling helps calibration, not ranking.

**"How do you know it works on real stars?"**
On real data I have shown the orbit pipeline (BH3, Gaia-4). I also ran a pre-registered DR3 survey test, which returned an honest null on its pre-registered metric and a clear diagnosis of why. The DR3 survey test and the DR4 blind test are the real-data checks, and their success criteria were fixed in advance.

**"Couldn't you have tuned it to your labels?"**
- The labels are sealed and only their hash is public.
- Objects whose data I had seen (Gaia-4) are excluded.
- Thresholds were set on simulated validation data and kept unchanged on held-out data.

**"Why not just use RV scatter from surveys?"**
For a blended twin, the line centroid moves like the photocentre, so the RV scatter mimics a planet. Only line splitting or broadening is independent evidence.

**"What can't your method do?"**
For faint stars without RVS epochs and with large CMD scatter, a planet host with a wide companion is indistinguishable from an impostor. GAIA-FP says "ambiguous" there.

**"What did AI do vs. you?"**
AI tools helped draft code and search the literature, and this is disclosed. You must be able to derive a0 = a_rel(B − β)ϖ, explain the EM prior and walk through `joint_lr.py` line by line.

## Reproducibility

- `pip install -r requirements.txt`
- `./run_all.sh` for simulations
- `python -m pytest tests` for unit tests
- `python tools/fetch_realdata.py` downloads every public real-data table (queries as in `tools/ingest_queries.md`; provenance is written to `realdata/PROVENANCE.md`). Then run `cd src && python dr3_study.py`.
- `python src/report.py <scored.csv> --label "REAL DATA: Gaia DR3"` writes the per-candidate evidence report.
- Test suite: 18 tests, including an end-to-end run of the DR3 study on synthetic fixtures; all pass (9 Oct 2026).


## Answer to "what does it add beyond CMD?" (real data, pre-registered, 9 Oct 2026)
- On 1927 Gaia DR3 binaries with physical light labels, adding the RVS line width to the CMD raises AUC from 0.732 to 0.800 (ΔAUC +0.068 [+0.042, +0.095]).
- **Honest caveat:** a simple sum of the two signals does as well. The physics-based broadening model failed on real data (a selection effect), and that failure was found and reported before DR4.
