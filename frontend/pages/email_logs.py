"""Email automation logs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from utils.api import api_get
from utils.session import clear_session, require_login

st.set_page_config(page_title="Email Logs - AttendAI", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### AttendAI")
    if st.button("Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("Reports", use_container_width=True):
        st.switch_page("pages/reports.py")
    st.divider()
    if st.button("Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Email Logs")
resp = api_get("/email-logs")
logs = resp.json() if resp.status_code == 200 else []
if logs:
    st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
else:
    st.info("No email automation logs yet.")

