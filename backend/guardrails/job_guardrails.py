def validate_job_analysis(text: str) -> str:
    """
    Basic Guardrails validation for Job Agent output.
    """

    if not isinstance(text, str):
        raise ValueError("Job Agent output must be a string.")

    if not text.strip():
        raise ValueError("Job Agent returned an empty response.")

    required_sections = [
        "job",
        "skill",
        "recommend"
    ]

    text_lower = text.lower()

    missing_sections = [
        section
        for section in required_sections
        if section not in text_lower
    ]

    if missing_sections:
        raise ValueError(
            f"Job Agent output is missing required content: "
            f"{', '.join(missing_sections)}"
        )

    return text 