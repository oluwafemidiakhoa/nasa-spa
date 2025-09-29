#!/usr/bin/env python3
"""
Simple email test without unicode characters
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables
def load_env_file(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file(".env")

def main():
    print("NASA SPACE WEATHER FORECASTER - EMAIL TEST")
    print("=" * 50)
    
    try:
        from backend.email_alerts import EmailAlerter
        
        # Create emailer
        alerter = EmailAlerter()
        
        print(f"Email configured: {alerter.enabled}")
        print(f"From address: {alerter.email_user}")
        print(f"SMTP server: {alerter.smtp_server}:{alerter.smtp_port}")
        print(f"Test recipient: {alerter.test_recipient}")
        print()
        
        if not alerter.enabled:
            print("Email not configured properly!")
            return
        
        # Send test email
        print("Sending test email...")
        success = alerter.test_email_connection()
        
        if success:
            print("SUCCESS! Test email sent!")
            print("Check your email inbox for the test message.")
        else:
            print("FAILED! Email test did not work.")
            print("Check your Zoho settings and credentials.")
        
        print()
        print("Testing forecast alert...")
        
        # Test with a sample forecast
        from backend.universal_forecaster import run_universal_forecast
        forecast = run_universal_forecast(days_back=1, max_tokens=600)
        
        alert_success = alerter.send_forecast_alert(forecast)
        
        if alert_success:
            print("SUCCESS! Forecast alert sent!")
            print("Check your email for the space weather alert.")
        else:
            print("FAILED! Forecast alert did not work.")
        
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Troubleshooting tips:")
        print("1. Check your Zoho email settings")
        print("2. Verify password is correct")
        print("3. Enable 'Less Secure Apps' in Zoho if needed")
        print("4. Try using an app-specific password")

if __name__ == "__main__":
    main()