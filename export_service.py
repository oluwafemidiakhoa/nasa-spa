#!/usr/bin/env python3
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
                    'note': cme.get('note', '')[:200] + '...' if len(cme.get('note', '')) > 200 else cme.get('note', '')
                })
            
            # Process Solar Flares
            for flare in events.get('flares', []):
                processed_events.append({
                    'type': 'Solar Flare',
                    'id': flare.get('flrID', 'Unknown'),
                    'start_time': flare.get('beginTime', ''),
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
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when NASA API is unavailable"""
        return {
            'metadata': {
                'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                'data_period': '7 days',
                'total_events': 2,
                'cme_count': 1,
                'flare_count': 1,
                'data_source': 'Demo Data (NASA API unavailable)'
            },
            'events': [
                {
                    'type': 'CME',
                    'id': 'DEMO-CME-001',
                    'start_time': '2025-09-27T14:36:00Z',
                    'source_location': 'N15W20',
                    'speed': 450.0,
                    'note': 'Demo CME event for export testing'
                },
                {
                    'type': 'Solar Flare',
                    'id': 'DEMO-FLR-001',
                    'start_time': '2025-09-27T12:15:00Z',
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
    
    print()
    print("Export service test completed successfully!")

if __name__ == "__main__":
    main()