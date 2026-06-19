from sqlalchemy import select

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.student import Student
from app.models.user import User, UserRole


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        faculty = db.scalar(select(User).where(User.username == "faculty"))
        if not faculty:
            faculty = User(
                username="faculty",
                password_hash=hash_password("faculty123"),
                role=UserRole.faculty,
            )
            db.add(faculty)

        hod = db.scalar(select(User).where(User.username == "hod"))
        if not hod:
            hod = User(
                username="hod",
                password_hash=hash_password("hod123"),
                role=UserRole.hod,
            )
            db.add(hod)

        student_user = db.scalar(select(User).where(User.username == "22EC001"))
        if not student_user:
            student_user = User(
                username="22EC001",
                password_hash=hash_password("22EC001"),
                role=UserRole.student,
            )
            db.add(student_user)
            db.flush()
            db.add(
                Student(
                    user_id=student_user.id,
                    roll_no="22EC001",
                    name="Demo Student",
                    department="ECE",
                    email="demo.student@example.com",
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seeded demo users: faculty/faculty123, hod/hod123, and 22EC001/22EC001")
