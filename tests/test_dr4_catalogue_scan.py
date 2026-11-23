import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_catalogue_scan as S

def _df(n=200, seed=0):
    r = np.random.default_rng(seed)
    return pd.DataFrame(dict(source_id=[str(10**15 + i) for i in range(n)], G=r.uniform(7, 14, n),
        P=r.uniform(100, 2500, n), e=r.uniform(0, .8, n), mfit=r.uniform(5, 95, n), M=r.uniform(.5, 1.4, n),
        dm=r.normal(-.3, .6, n), log_lr=r.normal(0, 2, n), P_impostor=r.uniform(0, 1, n), verdict='x'))

def test_counts_and_flags():
    d = _df(); s, top, cand = S.scan(d, 2010, top=10)
    assert s['n_candidates_mfit_lt_80'] == int((d.mfit < 80).sum())
    assert s['n_baseline_trap'] == int(((d.P / 2010) >= .85)[d.mfit < 80].sum())
    assert not top.evolved_flag.any() and len(top) == 10
    assert list(top.log_lr) == sorted(top.log_lr, reverse=True)

def test_sealed_removed_first(tmp_path):
    d = _df(); sealed = tmp_path / 'sealed.csv'
    pd.DataFrame(dict(source_id=d.source_id[:5])).to_csv(sealed, index=False)
    import h21_baseline as H
    old = H.drop_sealed.__defaults__
    S.drop_sealed = lambda df: H.drop_sealed(df, str(sealed))
    try:
        s, _, cand = S.scan(d, 2010)
        assert s['n_sealed_removed'] == 5 and not set(d.source_id[:5]) & set(cand.source_id)
    finally:
        S.drop_sealed = H.drop_sealed
