# GAIA-FP — Master research audit and close-out (3 November 2026)

## Executive conclusion

GAIA-FP is a substantial, reproducible DR3 development study and a prepared DR4 evaluation framework. It is **not yet a validated compact-companion classifier**. The corrected H10 comparison does not support the claim that the physical S1 score beats the stronger B2+VB empirical baseline. The 95-object dynamical subset is highly selected and cannot be transported to the Gaia population. Survey SB2 and APOGEE results are useful partial external checks, but the available positive-control sample is small and APOGEE RV variability does not distinguish the H10 classes. GALAH/LAMOST epoch-RV and the planned DR4 blind test remain unavailable.

The project's defensible contribution is therefore a physically motivated false-positive assessment framework, an auditable DR3 development analysis, and a pre-registered route to an independent DR4 test — not a demonstrated improvement over the strongest existing baseline and not a discovery/confirmation of dark companions.

## Evidence provenance convention

- **Project artifact:** contained in the supplied GAIA-FP QA2 archive and inspected in this session.
- **Independent audit report:** figures below are taken from the user's supplied `GAIAFP_P1_AUDIT_20261101T144221Z/FINAL_RESEARCH_AUDIT.md` summary; that separate audit directory was not present as a mounted project folder in this session, so these figures are not described as newly recomputed here.
- **This-session verification:** code or tests actually executed in the current environment are identified explicitly.
- **Blocked:** cannot be completed without missing catalogue rows, a live archive export, or Gaia DR4.

## 1. Corrected H10 model comparison

The corrected H10 comparison uses 1,926 labelled objects (841 luminous-positive and 1,085 dark-consistent-negative), according to the independent audit summary.

| Score | AUC |
|---|---:|
| B2 (CMD baseline) | 0.7318 |
| VB (empirical line-width score) | 0.7550 |
| B2+VB (stronger additive baseline) | 0.7957 |
| S1, corrected c=1 | 0.7764 |
| S2 | 0.8324 |

Corrected S1 minus B2 is +0.04446, 95% CI [+0.03340, +0.05510]. Corrected S1 minus B2+VB is −0.01932, 95% CI [−0.03149, −0.00747]. Thus S1 improves on B2 alone but is statistically worse than B2+VB in this comparison. S2 is not a clean independent predictive comparison because `a0` participates in the construction of the dynamical labels.

The old `S1` field in `results/mechanism_scored.csv` was generated before the period-unit erratum. It is now renamed `S1_pre_erratum_DO_NOT_USE`; the exact original file is preserved as `results/mechanism_scored_pre_erratum_original.csv`. The corrected H10 result is separately documented in `results/erratum_k_units.json`. Do not substitute the retired field into tables, figures, rankings, or claims.

## 2. Scoring coverage in the 22,127-object audit population

According to the independent audit summary:

- CMD-based scores cover 17,211 / 22,127 objects (77.8%).
- VB, S1 and B2+VB cover 9,372 / 22,127 objects (42.4%).
- The primary missing input is `vbroad` for 12,755 objects. No imputation or substitute is authorized by this audit.

The 22,127-object scored table and its source ID list were not included in the project archive inspected in this session. A Gaia Archive export specification and validator are supplied separately; no missing rows have been fabricated.

## 3. S1 incremental value and model redundancy

The independent audit summary reports:

- Spearman rank correlation of S1 with B2+VB: 0.87.
- R² for rank(S1) explained by rank(B2)+rank(VB): 0.874.
- In exploratory cross-validated logistic regression, adding S1 to B2 and VB lowered AUC by 0.0078 [−0.0124, −0.0033].

These are exploratory results, not a registered confirmatory test. They are consistent with S1 being largely redundant with the stronger baseline in the current labelled sample.

## 4. The 95-object dynamical subset

The independent audit reports that the 95 objects are not a random sample: they are selected by an implied-companion-mass threshold below 80 Jupiter masses. The approximate mass relation almost perfectly reconstructs the selection (AUC 0.9998); it selects 94 objects, 89 of which are in the 95-object subset. Within the 95, 42 are labelled luminous-consistent and only 2 dark-consistent; the remainder are indeterminate.

This is a selection-defined, impostor-rich tail, not a representative validation sample. Any reported sensitivity, specificity, recall, enrichment, or label stability must be explicitly conditional on this selected subset. It must not be generalized to the full Gaia candidate population.

The propensity analysis in the independent audit found poor common support: 93% of non-selected objects had propensity below the minimum selected-object propensity; weighted effective sample size was about 23/95; maximum standardized difference decreased from 1.69 to 1.35 but remained large. Population transport is not identified by these weights.

## 5. Other data checks

### SB2 positive controls

The project reports 2,102 candidates crossmatched against APOGEE, GALAH and LAMOST SB2 catalogues, with 16 positive matches (13 APOGEE, 2 GALAH, 1 LAMOST). On the principal score, 14 were labelled likely impostor and 2 ambiguous; none likely substellar. The 2,086 unmatched objects are **unlabelled**, not confirmed negatives. Therefore specificity, precision, and false-positive rate cannot be inferred from this crossmatch.

A post-hoc CMD-marginal fixed-prior challenger placed 10/16 positives in the top 20% (3.12× random-ranking enrichment; Holm-adjusted p about 0.00118, per the independent audit). This is exploratory, uses the same 16 positives, and requires untouched positive controls before being promoted to a primary model.

### APOGEE epoch RV

The independent audit reports 622 raw visit rows, 351 accepted visits, and 46 objects with at least three integer-MJD epochs (18 H10-positive, 28 H10-negative). Nominal constant-RV testing found 42/46 variable; under a 0.5 km/s uncertainty floor, 30/46 remained variable (12/18 vs 18/28), with Fisher p=1.0. The data show RV variability but do not separate the H10 classes or establish a compact companion.

A 414,000-injection cadence-summary-matched proxy was run, but used random times within each baseline rather than the exact 351 visit timestamps. It is not an exact-cadence injection-recovery experiment.

### GALAH and LAMOST

Epoch-RV ingestion pipelines and fixture tests exist. Real per-epoch data were not acquired in the audited environment. Catalogue crossmatches are not substitutes for real epoch-RV analysis.

### Null calibration

The independent audit reports 10,000 synthetic null iterations: AUC rejection 490/10,000 (4.90%) and paired-ΔAUC rejection 502/10,000 (5.02%); KS p-values 0.475 and 0.714. These validate calibration only under the chosen synthetic null generators, not the real Gaia population's false-positive rate.

### H11 controls

A 2,102-object matched DR3 control set was regenerated and its hash matched the archived file. The matching is balanced on observed covariates, but the 80–300 Jupiter-mass interval is an approximate mass proxy, not a set of dynamically confirmed single-star negatives and not a DR4 result.

## 6. Selection and lineage issues

Keep the following as separate lineage questions:

1. `2,672 - 1,926 = 746` duplicate rows in an earlier H10 source file. These are excess rows, not 746 distinct bad stars; the original 2,672-row source file is absent from the current archive.
2. A different 746-ID mismatch between the 71,759-row raw NSS extract and the 10,118-row mechanism scoring table. These products used different upstream source tables and filters; it is not established that this is a corruption or release mismatch.
3. Of 95 dynamically labelled objects, 62 appear in `mechanism_scored.csv` and 33 do not. The upstream scored source needed to identify each missing object's exact filter reason is absent.

The independent audit also reports that the 22,127-object population is not a superset of H10: 746 H10 objects have parallax below 2 mas, and the H10 `dm > -2` cut removes 4,536 objects (20.5%), disproportionately affecting over-luminous systems.

## 7. Synthetic phase injection-recovery

The earlier simulation grid reports higher phase-score recovery with more epochs and lower RV errors. The project documentation itself identifies a mismatch between the older `q**n >= 0.2` condition and the total-light-fraction condition `q**n/(1+q**n) >= 0.2`. This has now been reconciled in the DR4 v3.2 implementation: A6 uses the registered secondary-to-primary light ratio `ell=q**n >= 0.2`, not `beta=ell/(1+ell)`. See A28 and the deviation log. Synthetic uniform epochs remain distinct from Gaia scanning-law epochs.

## 8. Code and test verification in this session

The supplied archive contains a 112-test pre-existing suite. Two additional regression tests were added in this session: one for the A6 light-ratio definition and one ensuring that the pre-erratum S1 column is retired in mechanism outputs. All 114 tests passed when run file-by-file. The full monolithic `pytest -q` invocation timed out in this environment, so do not report a single clean monolithic run. Individual test-file results are in `TEST_RECONCILIATION_2026-11-03.md`.

Specific code changes:

- `src/rvs_v32.py`: A6 now applies `q**n >= 0.2` and the velocity-separation threshold; it no longer substitutes `beta >= 0.2`.
- `tests/test_rvs_v32.py`: boundary-case regression test added.
- `PREREG_AMENDMENT_v0.6_DRAFT.md`: A28 implementation clarification added before DR4.
- `DEVIATIONS_v0.6.md`: dated record added.
- `src/mechanism.py`: legacy S1 output is renamed `S1_pre_erratum_DO_NOT_USE`.
- `results/mechanism_scored.csv`: unsafe S1 header retired; original exact file preserved.

## 9. External blockers and final status

| Work item | Status | What is needed |
|---|---|---|
| DR3 development analyses and local model comparisons | DONE / audited | Keep limitations and source provenance visible |
| Corrected H10 S1 vs B2+VB | DONE as a reported analysis | Do not claim S1 superiority |
| Retire pre-erratum S1 column | DONE in this package | Use corrected H10 result only with its own provenance |
| A6 v3.2 code/prereg reconciliation | DONE in this package | Re-run frozen DR4 runner tests on release day |
| 22,127-object full-population export | BLOCKED | Upload ID list and execute Gaia Archive query outside sandbox |
| Full-population corrected rescoring | BLOCKED | Complete export plus audited scoring pipeline |
| GALAH epoch-RV | BLOCKED | Real visit-level measurements and IDs |
| LAMOST epoch-RV | BLOCKED | Real visit-level measurements and IDs |
| Exact APOGEE cadence injection | PARTIAL | Original 351 visit timestamps |
| Per-ID 746/33 lineage | PARTIAL | Missing upstream source tables and original extract |
| Independent external SB2 validation | PARTIAL | Larger untouched positive-control sample and validated negatives |
| Gaia DR4 blind evaluation | NOT YET CONDUCTED | DR4 release, schema validation, sealed blind protocol |
| Prospective/independent compact-object confirmation | BLOCKED | Independent dynamical/spectroscopic orbit evidence |

## 10. Claim language recommended for ISEF

**Defensible:** “We developed and audited a physically motivated framework for assessing luminous-companion contamination in Gaia DR3 compact-companion candidates, and prepared a pre-registered Gaia DR4 evaluation. In the corrected DR3 labelled sample, our physical S1 score outperformed CMD-only B2 but did not outperform the stronger B2+VB baseline. Selected dynamical and survey crossmatches provide partial, non-representative checks; independent DR4 validation remains pending.”

**Do not claim:** confirmed black-hole/neutron-star detections; population-wide false-positive rate; S1 superiority over B2+VB; representative validation from the 95-object sample; confirmed negatives among SB2-unmatched sources; real GALAH/LAMOST epoch-RV results; or a completed DR4 blind test.
