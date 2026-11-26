"""Cross-runtime tests against the actual command-line entry points."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/earth-observatory-synthetic.json'
CONFIG = ROOT / 'data/earth-facilities-synthetic.json'


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = cls.generate(SNAPSHOT, CONFIG)
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.baseline = json.loads(result.stdout)

    @staticmethod
    def generate(snapshot, config):
        return subprocess.run(['node', str(ROOT/'scripts/earth-batch.mjs'), str(snapshot), str(config)], capture_output=True, text=True, timeout=10)

    def verify(self, report, snapshot=SNAPSHOT, config=CONFIG):
        return subprocess.run([sys.executable, str(ROOT/'scripts/verify_earth_batch.py'), str(snapshot), str(config), str(report)], capture_output=True, text=True, timeout=10)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def write(self, name, data):
        p = self.dir/name
        p.write_text(json.dumps(data), encoding='utf-8')
        return p

    def assert_rejected(self, report, snapshot=SNAPSHOT, config=CONFIG):
        result = self.verify(report, snapshot, config)
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'REJECTED')

    def test_replay_and_known_results(self):
        r = self.baseline
        self.assertEqual([x['facilityId'] for x in r['results']], ['EXAMPLE-A','EXAMPLE-B','EXAMPLE-C'])
        self.assertEqual([x['status'] for x in r['results']], ['POINTS_WITHIN_RADIUS','POINTS_WITHIN_RADIUS','NO_MATCH_IN_AVAILABLE_POINTS'])
        self.assertEqual([r['results'][0]['matches'][0]['distanceKm'],r['results'][1]['matches'][0]['distanceKm']], [14.707,0])
        self.assertEqual(r['snapshot']['sha256'], hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())
        self.assertEqual(r['configuration']['sha256'], hashlib.sha256(CONFIG.read_bytes()).hexdigest())
        result = self.verify(self.write('r.json', r))
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout), {'status':'REPLAY_MATCH','facilities':3,'sourceAuthenticated':False,'scientificValidityEstablished':False})

    def test_deterministic_generator(self):
        self.assertEqual(self.generate(SNAPSHOT,CONFIG).stdout,self.generate(SNAPSHOT,CONFIG).stdout)

    def test_report_tampering(self):
        mutations = {
            'snapshot digest': lambda r: r['snapshot'].update(sha256='0'*64),
            'configuration digest': lambda r: r['configuration'].update(sha256='0'*64),
            'distance': lambda r: r['results'][0]['matches'][0].update(distanceKm=1),
            'title': lambda r: r['results'][0]['matches'][0].update(title='Changed'),
            'coverage': lambda r: r['results'][0]['coverage'].update(eligiblePoints=999),
            'boolean count': lambda r: r['results'][0]['coverage'].update(unsupportedGeometries=True),
            'parameters': lambda r: r['results'][0]['parameters'].update(radiusKm=1),
            'missing facility': lambda r: r['results'].pop(),
            'reordered facilities': lambda r: r['results'].reverse(),
            'extra field': lambda r: r.update(sourceAuthenticated=True),
            'hidden match': lambda r: r['results'][0]['matches'].clear(),
            'source kind': lambda r: r['snapshot'].update(kind='user-import-unverified'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                report = copy.deepcopy(self.baseline)
                mutate(report)
                self.assert_rejected(self.write('r.json',report))

    def test_original_snapshot_bytes_required(self):
        alternate = self.dir/'snapshot.json'
        alternate.write_bytes(SNAPSHOT.read_bytes()+b' ')
        self.assert_rejected(self.write('r.json',self.baseline),snapshot=alternate)

    def test_original_config_bytes_required(self):
        alternate = self.dir/'config.json'
        alternate.write_bytes(CONFIG.read_bytes()+b' ')
        self.assert_rejected(self.write('r.json',self.baseline),config=alternate)

    def test_wrong_configuration_even_with_recomputed_digest(self):
        config = json.loads(CONFIG.read_bytes())
        config['radiusKm'] = 10
        path = self.write('config.json',config)
        report = copy.deepcopy(self.baseline)
        report['configuration'] = {'bytes':len(path.read_bytes()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        self.assert_rejected(self.write('r.json',report),config=path)

    def test_generator_invalid_configuration(self):
        mutations = {
            'duplicate IDs': lambda c: c['facilities'].append(c['facilities'][0]),
            'coordinate out of range': lambda c: c['facilities'][0].update(coordinates=[181,0]),
            'boolean coordinate': lambda c: c['facilities'][0].update(coordinates=[True,0]),
            'bad timestamp': lambda c: c.update(asOf='2026-02-30T00:00:00Z'),
            'bad ID': lambda c: c['facilities'][0].update(id='bad/id'),
            'zero facilities': lambda c: c.update(facilities=[]),
            'too many facilities': lambda c: c.update(facilities=[{'id':f'F{i}','coordinates':[0,0]} for i in range(26)]),
            'unknown kind': lambda c: c.update(snapshotKind='verified-nasa'),
            'unknown parameter': lambda c: c.update(extra=True),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                config = json.loads(CONFIG.read_bytes())
                mutate(config)
                result = self.generate(SNAPSHOT,self.write('config.json',config))
                self.assertEqual(result.returncode,1)
                self.assertEqual(result.stdout,'')

    def test_duplicate_report_key_rejected(self):
        r = self.dir/'r.json'
        r.write_text('{"schema":"gaia-earth-batch-v0.3",'+json.dumps(self.baseline)[1:],encoding='utf-8')
        self.assert_rejected(r)

    def test_duplicate_snapshot_key_rejected_at_replay(self):
        p = self.dir/'snapshot.json'
        p.write_text('{"events":[],'+SNAPSHOT.read_text(encoding='utf-8')[1:],encoding='utf-8')
        generated = self.generate(p,CONFIG)
        self.assertEqual(generated.returncode,0)
        self.assert_rejected(self.write('r.json',json.loads(generated.stdout)),snapshot=p)

    def test_oversized_snapshot_rejected(self):
        p = self.dir/'snapshot.json'
        p.write_bytes(b' '*2_000_001)
        generated = self.generate(p,CONFIG)
        self.assertEqual(generated.returncode,1)
        self.assertEqual(generated.stdout,'')

    def test_antimeridian_and_time_window(self):
        raw = {'events':[{'id':'X','title':'Synthetic','geometry':[{'type':'Point','date':'2026-11-01T12:00:00Z','coordinates':[-179,0]},{'type':'Point','date':'2026-11-01T12:00:00.001Z','coordinates':[179,0]}]}]}
        cfg = {'snapshotKind':'synthetic-demo','asOf':'2026-11-01T12:00:00Z','hours':1,'radiusKm':300,'facilities':[{'id':'EDGE','coordinates':[179,0]}]}
        s,c = self.write('s.json',raw),self.write('c.json',cfg)
        generated = self.generate(s,c)
        self.assertEqual(generated.returncode,0,generated.stderr)
        report = json.loads(generated.stdout)
        self.assertEqual(report['results'][0]['matches'][0]['distanceKm'],222.39)
        self.assertEqual(report['results'][0]['coverage']['outsideWindow'],1)
        result = self.verify(self.write('r.json',report),s,c)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
