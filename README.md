# Gaia Observatory

**From Scientific Data to Verifiable Intelligence.**

Gaia Observatory is the independent research-platform evolution of the earlier NASA Space Apps project in this repository. The existing Moon-to-Mars Mission Trainer, Decision Atlas and 3D navigator remain intact. This is separate from [Gaia Lunar Systems — The First Night](https://github.com/oluwafemidiakhoa/gaia-lunar-systems-2026), the 2026 team project.

## Observatory v0.4 (development)

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

The existing root route, competition validation, datasets and submission documents are unchanged. Do not treat the Observatory as an operational alert or flight-planning service. Before a public or commercial release, confirm contributor permissions, licenses, source terms, browser integration and deployment safety.

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

## Expansion roadmap

1. Verify archived scientific source bytes independently and record reproducible verification receipts.
2. Validate the implemented acquisition/archive and Earth batch replay against an actual authoritative snapshot, then build a multi-facility interface.
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
