"""
Condition checkers for discount rules using Chain of Responsibility pattern.

This design satisfies:
- Single Responsibility: Each checker handles ONE condition type
- Open-Closed Principle: Add new conditions by creating new classes, no modification needed
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Session, select, func

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem
    from app.models.user import User
    from app.models.discount import DiscountRule


class ConditionChecker(ABC):
    """Base class for discount condition checkers."""

    @abstractmethod
    def check(
        self,
        order: "Order",
        user: "User",
        conditions: dict,
        session: Session
    ) -> tuple[bool, str]:
        """
        Check if condition is satisfied.

        Returns:
            (is_satisfied: bool, reason: str)
            - If True: ("", reason can be empty)
            - If False: (False, "reason why it failed")
        """
        pass


class MinPurchasesChecker(ConditionChecker):
    """Check if user has minimum number of completed purchases."""

    def check(self, order: "Order", user: "User", conditions: dict, session: Session) -> tuple[bool, str]:
        if "min_purchases" not in conditions:
            return True, ""  # Condition not applicable, skip

        from app.models.order import Order, OrderStatus

        min_purchases = conditions["min_purchases"]
        status_filter = conditions.get("status_filter", ["COMPLETED"])

        # Convert status strings to enum values
        status_enums = [OrderStatus(s) for s in status_filter]

        # Count completed orders (excluding current order)
        query = select(func.count(Order.id)).where(
            Order.user_id == user.id,
            Order.status.in_(status_enums),
            Order.id != order.id
        )

        result = session.exec(query)
        completed_count = result.one()

        if completed_count < min_purchases:
            return False, f"User has {completed_count} purchases, needs {min_purchases}"

        return True, ""


class MinCartValueChecker(ConditionChecker):
    """Check if cart meets minimum value requirement."""

    def check(self, order: "Order", user: "User", conditions: dict, session: Session) -> tuple[bool, str]:
        if "min_cart_value" not in conditions:
            return True, ""  # Condition not applicable

        min_cart_value = conditions["min_cart_value"]

        if order.subtotal < Decimal(str(min_cart_value)):
            return False, f"Cart value ₹{order.subtotal} is below minimum ₹{min_cart_value}"

        return True, ""


class CategoryConditionChecker(ConditionChecker):
    """Check category-specific conditions (category_id, min_quantity)."""

    def check(self, order: "Order", user: "User", conditions: dict, session: Session) -> tuple[bool, str]:
        # Only apply for category-specific conditions
        if "category_id" not in conditions:
            return True, ""  # Not a category discount

        # Defensive: Validate required field exists
        category_id = conditions.get("category_id")
        if not category_id:
            raise ValueError("Category discount missing required 'category_id' in conditions")

        try:
            category_uuid = UUID(category_id)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid category_id format '{category_id}'. Expected UUID.") from e

        min_quantity = conditions.get("min_quantity", 1)

        # Sum quantities for items in target category
        total_quantity = sum(
            item.quantity
            for item in order.items
            if item.product_category_id == category_uuid
        )

        if total_quantity < min_quantity:
            return False, f"Need {min_quantity} items from category, found {total_quantity}"

        return True, ""


class ProductConditionChecker(ConditionChecker):
    """Check product-specific conditions (product_ids, min_quantity)."""

    def check(self, order: "Order", user: "User", conditions: dict, session: Session) -> tuple[bool, str]:
        # Only apply for product-specific conditions
        if "product_ids" not in conditions:
            return True, ""  # Not a product discount

        # Defensive: Validate required field exists
        product_ids = conditions.get("product_ids", [])
        if not product_ids:
            raise ValueError("Product discount missing or empty 'product_ids' in conditions")

        # Check if any order items match target products
        order_product_ids = {str(item.product_id) for item in order.items}
        if not any(pid in order_product_ids for pid in product_ids):
            return False, "No matching products in cart"

        return True, ""


class ConditionChain:
    """
    Chain of Responsibility for condition checking.

    This satisfies Open-Closed Principle:
    - To add new conditions: Create new ConditionChecker class and register it
    - No need to modify existing checkers
    """

    def __init__(self):
        self.checkers: list[ConditionChecker] = [
            MinPurchasesChecker(),
            MinCartValueChecker(),
            CategoryConditionChecker(),
            ProductConditionChecker(),
        ]

    def register_checker(self, checker: ConditionChecker):
        """Add a new condition checker to the chain (for extensions)."""
        self.checkers.append(checker)

    def check_all(
        self,
        order: "Order",
        user: "User",
        conditions: dict,
        session: Session
    ) -> tuple[bool, str]:
        """
        Run all condition checks in sequence.

        Returns:
            (all_passed: bool, failure_reason: str)
            - If all pass: (True, "")
            - If any fails: (False, "reason from first failed checker")
        """
        for checker in self.checkers:
            passed, reason = checker.check(order, user, conditions, session)
            if not passed:
                return False, reason

        return True, ""


# Global condition chain instance
_condition_chain = ConditionChain()


def get_condition_chain() -> ConditionChain:
    """Get the global condition chain instance."""
    return _condition_chain
