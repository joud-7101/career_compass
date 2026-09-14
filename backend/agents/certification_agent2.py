from datetime import date
import json

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from backend.graph.state import CareerState
from backend.config import settings

from backend.tools.certification_search import (
    search_certifications,
    get_certification_blueprint,
)

from backend.tools.web_search import (
    search_certification_web,
)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.openai_api_key,
)


# =========================================================
# Structured output for Stage 1
# =========================================================

class SearchKeywords(BaseModel):
    keywords: list[str] = Field(
        description=(
            "Short professional certification search keywords "
            "derived from the user's profile."
        )
    )

class CertificationRecommendation(BaseModel):
    exam_id: str
    exam_name: str
    exam_code: str | None = None
    certifying_body: str
    reason: str
    priority: str

class CertificationRecommendationList(BaseModel):
    recommendations: list[CertificationRecommendation]


# =========================================================
# Structured LLMs
# =========================================================

keyword_llm = llm.with_structured_output(
    SearchKeywords
)

recommendation_llm = llm.with_structured_output(
    CertificationRecommendationList
)


# =========================================================
# Helper: Build Cert Atlas candidates
# =========================================================

def get_candidate_certifications(
    profile: dict
) -> list[dict]:
    """
    Generate search keywords from the user profile,
    then search Cert Atlas for matching certifications.
    """

    keyword_prompt = f"""
You are helping search a professional certification database.

USER PROFILE
------------
Education:
{profile.get("education", "")}

Experience:
{profile.get("experience", [])}

Skills:
{profile.get("skills", [])}

Interests:
{profile.get("interests", [])}

Create short search keywords that can be used to find
relevant professional certifications.

Examples of good keywords:
- AWS
- Azure
- Power BI
- Data
- Cloud
- Security
- Python
- Project Management

Rules:
- Return professional or technical search keywords only.
- Do not return certification names.
- Do not invent certifications.
- Keywords should be based only on the user's profile.
"""

    keyword_result = keyword_llm.invoke(
        keyword_prompt
    )

    candidates = {}

    for keyword in keyword_result.keywords:

        results = search_certifications(
            keyword
        )

        for exam in results:

            exam_id = exam.get("exam_id")

            if exam_id:
                candidates[exam_id] = exam

    return list(
        candidates.values()
    )


# =========================================================
# Stage 1: Recommend Certifications
# =========================================================

def recommend_certifications(
    state: CareerState
) -> dict:

    profile = state.get(
        "user_profile",
        {}
    )

    candidates = get_candidate_certifications(
        profile
    )

    if not candidates:

        return {
            "certification_recommendations": [],
            "certification_analysis": (
                "No matching certifications were found "
                "in Cert Atlas for the current user profile."
            ),
        }

    # Only send fields needed by the LLM
    candidate_text = "\n".join(
        [
            (
                f"Exam ID: {exam.get('exam_id')}\n"
                f"Name: {exam.get('exam_name')}\n"
                f"Code: {exam.get('exam_code')}\n"
                f"Provider: {exam.get('certifying_body')}\n"
            )
            for exam in candidates
        ]
    )

    prompt = f"""
You are the Certification Agent for Career Compass.

Your task is to select professional certifications
that are suitable for the user.

USER PROFILE
------------
Education:
{profile.get("education", "")}

Experience:
{profile.get("experience", [])}

Skills:
{profile.get("skills", [])}

Interests:
{profile.get("interests", [])}

USER REQUEST
------------
{state.get("query", "")}

CERTIFICATIONS FOUND IN CERT ATLAS
----------------------------------
{candidate_text}

IMPORTANT RULES
---------------
- Recommend only certifications listed above.
- Never invent a certification.
- Keep the exact exam_id from Cert Atlas.
- Recommend every certification that is meaningfully
  relevant to the user's profile.
- Do not force a fixed number of recommendations.
- Exclude certifications that are clearly unrelated.
- Avoid duplicate certifications.
- Consider:
    - Education
    - Experience
    - Current skills
    - Interests
    - Career direction
    - Skill gaps

For every recommended certification provide:
- exam_id
- exam_name
- exam_code
- certifying_body
- reason
- priority

Priority must be:
- High
- Medium
- Low
"""

    result = recommendation_llm.invoke(
        prompt
    )

    recommendations = [
        recommendation.model_dump()
        for recommendation
        in result.recommendations
    ]

    analysis = "\n\n".join(
        [
            (
                f"{index + 1}. "
                f"{item.exam_name}"
                f" ({item.exam_code or 'No exam code'})\n"
                f"Provider: {item.certifying_body}\n"
                f"Reason: {item.reason}\n"
                f"Priority: {item.priority}"
            )
            for index, item
            in enumerate(
                result.recommendations
            )
        ]
    )

    return {
        "certification_recommendations":
            recommendations,

        "certification_analysis":
            analysis,
    }


# =========================================================
# Stage 2: Selected Certification
# =========================================================

def prepare_selected_certification(
    state: CareerState
) -> dict:

    selected_certification = state.get(
        "selected_certification"
    )

    current_level = state.get(
        "current_level"
    )

    exam_date_text = state.get(
        "exam_date"
    )

    # -----------------------------------------
    # Validate inputs
    # -----------------------------------------

    if not selected_certification:
        return {
            "certification_analysis":
                "No certification was selected."
        }

    if not current_level:
        return {
            "certification_analysis":
                "Current level is required."
        }

    if not exam_date_text:
        return {
            "certification_analysis":
                "Exam date is required."
        }

    # -----------------------------------------
    # Validate exam date
    # -----------------------------------------

    try:
        exam_date = date.fromisoformat(
            exam_date_text
        )

    except ValueError:
        return {
            "certification_analysis": (
                "Invalid exam date. "
                "Use YYYY-MM-DD format."
            )
        }

    today = date.today()

    days_remaining = (
        exam_date - today
    ).days

    if days_remaining < 0:
        return {
            "certification_analysis":
                "Exam date cannot be in the past."
        }

    # -----------------------------------------
    # Cert Atlas
    # -----------------------------------------

    blueprint = get_certification_blueprint(
        selected_certification
    )

    if blueprint is None:
        return {
            "certification_analysis": (
                "The selected certification "
                "could not be found in Cert Atlas."
            )
        }

    exam_name = blueprint.get(
        "exam_name"
    )

    exam_code = blueprint.get(
        "exam_code"
    )

    certifying_body = blueprint.get(
        "certifying_body"
    )

    # -----------------------------------------
    # Official Web Search
    # -----------------------------------------

    web_data = search_certification_web(
        exam_name=exam_name,
        exam_code=exam_code,
        certifying_body=certifying_body,
    )

    # -----------------------------------------
    # Generate final answer
    # -----------------------------------------

    prompt = f"""
You are the Certification Agent for Career Compass.

The user has already selected a certification.

USER INPUT
----------
Selected certification:
{exam_name}

Current level:
{current_level}

Exam date:
{exam_date_text}

Days remaining:
{days_remaining}


CERT ATLAS DATA
---------------
{json.dumps(
    blueprint,
    indent=2,
    ensure_ascii=False
)}


CURRENT OFFICIAL WEB DATA
-------------------------
{json.dumps(
    web_data,
    indent=2,
    ensure_ascii=False
)}


YOUR TASK
---------

Create:

1. Exam Information
2. Personalized Study Plan


EXAM INFORMATION MUST INCLUDE
-----------------------------
- Certification name
- Exam code
- Certifying body
- Exam domains with weights only
- Skills covered, only if explicitly available
- Number of questions
- Exam duration
- Exam format / question types
- Official practice exam availability


PERSONALIZED STUDY PLAN
-----------------------
Create the plan using:

- Current level
- Days remaining
- Exam domain weights

The study plan should include:

1. Study Priorities
2. Weekly Plan
3. Exam Preparation


STRICT RULES
------------
- Use only the Cert Atlas data and official Web Search data provided.
- Never invent exam facts.
- Never invent domain names or weights.
- Never invent skills.
- Prefer current official web information when it clearly updates
  older Cert Atlas information.
- Use Cert Atlas when the official web result does not provide
  the information.
- If information is unavailable from both sources, write:
  "Not available in the available sources."
- Do not include domain objectives.
- Show domain NAME and WEIGHT only.
- The study plan may recommend how to divide study time,
  but it must be based on the provided domain weights.
- Keep the response clear and practical.
"""

    response = llm.invoke(
        prompt
    )

    return {
        "certification_analysis":
            response.content
    }

# =========================================================
# Main Certification Agent
# =========================================================

def certification_agent(
    state: CareerState
):

    selected_certification = state.get(
        "selected_certification"
    )

    # Stage 1
    if not selected_certification:
        return recommend_certifications(
            state
        )

    # Stage 2
    return prepare_selected_certification(
        state
    )
