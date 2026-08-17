import aiosmtplib
from email.message import EmailMessage
from config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def send_contact_email(name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, reason: Optional[str] = None, summary: str = "", decline_reason: Optional[str] = None) -> str:
    try:
        msg = EmailMessage()
        msg['From'] = settings.sender_email
        msg['To'] = settings.recipient_email

        if name and email and phone:
            msg['Subject'] = f"New Contact Request from {name}"
            body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nReason: {reason or 'Future updates'}\n\nChat Summary:\n{summary}"
        else:
            msg['Subject'] = "Chat Summary - User Declined Contact Info"
            body = f"Decline Reason: {decline_reason or 'Not provided'}\n\nChat Summary:\n{summary}"

        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.sender_email,
            password=settings.sender_password,
            start_tls=True,
        )
        logger.info("Email sent successfully.")
        return "Email sent successfully."
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise RuntimeError(f"Failed to send email: {e}") from e