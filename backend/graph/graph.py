from langgraph.graph import StateGraph, START, END

from backend.graph.state import CareerState
from backend.graph.nodes import (
    load_user_profile,
    orchestrator,
    synthesize_results,
)

from backend.agents.job_agent import job_agent
from backend.agents.certification_agent import certification_agent
from backend.agents.freelance_agent import freelance_agent


# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------

def route_agents(state: CareerState):

    return state["requested_agents"]


# ---------------------------------------------------------
# BUILD GRAPH
# ---------------------------------------------------------

builder = StateGraph(CareerState)


# Nodes
builder.add_node(
    "load_user_profile",
    load_user_profile
)

builder.add_node(
    "orchestrator",
    orchestrator
)

builder.add_node(
    "job_agent",
    job_agent
)

builder.add_node(
    "certification_agent",
    certification_agent
)

builder.add_node(
    "freelance_agent",
    freelance_agent
)

builder.add_node(
    "synthesize_results",
    synthesize_results
)


# ---------------------------------------------------------
# EDGES
# ---------------------------------------------------------

builder.add_edge(
    START,
    "load_user_profile"
)

builder.add_edge(
    "load_user_profile",
    "orchestrator"
)


# Orchestrator decides which agents run
builder.add_conditional_edges(
    "orchestrator",
    route_agents,
    {
        "job": "job_agent",
        "certification": "certification_agent",
        "freelance": "freelance_agent",
    }
)


# All selected agents eventually go to synthesis
builder.add_edge(
    "job_agent",
    "synthesize_results"
)

builder.add_edge(
    "certification_agent",
    "synthesize_results"
)

builder.add_edge(
    "freelance_agent",
    "synthesize_results"
)

builder.add_edge(
    "synthesize_results",
    END
)


# ---------------------------------------------------------
# COMPILE
# ---------------------------------------------------------

career_graph = builder.compile()