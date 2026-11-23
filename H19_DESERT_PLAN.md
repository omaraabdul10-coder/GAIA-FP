# The brown-dwarf desert after removing impostors: reporting plan for H19 by mass (written before Gaia DR4)

Date: 23 Nov 2026. Status: reporting plan, not a new test. It adds a fixed, pre-declared breakdown of the
registered secondary test H19 (v0.6) and changes nothing in H19 itself. Code: `src/h19_desert.py`.

## Why it uses dynamical labels and not GAIA-FP probabilities
GAIA-FP's impostor probabilities are dominated by the covariate prior, which itself depends on the catalogue mass
(DR3: median prior 0.97; with a flat prior of 0.3 the mean probability per mass bin is 0.42–0.49; see
`NOTE_PRIOR_DOMINANCE.md`). Weighting the mass function by those probabilities would partly return the prior.
H19 instead labels each system from its combined astrometric + spectroscopic orbit (ρ and m2,dyn), independently of
the score, so the breakdown below is not circular.

## What is reported on DR4
On the H19 table (`new_hypotheses.h18_h19`, new DR4 combined orbits only), for dark-assumed masses in the bins
1–13, 13–30, 30–50 and 50–80 MJ:
- n, number labelled luminous, fraction luminous with a 95% Clopper–Pearson interval;
- number consistent with a dark companion;
- median ratio of dynamical to dark-assumed mass for the luminous ones.
The same numbers on DR3 are in `results/h19_desert_dev_dr3.json` (13–30: 1 of 1, 30–50: 4 of 4, 50–80: 28 of 30;
development values).

## Caveat stated in advance
Combined orbits need a detectable spectroscopic orbit, which favours massive companions. The fractions describe that
subsample, not every Gaia astrometric candidate, and no extrapolation to the full catalogue is made.
