# Gaia-only blind spot map (exploratory, 23 Nov 2026)

Status: exploratory. Not pre-registered and not part of any test. It uses no sealed objects.

Code: `exploratory/blind_spot_map.py`
Output: `exploratory/blind_spot_map.json`, `exploratory/blind_spot_map.png`

## The question

For which binaries are Gaia's own data (astrometric orbit plus CMD position) unable to tell a luminous stellar companion from a dark substellar one?

## The key result: period and parallax cancel

A luminous companion with mass ratio q moves the photocentre by a0 = a_rel(B−β)ϖ. A dark companion of mass m gives the same a0 when

(M1+m)^(1/3) · m/(M1+m) = (M1(1+q))^(1/3) · (B − β(q)).

P and ϖ appear the same way on both sides, so they drop out. The "equivalent dark mass" therefore depends only on M1, q and the mass–luminosity slope n. The blind spot is a fixed region in the (M1, q) plane. It is the same for every period and distance.

## Numbers (L ∝ M^n)

The smallest q that still looks like a companion below 80 MJ:

| M1 [M☉] | n = 3.5 | n = 4 | n = 4.5 |
|---|---|---|---|
| 0.40 | 0.79 | 0.83 | 0.85 |
| 0.65 | 0.87 | 0.89 | 0.91 |
| 0.90 | 0.90 | 0.92 | 0.93 |
| 1.15 | 0.93 | 0.94 | 0.95 |
| 1.40 | 0.94 | 0.95 | 0.96 |

- Inside this band the CMD excess is at most 0.65 mag.
- The median CMD uncertainty for our DR3 candidates is σ_cmd = 0.44 mag. So even the most luminous impostor in the blind spot sits at ≤ 1.5σ in the CMD.
- Even an exact twin (0.75 mag) is below 2σ for 64% of candidates and below 3σ for 86%.

## Caveats

- Below M1 ≈ 0.25 M☉ the shaded region extends to low q. There the companion itself is only 0.05–0.07 M☉, near the hydrogen-burning limit. That corner is a mass-boundary question, not a luminous-impostor problem.
- L ∝ M^n is crude. A real isochrone would shift the q values by a few hundredths.

## Why it matters

1. **It shows what GAIA-FP's score depends on.** Gaia-only evidence cannot separate near-twins (q ≳ 0.8–0.95) from substellar companions. In that region the verdict comes from the prior and from the non-astrometric terms (RUWE, significance, baseline). NOTE_PRIOR_DOMINANCE.md shows the same thing numerically.

2. **It shows why the follow-up methods are the right ones.** The near-twins in the blind spot are exactly the cases that give double lines at the orbit extremes. That is the Shamakhy line-doubling test. It needs no new assumptions.

3. **It is the second Gaia-only blind spot.** The first is the baseline trap (H21; see RESULTS_1878822452815621120.md), where a long stellar orbit leaks into a short fitted orbit. The twin band and the baseline trap are two different failure modes, and both have a clear physical mechanism.
