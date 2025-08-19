"""
Invoice service for business logic
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
import json

class InvoiceService:
    """Service for invoice-related operations"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all invoices"""
        try:
            response = self.db.table('invoice').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []
    
    def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID with items"""
        try:
            # Get invoice
            response = self.db.table('invoice').select('*').eq('id', invoice_id).execute()
            if not response.data:
                return None
            
            invoice = response.data[0]
            
            # Get invoice items
            items_response = self.db.table('invoice_items').select('*').eq('invoice_id', invoice_id).execute()
            invoice['items'] = items_response.data if items_response.data else []
            
            return invoice
        except Exception as e:
            print(f"Error fetching invoice {invoice_id}: {e}")
            return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new invoice with items"""
        try:
            # Extract items from data
            items = data.pop('items', [])
            
            # Add timestamp
            data['created_at'] = datetime.utcnow().isoformat()
            
            # Create invoice
            response = self.db.table('invoice').insert(data).execute()
            if not response.data:
                raise Exception("Failed to create invoice")
            
            invoice = response.data[0]
            invoice_id = invoice['id']
            
            # Create invoice items
            if items:
                for item in items:
                    item['invoice_id'] = invoice_id
                    item['created_at'] = datetime.utcnow().isoformat()
                
                items_response = self.db.table('invoice_items').insert(items).execute()
                invoice['items'] = items_response.data if items_response.data else []
            else:
                invoice['items'] = []
            
            return invoice
        except Exception as e:
            print(f"Error creating invoice: {e}")
            raise
    
    def update(self, invoice_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update invoice"""
        try:
            # Handle items separately if included
            items = data.pop('items', None)
            
            # Add timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update invoice
            response = self.db.table('invoice').update(data).eq('id', invoice_id).execute()
            if not response.data:
                return None
            
            invoice = response.data[0]
            
            # Update items if provided
            if items is not None:
                # Delete existing items
                self.db.table('invoice_items').delete().eq('invoice_id', invoice_id).execute()
                
                # Insert new items
                if items:
                    for item in items:
                        item['invoice_id'] = invoice_id
                        item['created_at'] = datetime.utcnow().isoformat()
                    
                    items_response = self.db.table('invoice_items').insert(items).execute()
                    invoice['items'] = items_response.data if items_response.data else []
                else:
                    invoice['items'] = []
            else:
                # Fetch existing items
                items_response = self.db.table('invoice_items').select('*').eq('invoice_id', invoice_id).execute()
                invoice['items'] = items_response.data if items_response.data else []
            
            return invoice
        except Exception as e:
            print(f"Error updating invoice {invoice_id}: {e}")
            return None
    
    def delete(self, invoice_id: str) -> bool:
        """Delete invoice and its items"""
        try:
            # Delete items first
            self.db.table('invoice_items').delete().eq('invoice_id', invoice_id).execute()
            
            # Delete invoice
            self.db.table('invoice').delete().eq('id', invoice_id).execute()
            
            return True
        except Exception as e:
            print(f"Error deleting invoice {invoice_id}: {e}")
            return False
    
    def get_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all invoices for a company"""
        try:
            response = self.db.table('invoice').select('*').eq('company_id', company_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching invoices for company {company_id}: {e}")
            return []
    
    def duplicate(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Duplicate an invoice"""
        try:
            # Get original invoice
            original = self.get_by_id(invoice_id)
            if not original:
                return None
            
            # Prepare new invoice data
            new_data = {k: v for k, v in original.items() if k not in ['id', 'created_at', 'updated_at']}
            new_data['invoice_number'] = f"{original.get('invoice_number', 'INV')}-COPY"
            new_data['status'] = 'draft'
            
            # Create new invoice
            return self.create(new_data)
        except Exception as e:
            print(f"Error duplicating invoice {invoice_id}: {e}")
            return None
    
    def mark_as_paid(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Mark invoice as paid"""
        return self.update(invoice_id, {
            'status': 'paid',
            'paid_date': datetime.utcnow().isoformat()
        })