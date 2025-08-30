"""
Work Order Staff Assignment model for multiple staff per work order
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database_factory import Base


class WorkOrderStaffAssignment(Base):
    """Junction table for work order to staff many-to-many relationship"""
    __tablename__ = "work_order_staff_assignments"
    __table_args__ = (
        Index('ix_work_order_staff', 'work_order_id', 'staff_id'),
        {'extend_existing': True}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    
    # Assignment Details
    assigned_role = Column(String(50))  # primary, secondary, reviewer, etc.
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<WorkOrderStaffAssignment(work_order_id={self.work_order_id}, staff_id={self.staff_id})>"