from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.graph.state import CareerState
from backend.config import settings


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.openai_api_key
)


# ---------------------------------------------------------
# Structured output for the orchestrator
# ---------------------------------------------------------

class RouteDecision(BaseModel):
    agents: list[
        Literal["job", "certification", "freelance"]
    ] = Field(
        description=(
            "The specialist agents required to answer the "
            "user's request."
        )
    )


router_llm = llm.with_structured_output(RouteDecision)


# ---------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------

def orchestrator(state: CareerState):

    query = state["query"]
    user_profile = state["user_profile"]

    system_prompt = """
You are the Orchestrator Agent for Career Compass.

Your job is NOT to answer the user's career question.

Your job is to decide which specialist agents should
work on the user's request.

Available specialist agents:

1. job
   - Finds and analyzes job opportunities
   - Matches jobs to the user's skills
   - Identifies job skill gaps

2. certification
   - Finds relevant certifications
   - Recommends certifications based on career goals
   - Identifies useful learning paths

3. freelance
   - Finds freelance opportunities
   - Matches projects to user skills
   - Identifies freelance skill gaps

Rules:

- Select only the agents that are actually necessary.
- You can select multiple agents.
- Do not select agents that are irrelevant.
- At least one agent must be selected.

Examples:

"Find software engineering jobs in Jeddah"
→ job

"What certifications should I get?"
→ certification

"Find freelance Python projects"
→ freelance

"Find me software engineering jobs and tell me
which certifications I should get"
→ job, certification

"Find jobs, certifications, and freelance opportunities"
→ job, certification, freelance
"""

    user_prompt = f"""
USER PROFILE:
{user_profile}

USER REQUEST:
{query}
"""

    decision = router_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    )

    return {
        "requested_agents": decision.agents
    }


# ---------------------------------------------------------
# LOAD USER PROFILE
# ---------------------------------------------------------

def load_user_profile(state: CareerState):

    # Database logic will go here.
    #
    # For the first version, we use the profile
    # that comes from the API request.

    return {
        "user_profile": state["user_profile"]
    }


# ---------------------------------------------------------
# FINAL SYNTHESIS
# ---------------------------------------------------------

def synthesize_results(state: CareerState):

    prompt = f"""
You are the final Career Compass advisor.

The specialist agents have analyzed the user's request.

USER PROFILE:
{state.get("user_profile", {})}

USER REQUEST:
{state.get("query", "")}

JOB AGENT:
{state.get("job_analysis", "")}

CERTIFICATION AGENT:
{state.get("certification_analysis", "")}

FREELANCE AGENT:
{state.get("freelance_analysis", "")}

Combine the useful findings into one clear,
personalized answer.

Do not mention internal agents or orchestration.

Give practical recommendations and explain
why they are relevant to the user.
"""

    response = llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return {
        "final_response": response.content
    }