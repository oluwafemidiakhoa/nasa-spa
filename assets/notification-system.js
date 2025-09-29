/**
 * NASA Real-Time Alert and Notification System
 * Advanced notification management with space weather alerting
 */

class NASANotificationSystem {
    constructor() {
        this.notifications = [];
        this.alertRules = new Map();
        this.userPreferences = {
            enableSounds: true,
            enableDesktopNotifications: true,
            alertLevels: ['high', 'critical'],
            maxNotifications: 5,
            autoHideDelay: 8000
        };
        this.soundEnabled = true;
        this.isMonitoring = false;
        
        this.init();
    }

    init() {
        this.createNotificationContainer();
        this.setupAlertRules();
        this.requestNotificationPermission();
        this.createSoundEffects();
        this.setupDataMonitoring();
        this.createControlPanel();
        
        console.log('🔔 NASA Notification System initialized');
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'nasa-notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.userPreferences.enableDesktopNotifications = permission === 'granted';
            
            if (permission === 'granted') {
                this.showNotification('Desktop notifications enabled', 'success');
            }
        }
    }

    setupAlertRules() {
        // Define space weather alert conditions
        this.alertRules.set('high_cme_speed', {
            condition: (data) => data.cmes && data.cmes.some(cme => cme.speed > 1000),
            level: 'critical',
            title: 'High-Speed CME Detected',
            message: 'Fast CME detected - potential geomagnetic storm risk',
            sound: 'critical'
        });

        this.alertRules.set('multiple_flares', {
            condition: (data) => data.solar_flares && data.solar_flares.length > 3,
            level: 'high',
            title: 'Multiple Solar Flares',
            message: 'Multiple solar flares detected in recent period',
            sound: 'warning'
        });

        this.alertRules.set('x_class_flare', {
            condition: (data) => data.solar_flares && data.solar_flares.some(flare => 
                flare.class_type && flare.class_type.startsWith('X')),
            level: 'critical',
            title: 'X-Class Solar Flare',
            message: 'Major X-class solar flare detected - significant space weather effects possible',
            sound: 'emergency'
        });

        this.alertRules.set('high_activity', {
            condition: (data) => (data.cmes?.length || 0) + (data.solar_flares?.length || 0) > 10,
            level: 'medium',
            title: 'High Space Weather Activity',
            message: 'Elevated space weather activity detected',
            sound: 'info'
        });

        this.alertRules.set('data_loss', {
            condition: () => !window.LIVE_NASA_DATA || !window.LIVE_NASA_DATA.events,
            level: 'warning',
            title: 'Data Connection Lost',
            message: 'Lost connection to NASA data streams',
            sound: 'error'
        });
    }

    showNotification(message, type = 'info', options = {}) {
        const notification = {
            id: Date.now() + Math.random(),
            message,
            type,
            timestamp: new Date(),
            persistent: options.persistent || false,
            actions: options.actions || [],
            icon: this.getTypeIcon(type),
            ...options
        };

        this.notifications.unshift(notification);
        
        // Limit number of visible notifications
        if (this.notifications.length > this.userPreferences.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.userPreferences.maxNotifications);
        }

        this.renderNotifications();
        this.playNotificationSound(type);
        
        // Show desktop notification if enabled
        if (this.userPreferences.enableDesktopNotifications && type !== 'info') {
            this.showDesktopNotification(notification);
        }

        // Auto-hide non-persistent notifications
        if (!notification.persistent) {
            setTimeout(() => {
                this.removeNotification(notification.id);
            }, options.duration || this.userPreferences.autoHideDelay);
        }

        return notification.id;
    }

    showAlert(rule, data) {
        const alertData = this.alertRules.get(rule);
        if (!alertData) return;

        // Check if this alert level is enabled
        if (!this.userPreferences.alertLevels.includes(alertData.level)) return;

        const alertId = this.showNotification(alertData.message, alertData.level, {
            title: alertData.title,
            persistent: alertData.level === 'critical',
            actions: alertData.level === 'critical' ? [
                { label: 'View Details', action: () => this.showAlertDetails(rule, data) },
                { label: 'Acknowledge', action: () => this.acknowledgeAlert(alertId) }
            ] : []
        });

        // Log alert for analysis
        console.warn(`🚨 Space Weather Alert: ${alertData.title}`, data);
        
        return alertId;
    }

    renderNotifications() {
        const container = document.getElementById('nasa-notification-container');
        container.innerHTML = '';

        this.notifications.forEach((notification, index) => {
            const element = this.createNotificationElement(notification, index);
            container.appendChild(element);
        });
    }

    createNotificationElement(notification, index) {
        const element = document.createElement('div');
        element.className = `nasa-notification notification-${notification.type}`;
        element.style.cssText = `
            background: ${this.getTypeColor(notification.type)};
            border: 2px solid ${this.getTypeBorderColor(notification.type)};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            font-family: 'Inter', sans-serif;
            color: white;
            pointer-events: auto;
            cursor: pointer;
            transform: translateX(400px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            animation: slideIn 0.4s ease-out forwards;
            animation-delay: ${index * 0.1}s;
        `;

        const timeString = notification.timestamp.toLocaleTimeString();
        
        element.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <div style="font-size: 1.5rem; flex-shrink: 0;">${notification.icon}</div>
                <div style="flex: 1; min-width: 0;">
                    ${notification.title ? `<div style="font-weight: 600; margin-bottom: 4px; color: #ffffff;">${notification.title}</div>` : ''}
                    <div style="font-size: 0.9rem; line-height: 1.4; opacity: 0.9;">${notification.message}</div>
                    <div style="font-size: 0.7rem; opacity: 0.6; margin-top: 6px;">${timeString}</div>
                    ${notification.actions.length > 0 ? this.createActionButtons(notification) : ''}
                </div>
                <button onclick="nasaNotificationSystem.removeNotification('${notification.id}')" 
                        style="background: none; border: none; color: white; opacity: 0.6; 
                               cursor: pointer; font-size: 1.2rem; padding: 0; margin-left: 8px;">
                    ✕
                </button>
            </div>
        `;

        // Add click handler for non-persistent notifications
        if (!notification.persistent) {
            element.addEventListener('click', () => {
                this.removeNotification(notification.id);
            });
        }

        return element;
    }

    createActionButtons(notification) {
        return `
            <div style="margin-top: 10px; display: flex; gap: 8px;">
                ${notification.actions.map(action => `
                    <button onclick="${action.action.toString()}" 
                            style="background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.3); 
                                   color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; cursor: pointer;">
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.renderNotifications();
    }

    getTypeIcon(type) {
        const icons = {
            success: '✅',
            info: 'ℹ️',
            warning: '⚠️',
            error: '❌',
            critical: '🚨',
            high: '⚡',
            medium: '📊',
            low: '📈'
        };
        return icons[type] || 'ℹ️';
    }

    getTypeColor(type) {
        const colors = {
            success: 'linear-gradient(135deg, rgba(0, 120, 0, 0.9), rgba(0, 80, 0, 0.8))',
            info: 'linear-gradient(135deg, rgba(0, 100, 200, 0.9), rgba(0, 60, 120, 0.8))',
            warning: 'linear-gradient(135deg, rgba(200, 120, 0, 0.9), rgba(120, 80, 0, 0.8))',
            error: 'linear-gradient(135deg, rgba(200, 0, 0, 0.9), rgba(120, 0, 0, 0.8))',
            critical: 'linear-gradient(135deg, rgba(255, 0, 0, 0.9), rgba(150, 0, 0, 0.8))',
            high: 'linear-gradient(135deg, rgba(255, 100, 0, 0.9), rgba(150, 60, 0, 0.8))',
            medium: 'linear-gradient(135deg, rgba(100, 150, 255, 0.9), rgba(60, 90, 150, 0.8))',
            low: 'linear-gradient(135deg, rgba(0, 150, 100, 0.9), rgba(0, 90, 60, 0.8))'
        };
        return colors[type] || colors.info;
    }

    getTypeBorderColor(type) {
        const colors = {
            success: '#00ff00',
            info: '#00aaff',
            warning: '#ffaa00',
            error: '#ff0000',
            critical: '#ff0000',
            high: '#ff6600',
            medium: '#66aaff',
            low: '#00cc66'
        };
        return colors[type] || colors.info;
    }

    createSoundEffects() {
        this.sounds = {
            info: this.createBeep(800, 0.1, 'sine'),
            warning: this.createBeep(600, 0.2, 'square'),
            error: this.createBeep(400, 0.3, 'sawtooth'),
            critical: this.createAlertTone(),
            emergency: this.createEmergencyTone()
        };
    }

    createBeep(frequency, duration, type = 'sine') {
        return () => {
            if (!this.userPreferences.enableSounds) return;
            
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = type;
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        };
    }

    createAlertTone() {
        return () => {
            if (!this.userPreferences.enableSounds) return;
            
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create a more complex alert tone
            const frequencies = [880, 1047, 880, 1047, 880];
            let time = 0;
            
            frequencies.forEach((freq, index) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = freq;
                oscillator.type = 'square';
                
                gainNode.gain.setValueAtTime(0.2, audioContext.currentTime + time);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + time + 0.2);
                
                oscillator.start(audioContext.currentTime + time);
                oscillator.stop(audioContext.currentTime + time + 0.2);
                
                time += 0.25;
            });
        };
    }

    createEmergencyTone() {
        return () => {
            if (!this.userPreferences.enableSounds) return;
            
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Emergency siren-like sound
            for (let i = 0; i < 3; i++) {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime + i * 0.7);
                oscillator.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + i * 0.7 + 0.3);
                oscillator.frequency.exponentialRampToValueAtTime(800, audioContext.currentTime + i * 0.7 + 0.6);
                
                oscillator.type = 'sawtooth';
                
                gainNode.gain.setValueAtTime(0.2, audioContext.currentTime + i * 0.7);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + i * 0.7 + 0.6);
                
                oscillator.start(audioContext.currentTime + i * 0.7);
                oscillator.stop(audioContext.currentTime + i * 0.7 + 0.6);
            }
        };
    }

    playNotificationSound(type) {
        const soundMap = {
            success: 'info',
            info: 'info',
            warning: 'warning',
            error: 'error',
            critical: 'critical',
            high: 'warning',
            medium: 'info'
        };
        
        const soundType = soundMap[type] || 'info';
        if (this.sounds[soundType]) {
            this.sounds[soundType]();
        }
    }

    showDesktopNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const desktopNotification = new Notification(
                notification.title || 'NASA Space Weather Alert',
                {
                    body: notification.message,
                    icon: '/favicon.ico',
                    badge: '/favicon.ico',
                    tag: 'nasa-alert',
                    requireInteraction: notification.type === 'critical'
                }
            );

            desktopNotification.onclick = () => {
                window.focus();
                desktopNotification.close();
            };

            // Auto-close after 10 seconds
            setTimeout(() => {
                desktopNotification.close();
            }, 10000);
        }
    }

    setupDataMonitoring() {
        this.isMonitoring = true;
        this.lastDataCheck = null;
        
        // Monitor data changes every 30 seconds
        setInterval(() => {
            if (this.isMonitoring) {
                this.checkForAlerts();
            }
        }, 30000);
        
        // Initial check
        setTimeout(() => this.checkForAlerts(), 5000);
    }

    checkForAlerts() {
        if (!window.LIVE_NASA_DATA) {
            this.showAlert('data_loss');
            return;
        }

        const data = window.LIVE_NASA_DATA.events ? {
            cmes: window.LIVE_NASA_DATA.events.filter(e => e.type === 'CME'),
            solar_flares: window.LIVE_NASA_DATA.events.filter(e => e.type === 'FLARE')
        } : {};

        // Check each alert rule
        this.alertRules.forEach((rule, ruleName) => {
            if (rule.condition(data)) {
                this.showAlert(ruleName, data);
            }
        });
    }

    createControlPanel() {
        // Create notification settings panel (hidden by default)
        const panel = document.createElement('div');
        panel.id = 'nasa-notification-settings';
        panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9));
            border: 2px solid #00ffff;
            border-radius: 15px;
            padding: 25px;
            width: 400px;
            z-index: 10001;
            display: none;
            color: white;
            font-family: 'Inter', sans-serif;
        `;
        
        panel.innerHTML = `
            <h3 style="color: #00ffff; margin-bottom: 20px; text-align: center;">🔔 Notification Settings</h3>
            
            <label style="display: flex; align-items: center; margin-bottom: 10px; cursor: pointer;">
                <input type="checkbox" id="enable-sounds" ${this.userPreferences.enableSounds ? 'checked' : ''} 
                       style="margin-right: 10px;"> Enable Sounds
            </label>
            
            <label style="display: flex; align-items: center; margin-bottom: 15px; cursor: pointer;">
                <input type="checkbox" id="enable-desktop" ${this.userPreferences.enableDesktopNotifications ? 'checked' : ''} 
                       style="margin-right: 10px;"> Desktop Notifications
            </label>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px;">Alert Levels:</label>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    ${['low', 'medium', 'high', 'critical'].map(level => `
                        <label style="display: flex; align-items: center; cursor: pointer;">
                            <input type="checkbox" value="${level}" class="alert-level" 
                                   ${this.userPreferences.alertLevels.includes(level) ? 'checked' : ''}
                                   style="margin-right: 5px;"> ${level}
                        </label>
                    `).join('')}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button onclick="nasaNotificationSystem.saveSettings()" 
                        style="background: #00ffff; color: black; border: none; padding: 8px 16px; 
                               border-radius: 5px; cursor: pointer; margin-right: 10px;">Save</button>
                <button onclick="document.getElementById('nasa-notification-settings').style.display='none'" 
                        style="background: #666; color: white; border: none; padding: 8px 16px; 
                               border-radius: 5px; cursor: pointer;">Cancel</button>
            </div>
        `;
        
        document.body.appendChild(panel);
    }

    openSettings() {
        document.getElementById('nasa-notification-settings').style.display = 'block';
    }

    saveSettings() {
        this.userPreferences.enableSounds = document.getElementById('enable-sounds').checked;
        this.userPreferences.enableDesktopNotifications = document.getElementById('enable-desktop').checked;
        
        const alertLevels = Array.from(document.querySelectorAll('.alert-level:checked')).map(cb => cb.value);
        this.userPreferences.alertLevels = alertLevels;
        
        // Save to localStorage
        localStorage.setItem('nasaNotificationPreferences', JSON.stringify(this.userPreferences));
        
        document.getElementById('nasa-notification-settings').style.display = 'none';
        this.showNotification('Settings saved successfully', 'success');
    }

    loadSettings() {
        const saved = localStorage.getItem('nasaNotificationPreferences');
        if (saved) {
            this.userPreferences = { ...this.userPreferences, ...JSON.parse(saved) };
        }
    }

    // Public API methods
    clearAllNotifications() {
        this.notifications = [];
        this.renderNotifications();
    }

    toggleMonitoring() {
        this.isMonitoring = !this.isMonitoring;
        const status = this.isMonitoring ? 'enabled' : 'disabled';
        this.showNotification(`Alert monitoring ${status}`, 'info');
    }

    testAlert(level = 'warning') {
        this.showNotification(`Test ${level} notification`, level, {
            title: 'System Test',
            persistent: level === 'critical'
        });
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .nasa-notification:hover {
        transform: scale(1.02);
        transition: transform 0.2s ease;
    }
`;
document.head.appendChild(style);

// Initialize notification system
let nasaNotificationSystem;

document.addEventListener('DOMContentLoaded', () => {
    nasaNotificationSystem = new NASANotificationSystem();
    
    // Show welcome notification
    setTimeout(() => {
        nasaNotificationSystem.showNotification(
            'Real-time space weather alerts are now active!',
            'success',
            { title: 'Alert System Online' }
        );
    }, 2000);
});

// Export for global access
window.NASANotificationSystem = NASANotificationSystem;