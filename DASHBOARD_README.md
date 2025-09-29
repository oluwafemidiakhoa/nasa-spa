# NASA Space Weather Professional Dashboard

## 🚀 **Your Space Weather Forecaster is Ready!**

The professional dashboard provides a mission-control style interface for monitoring space weather conditions using OpenAI AI analysis.

## 🌟 **Features**

- **Real-time Space Weather Analysis** using OpenAI GPT-4
- **NASA Data Integration** (DONKI, EPIC, GIBS)
- **Mission Control Interface** with status indicators
- **AI-Powered Forecasting** with confidence levels
- **Risk Assessment** and impact predictions
- **Evidence Chain Tracking** for forecast transparency
- **Auto-refresh** every 5 minutes

## 🏃 **Quick Start**

### Method 1: Simple Launch (Recommended)
```bash
# Double-click this file:
launch_dashboard.bat
```

### Method 2: Manual Launch
```bash
# Terminal 1: Start API Server
python dashboard_api.py

# Terminal 2: Open Dashboard
# Open professional_dashboard.html in your browser
```

## 📊 **Dashboard Components**

### **System Status Panel**
- API connection status
- AI analysis engine status  
- NASA data feed status
- Manual refresh/analyze buttons

### **AI Forecast Panel**
- Current forecast summary
- Confidence meter
- Risk level indicator

### **Space Weather Index**
- Visual gauge showing activity level
- Numerical score (0-100)
- Activity classification

### **Evidence Chain**
- Source data references
- DONKI event IDs
- Confidence scores

### **Impact Assessment**
- Predicted effects on technology
- Risk severity levels
- Affected systems

### **Mission Recommendations**
- AI-generated action items
- Priority levels
- Operational guidance

## 🔧 **Configuration**

The dashboard automatically uses your configured API keys from `.env`:
- `OPENAI_API_KEY` - Required for AI analysis
- `NASA_API_KEY` - Required for space weather data

## 🌐 **API Endpoints**

The dashboard API provides these endpoints:

- `GET /` - API status
- `GET /api/v1/status` - System status
- `GET /api/v1/forecasts/simple` - Basic forecast
- `GET /api/v1/forecasts/advanced` - Dashboard-formatted forecast
- `POST /api/v1/forecasts/generate` - Generate new forecast

## 🛠 **Troubleshooting**

### **Dashboard Not Loading**
1. Check that API server is running on port 8001
2. Verify your browser allows local file access
3. Check browser console for errors

### **No Forecast Data**
1. Verify OpenAI API key is valid
2. Check NASA API connectivity
3. Look at API server logs for errors

### **"Connection Error" Messages**
1. Ensure API server is running: `http://localhost:8001`
2. Check firewall isn't blocking port 8001
3. Verify no other service is using port 8001

## 📈 **Understanding the Data**

### **Risk Levels**
- **MINIMAL** - Normal space weather conditions
- **LOW** - Minor disturbances possible
- **MODERATE** - Noticeable effects on technology
- **HIGH** - Strong impacts likely
- **EXTREME** - Severe disruption possible

### **Confidence Scores**
- **80-100%** - High confidence prediction
- **60-79%** - Moderate confidence
- **40-59%** - Lower confidence
- **<40%** - Uncertain conditions

### **Impact Categories**
- **Aurora** - Visibility predictions
- **HF Communications** - Radio disruption
- **GNSS/GPS** - Navigation accuracy
- **Satellite Operations** - Orbital effects
- **Power Grid** - Infrastructure risk

## 🔄 **Auto-Refresh**

The dashboard automatically updates every 5 minutes. You can also:
- Click **REFRESH** to update data
- Click **ANALYZE** to generate new forecast

## 🎯 **Mission Control Features**

- **Real-time mission clock** in UTC
- **Status light indicators** for all systems
- **Professional space agency styling**
- **Responsive design** for different screen sizes
- **Alert notifications** for high-risk conditions

## 📱 **Mobile Friendly**

The dashboard adapts to mobile screens with:
- Single-column layout
- Touch-friendly controls
- Optimized font sizes
- Simplified navigation

---

**Ready for launch! Your space weather mission control center is operational.** 🛰️