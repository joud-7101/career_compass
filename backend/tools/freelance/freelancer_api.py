"""
backend/tools/freelance/freelancer_api.py

Replaces the old Apify-based web scraper with the official Freelancer.com
Python SDK (freelancersdk). This calls the real Freelancer REST API at:

    https://www.freelancer.com/api/projects/0.1/

WHY THIS IS BETTER THAN APIFY
-------------------------------
- Speed   : 1-3 seconds instead of 30-60 seconds
- Cost    : Free (official API quota) vs Apify credits per run
- Stability: Stable versioned JSON API vs scraped HTML that breaks on layout changes
- Accuracy : Official structured data vs parsed web pages
- No risk  : Official client, not a bot that Freelancer.com can block

HOW SKILL MATCHING WORKS
--------------------------
The Freelancer API does not filter by free-text skill names.
It uses numeric job IDs (e.g. "Python" = 13, "Django" = 9).
We handle this transparently:
  1. Call search_projects() with the skill names as a text query.
     Freelancer's own search engine handles the text → ID resolution.
  2. Every project response includes a `jobs` list with full skill
     objects (id, name). We use those for exact skill matching.

TOKEN
------
Uses FREELANCER_ACCESS_TOKEN from .env — the personal developer access
token from https://www.freelancer.com/api/docs. No OAuth2 flow needed
for read-only project searches.
"""

import os
import re
import logging
from dotenv import load_dotenv
from langchain_core.tools import tool

from freelancersdk.session import Session
from freelancersdk.resources.projects.projects import (
    search_projects,
    ProjectsNotFoundException,
)

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================
# Helper: Normalize text
# ============================================================

def normalize_text(text: str) -> str:
    """
    Lowercase and strip punctuation for reliable skill matching.
    Keeps: letters, digits, +, #, ., -, spaces.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\- ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# Helper: Calculate skill match score
# ============================================================

def calculate_skill_match(
    project: dict,
    user_skills: list[str],
) -> tuple[float, list[str]]:
    """
    Score a project against the user's skill list.

    Priority order:
      1. Strong match  — skill appears in project's `jobs` list (official skills).
      2. Secondary match — skill appears in project title or description text.

    Returns (score_0_to_100, list_of_matched_skill_names).
    """
    title = normalize_text(project.get("title", ""))
    # Use preview_description for text matching — it's always populated
    description = normalize_text(
        project.get("preview_description") or project.get("description", "")
    )

    # `jobs` is a list of dicts: [{"id": 13, "name": "Python", ...}, ...]
    project_jobs = project.get("jobs") or []
    normalized_project_skills = [
        normalize_text(j.get("name", ""))
        for j in project_jobs
        if isinstance(j, dict) and j.get("name")
    ]

    matched_skills = []

    for skill in user_skills:
        skill_normalized = normalize_text(skill)
        if not skill_normalized:
            continue

        # ── 1. Strong: skill matches a declared project skill ──────────
        skill_in_project = any(
            skill_normalized == ps
            or skill_normalized in ps
            or ps in skill_normalized
            for ps in normalized_project_skills
        )

        if skill_in_project:
            matched_skills.append(skill)
            continue

        # ── 2. Secondary: word-boundary match in title / description ───
        escaped = re.escape(skill_normalized)
        pattern = rf"\b{escaped}\b"
        if re.search(pattern, title) or re.search(pattern, description):
            matched_skills.append(skill)

    if not user_skills:
        return 0.0, []

    score = (len(matched_skills) / len(user_skills)) * 100
    return round(score, 2), matched_skills


# ============================================================
# Helper: Normalize a raw API project into our standard shape
# ============================================================

def normalize_project(project: dict, user_skills: list[str]) -> dict:
    """
    Convert the raw Freelancer API project dict into the clean structure
    that the Freelancer Agent LLM prompt expects.

    Field mapping (API → our schema):
      seo_url       → url  (full freelancer.com/projects/... link)
      budget        → budget_min / budget_max / budget_str
      jobs          → skills (list of names), used for matching
      bid_stats     → bid_count
      preview_description → description
    """
    score, matched_skills = calculate_skill_match(project, user_skills)

    # ── URL ──────────────────────────────────────────────────────────────
    seo_url = project.get("seo_url", "")
    project_url = (
        f"https://www.freelancer.com/projects/{seo_url}"
        if seo_url
        else None
    )

    # ── Budget ───────────────────────────────────────────────────────────
    # budget = {"minimum": 12500.0, "maximum": 37500.0, ...}
    budget = project.get("budget") or {}
    budget_min = budget.get("minimum")
    budget_max = budget.get("maximum")

    # currency = {"id": 1, "code": "USD", "sign": "$", ...}
    currency = project.get("currency") or {}
    currency_code = currency.get("code", "USD")
    currency_sign = currency.get("sign", "$")

    budget_str = None
    if budget_min is not None and budget_max is not None:
        budget_str = f"{currency_sign}{int(budget_min)}–{currency_sign}{int(budget_max)} {currency_code}"
    elif budget_min is not None:
        budget_str = f"{currency_sign}{int(budget_min)}+ {currency_code}"

    # ── Skills ───────────────────────────────────────────────────────────
    skill_names = [
        j.get("name", "")
        for j in (project.get("jobs") or [])
        if isinstance(j, dict) and j.get("name")
    ]

    # ── Bid stats ────────────────────────────────────────────────────────
    bid_stats = project.get("bid_stats") or {}
    bid_count = bid_stats.get("bid_count")

    return {
        "title": project.get("title"),
        "description": project.get("preview_description") or "",
        "url": project_url,
        "skills": skill_names,
        "matched_skills": matched_skills,
        "match_score": score,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "currency": currency_code,
        "budget_str": budget_str,
        "project_type": project.get("type"),
        "bid_count": bid_count,
        "time_submitted": project.get("time_submitted"),
    }


# ============================================================
# Main LangChain Tool
# ============================================================

@tool
def search_freelancer_projects(
    skills: list[str],
) -> list[dict]:
    """
    Search Freelancer.com for real, live, open freelance projects
    that match the user's skills. Uses the official Freelancer.com
    Python SDK — no scraping, no Apify, no third-party services.

    Steps:
      1. Build a text search query from the user's skills.
      2. Call the Freelancer REST API (active projects only).
      3. Score each result against the user's skill list.
      4. Filter out zero-match projects, sort by score.
      5. Return the top 10.

    Returns a list of normalized project dicts.
    """
    token = os.getenv("FREELANCER_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "FREELANCER_ACCESS_TOKEN is not set in the environment."
        )

    if not skills:
        raise ValueError("At least one skill is required.")

    # ── 1. Create SDK session ─────────────────────────────────────────
    session = Session(oauth_token=token)

    # ── 2. Build the search query ─────────────────────────────────────
    # Join the user's top 6 skills into a text query.
    # Freelancer's search engine handles skill → job ID resolution.
    query = " ".join(skills[:6])

    print("\n==========================================")
    print("Freelancer SDK Search")
    print("==========================================")
    print(f"Skills   : {skills}")
    print(f"Query    : {query}")
    print("Calling  : https://www.freelancer.com/api/projects/0.1/projects/active/")

    # ── 3. Call the API ───────────────────────────────────────────────
    # project_details dict asks the API to include the job/skill names
    # and the full preview description in the response.
    try:
        result = search_projects(
            session,
            query=query,
            project_details={
                "full_description": True,   # include description text
                "job_details": True,        # include skill names in `jobs`
            },
            limit=50,           # fetch a larger pool so we can rank them
            offset=0,
            active_only=True,   # only open projects accepting bids
        )
    except ProjectsNotFoundException:
        print("[Freelancer SDK] No projects found for these skills.")
        return []
    except Exception as exc:
        logger.error(f"[Freelancer SDK] search_projects failed: {exc}")
        raise RuntimeError(
            f"Freelancer API search failed: {exc}"
        ) from exc

    raw_projects = result.get("projects", [])
    print(f"Raw projects returned: {len(raw_projects)}")

    # ── 4. Normalize + score ──────────────────────────────────────────
    normalized = [
        normalize_project(p, skills)
        for p in raw_projects
    ]

    # ── 5. Filter zero-match, sort by score ──────────────────────────
    matched = [p for p in normalized if p["match_score"] > 0]
    matched.sort(
        key=lambda p: (p["match_score"], len(p["matched_skills"])),
        reverse=True,
    )

    top_projects = matched[:10]

    print(f"Matched  : {len(matched)} projects")
    print(f"Returning: {len(top_projects)} top projects")
    print("\n========== TOP MATCHES ==========")
    for i, p in enumerate(top_projects, 1):
        # Encode title safely — some project titles contain non-ASCII characters
        safe_title = (p['title'] or "").encode("ascii", errors="replace").decode()
        safe_budget = (p['budget_str'] or "N/A").encode("ascii", errors="replace").decode()
        print(f"  {i}. {safe_title}")
        print(f"     Match : {p['match_score']}%  |  Skills: {p['matched_skills']}")
        print(f"     Budget: {safe_budget}  |  Bids: {p['bid_count']}")
        print(f"     URL   : {p['url']}")
    print("==========================================\n")

    return top_projects