#!/usr/bin/env python3
"""
Implement physics-based space weather models for NASA Space Weather Dashboard
Includes CME propagation, solar wind modeling, and geomagnetic predictions
"""

import os
import sys
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

def create_cme_propagation_model():
    """Create CME propagation physics model"""
    print("=" * 60)
    print("CREATING CME PROPAGATION PHYSICS MODEL")
    print("=" * 60)
    
    physics_model_content = '''#!/usr/bin/env python3
"""
CME Propagation Physics Model
Implements drag-based and kinematic models for CME Earth arrival prediction
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Physical constants
AU = 1.496e11  # Astronomical Unit in meters
SOLAR_RADIUS = 6.96e8  # Solar radius in meters
EARTH_ORBIT_RADIUS = 1 * AU  # Earth's orbital distance

class CMEPropagationModel:
    """Physics-based CME propagation model"""
    
    def __init__(self):
        # Solar wind parameters (typical values)
        self.solar_wind_speed = 400  # km/s (typical)
        self.solar_wind_density = 5  # particles/cm³
        self.drag_coefficient = 1.0  # Dimensionless drag coefficient
        
        # Model parameters
        self.acceleration_distance = 30 * SOLAR_RADIUS  # Distance where acceleration ends
        
    def drag_based_model(self, initial_speed: float, cme_mass: float = 1e15) -> Dict:
        """
        Drag-based CME propagation model
        
        Args:
            initial_speed: CME initial speed in km/s
            cme_mass: CME mass in kg (estimated)
            
        Returns:
            Dictionary with propagation results
        """
        # Convert units
        v0 = initial_speed * 1000  # m/s
        vsw = self.solar_wind_speed * 1000  # m/s
        
        # Calculate drag parameters
        # Drag force: F = 0.5 * ρ * A * Cd * (v - vsw)²
        # Assuming spherical CME with radius ~0.1 AU
        cme_radius = 0.1 * AU
        cross_section = math.pi * cme_radius**2
        
        # Solar wind mass density (approximate)
        proton_mass = 1.67e-27  # kg
        sw_density = self.solar_wind_density * 1e6 * proton_mass  # kg/m³
        
        # Calculate characteristic time and distance
        drag_param = 0.5 * sw_density * cross_section * self.drag_coefficient / cme_mass
        
        # Numerical integration for CME trajectory
        dt = 3600  # 1 hour time step
        distance = 0
        velocity = v0
        time_elapsed = 0
        
        trajectory = []
        
        while distance < EARTH_ORBIT_RADIUS:
            # Drag acceleration
            if velocity > vsw:
                drag_accel = -drag_param * (velocity - vsw)**2
            else:
                drag_accel = 0
            
            # Update velocity and position
            velocity += drag_accel * dt
            distance += velocity * dt
            time_elapsed += dt
            
            # Store trajectory point
            if len(trajectory) % 6 == 0:  # Store every 6 hours
                trajectory.append({
                    'time_hours': time_elapsed / 3600,
                    'distance_au': distance / AU,
                    'velocity_km_s': velocity / 1000
                })
        
        arrival_time = time_elapsed / 3600  # hours
        final_velocity = velocity / 1000  # km/s
        
        return {
            'model_type': 'drag_based',
            'initial_speed_km_s': initial_speed,
            'arrival_time_hours': arrival_time,
            'final_velocity_km_s': final_velocity,
            'trajectory': trajectory,
            'solar_wind_speed': self.solar_wind_speed,
            'model_confidence': self._calculate_confidence(initial_speed, arrival_time)
        }
    
    def kinematic_model(self, initial_speed: float, acceleration: float = 0) -> Dict:
        """
        Simple kinematic CME propagation model
        
        Args:
            initial_speed: CME initial speed in km/s
            acceleration: CME acceleration in m/s² (usually negative due to drag)
            
        Returns:
            Dictionary with propagation results
        """
        # Convert units
        v0 = initial_speed * 1000  # m/s
        distance = EARTH_ORBIT_RADIUS  # m
        
        if acceleration == 0:
            # Constant velocity
            arrival_time = distance / v0
            final_velocity = v0
        else:
            # Uniformly accelerated motion
            # s = v0*t + 0.5*a*t²
            # Solve quadratic equation: 0.5*a*t² + v0*t - s = 0
            discriminant = v0**2 + 2 * acceleration * distance
            
            if discriminant < 0:
                # CME stops before reaching Earth
                return {
                    'model_type': 'kinematic',
                    'error': 'CME stops before reaching Earth',
                    'initial_speed_km_s': initial_speed,
                    'model_confidence': 0.0
                }
            
            arrival_time = (-v0 + math.sqrt(discriminant)) / acceleration
            final_velocity = v0 + acceleration * arrival_time
        
        arrival_time_hours = arrival_time / 3600
        final_velocity_km_s = final_velocity / 1000
        
        # Generate trajectory
        trajectory = []
        num_points = 20
        for i in range(num_points + 1):
            t = arrival_time * i / num_points
            if acceleration == 0:
                d = v0 * t
                v = v0
            else:
                d = v0 * t + 0.5 * acceleration * t**2
                v = v0 + acceleration * t
            
            trajectory.append({
                'time_hours': t / 3600,
                'distance_au': d / AU,
                'velocity_km_s': v / 1000
            })
        
        return {
            'model_type': 'kinematic',
            'initial_speed_km_s': initial_speed,
            'arrival_time_hours': arrival_time_hours,
            'final_velocity_km_s': final_velocity_km_s,
            'acceleration_m_s2': acceleration,
            'trajectory': trajectory,
            'model_confidence': self._calculate_confidence(initial_speed, arrival_time_hours)
        }
    
    def enlil_approximate_model(self, initial_speed: float, solar_wind_speed: float = None) -> Dict:
        """
        Approximate ENLIL-like model for CME propagation
        Simplified version of the WSA-ENLIL model used by NOAA
        
        Args:
            initial_speed: CME initial speed in km/s
            solar_wind_speed: Background solar wind speed in km/s
            
        Returns:
            Dictionary with propagation results
        """
        if solar_wind_speed is None:
            solar_wind_speed = self.solar_wind_speed
        
        # ENLIL-like empirical relationships
        # Based on statistical analysis of CME observations
        
        # Calculate effective speed considering solar wind interaction
        speed_ratio = initial_speed / solar_wind_speed
        
        if speed_ratio > 2.0:
            # Fast CME - significant deceleration
            effective_speed = initial_speed * 0.7 + solar_wind_speed * 0.3
        elif speed_ratio > 1.5:
            # Moderate CME
            effective_speed = initial_speed * 0.8 + solar_wind_speed * 0.2
        else:
            # Slow CME - minimal deceleration
            effective_speed = initial_speed * 0.9 + solar_wind_speed * 0.1
        
        # Calculate arrival time
        distance_km = EARTH_ORBIT_RADIUS / 1000  # Convert to km
        arrival_time_hours = distance_km / effective_speed / 3600
        
        # Generate trajectory with speed evolution
        trajectory = []
        num_points = 24  # Hourly points
        
        for i in range(num_points + 1):
            t_hours = arrival_time_hours * i / num_points
            
            # Speed evolution (exponential decay toward solar wind speed)
            decay_rate = 1.0 / (arrival_time_hours * 0.3)  # Time constant
            speed_t = solar_wind_speed + (initial_speed - solar_wind_speed) * math.exp(-decay_rate * t_hours)
            
            # Distance (integrate speed over time)
            if i == 0:
                distance_t = 0
            else:
                # Approximate integration
                prev_t = arrival_time_hours * (i-1) / num_points
                avg_speed = (speed_prev + speed_t) / 2
                distance_t = distance_prev + avg_speed * (t_hours - prev_t) * 3600
            
            trajectory.append({
                'time_hours': t_hours,
                'distance_au': distance_t / (distance_km * 1000) if distance_t > 0 else 0,
                'velocity_km_s': speed_t
            })
            
            speed_prev = speed_t
            distance_prev = distance_t if i > 0 else 0
        
        return {
            'model_type': 'enlil_approximate',
            'initial_speed_km_s': initial_speed,
            'effective_speed_km_s': effective_speed,
            'arrival_time_hours': arrival_time_hours,
            'final_velocity_km_s': effective_speed,
            'solar_wind_speed': solar_wind_speed,
            'trajectory': trajectory,
            'model_confidence': self._calculate_confidence(initial_speed, arrival_time_hours)
        }
    
    def _calculate_confidence(self, initial_speed: float, arrival_time_hours: float) -> float:
        """Calculate model confidence based on CME characteristics"""
        confidence = 0.8  # Base confidence
        
        # Adjust based on speed (faster CMEs are easier to track)
        if initial_speed > 1000:
            confidence += 0.1
        elif initial_speed < 300:
            confidence -= 0.2
        
        # Adjust based on arrival time (shorter times have higher uncertainty)
        if arrival_time_hours < 24:
            confidence -= 0.1
        elif arrival_time_hours > 72:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def ensemble_prediction(self, cme_data: Dict) -> Dict:
        """
        Create ensemble prediction using multiple models
        
        Args:
            cme_data: Dictionary with CME parameters
            
        Returns:
            Ensemble prediction results
        """
        initial_speed = cme_data.get('speed', 400)  # km/s
        
        # Run different models
        models = []
        
        # Drag-based model
        try:
            drag_result = self.drag_based_model(initial_speed)
            models.append(drag_result)
        except Exception as e:
            logging.warning(f"Drag model failed: {e}")
        
        # Kinematic model (constant velocity)
        try:
            kinematic_result = self.kinematic_model(initial_speed)
            models.append(kinematic_result)
        except Exception as e:
            logging.warning(f"Kinematic model failed: {e}")
        
        # ENLIL-like model
        try:
            enlil_result = self.enlil_approximate_model(initial_speed)
            models.append(enlil_result)
        except Exception as e:
            logging.warning(f"ENLIL model failed: {e}")
        
        if not models:
            return {
                'error': 'All models failed',
                'initial_speed_km_s': initial_speed
            }
        
        # Calculate ensemble statistics
        arrival_times = [m['arrival_time_hours'] for m in models if 'arrival_time_hours' in m]
        confidences = [m['model_confidence'] for m in models if 'model_confidence' in m]
        
        if not arrival_times:
            return {
                'error': 'No valid arrival time predictions',
                'initial_speed_km_s': initial_speed
            }
        
        # Weighted average based on confidence
        if confidences:
            weights = np.array(confidences)
            weights = weights / np.sum(weights)
            ensemble_arrival = np.average(arrival_times, weights=weights)
            ensemble_confidence = np.mean(confidences)
        else:
            ensemble_arrival = np.mean(arrival_times)
            ensemble_confidence = 0.5
        
        # Calculate uncertainty (standard deviation)
        uncertainty_hours = np.std(arrival_times)
        
        # Create arrival window
        arrival_window_start = ensemble_arrival - uncertainty_hours
        arrival_window_end = ensemble_arrival + uncertainty_hours
        
        return {
            'ensemble_prediction': True,
            'initial_speed_km_s': initial_speed,
            'arrival_time_hours': ensemble_arrival,
            'arrival_window_start_hours': max(0, arrival_window_start),
            'arrival_window_end_hours': arrival_window_end,
            'uncertainty_hours': uncertainty_hours,
            'confidence': ensemble_confidence,
            'models_used': [m['model_type'] for m in models],
            'individual_predictions': models,
            'num_models': len(models)
        }

def test_cme_model():
    """Test the CME propagation models"""
    print("Testing CME Propagation Models...")
    
    model = CMEPropagationModel()
    
    # Test with typical CME parameters
    test_cmes = [
        {'speed': 400, 'description': 'Slow CME'},
        {'speed': 800, 'description': 'Fast CME'},
        {'speed': 1200, 'description': 'Very fast CME'}
    ]
    
    for cme in test_cmes:
        print(f"\\nTesting {cme['description']} ({cme['speed']} km/s):")
        
        result = model.ensemble_prediction(cme)
        
        if 'error' not in result:
            print(f"  Ensemble arrival: {result['arrival_time_hours']:.1f} hours")
            print(f"  Arrival window: {result['arrival_window_start_hours']:.1f} - {result['arrival_window_end_hours']:.1f} hours")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Models used: {', '.join(result['models_used'])}")
        else:
            print(f"  Error: {result['error']}")

if __name__ == "__main__":
    test_cme_model()
'''
    
    try:
        with open('cme_physics_model.py', 'w', encoding='utf-8') as f:
            f.write(physics_model_content)
        
        print("SUCCESS: CME propagation model created as cme_physics_model.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create CME model: {e}")
        return False

def create_solar_wind_model():
    """Create solar wind physics model"""
    print("\n" + "=" * 60)
    print("CREATING SOLAR WIND PHYSICS MODEL")
    print("=" * 60)
    
    solar_wind_content = '''#!/usr/bin/env python3
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
    print("\\nParker Solar Wind Model:")
    for distance in [0.3, 1.0, 5.0]:
        result = model.parker_solar_wind_model(distance)
        print(f"  {distance} AU: {result['wind_speed_km_s']:.0f} km/s, {result['density_cm3']:.1f} cm⁻³")
    
    # Test fast/slow wind model
    print("\\nFast/Slow Wind Model:")
    for activity in ['minimum', 'moderate', 'maximum']:
        result = model.fast_slow_wind_model(0, activity)
        print(f"  Solar {activity}: {result['wind_type']} wind, {result['wind_speed_km_s']:.0f} km/s")
    
    # Test CIR model
    print("\\nCorotating Interaction Region:")
    for phase in [0, 0.25, 0.5, 0.75]:
        time_h = phase * 27 * 24  # Phase of solar rotation
        result = model.corotating_interaction_region(time_h)
        print(f"  Phase {phase:.2f}: {result['region_type']}, {result['wind_speed_km_s']:.0f} km/s")

if __name__ == "__main__":
    test_solar_wind_model()
'''
    
    try:
        with open('solar_wind_model.py', 'w', encoding='utf-8') as f:
            f.write(solar_wind_content)
        
        print("SUCCESS: Solar wind model created as solar_wind_model.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create solar wind model: {e}")
        return False

def create_geomagnetic_model():
    """Create geomagnetic field physics model"""
    print("\n" + "=" * 60)
    print("CREATING GEOMAGNETIC FIELD PHYSICS MODEL")
    print("=" * 60)
    
    geomagnetic_content = '''#!/usr/bin/env python3
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
        print(f"\\n{condition['name']} conditions:")
        
        dst_result = model.dst_index_model(condition)
        print(f"  Dst: {dst_result['dst_predicted_nt']:.0f} nT ({dst_result['activity_level']})")
        
        kp_result = model.kp_index_model(condition)
        print(f"  Kp: {kp_result['kp_predicted']:.1f} ({kp_result['activity_level']})")
        
        aurora_result = model.aurora_model(kp_result['kp_predicted'], 65)
        print(f"  Aurora at 65°N: {aurora_result['visibility']} ({aurora_result['intensity']})")

if __name__ == "__main__":
    test_geomagnetic_model()
'''
    
    try:
        with open('geomagnetic_model.py', 'w', encoding='utf-8') as f:
            f.write(geomagnetic_content)
        
        print("SUCCESS: Geomagnetic model created as geomagnetic_model.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create geomagnetic model: {e}")
        return False

def create_physics_integration_service():
    """Create integrated physics service that combines all models"""
    print("\n" + "=" * 60)
    print("CREATING PHYSICS INTEGRATION SERVICE")
    print("=" * 60)
    
    integration_content = '''#!/usr/bin/env python3
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
    
    print("\\nTesting CME analysis:")
    cme_result = forecaster.analyze_cme_event(test_cme)
    if 'error' not in cme_result:
        print(f"  CME {cme_result['cme_id']}: {cme_result['initial_speed_km_s']} km/s")
        print(f"  Arrival: {cme_result['arrival_prediction']['arrival_time']}")
        print(f"  Confidence: {cme_result['physics_models']['confidence']:.2f}")
    
    # Test comprehensive forecast
    print("\\nTesting comprehensive forecast:")
    comprehensive = forecaster.comprehensive_space_weather_forecast([test_cme], 48)
    print(f"  Overall risk: {comprehensive['overall_assessment']['risk_level']}")
    print(f"  Max Kp: {comprehensive['summary_statistics']['max_kp_predicted']:.1f}")
    print(f"  Models used: {', '.join(comprehensive['forecast_metadata']['models_used'])}")

if __name__ == "__main__":
    import math  # Add this for fallback methods
    test_physics_integration()
'''
    
    try:
        with open('physics_integration.py', 'w', encoding='utf-8') as f:
            f.write(integration_content)
        
        print("SUCCESS: Physics integration service created as physics_integration.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create physics integration: {e}")
        return False

def main():
    """Main physics models implementation function"""
    print("NASA Space Weather Dashboard - Physics Models Implementation")
    print(f"Starting physics implementation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Create CME propagation model
    cme_ok = create_cme_propagation_model()
    
    # Step 2: Create solar wind model
    solar_wind_ok = create_solar_wind_model()
    
    # Step 3: Create geomagnetic model
    geomagnetic_ok = create_geomagnetic_model()
    
    # Step 4: Create physics integration service
    integration_ok = create_physics_integration_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("PHYSICS MODELS IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    successful_components = sum([cme_ok, solar_wind_ok, geomagnetic_ok, integration_ok])
    total_components = 4
    
    if successful_components == total_components:
        print("STATUS: PHYSICS MODELS COMPLETE")
        print()
        print("Successfully implemented:")
        print("   • CME Propagation Model (cme_physics_model.py)")
        print("   • Solar Wind Model (solar_wind_model.py)")
        print("   • Geomagnetic Field Model (geomagnetic_model.py)")
        print("   • Physics Integration Service (physics_integration.py)")
        print()
        print("Physics capabilities:")
        print("   • Drag-based CME propagation calculations")
        print("   • Parker solar wind model")
        print("   • Corotating Interaction Regions (CIRs)")
        print("   • Dst and Kp index predictions")
        print("   • Aurora visibility modeling")
        print("   • Ensemble physics forecasting")
        print()
        print("Models available:")
        print("   • CME arrival time prediction (3 models)")
        print("   • Solar wind speed/density forecasts")
        print("   • Geomagnetic storm intensity")
        print("   • Aurora boundary calculations")
        print("   • Magnetosphere-ionosphere coupling")
        print()
        print("Testing:")
        print("   1. Run: python cme_physics_model.py")
        print("   2. Run: python solar_wind_model.py")
        print("   3. Run: python geomagnetic_model.py")
        print("   4. Run: python physics_integration.py")
        print()
        print("Task 7 (Physics Models) COMPLETE")
        print("Ready to proceed to Task 8 (Docker containerization)")
        
    else:
        print("STATUS: PARTIAL IMPLEMENTATION")
        print(f"Successfully implemented: {successful_components}/{total_components} components")
        print("Some physics models may need manual adjustment")
    
    print()

if __name__ == "__main__":
    main()