from fastapi import FastAPI, Depends
from sqlmodel import Session

from backend.database.database import (
    create_db_and_tables,
    get_session
)

from backend.database.crud import create_user

from backend.schemas.career import (
    CareerRequest,
    UserProfileRequest
)

from backend.graph.graph import career_graph


app = FastAPI(
    title="Career Compass API",
    version="0.1.0"
)


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


@app.post("/api/career")
def career_assistant(
    request: CareerRequest
):

    initial_state = {
        "user_id": request.user_id,
        "query": request.query
    }

    result = graph.invoke(
        initial_state
    )

    return {
        "response": result.get(
            "final_response",
            ""
        ),
        "jobs": result.get(
            "jobs",
            []
        ),
        "certifications": result.get(
            "certifications",
            []
        ),
        "freelance_projects": result.get(
            "freelance_projects",
            []
        )
    }