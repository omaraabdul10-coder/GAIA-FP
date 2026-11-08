"""Tests of gaia_live_smoke error handling using STUB transports (no network). A PASS here proves parsing/classification logic only,
NOT that the live archive works -- see QA2_README.md for the real live run."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src')); sys.path.insert(0, os.path.dirname(__file__))
try: import pytest
except ImportError: import _minipytest as pytest
import requests, gaia_live_smoke as S

class R:
    def __init__(self, code=200, text='', content=None): self.status_code = code; self.text = text; self.content = content if content is not None else text.encode()
class Sess:
    def __init__(self, tap=None, dl=None): self.tap, self.dl = tap, dl
    def _do(self, x):
        if isinstance(x, Exception): raise x
        return x
    def post(self, *a, **k): return self._do(self.tap)
    def get(self, *a, **k): return self._do(self.dl)

CSV = 'source_id,phot_g_mean_mag,ref_epoch\n1,10.0,2016.0\n2,11.0,2016.0\n'
VOT = ('<?xml version="1.0"?><VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3"><RESOURCE><TABLE><FIELD name="ID"/><FIELD name="access_url"/>'
       '<FIELD name="semantics"/><DATA><TABLEDATA><TR><TD>x</TD><TD>http://a</TD><TD>#progenitor</TD></TR></TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>')

def test_dns_failure_is_classified_and_never_pass():
    e = requests.exceptions.ConnectionError("NameResolutionError: Failed to resolve (Temporary failure in name resolution)")
    r = S.run(session=Sess(e, e)); assert r['overall'] == 'FAIL'
    assert [s['category'] for s in r['stages']] == ['DNS', 'DNS'] and all(s['status'] == 'FAIL' for s in r['stages'])

def test_timeout_and_tls_and_connect():
    assert S.tap_stage('gaiadr3', 1, Sess(requests.exceptions.ReadTimeout('t')))['category'] == 'TIMEOUT'
    assert S.tap_stage('gaiadr3', 1, Sess(requests.exceptions.SSLError('bad cert')))['category'] == 'TLS'
    assert S.tap_stage('gaiadr3', 1, Sess(requests.exceptions.ConnectionError('refused')))['category'] == 'CONNECT'

def test_http_errors_and_auth():
    assert S.tap_stage('gaiadr3', 1, Sess(R(503, 'down')))['category'] == 'HTTP_503'
    assert S.datalink_stage('gaiadr3', '1', 1, Sess(dl=R(403)))['category'] == 'AUTH'

def test_api_change_detected_not_pass():
    s = S.tap_stage('gaiadr3', 1, Sess(R(200, 'foo,bar\n1,2\n'))); assert s['status'] == 'FAIL' and s['category'] == 'API_CHANGED'
    d = S.datalink_stage('gaiadr3', '1', 1, Sess(dl=R(200, '<html>login</html>'))); assert d['status'] == 'FAIL' and d['category'] == 'API_CHANGED'
    d = S.datalink_stage('gaiadr3', '1', 1, Sess(dl=R(200, VOT.replace('access_url', 'url')))); assert d['category'] == 'API_CHANGED'

def test_stub_success_parses_both_stages():
    r = S.run(session=Sess(R(200, CSV), R(200, VOT)))
    assert r['overall'] == 'PASS' and r['stages'][0]['n_rows'] == 2 and r['stages'][1]['n_links'] == 1

def test_stages_are_independent():
    r = S.run(session=Sess(requests.exceptions.ReadTimeout('t'), R(200, VOT)))
    assert [s['status'] for s in r['stages']] == ['FAIL', 'PASS'] and r['overall'] == 'FAIL'

def test_offline_is_skipped_not_pass():
    r = S.run(offline=True); assert r['overall'] == 'SKIPPED'

def test_report_never_claims_live_success_when_offline_or_failed():
    off = S.run(offline=True); assert off['live_attempt'] is False and off['overall'] != 'PASS'
    e = requests.exceptions.ConnectionError('name resolution'); r = S.run(session=Sess(e, e)); assert r['overall'] == 'FAIL' and 'live_data' not in r
