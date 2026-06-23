# Winning Strategy

## Strongest Challenge Fit

**Best fit:** `Space Weather / Earth Impact` or `Best Use of NASA Open Data`.

This project should not read like a generic dashboard. The winning version is a **solar storm readiness brief** that helps aviation and satellite operators understand whether current Sun-Earth conditions merit caution.

The sharp mission is: **turn live NASA and NOAA space weather data into an operationally useful, human-readable readiness signal.**

That gives judges a clean combination of:
- NASA/open data usage
- a credible scientific foundation
- a focused real-world mission
- a demo that feels useful, not decorative

## Problem

NASA and NOAA publish excellent space weather data, but mission teams still have to stitch together CMEs, flares, Kp values, solar wind speed, and storm notices before they can answer a simple operational question:

**"Do we need to pay attention right now?"**

For pilots, dispatch teams, satellite operators, and communications planners, raw feeds are informative but too fragmented to use quickly in a briefing.

## Target Users

- Aviation and flight operations teams
- Satellite mission operators
- Space weather learners and teachers
- Hackathon judges looking for a credible, focused demo

## Product Concept

**Solar Storyline**: a solar storm readiness brief for aviation and satellite operations.

The app should answer three questions immediately:
- What happened on the Sun recently?
- What is the current near-Earth context?
- How cautious should this user be right now?

The winning angle is not prediction accuracy alone. It is **operational translation**: turning complex science into a concise readiness signal with evidence attached.

## Datasets and APIs

Use a small set of trustworthy public sources:

- NASA DONKI CME endpoint
- NASA DONKI FLR endpoint
- NASA DONKI SEP endpoint
- NASA DONKI GST endpoint
- NASA EPIC recent Earth imagery
- NOAA SWPC planetary K index
- NOAA SWPC solar wind plasma feed
- NOAA SWPC solar wind magnetic field feed

Optional enrichments if time allows:
- NASA GIBS imagery layers
- Additional NOAA SWPC advisories or forecast products

## Architecture

Keep the implementation small and reliable.

### Frontend

- Next.js page for the main experience
- Single-screen briefing layout
- Role selector focused on `Pilot`, `Satellite Ops`, and `Aurora Watch`
- Readiness badge or status band
- Metric cards for the live solar snapshot
- Timeline of recent events
- Evidence/source panel with links and timestamps
- Loading, partial-data, and fallback states

### Data Layer

- One adapter that fetches NASA and NOAA feeds
- Normalize each API into a single readiness snapshot
- Convert the snapshot into:
  - readiness level
  - user-specific operational guidance
  - short evidence bullets
  - source health metadata

### Reliability

- If one or more feeds fail, show partial data instead of a blank screen
- If all feeds fail, show a clearly labeled demo fallback state
- Preserve scientific honesty with an explicit caveat that this is an educational briefing, not an official operational forecast

## Demo Flow

The demo should be short, visual, and scripted.

1. Open the app on the main briefing screen.
2. Show the current readiness status.
3. Select `Pilot` or `Satellite Ops`.
4. Show how the operational guidance changes.
5. Highlight the evidence panel to prove the brief comes from real NASA and NOAA data.
6. Show the timeline of recent solar activity.
7. End on the caveat and explain that the app is a decision-support briefing, not a forecast engine.

## Judging Criteria Alignment

### Impact

- Solves a real decision-support problem
- Makes technical science usable in a briefing context
- Can be used in classrooms, outreach, and hackathon judging

### Creativity

- Uses the same data that scientists use, but presents it as a readiness brief
- Converts raw telemetry into a mission-oriented narrative, not just charts

### Use of NASA/Open Data

- NASA DONKI and EPIC are central to the product
- NOAA SWPC feeds provide scientific context and credibility
- Source links remain visible in the UI

### Scientific Credibility

- Uses real agency data
- Clearly labels uncertainty and fallback behavior
- Avoids overclaiming forecasts or operational advice

### Technical Execution

- Focused scope
- Small surface area
- Real data ingestion with graceful failure states
- Clean UX and polished visuals

### Storytelling / Demo Quality

- The user can understand the app in seconds
- The story has a beginning, middle, and end
- The demo shows both the science and the operational relevance

## 48-Hour Execution Plan

### Hours 0-4

- Lock the concept and scope
- Confirm the challenge fit
- Choose the exact data sources
- Define the readiness snapshot data model

### Hours 4-10

- Build the data adapter
- Fetch and normalize NASA DONKI, EPIC, and NOAA feeds
- Add fallback handling and source health tracking

### Hours 10-18

- Build the main briefing UI
- Add role selector
- Add readiness status, metrics, timeline, and evidence panel

### Hours 18-24

- Add loading, partial, and error states
- Add clear scientific caveat
- Polish layout, spacing, and responsiveness

### Hours 24-32

- Improve the visual language
- Tighten copy for judges and demo viewers
- Verify the page against the live data flow

### Hours 32-40

- Write the README submission narrative
- Prepare the demo script
- Test the app with live and fallback conditions

### Hours 40-48

- Fix bugs
- Do final build and type checks
- Capture screenshots or a short demo video if needed
- Submit with a concise story, strong data references, and a credible scientific disclaimer

## Winning Thesis

This project wins by being:

- scientifically grounded
- visually polished
- easy to understand
- demoable in under two minutes
- clearly tied to NASA open data
- focused on one operational mission

The key is to avoid building a generic space dashboard. Build a **solar storm readiness brief** that turns science into a concise action signal.
