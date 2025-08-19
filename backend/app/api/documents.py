"""
Document API endpoints (combined estimates and invoices)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import io
from app.schemas.document import Document, DocumentFilter, PaginatedDocuments
from app.services.document_service import DocumentService
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=PaginatedDocuments)
async def get_documents(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """Get documents with filters and pagination"""
    service = DocumentService(db)
    
    filter_params = DocumentFilter(
        type=type,
        status=status,
        company_id=company_id,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    result = service.get_documents(filter_params, page, pageSize)
    return result

@router.get("/{document_id}")
async def get_document(document_id: str, db=Depends(get_db)):
    """Get single document by ID"""
    service = DocumentService(db)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"data": document}

@router.delete("/{document_id}")
async def delete_document(document_id: str, db=Depends(get_db)):
    """Delete document"""
    service = DocumentService(db)
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@router.post("/{document_id}/duplicate")
async def duplicate_document(document_id: str, db=Depends(get_db)):
    """Duplicate document"""
    service = DocumentService(db)
    try:
        new_document = service.duplicate_document(document_id)
        if not new_document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"data": new_document, "message": "Document duplicated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}/pdf")
async def generate_pdf(document_id: str, db=Depends(get_db)):
    """Generate PDF for document"""
    service = DocumentService(db)
    
    try:
        pdf_bytes = service.generate_pdf(document_id)
        if not pdf_bytes:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=document_{document_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/send")
async def send_document(document_id: str, email: str, db=Depends(get_db)):
    """Send document via email"""
    service = DocumentService(db)
    try:
        success = service.send_document(document_id, email)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": f"Document sent to {email}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/export")
async def export_documents(filter_params: DocumentFilter, db=Depends(get_db)):
    """Export documents to Excel"""
    service = DocumentService(db)
    try:
        excel_bytes = service.export_to_excel(filter_params)
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=documents_export.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))