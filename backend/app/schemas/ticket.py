from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.ticket import TicketStatus, TicketPriority


class TicketCreate(BaseModel):
    """Schema for creating a new ticket."""

    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1)
    order_id: Optional[str] = None


class TicketResponse(BaseModel):
    """Schema for ticket response."""

    id: int
    ticket_number: str
    customer_email: str
    customer_name: str
    subject: str
    message: str
    status: TicketStatus
    priority: TicketPriority
    intent: Optional[str] = None
    confidence: Optional[float] = None
    ai_response: Optional[str] = None
    final_response: Optional[str] = None
    response_approved: bool
    order_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""

    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    final_response: Optional[str] = None
    response_approved: Optional[bool] = None


class TicketWithTraces(TicketResponse):
    """Ticket response with agent traces included."""

    agent_traces: List["AgentTraceResponse"] = []
    messages: List["MessageResponse"] = []


# Import here to avoid circular dependency
from app.schemas.agent_trace import AgentTraceResponse
from app.schemas.message import MessageResponse

TicketWithTraces.model_rebuild()
