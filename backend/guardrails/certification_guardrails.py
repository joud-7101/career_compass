def validate_certification_analysis(analysis: str) -> str:
    """
    Basic Guardrails validation for Certification Agent output.
    """

    if not isinstance(analysis, str):
        raise ValueError(
            "Certification analysis must be a string."
        )

    if not analysis.strip():
        raise ValueError(
            "Certification Agent returned an empty analysis."
        )

    return analysis 