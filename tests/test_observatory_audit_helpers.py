import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit', ROOT/'scripts/observatory_browser_audit.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class AuditHelpers(unittest.TestCase):
    def test_source_digest(self):
        data=b'{"events":[]}'
        receipt={'bodyBase64':base64.b64encode(data).decode(), 'sourceSha256':hashlib.sha256(data).hexdigest()}
        self.assertEqual(audit.receipt_bytes(receipt), data)
        receipt['sourceSha256']='0'*64
        with self.assertRaises(AssertionError): audit.receipt_bytes(receipt)

    def test_strict_json(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}']:
            with self.assertRaises((AssertionError,ValueError)): audit.strict_json(raw)

    def test_actual_synthetic_bundle(self):
        raw=(ROOT/'data/earth-evidence-synthetic.json').read_bytes()
        self.assertEqual(audit.bundle_bytes(raw)['configuration']['snapshotKind'],'synthetic-demo')

    def test_tampered_component(self):
        raw=(ROOT/'data/earth-evidence-synthetic.json').read_bytes()
        b=json.loads(raw)
        b['files']['archive']['sha256']='0'*64
        with self.assertRaises(AssertionError): audit.bundle_bytes(json.dumps(b).encode())

if __name__=='__main__': unittest.main()
