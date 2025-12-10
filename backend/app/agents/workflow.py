from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from app.agents.agent_nodes import (
    triage_agent,
    research_agent,
    policy_agent,
    response_agent,
    escalation_agent,
)


class SupportAgentState(TypedDict):
    """State passed between agents in the workflow."""

    # Input fields
    ticket_id: int
    customer_email: str
    customer_name: str
    subject: str
    message: str
    order_id: str | None

    # Agent outputs (stored as Pydantic models)
    triage: dict | None
    research: dict | None
    policy_check: dict | None
    response: dict | None
    escalation: dict | None

    # Final outputs
    final_response: str | None
    requires_human: bool
    overall_confidence: float

    # Internal traces
    _traces: list[dict]


def create_support_workflow():
    """
    Create the LangGraph workflow for support ticket processing.

    The workflow follows this path:
    1. Triage Agent - Classify intent and priority
    2. Research Agent - Search knowledge base
    3. Policy Agent - Check eligibility and enforce policies
    4. Response Agent - Draft customer response
    5. Escalation Agent - Decide if human review needed
    """

    # Create the graph
    workflow = StateGraph(SupportAgentState)

    # Add nodes (use different names to avoid conflict with state attributes)
    workflow.add_node("triage_node", triage_agent)
    workflow.add_node("research_node", research_agent)
    workflow.add_node("policy_node", policy_agent)
    workflow.add_node("response_node", response_agent)
    workflow.add_node("escalation_node", escalation_agent)

    # Define the workflow edges (linear for MVP, can be made conditional later)
    workflow.set_entry_point("triage_node")
    workflow.add_edge("triage_node", "research_node")
    workflow.add_edge("research_node", "policy_node")
    workflow.add_edge("policy_node", "response_node")
    workflow.add_edge("response_node", "escalation_node")
    workflow.add_edge("escalation_node", END)

    # Compile the graph
    return workflow.compile()


# Create the compiled workflow
support_workflow = create_support_workflow()
