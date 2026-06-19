"""Session state helpers for Streamlit pages."""
import streamlit as st


def require_login(role: str | None = None) -> bool:
    """
    Guard a page. Returns True if authenticated (and role matches).
    Shows an error and stops rendering if not logged in.
    """
    if not st.session_state.get("token"):
        st.error("🔒 Please log in to access this page.")
        st.stop()
        return False

    if role and st.session_state.get("role") != role:
        st.error(f"⛔ This page requires {role} access.")
        st.stop()
        return False

    return True


def require_password_change() -> None:
    """Redirect students who haven't changed their default password."""
    if st.session_state.get("must_change_password"):
        st.warning("⚠️ You must change your default password before continuing.")
        st.stop()


def clear_session() -> None:
    for key in ["token", "role", "username", "user_id", "student_id", "must_change_password"]:
        st.session_state.pop(key, None)


def is_faculty() -> bool:
    return st.session_state.get("role") == "faculty"


def is_student() -> bool:
    return st.session_state.get("role") == "student"


def is_hod() -> bool:
    return st.session_state.get("role") == "hod"


def get_student_id() -> int | None:
    return st.session_state.get("student_id")
