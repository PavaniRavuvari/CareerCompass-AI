import streamlit as st

from core import db
from core.data import careers, split_list
from core.resume import extract_text
from views.ui import go, title

ALL_SKILLS = sorted({s for c in careers() for s in c["skills"]})


def render(conn):
    title("👤 Your Profile", "Fields marked * are required. Optional fields can stay blank.")
    p = db.load_profile(conn) or {}
    with st.form("profile"):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name / profile label *", p.get("name", ""))
        email = c2.text_input("Email", p.get("email", ""))
        phone = c3.text_input("Phone", p.get("phone", ""))
        c1, c2, c3, c4 = st.columns(4)
        education = c1.selectbox("Education *", ["", "High School", "Diploma", "B.Tech/B.E.", "B.Sc", "BCA", "B.Com", "BBA", "M.Tech", "M.Sc", "MCA", "MBA", "Other"],
                                 index=0 if not p.get("education") else ["", "High School", "Diploma", "B.Tech/B.E.", "B.Sc", "BCA", "B.Com", "BBA", "M.Tech", "M.Sc", "MCA", "MBA", "Other"].index(p["education"]))
        specialization = c2.text_input("Specialization", p.get("specialization", ""))
        institution = c3.text_input("Institution", p.get("institution", ""))
        grad_year = c4.number_input("Graduation year", 1980, 2040, int(p.get("grad_year") or 2026))
        known = [s for s in split_list(p.get("skills")) if s in ALL_SKILLS]
        extra = [s for s in split_list(p.get("skills")) if s not in ALL_SKILLS]
        skills = st.multiselect("Skills *", ALL_SKILLS, default=known)
        other_skills = st.text_input("Other skills (comma separated)", ", ".join(extra))
        c1, c2 = st.columns(2)
        interests = c1.text_input("Interests (comma separated)", ", ".join(split_list(p.get("interests"))))
        industries = c2.text_input("Preferred industries", p.get("industries", ""))
        target_roles = c1.text_input("Target roles", ", ".join(split_list(p.get("target_roles"))))
        linkedin = c2.text_input("LinkedIn / portfolio URL", p.get("linkedin", ""))
        goals = st.text_area("Career goals", p.get("goals", ""), height=70)
        projects = st.text_area("Projects (one per line)", p.get("projects", ""), height=90)
        certifications = st.text_area("Certifications (one per line)", p.get("certifications", ""), height=70)
        experience = st.text_area("Internships / work experience (one per line)", p.get("experience", ""), height=90)
        c1, c2 = st.columns(2)
        hours = c1.slider("Study hours per week", 1, 40, int(p.get("hours_per_week") or 8))
        pace = c2.select_slider("Preferred pace", ["Relaxed", "Moderate", "Intensive"], p.get("pace", "Moderate"))
        resume_file = st.file_uploader("Existing resume (optional: PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        submitted = st.form_submit_button("💾 Save profile", type="primary")

    if submitted:
        all_skills = skills + split_list(other_skills)
        errors = [m for ok, m in [(name.strip(), "Name is required."), (education, "Education is required."), (all_skills, "Add at least one skill.")] if not ok]
        if errors:
            for e in errors:
                st.error(e)
            return
        data = dict(name=name.strip(), email=email, phone=phone, education=education, specialization=specialization,
                    institution=institution, grad_year=grad_year, skills=all_skills, interests=split_list(interests),
                    industries=industries, target_roles=split_list(target_roles), linkedin=linkedin, goals=goals,
                    projects=projects, certifications=certifications, experience=experience, hours_per_week=hours,
                    pace=pace, resume_text=p.get("resume_text", ""))
        if resume_file:
            data["resume_text"] = extract_text(resume_file.name, resume_file.getvalue())
        db.save_profile(conn, data)
        st.success("Profile saved.")
        st.button("Next: get career recommendations →", on_click=go, args=("🎯 Career Recommendations",), type="primary")
    if p.get("resume_text"):
        with st.expander("Stored resume text"):
            st.text(p["resume_text"][:3000])
