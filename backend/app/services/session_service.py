"""Attendance session service."""
import logging
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import AttendanceSession

logger = logging.getLogger(__name__)


def create_session(
    db: Session,
    faculty_id: int,
    title: str,
    subject: str,
    session_date: date,
    start_time: time,
    end_time: time | None = None,
) -> AttendanceSession:
    session = AttendanceSession(
        title=title,
        subject=subject,
        faculty_id=faculty_id,
        session_date=session_date,
        start_time=start_time,
        end_time=end_time,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("Created session id=%s title=%s", session.id, title)
    return session


def list_sessions(db: Session, faculty_id: int | None = None) -> list[AttendanceSession]:
    q = select(AttendanceSession).order_by(AttendanceSession.created_at.desc())
    if faculty_id is not None:
        q = q.where(AttendanceSession.faculty_id == faculty_id)
    return list(db.scalars(q).all())


def get_session(db: Session, session_id: int) -> AttendanceSession | None:
    return db.get(AttendanceSession, session_id)


def close_session(db: Session, session_id: int, faculty_id: int) -> AttendanceSession:
    session = db.get(AttendanceSession, session_id)
    if not session:
        raise ValueError("Session not found")
    if session.faculty_id != faculty_id:
        raise PermissionError("Not your session")
    if session.status == "closed":
        raise ValueError("Session already closed")
    session.status = "closed"
    db.commit()
    db.refresh(session)
    try:
        from app.services import report_service

        report_service.generate_session_report(db, session_id, notify_faculty=True)
    except Exception as exc:
        logger.warning("Session report generation failed for session %s: %s", session_id, exc)
    logger.info("Closed session id=%s", session_id)
    return session
