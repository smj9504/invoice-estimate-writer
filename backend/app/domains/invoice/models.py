"""
Invoice domain models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, DECIMAL, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database_factory import Base
from app.core.base_models import BaseModel


class Invoice(Base, BaseModel):
    __tablename__ = "invoices"
    __table_args__ = (
        Index('ix_invoice_number_version', 'invoice_number', 'version'),
        {'extend_existing': True}
    )

    invoice_number = Column(String(50), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text)
    client_phone = Column(String(50))
    client_email = Column(String(255))
    
    invoice_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="pending")  # pending, paid, overdue, cancelled
    
    subtotal = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), default=0)
    
    notes = Column(Text)
    terms = Column(Text)
    payment_terms = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base, BaseModel):
    __tablename__ = "invoice_items"

    invoice_id = Column(String, ForeignKey("invoices.id"))
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(10, 2), default=1)
    unit = Column(String(50))
    rate = Column(DECIMAL(15, 2), default=0)
    amount = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="items")