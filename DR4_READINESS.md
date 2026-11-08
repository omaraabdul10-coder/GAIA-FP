# DR4 readiness (audit of 31 Oct 2026)

**Goal:** on 2 December 2026 the pipeline runs once, without hand fixes. If something DR4 needs does not exist, the affected hypothesis is reported as NOT CONDUCTED with a reason. NOT CONDUCTED is never FAIL.

The ESA facts below come from `audit/C_dr4_datamodel.md` (independent web research, with sources).

## 1. What ESA has announced (and what is still unknown)
| Fact | Status | Consequence for us |
|---|---|---|
| Release 2 Dec 2026, ~12:00 CET | confirmed | — |
| **Archive closed from 25 Nov 12:00 CET until DR4** | confirmed | **Every DR3 download (H11 control group) and every live fetch test must be finished by 24 Nov.** The user's deadline of 25 Nov is too late for these two items. |
| Reference epoch J2017.5 (DR3: J2016.0) | confirmed | t_periastron is probably relative to J2017.5 (+547.875 d). Epoch times must be put on the same zero point. `dr4_adapters` does this, and a test shows the signal is lost with the wrong epoch. |
| DR4 source_ids independent of DR3; cross-match table `dr3_neighbourhood` (0, 1 or more counterparts) | confirmed | Every DR3 → DR4 step uses the map (nearest within 1″). Never equality of ids. Fixed in `dr4_mechanism.exclusion_ids`, `h11_outcomes`, `dr4_evaluate.map_ids`. |
| `nss_two_body_orbit`: 5 901 111 rows (DR3: 443 205); new `rvs_two_body_orbit`, `nss_masses` | confirmed | Solution-type names and counts not yet published. Unknown types are quarantined, not crashed on. |
| Per-transit RV **and line broadening**: `rvs_epoch_parameters_single` / `_double`; DataLink `EPOCH_PARAMETERS_RVS_SINGLE` / `_DOUBLE` | confirmed (names), columns unknown | The core of H2 exists. The adapter accepts three layouts (A, A′, B) and column-name synonyms. |
| Mean vbroad moved to `all_source_rvs` | confirmed | The H12–H14 query must join `all_source_rvs`, not `gaia_source`. |
| gaia_source parameters may come from a binary model for binaries | confirmed in principle | parallax/RUWE semantics may differ from DR3. Do not reuse DR3 cuts blindly; report. |
| DataLink renames on 14 Oct 2026 (`INDIVIDUAL` → `DATAMODEL_STANDARD`); astroquery 0.4.11 still uses the old names | confirmed | Pin astroquery ≥ 0.4.12 (dev) and check at start-up. |
| Archive limits: anonymous 50 000 rows and 50 ids per DataLink call; **registered**: unlimited rows, 5 000 ids, 120-min async, 5 concurrent jobs | confirmed | **The user must register a Gaia archive account** (we cannot do this for them). |
| Final DR4 data model (column names, units) | **NOT public**. The draft PDF (26 Jun 2026) could not be read from this workspace | **Action:** download `gaia-dr4-prerelease-draft-data-model_2026-06-26.zip` (URL in the C report) on a normal computer and check it against `src/dr4_schema.py`. |

## 2. Component status
| Step | Code | Tested how | Open |
|---|---|---|---|
| Fetch (TAP + DataLink) | `src/dr4_fetch.py` exists with runtime schema discovery, candidate query, provenance hashes, and epoch DataLink retrieval | static review only; not live-tested in this workspace | Test `dr4_fetch.py --release gaiadr3` from an internet-connected registered Gaia Archive account before 24 Nov; validate actual DR4 table/column names on release day |
| Schema/unit guard | `dr4_schema.py` | 5 tests: real DR3 passes; missing column, ×1000 unit error, years-for-days, eccentricity ×100, float-mangled ids, empty table all stop | Replace the DR3-based expectations with the draft DR4 data model |
| RVS epoch adapter | `dr4_adapters.py` | 4 tests: three layouts give identical arrays; injected signal z > 3 survives; wrong epoch loses it; wrong time unit and ambiguous columns stop | Real column names |
| Scoring | `dr4_run.py` (v3.2 primary per v0.6 A25 + registered v3.1 + A6-off + A7), `rvs_v32.py` | 6 tests (monotone LLR, determinism, MC SD, invalid input) + dry run | parallelise (≈ 2 h on DR4 scale) |
| Unblinding H1/H2/H3/H5/H8/A5 + Holm | `dr4_evaluate.py` | 6 tests: hash refusals, count assertions, NOT_CONDUCTED paths, textbook Holm, null p-values | H6 runner (ML baseline) still missing |
| H11 outcomes + metrics | `h11_outcomes.py`, `h11_prepare.py` | smoke run with ids changed, vanished orbits, SB2 rows | Control group: data needed by 24 Nov |
| H8 labels | `dr4_dynamical.py` | **reproduces the DR3 labels exactly** (regression test) | — |
| H12–H14 | `dr4_mechanism.py` | dry run: of 3000 rows, the 1500 DR3-mapped ones were excluded; n = 476 < 668 → NOT CONDUCTED | — |
| H7 | `survey_xmatch.py` (frozen) | not dry-run | needs SB2 files with the documented column names |
| H4 | `fit_real.py`, `mcmc_orbit.py` (pre-release format) | pre-release, June 2026 | adapter for DR4 epoch astrometry: ns times, 10-element CCD arrays, index 0 = sky mapper |

## 3. Data volume and query plan (registered account)
- **Candidates:** `nss_two_body_orbit` ⋈ `gaia_source` with the frozen cuts. DR3 gave 2192 of 443 k; scaled, DR4 gives perhaps 20–30 k (estimate). One async job; split by source_id ranges if it exceeds 120 min.
- **RVS epochs** for candidates with G_RVS ≤ 14: DataLink `EPOCH_PARAMETERS_RVS_SINGLE`, ≤ 5000 ids per call. Roughly 0.5–2 GB per 10⁵ sources, so small.
- **H12–H14:** combined astrometric + SB1 solutions ⋈ `all_source_rvs` (vbroad). DR3 had 33 467; DR4 is unknown.
- **H11:** `dr3_neighbourhood` for 2102 candidates + controls, then their DR4 solutions.
- Epoch astrometry (H4 only): two sources. Epoch spectra: not needed.

## 4. Fallback plan (fixed now; status words from v0.6 A19)
| What is missing on 2 Dec | Not conducted (reason) | Still conducted |
|---|---|---|
| Per-transit line widths | H2 (DATA_ABSENT); H11 O5 | H1, H3, H5 (with z = 0: the RVS term is neutral), H8, H11a/b, H12–H14 (they use mean vbroad) |
| Combined astrometric + SB1 solutions | H8 (a), (b), A5; H12–H14; H11 O3 | H1–H3, H5, H11 (O1, O2, O4) |
| Mean vbroad | H12–H14 | everything else |
| `dr3_neighbourhood` | — | Fallback, fixed now: positional match after propagating DR3 positions to J2017.5 with DR3 proper motions, nearest within 1″; reported as a deviation |
| Some labelled objects absent from DR4 NSS | — | H1 on the remainder. If a class has < 10 objects: NOT CONDUCTED (BELOW_MIN_N) |
| A schema mismatch | the affected step stops. A name mapping may be added **only** as a logged deviation, before any score is computed | — |
| Archive overloaded | nothing; wait or use a partner data centre (ARI/GAVO, AIP, CDS), with the provenance logged | — |

## 5. Dry run (31 Oct 2026, `src/dr4_day.py dryrun`, log `dryrun/dryrun_log.json`)
**Result: COMPLETED, all 11 steps OK** (second run, after the auditors' fixes).

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

**Checks on the dry-run catalogue:**
- 2119 input candidates, 2057 scored: 45 dropped for colour outside the ridge, 17 for non-finite inputs.
- σ_a0 came from `significance` for all 2057.
- Null widths give z with mean −0.008 and SD 1.002.
- No warnings were recorded.
- RVS status: OK 1071, no epochs 787, H_t excluded by A6 146, fewer than 6 epochs 53.

**Timing risk:**
- The v3.2 scoring costs about 0.3 s per RVS candidate.
- With DR4 at about 10× DR3, scoring is about 2 hours. That is acceptable, but `dr4_run` should be parallelised over candidates before 1 Dec; the results are order-independent by construction.

**Observation to report:** under A6, 146 candidates have almost every H_t draw excluded (bright, high-K posteriors), so their RVS term is "no information". This is a consequence of the registered A6, not a bug. P_impostor_noA6 shows what happens without A6.

**Not covered by the dry run:**
- the network fetch;
- the real DR4 column names;
- the H4 epoch-astrometry adapter.

## 6. Schedule (proposed)
| Date | Work | Who |
|---|---|---|
| by 7 Nov | Integrate the two code auditors' findings; fix in new files; write `dr4_fetch.py` and the H6 runner | AI code assistant |
| by 10 Nov | User registers a Gaia archive account; downloads and reads the DR4 draft data model; runs the fetch test on DR3 | user (+ assistant for the script) |
| by 14 Nov | Control-group DR3 download (**needs your permission**) → `h11_controls.csv` hash; final dry run on 2 formats | team |
| 15 Nov | v0.6 final + `FREEZE_MANIFEST_v0.6` | AI code assistant |
| 15–18 Nov | User and teammate read v0.6 | user |
| **19 Nov** | OSF draft; user presses Register and approves by email | user |
| 24 Nov | **Last day the Gaia archive is open** | — |
| 25 Nov | All deliverables done (your deadline) | — |
| 1 Dec | Final timed dry run; log committed | AI code assistant |
| 2 Dec | DR4 | — |

## Update 7 Nov 2026: ESA draft DR4 data model checked
Four breaking differences from DR3 were found and are handled by `src/dr4_release_map.py` (tests in `tests/test_dr4_release_map.py`); `src/dr4_fetch.py` now requests the DR4 column names:
1. `solution_type` replaces `nss_solution_type` (also in the solution-type count query).
2. No `c_thiele_innes`/`h_thiele_innes`: a1 sin i is rebuilt from `semi_amplitude_primary`.
3. `dr3_neighbourhood.angular_distance` is in mas (converted to arcsec).
4. Per-transit RVS time = `obs_time_rv` + `obs_time_bary_corr`; only valid vbroad transits are kept.
DR4-day order: fetch → `dr4_release_map` (nss, neighbourhood, rvs_epochs) → `dr4_schema.check` → runners. The data model is a draft; the schema guard still stops on any further change.

## Update 8 Nov 2026: the real DR4 chain is wired (previously only the dry run was)
```
python dr4_fetch.py --release gaiadr3 --out dr3_fetch_test --user <login> --skip-rvs   # by 24 Nov: live archive test
python dr4_fetch.py --release gaiadr4 --out dr4_raw --user <login>                     # 2 Dec
python dr4_day.py prepare --raw dr4_raw --std dr4_std
python dr4_day.py run --std dr4_std --labels <path>/labels_v2_PRIVATE.json --out dr4_out
```
- **Fetch now also downloads:**
  - the DR3→DR4 id map (`dr3_neighbourhood`) for DR3 candidates, sealed ids (ids only), DR3 AstroSpectroSB1 and H11 controls;
  - the H11 orbits of their counterparts;
  - the H12 combined orbits (D3) and the field vbroad sample (D2).
- **Query limits:** every id list is sent in chunks of ≤ 2000 ids. The unrestricted RVS × NSS join is gone.
- **DR4 data model:** `non_single_star` is in `all_source_flags`; the field queries join it (same criteria).
- **One chain:** `dr4_day.py dryrun` and `run` call the same `run_chain`:
  - score → hash → H11 → H8 → H12–H14 + H18/H19 → unblind + weighted Holm → H7 → H15 → H17.
  - Dry run 8 Nov: COMPLETED, 13 steps, 352 s.
- **Tests:** a fake-archive test (`tests/test_dr4_fetch_prepare.py`) checks the DR4 names, the chunking, that sealed ids are mapped, and that `prepare` produces the standard inputs.
- **The sealed label file is needed on DR4 day** at the path given to `--labels`. Its SHA-256 must equal `sealed/labels_v2.sha256`, or the run stops.
