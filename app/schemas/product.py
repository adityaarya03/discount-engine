"""
Pydantic schemas for product and category requests/responses.
"""
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from typing import Optional

class CategoryCreate(BaseModel):
    """Schema for creating a category."""
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100, description="URL-friendly identifier")
    parent_category_id: Optional[UUID] = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_category_id: Optional[UUID] = None


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: UUID
    name: str
    slug: str
    parent_category_id: Optional[UUID]
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return str(value)

    class Config:
        from_attributes = True


# ============================================
# Product Schemas
# ============================================

class ProductCreate(BaseModel):
    """Schema for creating a product."""
    category_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(gt=0, description="Price must be greater than 0")
    sku: str = Field(min_length=1, max_length=50)
    stock_quantity: int = Field(ge=0, description="Stock cannot be negative")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    category_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: UUID
    category_id: UUID
    name: str
    description: Optional[str]
    price: Decimal
    sku: str
    stock_quantity: int
    is_active: bool
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return str(value)

    class Config:
        from_attributes = True


class ProductWithCategoryResponse(ProductResponse):
    """Schema for product response with category details."""
    category: CategoryResponse
    
    class Config:
        from_attributes = True