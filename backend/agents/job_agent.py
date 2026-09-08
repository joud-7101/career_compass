from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from backend.graph.state import CareerState
from backend.config import settings
from backend.tools.job_search import search_jobs


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
Name: {user_profile.get("name", "")}
Education: {user_profile.get("education", "")}
Experience: {user_profile.get("experience", [])}
Skills: {user_profile.get("skills", [])}
Interests: {user_profile.get("interests", [])}
Location: {user_profile.get("location", "")}

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
"""

    messages = [HumanMessage(content=prompt)]

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

        # Let the LLM analyze the tool results
        final_response = llm_with_tools.invoke(messages)

    else:
        final_response = response

    return {
        "job_analysis": final_response.content
    }