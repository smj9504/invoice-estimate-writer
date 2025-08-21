"""
Invoice Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


# Nested schemas
class CompanyInfo(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None


class ClientInfo(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class InsuranceInfo(BaseModel):
    company: Optional[str] = None
    policy_number: Optional[str] = None
    claim_number: Optional[str] = None
    deductible: Optional[float] = None


class InvoiceItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: float = 1
    unit: str = "ea"
    rate: float = 0


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int
    amount: float
    order_index: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Main invoice schemas
class InvoiceBase(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = "draft"
    
    company: CompanyInfo
    client: ClientInfo
    insurance: Optional[InsuranceInfo] = None
    
    tax_rate: Optional[float] = 0
    discount: Optional[float] = 0
    shipping: Optional[float] = 0
    paid_amount: Optional[float] = 0
    
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    
    company: Optional[CompanyInfo] = None
    client: Optional[ClientInfo] = None
    insurance: Optional[InsuranceInfo] = None
    
    items: Optional[List[InvoiceItemCreate]] = None
    
    tax_rate: Optional[float] = None
    discount: Optional[float] = None
    shipping: Optional[float] = None
    paid_amount: Optional[float] = None
    
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceListResponse(BaseModel):
    id: int
    invoice_number: str
    date: date
    due_date: date
    status: str
    client_name: str
    total: float
    paid_amount: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    date: date
    due_date: date
    status: str
    
    # Company info
    company_name: str
    company_address: Optional[str]
    company_city: Optional[str]
    company_state: Optional[str]
    company_zip: Optional[str]
    company_phone: Optional[str]
    company_email: Optional[str]
    company_logo: Optional[str]
    
    # Client info
    client_name: str
    client_address: Optional[str]
    client_city: Optional[str]
    client_state: Optional[str]
    client_zip: Optional[str]
    client_phone: Optional[str]
    client_email: Optional[str]
    
    # Insurance info
    insurance_company: Optional[str]
    insurance_policy_number: Optional[str]
    insurance_claim_number: Optional[str]
    insurance_deductible: Optional[float]
    
    # Financial
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount: float
    shipping: float
    total: float
    paid_amount: float
    
    # Additional
    payment_terms: Optional[str]
    notes: Optional[str]
    
    # Relationships
    items: List[InvoiceItemResponse] = []
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InvoicePDFRequest(BaseModel):
    """Request model for generating PDF preview"""
    invoice_number: str = Field(default_factory=lambda: f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    due_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    company: CompanyInfo
    client: ClientInfo
    insurance: Optional[InsuranceInfo] = None
    
    items: List[InvoiceItemBase] = []
    
    subtotal: float = 0
    tax_rate: float = 0
    tax_amount: float = 0
    discount: float = 0
    shipping: float = 0
    total: float = 0
    paid_amount: float = 0
    
    payment_terms: Optional[str] = None
    notes: Optional[str] = None