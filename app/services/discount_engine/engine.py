"""
Main discount engine logic

Handles:
- Loading active discount rules
- Applying discount strategies
- Stacking logic
"""
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlmodel import Session, select
from app.models.discount import DiscountRule,AppliedDiscount, DiscountType
from app.services.discount_engine.strategies import STRATEGY_MAP


if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User
    
class DiscountEngine:
    
    def __init__ (self, sesson:Session):
        self.session = Session
        
    def get_active_discount_rules(self) -> list[DiscountRule]:
        
        query = (
            select(DiscountRule)
            .where(DiscountRule.is_active == True)
            .order_by(DiscountRule.priority.asc())
        )
        result = self.session.exec (query)
        return result.all()
    
    def apply_discounts(self, order: "Order", user:"User") -> dict:
        
        rules = self.get_active_discount_rules()
        applicable_discounts = []
        for rule in rules:
            strategy_class = STRATEGY_MAP.get(rule.discount_type.value)
            if not strategy_class:
                continue
            
            strategy = strategy_class(rule, self.session)
            
            if strategy.is_applicable(order, user):
                result = strategy.calculate(order, user)
                applicable_discounts.append({
                    "rule": rule,
                    "discount_amount": result["discount_amount"],
                    "calculation_details": result["calculation_details"]
                })
        
        if not applicable_discounts:
            return {
                "total_discount": Decimal("0.00"),
                "applied_rules": []
            }
        
        # Handle stacking logic
        final_discounts = self._handle_stacking(applicable_discounts)
        
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
                "rule_type": discount["rule"].discount_type.value,
                "discount_amount": float(discount["discount_amount"]),
                "details": discount["calculation_details"]
            })
        
        self.session.commit()
        
        return {
            "total_discount": float(total_discount),
            "applied_rules": applied_rules
        }
    
    def _handle_stacking(self, applicable_discounts: list) -> list:
        """
        Handle discount stacking logic.
        
        Strategy (as per brownie points):
        - If loyalty discount applies, it can stack with category discounts
        - Percentage and Flat discounts don't stack - choose the best one
        
        Returns:
            List of discounts to apply
        """
        if not applicable_discounts:
            return []
        
        # Separate discounts by type
        loyalty_discounts = [d for d in applicable_discounts if d["rule"].discount_type == DiscountType.FLAT_LOYALTY]
        category_discounts = [d for d in applicable_discounts if d["rule"].discount_type == DiscountType.CATEGORY_BASED]
        percentage_discounts = [d for d in applicable_discounts if d["rule"].discount_type == DiscountType.PERCENTAGE]
        
        final_discounts = []
        
        # Loyalty + Category can stack
        if loyalty_discounts:
            final_discounts.append(max(loyalty_discounts, key=lambda x: x["discount_amount"]))
        
        if category_discounts:
            # Sum all category discounts (they apply to different categories)
            final_discounts.extend(category_discounts)
        
        # For percentage vs flat (non-loyalty), choose the best
        if percentage_discounts:
            non_loyalty_options = percentage_discounts
            if not loyalty_discounts:  # If no loyalty, flat discounts compete with percentage
                non_loyalty_flat = [d for d in applicable_discounts if d["rule"].discount_type == DiscountType.FLAT_LOYALTY]
                non_loyalty_options.extend(non_loyalty_flat)
            
            if non_loyalty_options and not loyalty_discounts:
                # Choose best single discount
                best_discount = max(non_loyalty_options, key=lambda x: x["discount_amount"])
                final_discounts.append(best_discount)
            elif percentage_discounts and loyalty_discounts:
                # Loyalty already added, check if percentage is stackable
                for p_discount in percentage_discounts:
                    if p_discount["rule"].is_stackable:
                        final_discounts.append(p_discount)
        
        return final_discounts