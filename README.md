# 🌌 NASA Space Weather Forecaster

**Production-Ready Helio→Earth "Emergence Forecaster" with Full Automation**

A comprehensive, multimodal space weather monitoring and forecasting system built on NASA's APIs, Anthropic Claude AI, with automated monitoring, web dashboard, and real-time alerts.

## 🎯 Overview

This production-ready system combines NASA DONKI (solar events), EPIC Earth imagery, and GIBS time-layered tiles with Claude AI to provide **automated space weather monitoring** with:
- **Real-time forecasting** and alert generation
- **Interactive web dashboard** with live data visualization
- **Automated scheduling** with customizable intervals  
- **Multi-channel notifications** (email, SMS)
- **REST API** for third-party integrations
- **Complete evidence traceability** for all predictions

## 🚀 **IMPLEMENTED FEATURES**

### ✅ **Production Backend (FastAPI)**
- **REST API** with forecast, alert, and statistics endpoints
- **WebSocket** support for real-time updates
- **Database integration** (SQLite dev, PostgreSQL prod)
- **Automated monitoring** with configurable intervals
- **Flexible scheduling** system with cron support
- **Email & SMS notifications** via SMTP and Twilio

### ✅ **Interactive Web Dashboard (Next.js)**
- **Real-time forecast display** with confidence indicators
- **Live alert system** with severity-based styling
- **Connection status** and health monitoring
- **Responsive design** with space weather theme
- **Statistics dashboard** with accuracy metrics
- **Timeline view** of historical forecasts

### ✅ **Production Deployment**
- **Docker containerization** with multi-stage builds
- **Docker Compose** for development and production
- **Automated setup scripts** for easy deployment
- **Environment management** with comprehensive templates
- **Health checks** and monitoring integration

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** (recommended)
2. **NASA API Key** (free): Get from [api.nasa.gov](https://api.nasa.gov/)
3. **Anthropic API Key**: Get from [console.anthropic.com](https://console.anthropic.com/)

### ⚡ One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd NASA

# Run automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will:
- Check prerequisites
- Create environment configuration
- Build Docker images  
- Start all services
- Run health checks

### 🌐 Access Your Dashboard

After setup completes:
- **Web Dashboard**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Manual Setup (Alternative)

```bash
# 1. Configure environment
cp env.template .env
# Edit .env with your API keys

# 2. Start with Docker Compose
docker-compose up -d

# 3. Check service status
docker-compose ps
```

### Quick Test

```bash
# Test the basic forecasting
cd backend
python demo.py
```

### Programmatic Usage

```python
from backend.forecaster import run_forecast

# Simple forecast
result = run_forecast(days_back=3)

if result.forecasts:
    for forecast in result.forecasts:
        print(f"Event: {forecast.event}")
        print(f"Arrival: {forecast.predicted_arrival_window_utc}")
        print(f"Confidence: {forecast.confidence:.1%}")
        print(f"Impacts: {forecast.impacts}")
```

## 🏗️ System Architecture

### Production Stack
- **Backend**: FastAPI + Python 3.11
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS  
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Cache**: Redis (production)
- **AI**: Anthropic Claude Sonnet 3.5
- **Deployment**: Docker + Docker Compose

### 📁 Complete Project Structure

```
NASA/
├── README.md                    # This comprehensive guide
├── requirements.txt             # Python dependencies
├── env.template                # Environment configuration template
├── docker-compose.yml          # Development deployment
├── docker-compose.prod.yml     # Production deployment
├── Dockerfile.backend          # Backend container configuration
├── Dockerfile.frontend         # Frontend container configuration
├── 
├── backend/                    # 🐍 Python Backend Services
│   ├── api_server.py           # ⚡ FastAPI REST server with WebSocket
│   ├── database.py             # 🗄️ SQLAlchemy models & database management
│   ├── monitor.py              # 📡 Automated monitoring service
│   ├── scheduler.py            # ⏰ Flexible cron-based job scheduler
│   ├── notifications.py       # 📧 Email/SMS alert system
│   ├── forecaster.py           # 🧠 AI forecast orchestration
│   ├── schema.py               # 📋 Pydantic models for structured data
│   ├── nasa_client.py          # 🛰️ NASA API integration
│   ├── claude_client.py        # 🤖 Claude AI client with JSON schema
│   └── demo.py                 # 🎯 Standalone demo & testing
│
├── web/nextjs/                 # 🌐 Next.js Web Dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx       # 🏠 Main dashboard page
│   │   │   ├── _app.tsx        # ⚙️ App configuration with SWR
│   │   │   └── _document.tsx   # 📄 HTML document structure
│   │   ├── components/
│   │   │   ├── ForecastCard.tsx    # 🃏 Individual forecast display
│   │   │   ├── AlertBanner.tsx     # 🚨 Alert notification banner
│   │   │   ├── ConnectionStatus.tsx # 🔗 WebSocket status indicator
│   │   │   ├── StatsPanel.tsx      # 📊 Accuracy statistics
│   │   │   ├── TimelineView.tsx    # 📈 Historical forecast timeline
│   │   │   ├── MapView.tsx         # 🗺️ Earth visualization (GIBS)
│   │   │   └── Layout.tsx          # 🎨 App layout wrapper
│   │   ├── hooks/
│   │   │   ├── useForecasts.ts     # 🪝 Forecast data management
│   │   │   └── useWebSocket.ts     # 🔌 Real-time connection hook
│   │   ├── lib/
│   │   │   └── api.ts              # 🌐 API client with error handling
│   │   ├── types/
│   │   │   └── index.ts            # 🏷️ TypeScript type definitions
│   │   └── styles/
│   │       └── globals.css         # 🎨 Global styles & space theme
│   ├── package.json               # 📦 Node.js dependencies
│   ├── next.config.js             # ⚙️ Next.js configuration
│   ├── tailwind.config.js         # 🎨 Tailwind CSS configuration
│   └── tsconfig.json              # 📝 TypeScript configuration
│
└── scripts/
    └── setup.sh                   # 🚀 Automated deployment script
```

### 🔄 Service Communication Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   FastAPI API    │    │ NASA APIs       │
│                 │◄──►│   Server         │◄──►│ DONKI/EPIC/GIBS │
│ Next.js App     │    │ (Port 8000)      │    │                 │
│ (Port 3000)     │    └──────────────────┘    └─────────────────┘
└─────────────────┘           │                          │
         │                    │                          │
         │WebSocket           │                          ▼
         ▼                    ▼                ┌─────────────────┐
┌─────────────────┐    ┌──────────────────┐   │ Anthropic       │
│ Real-time       │    │ Background       │   │ Claude AI       │
│ Updates         │    │ Services         │◄─►│ API             │
└─────────────────┘    │                  │   └─────────────────┘
                       │ • Monitor        │
                       │ • Scheduler      │
                       │ • Notifications  │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Database         │
                       │ SQLite/PostgreSQL│
                       └──────────────────┘
```

## 🛠️ API Configuration

### Environment Variables (.env)

```bash
# NASA API Key - Get from https://api.nasa.gov/
NASA_API_KEY=your_nasa_api_key_here

# Anthropic API Key - Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### NASA Data Sources

- **DONKI** (Space Weather Database): CMEs, flares, solar energetic particles, geomagnetic storms
- **EPIC** (DSCOVR Earth imagery): Natural-color Earth frames by date
- **GIBS** (Global Imagery Browse Services): Time-parameterized map tiles

## 📈 Usage Examples

### Basic Forecast

```python
from backend.forecaster import run_forecast

# Get forecast for last 3 days of space weather
result = run_forecast(days_back=3)

if isinstance(result, ForecastBundle):
    print(f"Generated {len(result.forecasts)} forecasts")
    for forecast in result.forecasts:
        print(f"- {forecast.event}: {forecast.risk_summary}")
else:
    print(f"Error: {result.error}")
```

### Advanced Configuration

```python
from backend.forecaster import ForecastConfig, run_forecast_advanced

config = ForecastConfig(
    days_back=5,              # Look back 5 days
    max_events_per_source=10, # More events per source
    include_images=True,      # Include EPIC imagery analysis
    max_tokens=2000          # Extended analysis
)

result = run_forecast_advanced(config)
```

### JSON Output for Automation

```python
# Generate JSON for APIs/automation
result = run_forecast(days_back=2)
json_output = result.model_dump_json(indent=2)

# Save for external use
with open('forecast.json', 'w') as f:
    f.write(json_output)
```

## 📊 Output Schema

### ForecastBundle Structure

```json
{
  "forecasts": [
    {
      "event": "CME",
      "solar_timestamp": "2025-09-26T14:30:00Z",
      "predicted_arrival_window_utc": [
        "2025-09-28T06:00:00Z",
        "2025-09-29T18:00:00Z"
      ],
      "risk_summary": "Moderate geomagnetic storm expected...",
      "impacts": ["aurora_midlat", "HF_comms", "GNSS_jitter"],
      "confidence": 0.75,
      "evidence": {
        "donki_ids": ["CME-2025-09-26T14:30:00-CME-001"],
        "epic_frames": ["2025-09-26T14:30:00"],
        "gibs_layers": ["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
      }
    }
  ],
  "generated_at": "2025-09-26T20:15:30Z",
  "data_sources": ["NASA_DONKI", "NASA_EPIC", "NASA_GIBS"]
}
```

### Event Types

- **CME**: Coronal Mass Ejection
- **FLARE**: Solar Flare
- **SEP**: Solar Energetic Particle event
- **GEO_STORM**: Geomagnetic Storm

### Impact Types

- `aurora_midlat`: Aurora visible at mid-latitudes
- `aurora_highlat`: High-latitude aurora enhancement
- `HF_comms`: HF radio communication disruption
- `GNSS_jitter`: GPS/GNSS timing jitter
- `GNSS_outage`: GPS/GNSS service outage
- `satellite_drag`: Increased atmospheric drag on satellites
- `radiation_storm`: Radiation storm affecting aviation/satellites
- `power_grid`: Power grid vulnerability

## 🔧 Advanced Features

### Evidence Traceability

Every forecast includes complete evidence linking:

```python
# Access evidence for transparency
forecast = result.forecasts[0]
print("DONKI Event IDs:", forecast.evidence.donki_ids)
print("EPIC Timestamps:", forecast.evidence.epic_frames)
print("GIBS Layers:", forecast.evidence.gibs_layers)
```

### Custom Analysis Periods

```python
# Analyze specific date ranges
from datetime import date

result = run_forecast(
    days_back=7,
    epic_date_iso="2025-09-20"  # Specific EPIC date
)
```

### Error Handling

```python
from backend.schema import ForecastBundle, ForecastError

result = run_forecast()

if isinstance(result, ForecastBundle):
    # Success - process forecasts
    for forecast in result.forecasts:
        process_forecast(forecast)
elif isinstance(result, ForecastError):
    # Handle error
    print(f"Forecast failed: {result.error}")
    print(f"Error code: {result.error_code}")
```

## 🌐 Web Interface (Planned)

The web interface will feature:

- **Interactive Map**: GIBS tiles with time controls
- **Forecast Timeline**: Visualize predicted arrival windows
- **Evidence Browser**: Click to view source data
- **Alert System**: Notifications for significant events

## 🔬 Scientific Background

### Data Sources

- **DONKI**: Real-time space weather event database from NASA's CCMC
- **EPIC**: L1 Lagrange point Earth imagery from DSCOVR satellite
- **GIBS**: NASA's global imagery service with time-aware tiles

### Analysis Methodology

1. **Event Detection**: Identify significant space weather events from DONKI
2. **Earth-Direction Assessment**: Evaluate geometric and magnetic connectivity
3. **Transit Time Modeling**: Estimate arrival using solar wind speed ranges
4. **Impact Assessment**: Predict technology and aurora effects
5. **Confidence Scoring**: Weight predictions by data quality and uncertainty

## 📚 API Reference

### Core Functions

#### `run_forecast(days_back=3, epic_date_iso=None, include_images=False)`

Simple forecast generation.

**Parameters:**
- `days_back` (int): Days to look back for space weather events
- `epic_date_iso` (str): Specific date for EPIC imagery (ISO format)
- `include_images` (bool): Include EPIC image URLs in analysis

**Returns:** `ForecastBundle` or `ForecastError`

#### `run_forecast_advanced(config: ForecastConfig)`

Advanced forecast with custom configuration.

**Parameters:**
- `config` (ForecastConfig): Advanced configuration object

**Returns:** `ForecastBundle` or `ForecastError`

### Configuration Classes

#### `ForecastConfig`

```python
@dataclass
class ForecastConfig:
    days_back: int = 3                    # Days to look back
    max_events_per_source: int = 5        # Max events per DONKI source
    max_epic_frames: int = 3              # Max EPIC frames to analyze
    epic_date_iso: Optional[str] = None   # Specific EPIC date
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1500                # Claude response token limit
    include_images: bool = False          # Include image analysis
```

## 🧪 Testing

```bash
# Run the demo to test all components
cd backend
python demo.py

# Test individual components
python -c "from nasa_client import NASAClient; client = NASAClient(); print(len(client.fetch_donki_cmes()))"
```

## 🤝 Contributing

This is a research/demonstration project. Contributions welcome for:

- Enhanced physics models (CME propagation, magnetic connectivity)
- Additional data sources (solar wind, magnetometer data)
- Web interface development
- Improved error handling and validation

## 📄 License

MIT License - See LICENSE file for details.

NASA content is typically public domain. Check individual dataset terms and attribute appropriately.

## ⚠️ Disclaimer

This system is for research and educational purposes. Space weather forecasting is complex and uncertain. Do not rely on these forecasts for critical decisions without validation from official space weather services like NOAA SWPC.

## 📞 Support

- **Documentation**: Check this README and code comments
- **Issues**: Review error messages and API key configuration
- **NASA APIs**: [api.nasa.gov](https://api.nasa.gov/) for data source info
- **Claude API**: [docs.anthropic.com](https://docs.anthropic.com/) for AI service info

## 🔗 Related Resources

- [NASA DONKI](https://ccmc.gsfc.nasa.gov/tools/DONKI/) - Space Weather Event Database
- [NASA EPIC](https://epic.gsfc.nasa.gov/) - Earth Polychromatic Imaging Camera
- [NASA GIBS](https://wiki.earthdata.nasa.gov/display/GIBS) - Global Imagery Browse Services
- [NOAA SWPC](https://www.swpc.noaa.gov/) - Official Space Weather Predictions
- [Anthropic Claude](https://www.anthropic.com/claude) - AI Assistant Platform

---

**Happy building — and enjoy the auroras! 🌌**