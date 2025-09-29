#!/usr/bin/env python3
"""
Test the email alert system without requiring .env setup
"""

import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_email_system():
    """Test email system with mock configuration"""
    print("="*60)
    print("NASA SPACE WEATHER EMAIL ALERT SYSTEM TEST")
    print("="*60)
    
    # Test 1: Import email system
    print("\n[1/4] Testing email system import...")
    try:
        from backend.email_alerts import EmailAlerter
        print("SUCCESS: Email system imported successfully")
    except ImportError as e:
        print(f"ERROR: Failed to import email system: {e}")
        return False
    
    # Test 2: Check configuration
    print("\n[2/4] Checking email configuration...")
    alerter = EmailAlerter()
    
    if alerter.enabled:
        print("SUCCESS: Email configuration found")
        print(f"  - SMTP Server: {alerter.smtp_server}:{alerter.smtp_port}")
        print(f"  - Email User: {alerter.email_user}")
        print(f"  - Test Recipient: {alerter.test_recipient}")
        print(f"  - TLS Enabled: {alerter.use_tls}")
    else:
        print("INFO: Email not configured (this is normal for testing)")
        print("  - To enable: Run setup_email_alerts.py")
        print("  - Or create .env file with EMAIL_USER and EMAIL_PASSWORD")
    
    # Test 3: Generate sample alert
    print("\n[3/4] Testing alert generation...")
    try:
        # Create sample forecast data
        class MockForecast:
            def __init__(self):
                self.event = "CME"
                self.solar_timestamp = "2025-09-24T14:36:00Z"
                self.predicted_arrival_window_utc = ["2025-09-27T18:00:00Z", "2025-09-28T06:00:00Z"]
                self.risk_summary = "Earth-directed CME with moderate geomagnetic effects predicted"
                self.impacts = ["aurora_midlat", "HF_comms", "GNSS_jitter"]
                self.confidence = 0.87
                self.evidence = MockEvidence()
        
        class MockEvidence:
            def __init__(self):
                self.donki_ids = ["2025-09-24T14:36:00-CME-001"]
        
        class MockForecastData:
            def __init__(self):
                self.forecasts = [MockForecast()]
        
        forecast_data = MockForecastData()
        
        # Generate alert content
        text_alert = alerter._generate_text_alert(forecast_data, "MODERATE", "MEDIUM", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
        html_alert = alerter._generate_html_alert(forecast_data, "MODERATE", "MEDIUM", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
        
        print("SUCCESS: Alert content generated")
        print(f"  - Text alert: {len(text_alert)} characters")
        print(f"  - HTML alert: {len(html_alert)} characters")
        
        # Show preview of text alert
        print("\n  Preview of text alert:")
        print("  " + "="*50)
        preview_lines = text_alert.split('\n')[:10]
        for line in preview_lines:
            print(f"  {line}")
        print("  " + "="*50)
        
    except Exception as e:
        print(f"ERROR: Failed to generate alert: {e}")
        return False
    
    # Test 4: API integration test
    print("\n[4/4] Testing API integration...")
    try:
        # Import the API server classes
        from simple_api_server import EnsembleAPIHandler
        
        # Create mock handler
        class MockHandler(EnsembleAPIHandler):
            def __init__(self):
                pass
            
            def send_json_response(self, data):
                return data
        
        handler = MockHandler()
        forecast_data = handler.get_forecast_data_for_alert()
        
        print("SUCCESS: API integration working")
        print(f"  - Forecast data type: {type(forecast_data)}")
        print(f"  - Number of forecasts: {len(forecast_data.forecasts)}")
        
    except Exception as e:
        print(f"WARNING: API integration test failed: {e}")
        print("  - This is normal if the API server isn't running")
    
    # Summary
    print("\n" + "="*60)
    print("EMAIL SYSTEM TEST SUMMARY")
    print("="*60)
    
    if alerter.enabled:
        print("STATUS: Email system is CONFIGURED and ready")
        print("\nNext steps:")
        print("  1. Start API server: python simple_api_server.py")
        print("  2. Open dashboard: professional_dashboard.html")
        print("  3. Click 'EMAIL ALERT' button to send live alerts")
    else:
        print("STATUS: Email system is AVAILABLE but not configured")
        print("\nTo enable email alerts:")
        print("  1. Run: python setup_email_alerts.py")
        print("  2. Or manually create .env file with email settings")
        print("  3. Then restart API server and test alerts")
    
    print("\nSupported email providers:")
    print("  - Gmail (smtp.gmail.com:587)")
    print("  - Zoho (smtp.zoho.com:587)") 
    print("  - Outlook (smtp-mail.outlook.com:587)")
    print("  - Any SMTP server")
    
    return True

if __name__ == "__main__":
    test_email_system()