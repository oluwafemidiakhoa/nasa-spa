"""Cross-platform HTTP module delivery and diagnostic tests."""
import functools
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalog_e2e', ROOT/'scripts/observatory_catalog_e2e.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class ServerTests(unittest.TestCase):
    def run_server(self, root, handler, check):
        with ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(handler, directory=str(root))) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                check(f'http://127.0.0.1:{server.server_port}', server.server_port)
            finally:
                server.shutdown()
                thread.join()

    def test_all_packaged_modules_have_javascript_mime_even_if_os_is_wrong(self):
        # Simulate a broken platform MIME database, without editing it.
        with patch('mimetypes.guess_type', return_value=('application/octet-stream', None)):
            def check(base, port):
                rows = audit.verify_module_delivery(base)
                self.assertEqual(len(rows), len(list(ROOT.glob('*.mjs'))))
                self.assertTrue(all(row['mime']=='text/javascript' and row['status']==200 for row in rows))
                conn = HTTPConnection('127.0.0.1', port, timeout=5)
                try:
                    conn.request('GET','/live-dashboard.mjs')
                    r = conn.getresponse()
                    self.assertEqual(r.status, 200)
                    self.assertEqual(r.getheader('Content-Type'),'text/javascript')
                    self.assertEqual(r.read(), (ROOT/'live-dashboard.mjs').read_bytes())
                finally:
                    conn.close()
            self.run_server(ROOT, audit.Quiet, check)

    def test_bad_mime_is_detected_before_browser_startup(self):
        class BadHandler(audit.Quiet):
            extensions_map = {**audit.Quiet.extensions_map, '.mjs':'application/octet-stream'}
        def check(base, _port):
            with self.assertRaisesRegex(AssertionError,'MIME.*application/octet-stream'):
                audit.verify_module_delivery(base)
        self.run_server(ROOT, BadHandler, check)

    def test_missing_required_module_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'workspace.mjs').write_text('export const test = 1;', encoding='utf-8')
            with self.assertRaisesRegex(AssertionError,'Missing required module: live-dashboard.mjs'):
                audit.verify_module_delivery('http://127.0.0.1:1', root)

    def test_diagnostics_remove_url_query_and_keep_local_path(self):
        self.assertEqual(audit.local_path('http://127.0.0.1:1234/a.mjs?secret=1','http://127.0.0.1:1234'),'/a.mjs')
        self.assertIsNone(audit.local_path('https://example.com/image','http://127.0.0.1:1234'))
        self.assertNotIn('secret=1',audit.bounded_message('Error from https://example.com/x?secret=1'))
        self.assertLessEqual(len(audit.bounded_message('x'*2000)),1200)

if __name__ == '__main__':
    unittest.main()
