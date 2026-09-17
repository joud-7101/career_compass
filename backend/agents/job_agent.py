from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from backend.graph.state import CareerState
from backend.config import settings
from backend.tools.job_search import search_jobs
from backend.tools.onet import get_occupation_information
#from backend.tools.resume import get_required_skills
from backend.schemas.career_response import (
    JobOpportunity,
    MatchDetails,
)
from pydantic import BaseModel, Field

class JobAgentOutput(BaseModel):
    jobs: list[JobOpportunity] = Field(default_factory=list)
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.openai_api_key
)

llm_with_tools = llm.bind_tools([search_jobs])


def job_agent(state: CareerState):

    user_profile = state.get("user_profile", {})

    prompt = f"""
You are the Job Agent in Career Compass.

Your job is to help the user find and evaluate
job opportunities.

USER PROFILE
------------
Name: {user_profile.personal_information.name}
Education: {user_profile.education}
Experience: {user_profile.experience}
Skills: {user_profile.skills}
Location: {user_profile.personal_information.location}

USER REQUEST
------------
{state.get("query", "")}

Use the available job search tool when job opportunities
are needed.

After receiving the search results, analyze them and return:

1. Suitable job opportunities
2. Why each job matches the user
3. Important skill gaps
4. Recommended next steps
5. Use O*NET and Resume information to support
   the skill-gap analysis and recommendations.
 For every recommended job, return:

- title
- company
- location
- url
- employment_type
- source
- match:
    - score (0-100)
    - matching_skills
    - missing_skills
    - explanation

Only use information available in the tool results.
Never invent URLs, companies, or job details."""

    messages = [HumanMessage(content=prompt)]
    
    response = llm_with_tools.invoke(messages)
    structured_llm = llm.with_structured_output(
    JobAgentOutput,
    method="function_calling"
)#for structured output of the job agent

    # Let the LLM decide whether to use the job search tool
    response = llm_with_tools.invoke(messages)

    # Handle tool calls
    if response.tool_calls:

        messages.append(response)

        for tool_call in response.tool_calls:
            tool_result = search_jobs.invoke(tool_call["args"])

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
            )

        final_response = structured_llm.invoke(messages)

    else:
        final_response = response

    return {
    "jobs": final_response.jobs
}