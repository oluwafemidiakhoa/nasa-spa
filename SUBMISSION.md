# Moon→Mars Mission Trainer

**NASA Space Apps Challenge 2026 — Build a Junior Astronaut Mission Trainer**

## One line

**Moon→Mars Mission Trainer lets students run a lunar or Martian outpost, spend limited training credits on real NASA-documented technology gaps, and discover which mission systems still carry unresolved dependencies — with every engineering relationship traceable to NASA Moon-to-Mars architecture evidence.**

## Challenge fit

The 2026 challenge asks teams to build an interactive game or app that lets students run a lunar or Martian outpost while balancing competing engineering demands such as life support, radiation shielding, power, and food production so they can experience the decisions that shape mission outcomes.

Our response is a student-facing training layer built on top of the Moon→Mars Decision Atlas and NASA's official 2025 Architecture Concept Review products.

The competition experience is intentionally simple:

```text
Choose lunar or Mars outpost
        ↓
Receive limited training credits
        ↓
Choose which NASA technology gaps to address
        ↓
Run mission debrief
        ↓
See which architecture nodes are clear vs still exposed
        ↓
Inspect the remaining NASA technology gaps
        ↓
Open Decision Atlas / 3D context / NASA source evidence
```

## What is real vs what is game mechanics

### NASA-backed evidence

- technology-gap IDs and titles;
- priority ranking where present in the NASA source;
- campaign-segment mappings;
- sub-architecture mappings;
- residual gap relationships derived from the loaded graph;
- source workbook, sheet, row, URL, and SHA-256 provenance;
- Moon-to-Mars Architecture Revision C / document ID 20250010956.

### Explicit training mechanics

- 10 training credits;
- the credit cost assigned to each decision;
- the selected classroom scenario;
- the assumption that a selected technology gap is “addressed” for that training run.

The trainer does **not** convert these game mechanics into a NASA readiness percentage, survival probability, mission-success probability, or engineering sufficiency claim.

## Why the architecture matters

A student can choose to address lunar dust, long-duration darkness, communications, surface mobility, power, habitat systems, Mars entry/descent/landing, food and nutrition, transportation, ascent, and other mission demands.

After the student makes choices, the trainer removes only those selected gap nodes from the loaded NASA graph. It then asks a deeper question:

> **What still touches the same mission systems?**

Green architecture nodes have no other loaded technology-gap mapping after the selected training assumptions. Amber nodes still carry other NASA technology gaps.

This turns a simple resource-allocation game into a systems-thinking lesson: solving one engineering problem does not automatically make an outpost or mission ready.

## Competition-facing product architecture

### 1. Mission Trainer — `trainer.html`
The public front door. Students choose a lunar or Martian outpost, spend limited training credits, and run a debrief.

### 2. Decision Atlas — `index.html`
The evidence engine. It supports:

- Gap → Architecture
- Architecture → Gaps
- Compare Gaps
- Residual Dependency Analysis
- source provenance

### 3. 3D Mission Context — `navigator.html`
Places a selected technology gap in an illustrative Moon-to-Mars mission locus while keeping NASA architecture relationships separate from the 3D visualization.

## NASA data/resources

Primary evidence layer:

- NASA Moon to Mars Architecture Definition Document — Revision C
- NASA Technical Reports Server document ID **20250010956**
- 2025 Architecture Concept Review products
- NASA Lunar Objective Decomposition XLSX
- NASA Mars Objective Decomposition XLSX
- NASA Architecture-Driven Technology Gaps XLSX
- NASA Architecture-Driven Data Gaps XLSX

The automated ingestion pipeline discovers NASA's official XLSX products, downloads them, records SHA-256 hashes, normalizes the rows, validates the result, and commits the generated dataset only after validation passes.

The current official sync contains **57 technology gaps**, **19 normalized data gaps**, **10,871 lunar objective rows**, and **4,094 Mars objective rows**.

## Scientific and engineering guardrails

- no invented mission-readiness percentage;
- no fabricated survival or mission-success probability;
- no inferred graph edge when a relationship is absent from the loaded NASA data;
- no claim that broad graph reach equals higher strategic importance;
- no claim that selecting a training investment means NASA has solved that gap;
- no claim that closing one gap makes a mission segment ready;
- 3D geometry is illustrative and labeled separately from NASA traceability;
- training-credit values are clearly identified as fictional educational mechanics.

---

# 30-second judge demo

| Time | Visual | Voiceover / caption |
|---|---|---|
| 0–4s | Public root opens Moon→Mars Mission Trainer | “Real missions are systems of trade-offs. What should a young mission commander solve first?” |
| 4–8s | Choose **Lunar South Pole Outpost** | “Pick a lunar or Martian outpost.” |
| 8–14s | Select Dust + Shadow + Communications using limited credits | “You cannot fund everything. Each card is anchored to a NASA-documented technology gap.” |
| 14–20s | Run Mission Debrief | “The trainer removes only the gaps you assumed were addressed and shows what still touches the same systems.” |
| 20–25s | Green/amber architecture cards appear | “Green means no other loaded gap mapping remains. Amber means the system still carries other NASA technology gaps.” |
| 25–30s | Click Decision Atlas / 3D Context / NASA Source | “Then trace the lesson from game → architecture → 3D mission context → NASA evidence.” |

### Closing line

**Moon→Mars Mission Trainer — a student game on the surface, NASA systems engineering underneath.**

---

# 2-minute live demo

1. Open the public root and state the challenge in one sentence.
2. Choose **Lunar South Pole Outpost**.
3. Explain that the 10 credits are fictional training mechanics, not NASA risk scores.
4. Select three investments such as Dust, Extended Darkness, and Communications.
5. Point out the NASA technology-gap anchor shown on each card.
6. Run the mission debrief.
7. Explain green vs amber architecture nodes.
8. Open an amber node's remaining-gap context through the Decision Atlas.
9. Open one selected gap in 3D mission context.
10. Open the NASA source/provenance and show workbook, sheet, row, and hash.
11. Close on the scientific guardrail: one solved gap does not imply mission readiness.

## Final competition gates

- [x] Official 2026 challenge selected: **Build a Junior Astronaut Mission Trainer**.
- [x] Public competition front door created.
- [x] Official NASA XLSX sync deployed.
- [x] Game mechanics separated from NASA-derived evidence.
- [x] Mission debrief uses deterministic residual graph analysis.
- [x] Trainer → Decision Atlas → 3D → evidence paths exist.
- [ ] Test every competition-facing interaction in a clean browser after deployment.
- [ ] Record final 30-second demo from the deployed build.
- [ ] Record final 2-minute live-demo backup.
- [ ] Add final team profile and any collaborators before submission.

## Team and attribution

Built by **Oluwafemi Idiakhoa** for the NASA Space Apps Challenge 2026 preparation cycle.

Core technologies: NASA public Moon-to-Mars architecture data · HTML/CSS/JavaScript · Three.js · Python data normalization/validation · GitHub Actions · Vercel.

**Independent educational/research prototype. Not an official NASA product or flight-planning system.**
