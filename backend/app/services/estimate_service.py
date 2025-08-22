"""
Estimate service for business logic
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.services.document_number_service import DocumentNumberService
import json

class EstimateService:
    """Service for estimate-related operations"""
    
    def __init__(self, db):
        self.db = db
        self.doc_number_service = DocumentNumberService(db)
    
    def generate_estimate_number(self, client_address: str, company_code: str) -> str:
        """Generate estimate number using common document number service"""
        return self.doc_number_service.generate_document_number(
            'estimate',
            client_address,
            company_code
        )
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all estimates"""
        try:
            response = self.db.table('estimate').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching estimates: {e}")
            return []
    
    def get_by_id(self, estimate_id: str) -> Optional[Dict[str, Any]]:
        """Get estimate by ID with items"""
        try:
            # Get estimate
            response = self.db.table('estimate').select('*').eq('id', estimate_id).execute()
            if not response.data:
                return None
            
            estimate = response.data[0]
            
            # Get estimate items
            items_response = self.db.table('estimate_items').select('*').eq('estimate_id', estimate_id).execute()
            estimate['items'] = items_response.data if items_response.data else []
            
            return estimate
        except Exception as e:
            print(f"Error fetching estimate {estimate_id}: {e}")
            return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new estimate with items"""
        try:
            # Extract items from data
            items = data.pop('items', [])
            
            # Add timestamp
            data['created_at'] = datetime.utcnow().isoformat()
            
            # Create estimate
            response = self.db.table('estimate').insert(data).execute()
            if not response.data:
                raise Exception("Failed to create estimate")
            
            estimate = response.data[0]
            estimate_id = estimate['id']
            
            # Create estimate items
            if items:
                for item in items:
                    item['estimate_id'] = estimate_id
                    item['created_at'] = datetime.utcnow().isoformat()
                
                items_response = self.db.table('estimate_items').insert(items).execute()
                estimate['items'] = items_response.data if items_response.data else []
            else:
                estimate['items'] = []
            
            return estimate
        except Exception as e:
            print(f"Error creating estimate: {e}")
            raise
    
    def update(self, estimate_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update estimate"""
        try:
            # Handle items separately if included
            items = data.pop('items', None)
            
            # Add timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update estimate
            response = self.db.table('estimate').update(data).eq('id', estimate_id).execute()
            if not response.data:
                return None
            
            estimate = response.data[0]
            
            # Update items if provided
            if items is not None:
                # Delete existing items
                self.db.table('estimate_items').delete().eq('estimate_id', estimate_id).execute()
                
                # Insert new items
                if items:
                    for item in items:
                        item['estimate_id'] = estimate_id
                        item['created_at'] = datetime.utcnow().isoformat()
                    
                    items_response = self.db.table('estimate_items').insert(items).execute()
                    estimate['items'] = items_response.data if items_response.data else []
                else:
                    estimate['items'] = []
            else:
                # Fetch existing items
                items_response = self.db.table('estimate_items').select('*').eq('estimate_id', estimate_id).execute()
                estimate['items'] = items_response.data if items_response.data else []
            
            return estimate
        except Exception as e:
            print(f"Error updating estimate {estimate_id}: {e}")
            return None
    
    def delete(self, estimate_id: str) -> bool:
        """Delete estimate and its items"""
        try:
            # Delete items first
            self.db.table('estimate_items').delete().eq('estimate_id', estimate_id).execute()
            
            # Delete estimate
            self.db.table('estimate').delete().eq('id', estimate_id).execute()
            
            return True
        except Exception as e:
            print(f"Error deleting estimate {estimate_id}: {e}")
            return False
    
    def get_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all estimates for a company"""
        try:
            response = self.db.table('estimate').select('*').eq('company_id', company_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching estimates for company {company_id}: {e}")
            return []
    
    def duplicate(self, estimate_id: str) -> Optional[Dict[str, Any]]:
        """Duplicate an estimate"""
        try:
            # Get original estimate
            original = self.get_by_id(estimate_id)
            if not original:
                return None
            
            # Prepare new estimate data
            new_data = {k: v for k, v in original.items() if k not in ['id', 'created_at', 'updated_at']}
            new_data['estimate_number'] = f"{original.get('estimate_number', 'EST')}-COPY"
            new_data['status'] = 'draft'
            
            # Create new estimate
            return self.create(new_data)
        except Exception as e:
            print(f"Error duplicating estimate {estimate_id}: {e}")
            return None