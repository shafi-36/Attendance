"""Student attendance history page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from utils.api import api_get
from utils.session import clear_session, require_login, require_password_change

st.set_page_config(page_title="Attendance History — AttendAI", page_icon="📅", layout="wide")
require_login(role="student")
require_password_change()

with st.sidebar:
    st.markdown("### 🎓 AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")
    if st.button("📸 Mark Attendance", use_container_width=True):
        st.switch_page("pages/mark_attendance.py")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# 📅 My Attendance History")
st.divider()

@st.cache_data(ttl=30)
def fetch_history():
    try:
        resp = api_get("/attendance/my-history")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

col_ref, _ = st.columns([1, 5])
with col_ref:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

history = fetch_history()

if not history:
    st.info("No attendance records yet. Go mark your first attendance!")
    if st.button("📸 Mark Attendance Now"):
        st.switch_page("pages/mark_attendance.py")
    st.stop()

# ── Summary metrics ────────────────────────────────────────────────────────────
total = len(history)
avg_conf = sum(h["confidence"] for h in history) / total if total > 0 else 0
subjects = {h["subject"] for h in history}

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Sessions Attended", total)
with m2:
    st.metric("Avg. Confidence", f"{avg_conf:.1%}")
with m3:
    st.metric("Subjects", len(subjects))

st.divider()

# ── Filter ─────────────────────────────────────────────────────────────────────
col_subj, col_date = st.columns(2)
with col_subj:
    subj_opts = ["All"] + sorted(subjects)
    subj_filter = st.selectbox("Filter by Subject", subj_opts)
with col_date:
    date_filter = st.text_input("Filter by Date (YYYY-MM-DD)", placeholder="e.g. 2026-06-19")

filtered = history
if subj_filter != "All":
    filtered = [h for h in filtered if h["subject"] == subj_filter]
if date_filter:
    filtered = [h for h in filtered if h.get("session_date", "").startswith(date_filter)]

st.caption(f"Showing {len(filtered)} of {total} records")

# ── Table ─────────────────────────────────────────────────────────────────────
if filtered:
    df = pd.DataFrame([
        {
            "Session": h["session_title"],
            "Subject": h["subject"],
            "Date": h["session_date"],
            "Time Marked": h["attendance_time"][11:19] if h.get("attendance_time") else "—",
            "Confidence": f"{h['confidence']:.1%}",
            "Status": "✅ Present" if h["status"] == "present" else h["status"],
        }
        for h in filtered
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("No records match the current filters.")
