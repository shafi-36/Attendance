"""Analytics endpoints for faculty, HoD, and students."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_student_id_from_token, require_faculty_or_hod, require_student
from app.core.database import get_db
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> dict:
    return analytics_service.get_department_overview(db)


@router.get("/low-attendance")
def low_attendance(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> list[dict]:
    return analytics_service.get_low_attendance_students(db)


@router.get("/student/me")
def my_summary(
    db: Session = Depends(get_db),
    student_id: int = Depends(get_student_id_from_token),
    _student: User = Depends(require_student),
) -> dict:
    return analytics_service.get_student_summary(db, student_id)


@router.get("/student/{student_id}")
def student_summary(
    student_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> dict:
    return analytics_service.get_student_summary(db, student_id)


@router.get("/session/{session_id}")
def session_statistics(
    session_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> dict:
    return analytics_service.get_session_statistics(db, session_id)

