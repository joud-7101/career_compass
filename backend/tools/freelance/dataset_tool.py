
import ast
import re
from pathlib import Path

import pandas as pd


# ============================================================
# Dataset location
# ============================================================

DATA_PATH = Path(
    "C:\\Users\\alhar\\Documents\\career-compass\\data\\freelancer\\freelancer_job_postings.csv"
)


# ============================================================
# Load dataset
# ============================================================

def load_freelancer_dataset() -> pd.DataFrame:
    """
    Load the historical Freelancer.com dataset.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Freelancer dataset not found at: {DATA_PATH}"
        )

    return pd.read_csv(DATA_PATH)


# ============================================================
# Parse tags
# ============================================================

def parse_tags(value) -> list[str]:
    """
    Convert the dataset's string representation of tags
    into a Python list.
    """

    if pd.isna(value):
        return []

    try:
        tags = ast.literal_eval(value)

        if isinstance(tags, list):
            return [
                str(tag).strip().lower()
                for tag in tags
            ]

    except (ValueError, SyntaxError):
        pass

    return []


# ============================================================
# Normalize text
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for skill matching.
    """

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9+#.\s]",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ============================================================
# Search historical jobs
# ============================================================

def search_historical_jobs(
    skills: list[str],
    limit: int = 20
):
    """
    Search historical freelance jobs based on the user's skills.
    """

    df = load_freelancer_dataset()

    if not skills:
        return []

    # Parse tags
    df["parsed_tags"] = df["tags"].apply(parse_tags)

    normalized_skills = [
        normalize_text(skill)
        for skill in skills
        if skill
    ]

    results = []

    for _, row in df.iterrows():

        title = normalize_text(
            row.get("job_title", "")
        )

        description = normalize_text(
            row.get("job_description", "")
        )

        tags = row["parsed_tags"]

        tags_text = " ".join(tags)

        searchable_text = (
            f"{title} "
            f"{description} "
            f"{tags_text}"
        )

        matched_skills = []

        for skill in normalized_skills:

            if skill and skill in searchable_text:
                matched_skills.append(skill)

        if not matched_skills:
            continue

        results.append({
            "projectId": row.get("projectId"),
            "job_title": row.get("job_title"),
            "job_description": row.get("job_description"),
            "tags": tags,
            "client_country": row.get("client_country"),
            "client_rating": row.get(
                "client_average_rating"
            ),
            "client_reviews": row.get(
                "client_review_count"
            ),
            "min_price": row.get("min_price"),
            "max_price": row.get("max_price"),
            "avg_price": row.get("avg_price"),
            "currency": row.get("currency"),
            "rate_type": row.get("rate_type"),
            "matched_skills": matched_skills
        })

        if len(results) >= limit:
            break

    return results


# ============================================================
# Analyze historical market
# ============================================================

def analyze_historical_market(
    skills: list[str]
) -> dict:
    """
    Analyze historical freelance demand
    for the user's skills.
    """

    df = load_freelancer_dataset()

    if df.empty:
        return {
            "total_historical_jobs": 0,
            "user_skill_demand": [],
            "most_common_skills": []
        }

    # Parse tags
    df["parsed_tags"] = df["tags"].apply(parse_tags)

    total_jobs = len(df)

    normalized_skills = [
        normalize_text(skill)
        for skill in skills
        if skill
    ]

    skill_statistics = []

    for skill in normalized_skills:

        matches = df[
            df["parsed_tags"].apply(
                lambda tags: any(
                    skill in tag
                    for tag in tags
                )
            )
        ]

        count = len(matches)

        skill_statistics.append({
            "skill": skill,
            "matching_jobs": count,
            "percentage": round(
                (count / total_jobs) * 100,
                2
            )
        })

    # ========================================================
    # Most common tags in the entire dataset
    # ========================================================

    all_tags = []

    for tags in df["parsed_tags"]:
        all_tags.extend(tags)

    tag_counts = (
        pd.Series(all_tags)
        .value_counts()
        .head(20)
    )

    common_skills = [
        {
            "skill": skill,
            "job_count": int(count)
        }
        for skill, count in tag_counts.items()
    ]

    return {
        "total_historical_jobs": total_jobs,
        "user_skill_demand": skill_statistics,
        "most_common_skills": common_skills
    }
