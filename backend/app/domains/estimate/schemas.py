"""
Estimate domain Pydantic schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class EstimateItemBase(BaseModel):
    """Base schema for estimate items"""
    room: Optional[str] = None
    description: str
    quantity: float = 1.0
    unit: Optional[str] = "ea"
    rate: float = 0.0
    category: Optional[str] = None
    
    # Insurance specific fields
    depreciation_rate: Optional[float] = 0.0
    depreciation_amount: Optional[float] = 0.0
    acv_amount: Optional[float] = 0.0
    rcv_amount: Optional[float] = 0.0


class EstimateItemCreate(EstimateItemBase):
    """Schema for creating estimate items"""
    pass


class EstimateItemUpdate(BaseModel):
    """Schema for updating estimate items"""
    room: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    category: Optional[str] = None
    depreciation_rate: Optional[float] = None


class EstimateItemResponse(EstimateItemBase):
    """Response schema for estimate items"""
    id: UUID
    estimate_id: Optional[UUID] = None
    amount: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    order_index: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EstimateBase(BaseModel):
    """Base schema for estimates"""
    estimate_number: Optional[str] = None
    company_id: Optional[UUID] = None
    client_name: str
    client_address: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    
    estimate_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: Optional[str] = "draft"
    
    notes: Optional[str] = None
    terms: Optional[str] = None
    
    # Insurance estimate specific fields
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    deductible: Optional[float] = None
    
    # Room data for floor plans
    room_data: Optional[Dict[str, Any]] = None


class EstimateCreate(EstimateBase):
    """Schema for creating estimates"""
    items: List[EstimateItemCreate] = []


class EstimateUpdate(BaseModel):
    """Schema for updating estimates"""
    estimate_number: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    
    estimate_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: Optional[str] = None
    
    notes: Optional[str] = None
    terms: Optional[str] = None
    
    # Insurance fields
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    deductible: Optional[float] = None
    
    # Room data
    room_data: Optional[Dict[str, Any]] = None
    
    # Items
    items: Optional[List[EstimateItemCreate]] = None


class EstimateListResponse(BaseModel):
    """Response schema for estimate list"""
    id: UUID
    estimate_number: str
    company_id: Optional[UUID] = None
    client_name: str
    total_amount: float
    status: str
    estimate_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EstimateResponse(BaseModel):
    """Full response schema for estimates"""
    id: UUID
    estimate_number: str
    company_id: Optional[UUID] = None
    
    # Client info
    client_name: str
    client_address: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    
    # Dates
    estimate_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str = "draft"
    
    # Financial
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    
    # Insurance specific
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    deductible: Optional[float] = None
    depreciation_amount: Optional[float] = 0.0
    acv_amount: Optional[float] = 0.0
    rcv_amount: Optional[float] = 0.0
    
    # Additional
    notes: Optional[str] = None
    terms: Optional[str] = None
    room_data: Optional[Dict[str, Any]] = None
    
    # Relationships
    items: List[EstimateItemResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EstimatePDFRequest(BaseModel):
    """Request model for generating PDF preview"""
    estimate_number: str = Field(default_factory=lambda: f"EST-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    estimate_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    valid_until: Optional[str] = None
    
    company: Dict[str, Any]  # Company info
    client: Dict[str, Any]  # Client info
    
    items: List[Dict[str, Any]] = []
    room_data: Optional[Dict[str, Any]] = None
    
    # Financial
    subtotal: float = 0
    tax_rate: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    total_amount: float = 0
    
    # Insurance
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    deductible: Optional[float] = None
    depreciation_amount: Optional[float] = 0
    acv_amount: Optional[float] = 0
    rcv_amount: Optional[float] = 0
    
    notes: Optional[str] = None
    terms: Optional[str] = None