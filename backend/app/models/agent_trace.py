from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AgentTrace(Base):
    """Agent execution trace for transparency and debugging."""

    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)

    # Agent information
    agent_name = Column(String(100))  # e.g., "triage", "research", "policy", etc.
    step_number = Column(Integer)  # Order of execution

    # Execution details
    input_data = Column(JSON)  # What the agent received
    output_data = Column(JSON)  # What the agent produced
    reasoning = Column(Text)  # Agent's reasoning/thought process
    confidence = Column(Float, nullable=True)  # Confidence in decision

    # Tool usage
    tools_used = Column(JSON, nullable=True)  # List of tools called
    tool_results = Column(JSON, nullable=True)  # Results from tool calls

    # Performance metrics
    execution_time_ms = Column(Integer)  # How long the agent took
    tokens_used = Column(Integer, nullable=True)  # LLM tokens consumed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="agent_traces")

    def __repr__(self):
        return f"<AgentTrace {self.agent_name} for Ticket {self.ticket_id}>"
