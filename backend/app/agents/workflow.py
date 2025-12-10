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

    # Add nodes
    workflow.add_node("triage", triage_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("policy", policy_agent)
    workflow.add_node("response", response_agent)
    workflow.add_node("escalation", escalation_agent)

    # Define the workflow edges (linear for MVP, can be made conditional later)
    workflow.set_entry_point("triage")
    workflow.add_edge("triage", "research")
    workflow.add_edge("research", "policy")
    workflow.add_edge("policy", "response")
    workflow.add_edge("response", "escalation")
    workflow.add_edge("escalation", END)

    # Compile the graph
    return workflow.compile()


# Create the compiled workflow
support_workflow = create_support_workflow()
