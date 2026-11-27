# Gaia Observatory: saved investigations and evidence briefings

Local candidate based on the redesigned RC11 overlay and production reference commit `8abf4bcd7f4207088d86e80dc7ae24c7457d6a05`. **Not deployed. Not the full repository.** Keep all legacy pages, deployment configuration, datasets and workflows in the full repository. Do not replace the full application with this overlay. No new paid services, credentials, API calls or hosted workflow runs were introduced.

## What to try

Open My Locations, add labeled reference coordinates, choose an observation category and radius, and run a review or reopen two retained evidence bundles. Select **Save current review on this browser**. The stored evidence is replayed before a successful save. Reopen the same origin in the same browser profile, choose the saved review, search for a location and date, then generate and download its briefing. The briefing summarizes returned-record counts and set differences, explicitly withholds unsupported comparisons and includes source and bundle hashes and exact report JSON pointers. A deterministic report is not a prediction or scientific validation.

Saving is explicit; no automatic review retention or source polling occurs. The candidate uses IndexedDB with a single transactional history record, up to 20 reviews and 32,000,000 combined evidence bytes. Every restored pair is replayed, its identity checked, and the complete view published only after validation. Every write checks the current revision to reject conflicting changes by another tab. A failed write does not publish a new in-memory state. Reopening a corrupted store produces a visibly labeled tab-only fallback and leaves the saved bytes untouched; export evidence before clearing browser site data. Browser storage is origin-specific, unencrypted, not shared across devices, subject to browser quota/eviction, and accessible to code running on the same origin and potentially to other people using the same browser profile. Do not store sensitive business assets on a shared browser. Clearing or deleting history does not recall downloaded files or copies still held in other tabs.

## Windows verification (no deployment)

Extract this ZIP into a new folder, not over production or the original candidate. Open PowerShell there. Use Node 22 and Python 3.11 or later.

```powershell
node --test (Get-ChildItem tests\*.test.mjs).FullName (Get-ChildItem tests\*.test.cjs).FullName
python -m unittest discover -s tests -p test_observatory_audit_helpers.py -v
```

If the free Playwright package and Chromium are not already installed:

```powershell
python -m pip install playwright==1.57.0
python -m playwright install chromium
```

Then run the controlled browser acceptance suite:

```powershell
python scripts/observatory_catalog_e2e.py --screenshots qa-screenshots
```

It starts a loopback server; routes external requests to an explicit denial; uses fictional, controlled data fixtures; tests map, editor, evidence review, IndexedDB restoration after reload, briefing download, removal after reload, mobile width and uncaught browser errors; saves five actual screenshots if execution reaches those checkpoints. The script uses an isolated browser context, not your existing saved browser history. Do not run it against production or supply secrets. For a manual real-data review, use the separate full application only after the release is authorized and live source connections are verified.

## Current evidence and limitations

- 81 baseline JavaScript tests passed; 93 final tests passed (12 added). The new persistence tests use a controlled storage adapter, not a real browser IndexedDB implementation.
- Four existing Python verification helper tests passed.
- Static HTML checks found unique IDs, valid in-page anchors, and labeled input/select/textarea controls on the dashboard and My Locations. No computed-contrast or WCAG conformance claim.
- Actual Playwright with Chromium 144.0.7559.96 returned exit code 2 (`ERR_BLOCKED_BY_ADMINISTRATOR`); no new candidate screenshots or real IndexedDB acceptance were obtained. The actual UI and screenshot review are incomplete.
- Eleven science and API files match the preceding local interface candidate byte for byte. FIRMS public-feed activation, solar-image delivery and live-source checks are unchanged/unresolved.

See `evidence/history-audit.json`, `evidence/history-regression-node.txt`, `evidence/history-python.txt`, `evidence/history-playwright.txt`, `evidence/history-markup.json`, and `docs/saved-history-contract.md`. All earlier interface audit files are historical baseline evidence. Do not deploy until actual browser acceptance, review and live integration gates pass and a release is separately authorized.
