"""All students list — faculty view."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from utils.api import api_delete, api_get, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Students — AttendAI", page_icon="👥", layout="wide")
require_login(role="faculty")

with st.sidebar:
    st.markdown("### 🎓 AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("➕ Register Student", use_container_width=True):
        st.switch_page("pages/register_student.py")
    if st.button("📋 Sessions", use_container_width=True):
        st.switch_page("pages/attendance_sessions.py")
    if st.button("📊 Attendance", use_container_width=True):
        st.switch_page("pages/attendance_page.py")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session()
        st.switch_page("app.py")

st.markdown("# 👥 Registered Students")
st.divider()

@st.cache_data(ttl=20)
def fetch_students():
    try:
        resp = api_get("/students")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

students = fetch_students()

if not students:
    st.info("No students registered yet.")
    if st.button("➕ Register First Student"):
        st.switch_page("pages/register_student.py")
else:
    # Search
    col_search, col_dept, col_btn = st.columns([3, 2, 1])
    with col_search:
        search = st.text_input("🔍 Search by name or roll no", placeholder="Search…", label_visibility="collapsed")
    with col_dept:
        depts = ["All"] + sorted({s["department"] for s in students})
        dept_filter = st.selectbox("Department", depts, label_visibility="collapsed")
    with col_btn:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    # Filter
    filtered = students
    if search:
        s_lower = search.lower()
        filtered = [s for s in filtered if s_lower in s["name"].lower() or s_lower in s["roll_no"].lower()]
    if dept_filter != "All":
        filtered = [s for s in filtered if s["department"] == dept_filter]

    st.caption(f"Showing {len(filtered)} of {len(students)} students")

    # Table + Delete buttons
    for student in filtered:
        with st.container():
            c1, c2, c3, c4, c5, c_del = st.columns([2, 2, 2, 1.5, 1.5, 1])
            with c1:
                st.markdown(f"**{student['name']}**")
                st.caption(student["roll_no"])
            with c2:
                st.markdown(student["department"])
                st.caption(student["email"])
            with c3:
                st.caption(f"Registered: {student.get('created_at', '')[:10]}")
            with c4:
                if student.get("has_embedding"):
                    st.success("✅ Face Enrolled")
                else:
                    st.warning("⚠️ No Face")
            with c5:
                if student.get("image_url"):
                    st.markdown("🖼️ Photo ✓")
            with c_del:
                if st.button("🗑️", key=f"del_{student['id']}", help="Delete student"):
                    st.session_state[f"confirm_del_{student['id']}"] = True

            if st.session_state.get(f"confirm_del_{student['id']}"):
                st.warning(f"⚠️ Delete **{student['name']}** ({student['roll_no']})? This is irreversible.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Confirm Delete", key=f"yes_{student['id']}"):
                        resp = api_delete(f"/students/{student['id']}")
                        if not handle_error(resp, "Delete"):
                            st.success(f"Deleted {student['name']}")
                            st.session_state.pop(f"confirm_del_{student['id']}", None)
                            st.cache_data.clear()
                            st.rerun()
                with col_no:
                    if st.button("❌ Cancel", key=f"no_{student['id']}"):
                        st.session_state.pop(f"confirm_del_{student['id']}", None)
                        st.rerun()

            st.divider()
