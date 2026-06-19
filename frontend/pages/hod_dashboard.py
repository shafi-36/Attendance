"""HoD dashboard."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from utils.api import api_get, api_post, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="HoD Dashboard - AttendAI", layout="wide")
require_login(role="hod")

with st.sidebar:
    st.markdown("### AttendAI HoD")
    if st.button("Department Analytics", use_container_width=True):
        st.switch_page("pages/hod_dashboard.py")
    if st.button("Email Logs", use_container_width=True):
        st.switch_page("pages/hod_email_logs.py")
    st.divider()
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Department Analytics")
overview_resp = api_get("/analytics/overview")
overview = overview_resp.json() if overview_resp.status_code == 200 else {}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Students", overview.get("total_students", 0))
c2.metric("Closed Sessions", overview.get("closed_sessions", 0))
c3.metric("Average Attendance", f"{overview.get('average_attendance', 0)}%")
c4.metric("Below 75%", overview.get("low_attendance_count", 0))

trend = overview.get("trend", {})
st.markdown("### Attendance Trends")
st.write(
    f"Current 30-day attendance is {trend.get('current_30_day_percentage', 0)}%. "
    f"Previous 30-day attendance was {trend.get('previous_30_day_percentage', 0)}%."
)

st.markdown("### AI Reports")
if st.button("Generate Department Summary", use_container_width=True):
    resp = api_post("/reports/weekly-department?notify_hod=true")
    if not handle_error(resp, "Generate HoD report"):
        st.success("Department report generated.")
        st.write(resp.json()["report_text"])

reports_resp = api_get("/reports")
reports = reports_resp.json() if reports_resp.status_code == 200 else []
if reports:
    st.dataframe(pd.DataFrame(reports), use_container_width=True, hide_index=True)

st.markdown("### Low Attendance")
low_resp = api_get("/analytics/low-attendance")
low = low_resp.json() if low_resp.status_code == 200 else []
if low:
    st.dataframe(pd.DataFrame(low), use_container_width=True, hide_index=True)
else:
    st.success("No low-attendance students.")

