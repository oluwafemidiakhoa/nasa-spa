import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'verify_gaia_proof.py'

class CrossRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.directory=Path(cls.tmp.name)
        p=subprocess.run(['node',str(ROOT/'tests'/'gaia-independent-fixtures.mjs'),str(cls.directory)],capture_output=True,text=True,check=True,timeout=60)
        cls.manifest=json.loads((cls.directory/'manifest.json').read_text())
        spec=importlib.util.spec_from_file_location('proof_verifier',SCRIPT);cls.verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.verifier)
        print(p.stdout.strip())

    def test_frozen_fixture_outcomes(self):
        actual={0:0,1:0,2:0}
        for case in self.manifest:
            with self.subTest(case=case['id']):
                options=dict(zip(case['options'][::2],case['options'][1::2]))
                try:
                    r=self.verifier.verify((self.directory/(case['id']+'.json')).read_bytes(),options.get('--source-sha256',''),options.get('--packet-sha256',''));code=0
                except self.verifier.Inconclusive as e:
                    r=dict(status='INCONCLUSIVE_NUMERICAL_BOUNDARY',reason=str(e));code=2
                except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError,OSError) as e:
                    r=dict(status='REJECTED',reason=str(e));code=1
                self.assertEqual(code,case['expected'],str(r))
                self.assertEqual(r['status'],{0:'CROSS_RUNTIME_MATCH',1:'REJECTED',2:'INCONCLUSIVE_NUMERICAL_BOUNDARY'}[case['expected']]);actual[code]+=1
                if code==0:self.assertIs(r['sourceAuthenticated'],False);self.assertIs(r['scientificValidityEstablished'],False)
                if case['id']=='rehashed-batch':self.assertIn('Batch membership differs',r['reason'])
                if case['id']=='anchored':self.assertTrue(r['sourceAnchorMatched'] and r['packetAnchorMatched'])
                if case['id']=='robust':self.assertEqual(r['claim']['jointCountBounds'],[2,3]);self.assertEqual(r['claim']['verdict'],'CONDITIONALLY_SUPPORTED_AFTER_PERTURBATIONS')
                if case['id']=='empty':self.assertIsNone(r['claim']['nominalCount'])
        print(json.dumps({'crossRuntimeCases':len(self.manifest),'matches':actual[0],'rejected':actual[1],'inconclusive':actual[2]}))

    def test_cli_contract(self):
        for case in self.manifest:
            if case['id'] not in {'demo','anchored','boundary','malformed','rehashed-batch','alternate-anchored'}:continue
            with self.subTest(case=case['id']):
                p=subprocess.run([sys.executable,str(SCRIPT),str(self.directory/(case['id']+'.json')),*case['options']],capture_output=True,text=True,timeout=15)
                self.assertEqual(p.returncode,case['expected'],p.stdout+' '+p.stderr)
                r=json.loads(p.stdout);self.assertIs(r['sourceAuthenticated'],False);self.assertIs(r['scientificValidityEstablished'],False)

    def test_nonregular_input_rejected(self):
        files=[self.directory]
        if hasattr(os,'mkfifo'):
            fifo=self.directory/'not-a-file';os.mkfifo(fifo);files.append(fifo)
        for path in files:
            p=subprocess.run([sys.executable,str(SCRIPT),str(path)],capture_output=True,text=True,timeout=5)
            self.assertEqual(p.returncode,1);self.assertEqual(json.loads(p.stdout)['status'],'REJECTED')

    def test_no_node_required_to_verify_existing_packet(self):
        spec=importlib.util.spec_from_file_location('proof_verifier',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        r=m.verify((self.directory/'demo.json').read_bytes());self.assertEqual(r['claim']['jointCountBounds'],[0,5]);self.assertFalse(r['sourceAuthenticated'])
        with self.assertRaises(ValueError):m.verify(b'{"schema":1,"schema":1}')

if __name__=='__main__':unittest.main()
