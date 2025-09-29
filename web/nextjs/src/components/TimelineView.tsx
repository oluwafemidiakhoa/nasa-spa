// Timeline view component for historical space weather events

import React from 'react';
import { useForecastHistory } from '@/hooks/useForecasts';

export default function TimelineView() {
  const { forecasts, isLoading, error } = useForecastHistory();

  if (isLoading) {
    return (
      <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-space-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
        <h3 className="text-white font-semibold mb-4">Forecast Timeline</h3>
        <div className="text-red-400">Error loading timeline: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
      <h3 className="text-white font-semibold mb-4">Recent Forecast History</h3>
      
      {forecasts.length === 0 ? (
        <div className="text-space-400">No forecast history available</div>
      ) : (
        <div className="space-y-3">
          {forecasts.slice(0, 10).map((forecast, index) => (
            <div key={forecast.id || index} className="border-l-2 border-space-600 pl-4 py-2">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-white font-medium">
                    {forecast.forecast.forecasts?.length || 0} forecasts generated
                  </div>
                  <div className="text-space-300 text-sm">
                    {new Date(forecast.created_at).toLocaleString()}
                  </div>
                </div>
                {forecast.accuracy_score && (
                  <div className="text-green-400 text-sm font-medium">
                    {Math.round(forecast.accuracy_score * 100)}% accuracy
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}