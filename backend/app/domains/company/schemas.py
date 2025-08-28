"""
Company domain schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.common.schemas.base import BaseResponseSchema, PaginatedResponse
from app.common.schemas.shared import Address


class CompanyBase(BaseModel):
    """Base company schema"""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    company_code: Optional[str] = Field(None, max_length=10)
    license_number: Optional[str] = Field(None, max_length=100)
    insurance_info: Optional[str] = None
    logo: Optional[str] = None  # Base64 encoded logo
    is_active: bool = True
    is_default: bool = False


class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    company_code: Optional[str] = Field(None, max_length=10)
    license_number: Optional[str] = Field(None, max_length=100)
    insurance_info: Optional[str] = None
    logo: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class CompanyResponse(CompanyBase, BaseResponseSchema):
    """Company response schema with ID and timestamps"""
    pass


class CompanyFilter(BaseModel):
    """Filter parameters for companies"""
    search: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


# Paginated response for companies
CompanyPaginatedResponse = PaginatedResponse[CompanyResponse]