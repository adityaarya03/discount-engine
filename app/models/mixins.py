"""
Reusable mixins for models
"""
from datetime import datetime, UTC
from sqlmodel import Field


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to models."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)