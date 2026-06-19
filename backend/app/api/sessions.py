"""Attendance session endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_faculty, require_student
from app.core.database import get_db
from app.models.user import User
from app.schemas.session import SessionCreateRequest, SessionOut
from app.services import session_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    faculty: User = Depends(require_faculty),
) -> SessionOut:
    session = session_service.create_session(
        db=db,
        faculty_id=faculty.id,
        title=payload.title,
        subject=payload.subject,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    return SessionOut.model_validate(session)


@router.get("", response_model=list[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    faculty: User = Depends(require_faculty),
) -> list[SessionOut]:
    sessions = session_service.list_sessions(db, faculty_id=faculty.id)
    return [SessionOut.model_validate(s) for s in sessions]


@router.get("/all", response_model=list[SessionOut])
def list_all_sessions(
    db: Session = Depends(get_db),
    _faculty: User = Depends(require_faculty),
) -> list[SessionOut]:
    """List sessions from all faculties (for admin view)."""
    sessions = session_service.list_sessions(db)
    return [SessionOut.model_validate(s) for s in sessions]


@router.get("/active", response_model=list[SessionOut])
def list_active_sessions(
    db: Session = Depends(get_db),
    _student: User = Depends(require_student),
) -> list[SessionOut]:
    """List active sessions students can mark attendance for."""
    sessions = session_service.list_sessions(db)
    active_sessions = [s for s in sessions if s.status == "active"]
    return [SessionOut.model_validate(s) for s in active_sessions]


@router.put("/{session_id}/close", response_model=SessionOut)
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    faculty: User = Depends(require_faculty),
) -> SessionOut:
    try:
        session = session_service.close_session(db, session_id, faculty.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return SessionOut.model_validate(session)
