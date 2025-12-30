"""
Main discount engine logic

Handles:
- Loading active discount rules
- Applying discount strategies
- Stacking logic with coupon priority and loyalty gates
- Coupon code validation
"""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.discount import DiscountRule, AppliedDiscount
from app.services.discount_engine.strategies import get_strategy


if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class DiscountEngine:

    def __init__(self, session: Session):
        self.session = session

    def get_active_discount_rules(self, coupon_code: Optional[str] = None) -> list[DiscountRule]:
        """
        Get active discount rules.

        Args:
            coupon_code: Optional coupon code. If provided, only that rule is fetched.
                        If None, only auto-apply rules (coupon_code is NULL) are fetched.

        Returns:
            List of active discount rules sorted by priority
        """
        query = (
            select(DiscountRule)
            .where(DiscountRule.is_active == True)
        )

        if coupon_code:
            # User entered a coupon code - fetch that specific rule
            query = query.where(DiscountRule.coupon_code == coupon_code)
        else:
            # No coupon - fetch auto-apply rules only (coupon_code is NULL)
            query = query.where(DiscountRule.coupon_code == None)

        query = query.order_by(DiscountRule.priority.asc())
        result = self.session.exec(query)
        return result.all()

    def apply_discounts(self, order: "Order", user: "User", coupon_code: Optional[str] = None) -> dict:
        """
        Apply discounts to an order with proper stacking logic.

        Stacking Rules:
        1. If user enters a coupon:
           - Apply coupon first
           - If coupon is stackable, check for stackable auto-apply discounts
           - Auto-apply stackable discounts require loyalty if config.requires_loyalty=true
        2. If no coupon:
           - If user is loyalty member: stack all stackable auto-apply discounts
           - If not loyalty member: choose best single auto-apply discount

        Args:
            order: The order to apply discounts to
            user: The user placing the order
            coupon_code: Optional coupon code entered by user

        Returns:
            Dictionary with total_discount and applied_rules

        Raises:
            HTTPException: If coupon code is invalid or inactive
        """
        # Validate coupon code if provided
        coupon_discount = None
        if coupon_code:
            coupon_rules = self.get_active_discount_rules(coupon_code=coupon_code)
            if not coupon_rules:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid or inactive coupon code: {coupon_code}"
                )

            # Evaluate coupon discount
            coupon_rule = coupon_rules[0]
            strategy = get_strategy(coupon_rule, self.session)

            if strategy.is_applicable(order, user):
                result = strategy.calculate(order, user)
                coupon_discount = {
                    "rule": coupon_rule,
                    "discount_amount": result["discount_amount"],
                    "calculation_details": result["calculation_details"]
                }

        # Get auto-apply discounts
        auto_apply_rules = self.get_active_discount_rules(coupon_code=None)
        auto_apply_discounts = []

        for rule in auto_apply_rules:
            strategy = get_strategy(rule, self.session)

            if strategy.is_applicable(order, user):
                result = strategy.calculate(order, user)
                auto_apply_discounts.append({
                    "rule": rule,
                    "discount_amount": result["discount_amount"],
                    "calculation_details": result["calculation_details"]
                })

        # Apply stacking logic
        final_discounts = self._handle_stacking(
            coupon_discount=coupon_discount,
            auto_apply_discounts=auto_apply_discounts,
            user=user
        )

        if not final_discounts:
            return {
                "total_discount": Decimal("0.00"),
                "applied_rules": []
            }

        # Calculate total discount
        total_discount = sum(d["discount_amount"] for d in final_discounts)

        # Update order amounts
        order.discount_amount = total_discount
        order.total_amount = order.subtotal - total_discount + order.tax_amount

        # Record applied discounts in database
        applied_rules = []
        for discount in final_discounts:
            applied = AppliedDiscount(
                order_id=order.id,
                discount_rule_id=discount["rule"].id,
                discount_amount=discount["discount_amount"],
                calculation_details=discount["calculation_details"]
            )
            self.session.add(applied)
            applied_rules.append({
                "rule_name": discount["rule"].name,
                "rule_type": f"{discount['rule'].scope.value}:{discount['rule'].value_type.value}",
                "discount_amount": float(discount["discount_amount"]),
                "details": discount["calculation_details"]
            })

        self.session.commit()

        return {
            "total_discount": float(total_discount),
            "applied_rules": applied_rules
        }

    def _handle_stacking(
        self,
        coupon_discount: Optional[dict],
        auto_apply_discounts: list,
        user: "User"
    ) -> list:
        """
        Handle discount stacking logic with coupon priority and loyalty gates.

        Logic:
        1. If coupon exists:
           a. If coupon is non-stackable: return [coupon] only
           b. If coupon is stackable:
              - Add coupon
              - Filter auto-apply for stackable discounts
              - Check requires_loyalty flag for each auto-apply discount
              - Add auto-apply discounts that pass loyalty check

        2. If no coupon:
           a. If user is loyalty member:
              - Stack all stackable auto-apply discounts
           b. If not loyalty member:
              - Return best single discount (highest discount_amount)

        Args:
            coupon_discount: Coupon discount dict (or None)
            auto_apply_discounts: List of applicable auto-apply discounts
            user: The user placing the order

        Returns:
            List of discounts to apply
        """
        final_discounts = []

        # Check if user is loyalty member
        is_loyalty_member = user.is_loyalty_member(self.session)

        # CASE 1: User entered a coupon
        if coupon_discount:
            coupon_rule = coupon_discount["rule"]

            if not coupon_rule.is_stackable:
                # Non-stackable coupon: ONLY apply coupon, ignore all auto-apply
                return [coupon_discount]

            else:
                # Stackable coupon: Apply coupon + eligible auto-apply discounts
                final_discounts.append(coupon_discount)

                # Filter auto-apply for stackable discounts
                for discount in auto_apply_discounts:
                    rule = discount["rule"]

                    # Only stackable auto-apply discounts can combine with coupon
                    if not rule.is_stackable:
                        continue

                    # Check if loyalty membership required for stacking
                    loyalty_stacking_only = rule.config.get("loyalty_stacking_only", False)
                    if loyalty_stacking_only and not is_loyalty_member:
                        # This discount can only stack for loyalty members
                        continue

                    # Passed all checks - add this discount
                    final_discounts.append(discount)

                return final_discounts

        # CASE 2: No coupon - auto-apply only
        else:
            # Separate stackable and non-stackable discounts
            stackable_for_user = []
            non_stackable = []

            for discount in auto_apply_discounts:
                rule = discount["rule"]

                if rule.is_stackable:
                    # Check if loyalty membership required for stacking
                    loyalty_stacking_only = rule.config.get("loyalty_stacking_only", False)

                    if loyalty_stacking_only:
                        # Only stack if user is loyalty member
                        if is_loyalty_member:
                            stackable_for_user.append(discount)
                    else:
                        # Can stack for any user
                        stackable_for_user.append(discount)
                else:
                    # Non-stackable discount
                    non_stackable.append(discount)

            # If user has stackable discounts available, compare with best single
            if stackable_for_user:
                # Calculate total stackable amount
                total_stackable = sum(d["discount_amount"] for d in stackable_for_user)

                # Find best single discount from ALL applicable discounts
                best_single = max(auto_apply_discounts, key=lambda x: x["discount_amount"])

                # Per assignment: "ensure the customer gets the best possible benefit"
                # Compare stacking vs best single
                if total_stackable >= best_single["discount_amount"]:
                    # Stacking is better - return all stackable discounts
                    return stackable_for_user
                else:
                    # Best single discount is better
                    return [best_single]

            # No stackable discounts available - return best single discount
            if auto_apply_discounts:
                best_discount = max(auto_apply_discounts, key=lambda x: x["discount_amount"])
                return [best_discount]

            return []
