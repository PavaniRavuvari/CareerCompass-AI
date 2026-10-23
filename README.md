# CareerCompass AI

AI-powered career recommendation, resume intelligence and personalised learning roadmap system — built with **Python + Streamlit**.

| Feature | Technology |
|---|---|
| UI / dashboard (9 pages) | Streamlit, Plotly |
| Career recommendations (top 5, explainable) | scikit-learn TF-IDF + cosine similarity |
| AI explanations, resume polish, roadmap tips, chatbot | Google Gemini API (`google-genai`) |
| Retrieval-Augmented Generation | FAISS (TF-IDF+SVD embeddings offline, or Gemini embeddings) |
| Storage | SQLite |
| Resume parsing / export | pypdf, python-docx, fpdf2 |
| Live jobs (optional) | Adzuna API |

## Pages
Home · Profile · Career Recommendations · Resume Studio · ATS Resume Analyzer · Skill-Gap Analysis · Learning Roadmap · Job Opportunities · Career Assistant

## Scoring formulas
- **Career match** = 45% skill overlap + 35% TF-IDF profile-text similarity + 20% interest/goal similarity.
- **ATS estimate** = 40% keyword coverage + 30% TF-IDF relevance + 20% section completeness + 10% readability. It is an estimate, not a real ATS.
- **Skill status**: Acquired (listed + evidence in projects/certs/experience), Unverified (listed only), Not provided.

## Setup (local)
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your key in GEMINI_API_KEY
streamlit run app.py
```
Open http://localhost:8501. Without a Gemini key, all ML features (recommendations, ATS, skill gaps, roadmap, RAG search, resume drafting/export) still work; AI buttons are disabled.

## Tests
```bash
pytest -q
```

## Deploy on Render
1. Push this folder to a GitHub repo (`.env` and `*.db` are git-ignored).
2. In Render: **New → Blueprint**, pick the repo (uses `render.yaml`), or create a Web Service with
   - Build: `pip install -r requirements.txt`
   - Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
3. Add `GEMINI_API_KEY` (and optionally `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`) as environment variables.
4. Note: Render's free disk is ephemeral; attach a persistent disk and set `CAREERCOMPASS_DB=/var/data/careercompass.db` to keep data.

## Project structure
```
app.py                 # entry point, sidebar navigation
core/                  # logic: db, recommender, ats, skillgap, rag, gemini, resume, jobs, data
views/                 # one module per page + ui.py (styling/helpers)
data/                  # careers, learning resources, demo jobs, career guide (RAG corpus)
tests/                 # pytest suite
.streamlit/config.toml # theme
render.yaml            # Render blueprint
```
Job listings in `data/jobs.json` are **demo data** and clearly labelled in the UI.
