"""Attendance sessions — create and manage sessions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date, time

import streamlit as st
from utils.api import api_get, api_post, api_put, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Sessions — AttendAI", page_icon="📋", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### 🎓 AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("➕ Register Student", use_container_width=True):
        st.switch_page("pages/register_student.py")
    if st.button("👥 Students", use_container_width=True):
        st.switch_page("pages/students.py")
    if st.button("📊 View Attendance", use_container_width=True):
        st.switch_page("pages/attendance_page.py")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# 📋 Attendance Sessions")
st.divider()

col_create, col_list = st.columns([1, 1.5], gap="large")

# ── Create Session Form ────────────────────────────────────────────────────────
with col_create:
    st.markdown("### 🆕 Create New Session")
    with st.form("create_session_form"):
        title = st.text_input("Session Title *", placeholder="e.g. Morning Lecture")
        subject = st.text_input("Subject *", placeholder="e.g. Data Structures")
        session_date = st.date_input("Date *", value=date.today())
        c1, c2 = st.columns(2)
        with c1:
            start_time = st.time_input("Start Time *", value=time(9, 0))
        with c2:
            end_time = st.time_input("End Time", value=time(10, 0))
        submitted = st.form_submit_button("🗓️ Create Session", use_container_width=True)

        if submitted:
            if not title or not subject:
                st.error("Title and Subject are required.")
            else:
                payload = {
                    "title": title.strip(),
                    "subject": subject.strip(),
                    "session_date": session_date.isoformat(),
                    "start_time": start_time.strftime("%H:%M:%S"),
                    "end_time": end_time.strftime("%H:%M:%S") if end_time else None,
                }
                resp = api_post("/sessions", json=payload)
                if not handle_error(resp, "Create session"):
                    data = resp.json()
                    st.success(f"✅ Session **{data['title']}** created! ID: `{data['id']}`")
                    st.cache_data.clear()
                    st.rerun()

# ── Sessions List ──────────────────────────────────────────────────────────────
with col_list:
    st.markdown("### 📑 Your Sessions")

    @st.cache_data(ttl=15)
    def fetch_sessions():
        try:
            resp = api_get("/sessions")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    col_ref, col_filt = st.columns([1, 2])
    with col_ref:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col_filt:
        status_filter = st.selectbox("Filter", ["All", "active", "closed"], label_visibility="collapsed")

    sessions = fetch_sessions()
    filtered = sessions if status_filter == "All" else [s for s in sessions if s["status"] == status_filter]

    if not filtered:
        st.info("No sessions found. Create one on the left.")
    else:
        for sess in filtered:
            status_color = "🟢" if sess["status"] == "active" else "🔴"
            with st.container():
                sc1, sc2, sc3 = st.columns([3, 2, 1])
                with sc1:
                    st.markdown(f"**{sess['title']}**")
                    st.caption(f"📚 {sess['subject']} · 📅 {sess['session_date']}")
                with sc2:
                    st.markdown(f"{status_color} {sess['status'].capitalize()}")
                    st.caption(f"🕐 {sess['start_time'][:5]}")
                with sc3:
                    if sess["status"] == "active":
                        if st.button("🔒 Close", key=f"close_{sess['id']}"):
                            resp = api_put(f"/sessions/{sess['id']}/close")
                            if not handle_error(resp, "Close session"):
                                st.success("Session closed.")
                                st.cache_data.clear()
                                st.rerun()
                    else:
                        if st.button("👁️ View", key=f"view_{sess['id']}"):
                            st.session_state["view_session_id"] = sess["id"]
                            st.switch_page("pages/attendance_page.py")
                st.divider()
