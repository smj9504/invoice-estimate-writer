"""
Invoice API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Response, UploadFile, File
from typing import List, Optional
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path

from ..core.database_factory import get_db_session as get_db
from ..schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceItemResponse,
    InvoicePDFRequest,
    CompanyInfo
)
from ..services.pdf_service import pdf_service
from ..services.invoice_service import InvoiceService

router = APIRouter()


@router.get("/", response_model=List[InvoiceListResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    client_name: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """List all invoices with optional filtering"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    invoices = service.get_all(status=status, limit=limit, offset=skip)
    
    # Filter by client_name if provided
    if client_name:
        invoices = [inv for inv in invoices if client_name.lower() in inv.get('client_name', '').lower()]
    
    # Convert to response format
    return [
        InvoiceListResponse(
            id=inv['id'],
            invoice_number=inv.get('invoice_number', ''),
            date=inv.get('date', inv.get('created_at', '')),
            due_date=inv.get('due_date', ''),
            company_name=inv.get('company_name', ''),
            client_name=inv.get('client_name', ''),
            total=inv.get('total', 0),
            paid_amount=inv.get('paid_amount', 0),
            status=inv.get('status', 'draft'),
            created_at=inv.get('created_at', ''),
            updated_at=inv.get('updated_at', '')
        )
        for inv in invoices
    ]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db=Depends(get_db)):
    """Get a specific invoice by ID"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    invoice = service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Convert to response format
    return InvoiceResponse(
        id=invoice['id'],
        invoice_number=invoice.get('invoice_number', ''),
        date=invoice.get('invoice_date', invoice.get('date', invoice.get('created_at', ''))),
        invoice_date=invoice.get('invoice_date', invoice.get('date', invoice.get('created_at', ''))),
        due_date=invoice.get('due_date', ''),
        status=invoice.get('status', 'draft'),
        company_id=invoice.get('company_id'),
        company_name=invoice.get('company_name', ''),
        company_address=invoice.get('company_address'),
        company_city=invoice.get('company_city'),
        company_state=invoice.get('company_state'),
        company_zipcode=invoice.get('company_zipcode', invoice.get('company_zip')),
        company_phone=invoice.get('company_phone'),
        company_email=invoice.get('company_email'),
        company_logo=invoice.get('company_logo'),
        client_name=invoice.get('client_name', ''),
        client_address=invoice.get('client_address'),
        client_city=invoice.get('client_city'),
        client_state=invoice.get('client_state'),
        client_zipcode=invoice.get('client_zipcode', invoice.get('client_zip')),
        client_phone=invoice.get('client_phone'),
        client_email=invoice.get('client_email'),
        insurance_company=invoice.get('insurance_company'),
        insurance_policy_number=invoice.get('insurance_policy_number'),
        insurance_claim_number=invoice.get('insurance_claim_number'),
        insurance_deductible=invoice.get('insurance_deductible'),
        subtotal=invoice.get('subtotal', 0),
        tax_rate=invoice.get('tax_rate', 0),
        tax_amount=invoice.get('tax_amount', 0),
        discount=invoice.get('discount_amount', invoice.get('discount', 0)),
        discount_amount=invoice.get('discount_amount', invoice.get('discount', 0)),
        shipping=invoice.get('shipping', 0),
        total=invoice.get('total_amount', invoice.get('total', 0)),
        total_amount=invoice.get('total_amount', invoice.get('total', 0)),
        paid_amount=invoice.get('paid_amount', 0),
        payment_terms=invoice.get('payment_terms'),
        notes=invoice.get('notes'),
        created_at=invoice.get('created_at', ''),
        updated_at=invoice.get('updated_at', ''),
        items=[
            InvoiceItemResponse(
                id=item.get('id'),
                invoice_id=item.get('invoice_id'),
                name=item.get('description', ''),  # Map description to name for compatibility
                description=item.get('description'),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in invoice.get('items', [])
        ]
    )


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, db=Depends(get_db)):
    """Create a new invoice"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received invoice data: {invoice_data.dict()}")
    
    # Initialize service
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    
    # Determine if using saved company or custom company
    company_code = None
    company_name = None
    
    if invoice_data.company_id:
        # Using saved company - get company details
        try:
            from ..repositories.company_repository import get_company_repository
            company_repo = get_company_repository(db)
            company = company_repo.get_by_id(str(invoice_data.company_id))
            if company:
                company_code = company.get('company_code')
                company_name = company.get('name')
                # Set company info for storage
                invoice_data.company = CompanyInfo(
                    name=company.get('name'),
                    address=company.get('address'),
                    city=company.get('city'),
                    state=company.get('state'),
                    zip=company.get('zipcode'),
                    phone=company.get('phone'),
                    email=company.get('email'),
                    logo=company.get('logo')
                )
        except Exception as e:
            logger.error(f"Error fetching company: {e}")
    elif invoice_data.company:
        # Using custom company - generate temporary code
        company_name = invoice_data.company.name
        if company_name:
            # Generate a simple temp code for now
            company_code = f"TEMP-{company_name[:3].upper()}"
    
    # Generate invoice number if not provided
    if not invoice_data.invoice_number:
        # Fallback to timestamp-based number
        invoice_data.invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Calculate totals
    subtotal = sum(item.quantity * item.rate for item in invoice_data.items)
    tax_amount = 0
    if invoice_data.tax_rate:
        tax_amount = subtotal * invoice_data.tax_rate / 100
    
    # Use discount (not discount_amount) from schema
    discount = invoice_data.discount if hasattr(invoice_data, 'discount') else 0
    shipping = invoice_data.shipping if hasattr(invoice_data, 'shipping') else 0
    total = subtotal + tax_amount - discount + shipping
    
    # Convert date strings to datetime objects for SQLAlchemy
    invoice_date = invoice_data.date
    due_date = invoice_data.due_date
    
    # Parse date strings if provided
    if invoice_date:
        if isinstance(invoice_date, str):
            invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
    else:
        invoice_date = datetime.now()
    
    if due_date:
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d')
    else:
        due_date = datetime.now() + timedelta(days=30)
    
    # Prepare data for SQLAlchemy Invoice model
    invoice_dict = {
        'invoice_number': invoice_data.invoice_number,
        'invoice_date': invoice_date,
        'due_date': due_date,
        'status': invoice_data.status or 'pending',
        'company_id': str(invoice_data.company_id) if invoice_data.company_id else None,
        
        # Client information - directly on Invoice model
        'client_name': invoice_data.client.name if invoice_data.client else '',
        'client_address': invoice_data.client.address if invoice_data.client else '',
        'client_phone': invoice_data.client.phone if invoice_data.client else '',
        'client_email': invoice_data.client.email if invoice_data.client else '',
        
        # Financial information
        'subtotal': subtotal,
        'tax_rate': invoice_data.tax_rate or 0,
        'tax_amount': tax_amount,
        'discount_amount': discount,  # Use the discount we calculated above
        'total_amount': total,  # Invoice model uses total_amount, not total
        
        # Additional fields
        'payment_terms': invoice_data.payment_terms if hasattr(invoice_data, 'payment_terms') else 'Net 30',
        'notes': invoice_data.notes if hasattr(invoice_data, 'notes') else None,
        'terms': invoice_data.terms if hasattr(invoice_data, 'terms') else None,
    }
    
    # Prepare items separately
    items_data = [
        {
            'description': item.name,  # InvoiceItem model uses description as the main field
            'quantity': item.quantity,
            'unit': item.unit if hasattr(item, 'unit') else 'ea',
            'rate': item.rate,
            'amount': item.quantity * item.rate
        }
        for item in invoice_data.items
    ]
    
    # Create invoice using repository
    from ..repositories.invoice_repository import get_invoice_repository
    invoice_repo = get_invoice_repository(db)
    
    # Add items to the invoice_dict for the repository
    invoice_dict['items'] = items_data
    
    created_invoice = invoice_repo.create_with_items(invoice_dict)
    
    # Get company information if company_id was provided
    company_name = ''
    company_address = None
    company_city = None  
    company_state = None
    company_zipcode = None
    company_phone = None
    company_email = None
    company_logo = None
    
    if invoice_data.company_id and created_invoice.get('company'):
        company = created_invoice['company']
        company_name = company.get('name', '')
        company_address = company.get('address')
        company_city = company.get('city')
        company_state = company.get('state')
        company_zipcode = company.get('zipcode')
        company_phone = company.get('phone')
        company_email = company.get('email')
        company_logo = company.get('logo')
    elif invoice_data.company:
        company_name = invoice_data.company.name
        company_address = invoice_data.company.address
        company_city = invoice_data.company.city
        company_state = invoice_data.company.state
        company_zipcode = invoice_data.company.zipcode
        company_phone = invoice_data.company.phone
        company_email = invoice_data.company.email
        company_logo = invoice_data.company.logo
    
    # Convert date back to string for response
    date_str = created_invoice.get('invoice_date', '')
    if isinstance(date_str, datetime):
        date_str = date_str.strftime('%Y-%m-%d')
    
    due_date_str = created_invoice.get('due_date', '')
    if isinstance(due_date_str, datetime):
        due_date_str = due_date_str.strftime('%Y-%m-%d')
    
    # Convert to response format
    return InvoiceResponse(
        id=created_invoice['id'],
        invoice_number=created_invoice.get('invoice_number', ''),
        date=date_str,
        due_date=due_date_str,
        status=created_invoice.get('status', 'pending'),
        company_name=company_name,
        company_address=company_address,
        company_city=company_city,
        company_state=company_state,
        company_zipcode=company_zipcode,
        company_phone=company_phone,
        company_email=company_email,
        company_logo=company_logo,
        client_name=created_invoice.get('client_name', ''),
        client_address=created_invoice.get('client_address'),
        client_city=created_invoice.get('client_city'),
        client_state=created_invoice.get('client_state'),
        client_zipcode=created_invoice.get('client_zipcode'),
        client_phone=created_invoice.get('client_phone'),
        client_email=created_invoice.get('client_email'),
        insurance_company=None,  # Not stored directly on invoice
        insurance_policy_number=None,
        insurance_claim_number=None,
        insurance_deductible=None,
        subtotal=created_invoice.get('subtotal', 0),
        tax_rate=created_invoice.get('tax_rate', 0),
        tax_amount=created_invoice.get('tax_amount', 0),
        discount=created_invoice.get('discount_amount', 0),  # Map from discount_amount to discount
        shipping=0,  # Not in our model
        total=created_invoice.get('total_amount', 0),  # Map from total_amount to total
        paid_amount=0,  # Not in our model  
        payment_terms=created_invoice.get('payment_terms'),
        notes=created_invoice.get('notes'),
        created_at=created_invoice.get('created_at'),
        updated_at=created_invoice.get('updated_at'),
        items=[
            InvoiceItemResponse(
                id=item.get('id'),
                invoice_id=item.get('invoice_id'),
                name=item.get('description', ''),  # Map from description to name
                description=item.get('description'),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in created_invoice.get('items', [])
        ]
    )


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db=Depends(get_db)
):
    """Update an existing invoice"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    
    # Check if invoice exists
    existing = service.get_by_id(invoice_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Prepare update data
    update_dict = invoice_data.dict(exclude_unset=True)
    
    # Flatten nested objects
    if 'company' in update_dict:
        company = update_dict.pop('company')
        for key, value in company.items():
            update_dict[f'company_{key}'] = value
    
    if 'client' in update_dict:
        client = update_dict.pop('client')
        for key, value in client.items():
            update_dict[f'client_{key}'] = value
    
    if 'insurance' in update_dict:
        insurance = update_dict.pop('insurance')
        if insurance:
            for key, value in insurance.items():
                update_dict[f'insurance_{key}'] = value
    
    # Handle items if provided
    if 'items' in update_dict:
        items = update_dict.pop('items')
        # Convert items to list of dicts
        update_dict['items'] = [
            {
                'name': item.get('name', item['name'] if isinstance(item, dict) else item.name),
                'description': item.get('description', item['description'] if isinstance(item, dict) else item.description),
                'quantity': item.get('quantity', item['quantity'] if isinstance(item, dict) else item.quantity),
                'unit': item.get('unit', item['unit'] if isinstance(item, dict) else item.unit),
                'rate': item.get('rate', item['rate'] if isinstance(item, dict) else item.rate),
                'amount': item.get('quantity', item['quantity'] if isinstance(item, dict) else item.quantity) * item.get('rate', item['rate'] if isinstance(item, dict) else item.rate)
            }
            for item in items
        ]
        
        # Calculate new totals
        subtotal = sum(item['amount'] for item in update_dict['items'])
        tax_amount = subtotal * (update_dict.get('tax_rate', existing.get('tax_rate', 0))) / 100
        update_dict['subtotal'] = subtotal
        update_dict['tax_amount'] = tax_amount
        update_dict['total'] = subtotal + tax_amount - update_dict.get('discount', existing.get('discount', 0)) + update_dict.get('shipping', existing.get('shipping', 0))
    
    # Update invoice
    updated_invoice = service.update(invoice_id, update_dict)
    if not updated_invoice:
        raise HTTPException(status_code=500, detail="Failed to update invoice")
    
    # Convert to response format
    return InvoiceResponse(
        id=updated_invoice['id'],
        invoice_number=updated_invoice.get('invoice_number', ''),
        date=updated_invoice.get('date', ''),
        due_date=updated_invoice.get('due_date', ''),
        status=updated_invoice.get('status', 'draft'),
        company_name=updated_invoice.get('company_name', ''),
        company_address=updated_invoice.get('company_address'),
        company_city=updated_invoice.get('company_city'),
        company_state=updated_invoice.get('company_state'),
        company_zip=updated_invoice.get('company_zip'),
        company_phone=updated_invoice.get('company_phone'),
        company_email=updated_invoice.get('company_email'),
        company_logo=updated_invoice.get('company_logo'),
        client_name=updated_invoice.get('client_name', ''),
        client_address=updated_invoice.get('client_address'),
        client_city=updated_invoice.get('client_city'),
        client_state=updated_invoice.get('client_state'),
        client_zip=updated_invoice.get('client_zip'),
        client_phone=updated_invoice.get('client_phone'),
        client_email=updated_invoice.get('client_email'),
        insurance_company=updated_invoice.get('insurance_company'),
        insurance_policy_number=updated_invoice.get('insurance_policy_number'),
        insurance_claim_number=updated_invoice.get('insurance_claim_number'),
        insurance_deductible=updated_invoice.get('insurance_deductible'),
        subtotal=updated_invoice.get('subtotal', 0),
        tax_rate=updated_invoice.get('tax_rate', 0),
        tax_amount=updated_invoice.get('tax_amount', 0),
        discount=updated_invoice.get('discount', 0),
        shipping=updated_invoice.get('shipping', 0),
        total=updated_invoice.get('total', 0),
        paid_amount=updated_invoice.get('paid_amount', 0),
        payment_terms=updated_invoice.get('payment_terms'),
        notes=updated_invoice.get('notes'),
        created_at=updated_invoice.get('created_at', ''),
        updated_at=updated_invoice.get('updated_at', ''),
        items=[
            InvoiceItemResponse(
                id=item.get('id'),
                invoice_id=item.get('invoice_id'),
                name=item.get('description', ''),  # Map description to name for compatibility
                description=item.get('description'),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in updated_invoice.get('items', [])
        ]
    )


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, db=Depends(get_db)):
    """Delete an invoice"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    
    # Check if invoice exists
    existing = service.get_by_id(invoice_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete invoice
    if not service.delete(invoice_id):
        raise HTTPException(status_code=500, detail="Failed to delete invoice")
    
    return {"message": "Invoice deleted successfully"}


@router.post("/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, db=Depends(get_db)):
    """Generate PDF for an invoice"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    
    # Get invoice from database
    invoice = service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Prepare data for PDF generation
    pdf_data = {
        "invoice_number": invoice.get('invoice_number', ''),
        "date": invoice.get('date', invoice.get('created_at', '')),
        "due_date": invoice.get('due_date', ''),
        "company": {
            "name": invoice.get('company_name', ''),
            "address": invoice.get('company_address'),
            "city": invoice.get('company_city'),
            "state": invoice.get('company_state'),
            "zip": invoice.get('company_zip'),
            "phone": invoice.get('company_phone'),
            "email": invoice.get('company_email'),
            "logo": invoice.get('company_logo')
        },
        "client": {
            "name": invoice.get('client_name', ''),
            "address": invoice.get('client_address'),
            "city": invoice.get('client_city'),
            "state": invoice.get('client_state'),
            "zip": invoice.get('client_zip'),
            "phone": invoice.get('client_phone'),
            "email": invoice.get('client_email')
        },
        "items": [
            {
                "name": item.get('name', ''),
                "description": item.get('description'),
                "quantity": item.get('quantity', 0),
                "unit": item.get('unit', ''),
                "rate": item.get('rate', 0)
            }
            for item in invoice.get('items', [])
        ],
        "subtotal": invoice.get('subtotal', 0),
        "tax_rate": invoice.get('tax_rate', 0),
        "tax_amount": invoice.get('tax_amount', 0),
        "discount": invoice.get('discount', 0),
        "shipping": invoice.get('shipping', 0),
        "total": invoice.get('total', 0),
        "paid_amount": invoice.get('paid_amount', 0),
        "payment_terms": invoice.get('payment_terms'),
        "notes": invoice.get('notes')
    }
    
    # Add insurance info if present
    if invoice.get('insurance_company'):
        pdf_data["insurance"] = {
            "company": invoice.get('insurance_company'),
            "policy_number": invoice.get('insurance_policy_number'),
            "claim_number": invoice.get('insurance_claim_number'),
            "deductible": invoice.get('insurance_deductible')
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
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    if not pdf_service:
        raise HTTPException(status_code=500, detail="PDF service not available")
    
    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Prepare data for PDF generation
        pdf_data = data.dict()
        logger.info(f"Generating PDF preview with data keys: {pdf_data.keys()}")
        
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
        logger.error(f"PDF generation error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/duplicate", response_model=InvoiceResponse)
async def duplicate_invoice(invoice_id: str, db=Depends(get_db)):
    """Duplicate an existing invoice"""
    from ..core.database_factory import get_database
    database = get_database()
    service = InvoiceService(database)
    
    # Duplicate invoice
    duplicated = service.duplicate(invoice_id)
    if not duplicated:
        raise HTTPException(status_code=404, detail="Invoice not found or failed to duplicate")
    
    # Convert to response format
    return InvoiceResponse(
        id=duplicated['id'],
        invoice_number=duplicated.get('invoice_number', ''),
        date=duplicated.get('date', duplicated.get('created_at', '')),
        due_date=duplicated.get('due_date', ''),
        status=duplicated.get('status', 'draft'),
        company_name=duplicated.get('company_name', ''),
        company_address=duplicated.get('company_address'),
        company_city=duplicated.get('company_city'),
        company_state=duplicated.get('company_state'),
        company_zip=duplicated.get('company_zip'),
        company_phone=duplicated.get('company_phone'),
        company_email=duplicated.get('company_email'),
        company_logo=duplicated.get('company_logo'),
        client_name=duplicated.get('client_name', ''),
        client_address=duplicated.get('client_address'),
        client_city=duplicated.get('client_city'),
        client_state=duplicated.get('client_state'),
        client_zip=duplicated.get('client_zip'),
        client_phone=duplicated.get('client_phone'),
        client_email=duplicated.get('client_email'),
        insurance_company=duplicated.get('insurance_company'),
        insurance_policy_number=duplicated.get('insurance_policy_number'),
        insurance_claim_number=duplicated.get('insurance_claim_number'),
        insurance_deductible=duplicated.get('insurance_deductible'),
        subtotal=duplicated.get('subtotal', 0),
        tax_rate=duplicated.get('tax_rate', 0),
        tax_amount=duplicated.get('tax_amount', 0),
        discount=duplicated.get('discount', 0),
        shipping=duplicated.get('shipping', 0),
        total=duplicated.get('total', 0),
        paid_amount=duplicated.get('paid_amount', 0),
        payment_terms=duplicated.get('payment_terms'),
        notes=duplicated.get('notes'),
        created_at=duplicated.get('created_at', ''),
        updated_at=duplicated.get('updated_at', ''),
        items=[
            InvoiceItemResponse(
                id=item.get('id'),
                invoice_id=item.get('invoice_id'),
                name=item.get('description', ''),  # Map description to name for compatibility
                description=item.get('description'),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in duplicated.get('items', [])
        ]
    )