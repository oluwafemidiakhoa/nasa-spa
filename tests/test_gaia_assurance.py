import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import gaia_assurance as assurance


class AssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.fixtures = Path(cls.tmp.name)
        subprocess.run(['node', str(ROOT/'tests/gaia-independent-fixtures.mjs'), str(cls.fixtures)],
                       check=True, capture_output=True, timeout=60)
        cls.raw = (cls.fixtures/'demo.json').read_bytes()
        cls.dossier = assurance.build(cls.raw)

    def test_frozen_cross_runtime_matrix(self):
        manifest = json.loads((self.fixtures/'manifest.json').read_text())
        counts = {'PASS': 0, 'FAIL': 0, 'INCOMPLETE': 0}
        for case in manifest:
            with self.subTest(case=case['id']):
                raw = (self.fixtures/(case['id']+'.json')).read_bytes()
                dossier = assurance.build(raw)
                report = assurance.verify_dossier(dossier)
                options = dict(zip(case['options'][::2], case['options'][1::2]))
                result = assurance.session(report, dossier, packet_anchor=options.get('--packet-sha256',''),
                                           source_anchor=options.get('--source-sha256',''))
                status = report['controls'][0]['status']
                expected = 'PASS' if options or case['expected'] == 0 else 'FAIL' if case['expected'] == 1 else 'INCOMPLETE'
                self.assertEqual(status, expected)
                counts[status] += 1
                self.assertFalse(report['certified'])
                self.assertFalse(report['executionAuthorized'])
                self.assertTrue(all(c['status']=='INCOMPLETE' for c in report['controls'][2:]))
                if case['expected']==1:
                    self.assertEqual(result['conclusion'], 'NO-GO')
                if case['expected']==2:
                    self.assertEqual(result['conclusion'], 'INCOMPLETE')
        self.assertEqual(counts, {'PASS':74, 'FAIL':13, 'INCOMPLETE':2})
        print(json.dumps({'dossiers':len(manifest),'replay':counts}))

    def test_claim_verdict_distinct_from_replay(self):
        for name, claim_status, conclusion in [('robust','PASS','INCOMPLETE'),('far','FAIL','NO-GO'),
                                               ('empty','INCOMPLETE','INCOMPLETE'),('demo','INCOMPLETE','INCOMPLETE')]:
            report = assurance.assess((self.fixtures/(name+'.json')).read_bytes())
            self.assertEqual(report['controls'][0]['status'], 'PASS')
            self.assertEqual(report['controls'][1]['status'], claim_status)
            self.assertEqual(report['conclusion'], conclusion)

    def test_edit_report_or_binding_rejected(self):
        edits = [lambda d:d['report'].update(conclusion='EVIDENCE-SUFFICIENT'),
                 lambda d:d['report'].update(certified=True),
                 lambda d:d['report']['controls'][2].update(status='PASS'),
                 lambda d:d['report']['implementation'].update(gaia_assurance='0'*64),
                 lambda d:d['report']['claim'].update(nominalCount=99),
                 lambda d:d['proof'].update(sha256='0'*64),
                 lambda d:d.update(externalApproval=True)]
        for edit in edits:
            d = json.loads(self.dossier); edit(d)
            with self.assertRaises(ValueError): assurance.verify_dossier(assurance.encode(d))
        with self.assertRaises(ValueError): assurance.verify_dossier(b'{"schema":1,"schema":2}')

    def test_external_anchors_are_session_only(self):
        report = assurance.verify_dossier(self.dossier)
        good = assurance.session(report,self.dossier,packet_anchor=report['packetSha256'],
                                 source_anchor=report['sourceSha256'],dossier_anchor=assurance.proof.sha(self.dossier))
        self.assertEqual(set(good['anchors'].values()),{'MATCHED'})
        self.assertEqual(good['conclusion'],'INCOMPLETE')
        self.assertEqual(set(assurance.session(report,self.dossier)['anchors'].values()),{'NOT_SUPPLIED'})
        for name in ['packet_anchor','source_anchor','dossier_anchor']:
            bad=assurance.session(report,self.dossier,**{name:'0'*64})
            self.assertEqual(bad['conclusion'],'NO-GO')
        with self.assertRaises(ValueError): assurance.session(report,self.dossier,packet_anchor='not-a-digest')
        negative=assurance.build(b'not JSON')
        r=assurance.session(assurance.verify_dossier(negative),negative,source_anchor='0'*64)
        self.assertEqual(r['anchors']['source'],'NOT_CHECKABLE')
        self.assertEqual(r['conclusion'],'NO-GO')

    def test_cli_exclusive_output_and_negative_evidence(self):
        p=self.fixtures/'dossier.json'
        def run(*args):
            r=subprocess.run([sys.executable,str(ROOT/'scripts/gaia_assurance.py'),*map(str,args)],
                             capture_output=True,text=True,timeout=15)
            return r.returncode,json.loads(r.stdout)
        code,r=run('build',self.fixtures/'demo.json','--output',p)
        self.assertEqual(code,2);before=p.read_bytes()
        self.assertEqual(run('build',self.fixtures/'far.json','--output',p)[0],1)
        self.assertEqual(p.read_bytes(),before)
        self.assertEqual(run('verify',p,'--dossier-sha256',r['dossierSha256'])[0],2)
        self.assertEqual(run('verify',p,'--dossier-sha256','0'*64)[0],1)
        neg=self.fixtures/'negative-dossier.json'
        self.assertEqual(run('build',self.fixtures/'malformed.json','--output',neg)[0],1)
        self.assertTrue(neg.is_file())
        self.assertEqual(run('verify',neg)[0],1)
        self.assertEqual(run('verify',self.fixtures)[0],1)


if __name__=='__main__': unittest.main()
