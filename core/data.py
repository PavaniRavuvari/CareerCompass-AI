"""Loads bundled knowledge data (careers, resources, jobs, guide)."""
import json
import os
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@lru_cache
def careers():
    with open(os.path.join(DATA_DIR, "careers.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def resources():
    with open(os.path.join(DATA_DIR, "resources.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def sample_jobs():
    with open(os.path.join(DATA_DIR, "jobs.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def guide():
    with open(os.path.join(DATA_DIR, "career_guide.md"), encoding="utf-8") as f:
        return f.read()


def career_by_title(title):
    return next((c for c in careers() if c["title"] == title), None)


def norm(skill: str) -> str:
    return skill.strip().lower()


def split_list(text) -> list:
    if not text:
        return []
    if isinstance(text, list):
        return [t.strip() for t in text if str(t).strip()]
    return [t.strip() for t in str(text).replace("\n", ",").split(",") if t.strip()]
