"""Faculty dashboard: overview cards and navigation."""
import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.api import api_get
from utils.session import clear_session, require_login

st.set_page_config(page_title="Faculty Dashboard - AttendAI", page_icon="🎓", layout="wide")

require_login(role="faculty")


with st.sidebar:
    st.markdown("### AttendAI")
    st.markdown(f"**{st.session_state.get('username', 'Faculty')}**")
    st.divider()
    if st.button("Dashboard", use_container_width=True, key="faculty_nav_dashboard"):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("Register Student", use_container_width=True, key="faculty_nav_register_student"):
        st.switch_page("pages/register_student.py")
    if st.button("All Students", use_container_width=True, key="faculty_nav_students"):
        st.switch_page("pages/students.py")
    if st.button("Attendance Sessions", use_container_width=True, key="faculty_nav_sessions"):
        st.switch_page("pages/attendance_sessions.py")
    if st.button("View Attendance", use_container_width=True, key="faculty_nav_attendance"):
        st.switch_page("pages/attendance_page.py")
    if st.button("Reports", use_container_width=True, key="faculty_nav_reports"):
        st.switch_page("pages/reports.py")
    if st.button("Analytics", use_container_width=True, key="faculty_nav_analytics"):
        st.switch_page("pages/analytics.py")
    if st.button("Email Logs", use_container_width=True, key="faculty_nav_email_logs"):
        st.switch_page("pages/email_logs.py")
    if st.button("AI Insights", use_container_width=True, key="faculty_nav_ai_insights"):
        st.switch_page("pages/ai_insights.py")
    st.divider()
    if st.button("Logout", use_container_width=True, key="faculty_nav_logout"):
        clear_session()
        st.switch_page("app.py")


st.markdown("# Faculty Dashboard")
st.markdown(f"Welcome back, **{st.session_state.get('username')}** - {date.today().strftime('%A, %d %B %Y')}")
st.divider()


@st.cache_data(ttl=30)
def fetch_students():
    try:
        resp = api_get("/students")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


@st.cache_data(ttl=30)
def fetch_sessions():
    try:
        resp = api_get("/sessions/all")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


students = fetch_students()
sessions = fetch_sessions()
today_str = date.today().isoformat()

total_students = len(students)
active_sessions = sum(1 for s in sessions if s.get("status") == "active")
today_sessions = [s for s in sessions if s.get("session_date") == today_str]
registered_today = sum(1 for s in students if s.get("created_at", "").startswith(today_str))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Students", total_students)
c2.metric("Active Sessions", active_sessions)
c3.metric("Today's Sessions", len(today_sessions))
c4.metric("Registered Today", registered_today)

st.divider()

st.markdown("### Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("Register Student", use_container_width=True, key="faculty_quick_register_student"):
        st.switch_page("pages/register_student.py")
with qa2:
    if st.button("View Students", use_container_width=True, key="faculty_quick_students"):
        st.switch_page("pages/students.py")
with qa3:
    if st.button("New Session", use_container_width=True, key="faculty_quick_new_session"):
        st.switch_page("pages/attendance_sessions.py")
with qa4:
    if st.button("View Attendance", use_container_width=True, key="faculty_quick_attendance"):
        st.switch_page("pages/attendance_page.py")

qa5, qa6, qa7 = st.columns(3)
with qa5:
    if st.button("Reports", use_container_width=True, key="faculty_quick_reports"):
        st.switch_page("pages/reports.py")
with qa6:
    if st.button("Analytics", use_container_width=True, key="faculty_quick_analytics"):
        st.switch_page("pages/analytics.py")
with qa7:
    if st.button("Email Logs", use_container_width=True, key="faculty_quick_email_logs"):
        st.switch_page("pages/email_logs.py")

st.divider()

st.markdown("### Recent Registrations")
if students:
    import pandas as pd

    recent = students[:10]
    df = pd.DataFrame(
        [
            {
                "Roll No": s["roll_no"],
                "Name": s["name"],
                "Department": s["department"],
                "Face Enrolled": "Yes" if s.get("has_embedding") else "No",
                "Registered": s.get("created_at", "")[:10],
            }
            for s in recent
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No students registered yet. Click 'Register Student' to get started.")

if today_sessions:
    st.markdown("### Today's Sessions")
    for sess in today_sessions:
        status_badge = "Active" if sess["status"] == "active" else "Closed"
        st.markdown(
            f"**{sess['title']}** - {sess['subject']} | {status_badge} | "
            f"Start: {sess['start_time']}"
        )
