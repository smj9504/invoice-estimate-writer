"""
Invoice schemas
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from .document import DocumentBase, DocumentItem

class InvoiceItem(DocumentItem):
    """Invoice item schema"""
    invoice_id: Optional[str] = None

class InvoiceCreate(DocumentBase):
    """Schema for creating an invoice"""
    payment_terms: Optional[str] = None
    due_date: Optional[datetime] = None
    items: List[InvoiceItem] = []

class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    payment_terms: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[InvoiceItem]] = None

class Invoice(InvoiceCreate):
    """Invoice schema with all fields"""
    id: str
    invoice_number: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    """Response schema for invoice endpoints"""
    data: Optional[Invoice] = None
    error: Optional[str] = None
    message: Optional[str] = None