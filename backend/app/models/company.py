"""
Company database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime

from ..database import Base


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100), default="USA")
    
    # Contact information
    phone = Column(String(50))
    email = Column(String(200))
    website = Column(String(200))
    
    # Business information
    business_license = Column(String(100))
    tax_id = Column(String(100))
    
    # Logo and branding
    logo = Column(Text)  # Base64 encoded or URL
    primary_color = Column(String(7))  # Hex color code
    secondary_color = Column(String(7))  # Hex color code
    
    # Additional fields
    description = Column(Text)
    notes = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)