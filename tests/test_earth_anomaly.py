import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import anomaly_demo
import eonet_archive as archive
import earth_evidence as evidence
import verify_earth_anomaly as anomaly
import verify_earth_history as history


def js_report(path):
    code = "import {readFile} from 'node:fs/promises';import {anomalyReport} from './anomaly.mjs';console.log(JSON.stringify(await anomalyReport(await readFile(process.argv[1]))));"
    return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', code, str(path)], cwd=ROOT, timeout=30))


class AnomalyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, _ = anomaly_demo.make_demo()
        cls.history = history.expected(cls.bundle, archive.sha(cls.bundle))
        cls.expected = anomaly.screen(cls.history)

    def test_independent_manufactured_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'demo.json'
            p.write_bytes(self.bundle)
            self.assertEqual(js_report(p), self.expected)
        self.assertEqual(self.expected['targetDate'], '2025-01-20')
        self.assertEqual([(f['status'], f['rankNumerator']) for f in self.expected['facilities']], [('ABOVE_BASELINE_MAX', 1), ('NOT_ABOVE_BASELINE_MAX', 20), ('NOT_ABOVE_BASELINE_MAX', 20)])

    def test_short_fixture_abstains(self):
        p = ROOT / 'data/earth-evidence-synthetic.json'
        result = anomaly.screen(history.expected(p.read_bytes()))
        self.assertEqual(js_report(p), result)
        self.assertTrue(all(f['rankNumerator'] is None for f in result['facilities']))

    def test_low_observation_and_tied_fraction(self):
        h = json.loads(json.dumps(self.history))
        h['facilities'][0]['days'][1]['availablePointRows'] = 4
        self.assertEqual(anomaly.screen(h)['facilities'][0]['status'], 'INSUFFICIENT_OBSERVATIONS')
        h = json.loads(json.dumps(self.history))
        day = next(d for d in h['facilities'][0]['days'] if d['date'] == '2025-01-01')
        day.update(availablePointRows=10, matchingPointRows=4)
        self.assertEqual(anomaly.screen(h)['facilities'][0]['rankNumerator'], 2)

    def test_cli_integrity_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            b, r = Path(tmp) / 'bundle.json', Path(tmp) / 'report.json'
            b.write_bytes(self.bundle)
            r.write_text(json.dumps(self.expected))
            args = [sys.executable, str(ROOT / 'scripts/verify_earth_anomaly.py'), str(b), str(r)]
            self.assertEqual(subprocess.run(args + ['--expected-sha256', archive.sha(self.bundle)], capture_output=True, timeout=30).returncode, 0)
            self.assertNotEqual(subprocess.run(args + ['--expected-sha256', '0' * 64], capture_output=True, timeout=30).returncode, 0)
            for field, val in [('rankNumerator', 2), ('status', 'NOT_ABOVE_BASELINE_MAX'), ('target', None)]:
                bad = json.loads(json.dumps(self.expected))
                bad['facilities'][0][field] = val
                r.write_text(json.dumps(bad))
                self.assertNotEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)
            r.write_text('{"schema":1,"schema":2}')
            self.assertNotEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)

    def test_changed_bundle_rejected(self):
        b = archive.parse(self.bundle)
        report = archive.parse(evidence.unpack(b['files']['report'], evidence.LIMITS['report']))
        report['results'][0]['matches'][0]['distanceKm'] = 1
        b['files']['report'] = evidence.component(archive.encode(report), evidence.LIMITS['report'])
        with self.assertRaises(ValueError):
            history.expected(archive.encode(b))


if __name__ == '__main__':
    unittest.main()
