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
import verify_earth_history as history
import verify_research_answer as research


def js_answers(path, queries):
    code = "import {readFile} from 'node:fs/promises';import {researchAnswer} from './research.mjs';const bytes=await readFile(process.argv[1]);console.log(JSON.stringify(await Promise.all(JSON.parse(process.argv[2]).map(q=>researchAnswer(bytes,q)))));"
    return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', code, str(path), json.dumps(queries)], cwd=ROOT, timeout=30))


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.short = ROOT / 'data/earth-evidence-synthetic.json'
        cls.demo = Path(cls.tmp.name) / 'demo.json'
        bundle, _ = anomaly_demo.make_demo()
        cls.demo.write_bytes(bundle)
        cls.h = history.expected(bundle, archive.sha(bundle))

    def test_cross_runtime_every_query_type_and_abstention(self):
        queries = ['summary', 'explain EXAMPLE-A', 'explain EXAMPLE-B', 'explain EXAMPLE-C', 'day EXAMPLE-A 2025-01-20', 'provenance', 'limits', 'is it safe?', 'explain UNKNOWN', 'day EXAMPLE-A 2025-02-01']
        self.assertEqual(js_answers(self.demo, queries), [research.answer(self.h, q) for q in queries])
        self.assertEqual(research.answer(self.h, queries[1])['facts'][1]['value']['status'], 'ABOVE_BASELINE_MAX')
        self.assertEqual(research.answer(self.h, queries[2])['facts'][1]['value']['status'], 'NOT_ABOVE_BASELINE_MAX')

    def test_short_data_and_missing_day(self):
        queries = ['explain EXAMPLE-A', 'day EXAMPLE-A 2026-10-30', 'day EXAMPLE-C 2026-11-01']
        h = history.expected(self.short.read_bytes())
        results = js_answers(self.short, queries)
        self.assertEqual(results, [research.answer(h, q) for q in queries])
        self.assertEqual(results[0]['reason'], 'INSUFFICIENT_BASELINE')
        self.assertEqual(results[1]['facts'][1]['value']['state'], 'NO_ELIGIBLE_POINTS')
        self.assertEqual(results[2]['facts'][1]['value']['matchingPointRows'], 0)

    def test_cli_rejects_tampering_query_substitution_and_bad_anchor(self):
        q = 'explain EXAMPLE-A'
        expected = research.answer(self.h, q)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'answer.json'
            args = [sys.executable, str(ROOT / 'scripts/verify_research_answer.py'), str(self.demo), str(p), '--query', q]
            p.write_text(json.dumps(expected))
            run = lambda extra=[]: subprocess.run(args + extra, capture_output=True, timeout=30).returncode
            self.assertEqual(run(['--expected-sha256', archive.sha(self.demo.read_bytes())]), 0)
            self.assertNotEqual(run(['--expected-sha256', '0' * 64]), 0)
            for k, v in [('message', 'Safe'), ('coverage', 'complete'), ('sourceAuthenticated', True), ('query', 'summary')]:
                p.write_text(json.dumps(dict(expected, **{k: v})))
                self.assertNotEqual(run(), 0)
            altered = json.loads(json.dumps(expected)); altered['facts'][1]['pointer'] = '/facilities/1'
            p.write_text(json.dumps(altered)); self.assertNotEqual(run(), 0)
            altered = json.loads(json.dumps(expected)); altered['facts'][1]['value']['rankNumerator'] = 20
            p.write_text(json.dumps(altered)); self.assertNotEqual(run(), 0)
            p.write_text(json.dumps(research.answer(self.h, 'summary'))); self.assertNotEqual(run(), 0)
            p.write_text('{"schema":1,"schema":2}'); self.assertNotEqual(run(), 0)

    def test_invalid_query(self):
        for q in ['', None, 'summary\n', '\u00e9', 'x' * 161]:
            with self.assertRaises(ValueError):
                research.answer(self.h, q)


if __name__ == '__main__':
    unittest.main()
