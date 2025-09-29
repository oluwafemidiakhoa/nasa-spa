// Map view component with GIBS Earth imagery layers

import React, { useEffect, useRef } from 'react';
import { MapViewport, GIBSLayer } from '@/types';

interface MapViewProps {
  viewport: MapViewport;
  onViewportChange: (viewport: MapViewport) => void;
  layers: GIBSLayer[];
  className?: string;
}

export default function MapView({ 
  viewport, 
  onViewportChange, 
  layers, 
  className = '' 
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // This is a placeholder for MapLibre GL integration
    // In a full implementation, you would initialize the map here
    console.log('Map initialization would happen here');
  }, []);

  return (
    <div className={`relative ${className}`}>
      <div
        ref={mapContainer}
        className="w-full h-full bg-space-900 rounded-lg border border-space-700 flex items-center justify-center"
      >
        <div className="text-center text-space-400">
          <div className="text-4xl mb-4">🌍</div>
          <div className="text-lg font-medium mb-2">Earth View</div>
          <div className="text-sm">
            Interactive map with GIBS layers will be displayed here
          </div>
          <div className="text-xs mt-2 opacity-75">
            Viewport: {viewport.latitude.toFixed(2)}, {viewport.longitude.toFixed(2)} @ zoom {viewport.zoom}
          </div>
        </div>
      </div>
    </div>
  );
}