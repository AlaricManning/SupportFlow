from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class MessageRole(str, enum.Enum):
    """Message role enumeration."""

    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class TicketMessage(Base):
    """Individual messages in a ticket conversation."""

    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)

    role = Column(Enum(MessageRole))
    content = Column(Text)
    sender_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")

    def __repr__(self):
        return f"<TicketMessage {self.role} for Ticket {self.ticket_id}>"
