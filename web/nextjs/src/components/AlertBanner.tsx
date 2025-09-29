// Alert banner component for displaying active space weather alerts

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Alert } from '@/types';

interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (alertId: number) => void;
}

export default function AlertBanner({ alerts, onDismiss }: AlertBannerProps) {
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<number>>(new Set());

  if (!alerts || alerts.length === 0) {
    return null;
  }

  const visibleAlerts = alerts.filter(alert => !dismissedAlerts.has(alert.id));

  if (visibleAlerts.length === 0) {
    return null;
  }

  const getSeverityConfig = (severity: string) => {
    switch (severity) {
      case 'SEVERE':
        return {
          bg: 'bg-red-900/90',
          border: 'border-red-500',
          text: 'text-red-100',
          icon: '🔴',
          pulse: true,
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-900/90',
          border: 'border-orange-500',
          text: 'text-orange-100',
          icon: '🟠',
          pulse: false,
        };
      case 'MODERATE':
        return {
          bg: 'bg-yellow-900/90',
          border: 'border-yellow-500',
          text: 'text-yellow-100',
          icon: '🟡',
          pulse: false,
        };
      default:
        return {
          bg: 'bg-blue-900/90',
          border: 'border-blue-500',
          text: 'text-blue-100',
          icon: '🔵',
          pulse: false,
        };
    }
  };

  const handleDismiss = (alertId: number) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    onDismiss?.(alertId);
  };

  // Show the most severe alert
  const highestSeverityAlert = visibleAlerts.reduce((prev, current) => {
    const severityOrder = { SEVERE: 4, HIGH: 3, MODERATE: 2, LOW: 1 };
    const prevSeverity = severityOrder[prev.severity as keyof typeof severityOrder] || 0;
    const currentSeverity = severityOrder[current.severity as keyof typeof severityOrder] || 0;
    return currentSeverity > prevSeverity ? current : prev;
  });

  const config = getSeverityConfig(highestSeverityAlert.severity);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -100, opacity: 0 }}
        className={`${config.bg} ${config.border} border-b backdrop-blur ${config.pulse ? 'animate-pulse-slow' : ''}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center space-x-3">
              <span className="text-xl">{config.icon}</span>
              <div>
                <div className="flex items-center space-x-2">
                  <span className={`${config.text} font-semibold text-sm`}>
                    {highestSeverityAlert.severity} SPACE WEATHER ALERT
                  </span>
                  <span className={`${config.text} opacity-75 text-sm`}>
                    {highestSeverityAlert.event_type}
                  </span>
                  {visibleAlerts.length > 1 && (
                    <span className={`${config.text} opacity-50 text-xs`}>
                      (+{visibleAlerts.length - 1} more)
                    </span>
                  )}
                </div>
                <p className={`${config.text} text-sm opacity-90 mt-1 max-w-2xl`}>
                  {highestSeverityAlert.message}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleDismiss(highestSeverityAlert.id)}
                className={`${config.text} hover:opacity-75 transition-opacity p-1`}
                aria-label="Dismiss alert"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          {/* Additional alerts dropdown */}
          {visibleAlerts.length > 1 && (
            <details className="pb-3 group">
              <summary className={`${config.text} cursor-pointer text-sm opacity-75 hover:opacity-100 transition-opacity`}>
                <span className="inline-block w-4 h-4 mr-1 group-open:rotate-90 transition-transform">▶</span>
                Show all {visibleAlerts.length} alerts
              </summary>
              <div className="mt-3 space-y-2">
                {visibleAlerts.slice(1).map((alert) => {
                  const alertConfig = getSeverityConfig(alert.severity);
                  return (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className={`${alertConfig.bg} ${alertConfig.border} border rounded-md p-3`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span>{alertConfig.icon}</span>
                          <span className={`${alertConfig.text} font-medium text-sm`}>
                            {alert.severity} {alert.event_type}
                          </span>
                        </div>
                        <button
                          onClick={() => handleDismiss(alert.id)}
                          className={`${alertConfig.text} hover:opacity-75 transition-opacity`}
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </div>
                      <p className={`${alertConfig.text} text-sm opacity-90 mt-1`}>
                        {alert.message}
                      </p>
                    </motion.div>
                  );
                })}
              </div>
            </details>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}