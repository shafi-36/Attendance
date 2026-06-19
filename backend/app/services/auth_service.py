"""Auth service — password change."""
import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User

logger = logging.getLogger(__name__)


def change_password(db: Session, user_id: int, new_password: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    logger.info("Password changed for user_id=%s", user_id)
    return user
