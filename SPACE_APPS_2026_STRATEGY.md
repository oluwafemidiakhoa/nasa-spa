# NASA Space Apps 2026 — Competition Strategy

> Goal: make this repository a high-credibility foundation for a **single official 2026 challenge**, then submit only the challenge-relevant experience.
>
> Event date currently published by NASA Space Apps: **November 14–15, 2026**.

## The rule that matters most

For Global Judging, the final project must respond directly to an **official NASA Space Apps challenge** and use NASA data/resources. Do not submit the entire repository as a grab-bag of modules. The platform can remain broad internally, but the judged project must have one clear problem, one primary user, one challenge statement, and one memorable result.

## Judge-facing architecture

The repository now contains three reusable scientific capabilities:

1. **Mission reasoning** — Artemis Navigator (3D Moon-to-Mars trajectory + mission context).
2. **Predictive science** — Solar Storyline / physics-based space-weather forecasting.
3. **Discovery reasoning** — Solar System Fossil Lab (observation → detection → model comparison → uncertainty).

When the official challenge is selected, choose the one capability that best answers it and hide/de-emphasize unrelated modules in the submission experience.

## Five judging criteria: design targets

NASA Space Apps judging uses five criteria: **Impact, Creativity, Validity, Relevance, Presentation**.

### Impact

Submission must answer, in one sentence:

> Who can do something better because this exists?

Requirements:
- One primary audience, not six unrelated audiences.
- One measurable improvement: time saved, concept learned, hazard interpreted, object detected, decision explained, etc.
- A visible before/after user journey.

### Creativity

Do not lead with “AI chatbot.” Lead with an original interaction or scientific workflow.

Strong existing candidates:
- Shift-and-stack astronomy detection with transparent ML false-positive reasoning.
- Evidence-vs-model comparison that exposes contradictions instead of hiding them.
- Role-aware physics forecasts tied to real measurements and uncertainty.
- Interactive mission trade-space rather than a static 3D scene.

### Validity

Every quantitative feature must be one of:
- measured from a named NASA/partner dataset,
- computed by a documented model,
- inferred under a stated assumption,
- or clearly labeled simulation/demo data.

Required before submission:
- Source IDs/links visible in UI.
- Units everywhere.
- UTC timestamps on live observations.
- Assumptions visible.
- Uncertainty visible.
- Historical validation/backtest where prediction is involved.
- No synthetic point may be presented as an observed NASA measurement.

### Relevance

Create a `CHALLENGE_ALIGNMENT.md` immediately after selecting the official challenge with this exact structure:

| Official challenge requirement | Where our project satisfies it | Evidence |
|---|---|---|
| Requirement 1 | Feature / screen | NASA dataset / screenshot / test |
| Requirement 2 | Feature / screen | NASA dataset / screenshot / test |
| Requirement 3 | Feature / screen | NASA dataset / screenshot / test |

If a major feature cannot be mapped to a challenge requirement, it should not consume demo time.

### Presentation

The judge should understand the project without reading the repository.

30-second video target:
- **0–5 s:** the problem / surprising question.
- **5–12 s:** NASA data entering the product.
- **12–21 s:** the distinctive interaction or computation.
- **21–27 s:** the useful result and evidence/provenance.
- **27–30 s:** one-line future impact + project name.

No feature tour. Tell one story.

## Recommended technical standard

### Evidence object

Normalize important scientific claims to an internal object similar to:

```json
{
  "claim": "...",
  "value": 0,
  "unit": "...",
  "status": "measured|computed|inferred|simulated",
  "source": {
    "agency": "NASA",
    "dataset": "...",
    "id": "...",
    "url": "...",
    "observed_at": "..."
  },
  "method": "...",
  "assumptions": [],
  "uncertainty": null
}
```

This makes provenance a product feature rather than a footnote.

### AI disclosure

NASA Space Apps submission guidance requires teams to disclose where AI tools were used. Maintain `AI_USAGE.md` during the hackathon with:
- AI-assisted code/files,
- AI-generated images/video/audio,
- models/providers used,
- what humans verified,
- which scientific results do **not** come from generative AI.

AI-generated visual media should follow the current Space Apps disclosure/watermark requirements.

## Solar System Fossil Lab: scientific guardrails

The new TNO module is intentionally separated from the Moon-to-Mars mission flow.

It may be used as a competition centerpiece only when the selected official challenge directly supports planetary-science education, small-body science, scientific visualization, telescope data, or discovery workflows.

Guardrails:
- The shift-and-stack display is explicitly labeled a synthetic educational simulation.
- Hot/cold orbits are schematic, not the measured 27-object orbital catalog.
- Diameter slider states its normalization and albedo assumption.
- “Same size distribution” is avoided; the safer statement is that the discovery subsamples are **consistent with the same power-law slope within uncertainty**.
- NASA release and paper links are visible in-product.

## 48-hour hackathon operating plan

### Before event
- Keep the reusable platform healthy.
- Do not pre-build the exact final solution before the official challenge is chosen.
- Prepare adapters for NASA APIs/data, visualization components, provenance UI, testing, and deployment.

### Hour 0–2
- Select challenge based on strongest data/skill fit.
- Write one-sentence user problem.
- Fill `CHALLENGE_ALIGNMENT.md` before coding.

### Hour 2–8
- Build one end-to-end “golden path.”
- Use one real NASA dataset immediately.
- Make a result appear on screen with provenance.

### Hour 8–20
- Add the distinctive scientific interaction/model.
- Add uncertainty and failure/fallback states.
- Remove unrelated features.

### Hour 20–30
- Validate output against a known case or documented source.
- Add automated smoke tests.
- Test mobile and slow-network behavior.

### Hour 30–38
- Freeze features.
- Create demo story and screenshots.
- Write submission text directly against challenge requirements.

### Hour 38–44
- Record 30-second demo with English captions.
- Verify public URLs in private/incognito browser.
- Verify source links and AI disclosure.

### Hour 44–48
- Fix only blocking defects.
- Submit early; do not spend the deadline window adding features.

## What not to do

- Do not submit every module because it exists.
- Do not call a simulation “live data.”
- Do not use AI-generated scientific numbers without deterministic verification.
- Do not hide uncertainty.
- Do not spend the demo listing frameworks/providers.
- Do not claim NASA endorsement or present this as an official NASA product.
- Do not optimize primarily for visual spectacle while challenge relevance remains ambiguous.

## Competition positioning

If challenge fit supports it, the strongest conceptual positioning is:

> **An evidence-first scientific reasoning interface that turns NASA observations into an auditable path from data → model → contradiction → explanation → next test.**

That positioning differentiates the work from ordinary dashboards and ordinary AI chat interfaces while building directly on the repository's existing physics, visualization, and provenance strengths.
