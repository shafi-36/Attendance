"""Streamlit app entry point — login and routing shell."""
import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8010")

st.set_page_config(
    page_title="AttendAI — Smart Attendance",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject global CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* Login card */
.login-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 24px;
    padding: 2.5rem 2rem;
    backdrop-filter: blur(20px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.4);
}

/* Hero title */
.hero-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.25rem;
}

.hero-sub {
    color: rgba(255,255,255,0.55);
    text-align: center;
    font-size: 1rem;
    margin-bottom: 2rem;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.3);
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #a78bfa;
}
.metric-label {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.55);
    margin-top: 0.25rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(124,58,237,0.4) !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
}

/* Success / error / warning */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 10px !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(15,12,41,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}

/* Table */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Form */
.stForm {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Login helpers ──────────────────────────────────────────────────────────────
def do_login(endpoint: str, payload: dict) -> None:
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=10)
    except requests.RequestException as exc:
        st.error(f"Backend unavailable: {exc}")
        return

    if resp.status_code != 200:
        detail = resp.json().get("detail", "Login failed")
        st.error(detail)
        return

    data = resp.json()
    st.session_state["token"] = data["access_token"]
    st.session_state["role"] = data["role"]
    st.session_state["username"] = data["username"]
    st.session_state["user_id"] = data["user_id"]
    st.session_state["student_id"] = data.get("student_id")
    st.session_state["must_change_password"] = data.get("must_change_password", False)
    st.rerun()


# ── If already logged in → redirect ───────────────────────────────────────────
if st.session_state.get("token"):
    role = st.session_state["role"]
    if st.session_state.get("must_change_password"):
        st.switch_page("pages/change_password.py")
    elif role == "faculty":
        st.switch_page("pages/faculty_dashboard.py")
    elif role == "hod":
        st.switch_page("pages/hod_dashboard.py")
    else:
        st.switch_page("pages/student_dashboard.py")

# ── Login UI ───────────────────────────────────────────────────────────────────
col_l, col_c, col_r = st.columns([1, 1.4, 1])
with col_c:
    st.markdown('<div class="hero-title">🎓 AttendAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">AI-Powered Attendance Management</div>', unsafe_allow_html=True)

    with st.container():
        tab_fac, tab_hod, tab_stu = st.tabs(["Faculty Login", "HoD Login", "Student Login"])

        with tab_fac:
            with st.form("faculty_login_form"):
                username = st.text_input("Username", placeholder="faculty username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login as Faculty", use_container_width=True)
                if submitted:
                    if username and password:
                        do_login("/auth/login", {"username": username, "password": password})
                    else:
                        st.warning("Please enter both username and password.")

        with tab_hod:
            with st.form("hod_login_form"):
                username_h = st.text_input("Username", placeholder="hod", key="hod_username")
                password_h = st.text_input("Password", type="password", placeholder="password", key="hod_password")
                submitted_h = st.form_submit_button("Login as HoD", use_container_width=True)
                if submitted_h:
                    if username_h and password_h:
                        do_login("/auth/login", {"username": username_h, "password": password_h})
                    else:
                        st.warning("Please enter both username and password.")

        with tab_stu:
            with st.form("student_login_form"):
                roll_no = st.text_input("Roll Number", placeholder="e.g. 22EC001")
                password_s = st.text_input("Password", type="password", placeholder="••••••••")
                submitted_s = st.form_submit_button("Login as Student", use_container_width=True)
                if submitted_s:
                    if roll_no and password_s:
                        do_login("/auth/student-login", {"roll_no": roll_no, "password": password_s})
                    else:
                        st.warning("Please enter roll number and password.")

    st.markdown(
        '<p style="text-align:center;color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:2rem;">'
        "Default student password = Roll Number</p>",
        unsafe_allow_html=True,
    )
