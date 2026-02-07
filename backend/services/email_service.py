# services/email_service.py
import os
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)

# Email service configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@trackrecord.life")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://trackrecord.life")


async def send_verification_email(to_email: str, username: str, verification_token: str) -> bool:
    """
    Send email verification link to user.
    Uses Resend API for email delivery.
    Returns True if sent successfully, False otherwise.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured - email verification disabled")
        # In development, log the verification link instead
        verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        logger.info(f"[DEV] Verification link for {to_email}: {verification_link}")
        return True  # Return True in dev mode so registration can proceed
    
    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: 900; color: #000; }}
            .button {{ display: inline-block; background: #000; color: #fff !important; padding: 14px 32px; text-decoration: none; font-weight: bold; margin: 20px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">TrackRecord</div>
            </div>
            
            <p>Hi {username},</p>
            
            <p>Welcome to TrackRecord! Please verify your email address to complete your registration and start making predictions.</p>
            
            <p style="text-align: center;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666; font-size: 14px;">{verification_link}</p>
            
            <p>This link will expire in 24 hours.</p>
            
            <div class="footer">
                <p>If you didn't create an account on TrackRecord, you can safely ignore this email.</p>
                <p>&copy; TrackRecord - Everyone talks. We keep score.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"TrackRecord <{FROM_EMAIL}>",
                    "to": [to_email],
                    "subject": "Verify your TrackRecord account",
                    "html": html_content
                }
            ) as response:
                if response.status == 200:
                    logger.info(f"Verification email sent to {to_email}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send verification email: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False


async def send_password_reset_email(to_email: str, username: str, reset_token: str) -> bool:
    """
    Send password reset link to user.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured - password reset email disabled")
        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        logger.info(f"[DEV] Password reset link for {to_email}: {reset_link}")
        return True
    
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: 900; color: #000; }}
            .button {{ display: inline-block; background: #000; color: #fff !important; padding: 14px 32px; text-decoration: none; font-weight: bold; margin: 20px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">TrackRecord</div>
            </div>
            
            <p>Hi {username},</p>
            
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_link}</p>
            
            <p>This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.</p>
            
            <div class="footer">
                <p>&copy; TrackRecord - Everyone talks. We keep score.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"TrackRecord <{FROM_EMAIL}>",
                    "to": [to_email],
                    "subject": "Reset your TrackRecord password",
                    "html": html_content
                }
            ) as response:
                if response.status == 200:
                    logger.info(f"Password reset email sent to {to_email}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send password reset email: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False
