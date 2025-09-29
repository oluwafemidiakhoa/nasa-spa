// Connection status indicator for WebSocket and API connectivity

import React from 'react';
import { motion } from 'framer-motion';

interface ConnectionStatusProps {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  className?: string;
}

export default function ConnectionStatus({
  isConnected,
  isConnecting,
  error,
  className = ''
}: ConnectionStatusProps) {
  const getStatusConfig = () => {
    if (error) {
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-900/20',
        borderColor: 'border-red-500/50',
        icon: '❌',
        text: 'Connection Error',
        pulse: false,
      };
    }

    if (isConnecting) {
      return {
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-900/20',
        borderColor: 'border-yellow-500/50',
        icon: '⏳',
        text: 'Connecting...',
        pulse: true,
      };
    }

    if (isConnected) {
      return {
        color: 'text-green-400',
        bgColor: 'bg-green-900/20',
        borderColor: 'border-green-500/50',
        icon: '✅',
        text: 'Real-time Connected',
        pulse: false,
      };
    }

    return {
      color: 'text-gray-400',
      bgColor: 'bg-gray-900/20',
      borderColor: 'border-gray-500/50',
      icon: '⚫',
      text: 'Disconnected',
      pulse: false,
    };
  };

  const config = getStatusConfig();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full border ${config.bgColor} ${config.borderColor} ${className}`}
    >
      <motion.span
        className="text-sm"
        animate={config.pulse ? { scale: [1, 1.2, 1] } : {}}
        transition={config.pulse ? { repeat: Infinity, duration: 1.5 } : {}}
      >
        {config.icon}
      </motion.span>
      
      <span className={`text-sm font-medium ${config.color}`}>
        {config.text}
      </span>

      {error && (
        <div className="relative group">
          <span className="text-red-400 text-xs cursor-help">ⓘ</span>
          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block z-10">
            <div className="bg-red-900 text-red-100 text-xs rounded-md p-2 shadow-lg whitespace-nowrap border border-red-700">
              {error}
              <div className="absolute top-full right-3 -mt-1 border-4 border-transparent border-t-red-900"></div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}