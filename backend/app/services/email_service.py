"""Email delivery and email log persistence."""
from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analytics import EmailLog


def send_email(
    db: Session,
    recipient: str,
    subject: str,
    body: str,
    email_type: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> EmailLog:
    settings = get_settings()
    log = EmailLog(recipient=recipient, email_type=email_type, status="pending")
    db.add(log)
    db.commit()
    db.refresh(log)

    if not settings.smtp_host:
        log.status = "skipped"
        log.error_message = "SMTP is not configured; email logged for MCP automation."
        db.commit()
        db.refresh(log)
        return log

    try:
        message = EmailMessage()
        message["From"] = settings.email_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        for filename, data, mime_type in attachments or []:
            maintype, subtype = mime_type.split("/", 1)
            message.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)

        log.status = "sent"
        log.sent_at = datetime.now(timezone.utc)
        log.error_message = None
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)

    db.commit()
    db.refresh(log)
    return log


def list_email_logs(db: Session, limit: int = 100) -> list[EmailLog]:
    from sqlalchemy import select

    return list(db.scalars(select(EmailLog).order_by(EmailLog.id.desc()).limit(limit)).all())

