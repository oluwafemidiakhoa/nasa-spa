"""Controlled loopback browser acceptance; no NASA requests or live data claims."""
import argparse
import base64
from datetime import datetime, timezone
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection
import re
import json
from pathlib import Path
import tempfile
import threading
from urllib.parse import urlsplit, parse_qs, urlencode
from playwright.sync_api import sync_playwright, expect, Error as PlaywrightError

ROOT = Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    # Do not let OS/Windows registry MIME associations determine module loading.
    # Chromium requires a JavaScript MIME type for every ES module dependency.
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript',
                      '.css': 'text/css', '.svg': 'image/svg+xml',
                      '.html': 'text/html', '.json': 'application/json'}

    def log_message(self, *_):
        pass


def verify_module_delivery(base, root=ROOT):
    """Check the actual HTTP headers, not the operating system MIME table."""
    origin = urlsplit(base)
    assert origin.scheme == 'http' and origin.hostname == '127.0.0.1'
    files = sorted(root.glob('*.mjs'))
    if not files:
        raise AssertionError('No JavaScript modules found; extract the complete candidate.')
    for name in ('live-dashboard.mjs', 'workspace.mjs', 'facility.mjs', 'portfolio-page.mjs'):
        if not (root / name).is_file():
            raise AssertionError('Missing required module: ' + name)
    checked = []
    for path in files:
        conn = HTTPConnection(origin.hostname, origin.port, timeout=5)
        try:
            conn.request('HEAD', '/' + path.name)
            resp = conn.getresponse()
            mime = (resp.getheader('Content-Type') or '').split(';')[0].strip().lower()
            if resp.status != 200 or mime != 'text/javascript':
                raise AssertionError(f'Module delivery failed: {path.name}: HTTP {resp.status}, MIME {mime!r}')
            checked.append({'path': path.name, 'status': resp.status, 'mime': mime})
        finally:
            conn.close()
    return checked


def local_path(url, base):
    u = urlsplit(url)
    return u.path if u.scheme + '://' + u.netloc == base else None


def bounded_message(value):
    # Only controlled test data should reach this audit. Remove URL query strings
    # anyway, and bound diagnostic text and the number of retained events.
    return re.sub(r'(https?://[^\s\"<>?]+)\?[^\s\"<>]*', r'\1?[query omitted]', str(value))[:1200]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-executable")
    parser.add_argument("--screenshots",type=Path,default=Path("qa-screenshots"))
    args=parser.parse_args()
    args.screenshots.mkdir(parents=True,exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    diagnostics = {'schema':'gaia-browser-diagnostics-v1', 'mode':'controlled-loopback-fixtures',
                   'status':'INCOMPLETE', 'modules':[], 'events':[]}
    diagnostic_path = args.screenshots / 'browser-diagnostics.json'
    def record(kind, **details):
        if len(diagnostics['events']) < 250:
            diagnostics['events'].append({'kind':kind, **details})
    try:
        diagnostics['modules'] = verify_module_delivery(base)
        print(f"PASS HTTP module preflight: {len(diagnostics['modules'])} JavaScript modules served as text/javascript", flush=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, **({"executable_path":args.browser_executable} if args.browser_executable else {}))
            try:
                context = browser.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
                page = context.new_page()
                errors, requests = [], []
                def page_error(error):
                    message = bounded_message(error)
                    errors.append(message)
                    record('pageerror', message=message)
                    print('BROWSER ERROR:', message, flush=True)
                def console_message(message):
                    if message.type not in ('error', 'warning'):
                        return
                    location = message.location or {}
                    path = local_path(location.get('url', ''), base)
                    # External images are deliberately denied in this fixture run.
                    # Keep console warnings, but do not label a blocked external image
                    # as an uncaught application error.
                    record('console', level=message.type, path=path,
                           line=location.get('lineNumber'), message=bounded_message(message.text))
                    if path and path.endswith(('.mjs', '.js', '.html')):
                        print('CONSOLE:', path, bounded_message(message.text), flush=True)
                def response_received(response):
                    path = local_path(response.url, base)
                    if path and (path.endswith(('.mjs', '.js', '.css')) or path.startswith('/api/')):
                        mime = response.headers.get('content-type', '').split(';')[0]
                        record('response', path=path, status=response.status, mime=mime)
                def request_failed(request):
                    path = local_path(request.url, base)
                    if path:
                        record('requestfailed', path=path, reason=bounded_message(request.failure))
                        print('REQUEST FAILED:', path, bounded_message(request.failure), flush=True)
                page.on('pageerror', page_error)
                page.on('console', console_message)
                page.on('response', response_received)
                page.on('requestfailed', request_failed)

                def route(r):
                    u = urlsplit(r.request.url)
                    if u.scheme + '://' + u.netloc != base:
                        return r.abort()
                    if u.path == '/api/nasa':
                        q=parse_qs(u.query)
                        payload={'title':'Controlled test astronomy record','date':'2026-11-26','explanation':'Fixture for browser acceptance, not NASA imagery.'} if q.get('type')==['apod'] else [{'startTime':'2026-11-26T12:00Z'}]
                        return r.fulfill(status=200,content_type='application/json',body=json.dumps(payload))
                    if u.path.startswith('/api/') and u.path != '/api/gaia-eonet':
                        return r.fulfill(status=503,content_type='application/json',body='{"code":"CONTROLLED_UNAVAILABLE"}')
                    if u.path != '/api/gaia-eonet':
                        return r.continue_()
                    q = parse_qs(u.query)
                    assert set(q) == {'start', 'end', 'category'}
                    assert all(len(v) == 1 for v in q.values())
                    start, end, category = (q[k][0] for k in ('start', 'end', 'category'))
                    requests.append((start, end, category))
                    raw = json.dumps({'events': [{'id': 'fixture-' + start, 'title': 'Controlled test observation', 'geometry': [{'type': 'Point', 'date': start + 'T12:00:00Z', 'coordinates': [-95, 30]}]}]}).encode()
                    query = urlencode({'status': 'all', 'start': start, 'end': end, 'category': category, 'limit': '200'})
                    receipt = {'requestUrl': 'https://eonet.gsfc.nasa.gov/api/v3/events?' + query, 'capturedAt': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'), 'sourceSha256': hashlib.sha256(raw).hexdigest(), 'bodyBase64': base64.b64encode(raw).decode()}
                    r.fulfill(status=200, content_type='application/json', body=json.dumps(receipt))

                page.route('**/*', route)
                def loc(id_): return page.locator('#' + id_)
                # Test the actual main page first. Network is restricted to loopback and controlled fixtures.
                response=page.goto(base+'/live_dashboard.html',wait_until='domcontentloaded')
                assert response and response.status==200
                # Mark the rendered test as controlled before any assertions or screenshots.
                page.evaluate("""() => {const b=document.createElement('p');b.textContent='Controlled QA fixture — not live observations';b.setAttribute('role','note');b.style.cssText='margin:0;padding:8px 12px;background:#ffd48a;color:#132f40;font-weight:700;text-align:center';document.body.prepend(b);}""")
                expect(loc('earth-status')).to_contain_text('NASA response received',timeout=15000)
                expect(loc('markers').locator('circle')).to_have_count(1)
                expect(loc('thermal-status')).to_contain_text('No thermal observations accepted: HTTP 503',timeout=15000)
                expect(loc('thermal-export')).to_be_disabled()
                expect(loc('wonders-sun-image-fallback')).to_be_visible(timeout=15000)
                assert page.evaluate("document.querySelector('#earth').getBoundingClientRect().top < document.querySelector('#overview').getBoundingClientRect().top")
                page.screenshot(path=str(args.screenshots/'01-home-desktop-controlled.png'),full_page=False)
                loc('register').locator('button').first.click()
                expect(loc('history-panel')).to_be_visible()
                loc('zoom').click()
                assert loc('map').get_attribute('viewBox')!='0 0 720 360'
                loc('reset').click()
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
                page.screenshot(path=str(args.screenshots/'02-home-mobile-controlled.png'),full_page=True)
                page.set_viewport_size({'width':1280,'height':900})
                print('PASS controlled homepage hierarchy, map, explicit source failures and mobile width',flush=True)
                requests.clear()
                response = page.goto(base + '/portfolio.html', wait_until='domcontentloaded')
                assert response.status == 200
                expect(loc('status')).to_contain_text('Enter locations')
                expect(loc('catalog-status')).to_contain_text('No reviews retained')
                print('PASS controlled page startup', flush=True)
                page.screenshot(path=str(args.screenshots/'03-locations-empty.png'),full_page=False)
                loc('location-id').fill('A');loc('location-lon').fill('-95');loc('location-lat').fill('30');loc('location-add').click()
                expect(loc('location-points').locator('circle')).to_have_count(1)
                loc('location-id').fill('B');loc('location-lon').fill('0');loc('location-lat').fill('0');loc('location-add').click()
                expect(loc('location-points').locator('circle')).to_have_count(2)
                loc('location-id').fill('B');loc('location-lon').fill('1');loc('location-lat').fill('1');loc('location-add').click()
                expect(loc('location-editor-status')).to_contain_text('already present')
                expect(loc('location-points').locator('circle')).to_have_count(2)
                loc('save').click();expect(loc('status')).to_contain_text('Portfolio saved')
                page.reload(wait_until='domcontentloaded');expect(loc('status')).to_contain_text('Saved portfolio restored')
                expect(loc('location-points').locator('circle')).to_have_count(2)
                print('PASS coordinate entry, validation, map and local restoration',flush=True)
                loc('run').click()
                expect(loc('results')).to_be_visible(timeout=15000)
                assert len(requests) == 2
                expect(loc('catalog-stats')).to_contain_text('0 / 20')
                loc('catalog-keep').click()
                expect(loc('catalog-status')).to_contain_text('Review saved on this browser')
                expect(loc('catalog-stats')).to_contain_text('1 / 20')
                page.reload(wait_until='domcontentloaded')
                expect(loc('catalog-status')).to_contain_text('Saved reviews restored and replayed',timeout=15000)
                expect(loc('catalog-stats')).to_contain_text('1 / 20')
                assert len(requests)==2, 'Restoration must not request new source data'
                loc('catalog-brief').click()
                expect(loc('catalog-brief-output')).to_contain_text('Locations reviewed: 2')
                expect(loc('catalog-brief-output')).to_contain_text('Report SHA-256:')
                with tempfile.TemporaryDirectory() as tmp:
                    with page.expect_download() as d:
                        loc('catalog-brief-download').click()
                    path=Path(tmp)/'brief.txt'
                    d.value.save_as(str(path))
                    assert path.read_text(encoding='utf-8')==loc('catalog-brief-output').text_content()
                print('PASS actual browser history reload and briefing download',flush=True)
                loc('catalog-search').click()
                expect(loc('catalog-results')).to_contain_text('Earlier matches: 1')
                expect(loc('catalog-results')).to_contain_text('Recent matches: 1')
                page.screenshot(path=str(args.screenshots/'04-review-desktop-controlled.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
                page.screenshot(path=str(args.screenshots/'05-review-mobile-controlled.png'),full_page=True)
                page.set_viewport_size({'width':1280,'height':900})
                print('PASS controlled review retention and retrieval', flush=True)
                loc('catalog-results').locator('summary').click()
                provenance = loc('catalog-results').locator('details p').inner_text()
                digest = provenance.split('Report SHA-256: ')[1].split(' | ')[0]
                with tempfile.TemporaryDirectory() as tmp:
                    with page.expect_download() as d:
                        loc('catalog-report').click()
                    path = Path(tmp) / 'report.json'
                    d.value.save_as(str(path))
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
                print('PASS exact report download hash', flush=True)
                loc('catalog-location').select_option('B')
                expect(loc('catalog-results')).to_be_empty()
                loc('catalog-search').click()
                expect(loc('catalog-results')).to_contain_text('Recent matches: 0')
                loc('catalog-forget').click()
                expect(loc('catalog-stats')).to_contain_text('0 / 20')
                expect(loc('catalog-report')).to_be_disabled()
                expect(loc('catalog-brief-download')).to_be_disabled()
                page.reload(wait_until='domcontentloaded')
                expect(loc('catalog-status')).to_contain_text('No reviews retained',timeout=15000)
                expect(loc('catalog-stats')).to_contain_text('0 / 20')
                assert len(requests) == 2
                loc('run').click()
                expect(loc('results')).to_be_visible(timeout=15000)
                assert len(requests)==4
                page.get_by_role('button',name='Remove B',exact=True).click()
                expect(loc('location-points').locator('circle')).to_have_count(1)
                expect(loc('results')).to_be_hidden()
                print('PASS location filter, persisted removal, stale result invalidation and no background requests', flush=True)
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
                assert not errors, 'Uncaught browser errors: ' + str(len(errors))
                print('PASS 390px viewport and no uncaught page errors', flush=True)
                diagnostics['status'] = 'PASS'
            except Exception as exc:
                diagnostics['status'] = 'BLOCKED' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc) else 'FAIL'
                diagnostics['failure'] = bounded_message(exc)
                if 'page' in locals() and diagnostics['status'] != 'BLOCKED':
                    try:
                        diagnostics['page'] = page.evaluate("""() => ({readyState:document.readyState, secureContext:window.isSecureContext, cryptoSubtle:!!globalThis.crypto?.subtle, earthStatus:document.getElementById('earth-status')?.textContent??null, reviewStatus:document.getElementById('status')?.textContent??null, scripts:Array.from(document.querySelectorAll('script[src]'),s=>({src:s.getAttribute('src'),type:s.type}))})""")
                        page.screenshot(path=str(args.screenshots/'failure-controlled.png'), full_page=False, timeout=5000)
                        print('Saved failure screenshot: failure-controlled.png', flush=True)
                    except Exception as capture_error:
                        record('capture_error', message=bounded_message(capture_error))
                    print('DIAGNOSTIC: '+json.dumps(diagnostics.get('page', {}), ensure_ascii=True), flush=True)
                    print('Uncaught browser errors:', len(errors), '| Controlled EONET calls:', len(requests), flush=True)
                raise
            finally:
                browser.close()
    except PlaywrightError as exc:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc):
            diagnostics['status'] = 'BLOCKED'
            print('BLOCKED: Chromium navigation prohibited by administrator policy; no browser acceptance or new screenshots established.',flush=True)
            return 2
        if diagnostics['status'] == 'INCOMPLETE':
            diagnostics['status'] = 'FAIL'
            diagnostics['failure'] = bounded_message(exc)
        raise
    except Exception as exc:
        if diagnostics['status'] == 'INCOMPLETE':
            diagnostics['status'] = 'FAIL'
            diagnostics['failure'] = bounded_message(exc)
        raise
    finally:
        diagnostic_path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
        print('Diagnostic report:', diagnostic_path, flush=True)
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    raise SystemExit(main() or 0)
