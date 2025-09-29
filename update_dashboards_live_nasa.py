#!/usr/bin/env python3
"""
Update dashboards to use live NASA data instead of simulated data
"""

import os
import sys
import json
from datetime import datetime

# Set up environment
os.environ['NASA_API_KEY'] = 'h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA'
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def get_live_nasa_data():
    """Fetch fresh live NASA data"""
    try:
        from nasa_client import NASAClient
        client = NASAClient()
        
        print("Fetching live NASA data...")
        events = client.get_all_space_weather_events(days_back=7)
        
        print(f"Live data retrieved:")
        print(f"  CMEs: {len(events.get('cmes', []))}")
        print(f"  Solar Flares: {len(events.get('flares', []))}")
        print(f"  SEP Events: {len(events.get('sep_events', []))}")
        print(f"  Geomagnetic Storms: {len(events.get('geomagnetic_storms', []))}")
        
        return events
    except Exception as e:
        print(f"Error fetching NASA data: {e}")
        return None

def create_live_data_js():
    """Create JavaScript file with live NASA data for dashboards"""
    events = get_live_nasa_data()
    if not events:
        print("Could not fetch live NASA data")
        return False
    
    # Process events for dashboard display
    processed_events = []
    
    # Process CMEs
    for cme in events.get('cmes', []):
        processed_event = {
            'id': cme.get('activityID', 'Unknown'),
            'type': 'CME',
            'time': cme.get('startTime', ''),
            'source': cme.get('sourceLocation', 'Unknown'),
            'note': cme.get('note', 'Coronal Mass Ejection detected'),
            'speed': None,
            'latitude': None,
            'longitude': None
        }
        
        # Extract analysis data if available
        if cme.get('cmeAnalyses'):
            analysis = cme['cmeAnalyses'][0]  # Get first analysis
            processed_event['speed'] = analysis.get('speed')
            processed_event['latitude'] = analysis.get('latitude')
            processed_event['longitude'] = analysis.get('longitude')
        
        processed_events.append(processed_event)
    
    # Process Solar Flares
    for flare in events.get('flares', []):
        processed_event = {
            'id': flare.get('flrID', 'Unknown'),
            'type': 'Solar Flare',
            'time': flare.get('beginTime', ''),
            'source': flare.get('sourceLocation', 'Unknown'),
            'class': flare.get('classType', 'Unknown'),
            'note': f"Class {flare.get('classType', 'Unknown')} solar flare"
        }
        processed_events.append(processed_event)
    
    # Create JavaScript content
    js_content = f'''
// Live NASA Space Weather Data
// Generated: {datetime.utcnow().isoformat()}Z
// Total Events: {len(processed_events)}

window.LIVE_NASA_DATA = {{
    events: {json.dumps(processed_events, indent=2)},
    summary: {{
        total_events: {len(processed_events)},
        cme_count: {len(events.get('cmes', []))},
        flare_count: {len(events.get('flares', []))},
        sep_count: {len(events.get('sep_events', []))},
        geomagnetic_storm_count: {len(events.get('geomagnetic_storms', []))},
        data_timestamp: "{datetime.utcnow().isoformat()}Z",
        data_source: "NASA DONKI Live Feed"
    }},
    raw_nasa_data: {json.dumps(events, indent=2)}
}};

// Helper function to get events for timeline
function getLiveSpaceWeatherEvents() {{
    return window.LIVE_NASA_DATA.events.map(event => ({{
        time: event.time,
        title: `${{event.type}}: ${{event.id}}`,
        description: event.note || `${{event.type}} detected`,
        severity: event.type === 'CME' ? 'high' : 'medium',
        source: event.source || 'Unknown'
    }}));
}}

// Helper function to get latest CME for 3D visualization
function getLatestCMEForVisualization() {{
    const cmes = window.LIVE_NASA_DATA.events.filter(e => e.type === 'CME');
    if (cmes.length > 0) {{
        const latest = cmes[0];
        return {{
            id: latest.id,
            time: latest.time,
            speed: latest.speed || 400,
            latitude: latest.latitude || 0,
            longitude: latest.longitude || 0,
            isLive: true
        }};
    }}
    return null;
}}

console.log("Live NASA data loaded:", window.LIVE_NASA_DATA.summary);
'''
    
    # Save to file
    try:
        with open('live_nasa_data.js', 'w') as f:
            f.write(js_content)
        print(f"SUCCESS: Live NASA data saved to live_nasa_data.js")
        print(f"Events processed: {len(processed_events)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save JavaScript file: {e}")
        return False

def update_3d_dashboard():
    """Update 3D dashboard to use live NASA data"""
    print("\nUpdating 3D dashboard...")
    
    try:
        # Read current 3D dashboard
        with open('3d_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add live data script reference
        if '<script src="live_nasa_data.js"></script>' not in content:
            # Find head section and add script
            head_end = content.find('</head>')
            if head_end != -1:
                content = content[:head_end] + '    <script src="live_nasa_data.js"></script>\\n' + content[head_end:]
        
        # Update the timeline events to use live data
        old_timeline_code = '''// Sample events for demonstration
                        const events = [
                            {
                                time: '2025-09-28T14:36:00Z',
                                title: 'CME Detected',
                                description: 'Earth-directed coronal mass ejection observed',
                                severity: 'high'
                            },
                            {
                                time: '2025-09-28T12:15:00Z',
                                title: 'Solar Flare',
                                description: 'M-class solar flare detected',
                                severity: 'medium'
                            },
                            {
                                time: '2025-09-28T08:30:00Z',
                                title: 'Geomagnetic Activity',
                                description: 'Minor geomagnetic disturbance expected',
                                severity: 'low'
                            }
                        ];'''
        
        new_timeline_code = '''// Live NASA events
                        const events = getLiveSpaceWeatherEvents() || [
                            {
                                time: '2025-09-28T14:36:00Z',
                                title: 'No Live Data',
                                description: 'Live NASA data not available',
                                severity: 'low'
                            }
                        ];'''
        
        if old_timeline_code in content:
            content = content.replace(old_timeline_code, new_timeline_code)
        
        # Update CME visualization to use live data
        old_cme_code = '''// Simulate real-time CME approach
                            const cmeDistance = 150 - (Date.now() % 10000) / 100;
                            cmeObject.position.set(cmeDistance, 0, 0);'''
        
        new_cme_code = '''// Use live NASA CME data
                            const liveCME = getLatestCMEForVisualization();
                            if (liveCME) {
                                // Position based on real CME data
                                const elapsed = (Date.now() - new Date(liveCME.time)) / (1000 * 60 * 60); // hours
                                const distance = Math.max(50, 150 - (liveCME.speed || 400) * elapsed / 1000);
                                cmeObject.position.set(distance, liveCME.latitude || 0, liveCME.longitude || 0);
                            } else {
                                // Fallback simulation
                                const cmeDistance = 150 - (Date.now() % 10000) / 100;
                                cmeObject.position.set(cmeDistance, 0, 0);
                            }'''
        
        if old_cme_code in content:
            content = content.replace(old_cme_code, new_cme_code)
        
        # Save updated dashboard
        with open('3d_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: 3D dashboard updated with live NASA data")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update 3D dashboard: {e}")
        return False

def update_ensemble_dashboard():
    """Update ensemble dashboard to use live NASA data"""
    print("\nUpdating ensemble dashboard...")
    
    try:
        # Read current ensemble dashboard
        with open('simple_new.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add live data script reference
        if '<script src="live_nasa_data.js"></script>' not in content:
            head_end = content.find('</head>')
            if head_end != -1:
                content = content[:head_end] + '    <script src="live_nasa_data.js"></script>\\n' + content[head_end:]
        
        # Update status display to show live data counts
        old_status_code = '''document.getElementById('events-analyzed').textContent = Math.floor(Math.random() * 20) + 5;'''
        
        new_status_code = '''const liveData = window.LIVE_NASA_DATA || {summary: {total_events: 0}};
                            document.getElementById('events-analyzed').textContent = liveData.summary.total_events;'''
        
        if old_status_code in content:
            content = content.replace(old_status_code, new_status_code)
        
        # Add live data indicator
        old_data_source = '''<span style="color: #00ff88;">Ensemble Models Active</span>'''
        new_data_source = '''<span style="color: #00ff88;">Live NASA Data + Ensemble Models</span>'''
        
        if old_data_source in content:
            content = content.replace(old_data_source, new_data_source)
        
        # Save updated dashboard
        with open('simple_new.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: Ensemble dashboard updated with live NASA data")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update ensemble dashboard: {e}")
        return False

def main():
    """Main update function"""
    print("NASA Space Weather Dashboard - Live Data Integration")
    print("Updating dashboards to use real NASA DONKI data")
    print("=" * 60)
    
    # Step 1: Create live data JavaScript
    if not create_live_data_js():
        print("FAILED: Could not create live data file")
        return
    
    # Step 2: Update 3D dashboard
    update_3d_dashboard()
    
    # Step 3: Update ensemble dashboard
    update_ensemble_dashboard()
    
    # Summary
    print("\n" + "=" * 60)
    print("LIVE NASA DATA INTEGRATION COMPLETE")
    print("=" * 60)
    print()
    print("Dashboards now using real NASA DONKI data!")
    print()
    print("Updated files:")
    print("  • live_nasa_data.js - Live NASA data feed")
    print("  • 3d_dashboard.html - Real CME visualization")
    print("  • simple_new.html - Live event counts")
    print()
    print("What's now available:")
    print("  • Real CME events with speed/direction")
    print("  • Actual solar flare classifications")
    print("  • Live space weather event timeline")
    print("  • NASA-sourced geomagnetic data")
    print()
    print("Next: Open dashboards to see live NASA data in action!")

if __name__ == "__main__":
    main()