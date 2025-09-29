#!/usr/bin/env python3
"""
Solar Wind Physics Model
Implements solar wind speed and density calculations for space weather forecasting
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class SolarWindModel:
    """Physics-based solar wind model"""
    
    def __init__(self):
        # Solar parameters
        self.solar_radius = 6.96e8  # meters
        self.solar_mass = 1.989e30  # kg
        self.corona_temperature = 2e6  # Kelvin (typical)
        
        # Physical constants
        self.k_boltzmann = 1.38e-23  # J/K
        self.proton_mass = 1.67e-27  # kg
        self.gravitational_constant = 6.67e-11  # m³/kg/s²
        
        # Model parameters
        self.base_density = 5e6  # particles/m³ at 1 AU
        self.base_speed = 400  # km/s (typical slow solar wind)
        
    def parker_solar_wind_model(self, distance_au: float = 1.0, 
                               corona_temp: float = None) -> Dict:
        """
        Parker solar wind model for speed and density at given distance
        
        Args:
            distance_au: Distance from Sun in AU
            corona_temp: Coronal temperature in Kelvin
            
        Returns:
            Solar wind parameters at specified distance
        """
        if corona_temp is None:
            corona_temp = self.corona_temperature
        
        # Convert distance to meters
        distance = distance_au * 1.496e11
        
        # Calculate escape velocity at solar surface
        v_escape = math.sqrt(2 * self.gravitational_constant * self.solar_mass / self.solar_radius)
        
        # Sound speed in corona
        # cs = sqrt(kT/mp) for fully ionized hydrogen
        sound_speed = math.sqrt(self.k_boltzmann * corona_temp / self.proton_mass)
        
        # Critical radius where wind speed equals sound speed
        r_critical = self.gravitational_constant * self.solar_mass / (2 * sound_speed**2)
        
        # Simplified Parker solution for wind speed
        # For distances >> critical radius, asymptotic speed
        if distance > 10 * r_critical:
            # Asymptotic wind speed
            wind_speed = math.sqrt(4 * sound_speed**2 - 2 * self.gravitational_constant * self.solar_mass / distance)
        else:
            # Approximate solution for inner regions
            wind_speed = sound_speed * math.sqrt(distance / r_critical)
        
        # Convert to km/s
        wind_speed_km_s = wind_speed / 1000
        
        # Solar wind density using mass conservation
        # ρ(r) = ρ₀ * (r₀/r)² * (v₀/v)
        # Assuming constant mass flux
        reference_distance = 1.496e11  # 1 AU
        reference_speed = self.base_speed * 1000  # m/s
        
        density_scaling = (reference_distance / distance)**2 * (reference_speed / wind_speed)
        density = self.base_density * density_scaling
        
        # Convert to particles/cm³
        density_cm3 = density / 1e6
        
        return {
            'model_type': 'parker_solar_wind',
            'distance_au': distance_au,
            'wind_speed_km_s': wind_speed_km_s,
            'density_cm3': density_cm3,
            'temperature_k': corona_temp,
            'sound_speed_km_s': sound_speed / 1000,
            'critical_radius_rs': r_critical / self.solar_radius
        }
    
    def fast_slow_wind_model(self, latitude_deg: float = 0, 
                           solar_activity: str = 'moderate') -> Dict:
        """
        Model for fast and slow solar wind streams
        
        Args:
            latitude_deg: Heliographic latitude in degrees
            solar_activity: 'minimum', 'moderate', or 'maximum'
            
        Returns:
            Solar wind parameters including stream structure
        """
        # Solar wind stream structure depends on solar cycle and latitude
        activity_factors = {
            'minimum': {'fast_fraction': 0.7, 'speed_enhancement': 1.0},
            'moderate': {'fast_fraction': 0.4, 'speed_enhancement': 1.2},
            'maximum': {'fast_fraction': 0.2, 'speed_enhancement': 1.5}
        }
        
        factor = activity_factors.get(solar_activity, activity_factors['moderate'])
        
        # Latitude dependence
        lat_rad = math.radians(abs(latitude_deg))
        
        # During solar minimum, fast wind from polar regions
        if solar_activity == 'minimum':
            if abs(latitude_deg) > 30:  # Polar regions
                wind_type = 'fast'
                base_speed = 700  # km/s
                base_density = 3  # cm⁻³
            else:  # Equatorial regions
                wind_type = 'slow'
                base_speed = 350  # km/s
                base_density = 8  # cm⁻³
        else:
            # During solar maximum, more complex structure
            # Simplified model: mix of fast and slow
            fast_probability = factor['fast_fraction'] * (1 - math.cos(2 * lat_rad))
            
            if np.random.random() < fast_probability:
                wind_type = 'fast'
                base_speed = 600 + 100 * np.random.random()  # 600-700 km/s
                base_density = 2 + 2 * np.random.random()    # 2-4 cm⁻³
            else:
                wind_type = 'slow'
                base_speed = 300 + 100 * np.random.random()  # 300-400 km/s
                base_density = 6 + 4 * np.random.random()    # 6-10 cm⁻³
        
        # Apply activity enhancement
        final_speed = base_speed * factor['speed_enhancement']
        final_density = base_density / math.sqrt(factor['speed_enhancement'])
        
        return {
            'model_type': 'fast_slow_wind',
            'wind_type': wind_type,
            'latitude_deg': latitude_deg,
            'solar_activity': solar_activity,
            'wind_speed_km_s': final_speed,
            'density_cm3': final_density,
            'temperature_k': 1e5 if wind_type == 'fast' else 5e4,
            'magnetic_field_nt': 5 if wind_type == 'fast' else 8
        }
    
    def corotating_interaction_region(self, time_hours: float = 0) -> Dict:
        """
        Model Corotating Interaction Regions (CIRs)
        
        Args:
            time_hours: Time offset in hours
            
        Returns:
            CIR parameters
        """
        # CIR period approximately 27 days (solar rotation)
        rotation_period_hours = 27 * 24
        phase = (time_hours % rotation_period_hours) / rotation_period_hours * 2 * math.pi
        
        # CIR structure: compression region between fast and slow wind
        # Simplified sinusoidal model
        
        # Base solar wind (slow wind)
        base_speed = 350  # km/s
        base_density = 8  # cm⁻³
        base_b_field = 5  # nT
        
        # Fast wind following slow wind
        fast_speed = 650  # km/s
        fast_density = 3  # cm⁻³
        fast_b_field = 4  # nT
        
        # CIR enhancement factors
        cir_phase = math.sin(phase)
        
        if cir_phase > 0.5:  # In compression region
            # Enhanced density and magnetic field
            speed = base_speed + (fast_speed - base_speed) * cir_phase
            density = base_density * (1 + 2 * cir_phase)
            b_field = base_b_field * (1 + 3 * cir_phase)
            temperature = 2e5  # Enhanced temperature in CIR
            region = 'compression'
        elif cir_phase < -0.5:  # Fast wind region
            speed = fast_speed
            density = fast_density
            b_field = fast_b_field
            temperature = 1e5
            region = 'fast_wind'
        else:  # Slow wind region
            speed = base_speed
            density = base_density
            b_field = base_b_field
            temperature = 5e4
            region = 'slow_wind'
        
        return {
            'model_type': 'corotating_interaction_region',
            'time_hours': time_hours,
            'rotation_phase': phase / (2 * math.pi),
            'region_type': region,
            'wind_speed_km_s': speed,
            'density_cm3': density,
            'magnetic_field_nt': b_field,
            'temperature_k': temperature,
            'cir_enhancement': max(0, cir_phase)
        }
    
    def predict_solar_wind_at_earth(self, forecast_hours: int = 48) -> List[Dict]:
        """
        Predict solar wind conditions at Earth for next N hours
        
        Args:
            forecast_hours: Number of hours to forecast
            
        Returns:
            List of hourly solar wind predictions
        """
        predictions = []
        
        for hour in range(forecast_hours):
            # Get CIR structure
            cir_result = self.corotating_interaction_region(hour)
            
            # Get Parker wind baseline
            parker_result = self.parker_solar_wind_model(1.0)
            
            # Combine models (CIR modulates Parker wind)
            prediction = {
                'forecast_hour': hour,
                'timestamp': (datetime.utcnow() + timedelta(hours=hour)).isoformat() + 'Z',
                'wind_speed_km_s': cir_result['wind_speed_km_s'],
                'density_cm3': cir_result['density_cm3'],
                'magnetic_field_nt': cir_result['magnetic_field_nt'],
                'temperature_k': cir_result['temperature_k'],
                'region_type': cir_result['region_type'],
                'parker_baseline_speed': parker_result['wind_speed_km_s'],
                'model_confidence': 0.7 if cir_result['region_type'] == 'compression' else 0.8
            }
            
            predictions.append(prediction)
        
        return predictions

def test_solar_wind_model():
    """Test the solar wind models"""
    print("Testing Solar Wind Models...")
    
    model = SolarWindModel()
    
    # Test Parker model at different distances
    print("\nParker Solar Wind Model:")
    for distance in [0.3, 1.0, 5.0]:
        result = model.parker_solar_wind_model(distance)
        print(f"  {distance} AU: {result['wind_speed_km_s']:.0f} km/s, {result['density_cm3']:.1f} cm⁻³")
    
    # Test fast/slow wind model
    print("\nFast/Slow Wind Model:")
    for activity in ['minimum', 'moderate', 'maximum']:
        result = model.fast_slow_wind_model(0, activity)
        print(f"  Solar {activity}: {result['wind_type']} wind, {result['wind_speed_km_s']:.0f} km/s")
    
    # Test CIR model
    print("\nCorotating Interaction Region:")
    for phase in [0, 0.25, 0.5, 0.75]:
        time_h = phase * 27 * 24  # Phase of solar rotation
        result = model.corotating_interaction_region(time_h)
        print(f"  Phase {phase:.2f}: {result['region_type']}, {result['wind_speed_km_s']:.0f} km/s")

if __name__ == "__main__":
    test_solar_wind_model()
