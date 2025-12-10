from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import string
from datetime import datetime

from app.core.database import get_db
from app.models import Ticket, TicketStatus, AgentTrace
from app.schemas import TicketCreate, TicketResponse, TicketUpdate, TicketWithTraces
from app.agents.workflow import support_workflow

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def generate_ticket_number() -> str:
    """Generate a unique ticket number."""
    return f"TKT-{random.randint(100000, 999999)}"


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_data: TicketCreate, db: Session = Depends(get_db)):
    """
    Create a new support ticket and process it through the agent workflow.
    """
    # Create ticket in database
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        customer_email=ticket_data.customer_email,
        customer_name=ticket_data.customer_name,
        subject=ticket_data.subject,
        message=ticket_data.message,
        order_id=ticket_data.order_id,
        status=TicketStatus.IN_PROGRESS,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Prepare state for agent workflow
    initial_state = {
        "ticket_id": ticket.id,
        "customer_email": ticket.customer_email,
        "customer_name": ticket.customer_name,
        "subject": ticket.subject,
        "message": ticket.message,
        "order_id": ticket.order_id,
        "triage": None,
        "research": None,
        "policy_check": None,
        "response": None,
        "escalation": None,
        "final_response": None,
        "requires_human": False,
        "overall_confidence": 0.0,
        "_traces": [],
    }

    try:
        # Run the agent workflow
        final_state = support_workflow.invoke(initial_state)

        # Update ticket with results
        if final_state.get("triage"):
            ticket.intent = final_state["triage"].intent
            ticket.priority = final_state["triage"].priority
            ticket.confidence = final_state["triage"].confidence

        ticket.ai_response = final_state.get("final_response")
        ticket.confidence = final_state.get("overall_confidence", 0.0)

        # Set status based on escalation
        if final_state.get("requires_human"):
            ticket.status = TicketStatus.WAITING_HUMAN
        else:
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.utcnow()
            ticket.final_response = final_state.get("final_response")
            ticket.response_approved = 1

        # Save agent traces
        for trace_data in final_state.get("_traces", []):
            trace = AgentTrace(
                ticket_id=ticket.id,
                agent_name=trace_data["agent_name"],
                step_number=trace_data["step_number"],
                input_data=trace_data.get("input_data"),
                output_data=trace_data.get("output_data"),
                reasoning=trace_data.get("reasoning"),
                confidence=trace_data.get("confidence"),
                tools_used=trace_data.get("tools_used"),
                execution_time_ms=trace_data.get("execution_time_ms", 0),
            )
            db.add(trace)

        db.commit()
        db.refresh(ticket)

    except Exception as e:
        # If agent workflow fails, mark ticket for human review
        ticket.status = TicketStatus.WAITING_HUMAN
        ticket.metadata = {"error": str(e)}
        db.commit()
        db.refresh(ticket)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {str(e)}",
        )

    return ticket


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status_filter: TicketStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List all tickets with optional status filter.
    """
    query = db.query(Ticket)

    if status_filter:
        query = query.filter(Ticket.status == status_filter)

    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketWithTraces)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get a specific ticket with all agent traces.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    return ticket


@router.get("/number/{ticket_number}", response_model=TicketWithTraces)
async def get_ticket_by_number(ticket_number: str, db: Session = Depends(get_db)):
    """
    Get a ticket by its ticket number.
    """
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int, update_data: TicketUpdate, db: Session = Depends(get_db)
):
    """
    Update a ticket (for admin approval/editing).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    # Update fields
    if update_data.status is not None:
        ticket.status = update_data.status
        if update_data.status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()

    if update_data.priority is not None:
        ticket.priority = update_data.priority

    if update_data.final_response is not None:
        ticket.final_response = update_data.final_response

    if update_data.response_approved is not None:
        ticket.response_approved = 1 if update_data.response_approved else 0

    db.commit()
    db.refresh(ticket)

    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Delete a ticket (admin only).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    db.delete(ticket)
    db.commit()

    return None
