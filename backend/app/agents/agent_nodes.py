import instructor
from openai import OpenAI
from typing import Dict, Any
import time
from app.core.config import settings
from app.schemas.agent_output import (
    TriageOutput,
    ResearchOutput,
    PolicyCheckOutput,
    ResponseOutput,
    EscalationDecision,
)
from app.agents.tools import (
    search_knowledge_base,
    get_order_details,
    check_refund_eligibility,
    process_refund,
)

# Initialize instructor-patched OpenAI client for structured outputs
client = instructor.patch(OpenAI(api_key=settings.OPENAI_API_KEY))


def triage_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triage Agent: Classifies intent and assigns priority.
    """
    start_time = time.time()

    prompt = f"""
    You are a customer support triage agent. Analyze the following support ticket and classify it.

    Customer: {state['customer_name']} ({state['customer_email']})
    Subject: {state['subject']}
    Message: {state['message']}
    Order ID: {state.get('order_id', 'Not provided')}

    Classify this ticket's intent, priority, and determine if order lookup is needed.
    Be specific with intent (e.g., 'refund_request', 'shipping_inquiry', 'product_question', 'account_issue').
    """

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_model=TriageOutput,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )

    execution_time = int((time.time() - start_time) * 1000)

    # Store triage output and trace
    state["triage"] = response
    state["_traces"] = state.get("_traces", [])
    state["_traces"].append(
        {
            "agent_name": "triage",
            "step_number": len(state["_traces"]) + 1,
            "input_data": {
                "subject": state["subject"],
                "message": state["message"][:200],
            },
            "output_data": response.model_dump(),
            "reasoning": response.reasoning,
            "confidence": response.confidence,
            "execution_time_ms": execution_time,
        }
    )

    return state


def research_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research Agent: Searches knowledge base for relevant information.
    """
    start_time = time.time()

    triage = state.get("triage")
    if not triage:
        return state

    # Search knowledge base
    search_queries = [
        state["subject"],
        triage.intent.replace("_", " "),
        f"{triage.intent} policy",
    ]

    all_articles = []
    for query in search_queries[:2]:  # Limit to 2 queries
        articles = search_knowledge_base.invoke({"query": query, "n_results": 2})
        all_articles.extend(articles)

    # Deduplicate by source
    seen_sources = set()
    unique_articles = []
    for article in all_articles:
        if article["source"] not in seen_sources:
            seen_sources.add(article["source"])
            unique_articles.append(article)

    # Summarize findings
    prompt = f"""
    You are a research agent. Based on the ticket intent '{triage.intent}' and these knowledge base articles,
    provide a summary of relevant information.

    Articles:
    {chr(10).join([f"- {a['source']}: {a['content'][:200]}..." for a in unique_articles[:3]])}

    Provide a concise summary and confidence score.
    """

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_model=ResearchOutput,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )

    # Add article details
    response.relevant_articles = [
        {"source": a["source"], "content": a["content"][:300]} for a in unique_articles[:3]
    ]
    response.search_queries_used = search_queries[:2]

    execution_time = int((time.time() - start_time) * 1000)

    state["research"] = response
    state["_traces"].append(
        {
            "agent_name": "research",
            "step_number": len(state["_traces"]) + 1,
            "input_data": {"intent": triage.intent, "queries": search_queries[:2]},
            "output_data": response.model_dump(),
            "reasoning": response.summary,
            "confidence": response.confidence,
            "tools_used": ["search_knowledge_base"],
            "execution_time_ms": execution_time,
        }
    )

    return state


def policy_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Policy/Refund Agent: Checks eligibility and can process actions.
    """
    start_time = time.time()

    triage = state.get("triage")
    if not triage:
        return state

    # Check if we need to look up order details
    order_details = None
    refund_check = None
    actions_taken = []

    if state.get("order_id") and triage.requires_order_lookup:
        # Get order details
        order_details = get_order_details.invoke({"order_id": state["order_id"]})
        actions_taken.append("get_order_details")

        # If refund-related, check eligibility
        if "refund" in triage.intent.lower():
            refund_check = check_refund_eligibility.invoke({"order_id": state["order_id"]})
            actions_taken.append("check_refund_eligibility")

    # Determine eligibility
    prompt = f"""
    You are a policy enforcement agent. Determine if the customer's request is eligible.

    Intent: {triage.intent}
    Order Details: {order_details if order_details else "No order provided"}
    Refund Check: {refund_check if refund_check else "N/A"}

    Provide eligibility decision and clear reasoning.
    """

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_model=PolicyCheckOutput,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )

    response.order_details = order_details
    response.actions_taken = actions_taken

    if refund_check and refund_check.get("eligible"):
        response.refund_amount = refund_check.get("refund_amount")

    execution_time = int((time.time() - start_time) * 1000)

    state["policy_check"] = response
    state["_traces"].append(
        {
            "agent_name": "policy",
            "step_number": len(state["_traces"]) + 1,
            "input_data": {"intent": triage.intent, "has_order": bool(order_details)},
            "output_data": response.model_dump(),
            "reasoning": response.reason,
            "confidence": response.confidence,
            "tools_used": actions_taken,
            "execution_time_ms": execution_time,
        }
    )

    return state


def response_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Response Agent: Drafts the final response to the customer.
    """
    start_time = time.time()

    triage = state.get("triage")
    research = state.get("research")
    policy = state.get("policy_check")

    prompt = f"""
    You are a customer support response agent. Draft a professional, empathetic response to the customer.

    Customer: {state['customer_name']}
    Intent: {triage.intent if triage else 'unknown'}
    Priority: {triage.priority if triage else 'medium'}

    Research Findings:
    {research.summary if research else 'No research available'}

    Policy Check:
    {policy.reason if policy else 'No policy check performed'}
    Eligible: {policy.is_eligible if policy else 'N/A'}

    Draft a response that:
    1. Addresses the customer's concern directly
    2. Provides relevant information from research
    3. Explains any policy decisions clearly
    4. Offers next steps or solutions
    5. Maintains a professional and empathetic tone

    Determine if human review is needed (complex cases, angry customers, edge cases).
    """

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_model=ResponseOutput,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )

    execution_time = int((time.time() - start_time) * 1000)

    state["response"] = response
    state["final_response"] = response.response_text
    state["_traces"].append(
        {
            "agent_name": "response",
            "step_number": len(state["_traces"]) + 1,
            "input_data": {
                "intent": triage.intent if triage else None,
                "research_available": bool(research),
                "policy_decision": policy.is_eligible if policy else None,
            },
            "output_data": response.model_dump(),
            "reasoning": f"Tone: {response.tone}, Requires review: {response.requires_human_review}",
            "confidence": response.confidence,
            "execution_time_ms": execution_time,
        }
    )

    return state


def escalation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Escalation Agent: Decides if human review is needed.
    """
    start_time = time.time()

    triage = state.get("triage")
    research = state.get("research")
    policy = state.get("policy_check")
    response = state.get("response")

    # Gather all confidence scores
    confidences = []
    if triage:
        confidences.append(triage.confidence)
    if research:
        confidences.append(research.confidence)
    if policy:
        confidences.append(policy.confidence)
    if response:
        confidences.append(response.confidence)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    prompt = f"""
    You are an escalation decision agent. Decide if this ticket needs human review.

    Average Confidence: {avg_confidence:.2f}
    Threshold: {settings.CONFIDENCE_THRESHOLD}
    Response Requires Review: {response.requires_human_review if response else False}
    Priority: {triage.priority if triage else 'unknown'}

    Consider:
    - Low confidence scores (< {settings.CONFIDENCE_THRESHOLD})
    - High priority or urgent tickets
    - Complex situations requiring judgment
    - Response agent flagged for review

    Provide escalation decision with clear reasons.
    """

    decision = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_model=EscalationDecision,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )

    decision.overall_confidence = avg_confidence

    execution_time = int((time.time() - start_time) * 1000)

    state["escalation"] = decision
    state["requires_human"] = decision.should_escalate
    state["overall_confidence"] = avg_confidence

    state["_traces"].append(
        {
            "agent_name": "escalation",
            "step_number": len(state["_traces"]) + 1,
            "input_data": {
                "avg_confidence": avg_confidence,
                "threshold": settings.CONFIDENCE_THRESHOLD,
            },
            "output_data": decision.model_dump(),
            "reasoning": ", ".join(decision.reasons),
            "confidence": avg_confidence,
            "execution_time_ms": execution_time,
        }
    )

    return state
