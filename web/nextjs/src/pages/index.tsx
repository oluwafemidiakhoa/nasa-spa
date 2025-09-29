// Main dashboard page for NASA Space Weather Forecaster

import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';

// Components
import Layout from '@/components/Layout';
import ForecastCard from '@/components/ForecastCard';
import AlertBanner from '@/components/AlertBanner';
import ConnectionStatus from '@/components/ConnectionStatus';
import StatsPanel from '@/components/StatsPanel';
import TimelineView from '@/components/TimelineView';
import MapView from '@/components/MapView';

// Hooks
import { useForecasts } from '@/hooks/useForecasts';
import { useWebSocket } from '@/hooks/useWebSocket';
import useSWR from 'swr';

// Utils
import { apiClient } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { Alert, WebSocketMessage } from '@/types';

export default function Dashboard() {
  const {
    currentForecast,
    isLoading: forecastLoading,
    error: forecastError,
    lastUpdated,
    source,
    refreshForecast,
    generateCustomForecast,
    isGenerating,
  } = useForecasts();

  // WebSocket for real-time updates
  const {
    isConnected: wsConnected,
    isConnecting: wsConnecting,
    error: wsError,
  } = useWebSocket(apiClient.getWebSocketURL(), {
    onMessage: (message: WebSocketMessage) => {
      console.log('WebSocket message:', message);
      
      if (message.type === 'new_forecast') {
        toast.success('New forecast available!');
        refreshForecast();
      } else if (message.type === 'new_alert') {
        toast.error(`New ${message.data.severity} alert: ${message.data.event_type}`);
        mutateAlerts(); // Refresh alerts
      }
    },
    onConnect: () => {
      toast.success('Connected to real-time updates');
    },
    onDisconnect: () => {
      toast.error('Lost connection to real-time updates');
    },
  });

  // Fetch active alerts
  const { data: alertsData, error: alertsError, mutate: mutateAlerts } = useSWR(
    'active-alerts',
    async () => {
      const response = await apiClient.getActiveAlerts();
      return response.success ? response.data : null;
    },
    {
      refreshInterval: 60 * 1000, // Refresh every minute
    }
  );

  const [selectedView, setSelectedView] = useState<'overview' | 'map' | 'timeline' | 'stats'>('overview');
  const [mapViewport, setMapViewport] = useState({
    longitude: -100,
    latitude: 40,
    zoom: 3,
  });

  // Handle custom forecast generation
  const handleGenerateCustomForecast = async () => {
    const success = await generateCustomForecast({
      days_back: 3,
      include_images: true,
      max_tokens: 2000,
    });

    if (success) {
      toast.success('Custom forecast generated successfully!');
    } else {
      toast.error('Failed to generate custom forecast');
    }
  };

  // Format last updated time
  const formatLastUpdated = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  };

  return (
    <>
      <Head>
        <title>NASA Space Weather Dashboard</title>
        <meta name="description" content="Real-time space weather forecasting dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Layout>
        <div className="min-h-screen bg-space-gradient">
          <Toaster position="top-right" />
          
          {/* Header */}
          <div className="border-b border-space-700 bg-space-900/50 backdrop-blur">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    NASA Space Weather Dashboard
                  </h1>
                  <p className="text-space-300 text-sm">
                    Real-time forecasting and monitoring system
                  </p>
                </div>
                
                <div className="flex items-center space-x-4">
                  <ConnectionStatus 
                    isConnected={wsConnected}
                    isConnecting={wsConnecting}
                    error={wsError}
                  />
                  
                  <button
                    onClick={handleGenerateCustomForecast}
                    disabled={isGenerating}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-space-600 hover:bg-space-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-space-500 disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"></circle>
                          <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating...
                      </>
                    ) : (
                      'Generate Forecast'
                    )}
                  </button>
                </div>
              </div>
              
              {/* Navigation */}
              <div className="flex space-x-8 -mb-px">
                {[
                  { key: 'overview', label: 'Overview', icon: '🌌' },
                  { key: 'map', label: 'Earth View', icon: '🌍' },
                  { key: 'timeline', label: 'Timeline', icon: '📊' },
                  { key: 'stats', label: 'Statistics', icon: '📈' },
                ].map(({ key, label, icon }) => (
                  <button
                    key={key}
                    onClick={() => setSelectedView(key as any)}
                    className={`${
                      selectedView === key
                        ? 'border-space-400 text-space-400'
                        : 'border-transparent text-space-300 hover:text-white hover:border-space-600'
                    } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                  >
                    <span className="mr-2">{icon}</span>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Alert Banner */}
          {alertsData?.alerts && alertsData.alerts.length > 0 && (
            <AlertBanner alerts={alertsData.alerts} />
          )}

          {/* Main Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Overview View */}
            {selectedView === 'overview' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                {/* Status Bar */}
                <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-medium text-white">Current Status</h2>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className="text-space-300">
                          Last Updated: {lastUpdated ? formatLastUpdated(lastUpdated) : 'Never'}
                        </span>
                        <span className="text-space-300">
                          Source: {source || 'Unknown'}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          forecastError ? 'bg-red-900 text-red-200' :
                          forecastLoading ? 'bg-yellow-900 text-yellow-200' :
                          'bg-green-900 text-green-200'
                        }`}>
                          {forecastError ? 'Error' : forecastLoading ? 'Loading' : 'Active'}
                        </span>
                      </div>
                    </div>
                    
                    <button
                      onClick={refreshForecast}
                      className="inline-flex items-center px-3 py-1 border border-space-600 text-sm font-medium rounded-md text-white hover:bg-space-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-space-500"
                    >
                      Refresh
                    </button>
                  </div>
                </div>

                {/* Forecasts Grid */}
                {forecastLoading ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="animate-pulse">
                        <div className="bg-space-700 rounded-lg h-64"></div>
                      </div>
                    ))}
                  </div>
                ) : forecastError ? (
                  <div className="text-center py-12">
                    <div className="text-red-400 text-lg mb-2">⚠️ Error Loading Forecasts</div>
                    <p className="text-space-300">{forecastError}</p>
                  </div>
                ) : currentForecast?.forecasts?.length ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {currentForecast.forecasts.map((forecast, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <ForecastCard forecast={forecast} />
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="text-space-300 text-lg mb-2">☀️ All Quiet</div>
                    <p className="text-space-400">No significant space weather events forecasted</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Map View */}
            {selectedView === 'map' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-96"
              >
                <MapView
                  viewport={mapViewport}
                  onViewportChange={setMapViewport}
                  layers={[]}
                  className="rounded-lg overflow-hidden border border-space-700"
                />
              </motion.div>
            )}

            {/* Timeline View */}
            {selectedView === 'timeline' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <TimelineView />
              </motion.div>
            )}

            {/* Stats View */}
            {selectedView === 'stats' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <StatsPanel />
              </motion.div>
            )}
          </div>
        </div>
      </Layout>
    </>
  );
}