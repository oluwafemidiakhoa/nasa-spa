#!/usr/bin/env python3
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
        print(f"\nTesting {cme['description']} ({cme['speed']} km/s):")
        
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
