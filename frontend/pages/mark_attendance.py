"""Mark attendance with camera capture or image upload."""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
import streamlit as st
from utils.api import api_get, api_post, handle_error
from utils.session import clear_session, require_login, require_password_change

st.set_page_config(page_title="Mark Attendance - AttendAI", page_icon="📸", layout="wide")
require_login(role="student")
require_password_change()


with st.sidebar:
    st.markdown("### AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("Dashboard", use_container_width=True, key="mark_nav_dashboard"):
        st.switch_page("pages/student_dashboard.py")
    if st.button("My History", use_container_width=True, key="mark_nav_history"):
        st.switch_page("pages/attendance_history.py")
    st.divider()
    if st.button("Logout", use_container_width=True, key="mark_nav_logout"):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Mark Attendance")
st.markdown("Select an active session, take or upload your face photo, and submit.")
st.divider()


@st.cache_data(ttl=20)
def fetch_active_sessions():
    try:
        resp = api_get("/sessions/active")
        if resp.status_code == 200:
            return resp.json()
        return []
    except requests.RequestException:
        return []


active_sessions = fetch_active_sessions()

if not active_sessions:
    st.warning("No active sessions available right now. Ask your faculty to open a session.")
    st.stop()

session_opts = {
    f"{s['title']} - {s['subject']} ({s['session_date']})": s["id"]
    for s in active_sessions
}
selected_label = st.selectbox("Select Active Session", list(session_opts.keys()))
selected_session_id = session_opts[selected_label]

st.divider()

col_photo, col_submit = st.columns([1.2, 1], gap="large")

with col_photo:
    st.markdown("### Face Photo")
    camera_photo = st.camera_input("Take photo")
    uploaded_file = st.file_uploader("Or upload photo", type=["jpg", "jpeg", "png", "webp"])

    image_file = uploaded_file or camera_photo
    if image_file:
        st.image(image_file, caption="Ready to submit", use_container_width=True)
    else:
        st.info("Take a photo or upload an image to continue.")

with col_submit:
    st.markdown("### Submit")
    st.caption(f"Session: **{selected_label}**")

    if st.button("Mark My Attendance", use_container_width=True, type="primary"):
        if image_file is None:
            st.error("Please take or upload your photo first.")
        else:
            with st.spinner("Verifying your identity..."):
                b64_img = base64.b64encode(image_file.getvalue()).decode("utf-8")
                try:
                    resp = api_post(
                        "/attendance/mark",
                        json={"session_id": selected_session_id, "image_base64": b64_img},
                    )
                except requests.RequestException as exc:
                    st.error(f"Attendance request failed: {exc}")
                    st.stop()

            if resp.status_code == 200:
                data = resp.json()
                st.success(data["message"])
                st.write(f"Student: {data['student_name']}")
                st.write(f"Roll: {data['roll_no']}")
                st.write(f"Confidence: {data['confidence']:.1%}")
                st.write(f"Status: {data['status'].capitalize()}")
                st.cache_data.clear()
            else:
                handle_error(resp, "Attendance")
                try:
                    detail = resp.json().get("detail", "")
                    if "already" in detail.lower():
                        st.info("Your attendance was already recorded for this session.")
                except Exception:
                    pass

    st.divider()
    st.markdown("**Tips for best results:**")
    st.markdown(
        """
        - Use good lighting
        - Look directly at the camera
        - Keep only one face in frame
        - Remove sunglasses or face coverings
        """
    )
