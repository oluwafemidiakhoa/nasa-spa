import React, { useState, useEffect } from 'react';
import Head from 'next/head';

interface Forecast {
  id: string;
  title: string;
  description: string;
  confidence: number;
  generated_at: string;
  source: string;
}

interface ForecastData {
  forecast: Forecast;
  generated_at: string;
  source: string;
}

const SimplePage: React.FC = () => {
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

  const fetchForecast = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/forecasts/current`);
      const result = await response.json();
      
      if (result.success) {
        setForecast(result.data);
      } else {
        setError('Failed to fetch forecast');
      }
    } catch (err) {
      setError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const generateNewForecast = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/forecasts/generate`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.success) {
        setForecast(result.data);
      } else {
        setError('Failed to generate forecast');
      }
    } catch (err) {
      setError(`Connection error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  return (
    <>
      <Head>
        <title>NASA Space Weather Forecaster</title>
        <meta name="description" content="Simple NASA Space Weather Dashboard" />
      </Head>
      
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
        color: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px' }}>
          
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <h1 style={{ fontSize: '3rem', margin: '0 0 10px 0', fontWeight: 'bold' }}>
              🛰️ NASA Space Weather
            </h1>
            <p style={{ fontSize: '1.2rem', opacity: 0.8, margin: 0 }}>
              Real-time space weather forecasting system
            </p>
          </div>

          {/* API Status */}
          <div style={{ 
            background: 'rgba(255,255,255,0.1)', 
            padding: '20px', 
            borderRadius: '10px',
            marginBottom: '30px',
            textAlign: 'center'
          }}>
            <p style={{ margin: '0 0 10px 0', fontSize: '1.1rem' }}>
              🔗 API Connection: {API_BASE}
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button 
                onClick={fetchForecast}
                disabled={loading}
                style={{
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '1rem'
                }}
              >
                {loading ? '⏳ Loading...' : '🔄 Refresh'}
              </button>
              
              <button 
                onClick={generateNewForecast}
                disabled={loading}
                style={{
                  background: '#2196F3',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '1rem'
                }}
              >
                {loading ? '⏳ Generating...' : '✨ Generate New'}
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div style={{ 
              background: '#f44336', 
              padding: '20px', 
              borderRadius: '10px',
              marginBottom: '30px',
              textAlign: 'center'
            }}>
              <h3 style={{ margin: '0 0 10px 0' }}>❌ Error</h3>
              <p style={{ margin: 0 }}>{error}</p>
            </div>
          )}

          {/* Forecast Display */}
          {forecast && (
            <div style={{ 
              background: 'rgba(255,255,255,0.1)', 
              padding: '30px', 
              borderRadius: '15px',
              marginBottom: '30px'
            }}>
              <h2 style={{ 
                margin: '0 0 20px 0', 
                fontSize: '2rem',
                textAlign: 'center'
              }}>
                {forecast.forecast.title}
              </h2>
              
              <p style={{ 
                fontSize: '1.2rem', 
                lineHeight: '1.6',
                marginBottom: '20px',
                textAlign: 'center'
              }}>
                {forecast.forecast.description}
              </p>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '20px',
                marginTop: '20px'
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '5px' }}>
                    {Math.round(forecast.forecast.confidence * 100)}%
                  </div>
                  <div style={{ opacity: 0.8 }}>Confidence</div>
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', marginBottom: '5px' }}>
                    {forecast.source}
                  </div>
                  <div style={{ opacity: 0.8 }}>Data Source</div>
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1rem', marginBottom: '5px' }}>
                    {new Date(forecast.generated_at).toLocaleString()}
                  </div>
                  <div style={{ opacity: 0.8 }}>Generated</div>
                </div>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div style={{ 
            background: 'rgba(255,255,255,0.05)', 
            padding: '20px', 
            borderRadius: '10px',
            textAlign: 'center',
            fontSize: '0.9rem',
            opacity: 0.8
          }}>
            <p style={{ margin: '0 0 10px 0' }}>
              This system monitors NASA's Space Weather Database and generates forecasts
            </p>
            <p style={{ margin: 0 }}>
              Data sources: NASA DONKI (CME, Solar Flares) • Updates every few minutes
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default SimplePage;