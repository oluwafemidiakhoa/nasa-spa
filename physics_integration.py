#!/usr/bin/env python3
"""
Physics Integration Service
Combines CME propagation, solar wind, and geomagnetic models for comprehensive forecasting
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add current directory to path for model imports
sys.path.append(os.path.dirname(__file__))

try:
    from cme_physics_model import CMEPropagationModel
    from solar_wind_model import SolarWindModel
    from geomagnetic_model import GeomagneticModel
except ImportError as e:
    print(f"Warning: Could not import physics models: {e}")
    print("Some physics features may not be available")

class PhysicsBasedForecaster:
    """Integrated physics-based space weather forecaster"""
    
    def __init__(self):
        try:
            self.cme_model = CMEPropagationModel()
            self.solar_wind_model = SolarWindModel()
            self.geomagnetic_model = GeomagneticModel()
            self.models_available = True
        except NameError:
            print("Physics models not available, using fallback methods")
            self.models_available = False
    
    def analyze_cme_event(self, cme_data: Dict) -> Dict:
        """
        Comprehensive CME analysis using physics models
        
        Args:
            cme_data: CME parameters from NASA DONKI
            
        Returns:
            Physics-based CME forecast
        """
        if not self.models_available:
            return self._fallback_cme_analysis(cme_data)
        
        try:
            # Extract CME parameters
            speed = self._extract_cme_speed(cme_data)
            start_time = cme_data.get('startTime', datetime.utcnow().isoformat() + 'Z')
            
            # Run ensemble CME propagation model
            propagation_result = self.cme_model.ensemble_prediction({'speed': speed})
            
            if 'error' in propagation_result:
                return {
                    'error': propagation_result['error'],
                    'cme_id': cme_data.get('activityID', 'Unknown')
                }
            
            # Calculate arrival time
            launch_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            arrival_time = launch_time + timedelta(hours=propagation_result['arrival_time_hours'])
            arrival_window_start = launch_time + timedelta(hours=propagation_result['arrival_window_start_hours'])
            arrival_window_end = launch_time + timedelta(hours=propagation_result['arrival_window_end_hours'])
            
            # Assess Earth impact potential
            earth_directed = self._assess_earth_direction(cme_data)
            
            # Calculate impact effects if Earth-directed
            if earth_directed:
                impact_effects = self._calculate_impact_effects(speed, propagation_result)
            else:
                impact_effects = {
                    'geomagnetic_effects': 'minimal',
                    'aurora_enhancement': 'none',
                    'radio_effects': 'none'
                }
            
            return {
                'physics_forecast': True,
                'cme_id': cme_data.get('activityID', 'Unknown'),
                'launch_time': start_time,
                'initial_speed_km_s': speed,
                'arrival_prediction': {
                    'arrival_time': arrival_time.isoformat() + 'Z',
                    'arrival_window_start': arrival_window_start.isoformat() + 'Z',
                    'arrival_window_end': arrival_window_end.isoformat() + 'Z',
                    'travel_time_hours': propagation_result['arrival_time_hours'],
                    'uncertainty_hours': propagation_result['uncertainty_hours']
                },
                'earth_directed': earth_directed,
                'impact_effects': impact_effects,
                'physics_models': {
                    'models_used': propagation_result['models_used'],
                    'confidence': propagation_result['confidence'],
                    'propagation_details': propagation_result
                }
            }
            
        except Exception as e:
            return {
                'error': f'Physics model error: {str(e)}',
                'cme_id': cme_data.get('activityID', 'Unknown')
            }
    
    def generate_solar_wind_forecast(self, forecast_hours: int = 72) -> List[Dict]:
        """
        Generate physics-based solar wind forecast
        
        Args:
            forecast_hours: Number of hours to forecast
            
        Returns:
            List of solar wind predictions
        """
        if not self.models_available:
            return self._fallback_solar_wind_forecast(forecast_hours)
        
        try:
            return self.solar_wind_model.predict_solar_wind_at_earth(forecast_hours)
        except Exception as e:
            print(f"Solar wind model error: {e}")
            return self._fallback_solar_wind_forecast(forecast_hours)
    
    def generate_geomagnetic_forecast(self, solar_wind_forecast: List[Dict] = None,
                                    observer_latitude: float = 60) -> List[Dict]:
        """
        Generate physics-based geomagnetic forecast
        
        Args:
            solar_wind_forecast: Solar wind predictions
            observer_latitude: Observer latitude for aurora predictions
            
        Returns:
            List of geomagnetic forecasts
        """
        if not self.models_available:
            return self._fallback_geomagnetic_forecast(48)
        
        if solar_wind_forecast is None:
            solar_wind_forecast = self.generate_solar_wind_forecast(48)
        
        try:
            return self.geomagnetic_model.comprehensive_geomagnetic_forecast(
                solar_wind_forecast, observer_latitude
            )
        except Exception as e:
            print(f"Geomagnetic model error: {e}")
            return self._fallback_geomagnetic_forecast(48)
    
    def comprehensive_space_weather_forecast(self, cme_events: List[Dict] = None,
                                           forecast_hours: int = 72) -> Dict:
        """
        Generate comprehensive space weather forecast using all physics models
        
        Args:
            cme_events: List of CME events to analyze
            forecast_hours: Forecast duration in hours
            
        Returns:
            Comprehensive forecast including all components
        """
        forecast_start = datetime.utcnow()
        
        # Solar wind baseline forecast
        solar_wind_forecast = self.generate_solar_wind_forecast(forecast_hours)
        
        # Geomagnetic forecast from solar wind
        geomagnetic_forecast = self.generate_geomagnetic_forecast(solar_wind_forecast)
        
        # CME analysis if events provided
        cme_forecasts = []
        if cme_events:
            for cme in cme_events:
                cme_forecast = self.analyze_cme_event(cme)
                if 'error' not in cme_forecast:
                    cme_forecasts.append(cme_forecast)
        
        # Combine forecasts and assess overall risk
        overall_risk = self._assess_overall_risk(cme_forecasts, geomagnetic_forecast)
        
        return {
            'forecast_metadata': {
                'generated_at': forecast_start.isoformat() + 'Z',
                'forecast_duration_hours': forecast_hours,
                'models_used': ['cme_propagation', 'solar_wind', 'geomagnetic'] if self.models_available else ['statistical'],
                'physics_based': self.models_available
            },
            'solar_wind_forecast': solar_wind_forecast,
            'geomagnetic_forecast': geomagnetic_forecast,
            'cme_forecasts': cme_forecasts,
            'overall_assessment': {
                'risk_level': overall_risk['level'],
                'confidence': overall_risk['confidence'],
                'key_concerns': overall_risk['concerns'],
                'recommendations': overall_risk['recommendations']
            },
            'summary_statistics': {
                'num_cmes_analyzed': len(cme_forecasts),
                'max_kp_predicted': max([f.get('kp_index', 0) for f in geomagnetic_forecast] + [0]),
                'min_dst_predicted': min([f.get('dst_nt', 0) for f in geomagnetic_forecast] + [0]),
                'aurora_probability_max': max([f.get('aurora_probability', 0) for f in geomagnetic_forecast] + [0])
            }
        }
    
    def _extract_cme_speed(self, cme_data: Dict) -> float:
        """Extract CME speed from DONKI data"""
        # Try to get speed from analysis data
        analyses = cme_data.get('cmeAnalyses', [])
        if analyses:
            speed = analyses[0].get('speed')
            if speed:
                return float(speed)
        
        # Fallback to typical speed
        return 500.0  # km/s
    
    def _assess_earth_direction(self, cme_data: Dict) -> bool:
        """Assess if CME is Earth-directed"""
        # Simple heuristic based on source location and analysis
        source = cme_data.get('sourceLocation', '')
        
        # Check for Earth-facing hemisphere
        if 'W' in source or 'E' in source:
            # Extract longitude
            try:
                if 'W' in source:
                    lon = -float(source.split('W')[1] if len(source.split('W')) > 1 else source.split('W')[0])
                else:
                    lon = float(source.split('E')[1] if len(source.split('E')) > 1 else source.split('E')[0])
                
                # Earth-directed if longitude is roughly facing Earth
                return abs(lon) < 90
            except:
                pass
        
        # Check CME analysis for Earth-directed flag (if available)
        # This is a simplified heuristic
        return True  # Assume Earth-directed for conservative forecasting
    
    def _calculate_impact_effects(self, speed: float, propagation_result: Dict) -> Dict:
        """Calculate expected impact effects from CME"""
        effects = {
            'geomagnetic_effects': 'minor',
            'aurora_enhancement': 'possible',
            'radio_effects': 'minimal'
        }
        
        # Scale effects based on CME speed
        if speed > 1000:
            effects['geomagnetic_effects'] = 'major'
            effects['aurora_enhancement'] = 'likely'
            effects['radio_effects'] = 'moderate'
        elif speed > 700:
            effects['geomagnetic_effects'] = 'moderate'
            effects['aurora_enhancement'] = 'likely'
            effects['radio_effects'] = 'minor'
        
        return effects
    
    def _assess_overall_risk(self, cme_forecasts: List[Dict], 
                           geomagnetic_forecast: List[Dict]) -> Dict:
        """Assess overall space weather risk"""
        risk_level = 'low'
        concerns = []
        recommendations = []
        confidence = 0.8
        
        # Check for high-speed CMEs
        high_speed_cmes = [c for c in cme_forecasts if c.get('initial_speed_km_s', 0) > 800]
        if high_speed_cmes:
            risk_level = 'high'
            concerns.append('High-speed CME detected')
            recommendations.append('Monitor geomagnetic conditions closely')
        
        # Check geomagnetic activity
        max_kp = max([f.get('kp_index', 0) for f in geomagnetic_forecast] + [0])
        if max_kp > 6:
            risk_level = 'high'
            concerns.append('Strong geomagnetic activity expected')
            recommendations.append('Aurora may be visible at lower latitudes')
        elif max_kp > 4:
            risk_level = 'moderate'
            concerns.append('Moderate geomagnetic activity expected')
        
        return {
            'level': risk_level,
            'confidence': confidence,
            'concerns': concerns,
            'recommendations': recommendations
        }
    
    def _fallback_cme_analysis(self, cme_data: Dict) -> Dict:
        """Fallback CME analysis when physics models unavailable"""
        speed = self._extract_cme_speed(cme_data)
        
        # Simple empirical relationship: travel_time = 149.6e6 km / speed
        travel_time_hours = 149.6e6 / speed / 3600 if speed > 0 else 72
        
        start_time = cme_data.get('startTime', datetime.utcnow().isoformat() + 'Z')
        launch_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        arrival_time = launch_time + timedelta(hours=travel_time_hours)
        
        return {
            'physics_forecast': False,
            'cme_id': cme_data.get('activityID', 'Unknown'),
            'launch_time': start_time,
            'initial_speed_km_s': speed,
            'arrival_prediction': {
                'arrival_time': arrival_time.isoformat() + 'Z',
                'travel_time_hours': travel_time_hours,
                'uncertainty_hours': 12
            },
            'earth_directed': True,
            'impact_effects': {
                'geomagnetic_effects': 'moderate' if speed > 600 else 'minor',
                'aurora_enhancement': 'possible',
                'radio_effects': 'minimal'
            },
            'note': 'Simplified model - physics models not available'
        }
    
    def _fallback_solar_wind_forecast(self, hours: int) -> List[Dict]:
        """Fallback solar wind forecast"""
        forecast = []
        for hour in range(hours):
            forecast.append({
                'forecast_hour': hour,
                'timestamp': (datetime.utcnow() + timedelta(hours=hour)).isoformat() + 'Z',
                'wind_speed_km_s': 400 + 50 * math.sin(hour * 0.1),  # Simple variation
                'density_cm3': 5,
                'magnetic_field_nt': 5,
                'temperature_k': 1e5,
                'model_confidence': 0.5
            })
        return forecast
    
    def _fallback_geomagnetic_forecast(self, hours: int) -> List[Dict]:
        """Fallback geomagnetic forecast"""
        forecast = []
        for hour in range(hours):
            forecast.append({
                'forecast_hour': hour,
                'timestamp': (datetime.utcnow() + timedelta(hours=hour)).isoformat() + 'Z',
                'dst_nt': -20,
                'kp_index': 2,
                'activity_level': 'quiet',
                'aurora_visibility': 'not_visible',
                'model_confidence': 0.5
            })
        return forecast

def test_physics_integration():
    """Test the integrated physics forecasting system"""
    print("Testing Physics Integration Service...")
    
    forecaster = PhysicsBasedForecaster()
    
    # Test CME analysis
    test_cme = {
        'activityID': 'TEST-CME-001',
        'startTime': '2025-09-28T12:00:00Z',
        'sourceLocation': 'N15W20',
        'cmeAnalyses': [{'speed': 800}]
    }
    
    print("\nTesting CME analysis:")
    cme_result = forecaster.analyze_cme_event(test_cme)
    if 'error' not in cme_result:
        print(f"  CME {cme_result['cme_id']}: {cme_result['initial_speed_km_s']} km/s")
        print(f"  Arrival: {cme_result['arrival_prediction']['arrival_time']}")
        print(f"  Confidence: {cme_result['physics_models']['confidence']:.2f}")
    
    # Test comprehensive forecast
    print("\nTesting comprehensive forecast:")
    comprehensive = forecaster.comprehensive_space_weather_forecast([test_cme], 48)
    print(f"  Overall risk: {comprehensive['overall_assessment']['risk_level']}")
    print(f"  Max Kp: {comprehensive['summary_statistics']['max_kp_predicted']:.1f}")
    print(f"  Models used: {', '.join(comprehensive['forecast_metadata']['models_used'])}")

if __name__ == "__main__":
    import math  # Add this for fallback methods
    test_physics_integration()
