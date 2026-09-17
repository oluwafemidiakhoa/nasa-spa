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
