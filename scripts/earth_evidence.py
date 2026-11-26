"""Pack an EONET archive and independently replayed Earth screening report."""
import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import eonet_archive as archive

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 'gaia-earth-evidence-v0.5'
LIMITS = {'archive': archive.MAX_ARCHIVE, 'configuration': 32768, 'report': 16_000_000}
MAX_BUNDLE = 26_000_000
METHODS = ('scripts/eonet_archive.py', 'earth.mjs', 'scripts/earth-batch.mjs',
           'scripts/verify_earth_batch.py')
require = archive.require


def fingerprints():
    return {name: archive.sha(archive.read_file(ROOT / name, 1_000_000)) for name in METHODS}


def component(raw, limit):
    require(0 < len(raw) <= limit, 'Component size out of bounds')
    return {'sha256': archive.sha(raw), 'bytes': len(raw),
            'base64': base64.b64encode(raw).decode('ascii')}


def unpack(value, limit):
    require(isinstance(value, dict) and set(value) == {'sha256', 'bytes', 'base64'}
            and type(value['bytes']) is int and 0 < value['bytes'] <= limit
            and isinstance(value['base64'], str)
            and len(value['base64']) == 4 * ((value['bytes'] + 2) // 3), 'Invalid component')
    raw = base64.b64decode(value['base64'], validate=True)
    require(component(raw, limit) == value, 'Component digest, length or encoding mismatch')
    return raw


def inputs(raw_archive, config, expected_archive=None):
    snapshot, result = archive.verify(raw_archive, expected_archive)
    cfg = archive.parse(config)
    require(isinstance(cfg, dict) and cfg.get('snapshotKind') in
            ('synthetic-demo', 'user-import-unverified'), 'Invalid snapshot declaration')
    require(not (result['receipt']['mode'] == 'https-eonet' and
                 cfg['snapshotKind'] == 'synthetic-demo'), 'HTTPS archive cannot be declared synthetic')
    return snapshot, result


def worker(args, output, limit):
    with output.open('wb') as stream:
        done = subprocess.run(args, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stream,
                              stderr=subprocess.DEVNULL, timeout=20, check=False)
    require(done.returncode == 0, 'Screening or independent replay rejected the inputs')
    return archive.read_file(output, limit)


def replay(snapshot, config, report=None):
    with tempfile.TemporaryDirectory(prefix='gaia-replay-') as tmp:
        directory = Path(tmp)
        src, cfg, result = (directory / name for name in ('snapshot.json', 'config.json', 'report.json'))
        src.write_bytes(snapshot)
        cfg.write_bytes(config)
        if report is None:
            report = worker(['node', str(ROOT / 'scripts/earth-batch.mjs'), str(src), str(cfg)],
                            result, LIMITS['report'])
        else:
            result.write_bytes(report)
        receipt = archive.parse(worker([sys.executable, str(ROOT / 'scripts/verify_earth_batch.py'),
                                         str(src), str(cfg), str(result)], directory / 'replay.json', 4096))
        require(isinstance(receipt, dict) and set(receipt) == {'status', 'facilities',
                'sourceAuthenticated', 'scientificValidityEstablished'} and receipt['status'] == 'REPLAY_MATCH'
                and type(receipt['facilities']) is int and 1 <= receipt['facilities'] <= 25
                and receipt['sourceAuthenticated'] is False and receipt['scientificValidityEstablished'] is False,
                'Invalid independent replay receipt')
        return report, receipt


def pack(raw_archive, config, expected_archive=None):
    methods = fingerprints()
    snapshot, _ = inputs(raw_archive, config, expected_archive)
    report, _ = replay(snapshot, config)
    require(fingerprints() == methods, 'Implementation changed during pack')
    bundle = archive.encode({'schema': SCHEMA, 'methods': methods,
        'files': {name: component(raw, LIMITS[name]) for name, raw in
                  zip(LIMITS, (raw_archive, config, report))}})
    receipt = verify(bundle)
    return bundle, receipt


def verify(bundle, expected=None):
    require(0 < len(bundle) <= MAX_BUNDLE, 'Empty or oversized bundle')
    digest = archive.sha(bundle)
    if expected is not None:
        require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected)
                and expected == digest, 'Bundle digest mismatch')
    data = archive.parse(bundle)
    require(isinstance(data, dict) and set(data) == {'schema', 'methods', 'files'}
            and data['schema'] == SCHEMA and isinstance(data['files'], dict)
            and set(data['files']) == set(LIMITS), 'Invalid bundle schema')
    methods = fingerprints()
    require(data['methods'] == methods, 'Implementation fingerprint mismatch')
    files = {name: unpack(data['files'][name], limit) for name, limit in LIMITS.items()}
    snapshot, record = inputs(files['archive'], files['configuration'])
    _, receipt = replay(snapshot, files['configuration'], files['report'])
    require(fingerprints() == methods, 'Implementation changed during replay')
    return {**receipt, 'bundleSha256': digest, 'anchorChecked': expected is not None,
            'archiveSha256': record['archiveSha256'], 'sourceSha256': record['receipt']['sourceSha256'],
            'snapshotKind': archive.parse(files['configuration'])['snapshotKind'], 'coverage': 'unknown'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('pack')
    build.add_argument('archive')
    build.add_argument('configuration')
    build.add_argument('output')
    build.add_argument('--expected-archive-sha256')
    check = commands.add_parser('verify')
    check.add_argument('bundle')
    check.add_argument('--expected-sha256')
    args = parser.parse_args()
    try:
        if args.command == 'pack':
            bundle, receipt = pack(archive.read_file(args.archive, LIMITS['archive']),
                                   archive.read_file(args.configuration, LIMITS['configuration']),
                                   args.expected_archive_sha256)
            archive.save_new(args.output, bundle)
        else:
            receipt = verify(archive.read_file(args.bundle, MAX_BUNDLE), args.expected_sha256)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, subprocess.SubprocessError) as exc:
        print('Evidence rejected: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
