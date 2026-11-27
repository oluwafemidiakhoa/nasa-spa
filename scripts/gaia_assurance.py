#!/usr/bin/env python3
"""Build and replay a bounded, offline Gaia Proof assurance dossier."""
import argparse
import base64
import json
import os
import stat
import sys
from pathlib import Path

import verify_gaia_proof as proof

MAX_DOSSIER = 55_000_000
SCHEMA = 'gaia-assurance-dossier-v1'
ERRORS = (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError)
LIMIT = ('Computational assurance on retained observations only. Same-team implementations, not an external audit. '
         'No source authenticity, coverage, trusted chronology, scientific validity, safety, certification or release authorization. '
         'Narrative metadata and display ordering are outside independent verification scope.')


def encode(obj):
    return (json.dumps(obj, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':'))+'\n').encode('ascii')


def read(path, cap):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as handle:
        proof.require(stat.S_ISREG(os.fstat(handle.fileno()).st_mode), 'Expected regular input file')
        raw = handle.read(cap+1)
    proof.require(0 < len(raw) <= cap, 'Input size limit')
    return raw


def implementation():
    return {name: proof.sha(Path(path).read_bytes()) for name, path in (
        ('gaia_assurance.py', __file__), ('verify_gaia_proof.py', proof.__file__))}


def assess(raw):
    proof.require(type(raw) is bytes and 0 < len(raw) <= proof.MAX_PACKET, 'Proof size limit')
    try:
        replay = proof.verify(raw)
        status, claim, source = 'PASS', replay['claim'], replay['sourceSha256']
    except proof.Inconclusive:
        status, claim, source = 'INCOMPLETE', None, None
    except ERRORS:
        status, claim, source = 'FAIL', None, None
    verdict = claim['verdict'] if claim else None
    claim_status = ('PASS' if verdict == 'CONDITIONALLY_SUPPORTED_AFTER_PERTURBATIONS' else
                    'FAIL' if verdict == 'UPPER_BOUND_BELOW_THRESHOLD_ON_RETAINED_RECORDS' else 'INCOMPLETE')
    controls = [
        dict(id='COMPUTATIONAL_REPLAY', status=status, evidence='Independent Python replay of retained proof and enumerated computational fields'),
        dict(id='CONDITIONAL_CLAIM', status=claim_status, evidence='Verified joint bounds on retained event IDs only; no general safety conclusion'),
    ]
    for key, detail in [
        ('SOURCE_AUTHENTICITY', 'No independently authenticated source'),
        ('SOURCE_COVERAGE', 'No verified complete observation population'),
        ('TRUSTED_CHRONOLOGY', 'No timestamp evidence bound to this proof'),
        ('SCIENTIFIC_VALIDITY', 'No external scientific validation of this claim'),
    ]:
        controls.append(dict(id=key, status='INCOMPLETE', evidence=detail))
    return dict(schema='gaia-assurance-report-v1', implementation=implementation(),
                packetSha256=proof.sha(raw), sourceSha256=source, claim=claim, controls=controls,
                conclusion='NO-GO' if 'FAIL' in (status, claim_status) else 'INCOMPLETE',
                certified=False, executionAuthorized=False, sourceAuthenticated=False,
                scientificValidityEstablished=False, limitations=LIMIT)


def build(raw):
    report = assess(raw)
    return encode(dict(schema=SCHEMA, proof=dict(sha256=report['packetSha256'], bytes=len(raw),
                       base64=base64.b64encode(raw).decode('ascii')), report=report))


def verify_dossier(raw):
    d = proof.parse(raw, MAX_DOSSIER)
    proof.fields(d, 'schema proof report')
    proof.check(d['schema'], SCHEMA, 'Unsupported dossier schema')
    original = proof.component(d['proof'], proof.MAX_PACKET)
    expected = assess(original)
    proof.check(d['report'], expected, 'Assurance report does not replay with this implementation')
    return expected


def session(report, dossier, *, packet_anchor='', source_anchor='', dossier_anchor=''):
    checks = {}
    for name, anchor, actual in [('packet', packet_anchor, report['packetSha256']),
                                 ('source', source_anchor, report['sourceSha256']),
                                 ('dossier', dossier_anchor, proof.sha(dossier))]:
        proof.require(not anchor or proof.hexhash(anchor), 'Expected lowercase SHA-256')
        checks[name] = ('NOT_SUPPLIED' if not anchor else 'NOT_CHECKABLE' if actual is None else
                        'MATCHED' if anchor == actual else 'MISMATCH')
    return dict(schema='gaia-assurance-session-v1', dossierSha256=proof.sha(dossier),
                dossierReplay='MATCHED', anchors=checks, report=report,
                conclusion='NO-GO' if 'MISMATCH' in checks.values() else report['conclusion'],
                certified=False, executionAuthorized=False,
                limitations='Supplied digests establish byte binding only. Anchor provenance is not verified.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'verify'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    for name in ['packet', 'source', 'dossier']:
        parser.add_argument('--'+name+'-sha256', default='')
    args = parser.parse_args(argv)
    try:
        proof.require((args.action == 'build') == bool(args.output), 'Build requires --output; verify does not write')
        raw = read(args.input, proof.MAX_PACKET if args.action == 'build' else MAX_DOSSIER)
        dossier = build(raw) if args.action == 'build' else raw
        report = verify_dossier(dossier)
        result = session(report, dossier, packet_anchor=args.packet_sha256,
                         source_anchor=args.source_sha256, dossier_anchor=args.dossier_sha256)
        if args.action == 'build':
            # Exclusive creation: no replacement of an existing file or symlink.
            with args.output.open('xb') as handle:
                handle.write(dossier)
        code = 1 if result['conclusion'] == 'NO-GO' else 2
    except ERRORS + (OSError,) as exc:
        result = dict(status='REJECTED', reason=str(exc)[:180], conclusion='NO-GO',
                      certified=False, executionAuthorized=False)
        code = 1
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
