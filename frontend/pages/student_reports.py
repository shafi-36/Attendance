"""Student attendance report page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from utils.api import api_get
from utils.session import clear_session, require_login, require_password_change

st.set_page_config(page_title="My Attendance Report - AttendAI", layout="wide")
require_login(role="student")
require_password_change()

with st.sidebar:
    if st.button("Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")
    if st.button("History", use_container_width=True):
        st.switch_page("pages/attendance_history.py")
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# My Attendance Report")
resp = api_get("/analytics/student/me")
summary = resp.json() if resp.status_code == 200 else {}

if not summary:
    st.info("Attendance summary is not available yet.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attendance", f"{summary.get('attendance_percentage', 0)}%")
    c2.metric("Present", summary.get("present_sessions", 0))
    c3.metric("Absent", summary.get("absent_sessions", 0))
    c4.metric("Total Sessions", summary.get("total_sessions", 0))

    if summary.get("warning"):
        st.warning(
            "Your attendance is below 75%. Continued absence may affect eligibility requirements."
        )
    else:
        st.success("Your attendance is currently above the warning threshold.")

    trend = summary.get("trend", {})
    st.markdown("### Trend Analysis")
    st.write(
        f"Current 30-day attendance is {trend.get('current_30_day_percentage', 0)}%. "
        f"Change from previous 30 days: {trend.get('change', 0)}%."
    )

