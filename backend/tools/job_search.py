#search_jobs()
##      ↓
#JobSpy
      ↓
#real jobs this is just a mock tool later it should use jobspy library
def search_jobs(
    skills: list[str],
    location: str = ""
) -> list[dict]:

    return [
        {
            "title": "Software Engineer",
            "company": "Example Company",
            "location": location or "Saudi Arabia",
            "required_skills": skills,
            "url": "https://example.com/job"
        }
    ]