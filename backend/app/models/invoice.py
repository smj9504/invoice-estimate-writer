"""
Invoice database models
"""

from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(20), default="draft")  # draft, sent, paid, overdue, cancelled
    
    # Company information
    company_name = Column(String(200))
    company_address = Column(String(500))
    company_city = Column(String(100))
    company_state = Column(String(50))
    company_zip = Column(String(20))
    company_phone = Column(String(50))
    company_email = Column(String(200))
    company_logo = Column(Text)  # Base64 encoded or URL
    
    # Client information
    client_name = Column(String(200), nullable=False)
    client_address = Column(String(500))
    client_city = Column(String(100))
    client_state = Column(String(50))
    client_zip = Column(String(20))
    client_phone = Column(String(50))
    client_email = Column(String(200))
    
    # Insurance information (optional)
    insurance_company = Column(String(200))
    insurance_policy_number = Column(String(100))
    insurance_claim_number = Column(String(100))
    insurance_deductible = Column(Float, default=0)
    
    # Financial information
    subtotal = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    discount = Column(Float, default=0)
    shipping = Column(Float, default=0)
    total = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    
    # Additional fields
    payment_terms = Column(Text)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"))
    
    name = Column(String(500), nullable=False)
    description = Column(Text)
    quantity = Column(Float, default=1)
    unit = Column(String(50), default="ea")
    rate = Column(Float, default=0)
    amount = Column(Float, default=0)
    
    # Order for display
    order_index = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")