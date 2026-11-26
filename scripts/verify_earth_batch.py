"""Independent offline replay of Gaia Earth batch v0.3. No external services."""
import hashlib
import json
import math
import os
import re
import stat
import sys
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

R = 6371.0088
LIMITATION = 'No match is not safety. Points are not hazard footprints; coverage, source authenticity, and actual facility exposure are unverified.'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Non-finite JSON constant')


def read(path, limit):
    with open(path, 'rb') as handle:
        require(stat.S_ISREG(os.fstat(handle.fileno()).st_mode), 'Expected regular file')
        raw = handle.read(limit + 1)
    require(0 < len(raw) <= limit, 'Empty or oversized input')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=invalid_constant)
    return raw, value


def digest(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def point(p):
    return isinstance(p, list) and len(p) == 2 and all(number(x) for x in p) and abs(p[0]) <= 180 and abs(p[1]) <= 90


def utc(s):
    require(isinstance(s, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z', s), 'Expected UTC timestamp')
    return datetime.fromisoformat(s[:-1] + '+00:00')


def stamp(t):
    return t.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def vector(p):
    lon, lat = map(math.radians, p)
    return math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat)


def distance(a, b):
    x, y, z = vector(a)
    u, v, w = vector(b)
    cross = math.hypot(y*w-z*v, z*u-x*w, x*v-y*u)
    return R*math.atan2(cross, x*u+y*v+z*w)


def round_km(d):
    return float(Decimal.from_float(d).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))


def text(s):
    return isinstance(s, str) and bool(s.strip())


def screen(raw, c, facility):
    end = utc(c['asOf'])
    start = end - timedelta(hours=c['hours'])
    events = raw.get('events') if isinstance(raw, dict) else None
    require(isinstance(events, list) and len(events) <= 2000, 'Invalid events')
    coverage = dict(events=len(events), eligiblePoints=0, unsupportedGeometries=0, outsideWindow=0, eventsWithoutGeometry=0)
    seen, matches, total = set(), [], 0
    for e in events:
        require(isinstance(e, dict) and text(e.get('id')) and text(e.get('title')) and isinstance(e.get('geometry'), list) and e['id'] not in seen, 'Invalid or duplicate event')
        seen.add(e['id'])
        if not e['geometry']:
            coverage['eventsWithoutGeometry'] += 1
        candidates = []
        for g in e['geometry']:
            total += 1
            require(total <= 20000 and isinstance(g, dict) and isinstance(g.get('type'), str), 'Invalid geometry')
            if g['type'] != 'Point':
                coverage['unsupportedGeometries'] += 1
                continue
            observed, coords = utc(g.get('date')), g.get('coordinates')
            require(point(coords), 'Invalid point')
            if not start <= observed <= end:
                coverage['outsideWindow'] += 1
                continue
            coverage['eligiblePoints'] += 1
            d = distance(facility['coordinates'], coords)
            if d <= c['radiusKm']:
                candidates.append((d, stamp(observed), coords))
        if candidates:
            d, observed, coords = min(candidates)
            matches.append(dict(eventId=e['id'], title=e['title'], observedAt=observed, coordinates=coords, distanceKm=d))
    matches.sort(key=lambda m: (m['distanceKm'], m['eventId'].encode('utf-16-be', errors='surrogatepass')))
    for m in matches:
        m['distanceKm'] = round_km(m['distanceKm'])
    status = 'POINTS_WITHIN_RADIUS' if matches else 'NO_MATCH_IN_AVAILABLE_POINTS' if coverage['eligiblePoints'] else 'NO_ELIGIBLE_POINTS'
    return dict(facilityId=facility['id'], method='spherical-point-screen-v0.2', parameters=dict(facility=facility['coordinates'], asOf=stamp(end), hours=c['hours'], radiusKm=c['radiusKm']), coverage=coverage, status=status, matches=matches, limitations=LIMITATION)


def expected(snapshot_bytes, raw, config_bytes, c):
    require(isinstance(c, dict) and set(c) == {'snapshotKind','asOf','hours','radiusKm','facilities'}, 'Invalid configuration fields')
    require(c['snapshotKind'] in ('synthetic-demo','user-import-unverified'), 'Invalid kind')
    require(number(c['hours']) and int(c['hours']) == c['hours'] and 1 <= c['hours'] <= 720 and number(c['radiusKm']) and 1 <= c['radiusKm'] <= 1000, 'Invalid parameters')
    utc(c['asOf'])
    require(isinstance(c['facilities'], list) and 1 <= len(c['facilities']) <= 25, 'Invalid facility count')
    ids = set()
    for f in c['facilities']:
        require(isinstance(f, dict) and set(f) == {'id','coordinates'} and isinstance(f['id'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', f['id']) and f['id'] not in ids and point(f['coordinates']), 'Invalid or duplicate facility')
        ids.add(f['id'])
    return dict(schema='gaia-earth-batch-v0.3', snapshot=dict(kind=c['snapshotKind'], authenticity='unverified', **digest(snapshot_bytes)), configuration=digest(config_bytes), results=[screen(raw, c, f) for f in sorted(c['facilities'], key=lambda f:f['id'])])


def equal(a, b):
    if type(a) is dict and type(b) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if type(a) is list and type(b) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if number(a) and number(b):
        return a == b
    return type(a) is type(b) and a == b


def main(args):
    try:
        require(len(args) == 3, 'Usage: verify_earth_batch.py SNAPSHOT CONFIG REPORT')
        sb, raw = read(args[0], 2_000_000)
        cb, c = read(args[1], 32768)
        _, report = read(args[2], 16_000_000)
        require(equal(expected(sb, raw, cb, c), report), 'Replay mismatch: input digest, fields, coverage, distances or results')
    except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
        print(json.dumps({'status':'REJECTED','reason':str(exc),'sourceAuthenticated':False}))
        return 1
    print(json.dumps({'status':'REPLAY_MATCH','facilities':len(c['facilities']),'sourceAuthenticated':False,'scientificValidityEstablished':False}))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
