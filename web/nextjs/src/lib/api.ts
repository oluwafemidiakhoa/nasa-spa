// API client for NASA Space Weather Forecaster

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { APIResponse, ForecastBundle, Alert, AccuracyStats, ScheduledJob } from '@/types';

class APIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use((config) => {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck(): Promise<APIResponse> {
    const response = await this.client.get('/api/v1/health');
    return response.data;
  }

  // Forecast endpoints
  async getCurrentForecast(): Promise<APIResponse<{ forecast: ForecastBundle; generated_at: string; source: string }>> {
    const response = await this.client.get('/api/v1/forecast/current');
    return response.data;
  }

  async generateCustomForecast(params: {
    days_back?: number;
    include_images?: boolean;
    epic_date_iso?: string;
    max_tokens?: number;
  }): Promise<APIResponse<{ forecast: ForecastBundle; generated_at: string }>> {
    const response = await this.client.post('/api/v1/forecast/generate', params);
    return response.data;
  }

  async getForecastHistory(params: {
    days?: number;
    limit?: number;
    event_type?: string;
  } = {}): Promise<APIResponse<{ forecasts: any[]; count: number }>> {
    const response = await this.client.get('/api/v1/forecast/history', { params });
    return response.data;
  }

  // Alert endpoints
  async getActiveAlerts(): Promise<APIResponse<{ alerts: Alert[] }>> {
    const response = await this.client.get('/api/v1/alerts/active');
    return response.data;
  }

  async subscribeToAlerts(subscription: {
    email?: string;
    phone?: string;
    alert_types: string[];
    min_confidence: number;
  }): Promise<APIResponse<{ subscription_id: number; message: string }>> {
    const response = await this.client.post('/api/v1/alerts/subscribe', subscription);
    return response.data;
  }

  // Statistics endpoints
  async getAccuracyStats(): Promise<APIResponse<AccuracyStats>> {
    const response = await this.client.get('/api/v1/stats/accuracy');
    return response.data;
  }

  // Utility methods
  getWebSocketURL(): string {
    const wsProtocol = this.baseURL.startsWith('https') ? 'wss' : 'ws';
    const wsBaseURL = this.baseURL.replace(/^https?/, wsProtocol);
    return `${wsBaseURL}/ws/forecasts`;
  }

  getGIBSUrl(layer: string, time: string, z: number, y: number, x: number): string {
    return `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${layer}/default/${time}/GoogleMapsCompatible_Level9/${z}/${y}/${x}.jpg`;
  }

  getEPICImageUrl(date: string, image: string, format: 'png' | 'jpg' = 'jpg'): string {
    return `https://epic.gsfc.nasa.gov/archive/natural/${date}/${format}/${image}.${format}`;
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// Export individual methods for easier imports
export const {
  healthCheck,
  getCurrentForecast,
  generateCustomForecast,
  getForecastHistory,
  getActiveAlerts,
  subscribeToAlerts,
  getAccuracyStats,
} = apiClient;