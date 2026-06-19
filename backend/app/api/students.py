"""Student registration and management endpoints."""
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_faculty
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.student import StudentListItem, StudentOut
from app.services import student_service
from app.services.minio_service import get_presigned_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/students", tags=["students"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/register", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def register_student(
    name: str = Form(...),
    roll_no: str = Form(...),
    department: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _faculty: User = Depends(require_faculty),
) -> StudentOut:
    # Validate image
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported image type: {image.content_type}. Use JPEG or PNG.",
        )
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large. Maximum 10 MB.",
        )
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty image file.",
        )

    try:
        student = student_service.register_student(
            db=db,
            name=name.strip(),
            roll_no=roll_no.strip(),
            department=department.strip(),
            email=email.strip(),
            password=password,
            image_bytes=image_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error("Student registration failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return StudentOut.model_validate(student)


@router.get("", response_model=list[StudentListItem])
def list_students(
    db: Session = Depends(get_db),
    _faculty: User = Depends(require_faculty),
) -> list[StudentListItem]:
    students = student_service.list_students(db)
    return [
        StudentListItem(
            id=s.id,
            roll_no=s.roll_no,
            name=s.name,
            department=s.department,
            email=s.email,
            image_url=get_presigned_url(s.image_url) if s.image_url else None,
            has_embedding=bool(s.face_embedding),
            created_at=s.created_at,
        )
        for s in students
    ]


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentOut:
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if current_user.role == UserRole.student and student.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role not in {UserRole.faculty, UserRole.student}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return StudentOut.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _faculty: User = Depends(require_faculty),
) -> None:
    deleted = student_service.delete_student(db, student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
