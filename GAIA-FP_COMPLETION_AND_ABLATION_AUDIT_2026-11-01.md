# GAIA-FP — completion and extended ablation audit

**Audit date:** 1 November 2026  
**Scope:** finish the parts reproducibly possible from the archived DR3 snapshot; correct the ablation analysis without label-driven model selection; prepare the remaining epoch-RV acquisition route.

## Executive result

The archived work now has three distinct evidence layers and they must remain separate:

1. **Real DR3 catalogue evidence:** published SB2 catalogue matches, 95-object AstroSpectroSB1 characterization, and the archived H10 `vbroad` comparison.
2. **Real-DR3 component ablation on a positive–unlabelled proxy:** a 2×2 ablation of conditional astrometric/CMD evidence and the population prior. It does not show the full C=1 model winning on the 16-SB2 proxy.
3. **Synthetic epoch-RVS injection–recovery:** after correcting the code to apply the exact A6 SB1 rejection rule and repeating each cadence/noise setting across three independent random seeds, the phase-locked line-width feature adds discrimination in all six scenario means. In 17/18 replicate runs, the paired-bootstrap interval for ΔAUC is above zero. This is a mechanism test, not Gaia DR3/DR4 evidence.

No analysis has been tuned to force a favourable result. Frozen v3.1/C=1 outputs remain intact; v3.2 prior-selection and phase-RVS injection results are marked supplementary.

## Status of the previously partial items

| Item | Now available | Honest status |
|---|---|---|
| Independent spectroscopic cross-match | Local APOGEE/GALAH/LAMOST SB2 cross-match rerun and exact flag reconciliation for all 2,102 candidates; 16 unique SB2 matches | Local catalogue cross-match complete; general epoch-RV variability still pending external rows |
| Independent epoch-RV cross-match | 22 chunked GALAH DR3 ADQL queries, a resumable downloader, quality-filtered summarizer and synthetic parser self-test | Acquisition pipeline ready; **no real epoch rows downloaded** in this runtime |
| Injection–recovery | 18 A6-filtered synthetic epoch-RVS runs (six cadence/noise settings × three independent seeds), held-out test data, 500 paired bootstrap replicates per run and phase-scrambled negative controls | Synthetic injection–recovery complete; empirical injection–recovery still requires real epoch observations |
| Ablation study | Real-DR3 2×2 ablation (a0-conditioning × population prior), C-sensitivity, top-k retrieval, v3.2 label-free prior-selection bridge; A6-filtered synthetic RVS-phase ablation | Astrometric/CMD/prior ablation complete on limited SB2 proxy; RVS-phase ablation complete only as a synthetic mechanism test |
| Baseline comparison | H10 `vbroad` S1 vs CMD-only and stronger CMD+VB comparator reconciled; 95-object classifier comparison reproduced from archived results | Archived comparisons reconciled; H10 raw 33,463-row input is not in this package, so not rerun from raw rows here |
| Real false-positive characterization | 95 AstroSpectroSB1 objects; 50,000-draw sensitivity at seeds 0/1/17; object-level export | Local characterization completed for this selected subset; not population-representative |

## 1. Independent SB2 catalogue cross-match

The full candidate table has 2,102 unique source IDs. The independent catalogue checks reproduce:

- LAMOST-MRS SB2: 1 exact Gaia DR3 ID match.
- GALAH FGK SB2: 2 Gaia DR2-ID matches under the stored DR3–DR2 neighbourhood mapping and the 1,000 mas guard.
- APOGEE SB2: 13 unique positional matches after Gaia 2016→J2000 proper-motion propagation, a 2″ radius and ambiguity exclusion.
- Union: 16 unique positive matches, with no overlap between these three survey subsets. The remaining 2,086 are **unlabelled**, not confirmed negatives.

A 200-realisation local offset control returned a median of zero chance matches (empirical 95% range 0–0). This is a local-density diagnostic, not a formal posterior match probability.

## 2. Epoch-RV data route

The GALAH DR3 catalogue documentation confirms that the per-spectrum table contains 678,423 spectra and uses `sobject_id` (`GALAH`) as the within-survey join key. The RV value-added table contains per-spectrum `rv_galah`, its uncertainty, method flag, HJD and MJD-local fields. Method flags 0 and 1 correspond to GALAH-derived RVs; flags 2 and 4 are Gaia-DR2 fallback and no-method entries, respectively. The official schema and VizieR ReadMe are cited in the companion report/protocol.

The following have been added:

- `results/qa2/partial_completion/galah_adql/galah_epoch_rv_chunk_01.adql` … `_22.adql` — 22 candidate-ID chunks.
- `tools/qa_audits/download_galah_epoch_rv.py` — resumable TAP CSV downloader (run from a machine with catalogue network access).
- `tools/qa_audits/summarize_galah_epoch_rv.py` — continuous epoch-RV diagnostics; does not impose an unregistered binary cutoff.
- `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md` — acquisition and quality rules.

The parser self-test passed. The actual external VizieR response could not be retrieved from this execution environment because its DNS resolver could not resolve the catalogue host. Hence there are no observed epoch-RV match counts or RV-variable-object claims.

## 3. Real H10 baseline comparison

On the archived post-unit-fix H10 subset (`n=1,927`; 841 luminous-positive and 1,086 dark-consistent-negative):

- CMD-only B2 AUC = **0.732** [0.708, 0.754].
- Physical `vbroad` alone AUC = **0.755** [0.733, 0.776].
- S1 (CMD + physical `vbroad` likelihood) AUC = **0.776** [0.755, 0.797].
- Registered S1−B2 paired ΔAUC = **+0.044** [+0.033, +0.055].
- Stronger simple B2+standardized-VB additive baseline AUC = **0.796**; S1−(B2+VB) = **−0.019** [−0.031, −0.007].

Therefore the spectroscopic broadening feature helps relative to CMD-only, but the more complex S1 model does not beat the stronger simple additive comparator. This is `vbroad`, not the time/phase-locked epoch-RVS feature.

The corrected H10 S1 result is 0.776, not the earlier pre-erratum 0.800. The old result used a period-unit error in the K-sum calculation and is not authoritative. This is an empirical feature-modality ablation: adding physical `vbroad` to CMD-only improves AUC by +0.044 [ +0.033, +0.055 ]. It is a genuine positive result against the registered CMD-only comparator, while the stronger additive CMD+VB comparator and the exploratory shared-astrometry comparators remain higher. These H10 archived values were reconciled, not recomputed from raw rows in this runtime.

## 4. Real-DR3 astrometric/CMD/prior ablation

The 2×2 design keeps the same 2,102 candidates and the same SB2 proxy labels:

- FULL: frozen conditional `p(ΔM_G | a0, H_t) / p(ΔM_G | H_p)` evidence + label-free EM-C1 prior.
- Joint evidence + fixed π=0.3: removes covariate-dependent prior variation.
- CMD-marginal evidence + EM-C1: removes `a0`-conditioning from the evidence likelihood.
- CMD-marginal + fixed π=0.3: removes both elements.

The original frozen v3.1/C=1 ablation results remain:

| Variant | AUC | 95% percentile CI |
|---|---:|---:|
| FULL joint + EM-C1 | 0.643 | [0.488, 0.786] |
| Joint + fixed π=0.3 | 0.722 | [0.586, 0.837] |
| CMD-marginal + EM-C1 | 0.738 | [0.634, 0.835] |
| CMD-marginal + fixed π=0.3 | 0.733 | [0.609, 0.844] |
| B2 CMD-only | 0.694 | [0.571, 0.812] |

The full model reproduced the archived frozen posterior to maximum absolute difference `7.77e−16`. The 20,000-resample paired intervals are conditional on these fitted scores; they do not account for every source of model-selection uncertainty.

### Prior-sensitivity audit

The registered `C=1` primary was not replaced. A supplementary grid `C={0.01,0.03,0.1,0.3,1,3,10}` showed mean EM prior from 0.916 to 0.941 and SB2 positive–unlabelled AUC from 0.697 down to 0.641. The v3.2 label-free held-out mixture-likelihood rule selected `C=0.3` for FULL (not by using SB2 labels); the resulting FULL AUC was 0.651 [0.497, 0.789]. For CMD-marginal it selected `C=1`, AUC 0.726 [0.633, 0.819]. This rule therefore does not reverse the DR3 proxy finding.

### Top-k check

The top-k output is included because most rows are unlabelled and ordinary false-positive rates cannot be estimated. In the top 5% (106 candidates), FULL retrieved 3/16 known SB2 matches; B2 CMD-only retrieved 4/16. At the 0.85 score threshold, FULL recalled 14/16 but flagged 1,911/2,102 candidates (91%). This is not a useful high-specificity operating point. None of these proxy metrics should be described as precision against verified negatives.

## 5. Epoch-RVS phase injection–recovery ablation (synthetic only)

The first synthetic version was corrected before final reporting: the project A6 SB1 filter in `src/rvs_predict.py` is **`q^n >= 0.2 AND K_sum*(1+e) >= 30 km/s`**. This uses the line-flux ratio `q^n`, not the companion flux fraction `q^n/(1+q^n)`. The initial draft had conflated those two quantities; its numbers are superseded and must not be quoted.

The corrected experiment generated 1,000 SB1-selected binary injections and 1,000 single-star/planet nulls per replicate; six cadence/noise settings (20 or 40 epochs; 2, 4 or 8 km/s width error); three independent data/split seeds per setting; 70/30 stratified train/test split; 500 paired bootstrap replicates per run. The scoring ephemeris was perturbed (P 1%, e 0.05, T0 0.02P, ω 10°). Standardized logistic regression C=1 compared CMD-only, RVS-phase-only, CMD+RVS-phase, and phase-scrambled negative-control scores.

| Epochs | Width error (km/s) | Mean CMD AUC | Mean RVS phase AUC | Mean CMD + phase AUC | Mean phase-scrambled AUC | Mean ΔAUC vs CMD | Runs with paired-bootstrap CI > 0 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 2 | 0.685 | 0.772 | 0.802 | 0.683 | +0.116 | 3/3 |
| 20 | 4 | 0.703 | 0.696 | 0.757 | 0.704 | +0.054 | 2/3 |
| 20 | 8 | 0.683 | 0.607 | 0.709 | 0.684 | +0.026 | 3/3 |
| 40 | 2 | 0.691 | 0.811 | 0.835 | 0.691 | +0.145 | 3/3 |
| 40 | 4 | 0.672 | 0.754 | 0.786 | 0.671 | +0.114 | 3/3 |
| 40 | 8 | 0.720 | 0.645 | 0.751 | 0.718 | +0.031 | 3/3 |

Across all 18 replicate runs, mean ΔAUC is +0.081 (range +0.020 to +0.156); 17/18 paired-bootstrap intervals are above zero. The phase-scrambled control remains close to CMD-only, consistent with the gain depending on phase alignment rather than merely adding a generic extra feature.

**Interpretation limit:** this supports the mechanism under the assumed injected line-width law and simulated cadence/noise/orbit-error distributions. It does not show that real Gaia DR4 epoch-RVS widths have these properties, that the 11 km/s instrumental floor is accurate for the selected stars, or that the current full GAIA-FP model beats a real-data baseline. The synthetic AUCs must never be merged with the real-DR3 AUC results.

## 6. Independent 95-object characterization

The selected AstroSpectroSB1 subset remains 42 historical impostors, 2 dark-compatible and 51 undetermined under the registered 400-draw primary. In the supplementary 50,000-draw seeds 0/1/17, 94/95 object labels were stable; one object was seed-sensitive. The group statistics and all 95 row-level outputs are retained in `results/qa2/partial_completion/astrospectro_95_object_characterization.csv`.

This characterization is complete for the supplied 95-object subset, not for the full candidate population. Only two dark-compatible labels exist, so comparisons of that class are descriptive.

## 7. Remaining external blockers

1. Run `tools/qa_audits/download_galah_epoch_rv.py` from an internet-connected environment and then run `summarize_galah_epoch_rv.py` on the resulting CSV. Until then, the independent epoch-RV cross-match is not empirically complete.
2. The raw H10 33,463-row D3 catalogue and field input are absent from this package; the baseline report is reconciled to saved post-erratum output, not recomputed from raw observations here.
3. Real Gaia DR4 is not yet in the archive on this audit date; no DR4 empirical schema, epoch-RVS or full-model ablation can be claimed.

## Reproducibility commands

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py
PYTHONPATH=src python tools/qa_audits/run_ablation_dr3.py
PYTHONPATH=src python tools/qa_audits/audit_ablation_prior_sensitivity.py
PYTHONPATH=src python tools/qa_audits/run_ablation_v32_priorselect.py
PYTHONPATH=src python tools/qa_audits/run_rvs_phase_injection_ablation.py
PYTHONPATH=src python tools/qa_audits/summarize_galah_epoch_rv.py --selftest
```

## Artifacts

- Real DR3 ablation: `results/qa2/partial_completion/ablation_dr3_component_results.json`, `ablation_dr3_candidate_scores.csv`, `ABLATION_DR3_COMPONENT_REPORT_2026-11-01.md`.
- Prior sensitivity: `ablation_prior_sensitivity.json`, `ABLATION_PRIOR_SENSITIVITY_2026-11-01.md`.
- v3.2 prior-selection bridge: `ablation_v32_priorselect.json`, `ABLATION_V32_PRIORSELECT_2026-11-01.md`.
- Synthetic RVS injection: `rvs_phase_injection_ablation.json`, `RVS_PHASE_INJECTION_ABLATION_2026-11-01.md`.
- Epoch-RV acquisition: `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md`, `tools/qa_audits/download_galah_epoch_rv.py`, `tools/qa_audits/summarize_galah_epoch_rv.py`, and 22 ADQL files.
- Real 95-object outputs and survey cross-match audit: `astrospectro_characterization.json`, `astrospectro_95_object_characterization.csv`, `rv_crossmatch_audit.json`, `candidate_survey_crossmatch_audit.csv`.
