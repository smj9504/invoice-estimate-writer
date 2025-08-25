"""
Company service with comprehensive business logic and validation.
"""

from typing import Any, Dict, List, Optional
import logging
import uuid
import random
import string
from fastapi import UploadFile
import base64

from app.services.base_service import BaseService
from app.repositories import get_company_repository
from app.core.interfaces import DatabaseProvider
from app.core.database_factory import get_database

logger = logging.getLogger(__name__)


class CompanyService(BaseService[Dict[str, Any], str]):
    """
    Service for company-related business operations.
    Provides comprehensive CRUD operations with validation and business logic.
    """
    
    def __init__(self, database: DatabaseProvider = None):
        super().__init__(database)
    
    def get_repository(self):
        """Get the company repository"""
        # This is called by the base class but we don't use it directly
        pass
    
    def _get_repository_instance(self, session):
        """Get company repository instance with the given session"""
        return get_company_repository(session)
    
    def generate_company_code(self, company_name: str, existing_codes: List[str] = None) -> str:
        """
        Generate a unique 4-character company code based on company name.
        
        Args:
            company_name: Name of the company
            existing_codes: List of existing codes to avoid duplicates
            
        Returns:
            Unique 4-character company code
        """
        if existing_codes is None:
            existing_codes = []
        
        # Extract uppercase letters from company name
        name_letters = ''.join([c.upper() for c in company_name if c.isalpha()])
        
        # Generate code with mix of letters from name and random characters
        code_chars = []
        
        # Try to use first 2 letters from company name
        if len(name_letters) >= 2:
            code_chars.extend(list(name_letters[:2]))
        elif len(name_letters) == 1:
            code_chars.append(name_letters[0])
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
        if code in existing_codes:
            # Generate a new one with more randomness
            return self.generate_company_code(
                company_name + str(random.randint(1, 999)), 
                existing_codes
            )
        
        return code
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search companies by name, address, email, or phone.
        
        Args:
            search_term: Text to search for
            
        Returns:
            List of matching company dictionaries
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.search_companies(search_term)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise
    
    def get_companies_with_filters(self, 
                                   search: Optional[str] = None,
                                   city: Optional[str] = None,
                                   state: Optional[str] = None,
                                   limit: Optional[int] = None,
                                   offset: Optional[int] = None) -> Dict[str, Any]:
        """
        Get companies with comprehensive filtering options.
        
        Args:
            search: Search term for name, address, email, or phone
            city: Filter by city
            state: Filter by state
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Dictionary with companies and metadata
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                companies = repository.get_by_filters(
                    search=search,
                    city=city,
                    state=state,
                    limit=limit,
                    offset=offset
                )
                
                total_count = repository.count()
                
                return {
                    'companies': companies,
                    'total': total_count,
                    'count': len(companies),
                    'has_more': len(companies) == limit if limit else False
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error getting companies with filters: {e}")
            raise
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get company by email address.
        
        Args:
            email: Company email address
            
        Returns:
            Company dictionary or None if not found
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.get_by_email(email)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error getting company by email: {e}")
            raise
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get company by exact name match.
        
        Args:
            name: Company name
            
        Returns:
            Company dictionary or None if not found
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.get_by_name(name)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error getting company by name: {e}")
            raise
    
    def get_companies_with_stats(self) -> List[Dict[str, Any]]:
        """
        Get companies with additional statistics (invoice count, estimate count).
        
        Returns:
            List of company dictionaries with statistics
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.get_companies_with_stats()
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error getting companies with stats: {e}")
            raise
    
    def create(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new company with validation and business logic.
        
        Args:
            company_data: Company data dictionary
            
        Returns:
            Created company dictionary
        """
        # Validate required fields
        validated_data = self._validate_create_data(company_data)
        
        # Generate UUID if not provided
        if 'id' not in validated_data:
            validated_data['id'] = str(uuid.uuid4())
        
        # Generate company code if not provided
        if not validated_data.get('company_code'):
            # Get existing codes to avoid duplicates
            existing_codes = []
            try:
                existing_companies = self.get_all()
                existing_codes = [
                    c.get('company_code') for c in existing_companies 
                    if c.get('company_code')
                ]
            except Exception:
                logger.warning("Could not retrieve existing company codes")
            
            validated_data['company_code'] = self.generate_company_code(
                validated_data.get('name', ''), existing_codes
            )
        
        return super().create(validated_data)
    
    def update(self, company_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a company with validation.
        
        Args:
            company_id: Company ID
            update_data: Updated company data
            
        Returns:
            Updated company dictionary or None if not found
        """
        # Validate update data
        validated_data = self._validate_update_data(update_data)
        
        return super().update(company_id, validated_data)
    
    async def upload_logo(self, company_id: str, file: UploadFile) -> Dict[str, str]:
        """
        Upload and process company logo.
        
        Args:
            company_id: Company ID
            file: Uploaded logo file
            
        Returns:
            Dictionary with logo data and message
        """
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith("image/"):
                raise ValueError("File must be an image")
            
            # Validate file size (5MB limit)
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:
                raise ValueError("File size must be less than 5MB")
            
            # Convert to base64
            base64_str = base64.b64encode(content).decode('utf-8')
            logo_data = f"data:{file.content_type};base64,{base64_str}"
            
            # Update company with logo
            updated_company = self.update(company_id, {"logo": logo_data})
            
            if not updated_company:
                raise ValueError(f"Company with ID {company_id} not found")
            
            return {
                "logo": logo_data,
                "message": "Logo uploaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Error uploading logo for company {company_id}: {e}")
            raise
    
    def delete_with_validation(self, company_id: str) -> bool:
        """
        Delete a company with validation to ensure no dependent records.
        
        Args:
            company_id: Company ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If company has dependent records
        """
        try:
            # Check for dependent records
            from app.services.invoice_service import InvoiceService
            from app.services.estimate_service import EstimateService
            
            invoice_service = InvoiceService(self.database)
            estimate_service = EstimateService(self.database)
            
            # Check for invoices
            invoices = invoice_service.get_invoices_by_company(company_id)
            if invoices:
                raise ValueError(
                    f"Cannot delete company: {len(invoices)} invoices exist. "
                    "Please delete or reassign invoices first."
                )
            
            # Check for estimates
            estimates = estimate_service.get_estimates_by_company(company_id)
            if estimates:
                raise ValueError(
                    f"Cannot delete company: {len(estimates)} estimates exist. "
                    "Please delete or reassign estimates first."
                )
            
            return self.delete(company_id)
            
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {e}")
            raise
    
    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for company creation"""
        if not data.get('name'):
            raise ValueError("Company name is required")
        
        # Clean data
        validated_data = data.copy()
        
        # Remove None values
        validated_data = {k: v for k, v in validated_data.items() if v is not None}
        
        # Remove system fields
        for field in ['created_at', 'updated_at']:
            validated_data.pop(field, None)
        
        # Validate email format if provided
        email = validated_data.get('email')
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        
        # Validate phone format if provided
        phone = validated_data.get('phone')
        if phone and len(phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')) < 10:
            logger.warning(f"Phone number might be invalid: {phone}")
        
        return validated_data
    
    def _validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for company update"""
        validated_data = data.copy()
        
        # Remove None values
        validated_data = {k: v for k, v in validated_data.items() if v is not None}
        
        # Remove system fields and ID
        for field in ['created_at', 'updated_at', 'id']:
            validated_data.pop(field, None)
        
        if not validated_data:
            raise ValueError("No valid data provided for update")
        
        # Validate email format if provided
        email = validated_data.get('email')
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        
        return validated_data
    
    def get_company_summary(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive company summary with related data.
        
        Args:
            company_id: Company ID
            
        Returns:
            Dictionary with company data and summary statistics
        """
        try:
            company = self.get_by_id(company_id)
            if not company:
                return None
            
            # Get related statistics
            from app.services.invoice_service import InvoiceService
            from app.services.estimate_service import EstimateService
            
            invoice_service = InvoiceService(self.database)
            estimate_service = EstimateService(self.database)
            
            invoices = invoice_service.get_invoices_by_company(company_id)
            estimates = estimate_service.get_estimates_by_company(company_id)
            
            # Calculate totals
            total_invoice_amount = sum(
                float(inv.get('total_amount', 0)) for inv in invoices
            )
            total_estimate_amount = sum(
                float(est.get('total_amount', 0)) for est in estimates
            )
            
            # Count by status
            invoice_status_counts = {}
            for invoice in invoices:
                status = invoice.get('status', 'unknown')
                invoice_status_counts[status] = invoice_status_counts.get(status, 0) + 1
            
            estimate_status_counts = {}
            for estimate in estimates:
                status = estimate.get('status', 'unknown')
                estimate_status_counts[status] = estimate_status_counts.get(status, 0) + 1
            
            company['summary'] = {
                'invoice_count': len(invoices),
                'estimate_count': len(estimates),
                'total_invoice_amount': total_invoice_amount,
                'total_estimate_amount': total_estimate_amount,
                'invoice_status_counts': invoice_status_counts,
                'estimate_status_counts': estimate_status_counts
            }
            
            return company
            
        except Exception as e:
            logger.error(f"Error getting company summary for {company_id}: {e}")
            raise