"""
LangGraph Multi-Agent Workflow definition.
Connects Job & Candidate Analysis, Supervisor evaluation, Application Generation,
and the LLM-as-a-Judge ReAct revision conditional loop.
"""
import logging
import uuid
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END

from app.graph.checkpoint import get_postgres_checkpointer
from app.graph.nodes import (
    application_generation_node,
    candidate_analysis_node,
    escalate_human_review_node,
    human_review_node,
    job_analysis_node,
    judge_node,
    react_revision_node,
    supervisor_node,
)
from app.graph.routing import route_judge_decision
from app.graph.state import AgentGraphState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Construct the StateGraph connecting all agents and conditional revision loops."""
    builder = StateGraph(AgentGraphState)  # type: ignore[arg-type]

    # 1. Register agent nodes
    builder.add_node("job_analysis", job_analysis_node)
    builder.add_node("candidate_analysis", candidate_analysis_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("application_generation", application_generation_node)
    builder.add_node("judge", judge_node)
    builder.add_node("react_revision", react_revision_node)
    builder.add_node("escalate_human_review", escalate_human_review_node)
    builder.add_node("human_review", human_review_node)

    # 2. Parallel edges from START to both analysis branches
    builder.add_edge(START, "job_analysis")
    builder.add_edge(START, "candidate_analysis")

    # 3. Join both branches into the Supervisor node
    builder.add_edge("job_analysis", "supervisor")
    builder.add_edge("candidate_analysis", "supervisor")

    # 4. Supervisor routes into Application Generation
    builder.add_edge("supervisor", "application_generation")

    # 5. Application generation routes to Judge
    builder.add_edge("application_generation", "judge")

    # 6. CONDITIONAL EDGE from Judge:
    builder.add_conditional_edges(
        "judge",
        route_judge_decision,
        {
            "human_review": "human_review",
            "react_revision": "react_revision",
            "escalate_human_review": "escalate_human_review",
        },
    )

    # 7. ReAct Revision loops back to Judge!
    builder.add_edge("react_revision", "judge")

    # 8. Terminal edges
    builder.add_edge("human_review", END)
    builder.add_edge("escalate_human_review", END)

    return builder


async def run_agent_workflow(
    user_id: int,
    job_raw_text: str,
    hint_title: Optional[str] = None,
    hint_company: Optional[str] = None,
    thread_id: Optional[str] = None,
    human_feedback: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the multi-agent graph asynchronously with PostgreSQL state checkpointing."""
    active_thread = thread_id or f"user-{user_id}-{uuid.uuid4().hex[:8]}"

    initial_state: AgentGraphState = {
        "user_id": user_id,
        "job_raw_text": job_raw_text,
        "hint_title": hint_title,
        "hint_company": hint_company,
        "job_analysis": None,
        "candidate_profile": None,
        "candidate_analysis": None,
        "supervisor_evaluation": None,
        "generated_application": None,
        "application_id": None,
        "judge_evaluation": None,
        "revision_count": 0,
        "human_feedback": human_feedback,
        "human_approved": False,
        "status": "in_progress",
        "errors": [],
    }

    builder = build_graph()

    async with get_postgres_checkpointer() as checkpointer:
        compiled_graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": active_thread}}
        result_state = await compiled_graph.ainvoke(initial_state, config=config)
        return result_state


async def stream_agent_workflow(
    user_id: int,
    job_raw_text: str,
    hint_title: Optional[str] = None,
    hint_company: Optional[str] = None,
    thread_id: Optional[str] = None,
    human_feedback: Optional[str] = None,
):
    """Execute the multi-agent graph with streaming state updates per completed node."""
    active_thread = thread_id or f"user-{user_id}-{uuid.uuid4().hex[:8]}"

    initial_state: AgentGraphState = {
        "user_id": user_id,
        "job_raw_text": job_raw_text,
        "hint_title": hint_title,
        "hint_company": hint_company,
        "job_analysis": None,
        "candidate_profile": None,
        "candidate_analysis": None,
        "supervisor_evaluation": None,
        "generated_application": None,
        "application_id": None,
        "judge_evaluation": None,
        "revision_count": 0,
        "human_feedback": human_feedback,
        "human_approved": False,
        "status": "in_progress",
        "errors": [],
    }

    builder = build_graph()

    async with get_postgres_checkpointer() as checkpointer:
        compiled_graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": active_thread}}
        async for chunk in compiled_graph.astream(initial_state, config=config, stream_mode="updates"):
            yield chunk