# Follow-up notes, 23 Nov 2026 (exploratory; local only)

None of this changes a frozen file or a registered test. None of it uses the 76 sealed objects.

## 1. Shamakhy target 1878822452815621120: the line-doubling test can't decide it

This star is the first target in `followup/shamakhy_targets.csv` (group A_likely_substellar). Its first good window is about 4 Dec 2026. The plan tests the impostor hypothesis as a near-twin with q_imp = 0.98, and checks for line doubling.

The CfA spectra (Latham et al. 2002; 79 RVs, see RESULTS_1878822452815621120.md) are **single-lined**. They show a 3977 d orbit whose companion is an M dwarf of about 0.2–0.4 M☉. That already rules out a near-twin. So if ShaFES sees no line doubling, it only repeats what CfA already showed, and the plan's decision rule would wrongly record "consistent with substellar". The other explanation is that the long stellar orbit leaks into the Gaia fit (the baseline trap). Line doubling can't test that, and two spectra can't either.

**Proposal** (to log as a deviation before the first spectrum, if Omar agrees):
- Either take this star out of the confirmatory Shamakhy decision rule, or keep it only as a reported "known-SB1 control".
- Use its nights for the next A/B target.
- Its real test is DR4. If the period is about 4000 d or the mass is far above 80 MJ, it is the baseline trap. If DR4 again gives about 1000 d, the dark companion stays.

## 2. Telescope time: the real numbers

Assumption: 2 spectra per target and about 2 h per target on the 2-m telescope. This follows from the Shamakhy plan (about 32–40 h for 16 targets).

- DR3: our list has 2102 candidates. Checking all of them would take about 4200 h, which is about 525 full 8-hour nights. Shamakhy's clear-night fraction isn't in this repo, so we don't convert this to years.
- DR4: the number of candidates is not known before 2 Dec. The figure scales linearly: each 1000 candidates costs about 2000 h.

(An earlier rough talking point, "5000 candidates → 10 000 h", was only an illustration. Use the DR3 number above, or the DR4 number once it exists.)

## 3. Triage value on DR3 (PU labels: 16 known SB2 impostors)

We ordered targets so the least impostor-like are observed first. File: `exploratory/telescope_time_dr3.json`.

| Observe only the lowest … of candidates | Hours | Known impostors skipped, using `log_lr` (H22 score) | … using `P_impostor` (H1 score) |
|---|---|---|---|
| 25% | 1050 | 15 / 16 | 13 / 16 |
| 50% | 2100 | 13 / 16 | 13 / 16 |
| 75% | 3150 | 10 / 16 | 7 / 16 |

How to read this: with the H22 score, halving the telescope time still skips 13 of the 16 known impostors.

Caveats:
- 16 positives is a small sample.
- The positives are SB2 twins, so the CMD helps more than it would on average.
- The `log_lr` score was chosen after seeing DR3 (see H22).
- We can't count how many true substellar companions would be lost, because DR3 has no clean substellar labels. That is exactly what the DR4 blind test measures.
