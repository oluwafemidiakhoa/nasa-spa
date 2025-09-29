"""
3D Visualization Engine for Space Weather Data
Advanced visualization system for CME propagation and space weather events
"""

import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CMEVisualizationData:
    """Data structure for CME 3D visualization"""
    
    def __init__(self, cme_id: str, launch_time: datetime, velocity: float, 
                 angular_width: float, direction: float, source_location: Dict):
        self.id = cme_id
        self.launch_time = launch_time
        self.velocity = velocity  # km/s
        self.angular_width = angular_width  # degrees
        self.direction = direction  # degrees from Earth direction
        self.source_location = source_location
        
        # Calculated properties
        self.positions = []  # Time series of positions
        self.arrival_time = None
        self.earth_impact_probability = 0.0
        self.visualization_params = {}
        
        self.calculate_trajectory()
    
    def calculate_trajectory(self):
        """Calculate CME trajectory for visualization"""
        # Constants
        AU_KM = 149597870.7
        EARTH_DISTANCE_AU = 1.0
        
        # Calculate arrival time
        distance_km = EARTH_DISTANCE_AU * AU_KM
        arrival_hours = distance_km / (self.velocity * 3600)  # Convert to hours
        self.arrival_time = self.launch_time + timedelta(hours=arrival_hours)
        
        # Generate trajectory points
        time_steps = np.linspace(0, arrival_hours * 1.2, 100)  # 20% beyond arrival
        
        for t in time_steps:
            # Simple propagation model
            distance_au = (self.velocity * t * 3600) / AU_KM
            
            # Position in 3D space (simplified)
            angle_rad = np.radians(self.direction)
            x = distance_au * np.cos(angle_rad)
            y = 0  # Assume ecliptic plane
            z = distance_au * np.sin(angle_rad)
            
            position = {
                'time': self.launch_time + timedelta(hours=t),
                'position': [x, y, z],
                'distance_au': distance_au,
                'velocity': self.velocity
            }
            self.positions.append(position)
        
        # Calculate Earth impact probability
        self.earth_impact_probability = self.calculate_earth_impact_probability()
    
    def calculate_earth_impact_probability(self) -> float:
        """Calculate probability of Earth impact based on trajectory"""
        # Simplified calculation based on angular width and direction
        earth_angular_size = 0.5  # degrees as seen from Sun
        
        if abs(self.direction) <= self.angular_width / 2:
            # CME angular width covers Earth direction
            base_probability = min(1.0, (self.angular_width / 2) / earth_angular_size)
            
            # Adjust for velocity (faster CMEs have higher impact probability)
            velocity_factor = min(1.0, self.velocity / 1000)  # Normalize to 1000 km/s
            
            return base_probability * velocity_factor
        else:
            return 0.0
    
    def get_position_at_time(self, target_time: datetime) -> Optional[Dict]:
        """Get CME position at specific time"""
        if target_time < self.launch_time:
            return None
        
        # Find closest time point
        time_diffs = [abs((pos['time'] - target_time).total_seconds()) for pos in self.positions]
        closest_idx = np.argmin(time_diffs)
        
        return self.positions[closest_idx] if closest_idx < len(self.positions) else None

class SolarSystemModel:
    """3D Solar System model for space weather visualization"""
    
    def __init__(self):
        self.celestial_bodies = {}
        self.satellites = {}
        self.current_time = datetime.utcnow()
        self.initialize_solar_system()
    
    def initialize_solar_system(self):
        """Initialize celestial bodies and satellites"""
        
        # Sun
        self.celestial_bodies['sun'] = {
            'position': [0, 0, 0],
            'radius': 0.00465,  # AU (actual ratio scaled)
            'color': '#ffff00',
            'type': 'star'
        }
        
        # Earth
        self.celestial_bodies['earth'] = {
            'position': [1.0, 0, 0],  # 1 AU
            'radius': 4.26e-5,  # AU (actual ratio scaled)
            'color': '#0080ff',
            'type': 'planet',
            'magnetosphere_radius': 0.01  # Simplified magnetosphere
        }
        
        # Moon
        self.celestial_bodies['moon'] = {
            'position': [1.00257, 0, 0],  # 1 AU + lunar distance
            'radius': 1.16e-5,  # AU
            'color': '#cccccc',
            'type': 'moon',
            'orbital_period': 27.3  # days
        }
        
        # Key satellites
        self.satellites = {
            'DSCOVR': {
                'position': [0.99, 0, 0],  # L1 point (approximate)
                'color': '#00ffff',
                'mission': 'Solar wind monitoring',
                'status': 'operational'
            },
            'ACE': {
                'position': [0.985, 0.01, 0.01],  # Near L1
                'color': '#ff8000',
                'mission': 'Space weather',
                'status': 'operational'
            },
            'STEREO-A': {
                'position': [0.95, 0, 0.1],  # Ahead of Earth
                'color': '#ff0080',
                'mission': '3D solar observation',
                'status': 'operational'
            }
        }
    
    def update_positions(self, time: datetime):
        """Update positions of celestial bodies at given time"""
        self.current_time = time
        
        # Update Moon position (simple circular orbit)
        days_since_epoch = (time - datetime(2024, 1, 1)).days
        moon_angle = (days_since_epoch / 27.3) * 2 * np.pi
        moon_distance = 0.00257  # AU
        
        self.celestial_bodies['moon']['position'] = [
            1.0 + moon_distance * np.cos(moon_angle),
            0,
            moon_distance * np.sin(moon_angle)
        ]
        
        # Satellites maintain relatively fixed positions for this simplified model
        # In reality, they have complex orbital mechanics
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current state of solar system for visualization"""
        return {
            'timestamp': self.current_time.isoformat(),
            'celestial_bodies': self.celestial_bodies,
            'satellites': self.satellites,
            'scale_factor': 1.0,  # AU units
            'reference_frame': 'heliocentric'
        }

class SpaceWeatherVisualizationEngine:
    """Main visualization engine for space weather events"""
    
    def __init__(self):
        self.solar_system = SolarSystemModel()
        self.active_cmes = []
        self.visualization_config = {
            'time_acceleration': 1.0,
            'quality_level': 'high',
            'show_magnetic_field': True,
            'show_solar_wind': True,
            'show_particle_radiation': True
        }
        self.current_simulation_time = datetime.utcnow()
    
    def add_cme_from_donki(self, donki_data: Dict[str, Any]) -> CMEVisualizationData:
        """Create CME visualization from DONKI data"""
        try:
            # Extract CME parameters
            cme_id = donki_data.get('activityID', f"CME_{len(self.active_cmes)}")
            
            # Parse launch time
            launch_time_str = donki_data.get('startTime', '')
            if launch_time_str:
                launch_time = datetime.fromisoformat(launch_time_str.replace('Z', '+00:00'))
            else:
                launch_time = datetime.utcnow()
            
            # Get CME analysis data
            analyses = donki_data.get('cmeAnalyses', [])
            if analyses:
                analysis = analyses[0]
                velocity = float(analysis.get('speed', 500))
                angular_width = float(analysis.get('halfAngle', 15)) * 2
                direction = float(analysis.get('longitude', 0))
            else:
                velocity = 500
                angular_width = 30
                direction = 0
            
            # Parse source location
            source_location = {
                'latitude': 0,
                'longitude': 0,
                'description': donki_data.get('sourceLocation', 'Unknown')
            }
            
            # Create visualization data
            cme_viz = CMEVisualizationData(
                cme_id=cme_id,
                launch_time=launch_time,
                velocity=velocity,
                angular_width=angular_width,
                direction=direction,
                source_location=source_location
            )
            
            self.active_cmes.append(cme_viz)
            logger.info(f"Added CME {cme_id} for visualization")
            
            return cme_viz
            
        except Exception as e:
            logger.error(f"Failed to create CME visualization: {e}")
            return None
    
    def create_synthetic_storm(self, intensity: str = 'moderate') -> CMEVisualizationData:
        """Create synthetic CME for demonstration"""
        
        storm_params = {
            'weak': {'velocity': 450, 'width': 25, 'direction': 15},
            'moderate': {'velocity': 650, 'width': 40, 'direction': 5},
            'strong': {'velocity': 900, 'width': 60, 'direction': 0},
            'extreme': {'velocity': 1200, 'width': 80, 'direction': 0}
        }
        
        params = storm_params.get(intensity, storm_params['moderate'])
        
        cme_viz = CMEVisualizationData(
            cme_id=f"SYNTHETIC_{intensity.upper()}_{datetime.now().strftime('%Y%m%d_%H%M')}",
            launch_time=datetime.utcnow(),
            velocity=params['velocity'],
            angular_width=params['width'],
            direction=params['direction'],
            source_location={'latitude': 0, 'longitude': -45, 'description': f'Synthetic {intensity} event'}
        )
        
        self.active_cmes.append(cme_viz)
        logger.info(f"Created synthetic {intensity} storm visualization")
        
        return cme_viz
    
    def get_visualization_data(self, target_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get complete visualization data for 3D rendering"""
        
        if target_time is None:
            target_time = self.current_simulation_time
        
        # Update solar system positions
        self.solar_system.update_positions(target_time)
        
        # Get CME positions at target time
        cme_data = []
        for cme in self.active_cmes:
            position_data = cme.get_position_at_time(target_time)
            if position_data:
                cme_info = {
                    'id': cme.id,
                    'position': position_data['position'],
                    'velocity': cme.velocity,
                    'angular_width': cme.angular_width,
                    'direction': cme.direction,
                    'earth_impact_probability': cme.earth_impact_probability,
                    'launch_time': cme.launch_time.isoformat(),
                    'arrival_time': cme.arrival_time.isoformat() if cme.arrival_time else None,
                    'visualization_params': {
                        'color': self._get_cme_color(cme.velocity),
                        'opacity': self._get_cme_opacity(cme, target_time),
                        'scale': self._get_cme_scale(cme.angular_width),
                        'trail_length': min(50, len(cme.positions))
                    }
                }
                cme_data.append(cme_info)
        
        # Get solar wind and magnetic field data
        solar_wind_data = self._generate_solar_wind_visualization(target_time)
        magnetic_field_data = self._generate_magnetic_field_visualization(target_time)
        
        return {
            'timestamp': target_time.isoformat(),
            'solar_system': self.solar_system.get_system_state(),
            'cmes': cme_data,
            'solar_wind': solar_wind_data,
            'magnetic_field': magnetic_field_data,
            'configuration': self.visualization_config,
            'simulation_stats': {
                'active_cmes': len(self.active_cmes),
                'time_acceleration': self.visualization_config['time_acceleration'],
                'total_simulation_time': (target_time - datetime.utcnow()).total_seconds() / 3600
            }
        }
    
    def _get_cme_color(self, velocity: float) -> str:
        """Get CME color based on velocity"""
        if velocity > 1000:
            return '#ff0040'  # Red for fast CMEs
        elif velocity > 700:
            return '#ff8000'  # Orange for moderate CMEs
        elif velocity > 400:
            return '#ffff00'  # Yellow for slow CMEs
        else:
            return '#80ff00'  # Green for very slow CMEs
    
    def _get_cme_opacity(self, cme: CMEVisualizationData, current_time: datetime) -> float:
        """Get CME opacity based on age and distance"""
        age_hours = (current_time - cme.launch_time).total_seconds() / 3600
        
        # Fade CMEs over time
        base_opacity = max(0.3, 1.0 - (age_hours / 100))  # Fade over 100 hours
        
        # Increase opacity near Earth
        position = cme.get_position_at_time(current_time)
        if position:
            distance = np.sqrt(sum(x**2 for x in position['position']))
            distance_factor = max(0.5, 1.0 - distance / 2)  # Brighter near Sun/Earth
            return min(1.0, base_opacity * distance_factor)
        
        return base_opacity
    
    def _get_cme_scale(self, angular_width: float) -> float:
        """Get CME scale factor based on angular width"""
        return max(0.5, min(2.0, angular_width / 30))  # Scale relative to 30° baseline
    
    def _generate_solar_wind_visualization(self, target_time: datetime) -> Dict[str, Any]:
        """Generate solar wind particle visualization data"""
        # Simplified solar wind model
        base_velocity = 400  # km/s
        base_density = 5     # particles/cm³
        
        # Add some variation
        time_factor = (target_time.timestamp() % 86400) / 86400  # Daily variation
        velocity_variation = 50 * np.sin(time_factor * 2 * np.pi)
        density_variation = 2 * np.sin(time_factor * 4 * np.pi)
        
        return {
            'velocity': base_velocity + velocity_variation,
            'density': base_density + density_variation,
            'temperature': 100000,  # K
            'magnetic_field': {
                'bx': np.random.normal(0, 3),
                'by': np.random.normal(0, 3),
                'bz': np.random.normal(-2, 4)
            },
            'particle_count': 1000,
            'visualization_params': {
                'color': '#00ffff',
                'opacity': 0.6,
                'speed_factor': 1.0
            }
        }
    
    def _generate_magnetic_field_visualization(self, target_time: datetime) -> Dict[str, Any]:
        """Generate magnetic field line visualization data"""
        
        # Earth's dipole field lines
        field_lines = []
        for i in range(20):
            angle = (i / 20) * 2 * np.pi
            
            # Generate dipole field line points
            points = []
            for t in np.linspace(-np.pi/2, np.pi/2, 50):
                r = 0.1 * (1 + 0.5 * np.cos(t)**2)  # Simplified dipole
                x = 1.0 + r * np.cos(angle) * np.cos(t)
                y = r * np.sin(t)
                z = r * np.sin(angle) * np.cos(t)
                points.append([x, y, z])
            
            field_lines.append({
                'points': points,
                'strength': 1.0,
                'color': '#00ff80',
                'opacity': 0.4
            })
        
        return {
            'field_lines': field_lines,
            'dipole_strength': 1.0,
            'tilt_angle': 11.5,  # degrees
            'visualization_params': {
                'show_field_lines': True,
                'line_density': 'medium',
                'animation_speed': 1.0
            }
        }
    
    def advance_simulation(self, time_step_hours: float):
        """Advance simulation time"""
        self.current_simulation_time += timedelta(hours=time_step_hours)
        
        # Remove old CMEs (older than 7 days)
        cutoff_time = self.current_simulation_time - timedelta(days=7)
        self.active_cmes = [cme for cme in self.active_cmes if cme.launch_time > cutoff_time]
    
    def get_cme_timeline(self, hours_back: int = 168, hours_forward: int = 168) -> List[Dict]:
        """Get timeline of CME events for visualization controls"""
        timeline = []
        
        start_time = self.current_simulation_time - timedelta(hours=hours_back)
        end_time = self.current_simulation_time + timedelta(hours=hours_forward)
        
        for cme in self.active_cmes:
            if start_time <= cme.launch_time <= end_time:
                timeline.append({
                    'id': cme.id,
                    'launch_time': cme.launch_time.isoformat(),
                    'arrival_time': cme.arrival_time.isoformat() if cme.arrival_time else None,
                    'velocity': cme.velocity,
                    'earth_impact_probability': cme.earth_impact_probability,
                    'severity': self._classify_cme_severity(cme)
                })
        
        return sorted(timeline, key=lambda x: x['launch_time'])
    
    def _classify_cme_severity(self, cme: CMEVisualizationData) -> str:
        """Classify CME severity for timeline display"""
        if cme.velocity > 1000 and cme.earth_impact_probability > 0.7:
            return 'extreme'
        elif cme.velocity > 700 and cme.earth_impact_probability > 0.5:
            return 'high'
        elif cme.velocity > 500 and cme.earth_impact_probability > 0.3:
            return 'moderate'
        else:
            return 'low'
    
    def export_animation_data(self, duration_hours: int = 72, time_step_hours: float = 1.0) -> List[Dict]:
        """Export time series data for animation"""
        animation_frames = []
        
        start_time = self.current_simulation_time
        num_frames = int(duration_hours / time_step_hours)
        
        for i in range(num_frames):
            frame_time = start_time + timedelta(hours=i * time_step_hours)
            frame_data = self.get_visualization_data(frame_time)
            frame_data['frame_number'] = i
            frame_data['frame_time_hours'] = i * time_step_hours
            animation_frames.append(frame_data)
        
        return animation_frames

# API functions for web interface
def get_visualization_data_api(cme_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """API function to get visualization data"""
    engine = SpaceWeatherVisualizationEngine()
    
    # Add sample CMEs if none specified
    if not cme_ids:
        engine.create_synthetic_storm('moderate')
    
    return engine.get_visualization_data()

def create_cme_animation_api(cme_data: Dict[str, Any], duration_hours: int = 72) -> List[Dict]:
    """API function to create CME animation data"""
    engine = SpaceWeatherVisualizationEngine()
    
    # Add CME from data
    if cme_data:
        engine.add_cme_from_donki(cme_data)
    else:
        engine.create_synthetic_storm('moderate')
    
    return engine.export_animation_data(duration_hours)

if __name__ == "__main__":
    # Test the visualization engine
    print("Testing 3D Space Weather Visualization Engine...")
    
    engine = SpaceWeatherVisualizationEngine()
    
    # Create test CME
    test_cme = engine.create_synthetic_storm('strong')
    print(f"Created test CME: {test_cme.id}")
    print(f"Velocity: {test_cme.velocity} km/s")
    print(f"Earth impact probability: {test_cme.earth_impact_probability:.1%}")
    
    # Get visualization data
    viz_data = engine.get_visualization_data()
    print(f"\nVisualization data generated:")
    print(f"Active CMEs: {len(viz_data['cmes'])}")
    print(f"Solar system objects: {len(viz_data['solar_system']['celestial_bodies'])}")
    print(f"Satellites: {len(viz_data['solar_system']['satellites'])}")
    
    # Get timeline
    timeline = engine.get_cme_timeline()
    print(f"\nCME Timeline: {len(timeline)} events")
    
    # Export animation (first 10 frames for test)
    animation_data = engine.export_animation_data(duration_hours=10, time_step_hours=1)
    print(f"Animation frames generated: {len(animation_data)}")
    
    print("\n3D Visualization Engine test completed successfully!")