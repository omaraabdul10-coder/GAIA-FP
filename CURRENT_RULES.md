# Which rules apply? (read this first)

The pre-registration is a chain. A later document changes only what it names, and where two documents differ, **the later one wins**. Frozen files are never edited, so the older files still show older wording.

| Order | File | Registered | What it is |
|---|---|---|---|
| 1 | `PREREGISTRATION.md` | OSF N5H4B, 9 Oct 2026 | Original plan. The header still says "v0.3 DRAFT" because the file is frozen byte-for-byte as registered. |
| 2 | `PREREG_AMENDMENT_v0.4.md` | OSF N5H4B, 9 Oct 2026 | Adds H8 and A1–A5 (A5: GAIA-FP vs CMD-only on DR4 dynamical labels). |
| 3 | `PREREG_AMENDMENT_v0.5.md` | OSF TBJGY, 10 Oct 2026 | A6–A9: empirical RVS score as primary (A7), the H11 DR3→DR4 test (A8). |
| 4 | `PREREG_AMENDMENT_v0.6_DRAFT.md` | to be registered before DR4 | A10–A36: multiplicity (weighted Holm), H12–H20, DR4 data model, DR4-day rules. |

## Common questions

**"H1: AUC ≥ 0.80" or "lower bound > 0.5"?** Both are in v0.3 and they do not conflict:
- AUC ≥ 0.80 is the *expected* value (descriptive).
- The *decision rule* has been the same since v0.3: H1 is falsified if the 95% CI of the AUC includes 0.5, so it passes only if the lower bound is > 0.5.
- v0.6 adds the multiplicity correction (A18/A31).

**H1–H7 or "H1, A5, H12, H2, H11a"?**
- H1–H7 are the original hypotheses (v0.3) and they all still exist.
- v0.6 A18 picks five of them as the **confirmatory family** that is corrected for multiplicity: H1, A5, H12, H2 and H11a.
- All others (H3, H5–H7, H11b, H13–H20) are secondary and are reported in full.

**76 or 65 systems?**
- The sealed set `labels_v2` has 76 systems.
- 65 of them enter the analysis: 39 impostors + 26 substellar.
- 11 are excluded by rules fixed in v0.3: 10 unresolved or conflicting, and 1 inspected during development (Gaia-4).

**GAIA-FP v3 or something new?**
- It is the same method.
- v3.1 is the registered model (v0.3–v0.4).
- v3.2 (v0.6 A25) is the primary DR4 scoring, after the audit fixes; v3.1 is computed alongside it as registered.
