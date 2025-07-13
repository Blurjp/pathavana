"""
Email service for sending transactional emails.

Provides email sending functionality for authentication,
notifications, and other transactional emails.
"""

import logging
from typing import Optional, List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import aiosmtplib
from jinja2 import Template

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        self.use_ssl = settings.SMTP_SSL
        self.frontend_url = settings.FRONTEND_URL
        
        # Email templates
        self.templates = {
            "verification": {
                "subject": "Verify your Pathavana email address",
                "html": """
                    <h2>Welcome to Pathavana, {{ name }}!</h2>
                    <p>Please verify your email address by clicking the button below:</p>
                    <p style="margin: 30px 0;">
                        <a href="{{ verification_url }}" style="background-color: #4CAF50; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px;">
                            Verify Email
                        </a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{{ verification_url }}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account with Pathavana, please ignore this email.</p>
                """
            },
            "password_reset": {
                "subject": "Reset your Pathavana password",
                "html": """
                    <h2>Password Reset Request</h2>
                    <p>Hi {{ name }},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="margin: 30px 0;">
                        <a href="{{ reset_url }}" style="background-color: #FF9800; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{{ reset_url }}</p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                """
            },
            "welcome": {
                "subject": "Welcome to Pathavana!",
                "html": """
                    <h2>Welcome to Pathavana, {{ name }}!</h2>
                    <p>Your account has been successfully created and verified.</p>
                    <p>Start planning your perfect trip today:</p>
                    <p style="margin: 30px 0;">
                        <a href="{{ frontend_url }}" style="background-color: #2196F3; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px;">
                            Start Planning
                        </a>
                    </p>
                    <p>Need help? Check out our <a href="{{ frontend_url }}/help">help center</a> or reply to this email.</p>
                """
            }
        }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email asynchronously.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of attachments (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.smtp_host:
            logger.warning("SMTP not configured. Email not sent.")
            logger.info(f"Would send email to {to_email}: {subject}")
            return True  # Return True in development
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.from_name, self.from_email))
            msg["To"] = to_email
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                use_tls=self.use_tls,
                start_tls=self.use_tls
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        name: str,
        verification_token: str
    ) -> bool:
        """Send email verification email."""
        template_data = self.templates["verification"]
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
        
        # Render template
        html_template = Template(template_data["html"])
        html_content = html_template.render(
            name=name,
            verification_url=verification_url
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=template_data["subject"],
            html_content=html_content
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        name: str,
        reset_token: str
    ) -> bool:
        """Send password reset email."""
        template_data = self.templates["password_reset"]
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        # Render template
        html_template = Template(template_data["html"])
        html_content = html_template.render(
            name=name,
            reset_url=reset_url
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=template_data["subject"],
            html_content=html_content
        )
    
    async def send_welcome_email(
        self,
        to_email: str,
        name: str
    ) -> bool:
        """Send welcome email after successful registration."""
        template_data = self.templates["welcome"]
        
        # Render template
        html_template = Template(template_data["html"])
        html_content = html_template.render(
            name=name,
            frontend_url=self.frontend_url
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=template_data["subject"],
            html_content=html_content
        )


# Global email service instance
email_service = EmailService()