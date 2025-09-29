"""
Ensemble Space Weather Forecasting System
Combines physics models, machine learning, and neural networks for superior accuracy
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
import logging
import json
from pathlib import Path

# Import our forecasting modules
from .space_physics import SpaceWeatherPhysics, CMEParameters, create_cme_from_donki
from .advanced_physics import AdvancedSpaceWeatherPhysics
from .ml_forecaster import MLSpaceWeatherForecaster, MLPrediction
from .neural_forecaster import NeuralSpaceWeatherForecaster
from .schema import ForecastBundle, Forecast, Evidence, ForecastError

logger = logging.getLogger(__name__)

class EnsemblePrediction:
    """Ensemble prediction result combining multiple models"""
    
    def __init__(self):
        self.physics_prediction: Optional[Dict[str, Any]] = None
        self.ml_prediction: Optional[MLPrediction] = None
        self.neural_prediction: Optional[Dict[str, Any]] = None
        self.ensemble_result: Dict[str, Any] = {}
        self.confidence_metrics: Dict[str, float] = {}
        self.model_weights: Dict[str, float] = {}
        self.uncertainty_quantification: Dict[str, Any] = {}

class ModelPerformanceTracker:
    """Tracks and validates model performance over time"""
    
    def __init__(self, tracking_db: str = "data/model_performance.db"):
        self.tracking_db = Path(tracking_db)
        self.tracking_db.parent.mkdir(parents=True, exist_ok=True)
        self._init_tracking_database()
        
    def _init_tracking_database(self):
        """Initialize performance tracking database"""
        import sqlite3
        
        with sqlite3.connect(self.tracking_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    predicted_value REAL NOT NULL,
                    predicted_time TEXT,
                    confidence REAL,
                    actual_value REAL,
                    actual_time TEXT,
                    error_magnitude REAL,
                    time_error_hours REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    evaluation_period_start TEXT NOT NULL,
                    evaluation_period_end TEXT NOT NULL,
                    total_predictions INTEGER,
                    mean_absolute_error REAL,
                    root_mean_square_error REAL,
                    mean_time_error_hours REAL,
                    accuracy_within_threshold REAL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def log_prediction(self, model_type: str, prediction_type: str, 
                      predicted_value: float, predicted_time: Optional[str] = None,
                      confidence: float = 0.5):
        """Log a model prediction for future validation"""
        import sqlite3
        
        with sqlite3.connect(self.tracking_db) as conn:
            conn.execute("""
                INSERT INTO model_predictions 
                (timestamp, model_type, prediction_type, predicted_value, 
                 predicted_time, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                model_type,
                prediction_type,
                predicted_value,
                predicted_time,
                confidence
            ))
    
    def update_with_actual_outcome(self, prediction_id: int, 
                                 actual_value: float, 
                                 actual_time: Optional[str] = None):
        """Update prediction with actual observed outcome"""
        import sqlite3
        
        with sqlite3.connect(self.tracking_db) as conn:
            # Calculate errors
            cursor = conn.execute("""
                SELECT predicted_value, predicted_time FROM model_predictions 
                WHERE id = ?
            """, (prediction_id,))
            
            result = cursor.fetchone()
            if result:
                predicted_value, predicted_time = result
                error_magnitude = abs(actual_value - predicted_value)
                
                time_error_hours = 0
                if predicted_time and actual_time:
                    try:
                        pred_dt = datetime.fromisoformat(predicted_time)
                        actual_dt = datetime.fromisoformat(actual_time)
                        time_error_hours = abs((actual_dt - pred_dt).total_seconds() / 3600)
                    except Exception:
                        time_error_hours = 0
                
                # Update record
                conn.execute("""
                    UPDATE model_predictions 
                    SET actual_value = ?, actual_time = ?, 
                        error_magnitude = ?, time_error_hours = ?
                    WHERE id = ?
                """, (actual_value, actual_time, error_magnitude, time_error_hours, prediction_id))
    
    def calculate_model_performance(self, model_type: str, 
                                  days_back: int = 30) -> Dict[str, Any]:
        """Calculate recent performance metrics for a model"""
        import sqlite3
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute("""
                SELECT prediction_type, predicted_value, actual_value, 
                       error_magnitude, time_error_hours, confidence
                FROM model_predictions 
                WHERE model_type = ? AND timestamp > ? AND actual_value IS NOT NULL
            """, (model_type, cutoff_date))
            
            results = cursor.fetchall()
            
            if not results:
                return {'status': 'insufficient_data', 'predictions_count': 0}
            
            # Group by prediction type
            by_type = {}
            for pred_type, pred_val, actual_val, error_mag, time_error, conf in results:
                if pred_type not in by_type:
                    by_type[pred_type] = []
                by_type[pred_type].append({
                    'predicted': pred_val,
                    'actual': actual_val,
                    'error': error_mag,
                    'time_error': time_error or 0,
                    'confidence': conf or 0.5
                })
            
            # Calculate metrics for each prediction type
            performance = {}
            for pred_type, predictions in by_type.items():
                errors = [p['error'] for p in predictions]
                time_errors = [p['time_error'] for p in predictions]
                confidences = [p['confidence'] for p in predictions]
                
                performance[pred_type] = {
                    'count': len(predictions),
                    'mean_absolute_error': np.mean(errors),
                    'root_mean_square_error': np.sqrt(np.mean([e**2 for e in errors])),
                    'mean_time_error_hours': np.mean(time_errors),
                    'accuracy_within_20_percent': np.mean([
                        e / abs(p['actual']) < 0.2 for p in predictions if p['actual'] != 0
                    ]),
                    'average_confidence': np.mean(confidences),
                    'confidence_calibration': self._calculate_confidence_calibration(predictions)
                }
            
            return {
                'status': 'success',
                'model_type': model_type,
                'evaluation_period_days': days_back,
                'by_prediction_type': performance,
                'overall_predictions': len(results)
            }
    
    def _calculate_confidence_calibration(self, predictions: List[Dict]) -> float:
        """Calculate how well-calibrated the model's confidence is"""
        if len(predictions) < 10:
            return 0.5
        
        # Group predictions by confidence bins
        bins = np.linspace(0, 1, 11)
        bin_accuracies = []
        
        for i in range(len(bins) - 1):
            bin_preds = [p for p in predictions 
                        if bins[i] <= p['confidence'] < bins[i+1]]
            
            if len(bin_preds) > 0:
                # Calculate accuracy within this confidence bin
                accuracy = np.mean([
                    p['error'] / abs(p['actual']) < 0.2 
                    for p in bin_preds if p['actual'] != 0
                ])
                bin_accuracies.append(accuracy)
        
        # Well-calibrated models have accuracy ≈ confidence
        return np.mean(bin_accuracies) if bin_accuracies else 0.5

class EnsembleSpaceWeatherForecaster:
    """Advanced ensemble forecasting system"""
    
    def __init__(self):
        self.physics_engine = SpaceWeatherPhysics()
        self.advanced_physics = AdvancedSpaceWeatherPhysics()
        self.ml_forecaster = MLSpaceWeatherForecaster()
        
        # Initialize neural forecaster if TensorFlow is available
        try:
            self.neural_forecaster = NeuralSpaceWeatherForecaster()
            self.neural_available = True
        except ImportError:
            self.neural_forecaster = None
            self.neural_available = False
            logger.warning("Neural forecasting disabled: TensorFlow not available")
        
        self.performance_tracker = ModelPerformanceTracker()
        
        # Model weights (learned from historical performance)
        self.default_weights = {
            'physics': 0.4,
            'ml': 0.35,
            'neural': 0.25
        }
        
    def generate_ensemble_forecast(self, cme_data: Dict[str, Any], 
                                 solar_wind_sequence: Optional[np.ndarray] = None) -> EnsemblePrediction:
        """Generate comprehensive ensemble forecast"""
        
        logger.info("Generating ensemble space weather forecast...")
        
        ensemble_pred = EnsemblePrediction()
        
        # 1. Physics-based prediction
        try:
            cme_params = create_cme_from_donki(cme_data)
            if cme_params:
                physics_result = self._get_physics_prediction(cme_params)
                ensemble_pred.physics_prediction = physics_result
                logger.info("Physics prediction completed")
            else:
                logger.warning("Failed to create CME parameters from DONKI data")
        except Exception as e:
            logger.error(f"Physics prediction failed: {e}")
        
        # 2. Machine learning prediction
        try:
            ml_input = self._extract_ml_features(cme_data)
            ml_result = self.ml_forecaster.predict_cme_arrival(ml_input)
            ensemble_pred.ml_prediction = ml_result
            
            # Log ML prediction for tracking
            self.performance_tracker.log_prediction(
                'ml_ensemble', 'cme_arrival_hours', 
                ml_result.prediction, 
                confidence=ml_result.confidence
            )
            logger.info("ML prediction completed")
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
        
        # 3. Neural network prediction (if available)
        if self.neural_available and solar_wind_sequence is not None:
            try:
                neural_result = self.neural_forecaster.predict_with_neural_ensemble(solar_wind_sequence)
                ensemble_pred.neural_prediction = neural_result
                logger.info("Neural prediction completed")
            except Exception as e:
                logger.error(f"Neural prediction failed: {e}")
        
        # 4. Combine predictions using ensemble methods
        ensemble_result = self._combine_predictions(ensemble_pred)
        ensemble_pred.ensemble_result = ensemble_result
        
        # 5. Calculate uncertainty quantification
        uncertainty = self._quantify_uncertainty(ensemble_pred)
        ensemble_pred.uncertainty_quantification = uncertainty
        
        # 6. Update model weights based on recent performance
        updated_weights = self._update_model_weights()
        ensemble_pred.model_weights = updated_weights
        
        logger.info("Ensemble forecast generation completed")
        return ensemble_pred
    
    def _get_physics_prediction(self, cme_params: CMEParameters) -> Dict[str, Any]:
        """Get comprehensive physics-based prediction"""
        
        # Basic physics models
        arrival_pred = self.physics_engine.predict_cme_arrival(cme_params)
        geo_analysis = self.physics_engine.analyze_cme_geoeffectiveness(cme_params)
        
        # Advanced physics models
        sep_prediction = self.advanced_physics.predict_solar_particle_event(
            f"M{np.random.uniform(1, 9):.1f}",  # Approximate flare class
            cme_params.source_longitude,
            cme_params.launch_time
        )
        
        substorm_prediction = self.advanced_physics.predict_magnetospheric_substorm(
            cme_params.initial_velocity, -8.0, 5.0  # Estimated solar wind conditions
        )
        
        return {
            'cme_arrival': arrival_pred,
            'geoeffectiveness': geo_analysis,
            'solar_particle_event': sep_prediction,
            'substorm_forecast': substorm_prediction,
            'model_confidence': arrival_pred['confidence']
        }
    
    def _extract_ml_features(self, cme_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract ML features from CME data"""
        
        # Extract basic parameters
        features = {
            'velocity': 400,  # Default
            'angular_width': 30,
            'direction': 0,
            'latitude': 0,
            'source_location': 0
        }
        
        # Parse CME analyses if available
        analyses = cme_data.get('cmeAnalyses', [])
        if analyses:
            analysis = analyses[0]
            features.update({
                'velocity': float(analysis.get('speed', 400)),
                'angular_width': float(analysis.get('halfAngle', 15)) * 2,
                'direction': float(analysis.get('longitude', 0)),
                'latitude': float(analysis.get('latitude', 0))
            })
        
        # Parse source location
        source_location = cme_data.get('sourceLocation', '')
        if source_location:
            try:
                if 'W' in source_location:
                    long_str = source_location.split('W')[1]
                    features['source_location'] = -float(long_str)
                elif 'E' in source_location:
                    long_str = source_location.split('E')[1]
                    features['source_location'] = float(long_str)
            except Exception:
                features['source_location'] = 0
        
        return features
    
    def _combine_predictions(self, ensemble_pred: EnsemblePrediction) -> Dict[str, Any]:
        """Combine predictions from multiple models using intelligent weighting"""
        
        predictions = []
        weights = []
        confidences = []
        
        # Physics prediction
        if ensemble_pred.physics_prediction:
            phys_arrival = ensemble_pred.physics_prediction['cme_arrival']['transit_time_hours']
            phys_confidence = ensemble_pred.physics_prediction['cme_arrival']['confidence']
            
            predictions.append(phys_arrival)
            weights.append(self.default_weights['physics'] * phys_confidence)
            confidences.append(phys_confidence)
        
        # ML prediction
        if ensemble_pred.ml_prediction:
            ml_arrival = ensemble_pred.ml_prediction.prediction
            ml_confidence = ensemble_pred.ml_prediction.confidence
            
            predictions.append(ml_arrival)
            weights.append(self.default_weights['ml'] * ml_confidence)
            confidences.append(ml_confidence)
        
        # Neural prediction
        if ensemble_pred.neural_prediction and ensemble_pred.neural_prediction.get('status') == 'success':
            # Extract arrival time from neural prediction (might be in aurora_latitude or custom field)
            neural_data = ensemble_pred.neural_prediction.get('transformer', {})
            neural_arrival = neural_data.get('aurora_latitude', 48)  # Placeholder
            neural_confidence = 0.7  # Default neural confidence
            
            predictions.append(neural_arrival)
            weights.append(self.default_weights['neural'] * neural_confidence)
            confidences.append(neural_confidence)
        
        if not predictions:
            return {
                'status': 'error',
                'message': 'No valid predictions available',
                'fallback_prediction': 48.0
            }
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            ensemble_arrival = sum(p * w for p, w in zip(predictions, weights)) / total_weight
        else:
            ensemble_arrival = np.mean(predictions)
        
        # Ensemble confidence
        ensemble_confidence = min(1.0, np.mean(confidences) * (len(predictions) / 3))
        
        # Calculate prediction spread (uncertainty indicator)
        prediction_spread = np.std(predictions) if len(predictions) > 1 else 0
        
        return {
            'status': 'success',
            'ensemble_arrival_hours': max(6.0, ensemble_arrival),
            'ensemble_confidence': ensemble_confidence,
            'prediction_spread_hours': prediction_spread,
            'model_agreement': prediction_spread < 12,  # Good agreement if spread < 12 hours
            'individual_predictions': {
                'physics': predictions[0] if len(predictions) > 0 else None,
                'ml': predictions[1] if len(predictions) > 1 else None,
                'neural': predictions[2] if len(predictions) > 2 else None
            },
            'model_weights_used': {
                'physics': weights[0] / total_weight if total_weight > 0 and len(weights) > 0 else 0,
                'ml': weights[1] / total_weight if total_weight > 0 and len(weights) > 1 else 0,
                'neural': weights[2] / total_weight if total_weight > 0 and len(weights) > 2 else 0
            }
        }
    
    def _quantify_uncertainty(self, ensemble_pred: EnsemblePrediction) -> Dict[str, Any]:
        """Quantify prediction uncertainty using multiple methods"""
        
        uncertainties = {}
        
        # Model disagreement uncertainty
        if ensemble_pred.ensemble_result.get('prediction_spread_hours'):
            uncertainties['model_disagreement'] = ensemble_pred.ensemble_result['prediction_spread_hours']
        
        # Confidence-based uncertainty
        confidences = []
        if ensemble_pred.physics_prediction:
            confidences.append(ensemble_pred.physics_prediction['model_confidence'])
        if ensemble_pred.ml_prediction:
            confidences.append(ensemble_pred.ml_prediction.confidence)
        
        if confidences:
            avg_confidence = np.mean(confidences)
            uncertainties['confidence_based'] = (1 - avg_confidence) * 24  # Hours of uncertainty
        
        # Historical performance uncertainty
        performance = self.performance_tracker.calculate_model_performance('ensemble', days_back=30)
        if performance.get('status') == 'success':
            uncertainties['historical_error'] = performance.get('by_prediction_type', {}).get(
                'cme_arrival_hours', {}
            ).get('mean_absolute_error', 12)
        
        # Combined uncertainty estimate
        uncertainty_values = [v for v in uncertainties.values() if v > 0]
        if uncertainty_values:
            combined_uncertainty = np.sqrt(np.mean([u**2 for u in uncertainty_values]))
        else:
            combined_uncertainty = 12.0  # Default uncertainty
        
        return {
            'combined_uncertainty_hours': combined_uncertainty,
            'uncertainty_sources': uncertainties,
            'confidence_level': max(0.3, 1.0 - (combined_uncertainty / 48)),
            'uncertainty_category': self._categorize_uncertainty(combined_uncertainty)
        }
    
    def _categorize_uncertainty(self, uncertainty_hours: float) -> str:
        """Categorize uncertainty level"""
        if uncertainty_hours < 6:
            return 'very_low'
        elif uncertainty_hours < 12:
            return 'low'
        elif uncertainty_hours < 24:
            return 'moderate'
        elif uncertainty_hours < 48:
            return 'high'
        else:
            return 'very_high'
    
    def _update_model_weights(self) -> Dict[str, float]:
        """Update model weights based on recent performance"""
        
        # Get recent performance for each model type
        physics_perf = self.performance_tracker.calculate_model_performance('physics', days_back=30)
        ml_perf = self.performance_tracker.calculate_model_performance('ml_ensemble', days_back=30)
        neural_perf = self.performance_tracker.calculate_model_performance('neural', days_back=30)
        
        # Calculate performance scores (lower error = higher score)
        scores = {}
        
        if physics_perf.get('status') == 'success':
            physics_error = physics_perf.get('by_prediction_type', {}).get(
                'cme_arrival_hours', {}
            ).get('mean_absolute_error', 12)
            scores['physics'] = 1 / (1 + physics_error)
        else:
            scores['physics'] = self.default_weights['physics']
        
        if ml_perf.get('status') == 'success':
            ml_error = ml_perf.get('by_prediction_type', {}).get(
                'cme_arrival_hours', {}
            ).get('mean_absolute_error', 12)
            scores['ml'] = 1 / (1 + ml_error)
        else:
            scores['ml'] = self.default_weights['ml']
        
        if neural_perf.get('status') == 'success':
            neural_error = neural_perf.get('by_prediction_type', {}).get(
                'dst_prediction', {}
            ).get('mean_absolute_error', 20)
            scores['neural'] = 1 / (1 + neural_error / 10)  # Scale neural error
        else:
            scores['neural'] = self.default_weights['neural']
        
        # Normalize scores to weights
        total_score = sum(scores.values())
        if total_score > 0:
            weights = {k: v / total_score for k, v in scores.items()}
        else:
            weights = self.default_weights
        
        return weights
    
    def validate_ensemble_performance(self, validation_period_days: int = 90) -> Dict[str, Any]:
        """Validate ensemble performance over a specified period"""
        
        ensemble_perf = self.performance_tracker.calculate_model_performance(
            'ensemble', days_back=validation_period_days
        )
        
        if ensemble_perf.get('status') != 'success':
            return {
                'status': 'insufficient_data',
                'message': 'Not enough validation data available'
            }
        
        # Compare ensemble vs individual models
        physics_perf = self.performance_tracker.calculate_model_performance(
            'physics', days_back=validation_period_days
        )
        ml_perf = self.performance_tracker.calculate_model_performance(
            'ml_ensemble', days_back=validation_period_days
        )
        
        validation_result = {
            'status': 'success',
            'validation_period_days': validation_period_days,
            'ensemble_performance': ensemble_perf,
            'model_comparison': {
                'physics': physics_perf,
                'ml': ml_perf
            },
            'ensemble_improvement': {},
            'recommendations': []
        }
        
        # Calculate improvement over individual models
        if physics_perf.get('status') == 'success':
            ensemble_error = ensemble_perf['by_prediction_type'].get('cme_arrival_hours', {}).get('mean_absolute_error', 12)
            physics_error = physics_perf['by_prediction_type'].get('cme_arrival_hours', {}).get('mean_absolute_error', 12)
            
            improvement = (physics_error - ensemble_error) / physics_error * 100
            validation_result['ensemble_improvement']['vs_physics'] = improvement
        
        # Generate recommendations
        if ensemble_perf['overall_predictions'] < 20:
            validation_result['recommendations'].append(
                "Collect more validation data for robust performance assessment"
            )
        
        ensemble_accuracy = ensemble_perf['by_prediction_type'].get('cme_arrival_hours', {}).get('accuracy_within_20_percent', 0.7)
        if ensemble_accuracy < 0.8:
            validation_result['recommendations'].append(
                "Consider retraining models or adjusting ensemble weights"
            )
        
        return validation_result

# Convenience function for external use
def get_ensemble_forecast(cme_data: Dict[str, Any], 
                         solar_wind_sequence: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Get ensemble space weather forecast"""
    forecaster = EnsembleSpaceWeatherForecaster()
    ensemble_pred = forecaster.generate_ensemble_forecast(cme_data, solar_wind_sequence)
    
    return {
        'ensemble_result': ensemble_pred.ensemble_result,
        'uncertainty_quantification': ensemble_pred.uncertainty_quantification,
        'model_weights': ensemble_pred.model_weights,
        'individual_predictions': {
            'physics': ensemble_pred.physics_prediction,
            'ml': ensemble_pred.ml_prediction.__dict__ if ensemble_pred.ml_prediction else None,
            'neural': ensemble_pred.neural_prediction
        }
    }

if __name__ == "__main__":
    # Test ensemble forecasting system
    print("Testing Ensemble Space Weather Forecasting System...")
    
    forecaster = EnsembleSpaceWeatherForecaster()
    
    # Test data
    test_cme = {
        'activityID': 'TEST-CME-001',
        'startTime': '2024-09-27T12:00:00Z',
        'sourceLocation': 'N15W45',
        'cmeAnalyses': [{
            'speed': '650',
            'longitude': '-45',
            'latitude': '15',
            'halfAngle': '22.5'
        }]
    }
    
    # Generate test solar wind sequence
    test_sequence = np.random.randn(144, 8) * 50 + np.array([400, 5, 0, 0, -5, 100000, 2, 8])
    
    print("\n1. Testing ensemble forecast generation...")
    ensemble_result = get_ensemble_forecast(test_cme, test_sequence)
    print(f"   Ensemble prediction: {ensemble_result['ensemble_result']}")
    
    print("\n2. Testing uncertainty quantification...")
    uncertainty = ensemble_result['uncertainty_quantification']
    print(f"   Uncertainty: {uncertainty}")
    
    print("\n3. Testing performance validation...")
    validation = forecaster.validate_ensemble_performance(validation_period_days=30)
    print(f"   Validation result: {validation}")
    
    print("\nEnsemble forecasting system test completed!")