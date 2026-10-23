import json

import streamlit as st

from core import db, gemini
from core.resume import draft_from_profile, to_docx, to_pdf
from views.ui import ai_call, need_profile, title


def render(conn):
    title("📝 Resume Studio", "Drafts use only the details in your profile. Edit freely, then export.")
    p = db.load_profile(conn)
    if need_profile(p):
        return
    target = st.text_input("Target role", (p.get("target_roles") or [""])[0])
    jd = st.text_area("Target job description (optional — used by the AI polish)", height=100)
    c1, c2 = st.columns(2)
    if c1.button("📄 Draft from my profile", type="primary", use_container_width=True):
        st.session_state.resume_text = draft_from_profile(p, target)
    if c2.button("✨ Polish with Gemini", use_container_width=True, disabled=not gemini.available()):
        base = st.session_state.get("resume_text") or draft_from_profile(p, target)
        prompt = (f"Rewrite this resume to be professional and ATS-friendly for the role '{target}'.\n"
                  f"Job description (optional): {jd}\n\nProfile JSON: {json.dumps({k: v for k, v in p.items() if k != 'resume_text'})}\n\n"
                  f"Current resume:\n{base}\n\nRules: plain text only; first line = name; UPPERCASE section headings "
                  "(SUMMARY, SKILLS, EXPERIENCE, PROJECTS, CERTIFICATIONS, EDUCATION); bullets start with '- ' and action verbs. "
                  "NEVER invent employers, dates, metrics, degrees or skills not present in the profile.")
        out = ai_call(gemini.generate, prompt, system=gemini.SYSTEM_COACH, spinner="Polishing resume…")
        if out:
            st.session_state.resume_text = out.replace("**", "").replace("```", "")
    if not gemini.available():
        st.caption("Set GEMINI_API_KEY to enable AI polishing.")

    text = st.text_area("Resume (editable)", st.session_state.get("resume_text", ""), height=420, key="resume_editor")
    st.session_state.resume_text = text
    if text.strip():
        c1, c2, c3, c4 = st.columns(4)
        c1.download_button("⬇️ PDF", to_pdf(text), "resume.pdf", "application/pdf", use_container_width=True)
        c2.download_button("⬇️ DOCX", to_docx(text), "resume.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        c3.download_button("⬇️ TXT", text, "resume.txt", use_container_width=True)
        if c4.button("💾 Save version", use_container_width=True):
            db.save_resume(conn, target or "Resume", text)
            st.success("Saved.")
    saved = db.list_resumes(conn)
    if saved:
        st.markdown("#### Saved versions")
        for r in saved[:10]:
            with st.expander(f"{r['title']} — {r['created_at']}"):
                st.text(r["content"])
                if st.button("Load into editor", key=f"load{r['id']}"):
                    st.session_state.resume_text = r["content"]
                    st.rerun()
