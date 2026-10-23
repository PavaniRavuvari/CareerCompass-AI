
"""CareerCompass AI — Home dashboard."""

import plotly.graph_objects as go_
import streamlit as st

from core import db
from views.ui import card, go, tags


def render(conn):
    # --------------------------------------------------
    # Load existing application data
    # --------------------------------------------------
    p = db.load_profile(conn)
    name = p.get("name") if p else "there"

    recs = db.latest_recommendations(conn)
    tasks = db.roadmap(conn)
    ats = db.list_ats(conn)

    done = sum(t["done"] for t in tasks)
    total_tasks = len(tasks)
    progress = round(100 * done / total_tasks) if total_tasks else 0

    # --------------------------------------------------
    # Dashboard-specific styling
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        .dashboard-metric {
            background: #FFFFFF;
            border: 1px solid #E6E0F3;
            border-radius: 15px;
            padding: 18px 17px;
            min-height: 142px;
            box-shadow: 0 3px 12px rgba(32, 23, 71, 0.055);
            border-top: 4px solid #7957E8;
            box-sizing: border-box;
            margin-bottom: 12px;
        }

        .dashboard-metric-label {
            font-size: 13px;
            font-weight: 600;
            color: #77728E;
            margin-bottom: 12px;
        }

        .dashboard-metric-value {
            font-size: clamp(23px, 2vw, 31px);
            font-weight: 800;
            color: #201747;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }

        .dashboard-metric-detail {
            font-size: 12px;
            color: #7957E8;
            margin-top: 8px;
            overflow-wrap: anywhere;
        }

        .dashboard-section-title {
            color: #201747;
            font-size: 19px;
            font-weight: 750;
            margin: 0 0 5px 0;
        }

        .dashboard-section-subtitle {
            color: #77728E;
            font-size: 13px;
            margin-bottom: 16px;
        }

        .dashboard-section-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 11px;
            background: #EEE8FF;
            font-size: 20px;
            margin-right: 10px;
            vertical-align: middle;
        }

        @media (max-width: 768px) {
            .dashboard-metric {
                padding: 14px;
                min-height: 125px;
            }

            .dashboard-metric-value {
                font-size: 23px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Welcome banner
    # --------------------------------------------------
    st.markdown(
        f"""
        <div class="hero">
            <h1>Welcome, {name} 👋</h1>
            <p>
                Discover your best-fit careers, close skill gaps,
                build an ATS-ready resume and follow a personalised
                learning roadmap.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Four dashboard metric cards
    # Values come from the existing database queries
    # --------------------------------------------------
    profile_value = "Complete" if p else "Missing"
    profile_detail = (
        "✓ Your profile is available"
        if p
        else "Create your profile to get started"
    )

    career_value = f"{recs[0]['score']}%" if recs else "—"
    career_detail = recs[0]["title"] if recs else "No recommendations yet"

    ats_value = str(ats[0]["score"]) if ats else "—"
    ats_detail = "Latest resume analysis" if ats else "Analyse a resume to begin"

    roadmap_value = f"{progress}%"
    roadmap_detail = f"{done} of {total_tasks} tasks completed"

    metrics = [
        ("👤", "Profile status", profile_value, profile_detail),
        ("🎯", "Top career match", career_value, career_detail),
        ("📊", "Latest ATS estimate", ats_value, ats_detail),
        ("🗺️", "Roadmap progress", roadmap_value, roadmap_detail),
    ]

    columns = st.columns(4)

    for column, (icon, label, value, detail) in zip(columns, metrics):
        with column:
            st.markdown(
                f"""
                <div class="dashboard-metric">
                    <div class="dashboard-metric-label">
                        {icon}&nbsp; {label}
                    </div>
                    <div class="dashboard-metric-value">
                        {value}
                    </div>
                    <div class="dashboard-metric-detail">
                        {detail}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------
    # Career matches graph and quick actions
    # --------------------------------------------------
    left, right = st.columns([3, 2], gap="large")

    with left:
        # A bordered container creates a separate card
        # around the heading, description and Plotly chart.
        with st.container(border=True):
            st.markdown(
                """
                <div>
                    <span class="dashboard-section-icon">📈</span>
                    <span class="dashboard-section-title">
                        Your top career matches
                    </span>
                </div>
                <div class="dashboard-section-subtitle">
                    Explore career suitability based on your profile.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if recs:
                scores = [r["score"] for r in recs][::-1]
                titles = [r["title"] for r in recs][::-1]

                fig = go_.Figure(
                    go_.Bar(
                        x=scores,
                        y=titles,
                        orientation="h",
                        marker=dict(
                            color="#7957E8",
                            line=dict(color="#6741D9", width=0.5),
                        ),
                        text=[f"{score}%" for score in scores],
                        textposition="auto",
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Career match: %{x}%"
                            "<extra></extra>"
                        ),
                    )
                )

                fig.update_layout(
                    height=max(300, min(440, len(recs) * 58 + 100)),
                    margin=dict(l=10, r=20, t=15, b=35),
                    xaxis=dict(
                        title="Match score (%)",
                        range=[0, 100],
                        gridcolor="#EEE8FF",
                        zeroline=False,
                        color="#77728E",
                    ),
                    yaxis=dict(
                        title=None,
                        color="#30264F",
                        automargin=True,
                    ),
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    font=dict(
                        color="#201747",
                        family="Arial, sans-serif",
                        size=12,
                    ),
                    showlegend=False,
                    bargap=0.35,
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False, "responsive": True},
                )

                st.caption(
                    "Scores are based on your application's existing "
                    "career recommendation algorithm."
                )

            else:
                st.markdown(
                    """
                    <div style="
                        background:#F7F5FC;
                        border:1px dashed #D8CEF8;
                        border-radius:12px;
                        padding:22px;
                        color:#77728E;
                        text-align:center;
                    ">
                        <div style="font-size:30px;">🎯</div>
                        <strong style="color:#201747;">
                            No career matches yet
                        </strong>
                        <p>
                            Complete your profile and generate
                            recommendations to see your results here.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.button(
                    "👤 Complete my profile",
                    on_click=go,
                    args=("👤 Profile",),
                    type="primary",
                    use_container_width=True,
                    key="home_complete_profile",
                )

    # --------------------------------------------------
    # Quick actions
    # --------------------------------------------------
    with right:
        with st.container(border=True):
            st.markdown(
                """
                <div>
                    <span class="dashboard-section-icon">⚡</span>
                    <span class="dashboard-section-title">
                        Quick actions
                    </span>
                </div>
                <div class="dashboard-section-subtitle">
                    Jump straight to a career tool.
                </div>
                """,
                unsafe_allow_html=True,
            )

            quick_actions = [
                ("👤 Edit profile", "👤 Profile"),
                ("🎯 Get recommendations", "🎯 Career Recommendations"),
                ("📊 Check my resume", "📊 ATS Resume Analyzer"),
                ("🗺️ Open roadmap", "🗺️ Learning Roadmap"),
                ("🤖 Ask the assistant", "🤖 Career Assistant"),
            ]

            for label, page in quick_actions:
                st.button(
                    label,
                    on_click=go,
                    args=(page,),
                    use_container_width=True,
                    key=f"qa_{page}",
                )

        # --------------------------------------------------
        # Skills card
        # --------------------------------------------------
        if p:
            with st.container(border=True):
                st.markdown(
                    """
                    <div>
                        <span class="dashboard-section-icon">✨</span>
                        <span class="dashboard-section-title">
                            Your skills
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(tags(p.get("skills", [])), unsafe_allow_html=True)

        # --------------------------------------------------
        # Get-started card when no profile exists
        # --------------------------------------------------
        if not p:
            card(
                "Get started",
                """
                <p class="muted">
                    1. Fill in your profile<br>
                    2. Generate recommendations<br>
                    3. Analyse skill gaps<br>
                    4. Build your roadmap
                </p>
                """,
            )
