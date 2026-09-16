# NASA Space Apps Hackathon Readiness Playbook

This repository is a **pre-existing open space-science research prototype**. It is not, by itself, a future NASA Space Apps Challenge submission.

The goal of this playbook is to preserve a clean boundary between work that existed before a hackathon and work created by the team during the official event window.

## 1. Competition integrity first

Before the event:

- Do not implement a solution to an official challenge.
- Do not pre-fill a future project submission with challenge-specific claims.
- Keep reusable infrastructure, research notes, validation utilities, UI components, and prior experiments clearly identified as pre-existing assets.
- Record the exact repository commit that exists immediately before the official start time.

During the event:

- Create a fresh challenge branch from the recorded baseline.
- Put the selected official challenge statement in the branch README.
- Build the challenge-specific solution only after the event opens.
- Keep a visible commit trail showing the work completed during the hackathon.
- Cite every external dataset, model, paper, image, library, and pre-existing code asset used.
- Disclose AI-assisted code, text, images, audio, or analysis exactly as required by the current competition rules.

After the event:

- Export a `git diff` from the baseline commit to the final submission commit.
- Preserve the final commit SHA in the project submission.
- Confirm the public demo and repository work without credentials or private access.

## 2. Judge-first design

Build the hackathon solution around the five recurring Space Apps judging dimensions:

### Impact

Answer in one sentence:

> Who has a real problem, and what becomes measurably easier, safer, faster, clearer, or more accessible because this project exists?

The UI should expose the impact in the first screen rather than requiring judges to explore the repository.

### Creativity

Do more than aggregate NASA feeds. A competitive project should introduce a new interaction, inference, scientific workflow, visualization, or decision-support capability that changes what a user can do with the data.

### Validity

Every scientific or predictive claim should have:

- a source;
- a method;
- an assumption;
- an uncertainty or limitation;
- and, where possible, a reproducible validation test.

Never label a simulation, heuristic, synthetic example, or model estimate as a direct NASA observation.

### Relevance

The final solution must answer the selected official challenge directly. Remove impressive features that do not help answer the challenge. A focused project is stronger than a large platform whose relationship to the prompt is unclear.

### Presentation

Design the demo before the final hours. The judge should understand the entire project in roughly this order:

1. problem;
2. NASA/partner data;
3. unique method;
4. live result;
5. scientific evidence/limitations;
6. human impact;
7. future extension.

## 3. Challenge-day repository structure

Create this only when the official event begins:

```text
hackathon/<year>-<challenge-slug>/
  README.md                 # exact challenge + solution summary
  DATA_SOURCES.md           # datasets, APIs, licenses, citations
  AI_DISCLOSURE.md          # AI tools and exactly how they were used
  VALIDATION.md              # tests, assumptions, uncertainty, limitations
  demo/                      # final judge-facing experience
  src/                       # challenge-specific implementation
  tests/                     # challenge-specific checks
```

Do not copy the whole legacy platform into the challenge folder. Import only the pre-existing components the team genuinely needs and list them in `PREEXISTING_ASSETS.md`.

## 4. Scientific evidence contract

For every important value shown to a judge, the implementation should be able to answer:

```text
What is this value?
Where did it come from?
When was the source updated?
Is it observed, derived, predicted, or simulated?
What assumptions were used?
What uncertainty or failure mode applies?
Can the result be reproduced?
```

A simple provenance object can be attached to derived results:

```json
{
  "status": "derived",
  "source": "NASA/partner dataset or cited paper",
  "observed_at": "ISO-8601 timestamp",
  "method": "named transformation/model",
  "assumptions": [],
  "uncertainty": "description or interval",
  "citation": "persistent source URL"
}
```

## 5. Minimum technical quality bar

Before submission, verify:

- No API secrets are committed.
- The demo works in a fresh browser session.
- The app has explicit loading, partial-data, stale-data, and failure states.
- Synthetic fallback data is visibly labeled.
- Live claims contain timestamps.
- Scientific calculations have unit tests or independent sanity checks.
- Numerical outputs show units.
- User-visible source links resolve.
- Accessibility includes keyboard navigation, readable contrast, semantic labels, and reduced-motion behavior where appropriate.
- Mobile layout does not hide the core demonstration.
- The demo can survive a temporary upstream API failure.

## 6. 48-hour execution discipline

### Opening block

- Select one official challenge.
- Read the prompt, constraints, provided datasets, and judging notes word-for-word.
- Write the one-sentence problem and one-sentence innovation.
- Record the baseline commit.
- Delete any feature from scope that does not directly answer the prompt.

### Build block

- Ingest one authoritative dataset correctly before adding more.
- Make one complete end-to-end user journey work.
- Add provenance and failure-state handling immediately.
- Validate the core scientific/technical claim before polishing secondary screens.

### Final block

- Freeze new features.
- Re-run validation and smoke tests.
- Capture the public demo.
- Verify citations and AI disclosures.
- Tighten the project page to the five judging criteria.
- Tag the final submission commit.

## 7. The standard for this repository

The existing platform should be treated as a library of prior research and reusable components, not as the future competition entry. The future entry should be smaller, challenge-specific, evidence-rich, and demonstrably created during the hackathon window.
