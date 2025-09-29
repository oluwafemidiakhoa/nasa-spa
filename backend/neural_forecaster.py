"""
Neural Network Architecture for Space Weather Pattern Recognition
Advanced deep learning models for complex space weather pattern analysis
"""

import numpy as np
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import logging

# Try to import deep learning libraries
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, callbacks, optimizers
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import (
        LSTM, GRU, Dense, Dropout, BatchNormalization,
        Conv1D, MaxPooling1D, GlobalAveragePooling1D,
        Attention, MultiHeadAttention, LayerNormalization,
        Input, Concatenate, TimeDistributed
    )
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class SpaceWeatherTransformer:
    """Transformer architecture for space weather sequence modeling"""
    
    def __init__(self, sequence_length: int = 144, # 6 days of hourly data
                 num_features: int = 8,
                 d_model: int = 128,
                 num_heads: int = 8,
                 num_layers: int = 4,
                 dropout_rate: float = 0.1):
        
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for neural network models")
            
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.model = None
        self.scaler = None
        
    def build_model(self):
        """Build transformer model for space weather prediction"""
        
        # Input layer
        inputs = Input(shape=(self.sequence_length, self.num_features))
        
        # Positional encoding
        x = self._add_positional_encoding(inputs)
        
        # Transformer encoder layers
        for i in range(self.num_layers):
            x = self._transformer_encoder_layer(x, f"transformer_{i}")
        
        # Global pooling and dense layers
        x = GlobalAveragePooling1D()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        x = Dense(128, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        
        # Multiple outputs for different predictions
        dst_output = Dense(1, activation='linear', name='dst_prediction')(x)
        kp_output = Dense(1, activation='sigmoid', name='kp_prediction')(x)  # Kp scaled 0-1
        arrival_output = Dense(1, activation='relu', name='arrival_time')(x)
        probability_output = Dense(1, activation='sigmoid', name='event_probability')(x)
        
        # Create model
        self.model = Model(
            inputs=inputs,
            outputs=[dst_output, kp_output, arrival_output, probability_output]
        )
        
        # Compile with multiple loss functions
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss={
                'dst_prediction': 'mse',
                'kp_prediction': 'mse',
                'arrival_time': 'mse',
                'event_probability': 'binary_crossentropy'
            },
            loss_weights={
                'dst_prediction': 1.0,
                'kp_prediction': 1.0,
                'arrival_time': 2.0,  # Higher weight for arrival time
                'event_probability': 1.5
            },
            metrics=['mae']
        )
        
        return self.model
    
    def _add_positional_encoding(self, inputs):
        """Add positional encoding to input embeddings"""
        seq_len = self.sequence_length
        d_model = self.d_model
        
        # Project input to d_model dimensions
        x = Dense(d_model)(inputs)
        
        # Create positional encoding
        position = tf.range(seq_len, dtype=tf.float32)[:, tf.newaxis]
        div_term = tf.exp(tf.range(0, d_model, 2, dtype=tf.float32) * 
                         -(tf.math.log(10000.0) / d_model))
        
        pos_encoding = tf.zeros((seq_len, d_model))
        pos_encoding = tf.tensor_scatter_nd_update(
            pos_encoding,
            tf.stack([tf.range(seq_len), tf.range(0, d_model, 2)], axis=1),
            tf.sin(position * div_term)
        )
        pos_encoding = tf.tensor_scatter_nd_update(
            pos_encoding,
            tf.stack([tf.range(seq_len), tf.range(1, d_model, 2)], axis=1),
            tf.cos(position * div_term)
        )
        
        return x + pos_encoding
    
    def _transformer_encoder_layer(self, inputs, name_prefix):
        """Single transformer encoder layer"""
        
        # Multi-head attention
        attention_output = MultiHeadAttention(
            num_heads=self.num_heads,
            key_dim=self.d_model // self.num_heads,
            name=f"{name_prefix}_attention"
        )(inputs, inputs)
        
        attention_output = Dropout(self.dropout_rate)(attention_output)
        attention_output = LayerNormalization(name=f"{name_prefix}_norm1")(
            inputs + attention_output
        )
        
        # Feed-forward network
        ffn_output = Dense(self.d_model * 4, activation='relu', 
                          name=f"{name_prefix}_ffn1")(attention_output)
        ffn_output = Dropout(self.dropout_rate)(ffn_output)
        ffn_output = Dense(self.d_model, name=f"{name_prefix}_ffn2")(ffn_output)
        ffn_output = Dropout(self.dropout_rate)(ffn_output)
        
        return LayerNormalization(name=f"{name_prefix}_norm2")(
            attention_output + ffn_output
        )

class LSTMSpaceWeatherModel:
    """LSTM-based model for space weather sequence prediction"""
    
    def __init__(self, sequence_length: int = 72, # 3 days of hourly data
                 num_features: int = 8,
                 lstm_units: int = 128,
                 num_lstm_layers: int = 3,
                 dropout_rate: float = 0.2):
        
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for neural network models")
            
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.lstm_units = lstm_units
        self.num_lstm_layers = num_lstm_layers
        self.dropout_rate = dropout_rate
        self.model = None
        self.scaler = None
    
    def build_model(self):
        """Build LSTM model for space weather prediction"""
        
        model = Sequential()
        
        # Input layer
        model.add(Input(shape=(self.sequence_length, self.num_features)))
        
        # LSTM layers
        for i in range(self.num_lstm_layers):
            return_sequences = (i < self.num_lstm_layers - 1)
            model.add(LSTM(
                self.lstm_units,
                return_sequences=return_sequences,
                dropout=self.dropout_rate,
                recurrent_dropout=self.dropout_rate,
                name=f'lstm_{i+1}'
            ))
            model.add(BatchNormalization())
        
        # Dense layers
        model.add(Dense(256, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(128, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(64, activation='relu'))
        
        # Output layer (predicting next 24 hours of Dst values)
        model.add(Dense(24, activation='linear', name='dst_forecast'))
        
        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model

class CNNLSTMHybrid:
    """CNN-LSTM hybrid model for multi-scale pattern recognition"""
    
    def __init__(self, sequence_length: int = 168, # 1 week hourly data
                 num_features: int = 8):
        
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for neural network models")
            
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.model = None
        self.scaler = None
    
    def build_model(self):
        """Build CNN-LSTM hybrid model"""
        
        inputs = Input(shape=(self.sequence_length, self.num_features))
        
        # CNN layers for feature extraction
        x = Conv1D(filters=64, kernel_size=3, activation='relu', padding='same')(inputs)
        x = MaxPooling1D(pool_size=2)(x)
        x = Conv1D(filters=128, kernel_size=3, activation='relu', padding='same')(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Conv1D(filters=256, kernel_size=3, activation='relu', padding='same')(x)
        
        # LSTM layers for temporal modeling
        x = LSTM(128, return_sequences=True, dropout=0.2)(x)
        x = LSTM(64, dropout=0.2)(x)
        
        # Dense layers
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.3)(x)
        x = Dense(64, activation='relu')(x)
        
        # Multiple outputs
        geomag_intensity = Dense(1, activation='linear', name='geomag_intensity')(x)
        storm_probability = Dense(1, activation='sigmoid', name='storm_probability')(x)
        aurora_latitude = Dense(1, activation='linear', name='aurora_latitude')(x)
        
        self.model = Model(
            inputs=inputs,
            outputs=[geomag_intensity, storm_probability, aurora_latitude]
        )
        
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss={
                'geomag_intensity': 'mse',
                'storm_probability': 'binary_crossentropy',
                'aurora_latitude': 'mse'
            },
            metrics=['mae']
        )
        
        return self.model

class NeuralSpaceWeatherForecaster:
    """Main neural forecasting system coordinating multiple models"""
    
    def __init__(self, model_dir: str = "data/neural_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        if not TF_AVAILABLE:
            logger.warning("TensorFlow not available. Neural models disabled.")
            return
            
        # Initialize models
        self.transformer_model = None
        self.lstm_model = None
        self.hybrid_model = None
        
        # Data preprocessing
        self.scalers = {}
        
    def prepare_training_data(self, data_source: str = "historical") -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequential training data for neural networks"""
        
        if data_source == "historical":
            return self._prepare_historical_sequences()
        elif data_source == "realtime":
            return self._prepare_realtime_sequences()
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def _prepare_historical_sequences(self, sequence_length: int = 144) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences from historical space weather data"""
        
        # Connect to historical database
        from .ml_forecaster import HistoricalDataCollector
        collector = HistoricalDataCollector()
        
        # Load historical solar wind and geomagnetic data
        # This would typically come from OMNI database or similar
        
        # For now, generate synthetic sequential data for demonstration
        logger.info("Generating synthetic sequential training data...")
        
        num_sequences = 1000
        features_per_timestep = 8  # velocity, density, bx, by, bz, temperature, pressure, dynamic_pressure
        
        # Generate realistic space weather sequences
        X_sequences = []
        y_sequences = []
        
        for i in range(num_sequences):
            # Generate a sequence with some realistic patterns
            sequence = self._generate_realistic_sequence(sequence_length, features_per_timestep)
            
            # Generate corresponding targets (future Dst, Kp, etc.)
            targets = self._generate_sequence_targets(sequence)
            
            X_sequences.append(sequence)
            y_sequences.append(targets)
        
        X = np.array(X_sequences)
        y = np.array(y_sequences)
        
        logger.info(f"Prepared {X.shape[0]} sequences of length {X.shape[1]} with {X.shape[2]} features")
        
        return X, y
    
    def _generate_realistic_sequence(self, length: int, num_features: int) -> np.ndarray:
        """Generate realistic space weather data sequence"""
        
        # Base parameters for realistic solar wind
        base_velocity = 400
        base_density = 5
        base_temperature = 100000
        
        sequence = np.zeros((length, num_features))
        
        for t in range(length):
            # Add some periodic and random variations
            time_factor = t / length * 2 * np.pi
            
            # Solar wind velocity (300-800 km/s typical)
            velocity = base_velocity + 100 * np.sin(time_factor) + np.random.normal(0, 50)
            velocity = np.clip(velocity, 200, 1000)
            
            # Density (1-50 p/cm³ typical)
            density = base_density + 2 * np.sin(time_factor * 1.5) + np.random.normal(0, 2)
            density = np.clip(density, 0.5, 50)
            
            # Magnetic field components (-20 to +20 nT typical)
            bx = np.random.normal(0, 5)
            by = np.random.normal(0, 5)
            bz = np.random.normal(0, 5) - 2  # Slight southward bias
            
            # Temperature (10^4 to 10^6 K)
            temperature = base_temperature * (1 + 0.5 * np.sin(time_factor) + np.random.normal(0, 0.2))
            temperature = np.clip(temperature, 10000, 1000000)
            
            # Dynamic pressure
            dynamic_pressure = 1.67e-27 * density * 1e6 * (velocity * 1000) ** 2 * 1e9  # nPa
            
            sequence[t] = [
                velocity, density, bx, by, bz, temperature, 
                dynamic_pressure, np.sqrt(bx**2 + by**2 + bz**2)  # total B
            ]
        
        return sequence
    
    def _generate_sequence_targets(self, sequence: np.ndarray) -> Dict[str, float]:
        """Generate target values from sequence"""
        
        # Extract key parameters from the end of sequence
        final_values = sequence[-24:, :]  # Last 24 hours
        
        velocity = np.mean(final_values[:, 0])
        bz = np.mean(final_values[:, 4])
        density = np.mean(final_values[:, 1])
        
        # Estimate Dst index using Burton equation approximation
        dst_estimate = -4.4 * velocity**0.5 * (bz + 0.5) if bz < 0 else 0
        dst_estimate = np.clip(dst_estimate, -400, 50)
        
        # Estimate Kp index
        if abs(bz) > 10 and velocity > 600:
            kp_estimate = 7 + np.random.normal(0, 1)
        elif abs(bz) > 5 and velocity > 450:
            kp_estimate = 5 + np.random.normal(0, 1)
        else:
            kp_estimate = 3 + np.random.normal(0, 1)
        kp_estimate = np.clip(kp_estimate, 0, 9)
        
        # Aurora latitude (approximate)
        aurora_lat = 67 - kp_estimate * 2
        
        return {
            'dst': dst_estimate,
            'kp': kp_estimate / 9.0,  # Normalize to 0-1
            'aurora_latitude': aurora_lat,
            'storm_probability': 1.0 if dst_estimate < -50 else 0.0
        }
    
    def train_transformer_model(self, epochs: int = 50, batch_size: int = 32) -> Dict[str, Any]:
        """Train transformer model for space weather prediction"""
        
        if not TF_AVAILABLE:
            return {'status': 'error', 'message': 'TensorFlow not available'}
        
        logger.info("Training transformer model...")
        
        # Prepare data
        X, y_dict = self.prepare_training_data()
        
        # Convert targets to proper format
        y_dst = np.array([y['dst'] for y in y_dict])
        y_kp = np.array([y['kp'] for y in y_dict])
        y_aurora = np.array([y['aurora_latitude'] for y in y_dict])
        y_prob = np.array([y['storm_probability'] for y in y_dict])
        
        # Initialize and build transformer
        self.transformer_model = SpaceWeatherTransformer()
        model = self.transformer_model.build_model()
        
        # Scale input data
        if SKLEARN_AVAILABLE:
            scaler = StandardScaler()
            X_reshaped = X.reshape(-1, X.shape[-1])
            X_scaled = scaler.fit_transform(X_reshaped)
            X_scaled = X_scaled.reshape(X.shape)
            self.scalers['transformer'] = scaler
        else:
            X_scaled = X
        
        # Split data
        split_idx = int(0.8 * len(X_scaled))
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train = {
            'dst_prediction': y_dst[:split_idx],
            'kp_prediction': y_kp[:split_idx],
            'arrival_time': y_aurora[:split_idx],
            'event_probability': y_prob[:split_idx]
        }
        y_val = {
            'dst_prediction': y_dst[split_idx:],
            'kp_prediction': y_kp[split_idx:],
            'arrival_time': y_aurora[split_idx:],
            'event_probability': y_prob[split_idx:]
        }
        
        # Callbacks
        callbacks_list = [
            callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
            callbacks.ModelCheckpoint(
                str(self.model_dir / "transformer_model.h5"),
                save_best_only=True
            )
        ]
        
        # Train model
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=1
        )
        
        # Evaluate model
        val_loss = min(history.history['val_loss'])
        
        logger.info(f"Transformer training completed. Best validation loss: {val_loss:.4f}")
        
        return {
            'status': 'success',
            'model_type': 'transformer',
            'validation_loss': val_loss,
            'epochs_trained': len(history.history['loss']),
            'training_samples': len(X_train)
        }
    
    def predict_with_neural_ensemble(self, input_sequence: np.ndarray) -> Dict[str, Any]:
        """Make predictions using ensemble of neural models"""
        
        if not TF_AVAILABLE:
            return {'status': 'error', 'message': 'TensorFlow not available'}
        
        predictions = {}
        
        # Load models if not already loaded
        self._load_models_if_needed()
        
        try:
            # Preprocess input
            if 'transformer' in self.scalers:
                input_scaled = self.scalers['transformer'].transform(
                    input_sequence.reshape(-1, input_sequence.shape[-1])
                ).reshape(input_sequence.shape)
            else:
                input_scaled = input_sequence
            
            # Transformer predictions
            if self.transformer_model and self.transformer_model.model:
                transformer_pred = self.transformer_model.model.predict(
                    input_scaled.reshape(1, *input_scaled.shape), verbose=0
                )
                predictions['transformer'] = {
                    'dst': float(transformer_pred[0][0][0]),
                    'kp': float(transformer_pred[1][0][0] * 9),  # Denormalize Kp
                    'aurora_latitude': float(transformer_pred[2][0][0]),
                    'storm_probability': float(transformer_pred[3][0][0])
                }
            
            # LSTM predictions (if model exists)
            if self.lstm_model and self.lstm_model.model:
                lstm_input = input_scaled[-72:]  # LSTM uses shorter sequences
                lstm_pred = self.lstm_model.model.predict(
                    lstm_input.reshape(1, *lstm_input.shape), verbose=0
                )
                predictions['lstm'] = {
                    'dst_forecast_24h': lstm_pred[0].tolist()
                }
            
            # Ensemble averaging
            if len(predictions) > 1:
                predictions['ensemble'] = self._compute_ensemble_average(predictions)
            
            predictions['status'] = 'success'
            predictions['timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Neural prediction failed: {e}")
            predictions = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        return predictions
    
    def _load_models_if_needed(self):
        """Load pre-trained models if available"""
        
        transformer_path = self.model_dir / "transformer_model.h5"
        if transformer_path.exists() and not self.transformer_model:
            try:
                self.transformer_model = SpaceWeatherTransformer()
                self.transformer_model.model = keras.models.load_model(str(transformer_path))
                logger.info("Loaded transformer model")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
    
    def _compute_ensemble_average(self, predictions: Dict[str, Dict]) -> Dict[str, float]:
        """Compute ensemble average of predictions"""
        
        ensemble = {}
        
        # Average DST predictions
        dst_values = [pred.get('dst', 0) for pred in predictions.values() 
                     if isinstance(pred, dict) and 'dst' in pred]
        if dst_values:
            ensemble['dst'] = np.mean(dst_values)
        
        # Average Kp predictions
        kp_values = [pred.get('kp', 3) for pred in predictions.values() 
                    if isinstance(pred, dict) and 'kp' in pred]
        if kp_values:
            ensemble['kp'] = np.mean(kp_values)
        
        # Average storm probability
        prob_values = [pred.get('storm_probability', 0.5) for pred in predictions.values() 
                      if isinstance(pred, dict) and 'storm_probability' in pred]
        if prob_values:
            ensemble['storm_probability'] = np.mean(prob_values)
            
        ensemble['confidence'] = min(len(predictions) / 3, 1.0)  # Higher confidence with more models
        
        return ensemble

# Convenience function for external use
def get_neural_enhanced_forecast(solar_wind_sequence: np.ndarray) -> Dict[str, Any]:
    """Get neural network enhanced space weather forecast"""
    forecaster = NeuralSpaceWeatherForecaster()
    return forecaster.predict_with_neural_ensemble(solar_wind_sequence)

if __name__ == "__main__":
    # Test neural forecasting system
    
    if not TF_AVAILABLE:
        print("TensorFlow not available. Install tensorflow for neural network functionality.")
        exit(1)
    
    print("Testing Neural Space Weather Forecasting System...")
    
    forecaster = NeuralSpaceWeatherForecaster()
    
    # Test data preparation
    print("\n1. Testing data preparation...")
    X, y = forecaster.prepare_training_data()
    print(f"   Generated {X.shape[0]} sequences with shape {X.shape[1:]} each")
    
    # Test transformer training
    print("\n2. Testing transformer model training...")
    train_result = forecaster.train_transformer_model(epochs=5, batch_size=16)  # Quick test
    print(f"   Training result: {train_result}")
    
    # Test prediction
    print("\n3. Testing neural prediction...")
    test_sequence = X[0]  # Use first training example
    predictions = forecaster.predict_with_neural_ensemble(test_sequence)
    print(f"   Predictions: {predictions}")
    
    print("\nNeural forecasting system test completed!")