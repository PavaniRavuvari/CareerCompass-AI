"""Explainable career matching with TF-IDF + cosine similarity (scikit-learn).

Final score (0-100) = 45% skill overlap + 35% TF-IDF text similarity + 20% interest/goal similarity.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import careers, norm, split_list

W_SKILL, W_TEXT, W_INTEREST = 0.45, 0.35, 0.20


def profile_text(p: dict) -> str:
    parts = [p.get("education", ""), p.get("specialization", ""), " ".join(split_list(p.get("skills"))),
             p.get("projects", ""), p.get("certifications", ""), p.get("experience", ""),
             " ".join(split_list(p.get("interests"))), p.get("goals", ""), " ".join(split_list(p.get("target_roles")))]
    return " ".join(x for x in parts if x)


def career_text(c: dict) -> str:
    return " ".join([c["title"], c["description"], " ".join(c["skills"]), " ".join(c["interests"])])


def recommend(profile: dict, top_k: int = 5):
    cs = careers()
    ptext = profile_text(profile)
    if not ptext.strip():
        raise ValueError("Profile is empty — add skills, interests or goals first.")
    docs = [career_text(c) for c in cs]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    m = vec.fit_transform(docs + [ptext])
    text_sim = cosine_similarity(m[-1], m[:-1]).ravel()

    interest_text = " ".join(split_list(profile.get("interests")) + [profile.get("goals", "")] + split_list(profile.get("target_roles")))
    if interest_text.strip():
        ivec = TfidfVectorizer(stop_words="english")
        im = ivec.fit_transform([" ".join(c["interests"]) + " " + c["title"] for c in cs] + [interest_text])
        int_sim = cosine_similarity(im[-1], im[:-1]).ravel()
    else:
        int_sim = [0.0] * len(cs)

    user_skills = {norm(s) for s in split_list(profile.get("skills"))}
    results = []
    for i, c in enumerate(cs):
        req = [norm(s) for s in c["skills"]]
        matched = [s for s in c["skills"] if norm(s) in user_skills]
        missing = [s for s in c["skills"] if norm(s) not in user_skills]
        skill_score = len(matched) / len(req) if req else 0
        score = 100 * (W_SKILL * skill_score + W_TEXT * float(text_sim[i]) + W_INTEREST * float(int_sim[i]))
        results.append({
            "title": c["title"], "score": round(min(score, 100), 1),
            "skill_overlap": round(100 * skill_score, 1), "text_similarity": round(100 * float(text_sim[i]), 1),
            "interest_similarity": round(100 * float(int_sim[i]), 1),
            "matched_skills": matched, "missing_skills": missing,
            "description": c["description"], "salary": c.get("salary", ""), "outlook": c.get("outlook", ""),
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]
