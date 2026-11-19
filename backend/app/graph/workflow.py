"""
LangGraph Multi-Agent Workflow definition.
Connects Job Analysis and Candidate Analysis parallel branches to the Supervisor join node.
"""
import logging
import uuid
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END

from app.graph.checkpoint import get_postgres_checkpointer
from app.graph.nodes import candidate_analysis_node, job_analysis_node, supervisor_node
from app.graph.state import AgentGraphState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Construct the StateGraph with parallel branches joining into the supervisor node."""
    builder = StateGraph(AgentGraphState)# type: ignore[arg-type]

    # 1. Register the three agent nodes
    builder.add_node("job_analysis", job_analysis_node)
    builder.add_node("candidate_analysis", candidate_analysis_node)
    builder.add_node("supervisor", supervisor_node)

    # 2. Parallel edges from START to both branches
    builder.add_edge(START, "job_analysis")
    builder.add_edge(START, "candidate_analysis")

    # 3. Join both branches into the Supervisor node
    builder.add_edge("job_analysis", "supervisor")
    builder.add_edge("candidate_analysis", "supervisor")

    # 4. Supervisor completes the workflow
    builder.add_edge("supervisor", END)

    return builder


async def run_agent_workflow(
    user_id: int,
    job_raw_text: str,
    hint_title: Optional[str] = None,
    hint_company: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the multi-agent graph asynchronously with PostgreSQL state checkpointing.

    Args:
        user_id: Current authenticated user ID (enforces data isolation).
        job_raw_text: Raw Job Description text.
        hint_title: Optional job title provided by user.
        hint_company: Optional company name provided by user.
        thread_id: Optional thread ID for checkpoint history (generates UUID if omitted).

    Returns:
        Final AgentGraphState dictionary.
    """
    active_thread = thread_id or f"user-{user_id}-{uuid.uuid4().hex[:8]}"

    # Initial graph state
    initial_state: AgentGraphState = {
        "user_id": user_id,
        "job_raw_text": job_raw_text,
        "hint_title": hint_title,
        "hint_company": hint_company,
        "job_analysis": None,
        "candidate_profile": None,
        "candidate_analysis": None,
        "supervisor_evaluation": None,
        "status": "in_progress",
        "errors": [],
    }

    builder = build_graph()

    # Compile graph with AsyncPostgresSaver checkpointer and invoke asynchronously
    async with get_postgres_checkpointer() as checkpointer:
        compiled_graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": active_thread}}
        result_state = await compiled_graph.ainvoke(initial_state, config=config)
        return result_state