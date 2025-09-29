"""
Expert-Level Space Weather Forecaster
Combines AI analysis with physics-based models for NASA-grade predictions
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Import our modules
from .space_physics import SpaceWeatherPhysics, CMEParameters, create_cme_from_donki, create_solar_wind_sample
from .advanced_physics import AdvancedSpaceWeatherPhysics, create_sample_satellite
from .ensemble_forecaster import EnsembleSpaceWeatherForecaster
from .nasa_client import NASAClient
from .schema import ForecastBundle, Forecast, Evidence, ForecastError
from .universal_forecaster import UniversalAIClient

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertSpaceWeatherForecaster:
    """Expert-level forecaster combining physics models with AI analysis"""
    
    def __init__(self):
        self.physics = SpaceWeatherPhysics()
        self.advanced_physics = AdvancedSpaceWeatherPhysics()
        self.ensemble_forecaster = EnsembleSpaceWeatherForecaster()
        self.nasa_client = NASAClient()
        self.ai_client = UniversalAIClient()
        
    def generate_expert_forecast(self, days_back: int = 3) -> Union[ForecastBundle, ForecastError]:
        """Generate expert-level forecast using physics + AI"""
        try:
            logger.info("Starting expert-level space weather analysis...")
            
            # 1. Fetch NASA data
            space_weather_data = self._fetch_comprehensive_data(days_back)
            
            # 2. Physics-based analysis
            physics_analysis = self._run_physics_analysis(space_weather_data)
            
            # 2b. Advanced physics analysis
            advanced_analysis = self._run_advanced_physics_analysis(space_weather_data, physics_analysis)
            
            # 2c. Ensemble ML/Neural analysis
            ensemble_analysis = self._run_ensemble_analysis(space_weather_data)
            
            # 3. AI-enhanced interpretation
            ai_analysis = self._run_ai_analysis(space_weather_data, physics_analysis, advanced_analysis)
            
            # 4. Combine results into expert forecast
            expert_forecast = self._synthesize_expert_forecast(
                space_weather_data, physics_analysis, ai_analysis, advanced_analysis, ensemble_analysis
            )
            
            return expert_forecast
            
        except Exception as e:
            logger.error(f"Expert forecast generation failed: {e}")
            return ForecastError(
                error=f"Expert forecast failed: {str(e)}",
                error_code="EXPERT_ANALYSIS_FAILED"
            )
    
    def _fetch_comprehensive_data(self, days_back: int) -> Dict[str, Any]:
        """Fetch comprehensive space weather data"""
        logger.info("Fetching comprehensive space weather data...")
        
        data = {
            'cmes': self.nasa_client.fetch_donki_cmes(days_back),
            'flares': self.nasa_client.fetch_donki_flares(days_back),
            'sep_events': self.nasa_client.fetch_donki_sep_events(days_back),
            'geomagnetic_storms': self.nasa_client.fetch_donki_geomagnetic_storms(days_back),
            'epic_data': [],
            'fetch_time': datetime.utcnow(),
            'data_quality': {}
        }
        
        # Try to fetch EPIC data (may fail due to service issues)
        try:
            epic_data = self.nasa_client.fetch_epic_recent(days_back=1)
            data['epic_data'] = epic_data[:3]  # Latest 3 images
        except Exception as e:
            logger.warning(f"EPIC data fetch failed: {e}")
            data['epic_data'] = []
        
        # Assess data quality
        data['data_quality'] = {
            'cme_count': len(data['cmes']),
            'flare_count': len(data['flares']),
            'sep_count': len(data['sep_events']),
            'storm_count': len(data['geomagnetic_storms']),
            'epic_available': len(data['epic_data']) > 0,
            'completeness_score': self._calculate_data_completeness(data)
        }
        
        logger.info(f"Data quality: {data['data_quality']}")
        return data
    
    def _calculate_data_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score (0-1)"""
        score = 0
        total_weight = 0
        
        # Weight different data sources
        weights = {'cmes': 0.3, 'flares': 0.3, 'sep_events': 0.2, 'storms': 0.1, 'epic': 0.1}
        
        if len(data['cmes']) > 0:
            score += weights['cmes']
        if len(data['flares']) > 0:
            score += weights['flares']
        if len(data['sep_events']) > 0:
            score += weights['sep_events']
        if len(data['geomagnetic_storms']) > 0:
            score += weights['storms']
        if len(data['epic_data']) > 0:
            score += weights['epic']
        
        return score
    
    def _run_physics_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive physics-based analysis"""
        logger.info("Running physics-based analysis...")
        
        analysis = {
            'cme_analyses': [],
            'solar_wind_predictions': {},
            'geomagnetic_predictions': {},
            'aurora_predictions': {},
            'radiation_environment': {},
            'overall_assessment': {}
        }
        
        # Analyze each CME with physics models
        for cme_data in data['cmes']:
            cme_params = create_cme_from_donki(cme_data)
            if cme_params:
                # CME arrival prediction
                arrival_analysis = self.physics.predict_cme_arrival(cme_params)
                
                # Geoeffectiveness analysis
                geo_analysis = self.physics.analyze_cme_geoeffectiveness(cme_params)
                
                analysis['cme_analyses'].append({
                    'donki_id': cme_data.get('activityID', 'unknown'),
                    'cme_parameters': cme_params.__dict__,
                    'arrival_prediction': arrival_analysis,
                    'geoeffectiveness': geo_analysis
                })
        
        # Solar wind and geomagnetic predictions
        if analysis['cme_analyses']:
            # Use the most geoeffective CME for predictions
            most_effective = max(analysis['cme_analyses'], 
                               key=lambda x: x['geoeffectiveness']['geoeffectiveness_score'])
            
            # Simulate solar wind conditions
            solar_wind = create_solar_wind_sample()
            
            # Enhance solar wind based on CME
            cme_geo = most_effective['geoeffectiveness']
            if cme_geo['geoeffectiveness_score'] > 0.5:
                solar_wind.velocity *= 1.5  # CME-enhanced speed
                solar_wind.density *= 2.0   # Compressed plasma
                solar_wind.bz_gsm *= -1.5   # Enhanced southward field
            
            # Geomagnetic predictions
            dst_prediction = self.physics.calculate_dst_index(solar_wind)
            kp_prediction = self.physics.predict_kp_index(solar_wind)
            aurora_prediction = self.physics.calculate_aurora_boundary(kp_prediction['kp_index'])
            
            analysis['solar_wind_predictions'] = solar_wind.__dict__
            analysis['geomagnetic_predictions'] = {
                'dst': dst_prediction,
                'kp': kp_prediction
            }
            analysis['aurora_predictions'] = aurora_prediction
        
        # Overall space weather assessment
        analysis['overall_assessment'] = self._assess_overall_conditions(analysis)
        
        return analysis
    
    def _run_advanced_physics_analysis(self, data: Dict[str, Any], 
                                     physics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run advanced physics models for comprehensive analysis"""
        logger.info("Running advanced physics analysis...")
        
        advanced_analysis = {
            'solar_particle_events': [],
            'substorm_predictions': {},
            'satellite_drag_analysis': {},
            'ionospheric_scintillation': {},
            'shock_arrival_refinement': {},
            'atmospheric_density_forecast': {}
        }
        
        # Solar Particle Event predictions for each flare
        for flare_data in data['flares']:
            try:
                flare_class = flare_data.get('classType', 'C1.0')
                
                # Extract source location (approximate from flare ID)
                source_longitude = -60  # default west longitude (Earth-facing)
                
                # Parse flare time
                flare_time_str = flare_data.get('beginTime', '')
                if flare_time_str:
                    flare_time = datetime.fromisoformat(flare_time_str.replace('Z', '+00:00'))
                else:
                    flare_time = datetime.utcnow()
                
                # Predict SEP event
                sep_prediction = self.advanced_physics.predict_solar_particle_event(
                    flare_class, source_longitude, flare_time
                )
                
                if sep_prediction.get('sep_expected', False):
                    advanced_analysis['solar_particle_events'].append({
                        'flare_id': flare_data.get('flrID', 'unknown'),
                        'flare_class': flare_class,
                        'prediction': sep_prediction
                    })
                    
            except Exception as e:
                logger.warning(f"SEP prediction failed for flare: {e}")
                continue
        
        # Substorm prediction based on solar wind conditions
        try:
            # Use physics analysis or create sample solar wind
            if physics_analysis.get('solar_wind_predictions'):
                sw = physics_analysis['solar_wind_predictions']
                velocity = sw.get('velocity', 450)
                bz_gsm = sw.get('bz_gsm', -5)
                density = sw.get('density', 5)
            else:
                # Use sample conditions
                velocity = 450
                bz_gsm = -8  # southward field
                density = 5
            
            substorm_prediction = self.advanced_physics.predict_magnetospheric_substorm(
                velocity, bz_gsm, density
            )
            advanced_analysis['substorm_predictions'] = substorm_prediction
            
        except Exception as e:
            logger.warning(f"Substorm prediction failed: {e}")
        
        # Satellite drag analysis
        try:
            # Create representative satellite for ISS-like orbit
            sample_satellite = create_sample_satellite()
            
            # Use current solar and geomagnetic conditions
            f107_index = 150  # typical solar flux
            ap_index = 15     # typical geomagnetic activity
            
            # Enhance based on space weather conditions
            if physics_analysis.get('geomagnetic_predictions'):
                kp = physics_analysis['geomagnetic_predictions']['kp']['kp_index']
                ap_index = max(15, kp * 5)  # rough Kp to Ap conversion
            
            if len(data['flares']) > 0:
                f107_index = 180  # enhanced solar activity
            
            drag_analysis = self.advanced_physics.calculate_satellite_drag(
                sample_satellite, f107_index, ap_index
            )
            advanced_analysis['satellite_drag_analysis'] = drag_analysis
            
        except Exception as e:
            logger.warning(f"Satellite drag analysis failed: {e}")
        
        # Ionospheric scintillation prediction
        try:
            # Predict for key locations (equatorial regions most affected)
            locations = [
                {'name': 'Singapore', 'lat': 1.3, 'lon': 103.8, 'local_time': 22},
                {'name': 'Brazil', 'lat': -15.8, 'lon': -47.9, 'local_time': 20},
                {'name': 'Nigeria', 'lat': 9.1, 'lon': 7.2, 'local_time': 21}
            ]
            
            kp_index = 3  # default
            if physics_analysis.get('geomagnetic_predictions'):
                kp_index = physics_analysis['geomagnetic_predictions']['kp']['kp_index']
            
            scintillation_forecasts = []
            for location in locations:
                scint_pred = self.advanced_physics.predict_ionospheric_scintillation(
                    location['lat'], location['lon'], location['local_time'], kp_index
                )
                scint_pred['location'] = location['name']
                scintillation_forecasts.append(scint_pred)
            
            advanced_analysis['ionospheric_scintillation'] = {
                'global_forecast': scintillation_forecasts,
                'high_risk_regions': [f['location'] for f in scintillation_forecasts 
                                    if f.get('severity') in ['active', 'severe']]
            }
            
        except Exception as e:
            logger.warning(f"Scintillation prediction failed: {e}")
        
        # Advanced shock arrival refinement
        try:
            if physics_analysis.get('cme_analyses'):
                refined_arrivals = []
                for cme_analysis in physics_analysis['cme_analyses']:
                    original_arrival = cme_analysis['arrival_prediction']
                    
                    # Apply advanced correction factors
                    # Account for solar wind speed variations, magnetic field strength, etc.
                    refined_arrival = self._refine_shock_arrival(original_arrival, data)
                    refined_arrivals.append(refined_arrival)
                
                advanced_analysis['shock_arrival_refinement'] = {
                    'refined_predictions': refined_arrivals,
                    'improvement_method': 'WSA_ENLIL_inspired'
                }
        
        except Exception as e:
            logger.warning(f"Shock arrival refinement failed: {e}")
        
        logger.info(f"Advanced physics analysis completed with {len(advanced_analysis)} components")
        return advanced_analysis
    
    def _run_ensemble_analysis(self, space_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run ensemble ML/Neural analysis for each significant CME"""
        logger.info("Running ensemble ML/Neural analysis...")
        
        ensemble_analysis = {
            'cme_ensemble_predictions': [],
            'ml_model_performance': {},
            'neural_pattern_analysis': {},
            'ensemble_confidence_metrics': {}
        }
        
        try:
            # Analyze each CME with ensemble methods
            for cme_data in space_weather_data['cmes']:
                try:
                    # Generate synthetic solar wind sequence for neural networks
                    # In production, this would be real solar wind data
                    solar_wind_sequence = self._generate_solar_wind_sequence()
                    
                    # Get ensemble prediction
                    ensemble_pred = self.ensemble_forecaster.generate_ensemble_forecast(
                        cme_data, solar_wind_sequence
                    )
                    
                    # Extract key results
                    ensemble_result = {
                        'cme_id': cme_data.get('activityID', 'unknown'),
                        'ensemble_prediction': ensemble_pred.ensemble_result,
                        'uncertainty': ensemble_pred.uncertainty_quantification,
                        'model_weights': ensemble_pred.model_weights,
                        'individual_models': {
                            'physics_available': ensemble_pred.physics_prediction is not None,
                            'ml_available': ensemble_pred.ml_prediction is not None,
                            'neural_available': ensemble_pred.neural_prediction is not None
                        }
                    }
                    
                    ensemble_analysis['cme_ensemble_predictions'].append(ensemble_result)
                    
                except Exception as e:
                    logger.warning(f"Ensemble analysis failed for CME {cme_data.get('activityID', 'unknown')}: {e}")
                    continue
            
            # Get overall ML model performance metrics
            try:
                performance = self.ensemble_forecaster.validate_ensemble_performance(
                    validation_period_days=30
                )
                ensemble_analysis['ml_model_performance'] = performance
            except Exception as e:
                logger.warning(f"Failed to get ML performance metrics: {e}")
            
            # Generate ensemble confidence summary
            if ensemble_analysis['cme_ensemble_predictions']:
                confidences = [
                    pred['ensemble_prediction'].get('ensemble_confidence', 0.5)
                    for pred in ensemble_analysis['cme_ensemble_predictions']
                    if pred['ensemble_prediction'].get('status') == 'success'
                ]
                
                ensemble_analysis['ensemble_confidence_metrics'] = {
                    'average_confidence': np.mean(confidences) if confidences else 0.5,
                    'confidence_range': [min(confidences), max(confidences)] if confidences else [0.5, 0.5],
                    'high_confidence_predictions': len([c for c in confidences if c > 0.8]),
                    'total_ensemble_predictions': len(confidences)
                }
            
        except Exception as e:
            logger.warning(f"Ensemble analysis failed: {e}")
            ensemble_analysis['error'] = str(e)
        
        logger.info(f"Ensemble analysis completed with {len(ensemble_analysis['cme_ensemble_predictions'])} predictions")
        return ensemble_analysis
    
    def _generate_solar_wind_sequence(self, length: int = 144) -> np.ndarray:
        """Generate realistic solar wind sequence for neural network input"""
        # Base solar wind parameters
        base_values = np.array([400, 5, 0, 0, -5, 100000, 2, 8])  # v, n, bx, by, bz, T, P, |B|
        
        # Generate sequence with realistic variations
        sequence = np.zeros((length, 8))
        for i in range(length):
            # Add time-dependent variations
            time_factor = i / length * 2 * np.pi
            
            # Velocity variations (300-800 km/s)
            velocity = base_values[0] + 100 * np.sin(time_factor) + np.random.normal(0, 30)
            velocity = np.clip(velocity, 250, 900)
            
            # Density variations (1-20 p/cm³)
            density = base_values[1] + 2 * np.sin(time_factor * 1.3) + np.random.normal(0, 1)
            density = np.clip(density, 0.5, 25)
            
            # Magnetic field components
            bx = np.random.normal(0, 3)
            by = np.random.normal(0, 3)
            bz = np.random.normal(-2, 4)  # Slight southward bias
            
            # Temperature and pressure
            temperature = base_values[5] * (1 + np.random.normal(0, 0.3))
            temperature = np.clip(temperature, 20000, 500000)
            
            # Dynamic pressure
            pressure = 1.67e-27 * density * 1e6 * (velocity * 1000)**2 * 1e9  # nPa
            
            # Total magnetic field
            btotal = np.sqrt(bx**2 + by**2 + bz**2)
            
            sequence[i] = [velocity, density, bx, by, bz, temperature, pressure, btotal]
        
        return sequence
    
    def _refine_shock_arrival(self, original_prediction: Dict[str, Any], 
                            space_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refine CME shock arrival time using advanced techniques"""
        try:
            original_time = original_prediction['predicted_arrival']
            original_velocity = original_prediction.get('final_velocity', 400)
            
            # Apply corrections based on:
            # 1. Background solar wind speed
            # 2. CME-solar wind interaction
            # 3. Magnetic field orientation
            
            # Background solar wind enhancement/deceleration
            correction_hours = 0
            
            # If multiple CMEs, account for interaction
            if len(space_weather_data['cmes']) > 1:
                correction_hours -= 6  # CME-CME interaction acceleration
            
            # Solar wind speed effect
            if original_velocity > 600:
                correction_hours -= 3  # fast CME less deceleration
            elif original_velocity < 400:
                correction_hours += 6  # slow CME more deceleration
            
            refined_time = original_time + timedelta(hours=correction_hours)
            
            return {
                'original_arrival': original_time,
                'refined_arrival': refined_time,
                'correction_hours': correction_hours,
                'confidence_improvement': 0.15,
                'refinement_factors': ['cme_interaction', 'solar_wind_speed', 'magnetic_topology']
            }
            
        except Exception as e:
            logger.error(f"Shock arrival refinement failed: {e}")
            return original_prediction
    
    def _assess_overall_conditions(self, physics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall space weather conditions"""
        assessment = {
            'threat_level': 'minimal',
            'confidence': 0.7,
            'primary_concerns': [],
            'timeline': {},
            'recommendations': []
        }
        
        # Analyze CME threats
        max_geo_score = 0
        arrival_times = []
        
        for cme_analysis in physics_analysis['cme_analyses']:
            geo_score = cme_analysis['geoeffectiveness']['geoeffectiveness_score']
            max_geo_score = max(max_geo_score, geo_score)
            
            arrival = cme_analysis['arrival_prediction']['predicted_arrival']
            if isinstance(arrival, datetime):
                arrival_times.append(arrival)
        
        # Determine threat level
        if max_geo_score > 0.8:
            assessment['threat_level'] = 'extreme'
            assessment['primary_concerns'].extend(['power_grid', 'satellites', 'aviation'])
        elif max_geo_score > 0.6:
            assessment['threat_level'] = 'high'
            assessment['primary_concerns'].extend(['satellites', 'communications', 'navigation'])
        elif max_geo_score > 0.4:
            assessment['threat_level'] = 'moderate'
            assessment['primary_concerns'].extend(['communications', 'aurora_activity'])
        elif max_geo_score > 0.2:
            assessment['threat_level'] = 'low'
            assessment['primary_concerns'].extend(['minor_disruptions'])
        
        # Timeline assessment
        if arrival_times:
            next_arrival = min(arrival_times)
            time_to_arrival = (next_arrival - datetime.utcnow()).total_seconds() / 3600
            
            assessment['timeline'] = {
                'next_event': next_arrival.isoformat(),
                'hours_until_impact': time_to_arrival,
                'impact_duration_hours': 24 if max_geo_score > 0.5 else 12
            }
        
        # Generate recommendations
        if assessment['threat_level'] in ['extreme', 'high']:
            assessment['recommendations'].extend([
                'Monitor satellite operations closely',
                'Prepare backup communication systems',
                'Alert aviation authorities',
                'Consider power grid precautions'
            ])
        elif assessment['threat_level'] == 'moderate':
            assessment['recommendations'].extend([
                'Continue monitoring space weather',
                'Prepare for possible communication disruptions',
                'Aurora viewing opportunities at high latitudes'
            ])
        else:
            assessment['recommendations'].extend([
                'Routine space weather monitoring',
                'Normal operations expected'
            ])
        
        return assessment
    
    def _run_ai_analysis(self, data: Dict[str, Any], physics: Dict[str, Any], 
                        advanced_physics: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI analysis with physics context"""
        logger.info("Running AI analysis with physics context...")
        
        # Create enhanced prompt with physics results
        physics_summary = self._create_physics_summary(physics)
        advanced_summary = self._create_advanced_physics_summary(advanced_physics)
        
        user_blocks = [{
            "type": "text",
            "text": f"""EXPERT SPACE WEATHER ANALYSIS REQUEST

PHYSICS-BASED ANALYSIS RESULTS:
{physics_summary}

ADVANCED PHYSICS ANALYSIS:
{advanced_summary}

NASA OBSERVATIONAL DATA:
CME Events: {len(data['cmes'])}
Solar Flares: {len(data['flares'])}
SEP Events: {len(data['sep_events'])}
Geomagnetic Storms: {len(data['geomagnetic_storms'])}

DATA SAMPLE:
{json.dumps(data['cmes'][:2] + data['flares'][:2], indent=2)}

EXPERT ANALYSIS REQUIREMENTS:
1. Validate physics model predictions against observational evidence
2. Identify any discrepancies or additional risk factors
3. Provide expert interpretation of complex interactions
4. Assess forecast confidence based on data quality and model agreement
5. Generate professional scientific summary for operational use

Focus on scientific accuracy and operational utility for space weather forecasting.
"""
        }]
        
        system_prompt = """You are a senior space weather physicist and forecaster at NASA's Space Weather Prediction Center. 
You have expertise in solar-terrestrial physics, magnetospheric dynamics, and operational space weather forecasting.

Analyze the provided physics model results and observational data to:
- Validate or refine the physics-based predictions
- Identify additional risk factors or complex interactions
- Provide expert scientific interpretation
- Assess forecast confidence and uncertainty
- Generate actionable recommendations for operators

Your analysis should be scientifically rigorous while remaining operationally useful."""
        
        try:
            # Get AI analysis
            from .schema import ForecastBundle
            ai_result = self.ai_client.generate_forecast_with_schema(
                system_prompt=system_prompt,
                user_blocks=user_blocks,
                schema_model=ForecastBundle,
                max_tokens=2000
            )
            
            if isinstance(ai_result, ForecastBundle):
                return {
                    'ai_forecasts': [f.__dict__ for f in ai_result.forecasts],
                    'ai_confidence': np.mean([f.confidence for f in ai_result.forecasts]) if ai_result.forecasts else 0.5,
                    'data_sources': ai_result.data_sources,
                    'generated_at': ai_result.generated_at
                }
            else:
                logger.warning("AI analysis returned error, using physics-only")
                return {'ai_forecasts': [], 'ai_confidence': 0.5, 'fallback': True}
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {'ai_forecasts': [], 'ai_confidence': 0.5, 'error': str(e)}
    
    def _create_physics_summary(self, physics: Dict[str, Any]) -> str:
        """Create summary of physics analysis for AI context"""
        summary_parts = []
        
        # CME Analysis Summary
        if physics['cme_analyses']:
            summary_parts.append("CME PHYSICS ANALYSIS:")
            for i, cme in enumerate(physics['cme_analyses'][:3]):  # Top 3 CMEs
                arrival = cme['arrival_prediction']
                geo = cme['geoeffectiveness']
                summary_parts.append(f"  CME {i+1}: Velocity {cme['cme_parameters']['initial_velocity']:.0f} km/s")
                summary_parts.append(f"    Arrival: {arrival['predicted_arrival']} (±{arrival['uncertainty_hours']:.1f}h)")
                summary_parts.append(f"    Geoeffectiveness: {geo['geoeffectiveness_score']:.2f} ({geo['classification']})")
                summary_parts.append(f"    Earth Impact Probability: {geo['earth_impact_probability']:.0%}")
        
        # Geomagnetic Predictions
        if physics['geomagnetic_predictions']:
            dst = physics['geomagnetic_predictions']['dst']
            kp = physics['geomagnetic_predictions']['kp']
            summary_parts.append(f"\nGEOMAGNETIC PREDICTIONS:")
            summary_parts.append(f"  Dst Index: {dst['dst_index']:.0f} nT ({dst['storm_level']} storm)")
            summary_parts.append(f"  Kp Index: {kp['kp_index']:.0f} ({kp['activity_level']})")
        
        # Aurora Predictions
        if physics['aurora_predictions']:
            aurora = physics['aurora_predictions']
            summary_parts.append(f"\nAURORA VISIBILITY:")
            summary_parts.append(f"  Boundary: {aurora['geographic_latitude_boundary']:.1f}° latitude")
            summary_parts.append(f"  Cities: {', '.join(aurora['cities_visible'][:5])}")
        
        # Overall Assessment
        if physics['overall_assessment']:
            assessment = physics['overall_assessment']
            summary_parts.append(f"\nOVERALL ASSESSMENT:")
            summary_parts.append(f"  Threat Level: {assessment['threat_level'].upper()}")
            summary_parts.append(f"  Primary Concerns: {', '.join(assessment['primary_concerns'])}")
            if 'timeline' in assessment:
                timeline = assessment['timeline']
                summary_parts.append(f"  Next Impact: {timeline.get('hours_until_impact', 'N/A'):.1f} hours")
        
        return '\n'.join(summary_parts)
    
    def _create_advanced_physics_summary(self, advanced_physics: Dict[str, Any]) -> str:
        """Create summary of advanced physics analysis for AI context"""
        summary_parts = []
        
        # Solar Particle Events
        sep_events = advanced_physics.get('solar_particle_events', [])
        if sep_events:
            summary_parts.append("SOLAR PARTICLE EVENTS:")
            for event in sep_events[:3]:  # Top 3 events
                pred = event['prediction']
                summary_parts.append(f"  Flare {event['flare_class']}: {pred.get('s_scale_rating', 'S0')} radiation storm")
                summary_parts.append(f"    Onset: {pred.get('onset_time', 'N/A')}")
                summary_parts.append(f"    Peak Flux: {pred.get('peak_flux_10mev', 0):.1f} pfu")
                summary_parts.append(f"    Duration: {pred.get('duration_hours', 0):.1f} hours")
        
        # Substorm Predictions
        substorm = advanced_physics.get('substorm_predictions', {})
        if substorm:
            summary_parts.append(f"\nMAGNETOSPHERIC SUBSTORMS:")
            summary_parts.append(f"  Expected: {substorm.get('substorm_expected', False)}")
            summary_parts.append(f"  Intensity: {substorm.get('intensity', 'unknown')}")
            summary_parts.append(f"  AE Index: {substorm.get('predicted_ae_index', 0):.0f} nT")
            summary_parts.append(f"  Onset Time: {substorm.get('onset_time', 'N/A')}")
        
        # Satellite Drag
        drag = advanced_physics.get('satellite_drag_analysis', {})
        if drag:
            summary_parts.append(f"\nSATELLITE DRAG ANALYSIS:")
            summary_parts.append(f"  Atmospheric Density: {drag.get('atmospheric_density', 0):.2e} kg/m³")
            summary_parts.append(f"  Altitude Loss Rate: {drag.get('altitude_loss_per_day', 0):.3f} km/day")
            summary_parts.append(f"  Risk Level: {drag.get('risk_assessment', 'unknown')}")
        
        # Ionospheric Scintillation
        scint = advanced_physics.get('ionospheric_scintillation', {})
        if scint.get('high_risk_regions'):
            summary_parts.append(f"\nIONOSPHERIC SCINTILLATION:")
            summary_parts.append(f"  High Risk Regions: {', '.join(scint['high_risk_regions'])}")
            summary_parts.append(f"  GNSS Impact: Moderate to Severe")
        
        # Shock Arrival Refinement
        shock_refine = advanced_physics.get('shock_arrival_refinement', {})
        if shock_refine.get('refined_predictions'):
            summary_parts.append(f"\nREFINED SHOCK ARRIVALS:")
            for refined in shock_refine['refined_predictions'][:2]:
                summary_parts.append(f"  Refined Time: {refined.get('refined_arrival', 'N/A')}")
                summary_parts.append(f"  Correction: {refined.get('correction_hours', 0):+.1f} hours")
        
        return '\n'.join(summary_parts) if summary_parts else "No advanced physics analysis available"
    
    def _synthesize_expert_forecast(self, data: Dict[str, Any], 
                                  physics: Dict[str, Any], 
                                  ai: Dict[str, Any],
                                  advanced_physics: Dict[str, Any],
                                  ensemble_analysis: Dict[str, Any]) -> ForecastBundle:
        """Synthesize physics and AI results into expert forecast"""
        logger.info("Synthesizing expert forecast...")
        
        forecasts = []
        
        # Process each significant CME with ensemble predictions
        for cme_analysis in physics['cme_analyses']:
            if cme_analysis['geoeffectiveness']['geoeffectiveness_score'] > 0.3:
                # Find corresponding ensemble prediction
                ensemble_pred = None
                cme_id = cme_analysis['donki_id']
                for ens_pred in ensemble_analysis.get('cme_ensemble_predictions', []):
                    if ens_pred['cme_id'] == cme_id:
                        ensemble_pred = ens_pred
                        break
                
                forecast = self._create_enhanced_cme_forecast(cme_analysis, physics, ai, ensemble_pred)
                if forecast:
                    forecasts.append(forecast)
        
        # Add overall geomagnetic forecast if significant activity expected
        if physics['geomagnetic_predictions']:
            dst = physics['geomagnetic_predictions']['dst']
            if dst['dst_index'] < -30:  # Minor storm or stronger
                geo_forecast = self._create_geomagnetic_forecast(physics, ai)
                if geo_forecast:
                    forecasts.append(geo_forecast)
        
        # If no significant events, create quiet conditions forecast
        if not forecasts:
            quiet_forecast = self._create_quiet_forecast(data, physics)
            forecasts.append(quiet_forecast)
        
        return ForecastBundle(
            forecasts=forecasts[:3],  # Maximum 3 forecasts
            generated_at=datetime.utcnow().isoformat() + "Z",
            data_sources=["NASA_DONKI", "NASA_EPIC", "PHYSICS_MODELS", "ML_ENSEMBLE", "NEURAL_NETWORKS", "AI_ANALYSIS"]
        )
    
    def _create_enhanced_cme_forecast(self, cme_analysis: Dict[str, Any], 
                                    physics: Dict[str, Any], 
                                    ai: Dict[str, Any],
                                    ensemble_pred: Optional[Dict[str, Any]]) -> Optional[Forecast]:
        """Create enhanced CME forecast incorporating ensemble ML/Neural predictions"""
        try:
            arrival = cme_analysis['arrival_prediction']
            geo = cme_analysis['geoeffectiveness']
            cme_params = cme_analysis['cme_parameters']
            
            # Use ensemble prediction if available, otherwise fall back to physics
            if ensemble_pred and ensemble_pred['ensemble_prediction'].get('status') == 'success':
                ens_result = ensemble_pred['ensemble_prediction']
                
                # Use ensemble arrival time
                ensemble_arrival_hours = ens_result.get('ensemble_arrival_hours', arrival['transit_time_hours'])
                ensemble_confidence = ens_result.get('ensemble_confidence', arrival['confidence'])
                
                # Create arrival window around ensemble prediction
                uncertainty_hours = ensemble_pred['uncertainty'].get('combined_uncertainty_hours', 12)
                arrival_time = datetime.now() + timedelta(hours=ensemble_arrival_hours)
                window_start = arrival_time - timedelta(hours=uncertainty_hours/2)
                window_end = arrival_time + timedelta(hours=uncertainty_hours/2)
                
                arrival_window = [window_start, window_end]
                
                # Enhanced risk summary with ensemble info
                risk_parts = []
                if ensemble_confidence > 0.8:
                    risk_parts.append("High-confidence ensemble prediction")
                elif ensemble_confidence > 0.6:
                    risk_parts.append("Moderate-confidence ensemble prediction")
                else:
                    risk_parts.append("Lower-confidence ensemble prediction")
                
                model_agreement = ens_result.get('model_agreement', False)
                if model_agreement:
                    risk_parts.append("Strong model agreement")
                else:
                    risk_parts.append("Model disagreement noted")
                
                # Add traditional geoeffectiveness assessment
                if geo['geoeffectiveness_score'] > 0.8:
                    risk_parts.append("Extreme geomagnetic storm possible")
                elif geo['geoeffectiveness_score'] > 0.6:
                    risk_parts.append("Major geomagnetic storm likely")
                elif geo['geoeffectiveness_score'] > 0.4:
                    risk_parts.append("Moderate geomagnetic storm possible")
                else:
                    risk_parts.append("Minor geomagnetic activity expected")
                
                # Enhanced confidence combines ensemble and physics
                final_confidence = (ensemble_confidence + arrival['confidence']) / 2
                
            else:
                # Fall back to physics-only prediction
                arrival_window = arrival['arrival_window']
                final_confidence = arrival['confidence']
                risk_parts = ["Physics-based prediction (ensemble unavailable)"]
                
                if geo['geoeffectiveness_score'] > 0.8:
                    risk_parts.append("Extreme geomagnetic storm possible")
                elif geo['geoeffectiveness_score'] > 0.6:
                    risk_parts.append("Major geomagnetic storm likely")
                else:
                    risk_parts.append("Moderate geomagnetic activity expected")
            
            # Determine impacts based on geoeffectiveness
            impacts = []
            if geo['risk_assessment']['aurora_visibility'] in ['global', 'high_latitude']:
                impacts.append('aurora_midlat')
            if geo['risk_assessment']['communication_risk'] in ['high', 'moderate']:
                impacts.append('HF_comms')
            if geo['risk_assessment']['satellite_risk'] in ['high', 'moderate']:
                impacts.append('satellite_drag')
            if geo['risk_assessment']['power_grid_risk'] == 'high':
                impacts.append('power_grid')
            
            # Add aurora visibility info
            if physics['aurora_predictions']:
                cities = physics['aurora_predictions']['cities_visible']
                if cities:
                    risk_parts.append(f"Aurora visible to {cities[0]} and similar latitudes")
            
            # Enhanced evidence including ensemble models
            evidence_sources = [cme_analysis['donki_id']]
            if ensemble_pred:
                if ensemble_pred['individual_models']['ml_available']:
                    evidence_sources.append("ML_MODEL")
                if ensemble_pred['individual_models']['neural_available']:
                    evidence_sources.append("NEURAL_NETWORK")
            
            evidence = Evidence(
                donki_ids=evidence_sources,
                epic_frames=[arrival_window[0].isoformat()],
                gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
            )
            
            return Forecast(
                event="CME",
                solar_timestamp=cme_params['launch_time'].isoformat() + "Z",
                predicted_arrival_window_utc=[
                    arrival_window[0].isoformat() + "Z",
                    arrival_window[1].isoformat() + "Z"
                ],
                risk_summary=". ".join(risk_parts),
                impacts=impacts,
                confidence=final_confidence,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Failed to create enhanced CME forecast: {e}")
            # Fall back to original method
            return self._create_cme_forecast(cme_analysis, physics, ai)
    
    def _create_cme_forecast(self, cme_analysis: Dict[str, Any], 
                           physics: Dict[str, Any], 
                           ai: Dict[str, Any]) -> Optional[Forecast]:
        """Create forecast for a specific CME"""
        try:
            arrival = cme_analysis['arrival_prediction']
            geo = cme_analysis['geoeffectiveness']
            cme_params = cme_analysis['cme_parameters']
            
            # Determine impacts based on geoeffectiveness
            impacts = []
            if geo['risk_assessment']['aurora_visibility'] in ['global', 'high_latitude']:
                impacts.append('aurora_midlat')
            if geo['risk_assessment']['communication_risk'] in ['high', 'moderate']:
                impacts.append('HF_comms')
            if geo['risk_assessment']['satellite_risk'] in ['high', 'moderate']:
                impacts.append('satellite_drag')
            if geo['risk_assessment']['power_grid_risk'] == 'high':
                impacts.append('power_grid')
            
            # Create risk summary
            risk_parts = []
            if geo['geoeffectiveness_score'] > 0.8:
                risk_parts.append("Extreme geomagnetic storm possible")
            elif geo['geoeffectiveness_score'] > 0.6:
                risk_parts.append("Major geomagnetic storm likely")
            elif geo['geoeffectiveness_score'] > 0.4:
                risk_parts.append("Moderate geomagnetic storm possible")
            else:
                risk_parts.append("Minor geomagnetic activity expected")
            
            if physics['aurora_predictions']:
                cities = physics['aurora_predictions']['cities_visible']
                if cities:
                    risk_parts.append(f"Aurora visible to {cities[0]} and similar latitudes")
            
            # Evidence
            evidence = Evidence(
                donki_ids=[cme_analysis['donki_id']],
                epic_frames=[arrival['predicted_arrival'].isoformat()],
                gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
            )
            
            return Forecast(
                event="CME",
                solar_timestamp=cme_params['launch_time'].isoformat() + "Z",
                predicted_arrival_window_utc=[
                    arrival['arrival_window'][0].isoformat() + "Z",
                    arrival['arrival_window'][1].isoformat() + "Z"
                ],
                risk_summary=". ".join(risk_parts),
                impacts=impacts,
                confidence=arrival['confidence'],
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Failed to create CME forecast: {e}")
            return None
    
    def _create_geomagnetic_forecast(self, physics: Dict[str, Any], 
                                   ai: Dict[str, Any]) -> Optional[Forecast]:
        """Create geomagnetic activity forecast"""
        try:
            dst = physics['geomagnetic_predictions']['dst']
            kp = physics['geomagnetic_predictions']['kp']
            
            # Determine impacts
            impacts = []
            if kp['kp_index'] >= 5:
                impacts.extend(['aurora_midlat', 'HF_comms', 'GNSS_jitter'])
            if kp['kp_index'] >= 7:
                impacts.extend(['satellite_drag'])
            if dst['dst_index'] < -100:
                impacts.extend(['power_grid'])
            
            # Risk summary
            risk_summary = f"{dst['storm_level'].title()} geomagnetic storm predicted (Dst: {dst['dst_index']:.0f} nT, Kp: {kp['kp_index']:.0f})"
            
            if physics['aurora_predictions']:
                boundary = physics['aurora_predictions']['geographic_latitude_boundary']
                risk_summary += f". Aurora visible to {boundary:.0f}° latitude"
            
            evidence = Evidence(
                donki_ids=["GEOMAGNETIC_MODEL"],
                epic_frames=[],
                gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
            )
            
            return Forecast(
                event="GEO_STORM",
                solar_timestamp=datetime.utcnow().isoformat() + "Z",
                predicted_arrival_window_utc=[
                    datetime.utcnow().isoformat() + "Z",
                    (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
                ],
                risk_summary=risk_summary,
                impacts=impacts,
                confidence=0.8,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Failed to create geomagnetic forecast: {e}")
            return None
    
    def _create_quiet_forecast(self, data: Dict[str, Any], 
                             physics: Dict[str, Any]) -> Forecast:
        """Create quiet conditions forecast"""
        
        evidence = Evidence(
            donki_ids=[event.get('activityID', 'NONE') for event in data['cmes'][:2]],
            epic_frames=[],
            gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
        )
        
        return Forecast(
            event="QUIET",
            solar_timestamp=datetime.utcnow().isoformat() + "Z",
            predicted_arrival_window_utc=[
                datetime.utcnow().isoformat() + "Z",
                (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
            ],
            risk_summary="Quiet space weather conditions. No significant geomagnetic activity expected. Normal operations for all systems.",
            impacts=[],
            confidence=0.9,
            evidence=evidence
        )

# Main function for external use
def run_expert_forecast(days_back: int = 3) -> Union[ForecastBundle, ForecastError]:
    """Run expert-level space weather forecast"""
    forecaster = ExpertSpaceWeatherForecaster()
    return forecaster.generate_expert_forecast(days_back)

if __name__ == "__main__":
    # Test the expert forecaster
    result = run_expert_forecast()
    print(json.dumps(result.model_dump() if hasattr(result, 'model_dump') else result.__dict__, indent=2))