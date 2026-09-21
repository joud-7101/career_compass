from datetime import date
import json

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from backend.graph.state import CareerState
from backend.config import settings

from backend.tools.certification_search import (
    semantic_search_certifications,
    get_certification_blueprint,
)
from backend.tools.web_search import (
    search_certification_web,
)

from backend.schemas.career_response import (
    CertificationRecommendation,
)
from backend.schemas.profile import UserProfile


llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.openai_api_key,
)


# =========================================================
# Structured output for Stage 1
# =========================================================


# class SearchKeywords(BaseModel):
#     keywords: list[str] = Field(
#         description=(
#             "Short professional certification search keywords "
#             "derived from the user's profile."
#         )
#     )


#     exam_id: str
#     exam_name: str
#     exam_code: str | None = None
#     certifying_body: str
#     reason: str
#     priority: str


class CertificationRecommendationList(BaseModel):
    recommendations: list[CertificationRecommendation] = Field(
        min_length=20,
        max_length=20,
    )


# =========================================================
# Structured LLMs
# =========================================================

# The Pydantic serialization warning is suppressed process-wide
# in main.py via warnings.filterwarnings(). See that file for
# the full explanation of why this warning occurs.

# keyword_llm = llm.with_structured_output(SearchKeywords)

recommendation_llm = llm.with_structured_output(
    CertificationRecommendationList
)


# =========================================================
# Helper: Build Cert Atlas candidates
# =========================================================


def get_candidate_certifications(
    profile: UserProfile,
) -> list[dict]:

    education = [
        " ".join(
            filter(
                None,
                [
                    edu.degree,
                    edu.field_of_study,
                ],
            )
        )
        for edu in profile.education
    ]

    experience = [
        " ".join(
            filter(
                None,
                [
                    exp.title,
                    exp.description,
                    " ".join(exp.skills or []),
                ],
            )
        )
        for exp in profile.experience
    ]

    skills = [
        skill.name
        for skill in profile.skills
    ]

    profile_text = f"""
Professional Summary:
{profile.professional_summary or ""}

Education:
{" | ".join(education)}

Experience:
{" | ".join(experience)}

Skills:
{", ".join(skills)}
"""

    return semantic_search_certifications(
        profile_text,
        top_k=20,
    )


# =========================================================
# Stage 1: Recommend Certifications
# =========================================================


def recommend_certifications(state: CareerState) -> dict:

    profile = state.get("user_profile")

    if not profile:
        return {
            "certifications": [],
            "certification_analysis": (
                "No user profile was provided."
            ),
        }

    # -----------------------------------------------------
    # Extract fields from UserProfile
    # -----------------------------------------------------

    education = [
        {
            "institution": edu.institution,
            "degree": edu.degree,
            "field_of_study": edu.field_of_study,
        }
        for edu in profile.education
    ]

    experience = [
        {
            "title": exp.title,
            "company": exp.company,
            "description": exp.description,
            "skills": exp.skills,
        }
        for exp in profile.experience
    ]

    skills = [
        skill.name
        for skill in profile.skills
    ]

    # -----------------------------------------------------
    # Find certification candidates
    # -----------------------------------------------------

    candidates = get_candidate_certifications(
        profile
    )

    if not candidates:

        return {
            "certifications": [],
            "certification_analysis": (
                "No matching certifications were found "
                "in Cert Atlas for the current user profile."
            ),
        }

    # Only send fields needed by the LLM
    # -----------------------------------------------------
    # Only send fields needed by the LLM
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Recommendation prompt
    # -----------------------------------------------------

    # prompt = f"""
    # You are the Certification Agent for Career Compass.
    #
    # Your task is to select professional certifications
    # that are suitable for the user.
    #
    # USER PROFILE

    prompt = f"""
You are the Certification Agent for Career Compass.

Your task is to evaluate and rank the 20 professional
certifications retrieved as most relevant to the user.

You MUST return all 20 certifications.

USER PROFILE
------------

Education:
{education}

Experience:
{experience}

Skills:
{skills}

USER REQUEST
------------
{state.get("query", "")}

TOP 20 RELEVANT CERTIFICATION CANDIDATES FROM CERT ATLAS
--------------------------------------------------------
{candidate_text}

IMPORTANT RULES
---------------
- You are given exactly 20 certification candidates retrieved from Cert Atlas.
- Evaluate ALL 20 candidates.
- Return ALL 20 candidates in the final recommendations.
- Do not omit any candidate.
- Rank them from most suitable to least suitable for the user.
- Recommend only certifications listed above.
- Never invent a certification.
- Keep the exact exam_id from Cert Atlas.
- Keep the exact certification name from Cert Atlas.
- Keep the exact provider from Cert Atlas.
- Keep the exact exam code from Cert Atlas.
- Avoid duplicate certifications.
- Every one of the 20 candidate exam IDs must appear exactly once.

Consider:
- Education
- Experience
- Current skills
- Career direction
- Skill gaps

For every recommended certification provide:

- exam_id
- name
- provider
- exam_code
- priority
- match:
    - score from 0 to 100
    - matching_skills
    - missing_skills
    - explanation

Priority must be one of:
- high
- medium
- low
"""

    result = recommendation_llm.invoke(prompt)

    # -----------------------------------------------------
    # Keep ALL 20 Cert Atlas candidates
    # LLM is used only for evaluation/ranking information
    # -----------------------------------------------------

    llm_by_id = {
        str(item.exam_id).strip().lower(): item
        for item in result.recommendations
        if item.exam_id
    }

    recommendations = []

    for exam in candidates:

        exam_id = exam.get("exam_id")

        if not exam_id:
            continue

        llm_result = llm_by_id.get(
            str(exam_id).strip().lower()
        )

        if llm_result:

            recommendation = llm_result.model_copy(
                update={
                    "exam_id": exam_id,
                    "name": exam.get("exam_name"),
                    "provider": exam.get("certifying_body"),
                    "exam_code": exam.get("exam_code"),
                    "url": exam.get("source_url"),
                }
            )

        else:

            # If the LLM failed to return this candidate,
            # do NOT delete it.
            # It was already selected by semantic retrieval
            # as one of the user's Top 20 matches.

            recommendation = CertificationRecommendation(
                exam_id=exam_id,
                name=exam.get("exam_name") or "Certification",
                provider=exam.get("certifying_body") or "Unknown",
                exam_code=exam.get("exam_code"),
                url=exam.get("source_url"),
                priority="medium",
                match={
                    "score": None,
                    "matching_skills": [],
                    "missing_skills": [],
                    "explanation": (
                        "Selected as one of the top certifications "
                        "matched to your profile."
                    ),
                },
            )

        recommendations.append(
            recommendation
        )

    # -----------------------------------------------------
    # Sort evaluated results first
    # -----------------------------------------------------

    recommendations.sort(
        key=lambda item: (
            item.match.score
            if item.match.score is not None
            else 0
        ),
        reverse=True,
    )

    # Safety: return exactly the Top 20
    recommendations = recommendations[:20]

    print(
        f"[DEBUG] Certification Agent returning "
        f"{len(recommendations)} recommendations"
    )

    return {
        "certifications": recommendations,
    }

    # -----------------------------------------------------
    # Validate LLM recommendations against Cert Atlas
    # -----------------------------------------------------

    candidate_by_id = {
        exam["exam_id"]: exam
        for exam in candidates
        if exam.get("exam_id")
    }

    recommendations = []
    seen = set()

    for recommendation in result.recommendations:

        exam_id = recommendation.exam_id

        # Must actually exist in the retrieved Cert Atlas results
        if exam_id not in candidate_by_id:
            continue

        # Prevent duplicates
        if exam_id in seen:
            continue

        exam = candidate_by_id[
            exam_id
        ]

        recommendation = recommendation.model_copy(
            update={
                "exam_id": exam_id,
                "name": exam.get(
                    "exam_name"
                ),
                "provider": exam.get(
                    "certifying_body"
                ),
                "exam_code": exam.get(
                    "exam_code"
                ),
                "url": exam.get(
                    "source_url"
                ),
            }
        )

        recommendations.append(
            recommendation
        )

        seen.add(
            exam_id
        )

    # -----------------------------------------------------
    # Highest match score first
    # -----------------------------------------------------

    recommendations.sort(
        key=lambda item: (
            item.match.score
            if item.match.score is not None
            else 0
        ),
        reverse=True,
    )

    return {
        "certifications": recommendations,
    }

    # recommendations = [
    #     recommendation.model_dump()
    #     for recommendation
    #     in result.recommendations
    # ]

    # keeping them as pydantic models

    # recommendations = result.recommendations


# commented it because i've changed the structer


# =========================================================
# Stage 2: Selected Certification
# =========================================================


def prepare_selected_certification(
    state: CareerState,
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
    state: CareerState,
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