# vbroad model v2: correcting the selection effect. Plan written BEFORE fitting or testing

**Written:** 9 Oct 2026, ~23:40 UTC+4.
**Data:** the same real DR3 AstroSpectroSB1 set as H10 (`results/dark_companion_scored.csv`).
**Status:** development work. DR4 stays blind.

## Problem found in H10
The v1 physical vbroad likelihood ranked systems in the wrong direction (AUC 0.444). The suspected cause: Gaia solved these systems as SB1, so configurations with a bright, well-separated second set of lines are absent from this sample. The v1 model ignores that, and its blend broadening is unbounded.

## v2 model (fixed now)
1. **SB1 truncation.** A (q, n) draw is kept for H_t only if it would not have been resolved as double-lined. The draw is dropped if the RVS light ratio ℓ = qⁿ ≥ 0.2 **and** the maximum line separation K_sum · max_t |cos(ν+ω) + e cos ω| ≥ 30 km/s. The weights are renormalised. If no draw survives, H_t takes the single most SB1-like draw.
2. **Saturating blend.** vb_pred² = vb_int² + c · f(1−f) · min(⟨Δv²⟩, (30 km/s)²). A blend wider than the RVS line-spread scale is no longer fitted as one broadened line.
3. **One free constant c**, chosen on TRAIN only, from the grid {0.05, 0.1, 0.2, 0.5, 1, 2, 4}, by the AUC of the v2 vbroad-LR alone on TRAIN.

## Split (fixed now)
- **TRAIN:** source_id even.
- **TEST:** source_id odd.

TEST is evaluated **once**, after c is fixed.

## Pre-stated tests on TEST
| ID | Test | Pass if |
|---|---|---|
| V1 | v2 vbroad-LR alone | AUC lower 95% bound > 0.5 |
| V2 | S1v2 = CMD-LR + v2 vbroad-LR vs CMD only (B2) | ΔAUC lower bound > 0 |
| V3 (**key**) | S1v2 vs naive sum B2 + VB | ΔAUC lower bound > 0 |

V3 asks the real question: does the physical model add anything beyond a simple empirical combination? If V3 fails, the conclusion is that "the physical per-system model is not yet better than a naive combination". The DR4 RVS term is then calibrated empirically, not with this physics.

Bootstrap: 2000 resamples, stratified, seed 7. Results are reported whatever they are.
