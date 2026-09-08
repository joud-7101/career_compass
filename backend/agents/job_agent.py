from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.graph.state import CareerState


from backend.config import settings

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.openai_api_key
)


def job_agent(state: CareerState):

    prompt = f"""
You are the Job Agent in Career Compass.

Your job is to help the user find and evaluate
job opportunities.

USER PROFILE
------------
Name: {state.get("name", "")}
Education: {state.get("education", "")}
Experience: {state.get("experience", [])}
Skills: {state.get("skills", [])}
Interests: {state.get("interests", [])}
Location: {state.get("location", "")}

USER REQUEST
------------
{state.get("query", "")}

Analyze the user's request and determine what
job-related information is needed.

You have access to job search and career tools.
Use them when necessary.

Return:
1. Suitable job opportunities
2. Why each job matches the user
3. Important skill gaps
4. Recommended next steps
"""

    response = llm.invoke([
        HumanMessage(content=prompt)
    ])

    return {
        "job_analysis": response.content,
        "messages": [
            response
        ]
    }