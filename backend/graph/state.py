from typing import Annotated
import operator

from typing_extensions import TypedDict


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
    # Certification flow
    # -------------------------

    certification_recommendations: list[dict]

    selected_certification: str
    current_level: Literal[
        "Beginner",
        "Intermediate",
        "Advanced"
    ]
    exam_date: str
    
    # -------------------------
    # Agent outputs
    # -------------------------

    job_analysis: str
    certification_analysis: str
    freelance_analysis: str

    # -------------------------
    # Final output
    # -------------------------

    final_response: str