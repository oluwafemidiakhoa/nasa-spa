#!/usr/bin/env python3
"""
WebSocket Server for Real-Time Space Weather Data Streaming
Provides live updates to all connected dashboards
"""

import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime, timedelta
import threading
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up environment
os.environ['NASA_API_KEY'] = 'h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpaceWeatherWebSocketServer:
    def __init__(self, host='localhost', port=9002):
        self.host = host
        self.port = port
        self.clients = set()
        self.latest_data = {}
        self.nasa_client = None
        self.running = False
        
    async def register(self, websocket, path):
        """Register a new client"""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_info} (Total: {len(self.clients)})")
        
        # Send current data to new client
        if self.latest_data:
            await self.send_to_client(websocket, {
                "type": "initial_data",
                "data": self.latest_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        try:
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {client_info}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from {client_info}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_info}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client removed: {client_info} (Remaining: {len(self.clients)})")
    
    async def handle_client_message(self, websocket, data):
        """Handle messages from clients"""
        message_type = data.get('type', 'unknown')
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        if message_type == 'ping':
            await self.send_to_client(websocket, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        elif message_type == 'request_update':
            logger.info(f"Update requested by {client_info}")
            await self.force_update()
        
        elif message_type == 'subscribe':
            # Handle subscription preferences
            preferences = data.get('preferences', {})
            logger.info(f"Client {client_info} subscription preferences: {preferences}")
            # Store preferences for this client (could be expanded)
        
        else:
            logger.warning(f"Unknown message type from {client_info}: {message_type}")
    
    async def send_to_client(self, websocket, data):
        """Send data to a specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            self.clients.discard(websocket)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
    
    async def broadcast(self, data):
        """Broadcast data to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(data)
        logger.info(f"Broadcasting to {len(self.clients)} clients: {data.get('type', 'unknown')}")
        
        # Send to all clients concurrently
        disconnected_clients = set()
        
        for client in self.clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        self.clients -= disconnected_clients
        if disconnected_clients:
            logger.info(f"Removed {len(disconnected_clients)} disconnected clients")
    
    def initialize_nasa_client(self):
        """Initialize NASA API client"""
        try:
            from nasa_client import NASAClient
            self.nasa_client = NASAClient()
            logger.info("NASA client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NASA client: {e}")
            return False
    
    async def fetch_live_data(self):
        """Fetch live space weather data from NASA"""
        try:
            if not self.nasa_client:
                if not self.initialize_nasa_client():
                    return None
            
            # Fetch all space weather events
            events = self.nasa_client.get_all_space_weather_events(days_back=7)
            
            # Process and format data
            processed_data = {
                "events": events,
                "summary": {
                    "total_events": sum(len(event_list) for event_list in events.values()),
                    "cme_count": len(events.get('cmes', [])),
                    "flare_count": len(events.get('flares', [])),
                    "sep_count": len(events.get('sep_events', [])),
                    "geomagnetic_storm_count": len(events.get('geomagnetic_storms', [])),
                    "last_updated": datetime.utcnow().isoformat() + "Z"
                },
                "data_sources": ["NASA DONKI (Live)"],
                "stream_source": "WebSocket Real-Time"
            }
            
            logger.info(f"Fetched live data: {processed_data['summary']['total_events']} total events")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            return None
    
    async def data_update_loop(self):
        """Continuous loop to fetch and broadcast data updates"""
        logger.info("Starting data update loop...")
        
        while self.running:
            try:
                # Fetch new data
                new_data = await self.fetch_live_data()
                
                if new_data:
                    # Check if data has changed
                    data_changed = (
                        not self.latest_data or 
                        new_data['summary']['total_events'] != self.latest_data.get('summary', {}).get('total_events', 0)
                    )
                    
                    # Update stored data
                    self.latest_data = new_data
                    
                    # Broadcast to clients
                    broadcast_data = {
                        "type": "data_update",
                        "data": new_data,
                        "changed": data_changed,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    await self.broadcast(broadcast_data)
                    
                    if data_changed:
                        logger.info("Data changed - update broadcasted")
                    
                else:
                    # Send heartbeat if no data
                    await self.broadcast({
                        "type": "heartbeat",
                        "status": "alive",
                        "clients": len(self.clients),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                
                # Wait before next update (configurable interval)
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("Data update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in data update loop: {e}")
                await asyncio.sleep(10)  # Wait before retry
    
    async def force_update(self):
        """Force an immediate data update"""
        try:
            new_data = await self.fetch_live_data()
            if new_data:
                self.latest_data = new_data
                await self.broadcast({
                    "type": "forced_update",
                    "data": new_data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                logger.info("Forced update completed")
        except Exception as e:
            logger.error(f"Error in forced update: {e}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start data update loop
        update_task = asyncio.create_task(self.data_update_loop())
        
        try:
            # Start WebSocket server
            async with websockets.serve(self.register, self.host, self.port):
                logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
                logger.info("Waiting for client connections...")
                
                # Keep server running
                await asyncio.Future()  # Run forever
                
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            update_task.cancel()
            logger.info("WebSocket server stopped")

def main():
    """Main server function"""
    print("NASA Space Weather WebSocket Server")
    print("Real-time data streaming for dashboards")
    print("=" * 50)
    
    server = SpaceWeatherWebSocketServer()
    
    try:
        # Run the server
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Server failed to start: {e}")

if __name__ == "__main__":
    main()
