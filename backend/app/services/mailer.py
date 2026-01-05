import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

# Simple mailer: uses SMTP if configured via env vars, otherwise logs the
# message via the standard logging subsystem so it appears in app logs.
# Tests can monkeypatch `send_confirmation_email` if needed.

logger = logging.getLogger("app.mailer")
DEFAULT_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")
SMTP_HOST = os.getenv("SMTP_HOST")
# If SMTP_PORT not set, defer to defaults depending on SSL setting below
_smtp_port_env = os.getenv("SMTP_PORT")
SMTP_PORT = int(_smtp_port_env) if _smtp_port_env is not None else None
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
# Controls whether to use STARTTLS (on plain SMTP) — default true
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
# Controls whether to use implicit SSL (SMTP over SSL, port 465)
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
# Timeout in seconds for SMTP connections
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "10"))


def _send_smtp(msg: EmailMessage) -> None:
    # Determine configured port defaulting to 465 for SSL, 587 otherwise
    port = SMTP_PORT or (465 if SMTP_USE_SSL else 587)

    if not SMTP_HOST:
        # No SMTP configured; log the message for dev visibility
        logger.info(
            "SMTP not configured; email would be sent:\nTo: %s\nSubject: %s\nBody:\n%s",
            msg["To"],
            msg["Subject"],
            msg.get_content(),
        )
        return

    try:
        if SMTP_USE_SSL:
            # Implicit SSL (SMTPS)
            with smtplib.SMTP_SSL(SMTP_HOST, port, timeout=SMTP_TIMEOUT) as s:
                if SMTP_USER and SMTP_PASS:
                    s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            # Plain SMTP with optional STARTTLS
            with smtplib.SMTP(SMTP_HOST, port, timeout=SMTP_TIMEOUT) as s:
                s.ehlo()
                if SMTP_USE_TLS:
                    try:
                        s.starttls()
                        s.ehlo()
                    except Exception:
                        logger.exception("STARTTLS failed; continuing without TLS")
                if SMTP_USER and SMTP_PASS:
                    s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
    except Exception:
        logger.exception("Failed to send email via SMTP")


def send_confirmation_email(to_address: str, confirm_url: str, *, subject: Optional[str] = None) -> None:
    subject = subject or "ようこそ — メールアドレスの確認"
    body = (
        f"この度はご登録ありがとうございます。\n\nメールアドレスを確認するには、以下のリンクをクリックしてください。\n\n{confirm_url}\n\nもしご自身で登録していない場合はこのメールを無視してください。"
    )

    msg = EmailMessage()
    msg["From"] = DEFAULT_FROM
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    _send_smtp(msg)
