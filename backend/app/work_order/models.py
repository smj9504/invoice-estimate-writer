"""
Work Order database models
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..core.database_factory import Base


class WorkOrderStatus(str, enum.Enum):
    """Work order status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    ESTIMATE = "estimate"
    INVOICE = "invoice"
    INSURANCE_ESTIMATE = "insurance_estimate"
    PLUMBER_REPORT = "plumber_report"
    WORK_ORDER = "work_order"


class WorkOrder(Base):
    """Work Order model"""
    __tablename__ = "work_orders"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Work Order Information
    work_order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Company relationship
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    # company = relationship("Company", back_populates="work_orders")
    
    # Client Information
    client_name = Column(String(200), nullable=False)
    client_address = Column(String(500))
    client_city = Column(String(100))
    client_state = Column(String(50))
    client_zipcode = Column(String(20))
    client_phone = Column(String(50))
    client_email = Column(String(200))
    
    # Job Information
    job_site_address = Column(String(500))
    job_site_city = Column(String(100))
    job_site_state = Column(String(50))
    job_site_zipcode = Column(String(20))
    
    # Work Details
    document_type = Column(Enum(DocumentType), nullable=False)
    work_description = Column(Text)
    scope_of_work = Column(Text)
    special_instructions = Column(Text)
    
    # Status and Assignment
    status = Column(Enum(WorkOrderStatus), default=WorkOrderStatus.DRAFT)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Staff Assignment
    created_by_staff_id = Column(UUID(as_uuid=True), nullable=False)
    assigned_to_staff_id = Column(UUID(as_uuid=True))
    
    # Scheduling
    scheduled_start_date = Column(DateTime)
    scheduled_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Financial Information
    estimated_hours = Column(String(20))
    estimated_cost = Column(String(50))
    actual_hours = Column(String(20))
    actual_cost = Column(String(50))
    
    # Additional Information
    materials_required = Column(Text)
    tools_required = Column(Text)
    permits_required = Column(Text)
    safety_notes = Column(Text)
    
    # Internal Notes
    internal_notes = Column(Text)
    completion_notes = Column(Text)
    
    # Status Flags
    is_active = Column(Boolean, default=True)
    is_billable = Column(Boolean, default=True)
    requires_permit = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __str__(self):
        return f"Work Order #{self.work_order_number} - {self.client_name}"
    
    def __repr__(self):
        return f"<WorkOrder(id={self.id}, number={self.work_order_number}, status={self.status})>"