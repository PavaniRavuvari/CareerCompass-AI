import streamlit as st
from dotenv import load_dotenv

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load .env from the same directory as app.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from core import db, gemini
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


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
)

# Apply shared styling
inject_css()


# --------------------------------------------------
# Page navigation
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
# Database connection
# --------------------------------------------------

@st.cache_resource
def get_conn():
    """Create and cache the database connection."""
    return db.connect()


conn = get_conn()


# --------------------------------------------------
# Initialize selected page
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

# Handle stale session values safely
if st.session_state.page not in PAGES:
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

    # Navigation only — keep dashboard content outside this block.
    choice = st.radio(
        "Navigate",
        options=list(PAGES.keys()),
        key="page",
        label_visibility="collapsed",
    )

    # Push the footer toward the bottom of the sidebar.
    st.markdown(
        "<div class='side-spacer'></div>",
        unsafe_allow_html=True,
    )

    # Gemini configuration status
    if gemini.available():
        pill = (
            f"<span class='side-pill on'>"
            f"● Gemini connected · {gemini.MODEL}"
            f"</span>"
        )
    else:
        pill = (
            "<span class='side-pill off'>"
            "● Gemini not configured — set GEMINI_API_KEY"
            "</span>"
        )

    # Profile name, if a profile exists
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
            <div class="side-profile">
                👤 {profile_name}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Render the selected page
# --------------------------------------------------

page_renderer = PAGES[choice]
page_renderer(conn)
