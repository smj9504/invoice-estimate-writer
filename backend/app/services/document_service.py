"""
Document service for combined document operations
"""

from typing import Optional, Dict, Any, List
import io
from datetime import datetime

from app.services.estimate_service import EstimateService
from app.services.invoice_service import InvoiceService
from app.schemas.document import DocumentFilter, PaginatedDocuments

class DocumentService:
    """Service for document-related operations"""
    
    def __init__(self, db):
        self.db = db
        self.estimate_service = EstimateService(db)
        self.invoice_service = InvoiceService(db)
    
    def get_documents(self, filter_params: DocumentFilter, page: int, page_size: int) -> PaginatedDocuments:
        """Get documents with filters and pagination"""
        documents = []
        
        # Get estimates if included in filter
        if not filter_params.type or filter_params.type in ['all', 'estimate']:
            estimates = self.estimate_service.get_all()
            for estimate in estimates:
                # Apply filters
                if filter_params.status and estimate.get('status') != filter_params.status:
                    continue
                if filter_params.company_id and estimate.get('company_id') != filter_params.company_id:
                    continue
                if filter_params.date_from and estimate.get('created_at') < filter_params.date_from.isoformat():
                    continue
                if filter_params.date_to and estimate.get('created_at') > filter_params.date_to.isoformat():
                    continue
                
                documents.append({
                    'id': estimate['id'],
                    'type': 'estimate',
                    'number': estimate.get('estimate_number', ''),
                    'date': estimate.get('created_at', ''),
                    'status': estimate.get('status', 'draft'),
                    'total': estimate.get('total', 0),
                    'company_id': estimate.get('company_id'),
                    'company_name': estimate.get('company_name', ''),
                    'client_name': estimate.get('client_name', ''),
                })
        
        # Get invoices if included in filter
        if not filter_params.type or filter_params.type in ['all', 'invoice']:
            invoices = self.invoice_service.get_all()
            for invoice in invoices:
                # Apply filters
                if filter_params.status and invoice.get('status') != filter_params.status:
                    continue
                if filter_params.company_id and invoice.get('company_id') != filter_params.company_id:
                    continue
                if filter_params.date_from and invoice.get('created_at') < filter_params.date_from.isoformat():
                    continue
                if filter_params.date_to and invoice.get('created_at') > filter_params.date_to.isoformat():
                    continue
                
                documents.append({
                    'id': invoice['id'],
                    'type': 'invoice',
                    'number': invoice.get('invoice_number', ''),
                    'date': invoice.get('created_at', ''),
                    'status': invoice.get('status', 'draft'),
                    'total': invoice.get('total', 0),
                    'company_id': invoice.get('company_id'),
                    'company_name': invoice.get('company_name', ''),
                    'client_name': invoice.get('client_name', ''),
                })
        
        # Sort by date (newest first)
        documents.sort(key=lambda x: x['date'], reverse=True)
        
        # Apply search filter
        if filter_params.search:
            search_term = filter_params.search.lower()
            documents = [
                doc for doc in documents
                if search_term in doc['number'].lower()
                or search_term in doc.get('client_name', '').lower()
                or search_term in doc.get('company_name', '').lower()
            ]
        
        # Pagination
        total = len(documents)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = documents[start:end]
        
        return PaginatedDocuments(
            items=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 0
        )
    
    def generate_pdf(self, document_type: str, document_id: str) -> bytes:
        """Generate PDF for a document"""
        # This is a placeholder - actual PDF generation would require
        # setting up WeasyPrint and templates in the backend
        # For now, return empty bytes
        return b''
    
    def export_to_excel(self, document_type: str, document_id: str) -> bytes:
        """Export document to Excel format"""
        # This is a placeholder for Excel export functionality
        return b''