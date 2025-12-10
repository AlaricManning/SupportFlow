from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class AgentTraceResponse(BaseModel):
    """Schema for agent trace response."""

    id: int
    ticket_id: int
    agent_name: str
    step_number: int
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    tools_used: Optional[List[str]] = None
    tool_results: Optional[dict] = None
    execution_time_ms: int
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
