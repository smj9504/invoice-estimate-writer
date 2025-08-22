"""
Invoice service for business logic
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.services.document_number_service import DocumentNumberService
import json
import re

class InvoiceService:
    """Service for invoice-related operations"""
    
    def __init__(self, db):
        self.db = db
        self.doc_number_service = DocumentNumberService(db)
    
    def generate_invoice_number(self, client_address: str, company_code: str) -> str:
        """Generate invoice number using common document number service"""
        return self.doc_number_service.generate_document_number(
            'invoice',
            client_address,
            company_code
        )
    
    def get_all(self, company_id: Optional[str] = None, status: Optional[str] = None, 
                limit: Optional[int] = 50, offset: Optional[int] = 0) -> List[Dict[str, Any]]:
        """Get all invoices with optional filtering"""
        try:
            query = self.db.table('general_invoice').select('*')
            
            if company_id:
                query = query.eq('company_id', company_id)
            if status:
                query = query.eq('status', status)
            
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []
    
    def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID with items"""
        try:
            # Get invoice
            response = self.db.table('general_invoice').select('*').eq('id', invoice_id).execute()
            if not response.data:
                return None
            
            invoice = response.data[0]
            
            # Get invoice items
            items_response = self.db.table('general_invoice_items').select('*').eq('invoice_id', invoice_id).execute()
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
            response = self.db.table('general_invoice').insert(data).execute()
            if not response.data:
                raise Exception("Failed to create invoice")
            
            invoice = response.data[0]
            invoice_id = invoice['id']
            
            # Create invoice items
            if items:
                for item in items:
                    item['invoice_id'] = invoice_id
                    item['created_at'] = datetime.utcnow().isoformat()
                
                items_response = self.db.table('general_invoice_items').insert(items).execute()
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
            response = self.db.table('general_invoice').update(data).eq('id', invoice_id).execute()
            if not response.data:
                return None
            
            invoice = response.data[0]
            
            # Update items if provided
            if items is not None:
                # Delete existing items
                self.db.table('general_invoice_items').delete().eq('invoice_id', invoice_id).execute()
                
                # Insert new items
                if items:
                    for item in items:
                        item['invoice_id'] = invoice_id
                        item['created_at'] = datetime.utcnow().isoformat()
                    
                    items_response = self.db.table('general_invoice_items').insert(items).execute()
                    invoice['items'] = items_response.data if items_response.data else []
                else:
                    invoice['items'] = []
            else:
                # Fetch existing items
                items_response = self.db.table('general_invoice_items').select('*').eq('invoice_id', invoice_id).execute()
                invoice['items'] = items_response.data if items_response.data else []
            
            return invoice
        except Exception as e:
            print(f"Error updating invoice {invoice_id}: {e}")
            return None
    
    def delete(self, invoice_id: str) -> bool:
        """Delete invoice and its items"""
        try:
            # Delete items first
            self.db.table('general_invoice_items').delete().eq('invoice_id', invoice_id).execute()
            
            # Delete invoice
            self.db.table('general_invoice').delete().eq('id', invoice_id).execute()
            
            return True
        except Exception as e:
            print(f"Error deleting invoice {invoice_id}: {e}")
            return False
    
    def get_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all invoices for a company"""
        try:
            response = self.db.table('general_invoice').select('*').eq('company_id', company_id).execute()
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
    
    def generate_pdf(self, invoice_id: str) -> Optional[bytes]:
        """Generate PDF for invoice"""
        try:
            # Import PDF generator
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
            from pdf_generator import generate_pdf
            
            # Get invoice data
            invoice = self.get_by_id(invoice_id)
            if not invoice:
                return None
            
            # Convert to format expected by PDF generator
            pdf_data = self._convert_to_pdf_format(invoice)
            
            # Generate PDF
            pdf_bytes = generate_pdf("invoice", pdf_data)
            return pdf_bytes
        except Exception as e:
            print(f"Error generating PDF for invoice {invoice_id}: {e}")
            return None
    
    def convert_json_to_invoice(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert imported JSON data to invoice format"""
        try:
            # Extract client information
            client = json_data.get("client", {})
            
            # Convert service sections to items
            items = []
            sections = json_data.get("serviceSections", [])
            for section in sections:
                for item in section.get("items", []):
                    items.append({
                        "name": item.get("name", ""),
                        "description": item.get("dec", ""),
                        "quantity": float(item.get("qty", 0)),
                        "unit": item.get("unit", ""),
                        "unit_price": float(item.get("price", 0)),
                        "total": float(item.get("qty", 0)) * float(item.get("price", 0)),
                        "category": section.get("title", ""),
                        "hide_price": item.get("hide_price", False)
                    })
            
            # Convert to invoice format
            invoice_data = {
                "invoice_number": json_data.get("invoice_number", ""),
                "date_of_issue": json_data.get("date_of_issue", datetime.utcnow().isoformat()),
                "due_date": json_data.get("date_due", datetime.utcnow().isoformat()),
                "client_name": client.get("name", ""),
                "client_email": client.get("email", ""),
                "client_phone": client.get("phone", ""),
                "client_address": f"{client.get('address', '')} {client.get('city', '')} {client.get('state', '')} {client.get('zip', '')}".strip(),
                "client_type": json_data.get("client_type", "individual"),
                "company_id": json_data.get("company", {}).get("id"),
                "notes": json_data.get("top_note", ""),
                "bottom_notes": json_data.get("bottom_note", ""),
                "disclaimer": json_data.get("disclaimer", ""),
                "tax_type": json_data.get("tax_type", "none"),
                "tax_rate": float(json_data.get("tax_rate", 0)),
                "tax_amount": float(json_data.get("tax_amount", 0)),
                "status": "draft",
                "items": items,
                "payments": json_data.get("payments", [])
            }
            
            return invoice_data
        except Exception as e:
            print(f"Error converting JSON to invoice: {e}")
            raise
    
    def get_item_suggestions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get invoice item suggestions from database"""
        try:
            query = self.db.table('general_invoice_items').select('*')
            if category:
                query = query.eq('category', category)
            
            response = query.order('name').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching item suggestions: {e}")
            return []
    
    def _convert_to_pdf_format(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Convert invoice data to format expected by PDF generator"""
        items = invoice.get('items', [])
        
        # Group items by category into sections
        sections_dict = {}
        for item in items:
            category = item.get('category', 'Items')
            if category not in sections_dict:
                sections_dict[category] = {
                    "title": category,
                    "items": [],
                    "showSubtotal": True,
                    "subtotal": 0.0
                }
            
            sections_dict[category]["items"].append({
                "name": item.get("name", ""),
                "dec": item.get("description", ""),
                "qty": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "price": item.get("unit_price", 0),
                "hide_price": item.get("hide_price", False)
            })
            
            if not item.get("hide_price", False):
                sections_dict[category]["subtotal"] += item.get("total", 0)
        
        sections = list(sections_dict.values())
        
        # Calculate totals
        subtotal_total = sum(section["subtotal"] for section in sections)
        tax_calculated = 0.0
        
        if invoice.get("tax_type") == "percentage":
            tax_calculated = subtotal_total * (invoice.get("tax_rate", 0) / 100)
        elif invoice.get("tax_type") == "fixed":
            tax_calculated = invoice.get("tax_amount", 0)
        
        total_with_tax = subtotal_total + tax_calculated
        payments_total = sum(p.get("amount", 0) for p in invoice.get("payments", []))
        total_due = total_with_tax - payments_total
        
        return {
            "invoice_number": invoice.get("invoice_number", ""),
            "date_of_issue": invoice.get("date_of_issue", ""),
            "date_due": invoice.get("due_date", ""),
            "client": {
                "name": invoice.get("client_name", ""),
                "email": invoice.get("client_email", ""),
                "phone": invoice.get("client_phone", ""),
                "address": invoice.get("client_address", ""),
                "type": invoice.get("client_type", "individual")
            },
            "company": {
                "id": invoice.get("company_id", "")
            },
            "serviceSections": sections,
            "top_note": invoice.get("notes", ""),
            "bottom_note": invoice.get("bottom_notes", ""),
            "disclaimer": invoice.get("disclaimer", ""),
            "tax_type": invoice.get("tax_type", "none"),
            "tax_rate": invoice.get("tax_rate", 0),
            "tax_amount": invoice.get("tax_amount", 0),
            "tax_calculated": tax_calculated,
            "subtotal_total": subtotal_total,
            "total_with_tax": total_with_tax,
            "total": total_due,
            "payments": invoice.get("payments", [])
        }