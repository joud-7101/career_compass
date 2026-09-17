from fastapi import FastAPI, Depends
from sqlmodel import Session

from backend.routers.auth import router as auth_router
from backend.routers.portfolio import router as portfolio_router
from backend.routers.career import router as career_router

from backend.database.database import (
    create_db_and_tables,
    get_session
)

from backend.database.crud import (
    create_user,
    get_user
)

from backend.schemas.career import (
    CareerRequest,
    UserProfileRequest
)

from backend.schemas.career_response import (
    CareerResponse
)

from backend.graph.graph import career_graph
from backend.schemas.profile import (
    UserProfile,
    PersonalInformation,
    Education,
    Experience,
    Skill,
)


app = FastAPI(
    title="Career Compass API",
    version="0.1.0"
)

app.include_router(auth_router)
app.include_router(portfolio_router)
app.include_router(career_router)


@app.on_event("startup")
def startup():

    create_db_and_tables()


@app.get("/")
def root():

    return {
        "message": "Career Compass API is running"
    }


@app.post("/api/users")
def create_user_profile(
    request: UserProfileRequest,
    session: Session = Depends(get_session)
):

    user = create_user(
        session=session,
        user_id=request.user_id,
        name=request.name,
        education=request.education,
        location=request.location,
        skills=",".join(request.skills),
        experience=",".join(request.experience),
        interests=",".join(request.interests)
    )

    return {
        "message": "User created successfully",
        "user_id": user.id
    }


@app.post(
    "/api/career",
    response_model=CareerResponse
)
def career_assistant(
    request: CareerRequest,
    session: Session = Depends(get_session)
):

    user = get_user(
        session=session,
        user_id=request.user_id
    )

    if not user:
        return {
            "error": "User not found"
        }

    user_profile = UserProfile(
    personal_information=PersonalInformation(
        name=user.name,
        location=user.location
    ),

    education=[
        Education(
            institution="University of Jeddah",
            degree="Bachelor's",
            field_of_study=user.education
        )
    ] if user.education else [],

    experience=[
        Experience(
            title=exp.strip()
        )
        for exp in user.experience.split(",")
        if exp.strip()
    ] if user.experience else [],

    skills=[
        Skill(
            name=skill.strip()
        )
        for skill in user.skills.split(",")
        if skill.strip()
    ] if user.skills else [],

    languages=[],
    certifications=[],
    projects=[],
    professional_links=[],
    achievements=[],
    volunteering=[]
    )

    initial_state = {
        "user_id": request.user_id,
        "query": request.query,
        "user_profile": user_profile
    }

    result = career_graph.invoke(
        initial_state
    )

    return CareerResponse(
        request_id=result.get("request_id"),

        final_response=result.get(
            "final_response",
            ""
        ),

        jobs=result.get(
            "jobs",
            []
        ),

        certifications=result.get(
            "certifications",
            []
        ),

        freelance_projects=result.get(
            "freelance_projects",
            []
        ),

        issues=result.get(
            "issues",
            []
        )
    )