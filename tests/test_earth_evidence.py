"""Offline integration and negative tests against both actual implementations."""
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import earth_evidence as evidence
import eonet_archive as archive


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'data/earth-observatory-synthetic.json').read_bytes()
        cls.config = (ROOT / 'data/earth-facilities-synthetic.json').read_bytes()
        cls.raw_archive = archive.encode(archive.envelope(cls.source, 'offline-import', '2026-11-26T12:00:00Z'))
        cls.bundle, cls.receipt = evidence.pack(cls.raw_archive, cls.config, archive.sha(cls.raw_archive))

    def data(self):
        return archive.parse(self.bundle)

    def reject(self, obj):
        with self.assertRaises(ValueError):
            evidence.verify(archive.encode(obj))

    def test_exact_bytes_and_independent_replay(self):
        self.assertEqual(self.receipt['facilities'], 3)
        self.assertFalse(self.receipt['sourceAuthenticated'])
        self.assertFalse(self.receipt['scientificValidityEstablished'])
        files = self.data()['files']
        self.assertEqual(evidence.unpack(files['archive'], evidence.LIMITS['archive']), self.raw_archive)
        self.assertEqual(evidence.unpack(files['configuration'], 32768), self.config)
        result = archive.parse(evidence.unpack(files['report'], 16_000_000))['results']
        self.assertEqual([r['status'] for r in result], ['POINTS_WITHIN_RADIUS', 'POINTS_WITHIN_RADIUS', 'NO_MATCH_IN_AVAILABLE_POINTS'])
        checked = evidence.verify(self.bundle, archive.sha(self.bundle))
        self.assertTrue(checked['anchorChecked'])
        self.assertEqual(checked['sourceSha256'], archive.sha(self.source))

    def test_deterministic_bundle(self):
        self.assertEqual(evidence.pack(self.raw_archive, self.config)[0], self.bundle)

    def test_wrong_anchor(self):
        with self.assertRaises(ValueError):
            evidence.verify(self.bundle, '0' * 64)
        with self.assertRaises(ValueError):
            evidence.pack(self.raw_archive, self.config, '0' * 64)

    def test_component_tampering(self):
        for name in evidence.LIMITS:
            for field, value in [('sha256', '0' * 64), ('bytes', 1), ('base64', '!!!!')]:
                with self.subTest(name=name, field=field):
                    obj = self.data()
                    obj['files'][name][field] = value
                    self.reject(obj)

    def test_recomputed_component_hashes(self):
        obj = self.data()
        report = archive.parse(base64.b64decode(obj['files']['report']['base64']))
        report['results'][0]['matches'][0]['distanceKm'] = 0
        obj['files']['report'] = evidence.component(archive.encode(report), evidence.LIMITS['report'])
        self.reject(obj)
        obj = self.data()
        config = archive.parse(self.config)
        config['radiusKm'] = 1
        obj['files']['configuration'] = evidence.component(archive.encode(config), 32768)
        self.reject(obj)
        obj = self.data()
        altered = archive.parse(self.raw_archive)
        altered['receipt']['pointCount'] = 999
        obj['files']['archive'] = evidence.component(archive.encode(altered), evidence.LIMITS['archive'])
        self.reject(obj)

    def test_invalid_schema_and_method(self):
        for field in ['schema', 'methods', 'files']:
            obj = self.data()
            obj.pop(field)
            self.reject(obj)
        obj = self.data()
        obj['extra'] = True
        self.reject(obj)
        obj = self.data()
        obj['methods']['earth.mjs'] = '0' * 64
        self.reject(obj)
        with self.assertRaises(ValueError):
            evidence.verify(b'{"schema":1,"schema":2}')
        with self.assertRaises(ValueError):
            evidence.verify(b'x' * (evidence.MAX_BUNDLE + 1))

    def test_https_archive_not_synthetic(self):
        q = archive.query('2026-11-01', '2026-11-01', 'wildfires', 10)
        raw = archive.encode(archive.envelope(self.source, 'https-eonet', '2026-11-26T12:00:00Z', q))
        with self.assertRaises(ValueError):
            evidence.pack(raw, self.config)

    def test_cli_no_overwrite_and_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            src, cfg, out = d / 'archive.json', d / 'config.json', d / 'bundle.json'
            src.write_bytes(self.raw_archive)
            cfg.write_bytes(self.config)
            args = [sys.executable, str(ROOT / 'scripts/earth_evidence.py'), 'pack', str(src), str(cfg), str(out)]
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
            first = out.read_bytes()
            self.assertEqual(first, self.bundle)
            self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)
            self.assertEqual(first, out.read_bytes())
            out.unlink()
            cfg.write_bytes(b'{"snapshotKind":"synthetic-demo","snapshotKind":"synthetic-demo"}')
            self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())
            self.assertFalse(list(d.glob('.gaia-*')))

    def test_timeout_and_failed_replay(self):
        with patch('earth_evidence.subprocess.run', side_effect=subprocess.TimeoutExpired('worker', 20)):
            with self.assertRaises(subprocess.TimeoutExpired):
                evidence.verify(self.bundle)
        with patch('earth_evidence.subprocess.run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(ValueError):
                evidence.verify(self.bundle)


if __name__ == '__main__':
    unittest.main()
