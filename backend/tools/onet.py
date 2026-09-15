from pathlib import Path

import pandas as pd
from langchain_core.tools import tool


DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "onet"
)


# Generic words that should not determine occupation matching
GENERIC_TITLE_WORDS = {
    "engineer",
    "engineers",
    "developer",
    "developers",
    "scientist",
    "scientists",
    "analyst",
    "analysts",
    "specialist",
    "specialists",
    "manager",
    "managers",
    "architect",
    "architects",
}


def normalize_text(value: str) -> str:
    """Normalize text for matching."""
    return " ".join(
        str(value).strip().lower().split()
    )


def match_occupation(
    job_title: str,
    job_titles: pd.DataFrame,
    user_skills: list[str] | None = None,
    context: list[str] | None = None
) -> list[dict]:
    """
    Match a job title to relevant O*NET occupations.

    Ranking uses:
    1. Specific job-title relevance
    2. Context relevance against O*NET technologies
    3. User-skill relevance against O*NET technologies
    """

    normalized_title = normalize_text(job_title)

    # Handle simple singular/plural differences
    normalized_title_variants = {
        normalized_title,
        normalized_title.rstrip("s"),
        normalized_title + "s"
    }

    user_skills = [
        normalize_text(skill)
        for skill in (user_skills or [])
        if normalize_text(skill)
    ]

    context = [
        normalize_text(item)
        for item in (context or [])
        if normalize_text(item)
    ]

    job_titles = job_titles.copy()

    # --------------------------------
    # Normalize O*NET title fields
    # --------------------------------
    job_titles["job_title_normalized"] = (
        job_titles["Job Title"]
        .apply(normalize_text)
    )

    job_titles["occupation_title_normalized"] = (
        job_titles["Title"]
        .apply(normalize_text)
    )

    # --------------------------------
    # Extract meaningful title words
    # --------------------------------
    title_words = [
        word
        for word in normalized_title.split()
        if (
            len(word) > 2
            and word not in GENERIC_TITLE_WORDS
        )
    ]

    # --------------------------------
    # Title relevance
    # --------------------------------
    def calculate_title_score(row) -> int:

        job_title_text = row["job_title_normalized"]
        occupation_title = row["occupation_title_normalized"]

        # Exact O*NET occupation title match
        if occupation_title in normalized_title_variants:
            return 12

        # Exact Job Title match
        if job_title_text == normalized_title:
            return 10

        # Full phrase inside Job Title
        if normalized_title in job_title_text:
            return 5

        # Full phrase inside occupation title
        if normalized_title in occupation_title:
            return 5

        # Meaningful word matching
        if not title_words:
            return 0

        occupation_words = set(
            occupation_title.split()
        )

        matched_words = [
            word
            for word in title_words
            if word in occupation_words
        ]

        # All meaningful words match
        if len(matched_words) == len(title_words):
            return 4

        # At least two meaningful words match
        if len(matched_words) >= 2:
            return 3
        return 0
    
    job_titles["title_score"] = job_titles.apply(
        calculate_title_score,
        axis=1
    )

    # --------------------------------
    # Initial candidates
    # --------------------------------
    candidates = job_titles[
        job_titles["title_score"] > 0
    ].copy()

    if candidates.empty:
        return []

    # --------------------------------
    # Load O*NET software data
    # --------------------------------
    software = pd.read_csv(
        DATA_DIR / "onet_software_mapping.csv"
    )

    software["element_normalized"] = (
        software["Element Name"]
        .fillna("")
        .apply(normalize_text)
    )

    software["example_normalized"] = (
        software["Workplace Example"]
        .fillna("")
        .apply(normalize_text)
    )

    # --------------------------------
    # Score context and user skills
    # --------------------------------
    ranked_occupations = []

    for _, occupation in candidates.iterrows():

        soc_code = occupation["O*NET-SOC Code"]

        occupation_software = software[
            software["O*NET-SOC Code"] == soc_code
        ]

        technology_records = []

        for _, row in occupation_software.iterrows():

            element = row["element_normalized"]
            example = row["example_normalized"]

            technology_records.append(
                f"{element} {example}"
            )

        # ----------------------------
        # Context matching
        # ----------------------------
        matched_context = []

        for item in context:
            if any(
                item in technology_text
                for technology_text in technology_records
            ):
                matched_context.append(item)

        context_score = len(
            set(matched_context)
        )

        # ----------------------------
        # User skill matching
        # ----------------------------
        matched_skills = []

        for skill in user_skills:
            if any(
                skill in technology_text
                for technology_text in technology_records
            ):
                matched_skills.append(skill)

        skill_match_score = len(
            set(matched_skills)
        )

        # ----------------------------
        # Final hybrid score
        # ----------------------------
        hybrid_score = (
            occupation["title_score"] * 3
            + context_score * 2
            + skill_match_score
        )

        ranked_occupations.append({
            "O*NET-SOC Code": soc_code,
            "Title": occupation["Title"],
            "hybrid_score": hybrid_score,
            "title_score": occupation["title_score"],
            "context_score": context_score,
            "skill_match_score": skill_match_score,
            "matched_context": matched_context,
            "matched_user_skills": matched_skills
        })

    # --------------------------------
    # Rank occupations
    # --------------------------------
    ranked_occupations.sort(
        key=lambda item: (
            item["hybrid_score"],
            item["title_score"],
            item["context_score"],
            item["skill_match_score"]
        ),
        reverse=True
    )

    # --------------------------------
    # Remove duplicate occupations
    # --------------------------------
    unique_occupations = []

    seen_soc_codes = set()

    for occupation in ranked_occupations:

        soc_code = occupation["O*NET-SOC Code"]

        if soc_code in seen_soc_codes:
            continue

        seen_soc_codes.add(soc_code)
        unique_occupations.append(occupation)

        if len(unique_occupations) == 3:
            break

    return unique_occupations


@tool
def get_occupation_information(
    job_title: str,
    user_skills: list[str] | None = None,
    context: list[str] | None = None
) -> dict:
    """
    Retrieve O*NET occupation, essential skills,
    and technology information for a job title.
    """

    # --------------------------------
    # 1. Load job title mapping
    # --------------------------------
    job_titles = pd.read_csv(
        DATA_DIR / "onet_job_title_mapping.csv"
    )

    user_skills = [
        normalize_text(skill)
        for skill in (user_skills or [])
        if normalize_text(skill)
    ]

    context = [
        normalize_text(item)
        for item in (context or [])
        if normalize_text(item)
    ]

    # --------------------------------
    # 2. Find related occupations
    # --------------------------------
    occupations = match_occupation(
        job_title=job_title,
        job_titles=job_titles,
        user_skills=user_skills,
        context=context
    )

    # --------------------------------
    # No occupation found
    # --------------------------------
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

    # --------------------------------
    # 3. Essential Skills
    # --------------------------------
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

    # --------------------------------
    # 4. Technologies
    # --------------------------------
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
        .dropna()
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