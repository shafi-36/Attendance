"""Faculty attendance viewer — select session, see who is present."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from utils.api import api_get, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Attendance — AttendAI", page_icon="📊", layout="wide")
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
    if st.button("📋 Sessions", use_container_width=True):
        st.switch_page("pages/attendance_sessions.py")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# 📊 Attendance Records")
st.divider()

# ── Load sessions ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=20)
def fetch_sessions():
    try:
        resp = api_get("/sessions/all")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

sessions = fetch_sessions()

if not sessions:
    st.info("No sessions created yet.")
    if st.button("📋 Create a Session"):
        st.switch_page("pages/attendance_sessions.py")
    st.stop()

# ── Session selector ──────────────────────────────────────────────────────────
session_opts = {
    f"{s['title']} | {s['subject']} | {s['session_date']} [{s['status']}]": s["id"]
    for s in sessions
}

# Pre-select if coming from sessions page
default_label = None
preselect_id = st.session_state.pop("view_session_id", None)
if preselect_id:
    for label, sid in session_opts.items():
        if sid == preselect_id:
            default_label = label
            break

selected_label = st.selectbox(
    "Select Session",
    list(session_opts.keys()),
    index=list(session_opts.keys()).index(default_label) if default_label else 0,
)
selected_id = session_opts[selected_label]

col_ref, _ = st.columns([1, 5])
with col_ref:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Attendance records for selected session ───────────────────────────────────
@st.cache_data(ttl=15)
def fetch_attendance(session_id: int):
    try:
        resp = api_get(f"/attendance/session/{session_id}")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

records = fetch_attendance(selected_id)

# Find selected session info
sel_session = next((s for s in sessions if s["id"] == selected_id), {})
status_badge = "🟢 Active" if sel_session.get("status") == "active" else "🔴 Closed"

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric("Session", sel_session.get("title", "—"))
with col_info2:
    st.metric("Subject", sel_session.get("subject", "—"))
with col_info3:
    st.metric("Present Count", len(records))

st.markdown(f"**Status:** {status_badge} · **Date:** {sel_session.get('session_date', '—')}")
st.divider()

if not records:
    st.info("No attendance marked for this session yet.")
else:
    df = pd.DataFrame(
        [
            {
                "Roll No": r["roll_no"],
                "Name": r["student_name"],
                "Department": r["department"],
                "Marked At": r["attendance_time"][:19].replace("T", " "),
                "Confidence": f"{r['confidence']:.1%}",
                "Status": r["status"].capitalize(),
            }
            for r in records
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Summary
    st.markdown(f"**Total Present: {len(records)}**")
