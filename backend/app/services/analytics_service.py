"""Attendance analytics and low-attendance detection."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics import AttendanceSummary
from app.models.attendance import Attendance
from app.models.session import AttendanceSession
from app.models.student import Student


LOW_ATTENDANCE_THRESHOLD = 75.0


def _closed_session_count(db: Session) -> int:
    return db.scalar(
        select(func.count(AttendanceSession.id)).where(AttendanceSession.status == "closed")
    ) or 0


def refresh_attendance_summaries(db: Session) -> list[AttendanceSummary]:
    total_sessions = _closed_session_count(db)
    students = list(db.scalars(select(Student).order_by(Student.roll_no)).all())
    summaries: list[AttendanceSummary] = []

    for student in students:
        present_sessions = db.scalar(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student.id,
                Attendance.status == "present",
            )
        ) or 0
        absent_sessions = max(total_sessions - present_sessions, 0)
        percentage = (present_sessions / total_sessions * 100) if total_sessions else 0.0

        summary = db.scalar(
            select(AttendanceSummary).where(AttendanceSummary.student_id == student.id)
        )
        if summary is None:
            summary = AttendanceSummary(student_id=student.id)
            db.add(summary)

        summary.total_sessions = total_sessions
        summary.present_sessions = present_sessions
        summary.absent_sessions = absent_sessions
        summary.attendance_percentage = round(percentage, 2)
        summaries.append(summary)

    db.commit()
    return summaries


def get_low_attendance_students(db: Session, threshold: float = LOW_ATTENDANCE_THRESHOLD) -> list[dict]:
    refresh_attendance_summaries(db)
    rows = db.execute(
        select(Student, AttendanceSummary)
        .join(AttendanceSummary, AttendanceSummary.student_id == Student.id)
        .where(AttendanceSummary.total_sessions > 0)
        .where(AttendanceSummary.attendance_percentage < threshold)
        .order_by(AttendanceSummary.attendance_percentage.asc())
    ).all()
    return [
        {
            "student_id": student.id,
            "roll_no": student.roll_no,
            "name": student.name,
            "department": student.department,
            "email": student.email,
            "total_sessions": summary.total_sessions,
            "present_sessions": summary.present_sessions,
            "absent_sessions": summary.absent_sessions,
            "attendance_percentage": summary.attendance_percentage,
        }
        for student, summary in rows
    ]


def get_student_summary(db: Session, student_id: int) -> dict:
    refresh_attendance_summaries(db)
    student = db.get(Student, student_id)
    summary = db.scalar(select(AttendanceSummary).where(AttendanceSummary.student_id == student_id))
    if not student or not summary:
        return {}

    return {
        "student_id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "department": student.department,
        "email": student.email,
        "total_sessions": summary.total_sessions,
        "present_sessions": summary.present_sessions,
        "absent_sessions": summary.absent_sessions,
        "attendance_percentage": summary.attendance_percentage,
        "warning": summary.attendance_percentage < LOW_ATTENDANCE_THRESHOLD if summary.total_sessions else False,
        "trend": get_student_trend(db, student_id),
    }


def get_session_statistics(db: Session, session_id: int) -> dict:
    session = db.get(AttendanceSession, session_id)
    if not session:
        raise ValueError("Session not found")

    total_students = db.scalar(select(func.count(Student.id))) or 0
    present = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.session_id == session_id,
            Attendance.status == "present",
        )
    ) or 0
    absent = max(total_students - present, 0)
    percentage = (present / total_students * 100) if total_students else 0.0

    return {
        "session_id": session.id,
        "title": session.title,
        "subject": session.subject,
        "session_date": session.session_date.isoformat(),
        "status": session.status,
        "total_students": total_students,
        "present_students": present,
        "absent_students": absent,
        "attendance_percentage": round(percentage, 2),
    }


def get_department_overview(db: Session) -> dict:
    summaries = refresh_attendance_summaries(db)
    total_students = len(summaries)
    avg_attendance = (
        sum(item.attendance_percentage for item in summaries) / total_students if total_students else 0.0
    )
    low_count = sum(
        1
        for item in summaries
        if item.total_sessions and item.attendance_percentage < LOW_ATTENDANCE_THRESHOLD
    )
    return {
        "total_students": total_students,
        "closed_sessions": _closed_session_count(db),
        "average_attendance": round(avg_attendance, 2),
        "low_attendance_count": low_count,
        "trend": get_department_trend(db),
    }


def get_student_trend(db: Session, student_id: int) -> dict:
    today = date.today()
    current_start = today - timedelta(days=30)
    previous_start = today - timedelta(days=60)
    current = _student_period_percentage(db, student_id, current_start, today)
    previous = _student_period_percentage(db, student_id, previous_start, current_start)
    return {
        "current_30_day_percentage": current,
        "previous_30_day_percentage": previous,
        "change": round(current - previous, 2),
    }


def get_department_trend(db: Session) -> dict:
    today = date.today()
    current_start = today - timedelta(days=30)
    previous_start = today - timedelta(days=60)
    current = _department_period_percentage(db, current_start, today)
    previous = _department_period_percentage(db, previous_start, current_start)
    return {
        "current_30_day_percentage": current,
        "previous_30_day_percentage": previous,
        "change": round(current - previous, 2),
    }


def _student_period_percentage(db: Session, student_id: int, start: date, end: date) -> float:
    sessions = list(
        db.scalars(
            select(AttendanceSession)
            .where(AttendanceSession.status == "closed")
            .where(AttendanceSession.session_date >= start)
            .where(AttendanceSession.session_date < end)
        ).all()
    )
    if not sessions:
        return 0.0
    session_ids = [session.id for session in sessions]
    present = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.student_id == student_id,
            Attendance.session_id.in_(session_ids),
            Attendance.status == "present",
        )
    ) or 0
    return round(present / len(session_ids) * 100, 2)


def _department_period_percentage(db: Session, start: date, end: date) -> float:
    total_students = db.scalar(select(func.count(Student.id))) or 0
    sessions = list(
        db.scalars(
            select(AttendanceSession)
            .where(AttendanceSession.status == "closed")
            .where(AttendanceSession.session_date >= start)
            .where(AttendanceSession.session_date < end)
        ).all()
    )
    possible = total_students * len(sessions)
    if not possible:
        return 0.0
    session_ids = [session.id for session in sessions]
    present = db.scalar(
        select(func.count(Attendance.id)).where(
            Attendance.session_id.in_(session_ids),
            Attendance.status == "present",
        )
    ) or 0
    return round(present / possible * 100, 2)

