from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.ticket import TicketPriority


class TriageOutput(BaseModel):
    """Structured output from the Triage Agent."""

    intent: str = Field(..., description="Classified intent (e.g., refund_request, product_inquiry)")
    priority: TicketPriority = Field(..., description="Ticket priority level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Explanation of the classification")
    requires_order_lookup: bool = Field(
        default=False, description="Whether order information is needed"
    )
    suggested_tags: List[str] = Field(default_factory=list, description="Suggested tags")


class ResearchOutput(BaseModel):
    """Structured output from the Research Agent."""

    relevant_articles: List[Dict[str, str]] = Field(
        default_factory=list, description="List of relevant KB articles"
    )
    search_queries_used: List[str] = Field(
        default_factory=list, description="Queries used to search KB"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in findings")
    summary: str = Field(..., description="Summary of research findings")


class PolicyCheckOutput(BaseModel):
    """Structured output from the Policy/Refund Agent."""

    is_eligible: bool = Field(..., description="Whether customer is eligible for action")
    reason: str = Field(..., description="Explanation of eligibility decision")
    order_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Order information if available"
    )
    refund_amount: Optional[float] = Field(default=None, description="Refund amount if applicable")
    actions_taken: List[str] = Field(default_factory=list, description="Actions performed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in decision")


class ResponseOutput(BaseModel):
    """Structured output from the Response Agent."""

    response_text: str = Field(..., description="The drafted response to customer")
    tone: str = Field(default="professional", description="Tone of the response")
    includes_apology: bool = Field(default=False, description="Whether response includes apology")
    includes_action_items: List[str] = Field(
        default_factory=list, description="Action items mentioned"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in response quality")
    requires_human_review: bool = Field(
        default=False, description="Whether human review is needed"
    )


class EscalationDecision(BaseModel):
    """Structured output from the Escalation Agent."""

    should_escalate: bool = Field(..., description="Whether to escalate to human")
    reasons: List[str] = Field(..., description="Reasons for escalation decision")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    recommended_specialist: Optional[str] = Field(
        default=None, description="Recommended specialist type if escalating"
    )


class AgentState(BaseModel):
    """Complete state passed between agents in the workflow."""

    # Input
    ticket_id: int
    customer_email: str
    customer_name: str
    subject: str
    message: str
    order_id: Optional[str] = None

    # Agent outputs
    triage: Optional[TriageOutput] = None
    research: Optional[ResearchOutput] = None
    policy_check: Optional[PolicyCheckOutput] = None
    response: Optional[ResponseOutput] = None
    escalation: Optional[EscalationDecision] = None

    # Final decision
    final_response: Optional[str] = None
    requires_human: bool = False
    overall_confidence: float = 0.0

    class Config:
        arbitrary_types_allowed = True
