from typing import Literal
from typing_extensions import TypedDict

from backend.schemas.career import (
    JobOpportunity,
    CertificationRecommendation,
    FreelanceProject,
    AgentIssue,
)

from backend.schemas.profile import UserProfile


AgentName = Literal[
    "job",
    "certification",
    "freelance"
]



# # User information shared between agents

# class CareerState(TypedDict, total=False):

#     user_id: str
#     query: str

#     user_profile: UserProfile





class CareerState(TypedDict, total=False):

    # -------------------------
    # User / session
    # -------------------------

    user_id: str
    request_id: str
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
    # Certification inputs
    # -------------------------

    selected_certification: str

    certification_recommendations: list[dict]

    selected_certification: str
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
        # -------------------------
    # Errors / warnings
    # -------------------------




    issues: list[AgentIssue]

    # -------------------------
    # Final output
    # -------------------------
#new archture
#     final_response: str

#     Job Agent
#     ↓
# JobOpportunity objects
#     ↓
# CareerState.jobs
#     ↓
# CareerResponse.jobs
#     ↓
# Frontend directly displays cards

#For example, Streamlit can simply do:
# for job in response.jobs:
#     st.write(job.title)
#     st.write(job.company)
#     st.write(job.match.score)
#     st.write(job.match.matching_skills)