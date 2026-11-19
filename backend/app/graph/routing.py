"""
Conditional Routing logic for the LangGraph multi-agent workflow.
Determines whether to approve, loop for ReAct revision, or escalate to human review.
"""
from typing import Literal
from app.graph.state import AgentGraphState


def route_judge_decision(
    state: AgentGraphState,
) -> Literal["human_review", "react_revision", "escalate_human_review"]:
    """Evaluate Judge verdict and revision counter to determine next graph node.

    Rules:
    1. If judge decision is 'APPROVED' -> route to 'human_review'.
    2. If judge decision is 'REJECTED' and revision_count < 3 -> route to 'react_revision'.
    3. If revision_count >= 3 -> route to 'escalate_human_review' (bounded retry limit).
    """
    judge_eval = state.get("judge_evaluation")
    revision_count = state.get("revision_count", 0)

    decision = "APPROVED"
    if judge_eval and isinstance(judge_eval, dict):
        decision = judge_eval.get("decision", "APPROVED")

    if decision == "APPROVED":
        return "human_review"

    # Decision is REJECTED
    if revision_count < 3:
        return "react_revision"

    return "escalate_human_review"