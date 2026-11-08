# Research audit of GAIA-FP (9 October 2026, 04:30 UTC+4)

**Method.** I re-read the source, the commit history (16 commits as of this audit), the results and the pre-registration. Each claim below is classified by the evidence behind it.

## 1. What actually works, tested on REAL data

| Item | Evidence | Status |
|---|---|---|
| Orbit pipeline (`gaia_orbit.py`, `fit_real.py`, `mcmc_orbit.py`) | Gaia DR4 **pre-release** epoch astrometry of Gaia BH3: P, e and a0 within 1σ of the published solution; parallax off by 1.6σ | Works on real data, n = 2 systems |
| Gaia-4b recovery | P = 579 ± 4 d, Δχ² = 1683; e biased high (0.41 vs 0.34) | Works; known low-S/N bias in e |
| Injection–recovery on the real Gaia-4 cadence | 40 trials per cell; FAP from 400 null runs | Real cadence, simulated signals |
| DR3 real-data test (`dr3_study.py`) | Run 9 Oct 2026 on 2102 real candidates (`RESULTS_DR3.md`). P1 underpowered (1 positive); P2 AUC 0.643 [0.487, 0.788], not significant; does not beat the CMD-only baseline | Real result, reported as pre-registered. EM prior near 0.94, independently supported by AstroSpectroSB1 dynamics (42/44 determined objects are impostors); amendment v0.4 drafted |

## 2. Tested only on SIMULATED data (Lammers & Winn mocks plus our observation model)

These items are the classification AUCs, the stress tests, the tournament, contamination recovery, the abstention operating point, EIG follow-up ranking and the identifiability maps.

**None of these numbers may be presented as real-data performance.** The website and README say so; this audit confirms the labelling is correct.

## 3. Overstated, unsupported or leakage-prone claims found, and fixes

| Finding | Severity | Fix |
|---|---|---|
| Gaia-4 was in the sealed label set, but its DR4 pre-release data had been analysed | High (blinding breach) | Excluded from all metrics; disclosed (labels_v2, PREREGISTRATION §5) |
| "76 systems" vs "66" inconsistency | Medium | Corrected to 76 listed / **65 analysed** |
| Site said "real DR4 data" without saying pre-release vs full release | Medium | Data-provenance table added |
| RVS template assumed σ_P = 1%; the mocks have a median of 3.5% | Medium (optimistic) | Per-candidate σ_P (C2) |
| ML baseline advantage came from simulator demographics | Medium (baseline unfair to us, not to ML) | Diagnosed and documented |
| `benchmark.py` loaded the mock catalogues at import, so the real-data pipeline silently depended on simulation files | Medium (software) | Fixed: mocks load only if present |
| Joint a0–CMD coupling was described as a discrimination gain | Medium | Identifiability analysis shows it adds **calibration**, not ranking; wording corrected |
| Novelty of "astrometry + photometry" | High | Bailer-Jones & Kreidberg 2026 already did this; the claim is withdrawn |
| Mass–luminosity table in `dr4_pipeline.py` is approximate | Low (until freeze) | Uses archive m1 when present; isochrones still to do before the freeze |
| Contamination estimator under misspecification | Medium | Criterion failed (X4); reported as a bracket |

## 4. Current scientific contribution (defensible)

1. Calibrated, label-free, per-object impostor probabilities from Gaia observables, with an explicit "ambiguous" output. Validated in simulation, including a held-out DR5 mock set.
2. Quantitative identifiability limits:
   - RVS power maps;
   - planet-host-with-third-light vs twin non-identifiability without RVS;
   - the RV-centroid degeneracy (the qualitative point is already known).
3. Pre-registered blind design with sealed labels.
4. **Done (null on P2, P1 underpowered):** a real-data validation of an astrometric-impostor vetting method against independent survey SB2 catalogues (DR3 now, DR4 confirmatory). We did not find an earlier one in the literature we searched; this is not a claim that none exists.

## 5. Keep / revise / remove

| Item | Decision |
|---|---|
| Orbit pipeline, joint likelihood, EM prior, abstention, EIG ranking, identifiability, pre-registration | **Keep** |
| `fp_score.py` and `combo_*.py` (v0.1 scoring) | Keep only as history |
| Approximate mass–luminosity relation | **Revise** before the freeze |
| H_pw hypothesis | Keep as a *reported alternative* only |
| Any wording implying real-data classification performance | **Remove** wherever it appears |
| Single-number contamination | **Remove** in favour of the bracket |

## 6. Blocker found during this audit

At 04:25 the browser automation (used to query the Gaia archive and VizieR, which this workspace cannot reach directly) hit the account's 5-hour usage limit. The limit resets at about 07:10 (UTC+4).

Done before the block:
- The DR3 candidate count was confirmed on the real archive: **2192** solutions with dark-companion m2 < 80 M_J.
- The VizieR tables were located: APOGEE J/AJ/162/184, GALAH J/A+A/638/A145, LAMOST J/MNRAS/527/521 and J/ApJS/244/27.
- The study was **pre-registered** in `DR3_STUDY_PLAN.md`; its hash is recorded in `DR3_STUDY_PLAN.sha256`.


## Freeze status (9 Oct 2026)
**OSF pre-registration (public, frozen 9 Oct 2026, 08:52 UTC): https://osf.io/n5h4b — DOI [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B).** It freezes PREREGISTRATION.md v0.3, PREREG_AMENDMENT_v0.4.md, the plans, and the SHA-256 of every source file (`FREEZE_MANIFEST.sha256`). A file in this repository is the frozen version if and only if its hash matches the manifest. All 9 archived files were checked against their local SHA-256 after registration.

**Amendment v0.5 (public, registered 10 Oct 2026, 04:43 UTC, before Gaia DR4): https://osf.io/tbjgy — DOI [10.17605/OSF.IO/TBJGY](https://doi.org/10.17605/OSF.IO/TBJGY).** It registers PREREG_AMENDMENT_v0.5.md (A6 SB1 truncation, A7 empirical-primary DR4 RVS score, A8 the H11 DR3→DR4 time-separated test, A9 label limitation), DR3_TO_DR4_PREDICTION_PLAN.md, VBROAD_V2_PLAN.md and `FREEZE_MANIFEST_v0.5.sha256` (SHA-256 1a6bce97…, 56 files, including the frozen DR3 predictions `results/dr3_candidates_scored.csv` 14173467…). All archived hashes were checked against the local files after registration.

