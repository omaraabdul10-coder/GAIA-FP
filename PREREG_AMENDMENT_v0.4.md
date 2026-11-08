# Pre-registration amendment v0.4

**Status: v0.4, written 9 Oct 2026, frozen by OSF registration (the OSF timestamp is authoritative), before Gaia DR4 (2 Dec 2026).** The DR4 evaluation set is still blind. Everything below was learnt on **Gaia DR3 (development data)** and on simulated validation mocks.

## Why
The H7-DR3 study (`RESULTS_DR3.md`) found three things:
1. The pre-registered survey-SB2 metric is biased toward near-twin binaries.
2. Independent dynamical labels (AstroSpectroSB1, a0 vs a1) confirm a very high impostor fraction near the brown-dwarf boundary.
3. The CMD-only baseline matches GAIA-FP on DR3.

## Changes
| # | Change | Kind |
|---|---|---|
| A1 | **Population prior:** π(x) flexibility is chosen by `prior_select.select` (grid C ∈ {0, 0.003, 0.03, 0.3, 1}, 5-fold held-out observed-data likelihood, ties within 1 nat go to smaller C, seed 0). Otherwise the frozen v3.1 scoring is unchanged. | method (robustness) |
| A2 | **New hypothesis H8:** on DR4 combined astrometric + spectroscopic solutions, GAIA-FP's AUC for the dynamical labels exceeds 0.5 (lower 95% bootstrap bound > 0.5), and GAIA-FP's impostor recall at P ≥ 0.85 is ≥ 80%. | hypothesis |
| A3 | **Dynamical label rules:** impostor if m2_dyn 2.5% > 80 MJ or ρ 97.5% < 0.9; genuine-consistent if m2_dyn 97.5% < 80 MJ and ρ 2.5% > 0.9; otherwise excluded. Monte Carlo errors as in `src/astrospectro_check.py`. | labels |
| A4 | **Metric role:** H7 (survey SB2) is reported as a secondary metric with the twin bias stated. The B2 CMD-only baseline is shown next to every GAIA-FP number. | reporting |
| A5 | **Success claim:** GAIA-FP claims added value over the CMD-only baseline **only if** the paired bootstrap ΔAUC (GAIA-FP − B2) on the H8 labels has a lower 95% bound > 0. Otherwise the report says "no gain over CMD-only". | criterion |

## Not changed
- Sealed labelled set and its hashes.
- Thresholds (t = 0.15).
- Likelihoods.
- RVS test.
- Follow-up ranking.
- H1–H7 definitions.
