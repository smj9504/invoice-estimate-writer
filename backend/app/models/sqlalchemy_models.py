"""
SQLAlchemy models for all database tables
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, JSON, DECIMAL, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database_factory import Base
import uuid

# Import new models
from app.work_order.models import WorkOrder, WorkOrderStatus, DocumentType
from app.payment.models import Payment, BillingSchedule, PaymentRefund, PaymentStatus, PaymentMethod, BillingCycle
from app.credit.models import CustomerCredit, DiscountRule, AppliedDiscount, CreditTransaction, CreditType, DiscountType, CreditStatus
from app.staff.models import Staff, StaffPermission, StaffSession, AuditLog, StaffRole, PermissionLevel


def generate_uuid():
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    logo = Column(Text)  # Base64 encoded logo
    city = Column(String(100))
    state = Column(String(50))
    zipcode = Column(String(20))
    company_code = Column(String(10))  # Unique company code
    license_number = Column(String(100))
    insurance_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoices = relationship("Invoice", back_populates="company", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="company", cascade="all, delete-orphan")
    plumber_reports = relationship("PlumberReport", back_populates="company", cascade="all, delete-orphan")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), unique=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text)
    client_phone = Column(String(50))
    client_email = Column(String(255))
    
    invoice_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="pending")  # pending, paid, overdue, cancelled
    
    subtotal = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), default=0)
    
    notes = Column(Text)
    terms = Column(Text)
    payment_terms = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    invoice_id = Column(String, ForeignKey("invoices.id"))
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(10, 2), default=1)
    unit = Column(String(50))
    rate = Column(DECIMAL(15, 2), default=0)
    amount = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="items")


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(String, primary_key=True, default=generate_uuid)
    estimate_number = Column(String(50), unique=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text)
    client_phone = Column(String(50))
    client_email = Column(String(255))
    
    estimate_date = Column(DateTime(timezone=True), default=func.now())
    valid_until = Column(DateTime(timezone=True))
    status = Column(String(50), default="draft")  # draft, sent, accepted, rejected, expired
    
    subtotal = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), default=0)
    
    notes = Column(Text)
    terms = Column(Text)
    
    # Insurance estimate specific fields
    claim_number = Column(String(100))
    policy_number = Column(String(100))
    deductible = Column(DECIMAL(15, 2))
    depreciation_amount = Column(DECIMAL(15, 2), default=0)
    acv_amount = Column(DECIMAL(15, 2), default=0)  # Actual Cash Value
    rcv_amount = Column(DECIMAL(15, 2), default=0)  # Replacement Cost Value
    
    # Room data for floor plans
    room_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="estimates")
    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")


class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    estimate_id = Column(String, ForeignKey("estimates.id"))
    room = Column(String(100))
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(10, 2), default=1)
    unit = Column(String(50))
    rate = Column(DECIMAL(15, 2), default=0)
    amount = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    
    # Insurance specific fields
    depreciation_rate = Column(DECIMAL(5, 2), default=0)
    depreciation_amount = Column(DECIMAL(15, 2), default=0)
    acv_amount = Column(DECIMAL(15, 2), default=0)
    rcv_amount = Column(DECIMAL(15, 2), default=0)
    
    order_index = Column(Integer, default=0)
    category = Column(String(100))  # labor, material, equipment, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    estimate = relationship("Estimate", back_populates="items")


class PlumberReport(Base):
    __tablename__ = "plumber_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    report_number = Column(String(50), unique=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    
    # Client Information
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text)
    client_phone = Column(String(50))
    client_email = Column(String(255))
    
    # Report Details
    report_date = Column(DateTime(timezone=True), default=func.now())
    inspection_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="draft")  # draft, completed, sent
    
    # Findings
    water_source = Column(String(100))
    water_pressure = Column(String(100))
    main_line_size = Column(String(50))
    main_line_material = Column(String(100))
    
    findings = Column(Text)
    recommendations = Column(Text)
    
    # Inspection Areas (JSON structure for flexibility)
    inspection_areas = Column(JSON)
    
    # Photos/Attachments (store as JSON array of base64 or URLs)
    attachments = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="plumber_reports")


class Document(Base):
    """Generic document table for tracking all document types"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_type = Column(String(50), nullable=False)  # invoice, estimate, plumber_report
    document_id = Column(String, nullable=False)  # ID from specific table
    document_number = Column(String(50), nullable=False)
    client_name = Column(String(255))
    total_amount = Column(DECIMAL(15, 2))
    status = Column(String(50))
    created_date = Column(DateTime(timezone=True))
    pdf_url = Column(Text)  # URL or path to generated PDF
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())