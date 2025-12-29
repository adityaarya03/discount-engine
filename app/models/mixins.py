"""
Reusable mixins for models
"""
from datetime import datetime, UTC
from sqlmodel import Field

class TimeStampMixin:
    created_at: datetime = Field(default_factory = datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory = datetime.now(UTC), nullable = False)