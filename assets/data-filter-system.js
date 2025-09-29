/**
 * NASA Advanced Data Filtering and Search System
 * Powerful data analysis and filtering capabilities
 */

class NASADataFilterSystem {
    constructor() {
        this.filters = {
            dateRange: {
                start: null,
                end: null
            },
            eventTypes: ['CME', 'FLARE', 'SEP', 'GEO_STORM'],
            severity: ['ALL'],
            speed: {
                min: 0,
                max: 10000
            },
            location: {
                latitude: { min: -90, max: 90 },
                longitude: { min: -180, max: 180 }
            },
            classification: ['ALL'],
            source: ['ALL']
        };
        
        this.sortOptions = {
            field: 'time',
            direction: 'desc'
        };
        
        this.searchQuery = '';
        this.filteredData = [];
        this.originalData = [];
        
        this.init();
    }

    init() {
        this.createFilterInterface();
        this.setupEventListeners();
        this.loadInitialData();
        
        console.log('🔍 NASA Data Filter System initialized');
    }

    createFilterInterface() {
        const container = document.createElement('div');
        container.id = 'nasa-filter-system';
        container.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.9);
            display: none;
            z-index: 10002;
            overflow-y: auto;
        `;
        
        container.innerHTML = `
            <div style="max-width: 1400px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9)); 
                            border: 2px solid #00ffff; border-radius: 15px; padding: 30px;">
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                        <h2 style="color: #00ffff; font-family: 'JetBrains Mono', monospace;">
                            🔍 Advanced Data Analysis & Filtering
                        </h2>
                        <button onclick="nasaDataFilterSystem.closeFilterSystem()" 
                                style="background: #ff6666; color: white; border: none; padding: 8px 16px; 
                                       border-radius: 5px; cursor: pointer;">Close</button>
                    </div>
                    
                    <!-- Search Bar -->
                    <div style="margin-bottom: 25px;">
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="data-search-input" placeholder="Search events, IDs, descriptions..." 
                                   style="flex: 1; padding: 12px; background: rgba(0, 0, 0, 0.5); 
                                          border: 1px solid #00ffff; border-radius: 8px; color: white; font-size: 1rem;">
                            <button onclick="nasaDataFilterSystem.performSearch()" 
                                    style="background: #00ffff; color: black; border: none; padding: 12px 20px; 
                                           border-radius: 8px; cursor: pointer; font-weight: 600;">Search</button>
                            <button onclick="nasaDataFilterSystem.clearFilters()" 
                                    style="background: #666; color: white; border: none; padding: 12px 20px; 
                                           border-radius: 8px; cursor: pointer;">Clear</button>
                        </div>
                    </div>
                    
                    <!-- Filter Controls -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 25px;">
                        
                        <!-- Date Range Filter -->
                        <div style="background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 8px;">
                            <h3 style="color: #00ff88; margin-bottom: 10px;">📅 Date Range</h3>
                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                <input type="date" id="filter-date-start" style="padding: 8px; background: #333; color: white; border: 1px solid #666; border-radius: 4px;">
                                <input type="date" id="filter-date-end" style="padding: 8px; background: #333; color: white; border: 1px solid #666; border-radius: 4px;">
                            </div>
                        </div>
                        
                        <!-- Event Types -->
                        <div style="background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 8px;">
                            <h3 style="color: #00ff88; margin-bottom: 10px;">🌀 Event Types</h3>
                            <div style="display: flex; flex-direction: column; gap: 5px;">
                                ${['CME', 'FLARE', 'SEP', 'GEO_STORM'].map(type => `
                                    <label style="display: flex; align-items: center; cursor: pointer;">
                                        <input type="checkbox" value="${type}" class="event-type-filter" checked 
                                               style="margin-right: 8px;"> ${type}
                                    </label>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Speed Range -->
                        <div style="background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 8px;">
                            <h3 style="color: #00ff88; margin-bottom: 10px;">⚡ Speed Range (km/s)</h3>
                            <div style="display: flex; gap: 8px;">
                                <input type="number" id="speed-min" placeholder="Min" value="0" 
                                       style="flex: 1; padding: 8px; background: #333; color: white; border: 1px solid #666; border-radius: 4px;">
                                <input type="number" id="speed-max" placeholder="Max" value="10000" 
                                       style="flex: 1; padding: 8px; background: #333; color: white; border: 1px solid #666; border-radius: 4px;">
                            </div>
                        </div>
                        
                        <!-- Classification -->
                        <div style="background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 8px;">
                            <h3 style="color: #00ff88; margin-bottom: 10px;">📊 Classification</h3>
                            <select id="classification-filter" multiple 
                                    style="width: 100%; padding: 8px; background: #333; color: white; border: 1px solid #666; border-radius: 4px;">
                                <option value="ALL" selected>All Classifications</option>
                                <option value="A">A-Class Flare</option>
                                <option value="B">B-Class Flare</option>
                                <option value="C">C-Class Flare</option>
                                <option value="M">M-Class Flare</option>
                                <option value="X">X-Class Flare</option>
                            </select>
                        </div>
                        
                    </div>
                    
                    <!-- Results Summary -->
                    <div style="background: rgba(0, 60, 40, 0.3); border: 1px solid #00ff88; border-radius: 8px; 
                                padding: 15px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="color: #00ff88; font-weight: 600;">
                                Results: <span id="results-count">0</span> events found
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <select id="sort-field" style="padding: 5px; background: #333; color: white; border: 1px solid #666;">
                                    <option value="time">Sort by Time</option>
                                    <option value="speed">Sort by Speed</option>
                                    <option value="type">Sort by Type</option>
                                </select>
                                <select id="sort-direction" style="padding: 5px; background: #333; color: white; border: 1px solid #666;">
                                    <option value="desc">Newest First</option>
                                    <option value="asc">Oldest First</option>
                                </select>
                                <button onclick="nasaDataFilterSystem.exportResults()" 
                                        style="background: #00ff88; color: black; border: none; padding: 5px 12px; 
                                               border-radius: 4px; cursor: pointer; font-size: 0.9rem;">Export</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Results Table -->
                    <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; overflow: hidden;">
                        <div id="results-table" style="max-height: 400px; overflow-y: auto;"></div>
                    </div>
                    
                    <!-- Analysis Tools -->
                    <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        <button onclick="nasaDataFilterSystem.showStatistics()" 
                                style="background: linear-gradient(135deg, #0066cc, #004499); color: white; 
                                       border: none; padding: 12px; border-radius: 8px; cursor: pointer;">
                            📊 Show Statistics
                        </button>
                        <button onclick="nasaDataFilterSystem.showTimeline()" 
                                style="background: linear-gradient(135deg, #cc6600, #994400); color: white; 
                                       border: none; padding: 12px; border-radius: 8px; cursor: pointer;">
                            📈 Timeline Analysis
                        </button>
                        <button onclick="nasaDataFilterSystem.showCorrelations()" 
                                style="background: linear-gradient(135deg, #6600cc, #440099); color: white; 
                                       border: none; padding: 12px; border-radius: 8px; cursor: pointer;">
                            🔗 Find Correlations
                        </button>
                        <button onclick="nasaDataFilterSystem.showPredictions()" 
                                style="background: linear-gradient(135deg, #cc0066, #990044); color: white; 
                                       border: none; padding: 12px; border-radius: 8px; cursor: pointer;">
                            🔮 AI Predictions
                        </button>
                    </div>
                    
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
    }

    setupEventListeners() {
        // Real-time filtering on input changes
        document.addEventListener('input', (e) => {
            if (e.target.id === 'data-search-input') {
                this.searchQuery = e.target.value;
                this.debounceFilter();
            }
        });
        
        // Filter controls
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('event-type-filter') ||
                e.target.id.startsWith('filter-') ||
                e.target.id.startsWith('speed-') ||
                e.target.id === 'classification-filter' ||
                e.target.id.startsWith('sort-')) {
                this.applyFilters();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                this.openFilterSystem();
            }
            
            if (e.key === 'Escape' && document.getElementById('nasa-filter-system').style.display !== 'none') {
                this.closeFilterSystem();
            }
        });
    }

    loadInitialData() {
        if (window.LIVE_NASA_DATA && window.LIVE_NASA_DATA.events) {
            this.originalData = window.LIVE_NASA_DATA.events;
            this.filteredData = [...this.originalData];
        } else {
            this.originalData = [];
            this.filteredData = [];
        }
    }

    openFilterSystem() {
        this.loadInitialData();
        this.applyFilters();
        document.getElementById('nasa-filter-system').style.display = 'block';
        
        // Focus search input
        setTimeout(() => {
            document.getElementById('data-search-input').focus();
        }, 100);
    }

    closeFilterSystem() {
        document.getElementById('nasa-filter-system').style.display = 'none';
    }

    debounceFilter() {
        clearTimeout(this.filterTimeout);
        this.filterTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }

    performSearch() {
        this.searchQuery = document.getElementById('data-search-input').value;
        this.applyFilters();
    }

    applyFilters() {
        let filtered = [...this.originalData];
        
        // Apply search query
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(event => 
                (event.id && event.id.toLowerCase().includes(query)) ||
                (event.note && event.note.toLowerCase().includes(query)) ||
                (event.type && event.type.toLowerCase().includes(query)) ||
                (event.source && event.source.toLowerCase().includes(query))
            );
        }
        
        // Apply event type filter
        const selectedTypes = Array.from(document.querySelectorAll('.event-type-filter:checked'))
                                    .map(cb => cb.value);
        if (selectedTypes.length > 0) {
            filtered = filtered.filter(event => selectedTypes.includes(event.type));
        }
        
        // Apply date range filter
        const startDate = document.getElementById('filter-date-start')?.value;
        const endDate = document.getElementById('filter-date-end')?.value;
        
        if (startDate) {
            filtered = filtered.filter(event => 
                new Date(event.time) >= new Date(startDate)
            );
        }
        
        if (endDate) {
            filtered = filtered.filter(event => 
                new Date(event.time) <= new Date(endDate + 'T23:59:59')
            );
        }
        
        // Apply speed filter
        const speedMin = parseInt(document.getElementById('speed-min')?.value) || 0;
        const speedMax = parseInt(document.getElementById('speed-max')?.value) || 10000;
        
        filtered = filtered.filter(event => {
            if (event.speed === null || event.speed === undefined) return true;
            return event.speed >= speedMin && event.speed <= speedMax;
        });
        
        // Apply classification filter
        const classificationFilter = document.getElementById('classification-filter');
        if (classificationFilter) {
            const selectedClasses = Array.from(classificationFilter.selectedOptions)
                                          .map(option => option.value);
            
            if (!selectedClasses.includes('ALL')) {
                filtered = filtered.filter(event => {
                    if (event.class_type) {
                        return selectedClasses.some(cls => event.class_type.startsWith(cls));
                    }
                    return true;
                });
            }
        }
        
        // Apply sorting
        const sortField = document.getElementById('sort-field')?.value || 'time';
        const sortDirection = document.getElementById('sort-direction')?.value || 'desc';
        
        filtered.sort((a, b) => {
            let aVal = a[sortField];
            let bVal = b[sortField];
            
            if (sortField === 'time') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }
            
            if (sortDirection === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        this.filteredData = filtered;
        this.updateResults();
    }

    updateResults() {
        // Update count
        const countElement = document.getElementById('results-count');
        if (countElement) {
            countElement.textContent = this.filteredData.length;
        }
        
        // Update table
        this.renderResultsTable();
    }

    renderResultsTable() {
        const tableContainer = document.getElementById('results-table');
        if (!tableContainer) return;
        
        if (this.filteredData.length === 0) {
            tableContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <div style="font-size: 3rem; margin-bottom: 15px;">🔍</div>
                    <div style="font-size: 1.2rem; margin-bottom: 10px;">No events found</div>
                    <div style="font-size: 0.9rem;">Try adjusting your filters or search query</div>
                </div>
            `;
            return;
        }
        
        const table = `
            <table style="width: 100%; border-collapse: collapse; color: white;">
                <thead>
                    <tr style="background: rgba(0, 255, 255, 0.1); border-bottom: 1px solid #00ffff;">
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #333;">Time</th>
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #333;">Type</th>
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #333;">ID</th>
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #333;">Speed</th>
                        <th style="padding: 12px; text-align: left; border-right: 1px solid #333;">Location</th>
                        <th style="padding: 12px; text-align: left;">Details</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.filteredData.slice(0, 100).map(event => `
                        <tr style="border-bottom: 1px solid #333; cursor: pointer;" 
                            onclick="nasaDataFilterSystem.showEventDetails('${event.id}')"
                            onmouseover="this.style.background='rgba(0, 255, 255, 0.05)'"
                            onmouseout="this.style.background='transparent'">
                            <td style="padding: 10px; border-right: 1px solid #333;">
                                ${new Date(event.time).toLocaleString()}
                            </td>
                            <td style="padding: 10px; border-right: 1px solid #333;">
                                <span style="background: ${this.getTypeColor(event.type)}; 
                                             padding: 2px 6px; border-radius: 3px; font-size: 0.8rem;">
                                    ${event.type}
                                </span>
                            </td>
                            <td style="padding: 10px; border-right: 1px solid #333; font-family: monospace; font-size: 0.8rem;">
                                ${event.id.substring(0, 20)}...
                            </td>
                            <td style="padding: 10px; border-right: 1px solid #333;">
                                ${event.speed ? event.speed.toLocaleString() + ' km/s' : 'N/A'}
                            </td>
                            <td style="padding: 10px; border-right: 1px solid #333;">
                                ${event.latitude !== null && event.longitude !== null ? 
                                  `${event.latitude}°, ${event.longitude}°` : 'N/A'}
                            </td>
                            <td style="padding: 10px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                ${event.note ? event.note.substring(0, 50) + '...' : 'No details'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${this.filteredData.length > 100 ? `
                <div style="text-align: center; padding: 15px; color: #666;">
                    Showing first 100 of ${this.filteredData.length} results
                </div>
            ` : ''}
        `;
        
        tableContainer.innerHTML = table;
    }

    getTypeColor(type) {
        const colors = {
            'CME': '#ff6600',
            'FLARE': '#ff0000',
            'SEP': '#ffaa00',
            'GEO_STORM': '#aa00ff'
        };
        return colors[type] || '#666666';
    }

    showEventDetails(eventId) {
        const event = this.filteredData.find(e => e.id === eventId);
        if (!event) return;
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                `Event Details: ${event.type} - ${event.id}`,
                'info',
                { persistent: true }
            );
        }
        
        console.log('Event Details:', event);
    }

    clearFilters() {
        // Reset all filter inputs
        document.getElementById('data-search-input').value = '';
        document.getElementById('filter-date-start').value = '';
        document.getElementById('filter-date-end').value = '';
        document.getElementById('speed-min').value = '0';
        document.getElementById('speed-max').value = '10000';
        
        // Reset checkboxes
        document.querySelectorAll('.event-type-filter').forEach(cb => cb.checked = true);
        
        // Reset selects
        const classSelect = document.getElementById('classification-filter');
        if (classSelect) {
            Array.from(classSelect.options).forEach(option => {
                option.selected = option.value === 'ALL';
            });
        }
        
        this.searchQuery = '';
        this.applyFilters();
    }

    exportResults() {
        const data = {
            query: this.searchQuery,
            filters: this.filters,
            results: this.filteredData,
            exportDate: new Date().toISOString(),
            totalResults: this.filteredData.length
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nasa-filtered-data-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                `Exported ${this.filteredData.length} events to JSON`,
                'success'
            );
        }
    }

    showStatistics() {
        const stats = this.calculateStatistics();
        
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                `Statistics: ${stats.cmeCount} CMEs, ${stats.flareCount} Flares, Avg Speed: ${stats.avgSpeed} km/s`,
                'info',
                { persistent: true }
            );
        }
        
        console.log('Data Statistics:', stats);
    }

    calculateStatistics() {
        const stats = {
            totalEvents: this.filteredData.length,
            cmeCount: this.filteredData.filter(e => e.type === 'CME').length,
            flareCount: this.filteredData.filter(e => e.type === 'FLARE').length,
            sepCount: this.filteredData.filter(e => e.type === 'SEP').length,
            avgSpeed: 0,
            maxSpeed: 0,
            minSpeed: Infinity,
            dateRange: {
                start: null,
                end: null
            }
        };
        
        const eventsWithSpeed = this.filteredData.filter(e => e.speed);
        if (eventsWithSpeed.length > 0) {
            stats.avgSpeed = Math.round(
                eventsWithSpeed.reduce((sum, e) => sum + e.speed, 0) / eventsWithSpeed.length
            );
            stats.maxSpeed = Math.max(...eventsWithSpeed.map(e => e.speed));
            stats.minSpeed = Math.min(...eventsWithSpeed.map(e => e.speed));
        }
        
        if (this.filteredData.length > 0) {
            const dates = this.filteredData.map(e => new Date(e.time)).sort();
            stats.dateRange.start = dates[0];
            stats.dateRange.end = dates[dates.length - 1];
        }
        
        return stats;
    }

    showTimeline() {
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                'Timeline analysis would show event distribution over time',
                'info'
            );
        }
    }

    showCorrelations() {
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                'Correlation analysis would identify patterns between event types',
                'info'
            );
        }
    }

    showPredictions() {
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                'AI predictions would forecast future space weather events',
                'info'
            );
        }
    }

    // Public API
    getFilteredData() {
        return this.filteredData;
    }

    setFilter(filterType, value) {
        this.filters[filterType] = value;
        this.applyFilters();
    }
}

// Initialize data filter system
let nasaDataFilterSystem;

document.addEventListener('DOMContentLoaded', () => {
    nasaDataFilterSystem = new NASADataFilterSystem();
});

// Export for global access
window.NASADataFilterSystem = NASADataFilterSystem;