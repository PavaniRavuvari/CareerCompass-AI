
"""Shared UI helpers and styling for CareerCompass AI."""

import streamlit as st

CSS = """
<style>

/* =============== MIDNIGHT PURPLE THEME =============== */

:root {
    --navy: #201747;
    --indigo: #7957E8;
    --purple-dark: #6741D9;
    --purple-hover: #5B36C9;
    --soft: #EEE8FF;
    --ok: #17A673;
    --warn: #E8A317;
    --bad: #D64545;

    --side-bg: #17152F;
    --side-active: #7957E8;
    --side-hover: #30264F;
    --side-text: #F5F3FF;
    --side-muted: #C9C2E3;

    --page-bg: #F7F5FC;
    --card-bg: #FFFFFF;
    --border: #E6E0F3;
}

/* =============== MAIN PAGE =============== */

.stApp {
    background: var(--page-bg);
}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

/* =============== SIDEBAR =============== */

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background-color: var(--side-bg) !important;
}

section[data-testid="stSidebar"] {
    min-width: 270px !important;
    width: 270px !important;
    border-right: 1px solid rgba(255,255,255,.08);
}

section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1.1rem .85rem 1rem;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--side-text);
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,.14);
}

/* Sidebar brand */

.side-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0 18px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.14);
    margin-bottom: 18px;
    width: 100%;
    box-sizing: border-box;
}

.side-logo {
    width: 60px;
    height: 60px;
    min-width: 60px;
    flex-shrink: 0;
    border-radius: 18px;
    background: #7957E8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    line-height: 1;
}

.side-brand > div:last-child {
    flex: 1;
    min-width: 0;
}

.side-name {
    font-size: 19px;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.3;
    white-space: nowrap;
    letter-spacing: -0.6px;
}

.side-name span {
    color: #BDAAFF;
}

.side-sub {
    font-size: 13px;
    color: #D5CDEE;
    margin-top: 6px;
    line-height: 1.5;
}




/* Navigation */

section[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    min-height: 43px;
    box-sizing: border-box;
    padding: 10px 13px !important;
    margin: 0 !important;
    border-radius: 9px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: background .18s ease;
}

/* Hide radio circles only; keep the navigation clickable. */

section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
    color: var(--side-text) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: var(--side-hover) !important;
    border-color: rgba(255,255,255,.12);
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input[type="radio"]:checked) {
    background: var(--side-active) !important;
    border-color: rgba(255,255,255,.12);
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input[type="radio"]:checked) p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Sidebar footer */

.side-foot {
    border-top: 1px solid rgba(255,255,255,.14);
    padding-top: 12px;
    margin-top: 12px;
}

.side-pill {
    display: inline-block;
    font-size: 12px;
    padding: 5px 9px;
    border-radius: 8px;
    margin-bottom: 8px;
}

.side-pill.on {
    background: rgba(23,166,115,.18);
    color: #91E6C8 !important;
}

.side-pill.off {
    background: rgba(232,163,23,.18);
    color: #FFE09A !important;
}

.side-profile {
    font-size: 12px;
    color: var(--side-muted) !important;
    padding: 5px 2px;
}

/* =============== WELCOME BANNER =============== */

.hero {
    background: linear-gradient(120deg, #201747, #7048D6);
    color: #FFFFFF;
    padding: 30px 32px;
    border-radius: 18px;
    margin-bottom: 22px;
    box-shadow: 0 5px 16px rgba(32,23,71,.12);
}

.hero h1 {
    color: #FFFFFF !important;
    margin: 0 0 10px;
    font-size: clamp(24px, 3vw, 36px);
    line-height: 1.25;
}

.hero p {
    color: #EEE8FF !important;
    margin: 0;
    font-size: 16px;
    line-height: 1.6;
}

/* =============== CONTENT CARDS =============== */

.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 3px 10px rgba(32,23,71,.06);
}

.card h4 {
    margin: 0 0 9px;
    color: var(--navy) !important;
    font-size: 17px;
}

.muted {
    color: #77728E;
    font-size: 13px;
}

.tag {
    display: inline-block;
    padding: 4px 10px;
    margin: 3px 4px 3px 0;
    border-radius: 999px;
    font-size: 12px;
    background: var(--soft);
    color: var(--indigo);
}

.tag.ok {
    background: #E3F6EE;
    color: #087D55;
}

.tag.bad {
    background: #FBE9E9;
    color: #B42323;
}

.tag.warn {
    background: #FDF3DC;
    color: #8B6200;
}

.metric-big {
    font-size: clamp(26px, 3vw, 36px);
    font-weight: 800;
    color: var(--indigo);
}

.page-title {
    color: var(--navy) !important;
    font-weight: 800;
    margin-bottom: 0;
}

/* =============== ALL BUTTONS =============== */

/* Primary buttons: Save profile, Analyse, Generate, etc. */

.stApp button[kind="primary"],
.stApp button[data-testid="baseButton-primary"] {
    background: #7957E8 !important;
    background-color: #7957E8 !important;
    color: #FFFFFF !important;
    border: 1px solid #7957E8 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 42px;
    transition: all .18s ease;
}

.stApp button[kind="primary"]:hover,
.stApp button[data-testid="baseButton-primary"]:hover {
    background: #6741D9 !important;
    background-color: #6741D9 !important;
    border-color: #6741D9 !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 12px rgba(121,87,232,.22);
}

/* Secondary buttons remain white with purple borders */

.stApp .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
    background: #FFFFFF !important;
    color: #6741D9 !important;
    border: 1px solid #D8CEF8 !important;
    border-radius: 10px !important;
    min-height: 42px;
    font-weight: 600;
    transition: all .18s ease;
}

.stApp .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
    background: #F3EFFF !important;
    color: #4F2DB5 !important;
    border-color: #7957E8 !important;
}

/* =============== FORM CONTROLS =============== */

.stApp input,
.stApp textarea {
    border-radius: 9px;
}

.stApp input:focus,
.stApp textarea:focus,
.stApp [data-baseweb="select"]:focus-within {
    border-color: #7957E8 !important;
    box-shadow: 0 0 0 1px #7957E8 !important;
}

/* Sliders: purple selected track and handle */

.stApp [data-testid="stSlider"] [role="slider"] {
    background-color: #7957E8 !important;
    border-color: #7957E8 !important;
    box-shadow: none !important;
}

.stApp [data-testid="stSlider"] [data-baseweb="slider"] {
    accent-color: #7957E8;
}

/* Progress indicators */

.stApp [data-testid="stProgress"] > div > div > div {
    background-color: #7957E8 !important;
}

/* Tabs */

.stApp [data-baseweb="tab-highlight"] {
    background-color: #7957E8 !important;
}

.stApp [data-baseweb="tab"][aria-selected="true"] {
    color: #7957E8 !important;
}

/* Links */

.stApp a {
    color: #6741D9;
}

.stApp a:hover {
    color: #4F2DB5;
}

/* File uploader */

.stApp [data-testid="stFileUploader"] section {
    border-color: #D8CEF8 !important;
    border-radius: 12px !important;
}

/* Focus accessibility */

.stApp button:focus-visible,
.stApp a:focus-visible {
    outline: 2px solid #9A83F5 !important;
    outline-offset: 2px !important;
}

/* =============== RESPONSIVE =============== */

@media (max-width: 768px) {
    .block-container {
        padding: 1rem .8rem 2rem;
    }

    section[data-testid="stSidebar"] {
        min-width: 0 !important;
        width: auto !important;
    }

    .hero {
        padding: 22px 18px;
        border-radius: 14px;
    }

    .hero p {
        font-size: 14px;
    }

    .card {
        padding: 14px;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
    }
}

/* ========== PURPLE ALERTS AND NOTIFICATIONS ========== */

/* Info messages: Create your profile first, etc. */
.stApp [data-testid="stAlert"][data-baseweb="notification"] {
    background-color: #EEE8FF !important;
    border: 1px solid #D8CEF8 !important;
    border-radius: 12px !important;
    color: #201747 !important;
}

/* Alert text and icons */
.stApp [data-testid="stAlert"] p,
.stApp [data-testid="stAlert"] span,
.stApp [data-testid="stAlert"] svg {
    color: #6741D9 !important;
}

/* Other alert variants */
.stApp [data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* Purple links inside alerts */
.stApp [data-testid="stAlert"] a {
    color: #6741D9 !important;
    font-weight: 600;
}

/* Success messages */
.stApp [data-testid="stAlert"][kind="success"] {
    background-color: #E8F7F0 !important;
}

/* Warning messages */
.stApp [data-testid="stAlert"][kind="warning"] {
    background-color: #FFF5DE !important;
}
/* Keep all sidebar navigation labels aligned */
[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding-left: 12px !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    margin-left: 0 !important;
    flex-shrink: 0;
}

/* Keep emoji/icon spacing consistent */
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    margin-left: 0 !important;
}


</style>
"""


def inject_css():
    """Apply shared application styling."""
    st.markdown(CSS, unsafe_allow_html=True)



def title(heading, subtitle=""):
    st.markdown(
        f"""
        <div style="
            background: #201747;
            border-radius: 22px;
            padding: 22px 24px;
            margin-bottom: 22px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-sizing: border-box;
            width: 100%;
        ">
            <div style="
                flex: 1;
                min-width: 0;
            ">
                <h1 style="
                    color: #FFFFFF;
                    font-size: 29px;
                    font-weight: 800;
                    line-height: 1.3;
                    margin: 0 0 7px 0;
                ">
                    {heading}
                </h1>
                <p style="
                    color: #E6DEFF;
                    font-size: 16px;
                    line-height: 1.5;
                    margin: 0;
                ">
                    {subtitle}
        </div>
        """,
        unsafe_allow_html=True,
    )



def tags(items, kind=""):
    """Return HTML tags for a list of items."""
    if not items:
        return "<span class='muted'>—</span>"

    return "".join(
        f"<span class='tag {kind}'>{item}</span>"
        for item in items
    )


def card(header, body_html):
    """Render a reusable content card."""
    st.markdown(
        f"<div class='card'><h4>{header}</h4>{body_html}</div>",
        unsafe_allow_html=True,
    )


def go(page):
    """Navigate to a page using session state."""
    st.session_state.page = page


def need_profile(profile):
    """Require a profile before using personalised features."""
    if not profile:
        st.info(
            "Create your profile first so recommendations and analysis "
            "are personalised."
        )
        st.button(
            "Go to Profile →",
            on_click=go,
            args=("👤 Profile",),
            type="primary",
        )
        return True

    return False


def ai_call(fn, *args, spinner="Asking Gemini…", **kw):
    """Run an AI function and display expected Gemini errors."""
    from core.gemini import GeminiError

    try:
        with st.spinner(spinner):
            return fn(*args, **kw)
    except GeminiError as error:
        st.error(str(error))
        return None
