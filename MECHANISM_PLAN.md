# Why does line broadening flag luminous companions? Mechanism plan, written BEFORE the tests are run

**Written:** 30 Oct 2026, ~23:30 UTC+4. The SHA-256 of this file is stored (`MECHANISM_PLAN.sha256`) before `src/mechanism.py` is run.
**Data:** the same real Gaia DR3 AstroSpectroSB1 sample as H10 (`results/dark_companion_scored.csv`, 19 506 systems after cuts).
**Status:** DEVELOPMENT. The DR3 data have been used before (H10, vbroad v2): the relation between vbroad and the binary label is known in aggregate (median vbroad 14.9 vs 8.1 km/s). The relations tested here (vbroad against the per-system blend term, against K1, and the occupancy of the (light ratio, RV separation) plane) have **not** been computed before. The confirmatory version of every test is the DR4 run (section 6), registered on OSF before 2 Dec 2026.

## 1. Question
On real DR3 data, Gaia's vbroad separates luminous from dark companions (H10: AUC 0.755). Our first physical model predicted broadening in the wrong direction (AUC 0.43); adding the SB1 selection fixed it (0.76). Is the signal really caused by **the companion's lines blending with the primary's** (mechanism B), shaped by **which systems Gaia could still solve as single-lined** (selection S)? Or by something else?

## 2. Per-system quantities (no vbroad used; computed from the astrometric + SB1 orbit)
- a1 sin i = hypot(C, H) [AU]; inclination i from the Thiele–Innes A, B, F, G; P in years.
- m1 = photometric mass from M_G (as in H10). m2 = the positive root of m2³/(m1+m2)² = (a1 sin i / sin i)³ / P².
- B = m2/(m1+m2). ρ = median of the Monte Carlo ρ (as in H10); σ_ρ = (97.5% − 2.5%)/3.92.
- **Light fraction** β̂ = clip(B·(1 − ρ), 0, 0.5) (G band; the RVS-band fraction of a cooler companion is somewhat larger, so β̂ is conservative).
- K1 = 29.78 · (a1 sin i) / (P · √(1−e²)) km/s; K_sum = K1 / B.
- pavg(e, ω) and smax(e, ω) as in `vbroad_v2.py`.
- **Blend term** b = β̂(1−β̂) · min(K_sum² · pavg, 30²) [(km/s)²]. **Smearing term** k = K1² · pavg.
- Excess VB = (vbroad − field median)/field robust σ, the same calibration as H10.
- Sample V: systems with vbroad from ≥ 5 transits and a field calibration (n ≈ 10 121). Dark sample: V with label 0 (ρ 2.5% > 0.9).

## 3. Competing explanations and what each predicts
| ID | Explanation | Prediction that differs from B |
|---|---|---|
| B | Companion lines blend with the primary's (mechanism) | VB rises with b, i.e. needs **both** light (β̂) and velocity separation (K_sum) |
| A1 | Youth / fast rotation / activity | Acts through over-luminosity (CMD), not through ρ: no partial relation with b once colour and magnitude are fixed |
| A2 | vbroad systematics with brightness, colour, SNR | Explained by G_RVS and BP−RP covariates |
| A3 | Evolved primaries (sub-giants) | Disappears when the CMD offset dM_G is added as a covariate |
| A4 | Metallicity | **Not testable here** (no [M/H] in our download). Declared limitation |
| A5 | The primary's own orbital motion smears its lines (no companion light needed) | VB rises with k = K1²·pavg **also in dark-companion systems** |
| A6 | Blending dilutes the measured K1 (`rv_degeneracy.py`) | Works **against** B (lowers β̂ for blends); cannot create the signal |

## 4. Tests (all on sample V; bootstrap 2000, seed 7, resampling systems)
Partial Spearman correlation = Pearson correlation of rank-transformed variables after regressing out the rank-transformed covariates. **Primary covariates:** G_RVS, BP−RP, log P, e. **Secondary:** + dM_G.

| ID | Test | Pass (supports B) | Fails / alternative |
|---|---|---|---|
| **M1** (primary) | partial ρ_s(VB, b \| primary covariates) | 95% lower bound > 0 | ≤ 0: B not supported |
| M1s | same with + dM_G | reported; lower bound > 0 means not explained by A1/A3 | |
| **M2a** | dark sample: partial ρ_s(VB, k \| primary covariates) | 95% upper bound < 0.10 | lower bound > 0.10 → A5 supported |
| **M2b** | ρ_s(VB, b) − ρ_s(VB, k), partial, sample V, paired bootstrap | lower bound > 0 (light is needed, not just motion) | ≤ 0 |
| **M3** (selection S) | depletion D = [f_obs(β̂ ≥ 0.2 \| K_sum·smax ≥ 30) / f_obs(β̂ ≥ 0.2 \| K_sum·smax < 15)] ÷ [the same ratio from the forward model WITHOUT SB2 selection] | 95% upper bound of D < 0.5 | D ≈ 1: no selection signature |
| M4 (amplitude) | ĉ = median of (vbroad² − med²)/b over V with b ≥ 25 (km/s)² | CI overlaps [2, 8] (theory: c = 4, the variance of a rotational kernel) | reported either way |
| P0 (placebo) | M1 with VB permuted across systems (200 permutations) | |ρ_s| of the real data above the 99th percentile of the permutations | |

**M3 forward model (catalogue entry).** For every observed system keep its m1, P, e, i, ω, ϖ and a0 error; redraw the companion: q ~ U(0.1, 1), n ~ U{2, 2.5, …, 6}, β = qⁿ/(1+qⁿ). Keep a draw only if Gaia could detect it as AstroSpectroSB1: predicted a0/σ_a0 ≥ the 1st percentile of the observed a0/σ_a0, and K1 ≥ the 1st percentile of the observed K1. Add each system's own ρ noise (σ_ρ) before forming β̂. 50 draws per system. Sensitivity: q log-uniform. The depletion is computed only from orbital quantities; vbroad is not used.

**Overall verdict (fixed now):**
- **Mechanism B supported** if M1, M2a and M2b pass.
- **Selection S supported** if M3 passes.
- **A5 favoured** if M2a's lower bound > 0.10 and M2b fails.
- Anything else is reported as **inconclusive**. No new test is added to rescue a failed one.

## 5. Power (computed after the DR3 run, before DR4)
Minimum detectable partial correlation at α = 0.05 (two-sided), 80% power: r_min ≈ 2.80/√(n − 7). The DR4 tests are declared confirmatory only if r_min ≤ half of the DR3 M1 estimate. Otherwise the DR4 result is reported as non-informative.

## 6. DR4 (confirmatory; to be registered on OSF before 2 Dec 2026 as amendment v0.6)
The same code (hash in the manifest) is applied to DR4 combined astrometric + single-lined solutions **whose source_id is not in the DR3 AstroSpectroSB1 table** and not in the sealed list, with vbroad (or the DR4 equivalent line-broadening parameter). If DR4 does not publish such solutions or a line-broadening parameter, the test is not run, and that is reported.

## 7. Reporting
Every number above is reported, pass or fail, in `RESULTS_MECHANISM.md`, with the label "DR3 development". Any deviation goes into `DR3_STUDY_DEVIATIONS.md`.
