# Gaia Observatory

**From Scientific Data to Verifiable Intelligence.**

Gaia Observatory is the independent research-platform evolution of the earlier NASA Space Apps project in this repository. The existing Moon-to-Mars Mission Trainer, Decision Atlas and 3D navigator remain intact. This is separate from [Gaia Lunar Systems — The First Night](https://github.com/oluwafemidiakhoa/gaia-lunar-systems-2026), the 2026 team project.

## Observatory v1.0 RC10 (release candidate)

- [Observatory entrance](observatory.html): links to existing modules and a NASA source-manifest catalog.
- Recorded source URLs, SHA-256 digests, workbook row counts and normalized record counts are displayed separately. The catalog validates manifest structure, not authenticity or raw source bytes.
- Legacy space-weather modules are linked as unvalidated prototypes. Earth Intelligence has an offline point-screening pilot; Cosmic Intelligence remains planned.
- No new dependencies, API keys, or external requests are needed to render the local catalog.

Run from the repository root:

```sh
python -m http.server 8000
# open http://localhost:8000/observatory.html
node --test tests/observatory.test.mjs tests/earth.test.mjs
```

The RC10 candidate changes the Vercel root to `/live_dashboard.html`; the preserved competition trainer remains at `/mission-trainer`, `/trainer`, `/atlas` and `/navigator`. Competition datasets and submission documents are unchanged. Do not treat the Observatory as an operational alert or flight-planning service. Before a public or commercial release, confirm contributor permissions, licenses, source terms, browser integration and deployment safety.

## Earth Intelligence pilot

Open [earth.html](earth.html) using localhost or HTTPS. Choose a location, UTC cutoff, lookback and radius, then use the explicitly synthetic fixture or import a saved NASA EONET v3 events JSON file (maximum 2 MB). The analysis is browser-local; there is no live data acquisition or API key. Export a JSON report containing the raw snapshot SHA-256, parameters, nearest point per matching event, and coverage exclusions. Retain the source bytes for replay. Source authenticity is not established, and no match does not imply safety.

[Method and limits](earth-method.md) · [NASA EONET v3 documentation](https://eonet.gsfc.nasa.gov/docs/v3).

Local Node 22.16.0: 18 Earth tests passed, including negative inputs, distance/time boundaries, coverage and an independent digest comparison. The method digest recorded before execution was `33518f869a0ac954c3700abc01482ef05ae9240d1e265afaee06fb52c65115fc` (unsigned, no trusted timestamp). Browser smoke testing was blocked by the execution environment; live NASA payload compatibility, visual QA, and full repository regression tests remain unverified.

## Multi-facility screening and independent replay (v0.3)

[Batch method and commands](docs/earth-batch.md). Screen up to 25 facility coordinates against a single retained snapshot and explicit shared time window/radius. The Node.js generator hashes the original snapshot and configuration bytes; a separate Python verifier independently recomputes results with a spherical vector formula and requires the original input files. Use the supplied synthetic configuration to exercise the workflow offline.

Verified locally with Node.js 22.16.0 and Python 3.13.5: 11 new cross-runtime test methods (including 12 distinct report-tampering subcases and 9 invalid configuration subcases) and all 18 existing Earth tests passed. The synthetic run had two matching facilities and one with no matching point, and independent replay matched all three results. The locally recorded, unsigned method SHA-256 before testing is `f67d415382bf9994deca826a1496934e3df307d5f4f97597f23b4149a1cfd067`. This is not a trusted timestamp.

Replay is the acceptance gate: the Node JSON parser alone permits duplicate object keys; the Python verifier rejects them. Reports are limited to 16 MB. Numeric ties and cutoff boundaries may disagree across implementations and are rejected rather than silently accepted. Batch replay does not verify the older v0.2 single-facility report format. NASA's v3 documentation was consulted, but archived API data could not be retrieved in the execution environment. No real-event performance, source authenticity, browser QA, full repository regression, or production readiness is claimed.

## NASA EONET acquisition and archive (v0.4)

[Acquisition contract and CLI commands](docs/eonet-archive.md). The standard-library Python tool retrieves a bounded, explicit date/category query from the fixed EONET v3 endpoint, retains the exact response bytes, and records UTC capture time, query metadata, SHA-256, byte and observation counts, and unknown coverage. Offline imports never assert NASA retrieval. The verifier recomputes receipt consistency and optionally checks an independently retained archive digest; it can export exact source bytes for v0.3 screening. There are no new dependencies, API keys, redirects, automatic retries, or scheduled requests.

**Verification (2026-11-26):** Python 3.13.5: 10 new test methods passed, including mocked HTTP failure paths, malformed data, tampered receipts, digest mismatch, worker timeout and no-overwrite behavior. Python compilation passed. The existing synthetic snapshot (Git blob `641024e82bf842a77ed25a616ae5fc5a089e5a09`) was imported and exported byte-for-byte with the separately supplied archive digest; 795 source bytes, four events, five points, one non-point geometry. Source SHA-256: `0d50093b50a4ec9657597fa5962627659495a70a68dcf735fb546d0271855f78`. The acquisition contract SHA-256 recorded before test execution was `729e3aab5f0ea0f32476251614c8efb269bc98cbe8b1a78338202a54841027c9` (unsigned local digest, not trusted chronology). One bounded live command failed with DNS resolution error, exit 1, and no output archive. No live payload, successful TLS session, end-to-end batch replay, browser, full repository regression, crash recovery or production readiness is claimed for v0.4. Network success paths were mocked; archive integrity is not authenticated scientific provenance. Retain the archive digest independently. A valid but modified archive with newly computed metadata can pass unanchored verification.

## Portable Earth evidence (v0.5)

[Evidence bundle contract and commands](docs/earth-evidence.md). The new offline CLI packs the exact v0.4 archive, v0.3 screening configuration and independently replayed report into one bounded JSON bundle. It records component SHA-256 digests and implementation fingerprints, repeats independent replay before publishing a new bundle, and refuses to overwrite output. An optional independently retained bundle digest detects complete replacement. No NASA authenticity, scientific validity, complete coverage, or operational safety is established.

Verified locally with Python 3.13.5 and Node.js 22.16.0: 9 new integration and adversarial test methods passed; the earlier synthetic baseline independently replayed all three facilities. The original source files used in the test were matched to their Git blob identifiers at baseline commit `2b38ae2f749df73723112811110b77e913e49ec0`. The synthetic result contains two facilities with matches and one without. The method contract was hashed before testing (SHA-256 `d2e193e5aeaab320a236c63964978a7a2b14a81a8df2264e9569fa48693329f9`); this is local and unsigned, not trusted chronology. No live data, browser QA, whole-repository regression, CI or production readiness is claimed.

## Facility evidence dashboard (v0.6)

Open [facilities.html](facilities.html) on localhost to inspect an existing v0.5 bundle or load the committed synthetic demonstration. The interface checks component digests, archived source bytes and declared method identifiers; it reruns the JavaScript screening method and compares all report results before showing them. Optional independent digest matching, a facility selector, paginated observations and explicit coverage limits are included. No remote data requests or application dependencies are introduced. The browser does not run the independent Python verifier. See [method and limitations](docs/facility-dashboard.md).

Local verification on 2026-11-26: Node 22.16.0 `node --test tests/facility.test.mjs` passed 9 tests; Python 3.13.5 `python -m unittest discover -s tests -p 'test_earth_evidence.py' -v` passed 9 regression tests. Independent CLI replay of the committed synthetic fixture with SHA-256 `581858bf6af04be1b2ecdbe6d9db6e50d621c9cac0629dbb2076d8fe22905bb8` returned `REPLAY_MATCH` for three facilities. Chromium launched, but navigation to the local HTTP server was blocked (`ERR_BLOCKED_BY_ADMINISTRATOR`); browser interaction, mobile layout, whole-repository regression, CI, live NASA data and production readiness remain unverified. The method contract digest recorded locally before testing was `daae2bc6489686c1085a988f9ea97f48dbd27bd6930552aed1289adfc854857b` (unsigned, not a trusted timestamp).

## Historical Earth Intelligence (v0.7)

Open [history.html](history.html) on localhost. Import a v0.5 bundle or use the synthetic example. The new module verifies the original bundle using the existing browser replay, divides its original inclusive UTC window into at most 31 calendar dates, and reports eligible point rows, matching rows, and distinct matching event IDs separately for up to 25 facilities. Missing observations are distinguished from no matches. Export JSON and independently recompute every field using `python scripts/verify_earth_history.py BUNDLE.json HISTORY.json --expected-sha256 DIGEST` (optional independently retained digest). [Method and limitations](docs/earth-history.md).

Local verification on 2026-11-26: Node 22.16.0 passed 6 new history and 9 existing dashboard tests; Python 3.13.5 passed 5 new history and 9 existing evidence tests. The synthetic history exported from JavaScript independently replayed against the committed bundle and its retained SHA-256. All 3 facilities and 4 dates matched; the report SHA-256 is `11cc5605548c43600d4a5d6a66ea6b2adce4dad720399f325401e84084aea613`. The method contract was hashed before implementation (`6e84171b0ab1857f27c4a545c38596595c6e629f23e36b1a2852fe35c037034d`, local unsigned hash, not trusted chronology). A bounded NASA EONET request for January 7–15, 2025 wildfires failed DNS resolution (exit 1, no output archive). New browser interaction, live data, entire-repository regression, CI, and production deployment remain unverified. The reported counts are not trends, exposure estimates, or evidence of operational safety.

## Scientific observation screening (v0.8)

Open [anomaly.html](anomaly.html) on localhost. A fixed 19-day baseline compares the latest fully contained UTC date using exact daily matching-point shares. The research prototype abstains if any of the 20 days is missing or has fewer than five eligible recorded point rows. Ties are conservative and the descriptive rank is not a calibrated p-value or hazard forecast. The report binds original evidence digests; [the independent Python verifier](scripts/verify_earth_anomaly.py) recomputes the historical observations and exact rational ranks. [Method and limitations](docs/earth-anomaly.md).

Local verification on 2026-11-26: Node 22.16.0 passed all 21 tests across anomaly (6), history (6), and facility (9) suites. Python 3.13.5 reported 5/5 new anomaly and 9/9 existing evidence tests as passing before the broader suite was interrupted during the older history tests; complete Python regression remains unverified. The synthetic 20-day bundle independently replayed all three facilities, with one above the baseline maximum and two not above it (including ties). The short synthetic bundle abstained for all facilities. Bundle SHA-256 `904104d5488e7ff4f79b1720ef35ccd74b85e01c96d52897c1af63300b279c05`; report SHA-256 `e88486a500151198c5b1b880136b9c832687fdf592886f86d4c8ef63dd872a03`; method document SHA-256 recorded before implementation `777f49884640549a9c5669c96a018f9983936bc051cacbbe3a056df4f0774ea7` (local unsigned digest, not trusted chronology). No real-data scientific validation, browser interaction, entire-repository regression, CI or production deployment is claimed.

## Evidence-backed research desk (v0.9)

Open [research.html](research.html) on localhost. This deterministic question interface derives facts from the original retained bundle via historical and observation screening replay. It supports five exact command types: summary, explain FACILITY-ID, day FACILITY-ID YYYY-MM-DD, provenance and limits. Unknown commands and unavailable records abstain. Every answer binds the query, bundle/source digests, and data facts with intermediate-report JSON pointers. It is not a general chatbot or LLM. See [the method](docs/research-assistant.md) and [independent verifier](scripts/verify_research_answer.py).

Local verification: 27 JavaScript tests passed (6 new research and 21 regression); four new Python research tests passed, including cross-runtime replay for all supported commands, unsupported queries, altered values/pointers, query substitution and wrong digest. The manufactured synthetic example explains one above-baseline facility and two not above. No live-data scientific validation, full repository regression, browser interaction, CI or deployment is established.

## Mission Control and cloud Earth workspace (v1.0 RC7)

Open the [visual observation console](live_dashboard.html) for the world map, NASA imagery and space-weather charts, or [Mission Control](mission-control.html) for the four product areas: Earth Intelligence, Cosmic Research, Space Intelligence and Universe Academy, with shared evidence tools. The new [Earth workspace](workspace.html) uses the preview-only bounded EONET retrieval endpoint; public date and category parameters go to Vercel, while location screening, evidence packaging and imports remain in the browser. Mission Control automatically requests EONET wildfires from the last seven complete UTC days, APOD and DONKI CME records on entry. The Earth workspace automatically runs a recent wildfire study. Manual refresh is available; no continuous polling is used. APOD and DONKI reuse the existing API; runtime availability of all cloud sources remains to be verified. They display recorded title/date and returned-record counts, not scientific predictions. FIRMS, JPL and Earthdata are planned, not connected. Academy and other mission prototypes remain preserved and have not been revalidated.

Local Node 22.16.0 execution: `node --test tests/cloud-eonet.test.cjs tests/cloud-workspace.test.mjs tests/mission-control.test.mjs tests/auto-start.test.mjs tests/live-dashboard.test.mjs` passed 26/26 targeted tests on 2026-11-26. Tests use controlled responses; no live retrieval through the cloud interface, browser end-to-end test, cross-runtime Python verification of newly generated browser bundles, or scientific validity is established by these tests. See [cloud workspace instructions](docs/cloud-workspace.md). Preview only; no production promotion or new paid services.

## Expansion roadmap

1. Verify archived scientific source bytes independently and record reproducible verification receipts.
2. Validate the implemented acquisition/archive and Earth batch replay against an actual authoritative snapshot, then validate the multi-facility interface in a real browser.
3. Audit legacy astronomy and space-weather ingestion, freshness and scientific claims.
4. Evaluate anomaly detection against frozen baselines before publishing scientific or commercial claims.

---

## Preserved mission-training documentation

# Moon→Mars Mission Trainer

**NASA Space Apps Challenge 2026 — Build a Junior Astronaut Mission Trainer**

🔗 **Live demo:** https://nasa-spa.vercel.app/

Moon→Mars Mission Trainer is a student-facing lunar/Martian outpost simulation powered by NASA's Moon-to-Mars architecture data. Students receive limited training credits, choose which NASA-documented technology gaps to address, then run a debrief to see which mission systems still carry other unresolved dependencies.

The competition experience is intentionally layered:

- `trainer.html` — public Mission Trainer front door.
- `index.html` — Moon→Mars Decision Atlas evidence engine.
- `navigator.html` — gap-aware 3D mission context.
- `data/moon_to_mars_revision_c.json` — normalized NASA architecture dataset.
- `data/moon_to_mars_source_manifest.json` — authoritative source URLs, hashes, and counts.

## Competition concept

The 2026 challenge asks teams to build an interactive game or app that lets students run a lunar or Martian outpost while balancing competing engineering demands.

Our response is not a fictional mission simulator disconnected from real data. The game layer uses clearly labeled training mechanics, while the engineering relationships underneath come from NASA's official Moon-to-Mars Architecture Revision C products.

### Student flow

```text
Choose lunar or Mars outpost
        ↓
Spend limited training credits
        ↓
Select NASA technology gaps to address
        ↓
Run mission debrief
        ↓
Inspect clear vs still-exposed architecture nodes
        ↓
Open Decision Atlas / 3D context / NASA source evidence
```

## NASA evidence layer

The automated sync pipeline ingests NASA's official 2025 Architecture Concept Review XLSX products:

- Lunar Objective Decomposition
- Mars Objective Decomposition
- Architecture-Driven Technology Gaps
- Architecture-Driven Data Gaps

The current production sync contains:

- **57 technology gaps**
- **19 normalized data gaps**
- **10,871 lunar objective rows**
- **4,094 Mars objective rows**

Each source is recorded with URL, filename, byte size, record count, and SHA-256 provenance. Technology-gap rows also preserve source workbook, sheet, and row where available.

## Decision Atlas

`index.html` is the engineering/evidence layer behind the student trainer. It supports:

- Gap → Architecture
- Architecture → Gaps
- Compare Gaps
- Residual Dependency Analysis
- NASA source provenance

The residual engine performs deterministic graph subtraction: when a technology gap is assumed addressed in a training scenario, the Atlas removes only that gap from the loaded graph and reports which other mapped gaps still touch the same architecture nodes.

## 3D mission context

`navigator.html` preserves the selected ESDMD technology-gap ID and maps it into an illustrative mission locus such as Earth→Moon, lunar/cislunar operations, Moon→Mars transit, or Mars approach.

The 3D geometry is explicitly labeled illustrative. NASA architecture relationships remain source-backed and are not inferred from scene geometry.

## Scientific guardrails

This project deliberately avoids claims the data cannot support:

- no invented mission-readiness percentage;
- no fabricated survival or mission-success probability;
- no inferred graph edge when NASA relationships are absent;
- no claim that broad architecture reach equals strategic importance;
- no claim that a selected training investment means NASA has solved that gap;
- no claim that closing one gap makes a mission ready;
- training-credit values are fictional educational mechanics and are labeled as such.

## Data pipeline

The NASA sync is implemented in `scripts/sync_nasa_moon_to_mars.py` and validated in GitHub Actions. The workflow:

1. discovers the current NASA Moon-to-Mars Architecture Definition Documents page;
2. downloads the official XLSX products;
3. computes SHA-256 hashes;
4. normalizes the workbook rows;
5. validates IDs, counts, objectives, and source provenance;
6. fails closed if required source products or integrity checks are missing;
7. commits generated data only after validation passes.

Transient NASA HTTP 429 responses are handled with bounded backoff retries.

## Local use

The flagship experiences are dependency-light static HTML pages. Serve the repository with any local HTTP server so browser `fetch()` calls can load the JSON dataset.

Example:

```bash
python -m http.server 8000
# open http://localhost:8000/trainer.html
```

## Competition validation

`scripts/validate_competition_readiness.py` checks the NASA dataset structure, Atlas markers, Trainer markers, 3D handoff, provenance, challenge narrative, and other competition-critical invariants on CI.

See `SUBMISSION.md` for the current 30-second and 2-minute judge demo scripts.

## Attribution

Built by **Oluwafemi Idiakhoa** for NASA Space Apps Challenge 2026.

Core technologies: NASA public Moon-to-Mars architecture data · HTML/CSS/JavaScript · Three.js · Python · GitHub Actions · Vercel.

**Independent educational/research prototype. Not an official NASA product or flight-planning system.**

### RC3 EONET transport recovery

The RC2 preview showed a 502 on EONET while APOD and DONKI reported records in a user browser. The upstream cause remains unconfirmed; the original proxy suppressed diagnostics. RC3 accepts supported HTTP content encodings via Node fetch and checks decoded JSON bytes against the existing size limit, with identity-only length equality. Safe upstream failure codes appear in the UI and Vercel logs. A local loopback HTTP server reproduced the compressed-response defect and verifies recovery, corruption rejection and decompressed size limits. No live upstream recovery is claimed; the environment could not resolve the NASA host. No changes to scientific screening, source selection or production.

### RC4 visual observation console

The dashboard uses a generalized Natural Earth land-outline basemap (public domain, https://www.naturalearthdata.com/about/terms-of-use/), not satellite imagery. It automatically requests EONET, APOD and DONKI on entry. Select EONET categories and returned event markers, zoom to a point, and inspect or download evidence. APOD may show a validated NASA-hosted still-image URL and returned text; DONKI shows counts by usable returned UTC observation dates. Source coverage, authenticity and scientific validity remain unknown. On acquisition failure the map remains visible without fabricated points. Synthetic data is displayed only through an explicit labeled selection. Local Node 22.16.0 tests: 26/26 passed, exit 0; the test suite includes controlled upstream responses, real loopback compressed HTTP and simulated DOM interactions, not a browser end-to-end or successful live NASA test. RC3 transport recovery is not independently confirmed in the live preview. The protected preview is not production-ready. Original main, root routes and scientific methods are unchanged.

### RC7 visual scientific dashboard

The visual dashboard now opens with four image-led product tiles. It includes a historical NASA GIBS Blue Marble mosaic (with Natural Earth outlines as a fallback), historical NASA SDO and Webb images with source links, current feed summaries, and an interactive illustrative eight-planet model. The latter uses approximate NASA orbital periods, arbitrary phases and compressed scales; it is not an ephemeris. The new regional FIRMS NOAA-20 VIIRS panel requires `FIRMS_MAP_KEY` in Preview; thermal detection rows are not confirmed fires. Historical imagery and simulated positions are not live data. JPL, NOAA continuous measurements and authenticated Earthdata remain planned. RC5 selected-event histories and safe APOD credits are included. Node 22.16.0: 43/43 targeted tests passed (`node --test tests/*.test.cjs tests/*.test.mjs`); static HTML inspection found 79 unique IDs and valid internal anchors. Browser navigation was blocked by local Chromium policy, and NASA image download was blocked by local DNS; external imagery and deployed FIRMS operation remain unverified. The previously confirmed RC4 deployment displayed EONET severe storms, APOD imagery and a DONKI empty collection in the user's browser. No production promotion, credential-scope change, paid service, or polling was performed.

### RC8 regional imagery and measured geomagnetic indices

The visual console requests a region-specific historical GIBS Blue Marble mosaic instead of magnifying the global image. The two independently fetched NOAA SWPC products are `https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json` and `https://services.swpc.noaa.gov/products/kyoto-dst.json`. Charts plot recorded estimated planetary Kp (three-hour cadence) and Kyoto Dst (hourly), retain missing samples, break lines across gaps, and offer exact-byte source receipts. These are geomagnetic indices, not solar-wind measurements or forecasts. No new keys, paid services, polling or production changes. Local Node 22.16.0 targeted suite: 51/51 passed, exit 0; 90 unique HTML IDs and valid internal anchors; static scanner found no pattern matches (not a security certification). Browser rendering blocked by local Chromium policy. Live retrieval and regional imagery sharpness remain unverified. FIRMS and Earthdata credentials were confirmed production-only; their scopes were not changed. Protected preview only.

### RC9 Vercel landing and recovery candidate

The public name is Gaia Observatory. This candidate redirects `/` to `/live_dashboard.html` and keeps `/mission-trainer` as a versioned entry into the original competition experience. The EONET transport accepts mislabeled JSON only after strict envelope and observation validation; HTML errors still fail closed. A fixed-origin solar image proxy is added; NOAA and EONET support the production environment with bounded responses and shared cache directives. FIRMS remains gated in production pending a quota and authentication check; keys are never exposed. Existing mission and evidence algorithms are preserved. The focused 56-test suite was re-executed locally on Node 22.16.0; all passed. Live endpoint and image checks, complete CI, public release and source-rights review remain open. RC8 was previously merged as PR #33; this is a separate corrective candidate.

### RC10 My Locations — environmental observation reviews

Open [My Locations](portfolio.html) from the dashboard. Save up to 25 reference locations and the selected category/radius in browser-local storage. The review makes two bounded global EONET requests for the two most recent adjacent seven-day UTC calendar windows; site coordinates stay local. It compares retained event-ID sets at each location, not hazard rates or newly occurring incidents. The screening intervals share their midnight endpoint, and completeness/authenticity are unknown. If either global collection has no eligible points or reaches the source limit, derived set comparisons are withheld. Users can download both original evidence bundles and a derived JSON report, and recompute from retained bundles. No independent scientific validation, background monitoring, account sync, alerting or subscriptions are provided. Controlled-response tests passed 61/61 on Node v22.16.0 on 2026-11-26; all 32 tested local files matched the staged Git blobs. This is a focused subset, not the entire repository or browser acceptance suite. Production RC8 and the existing trainer remain available until release gates pass. No new paid service, secrets, or automatic polling.
