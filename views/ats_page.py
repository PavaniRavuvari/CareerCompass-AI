
import plotly.graph_objects as go_
import streamlit as st

from core import db, gemini
from core.ats import analyze
from core.resume import extract_text
from views.ui import ai_call, tags, title


def render(conn):
    # --------------------------------------------------
    # Page heading
    # --------------------------------------------------
    title(
        "📊 ATS Resume Analyzer",
        "Evaluate your resume against a job description, identify missing "
        "keywords, and improve relevance."
    )

    st.markdown(
        """
        <div style="
            background:#EEE8FF;
            border:1px solid #D8CEF8;
            border-radius:12px;
            padding:14px 18px;
            margin-bottom:20px;
            color:#6741D9;
            line-height:1.7;
        ">
            <strong>How the ATS estimate works</strong><br>
            40% keywords · 30% relevance · 20% sections · 10% readability.<br>
            This is an ATS-oriented compatibility estimate. Real applicant
            tracking systems vary.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Load saved profile
    # --------------------------------------------------
    profile = db.load_profile(conn) or {}

    # --------------------------------------------------
    # Resume and job description inputs
    # --------------------------------------------------
    col_resume, col_job = st.columns(2, gap="large")

    with col_resume:
        with st.container(border=True):
            st.markdown(
                "### 📄 Your resume"
            )

            uploaded_file = st.file_uploader(
                "Upload resume (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                key="ats_resume_upload",
            )

            # Read the uploaded file or use the saved resume.
            if uploaded_file is not None:
                try:
                    initial_resume = extract_text(
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                    )
                except Exception as error:
                    st.error(f"Could not read the uploaded resume: {error}")
                    initial_resume = ""
            else:
                initial_resume = (
                    st.session_state.get("resume_text")
                    or profile.get("resume_text", "")
                )

            # Initialize the widget value only once so Streamlit
            # preserves edits when the app reruns.
            if "ats_resume_text" not in st.session_state:
                st.session_state["ats_resume_text"] = initial_resume

            # Update the text area when a new file is uploaded.
            upload_signature = (
                uploaded_file.name,
                uploaded_file.size,
            ) if uploaded_file is not None else None

            if (
                upload_signature is not None
                and st.session_state.get("ats_upload_signature")
                != upload_signature
            ):
                st.session_state["ats_resume_text"] = initial_resume
                st.session_state["ats_upload_signature"] = upload_signature

            resume = st.text_area(
                "Resume text",
                height=300,
                key="ats_resume_text",
                placeholder="Upload a resume or paste your resume text here...",
            )

    with col_job:
        with st.container(border=True):
            st.markdown(
                "### 💼 Target job description"
            )

            jd = st.text_area(
                "Job description *",
                height=380,
                key="ats_job_description",
                placeholder="Paste the job description you want to target...",
            )

    # --------------------------------------------------
    # Analyze button
    # --------------------------------------------------
    if st.button(
        "🔍 Analyse resume",
        type="primary",
        use_container_width=True,
        key="run_ats_analysis",
    ):
        try:
            if not resume.strip():
                st.error("Please upload a resume or enter your resume text.")
                return

            if not jd.strip():
                st.error("Please enter the target job description.")
                return

            report = analyze(resume, jd)

            st.session_state["ats"] = report
            st.session_state["ats_inputs"] = (resume, jd)

            db.save_ats(
                conn,
                report["score"],
                report,
            )

            st.success("Resume analysis completed!")

        except ValueError as error:
            st.error(str(error))
            return

        except Exception as error:
            st.error(f"Could not complete the analysis: {error}")
            return

    # --------------------------------------------------
    # Display analysis results
    # --------------------------------------------------
    report = st.session_state.get("ats")

    if not report:
        st.info(
            "Upload or enter your resume, add the target job description, "
            "and select Analyse resume to view your results."
        )
        return

    st.markdown("## ✨ Your resume analysis")

    # --------------------------------------------------
    # Score gauge and score breakdown
    # --------------------------------------------------
    col_score, col_breakdown = st.columns([1, 2], gap="large")

    with col_score:
        with st.container(border=True):
            st.markdown("### 🎯 ATS compatibility estimate")

            score = max(0, min(100, float(report["score"])))

            figure = go_.Figure(
                go_.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={
                        "suffix": "%",
                        "font": {
                            "color": "#7957E8",
                            "size": 38,
                        },
                    },
                    title={
                        "text": "Resume match score",
                        "font": {
                            "color": "#77728E",
                            "size": 13,
                        },
                    },
                    gauge={
                        "axis": {
                            "range": [0, 100],
                            "tickcolor": "#77728E",
                        },
                        "bar": {
                            "color": "#7957E8",
                            "thickness": 0.25,
                        },
                        "bgcolor": "#FFFFFF",
                        "borderwidth": 0,
                        "steps": [
                            {
                                "range": [0, 50],
                                "color": "#EEE8FF",
                            },
                            {
                                "range": [50, 75],
                                "color": "#DCD0FF",
                            },
                            {
                                "range": [75, 100],
                                "color": "#C5B2FF",
                            },
                        ],
                    },
                )
            )

            figure.update_layout(
                height=280,
                margin=dict(t=35, b=10, l=20, r=20),
                paper_bgcolor="#FFFFFF",
                font=dict(color="#201747"),
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
                key="ats_score_gauge",
            )

    with col_breakdown:
        with st.container(border=True):
            st.markdown("### 📈 Score breakdown")

            for category, value in report["breakdown"].items():
                percentage = max(0, min(100, float(value)))

                st.markdown(
                    f"""
                    <div style="
                        color:#30264F;
                        font-size:14px;
                        font-weight:600;
                        margin:12px 0 5px;
                    ">
                        {category}
                        <span style="float:right;color:#7957E8;">
                            {percentage:g}%
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.progress(percentage / 100)

    # --------------------------------------------------
    # Keywords found and missing
    # --------------------------------------------------
    col_found, col_missing = st.columns(2, gap="large")

    with col_found:
        with st.container(border=True):
            st.markdown("### ✅ Keywords found")

            st.markdown(
                tags(report["found_keywords"], "ok"),
                unsafe_allow_html=True,
            )

    with col_missing:
        with st.container(border=True):
            st.markdown("### 🔎 Missing keywords")

            st.markdown(
                tags(report["missing_keywords"], "bad"),
                unsafe_allow_html=True,
            )

    # --------------------------------------------------
    # Strengths and improvements
    # --------------------------------------------------
    col_strengths, col_improvements = st.columns(2, gap="large")

    with col_strengths:
        with st.container(border=True):
            st.markdown("### ✅ Resume strengths")

            if report["strengths"]:
                for strength in report["strengths"]:
                    st.markdown(f"- {strength}")
            else:
                st.caption("No strengths were returned.")

    with col_improvements:
        with st.container(border=True):
            st.markdown("### 🛠️ Suggested improvements")

            if report["improvements"]:
                for improvement in report["improvements"]:
                    st.markdown(f"- {improvement}")
            else:
                st.caption("No improvement suggestions were returned.")

    # --------------------------------------------------
    # AI-powered rewrite suggestions
    # --------------------------------------------------
    st.markdown("")

    if st.button(
        "✨ Get AI rewrite suggestions",
        disabled=not gemini.available(),
        type="primary",
        use_container_width=True,
        key="ats_ai_rewrite",
    ):
        inputs = st.session_state.get("ats_inputs")

        if not inputs:
            st.warning("Please run the resume analysis first.")
        else:
            resume_input, job_input = inputs

            prompt = (
                f"Resume:\n{resume_input}\n\n"
                f"Job description:\n{job_input}\n\n"
                f"Missing keywords: {report['missing_keywords']}\n\n"
                "Suggest 6–8 specific, truthful resume bullet rewrites "
                "or additions. Only suggest skills the candidate can "
                "honestly claim. Clearly flag any skills that require "
                "further learning or experience."
            )

            output = ai_call(
                gemini.generate,
                prompt,
                system=gemini.SYSTEM_COACH,
            )

            if output:
                with st.container(border=True):
                    st.markdown("### ✨ AI rewrite suggestions")
                    st.markdown(output)
