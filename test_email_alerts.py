#!/usr/bin/env python3
"""
Test email alerts for NASA Space Weather Forecaster
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

def test_email_configuration():
    """Test email configuration"""
    print("NASA SPACE WEATHER FORECASTER - EMAIL ALERT TEST")
    print("=" * 60)
    
    # Check environment variables
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    test_recipient = os.getenv("TEST_ALERT_EMAIL")
    
    print(f"Email User: {email_user}")
    print(f"Email Password: {'*' * len(email_password) if email_password else 'NOT SET'}")
    print(f"Test Recipient: {test_recipient}")
    print()
    
    if not email_user or not email_password:
        print("❌ Email credentials not configured!")
        print("Please check your .env file settings:")
        print("  EMAIL_USER=your_zoho_email@domain.com")
        print("  EMAIL_PASSWORD=your_zoho_password")
        print("  TEST_ALERT_EMAIL=recipient@domain.com")
        return False
    
    return True

def test_email_system():
    """Test the email alert system"""
    try:
        from backend.email_alerts import EmailAlerter
        
        print("Testing email connection...")
        alerter = EmailAlerter()
        
        if not alerter.enabled:
            print("❌ Email system not enabled (missing credentials)")
            return False
        
        # Test basic email sending
        success = alerter.test_email_connection()
        
        if success:
            print("✅ Email test successful!")
            print(f"Test email sent to: {alerter.test_recipient}")
            return True
        else:
            print("❌ Email test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Email test error: {e}")
        return False

def test_forecast_alert():
    """Test sending a forecast alert"""
    try:
        from backend.email_alerts import EmailAlerter
        from backend.universal_forecaster import run_universal_forecast
        
        print("\nTesting forecast alert...")
        
        # Generate a real forecast
        print("Generating sample forecast...")
        forecast_result = run_universal_forecast(days_back=2, max_tokens=800)
        
        # Send forecast alert
        alerter = EmailAlerter()
        success = alerter.send_forecast_alert(forecast_result)
        
        if success:
            print("✅ Forecast alert sent successfully!")
            return True
        else:
            print("❌ Forecast alert failed!")
            return False
            
    except Exception as e:
        print(f"❌ Forecast alert error: {e}")
        return False

def main():
    """Main test function"""
    
    if not test_email_configuration():
        return
    
    # Test basic email
    email_success = test_email_system()
    
    if email_success:
        # Test forecast alert
        forecast_success = test_forecast_alert()
        
        if forecast_success:
            print("\n" + "=" * 60)
            print("🎉 ALL EMAIL TESTS PASSED!")
            print("Your Zoho email alerts are working correctly.")
            print("\nNext steps:")
            print("- Check your email for test messages")
            print("- Set up automated alerting in your dashboard")
            print("- Configure alert thresholds as needed")
        else:
            print("\n❌ Forecast alerts need attention")
    else:
        print("\n❌ Basic email setup needs fixing")
        print("\nTroubleshooting:")
        print("1. Verify Zoho email credentials in .env")
        print("2. Check if 2FA is enabled (use app password)")
        print("3. Ensure SMTP access is allowed in Zoho settings")
        print("4. Try different SMTP settings if needed")

if __name__ == "__main__":
    main()