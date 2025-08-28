"""
Estimate domain models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base_models import BaseModel


class Estimate(BaseModel):
    __tablename__ = "estimates"

    estimate_number = Column(String(50), unique=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text)
    client_phone = Column(String(50))
    client_email = Column(String(255))
    
    estimate_date = Column(DateTime(timezone=True), default=func.now())
    valid_until = Column(DateTime(timezone=True))
    status = Column(String(50), default="draft")  # draft, sent, accepted, rejected, expired
    
    subtotal = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), default=0)
    
    notes = Column(Text)
    terms = Column(Text)
    
    # Insurance estimate specific fields
    claim_number = Column(String(100))
    policy_number = Column(String(100))
    deductible = Column(DECIMAL(15, 2))
    depreciation_amount = Column(DECIMAL(15, 2), default=0)
    acv_amount = Column(DECIMAL(15, 2), default=0)  # Actual Cash Value
    rcv_amount = Column(DECIMAL(15, 2), default=0)  # Replacement Cost Value
    
    # Room data for floor plans
    room_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="estimates")
    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")


class EstimateItem(BaseModel):
    __tablename__ = "estimate_items"

    estimate_id = Column(String, ForeignKey("estimates.id"))
    room = Column(String(100))
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(10, 2), default=1)
    unit = Column(String(50))
    rate = Column(DECIMAL(15, 2), default=0)
    amount = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    
    # Insurance specific fields
    depreciation_rate = Column(DECIMAL(5, 2), default=0)
    depreciation_amount = Column(DECIMAL(15, 2), default=0)
    acv_amount = Column(DECIMAL(15, 2), default=0)
    rcv_amount = Column(DECIMAL(15, 2), default=0)
    
    order_index = Column(Integer, default=0)
    category = Column(String(100))  # labor, material, equipment, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    estimate = relationship("Estimate", back_populates="items")