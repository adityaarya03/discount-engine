"""
Generic discount strategy for all discount types.

This module provides a single GenericDiscountStrategy that handles all combinations
of scope (CART, CATEGORY, PRODUCT) and value_type (PERCENTAGE, FLAT, BOGO).
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Session

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem
    from app.models.user import User
    from app.models.discount import DiscountRule


class DiscountStrategy(ABC):
    """Base class for discount strategies."""

    def __init__(self, rule: "DiscountRule", session: Session):
        self.rule = rule
        self.session = session
        self.config = rule.config

    @abstractmethod
    def is_applicable(self, order: "Order", user: "User") -> bool:
        """Check if discount can be applied to this order."""
        pass

    @abstractmethod
    def calculate(self, order: "Order", user: "User") -> dict:
        """Calculate discount amount."""
        pass

    def _apply_max_cap(self, discount_amount: Decimal) -> Decimal:
        """
        Apply max_discount_amount cap if specified in config.
        This is a shared utility for all strategies.
        """
        max_cap = self.config.get("max_discount_amount")
        if max_cap is not None:
            max_cap_decimal = Decimal(str(max_cap))
            return min(discount_amount, max_cap_decimal)
        return discount_amount


class GenericDiscountStrategy(DiscountStrategy):
    """
    Universal strategy that handles all scope + value_type combinations.

    Supported combinations:
    - CART + PERCENTAGE: % off entire cart (e.g., 10% off cart > ₹5000)
    - CART + FLAT: Flat discount on cart (e.g., ₹500 off cart > ₹2000)
    - CATEGORY + PERCENTAGE: % off category items (e.g., 15% off Electronics)
    - CATEGORY + FLAT: Flat discount on category (e.g., ₹300 off Fashion)
    - PRODUCT + PERCENTAGE: % off specific products
    - PRODUCT + FLAT: Flat discount on specific products
    """

    def is_applicable(self, order: "Order", user: "User") -> bool:
        """
        Check if discount is applicable based on scope and conditions.

        Uses Chain of Responsibility pattern for condition checking.
        This satisfies:
        - Single Responsibility: Delegates to specialized condition checkers
        - Open-Closed Principle: Add new conditions by registering new checkers

        Returns:
            True if all conditions are met
        """
        from app.services.discount_engine.conditions import get_condition_chain

        conditions = self.config.get("conditions", {})

        # Delegate to condition chain for validation
        condition_chain = get_condition_chain()
        all_passed, failure_reason = condition_chain.check_all(
            order=order,
            user=user,
            conditions=conditions,
            session=self.session
        )

        return all_passed

    def calculate(self, order: "Order", user: "User") -> dict:
        """
        Calculate discount amount based on scope and value_type.

        Returns:
            Dictionary with discount_amount and calculation_details
        """
        from app.models.discount import DiscountScope, DiscountValueType

        # Determine calculation base (what amount to apply discount to)
        if self.rule.scope == DiscountScope.CART:
            base_amount = order.subtotal
            items_affected = [str(item.id) for item in order.items]

        elif self.rule.scope == DiscountScope.CATEGORY:
            category_id = UUID(self.config["conditions"]["category_id"])
            base_amount = sum(
                item.subtotal
                for item in order.items
                if item.product_category_id == category_id
            )
            items_affected = [
                str(item.id)
                for item in order.items
                if item.product_category_id == category_id
            ]

        elif self.rule.scope == DiscountScope.PRODUCT:
            product_ids = self.config["conditions"]["product_ids"]
            base_amount = sum(
                item.subtotal
                for item in order.items
                if str(item.product_id) in product_ids
            )
            items_affected = [
                str(item.id)
                for item in order.items
                if str(item.product_id) in product_ids
            ]

        else:
            # Unknown scope
            base_amount = Decimal("0.00")
            items_affected = []

        # Calculate discount based on value_type
        if self.rule.value_type == DiscountValueType.PERCENTAGE:
            discount_amount = (Decimal(str(base_amount)) * self.rule.value / 100).quantize(
                Decimal("0.01")
            )
            max_cap = self.config.get("max_discount_amount")
            capped_amount = self._apply_max_cap(discount_amount)

            return {
                "discount_amount": capped_amount,
                "calculation_details": {
                    "scope": self.rule.scope.value,
                    "value_type": "percentage",
                    "base_amount": float(base_amount),
                    "percentage": float(self.rule.value),
                    "calculated_discount": float(discount_amount),
                    "discount_amount": float(capped_amount),
                    "max_cap": float(max_cap) if max_cap else None,
                    "cap_applied": capped_amount < discount_amount,
                    "items_affected": items_affected,
                },
            }

        elif self.rule.value_type == DiscountValueType.FLAT:
            # Cap flat discount at base_amount (can't make it negative)
            discount_amount = min(self.rule.value, Decimal(str(base_amount))).quantize(
                Decimal("0.01")
            )

            return {
                "discount_amount": discount_amount,
                "calculation_details": {
                    "scope": self.rule.scope.value,
                    "value_type": "flat",
                    "base_amount": float(base_amount),
                    "flat_amount": float(self.rule.value),
                    "discount_amount": float(discount_amount),
                    "capped_at_base": discount_amount < self.rule.value,
                    "items_affected": items_affected,
                },
            }

        elif self.rule.value_type == DiscountValueType.BOGO:
            # BOGO implementation (future)
            # For now, return zero discount
            return {
                "discount_amount": Decimal("0.00"),
                "calculation_details": {
                    "scope": self.rule.scope.value,
                    "value_type": "bogo",
                    "message": "BOGO discounts not yet implemented",
                },
            }

        else:
            # Unknown value_type
            return {
                "discount_amount": Decimal("0.00"),
                "calculation_details": {
                    "error": f"Unknown value_type: {self.rule.value_type}",
                },
            }


# Strategy registry for dynamic dispatch
# With generic design, we only need one strategy for all types
STRATEGY_MAP = {
    "CART:PERCENTAGE": GenericDiscountStrategy,
    "CART:FLAT": GenericDiscountStrategy,
    "CATEGORY:PERCENTAGE": GenericDiscountStrategy,
    "CATEGORY:FLAT": GenericDiscountStrategy,
    "PRODUCT:PERCENTAGE": GenericDiscountStrategy,
    "PRODUCT:FLAT": GenericDiscountStrategy,
    "CART:BOGO": GenericDiscountStrategy,  # Future
    "CATEGORY:BOGO": GenericDiscountStrategy,  # Future
    "PRODUCT:BOGO": GenericDiscountStrategy,  # Future
}


def get_strategy(rule: "DiscountRule", session: Session) -> GenericDiscountStrategy:
    """
    Get appropriate strategy for a discount rule.

    Args:
        rule: The discount rule
        session: Database session

    Returns:
        GenericDiscountStrategy instance
    """
    # All rules now use GenericDiscountStrategy
    return GenericDiscountStrategy(rule, session)
