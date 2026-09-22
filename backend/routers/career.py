"""
Dedicated per-page career endpoints.
Each endpoint calls the relevant agent directly using the user's stored profile.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlmodel import Session

from backend.database.database import get_session
from backend.database.crud import get_user, get_profile_review
from backend.security import decode_access_token

from backend.agents.job_agent import job_agent
from backend.agents.freelance_agent import freelance_agent
from backend.agents.certification_agent2 import (
    recommend_certifications,
    prepare_selected_certification,
)
# Import the proposal agent functions.
# generate_proposal() creates the first draft; chat_with_proposal()
# handles follow-up refinement messages from the user.
from backend.agents.proposal_agent import generate_proposal, chat_with_proposal
from backend.schemas.career_response import CVTailoringResponse

router = APIRouter(
    prefix="/api/career",
    tags=["Career Agents"],
)


# --------------------------------------------------
# Auth helper
# --------------------------------------------------

def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --------------------------------------------------
# Helper: load & convert profile from DB to agent format
# --------------------------------------------------

from backend.schemas.profile import UserProfile

def load_agent_profile(
    user_id: int,
    session: Session,
) -> UserProfile:
    """
    Load the user's approved ProfileReview JSON and convert it to
    the UserProfile Pydantic object that the career agents expect.
    """
    review = get_profile_review(session, user_id)

    if not review or not review.profile_data:
        return UserProfile()

    try:
        # The agents now expect the full UserProfile object
        return UserProfile.model_validate_json(review.profile_data)
    except Exception:
        return UserProfile()


# ==================================================
# JOBS endpoint
# ==================================================

class JobsRequest(BaseModel):
    query: str = "Find jobs that match my profile"


@router.post("/jobs")
def get_job_recommendations(
    request: JobsRequest = JobsRequest(),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = load_agent_profile(user_id, session)

    state = {
        "user_id": str(user_id),
        "query": request.query,
        "user_profile": profile,
    }

    result = job_agent(state)

    return {
        "jobs": result.get("jobs", []),
        "analysis": result.get("job_analysis", ""),
    }


# ==================================================
# CV TAILORING endpoint
# ==================================================

class CVTailoringRequest(BaseModel):
    job_title: str
    job_description: str


@router.post("/jobs/tailor-cv")
def tailor_cv_for_job(
    request: CVTailoringRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    profile = load_agent_profile(user_id,session,)

    # CV tailoring assistant
    from openai import OpenAI
    client = OpenAI()
    tailoring_prompt = f"""
    You are a CV tailoring assistant.
    Analyze the user's existing profile against the target job.

    TARGET JOB:
    Title: {request.job_title}

    Description:
    {request.job_description}

    USER PROFILE:
    {json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2)}

    Your task:
    1. Estimate an ATS match score from 0 to 100.
    2. Suggest only realistic changes to the existing CV.
    3. Focus mainly on:
    - Professional title
    - Professional summary
    - Skills to emphasize
    - Experience/projects to emphasize
    4. Do NOT invent skills, experience, education, certifications, or achievements.
    5. Only recommend keywords that are supported by the user's existing profile.
    6. Never change factual personal information such as graduation status, degree, GPA, dates, employers, job titles, or certifications. Preserve the user's actual profile facts exactly.
    7. Keep suggestions concise and practical.

    Return ONLY valid JSON matching this structure:
    {{
        "ats_match": 0,
        "job_title": "{request.job_title}",
        "suggestions": [
            {{
                "category": "summary",
                "current": "...",
                "suggested": "...",
                "reason": "..."
            }}
        ],
        "keywords_to_emphasize": [],
        "missing_keywords": []
    }}
    """

    response = client.responses.create(
        model="gpt-5.6",
        input=tailoring_prompt,
    )

    result = json.loads(response.output_text)

    return CVTailoringResponse.model_validate(result)


# ==================================================
# FREELANCE endpoint
# ==================================================

class FreelanceRequest(BaseModel):
    query: str = "Find freelance projects that match my skills"


@router.post("/freelance")
def get_freelance_recommendations(
    request: FreelanceRequest = FreelanceRequest(),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = load_agent_profile(user_id, session)

    state = {
        "user_id": str(user_id),
        "query": request.query,
        "user_profile": profile,
    }

    result = freelance_agent(state)

    # Convert Pydantic models to dicts for consistent JSON serialization.
    # FastAPI can serialize Pydantic objects, but being explicit avoids
    # edge cases where nested models might not serialize as expected.
    raw_projects = result.get("freelance_projects", [])
    projects = [
        p.model_dump() if hasattr(p, "model_dump") else p
        for p in raw_projects
    ]

    print(f"\n[DEBUG] Freelance endpoint returning {len(projects)} projects")
    if projects:
        print(f"[DEBUG] First project keys: {list(projects[0].keys())}")

    return {
        "freelance_projects": projects,
        "analysis": result.get("freelance_analysis", ""),
    }


# ==================================================
# PROPOSAL endpoint — generate the first draft
# ==================================================

class ProposalRequest(BaseModel):
    """
    The frontend sends the project details it already has from the
    freelance cards — the agent then uses these plus the user profile
    to write a personalized proposal.
    """
    project_title: str
    project_description: str
    budget_or_rate: str | None = None
    matching_skills: list[str] = []  # skills user has that match the project
    missing_skills: list[str] = []   # skills the project needs but user lacks


@router.post("/freelance/proposal")
def get_proposal(
    request: ProposalRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """
    Generate a personalized first-draft proposal for a specific project.

    Called when the user clicks "View Proposal" on a freelance card.
    Only runs once per project (the frontend caches the result in
    session state), so latency here is acceptable.
    """
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Load the user's full profile — this is the same profile object
    # used by all other agents. It contains skills, experience, projects.
    profile = load_agent_profile(user_id, session)

    # Call the proposal agent to generate the first draft.
    # This is a straightforward LLM call — no tools, no structured output.
    proposal_text = generate_proposal(
        profile=profile,
        project_title=request.project_title,
        project_description=request.project_description,
        budget_or_rate=request.budget_or_rate,
        matching_skills=request.matching_skills,
        missing_skills=request.missing_skills,
    )

    return {"proposal": proposal_text}


# ==================================================
# PROPOSAL CHAT endpoint — refine the proposal
# ==================================================

class ChatMessage(BaseModel):
    """A single message in the conversation history."""
    role: str   # "user" or "assistant"
    content: str


class ProposalChatRequest(BaseModel):
    """
    The frontend sends the full conversation history on every turn.
    This "stateless" design means the backend doesn't need to store
    any session state — all history lives in the Streamlit session_state.
    """
    project_title: str
    project_description: str
    # The complete conversation so far, including the first AI proposal.
    # Example: [{"role": "assistant", "content": "Dear..."},
    #           {"role": "user",      "content": "make it shorter"}]
    messages: list[ChatMessage]


@router.post("/freelance/proposal/chat")
def refine_proposal(
    request: ProposalChatRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """
    Continue the proposal refinement conversation.

    Called every time the user sends a follow-up message in the chat
    window (e.g. "make it shorter", "focus on my Python experience").
    The entire conversation history is sent each time so the LLM
    always has full context of what has been asked before.
    """
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = load_agent_profile(user_id, session)

    # Convert Pydantic message objects to plain dicts for the agent
    messages_as_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    reply = chat_with_proposal(
        profile=profile,
        project_title=request.project_title,
        project_description=request.project_description,
        messages=messages_as_dicts,
    )

    return {"reply": reply}


# ==================================================
# CERTIFICATIONS endpoint — Stage 1: Recommendations
# ==================================================

@router.post("/certifications")
def get_certification_recommendations(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = load_agent_profile(user_id, session)

    state = {
        "user_id": str(user_id),
        "query": "Recommend certifications based on my profile",
        "user_profile": profile,
    }

    result = recommend_certifications(state)

    return {
        "recommendations": result.get("certifications", []),
        "analysis": result.get("certification_analysis", ""),
    }


# ==================================================
# CERTIFICATIONS/STUDY-PLAN — Stage 2: Study plan
# ==================================================

class StudyPlanRequest(BaseModel):
    selected_certification: str
    current_level: str = "Intermediate"
    exam_date: str  # YYYY-MM-DD


@router.post("/certifications/study-plan")
def get_study_plan(
    request: StudyPlanRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = load_agent_profile(user_id, session)

    state = {
        "user_id": str(user_id),
        "query": f"Create a study plan for {request.selected_certification}",
        "user_profile": profile,
        "selected_certification": request.selected_certification,
        "current_level": request.current_level,
        "exam_date": request.exam_date,
    }

    result = prepare_selected_certification(state)

    return {
        "study_plan": result.get("certification_analysis", ""),
    }
