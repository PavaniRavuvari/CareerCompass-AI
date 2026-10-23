
"""CareerCompass AI — Skill-Gap Analysis."""

import pandas as pd
import plotly.express as px
import streamlit as st

from core import db
from core.data import careers
from core.skillgap import analyze_gap, build_roadmap
from views.ui import go, need_profile, title


PURPLE = "#7957E8"
DARK_PURPLE = "#201747"
LAVENDER = "#EEE8FF"
BORDER = "#E6E0F3"


def render(conn):
    # --------------------------------------------------
    # Page heading
    # --------------------------------------------------
    title(
        "🧩 Skill-Gap Analysis",
        "Identify missing skills, evaluate your readiness, "
        "and build a personalized learning plan."
    )

    st.markdown(
        f"""
        <div style="
            background:{LAVENDER};
            border:1px solid #D8CEF8;
            border-radius:12px;
            padding:14px 18px;
            margin-bottom:22px;
            color:#6741D9;
            line-height:1.7;
        ">
            <strong>How skill verification works</strong><br>
            ✅ Acquired: supported by a project, certification, or experience.<br>
            🟡 Unverified: listed in your profile but not yet backed by evidence.<br>
            ❌ Not provided: missing from your profile.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Load profile
    # --------------------------------------------------
    profile = db.load_profile(conn)

    if need_profile(profile):
        return

    # --------------------------------------------------
    # Select target career
    # --------------------------------------------------
    recommendations = db.latest_recommendations(conn) or []
    career_data = careers() or []

    recommended_titles = [
        item["title"]
        for item in recommendations
        if item.get("title")
    ]

    other_titles = [
        item["title"]
        for item in career_data
        if item.get("title") and item["title"] not in recommended_titles
    ]

    options = recommended_titles + other_titles

    if not options:
        st.warning(
            "No career options are available yet. "
            "Please check your career data configuration."
        )
        return

    previous_career = st.session_state.get("target_career")
    default_index = (
        options.index(previous_career)
        if previous_career in options
        else 0
    )

    with st.container(border=True):
        st.markdown("### 🎯 Choose your target career")

        career = st.selectbox(
            "Target career",
            options=options,
            index=default_index,
            key="skill_gap_target_career",
        )

    st.session_state["target_career"] = career

    # --------------------------------------------------
    # Analyze skill gap
    # --------------------------------------------------
    try:
        gap = analyze_gap(profile, career)
    except Exception as error:
        st.error(f"Unable to analyze the skill gap: {error}")
        return

    rows = gap.get("rows", [])
    readiness = max(0, min(100, float(gap.get("readiness", 0))))

    # --------------------------------------------------
    # Readiness and status chart
    # --------------------------------------------------
    col_readiness, col_chart = st.columns([1, 2], gap="large")

    with col_readiness:
        with st.container(border=True):
            st.markdown("### 📊 Career readiness")

            st.markdown(
                f"""
                <div style="
                    color:{PURPLE};
                    font-size:44px;
                    font-weight:800;
                    margin:8px 0;
                ">
                    {readiness:.0f}%
                </div>
                <div style="color:#77728E;">
                    Estimated skill readiness
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.progress(readiness / 100)

            st.caption(
                "Readiness is an estimate based on the skills "
                "and evidence available in your profile."
            )

    with col_chart:
        with st.container(border=True):
            st.markdown("### 📈 Skill status overview")

            status_order = ["Acquired", "Unverified", "Not provided"]
            status_colors = {
                "Acquired": "#17A673",
                "Unverified": "#E8A317",
                "Not provided": "#D64545",
            }

            counts = pd.Series(
                [item.get("status", "Not provided") for item in rows],
                dtype="object",
            ).value_counts()

            chart_data = pd.DataFrame(
                {
                    "Status": status_order,
                    "Skills": [int(counts.get(status, 0)) for status in status_order],
                }
            )

            chart_data = chart_data[chart_data["Skills"] > 0]

            if not chart_data.empty:
                figure = px.pie(
                    chart_data,
                    names="Status",
                    values="Skills",
                    hole=0.58,
                    color="Status",
                    category_orders={"Status": status_order},
                    color_discrete_map=status_colors,
                )

                figure.update_layout(
                    height=290,
                    margin=dict(t=15, b=15, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=DARK_PURPLE),
                    legend=dict(orientation="h", y=-0.08),
                )

                st.plotly_chart(
                    figure,
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="skill_gap_status_chart",
                )
            else:
                st.info("No skill requirements were returned for this career.")

    # --------------------------------------------------
    # Skill-by-skill analysis
    # --------------------------------------------------
    st.markdown("## 🔍 Detailed skill analysis")

    if not rows:
        st.info(
            "No individual skill requirements were returned. "
            "Check your career skill definitions in core/data.py."
        )
    else:
        for index, item in enumerate(rows):
            skill = item.get("skill", "Unnamed skill")
            status = item.get("status", "Not provided")
            priority = item.get("priority", "—")

            status_icons = {
                "Acquired": "✅",
                "Unverified": "🟡",
                "Not provided": "❌",
            }
            icon = status_icons.get(status, "ℹ️")

            with st.expander(
                f"{icon} {skill} — {status} · Priority: {priority}"
            ):
                resources = item.get("resources", [])

                if resources:
                    st.markdown("**Recommended learning resources**")

                    for resource in resources:
                        resource_title = resource.get(
                            "title", "Learning resource"
                        )
                        resource_url = resource.get("url")
                        resource_type = resource.get("type", "Resource")

                        if resource_url:
                            st.markdown(
                                f"- [{resource_title}]({resource_url}) "
                                f"· {resource_type}"
                            )
                        else:
                            st.markdown(
                                f"- **{resource_title}** · {resource_type}"
                            )
                else:
                    st.caption(
                        "No bundled resource is available. "
                        "Search for official documentation and tutorials."
                    )

    # --------------------------------------------------
    # Portfolio projects
    # --------------------------------------------------
    st.markdown("## 💡 Suggested portfolio projects")

    projects = gap.get("projects", [])

    with st.container(border=True):
        if projects:
            for project in projects:
                st.markdown(f"- {project}")
        else:
            st.info(
                "No project suggestions are available for this career yet."
            )

    # --------------------------------------------------
    # Build learning roadmap
    # --------------------------------------------------
    st.markdown("## 🗺️ Turn your skill gaps into a learning plan")

    st.caption(
        "Generate a roadmap based on this career's skill gaps "
        "and your available weekly study hours."
    )

    if st.button(
        "🗺️ Build my learning roadmap",
        type="primary",
        use_container_width=True,
        key="build_skill_gap_roadmap",
    ):
        try:
            weekly_hours = profile.get("hours_per_week", 8)

            roadmap = build_roadmap(gap, weekly_hours)

            db.replace_roadmap(conn, career, roadmap)

            st.success("Your learning roadmap has been created!")

            go("🗺️ Learning Roadmap")

        except Exception as error:
            st.error(f"Could not build the learning roadmap: {error}")
