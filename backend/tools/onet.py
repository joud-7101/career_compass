from langchain_core.tools import tool

@tool
def get_occupation_information(
    skills: list[str]
) -> dict:
    """
    Get related occupation information and required skills for a given set of skills.
    """

    return {
        "related_occupations": [
            "Software Developer",
            "Backend Developer",
            "Machine Learning Engineer"
        ],
        "skills": skills
    }