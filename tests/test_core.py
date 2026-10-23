import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from core import db  # noqa: E402
from core.ats import analyze  # noqa: E402
from core.rag import RAGIndex  # noqa: E402
from core.recommender import recommend  # noqa: E402
from core.resume import draft_from_profile, to_docx, to_pdf  # noqa: E402
from core.skillgap import analyze_gap, build_roadmap  # noqa: E402

PROFILE = {"name": "Asha", "education": "B.Tech/B.E.", "skills": ["Python", "SQL", "Machine Learning", "Pandas"],
           "interests": ["data", "ai"], "goals": "Become a data scientist", "projects": "Churn model in Python with Pandas",
           "hours_per_week": 10}


def test_recommend_returns_top5_ranked():
    recs = recommend(PROFILE)
    assert len(recs) == 5
    assert recs[0]["title"] in {"Data Scientist", "Machine Learning Engineer"}
    assert [r["score"] for r in recs] == sorted([r["score"] for r in recs], reverse=True)


def test_recommend_rejects_empty_profile():
    with pytest.raises(ValueError):
        recommend({})


def test_ats_score_higher_for_matching_resume():
    jd = "Data analyst with SQL, Python, Power BI dashboards and statistics experience."
    good = "Summary\nSkills: SQL, Python, Power BI, statistics\nExperience\n- Built dashboards in Power BI\nEducation B.Tech"
    bad = "I like painting and travel."
    assert analyze(good, jd)["score"] > analyze(bad, jd)["score"]


def test_skill_gap_statuses():
    gap = analyze_gap(PROFILE, "Data Scientist")
    st = {r["skill"]: r["status"] for r in gap["rows"]}
    assert st["Python"] == "Acquired"
    assert st["Machine Learning"] == "Unverified"
    assert st["Statistics"] == "Not provided"


def test_roadmap_respects_weekly_hours():
    tasks = build_roadmap(analyze_gap(PROFILE, "Data Scientist"), 10)
    by_week = {}
    for t in tasks:
        by_week[t["week"]] = by_week.get(t["week"], 0) + t["hours"]
    assert all(h <= 10 + 1e-6 for h in by_week.values())


def test_db_roundtrip(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.save_profile(conn, PROFILE)
    assert db.load_profile(conn)["name"] == "Asha"
    db.add_message(conn, "user", "hi")
    assert db.messages(conn)[0]["content"] == "hi"


def test_rag_finds_resume_guidance():
    hits = RAGIndex(use_gemini=False).search("how to write an ATS friendly resume", k=3)
    assert any("resume" in h["text"].lower() for h in hits)


def test_resume_export():
    text = draft_from_profile(PROFILE, "Data Scientist")
    assert "Asha" in text and "SKILLS" in text
    assert to_pdf(text)[:4] == b"%PDF"
    assert to_docx(text)[:2] == b"PK"
