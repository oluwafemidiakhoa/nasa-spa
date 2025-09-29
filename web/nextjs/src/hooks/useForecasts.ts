// Custom hook for managing forecast data with SWR

import useSWR from 'swr';
import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { ForecastBundle, APIResponse } from '@/types';

interface UseForecastsReturn {
  currentForecast: ForecastBundle | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  source: 'cached' | 'generated' | null;
  refreshForecast: () => Promise<void>;
  generateCustomForecast: (params: {
    days_back?: number;
    include_images?: boolean;
    epic_date_iso?: string;
    max_tokens?: number;
  }) => Promise<boolean>;
  isGenerating: boolean;
}

export function useForecasts(): UseForecastsReturn {
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch current forecast with SWR
  const { data, error, isLoading, mutate } = useSWR(
    'current-forecast',
    async () => {
      const response = await apiClient.getCurrentForecast();
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch forecast');
    },
    {
      refreshInterval: 5 * 60 * 1000, // Refresh every 5 minutes
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      dedupingInterval: 60 * 1000, // 1 minute deduping
      onError: (error) => {
        console.error('Forecast fetch error:', error);
      }
    }
  );

  const refreshForecast = useCallback(async () => {
    try {
      await mutate();
    } catch (err) {
      console.error('Failed to refresh forecast:', err);
    }
  }, [mutate]);

  const generateCustomForecast = useCallback(async (params: {
    days_back?: number;
    include_images?: boolean;
    epic_date_iso?: string;
    max_tokens?: number;
  }): Promise<boolean> => {
    setIsGenerating(true);
    
    try {
      const response = await apiClient.generateCustomForecast(params);
      
      if (response.success && response.data) {
        // Update the current forecast cache with the new data
        await mutate({
          forecast: response.data.forecast,
          generated_at: response.data.generated_at,
          source: 'generated' as const
        }, false);
        
        return true;
      } else {
        console.error('Custom forecast generation failed:', response.error);
        return false;
      }
    } catch (err) {
      console.error('Custom forecast generation error:', err);
      return false;
    } finally {
      setIsGenerating(false);
    }
  }, [mutate]);

  return {
    currentForecast: data?.forecast || null,
    isLoading,
    error: error?.message || null,
    lastUpdated: data?.generated_at || null,
    source: (data?.source as 'cached' | 'generated') || null,
    refreshForecast,
    generateCustomForecast,
    isGenerating,
  };
}

// Hook for forecast history
interface UseForecastHistoryReturn {
  forecasts: any[];
  isLoading: boolean;
  error: string | null;
  loadMore: (params?: {
    days?: number;
    limit?: number;
    event_type?: string;
  }) => Promise<void>;
}

export function useForecastHistory(initialParams: {
  days?: number;
  limit?: number;
  event_type?: string;
} = {}): UseForecastHistoryReturn {
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMore = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.getForecastHistory({
        days: 7,
        limit: 20,
        ...initialParams,
        ...params,
      });

      if (response.success && response.data) {
        setForecasts(response.data.forecasts);
      } else {
        setError(response.error || 'Failed to load forecast history');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load forecast history');
    } finally {
      setIsLoading(false);
    }
  }, [initialParams]);

  // Load initial data
  useState(() => {
    loadMore();
  });

  return {
    forecasts,
    isLoading,
    error,
    loadMore,
  };
}