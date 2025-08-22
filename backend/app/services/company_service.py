"""
Company service for business logic
"""

from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import uuid
import os
import base64
import random
import string
from datetime import datetime
from app.core.config import settings

class CompanyService:
    """Service for company-related operations"""
    
    def __init__(self, db):
        self.db = db
    
    def generate_company_code(self, company_name: str) -> str:
        """Generate a unique 4-character company code based on company name"""
        # Extract uppercase letters from company name
        name_letters = ''.join([c.upper() for c in company_name if c.isalpha()])
        
        # Generate code with mix of letters from name and random characters
        code_chars = []
        
        # Try to use first 2 letters from company name
        if len(name_letters) >= 2:
            code_chars.extend(list(name_letters[:2]))
        elif len(name_letters) == 1:
            code_chars.append(name_letters[0])
            # Add random letter
            code_chars.append(random.choice(string.ascii_uppercase))
        else:
            # No letters in name, use random letters
            code_chars.extend([random.choice(string.ascii_uppercase) for _ in range(2)])
        
        # Add 2 random digits or letters
        for _ in range(2):
            if random.choice([True, False]):
                code_chars.append(random.choice(string.digits))
            else:
                code_chars.append(random.choice(string.ascii_uppercase))
        
        code = ''.join(code_chars)
        
        # Check if code already exists
        try:
            response = self.db.table('companies').select('company_code').eq('company_code', code).execute()
            if response.data:
                # Code exists, generate a new one recursively with more randomness
                return self.generate_company_code(company_name + str(random.randint(1, 999)))
        except:
            pass
        
        return code
    
    def get_all(self, search: Optional[str] = None, city: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all companies with optional filters"""
        try:
            query = self.db.table('companies').select('*')
            
            # Apply search filter across multiple fields
            if search:
                # Supabase doesn't support OR in the way we need, so we'll filter in Python
                response = query.execute()
                companies = response.data if response.data else []
                search_lower = search.lower()
                filtered = [
                    c for c in companies
                    if search_lower in (c.get('name', '') or '').lower()
                    or search_lower in (c.get('address', '') or '').lower()
                    or search_lower in (c.get('email', '') or '').lower()
                    or search_lower in (c.get('phone', '') or '').lower()
                ]
                
                # Apply additional filters
                if city:
                    filtered = [c for c in filtered if c.get('city', '').lower() == city.lower()]
                if state:
                    filtered = [c for c in filtered if c.get('state', '').lower() == state.lower()]
                
                return filtered
            else:
                # Apply city and state filters directly
                if city:
                    query = query.eq('city', city)
                if state:
                    query = query.eq('state', state)
                
                response = query.order('name').execute()
                return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching companies: {e}")
            return []
    
    def get_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company by ID"""
        try:
            response = self.db.table('companies').select('*').eq('id', company_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching company {company_id}: {e}")
            return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new company"""
        try:
            # Remove logo_url if present (we use 'logo' field)
            data.pop('logo_url', None)
            
            # Remove timestamps if they don't exist in database
            # The companies table in Supabase doesn't have created_at/updated_at columns
            data.pop('created_at', None)
            data.pop('updated_at', None)
            
            # Generate company code if not provided
            if not data.get('company_code'):
                data['company_code'] = self.generate_company_code(data.get('name', ''))
            
            response = self.db.table('companies').insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error creating company: {e}")
            raise
    
    def update(self, company_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update company"""
        try:
            # Remove fields that might cause issues
            data.pop('logo_url', None)
            data.pop('created_at', None)
            data.pop('updated_at', None)
            data.pop('id', None)  # Remove id from update data
            
            # Only update if there's data to update
            if not data:
                print(f"No data to update for company {company_id}")
                return None
            
            print(f"Updating company {company_id} with data: {data}")
            response = self.db.table('companies').update(data).eq('id', company_id).execute()
            
            if response.data:
                print(f"Update successful: {response.data[0]}")
                return response.data[0]
            else:
                print(f"No data returned from update for company {company_id}")
                return None
        except Exception as e:
            print(f"Error updating company {company_id}: {e}")
            raise e  # Re-raise the exception so it can be handled by the API layer
    
    def delete(self, company_id: str) -> bool:
        """Delete company"""
        try:
            self.db.table('companies').delete().eq('id', company_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting company {company_id}: {e}")
            return False
    
    async def upload_logo(self, company_id: str, file: UploadFile) -> str:
        """Upload company logo as base64"""
        try:
            # Read file content
            content = await file.read()
            
            # Convert to base64
            base64_str = base64.b64encode(content).decode('utf-8')
            
            # Add data URL prefix based on content type
            if file.content_type:
                logo_data = f"data:{file.content_type};base64,{base64_str}"
            else:
                # Default to PNG if content type is not provided
                logo_data = f"data:image/png;base64,{base64_str}"
            
            # Update company with logo data
            self.update(company_id, {"logo": logo_data})
            
            return logo_data
        except Exception as e:
            print(f"Error uploading logo for company {company_id}: {e}")
            raise