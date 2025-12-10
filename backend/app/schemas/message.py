from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.ticket_message import MessageRole


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    ticket_id: int
    role: MessageRole
    content: str = Field(..., min_length=1)
    sender_name: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: int
    ticket_id: int
    role: MessageRole
    content: str
    sender_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
