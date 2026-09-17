from pathlib import Path
import json

ROOT = Path('.')

# 1) Make Vercel routing explicit. Do not rely on cleanUrls filename inference.
vercel = {
  "redirects": [
    {"source": "/", "destination": "/trainer?release=2026-09-17-r3", "permanent": False},
    {"source": "/index.html", "destination": "/atlas", "permanent": False},
    {"source": "/index", "destination": "/atlas", "permanent": False},
    {"source": "/trainer.html", "destination": "/trainer", "permanent": False},
    {"source": "/navigator.html", "destination": "/navigator", "permanent": False}
  ],
  "rewrites": [
    {"source": "/trainer", "destination": "/trainer.html"},
    {"source": "/atlas", "destination": "/index.html"},
    {"source": "/navigator", "destination": "/navigator.html"}
  ],
  "headers": [],
  "functions": {
    "api/ai.js": {"maxDuration": 30},
    "api/nasa.js": {"maxDuration": 25}
  }
}

for route in ["/", "/trainer", "/trainer.html", "/atlas", "/index", "/index.html", "/navigator", "/navigator.html", "/release.json"]:
    vercel["headers"].append({
        "source": route,
        "headers": [
            {"key": "Cache-Control", "value": "no-store, no-cache, must-revalidate, max-age=0"},
            {"key": "CDN-Cache-Control", "value": "no-store"},
            {"key": "Vercel-CDN-Cache-Control", "value": "no-store"},
            {"key": "X-Moon-Mars-Release", "value": "2026-09-17-r3"}
        ]
    })

Path('vercel.json').write_text(json.dumps(vercel, indent=2) + '\n', encoding='utf-8')

# 2) Product links must use stable public routes, never physical HTML filenames.
repls = {
    'trainer.html': [
        ('href="/index.html"', 'href="/atlas"'),
        ('href="index.html"', 'href="/atlas"'),
        ('`/index.html?gap=${encodeURIComponent(g.id)}`', '`/atlas?gap=${encodeURIComponent(g.id)}`'),
        ('"/index.html?gap="', '"/atlas?gap="'),
    ],
    'navigator.html': [
        ("$('#backLink').href='index.html?gap='+encodeURIComponent(g.id)", "$('#backLink').href='/atlas?gap='+encodeURIComponent(g.id)"),
        ("$('#backLink').href='index.html'", "$('#backLink').href='/atlas'"),
        ('href="index.html"', 'href="/atlas"'),
        ('href="/index.html"', 'href="/atlas"'),
    ],
    'index.html': [
        ('href="navigator.html?gap=', 'href="/navigator?gap='),
        ('href="navigator.html"', 'href="/navigator"'),
        ("'navigator.html?gap='", "'/navigator?gap='"),
        ('"navigator.html?gap="', '"/navigator?gap="'),
    ],
    'scripts/e2e_trainer.mjs': [
        ('/index.html?gap=', '/atlas?gap='),
        ('/index.html', '/atlas'),
    ],
    'scripts/e2e_atlas.mjs': [
        ('/index.html?gap=', '/atlas?gap='),
        ('/index.html', '/atlas'),
    ],
    'scripts/validate_competition_readiness.py': [
        ('"Atlas handoff": "/index.html?gap="', '"Atlas handoff": "/atlas?gap="'),
        ("\"round-trip back link\": \"$('#backLink').href='index.html?gap='\"", "\"round-trip back link\": \"$('#backLink').href='/atlas?gap='\""),
        ('print("Evidence engine: index.html")', 'print("Evidence engine: /atlas -> index.html")'),
    ]
}

for name, pairs in repls.items():
    p = Path(name)
    if not p.exists():
        raise SystemExit(f'missing file: {name}')
    text = p.read_text(encoding='utf-8')
    for old, new in pairs:
        text = text.replace(old, new)
    p.write_text(text, encoding='utf-8')

# 3) Validator: enforce explicit public route contract and release r3.
p = Path('scripts/validate_competition_readiness.py')
v = p.read_text(encoding='utf-8')
start = v.index('    root_redirects_to_trainer = any(')
end = v.index('    stale_story_markers =', start)
block = '''    redirects = vercel.get("redirects", [])\n    rewrites = vercel.get("rewrites", [])\n    root_redirects_to_trainer = any(\n        r.get("source") == "/" and str(r.get("destination", "")).startswith("/trainer?release=") and r.get("permanent") is False\n        for r in redirects\n    )\n    atlas_rewrite = any(r.get("source") == "/atlas" and r.get("destination") == "/index.html" for r in rewrites)\n    legacy_index_redirect = any(r.get("source") == "/index.html" and r.get("destination") == "/atlas" for r in redirects)\n    navigator_rewrite = any(r.get("source") == "/navigator" and r.get("destination") == "/navigator.html" for r in rewrites)\n    trainer_rewrite = any(r.get("source") == "/trainer" and r.get("destination") == "/trainer.html" for r in rewrites)\n    if not root_redirects_to_trainer:\n        fail("Vercel root must explicitly redirect to a versioned /trainer URL", errors)\n    else:\n        ok("Public root explicitly redirects to versioned Mission Trainer")\n    if not atlas_rewrite or not legacy_index_redirect:\n        fail("Public Atlas routing must be /atlas -> index.html with legacy /index.html redirect", errors)\n    else:\n        ok("Public Atlas route is stable at /atlas and legacy index.html redirects")\n    if not navigator_rewrite or not trainer_rewrite:\n        fail("Trainer/Navigator clean public routes must be explicit rewrites", errors)\n    else:\n        ok("Trainer and Navigator public routes are explicit")\n\n'''
v = v[:start] + block + v[end:]
v = v.replace('print("Judge-facing root: / -> /trainer")', 'print("Judge-facing routes: / -> /trainer · /atlas · /navigator")')
p.write_text(v, encoding='utf-8')

# 4) Release fingerprint.
Path('release.json').write_text(json.dumps({
    "product": "Moon→Mars Mission Trainer",
    "release": "2026-09-17-r3",
    "public_routes": {"trainer": "/trainer", "atlas": "/atlas", "navigator": "/navigator"},
    "notes": "Explicit public route contract; legacy HTML URLs redirect to stable clean routes."
}, indent=2) + '\n', encoding='utf-8')

print('Public route migration applied')
