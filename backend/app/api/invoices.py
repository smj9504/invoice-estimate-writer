"""
Invoice API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db=Depends(get_db)):
    """Create new invoice"""
    service = InvoiceService(db)
    try:
        new_invoice = service.create(invoice.dict())
        return InvoiceResponse(data=new_invoice, message="Invoice created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db=Depends(get_db)):
    """Get single invoice"""
    service = InvoiceService(db)
    invoice = service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse(data=invoice)

@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, invoice: InvoiceUpdate, db=Depends(get_db)):
    """Update invoice"""
    service = InvoiceService(db)
    try:
        updated_invoice = service.update(invoice_id, invoice.dict(exclude_none=True))
        if not updated_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return InvoiceResponse(data=updated_invoice, message="Invoice updated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, db=Depends(get_db)):
    """Delete invoice"""
    service = InvoiceService(db)
    try:
        success = service.delete(invoice_id)
        if not success:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"message": "Invoice deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))