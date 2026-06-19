"""Student registration page with camera capture and file upload fallback."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
import streamlit as st
from utils.api import api_post_form, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Register Student - AttendAI", page_icon="➕", layout="wide")
require_login(role="faculty")


with st.sidebar:
    st.markdown("### AttendAI")
    st.markdown(f"**{st.session_state.get('username')}**")
    st.divider()
    if st.button("Dashboard", use_container_width=True, key="register_nav_dashboard"):
        st.switch_page("pages/faculty_dashboard.py")
    if st.button("All Students", use_container_width=True, key="register_nav_students"):
        st.switch_page("pages/students.py")
    if st.button("Sessions", use_container_width=True, key="register_nav_sessions"):
        st.switch_page("pages/attendance_sessions.py")
    st.divider()
    if st.button("Logout", use_container_width=True, key="register_nav_logout"):
        clear_session()
        st.switch_page("app.py")

st.markdown("# Register New Student")
st.markdown("Fill in the student details and take or upload a clear face photo.")
st.divider()

col_form, col_photo = st.columns([1, 1], gap="large")

with col_photo:
    st.markdown("### Face Photo")
    camera_photo = st.camera_input("Take photo")
    uploaded_file = st.file_uploader("Or upload photo", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded photo", use_container_width=True)
    elif camera_photo:
        st.image(camera_photo, caption="Camera photo", use_container_width=True)
    else:
        st.info("Use the camera or upload a face photo before registering.")

with col_form:
    st.markdown("### Student Details")
    with st.form("register_form", clear_on_submit=False):
        name = st.text_input("Full Name *", placeholder="e.g. Priya Sharma")
        roll_no = st.text_input("Roll Number *", placeholder="e.g. 24CSB22")
        department = st.selectbox("Department *", ["CSE", "ECE", "EEE", "ME", "CE", "IT", "Other"])
        email = st.text_input("Email *", placeholder="student@college.edu")
        password = st.text_input(
            "Initial Password",
            placeholder="Leave blank to use Roll No as default",
            type="password",
        )
        submitted = st.form_submit_button("Register Student", use_container_width=True)

    if submitted:
        image_file = uploaded_file or camera_photo

        if not name.strip() or not roll_no.strip() or not email.strip():
            st.error("Name, Roll Number, and Email are required.")
        elif image_file is None:
            st.error("Please take or upload a face photo.")
        else:
            image_bytes = image_file.getvalue()
            effective_password = password.strip() if password.strip() else roll_no.strip()
            with st.spinner("Registering student and detecting face..."):
                try:
                    resp = api_post_form(
                        "/students/register",
                        data={
                            "name": name.strip(),
                            "roll_no": roll_no.strip(),
                            "department": department,
                            "email": email.strip(),
                            "password": effective_password,
                        },
                        files={"image": ("profile.jpg", image_bytes, "image/jpeg")},
                        timeout=180,
                    )
                except requests.Timeout:
                    st.error(
                        "Registration timed out while the face model was loading. "
                        "Wait a moment, then click Register Student again."
                    )
                    st.stop()
                except requests.RequestException as exc:
                    st.error(f"Registration request failed: {exc}")
                    st.stop()

            if not handle_error(resp, "Registration"):
                st.success(f"{name} registered successfully. Roll: {roll_no} | Dept: {department}")
                st.cache_data.clear()
