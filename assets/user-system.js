/**
 * NASA User Authentication and Preferences System
 * Advanced user management with saved preferences and profiles
 */

class NASAUserSystem {
    constructor() {
        this.currentUser = null;
        this.isLoggedIn = false;
        this.userProfiles = new Map();
        this.preferences = {
            theme: 'dark',
            language: 'en',
            dashboardLayout: 'default',
            autoRefresh: true,
            refreshInterval: 30000,
            notifications: {
                enabled: true,
                levels: ['high', 'critical'],
                sounds: true,
                desktop: true
            },
            display: {
                units: 'metric',
                timezone: 'UTC',
                dateFormat: 'ISO',
                animations: true,
                particles: 'medium'
            },
            privacy: {
                analytics: true,
                crashReports: true,
                shareUsage: false
            }
        };
        
        this.init();
    }

    init() {
        this.loadStoredUser();
        this.createUserInterface();
        this.setupEventListeners();
        this.initializePreferences();
        
        console.log('👤 NASA User System initialized');
    }

    loadStoredUser() {
        const storedUser = localStorage.getItem('nasaUser');
        const storedPrefs = localStorage.getItem('nasaUserPreferences');
        
        if (storedUser) {
            this.currentUser = JSON.parse(storedUser);
            this.isLoggedIn = true;
        }
        
        if (storedPrefs) {
            this.preferences = { ...this.preferences, ...JSON.parse(storedPrefs) };
        }
        
        // Load demo profiles for demonstration
        this.loadDemoProfiles();
    }

    loadDemoProfiles() {
        const demoProfiles = [
            {
                id: 'demo_scientist',
                username: 'nasa_scientist',
                displayName: 'Dr. Sarah Chen',
                role: 'Space Weather Scientist',
                organization: 'NASA GSFC',
                avatar: '👩‍🔬',
                preferences: {
                    ...this.preferences,
                    display: { ...this.preferences.display, particles: 'high' },
                    dashboardLayout: 'expert'
                }
            },
            {
                id: 'demo_operator',
                username: 'mission_control',
                displayName: 'Alex Rodriguez',
                role: 'Mission Control Operator',
                organization: 'NASA JSC',
                avatar: '👨‍🚀',
                preferences: {
                    ...this.preferences,
                    autoRefresh: true,
                    refreshInterval: 15000,
                    notifications: { ...this.preferences.notifications, levels: ['medium', 'high', 'critical'] }
                }
            },
            {
                id: 'demo_researcher',
                username: 'space_researcher',
                displayName: 'Dr. Michael Kim',
                role: 'Research Scientist',
                organization: 'NOAA SWPC',
                avatar: '🔬',
                preferences: {
                    ...this.preferences,
                    display: { ...this.preferences.display, units: 'imperial' },
                    dashboardLayout: 'research'
                }
            }
        ];
        
        demoProfiles.forEach(profile => {
            this.userProfiles.set(profile.id, profile);
        });
    }

    createUserInterface() {
        this.createUserPanel();
        this.createLoginModal();
        this.createPreferencesModal();
        this.createUserMenu();
    }

    createUserPanel() {
        const panel = document.createElement('div');
        panel.id = 'nasa-user-panel';
        panel.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9));
            border: 2px solid #00ffff;
            border-radius: 10px;
            padding: 15px;
            backdrop-filter: blur(10px);
            font-family: 'Inter', sans-serif;
            color: white;
            z-index: 1000;
            min-width: 200px;
        `;
        
        this.updateUserPanel();
        document.body.appendChild(panel);
    }

    updateUserPanel() {
        const panel = document.getElementById('nasa-user-panel');
        if (!panel) return;
        
        if (this.isLoggedIn && this.currentUser) {
            panel.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="font-size: 2rem;">${this.currentUser.avatar || '👤'}</div>
                    <div>
                        <div style="font-weight: 600; color: #00ffff;">${this.currentUser.displayName}</div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">${this.currentUser.role}</div>
                        <div style="font-size: 0.7rem; opacity: 0.6;">${this.currentUser.organization}</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button onclick="nasaUserSystem.openPreferences()" 
                            style="background: rgba(0, 255, 255, 0.2); border: 1px solid #00ffff; 
                                   color: #00ffff; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">
                        ⚙️ Settings
                    </button>
                    <button onclick="nasaUserSystem.logout()" 
                            style="background: rgba(255, 0, 0, 0.2); border: 1px solid #ff6666; 
                                   color: #ff6666; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">
                        🚪 Logout
                    </button>
                </div>
            `;
        } else {
            panel.innerHTML = `
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">👤</div>
                    <div style="margin-bottom: 10px; color: #cccccc;">Guest User</div>
                    <button onclick="nasaUserSystem.showLogin()" 
                            style="background: linear-gradient(135deg, #00ffff, #0099cc); 
                                   border: none; color: black; padding: 8px 16px; 
                                   border-radius: 6px; cursor: pointer; font-weight: 600; width: 100%;">
                        🚀 Login / Sign Up
                    </button>
                </div>
            `;
        }
    }

    createLoginModal() {
        const modal = document.createElement('div');
        modal.id = 'nasa-login-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 10001;
        `;
        
        modal.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9)); 
                        border: 2px solid #00ffff; border-radius: 15px; padding: 30px; 
                        width: 450px; max-height: 80vh; overflow-y: auto;">
                <h2 style="color: #00ffff; text-align: center; margin-bottom: 25px;">🚀 NASA Mission Access</h2>
                
                <div id="login-tabs" style="display: flex; margin-bottom: 20px; border-radius: 8px; overflow: hidden;">
                    <button onclick="nasaUserSystem.switchTab('demo')" id="tab-demo" 
                            class="login-tab active" style="flex: 1; padding: 10px; background: #00ffff; color: black; border: none; cursor: pointer;">
                        Demo Profiles
                    </button>
                    <button onclick="nasaUserSystem.switchTab('custom')" id="tab-custom" 
                            class="login-tab" style="flex: 1; padding: 10px; background: #333; color: white; border: none; cursor: pointer;">
                        Custom Profile
                    </button>
                </div>
                
                <div id="demo-login" class="login-content">
                    <div style="margin-bottom: 20px; color: #cccccc; text-align: center;">
                        Select a demo profile to experience different user perspectives:
                    </div>
                    <div id="demo-profiles"></div>
                </div>
                
                <div id="custom-login" class="login-content" style="display: none;">
                    <form onsubmit="nasaUserSystem.handleCustomLogin(event)">
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #00ffff;">Display Name:</label>
                            <input type="text" id="custom-name" required 
                                   style="width: 100%; padding: 8px; background: rgba(0, 0, 0, 0.5); 
                                          border: 1px solid #00ffff; border-radius: 4px; color: white;" 
                                   placeholder="Enter your name">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; color: #00ffff;">Role:</label>
                            <select id="custom-role" 
                                    style="width: 100%; padding: 8px; background: rgba(0, 0, 0, 0.5); 
                                           border: 1px solid #00ffff; border-radius: 4px; color: white;">
                                <option value="Scientist">Space Weather Scientist</option>
                                <option value="Operator">Mission Control Operator</option>
                                <option value="Researcher">Research Scientist</option>
                                <option value="Engineer">Systems Engineer</option>
                                <option value="Student">Student/Trainee</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px; color: #00ffff;">Organization:</label>
                            <input type="text" id="custom-org" 
                                   style="width: 100%; padding: 8px; background: rgba(0, 0, 0, 0.5); 
                                          border: 1px solid #00ffff; border-radius: 4px; color: white;" 
                                   placeholder="NASA, NOAA, University, etc.">
                        </div>
                        <button type="submit" 
                                style="width: 100%; background: linear-gradient(135deg, #00ffff, #0099cc); 
                                       border: none; color: black; padding: 12px; border-radius: 6px; 
                                       cursor: pointer; font-weight: 600;">
                            Create Profile
                        </button>
                    </form>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button onclick="document.getElementById('nasa-login-modal').style.display='none'" 
                            style="background: #666; color: white; border: none; padding: 8px 16px; 
                                   border-radius: 5px; cursor: pointer;">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Populate demo profiles
        this.populateDemoProfiles();
        
        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    populateDemoProfiles() {
        const container = document.getElementById('demo-profiles');
        if (!container) return;
        
        const profiles = Array.from(this.userProfiles.values());
        container.innerHTML = profiles.map(profile => `
            <div onclick="nasaUserSystem.loginAsDemo('${profile.id}')" 
                 style="display: flex; align-items: center; gap: 15px; padding: 15px; 
                        border: 1px solid #333; border-radius: 8px; margin-bottom: 10px; 
                        cursor: pointer; transition: all 0.3s ease;"
                 onmouseover="this.style.borderColor='#00ffff'; this.style.background='rgba(0, 255, 255, 0.1)'"
                 onmouseout="this.style.borderColor='#333'; this.style.background='transparent'">
                <div style="font-size: 2.5rem;">${profile.avatar}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #00ffff; margin-bottom: 3px;">${profile.displayName}</div>
                    <div style="font-size: 0.9rem; color: #cccccc; margin-bottom: 2px;">${profile.role}</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">${profile.organization}</div>
                </div>
                <div style="color: #00ffff;">→</div>
            </div>
        `).join('');
    }

    createPreferencesModal() {
        const modal = document.createElement('div');
        modal.id = 'nasa-preferences-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 10001;
        `;
        
        modal.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9)); 
                        border: 2px solid #00ffff; border-radius: 15px; padding: 30px; 
                        width: 600px; max-height: 80vh; overflow-y: auto;">
                <h2 style="color: #00ffff; text-align: center; margin-bottom: 25px;">⚙️ User Preferences</h2>
                
                <div id="preferences-content"></div>
                
                <div style="text-align: center; margin-top: 25px;">
                    <button onclick="nasaUserSystem.savePreferences()" 
                            style="background: #00ffff; color: black; border: none; padding: 10px 20px; 
                                   border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: 600;">
                        Save Preferences
                    </button>
                    <button onclick="document.getElementById('nasa-preferences-modal').style.display='none'" 
                            style="background: #666; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 5px; cursor: pointer;">Cancel</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    createUserMenu() {
        // Add keyboard shortcut to open user menu
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'U') {
                if (this.isLoggedIn) {
                    this.openPreferences();
                } else {
                    this.showLogin();
                }
            }
        });
    }

    switchTab(tab) {
        // Update tab styles
        document.querySelectorAll('.login-tab').forEach(t => {
            t.style.background = '#333';
            t.style.color = 'white';
        });
        document.getElementById(`tab-${tab}`).style.background = '#00ffff';
        document.getElementById(`tab-${tab}`).style.color = 'black';
        
        // Show/hide content
        document.querySelectorAll('.login-content').forEach(c => c.style.display = 'none');
        document.getElementById(`${tab}-login`).style.display = 'block';
    }

    showLogin() {
        document.getElementById('nasa-login-modal').style.display = 'flex';
    }

    loginAsDemo(profileId) {
        const profile = this.userProfiles.get(profileId);
        if (profile) {
            this.currentUser = profile;
            this.isLoggedIn = true;
            this.preferences = { ...this.preferences, ...profile.preferences };
            
            this.saveUserData();
            this.updateUserPanel();
            this.applyPreferences();
            
            document.getElementById('nasa-login-modal').style.display = 'none';
            
            if (window.nasaAnimationController) {
                nasaAnimationController.showNotification(
                    `Welcome back, ${profile.displayName}!`,
                    'success'
                );
            }
        }
    }

    handleCustomLogin(event) {
        event.preventDefault();
        
        const name = document.getElementById('custom-name').value;
        const role = document.getElementById('custom-role').value;
        const org = document.getElementById('custom-org').value;
        
        const customUser = {
            id: 'custom_' + Date.now(),
            username: name.toLowerCase().replace(/\s+/g, '_'),
            displayName: name,
            role: role,
            organization: org || 'Independent',
            avatar: this.getRandomAvatar(role),
            preferences: { ...this.preferences }
        };
        
        this.currentUser = customUser;
        this.isLoggedIn = true;
        
        this.saveUserData();
        this.updateUserPanel();
        
        document.getElementById('nasa-login-modal').style.display = 'none';
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                `Profile created successfully! Welcome, ${name}!`,
                'success'
            );
        }
    }

    getRandomAvatar(role) {
        const avatars = {
            'Scientist': ['👩‍🔬', '👨‍🔬', '🔬', '🧪'],
            'Operator': ['👨‍🚀', '👩‍🚀', '🚀', '🛰️'],
            'Researcher': ['🔍', '📊', '📈', '🔬'],
            'Engineer': ['👨‍💻', '👩‍💻', '⚙️', '🔧'],
            'Student': ['👨‍🎓', '👩‍🎓', '📚', '🎓'],
            'Other': ['👤', '🌟', '💫', '🌍']
        };
        
        const roleAvatars = avatars[role] || avatars['Other'];
        return roleAvatars[Math.floor(Math.random() * roleAvatars.length)];
    }

    logout() {
        this.currentUser = null;
        this.isLoggedIn = false;
        this.preferences = {
            theme: 'dark',
            language: 'en',
            dashboardLayout: 'default',
            autoRefresh: true,
            refreshInterval: 30000,
            notifications: {
                enabled: true,
                levels: ['high', 'critical'],
                sounds: true,
                desktop: true
            },
            display: {
                units: 'metric',
                timezone: 'UTC',
                dateFormat: 'ISO',
                animations: true,
                particles: 'medium'
            },
            privacy: {
                analytics: true,
                crashReports: true,
                shareUsage: false
            }
        };
        
        localStorage.removeItem('nasaUser');
        localStorage.removeItem('nasaUserPreferences');
        
        this.updateUserPanel();
        this.applyPreferences();
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification('Logged out successfully', 'info');
        }
    }

    openPreferences() {
        this.populatePreferences();
        document.getElementById('nasa-preferences-modal').style.display = 'flex';
    }

    populatePreferences() {
        const container = document.getElementById('preferences-content');
        if (!container) return;
        
        container.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; color: white;">
                <div>
                    <h3 style="color: #00ff88; margin-bottom: 15px;">Display</h3>
                    
                    <label style="display: block; margin-bottom: 10px;">
                        <span style="display: block; margin-bottom: 5px;">Theme:</span>
                        <select id="pref-theme" style="width: 100%; padding: 5px; background: #333; color: white; border: 1px solid #666;">
                            <option value="dark" ${this.preferences.theme === 'dark' ? 'selected' : ''}>Dark</option>
                            <option value="light" ${this.preferences.theme === 'light' ? 'selected' : ''}>Light</option>
                            <option value="nasa" ${this.preferences.theme === 'nasa' ? 'selected' : ''}>NASA Blue</option>
                        </select>
                    </label>
                    
                    <label style="display: block; margin-bottom: 10px;">
                        <span style="display: block; margin-bottom: 5px;">Units:</span>
                        <select id="pref-units" style="width: 100%; padding: 5px; background: #333; color: white; border: 1px solid #666;">
                            <option value="metric" ${this.preferences.display.units === 'metric' ? 'selected' : ''}>Metric</option>
                            <option value="imperial" ${this.preferences.display.units === 'imperial' ? 'selected' : ''}>Imperial</option>
                        </select>
                    </label>
                    
                    <label style="display: block; margin-bottom: 10px;">
                        <span style="display: block; margin-bottom: 5px;">Particle Quality:</span>
                        <select id="pref-particles" style="width: 100%; padding: 5px; background: #333; color: white; border: 1px solid #666;">
                            <option value="low" ${this.preferences.display.particles === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${this.preferences.display.particles === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${this.preferences.display.particles === 'high' ? 'selected' : ''}>High</option>
                        </select>
                    </label>
                    
                    <label style="display: flex; align-items: center; margin-bottom: 10px; cursor: pointer;">
                        <input type="checkbox" id="pref-animations" ${this.preferences.display.animations ? 'checked' : ''} 
                               style="margin-right: 8px;"> Enable Animations
                    </label>
                </div>
                
                <div>
                    <h3 style="color: #00ff88; margin-bottom: 15px;">Notifications</h3>
                    
                    <label style="display: flex; align-items: center; margin-bottom: 10px; cursor: pointer;">
                        <input type="checkbox" id="pref-notifications" ${this.preferences.notifications.enabled ? 'checked' : ''} 
                               style="margin-right: 8px;"> Enable Notifications
                    </label>
                    
                    <label style="display: flex; align-items: center; margin-bottom: 10px; cursor: pointer;">
                        <input type="checkbox" id="pref-sounds" ${this.preferences.notifications.sounds ? 'checked' : ''} 
                               style="margin-right: 8px;"> Notification Sounds
                    </label>
                    
                    <label style="display: flex; align-items: center; margin-bottom: 15px; cursor: pointer;">
                        <input type="checkbox" id="pref-desktop" ${this.preferences.notifications.desktop ? 'checked' : ''} 
                               style="margin-right: 8px;"> Desktop Notifications
                    </label>
                    
                    <div style="margin-bottom: 15px;">
                        <span style="display: block; margin-bottom: 5px;">Alert Levels:</span>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${['low', 'medium', 'high', 'critical'].map(level => `
                                <label style="display: flex; align-items: center; cursor: pointer;">
                                    <input type="checkbox" value="${level}" class="pref-alert-level" 
                                           ${this.preferences.notifications.levels.includes(level) ? 'checked' : ''}
                                           style="margin-right: 4px;"> ${level}
                                </label>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h3 style="color: #00ff88; margin-bottom: 15px;">Data Refresh</h3>
                
                <label style="display: flex; align-items: center; margin-bottom: 10px; cursor: pointer;">
                    <input type="checkbox" id="pref-auto-refresh" ${this.preferences.autoRefresh ? 'checked' : ''} 
                           style="margin-right: 8px;"> Auto-refresh data
                </label>
                
                <label style="display: block; margin-bottom: 10px;">
                    <span style="display: block; margin-bottom: 5px;">Refresh Interval:</span>
                    <select id="pref-refresh-interval" style="padding: 5px; background: #333; color: white; border: 1px solid #666;">
                        <option value="15000" ${this.preferences.refreshInterval === 15000 ? 'selected' : ''}>15 seconds</option>
                        <option value="30000" ${this.preferences.refreshInterval === 30000 ? 'selected' : ''}>30 seconds</option>
                        <option value="60000" ${this.preferences.refreshInterval === 60000 ? 'selected' : ''}>1 minute</option>
                        <option value="300000" ${this.preferences.refreshInterval === 300000 ? 'selected' : ''}>5 minutes</option>
                    </select>
                </label>
            </div>
        `;
    }

    savePreferences() {
        // Collect all preference values
        this.preferences.theme = document.getElementById('pref-theme').value;
        this.preferences.display.units = document.getElementById('pref-units').value;
        this.preferences.display.particles = document.getElementById('pref-particles').value;
        this.preferences.display.animations = document.getElementById('pref-animations').checked;
        
        this.preferences.notifications.enabled = document.getElementById('pref-notifications').checked;
        this.preferences.notifications.sounds = document.getElementById('pref-sounds').checked;
        this.preferences.notifications.desktop = document.getElementById('pref-desktop').checked;
        
        const alertLevels = Array.from(document.querySelectorAll('.pref-alert-level:checked')).map(cb => cb.value);
        this.preferences.notifications.levels = alertLevels;
        
        this.preferences.autoRefresh = document.getElementById('pref-auto-refresh').checked;
        this.preferences.refreshInterval = parseInt(document.getElementById('pref-refresh-interval').value);
        
        this.saveUserData();
        this.applyPreferences();
        
        document.getElementById('nasa-preferences-modal').style.display = 'none';
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification('Preferences saved successfully!', 'success');
        }
    }

    applyPreferences() {
        // Apply theme
        document.body.className = `theme-${this.preferences.theme}`;
        
        // Apply animation preferences
        if (!this.preferences.display.animations) {
            document.body.style.setProperty('--animation-speed-fast', '0s');
            document.body.style.setProperty('--animation-speed-normal', '0s');
            document.body.style.setProperty('--animation-speed-slow', '0s');
        }
        
        // Update notification system if available
        if (window.nasaNotificationSystem) {
            nasaNotificationSystem.userPreferences = {
                ...nasaNotificationSystem.userPreferences,
                ...this.preferences.notifications
            };
        }
        
        // Trigger preference update event
        const event = new CustomEvent('nasaPreferencesUpdated', {
            detail: { preferences: this.preferences }
        });
        window.dispatchEvent(event);
    }

    saveUserData() {
        if (this.currentUser) {
            localStorage.setItem('nasaUser', JSON.stringify(this.currentUser));
        }
        localStorage.setItem('nasaUserPreferences', JSON.stringify(this.preferences));
    }

    initializePreferences() {
        this.applyPreferences();
        
        // Setup auto-refresh if enabled
        if (this.preferences.autoRefresh) {
            this.setupAutoRefresh();
        }
    }

    setupAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.autoRefreshInterval = setInterval(() => {
            // Trigger data refresh
            if (typeof loadRealNASAData === 'function') {
                loadRealNASAData();
            }
            
            // Refresh WebSocket if available
            if (window.websocketClient && window.websocketClient.reconnect) {
                window.websocketClient.reconnect();
            }
        }, this.preferences.refreshInterval);
    }

    setupEventListeners() {
        // Listen for preference updates from other systems
        window.addEventListener('nasaPreferencesUpdated', (e) => {
            console.log('Preferences updated:', e.detail.preferences);
        });
    }

    // Public API methods
    getCurrentUser() {
        return this.currentUser;
    }

    getPreferences() {
        return this.preferences;
    }

    updatePreference(key, value) {
        // Support nested keys like 'display.units'
        const keys = key.split('.');
        let target = this.preferences;
        
        for (let i = 0; i < keys.length - 1; i++) {
            target = target[keys[i]];
        }
        
        target[keys[keys.length - 1]] = value;
        this.saveUserData();
        this.applyPreferences();
    }

    exportUserData() {
        const data = {
            user: this.currentUser,
            preferences: this.preferences,
            exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nasa-user-data-${this.currentUser?.username || 'guest'}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Initialize user system
let nasaUserSystem;

document.addEventListener('DOMContentLoaded', () => {
    nasaUserSystem = new NASAUserSystem();
});

// Export for global access
window.NASAUserSystem = NASAUserSystem;