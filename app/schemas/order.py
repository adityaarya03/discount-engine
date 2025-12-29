"""
Pydantic schemas for order-related requests and responses.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""
    product_id: UUID
    quantity: int = Field(ge=1, description="Quantity must be at least 1")


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    items: list[OrderItemCreate] = Field(min_length=1, description="At least one item required")


class OrderItemResponse(BaseModel):
    """Schema for order item in responses."""
    id: UUID
    product_id: UUID
    product_name: str
    product_category_id: UUID
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    discount_amount: Decimal
    
    class Config:
        from_attributes = True


class AppliedDiscountResponse(BaseModel):
    """Schema for applied discount details."""
    rule_name: str
    rule_type: str
    discount_amount: float
    details: dict


class OrderResponse(BaseModel):
    """Schema for order response with full details."""
    id: UUID
    user_id: UUID
    status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: str
    items: list[OrderItemResponse]
    applied_discounts: list[AppliedDiscountResponse] = []
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for order list (without items)."""
    id: UUID
    status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    created_at: str
    items_count: int
    
    class Config:
        from_attributes = True