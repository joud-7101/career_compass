from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from urllib.parse import urlparse
import re

load_dotenv()


tavily = TavilySearch(
    max_results=8,
    topic="general"
)


# ============================================================
# URL HELPERS
# ============================================================

def normalize_url(url: str) -> str:
    """Normalize URL for duplicate detection."""

    if not url:
        return ""

    return url.rstrip("/")


def is_freelancer_project_url(url: str) -> bool:
    """
    Check whether a URL is an individual Freelancer.com
    project page.
    """

    if not url:
        return False

    parsed = urlparse(url)

    # Must be Freelancer.com
    if "freelancer.com" not in parsed.netloc.lower():
        return False

    path = parsed.path.lower()

    # Individual Freelancer projects use /projects/
    if not path.startswith("/projects/"):
        return False

    return True


# ============================================================
# SEARCH FOR FREELANCER PROJECTS
# ============================================================

def search_freelancer_projects(
    skills_query: str,
    project_type: str = "",
    location: str = ""
) -> list[dict]:

    query = f"""
    Find individual freelance projects on Freelancer.com
    that require these skills:

    {skills_query}
    """

    if project_type:
        query += f"""

        Project type:
        {project_type}
        """

    if location:
        query += f"""

        Location:
        {location}
        """

    query += """

    IMPORTANT:

    Return individual client project listings.

    Prefer URLs containing:

    /projects/

    Do NOT return:

    - /job-search/ pages
    - category pages
    - search pages
    - freelancer profiles
    - hire pages
    - tutorials
    - articles
    - blog posts
    - general employment jobs
    - company career pages

    We need a single project that a freelancer
    can apply to.
    """

    response = tavily.invoke({
        "query": query
    })

    if isinstance(response, str):
        return []

    return response.get("results", [])


# ============================================================
# EXTRACT INDIVIDUAL PROJECT URLS
# ============================================================

def extract_project_results(results: list[dict]) -> list[dict]:

    projects = []

    for result in results:

        original_url = result.get("url", "")
        content = result.get("content", "")
        title = result.get("title", "")
        score = result.get("score", 0)

        # ====================================================
        # CASE 1:
        # Tavily directly returned an individual project URL
        # ====================================================

        if is_freelancer_project_url(original_url):

            projects.append({
                "title": title,
                "url": normalize_url(original_url),
                "description": content,
                "source_score": score,
                "result_type": "individual_project"
            })

            continue

        # ====================================================
        # CASE 2:
        # Tavily returned an aggregate page, but the content
        # contains individual /projects/ URLs
        # ====================================================

        if content:

            matches = re.findall(
                r'https?://(?:www\.)?freelancer\.com/projects/[^\s<>"\'\]\)]+',
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                clean_url = match.rstrip(
                    ".,;:!?)]}>\"'"
                )

                if is_freelancer_project_url(clean_url):

                    projects.append({
                        "title": "",
                        "url": normalize_url(clean_url),
                        "description": "",
                        "source_score": score,
                        "result_type": "extracted_project"
                    })

    return projects


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def deduplicate_projects(projects: list[dict]) -> list[dict]:

    unique_projects = []
    seen_urls = set()

    for project in projects:

        url = normalize_url(
            project.get("url", "")
        )

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        unique_projects.append(project)

    return unique_projects


# ============================================================
# MAIN TOOL
# ============================================================

@tool
def search_freelance_projects(
    skills: list[str],
    project_type: str = "",
    location: str = "",
) -> list[dict]:
    """
    Find individual Freelancer.com freelance projects
    matching the user's skills and preferences.
    """

    skills_query = " ".join(skills)

    # ========================================================
    # STEP 1 — SEARCH
    # ========================================================

    raw_results = search_freelancer_projects(
        skills_query=skills_query,
        project_type=project_type,
        location=location
    )

    # ========================================================
    # STEP 2 — EXTRACT INDIVIDUAL PROJECTS
    # ========================================================

    projects = extract_project_results(
        raw_results
    )

    # ========================================================
    # STEP 3 — DEDUPLICATE
    # ========================================================

    projects = deduplicate_projects(
        projects
    )

    # ========================================================
    # STEP 4 — RETURN
    # ========================================================

    final_projects = []

    for project in projects[:10]:

        final_projects.append({
            "title": project.get("title", ""),
            "url": project.get("url", ""),
            "description": project.get("description", ""),
            "source_score": project.get("source_score", 0),
            "source": "Freelancer.com",
            "result_type": project.get(
                "result_type",
                "individual_project"
            )
        })

    return final_projects