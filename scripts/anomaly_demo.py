"""Generate a manufactured, explicitly synthetic 20-day evidence bundle."""
import json
import sys
from datetime import date, timedelta
import eonet_archive as archive
import earth_evidence as evidence


def make_demo():
    events = {name: dict(id='SYN-' + name, title='Manufactured ' + name, geometry=[]) for name in ('A', 'B', 'FAR')}
    for i in range(20):
        day = (date(2025, 1, 1) + timedelta(days=i)).isoformat()
        for name, lon, count in [('A', 0, 2 if i == 19 else 1), ('B', 30, 2), ('FAR', 90, 1 if i == 19 else 2)]:
            for j in range(count):
                events[name]['geometry'].append(dict(type='Point', date=day + f'T12:0{j}:00Z', coordinates=[lon, 0]))
    source = archive.encode(dict(events=list(events.values())))
    config = archive.encode(dict(snapshotKind='synthetic-demo', asOf='2025-01-20T23:59:59.999Z', hours=480, radiusKm=100, facilities=[dict(id='EXAMPLE-A', coordinates=[0, 0]), dict(id='EXAMPLE-B', coordinates=[30, 0]), dict(id='EXAMPLE-C', coordinates=[60, 0])]))
    raw = archive.encode(archive.envelope(source, 'offline-import', '2026-11-26T12:00:00Z'))
    return evidence.pack(raw, config)


if __name__ == '__main__':
    try:
        archive.require(len(sys.argv) == 2, 'Usage: anomaly_demo.py NEW_BUNDLE.json')
        bundle, receipt = make_demo()
        archive.save_new(sys.argv[1], bundle)
        print(json.dumps(receipt))
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, evidence.subprocess.SubprocessError) as exc:
        print('Demo rejected: ' + str(exc), file=sys.stderr)
        sys.exit(1)
