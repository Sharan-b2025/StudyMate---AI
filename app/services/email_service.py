"""
Email Service
--------------
Sends transactional email (currently just password resets) via SMTP if
configured. If no SMTP credentials are set, send_email() returns False and
the caller falls back to showing the content directly on screen — so the
password reset flow works out of the box on Render without any mail setup,
and upgrades to real email automatically once SMTP env vars are added.

Configure via environment variables:
    MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS, MAIL_FROM
"""
import smtplib
from email.message import EmailMessage
from flask import current_app


def is_configured():
    return bool(current_app.config.get("MAIL_SERVER") and current_app.config.get("MAIL_USERNAME"))


def send_email(to_address, subject, body_text):
    """Returns True if the email was sent, False if SMTP isn't configured
    or sending failed (callers should have a fallback for both cases)."""
    if not is_configured():
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = current_app.config.get("MAIL_FROM") or current_app.config["MAIL_USERNAME"]
        msg["To"] = to_address
        msg.set_content(body_text)

        server = current_app.config["MAIL_SERVER"]
        port = current_app.config.get("MAIL_PORT", 587)
        username = current_app.config["MAIL_USERNAME"]
        password = current_app.config.get("MAIL_PASSWORD", "")
        use_tls = current_app.config.get("MAIL_USE_TLS", True)

        with smtplib.SMTP(server, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception:  # noqa: BLE001 - email failures should never crash the app
        return False
