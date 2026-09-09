from pathlib import Path

import pandas as pd
from langchain_core.tools import tool


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "resume"
    / "resume_skills_only.csv"
)


@tool
def get_required_skills(job_title: str) -> dict:
    """
    Retrieve required skills associated with a job title
    from the Resume Skill Extractor Dataset.
    """

    skills = pd.read_csv(DATA_FILE)

    normalized_title = job_title.strip().lower()

    matches = skills[
        skills["title"]
        .astype(str)
        .str.strip()
        .str.lower()
        == normalized_title
    ]

    if matches.empty:
        return {
            "job_title": job_title,
            "required_skills": []
        }

    required_skills = (
        matches["skill_canonical"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    return {
        "job_title": job_title,
        "required_skills": required_skills
    }