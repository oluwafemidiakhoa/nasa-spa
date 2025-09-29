// Statistics panel component

import React from 'react';
import useSWR from 'swr';
import { apiClient } from '@/lib/api';

export default function StatsPanel() {
  const { data: statsData, error, isLoading } = useSWR(
    'accuracy-stats',
    async () => {
      const response = await apiClient.getAccuracyStats();
      return response.success ? response.data : null;
    }
  );

  if (isLoading) {
    return (
      <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-space-700 rounded w-1/4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-space-700 rounded w-1/2"></div>
            <div className="h-3 bg-space-700 rounded w-1/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !statsData) {
    return (
      <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
        <h3 className="text-white font-semibold mb-4">Forecast Accuracy Statistics</h3>
        <div className="text-space-400">Unable to load statistics</div>
      </div>
    );
  }

  return (
    <div className="bg-space-800/50 backdrop-blur rounded-lg p-6 border border-space-700">
      <h3 className="text-white font-semibold mb-4">Forecast Accuracy Statistics</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-space-700/30 rounded-md p-4">
          <div className="text-2xl font-bold text-green-400">
            {Math.round(statsData.average_accuracy * 100)}%
          </div>
          <div className="text-space-300 text-sm">Average Accuracy</div>
        </div>
        
        <div className="bg-space-700/30 rounded-md p-4">
          <div className="text-2xl font-bold text-blue-400">{statsData.total_forecasts}</div>
          <div className="text-space-300 text-sm">Total Forecasts</div>
        </div>
        
        <div className="bg-space-700/30 rounded-md p-4">
          <div className="text-2xl font-bold text-purple-400">{statsData.evaluated_forecasts}</div>
          <div className="text-space-300 text-sm">Evaluated Forecasts</div>
        </div>
      </div>
      
      {Object.keys(statsData.accuracy_by_event_type).length > 0 && (
        <div className="mt-6">
          <h4 className="text-white font-medium mb-3">Accuracy by Event Type</h4>
          <div className="space-y-2">
            {Object.entries(statsData.accuracy_by_event_type).map(([eventType, accuracy]) => (
              <div key={eventType} className="flex justify-between items-center">
                <span className="text-space-300">{eventType}</span>
                <span className="text-white font-medium">{Math.round(accuracy * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}