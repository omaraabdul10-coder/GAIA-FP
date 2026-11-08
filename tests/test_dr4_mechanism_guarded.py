import os
import sys
import pandas as pd
import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import dr4_mechanism_guarded as G


def test_idmap_nearest_match_and_radius(tmp_path):
    src = tmp_path / "idmap.csv"
    dst = tmp_path / "normalized.csv"
    pd.DataFrame({
        "dr3_source_id": ["101", "101", "202", "303"],
        "dr4_source_id": ["1001", "1002", "2002", "3003"],
        "angular_distance_arcsec": [0.8, 0.2, 1.4, 0.9],
    }).to_csv(src, index=False)
    meta = G.normalize_idmap(src, dst)
    got = pd.read_csv(dst, dtype={"dr3_source_id": str, "dr4_source_id": str})
    assert len(got) == 2
    assert dict(zip(got.dr3_source_id, got.dr4_source_id)) == {"101": "1002", "303": "3003"}
    assert meta["unique_dr3_matches"] == 2


def test_idmap_rejects_float_mangled_ids(tmp_path):
    src = tmp_path / "idmap.csv"
    pd.DataFrame({"dr3_source_id": ["1.0"], "dr4_source_id": ["2"], "angular_distance_arcsec": [0.1]}).to_csv(src, index=False)
    with pytest.raises(G.PreflightError, match="invalid/non-decimal"):
        G.normalize_idmap(src, tmp_path / "out.csv")


def test_idmap_rejects_duplicate_dr4_counterpart(tmp_path):
    src = tmp_path / "idmap.csv"
    pd.DataFrame({"dr3_source_id": ["1", "2"], "dr4_source_id": ["9", "9"], "angular_distance_arcsec": [0.1, 0.2]}).to_csv(src, index=False)
    with pytest.raises(G.PreflightError, match="not one-to-one"):
        G.normalize_idmap(src, tmp_path / "out.csv")


def test_preflight_requires_full_dr3_population_not_95_row_fixture(tmp_path):
    (tmp_path / "realdata").mkdir()
    (tmp_path / "results").mkdir()
    pd.DataFrame({"source_id": [str(i) for i in range(95)]}).to_csv(tmp_path / "realdata" / "dr3_astrospectro_all.csv", index=False)
    pd.DataFrame({"source_id": ["999"]}).to_csv(tmp_path / "realdata" / "excluded_sealed_ids.csv", index=False)
    pd.DataFrame({"source_id": ["1"], "dr3_source_id": ["1"], "angular_distance_arcsec": [0.1], "dr4_source_id": ["2"]}).to_csv(tmp_path / "idmap.csv", index=False)
    orbit = {c: [1.0] for c in G.ORBIT_REQUIRED if c != "source_id"}
    orbit["source_id"] = ["2"]
    orbit["eccentricity"] = [0.1]
    orbit["vbroad_nb_transits"] = [10]
    pd.DataFrame(orbit).to_csv(tmp_path / "orbits.csv", index=False)
    cmd = pd.DataFrame({"source_id": [str(i) for i in range(100)], "phot_g_mean_mag": [10.0]*100,
                        "bp_rp": [1.0]*100, "parallax": [10.0]*100})
    cmd.to_csv(tmp_path / "cmd.csv", index=False)
    vb = pd.DataFrame({"source_id": [str(i) for i in range(100)], "grvs_mag": [10.0]*100,
                       "vbroad": [5.0]*100, "vbroad_error": [1.0]*100, "vbroad_nb_transits": [10]*100})
    vb.to_csv(tmp_path / "vb.csv", index=False)
    with pytest.raises(G.PreflightError, match="95-row schema fixture"):
        G.validate_inputs(tmp_path / "orbits.csv", tmp_path / "cmd.csv", tmp_path / "vb.csv", tmp_path / "idmap.csv", tmp_path)


def test_preflight_rejects_missing_required_orbit_columns(tmp_path):
    (tmp_path / "realdata").mkdir()
    (tmp_path / "results").mkdir()
    pd.DataFrame({"source_id": [str(i) for i in range(1001)]}).to_csv(tmp_path / "realdata" / "dr3_astrospectro_all.csv", index=False)
    pd.DataFrame({"source_id": ["999"]}).to_csv(tmp_path / "realdata" / "excluded_sealed_ids.csv", index=False)
    pd.DataFrame({"source_id": ["1"], "dr4_source_id": ["2"], "angular_distance_arcsec": [0.1]}).to_csv(tmp_path / "idmap.csv", index=False)
    pd.DataFrame({"source_id": ["2"], "bad": [1]}).to_csv(tmp_path / "orbits.csv", index=False)
    pd.DataFrame({"source_id": ["3"], "phot_g_mean_mag": [10], "bp_rp": [1], "parallax": [10]}).to_csv(tmp_path / "cmd.csv", index=False)
    pd.DataFrame({"source_id": ["4"], "grvs_mag": [10], "vbroad": [5], "vbroad_error": [1], "vbroad_nb_transits": [10]}).to_csv(tmp_path / "vb.csv", index=False)
    with pytest.raises(G.PreflightError, match="missing required columns"):
        G.validate_inputs(tmp_path / "orbits.csv", tmp_path / "cmd.csv", tmp_path / "vb.csv", tmp_path / "idmap.csv", tmp_path)


def test_preflight_refuses_missing_idmap_argument():
    with pytest.raises(SystemExit):
        G.main(["orbits.csv", "cmd.csv", "vb.csv"])


def test_preflight_runs_field_calibration_gate_and_reports_it(tmp_path, monkeypatch):
    (tmp_path / "realdata").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "qa2").mkdir()
    pd.DataFrame({"source_id": [str(i) for i in range(1001)]}).to_csv(
        tmp_path / "realdata" / "dr3_astrospectro_all.csv", index=False)
    pd.DataFrame({"source_id": ["999999"]}).to_csv(
        tmp_path / "realdata" / "excluded_sealed_ids.csv", index=False)
    pd.DataFrame({"dr3_source_id": ["1"], "dr4_source_id": ["5000"],
                  "angular_distance_arcsec": [0.25]}).to_csv(tmp_path / "idmap.csv", index=False)

    orbit = {c: [1.0] for c in G.ORBIT_REQUIRED if c != "source_id"}
    orbit.update({"source_id": ["5000"], "period": [365.25], "eccentricity": [0.1],
                  "parallax": [10.0], "parallax_error": [0.1], "vbroad_nb_transits": [8]})
    pd.DataFrame(orbit).to_csv(tmp_path / "orbits.csv", index=False)
    ids = [str(10000 + i) for i in range(100)]
    pd.DataFrame({"source_id": ids, "phot_g_mean_mag": [10.0]*100,
                  "bp_rp": [1.0]*100, "parallax": [10.0]*100}).to_csv(
        tmp_path / "cmd.csv", index=False)
    pd.DataFrame({"source_id": ids, "grvs_mag": [10.0]*100, "vbroad": [5.0]*100,
                  "vbroad_error": [0.5]*100, "vbroad_nb_transits": [8]*100}).to_csv(
        tmp_path / "vb.csv", index=False)

    calls = []
    def fake_calibration(cmd, vb):
        calls.append((len(cmd), len(vb)))
        return {"field_cmd_rows": len(cmd), "field_vbroad_joined_rows": len(vb),
                "main_sequence_rvs_rows": len(vb), "usable_vbroad_cells": 15,
                "covered_colour_bins": 15}
    monkeypatch.setattr(G, "validate_field_calibration", fake_calibration)
    result = G.validate_inputs(tmp_path / "orbits.csv", tmp_path / "cmd.csv",
                               tmp_path / "vb.csv", tmp_path / "idmap.csv", tmp_path)
    assert calls == [(100, 100)]
    assert result["field_calibration"]["covered_colour_bins"] == 15
    assert result["field_vbroad_joined_rows"] == 100
    os.unlink(result["idmap_normalized"])


def test_preflight_stops_when_field_calibration_fails(tmp_path, monkeypatch):
    (tmp_path / "realdata").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "qa2").mkdir()
    pd.DataFrame({"source_id": [str(i) for i in range(1001)]}).to_csv(
        tmp_path / "realdata" / "dr3_astrospectro_all.csv", index=False)
    pd.DataFrame({"source_id": ["999999"]}).to_csv(
        tmp_path / "realdata" / "excluded_sealed_ids.csv", index=False)
    pd.DataFrame({"dr3_source_id": ["1"], "dr4_source_id": ["5000"],
                  "angular_distance_arcsec": [0.25]}).to_csv(tmp_path / "idmap.csv", index=False)
    orbit = {c: [1.0] for c in G.ORBIT_REQUIRED if c != "source_id"}
    orbit.update({"source_id": ["5000"], "period": [365.25], "eccentricity": [0.1],
                  "parallax": [10.0], "parallax_error": [0.1], "vbroad_nb_transits": [8]})
    pd.DataFrame(orbit).to_csv(tmp_path / "orbits.csv", index=False)
    ids = [str(10000 + i) for i in range(100)]
    pd.DataFrame({"source_id": ids, "phot_g_mean_mag": [10.0]*100,
                  "bp_rp": [1.0]*100, "parallax": [10.0]*100}).to_csv(tmp_path / "cmd.csv", index=False)
    pd.DataFrame({"source_id": ids, "grvs_mag": [10.0]*100, "vbroad": [5.0]*100,
                  "vbroad_error": [0.5]*100, "vbroad_nb_transits": [8]*100}).to_csv(
        tmp_path / "vb.csv", index=False)

    def reject_calibration(cmd, vb):
        raise G.PreflightError("test calibration failure")
    monkeypatch.setattr(G, "validate_field_calibration", reject_calibration)
    with pytest.raises(G.PreflightError, match="test calibration failure"):
        G.validate_inputs(tmp_path / "orbits.csv", tmp_path / "cmd.csv",
                          tmp_path / "vb.csv", tmp_path / "idmap.csv", tmp_path)
