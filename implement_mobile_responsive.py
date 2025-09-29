#!/usr/bin/env python3
"""
Implement mobile-responsive design for NASA Space Weather dashboards
"""

import os
import re
from datetime import datetime

def analyze_current_dashboards():
    """Analyze current dashboards for mobile responsiveness"""
    print("=" * 60)
    print("ANALYZING CURRENT DASHBOARDS FOR MOBILE RESPONSIVENESS")
    print("=" * 60)
    
    dashboards = ['3d_dashboard.html', 'simple_new.html', 'professional_dashboard.html']
    analysis = {}
    
    for dashboard in dashboards:
        if os.path.exists(dashboard):
            with open(dashboard, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis[dashboard] = {
                'has_viewport_meta': 'viewport' in content,
                'has_media_queries': '@media' in content,
                'has_flex_grid': 'display: flex' in content or 'display: grid' in content,
                'has_responsive_units': 'vw' in content or 'vh' in content or '%' in content,
                'size_kb': len(content) / 1024
            }
            
            print(f"\n{dashboard}:")
            print(f"  Size: {analysis[dashboard]['size_kb']:.1f} KB")
            print(f"  Viewport meta: {'YES' if analysis[dashboard]['has_viewport_meta'] else 'NO'}")
            print(f"  Media queries: {'YES' if analysis[dashboard]['has_media_queries'] else 'NO'}")
            print(f"  Flexible layout: {'YES' if analysis[dashboard]['has_flex_grid'] else 'NO'}")
            print(f"  Responsive units: {'YES' if analysis[dashboard]['has_responsive_units'] else 'NO'}")
        else:
            print(f"\n{dashboard}: FILE NOT FOUND")
            analysis[dashboard] = None
    
    return analysis

def create_mobile_responsive_3d_dashboard():
    """Create mobile-responsive version of 3D dashboard"""
    print("\n" + "=" * 60)
    print("CREATING MOBILE-RESPONSIVE 3D DASHBOARD")
    print("=" * 60)
    
    try:
        # Read current 3D dashboard
        with open('3d_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add/update viewport meta tag
        if '<meta name="viewport"' not in content:
            head_section = content.find('<head>')
            if head_section != -1:
                insert_pos = content.find('>', head_section) + 1
                viewport_meta = '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">'
                content = content[:insert_pos] + viewport_meta + content[insert_pos:]
        
        # Add mobile-responsive CSS
        mobile_css = '''
        
        /* Mobile-Responsive Design */
        @media screen and (max-width: 768px) {
            .dashboard-container {
                grid-template-areas: 
                    "header header header"
                    "controls controls controls"
                    "canvas canvas canvas"
                    "timeline timeline timeline";
                grid-template-columns: 1fr;
                grid-template-rows: auto auto 1fr auto;
                gap: 10px;
                padding: 10px;
            }
            
            .controls-panel {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                max-height: none;
                overflow: visible;
            }
            
            .control-group {
                margin-bottom: 15px;
            }
            
            .control-group h3 {
                font-size: 1rem;
                margin-bottom: 8px;
            }
            
            .control-row {
                flex-direction: column;
                gap: 8px;
            }
            
            .control-row button {
                width: 100%;
                padding: 12px;
                font-size: 0.9rem;
            }
            
            .timeline {
                padding: 10px;
            }
            
            .timeline-track {
                height: 40px;
            }
            
            .timeline-event {
                width: 8px;
                height: 8px;
            }
            
            #timeline-events {
                max-height: 100px;
                font-size: 0.8rem;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
            
            .header .subtitle {
                font-size: 0.9rem;
            }
        }
        
        @media screen and (max-width: 480px) {
            .dashboard-container {
                padding: 5px;
                gap: 5px;
            }
            
            .controls-panel {
                grid-template-columns: 1fr;
            }
            
            .control-row button {
                padding: 10px;
                font-size: 0.8rem;
            }
            
            .header h1 {
                font-size: 1.2rem;
            }
            
            .timeline {
                padding: 8px;
            }
            
            #timeline-events {
                font-size: 0.7rem;
            }
        }
        
        /* Touch-friendly controls */
        @media (hover: none) and (pointer: coarse) {
            .control-row button {
                min-height: 44px;
                font-size: 1rem;
            }
            
            .timeline-event {
                width: 12px;
                height: 12px;
            }
            
            .timeline-event-list {
                padding: 12px;
                margin-bottom: 8px;
            }
        }
        '''
        
        # Insert mobile CSS before closing </style> tag
        style_end = content.find('</style>')
        if style_end != -1:
            content = content[:style_end] + mobile_css + content[style_end:]
        
        # Make canvas container responsive
        canvas_js_fix = '''
        
        // Mobile-responsive canvas resizing
        function handleResize() {
            if (renderer && camera) {
                const container = renderer.domElement.parentElement;
                const width = container.clientWidth;
                const height = container.clientHeight;
                
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
                
                console.log(`Canvas resized to ${width}x${height}`);
            }
        }
        
        // Add resize listener
        window.addEventListener('resize', handleResize);
        window.addEventListener('orientationchange', () => {
            setTimeout(handleResize, 100);
        });
        '''
        
        # Insert before closing script tag
        script_end = content.rfind('</script>')
        if script_end != -1:
            content = content[:script_end] + canvas_js_fix + content[script_end:]
        
        # Save mobile-responsive version
        with open('3d_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: 3D dashboard updated with mobile-responsive design")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update 3D dashboard: {e}")
        return False

def create_mobile_responsive_ensemble_dashboard():
    """Create mobile-responsive version of ensemble dashboard"""
    print("\n" + "=" * 60)
    print("CREATING MOBILE-RESPONSIVE ENSEMBLE DASHBOARD")
    print("=" * 60)
    
    try:
        # Read current ensemble dashboard
        with open('simple_new.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add/update viewport meta tag
        if '<meta name="viewport"' not in content:
            head_section = content.find('<head>')
            if head_section != -1:
                insert_pos = content.find('>', head_section) + 1
                viewport_meta = '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
                content = content[:insert_pos] + viewport_meta + content[insert_pos:]
        
        # Add mobile-responsive CSS
        mobile_css = '''
        
        /* Mobile-Responsive Design */
        @media screen and (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .panel {
                padding: 15px;
            }
            
            .panel h3 {
                font-size: 1.1rem;
                margin-bottom: 10px;
            }
            
            .forecast-content {
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
            
            .header .subtitle {
                font-size: 1rem;
            }
            
            .confidence-meter {
                height: 15px;
            }
            
            .risk-badge {
                padding: 6px 12px;
                font-size: 0.9rem;
            }
            
            .refresh-button {
                padding: 12px 20px;
                font-size: 1rem;
                width: 100%;
                margin-top: 15px;
            }
        }
        
        @media screen and (max-width: 480px) {
            .container {
                padding: 8px;
            }
            
            .header {
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
            
            .header .subtitle {
                font-size: 0.9rem;
            }
            
            .panel {
                padding: 12px;
            }
            
            .panel h3 {
                font-size: 1rem;
            }
            
            .forecast-content {
                font-size: 0.8rem;
            }
            
            .dashboard-grid {
                gap: 12px;
            }
        }
        
        /* Touch-friendly controls */
        @media (hover: none) and (pointer: coarse) {
            .refresh-button {
                min-height: 44px;
                font-size: 1.1rem;
            }
            
            .panel {
                cursor: pointer;
            }
            
            .panel:active {
                transform: scale(0.98);
                transition: transform 0.1s ease;
            }
        }
        
        /* Landscape orientation for mobile */
        @media screen and (max-width: 768px) and (orientation: landscape) {
            .dashboard-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .header h1 {
                font-size: 1.3rem;
            }
        }
        '''
        
        # Insert mobile CSS before closing </style> tag
        style_end = content.find('</style>')
        if style_end != -1:
            content = content[:style_end] + mobile_css + content[style_end:]
        
        # Save mobile-responsive version
        with open('simple_new.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: Ensemble dashboard updated with mobile-responsive design")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update ensemble dashboard: {e}")
        return False

def create_mobile_responsive_professional_dashboard():
    """Create mobile-responsive version of professional dashboard"""
    print("\n" + "=" * 60)
    print("CREATING MOBILE-RESPONSIVE PROFESSIONAL DASHBOARD")
    print("=" * 60)
    
    try:
        # Read current professional dashboard
        with open('professional_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add/update viewport meta tag
        if '<meta name="viewport"' not in content:
            head_section = content.find('<head>')
            if head_section != -1:
                insert_pos = content.find('>', head_section) + 1
                viewport_meta = '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
                content = content[:insert_pos] + viewport_meta + content[insert_pos:]
        
        # Add mobile-responsive CSS
        mobile_css = '''
        
        /* Mobile-Responsive Design */
        @media screen and (max-width: 768px) {
            .dashboard-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto 1fr auto;
                grid-template-areas:
                    "header"
                    "controls"
                    "main"
                    "footer";
                gap: 10px;
                padding: 10px;
            }
            
            .forecast-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .forecast-card {
                padding: 15px;
            }
            
            .forecast-card h3 {
                font-size: 1.1rem;
            }
            
            .forecast-details {
                font-size: 0.9rem;
            }
            
            .control-panel {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                padding: 15px;
            }
            
            .control-group {
                margin-bottom: 10px;
            }
            
            .control-group button {
                width: 100%;
                padding: 12px;
                font-size: 0.9rem;
            }
            
            .header h1 {
                font-size: 1.6rem;
            }
            
            .status-bar {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            
            .status-item {
                margin: 0;
            }
        }
        
        @media screen and (max-width: 480px) {
            .dashboard-container {
                padding: 8px;
                gap: 8px;
            }
            
            .control-panel {
                grid-template-columns: 1fr;
                padding: 12px;
            }
            
            .forecast-card {
                padding: 12px;
            }
            
            .forecast-card h3 {
                font-size: 1rem;
            }
            
            .forecast-details {
                font-size: 0.8rem;
            }
            
            .header h1 {
                font-size: 1.4rem;
            }
            
            .header p {
                font-size: 0.9rem;
            }
        }
        
        /* Touch-friendly controls */
        @media (hover: none) and (pointer: coarse) {
            .control-group button {
                min-height: 44px;
                font-size: 1rem;
            }
            
            .forecast-card {
                cursor: pointer;
            }
            
            .forecast-card:active {
                transform: scale(0.98);
                transition: transform 0.1s ease;
            }
        }
        '''
        
        # Insert mobile CSS before closing </style> tag
        style_end = content.find('</style>')
        if style_end != -1:
            content = content[:style_end] + mobile_css + content[style_end:]
        
        # Save mobile-responsive version
        with open('professional_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("SUCCESS: Professional dashboard updated with mobile-responsive design")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update professional dashboard: {e}")
        return False

def create_mobile_test_page():
    """Create a test page for mobile responsiveness"""
    print("\n" + "=" * 60)
    print("CREATING MOBILE RESPONSIVENESS TEST PAGE")
    print("=" * 60)
    
    test_page_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NASA Space Weather - Mobile Test</title>
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
            max-width: 1200px;
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
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .test-card {
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        
        .test-card h3 {
            color: #00ff88;
            margin-bottom: 15px;
        }
        
        .test-link {
            display: inline-block;
            background: linear-gradient(45deg, #00bfff, #0080ff);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: transform 0.3s ease;
        }
        
        .test-link:hover {
            transform: scale(1.05);
        }
        
        .device-info {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #ffff00;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .device-info h3 {
            color: #ffff00;
            margin-bottom: 15px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .info-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 5px;
        }
        
        @media screen and (max-width: 768px) {
            .test-grid {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
        }
        
        @media screen and (max-width: 480px) {
            .test-card {
                padding: 15px;
            }
            
            .test-link {
                padding: 10px 20px;
                margin: 5px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 NASA Space Weather Mobile Test</h1>
            <p>Test all dashboards on mobile devices</p>
        </div>
        
        <div class="test-grid">
            <div class="test-card">
                <h3>🌌 3D Space Weather</h3>
                <p>Interactive 3D visualization with CME tracking</p>
                <a href="3d_dashboard.html" class="test-link">Test 3D Dashboard</a>
            </div>
            
            <div class="test-card">
                <h3>📊 Ensemble Forecast</h3>
                <p>AI-powered space weather predictions</p>
                <a href="simple_new.html" class="test-link">Test Ensemble Dashboard</a>
            </div>
            
            <div class="test-card">
                <h3>📈 Professional Analysis</h3>
                <p>Detailed space weather analysis tools</p>
                <a href="professional_dashboard.html" class="test-link">Test Professional Dashboard</a>
            </div>
        </div>
        
        <div class="device-info">
            <h3>📱 Device Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Screen Width:</strong>
                    <span id="screen-width">-</span>px
                </div>
                <div class="info-item">
                    <strong>Screen Height:</strong>
                    <span id="screen-height">-</span>px
                </div>
                <div class="info-item">
                    <strong>Device Pixel Ratio:</strong>
                    <span id="pixel-ratio">-</span>
                </div>
                <div class="info-item">
                    <strong>Orientation:</strong>
                    <span id="orientation">-</span>
                </div>
                <div class="info-item">
                    <strong>Touch Support:</strong>
                    <span id="touch-support">-</span>
                </div>
                <div class="info-item">
                    <strong>User Agent:</strong>
                    <span id="user-agent" style="font-size: 0.8rem;">-</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function updateDeviceInfo() {
            document.getElementById('screen-width').textContent = window.innerWidth;
            document.getElementById('screen-height').textContent = window.innerHeight;
            document.getElementById('pixel-ratio').textContent = window.devicePixelRatio || 1;
            document.getElementById('orientation').textContent = 
                window.innerWidth > window.innerHeight ? 'Landscape' : 'Portrait';
            document.getElementById('touch-support').textContent = 
                'ontouchstart' in window ? 'Yes' : 'No';
            document.getElementById('user-agent').textContent = 
                navigator.userAgent.substring(0, 100) + '...';
        }
        
        // Update on load and resize
        updateDeviceInfo();
        window.addEventListener('resize', updateDeviceInfo);
        window.addEventListener('orientationchange', () => {
            setTimeout(updateDeviceInfo, 100);
        });
        
        console.log('Mobile test page loaded successfully');
    </script>
</body>
</html>'''
    
    try:
        with open('mobile_test.html', 'w', encoding='utf-8') as f:
            f.write(test_page_content)
        
        print("SUCCESS: Mobile test page created as mobile_test.html")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create mobile test page: {e}")
        return False

def verify_mobile_responsiveness():
    """Verify that all dashboards are now mobile-responsive"""
    print("\n" + "=" * 60)
    print("VERIFYING MOBILE RESPONSIVENESS")
    print("=" * 60)
    
    dashboards = ['3d_dashboard.html', 'simple_new.html', 'professional_dashboard.html']
    responsive_features = {
        'viewport_meta': 'viewport',
        'media_queries': '@media',
        'touch_friendly': 'pointer: coarse',
        'orientation_change': 'orientationchange',
        'responsive_grid': 'grid-template-columns: 1fr'
    }
    
    all_responsive = True
    
    for dashboard in dashboards:
        if os.path.exists(dashboard):
            with open(dashboard, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n{dashboard}:")
            dashboard_responsive = True
            
            for feature, pattern in responsive_features.items():
                if pattern in content:
                    print(f"  ✓ {feature.replace('_', ' ').title()}")
                else:
                    print(f"  ✗ {feature.replace('_', ' ').title()}")
                    dashboard_responsive = False
            
            if dashboard_responsive:
                print(f"  STATUS: MOBILE-RESPONSIVE")
            else:
                print(f"  STATUS: NEEDS ATTENTION")
                all_responsive = False
        else:
            print(f"\n{dashboard}: FILE NOT FOUND")
            all_responsive = False
    
    return all_responsive

def main():
    """Main mobile responsiveness implementation"""
    print("NASA Space Weather Dashboard - Mobile-Responsive Design Implementation")
    print(f"Starting mobile optimization: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Analyze current state
    analysis = analyze_current_dashboards()
    
    # Step 2: Update each dashboard
    results = {}
    results['3d'] = create_mobile_responsive_3d_dashboard()
    results['ensemble'] = create_mobile_responsive_ensemble_dashboard()
    results['professional'] = create_mobile_responsive_professional_dashboard()
    
    # Step 3: Create mobile test page
    results['test_page'] = create_mobile_test_page()
    
    # Step 4: Verify implementation
    all_responsive = verify_mobile_responsiveness()
    
    # Step 5: Summary
    print("\n" + "=" * 60)
    print("MOBILE-RESPONSIVE IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    successful_updates = sum(1 for result in results.values() if result)
    
    if all_responsive and successful_updates == len(results):
        print("STATUS: ✓ MOBILE-RESPONSIVE DESIGN COMPLETE")
        print()
        print("🎯 Successfully implemented:")
        print("   • Responsive viewport meta tags")
        print("   • Mobile-first CSS media queries")
        print("   • Touch-friendly controls (44px minimum)")
        print("   • Flexible grid layouts")
        print("   • Orientation change handling")
        print("   • Canvas resizing for 3D dashboard")
        print()
        print("📱 Mobile features added:")
        print("   • Single-column layout on phones")
        print("   • Touch-optimized button sizes")
        print("   • Readable font sizes on small screens")
        print("   • Landscape orientation support")
        print("   • Responsive timeline and controls")
        print()
        print("🧪 Testing:")
        print("   • Open mobile_test.html to test all dashboards")
        print("   • Test on various device sizes")
        print("   • Check portrait and landscape orientations")
        print()
        print("✅ Task 4 (Mobile-Responsive Design) COMPLETE")
        print("🚀 Ready to proceed to Task 5 (WebSocket real-time streaming)")
        
    else:
        print("STATUS: ⚠ PARTIAL IMPLEMENTATION")
        print(f"Successfully updated: {successful_updates}/{len(results)} components")
        print("Some dashboards may need manual adjustment")
    
    print()

if __name__ == "__main__":
    main()