"""
Pydantic schemas for discount rule requests/responses.
"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Any
from app.models.discount import DiscountType


class DiscountRuleCreate(BaseModel):
    """
    Schema for creating a discount rule.
    
    Example configs:
    
    Percentage:
    {
        "name": "Summer Sale 15% off",
        "discount_type": "PERCENTAGE",
        "priority": 1,
        "is_stackable": false,
        "config": {
            "conditions": {"min_cart_value": 3000},
            "action": {"percentage": 15}
        }
    }
    
    Flat Loyalty:
    {
        "name": "Loyalty Reward ₹1000",
        "discount_type": "FLAT_LOYALTY",
        "priority": 1,
        "is_stackable": true,
        "config": {
            "conditions": {"min_purchases": 10, "status_filter": ["COMPLETED"]},
            "action": {"flat_amount": 1000}
        }
    }
    
    Category-based:
    {
        "name": "Electronics Flash Sale",
        "discount_type": "CATEGORY_BASED",
        "priority": 2,
        "is_stackable": true,
        "config": {
            "conditions": {"category_id": "uuid-here", "min_quantity": 2},
            "action": {"percentage": 10}
        }
    }
    """
    name: str = Field(min_length=1, max_length=255)
    discount_type: DiscountType
    priority: int = Field(default=0, description="Lower number = higher priority")
    is_active: bool = Field(default=True)
    is_stackable: bool = Field(default=False, description="Can combine with other discounts")
    config: dict[str, Any] = Field(description="JSONB config with conditions and action")
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DiscountRuleUpdate(BaseModel):
    """Schema for updating a discount rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    is_stackable: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DiscountRuleResponse(BaseModel):
    """Schema for discount rule response."""
    id: UUID
    name: str
    discount_type: DiscountType
    priority: int
    is_active: bool
    is_stackable: bool
    config: dict[str, Any]
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return str(value)

    class Config:
        from_attributes = True