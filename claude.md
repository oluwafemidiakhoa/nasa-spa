
# Helio→Earth “Emergence Forecaster” (Claude Edition)
*A novel, multimodal, structured-output space-weather oracle built on NASA’s free APIs and Anthropic Claude.*

> **Pitch in one line:** Fuse NASA DONKI (solar events), EPIC Earth imagery, and GIBS time-layered tiles. Ask Claude to produce a **typed, cited forecast**: predicted CME arrival window, risks (aurora, comms, GNSS), confidence, and the evidence IDs and timestamps that justify it.

---

## Why this stands out
- **Novelty:** Goes beyond listing events; it composes **causal, evidence-linked forecasts** you can automate.
- **Multimodal reasoning:** Mixes tabular events + image/context (EPIC frames, GIBS tiles).
- **Structured outputs:** Uses **Anthropic’s `json_schema` response formatting** for strict, parseable JSON.
- **Public resonance:** Auroras/space-weather risk demos create instant engagement.

---

## NASA data you’ll use
- **DONKI** (Space Weather Database Of Notifications, Knowledge, Information): CMEs, flares, solar energetic particles, geomagnetic storms.  
  `https://api.nasa.gov/DONKI/<ROUTE>?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&api_key=...`
- **EPIC** (DSCOVR Earth imagery): Natural-color frames by date.  
  `https://api.nasa.gov/EPIC/api/natural/date/YYYY-MM-DD?api_key=...`
- **GIBS** (Global Imagery Browse Services): Time-parameterized map tiles for your web viewer.  
  WMTS template (example):  
  `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{TIME}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`

> You’ll need a free `api.nasa.gov` key. EPIC responses include image metadata and endpoints for JPG/PNG. GIBS is public and time-parameterized — use the **`TIME`** in your map layer URL to match forecast scenes.

---

## Project structure
```
helio-forecaster/
├─ README.md
├─ .env
├─ backend/
│  ├─ nasa_client.py         # DONKI, EPIC fetchers
│  ├─ schema.py              # JSON schema(s) for Claude typed output
│  ├─ claude_client.py       # Anthropic Messages API wrapper
│  ├─ forecaster.py          # Orchestration: fetch → prompt → parse
│  └─ demo.py                # Minimal runnable demo
└─ web/
   ├─ nextjs/                # Optional viewer using GIBS tiles
   └─ public/
```

---

## Environment variables (`.env`)
```
NASA_API_KEY=your_nasa_key
ANTHROPIC_API_KEY=your_anthropic_key
```

---

## Python dependencies
```bash
pip install anthropic python-dotenv requests pydantic
```

---

## `backend/schema.py` — Typed JSON schemas for strict output
> Claude will be constrained to these shapes via `response_format={"type":"json_schema", ... , "strict": true}`.

```python
from pydantic import BaseModel, Field, HttpUrl, conlist
from typing import List, Literal, Optional
from datetime import datetime

EventKind = Literal["CME", "FLARE", "SEP", "GEO_STORM"]

class Evidence(BaseModel):
    donki_ids: List[str] = Field(..., description="Relevant DONKI IDs used by the analysis")
    epic_frames: List[str] = Field(..., description="ISO timestamps (UTC) or EPIC identifiers used as visual evidence")
    gibs_layers: List[str] = Field(..., description="Layer names used (e.g., AURORA proxy, clouds)")

class Forecast(BaseModel):
    event: EventKind
    solar_timestamp: str = Field(..., description="UTC time of the initiating solar event if applicable (ISO 8601)")
    predicted_arrival_window_utc: conlist(str, min_items=2, max_items=2)
    risk_summary: str
    impacts: List[str] = Field(..., description="List of affected domains, e.g., 'aurora_midlat', 'HF_comms', 'GNSS_jitter'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: Evidence

class ForecastBundle(BaseModel):
    """Allow multiple forecasts in one response."""
    forecasts: List[Forecast]
```

To pass this to Claude, you’ll export a **JSON Schema** from Pydantic at runtime (or copy a hand-written schema).

---

## `backend/nasa_client.py` — Minimal NASA fetchers
```python
import os, datetime as dt, requests
from typing import List, Dict, Any

NASA_KEY = os.getenv("NASA_API_KEY")

def fetch_donki_cmes(days_back: int = 3) -> List[Dict[str, Any]]:
    end = dt.date.today()
    start = end - dt.timedelta(days=days_back)
    url = "https://api.nasa.gov/DONKI/CME"
    r = requests.get(url, params={"startDate": start.isoformat(), "endDate": end.isoformat(), "api_key": NASA_KEY})
    r.raise_for_status()
    return r.json()

def fetch_donki_flares(days_back: int = 3) -> List[Dict[str, Any]]:
    end = dt.date.today()
    start = end - dt.timedelta(days=days_back)
    url = "https://api.nasa.gov/DONKI/FLR"
    r = requests.get(url, params={"startDate": start.isoformat(), "endDate": end.isoformat(), "api_key": NASA_KEY})
    r.raise_for_status()
    return r.json()

def fetch_epic_date(date_iso: str) -> List[Dict[str, Any]]:
    """EPIC list for a given date (UTC)."""
    url = f"https://api.nasa.gov/EPIC/api/natural/date/{date_iso}"
    r = requests.get(url, params={"api_key": NASA_KEY})
    r.raise_for_status()
    return r.json()

def gibs_tile_url(time_iso: str) -> str:
    """Return a GIBS WMTS template with TIME filled for convenience."""
    return (
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        "VIIRS_SNPP_CorrectedReflectance_TrueColor/default/"
        f"{time_iso}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
    )
```

---

## `backend/claude_client.py` — Anthropic wrapper with strict JSON
```python
import os, json
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Type, Any, Dict

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def parse_with_schema(self, system: str, user_blocks: list, schema: Dict[str, Any], max_tokens: int = 1200):
        # response_format: json_schema with strict mode
        resp = self.client.messages.create(
            model="claude-3-7-sonnet-2025-08-xx",  # pick latest Sonnet/Opus with vision+structured JSON
            system=system,
            max_output_tokens=max_tokens,
            messages=[{"role": "user", "content": user_blocks}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ForecastBundle",
                    "schema": schema,
                    "strict": True
                }
            }
        )
        # content is a list of blocks; first text block contains the JSON per response_format
        return resp.content[0].text
```

> **Note:** Replace the model with the latest Claude that supports images + JSON schema. Keep `max_output_tokens` conservative to avoid truncation.

---

## `backend/forecaster.py` — Orchestration
```python
import json
from typing import Dict, Any, List
from pydantic import TypeAdapter
from schema import ForecastBundle
from nasa_client import fetch_donki_cmes, fetch_donki_flares, fetch_epic_date, gibs_tile_url
from claude_client import ClaudeClient

SYSTEM = """You are a space-weather analyst. Use DONKI solar events and Earth imagery context to forecast potential Earth-side impacts.
Return only valid JSON following the provided schema. Link claims to specific DONKI IDs and imagery timestamps.
If uncertainty is high, widen the arrival window and reflect lower confidence. Be concise but specific.
"""

PROMPT_HINTS = """Tasks:
1) Review recent CMEs/flares. Identify which are Earth-directed or likely geo-effective.
2) Propose a predicted arrival window (UTC) for notable events.
3) Summarize risks (aurora reach, HF comms degradation, GNSS jitter) and provide confidence in [0,1].
4) Cite evidence: DONKI IDs; EPIC frames (timestamps) and any GIBS TIME used.
Rules:
- Provide 0–3 forecasts maximum.
- If no meaningful impact expected, return an empty list for forecasts.
- Never hallucinate IDs; only cite given inputs.
"""

def build_user_blocks(donki_cmes, donki_flares, epic_samples: List[Dict[str, Any]], gibs_time_iso: str) -> List[Dict[str, Any]]:
    blocks = [
        {"type": "text", "text": PROMPT_HINTS},
        {"type": "text", "text": "DONKI_CME_SAMPLE:\n" + json.dumps(donki_cmes[:5], ensure_ascii=False) },
        {"type": "text", "text": "DONKI_FLARE_SAMPLE:\n" + json.dumps(donki_flares[:5], ensure_ascii=False) },
        {"type": "text", "text": "EPIC_SAMPLES:\n" + json.dumps(epic_samples[:3], ensure_ascii=False) },
        {"type": "text", "text": "GIBS_TIME_URL:\n" + gibs_tile_url(gibs_time_iso) }
    ]
    return blocks

def run_forecast(days_back=3, epic_date_iso=None) -> ForecastBundle:
    client = ClaudeClient()
    cmes = fetch_donki_cmes(days_back=days_back)
    flares = fetch_donki_flares(days_back=days_back)
    # EPIC by date (use today if none)
    import datetime as dt
    epic_date_iso = epic_date_iso or dt.date.today().isoformat()
    epic_list = fetch_epic_date(epic_date_iso)

    # Build user content blocks
    blocks = build_user_blocks(cmes, flares, epic_list, epic_date_iso)

    # Produce JSON schema from Pydantic
    schema = TypeAdapter(ForecastBundle).json_schema()

    # Call Claude
    raw = client.parse_with_schema(system=SYSTEM, user_blocks=blocks, schema=schema)
    # Validate round-trip via Pydantic
    bundle = ForecastBundle.model_validate_json(raw)
    return bundle
```

---

## `backend/demo.py` — Minimal runner
```python
from forecaster import run_forecast

if __name__ == "__main__":
    bundle = run_forecast(days_back=3)
    print(bundle.model_dump_json(indent=2))
```

---

## Front-end viewer (optional, Next.js)
- Use **MapLibre GL** or your favorite WebGL map.
- Add a WMTS source using the **GIBS** URL template with the `TIME` matching your forecast bundle.
- List Claude’s `forecasts` in a side panel; on click, set the map `TIME` and fly to a region of interest (if you include lat/lon products later).

Pseudo-config:
```ts
const gibsUrl = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{TIME}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg";

// Replace {TIME} with e.g., "2025-09-20" for that day's tiles
```

---

## Prompting tips
- Keep **`PROMPT_HINTS`** short and rule-like. Ask for **0–3 forecasts** to avoid verbosity.
- Provide **only small slices** of DONKI/EPIC as input to keep token usage sane; include IDs/timestamps so Claude can cite.
- Consider adding **thumbnail URLs** for EPIC frames (Claude can “use” the links as context even if not fetching).

---

## Hardening & extensions
- **Backfill physics**: integrate basic CME speed→arrival estimation (Drag-Based Model approximations) as a “calibration” prior alongside Claude’s narrative.
- **Multi-source**: add solar wind (e.g., DSCOVR real-time) if you later expand beyond NASA-free endpoints.
- **Rate limits & caching**: cache recent DONKI/EPIC responses by date; rate-limit fetchers.
- **Alerts**: subscribe users to arrival-window notifications (cron/Cloud scheduler).

---

## Submission checklist
- ✅ Working demo (`demo.py`) prints valid JSON matching the schema.
- ✅ Screenshots/GIF of the GIBS viewer with TIME set to evidence dates.
- ✅ README that explains evidence traceability (DONKI IDs, EPIC timestamps, GIBS TIME).
- ✅ Notes on uncertainty handling and ethical use (no “guaranteed” impact claims).

---

## License
MIT for your app. NASA content is typically public domain; check per-dataset terms and attribute appropriately.

---

### FAQ
**Q: Why Claude instead of a traditional model?**  
A: We want rapid cross-modal synthesis + **strict, parseable JSON** for downstream automation without training a custom model.

**Q: What if there are no significant events?**  
A: The schema supports returning an empty `forecasts: []`. That’s still a valid, valuable outcome.

**Q: Can I add images directly to messages?**  
A: Yes — pass EPIC thumbnails as `image` blocks or as URLs in text blocks; keep payload size modest.

---

Happy building — and enjoy the auroras! 🌌
