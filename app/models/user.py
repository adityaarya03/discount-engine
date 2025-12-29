"""
User model for authentication and user management.
"""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins import TimeStampMixin
from enum import Enum

if TYPE_CHECKING:
    from app.models.order import Order
    
class UserRole(str,Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    
class User(SQLModel, TimeStampMixin, table=True):
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
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
    