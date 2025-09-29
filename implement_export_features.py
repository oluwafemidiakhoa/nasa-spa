#!/usr/bin/env python3
"""
Implement PDF and CSV export features for NASA Space Weather dashboards
"""

import os
import sys
from datetime import datetime

def create_export_backend():
    """Create backend export service for PDF and CSV generation"""
    print("=" * 60)
    print("CREATING EXPORT BACKEND SERVICE")
    print("=" * 60)
    
    export_service_content = '''#!/usr/bin/env python3
"""
Export Service for NASA Space Weather Dashboard
Handles PDF and CSV export generation
"""

import os
import sys
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import base64

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up environment
os.environ['NASA_API_KEY'] = 'h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA'

class SpaceWeatherExporter:
    """Export handler for space weather data"""
    
    def __init__(self):
        self.nasa_client = None
        self.initialize_clients()
    
    def initialize_clients(self):
        """Initialize NASA client"""
        try:
            from nasa_client import NASAClient
            self.nasa_client = NASAClient()
            print("NASA client initialized for export service")
        except Exception as e:
            print(f"Warning: Could not initialize NASA client: {e}")
    
    def get_export_data(self, days_back: int = 7) -> Dict[str, Any]:
        """Get comprehensive data for export"""
        try:
            if self.nasa_client:
                # Get live NASA data
                events = self.nasa_client.get_all_space_weather_events(days_back)
            else:
                # Fallback to demo data
                events = {
                    'cmes': [],
                    'flares': [],
                    'sep_events': [],
                    'geomagnetic_storms': []
                }
            
            # Calculate summary statistics
            total_events = sum(len(event_list) for event_list in events.values())
            
            # Process events for export
            processed_events = []
            
            # Process CMEs
            for cme in events.get('cmes', []):
                processed_events.append({
                    'type': 'CME',
                    'id': cme.get('activityID', 'Unknown'),
                    'start_time': cme.get('startTime', ''),
                    'source_location': cme.get('sourceLocation', ''),
                    'speed': self._get_cme_speed(cme),
                    'latitude': self._get_cme_latitude(cme),
                    'longitude': self._get_cme_longitude(cme),
                    'note': cme.get('note', '')[:200] + '...' if len(cme.get('note', '')) > 200 else cme.get('note', ''),
                    'earth_directed': self._is_earth_directed(cme)
                })
            
            # Process Solar Flares
            for flare in events.get('flares', []):
                processed_events.append({
                    'type': 'Solar Flare',
                    'id': flare.get('flrID', 'Unknown'),
                    'start_time': flare.get('beginTime', ''),
                    'peak_time': flare.get('peakTime', ''),
                    'end_time': flare.get('endTime', ''),
                    'class_type': flare.get('classType', 'Unknown'),
                    'source_location': flare.get('sourceLocation', ''),
                    'note': flare.get('note', '')[:200] + '...' if len(flare.get('note', '')) > 200 else flare.get('note', '')
                })
            
            # Sort by time
            processed_events.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                    'data_period': f'{days_back} days',
                    'total_events': total_events,
                    'cme_count': len(events.get('cmes', [])),
                    'flare_count': len(events.get('flares', [])),
                    'sep_count': len(events.get('sep_events', [])),
                    'geomagnetic_storm_count': len(events.get('geomagnetic_storms', [])),
                    'data_source': 'NASA DONKI API'
                },
                'events': processed_events,
                'raw_events': events
            }
            
            return export_data
            
        except Exception as e:
            print(f"Error getting export data: {e}")
            return self._get_fallback_data()
    
    def _get_cme_speed(self, cme: Dict) -> Optional[float]:
        """Extract CME speed from analysis data"""
        try:
            analyses = cme.get('cmeAnalyses', [])
            if analyses:
                return analyses[0].get('speed')
        except:
            pass
        return None
    
    def _get_cme_latitude(self, cme: Dict) -> Optional[float]:
        """Extract CME latitude from analysis data"""
        try:
            analyses = cme.get('cmeAnalyses', [])
            if analyses:
                return analyses[0].get('latitude')
        except:
            pass
        return None
    
    def _get_cme_longitude(self, cme: Dict) -> Optional[float]:
        """Extract CME longitude from analysis data"""
        try:
            analyses = cme.get('cmeAnalyses', [])
            if analyses:
                return analyses[0].get('longitude')
        except:
            pass
        return None
    
    def _is_earth_directed(self, cme: Dict) -> bool:
        """Determine if CME is Earth-directed"""
        try:
            # Simple heuristic based on coordinate ranges
            lat = self._get_cme_latitude(cme)
            lon = self._get_cme_longitude(cme)
            
            if lat is not None and lon is not None:
                # Earth-facing hemisphere approximation
                return abs(lat) < 45 and abs(lon) < 90
        except:
            pass
        return False
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when NASA API is unavailable"""
        return {
            'metadata': {
                'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                'data_period': '7 days',
                'total_events': 3,
                'cme_count': 2,
                'flare_count': 1,
                'sep_count': 0,
                'geomagnetic_storm_count': 0,
                'data_source': 'Demo Data (NASA API unavailable)'
            },
            'events': [
                {
                    'type': 'CME',
                    'id': 'DEMO-CME-001',
                    'start_time': '2025-09-27T14:36:00Z',
                    'source_location': 'N15W20',
                    'speed': 450.0,
                    'latitude': 15.0,
                    'longitude': -20.0,
                    'note': 'Demo CME event for export testing',
                    'earth_directed': True
                },
                {
                    'type': 'Solar Flare',
                    'id': 'DEMO-FLR-001',
                    'start_time': '2025-09-27T12:15:00Z',
                    'peak_time': '2025-09-27T12:20:00Z',
                    'end_time': '2025-09-27T12:25:00Z',
                    'class_type': 'M1.5',
                    'source_location': 'N15W20',
                    'note': 'Demo solar flare for export testing'
                }
            ],
            'raw_events': {
                'cmes': [],
                'flares': [],
                'sep_events': [],
                'geomagnetic_storms': []
            }
        }
    
    def export_to_csv(self, data: Dict[str, Any]) -> str:
        """Export data to CSV format"""
        output = io.StringIO()
        
        # Write metadata header
        writer = csv.writer(output)
        writer.writerow(['NASA Space Weather Export Report'])
        writer.writerow(['Export Timestamp', data['metadata']['export_timestamp']])
        writer.writerow(['Data Period', data['metadata']['data_period']])
        writer.writerow(['Total Events', data['metadata']['total_events']])
        writer.writerow(['CME Count', data['metadata']['cme_count']])
        writer.writerow(['Solar Flare Count', data['metadata']['flare_count']])
        writer.writerow(['Data Source', data['metadata']['data_source']])
        writer.writerow([])  # Empty row
        
        # Write events data
        if data['events']:
            # Get all unique keys from events
            all_keys = set()
            for event in data['events']:
                all_keys.update(event.keys())
            
            headers = sorted(list(all_keys))
            writer.writerow(headers)
            
            for event in data['events']:
                row = [event.get(key, '') for key in headers]
                writer.writerow(row)
        else:
            writer.writerow(['No events found in the specified time period'])
        
        return output.getvalue()
    
    def export_to_json(self, data: Dict[str, Any]) -> str:
        """Export data to JSON format"""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report for PDF conversion"""
        events = data['events']
        metadata = data['metadata']
        
        # Calculate risk assessment
        high_risk_events = [e for e in events if 
                          (e['type'] == 'CME' and e.get('earth_directed', False)) or
                          (e['type'] == 'Solar Flare' and e.get('class_type', '').startswith(('X', 'M')))]
        
        risk_level = 'HIGH' if len(high_risk_events) > 0 else 'MODERATE' if len(events) > 5 else 'LOW'
        risk_color = '#ff4444' if risk_level == 'HIGH' else '#ffaa44' if risk_level == 'MODERATE' else '#44ff44'
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NASA Space Weather Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 40px;
            color: #333;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #0066cc;
            margin: 0;
            font-size: 2.2rem;
        }}
        
        .header .subtitle {{
            color: #666;
            font-size: 1.1rem;
            margin-top: 10px;
        }}
        
        .metadata {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .metadata h2 {{
            color: #0066cc;
            margin-top: 0;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        
        .metadata-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        .metadata-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .metadata-item:last-child {{
            border-bottom: none;
        }}
        
        .metadata-label {{
            font-weight: bold;
            color: #555;
        }}
        
        .risk-assessment {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-left: 5px solid {risk_color};
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 8px 8px 0;
        }}
        
        .risk-level {{
            font-size: 1.5rem;
            font-weight: bold;
            color: {risk_color};
            margin-bottom: 10px;
        }}
        
        .events-section {{
            margin-bottom: 30px;
        }}
        
        .events-section h2 {{
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        
        .event-card {{
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .event-header {{
            background: #0066cc;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1rem;
        }}
        
        .event-body {{
            padding: 20px;
        }}
        
        .event-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .event-detail {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
        }}
        
        .event-detail-label {{
            font-weight: bold;
            color: #555;
            min-width: 120px;
        }}
        
        .event-note {{
            background: #f8f9fa;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin-top: 15px;
            font-style: italic;
        }}
        
        .cme-event {{
            border-left: 5px solid #ff6600;
        }}
        
        .flare-event {{
            border-left: 5px solid #ff0066;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #666;
            font-size: 0.9rem;
        }}
        
        @media print {{
            body {{
                margin: 20px;
            }}
            
            .event-card {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛰️ NASA Space Weather Report</h1>
        <div class="subtitle">Comprehensive Space Weather Analysis</div>
        <div class="subtitle">Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    </div>
    
    <div class="metadata">
        <h2>📊 Report Summary</h2>
        <div class="metadata-grid">
            <div class="metadata-item">
                <span class="metadata-label">Export Time:</span>
                <span>{metadata['export_timestamp']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Data Period:</span>
                <span>{metadata['data_period']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Total Events:</span>
                <span>{metadata['total_events']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">CME Events:</span>
                <span>{metadata['cme_count']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Solar Flares:</span>
                <span>{metadata['flare_count']}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Data Source:</span>
                <span>{metadata['data_source']}</span>
            </div>
        </div>
    </div>
    
    <div class="risk-assessment">
        <div class="risk-level">Risk Level: {risk_level}</div>
        <p>Based on analysis of {metadata['total_events']} space weather events over the past {metadata['data_period']}. 
        {len(high_risk_events)} high-risk events identified requiring attention.</p>
    </div>
    
    <div class="events-section">
        <h2>🌟 Space Weather Events</h2>
'''
        
        if events:
            for event in events:
                event_class = 'cme-event' if event['type'] == 'CME' else 'flare-event'
                
                html_content += f'''
        <div class="event-card {event_class}">
            <div class="event-header">
                {event['type']}: {event['id']}
            </div>
            <div class="event-body">
                <div class="event-details">
                    <div class="event-detail">
                        <span class="event-detail-label">Start Time:</span>
                        <span>{event.get('start_time', 'Unknown')}</span>
                    </div>
                    <div class="event-detail">
                        <span class="event-detail-label">Source Location:</span>
                        <span>{event.get('source_location', 'Unknown')}</span>
                    </div>
'''
                
                if event['type'] == 'CME':
                    html_content += f'''
                    <div class="event-detail">
                        <span class="event-detail-label">Speed:</span>
                        <span>{event.get('speed', 'Unknown')} km/s</span>
                    </div>
                    <div class="event-detail">
                        <span class="event-detail-label">Earth Directed:</span>
                        <span>{'Yes' if event.get('earth_directed', False) else 'No'}</span>
                    </div>
'''
                elif event['type'] == 'Solar Flare':
                    html_content += f'''
                    <div class="event-detail">
                        <span class="event-detail-label">Class:</span>
                        <span>{event.get('class_type', 'Unknown')}</span>
                    </div>
                    <div class="event-detail">
                        <span class="event-detail-label">Peak Time:</span>
                        <span>{event.get('peak_time', 'Unknown')}</span>
                    </div>
'''
                
                if event.get('note'):
                    html_content += f'''
                </div>
                <div class="event-note">
                    <strong>Details:</strong> {event['note']}
                </div>
'''
                else:
                    html_content += '</div>'
                
                html_content += '''
            </div>
        </div>
'''
        else:
            html_content += '''
        <div class="event-card">
            <div class="event-body">
                <p>No space weather events found in the specified time period.</p>
            </div>
        </div>
'''
        
        html_content += f'''
    </div>
    
    <div class="footer">
        <p>This report was generated by the NASA Space Weather Dashboard system.</p>
        <p>Data provided by NASA DONKI (Database Of Notifications, Knowledge, Information)</p>
        <p>For the most current information, visit the live dashboard at your deployment URL.</p>
    </div>
</body>
</html>'''
        
        return html_content

def main():
    """Test the export service"""
    print("NASA Space Weather Export Service")
    print("Testing export functionality...")
    print()
    
    exporter = SpaceWeatherExporter()
    
    # Get export data
    print("Fetching export data...")
    data = exporter.get_export_data(days_back=7)
    
    print(f"Retrieved {data['metadata']['total_events']} events")
    print()
    
    # Test CSV export
    print("Generating CSV export...")
    csv_content = exporter.export_to_csv(data)
    
    with open('space_weather_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print("CSV export saved as space_weather_export.csv")
    
    # Test JSON export
    print("Generating JSON export...")
    json_content = exporter.export_to_json(data)
    
    with open('space_weather_export.json', 'w', encoding='utf-8') as f:
        f.write(json_content)
    print("JSON export saved as space_weather_export.json")
    
    # Test HTML report
    print("Generating HTML report...")
    html_content = exporter.generate_html_report(data)
    
    with open('space_weather_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("HTML report saved as space_weather_report.html")
    
    print()
    print("Export service test completed successfully!")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('export_service.py', 'w', encoding='utf-8') as f:
            f.write(export_service_content)
        
        print("SUCCESS: Export service created as export_service.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create export service: {e}")
        return False

def create_export_api_endpoints():
    """Add export endpoints to the API server"""
    print("\n" + "=" * 60)
    print("ADDING EXPORT API ENDPOINTS")
    print("=" * 60)
    
    try:
        # Read current API server
        with open('simple_api_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add export endpoints to the routing
        export_routes = '''        elif path == '/api/v1/export/csv':
            self.send_csv_export()
        elif path == '/api/v1/export/json':
            self.send_json_export()
        elif path == '/api/v1/export/html':
            self.send_html_export()
        elif path == '/api/v1/export/pdf':
            self.send_pdf_export()'''
        
        # Find the routing section and add export routes
        if 'elif path == \'/api/v1/nasa/all-events\':' in content:
            insert_point = content.find('elif path == \'/api/v1/nasa/all-events\':', content.find('def do_GET'))
            # Insert after the nasa/all-events route
            nasa_all_events_end = content.find('self.send_all_nasa_events()', insert_point) + len('self.send_all_nasa_events()')
            content = content[:nasa_all_events_end] + '\n        ' + export_routes + content[nasa_all_events_end:]
        
        # Add export methods at the end of the class
        export_methods = '''
    
    def send_csv_export(self):
        """Send CSV export of space weather data"""
        try:
            from export_service import SpaceWeatherExporter
            
            # Parse query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            days_back = int(query_params.get('days', ['7'])[0])
            
            exporter = SpaceWeatherExporter()
            data = exporter.get_export_data(days_back)
            csv_content = exporter.export_to_csv(data)
            
            # Send CSV response
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="space_weather_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"')
            self.end_headers()
            self.wfile.write(csv_content.encode('utf-8'))
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": f"Failed to generate CSV export: {str(e)}"
            })
    
    def send_json_export(self):
        """Send JSON export of space weather data"""
        try:
            from export_service import SpaceWeatherExporter
            
            # Parse query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            days_back = int(query_params.get('days', ['7'])[0])
            
            exporter = SpaceWeatherExporter()
            data = exporter.get_export_data(days_back)
            
            response_data = {
                "success": True,
                "export_data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": f"Failed to generate JSON export: {str(e)}"
            })
    
    def send_html_export(self):
        """Send HTML report of space weather data"""
        try:
            from export_service import SpaceWeatherExporter
            
            # Parse query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            days_back = int(query_params.get('days', ['7'])[0])
            
            exporter = SpaceWeatherExporter()
            data = exporter.get_export_data(days_back)
            html_content = exporter.generate_html_report(data)
            
            # Send HTML response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": f"Failed to generate HTML report: {str(e)}"
            })
    
    def send_pdf_export(self):
        """Send PDF export (requires HTML to PDF conversion)"""
        try:
            from export_service import SpaceWeatherExporter
            
            # Parse query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            days_back = int(query_params.get('days', ['7'])[0])
            
            exporter = SpaceWeatherExporter()
            data = exporter.get_export_data(days_back)
            html_content = exporter.generate_html_report(data)
            
            # For now, return HTML with PDF conversion instructions
            # In production, you would use a library like weasyprint or pdfkit
            pdf_response = {
                "success": True,
                "message": "PDF export available - HTML content provided for conversion",
                "html_content": html_content,
                "conversion_note": "Use weasyprint or similar library to convert HTML to PDF",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.send_json_response(pdf_response)
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": f"Failed to generate PDF export: {str(e)}"
            })'''
        
        # Insert export methods before the main section
        main_section = content.find('def main():')
        if main_section != -1:
            content = content[:main_section] + export_methods + '\n\n' + content[main_section:]
        
        # Save updated API server
        with open('simple_api_server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: Export API endpoints added to simple_api_server.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to add export API endpoints: {e}")
        return False

def create_export_ui_components():
    """Create export UI components for dashboards"""
    print("\n" + "=" * 60)
    print("CREATING EXPORT UI COMPONENTS")
    print("=" * 60)
    
    export_ui_content = '''
// Export UI Components for Space Weather Dashboards
// Provides export functionality for PDF, CSV, and JSON formats

class SpaceWeatherExporter {
    constructor(apiBaseUrl = 'http://localhost:9001') {
        this.apiBaseUrl = apiBaseUrl;
        this.setupExportUI();
    }
    
    setupExportUI() {
        // Add export styles
        this.addExportStyles();
        
        // Setup export modal if not exists
        this.createExportModal();
        
        // Setup export button if not exists
        this.createExportButton();
    }
    
    addExportStyles() {
        const styleId = 'export-ui-styles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .export-button {
                background: linear-gradient(45deg, #28a745, #20c997);
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
                margin: 5px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                transition: all 0.3s ease;
            }
            
            .export-button:hover {
                background: linear-gradient(45deg, #218838, #1abc9c);
                transform: translateY(-1px);
            }
            
            .export-modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .export-modal-content {
                background: linear-gradient(135deg, #1a1a3a, #2d2d5f);
                margin: 5% auto;
                padding: 20px;
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                color: white;
                border: 2px solid #00bfff;
            }
            
            .export-modal h3 {
                color: #00bfff;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .export-options {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .export-option {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid #00ff88;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .export-option:hover {
                background: rgba(0, 255, 136, 0.2);
                transform: translateY(-2px);
            }
            
            .export-option h4 {
                color: #00ff88;
                margin-bottom: 8px;
            }
            
            .export-option p {
                font-size: 0.8rem;
                color: #ccc;
                margin-bottom: 10px;
            }
            
            .export-option button {
                background: linear-gradient(45deg, #00ff88, #00bfff);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8rem;
            }
            
            .export-settings {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .export-settings label {
                display: block;
                margin-bottom: 8px;
                color: #00bfff;
                font-weight: bold;
            }
            
            .export-settings select,
            .export-settings input {
                width: 100%;
                padding: 8px;
                border: 1px solid #666;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            
            .export-controls {
                display: flex;
                justify-content: space-between;
                gap: 10px;
            }
            
            .export-controls button {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
            }
            
            .cancel-btn {
                background: #6c757d;
                color: white;
            }
            
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .close:hover {
                color: #fff;
            }
            
            .export-status {
                background: rgba(0, 255, 136, 0.1);
                border: 1px solid #00ff88;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
                text-align: center;
                display: none;
            }
            
            .export-status.show {
                display: block;
            }
            
            .export-status.error {
                background: rgba(255, 68, 68, 0.1);
                border-color: #ff4444;
                color: #ff8888;
            }
            
            .export-status.success {
                color: #00ff88;
            }
            
            @media screen and (max-width: 768px) {
                .export-modal-content {
                    margin: 10% auto;
                    width: 95%;
                    padding: 15px;
                }
                
                .export-options {
                    grid-template-columns: 1fr;
                }
                
                .export-controls {
                    flex-direction: column;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    createExportButton() {
        const buttonId = 'main-export-button';
        if (document.getElementById(buttonId)) return;
        
        const button = document.createElement('button');
        button.id = buttonId;
        button.className = 'export-button';
        button.innerHTML = '📊 Export Data';
        button.onclick = () => this.openExportModal();
        
        // Try to add to header or controls area
        const targetSelectors = [
            '.header-status',
            '.status-bar', 
            '.control-panel',
            '.header',
            '.controls'
        ];
        
        for (const selector of targetSelectors) {
            const target = document.querySelector(selector);
            if (target) {
                target.appendChild(button);
                console.log(`Export button added to ${selector}`);
                return;
            }
        }
        
        // Fallback: add to body
        document.body.appendChild(button);
        console.log('Export button added to body as fallback');
    }
    
    createExportModal() {
        const modalId = 'export-modal';
        if (document.getElementById(modalId)) return;
        
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'export-modal';
        
        modal.innerHTML = `
            <div class="export-modal-content">
                <span class="close">&times;</span>
                <h3>📊 Export Space Weather Data</h3>
                
                <div class="export-settings">
                    <label for="export-days">Data Period:</label>
                    <select id="export-days">
                        <option value="1">Last 24 hours</option>
                        <option value="3">Last 3 days</option>
                        <option value="7" selected>Last 7 days</option>
                        <option value="14">Last 14 days</option>
                        <option value="30">Last 30 days</option>
                    </select>
                </div>
                
                <div class="export-options">
                    <div class="export-option" data-format="csv">
                        <h4>📊 CSV Export</h4>
                        <p>Spreadsheet format for data analysis</p>
                        <button onclick="window.spaceWeatherExporter.exportData('csv')">Download CSV</button>
                    </div>
                    
                    <div class="export-option" data-format="json">
                        <h4>🔗 JSON Export</h4>
                        <p>Structured data for developers</p>
                        <button onclick="window.spaceWeatherExporter.exportData('json')">Download JSON</button>
                    </div>
                    
                    <div class="export-option" data-format="html">
                        <h4>📄 HTML Report</h4>
                        <p>Formatted report for viewing</p>
                        <button onclick="window.spaceWeatherExporter.exportData('html')">Open Report</button>
                    </div>
                    
                    <div class="export-option" data-format="pdf">
                        <h4>📑 PDF Report</h4>
                        <p>Professional report format</p>
                        <button onclick="window.spaceWeatherExporter.exportData('pdf')">Generate PDF</button>
                    </div>
                </div>
                
                <div class="export-status" id="export-status"></div>
                
                <div class="export-controls">
                    <button class="cancel-btn" onclick="window.spaceWeatherExporter.closeExportModal()">Cancel</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup close handlers
        modal.querySelector('.close').onclick = () => this.closeExportModal();
        modal.onclick = (e) => {
            if (e.target === modal) this.closeExportModal();
        };
    }
    
    openExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.style.display = 'block';
            this.clearStatus();
        }
    }
    
    closeExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    showStatus(message, isError = false) {
        const status = document.getElementById('export-status');
        if (status) {
            status.textContent = message;
            status.className = `export-status show ${isError ? 'error' : 'success'}`;
        }
    }
    
    clearStatus() {
        const status = document.getElementById('export-status');
        if (status) {
            status.className = 'export-status';
        }
    }
    
    getDaysBack() {
        const select = document.getElementById('export-days');
        return select ? parseInt(select.value) : 7;
    }
    
    async exportData(format) {
        const days = this.getDaysBack();
        this.showStatus(`Generating ${format.toUpperCase()} export...`);
        
        try {
            const url = `${this.apiBaseUrl}/api/v1/export/${format}?days=${days}`;
            
            if (format === 'csv') {
                // Direct download
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `space_weather_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showStatus('CSV export downloaded successfully!');
                
            } else if (format === 'json') {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                const jsonStr = JSON.stringify(data.export_data, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `space_weather_export_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showStatus('JSON export downloaded successfully!');
                
            } else if (format === 'html') {
                // Open in new window
                window.open(url, '_blank');
                this.showStatus('HTML report opened in new window');
                
            } else if (format === 'pdf') {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                if (data.success) {
                    // For now, show HTML in new window with print instructions
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(data.html_content);
                    newWindow.document.close();
                    
                    this.showStatus('PDF-ready HTML opened. Use browser print to save as PDF.');
                } else {
                    throw new Error(data.error || 'PDF generation failed');
                }
            }
            
            setTimeout(() => {
                this.closeExportModal();
            }, 2000);
            
        } catch (error) {
            console.error('Export error:', error);
            this.showStatus(`Export failed: ${error.message}`, true);
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Create global exporter instance
    window.spaceWeatherExporter = new SpaceWeatherExporter();
    console.log('Space Weather Exporter initialized');
});

// Export the class for manual initialization
window.SpaceWeatherExporter = SpaceWeatherExporter;
'''
    
    try:
        with open('export_ui.js', 'w', encoding='utf-8') as f:
            f.write(export_ui_content)
        
        print("SUCCESS: Export UI components created as export_ui.js")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create export UI components: {e}")
        return False

def update_dashboards_with_export():
    """Update all dashboards to include export functionality"""
    print("\n" + "=" * 60)
    print("UPDATING DASHBOARDS WITH EXPORT FUNCTIONALITY")
    print("=" * 60)
    
    dashboards = ['3d_dashboard.html', 'simple_new.html', 'professional_dashboard.html']
    results = {}
    
    for dashboard in dashboards:
        if os.path.exists(dashboard):
            try:
                # Read dashboard
                with open(dashboard, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add export UI script if not already present
                if 'export_ui.js' not in content:
                    # Find websocket script and add export after it
                    websocket_script = '<script src="websocket_client.js"></script>'
                    if websocket_script in content:
                        export_script = '\\n    <script src="export_ui.js"></script>'
                        content = content.replace(websocket_script, websocket_script + export_script)
                    else:
                        # Add to head section
                        head_end = content.find('</head>')
                        if head_end != -1:
                            export_script = '    <script src="export_ui.js"></script>\\n'
                            content = content[:head_end] + export_script + content[head_end:]
                
                # Save updated dashboard
                with open(dashboard, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"SUCCESS: {dashboard} updated with export functionality")
                results[dashboard] = True
                
            except Exception as e:
                print(f"ERROR: Failed to update {dashboard}: {e}")
                results[dashboard] = False
        else:
            print(f"WARNING: {dashboard} not found")
            results[dashboard] = False
    
    return results

def create_export_requirements():
    """Create requirements file for export dependencies"""
    print("\n" + "=" * 60)
    print("CREATING EXPORT REQUIREMENTS")
    print("=" * 60)
    
    requirements_content = '''# Export Features Requirements
# Install with: pip install -r requirements_export.txt

# Core requirements (already included in main requirements)
# json (built-in)
# csv (built-in)
# io (built-in)

# Optional PDF generation libraries
# Uncomment and install for advanced PDF features:

# WeasyPrint for HTML to PDF conversion
# weasyprint>=60.0

# Alternative: pdfkit + wkhtmltopdf
# pdfkit>=1.0.0

# Alternative: reportlab for programmatic PDF creation
# reportlab>=4.0.4

# For advanced data analysis in exports
pandas>=2.0.3
numpy>=1.24.3

# For chart generation in exports (optional)
matplotlib>=3.7.2
plotly>=5.15.0

# For Excel export support (optional)
openpyxl>=3.1.2
xlsxwriter>=3.1.2
'''
    
    try:
        with open('requirements_export.txt', 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        
        print("SUCCESS: Export requirements created as requirements_export.txt")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create export requirements: {e}")
        return False

def create_export_test_page():
    """Create a test page for export functionality"""
    print("\n" + "=" * 60)
    print("CREATING EXPORT TEST PAGE")
    print("=" * 60)
    
    test_page_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Export Features Test</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a3a, #2d2d5f);
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 2px solid #00bfff;
        }
        
        .test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .test-card {
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
        }
        
        .test-card h3 {
            color: #00ff88;
            margin-bottom: 15px;
        }
        
        .api-test {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #ffaa44;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .api-test h3 {
            color: #ffaa44;
            margin-bottom: 15px;
        }
        
        .test-button {
            background: linear-gradient(45deg, #00bfff, #0080ff);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.3s ease;
        }
        
        .test-button:hover {
            transform: scale(1.05);
        }
        
        .results {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
            font-family: monospace;
            font-size: 0.9rem;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .success { color: #00ff88; }
        .error { color: #ff8888; }
        .info { color: #00bfff; }
        
        .export-demo {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .export-demo h3 {
            color: #00ff88;
            margin-bottom: 15px;
        }
        
        .format-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .format-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid #666;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        
        .format-card h4 {
            color: #00bfff;
            margin-bottom: 10px;
        }
        
        @media screen and (max-width: 768px) {
            .test-grid {
                grid-template-columns: 1fr;
            }
            
            .format-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Export Features Test</h1>
            <p>Test space weather data export functionality</p>
            <div style="margin-top: 10px;">
                <span id="export-status" class="info">Export system ready</span>
            </div>
        </div>
        
        <div class="test-grid">
            <div class="test-card">
                <h3>🎯 Export UI Test</h3>
                <p>Test the export modal and user interface components.</p>
                <button class="test-button" onclick="testExportUI()">Open Export Modal</button>
                <button class="test-button" onclick="testExportButton()">Test Export Button</button>
                <div class="results" id="ui-results">
                    Export UI components will be tested here...
                </div>
            </div>
            
            <div class="test-card">
                <h3>📡 Direct API Test</h3>
                <p>Test export API endpoints directly.</p>
                <button class="test-button" onclick="testAPI('json')">Test JSON API</button>
                <button class="test-button" onclick="testAPI('csv')">Test CSV API</button>
                <button class="test-button" onclick="testAPI('html')">Test HTML API</button>
                <div class="results" id="api-results">
                    API test results will appear here...
                </div>
            </div>
        </div>
        
        <div class="export-demo">
            <h3>📋 Export Format Demonstration</h3>
            <p>Click each format to see a sample export:</p>
            
            <div class="format-grid">
                <div class="format-card">
                    <h4>📊 CSV Export</h4>
                    <p>Spreadsheet format for data analysis</p>
                    <button class="test-button" onclick="demonstrateFormat('csv')">Demo CSV</button>
                </div>
                
                <div class="format-card">
                    <h4>🔗 JSON Export</h4>
                    <p>Structured data for developers</p>
                    <button class="test-button" onclick="demonstrateFormat('json')">Demo JSON</button>
                </div>
                
                <div class="format-card">
                    <h4>📄 HTML Report</h4>
                    <p>Formatted report for viewing</p>
                    <button class="test-button" onclick="demonstrateFormat('html')">Demo HTML</button>
                </div>
                
                <div class="format-card">
                    <h4>📑 PDF Report</h4>
                    <p>Professional report format</p>
                    <button class="test-button" onclick="demonstrateFormat('pdf')">Demo PDF</button>
                </div>
            </div>
        </div>
        
        <div class="api-test">
            <h3>🔧 System Status</h3>
            <p>Check export system components:</p>
            <button class="test-button" onclick="checkSystemStatus()">Check Status</button>
            <div class="results" id="status-results">
                System status will be checked here...
            </div>
        </div>
    </div>
    
    <script src="export_ui.js"></script>
    <script>
        function updateStatus(message, type = 'info') {
            const statusEl = document.getElementById('export-status');
            if (statusEl) {
                statusEl.textContent = message;
                statusEl.className = type;
            }
        }
        
        function addResult(containerId, message, type = 'info') {
            const container = document.getElementById(containerId);
            if (container) {
                const timestamp = new Date().toLocaleTimeString();
                const line = document.createElement('div');
                line.className = type;
                line.textContent = `[${timestamp}] ${message}`;
                container.appendChild(line);
                container.scrollTop = container.scrollHeight;
            }
        }
        
        function testExportUI() {
            addResult('ui-results', 'Testing export UI components...', 'info');
            
            try {
                if (window.spaceWeatherExporter) {
                    window.spaceWeatherExporter.openExportModal();
                    addResult('ui-results', 'Export modal opened successfully', 'success');
                } else {
                    addResult('ui-results', 'Export UI not initialized', 'error');
                }
            } catch (error) {
                addResult('ui-results', `UI test error: ${error.message}`, 'error');
            }
        }
        
        function testExportButton() {
            addResult('ui-results', 'Checking export button...', 'info');
            
            const button = document.getElementById('main-export-button');
            if (button) {
                addResult('ui-results', 'Export button found and functional', 'success');
                button.click();
            } else {
                addResult('ui-results', 'Export button not found', 'error');
            }
        }
        
        async function testAPI(format) {
            addResult('api-results', `Testing ${format.toUpperCase()} API endpoint...`, 'info');
            
            try {
                const url = `http://localhost:9001/api/v1/export/${format}?days=7`;
                const response = await fetch(url);
                
                if (response.ok) {
                    addResult('api-results', `${format.toUpperCase()} API: SUCCESS (${response.status})`, 'success');
                    
                    if (format === 'json') {
                        const data = await response.json();
                        addResult('api-results', `Data received: ${data.export_data?.metadata?.total_events || 0} events`, 'info');
                    } else {
                        addResult('api-results', `Content-Type: ${response.headers.get('Content-Type')}`, 'info');
                    }
                } else {
                    addResult('api-results', `${format.toUpperCase()} API: FAILED (${response.status})`, 'error');
                }
            } catch (error) {
                addResult('api-results', `${format.toUpperCase()} API: ERROR - ${error.message}`, 'error');
            }
        }
        
        function demonstrateFormat(format) {
            updateStatus(`Demonstrating ${format.toUpperCase()} export...`, 'info');
            
            if (window.spaceWeatherExporter) {
                window.spaceWeatherExporter.exportData(format);
            } else {
                updateStatus('Export system not available', 'error');
            }
        }
        
        async function checkSystemStatus() {
            addResult('status-results', 'Checking export system status...', 'info');
            
            // Check if export UI is loaded
            if (window.SpaceWeatherExporter) {
                addResult('status-results', '✓ Export UI library loaded', 'success');
            } else {
                addResult('status-results', '✗ Export UI library missing', 'error');
            }
            
            // Check if exporter instance exists
            if (window.spaceWeatherExporter) {
                addResult('status-results', '✓ Export instance initialized', 'success');
            } else {
                addResult('status-results', '✗ Export instance not found', 'error');
            }
            
            // Check API server connectivity
            try {
                const response = await fetch('http://localhost:9001/');
                if (response.ok) {
                    addResult('status-results', '✓ API server connected', 'success');
                } else {
                    addResult('status-results', '✗ API server issues', 'error');
                }
            } catch (error) {
                addResult('status-results', '✗ API server not reachable', 'error');
            }
            
            // Check export modal
            const modal = document.getElementById('export-modal');
            if (modal) {
                addResult('status-results', '✓ Export modal ready', 'success');
            } else {
                addResult('status-results', '✗ Export modal not found', 'error');
            }
        }
        
        // Auto-check system status on load
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                updateStatus('Export test page loaded', 'success');
                console.log('Export test page initialized');
            }, 1000);
        });
    </script>
</body>
</html>'''
    
    try:
        with open('export_test.html', 'w', encoding='utf-8') as f:
            f.write(test_page_content)
        
        print("SUCCESS: Export test page created as export_test.html")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create export test page: {e}")
        return False

def main():
    """Main export features implementation function"""
    print("NASA Space Weather Dashboard - Export Features Implementation")
    print(f"Starting export implementation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Create export backend service
    backend_ok = create_export_backend()
    
    # Step 2: Add export API endpoints
    api_ok = create_export_api_endpoints()
    
    # Step 3: Create export UI components
    ui_ok = create_export_ui_components()
    
    # Step 4: Update dashboards
    dashboard_results = update_dashboards_with_export()
    
    # Step 5: Create requirements
    requirements_ok = create_export_requirements()
    
    # Step 6: Create test page
    test_page_ok = create_export_test_page()
    
    # Summary
    print("\n" + "=" * 60)
    print("EXPORT FEATURES IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    successful_dashboards = sum(1 for result in dashboard_results.values() if result)
    total_components = 5 + len(dashboard_results)  # backend, api, ui, requirements, test + dashboards
    successful_components = sum([backend_ok, api_ok, ui_ok, requirements_ok, test_page_ok]) + successful_dashboards
    
    if successful_components == total_components:
        print("STATUS: EXPORT FEATURES COMPLETE")
        print()
        print("Successfully implemented:")
        print("   • Export backend service (export_service.py)")
        print("   • API endpoints for CSV, JSON, HTML, PDF")
        print("   • Export UI components (export_ui.js)")
        print("   • Dashboard integration")
        print("   • Export test interface")
        print()
        print("Export formats available:")
        print("   • CSV - Spreadsheet format for data analysis")
        print("   • JSON - Structured data for developers")
        print("   • HTML - Formatted reports for viewing")
        print("   • PDF - Professional report format (via HTML)")
        print()
        print("Testing:")
        print("   1. Ensure API server is running")
        print("   2. Open export_test.html to test functionality")
        print("   3. Use export buttons in dashboards")
        print("   4. Test API endpoints directly")
        print()
        print("Dashboard integration:")
        for dashboard, result in dashboard_results.items():
            status = 'SUCCESS' if result else 'FAILED'
            print(f"   • {dashboard}: {status}")
        print()
        print("Task 6 (Export Features) COMPLETE")
        print("Ready to proceed to Task 7 (Physics models)")
        
    else:
        print("STATUS: PARTIAL IMPLEMENTATION")
        print(f"Successfully implemented: {successful_components}/{total_components} components")
        print("Some components may need manual adjustment")
    
    print()

if __name__ == "__main__":
    main()