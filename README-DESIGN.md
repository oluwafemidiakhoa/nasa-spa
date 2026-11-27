# Gaia Observatory — Field desk interface candidate

**Historical design baseline.** For the current saved-history candidate and latest verification counts, see `README-HISTORY.md`.

Local review candidate, based on production `8abf4bcd7f4207088d86e80dc7ae24c7457d6a05` and the previously staged RC11 catalog. Not deployed or published. This is a focused source overlay and test workspace, **not the complete NASA repository**. The legacy trainer, astronomy research desk, history, atlas and academy still reside in the full repository. Do not replace the repository with this directory or deploy it directly. No new paid infrastructure or credentials are required by the local tests.

## What changed

The homepage now leads with its primary task: reviewing locations and investigating the real global observation map. Historical reference imagery appears later, instead of occupying the first screen. The My Locations workflow accepts separately labeled ID/longitude/latitude fields, previews exact reference coordinates on a geographic map, supports add/remove and explicit browser-local save, and retains the advanced coordinate-row editor. Report summaries and download controls are visible after successful review; reopened bundles restore their actual portfolio, and editing locations invalidates old results. Empty, missing, capped and zero-count states remain distinct. The retained investigation catalog remains tab-local. Existing scientific methods and API code are unchanged from the RC11 baseline.

## Test locally (no deployment)

Use Node.js 22 and Python 3.11 or later. Extract this ZIP to its own directory and open PowerShell there.

```powershell
node --test (Get-ChildItem tests\*.test.mjs).FullName (Get-ChildItem tests\*.test.cjs).FullName
python -m unittest discover -s tests -p test_observatory_audit_helpers.py -v
```

For actual browser acceptance and screenshots, use an installed Playwright Chromium browser, or install the free Playwright tooling if necessary:

```powershell
python -m pip install playwright==1.57.0
python -m playwright install chromium
python scripts/observatory_catalog_e2e.py --screenshots qa-screenshots
```

The controlled browser script serves the candidate on loopback, intercepts the expected data requests with labeled fictional test fixtures, denies external browser traffic, and checks the dashboard, map selection, zoom, local location entry and restoration, two-window review, retention, evidence download digest, removal, mobile layout and uncaught page errors. It saves five screenshots under `qa-screenshots/` only after reaching the corresponding actual browser state. It returns 2 if administrator navigation policy prevents execution. No screenshots of the redesigned pages were obtained in the assistant's environment. A blocked run is not a pass.

The existing `scripts/observatory_browser_audit.py` is a separate read-only check of the current public production URL, not this candidate. It retrieves live public data and should only be run when that live traffic is wanted. The controlled candidate test does not use live NASA requests. Do not paste or provide API secrets to either test.

## Installation as a patch

The application and test files can be reviewed against the RC10 production tree, and selectively applied to a clean full checkout on a local branch. The RC11 startup repair and catalog files are included because the redesigned location desk depends on them. Preserve the full checkout's legacy pages, datasets, Vercel routing and existing workflows. Do not push to the Vercel-connected repository until separately authorized: branch pushes may trigger Preview builds. The archive excludes CI workflow changes; no hosted workflow was run for this redesign.

See `docs/interface-audit.md` and `evidence/interface-audit.json` for the design plan, test findings, scope and blockers. `evidence/file-hashes.json` identifies the exact candidate files. All counts refer to the focused included test suite, not full repository CI, commercial validation or scientific validity.
