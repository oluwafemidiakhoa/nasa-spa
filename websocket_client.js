
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
