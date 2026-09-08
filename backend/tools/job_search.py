# Mock job search tool.
# This will later be replaced with the JobSpy library.

from langchain_core.tools import tool


@tool
def search_jobs(
    skills: list[str],
    location: str = ""
) -> list[dict]:
    """
    Search for job opportunities based on skills and location.
    This is currently a mock tool and will later be replaced with JobSpy.
    """

    return [
        {
            "title": "Software Engineer",
            "company": "Example Company",
            "location": location or "Saudi Arabia",
            "required_skills": skills,
            "url": "https://example.com/job"
        }
    ]