"""
Product and Category model for the e-commerce catalog.
"""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins import TimeStampMixin

if TYPE_CHECKING:
    from app.models.order import OrderItem


class Category(SQLModel, TimeStampMixin, table=True):
    __tablename__ = "categories"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    slug: str = Field(max_length=100, index=True, unique=True)

    parent_category_id: UUID | None = Field(
        default=None, foreign_key="categories.id")
    products: list["Product"] = Relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Product(SQLModel, TimeStampMixin, table=True):

    __tablename__ = "products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    category_id: UUID = Field(foreign_key="categories.id", index=True)

    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    # IMPORTANT: Use DECIMAL for money to avoid floating-point errors
    price: Decimal = Field(max_digits=10, decimal_places=2)

    sku: str = Field(unique=True, index=True, max_length=50)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)

    # Relationships
    category: Category = Relationship(back_populates="products")
    order_items: list["OrderItem"] = Relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.name} (₹{self.price})>"
