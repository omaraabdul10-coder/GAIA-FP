# Which rules apply (read this first)

The pre-registration is a sequence of documents. Each one amends only what it names, and where two conflict, the later one applies. Frozen files are not edited, so the older documents keep their original wording on purpose.

| Order | File | Registered | What it is |
|---|---|---|---|
| 1 | `PREREGISTRATION.md` | OSF N5H4B, 9 Oct 2026 | The original plan. Its header still reads "v0.3 DRAFT" because we froze the file byte for byte as registered. |
| 2 | `PREREG_AMENDMENT_v0.4.md` | OSF N5H4B, 9 Oct 2026 | Adds H8 and A1–A5. A5 compares GAIA-FP with a CMD-only model on DR4 dynamical labels. |
| 3 | `PREREG_AMENDMENT_v0.5.md` | OSF TBJGY, 10 Oct 2026 | A6–A9. Makes the empirical RVS score primary (A7) and adds the H11 DR3→DR4 test (A8). |
| 4 | `PREREG_AMENDMENT_v0.6.md` (final; the `_DRAFT` file shows how it got there) | OSF, before DR4 | A10–A38: weighted Holm for multiplicity, H12–H20, the DR4 data model and the DR4-day rules. |

## Common questions

**Is H1 "AUC ≥ 0.80" or "lower bound > 0.5"?**
v0.3 contains both phrases, and they mean different things. The 0.80 figure is our expected value and plays no part in the decision. The decision rule has not changed since v0.3: if the 95% CI of the AUC includes 0.5, H1 fails, so a pass requires a lower bound above 0.5. v0.6 adds the multiplicity correction (A18/A31).

**H1–H7, or "H1, A5, H12, H2, H11a"?**
None of the original v0.3 hypotheses (H1–H7) has been dropped. v0.6 A18 defines five hypotheses as the confirmatory family, which is the set corrected for multiplicity: H1, A5, H12, H2 and H11a. The others (H3, H5–H7, H11b, H13–H20) are secondary. All of them are reported in full.

**76 systems or 65?**
Both numbers are right. `labels_v2` seals 76 systems, and 65 of them enter the analysis: 39 impostors and 26 substellar. The other 11 are removed by rules fixed in v0.3. Ten are unresolved or have conflicting evidence. The eleventh, Gaia-4, is excluded because we inspected it during development.

**Is this still GAIA-FP v3, or something new?**
It is the same method. We registered v3.1 in v0.3–v0.4. v3.2 (v0.6 A25) is v3.1 with the audit's corrections and is the primary DR4 score. v3.1 is run alongside it, exactly as registered.

Not frozen (presentation only, may be edited after registration): `README.md`, `index.html`, `site_checker.html` and `docs/presentation/`. They are left out of `FREEZE_MANIFEST_v0.6.sha256`.
