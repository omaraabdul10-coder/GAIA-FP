# Pre-registration amendment v0.5

**Written:** 9 Oct 2026, before Gaia DR4 (2 Dec 2026). It extends OSF registration [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B), v0.3 + v0.4. The DR4 evaluation set stays blind. Everything below was learnt on Gaia DR3 (development data) or on validation mocks.

## Why
Real DR3 tests (`RESULTS_DARK_COMPANION.md`) found that:
1. RVS line broadening adds information beyond the CMD (H10a: ΔAUC +0.068 [+0.042, +0.095], n = 1927).
2. Our original physical H_t line-width model ranked systems in the wrong direction, because it ignored Gaia's single-/double-lined selection.
3. After the correction (v2) the physical model works (AUC 0.76), but it is not better than a naive empirical combination.

## Changes
| # | Change | Kind |
|---|---|---|
| A6 | `rvs_predict.SB1_TRUNCATE = True`. H_t draws that Gaia would have resolved as double-lined (light ratio ≥ 0.2 **and** K_sum·(1+e) ≥ 30 km/s) are excluded from the RVS phase-statistic prediction. Systems that DR4 does resolve as SB2 are labelled by H7 / H11-O4 instead. | method |
| A7 | **RVS term on DR4 follows the pre-stated V3 outcome** (`VBROAD_V2_PLAN.md`: V3 failed, so the RVS term is used empirically). **Primary:** an empirical combination, CMD z (−ΔM_G/σ) + RVS phase z (null N(0,1)), plain sum. No fitted physics. **Secondary:** the physical RVS likelihood (with A6), reported alongside. H2 (added value of RVS) is judged on the primary. A claim that "physics beats empiricism" is made only if the secondary beats the primary (paired ΔAUC lower bound > 0). | method / criterion |
| A8 | **H11 (DR3 → DR4 time-separated blind test)** is registered as `DR3_TO_DR4_PREDICTION_PLAN.md` (SHA-256 511eea20…). Frozen predictions: `results/dr3_candidates_scored.csv` (SHA-256 141734677a64942e…). | hypothesis |
| A9 | **Known limitation to report:** ρ-based labels can miss near-twin blends whose RV centroid is also diluted (`rv_degeneracy.py`). | reporting |

## Not changed
- H1–H8.
- Sealed labels and their hashes.
- The thresholds.
- v0.4 A1–A5.
