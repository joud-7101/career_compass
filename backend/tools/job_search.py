from langchain_core.tools import tool
from jobspy import scrape_jobs


@tool
def search_jobs(
    search_term: str,
    location: str = ""
) -> list[dict]:
    """
    Search for real job opportunities using JobSpy.
    """

    jobs = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term=search_term,
        location=location or "Saudi Arabia",
        results_wanted=10,
        hours_old=72,
        country_indeed="Saudi Arabia",
        verbose=0,
    )

    if jobs.empty:
        return []

    columns = [
        "site",
        "title",
        "company",
        "location",
        "job_type",
        "is_remote",
        "date_posted",
        "job_url",
        "description",
    ]

    available_columns = [
        column for column in columns
        if column in jobs.columns
    ]

    jobs = jobs[available_columns].copy()

    jobs = jobs.fillna("")

    if "job_url" in jobs.columns:
        jobs = jobs.drop_duplicates(
            subset=["job_url"]
        )

    return jobs.head(10).to_dict(
        orient="records"
    )