import re
import unicodedata
from functools import lru_cache

import requests

import numpy as np
from openai import OpenAI

from backend.config import settings


BASE_DATA_URL = (
    "https://raw.githubusercontent.com/"
    "hans6883/cert-atlas/master/data"
)

INDEX_URL = f"{BASE_DATA_URL}/index.json"

REQUEST_TIMEOUT = 30

EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 20
EMBEDDING_BATCH_SIZE = 200

embedding_client = OpenAI(
    api_key=settings.openai_api_key
)

def _normalize(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_json(url: str) -> dict:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object from {url}")
    return data


@lru_cache(maxsize=1)
def load_certifications() -> list[dict]:
    data = _get_json(INDEX_URL)
    exams = data.get("exams", [])
    if not isinstance(exams, list):
        raise ValueError("Cert Atlas index does not contain a valid exams list.")
    return exams


def refresh_certifications() -> None:
    load_certifications.cache_clear()
    _load_semantic_index.cache_clear()


def _is_retired(exam: dict) -> bool:
    return _normalize(exam.get("lifecycle_status")) == "retired"


def _clean_exam(exam: dict) -> dict:
    return {
        "exam_id": exam.get("exam_id"),
        "exam_name": exam.get("exam_name"),
        "exam_code": exam.get("exam_code"),
        "certifying_body": exam.get("certifying_body"),
        "vendor_slug": exam.get("vendor_slug"),
        "domains": exam.get("domains"),
        "total_questions": exam.get("total_questions"),
        "duration_minutes": exam.get("duration_minutes"),
        "source_url": exam.get("source_url"),
        "practice_url": exam.get("practice_url"),
        "enriched": exam.get("enriched"),
        "lifecycle_status": exam.get("lifecycle_status"),
        "retires_on": exam.get("retires_on"),
        "retired_on": exam.get("retired_on"),
        "replacement_exam_code": exam.get("replacement_exam_code"),
        "replacement_url": exam.get("replacement_url"),
    }


def get_all_certifications(include_retired: bool = False) -> list[dict]:
    exams = load_certifications()
    if not include_retired:
        exams = [e for e in exams if not _is_retired(e)]
    return [_clean_exam(e) for e in exams]


def search_certifications(query: str, include_retired: bool = False) -> list[dict]:
    search_value = _normalize(query)
    if not search_value:
        return []

    words = search_value.split()
    matches: list[tuple[int, dict]] = []

    for exam in load_certifications():
        if not include_retired and _is_retired(exam):
            continue

        exam_id = _normalize(exam.get("exam_id"))
        exam_name = _normalize(exam.get("exam_name"))
        exam_code = _normalize(exam.get("exam_code"))
        provider = _normalize(exam.get("certifying_body"))
        searchable_text = " ".join([exam_name, exam_code, provider, exam_id])

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
        elif all(word in searchable_text for word in words):
            score = 30

        if score > 0:
            matches.append((score, _clean_exam(exam)))

    matches.sort(key=lambda item: (-item[0], _normalize(item[1].get("exam_name"))))
    return [exam for _, exam in matches]


def find_certification(identifier: str, include_retired: bool = True) -> dict | None:
    value = _normalize(identifier)
    if not value:
        return None

    exams = load_certifications()
    if not include_retired:
        exams = [e for e in exams if not _is_retired(e)]

    for exam in exams:
        if value == _normalize(exam.get("exam_id")):
            return _clean_exam(exam)

    code_matches = [e for e in exams if value == _normalize(e.get("exam_code"))]
    if len(code_matches) == 1:
        return _clean_exam(code_matches[0])

    name_matches = [e for e in exams if value == _normalize(e.get("exam_name"))]
    if len(name_matches) == 1:
        return _clean_exam(name_matches[0])

    return None


def get_certification_blueprint(identifier: str) -> dict | None:
    exam = find_certification(identifier)
    if exam is None:
        return None

    vendor_slug = exam.get("vendor_slug")
    exam_id = exam.get("exam_id")

    if not vendor_slug or not exam_id:
        return None

    blueprint_url = f"{BASE_DATA_URL}/{vendor_slug}/{exam_id}.json"
    return _get_json(blueprint_url)

# =========================================================
# Semantic Search
# =========================================================


def _domains_to_text(domains) -> str:
    if not domains:
        return ""

    names = []

    for domain in domains:

        if isinstance(domain, dict):
            name = (
                domain.get("name")
                or domain.get("domain_name")
                or domain.get("domain")
            )

            if name:
                names.append(str(name))

        else:
            names.append(str(domain))

    return ", ".join(names)


def _build_certification_text(exam: dict) -> str:
    return (
        f"Certification: {exam.get('exam_name') or ''}\n"
        f"Exam code: {exam.get('exam_code') or ''}\n"
        f"Provider: {exam.get('certifying_body') or ''}\n"
        f"Domains: {_domains_to_text(exam.get('domains'))}"
    )


def _embed_texts(texts: list[str]) -> np.ndarray:

    vectors = []

    for start in range(
        0,
        len(texts),
        EMBEDDING_BATCH_SIZE,
    ):

        batch = texts[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        response = embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )

        ordered = sorted(
            response.data,
            key=lambda item: item.index,
        )

        vectors.extend(
            item.embedding
            for item in ordered
        )

    matrix = np.asarray(
        vectors,
        dtype=np.float32,
    )

    norms = np.linalg.norm(
        matrix,
        axis=1,
        keepdims=True,
    )

    return matrix / np.clip(
        norms,
        1e-12,
        None,
    )


@lru_cache(maxsize=1)
def _load_semantic_index():

    certifications = get_all_certifications(
        include_retired=False
    )

    texts = [
        _build_certification_text(exam)
        for exam in certifications
    ]

    vectors = _embed_texts(texts)

    return certifications, vectors


def semantic_search_certifications(
    profile_text: str,
    top_k: int = TOP_K,
) -> list[dict]:

    if not profile_text.strip():
        return []

    certifications, vectors = (
        _load_semantic_index()
    )

    query_vector = _embed_texts(
        [profile_text]
    )[0]

    similarities = vectors @ query_vector

    k = min(
        top_k,
        len(certifications),
    )

    top_indices = np.argsort(
        similarities
    )[::-1][:k]

    results = []

    for index in top_indices:

        exam = dict(
            certifications[int(index)]
        )

        exam["_retrieval_score"] = float(
            similarities[int(index)]
        )

        results.append(exam)

    return results