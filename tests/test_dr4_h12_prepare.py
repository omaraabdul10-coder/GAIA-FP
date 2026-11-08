import os
import sys
import pandas as pd
import numpy as np
import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import dr4_h12_prepare as P
from dr4_mechanism_guarded import PreflightError


def _files(tmp_path):
    O = {c: [1.0, 2.0] for c in P.ORBIT_CORE if c != "source_id"}
    O["source_id"] = ["100", "200"]
    O["eccentricity"] = [0.1, 0.2]
    pd.DataFrame(O).to_csv(tmp_path / "orbits.csv", index=False)
    pd.DataFrame({"source_id": ["100"], "grvs_mag": [11.0], "vbroad": [4.0],
                  "vbroad_error": [0.4], "vbroad_nb_transits": [8]}).to_csv(tmp_path / "candidate_rvs.csv", index=False)

    rng = np.random.default_rng(9)
    n = 6000
    colour = rng.uniform(0.35, 3.95, n)
    parallax = rng.uniform(5.0, 100.0, n)
    abs_g = 3.0 + 1.8*colour + rng.normal(0, 0.12, n)
    phot_g = abs_g - 5*np.log10(parallax/100.0)
    ids = [str(10000+i) for i in range(n)]
    pd.DataFrame({"source_id": ids, "phot_g_mean_mag": phot_g,
                  "bp_rp": colour, "parallax": parallax}).to_csv(tmp_path / "field_cmd.csv", index=False)
    grvs = rng.choice([9.5, 10.5, 12.0], size=n)
    vbroad = 5.0 + 0.3*colour + rng.normal(0, 0.25, n)
    pd.DataFrame({"source_id": ids, "grvs_mag": grvs,
                  "vbroad": vbroad, "vbroad_error": rng.uniform(0.1, 0.3, n),
                  "vbroad_nb_transits": rng.integers(5, 16, n)}).to_csv(tmp_path / "field_rvs.csv", index=False)


def test_prepare_merges_candidate_and_field_rvs_by_string_id(tmp_path):
    _files(tmp_path)
    out = tmp_path / "prepared"
    rep = P.prepare(tmp_path / "orbits.csv", tmp_path / "candidate_rvs.csv",
                    tmp_path / "field_cmd.csv", tmp_path / "field_rvs.csv", out)
    cand = pd.read_csv(out / "dr4_new_orbits.csv", dtype={"source_id": str})
    field = pd.read_csv(out / "dr4_field_vbroad.csv", dtype={"source_id": str})
    assert cand.source_id.tolist() == ["100", "200"]
    assert cand.vbroad.notna().sum() == 1
    assert len(field) == 6000
    assert rep["status"] == "PREPARED_LOCAL_INPUTS_NOT_SCIENTIFICALLY_VALIDATED"
    assert (out / "preparation_provenance.json").is_file()


def test_prepare_rejects_duplicate_candidate_rvs_ids(tmp_path):
    _files(tmp_path)
    rvs = pd.read_csv(tmp_path / "candidate_rvs.csv", dtype={"source_id": str})
    pd.concat([rvs, rvs], ignore_index=True).to_csv(tmp_path / "candidate_rvs_dup.csv", index=False)
    with pytest.raises(PreflightError, match="duplicate source_id"):
        P.prepare(tmp_path / "orbits.csv", tmp_path / "candidate_rvs_dup.csv",
                  tmp_path / "field_cmd.csv", tmp_path / "field_rvs.csv", tmp_path / "out")


def test_prepare_rejects_candidate_rvs_unknown_ids(tmp_path):
    _files(tmp_path)
    pd.DataFrame({"source_id": ["999"], "grvs_mag": [11.0], "vbroad": [4.0],
                  "vbroad_error": [0.4], "vbroad_nb_transits": [8]}).to_csv(tmp_path / "candidate_rvs_extra.csv", index=False)
    with pytest.raises(PreflightError, match="absent from orbit table"):
        P.prepare(tmp_path / "orbits.csv", tmp_path / "candidate_rvs_extra.csv",
                  tmp_path / "field_cmd.csv", tmp_path / "field_rvs.csv", tmp_path / "out")


def test_prepare_rejects_non_numeric_physical_columns(tmp_path):
    _files(tmp_path)
    O = pd.read_csv(tmp_path / "orbits.csv", dtype={"period": str})
    O.loc[0, "period"] = "bad-unit"
    O.to_csv(tmp_path / "orbits_bad.csv", index=False)
    with pytest.raises(PreflightError, match="non-numeric or missing"):
        P.prepare(tmp_path / "orbits_bad.csv", tmp_path / "candidate_rvs.csv",
                  tmp_path / "field_cmd.csv", tmp_path / "field_rvs.csv", tmp_path / "out")
