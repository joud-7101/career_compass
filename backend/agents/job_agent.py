from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from backend.graph.state import CareerState
from backend.config import settings
from backend.tools.job_search import search_jobs
from backend.tools.onet import get_occupation_information
from backend.tools.resume import get_required_skills
from backend.schemas.career import (
    JobOpportunity,
    MatchDetails,
)
from pydantic import BaseModel, Field

#for the structured output of the job agent
class JobAgentOutput(BaseModel):
    jobs: list[JobOpportunity] = Field(default_factory=list)

llm = ChatOpenAI(
    model="gpt-5.4-mini",
    temperature=0,
    api_key=settings.openai_api_key
)

llm_with_tools = llm.bind_tools([
    search_jobs,
    get_occupation_information,
    get_required_skills
])


def job_agent(state: CareerState):
    user_profile = state.get("user_profile", {})
    query = state.get("query", "")

    prompt = f"""
You are the Job Agent in Career Compass.

Your job is to find and evaluate real job opportunities
that match the user's request and profile.

USER PROFILE
------------
Name: {user_profile.get("name", "")}
Education: {user_profile.get("education", "")}
Experience: {user_profile.get("experience", [])}
Skills: {user_profile.get("skills", [])}
Interests: {user_profile.get("interests", [])}
Location: {user_profile.get("location", "")}

USER REQUEST
------------
{query}

INSTRUCTIONS
------------
1. Identify the target job role and relevant context from the user's request.
   The context may include technologies, specialization,
   industry, responsibilities, or career interests.

2. Use the job search tool to find real job listings.

3. Use a concise job-related search term, such as
   "Software Engineer", "AI Engineer", or "Data Scientist".

4. Use the O*NET tool to retrieve occupation,
   essential skills, and technology information
   for the identified job role.

   When calling the O*NET tool:
   - job_title must be the identified target role.
   - user_skills must come from the user's profile.
   - context must contain relevant terms extracted
     from the user's request, such as technologies,
     specialization, industry, responsibilities,
     or career interests.

   Do not use the user's skills as the job title.

5. Use the Resume tool to retrieve the
   required skills associated with the identified
   job title.

6. Use the user's location when available.

7. Do not search using only the user's skills.

8. Use Resume information only when the matched title
   is clearly relevant to the requested role.

9. Prefer the O*NET occupation whose title most closely
   matches the requested role. Treat context and user
   skills as supporting evidence, not as replacements
   for the requested job title.

10. Analyze the job, O*NET, and Resume results against
   the user's profile, including skill matches and gaps.

11. Use O*NET and Resume information to support
    your recommendations.

Return:
1. Suitable job opportunities
2. Why each job matches the user
3. Important skill gaps
4. Recommended next steps
5. Use O*NET and Resume information to support
   the skill-gap analysis and recommendations."""

    messages = [HumanMessage(content=prompt)]
    
    response = llm_with_tools.invoke(messages)
    structured_llm = llm.with_structured_output(JobAgentOutput)#for structured output of the job agent

    if response.tool_calls:
        messages.append(response)

        for tool_call in response.tool_calls:

            if tool_call["name"] == "search_jobs":
                tool_result = search_jobs.invoke(
                    tool_call["args"]
                )

            elif tool_call["name"] == "get_occupation_information":
                tool_result = get_occupation_information.invoke(
                    tool_call["args"]
                )

            elif tool_call["name"] == "get_required_skills":
                tool_result = get_required_skills.invoke(
                    tool_call["args"]
                )

            else:
                continue

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
            )

        final_response = llm.invoke(messages)

    else:
        final_response = response

    return {
        "job_analysis": final_response.content
    }