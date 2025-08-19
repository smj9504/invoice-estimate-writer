"""
Estimate schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from .document import DocumentBase, DocumentItem

class EstimateItem(DocumentItem):
    """Estimate item schema"""
    estimate_id: Optional[str] = None

class EstimateCreate(DocumentBase):
    """Schema for creating an estimate"""
    items: List[EstimateItem] = []
    room_data: Optional[Dict[str, Any]] = None  # For insurance estimates

class EstimateUpdate(BaseModel):
    """Schema for updating an estimate"""
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[EstimateItem]] = None

class Estimate(EstimateCreate):
    """Estimate schema with all fields"""
    id: str
    estimate_number: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EstimateResponse(BaseModel):
    """Response schema for estimate endpoints"""
    data: Optional[Estimate] = None
    error: Optional[str] = None
    message: Optional[str] = None