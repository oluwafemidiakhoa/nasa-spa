"""Independent retrospective history replay from an original v0.5 bundle."""
import argparse
import json
import sys
from datetime import timedelta

import earth_evidence as evidence
import eonet_archive as archive
import verify_earth_batch as independent


def expected(bundle, anchor=None):
    receipt = evidence.verify(bundle, anchor)
    data = archive.parse(bundle)
    files = {name: evidence.unpack(data['files'][name], limit) for name, limit in evidence.LIMITS.items()}
    source, _ = archive.verify(files['archive'])
    snapshot, config = archive.parse(source), archive.parse(files['configuration'])
    end = independent.utc(config['asOf'])
    start = end - timedelta(hours=config['hours'])
    count = (end.date() - start.date()).days + 1
    archive.require(1 <= count <= 31, 'Unsupported history interval')
    dates = [(start.date() + timedelta(days=i)).isoformat() for i in range(count)]
    bins = {day: [] for day in dates}
    for event in snapshot['events']:
        for g in event['geometry']:
            if g['type'] == 'Point':
                timestamp = independent.utc(g['date'])
                if start <= timestamp <= end:
                    bins[timestamp.date().isoformat()].append((event['id'], g['coordinates']))
    facilities = []
    for f in sorted(config['facilities'], key=lambda x: x['id']):
        rows = []
        for day, points in bins.items():
            matches = [event for event, coords in points if independent.distance(f['coordinates'], coords) <= config['radiusKm']]
            rows.append(dict(date=day, availablePointRows=len(points), matchingPointRows=len(matches), matchingEvents=len(set(matches)), state='OBSERVATIONS_AVAILABLE' if points else 'NO_ELIGIBLE_POINTS'))
        facilities.append(dict(id=f['id'], coordinates=f['coordinates'], days=rows))
    return dict(schema='gaia-earth-history-v0.7', bundleSha256=receipt['bundleSha256'], sourceSha256=receipt['sourceSha256'], snapshotKind=config['snapshotKind'], coverage='unknown', startUtc=independent.stamp(start), endUtc=independent.stamp(end), radiusKm=config['radiusKm'], facilities=facilities)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    parser.add_argument('report')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    try:
        bundle = archive.read_file(args.bundle, evidence.MAX_BUNDLE)
        report = archive.parse(archive.read_file(args.report, 1_000_000))
        archive.require(independent.equal(expected(bundle, args.expected_sha256), report), 'History replay mismatch')
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, evidence.subprocess.SubprocessError) as exc:
        print('History rejected: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(dict(status='HISTORY_REPLAY_MATCH', facilities=len(report['facilities']), dates=len(report['facilities'][0]['days']), anchorChecked=args.expected_sha256 is not None, sourceAuthenticated=False, scientificValidityEstablished=False)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
