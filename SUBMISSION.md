# Moon→Mars Decision Atlas

**NASA Space Apps Challenge 2026 — current submission narrative and demo script.**

> **Challenge alignment is intentionally pending.** The final submission must be mapped to the exact official 2026 challenge statement once NASA publishes it. Do not force this project into an unrelated challenge.

---

## One line

**Moon→Mars Decision Atlas transforms NASA's Moon-to-Mars architecture data into an auditable dependency map: select a technology gap, see what systems and campaign segments it touches, test what remains after that gap is addressed, open the gap in 3D mission context, and trace every relationship back to NASA evidence.**

## The problem

NASA publishes detailed Moon-to-Mars architecture material, including prioritized technology gaps, campaign segments, sub-architectures, objectives, data gaps, and technical source documents. The information is authoritative, but much of it is distributed across long technical documents and spreadsheet products.

A ranked gap list answers **what is important**. It does not immediately answer:

- What architecture does this gap touch?
- Which systems are exposed to several independent gaps?
- If one gap is addressed, what documented dependencies still remain?
- Where in the Moon-to-Mars journey does that capability matter?
- Can every displayed relationship be traced to its NASA source?

The Atlas turns those questions into an interactive, source-backed exploration workflow.

## What we built

```text
NASA Revision C architecture data
        ↓
normalized + validated dataset
        ↓
Gap → Architecture graph
        ↓
Architecture → Gaps reverse lookup
        ↓
Gap comparison
        ↓
Residual dependency analysis
        ↓
3D mission context
        ↓
NASA provenance
```

### 1. Gap → Architecture
Select a NASA-prioritized technology gap and see only the campaign segments and sub-architectures that are explicitly present in the loaded dataset.

### 2. Architecture → Gaps
Reverse the question. Select a system such as Mobility, Power, Habitation, Communications/PNT, or Transportation and see which loaded NASA technology gaps explicitly touch it.

### 3. Compare Gaps
Compare two gaps using shared and unique architecture reach. The Atlas reports descriptive graph overlap only; it does **not** convert architecture breadth into an invented importance score.

### 4. Residual Dependency Engine
Switch a gap from **UNRESOLVED** to **GAP ADDRESSED**. The Atlas removes only that selected gap from the loaded graph, then shows which other loaded NASA technology gaps still touch the affected architecture nodes.

Green means no other loaded gap mapping remains on that node. Amber means other loaded gaps remain. This is deterministic graph subtraction, not a readiness score or mission-success probability.

### 5. 3D Mission Context
Open the selected gap in the existing interactive 3D navigator. The selected ESDMD gap ID is preserved in the URL and mapped to a relevant mission locus such as Earth→Moon, lunar/cislunar operations, Moon→Mars transit, or Mars approach. Gaps that share the same physical locus still change the subsystem focus rather than fabricating different orbital geometry.

### 6. Evidence and provenance
Every displayed relationship is designed to trace back to NASA source material. The ingestion pipeline records workbook, sheet, row, source URL, and SHA-256 provenance when available. Missing relationships remain missing rather than being inferred.

## NASA data/resources

Primary source:

- **NASA Moon to Mars Architecture Definition Document — Revision C**
- NASA Technical Reports Server document ID **20250010956**
- 2025 Architecture Concept Review products
- NASA-published Lunar Objectives, Mars Objectives, Technology Gaps, and Data Gaps spreadsheets

The repository contains a deterministic sync pipeline that discovers NASA's official XLSX products, downloads them, records hashes, normalizes their rows, validates the result, and updates the Atlas dataset only when validation passes.

NASA data is therefore the product's core data model, not decorative background content.

## Scientific and engineering guardrails

The Atlas deliberately avoids claims the source data cannot support:

- no invented mission-readiness percentage;
- no fabricated probability of mission success;
- no inferred graph edge when a NASA relationship is absent from the loaded dataset;
- no claim that broad architecture reach equals higher strategic importance;
- no claim that closing one technology gap makes a mission or segment ready;
- 3D geometry is illustrative and is labeled separately from NASA architecture traceability.

## Current traceability status

The project distinguishes **priority verification** from **detailed architecture traceability**. Some ranked technology-gap rows currently contain rich verified mappings while other gaps remain rank-only until the official spreadsheet sync provides the corresponding relationships.

This is treated as a visible competition blocker, not hidden with guessed links. The permanent competition-readiness validator reports exact coverage on every pull request and main-branch push.

## Why this can matter

NASA's Moon-to-Mars architecture is a system of interacting decisions, capabilities, technologies, and mission objectives. The Atlas makes that architecture easier to interrogate for:

- students and educators;
- researchers;
- universities;
- technology developers and startups;
- industry and international partners;
- members of the public trying to understand what sustained Moon-to-Mars exploration actually requires.

The product does not replace NASA systems engineering. It provides an accessible, auditable interface over public NASA architecture information.

---

## 30-second judge demo

| Time | Visual | Voiceover / caption |
|---|---|---|
| 0–5s | Select **#1 Lunar Dust-Tolerant Systems and Dust Mitigation** | "NASA has already ranked technologies that Moon-to-Mars exploration still needs. But a ranked list does not show what each gap touches." |
| 5–10s | Gap → Architecture lights Mobility, Habitation, Logistics, Power and campaign segments | "The Atlas turns NASA architecture data into a dependency map." |
| 10–16s | Click **GAP ADDRESSED** | "Now solve only this one deficiency. Green nodes are clear of other loaded gaps; amber nodes still carry other NASA technology gaps." |
| 16–21s | Reverse lookup on **Mobility** | "Reverse the question: what other gaps still touch Mobility?" |
| 21–26s | Open selected gap in 3D | "Then place the selected technology in its Moon-to-Mars mission context." |
| 26–30s | Open NASA source/provenance | "And every relationship remains auditable back to NASA evidence." |

### Closing line

**Moon→Mars Decision Atlas: not another dashboard — an auditable way to interrogate what still has to mature, what it touches, and what remains after one problem is solved.**

---

## 2-minute live demo flow

1. Start on **Gap → Architecture** with Lunar Dust.
2. Point out the exact loaded sub-architectures and campaign segments.
3. Toggle **GAP ADDRESSED** and explain residual dependencies.
4. Click an amber node such as Mobility and switch to **Architecture → Gaps**.
5. Show the connected gaps returned by reverse lookup.
6. Use **Compare Gaps** to contrast Lunar Dust and Mars Transportation Propulsion without ranking them.
7. Click **OPEN THIS GAP IN 3D** and show preserved gap context.
8. Return to the Atlas with the same gap selected.
9. Open the NASA provenance link and close on the no-invented-links guardrail.

## Competition readiness gates

Before final submission:

- [ ] Exact official 2026 challenge statement selected.
- [ ] `CHALLENGE_ALIGNMENT.md` completed against every challenge requirement.
- [ ] Official NASA XLSX sync completes successfully on GitHub Actions.
- [ ] Detailed technology-gap traceability coverage reviewed and disclosed.
- [ ] Every selected gap survives Atlas → 3D → Atlas round-trip testing.
- [ ] 30-second and 2-minute demos recorded from the final deployed build.
- [ ] Submission wording contains no retired Solar Storyline/hub narrative.
- [ ] All simulations/illustrations are explicitly labeled.
- [ ] Public deployment and NASA source links tested in a clean browser session.

## Team and attribution

Built by **Oluwafemi Idiakhoa** for the NASA Space Apps Challenge 2026 preparation cycle.

Core technologies: NASA public Moon-to-Mars architecture data · HTML/CSS/JavaScript · Three.js · Python data normalization/validation · GitHub Actions · Vercel.

**This is an independent educational/research prototype and not an official NASA product or flight-planning system.**
