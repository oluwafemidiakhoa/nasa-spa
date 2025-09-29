/**
 * NASA Space Weather System - Keyboard Shortcuts Controller
 * Advanced keyboard navigation and power user features
 */

class NASAKeyboardController {
    constructor() {
        this.shortcuts = new Map();
        this.isCommandMode = false;
        this.commandBuffer = '';
        this.helpVisible = false;
        
        this.init();
    }

    init() {
        this.registerShortcuts();
        this.createHelpOverlay();
        this.setupEventListeners();
        this.showWelcomeTooltip();
        
        console.log('⌨️ NASA Keyboard Controller initialized - Press Ctrl+? for help');
    }

    registerShortcuts() {
        // Navigation shortcuts
        this.shortcuts.set('Ctrl+1', () => this.navigateTo('expert_dashboard.html', 'Expert Physics Dashboard'));
        this.shortcuts.set('Ctrl+2', () => this.navigateTo('3d_advanced_hub.html', '3D Advanced Systems'));
        this.shortcuts.set('Ctrl+3', () => this.navigateTo('professional_dashboard.html', 'Mission Control'));
        this.shortcuts.set('Ctrl+4', () => this.navigateTo('simple_new.html', 'Ensemble Dashboard'));
        this.shortcuts.set('Ctrl+5', () => this.navigateTo('export_test.html', 'Export & Testing'));

        // 3D System shortcuts
        this.shortcuts.set('Ctrl+Shift+H', () => this.navigateTo('nasa_heliophysics_observatory.html', 'NASA Heliophysics Observatory'));
        this.shortcuts.set('Ctrl+Shift+R', () => this.navigateTo('space_weather_research_center.html', 'Space Weather Research Center'));

        // Dashboard actions
        this.shortcuts.set('Ctrl+R', () => this.refreshData());
        this.shortcuts.set('Ctrl+Shift+R', () => this.hardRefresh());
        this.shortcuts.set('F5', () => this.refreshData());
        
        // Data operations
        this.shortcuts.set('Ctrl+E', () => this.exportData());
        this.shortcuts.set('Ctrl+F', () => this.toggleSearch());
        this.shortcuts.set('Ctrl+D', () => this.toggleDataPanel());
        
        // View controls
        this.shortcuts.set('F11', () => this.toggleFullscreen());
        this.shortcuts.set('Ctrl+Plus', () => this.zoomIn());
        this.shortcuts.set('Ctrl+Minus', () => this.zoomOut());
        this.shortcuts.set('Ctrl+0', () => this.resetZoom());
        
        // Command mode
        this.shortcuts.set('Ctrl+Shift+P', () => this.toggleCommandMode());
        this.shortcuts.set('Escape', () => this.escapeAction());
        
        // Help and info
        this.shortcuts.set('Ctrl+?', () => this.toggleHelp());
        this.shortcuts.set('F1', () => this.toggleHelp());
        this.shortcuts.set('Ctrl+I', () => this.showSystemInfo());
        
        // Quick actions
        this.shortcuts.set('Space', () => this.quickAction());
        this.shortcuts.set('Ctrl+Space', () => this.pauseAnimations());
        
        // Developer shortcuts
        this.shortcuts.set('Ctrl+Shift+D', () => this.toggleDebugMode());
        this.shortcuts.set('Ctrl+Shift+L', () => this.showLogs());
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            const shortcut = this.getShortcutString(e);
            
            // Handle command mode
            if (this.isCommandMode) {
                this.handleCommandMode(e);
                return;
            }
            
            // Skip if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.contentEditable === 'true') {
                return;
            }
            
            if (this.shortcuts.has(shortcut)) {
                e.preventDefault();
                this.shortcuts.get(shortcut)();
                this.showShortcutFeedback(shortcut);
            }
        });

        // Show available shortcuts on certain keys
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && !e.shiftKey && !e.altKey) {
                this.showQuickHints();
            }
        });

        document.addEventListener('keyup', (e) => {
            this.hideQuickHints();
        });
    }

    getShortcutString(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('Ctrl');
        if (e.shiftKey) parts.push('Shift');
        if (e.altKey) parts.push('Alt');
        
        const key = e.key === ' ' ? 'Space' : 
                    e.key === '+' ? 'Plus' :
                    e.key === '-' ? 'Minus' :
                    e.key === '?' ? '?' :
                    e.key;
        
        parts.push(key);
        return parts.join('+');
    }

    navigateTo(url, description) {
        this.showNotification(`Navigating to ${description}...`, 'info');
        
        // Use smooth transition if available
        if (window.nasaAnimationController) {
            nasaAnimationController.transitionToPage(url);
        } else {
            window.open(url, '_blank');
        }
    }

    refreshData() {
        this.showNotification('Refreshing NASA data streams...', 'info');
        
        // Trigger data refresh if function exists
        if (typeof loadRealNASAData === 'function') {
            loadRealNASAData();
        }
        
        // Refresh WebSocket connection if available
        if (window.websocketClient && window.websocketClient.reconnect) {
            window.websocketClient.reconnect();
        }
        
        setTimeout(() => {
            this.showNotification('Data refresh complete!', 'success');
        }, 2000);
    }

    hardRefresh() {
        this.showNotification('Performing hard refresh...', 'info');
        setTimeout(() => {
            window.location.reload(true);
        }, 1000);
    }

    exportData() {
        this.showNotification('Initiating data export...', 'info');
        
        // Check if we're on a page with export functionality
        if (typeof exportToCSV === 'function') {
            exportToCSV();
        } else if (typeof exportData === 'function') {
            exportData();
        } else {
            // Navigate to export page
            this.navigateTo('export_test.html', 'Export & Testing');
        }
    }

    toggleSearch() {
        // Create or toggle search overlay
        let searchOverlay = document.getElementById('nasa-search-overlay');
        
        if (!searchOverlay) {
            searchOverlay = this.createSearchOverlay();
        }
        
        if (searchOverlay.style.display === 'none' || !searchOverlay.style.display) {
            searchOverlay.style.display = 'flex';
            searchOverlay.querySelector('input').focus();
        } else {
            searchOverlay.style.display = 'none';
        }
    }

    createSearchOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'nasa-search-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;
        
        overlay.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9)); 
                        border: 2px solid #00ffff; border-radius: 15px; padding: 30px; width: 500px;">
                <h3 style="color: #00ffff; margin-bottom: 20px; text-align: center;">🔍 NASA System Search</h3>
                <input type="text" placeholder="Search dashboards, features, or data..." 
                       style="width: 100%; padding: 15px; background: rgba(0, 0, 0, 0.5); 
                              border: 1px solid #00ffff; border-radius: 8px; color: white; font-size: 1rem;"
                       id="nasa-search-input">
                <div id="search-results" style="margin-top: 15px; max-height: 300px; overflow-y: auto;"></div>
                <div style="margin-top: 15px; text-align: center; color: #888; font-size: 0.9rem;">
                    Press Escape to close
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Add search functionality
        const searchInput = overlay.querySelector('#nasa-search-input');
        const resultsDiv = overlay.querySelector('#search-results');
        
        searchInput.addEventListener('input', (e) => {
            this.performSearch(e.target.value, resultsDiv);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.style.display = 'none';
            }
        });
        
        return overlay;
    }

    performSearch(query, resultsDiv) {
        if (!query) {
            resultsDiv.innerHTML = '';
            return;
        }

        const searchableItems = [
            { name: 'Expert Physics Dashboard', url: 'expert_dashboard.html', description: 'Advanced physics models and calculations' },
            { name: 'NASA Heliophysics Observatory', url: 'nasa_heliophysics_observatory.html', description: '3D space weather visualization' },
            { name: 'Space Weather Research Center', url: 'space_weather_research_center.html', description: 'Research-grade analysis tools' },
            { name: 'Mission Control', url: 'professional_dashboard.html', description: 'Professional mission control interface' },
            { name: 'Ensemble Dashboard', url: 'simple_new.html', description: 'AI ensemble forecasting' },
            { name: 'Export Tools', url: 'export_test.html', description: 'Data export and testing' },
            { name: '3D Advanced Hub', url: '3d_advanced_hub.html', description: 'Advanced 3D visualization systems' }
        ];

        const results = searchableItems.filter(item => 
            item.name.toLowerCase().includes(query.toLowerCase()) ||
            item.description.toLowerCase().includes(query.toLowerCase())
        );

        resultsDiv.innerHTML = results.map(item => `
            <div style="padding: 10px; border: 1px solid #333; border-radius: 5px; margin: 5px 0; 
                        cursor: pointer; transition: background 0.3s ease;" 
                 onclick="window.open('${item.url}', '_blank')" 
                 onmouseover="this.style.background='rgba(0, 255, 255, 0.1)'"
                 onmouseout="this.style.background='transparent'">
                <div style="color: #00ffff; font-weight: bold;">${item.name}</div>
                <div style="color: #ccc; font-size: 0.9rem;">${item.description}</div>
            </div>
        `).join('');
    }

    toggleDataPanel() {
        const dataPanels = document.querySelectorAll('#data-panel, .data-panel, .research-data');
        dataPanels.forEach(panel => {
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                this.showNotification('Data panel shown', 'info');
            } else {
                panel.style.display = 'none';
                this.showNotification('Data panel hidden', 'info');
            }
        });
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            this.showNotification('Entered fullscreen mode', 'info');
        } else {
            document.exitFullscreen();
            this.showNotification('Exited fullscreen mode', 'info');
        }
    }

    zoomIn() {
        document.body.style.zoom = (parseFloat(document.body.style.zoom || 1) + 0.1).toString();
        this.showNotification('Zoomed in', 'info');
    }

    zoomOut() {
        document.body.style.zoom = Math.max(0.5, parseFloat(document.body.style.zoom || 1) - 0.1).toString();
        this.showNotification('Zoomed out', 'info');
    }

    resetZoom() {
        document.body.style.zoom = '1';
        this.showNotification('Zoom reset', 'info');
    }

    toggleCommandMode() {
        this.isCommandMode = !this.isCommandMode;
        
        if (this.isCommandMode) {
            this.showCommandPrompt();
        } else {
            this.hideCommandPrompt();
        }
    }

    showCommandPrompt() {
        let prompt = document.getElementById('nasa-command-prompt');
        if (!prompt) {
            prompt = document.createElement('div');
            prompt.id = 'nasa-command-prompt';
            prompt.style.cssText = `
                position: fixed;
                bottom: 50px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9));
                border: 2px solid #00ffff;
                border-radius: 10px;
                padding: 15px;
                font-family: 'JetBrains Mono', monospace;
                color: #00ffff;
                z-index: 10000;
                min-width: 400px;
                text-align: center;
            `;
            document.body.appendChild(prompt);
        }
        
        prompt.innerHTML = `
            <div style="margin-bottom: 10px;">Command Mode Active</div>
            <div style="color: white;">> <span id="command-buffer"></span><span style="animation: blink 1s infinite;">|</span></div>
            <div style="font-size: 0.8rem; color: #888; margin-top: 10px;">
                Type: refresh, export, nav:dashboard, help, or press Escape
            </div>
        `;
        prompt.style.display = 'block';
    }

    hideCommandPrompt() {
        const prompt = document.getElementById('nasa-command-prompt');
        if (prompt) {
            prompt.style.display = 'none';
        }
        this.commandBuffer = '';
    }

    handleCommandMode(e) {
        if (e.key === 'Escape') {
            this.toggleCommandMode();
            return;
        }
        
        if (e.key === 'Enter') {
            this.executeCommand(this.commandBuffer);
            this.commandBuffer = '';
            this.toggleCommandMode();
            return;
        }
        
        if (e.key === 'Backspace') {
            this.commandBuffer = this.commandBuffer.slice(0, -1);
        } else if (e.key.length === 1) {
            this.commandBuffer += e.key;
        }
        
        const bufferElement = document.getElementById('command-buffer');
        if (bufferElement) {
            bufferElement.textContent = this.commandBuffer;
        }
    }

    executeCommand(command) {
        const cmd = command.toLowerCase().trim();
        
        if (cmd === 'refresh') {
            this.refreshData();
        } else if (cmd === 'export') {
            this.exportData();
        } else if (cmd.startsWith('nav:')) {
            const page = cmd.substring(4);
            this.navigateByCommand(page);
        } else if (cmd === 'help') {
            this.toggleHelp();
        } else if (cmd === 'fullscreen') {
            this.toggleFullscreen();
        } else if (cmd === 'debug') {
            this.toggleDebugMode();
        } else {
            this.showNotification(`Unknown command: ${command}`, 'error');
        }
    }

    navigateByCommand(page) {
        const pageMap = {
            'dashboard': 'dashboard_hub.html',
            'expert': 'expert_dashboard.html',
            '3d': '3d_advanced_hub.html',
            'mission': 'professional_dashboard.html',
            'ensemble': 'simple_new.html',
            'export': 'export_test.html'
        };
        
        if (pageMap[page]) {
            this.navigateTo(pageMap[page], page);
        } else {
            this.showNotification(`Unknown page: ${page}`, 'error');
        }
    }

    escapeAction() {
        // Close any open overlays
        if (this.isCommandMode) {
            this.toggleCommandMode();
        } else if (this.helpVisible) {
            this.toggleHelp();
        } else {
            const searchOverlay = document.getElementById('nasa-search-overlay');
            if (searchOverlay && searchOverlay.style.display !== 'none') {
                searchOverlay.style.display = 'none';
            }
        }
    }

    toggleHelp() {
        this.helpVisible = !this.helpVisible;
        let helpOverlay = document.getElementById('nasa-help-overlay');
        
        if (this.helpVisible) {
            helpOverlay.style.display = 'flex';
        } else {
            helpOverlay.style.display = 'none';
        }
    }

    createHelpOverlay() {
        const helpOverlay = document.createElement('div');
        helpOverlay.id = 'nasa-help-overlay';
        helpOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.9);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 10001;
        `;
        
        helpOverlay.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9)); 
                        border: 2px solid #00ffff; border-radius: 15px; padding: 30px; max-width: 800px; 
                        max-height: 80vh; overflow-y: auto;">
                <h2 style="color: #00ffff; text-align: center; margin-bottom: 25px;">🚀 NASA Keyboard Shortcuts</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; color: white;">
                    <div>
                        <h3 style="color: #00ff88; margin-bottom: 15px;">Navigation</h3>
                        <div class="shortcut-item">Ctrl+1 - Expert Physics</div>
                        <div class="shortcut-item">Ctrl+2 - 3D Advanced</div>
                        <div class="shortcut-item">Ctrl+3 - Mission Control</div>
                        <div class="shortcut-item">Ctrl+4 - Ensemble</div>
                        <div class="shortcut-item">Ctrl+5 - Export Tools</div>
                        
                        <h3 style="color: #00ff88; margin: 20px 0 15px 0;">3D Systems</h3>
                        <div class="shortcut-item">Ctrl+Shift+H - Heliophysics</div>
                        <div class="shortcut-item">Ctrl+Shift+R - Research Center</div>
                    </div>
                    
                    <div>
                        <h3 style="color: #00ff88; margin-bottom: 15px;">Actions</h3>
                        <div class="shortcut-item">Ctrl+R / F5 - Refresh Data</div>
                        <div class="shortcut-item">Ctrl+E - Export Data</div>
                        <div class="shortcut-item">Ctrl+F - Search</div>
                        <div class="shortcut-item">F11 - Fullscreen</div>
                        <div class="shortcut-item">Ctrl+? / F1 - Help</div>
                        
                        <h3 style="color: #00ff88; margin: 20px 0 15px 0;">Advanced</h3>
                        <div class="shortcut-item">Ctrl+Shift+P - Command Mode</div>
                        <div class="shortcut-item">Ctrl+Space - Pause Animations</div>
                        <div class="shortcut-item">Escape - Close Overlays</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 25px;">
                    <button onclick="document.getElementById('nasa-help-overlay').style.display='none'" 
                            style="background: #00ffff; color: black; border: none; padding: 10px 20px; 
                                   border-radius: 5px; cursor: pointer; font-weight: bold;">
                        Close (Escape)
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpOverlay);
        
        // Add CSS for shortcut items
        const style = document.createElement('style');
        style.textContent = `
            .shortcut-item {
                padding: 5px 0;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.9rem;
            }
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    showSystemInfo() {
        const info = {
            userAgent: navigator.userAgent,
            memory: navigator.deviceMemory || 'Unknown',
            cores: navigator.hardwareConcurrency || 'Unknown',
            connection: navigator.connection?.effectiveType || 'Unknown',
            online: navigator.onLine
        };
        
        this.showNotification(`System: ${info.cores} cores, ${info.memory}GB RAM, ${info.connection} connection`, 'info', 6000);
    }

    quickAction() {
        // Context-sensitive quick action
        if (document.title.includes('3D')) {
            // In 3D view - toggle animation
            if (typeof toggleAnimation === 'function') {
                toggleAnimation();
                this.showNotification('Animation toggled', 'info');
            }
        } else {
            // In dashboard - refresh data
            this.refreshData();
        }
    }

    pauseAnimations() {
        const animatedElements = document.querySelectorAll('[style*="animation"]');
        animatedElements.forEach(el => {
            if (el.style.animationPlayState === 'paused') {
                el.style.animationPlayState = 'running';
            } else {
                el.style.animationPlayState = 'paused';
            }
        });
        
        this.showNotification('Animations toggled', 'info');
    }

    toggleDebugMode() {
        document.body.classList.toggle('debug-mode');
        const isDebug = document.body.classList.contains('debug-mode');
        
        if (isDebug) {
            console.log('🔧 Debug mode enabled');
            this.showNotification('Debug mode enabled', 'info');
        } else {
            this.showNotification('Debug mode disabled', 'info');
        }
    }

    showLogs() {
        // Open browser console
        this.showNotification('Check browser console for detailed logs', 'info');
        console.log('📊 NASA System Logs:', {
            shortcuts: Array.from(this.shortcuts.keys()),
            commandMode: this.isCommandMode,
            helpVisible: this.helpVisible
        });
    }

    showShortcutFeedback(shortcut) {
        // Brief visual feedback for shortcuts
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 255, 255, 0.9);
            color: black;
            padding: 8px 16px;
            border-radius: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: bold;
            z-index: 10002;
            pointer-events: none;
        `;
        feedback.textContent = shortcut;
        
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            feedback.style.opacity = '0';
            feedback.style.transform = 'translateX(-50%) translateY(-20px)';
            feedback.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }, 1000);
    }

    showQuickHints() {
        // Show number hints on dashboard cards
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach((card, index) => {
            if (index < 5) {
                let hint = card.querySelector('.keyboard-hint');
                if (!hint) {
                    hint = document.createElement('div');
                    hint.className = 'keyboard-hint';
                    hint.style.cssText = `
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background: rgba(0, 255, 255, 0.9);
                        color: black;
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 0.8rem;
                        z-index: 100;
                    `;
                    hint.textContent = index + 1;
                    card.style.position = 'relative';
                    card.appendChild(hint);
                }
                hint.style.display = 'flex';
            }
        });
    }

    hideQuickHints() {
        const hints = document.querySelectorAll('.keyboard-hint');
        hints.forEach(hint => {
            hint.style.display = 'none';
        });
    }

    showWelcomeTooltip() {
        setTimeout(() => {
            this.showNotification('💡 Press Ctrl+? for keyboard shortcuts', 'info', 5000);
        }, 3000);
    }

    showNotification(message, type = 'info', duration = 3000) {
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(message, type, duration);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Initialize keyboard controller
let nasaKeyboardController;

document.addEventListener('DOMContentLoaded', () => {
    nasaKeyboardController = new NASAKeyboardController();
});

// Export for global access
window.NASAKeyboardController = NASAKeyboardController;