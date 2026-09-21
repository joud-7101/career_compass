from pathlib import Path
from difflib import SequenceMatcher

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
    Retrieve relevant required skills associated with a job title
    from the Resume Skill Extractor Dataset.
    """

    skills = pd.read_csv(DATA_FILE)

    normalized_title = (
        job_title
        .strip()
        .lower()
    )

    skills["title_normalized"] = (
        skills["title"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Exact title match
    matches = skills[
        skills["title_normalized"] == normalized_title
    ]

    matched_title = job_title

    # Fallback: find the closest available job title
    if matches.empty:

        unique_titles = (
            skills[["title", "title_normalized"]]
            .drop_duplicates()
        )

        unique_titles["similarity"] = (
            unique_titles["title_normalized"]
            .apply(
                lambda title: SequenceMatcher(
                    None,
                    normalized_title,
                    title
                ).ratio()
            )
        )

        best_match = (
            unique_titles
            .sort_values("similarity", ascending=False)
            .iloc[0]
        )

        # Only use the fallback if the title is reasonably similar
        if best_match["similarity"] >= 0.60:

            matched_title = best_match["title"]

            matches = skills[
                skills["title_normalized"]
                == best_match["title_normalized"]
            ]

        else:
            return {
                "job_title": job_title,
                "matched_title": None,
                "required_skills": []
            }

    required_skills = (
        matches["skill_canonical"]
        .dropna()
        .drop_duplicates()
        .head(50)
        .tolist()
    )

    return {
        "job_title": job_title,
        "matched_title": matched_title,
        "required_skills": required_skills
    }
    
