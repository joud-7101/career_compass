from typing import  Annotated,Literal
from typing_extensions import TypedDict
from operator import add

from backend.schemas.career_response import (
    JobOpportunity,
    CertificationRecommendation,
    FreelanceProject,
    AgentIssue,
)

from typing import TypedDict, Literal


AgentName = Literal[
    "job",
    "certification",
    "freelance"
]

# User information shared between agents
class UserProfile(TypedDict, total=False):
    name: str
    education: str
    experience: list[str]
    skills: list[str]
    interests: list[str]
    location: str


class CareerState(TypedDict, total=False):

    # -------------------------
    # User/session
    # -------------------------

    user_id: str
    query: str

    # -------------------------
    # Shared user information
    # -------------------------

    user_profile: UserProfile

    # -------------------------
    # Orchestrator
    # -------------------------

    requested_agents: list[AgentName]

    # -------------------------
    # Agent outputs
    # -------------------------

    selected_certification: str

    certification_recommendations: list[dict]

    
    current_level: Literal[
        "Beginner",
        "Intermediate",
        "Advanced"
    ]
    exam_date: str
    
    # -------------------------
    # Structured Agent outputs
    # -------------------------

    jobs: list[JobOpportunity]
    certifications: list[CertificationRecommendation]
    freelance_projects: list[FreelanceProject]
    # -----------------------------------------------------
    # Errors / warnings
    #
    # `add` allows multiple parallel agents to contribute
    # issues without overwriting each other.
    # -----------------------------------------------------

    issues: Annotated[
        list[AgentIssue],
        add,
    ]
    # -------------------------
    # Final output
    # -------------------------
    final_response: str
#new archture
#     final_response: str

    