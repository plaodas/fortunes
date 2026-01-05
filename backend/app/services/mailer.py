import os
import smtplib
from email.message import EmailMessage
from typing import Optional

# Simple mailer: uses SMTP if configured via env vars, otherwise logs to stdout.
# Tests can monkeypatch `send_confirmation_email` if needed.

DEFAULT_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


def _send_smtp(msg: EmailMessage) -> None:
    if not SMTP_HOST or not SMTP_PORT:
        # No SMTP configured; fallback to printing
        print("[mailer] SMTP not configured, email would be:")
        print(msg)
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


def send_confirmation_email(to_address: str, confirm_url: str, *, subject: Optional[str] = None) -> None:
    subject = subject or "Fortunes — メールアドレスの確認"
    body = (
        f"この度はご登録ありがとうございます。\n\nメールアドレスを確認するには、以下のリンクをクリックしてください。\n\n{confirm_url}\n\nもしご自身で登録していない場合はこのメールを無視してください。"
    )

    msg = EmailMessage()
    msg["From"] = DEFAULT_FROM
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    _send_smtp(msg)
