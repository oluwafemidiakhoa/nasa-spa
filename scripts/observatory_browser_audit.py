#!/usr/bin/env python3
"""Bounded public-site browser acceptance audit; no credentials or production writes."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit, urljoin

PRODUCTION = 'https://nasa-spa.vercel.app'
CASES = ('homepage', 'navigation', 'eonet_live', 'solar_image', 'apod', 'donki',
         'kp', 'dst', 'firms', 'academy', 'map_and_evidence', 'portfolio_storage',
         'portfolio_review', 'mobile_layout', 'javascript_errors')
HEX = re.compile(r'[a-f0-9]{64}\Z')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))


def require_digest(data, digest):
    require(isinstance(digest, str) and HEX.fullmatch(digest), 'Invalid digest')
    require(hashlib.sha256(data).hexdigest() == digest, 'SHA-256 mismatch')


def receipt_bytes(receipt):
    raw = base64.b64decode(receipt['bodyBase64'], validate=True)
    require_digest(raw, receipt['sourceSha256'])
    return raw


def bundle_bytes(raw):
    require(0 < len(raw) <= 26_000_000, 'Evidence size outside allowed range')
    b = strict_json(raw)
    require(b['schema'] == 'gaia-earth-evidence-v0.5', 'Unexpected bundle schema')
    require(set(b['files']) == {'archive', 'configuration', 'report'}, 'Unexpected components')
    parts = {}
    for name, part in b['files'].items():
        data = base64.b64decode(part['base64'], validate=True)
        require(len(data) == part['bytes'], 'Incorrect component length: ' + name)
        require_digest(data, part['sha256'])
        parts[name] = strict_json(data)
    a = parts['archive']
    source = receipt_bytes({'bodyBase64': a['bodyBase64'], 'sourceSha256': a['receipt']['sourceSha256']})
    require(len(source) == a['receipt']['sourceBytes'], 'Source byte length mismatch')
    strict_json(source)
    return parts


def audit(output, executable=None):
    from playwright.sync_api import sync_playwright, expect
    started = datetime.now(timezone.utc).isoformat()
    result = {'schema': 'gaia-browser-audit-v1', 'target': PRODUCTION,
              'startedAt': started, 'mode': 'live public site plus explicitly selected synthetic UI example',
              'cases': [], 'apiResponses': []}
    # Only fixed public paths are recorded. No cookies, headers, query strings,
    # upstream response bodies, browser storage, screenshots, or tokens in the report.
    done = set()
    page_errors = []

    def record(name, state, detail):
        done.add(name)
        result['cases'].append({'case': name, 'status': state, 'detail': detail[:240]})
        print(f'{state:7} {name}: {detail[:160]}', flush=True)

    def run_case(name, fn):
        try:
            detail = fn()
            record(name, 'PASS', detail or 'Observed acceptance assertions passed')
        except Exception as e:
            # Test messages are authored below. Playwright exceptions may contain
            # arbitrary page content: retain the exception class, not raw text.
            message = str(e) if isinstance(e, AssertionError) else type(e).__name__
            record(name, 'FAIL', message)

    def finish():
        for case in CASES:
            if case not in done:
                record(case, 'BLOCKED', 'Prerequisite browser navigation or launch unavailable')
        result['finishedAt'] = datetime.now(timezone.utc).isoformat()
        result['summary'] = {s: sum(x['status'] == s for x in result['cases'])
                             for s in ('PASS', 'FAIL', 'BLOCKED')}
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        return 2 if result['summary']['BLOCKED'] else 1 if result['summary']['FAIL'] else 0

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True, **({'executable_path': executable} if executable else {}))
        except Exception as e:
            result['launchError'] = type(e).__name__
            return finish()
        result['browserVersion'] = browser.version
        context = browser.new_context(viewport={'width': 1440, 'height': 960}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(25_000)
        page.on('pageerror', lambda error: page_errors.append(type(error).__name__))

        def response(r):
            u = urlsplit(r.url)
            if u.netloc == urlsplit(PRODUCTION).netloc and u.path.startswith('/api/'):
                result['apiResponses'].append({'path': u.path, 'status': r.status})
        page.on('response', response)
        def loc(id_): return page.locator('#' + id_)
        def value(id_): return loc(id_).inner_text().strip()
        def settled(button): expect(loc(button)).to_be_enabled(timeout=30_000)
        def accepted(id_, prefix):
            require(value(id_).startswith(prefix), id_ + ' did not report an accepted source')
        def save_download(button, path):
            with page.expect_download(timeout=15_000) as d:
                loc(button).click()
            d.value.save_as(str(path))
            require(path.stat().st_size > 0, 'Empty download')
            return path.read_bytes()
        try:
            try:
                res = page.goto(PRODUCTION + '/', wait_until='domcontentloaded', timeout=30_000)
            except Exception as e:
                # An administrator block is infrastructure, not application failure.
                code = 'ERR_BLOCKED_BY_ADMINISTRATOR' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(e) else type(e).__name__
                record('homepage', 'BLOCKED', code)
                return finish()
            if not res or res.status != 200:
                record('homepage', 'FAIL', 'Homepage did not return HTTP 200')
                return finish()
            def home():
                require(urlsplit(page.url).netloc == urlsplit(PRODUCTION).netloc, 'Unexpected redirect origin')
                expect(page.locator('h1')).to_have_text('Gaia Observatory')
                require('wonders of the universe' not in page.title().lower(), 'Old browser title')
                require(not page.get_by_role('link', name='Wonders', exact=True).count(), 'Old navigation label')
                return 'Production root, heading and branding verified'
            run_case('homepage', home)

            def navigation():
                # Check anchors against their actual target and same-origin document
                # routes once, without loading another page's scripts or API panels.
                links = page.locator('a[href]').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))')
                urls = set()
                for href in links:
                    if href.startswith('#'):
                        require(page.locator('[id=' + json.dumps(href[1:]) + ']').count() == 1,
                                'Missing or duplicate internal anchor: ' + href)
                    else:
                        u = urlsplit(urljoin(page.url, href))
                        if u.scheme == 'https' and u.netloc == urlsplit(PRODUCTION).netloc:
                            urls.add(u.path)
                require(len(urls) <= 20, 'Internal link budget exceeded')
                for path in sorted(urls):
                    r = context.request.get(PRODUCTION + path, timeout=15_000)
                    require(r.status == 200, f'Internal route {path}: HTTP {r.status}')
                    require(urlsplit(r.url).netloc == urlsplit(PRODUCTION).netloc, 'Unexpected route redirect')
                # Exercise a real anchor click (not just attribute presence).
                page.locator('header nav a[href="#magnetic"]').click()
                expect(page).to_have_url(re.compile(r'#magnetic$'))
                return f'{len(urls)} internal document routes and all in-page anchors checked'
            run_case('navigation', navigation)

            def earth():
                settled('earth-refresh')
                accepted('earth-status', 'NASA response received')
                nums = [int(value(x)) for x in ('events', 'eligible', 'mapped')]
                require(0 <= nums[2] <= nums[0] <= 200 and nums[1] >= nums[2], 'Invalid Earth counters')
                require(loc('markers').locator('circle').count() == nums[2], 'Marker count mismatch')
                require(loc('register').locator('button').count() == nums[2], 'Register count mismatch')
                require(bool(re.search(r'[a-f0-9]{64}$', value('digest'))), 'Missing evidence digest')
                return f'{nums[0]} returned events, {nums[1]} eligible points, {nums[2]} plotted'
            run_case('eonet_live', earth)

            def solar():
                page.wait_for_function("() => {const x=document.getElementById('wonders-sun-image');return (x.complete&&x.naturalWidth>0)||!document.getElementById('wonders-sun-image-fallback').hidden}", timeout=30_000)
                require(loc('wonders-sun-image').evaluate('(x)=>!x.hidden&&x.complete&&x.naturalWidth>0'), 'Historical solar image did not render')
                return 'Rendered solar image has nonzero intrinsic dimensions'
            run_case('solar_image', solar)

            def apod():
                settled('apod-refresh'); accepted('apod-status', 'Record received')
                require(bool(value('apod-title')), 'APOD title missing')
                require(bool(re.search(r'\d{4}-\d{2}-\d{2}', value('apod-date'))), 'APOD date missing')
                if not loc('apod-image').is_hidden():
                    page.wait_for_function("() => document.getElementById('apod-image').complete", timeout=20_000)
                    require(loc('apod-image').evaluate('(x)=>x.naturalWidth>0'), 'APOD image failed to load')
                require('image failed to load' not in value('apod-status'), 'APOD image delivery failed')
                return 'APOD record and eligible image checked'
            run_case('apod', apod)

            def donki():
                settled('donki-refresh'); accepted('donki-status', 'Collection received')
                require(bool(re.match(r'\d+ returned', value('donki-count'))), 'DONKI count missing')
                require(loc('chart').locator('*').count() > 0, 'DONKI chart or empty-state missing')
                return 'DONKI collection and chart/empty-state verified'
            run_case('donki', donki)

            for series in ('kp', 'dst'):
                def magnetic(series=series):
                    settled('magnetic-refresh')
                    require('source hash matched' in value(series + '-status'), 'NOAA ' + series + ' source not accepted')
                    require(loc(series + '-chart').locator('circle').count() > 0, 'NOAA plot has no valid samples')
                    return 'Accepted source and plotted valid samples'
                run_case(series, magnetic)

            def thermal():
                settled('thermal-refresh')
                require('Source SHA-256 matched' in value('thermal-status'), 'FIRMS source not accepted')
                require(value('thermal-count').isdigit(), 'FIRMS count missing')
                require(int(value('thermal-high')) <= int(value('thermal-count')), 'Invalid FIRMS counts')
                expect(loc('thermal-export')).to_be_enabled()
                with tempfile.TemporaryDirectory() as tmp:
                    receipt_bytes(strict_json(save_download('thermal-export', Path(tmp) / 'firms.json')))
                return 'Thermal observation receipt digest independently matched'
            run_case('firms', thermal)

            def academy():
                loc('orbit-planet').select_option('Mars')
                loc('orbit-days').fill('365')
                expect(loc('orbit-time')).to_have_text('365 simulated Earth days')
                expect(loc('orbit-detail')).to_contain_text('Mars takes approximately 687')
                loc('orbit-reset').click()
                expect(loc('orbit-time')).to_have_text('0 simulated Earth days')
                expect(loc('orbit-planet')).to_have_value('Earth')
                return 'Planet selection, time slider and reset exercised'
            run_case('academy', academy)

            def map_evidence():
                settled('demo'); loc('demo').click(); settled('demo')
                accepted('earth-status', 'SYNTHETIC')
                require(loc('markers').locator('circle').count() > 0, 'Synthetic markers missing')
                loc('register').locator('button').first.click()
                expect(loc('history-panel')).to_be_visible()
                require(loc('history-rows').locator('tr').count() > 0, 'Observation history empty')
                loc('zoom').click(); require(loc('map').get_attribute('viewBox') != '0 0 720 360', 'Zoom did not change viewBox')
                loc('reset').click(); expect(loc('map')).to_have_attribute('viewBox', '0 0 720 360')
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / 'evidence.json'
                    raw = save_download('download', path)
                    b = bundle_bytes(raw)
                    require(b['configuration']['snapshotKind'] == 'synthetic-demo', 'Synthetic evidence mislabeled')
                    loc('bundle').set_input_files(str(path)); loc('import').click(); settled('import')
                    accepted('earth-status', 'SYNTHETIC')
                    path.write_bytes(b'{"invalid":true}')
                    loc('bundle').set_input_files(str(path)); loc('import').click(); settled('import')
                    accepted('earth-status', 'No observations accepted')
                    expect(loc('download')).to_be_disabled()
                    require(loc('markers').locator('circle').count() == 0, 'Stale markers retained after invalid import')
                return 'Explicit synthetic map selection, history, zoom, export, replay and invalid import tested'
            run_case('map_and_evidence', map_evidence)

            dashboard_mobile = False
            try:
                page.set_viewport_size({'width': 390, 'height': 844})
                dashboard_mobile = page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
            finally:
                page.set_viewport_size({'width': 1440, 'height': 960})

            def portfolio_storage():
                r = page.goto(PRODUCTION + '/portfolio.html', wait_until='domcontentloaded')
                require(r and r.status == 200, 'Portfolio route failed')
                expect(loc('status')).to_contain_text('Enter locations')
                loc('example').click(); text = loc('locations').input_value()
                require('LOS-ANGELES' in text and 'PASADENA' in text, 'Public example missing')
                loc('save').click(); expect(loc('status')).to_contain_text('Portfolio saved')
                page.reload(wait_until='domcontentloaded')
                expect(loc('status')).to_contain_text('Saved portfolio restored')
                require(set(loc('locations').input_value().splitlines()) == set(text.splitlines()), 'Restored locations differ')
                return 'Public examples saved and restored in isolated browser storage'
            run_case('portfolio_storage', portfolio_storage)

            def portfolio_review():
                require(page.url.endswith('/portfolio.html'), 'Portfolio prerequisite unavailable')
                loc('example').click(); loc('run').click(); settled('run')
                expect(loc('results')).to_be_visible(timeout=10_000)
                require(loc('rows').locator('tr').count() == 3, 'Expected three public example rows')
                with tempfile.TemporaryDirectory() as tmp:
                    p = Path(tmp); old = p / 'earlier.json'; new = p / 'recent.json'
                    a = save_download('download-previous', old); b = save_download('download-current', new)
                    bundle_bytes(a); bundle_bytes(b)
                    report = strict_json(save_download('download-report', p / 'review.json'))
                    require(report['schema'] == 'gaia-portfolio-review-v1', 'Unexpected review schema')
                    require_digest(a, report['previous']['bundleSha256']); require_digest(b, report['current']['bundleSha256'])
                    require(len(report['rows']) == 3, 'Unexpected report row count')
                    if loc('reopen-panel').count():
                        loc('reopen-panel').locator('summary').click()
                    loc('previous-file').set_input_files(str(old)); loc('current-file').set_input_files(str(new)); loc('reopen').click(); settled('reopen')
                    expect(loc('results')).to_be_visible()
                    loc('previous-file').set_input_files(str(new)); loc('current-file').set_input_files(str(old)); loc('reopen').click(); settled('reopen')
                    expect(loc('status')).to_contain_text('Review unavailable')
                    expect(loc('results')).to_be_hidden()
                loc('forget').click(); expect(loc('status')).to_contain_text('Saved portfolio removed')
                require(not loc('locations').input_value(), 'Forgotten locations still present')
                return 'Two-window live review, evidence digest checks, replay, reversed-bundle rejection and local cleanup'
            run_case('portfolio_review', portfolio_review)

            def mobile():
                # Resize the already loaded portfolio; no extra live API retrieval.
                page.set_viewport_size({'width': 390, 'height': 844})
                require(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), 'Portfolio has horizontal viewport overflow')
                expect(loc('run')).to_be_visible()
                require(dashboard_mobile, 'Dashboard has horizontal viewport overflow')
                return 'Dashboard and portfolio fit a 390px viewport; not a full visual review'
            run_case('mobile_layout', mobile)
            run_case('javascript_errors', lambda: require(not page_errors, f'{len(page_errors)} uncaught page errors'))
        finally:
            context.close(); browser.close()
    return finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('gaia-browser-audit.json'))
    parser.add_argument('--browser-executable', help='Optional installed Chromium executable')
    args = parser.parse_args()
    return audit(args.output, args.browser_executable)


if __name__ == '__main__':
    sys.exit(main())
