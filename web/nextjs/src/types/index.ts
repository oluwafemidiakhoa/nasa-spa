// Type definitions for NASA Space Weather Forecaster

export interface Forecast {
  event: 'CME' | 'FLARE' | 'SEP' | 'GEO_STORM';
  solar_timestamp: string;
  predicted_arrival_window_utc: [string, string];
  risk_summary: string;
  impacts: string[];
  confidence: number;
  evidence: {
    donki_ids: string[];
    epic_frames: string[];
    gibs_layers: string[];
  };
}

export interface ForecastBundle {
  forecasts: Forecast[];
  generated_at: string;
  data_sources: string[];
}

export interface Alert {
  id: number;
  event_type: string;
  severity: 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';
  message: string;
  created_at: string;
  expires_at?: string;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface AccuracyStats {
  period_days: number;
  total_forecasts: number;
  evaluated_forecasts: number;
  average_accuracy: number;
  accuracy_by_event_type: Record<string, number>;
}

export interface ScheduledJob {
  id: string;
  name: string;
  schedule_type: string;
  cron_expression: string;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
  success_count: number;
  failure_count: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'connection' | 'new_forecast' | 'new_alert' | 'echo';
  message?: string;
  data?: any;
  timestamp: string;
}

// Map and visualization types
export interface MapViewport {
  longitude: number;
  latitude: number;
  zoom: number;
}

export interface GIBSLayer {
  id: string;
  name: string;
  url_template: string;
  time?: string;
  opacity?: number;
  visible?: boolean;
}

// Component props types
export interface ForecastCardProps {
  forecast: Forecast;
  className?: string;
}

export interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (alertId: number) => void;
}

export interface MapComponentProps {
  viewport: MapViewport;
  onViewportChange: (viewport: MapViewport) => void;
  layers: GIBSLayer[];
  className?: string;
}

// API endpoints
export interface APIEndpoints {
  forecast: {
    current: '/api/v1/forecast/current';
    generate: '/api/v1/forecast/generate';
    history: '/api/v1/forecast/history';
  };
  alerts: {
    active: '/api/v1/alerts/active';
    subscribe: '/api/v1/alerts/subscribe';
  };
  stats: {
    accuracy: '/api/v1/stats/accuracy';
  };
  websocket: '/ws/forecasts';
}