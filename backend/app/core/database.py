from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.resolved_database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema(engine)


def _migrate_sqlite_schema(db_engine: Engine) -> None:
    """Apply small local SQLite migrations for existing development databases."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        user_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(users)")}
        if "must_change_password" not in user_columns:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0"
            )

        session_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(attendance_sessions)")
        }
        if "title" not in session_columns:
            connection.exec_driver_sql(
                "ALTER TABLE attendance_sessions "
                "ADD COLUMN title VARCHAR(200) NOT NULL DEFAULT 'Attendance Session'"
            )
