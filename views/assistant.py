import json

import streamlit as st

from core import db, gemini
from core.rag import RAGIndex
from views.ui import title


@st.cache_resource(show_spinner="Building knowledge index…")
def get_index():
    return RAGIndex()


def render(conn):
    title("🤖 Career Assistant", "Profile-aware chat grounded in the CareerCompass knowledge base via FAISS retrieval (RAG).")
    if not gemini.available():
        st.warning("Set GEMINI_API_KEY to chat. Retrieval still works — try the search below.")
    p = db.load_profile(conn) or {}
    use_profile = st.toggle("Use my profile for answers", value=bool(p))
    if st.button("🗑️ Clear conversation"):
        db.clear_chat(conn)
        st.rerun()
    for m in db.messages(conn):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    q = st.chat_input("Ask about careers, skills, resumes, interviews…")
    if not q:
        return
    with st.chat_message("user"):
        st.markdown(q)
    db.add_message(conn, "user", q)
    try:
        hits = get_index().search(q, k=4)
    except Exception as e:  # noqa: BLE001
        st.error(f"Retrieval failed: {e}")
        hits = []
    context = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits)
    if not gemini.available():
        answer = "**Relevant knowledge (Gemini not configured):**\n\n" + "\n\n".join(f"- *{h['source']}*: {h['text'][:300]}" for h in hits)
    else:
        history = db.messages(conn)[-10:]
        prof = json.dumps({k: v for k, v in p.items() if k != "resume_text"}) if use_profile else "Not shared."
        prompt = (f"User profile: {prof}\n\nRetrieved context:\n{context}\n\nConversation so far:\n" +
                  "\n".join(f"{m['role']}: {m['content']}" for m in history) +
                  f"\n\nAnswer the latest user question. Use the context where relevant and cite sources in [brackets]. "
                  "If unsure, say so.")
        try:
            with st.spinner("Thinking…"):
                answer = gemini.generate(prompt, system=gemini.SYSTEM_COACH)
        except gemini.GeminiError as e:
            answer = f"⚠️ {e}"
    with st.chat_message("assistant"):
        st.markdown(answer)
        if hits:
            with st.expander("Sources"):
                for h in hits:
                    st.caption(f"{h['source']} (similarity {h['score']:.2f})")
    db.add_message(conn, "assistant", answer)
