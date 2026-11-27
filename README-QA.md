> Historical RC11 baseline. Use README-HISTORY.md for the latest local candidate and test instructions.

# Gaia Observatory QA and knowledge catalog (local candidate)

This package is based on production RC10, commit `8abf4bcd7f4207088d86e80dc7ae24c7457d6a05`. It does not change the production website. All fixture data is explicitly controlled/synthetic and no secrets are needed. The RC11 candidate integrates the catalog with My Locations and repairs a workspace module startup collision. Production is unchanged until release approval.

## Run the real production browser audit on Windows

From an extracted package directory in PowerShell:

```powershell
python -m pip install playwright==1.57.0
python -m playwright install chromium
python scripts/observatory_browser_audit.py --output gaia-browser-audit.json
$LASTEXITCODE
```

The audit visits the public production site using an isolated browser context. It makes bounded public requests, checks desktop/mobile interactions, uses only public city-center examples and the explicit synthetic map, and downloads evidence to temporary storage for digest checks. No credentials, private coordinates, screenshots or raw API bodies are included in the resulting report. Exit 0 means all assertions passed, 1 means one or more failed without a blocked prerequisite, and 2 means at least one case was blocked. A dependency installation failure is not an application result. The browser audit has not completed in the assistant environment because Chromium navigation was blocked by policy.

## Run local catalog and helper tests

Use Node.js 22 and Python 3.11 or later; no npm dependencies are required for these tests.

```powershell
node --test tests/knowledge-catalog.test.mjs
python -m unittest discover -s tests -p test_observatory_audit_helpers.py -v
```

See `docs/knowledge-architecture.md` for the ingestion/retrieval contract, security boundaries, limitations and future implementation. The full baseline + catalog regression log and browser audit report are in `evidence/`. Tests establish software behavior on controlled inputs, not scientific validity or verified public data availability. No production promotion is performed by these commands.

## RC11 acceptance and retained investigations

Open `portfolio.html`, run a review or reopen the earlier/recent evidence bundles, then explicitly select **Retain current review**. The retained-investigations panel supports exact portfolio/date/location retrieval, source pointers and digests, exact evidence/report downloads and removal. Reviews live only in the current tab and are lost on reload; the existing saved-location configuration is separate. This is not a tenant-authenticated or durable cloud system. Do not use confidential coordinates on shared devices.

The previous `workspace.mjs` auto-start checked only the `run` ID, which is also used on the portfolio page. Reproduced on the exact RC10 local source with a DOM mock: importing `portfolio.mjs` threw a TypeError on a missing element. RC11 requires the dedicated `workspace-page` marker and uses a dedicated portfolio page entry module.

Run the controlled browser candidate test (it serves the repository on loopback, intercepts the two EONET requests with explicitly fictional fixtures, and denies external browser requests):

```powershell
python scripts/observatory_catalog_e2e.py
```

The proposed GitHub Actions workflow runs this controlled test and separately the live production audit. No credentials or external paid services are required. The 75 focused JavaScript and four Python helper tests passed locally; actual browser acceptance is still incomplete. Chromium 144.0.7559.96 launched but the production navigation was blocked by administrator policy (exit 2, 15/15 cases blocked). FIRMS activation and solar-image delivery are not changed by this candidate.
