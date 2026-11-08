# DR3 ablation with v3.2 label-free prior selection

**Exploratory bridge analysis. The original DR3 v3.1/C=1 result is preserved. The prior complexity is selected without reading SB2 labels.**

The v3.2 rule selected C=0.3 for FULL and C=1 for CMD-marginal. The SB2 proxy labels are used only for the final diagnostic evaluation.

| Variant | AUC | 95% percentile CI |
|---|---:|---:|
| FULL_v32_prior_select | 0.651 | [0.497, 0.789] |
| CMD_marginal_v32_prior_select | 0.726 | [0.633, 0.819] |
| FULL_fixed_pi_0.3 | 0.722 | [0.584, 0.832] |
| CMD_marginal_fixed_pi_0.3 | 0.733 | [0.614, 0.839] |

## Paired differences

| Contrast | ΔAUC (FULL − variant) | 95% CI |
|---|---:|---:|
| CMD_marginal_v32_prior_select | -0.075 | [-0.219, +0.048] |
| FULL_fixed_pi_0.3 | -0.071 | [-0.173, +0.015] |
| CMD_marginal_fixed_pi_0.3 | -0.082 | [-0.168, -0.001] |

## Interpretation

- The v3.2 C-selection rule optimizes held-out unlabelled mixture likelihood, not SB2 retrieval AUC. Its choice cannot be described as an AUC-tuned improvement.
- This diagnostic does not reverse the real-DR3 ablation finding: the CMD-marginal score remains at least as high as the fully conditioned score on this SB2 positive-unlabelled proxy.
- Only 16 positives are independently labelled and 2,086 rows remain unlabelled; do not call these AUCs definitive classification performance.
