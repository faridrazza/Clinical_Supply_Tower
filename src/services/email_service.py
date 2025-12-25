"""
Email Service for Supply Watchdog Alerts.

Uses Resend API to send email alerts when Workflow A detects risks.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service using Resend API.
    
    Sends structured alerts for:
    - Expiring batch notifications
    - Shortfall predictions
    - Daily supply watchdog summaries
    """
    
    def __init__(self):
        """Initialize email service with Resend API key."""
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("ALERT_EMAIL_FROM", "onboarding@resend.dev")
        self.to_email = os.getenv("ALERT_EMAIL_TO")
        self.enabled = bool(self.api_key and self.to_email)
        
        if not self.enabled:
            logger.warning("Email service disabled - missing RESEND_API_KEY or ALERT_EMAIL_TO")
    
    def send_alert(
        self,
        subject: str,
        html_content: str,
        json_attachment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email alert.
        
        Args:
            subject: Email subject
            html_content: HTML body content
            json_attachment: Optional JSON data to attach
            
        Returns:
            Dictionary with send status
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Email service not configured",
                "message": "Set RESEND_API_KEY and ALERT_EMAIL_TO in .env"
            }
        
        try:
            import resend
            resend.api_key = self.api_key
            
            email_params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_content
            }
            
            # Add JSON attachment if provided
            if json_attachment:
                json_str = json.dumps(json_attachment, indent=2)
                email_params["attachments"] = [{
                    "filename": f"supply_watchdog_{datetime.now().strftime('%Y%m%d')}.json",
                    "content": json_str
                }]
            
            response = resend.Emails.send(email_params)
            
            logger.info(f"Email sent successfully: {response}")
            return {
                "success": True,
                "message_id": response.get("id"),
                "to": self.to_email
            }
        
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_watchdog_alert(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Supply Watchdog alert email.
        
        Args:
            workflow_result: Result from Workflow A execution
            
        Returns:
            Dictionary with send status
        """
        if not workflow_result.get("success"):
            return self._send_error_alert(workflow_result)
        
        output = workflow_result.get("output", {})
        summary = workflow_result.get("summary", {})
        
        # Build email content
        subject = self._build_subject(summary)
        html_content = self._build_html_content(output, summary, workflow_result)
        
        return self.send_alert(
            subject=subject,
            html_content=html_content,
            json_attachment=output
        )
    
    def _build_subject(self, summary: Dict[str, Any]) -> str:
        """Build email subject based on risk level."""
        critical = summary.get("critical_batches", 0)
        expiring = summary.get("expiring_batches", 0)
        shortfalls = summary.get("shortfalls", 0)
        
        if critical > 0:
            return f"🚨 CRITICAL: {critical} batches expiring <30 days | Supply Watchdog Alert"
        elif expiring > 0 or shortfalls > 0:
            return f"⚠️ WARNING: {expiring} expiring batches, {shortfalls} shortfalls | Supply Watchdog"
        else:
            return "✅ Supply Watchdog: No Critical Risks Detected"
    
    def _build_html_content(
        self,
        output: Dict[str, Any],
        summary: Dict[str, Any],
        workflow_result: Dict[str, Any]
    ) -> str:
        """Build HTML email content."""
        alert_date = output.get("alert_date", datetime.now().strftime("%Y-%m-%d"))
        risk_summary = output.get("risk_summary", {})
        expiry_alerts = output.get("expiry_alerts", [])
        shortfall_predictions = output.get("shortfall_predictions", [])
        
        # Build expiry alerts table
        expiry_rows = ""
        for alert in expiry_alerts[:10]:  # Limit to 10 in email
            severity_color = {
                "CRITICAL": "#dc3545",
                "HIGH": "#fd7e14",
                "MEDIUM": "#ffc107"
            }.get(alert.get("severity"), "#6c757d")
            
            expiry_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    <span style="color: {severity_color}; font-weight: bold;">{alert.get('severity', 'N/A')}</span>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('batch_id', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('material', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('location', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('expiry_date', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('days_remaining', 'N/A')} days</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('quantity', 'N/A')}</td>
            </tr>
            """
        
        # Build shortfall table
        shortfall_rows = ""
        for sf in shortfall_predictions[:10]:
            shortfall_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{sf.get('country', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{sf.get('material', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{sf.get('current_stock', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{sf.get('projected_8week_demand', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545; font-weight: bold;">{sf.get('shortfall', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{sf.get('estimated_stockout_date', 'N/A')}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Supply Watchdog Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1f77b4, #2c3e50); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">🏥 Clinical Supply Chain Control Tower</h1>
                <h2 style="margin: 10px 0 0 0; font-weight: normal;">Supply Watchdog Alert</h2>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd;">
                <p><strong>Alert Date:</strong> {alert_date}</p>
                <p><strong>Execution Time:</strong> {workflow_result.get('execution_time', 'N/A')}</p>
                <p><strong>Trigger:</strong> {workflow_result.get('trigger_type', 'scheduled')}</p>
            </div>
            
            <div style="background: white; padding: 20px; border: 1px solid #ddd; margin-top: -1px;">
                <h3 style="color: #2c3e50; border-bottom: 2px solid #1f77b4; padding-bottom: 10px;">
                    📊 Risk Summary
                </h3>
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; flex: 1; min-width: 150px;">
                        <div style="font-size: 24px; font-weight: bold; color: #856404;">
                            {risk_summary.get('total_expiring_batches', 0)}
                        </div>
                        <div style="color: #856404;">Expiring Batches</div>
                    </div>
                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; flex: 1; min-width: 150px;">
                        <div style="font-size: 24px; font-weight: bold; color: #721c24;">
                            {summary.get('critical_batches', 0)}
                        </div>
                        <div style="color: #721c24;">Critical (&lt;30 days)</div>
                    </div>
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; flex: 1; min-width: 150px;">
                        <div style="font-size: 24px; font-weight: bold; color: #155724;">
                            {risk_summary.get('total_shortfall_predictions', 0)}
                        </div>
                        <div style="color: #155724;">Shortfall Predictions</div>
                    </div>
                </div>
            </div>
            
            {"" if not expiry_alerts else f'''
            <div style="background: white; padding: 20px; border: 1px solid #ddd; margin-top: -1px;">
                <h3 style="color: #2c3e50; border-bottom: 2px solid #fd7e14; padding-bottom: 10px;">
                    ⚠️ Expiry Alerts ({len(expiry_alerts)} batches)
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Severity</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Batch ID</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Material</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Location</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Expiry Date</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Days Left</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Quantity</th>
                        </tr>
                    </thead>
                    <tbody>
                        {expiry_rows}
                    </tbody>
                </table>
                {f"<p style='color: #6c757d; font-style: italic;'>Showing {min(10, len(expiry_alerts))} of {len(expiry_alerts)} alerts. See attached JSON for full data.</p>" if len(expiry_alerts) > 10 else ""}
            </div>
            '''}
            
            {"" if not shortfall_predictions else f'''
            <div style="background: white; padding: 20px; border: 1px solid #ddd; margin-top: -1px;">
                <h3 style="color: #2c3e50; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                    📉 Shortfall Predictions ({len(shortfall_predictions)} items)
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Country</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Material</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Current Stock</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">8-Week Demand</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Shortfall</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Stockout Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {shortfall_rows}
                    </tbody>
                </table>
            </div>
            '''}
            
            <div style="background: #2c3e50; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; margin-top: -1px;">
                <p style="margin: 0; font-size: 12px;">
                    Clinical Supply Chain Control Tower | Automated Alert System<br>
                    Generated by Supply Watchdog Agent
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_error_alert(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send error notification when workflow fails."""
        error = workflow_result.get("error", "Unknown error")
        error_type = workflow_result.get("error_type", "Error")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #dc3545; color: white; padding: 20px; border-radius: 8px;">
                <h1>🚨 Supply Watchdog Error</h1>
                <p>The Supply Watchdog workflow failed to execute.</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd;">
                <p><strong>Error Type:</strong> {error_type}</p>
                <p><strong>Error Message:</strong> {error}</p>
                <p><strong>Time:</strong> {workflow_result.get('execution_time', 'N/A')}</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_alert(
            subject=f"🚨 Supply Watchdog FAILED: {error_type}",
            html_content=html
        )


# Convenience function
def send_watchdog_alert(workflow_result: Dict[str, Any]) -> Dict[str, Any]:
    """Send Supply Watchdog alert email."""
    service = EmailService()
    return service.send_watchdog_alert(workflow_result)
