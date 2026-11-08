# GAIA-FP real-DR3 component ablation (1 Nov 2026)

## Scope
- N=2102; SB2 positives=16; non-SB2 rows=2086 (unlabelled, not verified negatives).
- The SB2 endpoint is therefore a positive-unlabelled proxy. Do not call these AUCs definitive real false-positive classification performance.
- 20,000 paired stratified bootstrap resamples were used for percentile intervals.

## Ablation definitions
- FULL: frozen conditional astrometric-amplitude/CMD likelihood + EM-C1 demographic prior.
- joint + fixed prior: same evidence, but remove learned demographic prior (constant pi=0.3).
- CMD-marginal + EM-C1: remove astrometric a0-conditioning in the evidence likelihood; integrate over q,n without a0.
- CMD-marginal + fixed prior: both changes above.
- B2 CMD-only is context baseline, not a GAIA-FP ablation.

## AUC results
| Variant | AUC | 95% percentile CI | Recall of 16 SB2 at score ≥0.85 |
|---|---:|---:|---:|
| FULL_joint_EM_C1 | 0.643 | [0.488, 0.786] | 14/16 |
| joint_fixed_prior_pi0.3 | 0.722 | [0.586, 0.837] | 4/16 |
| CMD_marginal_EM_C1 | 0.738 | [0.634, 0.835] | 16/16 |
| CMD_marginal_fixed_prior_pi0.3 | 0.733 | [0.609, 0.844] | 4/16 |
| B2_CMD_only | 0.694 | [0.571, 0.812] | 6/16 |

## Paired differences against FULL
| Contrast | ΔAUC (FULL − variant) | 95% percentile CI |
|---|---:|---:|
| joint_fixed_prior_pi0.3 | -0.078 | [-0.191, +0.017] |
| CMD_marginal_EM_C1 | -0.095 | [-0.245, +0.040] |
| CMD_marginal_fixed_prior_pi0.3 | -0.089 | [-0.189, -0.002] |
| B2_CMD_only | -0.050 | [-0.161, +0.055] |

## Interpretation
- Refitting the full pipeline reproduces the frozen posterior to max absolute difference 7.77e-16.
- The full EM prior mean is 0.940; the CMD-marginal EM prior mean is 0.904; fixed prior is 0.300.
- If fixed-prior AUC exceeds the full EM-C1 AUC on this SB2 proxy, that indicates the learned demographic prior may hurt ranking on this particular endpoint; it does not establish fixed prior as universally better.
- If removing a0 conditioning reduces AUC, it is only evidence on this small SB2 proxy, not proof of causal/physical component necessity.
- DR3 has no retrieved epoch-RVS widths, so the phase-locked RVS feature is not empirically ablated here.

## Reproducibility
- Run: `PYTHONPATH=src python tools/qa_audits/run_ablation_dr3.py`
- Machine-readable results: `results/qa2/partial_completion/ablation_dr3_component_results.json`
- Per-object scores: `results/qa2/partial_completion/ablation_dr3_candidate_scores.csv`
- No historical frozen outputs are modified.
