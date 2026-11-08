# H11: DR3 → DR4 time-separated blind test. Predictions frozen now, outcomes measured on DR4

**Written:** 9 Oct 2026, before Gaia DR4 (2 Dec 2026). It will be hashed and registered on OSF as an amendment of [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B). DR4 data do not exist yet, so every outcome below is unknown to the author.

## Question
Which Gaia DR3 astrometric substellar candidates are confirmed by DR4's longer baseline and new data products (epoch astrometry, epoch RVS), and which turn out to be stellar or dissolve? Were GAIA-FP's probabilities, assigned from DR3 alone, **calibrated** for what DR4 reveals?

## Frozen predictions
- **File:** `results/dr3_candidates_scored.csv`, 2102 candidates. Each row has P_impostor (frozen v3.1 scoring with EM prior, C = 1) and a three-way verdict (likely_impostor 1911, ambiguous 174, likely_substellar 17).
- **SHA-256:** `141734677a64942e38fc8512611c7653eaaa024a2d375524cc7f50b40200a7fc`.
- **Baselines frozen in the same file:**
  - B1: RUWE.
  - B2: CMD excess, dm / sig_cmd.
  - B3: inverse significance.
  - Likelihood-only: log_lr.
- **Not frozen here:** the v0.4 prior-selection variant (A1) is scored on DR3 now, on the same rows, and its file hash is added before DR4 as a second prediction set.

## Control group (rule fixed now, extracted from DR3 before DR4)
- **Selection:** DR3 `nss_two_body_orbit` astrometric solutions (Orbital, AstroSpectroSB1) whose implied dark-companion mass is between 80 and 300 MJ.
- **Matching:** each candidate is matched to one control by nearest neighbour in (G, log P, significance), without replacement, seed 11.
- **Purpose:** to measure how often DR4 changes ANY orbit, not only those of candidates.

## Outcomes measured on DR4 (definitions fixed now; DR3 → DR4 source match by the official DR4 neighbourhood table, nearest within 1″)
| Code | Outcome | Definition |
|---|---|---|
| O1 | Orbit dissolves | No DR4 two-body solution with period within 30% of the DR3 period (or of 2× / ½×) for the matched source |
| O2 | Stellar mass | A DR4 solution exists, and its implied dark-companion mass (same formula, DR4 m1) has a lower 95% bound > 80 MJ |
| O3 | Luminous companion (dynamical) | A DR4 combined astrometric + spectroscopic solution exists, with ρ 97.5% < 0.9 (amendment A3 rule) |
| O4 | Double-lined | A DR4 SB2 or double-lined RVS solution exists for the source |
| O5 | Phase-locked width | DR4 epoch RVS line widths give z > 2.3 with our frozen statistic (reported separately, because it is our own method) |
| D | Dark-consistent | A DR4 solution exists, implied m2 upper 95% < 80 MJ, and (if combined) ρ 2.5% > 0.9; none of O3–O5 |

- **DR4 impostor label:** O2 or O3 or O4.
- **DR4 substellar-consistent label:** D.
- **Excluded from calibration:** objects with neither label, and O1 cases (spurious orbits are analysed separately in M4).

## Metrics (all pre-stated; bootstrap 2000, seed 7)
- **M1 Calibration:** Brier score and a 5-bin reliability table of P_impostor against the DR4 impostor label. Expected vs observed impostor fraction in each verdict class.
- **M2 High-confidence errors:** the fraction of `likely_impostor` that are DR4-D, and of `likely_substellar` that are DR4 impostors, with Clopper–Pearson CIs.
- **M3 Discrimination:** AUC of P_impostor vs each baseline, with paired ΔAUC.
- **M4 Stability:**
  - the O1 rate for candidates vs controls;
  - whether P_impostor or significance predicts O1 (AUC);
  - the fraction of candidates whose verdict would change if re-scored on DR4.

## Success criteria
- **H11a:** GAIA-FP Brier < B2 Brier (paired bootstrap 95% CI of the difference excludes 0).
- **H11b:** high-confidence error rate (M2), upper 95% bound < 10%.
- **H11c (descriptive):** O1 rate among candidates exceeds that among controls. This tests the claim that low-mass DR3 orbits are less stable.

## Failure analysis (pre-committed)
Every high-confidence error is listed with its DR3 and DR4 parameters. The errors are grouped by cause:
- third light;
- metal-poor or under-luminous primary;
- period alias;
- low significance;
- a spurious DR3 orbit.

Only successful examples will **not** be shown.

## Leakage guard
The sealed DR4 labelled set (`labels_v2`) is analysed only under H1–H8. Its objects are excluded here, because they were already removed from the DR3 file.
