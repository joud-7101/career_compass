
# backend/tools/freelance/freelancer_api.py

import os
import re
from dotenv import load_dotenv
from apify_client import ApifyClient
from langchain_core.tools import tool

load_dotenv()


# ============================================================
# Helper: Normalize text
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text so skill matching is more reliable.
    """
    if not text:
        return ""

    text = text.lower()

    # Replace special characters with spaces
    text = re.sub(r"[^a-z0-9+#.\- ]", " ", text)

    # Remove duplicate whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# Helper: Calculate skill match
# ============================================================

def calculate_skill_match(
    project: dict,
    skills: list[str]
) -> tuple[float, list[str]]:
    """
    Calculate project relevance based primarily on
    the project's actual skills, with description/title
    used as secondary evidence.
    """

    title = normalize_text(
        project.get("title", "")
    )

    description = normalize_text(
        project.get("description", "")
    )

    project_skills = project.get("skills", [])

    if not isinstance(project_skills, list):
        project_skills = []

    normalized_project_skills = [
        normalize_text(str(skill))
        for skill in project_skills
    ]

    matched_skills = []

    for skill in skills:

        skill_normalized = normalize_text(skill)

        if not skill_normalized:
            continue

        # ------------------------------------------------
        # 1. Strong match: actual Freelancer skill
        # ------------------------------------------------

        skill_in_project_skills = any(
            skill_normalized == project_skill
            or skill_normalized in project_skill
            or project_skill in skill_normalized
            for project_skill in normalized_project_skills
        )

        if skill_in_project_skills:
            matched_skills.append(skill)
            continue

        # ------------------------------------------------
        # 2. Secondary match: title / description
        # ------------------------------------------------

        # Escape skill so regex characters don't cause
        # unexpected matches.
        escaped_skill = re.escape(
            skill_normalized
        )

        pattern = rf"\b{escaped_skill}\b"

        if (
            re.search(pattern, title)
            or re.search(pattern, description)
        ):
            matched_skills.append(skill)

    # ----------------------------------------------------
    # Calculate score
    # ----------------------------------------------------

    if not skills:
        return 0.0, []

    score = (
        len(matched_skills) / len(skills)
    ) * 100

    return round(score, 2), matched_skills


# ============================================================
# Helper: Normalize project
# ============================================================

def normalize_project(
    project: dict,
    skills: list[str]
) -> dict:
    """
    Convert the raw Apify project into a clean structure
    used by the Freelancer Agent.
    """

    score, matched_skills = calculate_skill_match(
        project,
        skills
    )

    return {
        "title": project.get("title"),

        "description": (
            project.get("description")
            or project.get("previewDescription")
            or ""
        ),

        "url": project.get("url"),

        "skills": project.get("skills", []),

        "matched_skills": matched_skills,

        "match_score": score,

        "budget_min": project.get("budgetMin"),

        "budget_max": project.get("budgetMax"),

        "currency": project.get("currency"),

        "project_type": project.get("type"),

        "bid_count": project.get("bidCount"),

        "posted_at": project.get("postedAt"),

        "bidding_deadline": project.get(
            "biddingDeadline"
        ),
    }


# ============================================================
# Main LangChain Tool
# ============================================================

@tool
def search_freelancer_projects(
    skills: list[str]
) -> list[dict]:
    """
    Search Freelancer.com for real freelance projects
    using Apify.

    The tool retrieves a larger pool of projects,
    calculates skill relevance, filters weak matches,
    and returns the top 10 projects.
    """

    apify_token = os.getenv("APIFY_API_TOKEN")

    if not apify_token:
        raise ValueError(
            "APIFY_API_TOKEN is not configured."
        )

    if not skills:
        raise ValueError(
            "At least one skill is required."
        )

    # ========================================================
    # Initialize Apify
    # ========================================================

    client = ApifyClient(apify_token)

    actor = client.actor(
        "unfenced-group/freelancercom-scraper"
    )

    # ========================================================
    # Search query
    # ========================================================

    search_query = " ".join(skills)

    print("\n==========================================")
    print("Freelancer Search")
    print("==========================================")
    print("Skills:", skills)
    print("Search query:", search_query)

    # ========================================================
    # Retrieve MORE projects than we eventually return
    # ========================================================

    run_input = {
        "searchQuery": search_query,

        # Retrieve 30 instead of only 10
        "maxResults": 30,

        # Get complete project information
        "fetchDetails": True,

        # Prefer recent projects
        "daysOld": 14,

        # Avoid duplicate/reposted projects
        "skipReposts": True,
    }

    print("\nRunning Apify Actor...")

    run = actor.call(
        run_input=run_input
    )

    if run is None:
        raise RuntimeError(
            "Apify Actor failed to start."
        )

    # ========================================================
    # Get dataset
    # ========================================================

    dataset = client.dataset(
        run.default_dataset_id
    )

    raw_projects = dataset.list_items().items

    print(
        f"Projects retrieved from Apify: "
        f"{len(raw_projects)}"
    )

    # ========================================================
    # Normalize + score
    # ========================================================

    projects = []

    for project in raw_projects:

        normalized = normalize_project(
            project,
            skills
        )

        projects.append(normalized)

    # ========================================================
    # Remove projects with no skill match
    # ========================================================

    matched_projects = [
        project
        for project in projects
        if project["match_score"] > 0
    ]

    print(
        f"Projects with skill matches: "
        f"{len(matched_projects)}"
    )

    # ========================================================
    # Sort by match score
    # ========================================================

    matched_projects.sort(
        key=lambda project: (
            project["match_score"],
            len(project["matched_skills"])
        ),
        reverse=True
    )

    # ========================================================
    # Return TOP 10
    # ========================================================

    top_projects = matched_projects[:10]

    print(
        f"Returning top {len(top_projects)} projects"
    )

    # ========================================================
    # Debug output
    # ========================================================

    print("\n========== TOP MATCHES ==========")

    for i, project in enumerate(
        top_projects,
        start=1
    ):

        print(
            f"\n{i}. {project['title']}"
        )

        print(
            f"   Match: "
            f"{project['match_score']}%"
        )

        print(
            f"   Matched skills: "
            f"{project['matched_skills']}"
        )

        print(
            f"   URL: "
            f"{project['url']}"
        )

    print("\n==========================================\n")

    return top_projects






    