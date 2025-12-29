"""
Discount models: DiscountRule (with JSONB config) and AppliedDiscount (audit trail).
"""
from typing import Optional, TYPE_CHECKING, Any
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"           # 10% off on cart > ₹5000
    FLAT_LOYALTY = "FLAT_LOYALTY"       # ₹500 off after 5 purchases
    CATEGORY_BASED = "CATEGORY_BASED"   # 5% off on 3+ Electronics items


class DiscountRule(SQLModel, TimestampMixin, table=True):
    """
    Discount rule with flexible JSONB configuration.
    
    This design allows admins to create new discount rules without code changes.
    
    Attributes:
        id: Unique identifier
        name: Offer name
        discount_type: Type of discount (enum)
        priority: For stacking - lower number applies first
        is_active: Whether rule is currently enabled
        is_stackable: Whether this discount can combine with others
        config: JSONB field storing conditions and actions
        
    Example configs:
    
    1. Percentage discount:
    {
        "conditions": {"min_cart_value": 5000},
        "action": {"percentage": 10}
    }
    
    2. Flat loyalty discount:
    {
        "conditions": {"min_purchases": 5, "status_filter": ["COMPLETED"]},
        "action": {"flat_amount": 500}
    }
    
    3. Category-based discount:
    {
        "conditions": {
            "category_id": "uuid-here",
            "min_quantity": 3
        },
        "action": {"percentage": 5}
    }
    """
    __tablename__ = "discount_rules"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    discount_type: DiscountType = Field(index=True)
    
    priority: int = Field(default=0, index=True)  # Lower = applies first
    is_active: bool = Field(default=True, index=True)
    is_stackable: bool = Field(default=False)
    
    # THE POWER MOVE: JSONB for flexibility
    # Using Column with JSON type for proper JSONB support in PostgreSQL
    config: dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Optional date range
    start_date: Optional[str] = Field(default=None)  # ISO date string
    end_date: Optional[str] = Field(default=None)
    
    # Relationships
    applied_to_orders: list["AppliedDiscount"] = Relationship(back_populates="discount_rule")
    
    def __repr__(self) -> str:
        return f"<DiscountRule {self.name} ({self.discount_type.value})>"


class AppliedDiscount(SQLModel, table=True):
    """
    Audit trail of discounts applied to orders.
    
    This table enables:
    1. Showing discount breakdown to users
    2. Analytics on discount usage
    3. Historical record for compliance
    
    Attributes:
        id: Unique identifier
        order_id: Foreign key to order
        discount_rule_id: Foreign key to discount rule
        discount_amount: Calculated discount amount
        calculation_details: JSONB storing how discount was calculated
    """
    __tablename__ = "applied_discounts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    discount_rule_id: UUID = Field(foreign_key="discount_rules.id")
    
    discount_amount: Decimal = Field(max_digits=10, decimal_places=2)
    
    # Store calculation breakdown for transparency
    calculation_details: dict[str, Any] = Field(sa_column=Column(JSON))
    # Example: {
    #   "original_amount": 6000,
    #   "discount_rate": 0.1,
    #   "items_affected": ["item_id_1", "item_id_2"]
    # }
    
    created_at: str = Field(default_factory=lambda: str(uuid4()))  # Timestamp
    
    # Relationships
    order: "Order" = Relationship(back_populates="applied_discounts")
    discount_rule: DiscountRule = Relationship(back_populates="applied_to_orders")
    
    def __repr__(self) -> str:
        return f"<AppliedDiscount ₹{self.discount_amount} on Order {self.order_id}>"