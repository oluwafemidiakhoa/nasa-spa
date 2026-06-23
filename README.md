# 🚀 Artemis Navigator — Moon to Mars Mission Platform

**A NASA Space Apps Challenge 2026 entry.**

🔗 **Live demo:** [nasa-spa.vercel.app](https://nasa-spa.vercel.app) · **Platform launcher:** [nasa-spa.vercel.app/hub](https://nasa-spa.vercel.app/hub)

Artemis Navigator turns NASA's open data and modern AI into an interactive Moon-to-Mars mission console: a 3D trajectory you can fly, live space-weather context, and an AI mission advisor you can question in plain language. It is built to make the science of deep-space navigation — orbital mechanics, lunar staging, Mars transfer windows, and radiation hazards — understandable to students, communicators, and judges alike.

The flagship experience is a single, dependency-light HTML page ([`index.html`](index.html)) that runs entirely in the browser. The repository also includes a polished Next.js companion app (**Solar Storyline**) and a collection of supporting space-weather dashboards.

---

## ✨ Flagship: Artemis Navigator (`index.html`)

Open [`index.html`](index.html) in any modern browser — no build step required.

### What it does

- **3D trajectory visualization** — a [Three.js](https://threejs.org/) (r128) scene renders the Earth–Moon–Mars corridor and animates the spacecraft along its transfer path.
- **Orbital mechanics, live** — computes orbit altitude and orbital period from adjustable mission parameters so users can see how geometry drives the trajectory.
- **Moon-to-Mars mission phases** — walks through Lunar Orbit, the Lunar Gateway, Lunar Surface Ops, Mars Approach, Mars Orbital Insertion, and the Mars Prep Hub.
- **Story Mode** — a guided, narrative walkthrough of the mission for outreach and demos.
- **Live NASA data** — pulls real space-weather and imagery context from NASA's open APIs (see below) so the mission environment reflects current solar conditions.

### 🤖 AI Mission Advisor — four providers, bring-your-own-key

Ask mission-briefing questions in natural language and get answers from the AI engine of your choice. Keys are entered in the UI and used **client-side only** — they are never committed or sent anywhere except directly to the chosen provider's API.

| Provider | Model | Endpoint |
|----------|-------|----------|
| **Anthropic** | Claude | `api.anthropic.com/v1/messages` |
| **OpenAI** | GPT-4o | `api.openai.com/v1/chat/completions` |
| **DeepSeek** | DeepSeek | `api.deepseek.com/v1/chat/completions` |
| **Google** | Gemini | `generativelanguage.googleapis.com` |

Get a key from the provider you prefer:
[Anthropic](https://console.anthropic.com) ·
[OpenAI](https://platform.openai.com/api-keys) ·
[DeepSeek](https://platform.deepseek.com) ·
Google AI Studio.

> ⚠️ **Security:** API keys are billable secrets. Paste them only into the running app; do not commit them. Rotate any key that has been shared.

---

## 🌌 Companion app: Solar Storyline (`web/nextjs`)

A focused Next.js MVP that turns live space-weather data into **role-based human stories**. Instead of asking people to interpret raw CME, flare, Kp, and solar-wind feeds, it explains what current Sun–Earth conditions could mean for a pilot, satellite operator, grid operator, astronaut, aurora chaser, or student.

Highlights:
- Earth-impact-weighted readiness score (measured Kp/Bz/solar wind/storms drive the level; CMEs count only when geometrically Earth-directed).
- Evidence panel with DONKI event IDs, timestamps, and source links.
- Live / partial / fallback data states with explicit feed-health reporting.

### Run it locally

```bash
cd web/nextjs
npm install
npm run dev
# open http://localhost:3000
```

Optional — for higher NASA API rate limits, create `web/nextjs/.env.local`:

```bash
NEXT_PUBLIC_NASA_API_KEY=your_nasa_api_key
```

Without a key the app falls back to NASA's rate-limited `DEMO_KEY`. Get a free key at [api.nasa.gov](https://api.nasa.gov/).

### Build checks

```bash
cd web/nextjs
npm run type-check
npm run build
```

---

## 🛰️ Supporting dashboards

A set of standalone HTML visualizations live at the repository root (open any directly in a browser):

- `dashboard_hub.html` — space-weather dashboard hub
- `3d_solar_system.html`, `working_3d_solar_system.html`, `spectacular_3d_space_weather.html` — 3D solar-system and space-weather scenes
- `iss_tracker.html` — ISS tracking
- `aurora_alerts.html` — aurora visibility alerts
- `space_weather_chatbot.html`, `space_weather_research_center.html`, `space_explorers_academy.html` — educational and research views

These are earlier prototypes and exploratory demos; the **Artemis Navigator** (`index.html`) and **Solar Storyline** (`web/nextjs`) are the maintained submission pieces.

---

## 📡 NASA & open data used

- **NASA DONKI** — CME, FLR (solar flare), and GST (geomagnetic storm) notifications
- **NASA APOD** — Astronomy Picture of the Day
- **NASA EPIC** — recent natural-color Earth imagery (Solar Storyline)
- **NOAA SWPC** — planetary K index, solar-wind plasma, and magnetic-field feeds (Solar Storyline)

---

## 🧰 Tech stack

- **Artemis Navigator:** vanilla HTML/CSS/JS + Three.js (r128), fetched from CDN; multi-provider AI integration via `fetch`.
- **Solar Storyline:** Next.js 14, React 18, TypeScript, Tailwind CSS.
- **Data:** direct browser calls to NASA and NOAA public APIs.

---

## 🏆 Why it fits NASA Space Apps

- **Impact:** makes deep-space mission planning and space-weather risk legible to a general audience.
- **Creativity:** combines a flyable 3D trajectory with a conversational, multi-model AI advisor.
- **Use of NASA/open data:** NASA DONKI and APOD drive the live mission environment; sources stay visible.
- **Scientific credibility:** real orbital-mechanics calculations, real agency data, and an explicit educational disclaimer.
- **Storytelling:** Story Mode gives the mission a clear beginning, middle, and end.

---

## ⚠️ Scientific caveat

This project is an educational NASA Space Apps prototype. It uses NASA and NOAA open data to explain space mission and space-weather context, but it is **not** an official operational forecast or flight-planning tool. Operational decisions should rely on NOAA Space Weather Prediction Center products, NASA mission systems, and established mission procedures.

---

*Built for the NASA Space Apps Challenge 2026.*
