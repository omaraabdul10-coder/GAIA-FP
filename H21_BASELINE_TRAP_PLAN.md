# H21: the baseline trap. Pre-registration plan (written before Gaia DR4)

Date: 23 Nov 2026. Status: secondary hypothesis, outside the weighted Holm family of v0.6 (A18/A31). It changes no
registered test, threshold or weight. Code: `src/h21_baseline.py`. Test: `tests/test_h21_baseline.py`.
No sealed label is used: the sample is the frozen DR3 prediction file, which never contained the 76 sealed objects, and
the sealed id list is dropped again in the code.

## 1. Idea
Gaia DR3 orbits come from T3 = 1038 days of data (25 Jul 2014 – 28 May 2017). An orbit with a period close to or longer
than T3 is seen only in part. A partial arc is fitted by a smaller, shorter orbit, and the dark-companion mass comes out
too small. It is a second way, apart from light blending, to make a stellar or massive companion look substellar.

Rough scaling (motivation, not part of the test): for a true period P_true > T3 the arc seen in T3 has an amplitude of
order a0_true (T3/P_true)^2, so with m2 ∝ a0 P^(−2/3) the fitted mass is low by about (T3/P_true)^(4/3).
The 80 MJ selection cut of the candidate list adds to this: near-baseline orbits have larger errors, and only the
low-mass side of a noisy estimate passes the cut.

Case that motivated it: Gaia DR3 1878822452815621120 (P = 1009 ± 138 d) also has a 3977 d ground-based orbit
(SB9, Latham et al. 2002). See `RESULTS_EXTERNAL_RV.md`.

DR4 uses about 66 months of data, so these orbits will be refitted with roughly twice the time span.

## 2. Samples (fixed now from the frozen DR3 file `results/dr3_candidates_scored.csv`)
- x = P_DR3 / 1038 d.
- Group N (near baseline): x ≥ 0.85. DR3 count: 108.
- Group S (short period): x < 0.5. DR3 count: 1295.
- 0.5 ≤ x < 0.85: reported only.
Counts and DR3 summaries are frozen in `results/h21_dr3_groups.json`.

## 3. DR4 matching and mass (same rules as H11, `src/h11_outcomes.py`)
- DR3 → DR4 id with the official `dr3_neighbourhood` table: nearest DR4 source within 1".
- DR4 astrometric orbit = a DR4 two-body solution with Thiele–Innes elements. If there are several, the one with the
  highest `significance` is used.
- m2_DR4 = median of `h11_outcomes.mass_bounds` (400 Monte Carlo draws, seed 0) with m1 fixed to the frozen DR3 m1 of
  the same star, so only the orbit changes. m2_DR3 = the frozen `mfit`.
- r = m2_DR4 / m2_DR3. REVISED_UP if r ≥ 1.5.

## 4. Primary test (H21)
- p_N, p_S = fraction REVISED_UP among the matched objects that have a DR4 astrometric orbit.
- PASS if p_N > p_S with a one-sided Fisher exact p < 0.05 and the one-sided 95% lower bound of p_N − p_S from a
  stratified bootstrap (B = 2000, seed 21) is above 0. Otherwise FAIL.
- NOT_CONDUCTED if fewer than 20 objects in N or fewer than 100 in S have a DR4 astrometric orbit; the counts are
  reported.

## 5. Reported with it (not tests)
- H21b: the same comparison when an N or S object with no DR4 astrometric orbit but another DR4 non-single-star
  solution (e.g. an acceleration solution) counts as revised.
- The same comparison restricted to m2_DR3 < 40 MJ, far from the 80 MJ cut, to separate the baseline effect from
  selection near the cut.
- P_DR4 / P_DR3 by group; the fraction with |P_DR4 − P_DR3| > 3 σ_P,DR3.
- Within N: how well GAIA-FP's P_impostor ranks REVISED_UP (AUC), to show whether the two mechanisms overlap.
- Every object's outcome, including unmatched and missing ones.

## 6. What a result would mean
- PASS: near-baseline DR3 orbits are a separate source of false substellar candidates; a later GAIA-FP version should
  carry a baseline flag. v0.6 results are not changed.
- FAIL: no evidence that near-baseline DR3 solutions are revised upward more often than short-period ones.
