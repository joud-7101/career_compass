from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.graph.state import CareerState


from backend.config import settings

llm = ChatOpenAI(
    model="gpt-5.4-mini",
    temperature=0,
    api_key=settings.openai_api_key
)
def freelance_agent(state: CareerState):

    prompt = f"""
You are the Freelance Agent for Career Compass.

USER PROFILE
------------
Skills: {state.get("skills", [])}
Experience: {state.get("experience", [])}
Interests: {state.get("interests", [])}

USER REQUEST
------------
{state.get("query", "")}

Find freelance opportunities that match the
user's actual abilities.

Analyze:
- Skill match
- Project requirements
- Difficulty
- Potential suitability
- Missing skills

Use freelance search tools when needed.

Return ranked opportunities with explanations.
"""

    response = llm.invoke(prompt)

    return {
        "freelance_analysis": response.content
    }