from langchain_openai import ChatOpenAI

from backend.graph.state import CareerState
from backend.config import settings


llm = ChatOpenAI(
    model="gpt-5.4-mini", 
    temperature=0,
    api_key=settings.openai_api_key
)


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

    response = llm.invoke(prompt)

    return {
        "certification_analysis": response.content

    }
