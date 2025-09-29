// Export UI Components for Space Weather Dashboards
// Provides export functionality for PDF, CSV, and JSON formats

class SpaceWeatherExporter {
    constructor(apiBaseUrl = 'http://localhost:9001') {
        this.apiBaseUrl = apiBaseUrl;
        this.setupExportUI();
    }
    
    setupExportUI() {
        // Add export styles
        this.addExportStyles();
        
        // Setup export modal if not exists
        this.createExportModal();
        
        // Setup export button if not exists
        this.createExportButton();
    }
    
    addExportStyles() {
        const styleId = 'export-ui-styles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .export-button {
                background: linear-gradient(45deg, #28a745, #20c997);
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
                margin: 5px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                transition: all 0.3s ease;
            }
            
            .export-button:hover {
                background: linear-gradient(45deg, #218838, #1abc9c);
                transform: translateY(-1px);
            }
            
            .export-modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .export-modal-content {
                background: linear-gradient(135deg, #1a1a3a, #2d2d5f);
                margin: 5% auto;
                padding: 20px;
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                color: white;
                border: 2px solid #00bfff;
            }
            
            .export-modal h3 {
                color: #00bfff;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .export-options {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .export-option {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid #00ff88;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .export-option:hover {
                background: rgba(0, 255, 136, 0.2);
                transform: translateY(-2px);
            }
            
            .export-option h4 {
                color: #00ff88;
                margin-bottom: 8px;
            }
            
            .export-option p {
                font-size: 0.8rem;
                color: #ccc;
                margin-bottom: 10px;
            }
            
            .export-option button {
                background: linear-gradient(45deg, #00ff88, #00bfff);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8rem;
            }
            
            .export-settings {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .export-settings label {
                display: block;
                margin-bottom: 8px;
                color: #00bfff;
                font-weight: bold;
            }
            
            .export-settings select {
                width: 100%;
                padding: 8px;
                border: 1px solid #666;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            
            .export-controls {
                display: flex;
                justify-content: space-between;
                gap: 10px;
            }
            
            .export-controls button {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
            }
            
            .cancel-btn {
                background: #6c757d;
                color: white;
            }
            
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .close:hover {
                color: #fff;
            }
            
            .export-status {
                background: rgba(0, 255, 136, 0.1);
                border: 1px solid #00ff88;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
                text-align: center;
                display: none;
            }
            
            .export-status.show {
                display: block;
            }
            
            .export-status.error {
                background: rgba(255, 68, 68, 0.1);
                border-color: #ff4444;
                color: #ff8888;
            }
            
            .export-status.success {
                color: #00ff88;
            }
            
            @media screen and (max-width: 768px) {
                .export-modal-content {
                    margin: 10% auto;
                    width: 95%;
                    padding: 15px;
                }
                
                .export-options {
                    grid-template-columns: 1fr;
                }
                
                .export-controls {
                    flex-direction: column;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    createExportButton() {
        const buttonId = 'main-export-button';
        if (document.getElementById(buttonId)) return;
        
        const button = document.createElement('button');
        button.id = buttonId;
        button.className = 'export-button';
        button.innerHTML = '📊 Export Data';
        button.onclick = () => this.openExportModal();
        
        // Try to add to header or controls area
        const targetSelectors = [
            '.header-status',
            '.status-bar', 
            '.control-panel',
            '.header',
            '.controls'
        ];
        
        for (const selector of targetSelectors) {
            const target = document.querySelector(selector);
            if (target) {
                target.appendChild(button);
                console.log(`Export button added to ${selector}`);
                return;
            }
        }
        
        // Fallback: add to body
        document.body.appendChild(button);
        console.log('Export button added to body as fallback');
    }
    
    createExportModal() {
        const modalId = 'export-modal';
        if (document.getElementById(modalId)) return;
        
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'export-modal';
        
        modal.innerHTML = `
            <div class="export-modal-content">
                <span class="close">&times;</span>
                <h3>📊 Export Space Weather Data</h3>
                
                <div class="export-settings">
                    <label for="export-days">Data Period:</label>
                    <select id="export-days">
                        <option value="1">Last 24 hours</option>
                        <option value="3">Last 3 days</option>
                        <option value="7" selected>Last 7 days</option>
                        <option value="14">Last 14 days</option>
                        <option value="30">Last 30 days</option>
                    </select>
                </div>
                
                <div class="export-options">
                    <div class="export-option" data-format="csv">
                        <h4>📊 CSV Export</h4>
                        <p>Spreadsheet format for data analysis</p>
                        <button onclick="window.spaceWeatherExporter.exportData('csv')">Download CSV</button>
                    </div>
                    
                    <div class="export-option" data-format="json">
                        <h4>🔗 JSON Export</h4>
                        <p>Structured data for developers</p>
                        <button onclick="window.spaceWeatherExporter.exportData('json')">Download JSON</button>
                    </div>
                </div>
                
                <div class="export-status" id="export-status"></div>
                
                <div class="export-controls">
                    <button class="cancel-btn" onclick="window.spaceWeatherExporter.closeExportModal()">Cancel</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup close handlers
        modal.querySelector('.close').onclick = () => this.closeExportModal();
        modal.onclick = (e) => {
            if (e.target === modal) this.closeExportModal();
        };
    }
    
    openExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.style.display = 'block';
            this.clearStatus();
        }
    }
    
    closeExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    showStatus(message, isError = false) {
        const status = document.getElementById('export-status');
        if (status) {
            status.textContent = message;
            status.className = `export-status show ${isError ? 'error' : 'success'}`;
        }
    }
    
    clearStatus() {
        const status = document.getElementById('export-status');
        if (status) {
            status.className = 'export-status';
        }
    }
    
    getDaysBack() {
        const select = document.getElementById('export-days');
        return select ? parseInt(select.value) : 7;
    }
    
    async exportData(format) {
        const days = this.getDaysBack();
        this.showStatus(`Generating ${format.toUpperCase()} export...`);
        
        try {
            if (format === 'csv') {
                // Use export service directly
                const response = await fetch(`${this.apiBaseUrl}/api/v1/export/csv?days=${days}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `space_weather_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showStatus('CSV export downloaded successfully!');
                
            } else if (format === 'json') {
                // Generate JSON export locally using live NASA data
                const exportData = {
                    metadata: {
                        export_timestamp: new Date().toISOString(),
                        data_period: `${days} days`,
                        total_events: window.LIVE_NASA_DATA ? window.LIVE_NASA_DATA.summary.total_events : 0,
                        data_source: 'Live NASA Data + Dashboard Export'
                    },
                    events: window.LIVE_NASA_DATA ? window.LIVE_NASA_DATA.events : [],
                    raw_events: window.LIVE_NASA_DATA ? window.LIVE_NASA_DATA.raw_nasa_data : {}
                };
                
                const jsonStr = JSON.stringify(exportData, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `space_weather_export_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showStatus('JSON export downloaded successfully!');
            }
            
            setTimeout(() => {
                this.closeExportModal();
            }, 2000);
            
        } catch (error) {
            console.error('Export error:', error);
            this.showStatus(`Export failed: ${error.message}`, true);
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Create global exporter instance
    window.spaceWeatherExporter = new SpaceWeatherExporter();
    console.log('Space Weather Exporter initialized');
});

// Export the class for manual initialization
window.SpaceWeatherExporter = SpaceWeatherExporter;