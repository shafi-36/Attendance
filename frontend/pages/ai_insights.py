"""AI insights page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from utils.api import api_get
from utils.session import clear_session, require_login

st.set_page_config(page_title="AI Insights - AttendAI", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### AttendAI")
    if st.button("Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("Reports", use_container_width=True):
        st.switch_page("pages/reports.py")
    if st.button("Analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")
    st.divider()
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# AI Insights")
overview_resp = api_get("/analytics/overview")
reports_resp = api_get("/reports")
overview = overview_resp.json() if overview_resp.status_code == 200 else {}
reports = reports_resp.json() if reports_resp.status_code == 200 else []

st.markdown("### Department Signal")
st.write(
    f"Average attendance is {overview.get('average_attendance', 0)}% with "
    f"{overview.get('low_attendance_count', 0)} students below the warning threshold."
)

if reports:
    st.markdown("### Latest AI Report")
    latest = reports[0]
    st.caption(f"{latest['report_type']} - {latest['generated_at']}")
    st.write(latest["report_text"])
else:
    st.info("Generate a report to see AI insights here.")

