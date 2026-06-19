"""Email automation log endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_faculty_or_hod
from app.core.database import get_db
from app.models.user import User
from app.services import email_service

router = APIRouter(prefix="/email-logs", tags=["email-logs"])


@router.get("")
def list_logs(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> list[dict]:
    return [
        {
            "id": log.id,
            "recipient": log.recipient,
            "email_type": log.email_type,
            "status": log.status,
            "sent_at": log.sent_at.isoformat() if log.sent_at else "",
            "error_message": log.error_message,
        }
        for log in email_service.list_email_logs(db)
    ]

