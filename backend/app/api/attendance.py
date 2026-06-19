"""Attendance marking and retrieval endpoints."""
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_student_id_from_token, require_faculty, require_student
from app.core.database import get_db
from app.models.user import User
from app.schemas.attendance import AttendanceMarkRequest, MarkAttendanceResponse
from app.services import attendance_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", response_model=MarkAttendanceResponse)
def mark_attendance(
    payload: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    _student: User = Depends(require_student),
) -> MarkAttendanceResponse:
    """Mark attendance via face recognition. Student submits a base64-encoded image."""
    # Decode base64 image
    try:
        # Strip data URL prefix if present (e.g. "data:image/jpeg;base64,...")
        b64_data = payload.image_base64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        image_bytes = base64.b64decode(b64_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid base64 image: {exc}",
        )

    try:
        result = attendance_service.mark_attendance(
            db=db,
            session_id=payload.session_id,
            image_bytes=image_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error("Attendance marking failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return MarkAttendanceResponse(**result)


@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    """Get attendance history for a student. Student can view own, faculty can view any."""
    from app.models.user import UserRole
    from app.models.student import Student
    from sqlalchemy import select

    if current_user.role == UserRole.student:
        # Students can only view their own records
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
        if not student or student.id != student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return attendance_service.get_attendance_by_student(db, student_id)


@router.get("/my-history")
def get_my_attendance(
    db: Session = Depends(get_db),
    student_token_id: int = Depends(get_student_id_from_token),
    _student: User = Depends(require_student),
) -> list:
    """Convenience endpoint: student views their own attendance using token."""
    return attendance_service.get_attendance_by_student(db, student_token_id)


@router.get("/session/{session_id}")
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    _faculty: User = Depends(require_faculty),
) -> list:
    return attendance_service.get_attendance_by_session(db, session_id)
