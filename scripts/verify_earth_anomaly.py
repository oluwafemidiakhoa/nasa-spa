"""Independent descriptive screening replay from the original v0.5 bundle."""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import eonet_archive as archive
import earth_evidence as evidence
import verify_earth_batch as independent
import verify_earth_history as history


def screen(h):
    start, end = independent.utc(h['startUtc']), independent.utc(h['endUtc'])
    full = []
    for row in h['facilities'][0]['days']:
        day = datetime.fromisoformat(row['date']).replace(tzinfo=timezone.utc)
        if start <= day and day + timedelta(days=1, milliseconds=-1) <= end:
            full.append(row['date'])
    target = full[-1] if full else None
    baseline = full[:-1][-19:]
    facilities = []
    for facility in h['facilities']:
        lookup = {r['date']: {k: r[k] for k in ('date', 'availablePointRows', 'matchingPointRows')} for r in facility['days']}
        current = lookup[target] if target else None
        prior = [lookup[d] for d in baseline]
        numerator = denominator = None
        status = 'INSUFFICIENT_BASELINE'
        if current is not None and len(prior) == 19:
            if any(r['availablePointRows'] < 5 for r in [current, *prior]):
                status = 'INSUFFICIENT_OBSERVATIONS'
            else:
                def share(r):
                    return Fraction(r['matchingPointRows'], r['availablePointRows'])
                numerator = 1 + sum(share(r) >= share(current) for r in prior)
                denominator = 20
                status = 'ABOVE_BASELINE_MAX' if numerator == 1 else 'NOT_ABOVE_BASELINE_MAX'
        facilities.append(dict(id=facility['id'], target=current, baseline=prior, rankNumerator=numerator, rankDenominator=denominator, status=status))
    return dict(schema='gaia-earth-anomaly-v0.8', policy='daily-point-share-19-full-days-min5-v1', bundleSha256=h['bundleSha256'], sourceSha256=h['sourceSha256'], snapshotKind=h['snapshotKind'], coverage='unknown', targetDate=target, baselineDates=baseline, radiusKm=h['radiusKm'], facilities=facilities)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle')
    p.add_argument('report')
    p.add_argument('--expected-sha256')
    a = p.parse_args()
    try:
        raw = archive.read_file(a.bundle, evidence.MAX_BUNDLE)
        report = archive.parse(archive.read_file(a.report, 1_000_000))
        archive.require(independent.equal(screen(history.expected(raw, a.expected_sha256)), report), 'Anomaly replay mismatch')
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, evidence.subprocess.SubprocessError) as exc:
        print('Anomaly report rejected: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(dict(status='ANOMALY_REPLAY_MATCH', facilities=len(report['facilities']), anchorChecked=a.expected_sha256 is not None, sourceAuthenticated=False, scientificValidityEstablished=False)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
