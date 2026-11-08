"""Build the three DR4 mechanism inputs from individually fetched TAP tables.

This is a pure local preparation step (no network calls). It joins mean RVS
measurements to the orbit candidates and the field-star CMD sample using exact
string source_id keys, validates one-to-one cardinality, and records provenance.
It does not infer/rename unknown DR4 columns; schema checks belong in dr4_fetch.py.

Example:
  python src/dr4_h12_prepare.py \
    --orbits raw/candidates.csv --candidate-rvs raw/candidate_all_source_rvs.csv \
    --field-cmd raw/field.csv --field-rvs raw/field_all_source_rvs.csv \
    --out prepared_dr4_h12
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from dr4_mechanism_guarded import (
    _clean_ids, _require_columns, _require_file, PreflightError,
    validate_field_calibration,
)

CANDIDATE_RVS = {"source_id", "grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits"}
FIELD_CMD = {"source_id", "phot_g_mean_mag", "bp_rp", "parallax"}
ORBIT_CORE = {
    "source_id", "phot_g_mean_mag", "bp_rp", "parallax", "parallax_error", "period", "eccentricity",
    "a_thiele_innes", "b_thiele_innes", "f_thiele_innes", "g_thiele_innes",
    "c_thiele_innes", "h_thiele_innes",
    "a_thiele_innes_error", "b_thiele_innes_error", "f_thiele_innes_error", "g_thiele_innes_error",
    "c_thiele_innes_error", "h_thiele_innes_error",
}


def _read(path: str | Path, label: str) -> tuple[Path, pd.DataFrame]:
    p = _require_file(path, label)
    df = pd.read_csv(p, dtype={"source_id": "string"}, low_memory=False)
    _require_columns(df, {"source_id"}, label)
    df["source_id"] = _clean_ids(df["source_id"], label)
    if df["source_id"].duplicated().any():
        raise PreflightError(f"{label} contains duplicate source_id rows; refusing a many-to-many/ambiguous join")
    return p, df


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare(orbits_path: str | Path, candidate_rvs_path: str | Path,
            field_cmd_path: str | Path, field_rvs_path: str | Path,
            out_dir: str | Path) -> dict:
    po, O = _read(orbits_path, "DR4 candidate orbit table")
    pr, R = _read(candidate_rvs_path, "DR4 candidate mean-RVS table")
    pf, F = _read(field_cmd_path, "DR4 field CMD table")
    pv, V = _read(field_rvs_path, "DR4 field mean-RVS table")

    _require_columns(O, ORBIT_CORE, "DR4 candidate orbit table")
    _require_columns(R, CANDIDATE_RVS, "DR4 candidate mean-RVS table")
    _require_columns(F, FIELD_CMD, "DR4 field CMD table")
    _require_columns(V, CANDIDATE_RVS, "DR4 field mean-RVS table")

    extra_candidate_rvs = set(R.source_id) - set(O.source_id)
    if extra_candidate_rvs:
        raise PreflightError(f"candidate RVS table contains {len(extra_candidate_rvs)} IDs absent from orbit table")
    extra_field_rvs = set(V.source_id) - set(F.source_id)
    # all_source_rvs may be queried over a broader field cone; retain only exact IDs
    # in the registered CMD field table, but record how many were outside it.
    candidate_join = O.merge(R[list(CANDIDATE_RVS)], on="source_id", how="left", validate="one_to_one", indicator=True)
    missing_candidate_rvs = int((candidate_join["_merge"] == "left_only").sum())
    candidate_join = candidate_join.drop(columns="_merge")

    field_rvs = V.merge(F[list(FIELD_CMD)], on="source_id", how="inner", validate="one_to_one")
    field_calibration = validate_field_calibration(F, field_rvs)

    # Do not permit null in the candidate orbit fields needed by the physical labels.
    for col in ORBIT_CORE - {"source_id"}:
        x = pd.to_numeric(candidate_join[col], errors="coerce")
        invalid_text = candidate_join[col].notna() & x.isna()
        if invalid_text.any() or not x.notna().all():
            raise PreflightError(f"candidate orbit input column {col} has non-numeric or missing values")
        candidate_join[col] = x

    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    cand_out = out / "dr4_new_orbits.csv"
    cmd_out = out / "dr4_field_cmd.csv"
    vb_out = out / "dr4_field_vbroad.csv"
    candidate_join.to_csv(cand_out, index=False)
    F.to_csv(cmd_out, index=False)
    field_rvs.to_csv(vb_out, index=False)

    report = {
        "status": "PREPARED_LOCAL_INPUTS_NOT_SCIENTIFICALLY_VALIDATED",
        "inputs": {
            "orbits": {"path": str(po), "rows": len(O), "sha256": _sha(po)},
            "candidate_rvs": {"path": str(pr), "rows": len(R), "sha256": _sha(pr)},
            "field_cmd": {"path": str(pf), "rows": len(F), "sha256": _sha(pf)},
            "field_rvs": {"path": str(pv), "rows": len(V), "sha256": _sha(pv)},
        },
        "outputs": {
            cand_out.name: {"rows": len(candidate_join), "sha256": _sha(cand_out)},
            cmd_out.name: {"rows": len(F), "sha256": _sha(cmd_out)},
            vb_out.name: {"rows": len(field_rvs), "sha256": _sha(vb_out)},
        },
        "candidate_rows_without_mean_rvs": missing_candidate_rvs,
        "field_rvs_rows_outside_cmd_field": len(extra_field_rvs),
        "field_rvs_rows_joined": len(field_rvs),
        "field_calibration": field_calibration,
        "note": "No DR4 data were fetched or analysed by this local join utility. Run dr4_mechanism_guarded.py only after the exact full DR3 exclusion table, sealed IDs, ID map, and released DR4 schemas are verified.",
    }
    (out / "preparation_provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prepare DR4 H12-H14 mechanism inputs from validated TAP extracts")
    ap.add_argument("--orbits", required=True)
    ap.add_argument("--candidate-rvs", required=True)
    ap.add_argument("--field-cmd", required=True)
    ap.add_argument("--field-rvs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        print(json.dumps(prepare(a.orbits, a.candidate_rvs, a.field_cmd, a.field_rvs, a.out), indent=2))
    except PreflightError as exc:
        ap.error(f"PREPARATION STOP: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
