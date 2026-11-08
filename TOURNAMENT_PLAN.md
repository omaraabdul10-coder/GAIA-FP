# Improvement tournament — plan written BEFORE running (9 October 2026)

This plan is committed before any tournament result exists. The results go in `EXPERIMENT_TOURNAMENT.md`.

## Data splits (all simulated; Lammers & Winn 2025 mocks + our observation model `sim.py`)

| Split | Content | Purpose |
|---|---|---|
| TRAIN | DR4 mocks: planets 3000 (sample seed 3, rows 0–2999); impostors: shuffled half A | used only to train the ML baseline |
| VALIDATION | DR4 mocks: planets rows 3000–5999; impostors: half B | all tournament decisions and threshold choices |
| HELD-OUT | **DR5** mocks: 4000 planets (seed 99) + 1500 impostors (seed 99) | evaluated **once**, after all decisions; observation model: span 3800 d, 45–85 RVS epochs |

The DR5 mocks were not used at any point in development. They differ in population (longer periods, lower masses, fainter hosts) as well as in cadence, so they act as a held-out set with a built-in distribution shift.

## Frozen baseline B0

GAIA-FP v3 + EM, exactly as in PREREGISTRATION v0.2 §6:
- joint conditional a0 | CMD likelihood;
- physics-predicted RVS likelihood;
- label-free logistic EM prior;
- CMD scatter assumed to be 0.30 mag.

## Extensions, hypotheses and success criteria (decided now)

| ID | Extension | Hypothesis | Success criterion on VALIDATION |
|---|---|---|---|
| X1 | Competing hypothesis H_pw: planet host with an unresolved wide stellar companion; prior w = 0.05 | When 10% of planet hosts have third light, B0 wrongly calls many of them impostors; X1 reduces this using the absence of phase-locked RVS width | (a) Among H_pw objects with RVS, the false-impostor rate at P > 0.5 falls by ≥ 30% relative to B0. (b) On the clean set (no H_pw), AUC falls by ≤ 0.005. |
| X2 | Three-way output with abstention: P ≤ t gives "likely substellar", P ≥ 1−t gives "likely impostor", otherwise "ambiguous" | Abstaining on the middle reduces errors among the decided objects | Choose the largest t with decided-error ≤ 2% on VALIDATION. Success if coverage is ≥ 60% at that t. Report it on HELD-OUT without re-tuning. |
| X3 | EIG-ranked follow-up for ambiguous candidates (0.1 < P < 0.9) | Ranking (candidate, observation) by EIG per cost resolves more ambiguous candidates per unit telescope cost than ranking by ambiguity with RV for all | With a budget equal to 30% of 3 × (number of ambiguous candidates), EIG policy resolves ≥ 1.2× more candidates correctly (final P < 0.05 or > 0.95 and correct) than the ambiguity policy, with no more mis-resolutions |
| X4 | Contamination estimators: heterogeneous EM, constant-π EM, constant-π profile likelihood | The contamination fraction is identifiable to within ±0.03 under realistic misspecification | Bias ≤ 0.03 in absolute value in all of: nominal, assumed CMD scatter wrong by ±20%, RVS noise twice the assumed value, 10% unmodelled H_pw. If any scenario fails, report the conditions for non-identifiability. |
| X5 | Distribution-shift suite: G < 12 only; G > 14 only; d < 60 pc; CMD scatter 0.45; RVS noise ×2; 10–20 RVS epochs; RVS missing; contamination 5% and 50% | B0 degrades no more than the simulator-trained ML | ΔAUC(B0) ≤ ΔAUC(ML) in ≥ 6 of the 9 shifts |

## Multiple-comparison guard

Five extensions are tested. Each is adopted only if its pre-stated criterion holds on VALIDATION. The HELD-OUT set is used once, for the final configuration, B0 and the baselines. No parameter is changed after the held-out evaluation; anything that would change is listed as future work.
