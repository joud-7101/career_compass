from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "onet"
)

@tool
def get_occupation_information(
    job_title: str
) -> dict:
    """
    Retrieve O*NET occupation, essential skills,
    and technology information for a job title.
    """

    # -------------------------
    # 1. Find related occupations
    # -------------------------
    job_titles = pd.read_csv(
        DATA_DIR / "onet_job_title_mapping.csv"
    )

    normalized_title = job_title.strip().lower()

    matches = job_titles[
        job_titles["Job Title"]
        .astype(str)
        .str.strip()
        .str.lower()
        == normalized_title
    ]

    occupations = (
        matches[
            ["O*NET-SOC Code", "Title"]
        ]
        .drop_duplicates()
        .to_dict(orient="records")
    )

    if not occupations:
        return {
            "job_title": job_title,
            "related_occupations": [],
            "essential_skills": [],
            "technologies": {
                "in_demand": [],
                "hot": [],
                "examples": []
            }
        }

    soc_codes = [
        occupation["O*NET-SOC Code"]
        for occupation in occupations
    ]

    # -------------------------
    # 2. Essential Skills
    # -------------------------
    essential_skills = pd.read_csv(
        DATA_DIR / "onet_essential_skills_mapping.csv"
    )

    skill_matches = essential_skills[
        essential_skills["O*NET-SOC Code"].isin(soc_codes)
    ]

    skills = (
        skill_matches[
            ["Element Name", "Importance", "Level"]
        ]
        .drop_duplicates()
        .to_dict(orient="records")
    )

    # -------------------------
    # 3. Technologies
    # -------------------------
    software = pd.read_csv(
        DATA_DIR / "onet_software_mapping.csv"
    )

    software_matches = software[
        software["O*NET-SOC Code"].isin(soc_codes)
    ].drop_duplicates()

    in_demand = (
        software_matches[
            software_matches["In Demand"] == "Y"
        ]["Element Name"]
        .drop_duplicates()
        .tolist()
    )

    hot = (
        software_matches[
            software_matches["Hot Technology"] == "Y"
        ]["Element Name"]
        .drop_duplicates()
        .tolist()
    )

    relevant_software = software_matches[
        (software_matches["In Demand"] == "Y") |
        (software_matches["Hot Technology"] == "Y")
    ]

    examples = (
        relevant_software["Workplace Example"]
        .drop_duplicates()
        .tolist()
    )

    return {
        "job_title": job_title,
        "related_occupations": occupations,
        "essential_skills": skills,
        "technologies": {
            "in_demand": in_demand,
            "hot": hot,
            "examples": examples
        }
    }