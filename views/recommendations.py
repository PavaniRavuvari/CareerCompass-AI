import json

import plotly.graph_objects as go_
import streamlit as st

from core import db, gemini
from core.recommender import W_INTEREST, W_SKILL, W_TEXT, recommend
from views.ui import ai_call, go, need_profile, tags, title


def _to_gap(career):
    st.session_state.target_career = career
    go("🧩 Skill-Gap Analysis")


def render(conn):
    title("🎯 Career Recommendations", f"Explainable ML: TF-IDF + cosine similarity. Score = {int(W_SKILL*100)}% skill overlap + "
          f"{int(W_TEXT*100)}% profile-text similarity + {int(W_INTEREST*100)}% interest/goal similarity.")
    p = db.load_profile(conn)
    if need_profile(p):
        return
    if st.button("🔄 Generate / refresh recommendations", type="primary"):
        try:
            db.save_recommendations(conn, recommend(p))
            st.session_state.pop("explanations", None)
        except ValueError as e:
            st.error(str(e))
    recs = db.latest_recommendations(conn)
    if not recs:
        st.info("Click the button above to rank your top 5 careers.")
        return

    cats = ["Skill overlap", "Text similarity", "Interest similarity"]
    fig = go_.Figure()
    for r in recs[:3]:
        fig.add_trace(go_.Scatterpolar(r=[r["skill_overlap"], r["text_similarity"], r["interest_similarity"]], theta=cats, fill="toself", name=r["title"]))
    fig.update_layout(height=340, polar=dict(radialaxis=dict(range=[0, 100])), margin=dict(t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    expl = st.session_state.setdefault("explanations", {})
    for i, r in enumerate(recs, 1):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"### {i}. {r['title']}")
            c1.caption(r["description"])
            c2.markdown(f"<div class='metric-big'>{r['score']}%</div>", unsafe_allow_html=True)
            c2.progress(min(r["score"] / 100, 1.0))
            st.markdown(f"**Matched skills:** {tags(r['matched_skills'], 'ok')}", unsafe_allow_html=True)
            st.markdown(f"**Skills to build:** {tags(r['missing_skills'], 'bad')}", unsafe_allow_html=True)
            st.caption(f"Salary: {r['salary']} · Outlook: {r['outlook']} · Skill {r['skill_overlap']}% · Text {r['text_similarity']}% · Interest {r['interest_similarity']}%")
            b1, b2, _ = st.columns([1.3, 1.3, 3])
            if b1.button("✨ Explain with AI", key=f"ex{i}", disabled=not gemini.available()):
                prompt = (f"User profile JSON: {json.dumps({k: v for k, v in p.items() if k != 'resume_text'})}\n\n"
                          f"Matching result: {json.dumps(r)}\n\nExplain in 5-7 bullets why '{r['title']}' fits this user, citing profile "
                          "evidence and the score components, then list the top 3 next steps. Do not invent facts.")
                out = ai_call(gemini.generate, prompt, system=gemini.SYSTEM_COACH)
                if out:
                    expl[r["title"]] = out
            b2.button("🧩 Analyse skill gap", key=f"sg{i}", on_click=_to_gap, args=(r["title"],))
            if r["title"] in expl:
                st.info(expl[r["title"]])
