"""Faculty AI reports page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from utils.api import api_get, api_post, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Reports - AttendAI", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### AttendAI")
    if st.button("Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("Analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")
    if st.button("Email Logs", use_container_width=True):
        st.switch_page("pages/email_logs.py")
    st.divider()
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Reports")

sessions_resp = api_get("/sessions")
sessions = sessions_resp.json() if sessions_resp.status_code == 200 else []
closed_sessions = [s for s in sessions if s.get("status") == "closed"]

col_session, col_department = st.columns(2)
with col_session:
    st.markdown("### Session Summary")
    if closed_sessions:
        options = {f"{s['title']} - {s['session_date']}": s["id"] for s in closed_sessions}
        selected = st.selectbox("Closed session", list(options.keys()))
        notify = st.checkbox("Email faculty after generating")
        if st.button("Generate Session Report", use_container_width=True):
            resp = api_post(f"/reports/session/{options[selected]}/summary?notify_faculty={str(notify).lower()}")
            if not handle_error(resp, "Generate report"):
                st.success("Report generated.")
                st.write(resp.json()["report_text"])
    else:
        st.info("Close a session to generate a session report.")

with col_department:
    st.markdown("### Weekly Department Report")
    notify_hod = st.checkbox("Email HoD after generating")
    if st.button("Generate Weekly Report", use_container_width=True):
        resp = api_post(f"/reports/weekly-department?notify_hod={str(notify_hod).lower()}")
        if not handle_error(resp, "Generate weekly report"):
            st.success("Weekly report generated.")
            st.write(resp.json()["report_text"])

st.divider()
st.markdown("### Generated Reports")
reports_resp = api_get("/reports")
if reports_resp.status_code == 200 and reports_resp.json():
    st.dataframe(pd.DataFrame(reports_resp.json()), use_container_width=True, hide_index=True)
else:
    st.info("No reports generated yet.")

