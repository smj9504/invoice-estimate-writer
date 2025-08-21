"""
Invoice API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Response, UploadFile, File
from typing import List, Optional
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path

from ..database import get_db
from ..models.invoice import Invoice, InvoiceItem
from ..schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoicePDFRequest
)
from ..services.pdf_service import pdf_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=List[InvoiceListResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    client_name: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """List all invoices with optional filtering"""
    query = db.query(Invoice)
    
    if client_name:
        query = query.filter(Invoice.client_name.contains(client_name))
    
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db=Depends(get_db)):
    """Get a specific invoice by ID"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db=Depends(get_db)):
    """Create a new invoice"""
    # Generate invoice number if not provided
    if not invoice.invoice_number:
        invoice.invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Create invoice
    db_invoice = Invoice(
        invoice_number=invoice.invoice_number,
        date=invoice.date or datetime.now().date(),
        due_date=invoice.due_date or (datetime.now() + timedelta(days=30)).date(),
        status=invoice.status or "draft",
        
        # Company info
        company_name=invoice.company.name,
        company_address=invoice.company.address,
        company_city=invoice.company.city,
        company_state=invoice.company.state,
        company_zip=invoice.company.zip,
        company_phone=invoice.company.phone,
        company_email=invoice.company.email,
        company_logo=invoice.company.logo,
        
        # Client info
        client_name=invoice.client.name,
        client_address=invoice.client.address,
        client_city=invoice.client.city,
        client_state=invoice.client.state,
        client_zip=invoice.client.zip,
        client_phone=invoice.client.phone,
        client_email=invoice.client.email,
        
        # Insurance info (optional)
        insurance_company=invoice.insurance.company if invoice.insurance else None,
        insurance_policy_number=invoice.insurance.policy_number if invoice.insurance else None,
        insurance_claim_number=invoice.insurance.claim_number if invoice.insurance else None,
        insurance_deductible=invoice.insurance.deductible if invoice.insurance else None,
        
        # Financial
        subtotal=0,
        tax_rate=invoice.tax_rate or 0,
        tax_amount=0,
        discount=invoice.discount or 0,
        shipping=invoice.shipping or 0,
        total=0,
        paid_amount=invoice.paid_amount or 0,
        
        # Additional fields
        payment_terms=invoice.payment_terms,
        notes=invoice.notes
    )
    
    db.add(db_invoice)
    db.flush()  # Get the ID without committing
    
    # Add invoice items
    subtotal = 0
    for item in invoice.items:
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            name=item.name,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            rate=item.rate,
            amount=item.quantity * item.rate
        )
        db.add(db_item)
        subtotal += db_item.amount
    
    # Update totals
    db_invoice.subtotal = subtotal
    db_invoice.tax_amount = subtotal * db_invoice.tax_rate / 100
    db_invoice.total = subtotal + db_invoice.tax_amount - db_invoice.discount + db_invoice.shipping
    
    db.commit()
    db.refresh(db_invoice)
    
    return db_invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice: InvoiceUpdate,
    db=Depends(get_db)
):
    """Update an existing invoice"""
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update fields
    update_data = invoice.dict(exclude_unset=True)
    
    # Handle nested objects
    if 'company' in update_data:
        company = update_data.pop('company')
        for key, value in company.items():
            setattr(db_invoice, f"company_{key}", value)
    
    if 'client' in update_data:
        client = update_data.pop('client')
        for key, value in client.items():
            setattr(db_invoice, f"client_{key}", value)
    
    if 'insurance' in update_data:
        insurance = update_data.pop('insurance')
        for key, value in insurance.items():
            setattr(db_invoice, f"insurance_{key}", value)
    
    # Handle items
    if 'items' in update_data:
        items = update_data.pop('items')
        
        # Delete existing items
        db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
        
        # Add new items
        subtotal = 0
        for item in items:
            db_item = InvoiceItem(
                invoice_id=invoice_id,
                name=item['name'],
                description=item.get('description'),
                quantity=item['quantity'],
                unit=item.get('unit', 'ea'),
                rate=item['rate'],
                amount=item['quantity'] * item['rate']
            )
            db.add(db_item)
            subtotal += db_item.amount
        
        db_invoice.subtotal = subtotal
        db_invoice.tax_amount = subtotal * db_invoice.tax_rate / 100
        db_invoice.total = subtotal + db_invoice.tax_amount - db_invoice.discount + db_invoice.shipping
    
    # Update other fields
    for key, value in update_data.items():
        if hasattr(db_invoice, key):
            setattr(db_invoice, key, value)
    
    db.commit()
    db.refresh(db_invoice)
    
    return db_invoice


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db=Depends(get_db)):
    """Delete an invoice"""
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete associated items
    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
    
    # Delete invoice
    db.delete(db_invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}


@router.post("/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: int, db=Depends(get_db)):
    """Generate PDF for an invoice"""
    # Get invoice from database
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get invoice items
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    
    # Prepare data for PDF generation
    pdf_data = {
        "invoice_number": invoice.invoice_number,
        "date": invoice.date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "company": {
            "name": invoice.company_name,
            "address": invoice.company_address,
            "city": invoice.company_city,
            "state": invoice.company_state,
            "zip": invoice.company_zip,
            "phone": invoice.company_phone,
            "email": invoice.company_email,
            "logo": invoice.company_logo
        },
        "client": {
            "name": invoice.client_name,
            "address": invoice.client_address,
            "city": invoice.client_city,
            "state": invoice.client_state,
            "zip": invoice.client_zip,
            "phone": invoice.client_phone,
            "email": invoice.client_email
        },
        "items": [
            {
                "name": item.name,
                "description": item.description,
                "quantity": item.quantity,
                "unit": item.unit,
                "rate": item.rate
            }
            for item in items
        ],
        "subtotal": invoice.subtotal,
        "tax_rate": invoice.tax_rate,
        "tax_amount": invoice.tax_amount,
        "discount": invoice.discount,
        "shipping": invoice.shipping,
        "total": invoice.total,
        "paid_amount": invoice.paid_amount,
        "payment_terms": invoice.payment_terms,
        "notes": invoice.notes
    }
    
    # Add insurance info if present
    if invoice.insurance_company:
        pdf_data["insurance"] = {
            "company": invoice.insurance_company,
            "policy_number": invoice.insurance_policy_number,
            "claim_number": invoice.insurance_claim_number,
            "deductible": invoice.insurance_deductible
        }
    
    # Generate PDF
    if not pdf_service:
        raise HTTPException(status_code=500, detail="PDF service not available")
    
    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Generate PDF
        pdf_path = pdf_service.generate_invoice_pdf(pdf_data, output_path)
        
        # Read PDF file
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Clean up temp file
        os.unlink(pdf_path)
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{invoice.invoice_number}.pdf"
            }
        )
    except Exception as e:
        # Clean up on error
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-pdf")
async def preview_invoice_pdf(data: InvoicePDFRequest):
    """Generate a preview PDF from invoice data without saving"""
    if not pdf_service:
        raise HTTPException(status_code=500, detail="PDF service not available")
    
    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Prepare data for PDF generation
        pdf_data = data.dict()
        
        # Generate PDF
        pdf_path = pdf_service.generate_invoice_pdf(pdf_data, output_path)
        
        # Read PDF file
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Clean up temp file
        os.unlink(pdf_path)
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=preview_invoice.pdf"
            }
        )
    except Exception as e:
        # Clean up on error
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/duplicate", response_model=InvoiceResponse)
async def duplicate_invoice(invoice_id: int, db=Depends(get_db)):
    """Duplicate an existing invoice"""
    # Get original invoice
    original = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get original items
    original_items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    
    # Create new invoice
    new_invoice = Invoice(
        invoice_number=f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        date=datetime.now().date(),
        due_date=(datetime.now() + timedelta(days=30)).date(),
        status="draft",
        
        # Copy company info
        company_name=original.company_name,
        company_address=original.company_address,
        company_city=original.company_city,
        company_state=original.company_state,
        company_zip=original.company_zip,
        company_phone=original.company_phone,
        company_email=original.company_email,
        company_logo=original.company_logo,
        
        # Copy client info
        client_name=original.client_name,
        client_address=original.client_address,
        client_city=original.client_city,
        client_state=original.client_state,
        client_zip=original.client_zip,
        client_phone=original.client_phone,
        client_email=original.client_email,
        
        # Copy insurance info
        insurance_company=original.insurance_company,
        insurance_policy_number=original.insurance_policy_number,
        insurance_claim_number=original.insurance_claim_number,
        insurance_deductible=original.insurance_deductible,
        
        # Copy financial info
        subtotal=original.subtotal,
        tax_rate=original.tax_rate,
        tax_amount=original.tax_amount,
        discount=original.discount,
        shipping=original.shipping,
        total=original.total,
        paid_amount=0,  # Reset paid amount
        
        # Copy additional fields
        payment_terms=original.payment_terms,
        notes=original.notes
    )
    
    db.add(new_invoice)
    db.flush()
    
    # Copy items
    for item in original_items:
        new_item = InvoiceItem(
            invoice_id=new_invoice.id,
            name=item.name,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            rate=item.rate,
            amount=item.amount
        )
        db.add(new_item)
    
    db.commit()
    db.refresh(new_invoice)
    
    return new_invoice