"""Skill-gap analysis and roadmap generation."""
import math

from .data import career_by_title, norm, resources, split_list


def evidence_text(p):
    return " ".join([p.get("projects", ""), p.get("certifications", ""), p.get("experience", "")]).lower()


def analyze_gap(profile: dict, career_title: str):
    career = career_by_title(career_title)
    if not career:
        raise ValueError(f"Unknown career: {career_title}")
    user = {norm(s) for s in split_list(profile.get("skills"))}
    ev = evidence_text(profile)
    rows = []
    for i, skill in enumerate(career["skills"]):
        s = norm(skill)
        if s in user and s in ev:
            status = "Acquired"
        elif s in user:
            status = "Unverified"  # listed, but no project/cert/experience evidence
        else:
            status = "Not provided"
        priority = "High" if i < len(career["skills"]) // 2 else "Medium"
        rows.append({"skill": skill, "status": status, "priority": priority if status != "Acquired" else "—",
                     "resources": resources_for(skill)})
    acquired = sum(r["status"] == "Acquired" for r in rows)
    partial = sum(r["status"] == "Unverified" for r in rows)
    readiness = round(100 * (acquired + 0.5 * partial) / len(rows), 1)
    return {"career": career_title, "rows": rows, "readiness": readiness, "projects": career.get("projects", [])}


def resources_for(skill, limit=3):
    s = norm(skill)
    return [r for r in resources() if s in [norm(x) for x in r["skills"]]][:limit]


def build_roadmap(gap: dict, hours_per_week: float = 8):
    hours_per_week = max(float(hours_per_week or 8), 1)
    tasks, week, used = [], 1, 0.0
    todo = sorted([r for r in gap["rows"] if r["status"] != "Acquired"], key=lambda r: (r["priority"] != "High", r["status"] == "Unverified"))
    for r in todo:
        need = 6 if r["status"] == "Unverified" else 14
        res = r["resources"][0] if r["resources"] else None
        detail = f"Learn via {res['title']} ({res['url']})" if res else "Study official docs and build a small exercise."
        remaining = need
        while remaining > 0:
            chunk = min(remaining, hours_per_week - used)
            tasks.append({"week": week, "title": f"{'Practice' if r['status']=='Unverified' else 'Learn'} {r['skill']}", "detail": detail, "hours": round(chunk, 1)})
            remaining -= chunk
            used += chunk
            if used >= hours_per_week - 1e-9:
                week, used = week + 1, 0.0
    if used > 0:
        week += 1
    for proj in gap["projects"]:
        tasks.append({"week": week, "title": f"Portfolio project: {proj}", "detail": "Build, document on GitHub, add to resume.", "hours": round(hours_per_week, 1)})
        week += 1
    return tasks


def total_weeks(tasks):
    return max((t["week"] for t in tasks), default=0)
