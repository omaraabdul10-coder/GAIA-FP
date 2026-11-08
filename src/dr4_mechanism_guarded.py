"""Fail-closed preflight for the frozen v0.6 DR4 mechanism runner.

This wrapper does not alter scientific calculations or thresholds in dr4_mechanism.py.
It validates the full DR4 input contract, requires an explicit DR3--DR4 ID map,
normalizes that map to the nearest counterpart within 1 arcsec, and only then
hands the files to the existing runner.

Run from any directory:
  PYTHONPATH=src python src/dr4_mechanism_guarded.py \
    dr4_new_orbits.csv dr4_field_cmd.csv dr4_field_vbroad.csv \
    --idmap dr3_dr4_idmap.csv
"""
from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


class PreflightError(RuntimeError):
    """Raised when an input violates the frozen DR4 input contract."""


ID_RE = re.compile(r"^[0-9]+$")

ORBIT_REQUIRED = {
    "source_id", "phot_g_mean_mag", "bp_rp", "parallax", "parallax_error",
    "period", "eccentricity",
    "a_thiele_innes", "b_thiele_innes", "f_thiele_innes", "g_thiele_innes",
    "c_thiele_innes", "h_thiele_innes",
    "a_thiele_innes_error", "b_thiele_innes_error", "f_thiele_innes_error",
    "g_thiele_innes_error", "c_thiele_innes_error", "h_thiele_innes_error",
    "grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits",
}
FIELD_CMD_REQUIRED = {"phot_g_mean_mag", "bp_rp", "parallax"}
FIELD_RVS_REQUIRED = {"source_id", "grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits"}
IDMAP_REQUIRED = {"dr3_source_id", "dr4_source_id", "angular_distance_arcsec"}


def _require_file(path: str | Path, label: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise PreflightError(f"{label} file is missing: {p}")
    if p.stat().st_size == 0:
        raise PreflightError(f"{label} file is empty: {p}")
    return p


def _require_columns(df: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise PreflightError(f"{label} is missing required columns: {', '.join(missing)}")


def _clean_ids(series: pd.Series, label: str) -> pd.Series:
    # Read IDs as strings from disk; reject float-mangled identifiers such as 123.0.
    x = series.astype("string").str.strip()
    bad = x.isna() | ~x.str.fullmatch(ID_RE.pattern, na=False)
    if bad.any():
        examples = x[bad].head(3).tolist()
        raise PreflightError(f"{label} contains invalid/non-decimal Gaia source_id values: {examples}")
    return x


def _read_csv(path: Path, id_columns: Iterable[str] = ()) -> pd.DataFrame:
    dtype = {c: "string" for c in id_columns}
    return pd.read_csv(path, dtype=dtype, low_memory=False)


def normalize_idmap(path: str | Path, output_path: str | Path) -> dict:
    """Validate map and write one nearest <=1-arcsec counterpart per DR3 ID."""
    p = _require_file(path, "DR3--DR4 ID map")
    m = _read_csv(p, ("dr3_source_id", "dr4_source_id"))
    _require_columns(m, IDMAP_REQUIRED, "DR3--DR4 ID map")
    m["dr3_source_id"] = _clean_ids(m["dr3_source_id"], "ID map dr3_source_id")
    m["dr4_source_id"] = _clean_ids(m["dr4_source_id"], "ID map dr4_source_id")
    m["angular_distance_arcsec"] = pd.to_numeric(m["angular_distance_arcsec"], errors="coerce")
    if not np.isfinite(m["angular_distance_arcsec"].to_numpy(dtype=float)).all():
        raise PreflightError("ID map angular_distance_arcsec contains non-finite/non-numeric values")
    if (m["angular_distance_arcsec"] < 0).any():
        raise PreflightError("ID map angular_distance_arcsec cannot be negative")
    n_input = len(m)
    m = m[m["angular_distance_arcsec"] <= 1.0].copy()
    if m.empty:
        raise PreflightError("ID map has no DR3--DR4 matches within the preregistered 1-arcsec radius")
    # Stable nearest-neighbour selection for each DR3 source. Ties are deterministic.
    m = m.sort_values(["dr3_source_id", "angular_distance_arcsec", "dr4_source_id"], kind="mergesort")
    m = m.drop_duplicates("dr3_source_id", keep="first")
    # One DR4 counterpart must not ambiguously represent multiple DR3 sources.
    duplicated_dr4 = m["dr4_source_id"].duplicated(keep=False)
    if duplicated_dr4.any():
        examples = m.loc[duplicated_dr4, ["dr3_source_id", "dr4_source_id"]].head(4).to_dict("records")
        raise PreflightError(f"ID map is not one-to-one after nearest-match selection; examples: {examples}")
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(out, index=False)
    return {"input_rows": n_input, "within_1arcsec_rows": int((pd.to_numeric(_read_csv(p)["angular_distance_arcsec"], errors="coerce") <= 1).sum()),
            "unique_dr3_matches": len(m), "normalized_path": str(out)}


def validate_field_calibration(field_cmd: pd.DataFrame, field_vbroad: pd.DataFrame) -> dict:
    """Run the project's own CMD ridge and vbroad calibration on the proposed DR4 inputs."""
    import dr4_pipeline as D
    import dark_companion as DC

    _require_columns(field_cmd, FIELD_CMD_REQUIRED | {"source_id"}, "DR4 field CMD table")
    _require_columns(field_vbroad, FIELD_RVS_REQUIRED | FIELD_CMD_REQUIRED, "joined DR4 field vbroad table")
    if field_cmd["source_id"].duplicated().any():
        raise PreflightError("DR4 field CMD table contains duplicate source_id rows")

    for col in FIELD_CMD_REQUIRED:
        raw = field_cmd[col]
        parsed = pd.to_numeric(raw, errors="coerce")
        if (raw.notna() & parsed.isna()).any() or not np.isfinite(parsed.to_numpy(dtype=float)).all():
            raise PreflightError(f"DR4 field CMD column {col} has non-numeric or missing values")
        field_cmd[col] = parsed
    if (field_cmd["parallax"] <= 0).any():
        raise PreflightError("DR4 field CMD table has non-positive parallaxes")

    ridge = D.fit_ms_ridge(field_cmd)
    if not (np.isfinite(ridge["color"]).all() and np.isfinite(ridge["ridge"]).all() and
            np.isfinite(ridge["sigma"]).all() and (ridge["sigma"] > 0).all()):
        raise PreflightError("DR4 field CMD table cannot produce a finite, non-zero-scatter 40-bin main-sequence ridge")

    for col in ("grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits"):
        raw = field_vbroad[col]
        parsed = pd.to_numeric(raw, errors="coerce")
        if (raw.notna() & parsed.isna()).any():
            raise PreflightError(f"DR4 field vbroad column {col} contains non-numeric values")
        vals = parsed.dropna().to_numpy(dtype=float)
        if not np.isfinite(vals).all():
            raise PreflightError(f"DR4 field vbroad column {col} contains infinite values")
        field_vbroad[col] = parsed
    for col in FIELD_CMD_REQUIRED:
        raw = field_vbroad[col]
        parsed = pd.to_numeric(raw, errors="coerce")
        if (raw.notna() & parsed.isna()).any() or not np.isfinite(parsed.to_numpy(dtype=float)).all():
            raise PreflightError(f"joined DR4 field vbroad column {col} has non-numeric or missing values")
        field_vbroad[col] = parsed
    if (field_vbroad["parallax"] <= 0).any():
        raise PreflightError("joined DR4 field vbroad table has non-positive parallaxes")

    MG = field_vbroad.phot_g_mean_mag + 5*np.log10(field_vbroad.parallax/100.0)
    msf = ((field_vbroad.bp_rp >= ridge["color"].min()) &
           (field_vbroad.bp_rp <= ridge["color"].max()) &
           (MG > np.interp(field_vbroad.bp_rp, ridge["color"], ridge["ridge"]) - 2.0))
    cal_input = field_vbroad[msf & np.isfinite(field_vbroad.vbroad) &
                            np.isfinite(field_vbroad.bp_rp) & np.isfinite(field_vbroad.grvs_mag) &
                            (field_vbroad.vbroad_nb_transits >= 5)]
    cal = DC.vb_field(cal_input)
    usable = {(int(i), int(j)) for (i, j), (_, sig, n) in cal[2].items()
              if np.isfinite(sig) and sig > 0 and n >= 30}
    covered = {i for i, _ in usable}
    if len(covered) != 15:
        raise PreflightError(f"DR4 field vbroad calibration covers {len(covered)}/15 colour bins with positive scatter; refusing incomplete calibration")
    return {"field_cmd_rows": int(len(field_cmd)), "field_vbroad_joined_rows": int(len(field_vbroad)),
            "main_sequence_rvs_rows": int(len(cal_input)), "usable_vbroad_cells": int(len(usable)),
            "covered_colour_bins": int(len(covered))}


def validate_inputs(orbits_path: str | Path, field_cmd_path: str | Path,
                    field_vbroad_path: str | Path, idmap_path: str | Path,
                    project_root: str | Path) -> dict:
    """Validate required inputs, and return paths/metadata for the runner."""
    root = Path(project_root).expanduser().resolve()
    orbits_p = _require_file(orbits_path, "DR4 combined orbit table")
    cmd_p = _require_file(field_cmd_path, "DR4 field CMD table")
    vb_p = _require_file(field_vbroad_path, "DR4 field vbroad table")
    dr3_full_p = _require_file(root / "realdata" / "dr3_astrospectro_all.csv", "Full DR3 AstroSpectroSB1 exclusion table")
    sealed_p = _require_file(root / "realdata" / "excluded_sealed_ids.csv", "Sealed-ID list")

    # Verify the full DR3 exclusion population before expensive DR4 validation.
    D3 = _read_csv(dr3_full_p, ("source_id",))
    _require_columns(D3, {"source_id"}, "Full DR3 AstroSpectroSB1 exclusion table")
    D3["source_id"] = _clean_ids(D3["source_id"], "Full DR3 AstroSpectroSB1 exclusion table")
    if len(D3) <= 1000:
        raise PreflightError(f"DR3 AstroSpectroSB1 exclusion file has only {len(D3)} rows; it may be the 95-row schema fixture, not the required full source table")
    if D3["source_id"].duplicated().any():
        raise PreflightError("Full DR3 AstroSpectroSB1 exclusion table contains duplicate source_id rows")
    S = _read_csv(sealed_p, ("source_id",))
    _require_columns(S, {"source_id"}, "Sealed-ID list")
    S["source_id"] = _clean_ids(S["source_id"], "Sealed-ID list")

    O = _read_csv(orbits_p, ("source_id",))
    _require_columns(O, ORBIT_REQUIRED, "DR4 combined orbit table")
    O["source_id"] = _clean_ids(O["source_id"], "DR4 combined orbit table")
    if O["source_id"].duplicated().any():
        raise PreflightError("DR4 combined orbit table contains duplicate source_id rows")
    if O.empty:
        raise PreflightError("DR4 combined orbit table contains no rows")

    F = _read_csv(cmd_p, ("source_id",))
    _require_columns(F, FIELD_CMD_REQUIRED, "DR4 field CMD table")
    if len(F) < 40:
        raise PreflightError(f"DR4 field CMD table has only {len(F)} rows; fewer than the 40 ridge bins")

    V = _read_csv(vb_p, ("source_id",))
    _require_columns(V, FIELD_RVS_REQUIRED, "DR4 field vbroad table")
    V["source_id"] = _clean_ids(V["source_id"], "DR4 field vbroad table")
    if V["source_id"].duplicated().any():
        raise PreflightError("DR4 field vbroad table has duplicate source_id rows; resolve archive multiplicity explicitly")
    # Underlying dr4_mechanism expects the CMD attributes on its field-vbroad input.
    if not FIELD_CMD_REQUIRED.issubset(V.columns):
        if "source_id" not in F.columns:
            raise PreflightError("DR4 field CMD table must include source_id so it can be joined to field vbroad")
        F["source_id"] = _clean_ids(F["source_id"], "DR4 field CMD table")
        if F["source_id"].duplicated().any():
            raise PreflightError("DR4 field CMD table has duplicate source_id rows; refusing a many-to-many calibration join")
        joined = V.merge(F[["source_id", *sorted(FIELD_CMD_REQUIRED)]], on="source_id", how="inner", validate="one_to_one")
        if len(joined) < 30:
            raise PreflightError(f"Only {len(joined)} field vbroad sources join to field CMD; fewer than one 30-source calibration cell")
        # Store a deterministic joined file next to the other inputs.
        joined_p = root / "results" / "qa2" / "dr4_field_vbroad_joined_preflight.csv"
        joined_p.parent.mkdir(parents=True, exist_ok=True)
        joined.to_csv(joined_p, index=False)
        vb_p = joined_p
    else:
        # Even if the input already contains the columns, still run the same
        # calibration checks used by the scientific pipeline below.
        pass

    # Validate that the field data can actually produce the registered CMD ridge
    # and all vbroad calibration colour bins. Merely checking filenames/columns
    # would allow an empty or under-populated calibration to pass preflight.
    V_joined = _read_csv(vb_p, ("source_id",))
    V_joined["source_id"] = _clean_ids(V_joined["source_id"], "DR4 field vbroad table")
    calibration_meta = validate_field_calibration(F, V_joined)

    # The orbit and dynamical-label columns must be finite. Mean RVS fields are
    # allowed to be null for sources without usable RVS measurements; h10 filters
    # those rows by vbroad_nb_transits and finite calibration values.
    core_numeric = (ORBIT_REQUIRED - {"source_id", "grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits"})
    optional_numeric = {"grvs_mag", "vbroad", "vbroad_error", "vbroad_nb_transits"}
    for col in core_numeric | optional_numeric:
        raw = O[col]
        parsed = pd.to_numeric(raw, errors="coerce")
        non_numeric = raw.notna() & parsed.isna()
        if non_numeric.any():
            raise PreflightError(f"DR4 orbit table column {col} contains non-numeric values")
        O[col] = parsed
    if not np.isfinite(O[list(core_numeric)].to_numpy(dtype=float)).all():
        raise PreflightError("DR4 combined orbit table has NaN/inf in required orbital/photometric/dynamical columns")
    for col in optional_numeric:
        vals = O[col].dropna().to_numpy(dtype=float)
        if not np.isfinite(vals).all():
            raise PreflightError(f"DR4 orbit table column {col} contains infinite values")
    if ((O["parallax"] <= 0) | (O["parallax_error"] <= 0) | (O["period"] <= 0) |
        (O["eccentricity"] < 0) | (O["eccentricity"] >= 1) | (O["vbroad_nb_transits"].dropna() < 0).any()).any():
        raise PreflightError("DR4 orbit table violates basic physical/data-domain constraints")

    # Build a normalized nearest-neighbour ID map in a private temporary file.
    tmp = tempfile.NamedTemporaryFile(prefix="gaiafp_idmap_", suffix=".csv", delete=False)
    tmp.close()
    idmap_meta = normalize_idmap(idmap_path, tmp.name)
    return {"orbits": str(orbits_p), "field_cmd": str(cmd_p), "field_vbroad": str(vb_p),
            "idmap_normalized": tmp.name, "dr3_exclusion_rows": len(D3), "sealed_rows": len(S),
            "dr4_orbit_rows": len(O), "field_cmd_rows": len(F), "field_vbroad_rows": len(V),
            "idmap": idmap_meta, "field_calibration": calibration_meta,
            "field_vbroad_joined_rows": int(calibration_meta["field_vbroad_joined_rows"])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fail-closed wrapper for the frozen GAIA-FP v0.6 DR4 mechanism analysis")
    ap.add_argument("orbits", help="DR4 combined astrometric + SB1 orbit table")
    ap.add_argument("field_cmd", help="DR4 field-star CMD calibration table")
    ap.add_argument("field_vbroad", help="DR4 field-star all_source_rvs calibration table")
    ap.add_argument("--idmap", required=True, help="official DR3--DR4 cross-match or preregistered positional fallback")
    ap.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]), help="GAIA-FP project root")
    args = ap.parse_args(argv)

    root = Path(args.project_root).expanduser().resolve()
    try:
        report = validate_inputs(args.orbits, args.field_cmd, args.field_vbroad, args.idmap, root)
    except PreflightError as exc:
        ap.error(f"PREFLIGHT STOP: {exc}")
        return 2

    # Run the frozen implementation from src/ because it uses ../realdata and ../results.
    import dr4_mechanism
    original_cwd = Path.cwd()
    try:
        os.chdir(root / "src")
        dr4_mechanism.main([report["orbits"], report["field_cmd"], report["field_vbroad"], "--idmap", report["idmap_normalized"]])
    finally:
        os.chdir(original_cwd)
        try:
            os.unlink(report["idmap_normalized"])
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
