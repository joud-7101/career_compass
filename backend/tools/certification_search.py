"""def search_certifications(
    skills: list[str],
    interests: list[str]
) -> list[dict]:

    return [
        {
            "name": "AWS Certified Developer",
            "provider": "AWS",
            "reason": "Relevant to software development skills.",
            "url": "https://aws.amazon.com/certification/"
        }
    ]
    #
    #
    Cert Atlas
   +
Web Search """



import re
import unicodedata
from functools import lru_cache

import requests


BASE_DATA_URL = (
    "https://raw.githubusercontent.com/"
    "hans6883/cert-atlas/master/data"
)

INDEX_URL = f"{BASE_DATA_URL}/index.json"

REQUEST_TIMEOUT = 30


def _normalize(value: object) -> str:
    """
    Normalize text to make certification
    names and codes easier to compare.
    """

    text = "" if value is None else str(value)

    text = unicodedata.normalize(
        "NFKC",
        text
    ).casefold()

    text = (
        text
        .replace("–", "-")
        .replace("—", "-")
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def _get_json(url: str) -> dict:
    """
    Download JSON data from Cert Atlas.
    """

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object from {url}"
        )

    return data


@lru_cache(maxsize=1)
def load_certifications() -> list[dict]:
    """
    Load the Cert Atlas certification index.
    The result is cached to avoid downloading
    the same data for every request.
    """

    data = _get_json(INDEX_URL)

    exams = data.get(
        "exams",
        []
    )

    if not isinstance(exams, list):
        raise ValueError(
            "Cert Atlas index does not contain a valid exams list."
        )

    return exams


def refresh_certifications() -> None:
    """
    Clear the cache so the next request
    loads the latest Cert Atlas data.
    """

    load_certifications.cache_clear()


def _is_retired(exam: dict) -> bool:
    """
    Check whether an exam is retired.
    """

    return (
        _normalize(
            exam.get("lifecycle_status")
        )
        == "retired"
    )


def _clean_exam(exam: dict) -> dict:
    """
    Keep the fields needed by CareerCompass.
    """

    return {
        "exam_id": exam.get("exam_id"),
        "exam_name": exam.get("exam_name"),
        "exam_code": exam.get("exam_code"),
        "certifying_body": exam.get(
            "certifying_body"
        ),
        "vendor_slug": exam.get(
            "vendor_slug"
        ),
        "domains": exam.get("domains"),
        "total_questions": exam.get(
            "total_questions"
        ),
        "duration_minutes": exam.get(
            "duration_minutes"
        ),
        "source_url": exam.get(
            "source_url"
        ),
        "practice_url": exam.get(
            "practice_url"
        ),
        "enriched": exam.get("enriched"),
        "lifecycle_status": exam.get(
            "lifecycle_status"
        ),
        "retires_on": exam.get(
            "retires_on"
        ),
        "retired_on": exam.get(
            "retired_on"
        ),
        "replacement_exam_code": exam.get(
            "replacement_exam_code"
        ),
        "replacement_url": exam.get(
            "replacement_url"
        ),
    }


def get_all_certifications(
    include_retired: bool = False
) -> list[dict]:
    """
    Return all certifications from Cert Atlas.

    Retired certifications are excluded
    by default.
    """

    exams = load_certifications()

    if not include_retired:
        exams = [
            exam
            for exam in exams
            if not _is_retired(exam)
        ]

    return [
        _clean_exam(exam)
        for exam in exams
    ]


def search_certifications(
    query: str,
    include_retired: bool = False
) -> list[dict]:
    """
    Search certifications by:

    - Exam name
    - Exam code
    - Certifying body
    - Exam ID

    Returns all matching certifications.
    There is no fixed result limit.
    """

    search_value = _normalize(query)

    if not search_value:
        return []

    words = search_value.split()

    matches: list[
        tuple[int, dict]
    ] = []

    for exam in load_certifications():

        if (
            not include_retired
            and _is_retired(exam)
        ):
            continue

        exam_id = _normalize(
            exam.get("exam_id")
        )

        exam_name = _normalize(
            exam.get("exam_name")
        )

        exam_code = _normalize(
            exam.get("exam_code")
        )

        provider = _normalize(
            exam.get("certifying_body")
        )

        searchable_text = " ".join([
            exam_name,
            exam_code,
            provider,
            exam_id
        ])

        score = 0

        if search_value == exam_id:
            score = 100

        elif search_value == exam_code:
            score = 95

        elif search_value == exam_name:
            score = 90

        elif search_value in exam_name:
            score = 70

        elif search_value in exam_code:
            score = 65

        elif search_value in provider:
            score = 50

        elif all(
            word in searchable_text
            for word in words
        ):
            score = 30

        if score > 0:
            matches.append(
                (
                    score,
                    _clean_exam(exam)
                )
            )

    matches.sort(
        key=lambda item: (
            -item[0],
            _normalize(
                item[1].get(
                    "exam_name"
                )
            )
        )
    )

    return [
        exam
        for _, exam in matches
    ]


def find_certification(
    identifier: str,
    include_retired: bool = True
) -> dict | None:
    """
    Find one certification using:

    - exam_id
    - exam_code
    - exact exam_name

    exam_id is preferred because
    it is unique.
    """

    value = _normalize(identifier)

    if not value:
        return None

    exams = load_certifications()

    if not include_retired:
        exams = [
            exam
            for exam in exams
            if not _is_retired(exam)
        ]

    # Best option: unique exam_id
    for exam in exams:

        if value == _normalize(
            exam.get("exam_id")
        ):
            return _clean_exam(exam)

    # Try exam code
    code_matches = [
        exam
        for exam in exams
        if value == _normalize(
            exam.get("exam_code")
        )
    ]

    if len(code_matches) == 1:
        return _clean_exam(
            code_matches[0]
        )

    # Try exact exam name
    name_matches = [
        exam
        for exam in exams
        if value == _normalize(
            exam.get("exam_name")
        )
    ]

    if len(name_matches) == 1:
        return _clean_exam(
            name_matches[0]
        )

    # Avoid choosing the wrong exam
    # when names/codes are duplicated.
    return None


def get_certification_blueprint(
    identifier: str
) -> dict | None:
    """
    Load the full Cert Atlas blueprint
    for the selected certification.

    exam_id should be used whenever possible.
    """

    exam = find_certification(
        identifier
    )

    if exam is None:
        return None

    vendor_slug = exam.get(
        "vendor_slug"
    )

    exam_id = exam.get(
        "exam_id"
    )

    if not vendor_slug or not exam_id:
        return None

    blueprint_url = (
        f"{BASE_DATA_URL}/"
        f"{vendor_slug}/"
        f"{exam_id}.json"
    )

    return _get_json(
        blueprint_url
    )