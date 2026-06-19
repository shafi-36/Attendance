"""MCP-facing email automation boundary.

The MVP logs and optionally sends email through SMTP. A production MCP server can
replace this module while preserving the same service calls.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import email_service


def deliver_email(
    db: Session,
    recipient: str,
    subject: str,
    body: str,
    email_type: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
):
    return email_service.send_email(
        db=db,
        recipient=recipient,
        subject=subject,
        body=body,
        email_type=email_type,
        attachments=attachments,
    )

