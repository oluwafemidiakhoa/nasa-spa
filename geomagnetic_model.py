#!/usr/bin/env python3
"""
Geomagnetic Field Physics Model
Implements geomagnetic indices calculation and disturbance prediction
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class GeomagneticModel:
    """Physics-based geomagnetic field model"""
    
    def __init__(self):
        # Earth parameters
        self.earth_radius = 6.371e6  # meters
        self.earth_magnetic_moment = 7.94e22  # A⋅m²
        self.dipole_tilt = 11.5  # degrees
        
        # Magnetosphere parameters
        self.magnetopause_standoff = 10  # Earth radii (typical)
        
    def dst_index_model(self, solar_wind_params: Dict) -> Dict:
        """
        Calculate Dst index from solar wind parameters
        Using Burton equation and similar empirical relationships
        
        Args:
            solar_wind_params: Dictionary with solar wind data
            
        Returns:
            Dst prediction and related indices
        """
        # Extract solar wind parameters
        v_sw = solar_wind_params.get('wind_speed_km_s', 400)  # km/s
        b_sw = solar_wind_params.get('magnetic_field_nt', 5)   # nT
        n_sw = solar_wind_params.get('density_cm3', 5)         # cm⁻³
        
        # Assume southward Bz component (most geoeffective)
        # In reality, this would come from IMF measurements
        bz_south = -abs(b_sw * 0.5)  # Simplified assumption
        
        # Calculate solar wind dynamic pressure
        # P = ρ * v² = n * mp * v²
        proton_mass = 1.67e-27  # kg
        v_sw_ms = v_sw * 1000   # m/s
        n_sw_m3 = n_sw * 1e6    # m⁻³
        
        dynamic_pressure = n_sw_m3 * proton_mass * v_sw_ms**2  # Pa
        dynamic_pressure_npa = dynamic_pressure * 1e9  # nPa
        
        # Calculate magnetopause standoff distance
        # R_mp = (2μ₀P_sw)^(-1/6) in Earth radii (simplified)
        standoff_distance = 10.22 * (dynamic_pressure_npa)**(-1/6.6)
        
        # Calculate ring current injection rate (Burton equation approach)
        # dDst/dt = Q(t) - Dst(t)/τ
        # Q(t) is injection function, τ is decay time
        
        # Injection function Q (empirical relationship)
        if bz_south < 0:  # Southward IMF
            # Enhanced injection for southward Bz
            electric_field = v_sw * abs(bz_south) * 1e-3  # mV/m
            
            # Empirical injection rate
            if electric_field > 0.5:
                injection_rate = -4 * (electric_field - 0.5)**1.5  # nT/hr
            else:
                injection_rate = 0
        else:
            injection_rate = 0
        
        # Decay time constant (typically 6-10 hours)
        decay_time = 8  # hours
        
        # Pressure correction for Dst
        # Dst_corrected = Dst_measured + b*sqrt(Pdyn)
        pressure_correction = 7.26 * math.sqrt(dynamic_pressure_npa)  # nT
        
        # Calculate steady-state Dst
        if injection_rate != 0:
            dst_steady_state = injection_rate * decay_time
        else:
            dst_steady_state = 0
        
        # Simple Dst prediction (quasi-steady state)
        dst_predicted = dst_steady_state - pressure_correction
        
        # Classify geomagnetic activity
        if dst_predicted > -30:
            activity_level = 'quiet'
            storm_category = None
        elif dst_predicted > -50:
            activity_level = 'minor_storm'
            storm_category = 'G1'
        elif dst_predicted > -100:
            activity_level = 'moderate_storm'
            storm_category = 'G2'
        elif dst_predicted > -200:
            activity_level = 'strong_storm'
            storm_category = 'G3'
        else:
            activity_level = 'severe_storm'
            storm_category = 'G4+'
        
        return {
            'model_type': 'dst_index',
            'dst_predicted_nt': dst_predicted,
            'injection_rate_nt_hr': injection_rate,
            'decay_time_hr': decay_time,
            'pressure_correction_nt': pressure_correction,
            'electric_field_mv_m': electric_field if bz_south < 0 else 0,
            'dynamic_pressure_npa': dynamic_pressure_npa,
            'magnetopause_distance_re': standoff_distance,
            'activity_level': activity_level,
            'storm_category': storm_category,
            'bz_imf_nt': bz_south,
            'solar_wind_speed_km_s': v_sw
        }
    
    def kp_index_model(self, solar_wind_params: Dict) -> Dict:
        """
        Calculate Kp index from solar wind parameters
        
        Args:
            solar_wind_params: Dictionary with solar wind data
            
        Returns:
            Kp prediction
        """
        v_sw = solar_wind_params.get('wind_speed_km_s', 400)
        b_sw = solar_wind_params.get('magnetic_field_nt', 5)
        n_sw = solar_wind_params.get('density_cm3', 5)
        
        # Assume Bz component
        bz = -abs(b_sw * 0.5)  # Southward
        
        # Calculate coupling function (Newell et al.)
        # Coupling ∝ v^(4/3) * B_t^(2/3) * sin^8(θ/2)
        # where θ is IMF clock angle
        
        if bz < 0:
            # Southward IMF - high coupling
            clock_angle = math.pi  # 180 degrees
            bt = abs(b_sw)  # Total transverse field
        else:
            # Northward IMF - low coupling
            clock_angle = 0
            bt = 0.1  # Minimal coupling
        
        # Newell coupling function (simplified)
        coupling = (v_sw/1000)**(4/3) * bt**(2/3) * (math.sin(clock_angle/2))**8
        
        # Convert coupling to Kp (empirical relationship)
        if coupling < 0.1:
            kp = 0
        elif coupling < 0.5:
            kp = 1 + 2 * coupling
        elif coupling < 2.0:
            kp = 2 + 2 * (coupling - 0.5)
        elif coupling < 5.0:
            kp = 5 + (coupling - 2.0)
        else:
            kp = min(9, 8 + (coupling - 5.0) / 2)
        
        # Kp activity levels
        if kp < 3:
            activity = 'quiet'
            g_scale = None
        elif kp < 4:
            activity = 'unsettled'
            g_scale = None
        elif kp < 5:
            activity = 'active'
            g_scale = 'G1'
        elif kp < 6:
            activity = 'minor_storm'
            g_scale = 'G1'
        elif kp < 7:
            activity = 'moderate_storm'
            g_scale = 'G2'
        elif kp < 8:
            activity = 'strong_storm'
            g_scale = 'G3'
        else:
            activity = 'severe_storm'
            g_scale = 'G4+'
        
        return {
            'model_type': 'kp_index',
            'kp_predicted': kp,
            'coupling_function': coupling,
            'clock_angle_deg': math.degrees(clock_angle),
            'activity_level': activity,
            'g_scale': g_scale,
            'confidence': 0.7 if coupling > 1.0 else 0.8
        }
    
    def aurora_model(self, kp_index: float, observer_lat: float = 65) -> Dict:
        """
        Model aurora visibility based on Kp index
        
        Args:
            kp_index: Planetary Kp index
            observer_lat: Observer latitude in degrees
            
        Returns:
            Aurora visibility prediction
        """
        # Empirical relationship between Kp and aurora oval boundary
        # Aurora oval typically at ~67° magnetic latitude during quiet times
        
        # Convert geographic to approximate magnetic latitude (simplified)
        # This is a very rough approximation
        magnetic_lat = observer_lat - 10  # Magnetic pole offset
        
        # Aurora oval boundary as function of Kp
        if kp_index < 1:
            aurora_boundary = 67  # degrees magnetic latitude
        elif kp_index < 3:
            aurora_boundary = 65 - 2 * (kp_index - 1)
        elif kp_index < 5:
            aurora_boundary = 61 - 3 * (kp_index - 3)
        elif kp_index < 7:
            aurora_boundary = 55 - 4 * (kp_index - 5)
        else:
            aurora_boundary = max(35, 47 - 6 * (kp_index - 7))
        
        # Determine visibility
        if abs(magnetic_lat) >= aurora_boundary:
            visibility = 'visible'
            if kp_index >= 6:
                intensity = 'bright'
            elif kp_index >= 4:
                intensity = 'moderate'
            else:
                intensity = 'faint'
        else:
            visibility = 'not_visible'
            intensity = None
        
        # Distance from aurora oval
        distance_from_oval = abs(magnetic_lat) - aurora_boundary
        
        return {
            'model_type': 'aurora_visibility',
            'observer_latitude': observer_lat,
            'magnetic_latitude': magnetic_lat,
            'kp_index': kp_index,
            'aurora_boundary_lat': aurora_boundary,
            'visibility': visibility,
            'intensity': intensity,
            'distance_from_oval_deg': distance_from_oval,
            'probability': max(0, min(1, (kp_index - 2) / 6)) if visibility == 'visible' else 0
        }
    
    def comprehensive_geomagnetic_forecast(self, solar_wind_forecast: List[Dict], 
                                         observer_lat: float = 65) -> List[Dict]:
        """
        Generate comprehensive geomagnetic forecast
        
        Args:
            solar_wind_forecast: List of solar wind predictions
            observer_lat: Observer latitude for aurora predictions
            
        Returns:
            List of geomagnetic forecasts
        """
        forecasts = []
        
        for sw_data in solar_wind_forecast:
            # Calculate Dst
            dst_result = self.dst_index_model(sw_data)
            
            # Calculate Kp
            kp_result = self.kp_index_model(sw_data)
            
            # Calculate aurora visibility
            aurora_result = self.aurora_model(kp_result['kp_predicted'], observer_lat)
            
            # Combine results
            forecast = {
                'timestamp': sw_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                'forecast_hour': sw_data.get('forecast_hour', 0),
                
                # Geomagnetic indices
                'dst_nt': dst_result['dst_predicted_nt'],
                'kp_index': kp_result['kp_predicted'],
                
                # Activity classification
                'activity_level': dst_result['activity_level'],
                'storm_category': dst_result['storm_category'],
                'g_scale': kp_result['g_scale'],
                
                # Aurora
                'aurora_visibility': aurora_result['visibility'],
                'aurora_intensity': aurora_result['intensity'],
                'aurora_probability': aurora_result['probability'],
                
                # Physics parameters
                'magnetopause_distance_re': dst_result['magnetopause_distance_re'],
                'coupling_function': kp_result['coupling_function'],
                'electric_field_mv_m': dst_result['electric_field_mv_m'],
                
                # Confidence
                'model_confidence': min(kp_result['confidence'], 0.8),
                
                # Source data
                'solar_wind_speed_km_s': sw_data.get('wind_speed_km_s'),
                'solar_wind_density_cm3': sw_data.get('density_cm3'),
                'imf_magnitude_nt': sw_data.get('magnetic_field_nt')
            }
            
            forecasts.append(forecast)
        
        return forecasts

def test_geomagnetic_model():
    """Test the geomagnetic models"""
    print("Testing Geomagnetic Models...")
    
    model = GeomagneticModel()
    
    # Test different solar wind conditions
    test_conditions = [
        {'wind_speed_km_s': 350, 'magnetic_field_nt': 3, 'density_cm3': 8, 'name': 'Quiet'},
        {'wind_speed_km_s': 500, 'magnetic_field_nt': 8, 'density_cm3': 5, 'name': 'Active'},
        {'wind_speed_km_s': 700, 'magnetic_field_nt': 15, 'density_cm3': 3, 'name': 'Storm'}
    ]
    
    for condition in test_conditions:
        print(f"\n{condition['name']} conditions:")
        
        dst_result = model.dst_index_model(condition)
        print(f"  Dst: {dst_result['dst_predicted_nt']:.0f} nT ({dst_result['activity_level']})")
        
        kp_result = model.kp_index_model(condition)
        print(f"  Kp: {kp_result['kp_predicted']:.1f} ({kp_result['activity_level']})")
        
        aurora_result = model.aurora_model(kp_result['kp_predicted'], 65)
        print(f"  Aurora at 65°N: {aurora_result['visibility']} ({aurora_result['intensity']})")

if __name__ == "__main__":
    test_geomagnetic_model()
