# Getting ready for DR4 (audit of 31 Oct 2026)

One run on 2 December 2026, start to finish, no hand fixes. That is the target. Where DR4 lacks something a hypothesis needs, that hypothesis gets reported as NOT CONDUCTED, with its reason. NOT CONDUCTED is never a FAIL.

Our information about ESA's plans comes from `audit/C_dr4_datamodel.md`, a piece of independent web research that cites its sources.

## 1. What ESA has announced, and what we still don't know
| Fact | Status | What it means for us |
|---|---|---|
| Release on 2 Dec 2026, around 12:00 CET | confirmed | — |
| The archive is closed from 25 Nov 12:00 CET until DR4 | confirmed | Every DR3 download (the H11 control group) and every live fetch test has to be done by 24 Nov. The 25 Nov deadline we had set is too late for these two. |
| Reference epoch J2017.5 (DR3 used J2016.0) | confirmed | t_periastron is probably counted from J2017.5 (+547.875 d), so epoch times need a common zero point. `dr4_adapters` handles this, and a test shows the signal disappears if the epoch is wrong. |
| DR4 source_ids are independent of DR3; the cross-match table `dr3_neighbourhood` can give 0, 1 or several counterparts | confirmed | Every step from DR3 to DR4 goes through the map (nearest within 1″), never through matching ids. Fixed in `dr4_mechanism.exclusion_ids`, `h11_outcomes` and `dr4_evaluate.map_ids`. |
| `nss_two_body_orbit` has 5 901 111 rows (DR3: 443 205); new tables `rvs_two_body_orbit` and `nss_masses` | confirmed | Solution-type names and counts aren't published yet. Unknown types are set aside rather than crashing the run. |
| Per-transit RV and line broadening in `rvs_epoch_parameters_single` / `_double`; DataLink `EPOCH_PARAMETERS_RVS_SINGLE` / `_DOUBLE` | names confirmed, columns unknown | The data H2 depends on will exist. The adapter accepts three layouts (A, A′, B) and synonyms for the column names. |
| Mean vbroad has moved to `all_source_rvs` | confirmed | The H12–H14 query has to join `all_source_rvs` instead of `gaia_source`. |
| For binaries, gaia_source parameters may come from a binary model | confirmed in principle | Parallax and RUWE may not mean quite what they meant in DR3, so we shouldn't reuse DR3 cuts without thinking; we report this. |
| DataLink names changed on 14 Oct 2026 (`INDIVIDUAL` → `DATAMODEL_STANDARD`); astroquery 0.4.11 still uses the old ones | confirmed | Pin astroquery ≥ 0.4.12 (dev) and check the version at start-up. |
| Archive limits: anonymous users get 50 000 rows and 50 ids per DataLink call; registered users get unlimited rows, 5 000 ids, 120-minute async jobs and 5 jobs at once | confirmed | The user needs to register a Gaia archive account. We can't do that for them. |
| Final DR4 data model (column names, units) | not public. We couldn't open the draft PDF (26 Jun 2026) from this workspace | To do: download `gaia-dr4-prerelease-draft-data-model_2026-06-26.zip` (the URL is in the C report) on an ordinary computer and compare it against `src/dr4_schema.py`. |

## 2. Where each component stands
| Step | Code | How it was tested | Still open |
|---|---|---|---|
| Fetch (TAP + DataLink) | `src/dr4_fetch.py` exists, with schema discovery at run time, the candidate query, provenance hashes and DataLink retrieval of epochs | reviewed by reading only; not tested live from this workspace | Run `dr4_fetch.py --release gaiadr3` from a registered Gaia Archive account with internet access before 24 Nov; check the real DR4 table and column names on release day |
| Schema and unit guard | `dr4_schema.py` | 5 tests. Real DR3 passes; a missing column, a ×1000 unit error, years given for days, eccentricity ×100, ids mangled by floats and an empty table all stop it | Swap the DR3-based expectations for the draft DR4 data model |
| RVS epoch adapter | `dr4_adapters.py` | 4 tests. The three layouts give identical arrays; an injected signal with z > 3 survives; the wrong epoch loses it; a wrong time unit and ambiguous columns stop it | Real column names |
| Scoring | `dr4_run.py` (v3.2 primary per v0.6 A25, plus registered v3.1, A6-off and A7), `rvs_v32.py` | 6 tests (monotone LLR, determinism, MC SD, invalid input) and the dry run | Parallelise (about 2 h at DR4 scale) |
| Unblinding for H1/H2/H3/H5/H8/A5, plus Holm | `dr4_evaluate.py` | 6 tests: refusals on a wrong hash, count checks, NOT_CONDUCTED paths, textbook Holm, null p-values | The H6 runner (ML baseline) is still missing |
| H11 outcomes and metrics | `h11_outcomes.py`, `h11_prepare.py` | smoke run with changed ids, vanished orbits and SB2 rows | Control group: data needed by 24 Nov |
| H8 labels | `dr4_dynamical.py` | reproduces the DR3 labels exactly (regression test) | — |
| H12–H14 | `dr4_mechanism.py` | dry run: of 3000 rows, the 1500 mapped to DR3 were excluded; n = 476 < 668, so NOT CONDUCTED | — |
| H7 | `survey_xmatch.py` (frozen) | not dry-run | Needs SB2 files with the documented column names |
| H4 | `fit_real.py`, `mcmc_orbit.py` (pre-release format) | pre-release, June 2026 | An adapter for DR4 epoch astrometry: ns times, 10-element CCD arrays, index 0 = sky mapper |

## 3. How much data, and how we'll query it (with a registered account)
Candidates first. We join `nss_two_body_orbit` with `gaia_source` and apply the frozen cuts. DR3 yielded 2192 out of 443 k, and a naive scale-up suggests 20–30 k for DR4; treat that as a guess. It fits in one async job, split by source_id range if it overruns 120 minutes.

The RVS epochs are lighter than they sound. For candidates with G_RVS ≤ 14 we call DataLink `EPOCH_PARAMETERS_RVS_SINGLE` with up to 5000 ids at a time, and the volume works out to roughly 0.5–2 GB per 10⁵ sources.

H12–H14 need the combined astrometric + SB1 solutions joined with `all_source_rvs` for vbroad. DR3 had 33 467 such solutions. DR4's count is anyone's guess.

H11 needs `dr3_neighbourhood` for the 2102 candidates and the controls, followed by their DR4 solutions. Epoch astrometry matters only for H4, and only for two sources. Epoch spectra we can skip entirely.

## 4. Fallbacks (fixed now; status words as in v0.6 A19)
| If this is missing on 2 Dec | Not conducted (reason) | Still conducted |
|---|---|---|
| Per-transit line widths | H2 (DATA_ABSENT); H11 O5 | H1, H3, H5 (with z = 0, so the RVS term is neutral), H8, H11a/b, H12–H14 (they use mean vbroad) |
| Combined astrometric + SB1 solutions | H8 (a), (b), A5; H12–H14; H11 O3 | H1–H3, H5, H11 (O1, O2, O4) |
| Mean vbroad | H12–H14 | everything else |
| `dr3_neighbourhood` | — | Fallback, fixed now: propagate DR3 positions to J2017.5 with DR3 proper motions and take the nearest source within 1″; reported as a deviation |
| Some labelled objects aren't in DR4 NSS | — | H1 on the rest. If a class drops below 10 objects: NOT CONDUCTED (BELOW_MIN_N) |
| A schema mismatch | The step affected stops. A name mapping can be added only as a logged deviation, before any score is computed | — |
| The archive is overloaded | nothing; we wait, or use a partner data centre (ARI/GAVO, AIP, CDS) and log the provenance | — |

## 5. Dry run (31 Oct 2026, `src/dr4_day.py dryrun`, log in `dryrun/dryrun_log.json`)
It took two attempts. The second, run after the auditors' fixes, finished with all 11 steps OK.

| Step | Seconds |
|---|---|
| fake inputs | 0.3 |
| RVS adapter | 0.2 |
| **scoring: v3.2 primary + v3.1 registered + A6-off + A7** | **642** |
| hash | 0.1 |
| unblinding (SYNTHETIC labels) + Holm | 2.1 |
| fake orbits | 0.1 |
| H11 (both prediction sets) | 5.6 |
| H8 labels | 1.4 |
| unblinding with H8 and the H11a p-value | 2.1 |
| H7 (string ids) | 0.4 |
| H12–H14 | 13.4 |

What did the dry-run catalogue look like? Of 2119 input candidates, 2057 were scored. Colour outside the ridge removed 45, non-finite inputs another 17. Every one of the 2057 took σ_a0 from `significance`. Null widths produced z with mean −0.008 and SD 1.002, which is what it should be. No warnings. By RVS status: 1071 OK, 787 with no epochs, 146 where A6 excluded H_t, 53 with fewer than 6 epochs.

Speed is the real risk. v3.2 spends about 0.3 s on each RVS candidate. If DR4 is about ten times DR3, scoring runs for around two hours. We can live with that, but `dr4_run` should be parallelised over candidates before 1 Dec, and since the results are order-independent by construction, nothing stops us.

Something to report rather than fix: under A6, 146 candidates lose almost every H_t draw (bright, high-K posteriors), so their RVS term says nothing. That is the registered A6 doing exactly what it says. P_impostor_noA6 shows the picture without it.

Three things the dry run cannot tell us: whether the network fetch works, what the real DR4 column names are, and whether the H4 epoch-astrometry adapter holds up.

## 6. Proposed schedule
| Date | Work | Who |
|---|---|---|
| by 7 Nov | Take in the two code auditors' findings; fix them in new files; write `dr4_fetch.py` and the H6 runner | AI code assistant |
| by 10 Nov | Register a Gaia archive account; download and read the DR4 draft data model; run the fetch test on DR3 | user (with the assistant for the script) |
| by 14 Nov | Download the control group from DR3 (needs your permission) → hash of `h11_controls.csv`; final dry run on 2 formats | team |
| 15 Nov | v0.6 final + `FREEZE_MANIFEST_v0.6` | AI code assistant |
| 15–18 Nov | User and teammate read v0.6 | user |
| **19 Nov** | OSF draft; user presses Register and approves by email | user |
| 24 Nov | Last day the Gaia archive is open | — |
| 25 Nov | Everything delivered (your deadline) | — |
| 1 Dec | Final timed dry run; log committed | AI code assistant |
| 2 Dec | DR4 | — |

## Update, 7 Nov 2026: ESA's draft DR4 data model, checked
Reading the draft turned up four differences from DR3, any one of which would have broken the run. `src/dr4_release_map.py` now absorbs them (tests in `tests/test_dr4_release_map.py`), and `src/dr4_fetch.py` requests the DR4 column names:
1. `solution_type` replaces `nss_solution_type`, the solution-type count query included.
2. `c_thiele_innes` and `h_thiele_innes` are gone, so we rebuild a1 sin i from `semi_amplitude_primary`.
3. `dr3_neighbourhood.angular_distance` comes in mas; we convert to arcsec.
4. Per-transit RVS time is `obs_time_rv` + `obs_time_bary_corr`, and only valid vbroad transits survive.

DR4-day order: fetch → `dr4_release_map` (nss, neighbourhood, rvs_epochs) → `dr4_schema.check` → runners. Since the data model is still a draft, the schema guard halts on any further change.

## Update, 8 Nov 2026: the real DR4 chain is wired (until now only the dry run was)
```
python dr4_fetch.py --release gaiadr3 --out dr3_fetch_test --user <login> --skip-rvs   # by 24 Nov: live archive test
python dr4_fetch.py --release gaiadr4 --out dr4_raw --user <login>                     # 2 Dec
python dr4_day.py prepare --raw dr4_raw --std dr4_std
python dr4_day.py run --std dr4_std --labels <path>/labels_v2_PRIVATE.json --out dr4_out
```

Fetch got bigger. It now pulls the DR3→DR4 id map (`dr3_neighbourhood`) for the DR3 candidates, the sealed ids (ids only), the DR3 AstroSpectroSB1 sources and the H11 controls. On top of that come the H11 orbits of their counterparts, the H12 combined orbits (D3) and the field vbroad sample (D2).

Id lists travel in chunks of at most 2000, and the unrestricted RVS × NSS join is gone. DR4 keeps `non_single_star` in `all_source_flags`, so the field queries join that table now, with the same criteria as before.

There is a single chain. `dr4_day.py dryrun` and `run` both call `run_chain`: score → hash → H11 → H8 → H12–H14 + H18/H19 → unblind + weighted Holm → H7 → H15 → H17. On 8 Nov the dry run went through all 13 steps in 352 s. A fake-archive test (`tests/test_dr4_fetch_prepare.py`) covers the DR4 names and the chunking, confirms that sealed ids get mapped, and confirms that `prepare` emits the standard inputs.

Don't forget the sealed label file. It has to sit at the path given to `--labels` on DR4 day, and its SHA-256 must equal `sealed/labels_v2.sha256`. If not, the run stops.
