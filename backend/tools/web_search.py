import json

from openai import OpenAI

from backend.config import settings


client = OpenAI(
    api_key=settings.openai_api_key
)

WEB_SEARCH_MODEL = "gpt-5.6"


def web_search(query: str) -> str:
    """
    General web search tool.
    """

    response = client.responses.create(
        model=WEB_SEARCH_MODEL,
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=query
    )

    return response.output_text


CERTIFICATION_WEB_SCHEMA = {
    "type": "object",
    "properties": {
        "exam_name": {
            "type": ["string", "null"]
        },
        "exam_code": {
            "type": ["string", "null"]
        },
        "certifying_body": {
            "type": ["string", "null"]
        },
        "status": {
            "type": ["string", "null"]
        },
        "total_questions": {
            "type": ["integer", "null"]
        },
        "duration_minutes": {
            "type": ["integer", "null"]
        },
        "question_types": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "exam_format": {
            "type": ["string", "null"]
        },
        "passing_score": {
            "type": ["number", "null"]
        },
        "prerequisites": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "recommended_experience": {
            "type": ["string", "null"]
        },
        "skills_covered": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "domains": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "weight_percent": {
                        "type": ["number", "null"]
                    }
                },
                "required": [
                    "name",
                    "weight_percent"
                ],
                "additionalProperties": False
            }
        },
        "practice_exam_available": {
            "type": ["boolean", "null"]
        },
        "official_resources": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "official_sources": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "exam_name",
        "exam_code",
        "certifying_body",
        "status",
        "total_questions",
        "duration_minutes",
        "question_types",
        "exam_format",
        "passing_score",
        "prerequisites",
        "recommended_experience",
        "skills_covered",
        "domains",
        "practice_exam_available",
        "official_resources",
        "official_sources"
    ],
    "additionalProperties": False
}


def search_certification_web(
    exam_name: str,
    exam_code: str | None,
    certifying_body: str | None
) -> dict:
    """
    Search official web sources for current
    certification information.
    """

    prompt = f"""
Search the web for current official information
about this certification.

Certification:
{exam_name}

Exam code:
{exam_code or "Not available"}

Certifying body:
{certifying_body or "Not available"}

Rules:
- Use only official sources from the certifying body.
- Do not use blogs, Reddit, QuizForge, or unofficial websites.
- Do not guess missing information.
- Return null or an empty list when information cannot be verified.
- Return current information only.

Find:
- Exam status
- Exam name
- Exam code
- Certifying body
- Number of questions
- Duration
- Question types
- Exam format
- Passing score
- Prerequisites
- Recommended experience
- Skills covered
- Domains and weights
- Official practice exam availability
- Official study resources
- Official source URLs
"""

    response = client.responses.create(
        model=WEB_SEARCH_MODEL,
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "certification_web_information",
                "strict": True,
                "schema": CERTIFICATION_WEB_SCHEMA
            }
        }
    )

    if not response.output_text:
        return {}

    try:
        return json.loads(
            response.output_text
        )

    except json.JSONDecodeError:
        return {}
