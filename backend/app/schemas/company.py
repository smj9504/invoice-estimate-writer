"""
Company schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class CompanyBase(BaseModel):
    """Base company schema"""
    name: str
    address: str
    city: str
    state: str
    zip: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo: Optional[str] = None  # Base64 encoded image
    company_code: Optional[str] = None  # 4-character unique code
    
class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass

class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo: Optional[str] = None
    company_code: Optional[str] = None

class Company(CompanyBase):
    """Company schema with all fields"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
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

class CompanyFilter(BaseModel):
    """Filter parameters for companies"""
    search: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None