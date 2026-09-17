from fastapi import FastAPI, Depends
from sqlmodel import Session

from backend.routers.auth import router as auth_router
from backend.routers.portfolio import router as portfolio_router
from backend.routers.career import router as career_router

from backend.database.database import (
    create_db_and_tables,
    get_session,
)

from backend.database.crud import (
    get_user,
    get_user_profile,
)

from backend.schemas.career import CareerRequest
from backend.graph.graph import career_graph


app = FastAPI(
    title="Career Compass API",
    version="0.1.0",
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


@app.post("/api/career")
def career_assistant(
    request: CareerRequest,
    session: Session = Depends(get_session),
):
    user = get_user(
        session=session,
        user_id=request.user_id,
    )

    if not user:
        return {
            "error": "User not found"
        }

    profile = get_user_profile(
        session=session,
        user_id=request.user_id,
    )

    user_profile = {
        "name": profile.name if profile else "",
        "education": profile.education if profile else "",
        "experience": [],
        "skills": [],
        "interests": profile.interests if profile else "",
        "location": profile.location if profile else "",
    }

    initial_state = {
        "user_id": request.user_id,
        "query": request.query,
        "user_profile": user_profile,
    }

    result = career_graph.invoke(initial_state)
    result = career_graph.invoke(initial_state)
    print("\n================ GRAPH RESULT ================")
    print(result)
    print("================================================\n")

    return {
    "response": result.get("final_response", ""),
    "jobs": result.get("jobs", []),
    "certifications": result.get("certifications", []),
    "freelance_projects": result.get("freelance_projects", []),
    }

    # return {
    #     "response": result.get("final_response", ""),
    #     "jobs": result.get("jobs", []),
    #     "certifications": result.get("certifications", []),
    #     "freelance_projects": result.get("freelance_projects", []),
    # }