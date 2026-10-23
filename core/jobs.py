"""Job listings: bundled DEMO data, plus live Adzuna results when ADZUNA_APP_ID/ADZUNA_APP_KEY are set."""
import os

import requests

from .data import sample_jobs


def adzuna_available():
    return bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))


def search_demo(query: str = "", job_type: str = "All"):
    q = query.lower().strip()
    out = []
    for j in sample_jobs():
        hay = f"{j['title']} {j['company']} {' '.join(j['skills'])}".lower()
        if (not q or any(w in hay for w in q.split())) and (job_type == "All" or j["type"] == job_type):
            out.append({**j, "source": "Demo data"})
    return out


def search_adzuna(query: str, location: str = "", country: str = None, limit: int = 20):
    country = country or os.getenv("ADZUNA_COUNTRY", "in")
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {"app_id": os.environ["ADZUNA_APP_ID"], "app_key": os.environ["ADZUNA_APP_KEY"],
              "what": query, "where": location, "results_per_page": limit, "content-type": "application/json"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return [{"title": j.get("title", ""), "company": j.get("company", {}).get("display_name", ""),
             "location": j.get("location", {}).get("display_name", ""), "type": j.get("contract_time", "N/A"),
             "skills": [], "url": j.get("redirect_url", ""), "description": (j.get("description") or "")[:300],
             "source": "Adzuna (live)"} for j in r.json().get("results", [])]


def match_score(job, user_skills):
    js = {s.lower() for s in job.get("skills", [])}
    if not js:
        return None
    return round(100 * len(js & {s.lower() for s in user_skills}) / len(js))
