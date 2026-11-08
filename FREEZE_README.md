# GAIA-FP: OSF freeze, 9 Oct 2026

This registration freezes the GAIA-FP analysis **before Gaia DR4 (2 December 2026)**.

| File | What it is |
|---|---|
| PREREGISTRATION.md | Hypotheses H1–H7, frozen method, metrics, deviation policy (v0.3) |
| PREREG_AMENDMENT_v0.4.md | Amendment learnt from Gaia DR3 development data: label-free prior selection, H8 dynamical labels, stricter added-value criterion |
| DR3_STUDY_PLAN.md and DR3_STUDY_PLAN.sha256 | Plan of the Gaia DR3 study (already run; results in RESULTS_DR3.md on GitHub) |
| TOURNAMENT_PLAN.md | Pre-registered simulation tournament |
| FREEZE_MANIFEST.sha256 | SHA-256 of every source file (src/*.py), the plans, and the two sealed label-set hashes |

## What is and is not included
- **Sealed labelled sets:** only their SHA-256 hashes are included (labels_v1 44f30e22…, labels_v2 d6b0aabb…). The label files stay private until unblinding after DR4.
- **Code:** at https://github.com/omaraabdul10-coder/GAIA-FP. A file matches the frozen version if and only if its SHA-256 equals the entry in the manifest.

Author: Omar Abdullayev (Ganja, Azerbaijan).
