import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    FacultyLoginRequest,
    LoginResponse,
    StudentLoginRequest,
)
from app.services.auth_service import change_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def faculty_login(payload: FacultyLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(
        select(User).where(
            User.username == payload.username,
            User.role.in_([UserRole.faculty, UserRole.hod]),
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid faculty or HoD credentials",
        )
    token = create_access_token(subject=str(user.id), data={"role": user.role.value})
    return LoginResponse(
        access_token=token,
        role=user.role.value,
        user_id=user.id,
        username=user.username,
        must_change_password=user.must_change_password,
    )


@router.post("/student-login", response_model=LoginResponse)
def student_login(payload: StudentLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    student = db.scalar(select(Student).where(Student.roll_no == payload.roll_no))
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student credentials",
        )
    user = db.get(User, student.user_id)
    if not user or user.role != UserRole.student or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student credentials",
        )
    token = create_access_token(
        subject=str(user.id),
        data={"role": user.role.value, "student_id": student.id},
    )
    return LoginResponse(
        access_token=token,
        role=user.role.value,
        user_id=user.id,
        username=student.roll_no,
        student_id=student.id,
        must_change_password=user.must_change_password,
    )


@router.post("/change-password")
def change_user_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        change_password(db, current_user.id, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"message": "Logged out"}
