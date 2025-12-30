"""
Pydantic schemas for discount rule requests/responses.
"""
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer, model_validator
from typing import Optional, Any, Union
from app.models.discount import DiscountScope, DiscountValueType


# ============================================
# CONDITION MODELS (Type-Safe, Validated)
# ============================================

class CartConditions(BaseModel):
    """
    Conditions for CART scope discounts.

    Examples:
    - 10% off cart > ₹5000: {"min_cart_value": 5000}
    - ₹500 after 5 purchases: {"min_purchases": 5, "status_filter": ["COMPLETED"]}
    """
    min_cart_value: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum cart subtotal in ₹ (optional)"
    )
    min_purchases: Optional[int] = Field(
        None,
        ge=1,
        description="Minimum completed orders required (optional, for loyalty rewards)"
    )
    status_filter: Optional[list[str]] = Field(
        None,
        description="Order statuses to count (e.g., ['COMPLETED']). Used with min_purchases."
    )


class CategoryConditions(BaseModel):
    """
    Conditions for CATEGORY scope discounts.

    Examples:
    - 5% off 3+ Electronics: {"category_id": "uuid", "min_quantity": 3}
    - 15% off any Electronics: {"category_id": "uuid", "min_quantity": 1}
    """
    category_id: UUID = Field(
        description="Target category UUID (required)"
    )
    min_quantity: int = Field(
        1,
        ge=1,
        description="Minimum items from this category (default: 1)"
    )


class ProductConditions(BaseModel):
    """
    Conditions for PRODUCT scope discounts.

    Examples:
    - 20% off specific products: {"product_ids": ["uuid1", "uuid2"]}
    """
    product_ids: list[UUID] = Field(
        min_length=1,
        description="List of target product UUIDs (at least 1 required)"
    )
    min_quantity: int = Field(
        1,
        ge=1,
        description="Minimum quantity of matching products (default: 1)"
    )


# Union type for conditions based on scope
DiscountConditions = Union[CartConditions, CategoryConditions, ProductConditions]


class DiscountRuleCreate(BaseModel):
    """
    Schema for creating a discount rule with type-safe conditions.

    The API validates conditions based on scope:
    - CART: CartConditions (min_cart_value, min_purchases)
    - CATEGORY: CategoryConditions (category_id, min_quantity)
    - PRODUCT: ProductConditions (product_ids, min_quantity)

    Example 1 - CART-level PERCENTAGE with max cap:
    {
        "name": "Summer Sale 15% off",
        "scope": "CART",
        "value_type": "PERCENTAGE",
        "value": 15.0,
        "conditions": {"min_cart_value": 3000},
        "max_discount_amount": 500,
        "requires_loyalty": false
    }

    Example 2 - CATEGORY-level PERCENTAGE:
    {
        "name": "Electronics Flash Sale",
        "scope": "CATEGORY",
        "value_type": "PERCENTAGE",
        "value": 10.0,
        "conditions": {
            "category_id": "uuid-here",
            "min_quantity": 2
        },
        "max_discount_amount": 300
    }

    Example 3 - CART-level FLAT loyalty reward:
    {
        "name": "Rewarded Buyer ₹500",
        "scope": "CART",
        "value_type": "FLAT",
        "value": 500.0,
        "conditions": {
            "min_purchases": 5,
            "status_filter": ["COMPLETED"]
        }
    }
    """
    name: str = Field(min_length=1, max_length=255)
    scope: DiscountScope = Field(description="Where discount applies (CART, CATEGORY, PRODUCT)")
    value_type: DiscountValueType = Field(description="How value is calculated (PERCENTAGE, FLAT, BOGO)")
    value: Decimal = Field(description="Discount amount (percentage or flat)")

    # Type-safe conditions based on scope
    conditions: DiscountConditions = Field(
        description="Typed conditions - structure depends on scope (CartConditions | CategoryConditions | ProductConditions)"
    )

    # Additional config fields
    max_discount_amount: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum discount cap in ₹ (for PERCENTAGE discounts)"
    )
    loyalty_stacking_only: bool = Field(
        False,
        description="If true and is_stackable=true, this discount can only stack when user is a loyalty member (10+ orders). If false, discount can stack for any user."
    )

    priority: int = Field(default=0, description="Lower number = higher priority")
    is_active: bool = Field(default=True)
    is_stackable: bool = Field(default=False, description="Can combine with other discounts")
    coupon_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Coupon code for manual entry. NULL for auto-apply discounts."
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @model_validator(mode='after')
    def validate_conditions_match_scope(self):
        """Validate that conditions type matches the scope."""
        scope_to_conditions = {
            DiscountScope.CART: CartConditions,
            DiscountScope.CATEGORY: CategoryConditions,
            DiscountScope.PRODUCT: ProductConditions,
        }

        expected_type = scope_to_conditions.get(self.scope)
        if expected_type and not isinstance(self.conditions, expected_type):
            raise ValueError(
                f"Scope '{self.scope.value}' requires {expected_type.__name__} but got {type(self.conditions).__name__}"
            )

        return self

    def to_db_config(self) -> dict[str, Any]:
        """Convert Pydantic model to database JSONB config format."""
        return {
            "conditions": self.conditions.model_dump(exclude_none=True),
            "max_discount_amount": self.max_discount_amount,
            "loyalty_stacking_only": self.loyalty_stacking_only,
        }


class DiscountRuleUpdate(BaseModel):
    """Schema for updating a discount rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scope: Optional[DiscountScope] = None
    value_type: Optional[DiscountValueType] = None
    value: Optional[Decimal] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    is_stackable: Optional[bool] = None
    coupon_code: Optional[str] = Field(None, max_length=50)
    config: Optional[dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DiscountRuleResponse(BaseModel):
    """Schema for discount rule response."""
    id: UUID
    name: str
    scope: DiscountScope
    value_type: DiscountValueType
    value: Decimal
    priority: int
    is_active: bool
    is_stackable: bool
    coupon_code: Optional[str]
    config: dict[str, Any]
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return str(value)

    @field_serializer('value')
    def serialize_value(self, value: Decimal) -> float:
        return float(value)

    class Config:
        from_attributes = True
