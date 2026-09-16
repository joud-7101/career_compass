from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from backend.graph.state import CareerState
from backend.config import settings


llm = ChatOpenAI(
    model="gpt-5.4-mini",
    temperature=0,
    api_key=settings.openai_api_key
)


class Certification(BaseModel):
    name: str
    relevance: str
    skills_gained: list[str] = Field(default_factory=list)
    priority: Literal["high", "medium", "low"]


class CertificationOutput(BaseModel):
    analysis: str = Field(
        description=(
            "The full written recommendation, covering "
            "recommended certifications, why each is relevant, "
            "skills gained, and priority, in prose form."
        )
    )
    certifications: list[Certification] = Field(default_factory=list)


structured_llm = llm.with_structured_output(CertificationOutput)


def certification_agent(state: CareerState):
    user_profile = state.get("user_profile", {})

    prompt = f"""
You are the Certification Agent for Career Compass.

USER PROFILE
------------
Education: {user_profile.get("education", "")}
Experience: {user_profile.get("experience", [])}
Skills: {user_profile.get("skills", [])}
Interests: {user_profile.get("interests", [])}

USER REQUEST
------------
{state.get("query", "")}

Your goal is to recommend certifications that
will provide meaningful career value.

Consider:
- Current skills
- Career interests
- Skill gaps
- Job market relevance
- Certification credibility

Use certification and web search tools when needed.

Return:
1. Recommended certifications
2. Why each is relevant
3. Skills gained
4. Priority
"""

    response = structured_llm.invoke(prompt)

    return {
        "certification_analysis": response.analysis,
        "certifications": [
            certification.model_dump()
            for certification in response.certifications
        ],
    } 