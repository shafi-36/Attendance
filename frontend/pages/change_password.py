"""Force-change-password page for first-time student login."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from utils.api import api_post, handle_error
from utils.session import clear_session, require_login

st.set_page_config(page_title="Change Password — AttendAI", page_icon="🔑", layout="centered")

require_login()

st.markdown("## 🔑 Change Your Password")
st.info("You are using a default password. Please set a new password to continue.")

with st.form("change_password_form"):
    new_pw = st.text_input("New Password", type="password", placeholder="Minimum 6 characters")
    confirm_pw = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
    submitted = st.form_submit_button("Set New Password", use_container_width=True)

    if submitted:
        if len(new_pw) < 6:
            st.error("Password must be at least 6 characters.")
        elif new_pw != confirm_pw:
            st.error("Passwords do not match.")
        else:
            resp = api_post("/auth/change-password", json={"new_password": new_pw})
            if not handle_error(resp, "Password change"):
                st.session_state["must_change_password"] = False
                st.success("✅ Password changed successfully! Redirecting…")
                st.rerun()

st.divider()
if st.button("Logout"):
    clear_session()
    st.switch_page("app.py")
