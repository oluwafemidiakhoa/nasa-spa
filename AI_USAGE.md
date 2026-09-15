# AI Usage Disclosure Log

Maintain this file during NASA Space Apps development and update it before submission.

NASA Space Apps submission guidance requires teams to clearly identify where AI tools were used. This repository uses AI as an engineering/research assistant, but scientific outputs must remain traceable to source data, deterministic calculations, documented models, or explicitly labeled simulations.

## Current disclosure

| Area | AI use | Human/scientific verification |
|---|---|---|
| Software development | AI assistants have contributed to code generation, debugging, refactoring, documentation, and interface copy in this repository. | Code is reviewed through repository diffs, runtime/build checks where available, source inspection, and scientific validation appropriate to the feature. |
| Scientific explanations | AI assistance may be used to draft plain-language explanations. | Claims should be checked against cited NASA/NOAA/peer-reviewed sources before competition submission. |
| Scientific calculations | Generative AI must not be the authoritative source of numeric scientific results. | Numeric outputs should come from named datasets, deterministic code, or documented models with units/assumptions. |
| Synthetic educational visuals | Some interactive demonstrations may use generated/synthetic data to teach a method. | Synthetic content is labeled as simulation/schematic and must not be represented as NASA observation data. |

## Hackathon log template

Add one row for each material use during the event.

| Date/time | Tool/model | Files/content affected | Purpose | Verified by | Notes |
|---|---|---|---|---|---|
| | | | | | |

## Media checklist

Before submission:

- [ ] Identify any AI-generated or AI-modified images.
- [ ] Apply any watermark/disclosure required by the current NASA Space Apps rules.
- [ ] Identify AI-generated video/audio and disclose it in descriptive text/metadata as required.
- [ ] List external code, datasets, text, images, and other resources in the submission fields.
- [ ] Confirm no NASA branding or mission identity is altered or used in a way that implies NASA endorsement.

## Scientific integrity rule

For every important number shown to a judge, the team should be able to answer:

1. Where did this value come from?
2. Is it measured, computed, inferred, or simulated?
3. What units does it use?
4. What assumptions affect it?
5. What uncertainty or limitation applies?
6. Can the judge reach the source or reproduce the calculation?
