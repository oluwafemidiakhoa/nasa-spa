# Solar Storyline

Solar Storyline is a NASA Space Apps MVP that turns open space weather data into role-based human stories. Instead of asking judges or students to interpret raw CME, flare, Kp, and solar wind feeds, the app explains what the current Sun-Earth conditions could mean for a pilot, satellite operator, grid operator, astronaut, aurora chaser, or student.

This repository contains many earlier prototypes. The competition MVP is the Next.js app in `web/nextjs`.

## NASA Space Apps Submission

**Concept:** Space weather through human eyes.

**Core problem:** NASA and NOAA publish rich open data about solar activity, but most people cannot connect a CME, flare, geomagnetic storm, or Kp reading to real-world impacts.

**Solution:** Solar Storyline fetches public space weather feeds, summarizes current conditions, shows the evidence, and translates the same data into different role-specific stories.

**Audience:**
- Students and educators
- Science communicators
- Aurora observers
- Space Apps judges
- Public users who need an accessible explanation of space weather

## Open Data Used

The MVP uses public data sources directly from the browser:

- NASA DONKI CME endpoint
- NASA DONKI FLR endpoint
- NASA DONKI SEP endpoint
- NASA DONKI GST endpoint
- NASA EPIC recent Earth imagery
- NOAA SWPC planetary K index
- NOAA SWPC solar wind plasma
- NOAA SWPC solar wind magnetic field

The interface labels feed health and warns when it is using partial data or a fallback sample. The app is an educational prototype, not an official operational forecast.

## Demo Flow

1. Open the homepage.
2. Show the live/partial/fallback data badge.
3. Explain the activity score, confidence, and data caveats.
4. Select a role such as Pilot or Aurora Chaser.
5. Show how the same NASA/NOAA data becomes a human-centered story.
6. Open the evidence panel to show DONKI IDs, timestamps, and source links.
7. End with the scientific caveat: official decisions should use NOAA SWPC and mission procedures.

## Why It Can Win

**Impact:** Connects space weather to aviation, satellites, power grids, astronauts, education, and aurora viewing.

**Creativity:** Uses storytelling as the interface for scientific data.

**Use of NASA/open data:** Makes DONKI and EPIC visible in the product and keeps source evidence accessible.

**Scientific credibility:** Shows uncertainty, confidence, source health, timestamps, and an official-forecast disclaimer.

**Technical execution:** A focused, deployable Next.js MVP instead of a collection of disconnected demos.

**Storytelling quality:** The demo has a clear beginning, middle, and end: Sun event, Earth conditions, human impact.

## Local Development

```bash
cd web/nextjs
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

Optional environment variable:

```bash
NEXT_PUBLIC_NASA_API_KEY=your_nasa_api_key
```

If no key is provided, the app uses NASA's `DEMO_KEY`, which is rate-limited.

## Build Checks

```bash
cd web/nextjs
npm run type-check
npm run build
```

## Current Scope

Implemented:

- Single polished MVP homepage
- NASA/NOAA open data adapter
- Role-based impact stories
- Loading, error, partial-data, and fallback states
- Evidence panel with source links
- NASA Space Apps submission README

Not yet implemented:

- Full MapLibre/GIBS map layer
- Backend data cache
- Historical validation dashboard
- Alert subscriptions
- Production deployment hardening

## Scientific Caveat

Solar Storyline is an educational and storytelling prototype built for NASA Space Apps. It should not be used as an operational forecast. Official space weather alerts, warnings, and operational products should come from NOAA's Space Weather Prediction Center and relevant mission procedures.
