"""Bounded NASA EONET acquisition and offline archival verification."""
import argparse
import base64
import hashlib
import http.client
import json
import math
import os
import re
import ssl
import stat
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

HOST = 'eonet.gsfc.nasa.gov'
ENDPOINT = '/api/v3/events'
MAX_BODY = 2_000_000
MAX_ARCHIVE = 3_000_000
SCHEMA = 'gaia-eonet-archive-v0.4'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'Duplicate JSON key')
        result[k] = v
    return result


def bad_constant(_):
    raise ValueError('Non-finite JSON constant')


def parse(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=bad_constant)


def encode(obj):
    return (json.dumps(obj, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(s):
    require(isinstance(s, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z', s), 'Expected UTC timestamp')
    datetime.fromisoformat(s[:-1] + '+00:00')
    return s


def query(start, end, category, limit):
    require(all(isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v) for v in (start, end)), 'Expected YYYY-MM-DD dates')
    require(0 <= (date.fromisoformat(end)-date.fromisoformat(start)).days <= 30, 'Date range must be 1-31 days')
    require(isinstance(category, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}', category), 'Invalid category')
    require(type(limit) is int and 1 <= limit <= 200, 'Limit must be 1-200')
    return dict(status='all', start=start, end=end, category=category, limit=limit)


def query_path(q):
    require(isinstance(q, dict) and set(q) == {'status','start','end','category','limit'} and q['status'] == 'all', 'Invalid query')
    q = query(q['start'], q['end'], q['category'], q['limit'])
    return ENDPOINT + '?' + urlencode(q)


def valid_point(coords):
    return isinstance(coords, list) and len(coords) == 2 and all(type(x) in (int, float) and math.isfinite(x) for x in coords) and abs(coords[0]) <= 180 and abs(coords[1]) <= 90


def summarize(raw):
    require(0 < len(raw) <= MAX_BODY, 'Empty or oversized source body')
    data = parse(raw)
    events = data.get('events') if isinstance(data, dict) else None
    require(isinstance(events, list) and len(events) <= 2000, 'Invalid event array')
    seen = set()
    summary = dict(eventCount=len(events), pointCount=0, nonPointCount=0, eventsWithoutGeometry=0)
    for e in events:
        require(isinstance(e, dict) and all(isinstance(e.get(k), str) and e[k].strip() for k in ('id','title')) and e['id'] not in seen and isinstance(e.get('geometry'), list), 'Invalid event or duplicate ID')
        seen.add(e['id'])
        if not e['geometry']:
            summary['eventsWithoutGeometry'] += 1
        for g in e['geometry']:
            require(isinstance(g, dict) and isinstance(g.get('type'), str) and bool(g['type']), 'Invalid geometry')
            if g['type'] == 'Point':
                utc(g.get('date'))
                require(valid_point(g.get('coordinates')), 'Invalid point coordinates')
                summary['pointCount'] += 1
            else:
                summary['nonPointCount'] += 1
            require(summary['pointCount'] + summary['nonPointCount'] <= 20000, 'Too many geometries')
    return summary


def envelope(raw, mode, captured, q=None):
    utc(captured)
    summary = summarize(raw)
    require(mode in ('https-eonet','offline-import'), 'Invalid acquisition mode')
    if mode == 'https-eonet':
        url = 'https://' + HOST + query_path(q)
        require(summary['eventCount'] <= q['limit'], 'Response exceeds requested limit')
        status, cap = 200, summary['eventCount'] == q['limit']
    else:
        require(q is None, 'Offline import cannot assert request metadata')
        url = status = cap = None
    receipt = dict(mode=mode, capturedAt=captured, requestUrl=url, query=q, httpStatus=status,
                   limitReached=cap, coverage='unknown', sourceAuthenticated=False,
                   sourceSha256=sha(raw), sourceBytes=len(raw), **summary)
    return dict(schema=SCHEMA, receipt=receipt, bodyBase64=base64.b64encode(raw).decode('ascii'))


def verify(raw_archive, expected=None):
    require(0 < len(raw_archive) <= MAX_ARCHIVE, 'Empty or oversized archive')
    digest = sha(raw_archive)
    if expected is not None:
        require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected) and digest == expected, 'Archive digest mismatch')
    archive = parse(raw_archive)
    require(isinstance(archive, dict) and set(archive) == {'schema','receipt','bodyBase64'} and archive['schema'] == SCHEMA and isinstance(archive['receipt'], dict) and isinstance(archive['bodyBase64'], str), 'Invalid archive')
    raw = base64.b64decode(archive['bodyBase64'], validate=True)
    receipt = archive['receipt']
    rebuilt = envelope(raw, receipt.get('mode'), receipt.get('capturedAt'), receipt.get('query'))
    require(encode(rebuilt) == encode(archive), 'Archive receipt or source mismatch')
    return raw, dict(status='INTEGRITY_MATCH', archiveSha256=digest, anchorChecked=expected is not None, receipt=rebuilt['receipt'])


def read_file(path, limit):
    require(stat.S_ISREG(os.stat(path).st_mode), 'Expected regular file')
    with open(path, 'rb') as f:
        require(stat.S_ISREG(os.fstat(f.fileno()).st_mode), 'Expected regular file')
        data = f.read(limit + 1)
    require(0 < len(data) <= limit, 'Empty or oversized file')
    return data


def save_new(path, data):
    path = Path(path)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.gaia-', delete=False) as f:
            name = f.name
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(name, path)
    finally:
        if name is not None:
            os.unlink(name)


def fetch_body(q):
    path = query_path(q)
    conn = http.client.HTTPSConnection(HOST, timeout=10, context=ssl.create_default_context())
    try:
        conn.request('GET', path, headers={'Accept':'application/json','Accept-Encoding':'identity','User-Agent':'Gaia-Observatory/0.4'})
        r = conn.getresponse()
        require(r.status == 200, 'Upstream HTTP status ' + str(r.status))
        require(r.getheader('Content-Type','').split(';')[0].strip().lower() == 'application/json', 'Unexpected content type')
        require(r.getheader('Content-Encoding','identity').strip().lower() == 'identity', 'Unexpected content encoding')
        length = r.getheader('Content-Length')
        if length is not None:
            require(re.fullmatch(r'[0-9]+', length) and int(length) <= MAX_BODY and r.getheader('Transfer-Encoding') is None, 'Invalid content length')
        raw = r.read(MAX_BODY + 1)
        require(0 < len(raw) <= MAX_BODY and (length is None or len(raw) == int(length)), 'Empty, oversized or truncated response')
        return raw
    finally:
        conn.close()


def bounded_fetch(q):
    query_path(q)
    args = [sys.executable, str(Path(__file__).resolve()), '_fetch', '--start', q['start'], '--end', q['end'], '--category', q['category'], '--limit', str(q['limit'])]
    r = subprocess.run(args, capture_output=True, timeout=25, stdin=subprocess.DEVNULL)
    require(r.returncode == 0, 'EONET retrieval failed: ' + r.stderr.decode('utf-8', errors='replace')[:300].strip())
    return r.stdout


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='cmd', required=True)
    for cmd in ('fetch','_fetch'):
        f = commands.add_parser(cmd)
        for field in ('start','end','category'):
            f.add_argument('--'+field, required=True)
        f.add_argument('--limit', type=int, required=True)
        if cmd == 'fetch':
            f.add_argument('output')
    imp = commands.add_parser('import')
    imp.add_argument('source')
    imp.add_argument('output')
    for cmd in ('verify','export'):
        f = commands.add_parser(cmd)
        f.add_argument('archive')
        f.add_argument('--expected-sha256')
        if cmd == 'export':
            f.add_argument('output')
    a = p.parse_args()
    try:
        if a.cmd in ('fetch','_fetch'):
            q = query(a.start, a.end, a.category, a.limit)
            if a.cmd == '_fetch':
                sys.stdout.buffer.write(fetch_body(q))
                return 0
            raw, mode = bounded_fetch(q), 'https-eonet'
        elif a.cmd == 'import':
            raw, mode, q = read_file(a.source, MAX_BODY), 'offline-import', None
        else:
            raw, result = verify(read_file(a.archive, MAX_ARCHIVE), a.expected_sha256)
            if a.cmd == 'export':
                save_new(a.output, raw)
            print(json.dumps(result))
            return 0
        captured = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
        archived = encode(envelope(raw, mode, captured, q))
        _, result = verify(archived)
        save_new(a.output, archived)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, http.client.HTTPException, subprocess.SubprocessError) as e:
        print('Archive rejected: ' + str(e), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
