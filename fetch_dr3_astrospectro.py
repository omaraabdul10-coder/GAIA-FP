#!/usr/bin/env python3
"""Rebuild the DR3 AstroSpectroSB1 D3 table used by dark_companion.h10.

Source catalogues: VizieR I/357/tboasb1c joined to I/355/gaiadr3 on Source.
The query is asynchronous because the resulting table has ~33k rows.

This script DOES NOT remove sealed IDs from the downloaded source table: the
frozen analysis function dark_companion.h10 excludes them before deriving any
labels. The output is saved only after schema and row-count checks pass.

Run on a machine with VizieR TAP access:
  python tools/fetch_dr3_astrospectro.py --out realdata/dr3_astrospectro_all.csv
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap"
EXPECTED_ROWS = 33464  # archived pre-sealed D3 query count; mismatch is a hard stop by default

QUERY = r'''SELECT
  o.Source AS source_id,
  'AstroSpectroSB1' AS nss_solution_type,
  o.Per AS period,
  o.e_Per AS period_error,
  o.ecc AS eccentricity,
  o.e_ecc AS eccentricity_error,
  o.Tperi AS t_periastron,
  o.ATI AS a_thiele_innes,
  o.BTI AS b_thiele_innes,
  o.FTI AS f_thiele_innes,
  o.GTI AS g_thiele_innes,
  o.e_ATI AS a_thiele_innes_error,
  o.e_BTI AS b_thiele_innes_error,
  o.e_FTI AS f_thiele_innes_error,
  o.e_GTI AS g_thiele_innes_error,
  o.CTI AS c_thiele_innes,
  o.HTI AS h_thiele_innes,
  o.e_CTI AS c_thiele_innes_error,
  o.e_HTI AS h_thiele_innes_error,
  o.Plx AS parallax,
  o.e_Plx AS parallax_error,
  g.Gmag AS phot_g_mean_mag,
  g."BP-RP" AS bp_rp,
  g.RUWE AS ruwe,
  g.Vbroad AS vbroad,
  g.e_Vbroad AS vbroad_error,
  g.o_Vbroad AS vbroad_nb_transits,
  g.GRVSmag AS grvs_mag
FROM "I/357/tboasb1c" AS o
JOIN "I/355/gaiadr3" AS g ON g.Source = o.Source
WHERE o.e_Plx > 0 AND o.Plx/o.e_Plx > 10'''

REQUIRED = {
    "source_id", "nss_solution_type", "period", "period_error", "eccentricity",
    "eccentricity_error", "t_periastron", "a_thiele_innes", "b_thiele_innes",
    "f_thiele_innes", "g_thiele_innes", "a_thiele_innes_error",
    "b_thiele_innes_error", "f_thiele_innes_error", "g_thiele_innes_error",
    "c_thiele_innes", "h_thiele_innes", "c_thiele_innes_error",
    "h_thiele_innes_error", "parallax", "parallax_error", "phot_g_mean_mag",
    "bp_rp", "ruwe", "vbroad", "vbroad_error", "vbroad_nb_transits", "grvs_mag",
}


def validate_d3(df: pd.DataFrame, expected_rows: int | None = EXPECTED_ROWS) -> pd.DataFrame:
    if df.empty:
        raise ValueError("VizieR D3 query returned zero rows")
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise ValueError(f"D3 query missing required columns: {missing}")
    out = df.copy()
    out["source_id"] = out["source_id"].astype("string").str.strip()
    if out["source_id"].isna().any() or (out["source_id"] == "").any():
        raise ValueError("D3 source_id contains null/empty values")
    if out["source_id"].duplicated().any():
        raise ValueError("D3 query returned duplicate source_id rows")
    numeric = REQUIRED - {"source_id", "nss_solution_type"}
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    core = [
        "period", "eccentricity", "a_thiele_innes", "b_thiele_innes",
        "f_thiele_innes", "g_thiele_innes", "c_thiele_innes", "h_thiele_innes",
        "parallax", "parallax_error", "phot_g_mean_mag", "bp_rp",
    ]
    if out[core].isna().any().any():
        bad = [c for c in core if out[c].isna().any()]
        raise ValueError(f"D3 mandatory physical/photometric columns contain nulls: {bad}")
    if (out["period"] <= 0).any() or (out["parallax"] <= 0).any() or (out["parallax_error"] <= 0).any():
        raise ValueError("D3 period/parallax/error domain check failed")
    if not out["nss_solution_type"].eq("AstroSpectroSB1").all():
        raise ValueError("D3 table contains a non-AstroSpectroSB1 solution type")
    if expected_rows is not None and len(out) != expected_rows:
        raise ValueError(f"D3 row-count mismatch: expected {expected_rows}, received {len(out)}; output not written")
    return out


def run_async(query: str = QUERY, max_wait: int = 3600, poll_seconds: int = 10):
    r = requests.post(
        VIZIER_TAP + "/async",
        data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "PHASE": "RUN", "QUERY": query},
        timeout=120,
    )
    r.raise_for_status()
    job_url = r.url
    start = time.monotonic()
    while time.monotonic() - start < max_wait:
        phase = requests.get(job_url + "/phase", timeout=60).text.strip().upper()
        if phase == "COMPLETED":
            break
        if phase in {"ERROR", "ABORTED"}:
            raise RuntimeError(f"VizieR TAP job {job_url} ended in {phase}")
        time.sleep(poll_seconds)
    else:
        raise TimeoutError(f"VizieR TAP job {job_url} exceeded {max_wait}s")
    result = requests.get(job_url + "/results/result", timeout=300)
    result.raise_for_status()
    frame = pd.read_csv(io.StringIO(result.text), dtype={"source_id": "string"})
    return frame, job_url


def fetch(out: str | Path, expected_rows: int | None = EXPECTED_ROWS) -> dict:
    frame, job = run_async()
    clean = validate_d3(frame, expected_rows=expected_rows)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    clean.to_csv(tmp, index=False)
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    tmp.replace(out)
    report = {
        "status": "DOWNLOADED_AND_SCHEMA_VALIDATED_NOT_REANALYSED",
        "source_catalogues": ["VizieR I/357/tboasb1c", "VizieR I/355/gaiadr3"],
        "query": QUERY,
        "job_url": job,
        "rows": len(clean),
        "sha256": digest,
        "output": str(out.resolve()),
        "sealed_ids_removed": False,
        "note": "Sealed IDs are excluded inside dark_companion.h10 before scientific calculations. Re-run the registered analysis after retrieval; this fetch does not claim to reproduce the published metrics.",
    }
    out.with_suffix(out.suffix + ".provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the full Gaia DR3 AstroSpectroSB1 D3 table from VizieR")
    ap.add_argument("--out", default="realdata/dr3_astrospectro_all.csv")
    ap.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS,
                    help="Expected pre-sealed rows; use --allow-row-count-drift to disable the guard")
    ap.add_argument("--allow-row-count-drift", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = fetch(args.out, expected_rows=None if args.allow_row_count_drift else args.expected_rows)
    except Exception as exc:
        ap.exit(2, f"STOP: {type(exc).__name__}: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
