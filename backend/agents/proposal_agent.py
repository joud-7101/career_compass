"""
Proposal Agent -- generates and refines personalized freelance proposals.

This agent has two jobs:
  1. generate_proposal()  -- writes the first draft of a proposal for a
                             specific project, using the user''s full profile.
  2. chat_with_proposal() -- takes the entire conversation history and
                             returns the next AI reply (refinement or question).

WHY a separate agent instead of putting this inside freelance_agent.py?
The main freelance agent already takes 30-60 seconds because it searches
live APIs and ranks projects. Generating proposals for all 10 projects
at once would make the page unusable. Instead we generate proposals
on-demand -- only when the user clicks "View Proposal" on a card they
actually care about. This keeps the main page fast.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.config import settings
from backend.schemas.profile import UserProfile


# The LLM -- we use a plain ChatOpenAI (no structured output) because
# proposals are free-form text, not structured data. A slightly
# higher temperature (0.4) gives the writing more personality while
# still staying professional and accurate.
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.4,
    api_key=settings.openai_api_key,
)


# System prompt shared by both generate and chat functions.
# It sets the persona, the rules, and the exact proposal structure
# so the LLM always produces something consistent and professional.
SYSTEM_PROMPT = """\
You are a professional freelance proposal writer for CareerCompass.
Your job is to write personalized, compelling proposals that help
freelancers win projects on platforms like Freelancer.com.

RULES
-----
- Write in first person ("I", "my", "I have").
- Use the user''s REAL skills and REAL experience from their profile.
  Never invent experience they do not have.
- Be specific -- mention actual project names, technologies, or
  achievements from the user''s profile where relevant.
- Keep the tone professional but warm, not robotic or generic.
- Do NOT use filler phrases like "I am writing to express my interest"
  or "I am the perfect candidate". Get straight to the value.
- Do NOT add a subject line or email header -- just the body text.
- Aim for 150-250 words unless the user asks for something different.

PROPOSAL STRUCTURE (3 paragraphs)
-----------------------------------
1. HOOK -- Open with why this specific project caught your eye and
   one concrete reason you are well-placed to deliver it.
2. PROOF -- Highlight 2-3 directly relevant skills or past experiences.
   Be specific (project names, technologies, outcomes).
3. CLOSE -- A confident, low-pressure call to action. Offer to share
   portfolio, answer questions, or schedule a quick call.
"""


def _build_profile_context(profile: UserProfile) -> str:
    """
    Convert the UserProfile object into a readable text block that the
    LLM can use as context. We extract only the most relevant fields
    so the prompt does not become too long.
    """
    # Skills -- just the names
    skills = [s.name for s in profile.skills] if profile.skills else []

    # Experience -- title + company + short description
    experience_lines = []
    for exp in profile.experience:
        line = f"- {exp.title}"
        if exp.company:
            line += f" at {exp.company}"
        if exp.description:
            # Truncate long descriptions to keep the prompt tight
            snippet = exp.description[:200].strip()
            if len(exp.description) > 200:
                snippet += "..."
            line += f": {snippet}"
        experience_lines.append(line)

    # Projects -- name + short description + technologies
    project_lines = []
    for proj in profile.projects:
        line = f"- {proj.name}"
        if proj.technologies:
            line += f" ({', '.join(proj.technologies)})"
        if proj.description:
            snippet = proj.description[:150].strip()
            if len(proj.description) > 150:
                snippet += "..."
            line += f": {snippet}"
        project_lines.append(line)

    # Summary -- the user''s professional headline / about section
    summary = profile.professional_summary or ""

    # Build the context block
    parts = []
    if summary:
        parts.append(f"PROFESSIONAL SUMMARY\n{summary}")
    if skills:
        parts.append(f"SKILLS\n{', '.join(skills)}")
    if experience_lines:
        parts.append("WORK EXPERIENCE\n" + "\n".join(experience_lines))
    if project_lines:
        parts.append("PERSONAL / SIDE PROJECTS\n" + "\n".join(project_lines))

    return "\n\n".join(parts) if parts else "No profile information available."


# ─────────────────────────────────────────────────────────────────
# FUNCTION 1 -- Generate the first draft
# ─────────────────────────────────────────────────────────────────

def generate_proposal(
    profile: UserProfile,
    project_title: str,
    project_description: str,
    budget_or_rate: str | None,
    matching_skills: list[str],
    missing_skills: list[str],
) -> str:
    """
    Generate a personalized first-draft proposal for a specific project.

    Parameters
    ----------
    profile             -- The user''s full profile (skills, experience, projects)
    project_title       -- The title of the freelance project
    project_description -- A short description / match explanation
    budget_or_rate      -- The project budget (optional, for context)
    matching_skills     -- Skills the user has that match the project
    missing_skills      -- Skills the project needs that the user lacks

    Returns
    -------
    A string containing the ready-to-send proposal text.
    """
    # Build the user profile context and embed it in the prompt
    profile_context = _build_profile_context(profile)

    # The human message gives the LLM the specific project details
    # so it can tailor the proposal precisely to this one project
    human_prompt = f"""Write a personalized freelance proposal for the following project.

PROJECT DETAILS
---------------
Title: {project_title}
Description: {project_description}
Budget / Rate: {budget_or_rate or "Not specified"}
Skills that match my profile: {", ".join(matching_skills) if matching_skills else "None listed"}
Skills I am missing: {", ".join(missing_skills) if missing_skills else "None"}

MY PROFILE
----------
{profile_context}

Write the proposal now. Output only the proposal text -- no subject line,
no "Here is the proposal:" header, just the body."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    # Invoke the LLM and return just the text content
    response = llm.invoke(messages)
    return response.content.strip()


# ─────────────────────────────────────────────────────────────────
# FUNCTION 2 -- Continue the refinement conversation
# ─────────────────────────────────────────────────────────────────

def chat_with_proposal(
    profile: UserProfile,
    project_title: str,
    project_description: str,
    messages: list[dict],
) -> str:
    """
    Continue the proposal refinement conversation.

    The messages list contains the full conversation history as dicts:
        [{"role": "assistant", "content": "<first proposal>"},
         {"role": "user",      "content": "make it shorter"},
         ...]

    The LLM sees the entire history plus the user profile, so it can
    refine the proposal intelligently based on all previous requests.

    Returns
    -------
    A string containing the AI''s next reply (updated proposal or answer).
    """
    profile_context = _build_profile_context(profile)

    # The system prompt stays the same -- it keeps the LLM in "proposal
    # writer" mode even as the conversation evolves.
    # We append extra context about the specific project so the LLM
    # never forgets what project we are talking about.
    full_system = f"""{SYSTEM_PROMPT}

PROJECT CONTEXT (do not lose sight of this)
--------------------------------------------
Title: {project_title}
Description: {project_description}

USER PROFILE
------------
{profile_context}

You are in a refinement conversation. The user will ask you to adjust
the proposal. Always output the FULL updated proposal after any change,
not just the changed part -- so the user can copy it immediately.
If the user asks a question, answer it briefly then show the proposal."""

    # Convert the dict history into LangChain message objects.
    # "assistant" messages become AIMessage, "user" become HumanMessage.
    lc_messages: list = [SystemMessage(content=full_system)]

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    response = llm.invoke(lc_messages)
    return response.content.strip()
