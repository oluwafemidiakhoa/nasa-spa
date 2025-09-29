"""
Notification service for NASA Space Weather Forecaster
Handles email and SMS notifications for space weather alerts
"""

import os
import smtplib
import asyncio
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dataclasses import dataclass

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

from jinja2 import Template


@dataclass
class NotificationConfig:
    """Configuration for notification services"""
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: Optional[str] = None
    email_password: Optional[str] = None
    from_email: Optional[str] = None
    
    # SMS settings (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_phone: Optional[str] = None
    
    # Notification limits
    max_emails_per_hour: int = 50
    max_sms_per_hour: int = 20
    
    def __post_init__(self):
        # Load from environment variables if not provided
        if not self.email_user:
            self.email_user = os.getenv("EMAIL_USER")
        if not self.email_password:
            self.email_password = os.getenv("EMAIL_PASSWORD")
        if not self.from_email:
            self.from_email = self.email_user or os.getenv("FROM_EMAIL")
        
        if not self.twilio_account_sid:
            self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not self.twilio_from_phone:
            self.twilio_from_phone = os.getenv("TWILIO_FROM_PHONE")


class EmailTemplates:
    """Email templates for different alert types"""
    
    ALERT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .severity-severe { color: #d32f2f; border-left: 4px solid #d32f2f; padding-left: 15px; }
        .severity-high { color: #f57c00; border-left: 4px solid #f57c00; padding-left: 15px; }
        .severity-moderate { color: #fbc02d; border-left: 4px solid #fbc02d; padding-left: 15px; }
        .details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }
        .impacts { margin: 10px 0; }
        .impacts li { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌌 NASA Space Weather Alert</h1>
        </div>
        
        <div class="severity-{{ severity.lower() }}">
            <h2>{{ severity }} SPACE WEATHER EVENT</h2>
            <p><strong>Event Type:</strong> {{ event_type }}</p>
            <p><strong>Confidence:</strong> {{ confidence }}%</p>
        </div>
        
        <div class="details">
            <h3>Expected Earth Impact</h3>
            <p><strong>Time Window:</strong> {{ arrival_window }}</p>
            
            <h3>Potential Effects</h3>
            <ul class="impacts">
            {% for impact in impacts %}
                <li>{{ impact }}</li>
            {% endfor %}
            </ul>
            
            <h3>Risk Summary</h3>
            <p>{{ risk_summary }}</p>
        </div>
        
        <div class="footer">
            <p>This is an automated alert from the NASA Space Weather Forecaster.</p>
            <p>Generated at {{ timestamp }}</p>
            <p>To unsubscribe or manage your alert preferences, please contact your system administrator.</p>
        </div>
    </div>
</body>
</html>
"""
    
    ALERT_TEXT_TEMPLATE = """
NASA SPACE WEATHER ALERT
{{ "="*50 }}

{{ severity }} SPACE WEATHER EVENT

Event Type: {{ event_type }}
Confidence: {{ confidence }}%

Expected Earth Impact
Time Window: {{ arrival_window }}

Potential Effects:
{% for impact in impacts %}
- {{ impact }}
{% endfor %}

Risk Summary:
{{ risk_summary }}

{{ "-"*50 }}
This is an automated alert from the NASA Space Weather Forecaster.
Generated at {{ timestamp }}
"""


class NotificationService:
    """Handles sending notifications via email and SMS"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.email_templates = EmailTemplates()
        
        # Initialize Twilio client if available
        self.twilio_client = None
        if (TWILIO_AVAILABLE and 
            self.config.twilio_account_sid and 
            self.config.twilio_auth_token):
            try:
                self.twilio_client = TwilioClient(
                    self.config.twilio_account_sid,
                    self.config.twilio_auth_token
                )
            except Exception as e:
                print(f"Failed to initialize Twilio client: {e}")
        
        # Rate limiting tracking
        self._email_count = 0
        self._sms_count = 0
        self._last_reset = datetime.utcnow()
    
    def _reset_rate_limits_if_needed(self):
        """Reset rate limiting counters if an hour has passed"""
        now = datetime.utcnow()
        if (now - self._last_reset).seconds >= 3600:  # 1 hour
            self._email_count = 0
            self._sms_count = 0
            self._last_reset = now
    
    async def send_alert_notifications(self, alert_info: Dict[str, Any]):
        """Send alert notifications to all subscribers"""
        try:
            # Get subscribers from database (would need to import DatabaseManager)
            # For now, we'll use environment-based test recipients
            test_email = os.getenv("TEST_ALERT_EMAIL")
            test_phone = os.getenv("TEST_ALERT_PHONE")
            
            if test_email:
                await self.send_email_alert(test_email, alert_info)
            
            if test_phone and self.twilio_client:
                await self.send_sms_alert(test_phone, alert_info)
            
            print(f"Alert notifications sent for {alert_info['event_type']} - {alert_info['severity']}")
            
        except Exception as e:
            print(f"Failed to send alert notifications: {e}")
    
    async def send_email_alert(self, recipient_email: str, alert_info: Dict[str, Any]) -> bool:
        """Send an email alert"""
        self._reset_rate_limits_if_needed()
        
        if self._email_count >= self.config.max_emails_per_hour:
            print("Email rate limit exceeded")
            return False
        
        if not self.config.email_user or not self.config.email_password:
            print("Email configuration not available")
            return False
        
        try:
            # Prepare template data
            template_data = self._prepare_template_data(alert_info)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 {alert_info['severity']} Space Weather Alert - {alert_info['event_type']}"
            msg['From'] = self.config.from_email
            msg['To'] = recipient_email
            
            # Create text version
            text_template = Template(self.email_templates.ALERT_TEXT_TEMPLATE)
            text_content = text_template.render(**template_data)
            text_part = MIMEText(text_content, 'plain')
            
            # Create HTML version
            html_template = Template(self.email_templates.ALERT_HTML_TEMPLATE)
            html_content = html_template.render(**template_data)
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_email_sync, msg
            )
            
            self._email_count += 1
            return True
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
    
    def _send_email_sync(self, msg: MIMEMultipart):
        """Synchronous email sending (run in executor)"""
        server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
        server.starttls()
        server.login(self.config.email_user, self.config.email_password)
        server.send_message(msg)
        server.quit()
    
    async def send_sms_alert(self, recipient_phone: str, alert_info: Dict[str, Any]) -> bool:
        """Send an SMS alert"""
        self._reset_rate_limits_if_needed()
        
        if self._sms_count >= self.config.max_sms_per_hour:
            print("SMS rate limit exceeded")
            return False
        
        if not self.twilio_client:
            print("SMS service not available")
            return False
        
        try:
            # Create SMS message (keep it short)
            arrival_start = alert_info['arrival_window'][0]
            arrival_end = alert_info['arrival_window'][1]
            
            # Parse arrival times for display
            try:
                start_dt = datetime.fromisoformat(arrival_start.replace("Z", "+00:00"))
                arrival_text = start_dt.strftime('%b %d, %H:%M UTC')
            except:
                arrival_text = arrival_start
            
            sms_text = f"""NASA SPACE WEATHER ALERT
{alert_info['severity']} {alert_info['event_type']}
Impact: {arrival_text}
Confidence: {alert_info['confidence']:.0%}
Effects: {', '.join(alert_info['impacts'][:2])}"""
            
            # Send SMS
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.twilio_client.messages.create(
                    body=sms_text,
                    from_=self.config.twilio_from_phone,
                    to=recipient_phone
                )
            )
            
            self._sms_count += 1
            return True
            
        except Exception as e:
            print(f"Failed to send SMS alert: {e}")
            return False
    
    def _prepare_template_data(self, alert_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        # Format arrival window
        arrival_start = alert_info['arrival_window'][0]
        arrival_end = alert_info['arrival_window'][1]
        
        try:
            start_dt = datetime.fromisoformat(arrival_start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(arrival_end.replace("Z", "+00:00"))
            arrival_window = f"{start_dt.strftime('%B %d, %H:%M')} - {end_dt.strftime('%H:%M UTC')}"
        except:
            arrival_window = f"{arrival_start} - {arrival_end}"
        
        # Format impacts for display
        impact_descriptions = {
            "aurora_lowlat": "Aurora visible at low latitudes",
            "aurora_midlat": "Aurora visible at mid-latitudes",
            "aurora_highlat": "Aurora visible at high latitudes",
            "HF_comms": "HF radio communication disruptions",
            "GNSS_jitter": "GPS/GNSS navigation accuracy degradation",
            "satellite_ops": "Satellite operations affected",
            "power_grid": "Power grid voltage fluctuations"
        }
        
        formatted_impacts = []
        for impact in alert_info['impacts']:
            description = impact_descriptions.get(impact, impact.replace("_", " ").title())
            formatted_impacts.append(description)
        
        return {
            "severity": alert_info['severity'],
            "event_type": alert_info['event_type'],
            "confidence": int(alert_info['confidence'] * 100),
            "arrival_window": arrival_window,
            "impacts": formatted_impacts,
            "risk_summary": alert_info.get('message', 'Space weather event detected'),
            "timestamp": datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')
        }
    
    async def test_email_notification(self, recipient_email: str) -> bool:
        """Send a test email notification"""
        test_alert = {
            "event_type": "TEST",
            "severity": "MODERATE",
            "confidence": 0.8,
            "arrival_window": ["2025-09-26T12:00:00Z", "2025-09-26T18:00:00Z"],
            "impacts": ["aurora_highlat", "HF_comms"],
            "message": "This is a test alert to verify email notification functionality."
        }
        
        return await self.send_email_alert(recipient_email, test_alert)
    
    async def test_sms_notification(self, recipient_phone: str) -> bool:
        """Send a test SMS notification"""
        test_alert = {
            "event_type": "TEST",
            "severity": "MODERATE",
            "confidence": 0.8,
            "arrival_window": ["2025-09-26T12:00:00Z", "2025-09-26T18:00:00Z"],
            "impacts": ["aurora_highlat", "HF_comms"],
            "message": "This is a test alert."
        }
        
        return await self.send_sms_alert(recipient_phone, test_alert)


# CLI test functions
async def test_notifications():
    """Test notification functionality"""
    service = NotificationService()
    
    test_email = os.getenv("TEST_ALERT_EMAIL")
    test_phone = os.getenv("TEST_ALERT_PHONE")
    
    if test_email:
        print("Testing email notification...")
        success = await service.test_email_notification(test_email)
        print(f"Email test: {'SUCCESS' if success else 'FAILED'}")
    
    if test_phone:
        print("Testing SMS notification...")
        success = await service.test_sms_notification(test_phone)
        print(f"SMS test: {'SUCCESS' if success else 'FAILED'}")


if __name__ == "__main__":
    asyncio.run(test_notifications())