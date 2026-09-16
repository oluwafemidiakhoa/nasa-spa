# NASA Space Apps 2026 — Competition Strategy

## Status

This repository is a pre-hackathon technical foundation. The final 2026 submission must be mapped to an official 2026 Space Apps challenge after the challenge statements are published. Do not submit an Artemis-themed project merely because it is polished; challenge fit is a hard gate.

The latest official judging guide verified during preparation is the 2025 NASA Space Apps Judging & Awards Guide. It evaluates projects on five equally visible dimensions: **Impact, Creativity, Validity, Relevance, and Presentation**. The 2026 guide may change, so re-check it when published.

## What winning projects tend to do

1. Solve **one sharply defined challenge**, not a portfolio of unrelated tools.
2. Make NASA/partner data **integral to the user action** rather than using it as background decoration.
3. Show a working method whose output can be inspected and reproduced.
4. Give a judge one memorable interaction that can be understood in seconds.
5. Make uncertainty, assumptions, and provenance obvious.
6. Tell the whole story in a short demo without requiring a long tour.

## 2026 product direction

### Moon→Mars Decision Atlas

The Decision Atlas is based on NASA's public Moon-to-Mars Architecture Definition Document Revision C and its architecture-driven technology gaps.

The core interaction is:

**select NASA priority gap → trace verified sub-architectures → trace campaign segments → inspect documented impact → compare unresolved vs gap-closed state → open authoritative source**

This mirrors a real NASA architecture practice. NASA describes priority decisions as decisions with major downstream flow-down impacts and says it tracks these impacts using digital engineering tools. The Atlas translates that systems-engineering idea into an accessible, source-backed interactive.

## Why this direction is stronger than the old dashboard

The removed readiness dashboard invented a composite GO/WATCH/HOLD score. Even with transparent rules, that looked more operationally authoritative than the public data justified.

The Decision Atlas instead shows relationships NASA actually publishes:

- official technology-gap priority ranking;
- official priority bin;
- documented gap description;
- documented architecture impact/benefit;
- documented campaign segments;
- documented sub-architectures;
- current state of the art and performance target where loaded;
- direct provenance back to NASA.

If a mapping has not been ingested, the interface leaves the graph blank rather than infer it.

## Rubric design

### Impact

User problem: Moon-to-Mars architecture documents are deep, technical, and difficult to navigate quickly. The Atlas turns architecture dependencies into an explorable map useful to students, researchers, technology developers, potential partners, and technical communicators.

Evidence to add during the hackathon:
- 3–5 short user tests;
- task completion time before/after using the Atlas;
- one concrete partner/research workflow enabled by the chosen challenge.

### Creativity

The creative element is not a chatbot. It is interactive architecture **flow-down reasoning**: a user can move from one technology deficiency to the affected systems and campaign stages while keeping the authoritative NASA source visible.

### Validity

Rules:
- never invent NASA priority scores or probabilities;
- do not infer missing traceability;
- distinguish NASA facts from prototype state changes;
- keep the source revision/date visible;
- prefer deterministic transformations of public data over opaque AI output;
- if AI is later added, use it only for bounded explanation/retrieval with cited source passages.

### Relevance

This remains the highest-risk criterion until the official 2026 challenges are public. A 2026 challenge must directly require or strongly benefit from the architecture/data interaction. If no official challenge fits, pivot to a different project rather than forcing Artemis into an unrelated challenge.

### Presentation

30-second judge story:

- **0–3 s:** "NASA has already ranked the technologies that Moon-to-Mars exploration still needs. But a ranked list does not show what each gap touches."
- **3–10 s:** Select #0801 Lunar Dust. Four sub-architectures and two campaign segments illuminate.
- **10–17 s:** Select #0103 Surface Communications. One systems domain reaches from lunar operations through Humans to Mars.
- **17–24 s:** Select #1104 Mars Transportation Propulsion. The map collapses onto the Humans-to-Mars transportation dependency.
- **24–30 s:** Toggle unresolved/closed and show the NASA provenance link. "No invented risk score—just NASA's architecture, made explorable."

## What is intentionally excluded

Do not put these on the competition front door unless the selected official challenge requires them:
- old ISS tracker;
- aurora dashboard;
- old Solar Storyline;
- TNO Fossil Lab;
- generic AI chat;
- unrelated 3D demos;
- arbitrary readiness percentages;
- long landing-page marketing copy.

The original 3D navigator can remain a secondary technical exhibit at `navigator.html`, but it is not the judge story.

## Data foundation

Primary source:
- NASA Moon-to-Mars Architecture Definition Document, Revision C, Document ID 20250010956.

NASA publishes machine-importable spreadsheets for:
- lunar objective mapping;
- Mars objective mapping;
- architecture-driven technology gaps;
- architecture-driven data gaps.

### Reproducible official-data pipeline

The repository now includes `scripts/sync_nasa_moon_to_mars.py`, which:

1. discovers the current 2025 Architecture Concept Review XLSX links from NASA's official Architecture Definition Documents page;
2. downloads all four workbooks directly from NASA;
3. calculates a SHA-256 hash for every source workbook;
4. parses the workbooks with `openpyxl`;
5. normalizes technology gaps, data gaps, and lunar/Mars objective mappings;
6. retains workbook filename, sheet, row, URL, and source hash as row-level provenance;
7. validates the generated dataset before replacing the existing JSON;
8. fails closed if discovery, download, parsing, or validation fails.

The GitHub Action `.github/workflows/sync-moon-to-mars-data.yml` runs offline parser tests before every real sync, supports manual execution, and checks NASA weekly. It commits generated data only when the authoritative source changes.

Generated files:
- `data/moon_to_mars_revision_c.json`
- `data/moon_to_mars_source_manifest.json`

Local/manual command:

```bash
python -m pip install requests beautifulsoup4 openpyxl
python scripts/sync_nasa_moon_to_mars.py
```

This pipeline is intentionally deterministic. The competition dataset is derived from NASA spreadsheets, not generated by an LLM.

## Final competition gate

Do not call the project "submission ready" until all are true:

- [ ] official 2026 challenge selected;
- [ ] one-sentence user/problem statement matches challenge wording;
- [ ] required NASA/partner data identified;
- [ ] NASA data changes the product output, not just the decoration;
- [ ] all displayed relationships have provenance;
- [ ] 30-second demo recorded and understandable without narration context;
- [ ] README reproduces the data pipeline;
- [ ] AI use disclosed;
- [ ] no dead links or external preview deployments;
- [ ] one teammate/user who did not build it can successfully demo it.
