"""Student dashboard — profile card and navigation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date

import streamlit as st
from utils.api import api_get
from utils.session import clear_session, get_student_id, require_login, require_password_change

st.set_page_config(page_title="Student Dashboard — AttendAI", page_icon="🧑‍🎓", layout="wide")
require_login(role="student")
require_password_change()

student_id = get_student_id()

with st.sidebar:
    st.markdown("### 🎓 AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")
    if st.button("📸 Mark Attendance", use_container_width=True):
        st.switch_page("pages/mark_attendance.py")
    if st.button("📅 My History", use_container_width=True):
        st.switch_page("pages/attendance_history.py")
    if st.button("Attendance Reports", use_container_width=True):
        st.switch_page("pages/student_reports.py")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# 🧑‍🎓 Student Dashboard")
st.markdown(f"Welcome, **{st.session_state.get('username')}** · {date.today().strftime('%A, %d %B %Y')}")
st.divider()

# ── Fetch student profile ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_profile(sid: int):
    if not sid:
        return None
    try:
        resp = api_get(f"/students/{sid}")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=30)
def fetch_history(sid: int):
    if not sid:
        return []
    try:
        resp = api_get("/attendance/my-history")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


profile = fetch_profile(student_id)
history = fetch_history(student_id)

# ── Profile Card ───────────────────────────────────────────────────────────────
col_prof, col_stats = st.columns([1, 2], gap="large")

with col_prof:
    st.markdown("### 👤 Profile")
    if profile:
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 1.5rem;
        ">
            <p style="font-size:1.5rem; font-weight:700; margin:0;">{profile['name']}</p>
            <p style="color:#a78bfa; margin:0.25rem 0;">🎫 {profile['roll_no']}</p>
            <p style="color:rgba(255,255,255,0.6); margin:0;">🏛️ {profile['department']}</p>
            <p style="color:rgba(255,255,255,0.6); margin:0;">📧 {profile['email']}</p>
            <p style="color:{'#34d399' if profile.get('image_url') else '#f87171'}; margin-top:0.75rem;">
                {'✅ Face Enrolled' if profile.get('image_url') else '❌ No Face Photo'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Profile not loaded.")

with col_stats:
    st.markdown("### 📊 Attendance Summary")
    total = len(history)
    today_count = sum(1 for h in history if h.get("session_date") == date.today().isoformat())

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Sessions Attended", total)
    with m2:
        st.metric("Today", today_count)
    with m3:
        if total > 0:
            avg_conf = sum(h["confidence"] for h in history) / total
            st.metric("Avg Confidence", f"{avg_conf:.1%}")
        else:
            st.metric("Avg Confidence", "—")

    st.divider()
    st.markdown("### ⚡ Quick Actions")
    a1, a2 = st.columns(2)
    with a1:
        if st.button("📸 Mark Attendance Now", use_container_width=True):
            st.switch_page("pages/mark_attendance.py")
    with a2:
        if st.button("📅 View Full History", use_container_width=True):
            st.switch_page("pages/attendance_history.py")
    if st.button("View Attendance Report", use_container_width=True):
        st.switch_page("pages/student_reports.py")

# ── Recent attendance ──────────────────────────────────────────────────────────
if history:
    st.divider()
    st.markdown("### 🕐 Recent Attendance")
    import pandas as pd
    df = pd.DataFrame([
        {
            "Session": h["session_title"],
            "Subject": h["subject"],
            "Date": h["session_date"],
            "Time": h["attendance_time"][11:19] if h.get("attendance_time") else "",
            "Confidence": f"{h['confidence']:.1%}",
            "Status": h["status"].capitalize(),
        }
        for h in history[:5]
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
