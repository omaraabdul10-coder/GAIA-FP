# Epoch-RVS phase component — synthetic injection/recovery ablation

**Status: completed synthetic mechanism test; NOT real Gaia validation.**

Each scenario has 3 independent data/split seeds, 1000 objects per class per replicate, a 70/30 stratified split, and 500 paired stratified bootstrap replicates per run.
Known luminous-binary injections follow the project A6 SB1/SB2 rejection rule. The scoring ephemeris is perturbed (P 1%, e 0.05, T0 0.02P, omega 10°). Standardized logistic regression (C=1) compares CMD-only, RVS-phase-only, CMD+RVS-phase, and a phase-scrambled negative control.

| Epochs | RV error (km/s) | Mean CMD AUC | Mean RVS phase AUC | Mean CMD + phase AUC | Mean scrambled AUC | Mean ΔAUC vs CMD | Replicates with CI > 0 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 2.0 | 0.685 | 0.772 | 0.802 | 0.683 | +0.116 | 3/3 |
| 20 | 4.0 | 0.703 | 0.696 | 0.757 | 0.704 | +0.054 | 2/3 |
| 20 | 8.0 | 0.683 | 0.607 | 0.709 | 0.684 | +0.026 | 3/3 |
| 40 | 2.0 | 0.691 | 0.811 | 0.835 | 0.691 | +0.145 | 3/3 |
| 40 | 4.0 | 0.672 | 0.754 | 0.786 | 0.671 | +0.114 | 3/3 |
| 40 | 8.0 | 0.720 | 0.645 | 0.751 | 0.718 | +0.031 | 3/3 |

## Interpretation

- Synthetic positive injections apply the exact A6 rule in `src/rvs_predict.py`: remove systems with q^n ≥0.2 AND K_sum(1+e) ≥30 km/s. Here q^n is the line-flux ratio, not the companion flux fraction q^n/(1+q^n).
- This tests mechanism recovery under the specified simulation assumptions; it is not evidence that real Gaia epoch-RVS widths carry the same signal.
- The phase-scrambled control tests whether the information depends on correct epoch/orbit alignment.
- DR3 empirical ablation remains limited to astrometric/CMD likelihood and population prior. Empirical DR4 RVS ablation requires released epoch rows and validated units.
- Label all numbers synthetic; never merge them with real-DR3 AUC results.

Reproduce: `PYTHONPATH=src python tools/qa_audits/run_rvs_phase_injection_ablation.py`
