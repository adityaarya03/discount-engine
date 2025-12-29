from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Session, select, func

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem
    from app.models.user import User
    from app.models.discount import DiscountRule


class DiscountStrategy(ABC):
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
        """
        Calculate discount amount.
        """
        pass
    
class PercentageDiscountStrategy(DiscountStrategy):
    def is_applicable(self, order: "Order", user: "User") -> bool:
        min_value = Decimal(str(self.config["conditions"]["min_cart_value"]))
        return order.subtotal >= min_value
    
    def calculate(self, order:"Order", user:"User") -> dict:
        percentage = Decimal(str(self.config["action"]["percentage"]))
        discount_amount = (order.subtotal * percentage / 100).quantize(Decimal("0.01"))
        
        return {
            "discount_amount": discount_amount,
            "calculation_details":{
                "type":"percentage",
                "original_amount": float(order.subtotal),
                "percentage": float(percentage),
                "discount_amount": float(discount_amount),
                "condition_met": f"Cart value ₹{order.subtotal} >= ₹{self.config['conditions']['min_cart_value']}"
            }
        }
        
class FlatLoyaltyDiscountStrategy(DiscountStrategy):
    """
    Flat discount for loyal customers after N purchases.
    
    Config example:
    {
        "conditions": {
            "min_purchases": 5,
            "status_filter": ["COMPLETED"]
        },
        "action": {"flat_amount": 500}
    }
    """
    
    def is_applicable(self, order: "Order", user: "User") -> bool:
        from app.models.order import Order, OrderStatus
        
        # Count completed orders (excluding current order)
        min_purchases = self.config["conditions"]["min_purchases"]
        status_filter = self.config["conditions"].get("status_filter", ["COMPLETED"])
        
        # Convert status strings to enum values
        status_enums = [OrderStatus(s) for s in status_filter]
        
        query = select(func.count(Order.id)).where(
            Order.user_id == user.id,
            Order.status.in_(status_enums),
            Order.id != order.id  # Exclude current order
        )
        
        result = self.session.exec(query)
        completed_count = result.one()
        
        return completed_count >= min_purchases
    
    def calculate(self, order: "Order", user: "User") -> dict:
        flat_amount = Decimal(str(self.config["action"]["flat_amount"]))
        
        # Cap discount at order subtotal (can't be negative)
        discount_amount = min(flat_amount, order.subtotal).quantize(Decimal("0.01"))
        
        return {
            "discount_amount": discount_amount,
            "calculation_details": {
                "type": "flat_loyalty",
                "flat_amount": float(flat_amount),
                "discount_amount": float(discount_amount),
                "condition_met": f"User has completed {self.config['conditions']['min_purchases']} eligible purchases"
            }
        }
        
class CategoryBasedDiscountStrategy(DiscountStrategy):
    """
    Percentage discount on specific category items.
    
    Config example:
    {
        "conditions": {
            "category_id": "uuid-here",
            "min_quantity": 3
        },
        "action": {"percentage": 5}
    }
    """
    
    def is_applicable(self, order: "Order", user: "User") -> bool:
        category_id = UUID(self.config["conditions"]["category_id"])
        min_quantity = self.config["conditions"]["min_quantity"]
        
        # Sum quantities for items in target category
        # Using denormalized category_id from order_items for performance
        total_quantity = sum(
            item.quantity 
            for item in order.items 
            if item.product_category_id == category_id
        )
        
        return total_quantity >= min_quantity
    
    def calculate(self, order: "Order", user: "User") -> dict:
        category_id = UUID(self.config["conditions"]["category_id"])
        percentage = Decimal(str(self.config["action"]["percentage"]))
        
        # Calculate discount only on category items
        category_items_total = sum(
            item.subtotal 
            for item in order.items 
            if item.product_category_id == category_id
        )
        
        discount_amount = (Decimal(str(category_items_total)) * percentage / 100).quantize(Decimal("0.01"))
        
        affected_items = [
            str(item.id) 
            for item in order.items 
            if item.product_category_id == category_id
        ]
        
        return {
            "discount_amount": discount_amount,
            "calculation_details": {
                "type": "category_based",
                "category_id": str(category_id),
                "category_items_total": float(category_items_total),
                "percentage": float(percentage),
                "discount_amount": float(discount_amount),
                "items_affected": affected_items
            }
        }


# Strategy registry for dynamic dispatch
STRATEGY_MAP = {
    "PERCENTAGE": PercentageDiscountStrategy,
    "FLAT_LOYALTY": FlatLoyaltyDiscountStrategy,
    "CATEGORY_BASED": CategoryBasedDiscountStrategy,
}