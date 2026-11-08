"""
gaia_live_smoke.py — live connectivity smoke test for the Gaia Archive (TAP and DataLink tested SEPARATELY).

Standalone: needs only `requests` (no astroquery).  Each stage reports exactly one of
  PASS      the live server answered and the answer was parsed (row count / link count recorded)
  FAIL      the request was made and failed; `category` says why
  SKIPPED   not attempted (e.g. offline mode, or a prerequisite stage failed and --no-skip was not given)
A stage is NEVER PASS unless a real HTTP response with parseable content was received.
Failure categories: DNS, CONNECT, TIMEOUT, TLS, HTTP_<code>, AUTH, API_CHANGED (200 but unexpected content), OTHER.

Usage:  python gaia_live_smoke.py [--release gaiadr3] [--source-id 4318465066420528000] [--timeout 30]
                                  [--out ../results/live_smoke_report.json]
Exit code: 0 only if BOTH stages PASS; 1 otherwise (2 for bad arguments).
The report never contains credentials.  Anonymous access is used (no login needed for these small queries).
"""
import argparse, csv, io, json, socket, sys, time, xml.etree.ElementTree as ET

TAP_URL = 'https://gea.esac.esa.int/tap-server/tap/sync'
DATALINK_URL = 'https://gea.esac.esa.int/data-server/datalink/links'
DEFAULT_SOURCE_ID = '4318465066420528000'   # Gaia BH3 (DR3 NSS source); only a test target, no science use
DR_LABEL = {'gaiadr3': 'Gaia DR3', 'gaiadr4': 'Gaia DR4'}

def classify_exception(exc):
    """Map an exception from `requests` (or a stub) to a stable failure category."""
    import requests
    name = type(exc).__name__; msg = str(exc)
    low = msg.lower()
    if isinstance(exc, requests.exceptions.SSLError): return 'TLS'
    if isinstance(exc, (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout, requests.exceptions.Timeout, socket.timeout, TimeoutError)):
        return 'TIMEOUT'
    if any(k in low for k in ('name resolution', 'name or service not known', 'nodename nor servname', 'getaddrinfo', 'no address associated')):
        return 'DNS'
    if isinstance(exc, requests.exceptions.ConnectionError): return 'CONNECT'
    return 'OTHER'

def _stage(name, status, category=None, detail=None, **extra):
    d = dict(stage=name, status=status, category=category, detail=detail); d.update(extra); return d

def _get_session():
    import requests; return requests.Session()

def tap_stage(release, timeout, session=None, url=TAP_URL):
    """Run `SELECT TOP 3 source_id, ... FROM <release>.gaia_source` synchronously (CSV)."""
    s = session or _get_session(); table = f'{release}.gaia_source'
    adql = f'SELECT TOP 3 source_id, phot_g_mean_mag, ref_epoch FROM {table}'
    t0 = time.time()
    try:
        r = s.post(url, data=dict(REQUEST='doQuery', LANG='ADQL', FORMAT='csv', QUERY=adql), timeout=timeout)
    except Exception as e:
        return _stage('tap', 'FAIL', classify_exception(e), f'{type(e).__name__}: {str(e)[:300]}', adql=adql, seconds=round(time.time()-t0, 2))
    sec = round(time.time()-t0, 2)
    if r.status_code in (401, 403): return _stage('tap', 'FAIL', 'AUTH', f'HTTP {r.status_code}', adql=adql, seconds=sec)
    if r.status_code != 200:
        return _stage('tap', 'FAIL', f'HTTP_{r.status_code}', r.text[:300], adql=adql, seconds=sec)
    try:
        rows = list(csv.DictReader(io.StringIO(r.text)))
    except Exception as e:
        return _stage('tap', 'FAIL', 'API_CHANGED', f'unparseable CSV: {e}', adql=adql, seconds=sec)
    need = {'source_id', 'phot_g_mean_mag', 'ref_epoch'}
    if not rows or not need <= set(rows[0]):
        return _stage('tap', 'FAIL', 'API_CHANGED', f'HTTP 200 but columns={list(rows[0]) if rows else None}, rows={len(rows)}; body[:200]={r.text[:200]!r}', adql=adql, seconds=sec)
    return _stage('tap', 'PASS', None, 'live TAP query answered', adql=adql, seconds=sec, n_rows=len(rows),
                  ref_epoch_seen=sorted({x['ref_epoch'] for x in rows}), first_source_id=rows[0]['source_id'])

def datalink_stage(release, source_id, timeout, session=None, url=DATALINK_URL):
    """Request the DataLink link table (list of available products) for ONE source; independent of the TAP stage."""
    s = session or _get_session(); ident = f'{DR_LABEL.get(release, release)} {source_id}'
    t0 = time.time()
    try:
        r = s.get(url, params=dict(ID=ident), timeout=timeout)
    except Exception as e:
        return _stage('datalink', 'FAIL', classify_exception(e), f'{type(e).__name__}: {str(e)[:300]}', identifier=ident, seconds=round(time.time()-t0, 2))
    sec = round(time.time()-t0, 2)
    if r.status_code in (401, 403): return _stage('datalink', 'FAIL', 'AUTH', f'HTTP {r.status_code}', identifier=ident, seconds=sec)
    if r.status_code != 200: return _stage('datalink', 'FAIL', f'HTTP_{r.status_code}', r.text[:300], identifier=ident, seconds=sec)
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        return _stage('datalink', 'FAIL', 'API_CHANGED', f'HTTP 200 but not XML/VOTable: {e}', identifier=ident, seconds=sec)
    ns = root.tag.split('}')[0] + '}' if root.tag.startswith('{') else ''
    fields = [f.get('name') for f in root.iter(ns + 'FIELD')]
    trs = list(root.iter(ns + 'TR'))
    if not fields or 'access_url' not in fields:
        return _stage('datalink', 'FAIL', 'API_CHANGED', f'VOTable without access_url column; FIELDs={fields}', identifier=ident, seconds=sec)
    i_sem = fields.index('semantics') if 'semantics' in fields else None; i_id = fields.index('service_def') if 'service_def' in fields else None
    sems = []
    for tr in trs:
        tds = [(td.text or '') for td in tr.iter(ns + 'TD')]
        if i_sem is not None and i_sem < len(tds): sems.append(tds[i_sem])
    if not trs:
        return _stage('datalink', 'FAIL', 'API_CHANGED', 'VOTable parsed but contains zero link rows (source has no products, or API changed)', identifier=ident, seconds=sec)
    return _stage('datalink', 'PASS', None, 'live DataLink link table answered', identifier=ident, seconds=sec, n_links=len(trs),
                  link_semantics_sample=sorted(set(sems))[:8])

def run(release='gaiadr3', source_id=DEFAULT_SOURCE_ID, timeout=30.0, offline=False, session=None):
    rep = dict(tool='gaia_live_smoke.py', utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), release=release,
               source_id=str(source_id), timeout_s=timeout, live_attempt=(not offline), stages=[])
    if offline:
        rep['stages'] = [_stage('tap', 'SKIPPED', None, '--offline'), _stage('datalink', 'SKIPPED', None, '--offline')]
    else:
        rep['stages'] = [tap_stage(release, timeout, session), datalink_stage(release, source_id, timeout, session)]
    st = {x['stage']: x['status'] for x in rep['stages']}
    rep['overall'] = 'PASS' if all(v == 'PASS' for v in st.values()) else ('SKIPPED' if all(v == 'SKIPPED' for v in st.values()) else 'FAIL')
    rep['note'] = ('A PASS here means only that the public archive endpoints answered in the expected format for this one source; '
                   'it does NOT validate DR4 (use --release gaiadr4 on release day) nor the science pipeline.')
    return rep

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--release', default='gaiadr3', choices=list(DR_LABEL)); ap.add_argument('--source-id', default=DEFAULT_SOURCE_ID)
    ap.add_argument('--timeout', type=float, default=30.0); ap.add_argument('--offline', action='store_true')
    ap.add_argument('--out', default='live_smoke_report.json')
    a = ap.parse_args(argv)
    if not str(a.source_id).isdigit(): print('source-id must be an integer', file=sys.stderr); return 2
    rep = run(a.release, a.source_id, a.timeout, a.offline)
    json.dump(rep, open(a.out, 'w'), indent=1)
    for s in rep['stages']: print(f"{s['stage']:9s} {s['status']:8s} {s.get('category') or ''} {s.get('detail') or ''}"[:200])
    print('OVERALL', rep['overall'], '->', a.out); return 0 if rep['overall'] == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main())
