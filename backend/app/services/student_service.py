"""Student CRUD service."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.student import Student
from app.models.user import User, UserRole
from app.services import face_service, minio_service

logger = logging.getLogger(__name__)


def register_student(
    db: Session,
    name: str,
    roll_no: str,
    department: str,
    email: str,
    password: str,
    image_bytes: bytes,
) -> Student:
    """Full registration flow: validate face → upload to MinIO → store embedding → create records."""

    # 1. Ensure roll_no / email / username are unique
    existing_roll = db.scalar(select(Student).where(Student.roll_no == roll_no))
    if existing_roll:
        raise ValueError(f"Roll number '{roll_no}' already registered")

    existing_email = db.scalar(select(Student).where(Student.email == email))
    if existing_email:
        raise ValueError(f"Email '{email}' already registered")

    existing_user = db.scalar(select(User).where(User.username == roll_no))
    if existing_user:
        raise ValueError(f"Username '{roll_no}' already exists")

    # 2. Extract face embedding (raises ValueError if no face / multiple faces)
    img_bgr = face_service.bytes_to_bgr(image_bytes)
    embedding = face_service.extract_embedding(img_bgr)
    embedding_str = face_service.embedding_to_str(embedding)

    # 3. Upload image to MinIO
    try:
        image_url = minio_service.upload_image(roll_no, image_bytes, "profile.jpg")
    except Exception as exc:
        logger.warning("MinIO upload failed, continuing without image URL: %s", exc)
        image_url = None

    # 4. Create User record
    user = User(
        username=roll_no,
        password_hash=hash_password(password),
        role=UserRole.student,
        must_change_password=(password == roll_no),  # flag default-password students
    )
    db.add(user)
    db.flush()  # get user.id

    # 5. Create Student record
    student = Student(
        user_id=user.id,
        roll_no=roll_no,
        name=name,
        department=department,
        email=email,
        face_embedding=embedding_str,
        image_url=image_url,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info("Registered student: %s (roll: %s)", name, roll_no)
    return student


def list_students(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.created_at.desc())).all())


def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def delete_student(db: Session, student_id: int) -> bool:
    student = db.get(Student, student_id)
    if not student:
        return False
    # Remove MinIO image if present
    if student.image_url:
        minio_service.delete_image(student.image_url)
    # Remove linked user
    user = db.get(User, student.user_id)
    db.delete(student)
    if user:
        db.delete(user)
    db.commit()
    logger.info("Deleted student id=%s", student_id)
    return True
