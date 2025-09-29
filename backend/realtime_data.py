"""
Real-time Space Weather Data Integration
Fetches live data from multiple sources including NOAA, NASA, and ESA
"""

import requests
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RealTimeSpaceWeatherData:
    """Real-time space weather data fetcher"""
    
    def __init__(self):
        self.sources = {
            'noaa_swpc': 'https://services.swpc.noaa.gov/json',
            'noaa_ace': 'https://services.swpc.noaa.gov/json/rtsw',
            'esa_swe': 'https://swe.ssa.esa.int/web-services',
        }
        
    def get_current_solar_wind(self) -> Dict[str, Any]:
        """Get current solar wind conditions from NOAA ACE satellite"""
        try:
            # NOAA Real-Time Solar Wind from ACE satellite
            ace_url = f"{self.sources['noaa_swpc']}/ace_swepam_1m.json"
            response = requests.get(ace_url, timeout=10)
            response.raise_for_status()
            
            ace_data = response.json()
            if not ace_data:
                raise Exception("No ACE solar wind data available")
            
            latest = ace_data[-1]  # Most recent measurement
            
            # Get magnetic field data
            mag_url = f"{self.sources['noaa_swpc']}/ace_mag_1m.json"
            mag_response = requests.get(mag_url, timeout=10)
            mag_data = mag_response.json() if mag_response.status_code == 200 else []
            
            mag_latest = mag_data[-1] if mag_data else {}
            
            return {
                'timestamp': latest.get('time_tag', ''),
                'velocity': float(latest.get('bulk_speed', 400)),
                'density': float(latest.get('density', 5)),
                'temperature': float(latest.get('temperature', 100000)),
                'bx_gsm': float(mag_latest.get('bx', 0)),
                'by_gsm': float(mag_latest.get('by', 0)),
                'bz_gsm': float(mag_latest.get('bz', 0)),
                'bt': float(mag_latest.get('bt', 5)),
                'source': 'NOAA_ACE',
                'quality': 'real_time'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch ACE solar wind data: {e}")
            # Return estimated values based on typical conditions
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'velocity': 450.0,
                'density': 5.0,
                'temperature': 100000,
                'bx_gsm': 2.0,
                'by_gsm': 3.0,
                'bz_gsm': -2.0,
                'bt': 5.0,
                'source': 'ESTIMATED',
                'quality': 'fallback'
            }
    
    def get_current_geomagnetic_indices(self) -> Dict[str, Any]:
        """Get current geomagnetic indices (Kp, Dst, etc.)"""
        try:
            # NOAA Planetary K-index
            kp_url = f"{self.sources['noaa_swpc']}/planetary_k_index_1m.json"
            response = requests.get(kp_url, timeout=10)
            response.raise_for_status()
            
            kp_data = response.json()
            latest_kp = kp_data[-1] if kp_data else {}
            
            # Estimated Dst from Kp (approximate relationship)
            kp_value = float(latest_kp.get('kp_index', 2))
            estimated_dst = self._kp_to_dst_estimate(kp_value)
            
            return {
                'kp_index': kp_value,
                'kp_timestamp': latest_kp.get('time_tag', ''),
                'estimated_dst': estimated_dst,
                'ap_index': float(latest_kp.get('a_index', 7)),
                'source': 'NOAA_SWPC',
                'quality': 'real_time'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch geomagnetic indices: {e}")
            return {
                'kp_index': 2.0,
                'estimated_dst': -20.0,
                'ap_index': 7.0,
                'source': 'ESTIMATED',
                'quality': 'fallback'
            }
    
    def get_solar_xray_flux(self) -> Dict[str, Any]:
        """Get current solar X-ray flux levels"""
        try:
            xray_url = f"{self.sources['noaa_swpc']}/goes_xray_flux_1m.json"
            response = requests.get(xray_url, timeout=10)
            response.raise_for_status()
            
            xray_data = response.json()
            latest = xray_data[-1] if xray_data else {}
            
            # Parse flux levels
            flux_short = float(latest.get('flux_short', 1e-6))
            flux_long = float(latest.get('flux_long', 1e-7))
            
            # Determine flare class
            flare_class = self._determine_flare_class(flux_long)
            
            return {
                'timestamp': latest.get('time_tag', ''),
                'flux_short_1_8A': flux_short,
                'flux_long_0_5_4A': flux_long,
                'flare_class': flare_class,
                'background_subtracted': True,
                'source': 'NOAA_GOES',
                'quality': 'real_time'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch X-ray flux: {e}")
            return {
                'flux_short_1_8A': 1e-6,
                'flux_long_0_5_4A': 1e-7,
                'flare_class': 'A',
                'source': 'ESTIMATED',
                'quality': 'fallback'
            }
    
    def get_solar_energetic_particles(self) -> Dict[str, Any]:
        """Get solar energetic particle measurements"""
        try:
            sep_url = f"{self.sources['noaa_swpc']}/goes_proton_flux_1m.json"
            response = requests.get(sep_url, timeout=10)
            response.raise_for_status()
            
            sep_data = response.json()
            latest = sep_data[-1] if sep_data else {}
            
            # Parse proton flux channels
            channels = {
                'proton_flux_10MeV': float(latest.get('channel_1', 1)),
                'proton_flux_50MeV': float(latest.get('channel_2', 0.1)),
                'proton_flux_100MeV': float(latest.get('channel_3', 0.01)),
            }
            
            # Determine SEP event level
            sep_level = self._determine_sep_level(channels['proton_flux_10MeV'])
            
            return {
                'timestamp': latest.get('time_tag', ''),
                'proton_channels': channels,
                'sep_event_level': sep_level,
                'radiation_storm_scale': self._sep_to_s_scale(channels['proton_flux_10MeV']),
                'source': 'NOAA_GOES',
                'quality': 'real_time'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch SEP data: {e}")
            return {
                'proton_channels': {'proton_flux_10MeV': 1, 'proton_flux_50MeV': 0.1},
                'sep_event_level': 'background',
                'radiation_storm_scale': 'S0',
                'source': 'ESTIMATED',
                'quality': 'fallback'
            }
    
    def get_comprehensive_space_weather(self) -> Dict[str, Any]:
        """Get comprehensive real-time space weather snapshot"""
        logger.info("Fetching comprehensive real-time space weather data...")
        
        data = {
            'fetch_time': datetime.utcnow().isoformat() + 'Z',
            'solar_wind': self.get_current_solar_wind(),
            'geomagnetic': self.get_current_geomagnetic_indices(),
            'xray_flux': self.get_solar_xray_flux(),
            'energetic_particles': self.get_solar_energetic_particles(),
            'alerts': self._get_space_weather_alerts(),
            'summary': {}
        }
        
        # Generate summary
        data['summary'] = self._generate_conditions_summary(data)
        
        return data
    
    def _get_space_weather_alerts(self) -> List[Dict[str, Any]]:
        """Get current space weather alerts and warnings"""
        try:
            alerts_url = f"{self.sources['noaa_swpc']}/alerts.json"
            response = requests.get(alerts_url, timeout=10)
            response.raise_for_status()
            
            alerts_data = response.json()
            
            # Filter recent alerts (last 24 hours)
            recent_alerts = []
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for alert in alerts_data:
                try:
                    alert_time = datetime.fromisoformat(alert.get('issue_datetime', '').replace('Z', '+00:00'))
                    if alert_time > cutoff_time:
                        recent_alerts.append({
                            'type': alert.get('product_id', ''),
                            'message': alert.get('message', ''),
                            'issue_time': alert.get('issue_datetime', ''),
                            'serial_number': alert.get('serial_number', '')
                        })
                except:
                    continue
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Failed to fetch space weather alerts: {e}")
            return []
    
    def _generate_conditions_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall space weather conditions summary"""
        
        summary = {
            'overall_condition': 'quiet',
            'activity_level': 'low',
            'concerns': [],
            'highlights': []
        }
        
        # Analyze solar wind
        sw = data['solar_wind']
        if sw['velocity'] > 600:
            summary['concerns'].append('High-speed solar wind stream')
            summary['activity_level'] = 'elevated'
        
        if sw['bz_gsm'] < -10:
            summary['concerns'].append('Strong southward magnetic field')
            summary['activity_level'] = 'elevated'
        
        # Analyze geomagnetic activity
        geo = data['geomagnetic']
        if geo['kp_index'] >= 5:
            summary['concerns'].append('Active geomagnetic conditions')
            summary['overall_condition'] = 'active'
            
        if geo['kp_index'] >= 7:
            summary['concerns'].append('Geomagnetic storm in progress')
            summary['overall_condition'] = 'stormy'
        
        # Analyze X-ray flux
        xray = data['xray_flux']
        if xray['flare_class'] in ['M', 'X']:
            summary['highlights'].append(f"Solar flare activity: {xray['flare_class']}-class")
            
        # Analyze particle flux
        sep = data['energetic_particles']
        if sep['sep_event_level'] != 'background':
            summary['concerns'].append('Elevated solar particle flux')
        
        # Check alerts
        if data['alerts']:
            summary['concerns'].append(f"{len(data['alerts'])} active space weather alerts")
        
        # Determine overall condition
        if len(summary['concerns']) >= 3:
            summary['overall_condition'] = 'disturbed'
        elif len(summary['concerns']) >= 1:
            summary['overall_condition'] = 'unsettled'
        
        return summary
    
    # Utility functions
    def _kp_to_dst_estimate(self, kp: float) -> float:
        """Rough estimate of Dst from Kp index"""
        # Empirical relationship (very approximate)
        if kp <= 3:
            return -15 * kp
        else:
            return -45 - 20 * (kp - 3)
    
    def _determine_flare_class(self, flux: float) -> str:
        """Determine solar flare class from X-ray flux"""
        if flux >= 1e-3:
            return 'X'
        elif flux >= 1e-4:
            return 'M'
        elif flux >= 1e-5:
            return 'C'
        elif flux >= 1e-6:
            return 'B'
        else:
            return 'A'
    
    def _determine_sep_level(self, flux_10mev: float) -> str:
        """Determine SEP event level"""
        if flux_10mev >= 1000:
            return 'major_event'
        elif flux_10mev >= 100:
            return 'moderate_event'
        elif flux_10mev >= 10:
            return 'minor_event'
        else:
            return 'background'
    
    def _sep_to_s_scale(self, flux_10mev: float) -> str:
        """Convert SEP flux to NOAA S-scale"""
        if flux_10mev >= 10000:
            return 'S4'
        elif flux_10mev >= 1000:
            return 'S3'
        elif flux_10mev >= 100:
            return 'S2'
        elif flux_10mev >= 10:
            return 'S1'
        else:
            return 'S0'

# Convenience function
def get_realtime_space_weather() -> Dict[str, Any]:
    """Get comprehensive real-time space weather data"""
    fetcher = RealTimeSpaceWeatherData()
    return fetcher.get_comprehensive_space_weather()

if __name__ == "__main__":
    # Test the real-time data fetcher
    data = get_realtime_space_weather()
    print(json.dumps(data, indent=2, default=str))