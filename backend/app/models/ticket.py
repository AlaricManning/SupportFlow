from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_HUMAN = "waiting_human"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    """Support ticket model."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True)
    customer_email = Column(String(255), index=True)
    customer_name = Column(String(255))
    subject = Column(String(500))
    message = Column(Text)

    # Triage results
    status = Column(Enum(TicketStatus), default=TicketStatus.NEW, index=True)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    intent = Column(String(255))  # e.g., "refund_request", "product_inquiry", etc.
    confidence = Column(Float)  # AI confidence score

    # Response
    ai_response = Column(Text, nullable=True)
    final_response = Column(Text, nullable=True)
    response_approved = Column(Integer, default=0)  # Boolean: 0=pending, 1=approved

    # Metadata
    order_id = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=True)  # Store additional structured data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    agent_traces = relationship("AgentTrace", back_populates="ticket", cascade="all, delete-orphan")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket {self.ticket_number}: {self.subject}>"
