from typing import Dict, Any, List
from langchain.tools import tool
from app.services.knowledge_base import kb
from app.services.mock_order_api import order_api


@tool
def search_knowledge_base(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant information.

    Args:
        query: The search query
        n_results: Number of results to return (default: 3)

    Returns:
        List of relevant knowledge base articles with content and metadata
    """
    return kb.search(query, n_results=n_results)


@tool
def get_order_details(order_id: str) -> Dict[str, Any]:
    """
    Retrieve order details by order ID.

    Args:
        order_id: The order ID to look up

    Returns:
        Order details including items, status, total, etc.
    """
    order = order_api.get_order(order_id)
    if not order:
        return {"error": "Order not found", "order_id": order_id}
    return order


@tool
def check_refund_eligibility(order_id: str) -> Dict[str, Any]:
    """
    Check if an order is eligible for refund.

    Args:
        order_id: The order ID to check

    Returns:
        Eligibility status, reason, and order details
    """
    return order_api.check_refund_eligibility(order_id)


@tool
def process_refund(order_id: str, amount: float = None) -> Dict[str, Any]:
    """
    Process a refund for an order.

    Args:
        order_id: The order ID to refund
        amount: Optional specific amount to refund (defaults to full order total)

    Returns:
        Refund processing result with refund ID and estimated timeline
    """
    return order_api.process_refund(order_id, amount)


# Export all tools as a list
ALL_TOOLS = [
    search_knowledge_base,
    get_order_details,
    check_refund_eligibility,
    process_refund,
]
