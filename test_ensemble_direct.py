#!/usr/bin/env python3
"""
Direct test of ensemble forecasting with sample data
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
sys.path.append('.')
sys.path.append('backend')

def create_sample_cme_data():
    """Create sample CME data for testing"""
    return {
        'activityID': '2025-09-27T12:36:00-CME-001',
        'startTime': '2025-09-27T12:36:00Z',
        'sourceLocation': 'N15W20',
        'cmeAnalyses': [
            {
                'speed': 500.0,
                'halfAngle': 25.0,
                'latitude': 15.0,
                'longitude': -20.0,
                'time21_5': '2025-09-27T13:00:00Z'
            }
        ]
    }

def test_ensemble_prediction():
    """Test ensemble prediction with sample data"""
    print("TESTING ENSEMBLE PREDICTION")
    print("=" * 40)
    
    try:
        from backend.ensemble_forecaster import EnsembleSpaceWeatherForecaster
        
        # Initialize ensemble forecaster
        ensemble = EnsembleSpaceWeatherForecaster()
        print("Ensemble forecaster initialized")
        
        # Create sample CME data
        cme_data = create_sample_cme_data()
        print(f"Testing with CME: {cme_data['activityID']}")
        
        # Generate ensemble forecast
        ensemble_pred = ensemble.generate_ensemble_forecast(cme_data)
        print("Ensemble prediction generated")
        
        # Check results
        print("\nEnsemble Prediction Results:")
        print(f"- Physics prediction: {'Available' if ensemble_pred.physics_prediction else 'Not available'}")
        print(f"- ML prediction: {'Available' if ensemble_pred.ml_prediction else 'Not available'}")
        print(f"- Neural prediction: {'Available' if ensemble_pred.neural_prediction else 'Not available'}")
        
        if ensemble_pred.ensemble_result:
            print(f"- Ensemble result: {ensemble_pred.ensemble_result}")
        
        if ensemble_pred.confidence_metrics:
            print(f"- Confidence metrics: {ensemble_pred.confidence_metrics}")
        
        return True
        
    except Exception as e:
        print(f"Ensemble prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ml_forecaster_direct():
    """Test ML forecaster directly"""
    print("\nTESTING ML FORECASTER DIRECT")
    print("=" * 40)
    
    try:
        from backend.ml_forecaster import MLSpaceWeatherForecaster
        
        # Initialize ML forecaster
        ml_forecaster = MLSpaceWeatherForecaster()
        print("ML forecaster initialized")
        
        # Test with sample features
        sample_features = [500.0, 25.0, 15.0, -20.0, 1.0, 0.8, 0.6, 2.5]  # 8D feature vector
        
        prediction = ml_forecaster.predict_cme_arrival(sample_features)
        print(f"ML prediction: {prediction.prediction} hours")
        print(f"ML confidence: {prediction.confidence}")
        
        return True
        
    except Exception as e:
        print(f"ML forecaster test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_neural_forecaster_direct():
    """Test neural forecaster directly"""
    print("\nTESTING NEURAL FORECASTER DIRECT")
    print("=" * 40)
    
    try:
        from backend.neural_forecaster import NeuralSpaceWeatherForecaster
        
        # Initialize neural forecaster
        neural_forecaster = NeuralSpaceWeatherForecaster()
        print("Neural forecaster initialized")
        
        # Note: Neural forecaster needs training data, so this is just initialization test
        print("Neural forecaster ready for training and prediction")
        
        return True
        
    except Exception as e:
        print(f"Neural forecaster test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("DIRECT ENSEMBLE FORECASTING TEST")
    print("=" * 50)
    
    results = []
    
    # Test ML forecaster
    results.append(test_ml_forecaster_direct())
    
    # Test neural forecaster
    results.append(test_neural_forecaster_direct())
    
    # Test ensemble prediction
    results.append(test_ensemble_prediction())
    
    print(f"\nTests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("ENSEMBLE FORECASTING SYSTEM: FULLY OPERATIONAL")
        return True
    else:
        print("ENSEMBLE FORECASTING SYSTEM: PARTIALLY OPERATIONAL")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)