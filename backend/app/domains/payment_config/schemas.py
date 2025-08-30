"""
Payment configuration schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    requires_account_info: bool = False
    account_info_fields: Optional[str] = None
    display_order: int = 0
    icon: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    requires_account_info: Optional[bool] = None
    account_info_fields: Optional[str] = None
    display_order: Optional[int] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PaymentMethodResponse(PaymentMethodBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Payment Frequency Schemas
class PaymentFrequencyBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    days_interval: Optional[int] = None
    display_order: int = 0
    is_active: bool = True
    is_default: bool = False


class PaymentFrequencyCreate(PaymentFrequencyBase):
    pass


class PaymentFrequencyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    days_interval: Optional[int] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PaymentFrequencyResponse(PaymentFrequencyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True