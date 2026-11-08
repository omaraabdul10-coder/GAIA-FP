"""Tests of the unblinding runner on SYNTHETIC labels and catalogue (the real sealed file is never used here)."""
import sys, os, json, hashlib, numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_evaluate as E

def fake(tmp_path, n_imp=39, n_sub=26, signal=1.5, nep=20, seed=0):
    rng = np.random.default_rng(seed)
    labs = ['impostor']*n_imp + ['substellar']*n_sub + ['unresolved']*10 + ['excluded_inspected']
    ids = [str(10**17 + i) for i in range(len(labs))]
    J = dict(version='fake', created='x', rules='x', entries=[dict(source_id=i, label=l, name='n', confidence='high', ref='r', origin='o',
             evidence=None, notes=None, companion_mass_MJ=None) for i, l in zip(ids, labs)])
    lp = tmp_path/'labels.json'; lp.write_text(json.dumps(J))
    y = np.array([1 if l == 'impostor' else 0 for l in labs])
    z = rng.normal(signal*y, 1); dm = -rng.normal(0.8*y, 0.3)
    C = pd.DataFrame(dict(source_id=ids, P_impostor=1/(1+np.exp(-z)), prior_pi=0.6, llr_cmd=-dm/0.3, dm=dm, sig_cmd=0.3,
                          nep=nep, score_emp=-dm/0.3 + rng.normal(1.0*y, 1)))
    cp = tmp_path/'cat.csv'; C.to_csv(cp, index=False)
    return str(cp), E.sha256(str(cp)), str(lp), E.sha256(str(lp))

def test_runs_and_statuses(tmp_path):
    cp, ch, lp, lh = fake(tmp_path)
    out = E.evaluate(cp, ch, lp, labels_sha=lh)
    assert out['n_labelled_in_catalogue'] == 65 and out['missing_from_catalogue'] == 0
    assert out['H1']['status'] == 'CONDUCTED' and out['H1']['auc'] > 0.7 and out['H1']['p'] < 0.01
    assert out['H2']['status'] == 'CONDUCTED'
    assert out['H8']['status'].startswith('NOT_CONDUCTED')
    assert 'H11a' in out['holm_family']['not_conducted'] and 'H1' in out['holm_family']['conducted']

def test_refuses_wrong_catalogue_hash(tmp_path):
    cp, ch, lp, lh = fake(tmp_path)
    with pytest.raises(SystemExit): E.evaluate(cp, '0'*64, lp, labels_sha=lh)

def test_refuses_wrong_label_hash_or_counts(tmp_path):
    cp, ch, lp, lh = fake(tmp_path)
    with pytest.raises(SystemExit): E.evaluate(cp, ch, lp, labels_sha='0'*64)
    cp, ch, lp, lh = fake(tmp_path, n_imp=38, n_sub=27)
    with pytest.raises(SystemExit): E.evaluate(cp, ch, lp, labels_sha=lh)

def test_h2_not_conducted_with_few_rvs_epochs(tmp_path):
    cp, ch, lp, lh = fake(tmp_path, nep=3)
    out = E.evaluate(cp, ch, lp, labels_sha=lh)
    assert out['H2']['status'] == 'NOT_CONDUCTED:BELOW_MIN_N' and 'H2' in out['holm_family']['not_conducted']

def test_holm_textbook():
    r = E.holm({'a': 0.001, 'b': 0.012, 'c': 0.02}, alpha=0.05)
    assert r['a']['rejected'] and r['b']['rejected'] and r['c']['rejected']      # 0.001<.0167, .012<.025, .02<.05
    r = E.holm({'a': 0.001, 'b': 0.04, 'c': 0.03}, alpha=0.05)
    assert r['a']['rejected'] and not r['c']['rejected'] and not r['b']['rejected']  # .03 > .025 stops the chain; b is not rejected although .04 < .05

def test_bootstrap_p_null():
    rng = np.random.default_rng(3); ps = []
    for _ in range(60):
        y = np.r_[np.ones(39, int), np.zeros(26, int)]; s = rng.normal(size=65)
        bs = E.strat_boot(lambda i: E.auc(s[i], y[i]), y, n=300); ps.append(E.p_one_sided(bs, 0.5, 'greater'))
    assert 0.25 < np.mean(np.array(ps) < 0.5) < 0.75     # under the null roughly half the p-values are below 0.5

def test_retention_order_statistic():
    rng = np.random.default_rng(0)
    for n0 in (12, 13, 26):
        s = np.r_[rng.normal(1, 1, 39), rng.normal(0, 1, n0)]; y = np.r_[np.ones(39, int), np.zeros(n0, int)]
        rej, ach = E.rejection_at_retention(s, y, 0.95, achieved=True)
        assert ach >= 0.95 and 0 <= rej <= 1

def test_weighted_holm():
    import dr4_evaluate as E
    # H1 alone at 0.4*0.025 = 0.01 is rejected; its weight passes on, so A5 is then tested at 0.2/0.6*0.025
    r = E.weighted_holm({'H1': 0.009, 'A5': 0.008, 'H12': 0.5, 'H2': 0.5, 'H11a': 0.5})
    assert r['H1']['rejected'] and r['A5']['rejected'] and not r['H12']['rejected']
    # only conducted hypotheses share the weight
    r = E.weighted_holm({'H1': 0.02})
    assert r['H1']['rejected'] and abs(r['H1']['weighted_threshold'] - 0.025) < 1e-12
    # equal weights reproduce plain Holm
    p = {'H1': 0.004, 'A5': 0.009, 'H12': 0.03}
    eq = E.weighted_holm(p, weights=dict(H1=1, A5=1, H12=1))
    assert {k: v['rejected'] for k, v in eq.items()} == {k: v['rejected'] for k, v in E.holm(p).items()}

def test_h20_head_to_head():
    import numpy as np, pandas as pd, dr4_evaluate as E
    rng = np.random.default_rng(0); y = np.r_[np.ones(30, int), np.zeros(30, int)]
    D = pd.DataFrame(dict(y=y, P_impostor=y*0.6 + rng.uniform(0, .4, 60), fluxratio=rng.uniform(0, 1, 60), bjk_m2=np.r_[rng.uniform(0, 1, 50), [np.nan]*10]))
    r = E.h20(D)
    assert r['DPAC_fluxratio']['verdict'] == 'GAIA-FP better' and r['BJK2026_m2']['status'] == 'CONDUCTED'
    assert r['DPAC_substellar_proba']['status'].startswith('NOT_CONDUCTED')
