# Solar Storyline — Space Weather, Forecast and Understood

**NASA Space Apps Challenge 2026 — submission narrative & demo script.**

> ⚠️ Action for you: map this to the **exact official 2026 challenge** you enter
> (a Space Weather / "Do You Know Your Sun?" / heliophysics challenge is the best
> fit). Paste the relevant sections into the Space Apps project page and tighten
> the wording to that challenge's prompt.

---

## One line

**We turn live NASA and NOAA data into a real physics-based space-weather
forecast — and then into a decision a pilot, grid operator, or astronaut can act
on in seconds.**

## The problem

Space weather is a multi-billion-dollar operational risk: a single severe
geomagnetic storm can damage power grids, disrupt aviation and GPS, threaten
satellites, and endanger astronauts. NASA and NOAA publish excellent open data —
CMEs, flares, solar wind, Kp — but it arrives as **fragmented raw feeds**. Two
gaps remain:

1. **Forecasting:** raw event lists don't tell you *when* a CME hits Earth or
   *how strong* the storm will be.
2. **Translation:** even a good forecast is useless to a non-scientist unless it
   says what to *do*.

## What we built

An **end-to-end space-weather pipeline** that closes both gaps:

```
 NASA DONKI / NOAA SWPC  ──►  Physics forecast engine  ──►  Ensemble + uncertainty  ──►  Role-based decisions
 (CME, flare, solar wind)     (CME drag, Parker wind,        (model blend, confidence)     (pilot, grid, satellite,
                               Burton Dst)                                                  astronaut, aurora, student)
```

- **A real physics forecast engine** (Python): drag-based CME propagation,
  Parker solar-wind model, and a Burton-equation Dst / geomagnetic model.
- **Live ingestion** of NASA DONKI (CME/FLR/GST) and NOAA SWPC feeds, with
  historical storage, a scheduler, websocket streaming, and email alerts.
- **Role-based translation** (Solar Storyline) that converts the forecast into
  plain-language guidance for six audiences, with an Earth-impact readiness
  score that only escalates on *measured* near-Earth disturbance.
- **An interactive 3D mission layer** (Artemis Navigator) that puts the same
  open data into a Moon-to-Mars context with a multi-model AI advisor.
- **A unified platform hub** tying every module together at one URL.

## The science (this is our credibility — and it actually runs)

Every number below is produced by our models live, not hard-coded:

| Model | Input | Output (verified) |
|-------|-------|-------------------|
| **CME propagation** (drag-based) | 1500 km/s Earth-directed CME | **Earth arrival in ~28 h**, with velocity trajectory + confidence |
| **Geomagnetic response** (Burton Dst) | 700 km/s, 18 nT, 12 cm⁻³ solar wind | **Dst −470 nT → severe storm, NOAA G4+**, magnetopause at 7.2 Rₑ |
| **Solar wind** (Parker) | coronal temperature, distance | speed/density profile vs. heliocentric distance |

These are established heliophysics methods — the drag-based CME model, the Parker
solar-wind solution, and the Burton equation for ring-current injection/decay —
not invented relationships. We **label uncertainty and never present an
educational prototype as an official forecast.**

## How we use NASA & open data

- **NASA DONKI** — CME, solar flare (FLR), and geomagnetic storm (GST) feeds
- **NASA APOD / EPIC** — imagery context
- **NOAA SWPC** — planetary K index, solar-wind plasma & magnetic field
- Forecasts are driven *from* this live data; sources stay visible in the UI.

## Architecture

- **Backend:** Python physics models + FastAPI ensemble API, SQLite history,
  scheduler, websocket streaming, Dockerized (backend/frontend/nginx).
- **Frontend:** a static, dependency-light hub + the Artemis Navigator (Three.js
  3D, multi-model AI via a serverless proxy) + the Solar Storyline Next.js app.
- **Deploy:** live on Vercel with serverless proxies for AI and NASA data
  (server-side keys, nothing exposed in the browser).

## Why it wins (mapped to judging criteria)

- **Impact:** a real operational decision-support tool for aviation, power,
  satellites, human spaceflight, and education.
- **Creativity:** forecasting *and* human translation in one pipeline — not
  another dashboard.
- **Validity:** working physics models with verifiable outputs and explicit
  uncertainty; no overclaiming.
- **Use of data:** NASA DONKI + NOAA SWPC are the engine's fuel, end to end.
- **Storytelling:** the same storm becomes six different human stories.

## Impact / who it helps

Aviation & dispatch · power-grid operators · satellite mission teams · astronaut
safety · aurora chasers & the public · classrooms and science communicators.

---

## 🎬 30-second video script (shot-by-shot)

> Goal: a non-scientist understands the value in 30 seconds. No jargon. Live data
> on screen. End on impact.

| Time | Visual | Voiceover / caption |
|------|--------|---------------------|
| 0–4s | Sun → CME erupting (3D scene) | "Every day, the Sun fires storms at Earth." |
| 4–9s | Live NASA cards ticking: 51 CMEs, 4 flares | "NASA and NOAA publish the data — but it's raw and fragmented." |
| 9–16s | Forecast engine animates: CME → **arrival 28 h** → **Dst −470, G4+** | "Our engine runs real physics on it: when the storm hits, and how strong." |
| 16–23s | Role selector flips: Pilot → Grid → Astronaut, each guidance changing | "Then it tells *you* what to do — pilot, grid operator, astronaut." |
| 23–28s | Hub view, all modules, live badge | "Live data. Real forecasts. Real decisions." |
| 28–30s | Logo + URL: **nasa-spa.vercel.app** | "Solar Storyline. NASA Space Apps 2026." |

## 🧭 2-minute demo flow (for live judging)

1. Open the **hub** — "one platform, live NASA data."
2. Show the **live cards** (real CME/flare counts) — prove it's live.
3. Trigger a **forecast**: CME arrival time + Dst storm level + confidence.
4. Flip **roles** — same storm, different human decisions.
5. Open the **evidence/source panel** — DONKI IDs, timestamps, links.
6. Close on the **scientific caveat** — honesty as credibility.

## Roadmap

Validation dashboard vs. historical storms · alert subscriptions · GIBS/map
layer · ensemble uncertainty bands · model skill scoring against NOAA archives.

## Team & attribution

Built by Oluwafemi Idiakhoa · Texas, USA · NASA Space Apps Challenge 2026.
Powered by NASA Open APIs (DONKI · APOD · EPIC) · NOAA SWPC · Python physics
models · Three.js · multi-model AI.

*Educational prototype — not an official operational forecast. Operational
decisions should use NOAA SWPC products and mission-specific procedures.*
