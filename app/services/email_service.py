import asyncio
import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_smtp_email_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """Synchronous SMTP email delivery with direct SSL (port 465) or STARTTLS (port 587)."""
    if not settings.SMTP_SERVER or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP configuration is incomplete. Skipping email delivery.")
        return False

    msg = MIMEMultipart("alternative")
    sender_display = settings.FROM_NAME or "GJ Spaces CRM"
    sender_address = settings.FROM_EMAIL or settings.SMTP_USERNAME

    # RFC-compliant headers for fast spam verification and high priority delivery
    msg["From"] = f"{sender_display} <{sender_address}>"
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gjspaces.com")
    msg["X-Priority"] = "1"
    msg["Importance"] = "High"
    msg["Auto-Submitted"] = "auto-generated"

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    port = int(settings.SMTP_PORT or 587)
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_SERVER, 465, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_SERVER, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(sender_address, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {to_email} with subject '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """Non-blocking email delivery running in threadpool."""
    return await asyncio.to_thread(_send_smtp_email_sync, to_email, subject, html_body, text_body)


def dispatch_background_email(func_or_coro: Any, *args: Any, **kwargs: Any) -> asyncio.Task:
    """Dispatches an email coroutine or async function in the background with error logging."""
    if asyncio.iscoroutine(func_or_coro):
        coro = func_or_coro
    elif callable(func_or_coro):
        coro = func_or_coro(*args, **kwargs)
    else:
        raise ValueError("Expected coroutine or callable")

    task = asyncio.create_task(coro)

    def _log_result(t: asyncio.Task) -> None:
        try:
            if not t.cancelled() and t.exception():
                logger.error(f"Background email delivery failed: {t.exception()}", exc_info=t.exception())
        except Exception:
            pass

    task.add_done_callback(_log_result)
    return task


async def send_login_otp_email(
    to_email: str,
    recipient_name: str,
    otp_code: str,
    expire_minutes: int = 10
) -> bool:
    """Sends a high-priority formatted OTP verification email for login."""
    subject = f"{otp_code} is your GJ Spaces verification code"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Login Verification Code</title>
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }}
        .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e1e8ed; }}
        .header {{ background: #1e3a8a; color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; letter-spacing: 0.5px; }}
        .body {{ padding: 30px 24px; }}
        .otp-box {{ background: #f0f4ff; border: 2px dashed #3b82f6; border-radius: 8px; text-align: center; padding: 18px; margin: 24px 0; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e3a8a; }}
        .note {{ font-size: 13px; color: #64748b; line-height: 1.5; }}
        .footer {{ text-align: center; font-size: 12px; color: #94a3b8; padding: 16px; border-top: 1px solid #f1f5f9; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>GJ SPACES CRM</h1>
        </div>
        <div class="body">
          <p>Hello <strong>{recipient_name}</strong>,</p>
          <p>You requested to sign in to your GJ Spaces CRM account. Please use the verification code below to complete your login:</p>
          <div class="otp-box">{otp_code}</div>
          <p class="note">This code will expire in <strong>{expire_minutes} minutes</strong>. If you did not request this login, please contact your Super Admin immediately.</p>
        </div>
        <div class="footer">
          &copy; 2026 GJ Spaces CRM. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"Hello {recipient_name},\n\nYour login verification code is: {otp_code}\nThis code will expire in {expire_minutes} minutes.\n\nGJ Spaces CRM"
    return await send_email(to_email, subject, html_content, text_content)


async def send_user_credentials_email(
    to_email: str,
    recipient_name: str,
    role_name: str,
    password: str
) -> bool:
    """Sends account credentials to a newly registered workforce user."""
    subject = "Welcome to GJ Spaces CRM - Your Account Credentials"

    login_url = settings.BASE_URL or "http://localhost:8000"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Welcome to GJ Spaces CRM</title>
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e1e8ed; }}
        .header {{ background: #0f172a; color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .body {{ padding: 30px 24px; }}
        .credentials-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 6px; overflow: hidden; border: 1px solid #e2e8f0; }}
        .credentials-table td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #e2e8f0; }}
        .credentials-table td:first-child {{ font-weight: bold; width: 35%; color: #475569; }}
        .credentials-table td:last-child {{ font-family: monospace; font-size: 15px; color: #0f172a; }}
        .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px; }}
        .footer {{ text-align: center; font-size: 12px; color: #94a3b8; padding: 16px; border-top: 1px solid #f1f5f9; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>Welcome to GJ Spaces CRM</h1>
        </div>
        <div class="body">
          <p>Hello <strong>{recipient_name}</strong>,</p>
          <p>An account has been created for you on the GJ Spaces CRM platform. Below are your login credentials:</p>
          
          <table class="credentials-table">
            <tr>
              <td>Assigned Role</td>
              <td><strong>{role_name}</strong></td>
            </tr>
            <tr>
              <td>Email Address</td>
              <td>{to_email}</td>
            </tr>
            <tr>
              <td>Password</td>
              <td>{password}</td>
            </tr>
          </table>

          <p style="text-align: center;">
            <a href="{login_url}" class="btn">Login to CRM</a>
          </p>

          <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
            <strong>Important:</strong> For security purposes, please do not share these credentials with anyone.
          </p>
        </div>
        <div class="footer">
          &copy; 2026 GJ Spaces CRM. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = (
        f"Hello {recipient_name},\n\n"
        f"Your account has been created on GJ Spaces CRM.\n"
        f"Role: {role_name}\n"
        f"Email: {to_email}\n"
        f"Password: {password}\n"
        f"Login: {login_url}\n\n"
        f"GJ Spaces CRM"
    )
    return await send_email(to_email, subject, html_content, text_content)
