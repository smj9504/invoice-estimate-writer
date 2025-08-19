"""
Company schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class CompanyBase(BaseModel):
    """Base company schema"""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass

class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

class Company(CompanyBase):
    """Company schema with all fields"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CompanyResponse(BaseModel):
    """Response schema for company endpoints"""
    data: Optional[Company] = None
    error: Optional[str] = None
    message: Optional[str] = None

class CompaniesResponse(BaseModel):
    """Response schema for multiple companies"""
    data: list[Company]
    total: int