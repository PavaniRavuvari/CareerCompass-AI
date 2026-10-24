
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from textwrap import dedent

import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from core import auth, db, gemini
from views import (
    assistant,
    ats_page,
    home,
    jobs_page,
    profile,
    recommendations,
    resume_studio,
    roadmap_page,
    skill_gap,
)
from views.ui import inject_css


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
)

inject_css()


# --------------------------------------------------
# Authentication helpers
# --------------------------------------------------

def send_reset_email(email, token):
    """Send a password reset link using configured SMTP settings."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", smtp_user)
    app_url = os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")

    if not all([smtp_host, smtp_user, smtp_password, sender]):
        return False

    reset_url = f"{app_url}/?reset={token}"

    message = EmailMessage()
    message["Subject"] = "Reset your CareerCompass AI password"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        "We received a request to reset your CareerCompass AI password.\n\n"
        f"Open this link within 30 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException, ValueError):
        return False


def show_reset_password():
    """Display the password reset form for a token in the URL."""
    token = st.query_params.get("reset", "")

    st.markdown("## 🔐 Reset your password")
    st.write("Choose a new password for your account.")

    with st.form("reset_password_form"):
        new_password = st.text_input(
            "New password",
            type="password",
            help="Use at least 8 characters.",
        )
        confirm_password = st.text_input(
            "Confirm new password",
            type="password",
        )
        submitted = st.form_submit_button(
            "Update password",
            use_container_width=True,
        )

    if submitted:
        if new_password != confirm_password:
            st.error("The passwords do not match.")
        else:
            success, message = auth.reset_password(token, new_password)
            if success:
                st.success(message)
                st.query_params.clear()
                st.session_state.auth_view = "Login"
                st.rerun()
            else:
                st.error(message)

    if st.button("Back to login"):
        st.query_params.clear()
        st.session_state.auth_view = "Login"
        st.rerun()


def show_auth_screen():
    """Show login, account registration, and password recovery."""
    
    
    st.markdown(
        dedent("""
        <div style="background: linear-gradient(135deg, #201747 0%, #30205F 60%, #6741D9 100%); border-radius: 22px; padding: 38px 24px 34px; margin: 8px 0 28px; text-align: center; box-shadow: 0 10px 28px rgba(32,23,71,0.16);">
            <div style="width: 82px; height: 82px; margin: 0 auto 18px; background: #7957E8; border: 1px solid rgba(255,255,255,0.3); border-radius: 23px; display: flex; justify-content: center; align-items: center; font-size: 49px;">
                🧭
            </div>
            <h1 style="color: #FFFFFF; font-size: clamp(30px, 4vw, 43px); font-weight: 800; line-height: 1.2; margin: 0 0 12px; letter-spacing: -1px;">
                CareerCompass <span style="color: #BDAAFF;">AI</span>
            </h1>
            <p style="color: #E6DEFF; font-size: 19px; margin: 0 0 12px; line-height: 1.5;">
                Your AI-Powered Career Companion
            </p>
            <p style="color: #F5F3FF; font-size: 16px; margin: 0; line-height: 1.7;">
                Build your skills. Discover your path. Move your career forward.
            </p>
        </div>
        """),
        unsafe_allow_html=True,
    )



    _, form_col, _ = st.columns([1, 1.2, 1])

    with form_col:
        st.markdown("---")
        view = st.radio(
            "Choose an option",
            ["Login", "Create Account", "Forgot Password"],
            horizontal=True,
            key="auth_view",
        )

        if view == "Create Account":
            with st.form("register_form", clear_on_submit=False):
                name = st.text_input("Full name")
                email = st.text_input("Email address")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                )

            if submitted:
                if password != confirm:
                    st.error("The passwords do not match.")
                else:
                    success, message, _ = auth.register_user(
                        name, email, password
                    )
                    if success:
                        st.success("Account created! You can now log in.")
                        st.session_state.auth_view = "Login"
                        st.rerun()
                    else:
                        st.error(message)

        elif view == "Login":
            with st.form("login_form"):
                email = st.text_input("Email address")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                )

            if submitted:
                user = auth.authenticate_user(email, password)
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_email = user["email"]
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        else:
            st.write(
                "Enter your registered email address. "
                "If email delivery is configured, we'll send you a reset link."
            )
            with st.form("forgot_password_form"):
                email = st.text_input("Registered email address")
                submitted = st.form_submit_button(
                    "Send Reset Link",
                    use_container_width=True,
                )

            if submitted:
                token = auth.create_reset_token(email)
                if token:
                    if send_reset_email(email.strip().lower(), token):
                        st.success(
                            "If the account exists, a reset email has been sent."
                        )
                    else:
                        st.error(
                            "Email delivery isn't configured or failed. "
                            "Configure SMTP settings before using password recovery."
                        )
                else:
                    # Avoid confirming whether an email is registered.
                    st.success(
                        "If an account exists for that email, "
                        "a reset link can be sent."
                    )


# --------------------------------------------------
# Password reset link handling
# --------------------------------------------------

if st.query_params.get("reset"):
    show_reset_password()
    st.stop()


# --------------------------------------------------
# Require login before showing the dashboard
# --------------------------------------------------

if not st.session_state.get("user_id"):
    show_auth_screen()
    st.stop()


# --------------------------------------------------
# Page navigation — existing pages preserved
# --------------------------------------------------

PAGES = {
    "🏠 Home": home.render,
    "👤 Profile": profile.render,
    "🎯 Career Recommendations": recommendations.render,
    "📝 Resume Studio": resume_studio.render,
    "📊 ATS Resume Analyzer": ats_page.render,
    "🧩 Skill-Gap Analysis": skill_gap.render,
    "🗺️ Learning Roadmap": roadmap_page.render,
    "💼 Job Opportunities": jobs_page.render,
    "🤖 Career Assistant": assistant.render,
}


# --------------------------------------------------
# Per-user database connection
# --------------------------------------------------

@st.cache_resource
def get_user_conn(user_id):
    return db.connect_for_user(user_id)


conn = get_user_conn(st.session_state.user_id)


# --------------------------------------------------
# Initialize selected page
# --------------------------------------------------

if "page" not in st.session_state or st.session_state.page not in PAGES:
    st.session_state.page = "🏠 Home"


# --------------------------------------------------
# Sidebar branding and navigation
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">🧭</div>
            <div>
                <div class="side-name">
                    CareerCompass <span>AI</span>
                </div>
                <div class="side-sub">
                    Your AI-Powered Career Companion
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Signed in as {st.session_state.user_name}")

    if st.button("Log out", use_container_width=True):
        # Clear all page state to avoid exposing old session data
        # if another user signs in through this browser session.
        st.cache_resource.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    choice = st.radio(
        "Navigate",
        options=list(PAGES.keys()),
        key="page",
        label_visibility="collapsed",
    )

    st.markdown("<div class='side-spacer'></div>", unsafe_allow_html=True)

    if gemini.available():
        pill = (
            f"<span class='side-pill on'>"
            f"● Gemini connected · {gemini.MODEL}</span>"
        )
    else:
        pill = (
            "<span class='side-pill off'>"
            "● Gemini not configured — set GEMINI_API_KEY</span>"
        )

    saved_profile = db.load_profile(conn)
    profile_name = (
        saved_profile.get("name", "Profile")
        if saved_profile
        else "Profile not created"
    )

    st.markdown(
        f"""
        <div class="side-foot">
            {pill}
            <div class="side-profile">👤 {profile_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Render the selected page
# --------------------------------------------------

PAGES[choice](conn)
