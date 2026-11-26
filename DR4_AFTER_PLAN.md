# DR4 day, step 2: running the analyses registered after dr4_day.py (written before Gaia DR4)

Date: 26 Nov 2026. Status: run order only. No hypothesis, score, threshold or decision rule changes.
Code: `src/dr4_after.py`, tests `tests/test_dr4_after.py`. SHA-256 of this file: `DR4_AFTER_PLAN.sha256`.

## Why this step exists
`src/dr4_day.py` is frozen in the v0.6 manifest. It runs scoring, hashing, H11, H8, H12–H14 (with H18/H19), the
unblinding with weighted Holm, H7, H15 and H17. It does not call four analyses that were written later:

| Analysis | Plan | Code |
|---|---|---|
| H21 baseline trap | `H21_BASELINE_TRAP_PLAN.md` | `src/h21_baseline.py` |
| H22 likelihood-only AUC | `H22_LIKELIHOOD_ONLY_PLAN.md` | `src/h22_likelihood_only.py` |
| H19 desert, by mass | `H19_DESERT_PLAN.md` | `src/h19_desert.py` |
| DR4 catalogue scan | `DR4_CATALOGUE_SCAN_PLAN.md` | `src/dr4_catalogue_scan.py` |

`dr4_after.py` runs each of them with its own code and writes `DR4_SUMMARY.md`, a single table whose statuses are
copied from the JSON outputs. A failed analysis is logged as FAILED and the others still run.

## Two safeguards
1. Before anything runs, the SHA-256 of `gaiafp_dr4_catalogue.csv` must equal `catalogue_sha256` in
   `dr4_evaluation.json` (the hash checked at unblinding). If it differs, the script stops.
2. The catalogue scan removes sealed evaluation objects using `realdata/excluded_sealed_ids.csv`, which lists
   DR3 ids. DR4 ids are independent of DR3 ids, so that list alone would remove none of them from the DR4
   catalogue. `dr4_after.py` maps the DR3 ids through the DR3→DR4 map (matches within 1″, as in H21) and removes
   those DR4 rows before the scan. This carries out the scan plan's rule ("sealed evaluation objects are removed
   by id") on DR4 ids; the scan code itself is unchanged. The unit test `test_sealed_ids_follow_the_dr4_map`
   covers it.

## Order on 2 December 2026 (from `src/`)
```
python dr4_fetch.py --release gaiadr4 --out dr4_raw --user <login>
python dr4_day.py prepare --raw dr4_raw --std dr4_std
python dr4_day.py run --std dr4_std --labels <sealed labels_v2 file> --out ../dr4_out
python dr4_after.py run --std dr4_std --out ../dr4_out --labels <same file> --baseline-days <B>
```
B is the DR4 data span in days, read from the DR4 documentation on the day (expected about 2010 d). It is
written to `after_run_log.json` together with the SHA-256 of every output.

## Dry run, 26 Nov 2026
`python dr4_day.py dryrun --out /tmp/dry` completed all 14 steps in 341 s on fake DR4-like inputs with synthetic
labels; the sealed label file was not opened. `python dr4_after.py dryrun --out /tmp/dry` then completed all six
steps in 7 s and wrote `DR4_SUMMARY.md`. The numbers in that dry run come from synthetic labels and mean nothing
scientifically. Full test suite: 164 passed.
