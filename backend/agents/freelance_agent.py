from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.graph.state import CareerState
from backend.tools.freelance.dataset_tool import analyze_historical_market
from backend.tools.freelance.freelancer_api import (
    search_freelancer_projects as search_freelancer_api,
)
from backend.tools.freelance.freelance_search import search_freelance_projects
from pydantic import BaseModel, Field

from backend.schemas.career_response import FreelanceProject


class FreelancerAgentOutput(BaseModel):#for the structured output of the freelance agent
    freelance_projects: list[FreelanceProject] = Field(
        default_factory=list
    )


llm = ChatOpenAI(
    model="gpt-5.4-mini",
    temperature=0,
    api_key=settings.openai_api_key,
)
# Pydantic serialization warning (Expected `none` on AIMessage.parsed)
# is suppressed process-wide in main.py — see that file for details.
structured_llm = llm.with_structured_output(
    FreelancerAgentOutput
)

def _as_string_list(value: object) -> list[str]:
    """Return cleaned profile values that are expected to be lists of strings."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _run_tool(tool, payload: dict, source: str):
    """Return a source-specific error without stopping the rest of the agent."""
    try:
        return tool.invoke(payload)
    except Exception as exc:
        return {"error": f"{source} unavailable: {exc}"}


def freelance_agent(state: CareerState) -> dict:
    """Find current freelance opportunities plus historical market context."""
    profile = state.get("user_profile")#changed the extraxcted profile to user_profile to match the CareerState schema
    skills = [skill.name for skill in profile.skills] if profile else []
    experience = [
    exp.title
    for exp in profile.experience
] if profile else []
    
    location = (
    profile.personal_information.location
    if profile
    else ""
)
    query = str(state.get("query", "") or "").strip()#check if i should change it or not 

    try:
        market_analysis = analyze_historical_market(skills=skills)
    except Exception as exc:
        market_analysis = {"error": f"Historical market data unavailable: {exc}"}

    # These imports are LangChain StructuredTools. Call their declared schemas
    # through .invoke(); the API tool takes skills, not query or limit.
    if skills:
        live_projects = _run_tool(
            search_freelancer_api,
            {"skills": skills},
            "Freelancer API",
        )
        web_opportunities = _run_tool(
            search_freelance_projects,
            {"skills": skills, "location": location},
            "Freelancer web search",
        )
    else:
        message = "No profile skills were supplied, so live project search was skipped."
        live_projects = {"error": message}
        web_opportunities = {"error": message}

    prompt = f"""
You are the Freelancer Agent for CareerCompass. Find and rank current freelance
opportunities that realistically match the user's abilities.

USER PROFILE
Skills: {skills}
Experience: {experience}

Location: {location or 'Information unavailable'}
Request: {query or 'Information unavailable'}

HISTORICAL MARKET ANALYSIS (background only; never current opportunities)
{market_analysis}

LIVE FREELANCER API RESULTS (eligible current opportunities)
{live_projects}

LIVE WEB SEARCH RESULTS (eligible current opportunities)
{web_opportunities}

Only recommend opportunities in the two LIVE result sets. Never invent URLs,
budgets, titles, clients, requirements, or ratings. If a detail is absent, say
"Information unavailable." Do not present historical dataset jobs as live.

For every recommended project provide:

- title
- source
- URL
- budget or rate
- match score from 0-100
- matching skills
- missing skills
- explanation of why it matches

Only recommend projects from the LIVE result sets.
Never invent URLs or project information.
"""

    response = structured_llm.invoke(prompt)
    return {
    "freelance_projects": response.freelance_projects
}
