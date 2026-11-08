# Ablation supplementary sensitivity: EM regularization and top-k retrieval

**Exploratory only. The registered C=1 model remains primary; this sweep is not a hyperparameter-selection exercise.**

## EM prior regularization sweep

| C | Mean prior π | Median prior π | SB2 PU-proxy AUC | Fraction with P ≥ 0.85 |
|---:|---:|---:|---:|---:|
| 0.01 | 0.916 | 0.920 | 0.697 | 0.889 |
| 0.03 | 0.923 | 0.934 | 0.679 | 0.901 |
| 0.1 | 0.932 | 0.951 | 0.663 | 0.906 |
| 0.3 | 0.938 | 0.960 | 0.651 | 0.907 |
| 1 | 0.940 | 0.965 | 0.643 | 0.909 |
| 3 | 0.941 | 0.967 | 0.641 | 0.910 |
| 10 | 0.941 | 0.968 | 0.641 | 0.910 |

## Top-k known-SB2 retrieval

| Top fraction | k | Variant | Known SB2 matches captured | Recall of 16 | Enrichment vs full sample |
|---:|---:|---|---:|---:|---:|
| 0.5% | 11 | FULL_joint_EM_C1 | 1 | 0.062 | 11.94× |
| 0.5% | 11 | joint_fixed_prior_pi0.3 | 1 | 0.062 | 11.94× |
| 0.5% | 11 | CMD_marginal_EM_C1 | 1 | 0.062 | 11.94× |
| 0.5% | 11 | CMD_marginal_fixed_prior_pi0.3 | 1 | 0.062 | 11.94× |
| 0.5% | 11 | B2_CMD_only | 0 | 0.000 | 0.00× |
| 1.0% | 22 | FULL_joint_EM_C1 | 1 | 0.062 | 5.97× |
| 1.0% | 22 | joint_fixed_prior_pi0.3 | 1 | 0.062 | 5.97× |
| 1.0% | 22 | CMD_marginal_EM_C1 | 1 | 0.062 | 5.97× |
| 1.0% | 22 | CMD_marginal_fixed_prior_pi0.3 | 1 | 0.062 | 5.97× |
| 1.0% | 22 | B2_CMD_only | 2 | 0.125 | 11.94× |
| 2.0% | 43 | FULL_joint_EM_C1 | 1 | 0.062 | 3.06× |
| 2.0% | 43 | joint_fixed_prior_pi0.3 | 1 | 0.062 | 3.06× |
| 2.0% | 43 | CMD_marginal_EM_C1 | 1 | 0.062 | 3.06× |
| 2.0% | 43 | CMD_marginal_fixed_prior_pi0.3 | 1 | 0.062 | 3.06× |
| 2.0% | 43 | B2_CMD_only | 3 | 0.188 | 9.17× |
| 5.0% | 106 | FULL_joint_EM_C1 | 3 | 0.188 | 3.72× |
| 5.0% | 106 | joint_fixed_prior_pi0.3 | 3 | 0.188 | 3.72× |
| 5.0% | 106 | CMD_marginal_EM_C1 | 2 | 0.125 | 2.48× |
| 5.0% | 106 | CMD_marginal_fixed_prior_pi0.3 | 3 | 0.188 | 3.72× |
| 5.0% | 106 | B2_CMD_only | 4 | 0.250 | 4.96× |
| 10.0% | 211 | FULL_joint_EM_C1 | 4 | 0.250 | 2.49× |
| 10.0% | 211 | joint_fixed_prior_pi0.3 | 4 | 0.250 | 2.49× |
| 10.0% | 211 | CMD_marginal_EM_C1 | 4 | 0.250 | 2.49× |
| 10.0% | 211 | CMD_marginal_fixed_prior_pi0.3 | 5 | 0.312 | 3.11× |
| 10.0% | 211 | B2_CMD_only | 6 | 0.375 | 3.74× |
| 20.0% | 421 | FULL_joint_EM_C1 | 5 | 0.312 | 1.56× |
| 20.0% | 421 | joint_fixed_prior_pi0.3 | 8 | 0.500 | 2.50× |
| 20.0% | 421 | CMD_marginal_EM_C1 | 7 | 0.438 | 2.18× |
| 20.0% | 421 | CMD_marginal_fixed_prior_pi0.3 | 10 | 0.625 | 3.12× |
| 20.0% | 421 | B2_CMD_only | 6 | 0.375 | 1.87× |

## Interpretation

- C=1 remains the registered primary. The grid is a sensitivity display, not permission to choose the C with the highest AUC after seeing labels.
- At a constant π, posterior is a monotone transform of the likelihood ratio; changing the constant prior alone cannot improve AUC. Learned covariate-dependent π can alter rankings.
- Top-k retrieval avoids treating every non-SB2 as a confirmed negative, but still only measures recovery of known catalogue matches.
