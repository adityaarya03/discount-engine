"""
Order models: Order, OrderItem.
"""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product
    from app.models.discount import AppliedDiscount


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class Order(SQLModel, TimestampMixin, table=True):
    __tablename__ = "orders"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    
    # Money fields - DECIMAL for precision
    subtotal: Decimal = Field(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount: Decimal = Field(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_amount: Decimal = Field(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount: Decimal = Field(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    
    # Relationships
    user: "User" = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order", cascade_delete=True)
    applied_discounts: list["AppliedDiscount"] = Relationship(back_populates="order", cascade_delete=True)
    
    def __repr__(self) -> str:
        return f"<Order {self.id} - {self.status.value}>"


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    product_id: UUID = Field(foreign_key="products.id")
    
    # DENORMALIZED FIELDS - Snapshot at order time
    product_name: str = Field(max_length=255)
    product_category_id: UUID  # <-- KEY: Enables fast category-based discount checks
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    
    quantity: int = Field(ge=1)
    subtotal: Decimal = Field(max_digits=10, decimal_places=2)
    discount_amount: Decimal = Field(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    
    # Relationships
    order: Order = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="order_items")
    
    def __repr__(self) -> str:
        return f"<OrderItem {self.product_name} x{self.quantity}>"