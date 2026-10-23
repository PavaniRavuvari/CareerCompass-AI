
import streamlit as st

from core import db, jobs
from views.ui import tags, title


def render(conn):
    # --------------------------------------------------
    # Midnight Purple page heading and subtitle
    # --------------------------------------------------
    title(
        "💼 Job Opportunities",
        "Explore career opportunities that match your skills, interests, and target role."
    )

    # --------------------------------------------------
    # Load profile and career recommendations
    # --------------------------------------------------
    profile = db.load_profile(conn) or {}
    recommendations = db.latest_recommendations(conn) or []

    live = jobs.adzuna_available()

    # --------------------------------------------------
    # Search filters
    # --------------------------------------------------
    col_role, col_location, col_type = st.columns([3, 2, 1.4])

    default_role = (
        recommendations[0]["title"]
        if recommendations
        else ""
    )

    query = col_role.text_input(
        "Role or skill",
        value=default_role,
        key="jobs_role_query",
    )

    location = col_location.text_input(
        "Location",
        value="",
        disabled=not live,
        key="jobs_location",
    )

    job_type = col_type.selectbox(
        "Type",
        ["All", "Full-time", "Internship"],
        key="jobs_type",
    )

    # Keep the existing demo and live job search options.
    sources = ["Demo data", "Adzuna (live)"] if live else ["Demo data"]

    source = st.radio(
        "Source",
        sources,
        horizontal=True,
        key="jobs_source",
    )

    # --------------------------------------------------
    # Search jobs
    # --------------------------------------------------
    results = []

    if source == "Demo data":
        results = jobs.search_demo(query, job_type)

    elif (
        st.button("Search live jobs", type="primary", key="search_live_jobs")
        or st.session_state.get("live_jobs")
    ):
        try:
            if query.strip():
                st.session_state["live_jobs"] = jobs.search_adzuna(
                    query,
                    location,
                )

            results = st.session_state.get("live_jobs", [])

        except Exception as error:
            st.error(f"Unable to fetch live jobs: {error}")

    # --------------------------------------------------
    # Results
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔎 Search results")

    st.write(f"**{len(results)}** results")

    if not results:
        st.info(
            "No jobs found for these filters. Try another role or skill."
        )

    for index, job in enumerate(results):
        match = jobs.match_score(
            job,
            profile.get("skills", []),
        )

        with st.container(border=True):
            col_details, col_actions = st.columns([4, 1])

            with col_details:
                st.markdown(
                    f"#### {job['title']}\n"
                    f"**{job['company']}** · "
                    f"{job['location']} · {job['type']}"
                )

                st.caption(job["description"])

                if job.get("skills"):
                    st.markdown(
                        tags(job["skills"]),
                        unsafe_allow_html=True,
                    )

            with col_actions:
                if match is not None:
                    st.metric(
                        "Skill match",
                        f"{match}%",
                    )

                st.caption(f"Source: {job['source']}")

                st.link_button(
                    "Apply / view",
                    job["url"],
                    use_container_width=True,
                    key=f"apply_job_{index}",
                )
