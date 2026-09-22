def validate_job_analysis(text: str) -> str:
    """
    Basic Guardrails validation for Job Agent output.
    """

    if not isinstance(text, str):
        raise ValueError(
            "Job Agent output must be a string."
        )

    if not text.strip():
        raise ValueError(
            "Job Agent returned an empty response."
        )

    return text  