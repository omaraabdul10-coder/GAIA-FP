# GAIA-FP v3 — development results on independent mock catalogues (9 October 2026)

All numbers in this file come from simulations: the Lammers & Winn (2025) DR4 mock catalogues, with our own observation model. They are **not** results on real data. Scripts are in `src/`: `benchmark.py`, `eval_v3.py`, `contam_bins.py`, `rv_degeneracy.py`. Raw outputs are `v3_results.json` and `contamination_bins.json`.

## 1. What changed from v0.1

| Version | Likelihood ratio LR = p(data \| impostor) / p(data \| substellar) |
|---|---|
| v1 | CMD over-luminosity with q ~ U(0.5, 1), plus a generic RVS-width prior z ~ N(U(0,6), 1) |
| v2 | RVS term predicted **per candidate** from physics: astrometric orbit + photometric mass + the star's own RVS cadence and precision → simulated p(z \| H_t) |
| v3 | Astrometric amplitude a0 and CMD over-luminosity share one latent mass ratio q. The G-band mass–luminosity slope n ~ U(2, 6) is marginalised as a nuisance parameter. The blend's photometric mass is converted to the primary mass. LR uses the **conditional** p(ΔM_G \| a0, H): the candidate list is selected on a0, so the a0 marginal must not be double-counted. |
| v3 + EM | Population prior π(x), logistic in (G, log P, e, log d, log M_fit), fitted by expectation–maximisation on the **unlabelled** candidate list. It needs no training labels. |

## 2. Theory result: why Gaia RV centroids cannot unmask a twin, but line widths can

For a blended pair the line-centroid velocity is K_sum·(B − f)·g(t), where B = q/(1+q), f is the RVS-band light fraction, and g(t) = cos(ν+ω) + e cos ω.

The astrometric photocentre implies K_sum·(B − β_G)·g(t).

Therefore the centroid RV reproduces the photocentre motion up to a colour factor of about 0.80–0.90. It carries almost no independent information. The line-width term f(1−f)·(K_sum g)² does **not** cancel, which is why GAIA-FP uses widths. See `rv_degeneracy.py`.

## 3. Calibration of the likelihood ratios

For a correct LR, E_planet[LR] = 1 and E_impostor[1/LR] = 1.

| Version | E_planet[LR] | E_imp[1/LR] |
|---|---|---|
| v1 | 0.88 | 0.31 |
| v2 | 0.91 | 0.23 |
| **v3** | **1.05** | **0.99** |

Only v3 is close to calibrated.

## 4. GAIA-FP vs baselines (CMD scatter 0.30 mag; 3000 planets, 1151 impostors)

| Method | AUC [95% CI] | Impostors rejected at 95% planet retention |
|---|---|---|
| RUWE proxy | 0.518 [0.499, 0.539] | 6% |
| Random | 0.501 | 5% |
| CMD-only physics LR | 0.942 | 74% |
| GAIA-FP v1 | 0.958 | 79% |

RUWE cannot separate the classes: by construction, impostors mimic the planet wobble.

## 5. Stress tests

An ML classifier (gradient boosting) was trained on the train half of the simulator. All methods are evaluated on an independent test half.

Each cell shows AUC / rejection at 95% retention.

| Test | ML trained on simulator | GAIA-FP v3 | GAIA-FP v3 + EM (no labels) |
|---|---|---|---|
| (a) same distribution | 0.979 / 89% | 0.971 / 84% | **0.980 / 91%** |
| (b) demographic shift | 0.976 / 88% | 0.971 / 86% | **0.976 / 89%** |
| (c) CMD scatter 0.45 mag (ML trained at 0.30) | 0.929 / 67% | 0.901 / 56% | **0.949 / 72%** |

GAIA-FP v3 + EM uses **no labelled training data**. It matches a classifier trained on the simulator's own truth, and beats it when real conditions differ from the training assumptions.

A diagnostic shows that most of the ML advantage over v1 came from population demographics of the simulation (AUC 0.83 from demographics alone). On the physical features alone, the physics LR equals ML (0.958 vs 0.953).

## 6. Label-free measurement of contamination

The fraction of impostors among candidates is estimated by EM, without labels.

| True contamination | EM estimate [95% bootstrap CI] | Constant-π EM |
|---|---|---|
| 0.050 | 0.051 [0.044, 0.058] | 0.037 |
| 0.100 | 0.106 [0.093, 0.119] | 0.088 |
| 0.200 | 0.213 [0.199, 0.227] | 0.188 |
| 0.300 | 0.324 [0.305, 0.352] | 0.298 |
| 0.450 | 0.474 [0.448, 0.501] | 0.450 |

Contamination as a function of G magnitude, on a natural mix with 16% contamination:

| G | n | True | Estimate [95% CI] |
|---|---|---|---|
| < 10 | 457 | 0.024 | 0.016 [0.007, 0.026] |
| 10–12 | 833 | 0.054 | 0.062 [0.049, 0.074] |
| 12–14 | 1328 | 0.151 | 0.153 [0.137, 0.170] |
| 14–16 | 834 | 0.323 | 0.342 [0.317, 0.368] |
| > 16 | 123 | 0.407 | 0.546 [0.481, 0.613] (small n; biased) |

## 7. Honest caveats

- **Inherited simulator assumptions.** Everything here inherits the Lammers & Winn simulator: its binary population, its photometry and our own RVS observation model. Real DR4 RVS width precision is unknown until release.
- **Small positive bias.** The heterogeneous EM has a bias of +0.01 to +0.02 in total contamination, and is biased in the faintest bin. The bootstrap CI does not cover the truth at 0.30.
- **Tuned versus physical choices.** The slope range n ∈ [2, 6] was widened after seeing that a fixed n = 4 mis-predicts a0 in the mocks. It is a physically motivated range, but this choice was made during development and is disclosed here. It is frozen before DR4.
- **Labelled-set size.** The labelled real set (labels_v2: 65 analysed = 39 impostors + 26 substellar) is the only test that does not depend on any simulator.
