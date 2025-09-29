"""
Email alert system for NASA Space Weather Forecaster
Supports Zoho, Gmail, and other SMTP providers
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailAlerter:
    """Email alert system for space weather notifications"""
    
    def __init__(self):
        # Load email configuration from environment
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.test_recipient = os.getenv("TEST_ALERT_EMAIL", self.email_user)
        
        # Zoho SMTP settings (default)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.zoho.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.use_tls = os.getenv("SMTP_TLS", "true").lower() == "true"
        
        # Validate configuration
        if not self.email_user or not self.email_password:
            logger.warning("Email credentials not configured. Alerts disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Email alerts configured for {self.email_user}")
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   body: str, 
                   html_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Send email notification
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body
            attachments: Optional list of file paths to attach
            
        Returns:
            True if email sent successfully, False otherwise
        """
        
        if not self.enabled:
            logger.warning("Email not configured. Cannot send alert.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Connect to SMTP server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_forecast_alert(self, forecast_data: Dict[str, Any], recipients: Optional[List[str]] = None) -> bool:
        """
        Send space weather forecast alert
        
        Args:
            forecast_data: Forecast data from the universal forecaster
            recipients: Optional list of recipients (uses test email if not provided)
            
        Returns:
            True if alert sent successfully
        """
        
        if not recipients:
            recipients = [self.test_recipient] if self.test_recipient else []
        
        if not recipients:
            logger.error("No recipients configured for alerts")
            return False
        
        # Determine alert level
        if hasattr(forecast_data, 'forecasts'):
            forecasts = forecast_data.forecasts
            forecast_count = len(forecasts)
            
            if forecast_count == 0:
                alert_level = "ROUTINE"
                priority = "LOW"
            else:
                # Check for high-risk impacts
                high_risk_impacts = []
                for forecast in forecasts:
                    high_risk_impacts.extend([
                        impact for impact in forecast.impacts 
                        if impact in ["GNSS_outage", "satellite_drag", "radiation_storm", "power_grid"]
                    ])
                
                if high_risk_impacts:
                    alert_level = "HIGH"
                    priority = "HIGH"
                elif forecast_count > 1:
                    alert_level = "MODERATE"
                    priority = "MEDIUM"
                else:
                    alert_level = "LOW"
                    priority = "LOW"
        else:
            alert_level = "ERROR"
            priority = "HIGH"
            forecast_count = 0
            forecasts = []
        
        # Generate subject line
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        subject = f"🌞 NASA Space Weather Alert - {alert_level} - {timestamp}"
        
        # Generate plain text body
        body = self._generate_text_alert(forecast_data, alert_level, priority, timestamp)
        
        # Generate HTML body
        html_body = self._generate_html_alert(forecast_data, alert_level, priority, timestamp)
        
        # Send the alert
        return self.send_email(recipients, subject, body, html_body)
    
    def _generate_text_alert(self, forecast_data, alert_level: str, priority: str, timestamp: str) -> str:
        """Generate plain text alert email"""
        
        body = f"""NASA SPACE WEATHER ALERT
========================

ALERT LEVEL: {alert_level}
PRIORITY: {priority}
GENERATED: {timestamp}

"""
        
        if hasattr(forecast_data, 'forecasts') and forecast_data.forecasts:
            body += f"ACTIVE FORECASTS: {len(forecast_data.forecasts)}\n\n"
            
            for i, forecast in enumerate(forecast_data.forecasts, 1):
                body += f"FORECAST #{i}:\n"
                body += f"  Event Type: {forecast.event}\n"
                body += f"  Solar Event: {forecast.solar_timestamp}\n"
                body += f"  Earth Impact: {forecast.predicted_arrival_window_utc[0]} to {forecast.predicted_arrival_window_utc[1]}\n"
                body += f"  Confidence: {forecast.confidence:.1%}\n"
                body += f"  Risk: {forecast.risk_summary}\n"
                body += f"  Impacts: {', '.join(forecast.impacts)}\n"
                body += f"  Evidence: {len(forecast.evidence.donki_ids)} DONKI events\n\n"
        else:
            body += "STATUS: No significant space weather events detected.\n"
            body += "CONDITION: Quiet space weather conditions continue.\n\n"
        
        body += """
DATA SOURCES:
- NASA DONKI (Space Weather Database)
- NASA EPIC (Earth Imagery)
- OpenAI GPT-4 (AI Analysis)

DASHBOARD: http://localhost:9001
API STATUS: http://localhost:9001/api/v1/system/status

This is an automated alert from the NASA Space Weather Forecaster.
"""
        
        return body
    
    def _generate_html_alert(self, forecast_data, alert_level: str, priority: str, timestamp: str) -> str:
        """Generate HTML alert email"""
        
        # Color scheme based on alert level
        colors = {
            "ROUTINE": {"bg": "#00ff00", "text": "#000000"},
            "LOW": {"bg": "#80ff00", "text": "#000000"},
            "MODERATE": {"bg": "#ffff00", "text": "#000000"},
            "HIGH": {"bg": "#ff8000", "text": "#ffffff"},
            "ERROR": {"bg": "#ff0000", "text": "#ffffff"}
        }
        
        color = colors.get(alert_level, colors["LOW"])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NASA Space Weather Alert</title>
    <style>
        body {{ font-family: 'Courier New', monospace; background: #000; color: #00ff00; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #1a1a2e; border: 2px solid #00ff00; border-radius: 10px; padding: 20px; }}
        .header {{ background: {color['bg']}; color: {color['text']}; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px; }}
        .alert-level {{ font-size: 24px; font-weight: bold; }}
        .forecast-item {{ background: rgba(0, 255, 0, 0.1); border-left: 4px solid #00ff00; padding: 15px; margin: 10px 0; }}
        .confidence {{ background: linear-gradient(90deg, #ff0000, #ffff00, #00ff00); height: 20px; border-radius: 10px; position: relative; }}
        .confidence-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #000; font-weight: bold; }}
        .footer {{ margin-top: 20px; padding: 15px; background: rgba(0, 255, 255, 0.1); border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="alert-level">🌞 NASA SPACE WEATHER ALERT</div>
            <div>LEVEL: {alert_level} | PRIORITY: {priority}</div>
            <div>GENERATED: {timestamp}</div>
        </div>
"""
        
        if hasattr(forecast_data, 'forecasts') and forecast_data.forecasts:
            html += f"<h2>🚨 ACTIVE FORECASTS: {len(forecast_data.forecasts)}</h2>"
            
            for i, forecast in enumerate(forecast_data.forecasts, 1):
                confidence_pct = int(forecast.confidence * 100)
                html += f"""
        <div class="forecast-item">
            <h3>FORECAST #{i}: {forecast.event}</h3>
            <p><strong>Solar Event:</strong> {forecast.solar_timestamp}</p>
            <p><strong>Earth Impact Window:</strong> {forecast.predicted_arrival_window_utc[0]} to {forecast.predicted_arrival_window_utc[1]}</p>
            <p><strong>Risk Summary:</strong> {forecast.risk_summary}</p>
            <p><strong>Potential Impacts:</strong> {', '.join(forecast.impacts)}</p>
            <p><strong>Evidence Sources:</strong> {len(forecast.evidence.donki_ids)} DONKI events</p>
            <p><strong>Confidence Level:</strong></p>
            <div class="confidence">
                <div style="width: {confidence_pct}%; height: 100%; background: rgba(255,255,255,0.3); border-radius: 10px;"></div>
                <div class="confidence-text">{confidence_pct}%</div>
            </div>
        </div>
"""
        else:
            html += """
        <div class="forecast-item">
            <h3>✅ QUIET CONDITIONS</h3>
            <p>No significant space weather events detected.</p>
            <p>Current conditions are quiet with minimal Earth impact expected.</p>
        </div>
"""
        
        html += f"""
        <div class="footer">
            <h3>📊 DATA SOURCES</h3>
            <ul>
                <li>NASA DONKI - Space Weather Database</li>
                <li>NASA EPIC - Earth Imagery</li>
                <li>OpenAI GPT-4 - AI Analysis Engine</li>
            </ul>
            <p><strong>Dashboard:</strong> <a href="http://localhost:9001" style="color: #00ffff;">http://localhost:9001</a></p>
            <p><strong>API Status:</strong> <a href="http://localhost:9001/api/v1/system/status" style="color: #00ffff;">http://localhost:9001/api/v1/system/status</a></p>
            <p style="font-size: 12px; color: #888;">This is an automated alert from the NASA Space Weather Forecaster.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def test_email_connection(self) -> bool:
        """Test email configuration"""
        if not self.enabled:
            return False
        
        test_subject = "🧪 NASA Space Weather Forecaster - Email Test"
        test_body = f"""Email Test Successful!

Your NASA Space Weather Forecaster email alert system is working correctly.

Configuration:
- SMTP Server: {self.smtp_server}:{self.smtp_port}
- From Address: {self.email_user}
- TLS Enabled: {self.use_tls}

Test completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Ready to receive space weather alerts! 🛰️
"""
        
        return self.send_email([self.test_recipient], test_subject, test_body)

# Convenience functions
def send_forecast_alert(forecast_data, recipients=None):
    """Send a forecast alert using the configured email system"""
    alerter = EmailAlerter()
    return alerter.send_forecast_alert(forecast_data, recipients)

def test_email_alerts():
    """Test the email alert system"""
    alerter = EmailAlerter()
    return alerter.test_email_connection()

if __name__ == "__main__":
    # Test the email system
    print("Testing email alert system...")
    if test_email_alerts():
        print("✅ Email test successful!")
    else:
        print("❌ Email test failed!")