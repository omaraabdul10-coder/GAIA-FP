# GAIA-FP

**Hidden stars among Gaia's invisible companions: a pre-registered blind test on Gaia DR4.**

Gaia finds unseen companions (candidate planets, brown dwarfs, neutron stars and black holes) from the orbital wobble of their host stars. Many are **impostors**: a second star whose light shrinks the measured photocentre orbit, so a stellar binary looks substellar and its mass is underestimated. GAIA-FP assigns every candidate an impostor probability from **Gaia data alone**, and is tested once, blind, on Gaia DR4 (2 Dec 2026).

Authors: Omar Abdullayev, Mikayıl (Ganja, Azerbaijan). Regeneron ISEF 2027 project.

## Pre-registration

> **Read [`CURRENT_RULES.md`](CURRENT_RULES.md) first.** It explains how v0.3 → v0.4 → v0.5 → v0.6 fit together, and why the frozen v0.3 file still says "DRAFT" and "AUC ≥ 0.80".

| Version | Registered | DOI | What it freezes |
|---|---|---|---|
| v0.3 + v0.4 | 9 Oct 2026 | [10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B) | `PREREGISTRATION.md`, `PREREG_AMENDMENT_v0.4.md`, `FREEZE_MANIFEST.sha256` |
| v0.5 | 10 Oct 2026 | [10.17605/OSF.IO/TBJGY](https://doi.org/10.17605/OSF.IO/TBJGY) | `PREREG_AMENDMENT_v0.5.md`, DR3 predictions, `FREEZE_MANIFEST_v0.5.sha256` (56 files) |
| v0.6 | *to be registered before DR4* | — | `PREREG_AMENDMENT_v0.6_DRAFT.md`, `FREEZE_MANIFEST_v0.6_DRAFT.sha256` |

A file is the frozen version **if and only if** its SHA-256 matches a registered manifest:

```bash
sha256sum -c FREEZE_MANIFEST_v0.5.sha256      # must print OK for all 56 files
```

Frozen files are never edited. Every later change is a dated amendment or a logged deviation (`DEVIATIONS_v0.6.md`).

The blind test set (76 literature-labelled objects: 39 impostors, 26 substellar) is **not in this repository**. Only its hashes are public (`sealed/labels_v1.sha256`, `sealed/labels_v2.sha256`). Gaia data of those objects were never inspected: they are dropped by id first (`realdata/excluded_sealed_ids.csv`).

## Method in one paragraph

The photocentre orbit is a0 = a_rel(B − β)ϖ, where B is the companion mass fraction and β its light fraction. GAIA-FP combines three signals:
1. the colour–magnitude over-luminosity;
2. the photocentre orbit size a0;
3. Gaia RVS line broadening (vbroad), entered as an empirical monotone likelihood ratio.

The physical blending term b = β(1−β)·K²·⟨phase⟩ is tested separately as a mechanism (H12). On DR3 it beats the CMD alone (ΔAUC +0.044), but not the simpler CMD + empirical-vbroad combination (−0.019 [−0.032, −0.008]). This is why the empirical term is the primary score (v0.5 A7).

For systems that also have a spectroscopic orbit, ρ = a0 sin i / a1 sin i gives the light fraction directly, β̂ = B(1 − ρ). These "dynamical labels" provide an independent check that does not use the score.

## Development results (Gaia DR3; not the confirmatory test)

| Result | Value | File |
|---|---|---|
| DR3 planet / brown-dwarf candidates within 500 pc | 2102 | `results/dr3_candidates_scored.csv` |
| Classified by the model as likely impostor / ambiguous / likely substellar | 1911 (91%) / 174 / 17 — a model-based estimate (stable at 89–91% across EM regularisation), not a confirmed prevalence | same; `results/qa2/partial_completion/ABLATION_PRIOR_SENSITIVITY_2026-11-01.md` |
| Candidates whose Gaia combined astrometric + spectroscopic (AstroSpectroSB1) orbit shows an impostor (ρ < 0.9 or m₂,dyn > 80 MJ at 95%) | 42 of 95 | `results/astrospectro_check.json`, labels `results/astrospectro_labels.csv` |
| Their true / catalogue companion mass | median **4.0×** [3.5, 5.5]; this subsample is selected on astrometric mass, so it is not representative | `results/candidate_mass_bias.json` |
| vbroad information beyond the CMD (n = 1927) | ΔAUC +0.044 [+0.033, +0.055] | `results/erratum_k_units.json` |
| APOGEE DR17 external check: 8 RV-incompatible systems vs 53 unlabelled (positive-vs-unlabelled AUC) | 0.73 [0.58, 0.88]; 8/8 flagged | `RESULTS_APOGEE.md` |
| Companions ≥ 1.4 M☉ showing companion light (resolved; 5000 MC draws, 80/83 with 200) | 80 / 81 | `results/new_hypotheses_dev_dr3_mc5000.json` |
| Astrometric "brown dwarfs" (13–80 MJ) that are stars (resolved) | 33 / 35 | same |
| vs Bailer-Jones & Kreidberg 2026 masses (plan hashed first), survey-SB2 labels | ΔAUC **+0.22** [+0.08, +0.39] in GAIA-FP's favour; APOGEE labels: no detectable difference | `RESULTS_BJK_COMPARISON.md` |
| Black hole Gaia BH2 | ρ = 0.92, not flagged as luminous | `DEVIATIONS_v0.6.md` §27 |

Caveats are stated with each number in the result files. Combined orbits favour heavy companions, the sealed sample is small, and mechanism sub-test M3 failed on DR3.

**Prior art** (details in `NOVELTY_AND_PRIOR_ART.md`):
- The joint astrometry + photometry idea is published: Bailer-Jones & Kreidberg 2026, A&A 708, A249.
- vbroad as a binarity signal is published: Hadad et al. 2025.
- Spectroscopic follow-up found 13 impostors among 20 Gaia DR3 substellar candidates: Marcussen et al. 2026, arXiv:2609.08590.

GAIA-FP's own contribution is narrower:
- a phase-locked test on DR4 per-transit line widths;
- the light-blending mechanism;
- the same filter applied to brown-dwarf and compact-object candidates;
- a pre-registered, blind, single-run test.

**Erratum.** A units bug (F6: an orbital period in years passed where days were expected) affected the earlier H10 numbers and a "selection effect" interpretation. Registered values are kept and corrected values are reported next to them. See `RESULTS_DARK_COMPANION.md`, `AUDIT_REPORT.md` and `DEVIATIONS_v0.6.md` §17.

## Confirmatory tests on DR4

| Tests | Rule |
|---|---|
| Weighted Holm, one-sided family-wise α = 0.025 (v0.6 A18/A31) | **H1** (sealed labels, weight 0.4), **A5** (DR4 dynamical labels, 0.2), **H12** (blending mechanism, 0.2), **H2** (0.1), **H11a** (DR3→DR4 calibration, 0.1) |
| Secondary | H11b, H13, H14, H16 (APOGEE), **H17** (Gaia epoch photometry), **H18** (compact-object impostors), **H19** (brown-dwarf desert), **H20** (head-to-head vs Gaia DR4's own flux ratio and Bailer-Jones & Kreidberg 2026) |

The power of H1 was simulated before DR4 with the registered stratified-bootstrap test (B = 2000) at α = 0.01, for 39 + 26 objects and a true AUC of 0.73 (the APOGEE development value): **0.83** (0.71 if only 30 + 20 remain). Power is the chance of detecting a real effect, not the model's accuracy (`results/power_h1_bootstrap.json`). Outcomes are reported as PASS, FAIL or NOT_CONDUCTED:reason.

## Ground-based follow-up (draft, not yet registered)

[`SHAMAKHY_FOLLOWUP_PLAN.md`](SHAMAKHY_FOLLOWUP_PLAN.md) describes the planned spectroscopy with the 2-m telescope and ShaFES at the Shamakhy Astrophysical Observatory. The test is **line doubling** at the extremes of the orbit, not the RV semi-amplitude. A blended centroid reproduces the photocentre amplitude under both hypotheses (`src/rv_degeneracy.py`). Two spectra per target are enough: for 13 of the 16 targets, a near-twin impostor shows doubled lines with probability ≥ 0.85 at R = 56 000. Code is in `followup/`, tests in `tests/test_shamakhy_forward.py`. The plan will be hashed and registered before the first spectrum is taken.

## Repository layout

```
src/            analysis code (DR3 study, mechanism, DR4 runners)
  dr4_fetch.py        DR4 download (registered Gaia archive account needed)
  dr4_release_map.py  DR4 data model -> internal schema
  dr4_day.py          DR4-day orchestrator  (python dr4_day.py dryrun)
  dr4_run.py, dr4_evaluate.py, dr4_mechanism.py, h11_outcomes.py, new_hypotheses.py
tests/          pytest suite
realdata/       Gaia DR3 / APOGEE extracts used for development (provenance: realdata/PROVENANCE.md)
results/        frozen predictions and development outputs
audit/          independent audit reports, power analysis, dry-run logs
docs/           DR4 data model notes, history
sealed/         hashes of the sealed label files (the labels themselves are private)
index.html      project website; site_checker.html: look up any DR3 candidate
```

## Reproduce

```bash
pip install -r requirements-dev.txt   # requirements.txt itself is frozen in the v0.5 manifest
python -m pytest -q tests              # all pass
cd src && python dr4_day.py dryrun     # the real DR4 chain on DR3-derived fake data and synthetic labels (~6 min)
```

DR4 day (2 Dec 2026) commands are in `DR4_READINESS.md`.

## Use of AI tools

Because the authors are not native English speakers, AI was used to draft and edit the English text of the project documentation. The authors chose the research question, designed the study, made the pre-registration and analysis decisions, and interpret the results. An AI system (Claude, Anthropic) assisted with code writing and literature search.

## Licence and data

Code: MIT (`LICENSE`).

Data:
- Gaia data: ESA/Gaia/DPAC, under the [Gaia data licence](https://www.cosmos.esa.int/web/gaia-users/license).
- APOGEE data: SDSS DR17.

Please cite the OSF registrations above (`CITATION.cff`).
