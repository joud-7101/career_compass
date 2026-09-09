from langchain_openai import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.graph.state import CareerState


from backend.config import settings

llm = ChatOpenAI(
    model="gpt-5.4-mini",
    temperature=0,
    api_key=settings.openai_api_key
)





def certification_agent(state: CareerState):

    prompt = f"""
You are the Certification Agent for Career Compass.

USER PROFILE
------------
Education: {state.get("education", "")}
Experience: {state.get("experience", [])}
Skills: {state.get("skills", [])}
Interests: {state.get("interests", [])}

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