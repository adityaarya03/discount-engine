"""Pydantic schemas for request/response validation."""
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderResponse,
    OrderListResponse,
    OrderItemResponse,
    AppliedDiscountResponse,
)
from app.schemas.product import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithCategoryResponse,
)
from app.schemas.discount import (
    DiscountRuleCreate,
    DiscountRuleUpdate,
    DiscountRuleResponse,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "OrderCreate",
    "OrderItemCreate",
    "OrderResponse",
    "OrderListResponse",
    "OrderItemResponse",
    "AppliedDiscountResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductWithCategoryResponse",
    "DiscountRuleCreate",
    "DiscountRuleUpdate",
    "DiscountRuleResponse",
]