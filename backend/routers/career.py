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

    return {
        "freelance_projects": result.get("freelance_projects", []),
        "analysis": result.get("freelance_analysis", ""),
    }


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
