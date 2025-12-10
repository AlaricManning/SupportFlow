from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.core.database import get_db
from app.models import Ticket, TicketStatus, TicketPriority, AgentTrace

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("", response_model=Dict[str, Any])
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get overall system statistics.
    """
    # Total tickets
    total_tickets = db.query(Ticket).count()

    # Tickets by status
    status_counts = (
        db.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )
    status_breakdown = {status.value: count for status, count in status_counts}

    # Tickets by priority
    priority_counts = (
        db.query(Ticket.priority, func.count(Ticket.id))
        .group_by(Ticket.priority)
        .all()
    )
    priority_breakdown = {priority.value: count for priority, count in priority_counts}

    # Average confidence
    avg_confidence = db.query(func.avg(Ticket.confidence)).scalar() or 0.0

    # Human escalation rate
    human_needed = db.query(Ticket).filter(
        Ticket.status == TicketStatus.WAITING_HUMAN
    ).count()
    escalation_rate = (human_needed / total_tickets * 100) if total_tickets > 0 else 0

    # Most common intents
    intent_counts = (
        db.query(Ticket.intent, func.count(Ticket.id))
        .filter(Ticket.intent.isnot(None))
        .group_by(Ticket.intent)
        .order_by(func.count(Ticket.id).desc())
        .limit(5)
        .all()
    )
    top_intents = {intent: count for intent, count in intent_counts}

    # Agent performance
    agent_stats = (
        db.query(
            AgentTrace.agent_name,
            func.avg(AgentTrace.execution_time_ms).label("avg_time"),
            func.count(AgentTrace.id).label("executions"),
        )
        .group_by(AgentTrace.agent_name)
        .all()
    )
    agent_performance = {
        agent: {"avg_execution_time_ms": round(avg_time, 2), "total_executions": count}
        for agent, avg_time, count in agent_stats
    }

    return {
        "total_tickets": total_tickets,
        "status_breakdown": status_breakdown,
        "priority_breakdown": priority_breakdown,
        "average_confidence": round(avg_confidence, 3),
        "escalation_rate_percent": round(escalation_rate, 2),
        "top_intents": top_intents,
        "agent_performance": agent_performance,
    }
