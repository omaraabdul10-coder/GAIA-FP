import sys, os, json, pytest, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_after as A
import dr4_evaluate as E


def test_sealed_ids_follow_the_dr4_map(tmp_path):
    # DR4 ids are new: the DR3 sealed list alone would remove nothing. The map must carry them over.
    pd.DataFrame(dict(source_id=['111', '222', '333'])).to_csv(tmp_path / 'sealed.csv', index=False)
    pd.DataFrame(dict(dr3_source_id=['111', '222', '333', '444'], dr4_source_id=['9111', '9222', '9333', '9444'],
                      angular_distance_arcsec=[0.1, 0.3, 1.5, 0.1])).to_csv(tmp_path / 'map.csv', index=False)
    got = A.sealed_dr4_ids(str(tmp_path / 'map.csv'), str(tmp_path / 'sealed.csv'))
    assert got == {'9111', '9222'}          # 333 is beyond 1", 444 is not sealed


def test_refuses_a_changed_catalogue(tmp_path):
    p = tmp_path / 'gaiafp_dr4_catalogue.csv'
    pd.DataFrame(dict(source_id=['1'], P_impostor=[0.5])).to_csv(p, index=False)
    json.dump(dict(catalogue_sha256=E.sha256(str(p))), open(tmp_path / 'dr4_evaluation.json', 'w'))
    assert A.check_hash(str(tmp_path)) == E.sha256(str(p))
    pd.DataFrame(dict(source_id=['1'], P_impostor=[0.6])).to_csv(p, index=False)
    with pytest.raises(SystemExit):
        A.check_hash(str(tmp_path))


def test_summary_copies_statuses(tmp_path):
    json.dump(dict(catalogue_sha256='x', n_labelled_in_catalogue=65, n_labelled_registered=65,
                   H1=dict(status='CONDUCTED', auc=0.71, ci95=[0.58, 0.83], registered_pass=True)), open(tmp_path / 'dr4_evaluation.json', 'w'))
    json.dump(dict(H21='NOT_CONDUCTED: too few', counts=dict(N=0)), open(tmp_path / 'h21.json', 'w'))
    assert A.summary(str(tmp_path)) == 2
    md = open(tmp_path / 'DR4_SUMMARY.md').read()
    assert '| H1 | primary (Holm 0.4) | CONDUCTED |' in md and 'NOT_CONDUCTED: too few' in md
