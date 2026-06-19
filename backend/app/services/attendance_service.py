"""Attendance marking and retrieval service."""
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.attendance import Attendance
from app.models.session import AttendanceSession
from app.models.student import Student
from app.services import face_service

logger = logging.getLogger(__name__)


def mark_attendance(
    db: Session,
    session_id: int,
    image_bytes: bytes,
) -> dict:
    """
    Full face-recognition attendance flow:
    1. Validate session is active
    2. Extract face embedding from image
    3. Identify student by comparing to stored embeddings
    4. Check for duplicate attendance
    5. Store attendance record
    """
    settings = get_settings()

    # 1. Validate session
    session = db.get(AttendanceSession, session_id)
    if not session:
        raise ValueError("Session not found")
    if session.status != "active":
        raise ValueError("Session is not active. Attendance cannot be marked.")

    # 2. Extract embedding from submitted image
    img_bgr = face_service.bytes_to_bgr(image_bytes)
    query_embedding = face_service.extract_embedding(img_bgr)

    # 3. Load all students with embeddings and identify
    students = list(
        db.scalars(
            select(Student).where(Student.face_embedding.isnot(None))
        ).all()
    )
    match = face_service.identify_student(
        query_embedding,
        students,
        threshold=settings.face_similarity_threshold,
    )
    if match is None:
        raise ValueError(
            f"Face not recognized. Confidence below threshold ({settings.face_similarity_threshold:.0%}). "
            "Please try again with better lighting."
        )

    student_id = match["student_id"]
    confidence = match["confidence"]

    # 4. Check duplicate attendance
    existing = db.scalar(
        select(Attendance).where(
            Attendance.session_id == session_id,
            Attendance.student_id == student_id,
        )
    )
    if existing:
        raise ValueError(
            f"Attendance already marked for {match['student_name']} in this session."
        )

    # 5. Store attendance record
    record = Attendance(
        session_id=session_id,
        student_id=student_id,
        confidence=confidence,
        status="present",
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise ValueError("Duplicate attendance (race condition). Already marked.")

    logger.info(
        "Attendance marked: student_id=%s session_id=%s confidence=%.4f",
        student_id, session_id, confidence,
    )
    return {
        "attendance_id": record.id,
        "student_id": student_id,
        "student_name": match["student_name"],
        "roll_no": match["roll_no"],
        "confidence": confidence,
        "status": "present",
        "message": f"Attendance marked for {match['student_name']} (confidence: {confidence:.1%})",
    }


def get_attendance_by_student(db: Session, student_id: int) -> list:
    records = list(
        db.scalars(
            select(Attendance)
            .where(Attendance.student_id == student_id)
            .order_by(Attendance.attendance_time.desc())
        ).all()
    )
    results = []
    for r in records:
        session = db.get(AttendanceSession, r.session_id)
        results.append({
            "id": r.id,
            "session_id": r.session_id,
            "session_title": session.title if session else "Unknown",
            "subject": session.subject if session else "Unknown",
            "session_date": str(session.session_date) if session else "",
            "attendance_time": r.attendance_time.isoformat() if r.attendance_time else "",
            "confidence": r.confidence,
            "status": r.status,
        })
    return results


def get_attendance_by_session(db: Session, session_id: int) -> list:
    records = list(
        db.scalars(
            select(Attendance)
            .where(Attendance.session_id == session_id)
            .order_by(Attendance.attendance_time)
        ).all()
    )
    results = []
    for r in records:
        student = db.get(Student, r.student_id)
        results.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": student.name if student else "Unknown",
            "roll_no": student.roll_no if student else "",
            "department": student.department if student else "",
            "attendance_time": r.attendance_time.isoformat() if r.attendance_time else "",
            "confidence": r.confidence,
            "status": r.status,
        })
    return results
