import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import eonet_archive as a

STAMP = '2026-11-01T12:00:00Z'
Q = a.query('2025-01-07','2025-01-15','wildfires',2)
BODY = b'{"events":[{"id":"A","title":"Synthetic","geometry":[{"type":"Point","date":"2025-01-08T00:00:00Z","coordinates":[-95,30]},{"type":"Polygon"}]}]}\n'


class ArchiveTests(unittest.TestCase):
    def test_query_contract(self):
        self.assertEqual(a.query_path(Q), '/api/v3/events?status=all&start=2025-01-07&end=2025-01-15&category=wildfires&limit=2')
        for args in [('2025-02-30','2025-03-01','wildfires',1),('2025-01-01','2025-02-01','wildfires',1),('2025-01-02','2025-01-01','wildfires',1),('2025-01-01','2025-01-01','x&limit=999',1),('2025-01-01','2025-01-01','wildfires',201),('2025-01-01','2025-01-01','wildfires',True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                a.query(*args)

    def test_exact_bytes_and_anchor(self):
        archive = a.encode(a.envelope(BODY,'offline-import',STAMP))
        raw, report = a.verify(archive,hashlib.sha256(archive).hexdigest())
        self.assertEqual(raw,BODY)
        self.assertTrue(report['anchorChecked'])
        self.assertEqual(report['receipt']['sourceSha256'],hashlib.sha256(BODY).hexdigest())
        self.assertIsNone(report['receipt']['requestUrl'])
        self.assertIsNone(report['receipt']['httpStatus'])
        self.assertFalse(report['receipt']['sourceAuthenticated'])
        self.assertEqual(report['receipt']['pointCount'],1)
        self.assertEqual(report['receipt']['nonPointCount'],1)
        with self.assertRaises(ValueError): a.verify(archive,'0'*64)
        with self.assertRaises(ValueError): a.verify(archive+b' ',hashlib.sha256(archive).hexdigest())

    def test_https_receipt_cap_and_unknown_coverage(self):
        q = dict(Q,limit=1)
        r = a.envelope(BODY,'https-eonet',STAMP,q)['receipt']
        self.assertEqual(r['httpStatus'],200)
        self.assertTrue(r['limitReached'])
        self.assertEqual(r['coverage'],'unknown')
        self.assertTrue(r['requestUrl'].startswith('https://eonet.gsfc.nasa.gov/'))
        self.assertFalse(r['sourceAuthenticated'])
        self.assertFalse(a.envelope(BODY,'https-eonet',STAMP,Q)['receipt']['limitReached'])
        with self.assertRaises(ValueError): a.envelope(BODY,'offline-import',STAMP,Q)

    def test_malformed_sources(self):
        for raw in [b'{}',b'{"events":[],"events":[]}',b'{"events":[{"id":"A","title":"x","geometry":[]},{"id":"A","title":"x","geometry":[]}]}',BODY.replace(b'-95',b'181'),BODY.replace(b'-95',b'true'),BODY.replace(b'2025-01-08',b'2025-02-30'),BODY.replace(b'00:00:00Z',b'00:00:00'),b'{"events":[{"id":"X","title":"t"}]}',b'\xff',b' '* (a.MAX_BODY+1),b'{"events":[],"x":NaN}']:
            with self.subTest(raw=raw[:100]), self.assertRaises((ValueError,UnicodeError)):
                a.envelope(raw,'offline-import',STAMP)
        self.assertEqual(a.summarize(b'{"events":[]}')['eventCount'],0)

    def test_tampered_receipt_and_body(self):
        archive = a.envelope(BODY,'offline-import',STAMP)
        for key, value in [('sourceSha256','0'*64),('pointCount',99),('eventCount',True),('requestUrl','https://example.org'),('sourceAuthenticated',True),('coverage','complete'),('httpStatus',200),('limitReached',False),('extra','value')]:
            modified = copy.deepcopy(archive)
            modified['receipt'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): a.verify(a.encode(modified))
        modified = dict(archive,bodyBase64='%%%')
        with self.assertRaises(ValueError): a.verify(a.encode(modified))
        with self.assertRaises(ValueError): a.verify(b'{"schema":"x",'+a.encode(archive)[1:])

    def fake_response(self, status=200, headers=None, body=BODY):
        conn = MagicMock()
        r = conn.getresponse.return_value
        r.status = status
        h = {'Content-Type':'application/json','Content-Length':str(len(body))} if headers is None else headers
        r.getheader.side_effect = lambda name, default=None: h.get(name,default)
        r.read.return_value = body
        return conn

    def test_network_success_and_fixed_destination(self):
        c = self.fake_response()
        with patch.object(a.http.client,'HTTPSConnection',return_value=c) as factory:
            self.assertEqual(a.fetch_body(Q),BODY)
            self.assertEqual(factory.call_args.args,(a.HOST,))
            self.assertEqual(factory.call_args.kwargs['timeout'],10)
            self.assertEqual(c.request.call_args.args,('GET',a.query_path(Q)))
            c.getresponse.return_value.read.assert_called_once_with(a.MAX_BODY+1)
            c.close.assert_called_once()

    def test_network_failure_paths(self):
        scenarios = [self.fake_response(status=302),self.fake_response(status=429),self.fake_response(status=500),self.fake_response(headers={'Content-Type':'text/html'}),self.fake_response(headers={'Content-Type':'application/json','Content-Encoding':'gzip'}),self.fake_response(headers={'Content-Type':'application/json','Content-Length':str(a.MAX_BODY+1)}),self.fake_response(headers={'Content-Type':'application/json','Content-Length':'5'}),self.fake_response(headers={'Content-Type':'application/json','Content-Length':'bad'}),self.fake_response(headers={'Content-Type':'application/json'},body=b'x'*(a.MAX_BODY+1)),self.fake_response(headers={'Content-Type':'application/json'},body=b'')]
        for i,c in enumerate(scenarios):
            with self.subTest(case=i), patch.object(a.http.client,'HTTPSConnection',return_value=c), self.assertRaises(ValueError): a.fetch_body(Q)
            c.close.assert_called_once()

    def test_worker_deadline_and_error(self):
        with patch.object(a.subprocess,'run',side_effect=subprocess.TimeoutExpired('worker',25)) as run, self.assertRaises(subprocess.TimeoutExpired): a.bounded_fetch(Q)
        self.assertEqual(run.call_args.kwargs['timeout'],25)
        with patch.object(a.subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'network unavailable')), self.assertRaises(ValueError): a.bounded_fetch(Q)

    def test_no_overwrite_or_temp_residue(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'archive.json'
            a.save_new(p,BODY)
            with self.assertRaises(FileExistsError): a.save_new(p,b'new')
            self.assertEqual(p.read_bytes(),BODY)
            self.assertEqual(list(Path(d).iterdir()),[p])

    def test_cli_offline_export_and_rejection(self):
        def run(*args): return subprocess.run([sys.executable,str(ROOT/'scripts/eonet_archive.py'),*map(str,args)],capture_output=True,timeout=10)
        with tempfile.TemporaryDirectory() as d:
            s,p,o = (Path(d)/n for n in ('source.json','archive.json','original.json'))
            s.write_bytes(BODY)
            imported = run('import',s,p)
            self.assertEqual(imported.returncode,0,imported.stderr)
            digest = json.loads(imported.stdout)['archiveSha256']
            self.assertEqual(run('verify',p,'--expected-sha256',digest).returncode,0)
            self.assertEqual(run('export',p,o,'--expected-sha256',digest).returncode,0)
            self.assertEqual(o.read_bytes(),BODY)
            self.assertNotEqual(run('export',p,o).returncode,0)
            self.assertNotEqual(run('verify',p,'--expected-sha256','0'*64).returncode,0)
            p.write_bytes(b'{}')
            bad = Path(d)/'bad.json'
            self.assertNotEqual(run('export',p,bad).returncode,0)
            self.assertFalse(bad.exists())


if __name__ == '__main__':
    unittest.main()
