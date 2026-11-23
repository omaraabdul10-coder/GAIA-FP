# OSF registration v0.6: what to paste into the form and what to upload

## How to register

We do these steps ourselves on OSF:

1. Sign in and open the project at https://osf.io/4eytf.
2. Upload the files in the table at the bottom of this page to OSF Storage.
3. Go to Registrations → New registration → Open-Ended Registration. This is the same template we used for v0.5.
4. Paste in the title and summary below.
5. Check the file list one more time, then press Register. As with v0.4 and v0.5, choose "make public immediately".
6. Once OSF approves it, put the new DOI into `README.md`, `CURRENT_RULES.md` and the abstract.

## Title

GAIA-FP pre-registration amendment v0.6: weighted multiplicity, mechanism and secondary tests, DR4-day rules (before Gaia DR4)

## Summary (for the "Summary" box)

Amendment v0.6 extends the GAIA-FP pre-registration. The earlier versions are v0.3/v0.4 (OSF N5H4B) and v0.5 (OSF TBJGY, DOI 10.17605/OSF.IO/TBJGY). Gaia DR4 is due on 2 December 2026. We register before it, while no DR4 data exist.

The amendment, `PREREG_AMENDMENT_v0.6.md`, contains items A10 to A38. Its main change is a new confirmatory family: H1, A5, H12, H2 and H11a. The family is tested with a weighted Holm procedure at a one-sided family-wise α of 0.025 with weights 0.4/0.2/0.2/0.1/0.1, and A31 and A37 define the algorithm and the pass rule. In simulations with the registered test, H1 has power 0.83 under this correction for a true AUC of 0.73.

H12–H14 test the physical mechanism. There are six secondary tests, H15–H20. Among them, H17 checks our scores against Gaia epoch photometry, H18 looks for compact-object impostors, H19 measures contamination of the brown-dwarf desert, and H20 compares GAIA-FP with Gaia DR4's own flux ratio and with Bailer-Jones & Kreidberg 2026. The amendment also maps the DR4 data model onto our code, fixes the order of operations for DR4 day, and adds a rule for primary masses (A36).

We did not keep the original sealed label file, `labels_v2` (d6b0aabb…). A38 describes how we rebuilt it as `labels_v2r` (SHA-256 a8ccb9b6fd1b4bf97bd9669d8be866bb33bd83b3c630feb90933f9a05703d3aa), which now replaces it. The rebuilt file has the same 76 objects frozen on 9 Oct 2026, uses the same sources and rules, and gives identical counts: 39 impostors, 26 substellar, 10 unresolved, 1 excluded. We finished it before DR4 and have computed no score on these objects. The hash is public; the labels stay private until the DR4 run is complete.

Later changes will go into `DEVIATIONS_v0.6.md`, and `CURRENT_RULES.md` shows how v0.3 through v0.6 fit together. `FREEZE_MANIFEST_v0.6.sha256` records the SHA-256 of every file in the code and analysis repository. Code: https://github.com/omaraabdul10-coder/GAIA-FP (tag `v0.6-osf`).

Use of AI tools: Because the authors are not native English speakers, AI was used to draft and edit the English text of the project documentation. The authors chose the research question, designed the study, made the pre-registration and analysis decisions, and interpret the results. An AI system (Claude, Anthropic) assisted with code writing and literature search.

Not frozen (presentation only, may be edited after registration): `README.md`, `index.html`, `site_checker.html` and `docs/presentation/`. They are left out of `FREEZE_MANIFEST_v0.6.sha256`.

## Files to upload

| File | What it is |
|---|---|
| `PREREG_AMENDMENT_v0.6.md` | the amendment (A10–A38) |
| `FREEZE_MANIFEST_v0.6.sha256` | SHA-256 of every repository file |
| `CURRENT_RULES.md` | how v0.3 → v0.6 fit together |
| `DEVIATIONS_v0.6.md` | change log, entries 13–32 |
| `HYPOTHESIS_LEDGER.md` | every hypothesis, its sample and its status |
| `DR4_READINESS.md` | what we do on DR4 day |
| `labels_v2r.sha256` | hash of the sealed label file (contains no labels) |
| `power_h1_bootstrap.json` | the power simulation |
| `BJK_COMPARISON_PLAN.md`, `BJK_COMPARISON_PLAN.sha256`, `GAIA_RV_LABEL_PLAN.md`, `GAIA_RV_LABEL_PLAN.sha256` | plans whose hashes we stored before running the exploratory analyses |
| `EXTERNAL_RV_VALIDATION_PLAN.md`, `EXTERNAL_RV_VALIDATION_PLAN_AMENDMENT_1.md` and their `.sha256` files | plan for the SB9/SBX check, hashed before the data were fetched |
| `SHAMAKHY_FOLLOWUP_PLAN.md`, `SHAMAKHY_FOLLOWUP_PLAN.sha256` | line-doubling test for the Shamakhy spectra; registered before the first spectrum |
| `H21_BASELINE_TRAP_PLAN.md`, `H21_BASELINE_TRAP_PLAN.sha256` | secondary hypothesis H21: near-baseline DR3 orbits revised upward in mass by DR4 (outside the Holm family) |
| `H19_DESERT_PLAN.md`, `H19_DESERT_PLAN.sha256` | fixed mass-bin breakdown of H19 (reporting only, no new test) |
| `H22_LIKELIHOOD_ONLY_PLAN.md`, `H22_LIKELIHOOD_ONLY_PLAN.sha256` | secondary: frozen likelihood without the prior (outside the Holm family; H1 unchanged) |
| `RESULTS_1878822452815621120.md`, `NOTE_PRIOR_DOMINANCE.md` | exploratory notes filed before DR4: the baseline-trap example with its written DR4 prediction, and the evidence that motivated H22 (no tests) |

Do not upload `labels_v2r_PRIVATE.json` under any circumstances.
