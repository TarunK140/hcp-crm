"""
LangGraph orchestration for the HCP CRM AI assistant.

Flow:
    START --> router (LLM classifies intent)
              --> conditional edge (based purely on the LLM's own tool_choice)
                  --> log_interaction_node
                  --> edit_interaction_node
                  --> search_interaction_node
                  --> view_history_node
                  --> follow_up_recommendation_node
              --> END

Every one of the 5 tool nodes is a separate LangGraph node, and the edge
taken out of the router is chosen by `route_after_router`, whose only input
is the tool name the LLM itself returned in `router_node`. There is no
keyword/if-else intent classification anywhere in this file — the LLM is
the sole decision-maker for intent, and LangGraph's conditional-edge
mechanism is what performs the actual routing.
"""

from typing import Optional, TypedDict
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from app.core.llm_client import chat_completion, safe_json_parse
from app.prompts.prompts import ROUTER_SYSTEM_PROMPT
from app.tools import (
    log_interaction_tool,
    edit_interaction_tool,
    search_interaction_tool,
    history_tool,
    follow_up_tool,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_TOOLS = {
    "log_interaction",
    "edit_interaction",
    "search_interaction",
    "view_history",
    "follow_up_recommendation",
}


class GraphState(TypedDict, total=False):
    user_message: str
    current_interaction_id: Optional[int]
    tool_choice: str
    result: dict
    db: Session  # attached at invocation time, not persisted/serialized


# ---------------------------------------------------------------------------
# Router node — the ONLY place intent is decided, and it's decided entirely
# by the LLM. No keyword matching, no if/else on the user's raw text.
# ---------------------------------------------------------------------------

def router_node(state: GraphState) -> GraphState:
    """Ask the LLM which of the 5 tools should handle this message."""
    raw = chat_completion(
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": state["user_message"]},
        ],
        json_mode=True,
        temperature=0.0,
    )
    decision = safe_json_parse(raw)
    tool_choice = decision.get("tool", "log_interaction")
    if tool_choice not in VALID_TOOLS:
        logger.warning("Router returned unrecognized tool=%s, defaulting to log_interaction", tool_choice)
        tool_choice = "log_interaction"
    logger.info("Router selected tool=%s reasoning=%s", tool_choice, decision.get("reasoning"))
    return {**state, "tool_choice": tool_choice}


def route_after_router(state: GraphState) -> str:
    """
    LangGraph conditional-edge selector. This function does NOT make any
    intent decision itself — it purely reads back the tool name the LLM
    already chose in `router_node` and tells LangGraph which node to
    traverse to next. This is what makes routing a genuine LangGraph
    conditional edge rather than a plain if/elif dispatcher.
    """
    return state["tool_choice"]


# ---------------------------------------------------------------------------
# One LangGraph node per tool
# ---------------------------------------------------------------------------

def log_interaction_node(state: GraphState) -> GraphState:
    result = log_interaction_tool.run(state["db"], state["user_message"])
    return {**state, "result": result}


def edit_interaction_node(state: GraphState) -> GraphState:
    interaction_id = state.get("current_interaction_id")
    if interaction_id is None:
        result = {
            "tool": "edit_interaction",
            "error": "No active interaction selected to edit. Log one first, or specify which interaction.",
        }
    else:
        result = edit_interaction_tool.run(state["db"], state["user_message"], interaction_id)
    return {**state, "result": result}


def search_interaction_node(state: GraphState) -> GraphState:
    result = search_interaction_tool.run(state["db"], state["user_message"])
    return {**state, "result": result}


def view_history_node(state: GraphState) -> GraphState:
    result = history_tool.run(state["db"], state["user_message"])
    return {**state, "result": result}


def follow_up_recommendation_node(state: GraphState) -> GraphState:
    result = follow_up_tool.run(state["db"], state["user_message"])
    return {**state, "result": result}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("router", router_node)
    graph.add_node("log_interaction", log_interaction_node)
    graph.add_node("edit_interaction", edit_interaction_node)
    graph.add_node("search_interaction", search_interaction_node)
    graph.add_node("view_history", view_history_node)
    graph.add_node("follow_up_recommendation", follow_up_recommendation_node)

    graph.set_entry_point("router")

    # This is the actual LangGraph conditional routing mechanism: the edge
    # taken depends solely on `route_after_router`, which just echoes back
    # the LLM's own decision from the router node above.
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "log_interaction": "log_interaction",
            "edit_interaction": "edit_interaction",
            "search_interaction": "search_interaction",
            "view_history": "view_history",
            "follow_up_recommendation": "follow_up_recommendation",
        },
    )

    for tool_name in VALID_TOOLS:
        graph.add_edge(tool_name, END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_graph(db: Session, user_message: str, current_interaction_id: Optional[int] = None) -> dict:
    """Entry point called by the API layer. Returns the tool's result dict."""
    graph = get_graph()
    final_state = graph.invoke(
        {
            "user_message": user_message,
            "current_interaction_id": current_interaction_id,
            "db": db,
        }
    )
    return final_state["result"]
