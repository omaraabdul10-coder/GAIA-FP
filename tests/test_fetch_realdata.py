"""Offline tests for public-data acquisition helpers (all fixtures synthetic)."""
from pathlib import Path
import importlib.util
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fetch_realdata", ROOT / "tools" / "fetch_realdata.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)


def test_lamost_query_is_full_catalogue_and_has_positional_columns():
    q = F.Q_LAMOST_COV.upper()
    assert '"J/APJS/244/27/LAMOSTMRS"' in q
    assert 'GROUP BY GAIA' in q
    assert 'AVG(RAJ2000)' in q and 'AVG(DEJ2000)' in q
    assert 'WHERE GAIA IS NOT NULL' in q
    assert ' IN (' not in q


def test_normalise_lamost_cov_accepts_vizier_case_and_numeric_columns():
    raw = pd.DataFrame({
        "Gaia": ["123456789012345678", "223456789012345678"],
        "n_epochs": [3, 1], "RAJ2000": [10.5, 359.9], "DEJ2000": [-12.0, 89.0],
    })
    out = F.normalise_lamost_coverage(raw)
    assert list(out.columns) == ["gaia_dr2_source_id", "n_epochs", "ra", "dec"]
    assert out["n_epochs"].tolist() == [3, 1]
    assert out["gaia_dr2_source_id"].iloc[0] == "123456789012345678"


def test_normalise_lamost_cov_rejects_missing_positions():
    with pytest.raises(ValueError, match="missing required columns"):
        F.normalise_lamost_coverage(pd.DataFrame({"Gaia": [1], "n_epochs": [2]}))


def test_normalise_lamost_cov_rejects_bad_coordinates_and_counts():
    with pytest.raises(ValueError, match="RA values"):
        F.normalise_lamost_coverage(pd.DataFrame({"Gaia": [1], "n_epochs": [2], "RAJ2000": [361], "DEJ2000": [0]}))
    with pytest.raises(ValueError, match="positive integer"):
        F.normalise_lamost_coverage(pd.DataFrame({"Gaia": [1], "n_epochs": [0], "RAJ2000": [10], "DEJ2000": [0]}))


def test_fetch_lamost_coverage_uses_async_full_query(monkeypatch):
    fixture = pd.DataFrame({"Gaia": ["111", "222"], "n_epochs": [2, 4], "RAJ2000": [12.0, 13.0], "DEJ2000": [1.0, 2.0]})
    seen = {}
    def fake_async(base, query, max_wait):
        seen.update(base=base, query=query, max_wait=max_wait)
        return fixture, "mock-job"
    monkeypatch.setattr(F, "async_", fake_async)
    out, job = F.fetch_lamost_coverage()
    assert job == "mock-job"
    assert seen["base"] == F.VIZ and seen["max_wait"] == 3600
    assert "GROUP BY Gaia" in seen["query"]
    assert len(out) == 2 and set(["ra", "dec", "n_epochs"]).issubset(out.columns)

# The DR3 H10 source fetch is also kept offline-testable. This fixture validates
# the query/output contract only; no VizieR result is fabricated as an experiment.
D3_SPEC = importlib.util.spec_from_file_location("fetch_dr3_astrospectro", ROOT / "tools" / "fetch_dr3_astrospectro.py")
D3 = importlib.util.module_from_spec(D3_SPEC)
D3_SPEC.loader.exec_module(D3)


def _d3_fixture(n=2):
    data = {}
    for col in D3.REQUIRED:
        if col == "source_id":
            data[col] = [str(1000 + i) for i in range(n)]
        elif col == "nss_solution_type":
            data[col] = ["AstroSpectroSB1"] * n
        else:
            data[col] = [1.0] * n
    data["period"] = [100.0] * n
    data["eccentricity"] = [0.2] * n
    data["parallax"] = [10.0] * n
    data["parallax_error"] = [0.5] * n
    data["phot_g_mean_mag"] = [12.0] * n
    data["bp_rp"] = [1.0] * n
    return pd.DataFrame(data)


def test_d3_h10_query_is_joined_and_has_preregistered_parallax_cut():
    q = D3.QUERY.upper()
    assert '"I/357/TBOASB1C"' in q and '"I/355/GAIADR3"' in q
    assert "JOIN" in q and "G.SOURCE = O.SOURCE" in q
    assert "O.PLX/O.E_PLX > 10" in q
    assert "O.CTI AS C_THIELE_INNES" in q
    assert "O.HTI AS H_THIELE_INNES" in q
    assert "G.VBROAD AS VBROAD" in q and "G.O_VBROAD AS VBROAD_NB_TRANSITS" in q


def test_validate_d3_accepts_complete_fixture_and_rejects_rowcount_drift():
    df = D3.validate_d3(_d3_fixture(), expected_rows=2)
    assert len(df) == 2 and df.source_id.tolist() == ["1000", "1001"]
    with pytest.raises(ValueError, match="row-count mismatch"):
        D3.validate_d3(_d3_fixture(), expected_rows=33464)


def test_validate_d3_rejects_duplicate_sources_and_non_sb1_rows():
    dup = _d3_fixture()
    dup.loc[1, "source_id"] = dup.loc[0, "source_id"]
    with pytest.raises(ValueError, match="duplicate source_id"):
        D3.validate_d3(dup, expected_rows=2)
    other = _d3_fixture()
    other.loc[0, "nss_solution_type"] = "Orbital"
    with pytest.raises(ValueError, match="non-AstroSpectroSB1"):
        D3.validate_d3(other, expected_rows=2)
