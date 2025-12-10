from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import random


class MockOrderAPI:
    """Mock order API for demonstration purposes."""

    # Mock database of orders
    MOCK_ORDERS = {
        "ORD-001": {
            "order_id": "ORD-001",
            "customer_email": "john@example.com",
            "order_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "total": 149.99,
            "status": "delivered",
            "items": [
                {"name": "Wireless Mouse", "price": 29.99, "quantity": 1},
                {"name": "Mechanical Keyboard", "price": 119.99, "quantity": 1},
            ],
            "refund_eligible": True,
            "refund_window_days": 30,
        },
        "ORD-002": {
            "order_id": "ORD-002",
            "customer_email": "jane@example.com",
            "order_date": (datetime.utcnow() - timedelta(days=45)).isoformat(),
            "total": 299.99,
            "status": "delivered",
            "items": [{"name": "4K Monitor", "price": 299.99, "quantity": 1}],
            "refund_eligible": False,
            "refund_window_days": 30,
        },
        "ORD-003": {
            "order_id": "ORD-003",
            "customer_email": "bob@example.com",
            "order_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "total": 79.99,
            "status": "shipped",
            "items": [{"name": "USB-C Cable Pack", "price": 79.99, "quantity": 1}],
            "refund_eligible": True,
            "refund_window_days": 30,
        },
    }

    @staticmethod
    def get_order(order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details by order ID."""
        return MockOrderAPI.MOCK_ORDERS.get(order_id)

    @staticmethod
    def check_refund_eligibility(order_id: str) -> Dict[str, Any]:
        """Check if order is eligible for refund."""
        order = MockOrderAPI.get_order(order_id)

        if not order:
            return {
                "eligible": False,
                "reason": "Order not found",
                "order_exists": False,
            }

        order_date = datetime.fromisoformat(order["order_date"])
        days_since_order = (datetime.utcnow() - order_date).days

        if days_since_order > order["refund_window_days"]:
            return {
                "eligible": False,
                "reason": f"Order is {days_since_order} days old, outside {order['refund_window_days']}-day refund window",
                "order_exists": True,
                "order": order,
            }

        if order["status"] not in ["delivered", "shipped"]:
            return {
                "eligible": False,
                "reason": f"Order status is {order['status']}, not eligible for refund",
                "order_exists": True,
                "order": order,
            }

        return {
            "eligible": True,
            "reason": "Order is within refund window and eligible",
            "order_exists": True,
            "order": order,
            "refund_amount": order["total"],
        }

    @staticmethod
    def process_refund(order_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Process a refund (mock implementation)."""
        eligibility = MockOrderAPI.check_refund_eligibility(order_id)

        if not eligibility["eligible"]:
            return {
                "success": False,
                "message": eligibility["reason"],
            }

        order = eligibility["order"]
        refund_amount = amount if amount else order["total"]

        # Mock refund processing
        refund_id = f"REF-{random.randint(1000, 9999)}"

        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund_id,
            "refund_amount": refund_amount,
            "order_id": order_id,
            "estimated_days": random.randint(5, 10),
        }


# Global instance
order_api = MockOrderAPI()
