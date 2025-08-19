"""
Company service for business logic
"""

from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import uuid
import os
from datetime import datetime
from app.core.config import settings

class CompanyService:
    """Service for company-related operations"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all companies"""
        try:
            response = self.db.table('company').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching companies: {e}")
            return []
    
    def get_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company by ID"""
        try:
            response = self.db.table('company').select('*').eq('id', company_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching company {company_id}: {e}")
            return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new company"""
        try:
            # Add timestamp
            data['created_at'] = datetime.utcnow().isoformat()
            response = self.db.table('company').insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error creating company: {e}")
            raise
    
    def update(self, company_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update company"""
        try:
            # Add timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            response = self.db.table('company').update(data).eq('id', company_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating company {company_id}: {e}")
            return None
    
    def delete(self, company_id: str) -> bool:
        """Delete company"""
        try:
            self.db.table('company').delete().eq('id', company_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting company {company_id}: {e}")
            return False
    
    async def upload_logo(self, company_id: str, file: UploadFile) -> str:
        """Upload company logo"""
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{company_id}_{uuid.uuid4()}{file_extension}"
        file_path = settings.UPLOAD_DIR / "logos" / unique_filename
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update company with logo URL
        logo_url = f"/uploads/logos/{unique_filename}"
        self.update(company_id, {"logo_url": logo_url})
        
        return logo_url