# Which rules apply? (start here)

Think of the pre-registration as a chain. Each document amends only what it names. When two of them conflict, the later one governs. Frozen files stay frozen, so the older ones keep their older wording, and that is deliberate.

| Order | File | Registered | What it is |
|---|---|---|---|
| 1 | `PREREGISTRATION.md` | OSF N5H4B, 9 Oct 2026 | The original plan. Its header still reads "v0.3 DRAFT" because we froze the file byte for byte as registered. |
| 2 | `PREREG_AMENDMENT_v0.4.md` | OSF N5H4B, 9 Oct 2026 | Adds H8 and A1–A5. A5 compares GAIA-FP with a CMD-only model on DR4 dynamical labels. |
| 3 | `PREREG_AMENDMENT_v0.5.md` | OSF TBJGY, 10 Oct 2026 | A6–A9. Makes the empirical RVS score primary (A7) and adds the H11 DR3→DR4 test (A8). |
| 4 | `PREREG_AMENDMENT_v0.6.md` (final; the `_DRAFT` file shows how it got there) | OSF, before DR4 | A10–A38: weighted Holm for multiplicity, H12–H20, the DR4 data model and the DR4-day rules. |

## Questions that keep coming up

**Is H1 "AUC ≥ 0.80" or "lower bound > 0.5"?**
v0.3 contains both phrases. They answer different questions. The 0.80 figure is our expectation, nothing more; it decides nothing. The decision rule has stood unchanged since v0.3: if the 95% CI of the AUC includes 0.5, H1 fails, so a pass requires a lower bound above 0.5. v0.6 layers the multiplicity correction (A18/A31) on top.

**H1–H7, or "H1, A5, H12, H2, H11a"?**
None of the original v0.3 hypotheses, H1–H7, has been dropped. What v0.6 A18 does is single out five hypotheses as the confirmatory family, the set we correct for multiplicity: H1, A5, H12, H2 and H11a. The rest (H3, H5–H7, H11b, H13–H20) count as secondary. We report all of them, in full.

**76 systems or 65?**
Both numbers are right. `labels_v2` seals 76 systems, and 65 of them enter the analysis: 39 impostors and 26 substellar. Rules fixed back in v0.3 remove the other 11. Ten are unresolved or carry conflicting evidence. The eleventh, Gaia-4, we inspected during development, which disqualifies it.

**Is this still GAIA-FP v3, or something new?**
Same method. We registered v3.1 in v0.3–v0.4. v3.2 (v0.6 A25) is v3.1 with the audit's corrections, and it serves as the primary DR4 score. v3.1 runs alongside it, exactly as registered.
