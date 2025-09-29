// Forecast card component displaying individual space weather forecasts

import React from 'react';
import { motion } from 'framer-motion';
import { format, formatDistanceToNow } from 'date-fns';
import { Forecast } from '@/types';

interface ForecastCardProps {
  forecast: Forecast;
  className?: string;
}

export default function ForecastCard({ forecast, className = '' }: ForecastCardProps) {
  const getSeverityColor = (confidence: number) => {
    if (confidence >= 0.8) return 'border-red-500 bg-red-900/20';
    if (confidence >= 0.6) return 'border-orange-500 bg-orange-900/20';
    if (confidence >= 0.4) return 'border-yellow-500 bg-yellow-900/20';
    return 'border-blue-500 bg-blue-900/20';
  };

  const getEventIcon = (event: string) => {
    switch (event) {
      case 'CME': return '🌀';
      case 'FLARE': return '☀️';
      case 'SEP': return '⚡';
      case 'GEO_STORM': return '🌍';
      default: return '🌌';
    }
  };

  const getEventTitle = (event: string) => {
    switch (event) {
      case 'CME': return 'Coronal Mass Ejection';
      case 'FLARE': return 'Solar Flare';
      case 'SEP': return 'Solar Energetic Particles';
      case 'GEO_STORM': return 'Geomagnetic Storm';
      default: return event;
    }
  };

  const formatArrivalWindow = (window: [string, string]) => {
    try {
      const start = new Date(window[0]);
      const end = new Date(window[1]);
      
      const startStr = format(start, 'MMM dd, HH:mm');
      const endStr = format(end, 'HH:mm zzz');
      
      return `${startStr} - ${endStr}`;
    } catch {
      return `${window[0]} - ${window[1]}`;
    }
  };

  const formatImpacts = (impacts: string[]) => {
    const impactDescriptions: Record<string, string> = {
      'aurora_lowlat': 'Aurora at low latitudes',
      'aurora_midlat': 'Aurora at mid-latitudes',
      'aurora_highlat': 'Aurora at high latitudes',
      'HF_comms': 'HF radio disruption',
      'GNSS_jitter': 'GPS accuracy issues',
      'satellite_ops': 'Satellite operations',
      'power_grid': 'Power grid effects',
    };

    return impacts.map(impact => 
      impactDescriptions[impact] || impact.replace('_', ' ')
    );
  };

  const confidencePercentage = Math.round(forecast.confidence * 100);

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`bg-space-800/50 backdrop-blur border-2 ${getSeverityColor(forecast.confidence)} rounded-lg p-6 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getEventIcon(forecast.event)}</span>
          <div>
            <h3 className="text-lg font-semibold text-white">
              {getEventTitle(forecast.event)}
            </h3>
            <p className="text-space-300 text-sm">
              Solar Event: {format(new Date(forecast.solar_timestamp), 'MMM dd, HH:mm zzz')}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className={`text-2xl font-bold ${
            confidencePercentage >= 80 ? 'text-red-400' :
            confidencePercentage >= 60 ? 'text-orange-400' :
            confidencePercentage >= 40 ? 'text-yellow-400' :
            'text-blue-400'
          }`}>
            {confidencePercentage}%
          </div>
          <p className="text-space-400 text-xs">Confidence</p>
        </div>
      </div>

      {/* Earth Impact Window */}
      <div className="bg-space-700/30 rounded-md p-3 mb-4">
        <h4 className="text-white font-medium mb-1">Earth Impact Window</h4>
        <p className="text-space-200 text-sm">
          {formatArrivalWindow(forecast.predicted_arrival_window_utc)}
        </p>
        <p className="text-space-400 text-xs mt-1">
          Arrival in {formatDistanceToNow(new Date(forecast.predicted_arrival_window_utc[0]))}
        </p>
      </div>

      {/* Risk Summary */}
      <div className="mb-4">
        <h4 className="text-white font-medium mb-2">Risk Summary</h4>
        <p className="text-space-200 text-sm leading-relaxed">
          {forecast.risk_summary}
        </p>
      </div>

      {/* Expected Impacts */}
      <div className="mb-4">
        <h4 className="text-white font-medium mb-2">Expected Impacts</h4>
        <div className="flex flex-wrap gap-2">
          {formatImpacts(forecast.impacts).map((impact, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-space-600/50 text-space-200 border border-space-500"
            >
              {impact}
            </span>
          ))}
        </div>
      </div>

      {/* Evidence */}
      <div className="border-t border-space-600 pt-3">
        <details className="group">
          <summary className="cursor-pointer text-space-300 text-sm hover:text-white transition-colors">
            <span className="inline-block w-4 h-4 mr-1 group-open:rotate-90 transition-transform">▶</span>
            Evidence & Sources
          </summary>
          <div className="mt-2 space-y-2 text-xs text-space-300">
            {forecast.evidence.donki_ids.length > 0 && (
              <div>
                <span className="font-medium text-space-200">DONKI IDs:</span>
                <div className="mt-1">
                  {forecast.evidence.donki_ids.map((id, index) => (
                    <code key={index} className="block bg-space-700/50 px-2 py-1 rounded font-mono">
                      {id}
                    </code>
                  ))}
                </div>
              </div>
            )}
            
            {forecast.evidence.epic_frames.length > 0 && (
              <div>
                <span className="font-medium text-space-200">EPIC Frames:</span>
                <div className="mt-1 space-y-1">
                  {forecast.evidence.epic_frames.slice(0, 3).map((frame, index) => (
                    <code key={index} className="block bg-space-700/50 px-2 py-1 rounded font-mono">
                      {frame}
                    </code>
                  ))}
                </div>
              </div>
            )}
            
            {forecast.evidence.gibs_layers.length > 0 && (
              <div>
                <span className="font-medium text-space-200">GIBS Layers:</span>
                <div className="mt-1">
                  {forecast.evidence.gibs_layers.map((layer, index) => (
                    <span key={index} className="inline-block bg-space-700/50 px-2 py-1 rounded mr-1">
                      {layer}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </details>
      </div>
    </motion.div>
  );
}