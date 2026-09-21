from backend.schemas.profile import (
    UserProfile,
    ProfileSource,
)


def _normalize(value: str | None) -> str:
    if not value:
        return ""

    value = value.strip().lower()

    value = (
        value
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
    )

    return " ".join(value.split())


def _normalize_url(value: str | None) -> str:
    value = _normalize(value)

    return value.rstrip("/")


def _normalize_issuer(value: str | None) -> str:
    if not value:
        return ""

    return _normalize(value)


def _set_source(item, source: str, reference: str | None = None):
    """
    Preserve the item's existing source when available.
    Otherwise assign the source of the extraction.
    """
    if item.source is None:
        item.source = ProfileSource(
            kind=source,
            reference=reference,
        )

    return item


def _merge_unique_items(
    cv_items: list,
    portfolio_items: list,
    key_func,
) -> list:
    merged = []
    seen = set()

    for item in cv_items:
        key = key_func(item)

        if key and key not in seen:
            merged.append(item)
            seen.add(key)

    for item in portfolio_items:
        key = key_func(item)

        if key and key not in seen:
            merged.append(item)
            seen.add(key)

    return merged


def merge_profiles(
    cv_profile: UserProfile,
    portfolio_profile: UserProfile | None = None,
    portfolio_url: str | None = None,
) -> UserProfile:

    cv = cv_profile.model_copy(deep=True)

    # ---------------------------------------------
    # CV source
    # ---------------------------------------------

    for item in cv.education:
        _set_source(item, "resume")

    for item in cv.experience:
        _set_source(item, "resume")

    for item in cv.skills:
        _set_source(item, "resume")

    for item in cv.certifications:
        _set_source(item, "resume")

    for item in cv.projects:
        _set_source(item, "resume")

    for item in cv.achievements:
        _set_source(item, "resume")

    for item in cv.volunteering:
        _set_source(item, "resume")

    for item in cv.professional_links:
        if portfolio_url and str(item.url) == portfolio_url:
            continue


    if portfolio_profile is None:
        cv.review_status = "draft"
        return cv


    portfolio = portfolio_profile.model_copy(
        deep=True
    )

    # ---------------------------------------------
    # Portfolio source
    # ---------------------------------------------

    for item in portfolio.education:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.experience:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.skills:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.certifications:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.projects:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.achievements:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )

    for item in portfolio.volunteering:
        _set_source(
            item,
            "portfolio",
            portfolio_url,
        )


    # ---------------------------------------------
    # Personal information
    # ---------------------------------------------

    merged_personal = cv.personal_information.model_copy(
        deep=True
    )

    portfolio_personal = portfolio.personal_information

    if not merged_personal.name:
        merged_personal.name = portfolio_personal.name

    if not merged_personal.email:
        merged_personal.email = portfolio_personal.email

    if not merged_personal.phone:
        merged_personal.phone = portfolio_personal.phone

    if not merged_personal.location:
        merged_personal.location = portfolio_personal.location


    # ---------------------------------------------
    # Professional summary
    # ---------------------------------------------

    merged_summary = (
        cv.professional_summary
        or portfolio.professional_summary
    )


    # ---------------------------------------------
    # Education
    # ---------------------------------------------

    merged_education = _merge_unique_items(
        cv.education,
        portfolio.education,
        lambda item: (
            _normalize(item.institution),
            _normalize(item.degree),
        ),
    )


    # ---------------------------------------------
    # Experience
    # ---------------------------------------------

    merged_experience = _merge_unique_items(
        cv.experience,
        portfolio.experience,
        lambda item: (
            _normalize(item.title),
            _normalize(item.company),
        ),
    )


    # ---------------------------------------------
    # Skills
    # ---------------------------------------------

    merged_skills = _merge_unique_items(
        cv.skills,
        portfolio.skills,
        lambda item: _normalize(item.name),
    )


    # ---------------------------------------------
    # Certifications
    # ---------------------------------------------

    merged_certifications = _merge_unique_items(
        cv.certifications,
        portfolio.certifications,
        lambda item: (
            _normalize(item.name),
            _normalize_issuer(item.issuer),
        ),
    )


    # ---------------------------------------------
    # Projects
    # ---------------------------------------------
    
    print("CV PROJECT COUNT:", len(cv.projects))
    print("PORTFOLIO PROJECT COUNT:", len(portfolio.projects))

    print("PORTFOLIO PROJECTS BEFORE MERGE:")
    for item in portfolio.projects:
        print("-", item.name, "->", item.source.kind if item.source else None)

    merged_projects = _merge_unique_items(
        cv.projects,
        portfolio.projects,
        lambda item: _normalize(item.name),
    )


    # ---------------------------------------------
    # Languages
    # ---------------------------------------------

    merged_languages = []

    seen_languages = set()

    for language in (
        cv.languages + portfolio.languages
    ):
        normalized = _normalize(language)

        if normalized and normalized not in seen_languages:
            merged_languages.append(language)
            seen_languages.add(normalized)


    # ---------------------------------------------
    # Professional links
    # ---------------------------------------------

    merged_links = _merge_unique_items(
        cv.professional_links,
        portfolio.professional_links,
        lambda item: _normalize_url(str(item.url)),
    )


    # ---------------------------------------------
    # Achievements
    # ---------------------------------------------

    merged_achievements = _merge_unique_items(
        cv.achievements,
        portfolio.achievements,
        lambda item: (
            _normalize(item.title),
            _normalize(item.date),
        ),
    )


    # ---------------------------------------------
    # Volunteering
    # ---------------------------------------------

    merged_volunteering = _merge_unique_items(
        cv.volunteering,
        portfolio.volunteering,
        lambda item: (
            _normalize(item.role),
            _normalize(item.organization),
        ),
    )


    # ---------------------------------------------
    # Final unified profile
    # ---------------------------------------------
    print("EDUCATION:")
    for item in merged_education:
        print("-", item.institution, "|", item.degree, "|", item.field_of_study)

    print("CERTIFICATIONS:")
    for item in merged_certifications:
        print("-", item.name, "|", item.issuer)

    print("PROFESSIONAL LINKS:")
    for item in merged_links:
        print("-", item.url)

    print("ACHIEVEMENTS:")
    for item in merged_achievements:
        print("-", item.title, "|", item.date)

    return UserProfile(
        schema_version="1.0",
        personal_information=merged_personal,
        professional_summary=merged_summary,
        education=merged_education,
        experience=merged_experience,
        skills=merged_skills,
        certifications=merged_certifications,
        projects=merged_projects,
        languages=merged_languages,
        professional_links=merged_links,
        achievements=merged_achievements,
        volunteering=merged_volunteering,
        review_status="draft",
    )