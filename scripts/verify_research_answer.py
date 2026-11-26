"""Replay a deterministic research answer against the original evidence bundle."""
import argparse
import json
import re
import sys

import earth_evidence as evidence
import eonet_archive as archive
import verify_earth_anomaly as anomaly
import verify_earth_batch as independent
import verify_earth_history as history

ID = r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}'
MESSAGES = {
    'ABOVE_BASELINE_MAX': 'The target share strictly exceeded all 19 baseline shares.',
    'NOT_ABOVE_BASELINE_MAX': 'The target share did not strictly exceed every baseline share.',
    'INSUFFICIENT_BASELINE': 'The screening abstained because there were fewer than 19 complete baseline dates or no complete target date.',
    'INSUFFICIENT_OBSERVATIONS': 'The screening abstained because at least one required date contained fewer than five eligible point rows.',
}


def answer(h, q):
    archive.require(isinstance(q, str) and re.fullmatch(r'[\x20-\x7e]{1,160}', q), 'Query must contain 1-160 printable ASCII characters.')
    s = anomaly.screen(h)
    facts = []
    outcome = 'ANSWERED'

    def fact(label, report, pointer, value):
        facts.append(dict(label=label, report=report, pointer=pointer, value=value))

    if q == 'summary':
        reason, message = 'FACILITY_SUMMARY', 'Screening statuses for every facility in the retained window.'
        for i, f in enumerate(s['facilities']):
            fact('Facility', 'screening', f'/facilities/{i}/id', f['id'])
            fact('Status', 'screening', f'/facilities/{i}/status', f['status'])
    elif q == 'provenance':
        reason, message = 'SOURCE_PROVENANCE', 'The original retained input is identified below; authenticity is not established.'
        for label, key in [('Bundle SHA-256', 'bundleSha256'), ('Source SHA-256', 'sourceSha256'), ('Declared snapshot kind', 'snapshotKind'), ('Coverage', 'coverage'), ('Window start UTC', 'startUtc'), ('Window end UTC', 'endUtc'), ('Radius (km)', 'radiusKm')]:
            fact(label, 'history', '/' + key, h[key])
    elif q == 'limits':
        reason = 'METHOD_LIMITS'
        message = 'Archived observation descriptions only. No safety, hazard probability, causal, predictive or statistical significance conclusion is supported.'
    else:
        explain = re.fullmatch(r'explain (' + ID + r')', q)
        daily = re.fullmatch(r'day (' + ID + r') (\d{4}-\d{2}-\d{2})', q)
        if not explain and not daily:
            outcome, reason, message = 'ABSTAINED', 'UNSUPPORTED_QUERY', 'Unsupported question. Use one of the five exact query types.'
        else:
            identifier = (explain or daily).group(1)
            index = next((i for i, f in enumerate(h['facilities']) if f['id'] == identifier), None)
            if index is None:
                outcome, reason, message = 'ABSTAINED', 'FACILITY_NOT_FOUND', 'The requested facility is not in the retained bundle.'
            elif explain:
                f = s['facilities'][index]
                reason, message = 'SCREENING_EXPLANATION', MESSAGES[f['status']]
                fact('Screening policy', 'screening', '/policy', s['policy'])
                fact('Facility screening record', 'screening', f'/facilities/{index}', f)
                if f['rankNumerator'] is None:
                    outcome, reason = 'ABSTAINED', f['status']
            else:
                j = next((j for j, d in enumerate(h['facilities'][index]['days']) if d['date'] == daily.group(2)), None)
                if j is None:
                    outcome, reason, message = 'ABSTAINED', 'DATE_NOT_FOUND', 'The requested UTC date is not in the retained window.'
                else:
                    row = h['facilities'][index]['days'][j]
                    reason = 'DAILY_RECORD'
                    message = 'No eligible point rows were recorded for this date; this is not evidence of safety.' if row['state'] == 'NO_ELIGIBLE_POINTS' else 'The available, matching and distinct-event counts are shown for the requested UTC date.'
                    fact('Facility', 'history', f'/facilities/{index}/id', identifier)
                    fact('Daily observation record', 'history', f'/facilities/{index}/days/{j}', row)
    return dict(schema='gaia-research-answer-v0.9', query=q, bundleSha256=h['bundleSha256'], sourceSha256=h['sourceSha256'], snapshotKind=h['snapshotKind'], coverage='unknown', sourceAuthenticated=False, scientificValidityEstablished=False, outcome=outcome, reason=reason, message=message, facts=facts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle')
    p.add_argument('report')
    p.add_argument('--query', required=True)
    p.add_argument('--expected-sha256')
    a = p.parse_args()
    try:
        raw = archive.read_file(a.bundle, evidence.MAX_BUNDLE)
        report = archive.parse(archive.read_file(a.report, 1_000_000))
        archive.require(independent.equal(answer(history.expected(raw, a.expected_sha256), a.query), report), 'Research answer replay mismatch')
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, evidence.subprocess.SubprocessError) as exc:
        print('Answer rejected: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(dict(status='ANSWER_REPLAY_MATCH', query=report['query'], outcome=report['outcome'], facts=len(report['facts']), anchorChecked=a.expected_sha256 is not None, sourceAuthenticated=False, scientificValidityEstablished=False)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
