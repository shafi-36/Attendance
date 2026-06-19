"""Faculty analytics page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from utils.api import api_get, api_post, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Analytics - AttendAI", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### AttendAI")
    if st.button("Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("Reports", use_container_width=True):
        st.switch_page("pages/reports.py")
    if st.button("AI Insights", use_container_width=True):
        st.switch_page("pages/ai_insights.py")
    st.divider()
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Analytics")

overview_resp = api_get("/analytics/overview")
overview = overview_resp.json() if overview_resp.status_code == 200 else {}

m1, m2, m3, m4 = st.columns(4)
m1.metric("Students", overview.get("total_students", 0))
m2.metric("Closed Sessions", overview.get("closed_sessions", 0))
m3.metric("Average Attendance", f"{overview.get('average_attendance', 0)}%")
m4.metric("Below 75%", overview.get("low_attendance_count", 0))

trend = overview.get("trend", {})
st.caption(
    f"30-day attendance: {trend.get('current_30_day_percentage', 0)}% "
    f"({trend.get('change', 0)}% vs previous 30 days)"
)

st.divider()
st.markdown("### Low Attendance Students")
low_resp = api_get("/analytics/low-attendance")
low = low_resp.json() if low_resp.status_code == 200 else []
if low:
    st.dataframe(pd.DataFrame(low), use_container_width=True, hide_index=True)
    if st.button("Send Warning Emails", use_container_width=True):
        resp = api_post("/reports/low-attendance/send")
        if not handle_error(resp, "Send warnings"):
            st.success("Warnings processed.")
else:
    st.success("No students below the 75% threshold.")

