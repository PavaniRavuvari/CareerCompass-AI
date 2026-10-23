"""ATS-oriented resume compatibility ESTIMATE (not a real ATS).

Score (0-100) = 40% keyword coverage + 30% TF-IDF relevance + 20% section completeness + 10% readability.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SECTIONS = {
    "Contact": r"(email|@|phone|linkedin)",
    "Summary": r"(summary|objective|profile)",
    "Skills": r"skills",
    "Experience": r"(experience|employment|internship|work history)",
    "Education": r"(education|degree|university|college|b\.?tech|bachelor|master)",
    "Projects": r"projects?",
}
ACTION_VERBS = {"built", "developed", "designed", "led", "implemented", "created", "improved", "analyzed",
                "deployed", "managed", "optimized", "automated", "delivered", "reduced", "increased"}


def extract_keywords(jd: str, top_n: int = 25):
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=500)
    m = vec.fit_transform([jd])
    scores = zip(vec.get_feature_names_out(), m.toarray()[0])
    kws = [k for k, s in sorted(scores, key=lambda x: -x[1]) if not k.isdigit() and len(k) > 2]
    return kws[:top_n]


def analyze(resume: str, jd: str) -> dict:
    if not resume.strip() or not jd.strip():
        raise ValueError("Both resume text and job description are required.")
    r_low = resume.lower()
    kws = extract_keywords(jd)
    found = [k for k in kws if re.search(r"\b" + re.escape(k) + r"\b", r_low)]
    missing = [k for k in kws if k not in found]
    kw_cov = len(found) / len(kws) if kws else 0

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    m = vec.fit_transform([resume, jd])
    relevance = float(cosine_similarity(m[0], m[1])[0, 0])

    sections = {name: bool(re.search(p, r_low)) for name, p in SECTIONS.items()}
    sec_score = sum(sections.values()) / len(sections)

    words = re.findall(r"[A-Za-z']+", resume)
    sentences = [s for s in re.split(r"[.\n•\-]+", resume) if s.strip()]
    avg_len = len(words) / max(len(sentences), 1)
    verbs = sum(1 for w in words if w.lower() in ACTION_VERBS)
    numbers = len(re.findall(r"\d+%?", resume))
    readability = 0.4 * (1 if 6 <= avg_len <= 22 else 0.5) + 0.3 * min(verbs / 5, 1) + 0.3 * min(numbers / 4, 1)
    length_ok = 200 <= len(words) <= 900

    score = 100 * (0.40 * kw_cov + 0.30 * min(relevance * 1.6, 1) + 0.20 * sec_score + 0.10 * readability)
    strengths, improvements = [], []
    if kw_cov >= 0.5: strengths.append(f"Covers {len(found)} of {len(kws)} key job terms.")
    else: improvements.append("Add more of the job description's key terms where they truthfully apply.")
    for s, ok in sections.items():
        (strengths if ok else improvements).append(f"{s} section {'present' if ok else 'missing or unclear'}.")
    if verbs < 5: improvements.append("Start bullet points with strong action verbs (built, led, improved…).")
    else: strengths.append("Uses strong action verbs.")
    if numbers < 4: improvements.append("Quantify impact with numbers or percentages.")
    else: strengths.append("Includes quantified achievements.")
    if not length_ok: improvements.append(f"Resume has {len(words)} words; 300–800 is typical for entry level.")

    return {
        "score": round(score, 1),
        "breakdown": {"Keyword coverage": round(100 * kw_cov, 1), "Relevance": round(100 * min(relevance * 1.6, 1), 1),
                      "Sections": round(100 * sec_score, 1), "Readability": round(100 * readability, 1)},
        "found_keywords": found, "missing_keywords": missing, "sections": sections,
        "strengths": strengths, "improvements": improvements, "word_count": len(words),
    }
