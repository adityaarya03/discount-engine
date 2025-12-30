"""
User model for authentication and user management.
"""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins import TimestampMixin
from enum import Enum

if TYPE_CHECKING:
    from app.models.order import Order
    
class UserRole(str,Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    
class User(SQLModel, TimestampMixin, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory = uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name:str = Field(max_length=100)
    phone:str | None = Field(default=None, max_length=15)
    
    is_active: bool = Field(default=True)
    role: UserRole = Field(default= UserRole.CUSTOMER)
    
    # Relationships
    orders: list["Order"] = Relationship(back_populates="user")

    def is_loyalty_member(self, session) -> bool:
        """
        Check if user qualifies for loyalty program membership.

        Loyalty PROGRAM membership unlocks stacking privileges for discounts.
        This is SEPARATE from individual discount rewards (like rewarded buyer offer).

        Example:
        - After 5 orders: User gets rewarded buyer ₹500 discount (single, non-stackable)
        - After 10 orders: User becomes loyalty member (can NOW stack rewarded buyer with others)

        Args:
            session: SQLModel session for querying orders

        Returns:
            True if user has >= 10 completed orders (loyalty membership threshold)
        """
        from sqlmodel import select, func
        from app.models.order import Order, OrderStatus

        LOYALTY_THRESHOLD = 10  # Minimum completed orders for loyalty program membership

        query = select(func.count(Order.id)).where(
            Order.user_id == self.id,
            Order.status == OrderStatus.COMPLETED
        )

        result = session.exec(query)
        completed_count = result.one()

        return completed_count >= LOYALTY_THRESHOLD

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
    