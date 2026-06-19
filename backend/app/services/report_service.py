"""AI report orchestration for session, student, and department reports."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analytics import AIReport
from app.models.session import AttendanceSession
from app.models.student import Student
from app.models.user import User
from app.services import analytics_service, hf_service, mcp_client, minio_service, pdf_service


def generate_session_report(db: Session, session_id: int, notify_faculty: bool = False) -> AIReport:
    stats = analytics_service.get_session_statistics(db, session_id)
    text = hf_service.session_summary(stats)
    pdf = pdf_service.build_report_pdf(
        title=f"Session Report - {stats['title']}",
        lines=[
            f"Subject: {stats['subject']}",
            f"Date: {stats['session_date']}",
            f"Present: {stats['present_students']}",
            f"Absent: {stats['absent_students']}",
            f"Attendance: {stats['attendance_percentage']}%",
            "",
            text,
        ],
    )

    report_path = _store_report_pdf(pdf, f"reports/{date.today():%Y/%m}/session_{session_id}_report.pdf")
    report = AIReport(
        session_id=session_id,
        report_type="session_summary",
        report_text=text,
        report_path=report_path,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if notify_faculty:
        session = db.get(AttendanceSession, session_id)
        faculty = db.get(User, session.faculty_id) if session else None
        recipient = f"{faculty.username}@example.local" if faculty else get_settings().email_from
        mcp_client.deliver_email(
            db=db,
            recipient=recipient,
            subject=f"Attendance report: {stats['title']}",
            body=text,
            email_type="session_closure",
            attachments=[("attendance_summary.pdf", pdf, "application/pdf")],
        )

    return report


def send_low_attendance_warnings(db: Session) -> list[dict]:
    warnings = []
    for item in analytics_service.get_low_attendance_students(db):
        text = hf_service.low_attendance_warning(item)
        log = mcp_client.deliver_email(
            db=db,
            recipient=item["email"],
            subject="Low attendance warning",
            body=text,
            email_type="low_attendance_warning",
        )
        warnings.append({**item, "message": text, "email_status": log.status})
    return warnings


def generate_department_report(db: Session, notify_hod: bool = False) -> AIReport:
    overview = analytics_service.get_department_overview(db)
    text = hf_service.department_summary(overview)
    pdf = pdf_service.build_report_pdf(
        title="Department Attendance Report",
        lines=[
            f"Total students: {overview['total_students']}",
            f"Closed sessions: {overview['closed_sessions']}",
            f"Average attendance: {overview['average_attendance']}%",
            f"Low attendance count: {overview['low_attendance_count']}",
            f"30-day trend change: {overview['trend']['change']}%",
            "",
            text,
        ],
    )
    report_path = _store_report_pdf(pdf, f"reports/{date.today():%Y/%m}/weekly_department_report.pdf")
    report = AIReport(
        session_id=None,
        report_type="department_summary",
        report_text=text,
        report_path=report_path,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if notify_hod:
        mcp_client.deliver_email(
            db=db,
            recipient=get_settings().hod_email,
            subject="Weekly department attendance report",
            body=text,
            email_type="weekly_department_report",
            attachments=[("department_attendance_report.pdf", pdf, "application/pdf")],
        )
    return report


def list_reports(db: Session, limit: int = 100) -> list[AIReport]:
    return list(db.scalars(select(AIReport).order_by(AIReport.id.desc()).limit(limit)).all())


def _store_report_pdf(pdf: bytes, object_name: str) -> str | None:
    try:
        settings = get_settings()
        import socket

        host, _, port_text = settings.minio_endpoint.partition(":")
        port = int(port_text or "9000")
        with socket.create_connection((host, port), timeout=1):
            pass

        client = minio_service.get_minio_client()
        import io

        client.put_object(
            settings.minio_bucket,
            object_name,
            io.BytesIO(pdf),
            length=len(pdf),
            content_type="application/pdf",
        )
        return object_name
    except Exception:
        return None
