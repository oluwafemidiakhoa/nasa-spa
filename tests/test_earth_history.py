import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import earth_evidence as evidence
import eonet_archive as archive
import verify_earth_history as history


def js_report(path):
    command = "import {readFile} from 'node:fs/promises';import {historyReport} from './history.mjs';console.log(JSON.stringify(await historyReport(await readFile(process.argv[1]))));"
    return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', command, str(path)], cwd=ROOT, timeout=30))


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'data/earth-evidence-synthetic.json'
        cls.bundle = cls.path.read_bytes()
        cls.report = js_report(cls.path)

    def check_fixture(self, events, as_of, hours, facilities):
        source = archive.encode({'events': events})
        config = archive.encode(dict(snapshotKind='synthetic-demo', asOf=as_of, hours=hours, radiusKm=100, facilities=facilities))
        raw_archive = archive.encode(archive.envelope(source, 'offline-import', '2026-11-26T12:00:00Z'))
        bundle, _ = evidence.pack(raw_archive, config)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bundle.json'
            path.write_bytes(bundle)
            result = js_report(path)
        self.assertEqual(history.expected(bundle, archive.sha(bundle)), result)
        return result

    def test_committed_bundle_independent_replay(self):
        self.assertEqual(history.expected(self.bundle, archive.sha(self.bundle)), self.report)
        self.assertEqual(len(self.report['facilities']), 3)
        self.assertEqual(len(self.report['facilities'][0]['days']), 4)

    def test_midnight_start_cutoff_and_antimeridian(self):
        def point(t, coords):
            return dict(type='Point', date=t, coordinates=coords)
        geometry = [point('2026-10-31T23:59:59.999Z', [-179.9, 0]), point('2026-11-01T00:00:00Z', [-179.9, 0]), point('2026-11-01T00:00:00Z', [-179.9, 0]), point('2026-11-01T23:59:59.999Z', [179.9, 0]), point('2026-11-02T00:00:00Z', [179.9, 0]), point('2026-11-02T00:00:00.001Z', [179.9, 0]), dict(type='Polygon', coordinates=[])]
        r = self.check_fixture([dict(id='event', title='Synthetic', geometry=geometry)], '2026-11-02T00:00:00Z', 24, [dict(id='A', coordinates=[179.9, 0])])
        self.assertEqual([(d['date'], d['matchingPointRows'], d['matchingEvents']) for d in r['facilities'][0]['days']], [('2026-11-01', 3, 1), ('2026-11-02', 1, 1)])

    def test_empty_maximum_window(self):
        r = self.check_fixture([], '2026-11-30T12:00:00Z', 720, [dict(id='A', coordinates=[0, 0])])
        rows = r['facilities'][0]['days']
        self.assertEqual(len(rows), 31)
        self.assertTrue(all(d['state'] == 'NO_ELIGIBLE_POINTS' and d['matchingEvents'] == 0 for d in rows))

    def test_wrong_anchor(self):
        with self.assertRaises(ValueError):
            history.expected(self.bundle, '0' * 64)

    def test_cli_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'history.json'
            args = [sys.executable, str(ROOT / 'scripts/verify_earth_history.py'), str(self.path), str(path)]
            path.write_text(json.dumps(self.report))
            self.assertEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)
            for field in ('matchingPointRows', 'matchingEvents', 'availablePointRows', 'state'):
                bad = json.loads(json.dumps(self.report))
                bad['facilities'][0]['days'][-1][field] = 'tampered'
                path.write_text(json.dumps(bad))
                self.assertNotEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)
            path.write_text('{"schema":1,"schema":2}')
            self.assertNotEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)


if __name__ == '__main__':
    unittest.main()
