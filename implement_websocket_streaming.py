#!/usr/bin/env python3
"""
Implement WebSocket real-time data streaming for NASA Space Weather dashboards
"""

import os
import sys
import json
from datetime import datetime

def create_websocket_server():
    """Create WebSocket server for real-time data streaming"""
    print("=" * 60)
    print("CREATING WEBSOCKET SERVER")
    print("=" * 60)
    
    websocket_server_content = '''#!/usr/bin/env python3
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
        print("\\nShutdown requested by user")
    except Exception as e:
        print(f"Server failed to start: {e}")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('websocket_server.py', 'w', encoding='utf-8') as f:
            f.write(websocket_server_content)
        
        print("SUCCESS: WebSocket server created as websocket_server.py")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create WebSocket server: {e}")
        return False

def create_websocket_client_library():
    """Create client-side WebSocket library for dashboards"""
    print("\n" + "=" * 60)
    print("CREATING WEBSOCKET CLIENT LIBRARY")
    print("=" * 60)
    
    client_library_content = '''
// WebSocket Client Library for Real-Time Space Weather Data
// Handles connection, reconnection, and data streaming

class SpaceWeatherWebSocket {
    constructor(options = {}) {
        this.url = options.url || 'ws://localhost:9002';
        this.reconnectInterval = options.reconnectInterval || 5000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.debug = options.debug || false;
        
        this.socket = null;
        this.reconnectAttempts = 0;
        this.connected = false;
        this.callbacks = {};
        this.lastHeartbeat = null;
        
        this.log('SpaceWeatherWebSocket initialized');
    }
    
    log(message) {
        if (this.debug) {
            console.log(`[WebSocket] ${new Date().toLocaleTimeString()}: ${message}`);
        }
    }
    
    connect() {
        this.log(`Connecting to ${this.url}`);
        
        try {
            this.socket = new WebSocket(this.url);
            
            this.socket.onopen = (event) => {
                this.log('Connected successfully');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.trigger('connected', event);
                
                // Send initial ping
                this.ping();
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    this.log(`Error parsing message: ${e}`);
                }
            };
            
            this.socket.onclose = (event) => {
                this.log(`Connection closed: ${event.code} - ${event.reason}`);
                this.connected = false;
                this.trigger('disconnected', event);
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                } else {
                    this.log('Max reconnection attempts reached');
                    this.trigger('max_reconnect_attempts');
                }
            };
            
            this.socket.onerror = (error) => {
                this.log(`WebSocket error: ${error}`);
                this.trigger('error', error);
            };
            
        } catch (error) {
            this.log(`Failed to create WebSocket: ${error}`);
            this.scheduleReconnect();
        }
    }
    
    handleMessage(data) {
        this.log(`Received message type: ${data.type}`);
        
        switch (data.type) {
            case 'initial_data':
                this.trigger('initial_data', data.data);
                break;
                
            case 'data_update':
                this.trigger('data_update', data.data, data.changed);
                if (data.changed) {
                    this.trigger('data_changed', data.data);
                }
                break;
                
            case 'forced_update':
                this.trigger('forced_update', data.data);
                break;
                
            case 'heartbeat':
                this.lastHeartbeat = new Date();
                this.trigger('heartbeat', data);
                break;
                
            case 'pong':
                this.trigger('pong', data);
                break;
                
            default:
                this.log(`Unknown message type: ${data.type}`);
                this.trigger('unknown_message', data);
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectInterval}ms`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval);
            
            this.trigger('reconnect_scheduled', {
                attempt: this.reconnectAttempts,
                maxAttempts: this.maxReconnectAttempts
            });
        }
    }
    
    send(data) {
        if (this.connected && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
            this.log(`Sent message: ${data.type}`);
            return true;
        } else {
            this.log('Cannot send message - not connected');
            return false;
        }
    }
    
    ping() {
        return this.send({
            type: 'ping',
            timestamp: new Date().toISOString()
        });
    }
    
    requestUpdate() {
        return this.send({
            type: 'request_update',
            timestamp: new Date().toISOString()
        });
    }
    
    subscribe(preferences = {}) {
        return this.send({
            type: 'subscribe',
            preferences: preferences,
            timestamp: new Date().toISOString()
        });
    }
    
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    trigger(event, ...args) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(...args);
                } catch (e) {
                    this.log(`Error in event callback for ${event}: ${e}`);
                }
            });
        }
    }
    
    disconnect() {
        this.log('Manually disconnecting');
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
        
        if (this.socket) {
            this.socket.close();
        }
    }
    
    getStatus() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts,
            lastHeartbeat: this.lastHeartbeat,
            readyState: this.socket ? this.socket.readyState : null
        };
    }
}

// Helper function to create and configure WebSocket connection
function createSpaceWeatherWebSocket(options = {}) {
    const ws = new SpaceWeatherWebSocket({
        debug: true,
        ...options
    });
    
    // Set up basic event handlers
    ws.on('connected', () => {
        console.log('🔗 WebSocket connected - real-time data streaming active');
        updateConnectionStatus('connected');
    });
    
    ws.on('disconnected', () => {
        console.log('❌ WebSocket disconnected');
        updateConnectionStatus('disconnected');
    });
    
    ws.on('data_changed', (data) => {
        console.log('📡 New space weather data received:', data.summary);
        if (window.updateDashboardWithLiveData) {
            window.updateDashboardWithLiveData(data);
        }
    });
    
    ws.on('heartbeat', (data) => {
        console.log(`💓 Heartbeat - ${data.clients} clients connected`);
        updateConnectionStatus('connected', data.clients);
    });
    
    ws.on('error', (error) => {
        console.error('🚨 WebSocket error:', error);
        updateConnectionStatus('error');
    });
    
    ws.on('reconnect_scheduled', (info) => {
        console.log(`🔄 Reconnecting... (${info.attempt}/${info.maxAttempts})`);
        updateConnectionStatus('reconnecting', null, info.attempt);
    });
    
    return ws;
}

// Update connection status indicator
function updateConnectionStatus(status, clients = null, attempt = null) {
    const indicators = document.querySelectorAll('.ws-status, #ws-status, .connection-status');
    
    indicators.forEach(indicator => {
        if (!indicator) return;
        
        let statusText = '';
        let statusClass = '';
        
        switch (status) {
            case 'connected':
                statusText = clients ? `🔗 Live (${clients} clients)` : '🔗 Live';
                statusClass = 'connected';
                indicator.style.color = '#00ff88';
                break;
            case 'disconnected':
                statusText = '❌ Disconnected';
                statusClass = 'disconnected';
                indicator.style.color = '#ff8888';
                break;
            case 'reconnecting':
                statusText = attempt ? `🔄 Reconnecting (${attempt})` : '🔄 Reconnecting';
                statusClass = 'reconnecting';
                indicator.style.color = '#ffaa44';
                break;
            case 'error':
                statusText = '🚨 Error';
                statusClass = 'error';
                indicator.style.color = '#ff4444';
                break;
        }
        
        indicator.textContent = statusText;
        indicator.className = `ws-status ${statusClass}`;
    });
}

// Global WebSocket instance
window.spaceWeatherWS = null;

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing WebSocket connection...');
    
    window.spaceWeatherWS = createSpaceWeatherWebSocket();
    window.spaceWeatherWS.connect();
    
    // Add manual controls if elements exist
    const connectBtn = document.getElementById('ws-connect');
    const disconnectBtn = document.getElementById('ws-disconnect');
    const refreshBtn = document.getElementById('ws-refresh');
    
    if (connectBtn) {
        connectBtn.addEventListener('click', () => {
            window.spaceWeatherWS.connect();
        });
    }
    
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', () => {
            window.spaceWeatherWS.disconnect();
        });
    }
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            window.spaceWeatherWS.requestUpdate();
        });
    }
});

console.log('SpaceWeatherWebSocket library loaded');
'''
    
    try:
        with open('websocket_client.js', 'w', encoding='utf-8') as f:
            f.write(client_library_content)
        
        print("SUCCESS: WebSocket client library created as websocket_client.js")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create WebSocket client library: {e}")
        return False

def update_dashboards_with_websocket():
    """Update all dashboards to include WebSocket functionality"""
    print("\n" + "=" * 60)
    print("UPDATING DASHBOARDS WITH WEBSOCKET INTEGRATION")
    print("=" * 60)
    
    dashboards = ['3d_dashboard.html', 'simple_new.html', 'professional_dashboard.html']
    results = {}
    
    for dashboard in dashboards:
        if os.path.exists(dashboard):
            try:
                # Read dashboard
                with open(dashboard, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add WebSocket script if not already present
                if 'websocket_client.js' not in content:
                    # Find live_nasa_data.js script and add WebSocket after it
                    live_data_script = '<script src="live_nasa_data.js"></script>'
                    if live_data_script in content:
                        websocket_script = '\\n    <script src="websocket_client.js"></script>'
                        content = content.replace(live_data_script, live_data_script + websocket_script)
                    else:
                        # Add to head section
                        head_end = content.find('</head>')
                        if head_end != -1:
                            websocket_script = '    <script src="websocket_client.js"></script>\\n'
                            content = content[:head_end] + websocket_script + content[head_end:]
                
                # Add WebSocket status indicator to header if not present
                if 'ws-status' not in content and 'connection-status' not in content:
                    # Find a suitable location in the header/status area
                    header_patterns = [
                        '<div class="header-status">',
                        '<div class="status-bar">',
                        '<div class="header">'
                    ]
                    
                    for pattern in header_patterns:
                        if pattern in content:
                            # Add status indicator after the opening div
                            insert_pos = content.find('>', content.find(pattern)) + 1
                            status_html = '''
                <div class="ws-status" id="ws-status" style="color: #ffaa44; font-size: 0.9rem; margin: 5px 0;">
                    🔄 Connecting to real-time feed...
                </div>'''
                            content = content[:insert_pos] + status_html + content[insert_pos:]
                            break
                
                # Add WebSocket update function
                websocket_update_function = '''
        
        // WebSocket real-time data update handler
        window.updateDashboardWithLiveData = function(data) {
            console.log('Updating dashboard with real-time WebSocket data:', data);
            
            // Update live NASA data
            if (window.LIVE_NASA_DATA) {
                window.LIVE_NASA_DATA.events = data.events;
                window.LIVE_NASA_DATA.summary = data.summary;
                window.LIVE_NASA_DATA.summary.data_source = 'WebSocket Real-Time';
            }
            
            // Trigger dashboard updates
            if (typeof updateTimeline === 'function') {
                updateTimeline(data);
            }
            
            if (typeof updateForecastDisplay === 'function') {
                updateForecastDisplay(data);
            }
            
            if (typeof updateCMEVisualization === 'function') {
                updateCMEVisualization(data.events.cmes);
            }
            
            // Update event counts in ensemble dashboard
            const eventsCountEl = document.getElementById('events-count');
            if (eventsCountEl && data.summary) {
                const newCount = data.summary.total_events;
                eventsCountEl.style.transition = 'transform 0.3s ease, color 0.3s ease';
                eventsCountEl.style.transform = 'scale(1.1)';
                eventsCountEl.style.color = '#00ffff';
                
                setTimeout(() => {
                    eventsCountEl.textContent = newCount;
                    eventsCountEl.style.transform = 'scale(1)';
                    eventsCountEl.style.color = '';
                }, 200);
            }
            
            // Show update notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0, 255, 136, 0.9);
                color: black;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 0.9rem;
                z-index: 1000;
                animation: fadeInOut 3s ease-in-out;
            `;
            notification.textContent = `📡 Live update: ${data.summary.total_events} events`;
            
            // Add fade animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeInOut {
                    0% { opacity: 0; transform: translateX(100%); }
                    20% { opacity: 1; transform: translateX(0); }
                    80% { opacity: 1; transform: translateX(0); }
                    100% { opacity: 0; transform: translateX(100%); }
                }
            `;
            document.head.appendChild(style);
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 3000);
        };
'''
                
                # Insert before closing script tag
                script_end = content.rfind('</script>')
                if script_end != -1:
                    content = content[:script_end] + websocket_update_function + content[script_end:]
                
                # Save updated dashboard
                with open(dashboard, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"SUCCESS: {dashboard} updated with WebSocket integration")
                results[dashboard] = True
                
            except Exception as e:
                print(f"ERROR: Failed to update {dashboard}: {e}")
                results[dashboard] = False
        else:
            print(f"WARNING: {dashboard} not found")
            results[dashboard] = False
    
    return results

def create_websocket_requirements():
    """Create requirements file for WebSocket dependencies"""
    print("\n" + "=" * 60)
    print("CREATING WEBSOCKET REQUIREMENTS")
    print("=" * 60)
    
    requirements_content = '''# WebSocket Real-Time Streaming Requirements
# Install with: pip install -r requirements_websocket.txt

# Core WebSocket library
websockets>=11.0.3

# Async support (usually included with Python 3.7+)
asyncio

# JSON handling (built-in)
# json

# Logging (built-in)
# logging

# Additional useful libraries for real-time features
aiohttp>=3.8.5
aiofiles>=23.1.0

# For advanced monitoring (optional)
psutil>=5.9.5
'''
    
    try:
        with open('requirements_websocket.txt', 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        
        print("SUCCESS: WebSocket requirements created as requirements_websocket.txt")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create requirements file: {e}")
        return False

def create_websocket_test_page():
    """Create a test page for WebSocket functionality"""
    print("\n" + "=" * 60)
    print("CREATING WEBSOCKET TEST PAGE")
    print("=" * 60)
    
    test_page_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Real-Time Test</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a3a, #2d2d5f);
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            border: 2px solid #00bfff;
        }
        
        .test-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .test-card {
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: linear-gradient(45deg, #00bfff, #0080ff);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .btn:hover {
            background: linear-gradient(45deg, #0080ff, #0060ff);
        }
        
        .btn:disabled {
            background: #666;
            cursor: not-allowed;
        }
        
        .status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .status.connected {
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
        }
        
        .status.disconnected {
            background: rgba(255, 136, 136, 0.2);
            border: 1px solid #ff8888;
        }
        
        .status.reconnecting {
            background: rgba(255, 170, 68, 0.2);
            border: 1px solid #ffaa44;
        }
        
        .log {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #666;
            border-radius: 5px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.8rem;
            line-height: 1.4;
        }
        
        .log-entry {
            margin-bottom: 5px;
        }
        
        .log-entry.info {
            color: #00ffff;
        }
        
        .log-entry.success {
            color: #00ff88;
        }
        
        .log-entry.error {
            color: #ff8888;
        }
        
        .log-entry.warning {
            color: #ffaa44;
        }
        
        .data-display {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff88;
            border-radius: 5px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }
        
        @media screen and (max-width: 768px) {
            .test-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 WebSocket Real-Time Test</h1>
            <p>Test real-time space weather data streaming</p>
        </div>
        
        <div class="test-grid">
            <div class="test-card">
                <h3>🔗 Connection Control</h3>
                
                <div class="controls">
                    <button class="btn" id="ws-connect">Connect</button>
                    <button class="btn" id="ws-disconnect">Disconnect</button>
                    <button class="btn" id="ws-refresh">Force Update</button>
                    <button class="btn" id="clear-log">Clear Log</button>
                </div>
                
                <div class="status disconnected" id="connection-status">
                    ❌ Disconnected
                </div>
                
                <div>
                    <strong>Connection Info:</strong>
                    <div class="metric">
                        <span>Server:</span>
                        <span id="server-url">ws://localhost:9002</span>
                    </div>
                    <div class="metric">
                        <span>Attempts:</span>
                        <span id="reconnect-attempts">0/10</span>
                    </div>
                    <div class="metric">
                        <span>Last Heartbeat:</span>
                        <span id="last-heartbeat">Never</span>
                    </div>
                </div>
            </div>
            
            <div class="test-card">
                <h3>📡 Live Data</h3>
                
                <div class="data-display" id="live-data">
                    <div class="metric">
                        <span>Total Events:</span>
                        <span id="total-events">-</span>
                    </div>
                    <div class="metric">
                        <span>CMEs:</span>
                        <span id="cme-count">-</span>
                    </div>
                    <div class="metric">
                        <span>Solar Flares:</span>
                        <span id="flare-count">-</span>
                    </div>
                    <div class="metric">
                        <span>Last Updated:</span>
                        <span id="last-updated">-</span>
                    </div>
                    <div class="metric">
                        <span>Data Source:</span>
                        <span id="data-source">-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="test-card">
            <h3>📋 Activity Log</h3>
            <div class="log" id="activity-log">
                <div class="log-entry info">WebSocket test page loaded</div>
            </div>
        </div>
    </div>
    
    <script src="websocket_client.js"></script>
    <script>
        // Test page specific functionality
        let logCount = 1;
        
        function addLogEntry(message, type = 'info') {
            const log = document.getElementById('activity-log');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
            
            // Keep log manageable
            if (log.children.length > 100) {
                log.removeChild(log.firstChild);
            }
        }
        
        function updateConnectionInfo(status) {
            const statusEl = document.getElementById('connection-status');
            const attemptsEl = document.getElementById('reconnect-attempts');
            
            if (window.spaceWeatherWS) {
                const wsStatus = window.spaceWeatherWS.getStatus();
                attemptsEl.textContent = `${wsStatus.reconnectAttempts}/${wsStatus.maxReconnectAttempts}`;
            }
        }
        
        function updateLiveDataDisplay(data) {
            if (data && data.summary) {
                document.getElementById('total-events').textContent = data.summary.total_events || 0;
                document.getElementById('cme-count').textContent = data.summary.cme_count || 0;
                document.getElementById('flare-count').textContent = data.summary.flare_count || 0;
                document.getElementById('last-updated').textContent = 
                    data.summary.last_updated ? new Date(data.summary.last_updated).toLocaleTimeString() : '-';
                document.getElementById('data-source').textContent = 
                    data.stream_source || data.data_sources?.[0] || '-';
            }
        }
        
        // Override the connection status function
        window.updateConnectionStatus = function(status, clients = null, attempt = null) {
            const statusEl = document.getElementById('connection-status');
            
            let statusText = '';
            let statusClass = '';
            
            switch (status) {
                case 'connected':
                    statusText = clients ? `🔗 Connected (${clients} clients)` : '🔗 Connected';
                    statusClass = 'connected';
                    addLogEntry(statusText, 'success');
                    break;
                case 'disconnected':
                    statusText = '❌ Disconnected';
                    statusClass = 'disconnected';
                    addLogEntry('Connection lost', 'error');
                    break;
                case 'reconnecting':
                    statusText = attempt ? `🔄 Reconnecting (${attempt})` : '🔄 Reconnecting';
                    statusClass = 'reconnecting';
                    addLogEntry(`Reconnection attempt ${attempt}`, 'warning');
                    break;
                case 'error':
                    statusText = '🚨 Error';
                    statusClass = 'error';
                    addLogEntry('WebSocket error occurred', 'error');
                    break;
            }
            
            statusEl.textContent = statusText;
            statusEl.className = `status ${statusClass}`;
            updateConnectionInfo(status);
        };
        
        // Override the data update function
        window.updateDashboardWithLiveData = function(data) {
            addLogEntry(`Data update received: ${data.summary?.total_events || 0} events`, 'success');
            updateLiveDataDisplay(data);
        };
        
        // Set up custom WebSocket event handlers
        document.addEventListener('DOMContentLoaded', () => {
            addLogEntry('Setting up WebSocket connection...', 'info');
            
            // Wait a moment for WebSocket to initialize
            setTimeout(() => {
                if (window.spaceWeatherWS) {
                    // Add custom handlers
                    window.spaceWeatherWS.on('initial_data', (data) => {
                        addLogEntry('Initial data received', 'success');
                        updateLiveDataDisplay(data);
                    });
                    
                    window.spaceWeatherWS.on('heartbeat', (data) => {
                        document.getElementById('last-heartbeat').textContent = new Date().toLocaleTimeString();
                        addLogEntry(`Heartbeat - ${data.clients} clients`, 'info');
                    });
                    
                    window.spaceWeatherWS.on('data_changed', (data) => {
                        addLogEntry('Space weather data changed!', 'success');
                    });
                    
                    window.spaceWeatherWS.on('forced_update', (data) => {
                        addLogEntry('Forced update completed', 'info');
                    });
                }
            }, 1000);
            
            // Set up button handlers
            document.getElementById('clear-log').addEventListener('click', () => {
                const log = document.getElementById('activity-log');
                log.innerHTML = '<div class="log-entry info">Log cleared</div>';
            });
        });
        
        addLogEntry('WebSocket test interface ready', 'info');
    </script>
</body>
</html>'''
    
    try:
        with open('websocket_test.html', 'w', encoding='utf-8') as f:
            f.write(test_page_content)
        
        print("SUCCESS: WebSocket test page created as websocket_test.html")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create WebSocket test page: {e}")
        return False

def main():
    """Main WebSocket implementation function"""
    print("NASA Space Weather Dashboard - WebSocket Real-Time Streaming Implementation")
    print(f"Starting WebSocket integration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Create WebSocket server
    server_ok = create_websocket_server()
    
    # Step 2: Create client library
    client_ok = create_websocket_client_library()
    
    # Step 3: Update dashboards
    dashboard_results = update_dashboards_with_websocket()
    
    # Step 4: Create requirements
    requirements_ok = create_websocket_requirements()
    
    # Step 5: Create test page
    test_page_ok = create_websocket_test_page()
    
    # Summary
    print("\n" + "=" * 60)
    print("WEBSOCKET REAL-TIME STREAMING IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    successful_dashboards = sum(1 for result in dashboard_results.values() if result)
    total_components = 5 + len(dashboard_results)  # server, client, requirements, test page + dashboards
    successful_components = sum([server_ok, client_ok, requirements_ok, test_page_ok]) + successful_dashboards
    
    if successful_components == total_components:
        print("STATUS: ✓ WEBSOCKET REAL-TIME STREAMING COMPLETE")
        print()
        print("🚀 Successfully implemented:")
        print("   • WebSocket server (websocket_server.py)")
        print("   • Client-side library (websocket_client.js)")
        print("   • Real-time dashboard integration")
        print("   • Auto-reconnection and error handling")
        print("   • Live data broadcasting")
        print()
        print("📡 Real-time features:")
        print("   • 30-second update intervals")
        print("   • Instant data change notifications")
        print("   • Connection status indicators")
        print("   • Multi-client support")
        print("   • Automatic reconnection")
        print("   • Force refresh capability")
        print()
        print("🧪 Testing:")
        print("   1. Install: pip install -r requirements_websocket.txt")
        print("   2. Start server: python websocket_server.py")
        print("   3. Open websocket_test.html to test")
        print("   4. Open dashboards to see real-time updates")
        print()
        print("📱 Dashboard integration:")
        print(f"   • 3D Dashboard: {'✓' if dashboard_results.get('3d_dashboard.html') else '✗'}")
        print(f"   • Ensemble Dashboard: {'✓' if dashboard_results.get('simple_new.html') else '✗'}")
        print(f"   • Professional Dashboard: {'✓' if dashboard_results.get('professional_dashboard.html') else '✗'}")
        print()
        print("✅ Task 5 (WebSocket Real-Time Streaming) COMPLETE")
        print("🚀 Ready to proceed to Task 6 (Export features)")
        
    else:
        print("STATUS: ⚠ PARTIAL IMPLEMENTATION")
        print(f"Successfully implemented: {successful_components}/{total_components} components")
        print("Some components may need manual adjustment")
    
    print()

if __name__ == "__main__":
    main()