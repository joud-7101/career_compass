def validate_freelance_projects(projects: list) -> list:
    """
    Basic Guardrails validation for Freelance Agent output.
    """

    if not isinstance(projects, list):
        raise ValueError(
            "Freelance Agent output must be a list."
        )

    return projects 