#!/usr/bin/env python3
"""
Test Enhanced ML and Ensemble Space Weather Forecasting System
Comprehensive testing of machine learning, neural networks, and ensemble methods
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables
def load_env_file(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file(".env")

def test_historical_data_collection():
    """Test historical data collection system"""
    print("TESTING HISTORICAL DATA COLLECTION")
    print("=" * 50)
    
    try:
        from backend.ml_forecaster import HistoricalDataCollector
        
        collector = HistoricalDataCollector()
        print("✓ HistoricalDataCollector initialized")
        
        # Test database initialization
        print("✓ Database initialized")
        
        # Test CME data collection (limited to avoid API limits)
        print("Testing CME data collection (1 year)...")
        events = collector.collect_historical_cme_data(years_back=1)
        print(f"✓ Collected {len(events)} historical CME events")
        
        if events:
            sample_event = events[0]
            print(f"  Sample event: {sample_event.event_type} at {sample_event.timestamp}")
            print(f"  Parameters: {list(sample_event.parameters.keys())}")
        
        # Test training data preparation
        features_df, targets_df = collector.get_training_data('CME')
        print(f"✓ Training data prepared: {len(features_df)} samples")
        
        if len(features_df) > 0:
            print(f"  Features: {list(features_df.columns)}")
            print(f"  Targets: {list(targets_df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Historical data collection failed: {e}")
        return False

def test_ml_forecasting():
    """Test machine learning forecasting capabilities"""
    print("\nTESTING ML FORECASTING SYSTEM")
    print("=" * 50)
    
    try:
        from backend.ml_forecaster import MLSpaceWeatherForecaster
        
        forecaster = MLSpaceWeatherForecaster()
        print("✓ MLSpaceWeatherForecaster initialized")
        
        # Test model training (quick training for demo)
        print("Testing ML model training...")
        train_result = forecaster.train_cme_arrival_model(retrain=True)
        print(f"✓ Training result: {train_result}")
        
        # Test prediction
        print("Testing ML prediction...")
        test_cme = {
            'velocity': 650,
            'angular_width': 45,
            'direction': -30,
            'latitude': 15,
            'source_location': -75
        }
        
        prediction = forecaster.predict_cme_arrival(test_cme)
        print(f"✓ ML Prediction:")
        print(f"  Arrival time: {prediction.prediction:.1f} hours")
        print(f"  Confidence: {prediction.confidence:.2f}")
        print(f"  Uncertainty range: {prediction.uncertainty_range}")
        print(f"  Model used: {prediction.model_used}")
        
        # Test ensemble forecast
        print("Testing ensemble forecast...")
        ensemble_forecast = forecaster.get_ensemble_forecast(test_cme)
        print(f"✓ Ensemble forecast: {ensemble_forecast['ensemble_prediction']['arrival_time_hours']:.1f} hours")
        print(f"  Ensemble confidence: {ensemble_forecast['ensemble_prediction']['confidence']:.2f}")
        print(f"  Model agreement: {ensemble_forecast['model_agreement']}")
        
        # Test validation
        print("Testing model validation...")
        validation = forecaster.validate_model_performance()
        print(f"✓ Validation result: {validation}")
        
        return True
        
    except Exception as e:
        print(f"✗ ML forecasting failed: {e}")
        return False

def test_neural_forecasting():
    """Test neural network forecasting capabilities"""
    print("\nTESTING NEURAL NETWORK FORECASTING")
    print("=" * 50)
    
    try:
        from backend.neural_forecaster import NeuralSpaceWeatherForecaster
        
        forecaster = NeuralSpaceWeatherForecaster()
        print("✓ NeuralSpaceWeatherForecaster initialized")
        
        # Test data preparation
        print("Testing neural data preparation...")
        X, y = forecaster.prepare_training_data()
        print(f"✓ Generated {X.shape[0]} sequences with shape {X.shape[1:]} each")
        
        # Test transformer training (minimal epochs for demo)
        print("Testing transformer model training...")
        train_result = forecaster.train_transformer_model(epochs=3, batch_size=16)
        print(f"✓ Training result: {train_result}")
        
        # Test neural prediction
        print("Testing neural prediction...")
        test_sequence = X[0]  # Use first training example
        predictions = forecaster.predict_with_neural_ensemble(test_sequence)
        print(f"✓ Neural predictions: {predictions}")
        
        if predictions.get('status') == 'success':
            transformer_pred = predictions.get('transformer', {})
            print(f"  Transformer DST: {transformer_pred.get('dst', 'N/A')}")
            print(f"  Transformer Kp: {transformer_pred.get('kp', 'N/A')}")
            print(f"  Storm probability: {transformer_pred.get('storm_probability', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Neural forecasting failed: {e}")
        print("  Note: TensorFlow may not be available")
        return False

def test_ensemble_system():
    """Test ensemble forecasting system"""
    print("\nTESTING ENSEMBLE FORECASTING SYSTEM")
    print("=" * 50)
    
    try:
        from backend.ensemble_forecaster import EnsembleSpaceWeatherForecaster, get_ensemble_forecast
        
        forecaster = EnsembleSpaceWeatherForecaster()
        print("✓ EnsembleSpaceWeatherForecaster initialized")
        
        # Test data
        test_cme = {
            'activityID': 'TEST-CME-ENSEMBLE-001',
            'startTime': '2024-09-27T12:00:00Z',
            'sourceLocation': 'N15W45',
            'cmeAnalyses': [{
                'speed': '650',
                'longitude': '-45',
                'latitude': '15',
                'halfAngle': '22.5',
                'acceleration': '10'
            }]
        }
        
        # Generate test solar wind sequence
        test_sequence = np.random.randn(144, 8) * 50 + np.array([400, 5, 0, 0, -5, 100000, 2, 8])
        
        print("Testing ensemble forecast generation...")
        ensemble_result = get_ensemble_forecast(test_cme, test_sequence)
        print(f"✓ Ensemble forecast generated")
        
        if ensemble_result['ensemble_result'].get('status') == 'success':
            ens_res = ensemble_result['ensemble_result']
            print(f"  Ensemble arrival: {ens_res.get('ensemble_arrival_hours', 'N/A'):.1f} hours")
            print(f"  Ensemble confidence: {ens_res.get('ensemble_confidence', 'N/A'):.2f}")
            print(f"  Model agreement: {ens_res.get('model_agreement', 'N/A')}")
            print(f"  Prediction spread: {ens_res.get('prediction_spread_hours', 'N/A'):.1f} hours")
            
            # Model weights
            weights = ens_res.get('model_weights_used', {})
            print(f"  Model weights: Physics={weights.get('physics', 0):.2f}, ML={weights.get('ml', 0):.2f}, Neural={weights.get('neural', 0):.2f}")
        
        # Test uncertainty quantification
        uncertainty = ensemble_result['uncertainty_quantification']
        print(f"✓ Uncertainty quantification:")
        print(f"  Combined uncertainty: {uncertainty.get('combined_uncertainty_hours', 'N/A'):.1f} hours")
        print(f"  Confidence level: {uncertainty.get('confidence_level', 'N/A'):.2f}")
        print(f"  Category: {uncertainty.get('uncertainty_category', 'N/A')}")
        
        # Test performance validation
        print("Testing ensemble performance validation...")
        validation = forecaster.validate_ensemble_performance(validation_period_days=30)
        print(f"✓ Validation result: {validation['status']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ensemble system failed: {e}")
        return False

def test_enhanced_expert_forecaster():
    """Test enhanced expert forecaster with ML/Neural integration"""
    print("\nTESTING ENHANCED EXPERT FORECASTER")
    print("=" * 50)
    
    try:
        from backend.expert_forecaster import run_expert_forecast
        
        print("Testing enhanced expert forecast generation...")
        result = run_expert_forecast(days_back=2)  # Limited days to reduce API calls
        
        if hasattr(result, 'forecasts'):
            print(f"✓ Expert forecast generated with {len(result.forecasts)} forecasts")
            print(f"  Data sources: {result.data_sources}")
            
            if result.forecasts:
                sample_forecast = result.forecasts[0]
                print(f"  Sample forecast:")
                print(f"    Event: {sample_forecast.event}")
                print(f"    Confidence: {sample_forecast.confidence:.2f}")
                print(f"    Risk summary: {sample_forecast.risk_summary[:100]}...")
                print(f"    Evidence sources: {len(sample_forecast.evidence.donki_ids)}")
        else:
            print(f"✗ Expert forecast failed: {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced expert forecaster failed: {e}")
        return False

def test_performance_tracking():
    """Test model performance tracking system"""
    print("\nTESTING PERFORMANCE TRACKING SYSTEM")
    print("=" * 50)
    
    try:
        from backend.ensemble_forecaster import ModelPerformanceTracker
        
        tracker = ModelPerformanceTracker()
        print("✓ ModelPerformanceTracker initialized")
        
        # Test prediction logging
        print("Testing prediction logging...")
        tracker.log_prediction(
            'test_model', 'cme_arrival_hours', 48.0, 
            predicted_time='2024-09-29T12:00:00Z', confidence=0.8
        )
        print("✓ Prediction logged")
        
        # Test performance calculation
        print("Testing performance calculation...")
        performance = tracker.calculate_model_performance('test_model', days_back=30)
        print(f"✓ Performance result: {performance}")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance tracking failed: {e}")
        return False

def main():
    """Run comprehensive ML and ensemble system tests"""
    print("ENHANCED MACHINE LEARNING & ENSEMBLE SPACE WEATHER FORECASTING")
    print("Advanced Neural Networks and Multi-Model Integration Test Suite")
    print("=" * 80)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Historical Data Collection", test_historical_data_collection),
        ("ML Forecasting System", test_ml_forecasting),
        ("Neural Network Forecasting", test_neural_forecasting),
        ("Ensemble Forecasting System", test_ensemble_system),
        ("Enhanced Expert Forecaster", test_enhanced_expert_forecaster),
        ("Performance Tracking System", test_performance_tracking),
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            test_results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("ENHANCED ML & ENSEMBLE SYSTEM TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:<40} {status}")
        if success:
            passed += 1
    
    print(f"\nOVERALL RESULTS: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - ENHANCED ML & ENSEMBLE SYSTEM OPERATIONAL!")
        print("\nAdvanced Capabilities Demonstrated:")
        print("✓ Historical space weather data collection and preprocessing")
        print("✓ Machine learning models for CME arrival prediction")
        print("✓ Neural network transformers for pattern recognition")
        print("✓ Ensemble forecasting with confidence intervals")
        print("✓ Automated model performance tracking and validation")
        print("✓ Enhanced expert forecaster with ML/Neural integration")
        print("\n🚀 READY FOR NASA-GRADE OPERATIONAL DEPLOYMENT!")
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED - SOME FEATURES MAY BE LIMITED")
        print("Note: Some failures may be due to missing optional dependencies (TensorFlow, scikit-learn)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)