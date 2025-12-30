"""
Discount models: DiscountRule (with JSONB config) and AppliedDiscount (audit trail).
"""
from typing import Optional, TYPE_CHECKING, Any
from uuid import UUID, uuid4
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class DiscountScope(str, Enum):
    """Where the discount applies."""
    CART = "CART"           # Entire cart
    CATEGORY = "CATEGORY"   # Specific product category
    PRODUCT = "PRODUCT"     # Specific products


class DiscountValueType(str, Enum):
    """How the discount value is calculated."""
    PERCENTAGE = "PERCENTAGE"  # e.g., 10% off
    FLAT = "FLAT"             # e.g., ₹500 off
    BOGO = "BOGO"             # Buy one get one (future)


class DiscountRule(SQLModel, TimestampMixin, table=True):
    """
    Generic discount rule with scope + value_type separation.

    Attributes:
        id: Unique identifier
        name: Offer name
        scope: Where discount applies (CART, CATEGORY, PRODUCT)
        value_type: How value is calculated (PERCENTAGE, FLAT, BOGO)
        value: The discount amount/percentage
        priority: For stacking - lower number applies first
        is_active: Whether rule is currently enabled
        is_stackable: Whether this discount can combine with others
        coupon_code: NULL = auto-apply, non-NULL = manual coupon entry
        config: JSONB field storing conditions and additional settings

    Example configs:

    1. Cart-level 10% discount with max cap (stackable for all):
    {
        "conditions": {"min_cart_value": 5000},
        "max_discount_amount": 1000,
        "loyalty_stacking_only": false
    }

    2. Category-level 5% discount (stackable only for loyalty members):
    {
        "conditions": {
            "category_id": "uuid-here",
            "min_quantity": 3
        },
        "max_discount_amount": 500,
        "loyalty_stacking_only": true
    }

    3. Cart-level flat ₹500 coupon (stackable for all):
    {
        "conditions": {"min_cart_value": 1000},
        "loyalty_stacking_only": false
    }
    """
    __tablename__ = "discount_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)

    # Generic design: scope + value_type + value
    scope: DiscountScope = Field(index=True)
    value_type: DiscountValueType = Field(index=True)
    value: Decimal = Field(max_digits=10, decimal_places=2, description="Discount amount (percentage or flat)")
    
    priority: int = Field(default=0, index=True)  # Lower = applies first
    is_active: bool = Field(default=True, index=True)
    is_stackable: bool = Field(default=False)

    # PRODUCTION ENHANCEMENT: Coupon code support
    # NULL = auto-apply discount, non-NULL = manual coupon entry
    coupon_code: Optional[str] = Field(
        default=None,
        max_length=50,
        unique=True,
        index=True,
        description="Coupon code for manual entry (e.g., 'SAVE20'). NULL for auto-apply."
    )

    # THE POWER MOVE: JSONB for flexibility
    # Using Column with JSON type for proper JSONB support in PostgreSQL
    config: dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Optional date range
    start_date: Optional[str] = Field(default=None)  # ISO date string
    end_date: Optional[str] = Field(default=None)
    
    # Relationships
    applied_to_orders: list["AppliedDiscount"] = Relationship(back_populates="discount_rule")
    
    def __repr__(self) -> str:
        return f"<DiscountRule {self.name} ({self.scope.value}:{self.value_type.value})>"


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
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    order: "Order" = Relationship(back_populates="applied_discounts")
    discount_rule: DiscountRule = Relationship(back_populates="applied_to_orders")
    
    def __repr__(self) -> str:
        return f"<AppliedDiscount ₹{self.discount_amount} on Order {self.order_id}>"