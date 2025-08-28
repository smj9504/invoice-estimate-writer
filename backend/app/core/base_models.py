"""
Base models and mixins for all domain models
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
import uuid


def generate_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())


class UUIDMixin:
    """Mixin to add UUID primary key to models"""
    id = Column(String, primary_key=True, default=generate_uuid)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), onupdate=func.now())


class BaseModel(UUIDMixin, TimestampMixin):
    """Base model class with UUID and timestamps"""
    pass