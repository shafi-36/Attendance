"""AI report endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_faculty_or_hod
from app.core.database import get_db
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_out(report) -> dict:
    return {
        "id": report.id,
        "session_id": report.session_id,
        "report_type": report.report_type,
        "report_text": report.report_text,
        "report_path": report.report_path,
        "generated_at": report.generated_at.isoformat() if report.generated_at else "",
    }


@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> list[dict]:
    return [_report_out(report) for report in report_service.list_reports(db)]


@router.post("/session/{session_id}/summary")
def generate_session_summary(
    session_id: int,
    notify_faculty: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> dict:
    return _report_out(report_service.generate_session_report(db, session_id, notify_faculty))


@router.post("/low-attendance/send")
def send_low_attendance_warnings(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> list[dict]:
    return report_service.send_low_attendance_warnings(db)


@router.post("/weekly-department")
def generate_weekly_department_report(
    notify_hod: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_hod),
) -> dict:
    return _report_out(report_service.generate_department_report(db, notify_hod))

