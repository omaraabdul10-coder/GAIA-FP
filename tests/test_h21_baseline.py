"""H21 runner on synthetic DR4-like data: a planted upward revision in the near-baseline group must PASS,
no effect must not, and too few orbits must give NOT_CONDUCTED."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_pipeline as D
import h21_baseline as H21

MJ = 9.546e-4


def thiele(a0, inc=60.0, om=30.0, Om=50.0):
    w, W, i = np.radians(om), np.radians(Om), np.radians(inc)
    A = a0 * (np.cos(w) * np.cos(W) - np.sin(w) * np.sin(W) * np.cos(i))
    B = a0 * (np.cos(w) * np.sin(W) + np.sin(w) * np.cos(W) * np.cos(i))
    F = -a0 * (np.sin(w) * np.cos(W) + np.cos(w) * np.sin(W) * np.cos(i))
    G = -a0 * (np.sin(w) * np.sin(W) - np.cos(w) * np.cos(W) * np.cos(i))
    return A, B, F, G


def fake(nN=60, nS=300, up_N=0.5, up_S=0.1, seed=0):
    rng = np.random.default_rng(seed); rows, orb, ids = [], [], []
    for k, (g, n, pu) in enumerate([('N', nN, up_N), ('S', nS, up_S)]):
        for j in range(n):
            sid = f'{k}{j:06d}'; P = (rng.uniform(0.9, 1.3) if g == 'N' else rng.uniform(0.1, 0.45)) * H21.T3
            M, plx, m2 = 1.0, 10.0, rng.uniform(15, 70)
            arel = (M * (P / 365.25) ** 2) ** (1 / 3); a0_3 = m2 * MJ / M * arel * plx
            f = 2.0 if rng.random() < pu else 1.0
            A, B, F, G = thiele(a0_3 * f)
            rows.append(dict(source_id=sid, P=P, sigP=0.05, mfit=m2, M=M, P_impostor=rng.random(), verdict='x'))
            orb.append(dict(source_id='d' + sid, nss_solution_type='Orbital', period=P, a_thiele_innes=A, b_thiele_innes=B,
                            f_thiele_innes=F, g_thiele_innes=G, a_thiele_innes_error=1e-4, b_thiele_innes_error=1e-4,
                            f_thiele_innes_error=1e-4, g_thiele_innes_error=1e-4, parallax=plx, parallax_error=1e-3,
                            significance=20.0))
            ids.append(dict(dr3_source_id=sid, dr4_source_id='d' + sid, angular_distance_arcsec=0.01))
    return pd.DataFrame(rows), pd.DataFrame(ids), pd.DataFrame(orb)


def test_mass_recovered_and_planted_effect_passes():
    pred, idmap, orbits = fake()
    res, P = H21.run(pred, idmap, orbits)
    r = P.r[P.has_orbit]
    assert np.all((np.abs(r - 1) < 0.02) | (np.abs(r - 2) < 0.04))   # same orbit -> r = 1; doubled a0 -> r = 2
    assert res['H21'] == 'PASS'


def test_no_effect_fails():
    pred, idmap, orbits = fake(up_N=0.1, up_S=0.1, seed=1)
    assert H21.run(pred, idmap, orbits)[0]['H21'] == 'FAIL'


def test_too_few_orbits_not_conducted():
    pred, idmap, orbits = fake(nN=10)
    assert H21.run(pred, idmap, orbits)[0]['H21'].startswith('NOT_CONDUCTED')
